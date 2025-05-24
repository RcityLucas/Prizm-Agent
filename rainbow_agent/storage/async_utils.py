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
    
    创建新的事件循环，运行异步函数，并返回结果
    
    Args:
        coroutine_func: 异步函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        异步函数的返回值
    """
    logger.info(f"准备运行异步函数: {coroutine_func.__name__}, 参数: {args}, {kwargs}")
    loop = None
    try:
        # 尝试获取当前事件循环
        try:
            loop = asyncio.get_event_loop()
            logger.info("使用现有事件循环")
        except RuntimeError:
            # 如果当前线程没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("创建新的事件循环")
        
        # 检查循环是否已关闭
        if loop.is_closed():
            logger.warning("事件循环已关闭，创建新的事件循环")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 运行协程
        logger.info(f"开始运行异步函数: {coroutine_func.__name__}")
        coroutine = coroutine_func(*args, **kwargs)
        result = loop.run_until_complete(coroutine)
        logger.info(f"异步函数 {coroutine_func.__name__} 运行成功")
        return result
    except Exception as e:
        logger.error(f"运行异步函数 {coroutine_func.__name__} 失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"错误详情: {error_traceback}")
        # 返回空列表而不是抛出异常，以避免服务器崩溃
        if coroutine_func.__name__ == 'get_sessions':
            logger.info("返回空会话列表")
            return []
        elif coroutine_func.__name__ == 'get_turns':
            logger.info("返回空轮次列表")
            return []
        else:
            raise Exception(f"运行异步函数 {coroutine_func.__name__} 失败: {e}\n{error_traceback}")
    finally:
        # 只关闭我们创建的循环
        if loop and not loop.is_closed() and loop is not asyncio.get_event_loop():
            logger.info("关闭事件循环")
            loop.close()
