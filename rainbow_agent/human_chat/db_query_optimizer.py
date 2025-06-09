from typing import Dict, Any, List, Optional, Tuple, Set, Callable
import logging
import asyncio
import time
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

class DBQueryOptimizer:
    """数据库查询优化器，用于优化数据库查询操作"""
    
    def __init__(self, batch_size: int = 50, batch_wait_ms: int = 100):
        """
        初始化数据库查询优化器
        
        Args:
            batch_size: 批量查询大小
            batch_wait_ms: 批量查询等待时间（毫秒）
        """
        self.batch_size = batch_size
        self.batch_wait_ms = batch_wait_ms
        self.batch_operations = {}  # 操作类型 -> 批量操作队列
        self.batch_locks = {}  # 操作类型 -> 锁
        self.batch_events = {}  # 操作类型 -> 事件
        self.batch_results = {}  # 批处理ID -> 结果
        
        logger.info(f"数据库查询优化器初始化成功，批量大小={batch_size}，等待时间={batch_wait_ms}毫秒")
    
    def _get_batch_lock(self, operation_type: str):
        """获取批量操作锁"""
        if operation_type not in self.batch_locks:
            self.batch_locks[operation_type] = asyncio.Lock()
        return self.batch_locks[operation_type]
    
    def _get_batch_event(self, operation_type: str):
        """获取批量操作事件"""
        if operation_type not in self.batch_events:
            self.batch_events[operation_type] = asyncio.Event()
        return self.batch_events[operation_type]
    
    def _get_batch_queue(self, operation_type: str):
        """获取批量操作队列"""
        if operation_type not in self.batch_operations:
            self.batch_operations[operation_type] = []
        return self.batch_operations[operation_type]
    
    async def batch_get_sessions(self, session_ids: List[str], storage):
        """
        批量获取会话
        
        Args:
            session_ids: 会话ID列表
            storage: 存储实例
            
        Returns:
            Dict[str, Any]: 会话ID -> 会话数据
        """
        if not session_ids:
            return {}
        
        # 如果只有一个ID，直接查询
        if len(session_ids) == 1:
            session = await storage.get_session_async(session_ids[0])
            return {session_ids[0]: session} if session else {}
        
        # 批量查询
        results = {}
        
        # 分批处理，每批不超过batch_size
        for i in range(0, len(session_ids), self.batch_size):
            batch = session_ids[i:i + self.batch_size]
            batch_results = await asyncio.gather(
                *[storage.get_session_async(sid) for sid in batch]
            )
            
            # 将结果添加到结果字典
            for sid, result in zip(batch, batch_results):
                if result:
                    results[sid] = result
        
        return results
    
    async def batch_get_messages(self, message_ids: List[str], storage):
        """
        批量获取消息
        
        Args:
            message_ids: 消息ID列表
            storage: 存储实例
            
        Returns:
            Dict[str, Any]: 消息ID -> 消息数据
        """
        if not message_ids:
            return {}
        
        # 如果只有一个ID，直接查询
        if len(message_ids) == 1:
            message = await storage.get_turn_async(message_ids[0])
            return {message_ids[0]: message} if message else {}
        
        # 批量查询
        results = {}
        
        # 分批处理，每批不超过batch_size
        for i in range(0, len(message_ids), self.batch_size):
            batch = message_ids[i:i + self.batch_size]
            batch_results = await asyncio.gather(
                *[storage.get_turn_async(mid) for mid in batch]
            )
            
            # 将结果添加到结果字典
            for mid, result in zip(batch, batch_results):
                if result:
                    results[mid] = result
        
        return results
    
    async def batch_update_messages(self, updates: List[Tuple[str, Dict[str, Any]]], storage):
        """
        批量更新消息
        
        Args:
            updates: 更新列表，每个元素为(消息ID, 更新数据)
            storage: 存储实例
            
        Returns:
            Dict[str, bool]: 消息ID -> 更新结果
        """
        if not updates:
            return {}
        
        # 如果只有一个更新，直接执行
        if len(updates) == 1:
            mid, update_data = updates[0]
            success = await storage.update_turn_async(mid, update_data)
            return {mid: success}
        
        # 批量更新
        results = {}
        
        # 分批处理，每批不超过batch_size
        for i in range(0, len(updates), self.batch_size):
            batch = updates[i:i + self.batch_size]
            batch_results = await asyncio.gather(
                *[storage.update_turn_async(mid, update_data) for mid, update_data in batch]
            )
            
            # 将结果添加到结果字典
            for (mid, _), result in zip(batch, batch_results):
                results[mid] = result
        
        return results
    
    async def optimize_session_query(self, session_id: str, storage):
        """
        优化会话查询
        
        Args:
            session_id: 会话ID
            storage: 存储实例
            
        Returns:
            Dict[str, Any]: 会话数据
        """
        # 这里可以添加更多优化逻辑
        return await storage.get_session_async(session_id)
    
    async def optimize_messages_query(self, session_id: str, limit: int, before_id: Optional[str], storage):
        """
        优化消息查询
        
        Args:
            session_id: 会话ID
            limit: 消息数量限制
            before_id: 查询此ID之前的消息
            storage: 存储实例
            
        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        # 获取所有消息
        all_messages = await storage.list_turns_async(session_id)
        
        # 过滤出人类对话消息
        human_chat_messages = [
            msg for msg in all_messages 
            if msg.get("metadata", {}).get("human_chat", False)
        ]
        
        # 按创建时间降序排序
        human_chat_messages.sort(key=lambda m: m.get("created_at", ""), reverse=True)
        
        # 如果指定了before_id，找到该消息的位置
        if before_id:
            for i, msg in enumerate(human_chat_messages):
                if msg.get("id") == before_id:
                    human_chat_messages = human_chat_messages[i+1:]
                    break
        
        # 限制消息数量
        return human_chat_messages[:limit]
    
    def optimize_query_decorator(self, func):
        """
        查询优化装饰器
        
        Args:
            func: 要优化的查询函数
            
        Returns:
            装饰后的函数
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 记录查询开始时间
            start_time = time.time()
            
            # 执行原始查询
            result = await func(*args, **kwargs)
            
            # 计算查询耗时
            elapsed_ms = (time.time() - start_time) * 1000
            
            # 记录查询耗时
            logger.debug(f"查询 {func.__name__} 耗时 {elapsed_ms:.2f} 毫秒")
            
            return result
        
        return wrapper
