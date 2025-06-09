from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging
import threading
import time

logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器，用于缓存频繁访问的数据，减少数据库查询"""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        初始化缓存管理器
        
        Args:
            ttl_seconds: 缓存项的生存时间（秒）
        """
        self.ttl_seconds = ttl_seconds
        self.session_cache: Dict[str, Dict[str, Any]] = {}  # 会话缓存
        self.message_cache: Dict[str, Dict[str, Any]] = {}  # 消息缓存
        self.user_sessions_cache: Dict[str, List[Dict[str, Any]]] = {}  # 用户会话列表缓存
        self.session_messages_cache: Dict[str, List[Dict[str, Any]]] = {}  # 会话消息列表缓存
        
        self.cache_timestamps: Dict[str, Dict[str, float]] = {
            "session": {},
            "message": {},
            "user_sessions": {},
            "session_messages": {}
        }
        
        # 启动缓存清理线程
        self._start_cleanup_thread()
        
        logger.info(f"缓存管理器初始化成功，TTL={ttl_seconds}秒")
    
    def _start_cleanup_thread(self):
        """启动缓存清理线程"""
        def cleanup_task():
            while True:
                try:
                    self._cleanup_expired_cache()
                    time.sleep(60)  # 每分钟清理一次
                except Exception as e:
                    logger.error(f"缓存清理线程异常: {str(e)}")
        
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        logger.info("缓存清理线程已启动")
    
    def _cleanup_expired_cache(self):
        """清理过期的缓存项"""
        now = time.time()
        
        # 清理会话缓存
        expired_sessions = []
        for session_id, timestamp in self.cache_timestamps["session"].items():
            if now - timestamp > self.ttl_seconds:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            if session_id in self.session_cache:
                del self.session_cache[session_id]
            del self.cache_timestamps["session"][session_id]
        
        # 清理消息缓存
        expired_messages = []
        for message_id, timestamp in self.cache_timestamps["message"].items():
            if now - timestamp > self.ttl_seconds:
                expired_messages.append(message_id)
        
        for message_id in expired_messages:
            if message_id in self.message_cache:
                del self.message_cache[message_id]
            del self.cache_timestamps["message"][message_id]
        
        # 清理用户会话列表缓存
        expired_user_sessions = []
        for user_id, timestamp in self.cache_timestamps["user_sessions"].items():
            if now - timestamp > self.ttl_seconds:
                expired_user_sessions.append(user_id)
        
        for user_id in expired_user_sessions:
            if user_id in self.user_sessions_cache:
                del self.user_sessions_cache[user_id]
            del self.cache_timestamps["user_sessions"][user_id]
        
        # 清理会话消息列表缓存
        expired_session_messages = []
        for session_id, timestamp in self.cache_timestamps["session_messages"].items():
            if now - timestamp > self.ttl_seconds:
                expired_session_messages.append(session_id)
        
        for session_id in expired_session_messages:
            if session_id in self.session_messages_cache:
                del self.session_messages_cache[session_id]
            del self.cache_timestamps["session_messages"][session_id]
        
        if any([expired_sessions, expired_messages, expired_user_sessions, expired_session_messages]):
            logger.debug(f"已清理过期缓存: {len(expired_sessions)}个会话, {len(expired_messages)}个消息, "
                        f"{len(expired_user_sessions)}个用户会话列表, {len(expired_session_messages)}个会话消息列表")
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """从缓存获取会话"""
        if session_id in self.session_cache:
            return self.session_cache[session_id]
        return None
    
    def set_session(self, session_id: str, session_data: Dict[str, Any]):
        """设置会话缓存"""
        self.session_cache[session_id] = session_data
        self.cache_timestamps["session"][session_id] = time.time()
    
    def invalidate_session(self, session_id: str):
        """使会话缓存失效"""
        if session_id in self.session_cache:
            del self.session_cache[session_id]
        if session_id in self.cache_timestamps["session"]:
            del self.cache_timestamps["session"][session_id]
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """从缓存获取消息"""
        if message_id in self.message_cache:
            return self.message_cache[message_id]
        return None
    
    def set_message(self, message_id: str, message_data: Dict[str, Any]):
        """设置消息缓存"""
        self.message_cache[message_id] = message_data
        self.cache_timestamps["message"][message_id] = time.time()
    
    def invalidate_message(self, message_id: str):
        """使消息缓存失效"""
        if message_id in self.message_cache:
            del self.message_cache[message_id]
        if message_id in self.cache_timestamps["message"]:
            del self.cache_timestamps["message"][message_id]
    
    def get_user_sessions(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """从缓存获取用户会话列表"""
        if user_id in self.user_sessions_cache:
            return self.user_sessions_cache[user_id]
        return None
    
    def set_user_sessions(self, user_id: str, sessions_data: List[Dict[str, Any]]):
        """设置用户会话列表缓存"""
        self.user_sessions_cache[user_id] = sessions_data
        self.cache_timestamps["user_sessions"][user_id] = time.time()
    
    def invalidate_user_sessions(self, user_id: str):
        """使用户会话列表缓存失效"""
        if user_id in self.user_sessions_cache:
            del self.user_sessions_cache[user_id]
        if user_id in self.cache_timestamps["user_sessions"]:
            del self.cache_timestamps["user_sessions"][user_id]
    
    def get_session_messages(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """从缓存获取会话消息列表"""
        if session_id in self.session_messages_cache:
            return self.session_messages_cache[session_id]
        return None
    
    def set_session_messages(self, session_id: str, messages_data: List[Dict[str, Any]]):
        """设置会话消息列表缓存"""
        self.session_messages_cache[session_id] = messages_data
        self.cache_timestamps["session_messages"][session_id] = time.time()
    
    def invalidate_session_messages(self, session_id: str):
        """使会话消息列表缓存失效"""
        if session_id in self.session_messages_cache:
            del self.session_messages_cache[session_id]
        if session_id in self.cache_timestamps["session_messages"]:
            del self.cache_timestamps["session_messages"][session_id]
    
    def invalidate_all(self):
        """清空所有缓存"""
        self.session_cache.clear()
        self.message_cache.clear()
        self.user_sessions_cache.clear()
        self.session_messages_cache.clear()
        
        for cache_type in self.cache_timestamps:
            self.cache_timestamps[cache_type].clear()
        
        logger.info("已清空所有缓存")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "session_cache_size": len(self.session_cache),
            "message_cache_size": len(self.message_cache),
            "user_sessions_cache_size": len(self.user_sessions_cache),
            "session_messages_cache_size": len(self.session_messages_cache),
            "ttl_seconds": self.ttl_seconds
        }
