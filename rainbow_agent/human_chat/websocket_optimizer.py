from typing import Dict, Any, List, Optional, Set
import logging
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketOptimizer:
    """WebSocket通信优化器，用于优化实时消息传输"""
    
    def __init__(self, batch_interval_ms: int = 100, max_batch_size: int = 20):
        """
        初始化WebSocket优化器
        
        Args:
            batch_interval_ms: 批处理间隔（毫秒）
            max_batch_size: 最大批处理大小
        """
        self.batch_interval_ms = batch_interval_ms
        self.max_batch_size = max_batch_size
        self.message_batches: Dict[str, List[Dict[str, Any]]] = {}  # 用户ID -> 消息批次
        self.last_flush_time: Dict[str, float] = {}  # 用户ID -> 上次刷新时间
        self.active_users: Set[str] = set()  # 活跃用户集合
        
        logger.info(f"WebSocket优化器初始化成功，批处理间隔={batch_interval_ms}毫秒，最大批处理大小={max_batch_size}")
    
    def register_user(self, user_id: str) -> None:
        """注册用户连接"""
        self.active_users.add(user_id)
        self.message_batches[user_id] = []
        self.last_flush_time[user_id] = time.time()
        logger.debug(f"用户 {user_id} 已注册到WebSocket优化器")
    
    def unregister_user(self, user_id: str) -> None:
        """注销用户连接"""
        if user_id in self.active_users:
            self.active_users.remove(user_id)
        if user_id in self.message_batches:
            del self.message_batches[user_id]
        if user_id in self.last_flush_time:
            del self.last_flush_time[user_id]
        logger.debug(f"用户 {user_id} 已从WebSocket优化器注销")
    
    def is_user_active(self, user_id: str) -> bool:
        """检查用户是否活跃"""
        return user_id in self.active_users
    
    def queue_message(self, user_id: str, message: Dict[str, Any]) -> bool:
        """
        将消息加入用户的消息队列
        
        Args:
            user_id: 接收消息的用户ID
            message: 消息内容
            
        Returns:
            bool: 是否需要立即发送
        """
        if not self.is_user_active(user_id):
            logger.debug(f"用户 {user_id} 不活跃，消息不会被加入队列")
            return False
        
        # 为消息添加时间戳（如果没有）
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # 某些消息类型需要立即发送，不进行批处理
        if message.get("type") in ["typing", "presence_change", "error"]:
            logger.debug(f"消息类型 {message.get('type')} 需要立即发送")
            return True
        
        # 将消息添加到批次中
        self.message_batches[user_id].append(message)
        
        # 检查是否需要刷新批次
        now = time.time()
        time_since_last_flush = (now - self.last_flush_time.get(user_id, 0)) * 1000  # 转换为毫秒
        
        if len(self.message_batches[user_id]) >= self.max_batch_size or time_since_last_flush >= self.batch_interval_ms:
            logger.debug(f"批次已满或达到时间间隔，需要刷新批次，用户={user_id}，批次大小={len(self.message_batches[user_id])}")
            return True
        
        logger.debug(f"消息已加入队列，用户={user_id}，批次大小={len(self.message_batches[user_id])}")
        return False
    
    def get_pending_messages(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的待发送消息
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Dict[str, Any]]: 待发送的消息列表
        """
        if not self.is_user_active(user_id) or user_id not in self.message_batches:
            return []
        
        messages = self.message_batches[user_id]
        self.message_batches[user_id] = []
        self.last_flush_time[user_id] = time.time()
        
        logger.debug(f"获取用户 {user_id} 的待发送消息，数量={len(messages)}")
        return messages
    
    def optimize_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        优化单个消息，减少传输大小
        
        Args:
            message: 原始消息
            
        Returns:
            Dict[str, Any]: 优化后的消息
        """
        # 创建消息的副本，避免修改原始消息
        optimized = message.copy()
        
        # 移除不必要的字段
        for field in ["debug_info", "internal_metadata", "raw_data"]:
            if field in optimized:
                del optimized[field]
        
        # 压缩长文本内容（如果需要）
        if "content" in optimized and isinstance(optimized["content"], str) and len(optimized["content"]) > 1000:
            # 这里可以实现更复杂的文本压缩算法
            # 简单起见，我们只保留前1000个字符
            optimized["content"] = optimized["content"][:1000] + "..."
            optimized["content_truncated"] = True
        
        return optimized
    
    def create_batch_message(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        创建批处理消息
        
        Args:
            messages: 消息列表
            
        Returns:
            Dict[str, Any]: 批处理消息
        """
        optimized_messages = [self.optimize_message(msg) for msg in messages]
        
        return {
            "type": "batch",
            "messages": optimized_messages,
            "count": len(optimized_messages),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取优化器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_queued_messages = sum(len(batch) for batch in self.message_batches.values())
        
        return {
            "active_users": len(self.active_users),
            "total_queued_messages": total_queued_messages,
            "batch_interval_ms": self.batch_interval_ms,
            "max_batch_size": self.max_batch_size
        }
