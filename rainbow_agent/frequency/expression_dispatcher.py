# rainbow_agent/frequency/expression_dispatcher.py
"""
表达调度器，负责将生成的表达内容调度到适当的输出通道
"""
from typing import Dict, Any, List, Optional, Callable, Awaitable
import asyncio
import time
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ExpressionDispatcher:
    """
    表达调度器，负责将生成的表达内容调度到适当的输出通道
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化表达调度器
        
        Args:
            config: 配置参数，包含输出通道、调度策略等
        """
        self.config = config or {}
        
        # 输出通道注册表
        self.output_channels = {}
        
        # 调度队列
        self.dispatch_queue = asyncio.Queue()
        
        # 是否正在运行
        self.is_running = False
        
        # 调度任务
        self.dispatch_task = None
        
        # 调度历史
        self.dispatch_history = []
        
        # 最大历史记录数
        self.max_history_size = self.config.get("max_history_size", 50)
        
        logger.info("表达调度器初始化完成")
    
    def register_channel(self, channel_name: str, channel_func: Callable[[Dict[str, Any]], Awaitable[bool]]):
        """
        注册输出通道
        
        Args:
            channel_name: 通道名称
            channel_func: 通道函数，接收表达信息，返回是否成功的异步函数
        """
        self.output_channels[channel_name] = channel_func
        logger.info(f"注册输出通道: {channel_name}")
    
    def unregister_channel(self, channel_name: str):
        """
        注销输出通道
        
        Args:
            channel_name: 通道名称
        """
        if channel_name in self.output_channels:
            del self.output_channels[channel_name]
            logger.info(f"注销输出通道: {channel_name}")
    
    async def dispatch(self, expression: Dict[str, Any], channel: Optional[str] = None) -> bool:
        """
        调度表达内容到指定通道
        
        Args:
            expression: 表达信息
            channel: 指定的输出通道，如果为None则自动选择
            
        Returns:
            是否成功调度
        """
        # 确定输出通道
        target_channel = channel or self._select_channel(expression)
        
        # 检查通道是否存在
        if target_channel not in self.output_channels:
            logger.error(f"输出通道不存在: {target_channel}")
            return False
        
        try:
            # 调用通道函数
            channel_func = self.output_channels[target_channel]
            success = await channel_func(expression)
            
            # 记录调度历史
            dispatch_record = {
                "timestamp": time.time(),
                "expression_type": expression["content"]["type"],
                "channel": target_channel,
                "success": success,
                "expression_id": expression.get("id", "unknown")
            }
            self._update_dispatch_history(dispatch_record)
            
            if success:
                logger.info(f"表达内容成功调度到通道: {target_channel}")
            else:
                logger.warning(f"表达内容调度到通道失败: {target_channel}")
            
            return success
            
        except Exception as e:
            logger.error(f"调度表达内容错误: {e}")
            return False
    
    async def queue_expression(self, expression: Dict[str, Any], channel: Optional[str] = None):
        """
        将表达内容加入调度队列
        
        Args:
            expression: 表达信息
            channel: 指定的输出通道，如果为None则自动选择
        """
        # 将表达内容和通道信息加入队列
        await self.dispatch_queue.put((expression, channel))
        logger.debug(f"表达内容已加入调度队列，类型: {expression['content']['type']}")
    
    async def start_dispatcher(self):
        """
        启动调度器
        """
        if self.is_running:
            logger.warning("调度器已经在运行")
            return
        
        self.is_running = True
        self.dispatch_task = asyncio.create_task(self._dispatch_worker())
        logger.info("调度器已启动")
    
    async def stop_dispatcher(self):
        """
        停止调度器
        """
        if not self.is_running:
            logger.warning("调度器未在运行")
            return
        
        self.is_running = False
        if self.dispatch_task:
            self.dispatch_task.cancel()
            try:
                await self.dispatch_task
            except asyncio.CancelledError:
                pass
            self.dispatch_task = None
        
        logger.info("调度器已停止")
    
    async def _dispatch_worker(self):
        """
        调度工作器，从队列中获取表达内容并调度
        """
        logger.info("调度工作器启动")
        
        while self.is_running:
            try:
                # 从队列中获取表达内容
                expression, channel = await self.dispatch_queue.get()
                
                # 调度表达内容
                await self.dispatch(expression, channel)
                
                # 标记任务完成
                self.dispatch_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("调度工作器被取消")
                break
            except Exception as e:
                logger.error(f"调度工作器错误: {e}")
    
    def _select_channel(self, expression: Dict[str, Any]) -> str:
        """
        自动选择合适的输出通道
        
        Args:
            expression: 表达信息
            
        Returns:
            选择的通道名称
        """
        # 获取表达类型和优先级
        expression_type = expression["content"]["type"]
        priority = expression.get("priority_score", 0.5)
        
        # 根据表达类型和优先级选择通道
        # 这里是一个简单的示例，实际应用中可以根据需要扩展
        if priority > 0.8:
            # 高优先级使用主要通道
            return "main"
        elif expression_type in ["reminder", "alert"]:
            # 提醒和警报使用通知通道
            return "notification"
        elif expression_type in ["greeting", "observation"]:
            # 问候和观察使用次要通道
            return "secondary"
        else:
            # 默认使用主要通道
            return "main"
    
    def _update_dispatch_history(self, record: Dict[str, Any]):
        """
        更新调度历史
        
        Args:
            record: 调度记录
        """
        self.dispatch_history.append(record)
        
        # 限制历史记录大小
        if len(self.dispatch_history) > self.max_history_size:
            self.dispatch_history = self.dispatch_history[-self.max_history_size:]
    
    def get_dispatch_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取调度历史
        
        Args:
            limit: 限制返回的历史记录数量
            
        Returns:
            调度历史记录
        """
        if limit is None or limit >= len(self.dispatch_history):
            return self.dispatch_history
        return self.dispatch_history[-limit:]
