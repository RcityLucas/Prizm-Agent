"""
异步操作工具函数

提供异步操作的辅助函数，简化异步代码的编写
"""
import asyncio
import logging
from typing import Any, Callable, TypeVar, Awaitable

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

T = TypeVar('T')

def run_async(coroutine_func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
    """
    运行异步函数并返回结果
    
    为当前线程创建独立的事件循环，运行异步函数，并返回结果
    这种方式可以在多线程 Web 应用程序中安全地使用异步 IO
    
    Args:
        coroutine_func: 异步函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        异步函数的返回值
    """
    logger.info(f"准备运行异步函数: {coroutine_func.__name__}")
    
    # 始终创建新的事件循环，避免事件循环绑定问题
    loop = asyncio.new_event_loop()
    
    try:
        # 在新的事件循环中运行协程
        logger.info(f"在新事件循环中运行函数: {coroutine_func.__name__}")
        asyncio.set_event_loop(loop)
        coroutine = coroutine_func(*args, **kwargs)
        result = loop.run_until_complete(coroutine)
        logger.info(f"异步函数 {coroutine_func.__name__} 运行成功")
        return result
    except Exception as e:
        logger.error(f"运行异步函数 {coroutine_func.__name__} 失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"错误详情: {error_traceback}")
        
        # 为常用函数提供特殊错误处理
        if coroutine_func.__name__ == 'get_sessions':
            logger.info("返回空会话列表")
            return []
        elif coroutine_func.__name__ == 'get_turns':
            logger.info("返回空轮次列表")
            return []
        elif coroutine_func.__name__ == 'process_input':
            logger.info("返回空对话输入结果")
            return {
                "id": str(kwargs.get("session_id", "unknown")),
                "content": kwargs.get("content", ""),
                "response": f"处理输入时出现错误: {str(e)}",
                "success": False,
                "error": str(e)
            }
        else:
            # 其他函数抛出异常，以便上层代码处理
            raise Exception(f"运行异步函数 {coroutine_func.__name__} 失败: {e}\n{error_traceback}")
    finally:
        # 始终关闭循环，释放资源
        if not loop.is_closed():
            try:
                # 取消所有未完成的任务
                pending = asyncio.all_tasks(loop=loop)
                if pending:
                    logger.info(f"取消 {len(pending)} 个未完成的异步任务")
                    for task in pending:
                        task.cancel()
                    # 等待所有任务取消
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as e:
                logger.warning(f"清理事件循环任务时出错: {e}")
            finally:
                logger.info("关闭事件循环")
                loop.close()
