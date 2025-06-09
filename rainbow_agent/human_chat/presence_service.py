from typing import Dict, Set, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class PresenceService:
    """用户在线状态服务"""
    
    def __init__(self):
        # 在线用户集合 {user_id: last_active_time}
        self.online_users = {}
        # 状态订阅 {user_id: {subscriber_ids}}
        self.status_subscriptions = {}
        # 心跳超时（秒）
        self.heartbeat_timeout = 30
        
    async def start_monitoring(self):
        """启动状态监控"""
        while True:
            await self.check_timeouts()
            await asyncio.sleep(10)  # 每10秒检查一次
    
    async def check_timeouts(self):
        """检查超时用户"""
        now = datetime.now()
        timed_out = []
        
        for user_id, last_active in self.online_users.items():
            if (now - last_active).total_seconds() > self.heartbeat_timeout:
                timed_out.append(user_id)
        
        # 处理超时用户
        for user_id in timed_out:
            await self.set_offline(user_id)
    
    async def heartbeat(self, user_id: str):
        """用户心跳更新"""
        was_offline = user_id not in self.online_users
        self.online_users[user_id] = datetime.now()
        
        if was_offline:
            await self.notify_status_change(user_id, True)
    
    async def set_offline(self, user_id: str):
        """设置用户离线"""
        if user_id in self.online_users:
            del self.online_users[user_id]
            await self.notify_status_change(user_id, False)
    
    def is_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self.online_users
    
    def subscribe_to_status(self, subscriber_id: str, target_id: str):
        """订阅用户状态变化"""
        if target_id not in self.status_subscriptions:
            self.status_subscriptions[target_id] = set()
        self.status_subscriptions[target_id].add(subscriber_id)
    
    def unsubscribe_from_status(self, subscriber_id: str, target_id: str):
        """取消订阅用户状态"""
        if target_id in self.status_subscriptions:
            self.status_subscriptions[target_id].discard(subscriber_id)
            if not self.status_subscriptions[target_id]:
                del self.status_subscriptions[target_id]
    
    async def notify_status_change(self, user_id: str, is_online: bool):
        """通知状态变化"""
        if user_id not in self.status_subscriptions:
            return
            
        # 通知所有订阅者
        # 实际实现时，这里应该调用MessageRouter来发送通知
        status_message = {
            "type": "status_update",
            "user_id": user_id,
            "status": "online" if is_online else "offline",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"用户 {user_id} 状态变为 {'在线' if is_online else '离线'}")
        # 这里应该调用消息路由器发送通知