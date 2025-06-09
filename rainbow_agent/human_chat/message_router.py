from typing import Dict, Any, List, Optional, Callable
import asyncio
import logging

logger = logging.getLogger(__name__)

class MessageRouter:
    """消息路由系统，负责将消息传递给正确的接收者"""
    
    def __init__(self):
        # 用户连接映射 {user_id: [connection_handlers]}
        self.connections = {}
        # 离线消息队列 {user_id: [messages]}
        self.offline_messages = {}
        
    def register_connection(self, user_id: str, handler: Callable):
        """注册用户连接"""
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(handler)
        
        # 处理离线消息
        if user_id in self.offline_messages and self.offline_messages[user_id]:
            for message in self.offline_messages[user_id]:
                self.deliver_message_to_user(user_id, message)
            self.offline_messages[user_id] = []
            
    def unregister_connection(self, user_id: str, handler: Callable):
        """注销用户连接"""
        if user_id in self.connections:
            if handler in self.connections[user_id]:
                self.connections[user_id].remove(handler)
            if not self.connections[user_id]:
                del self.connections[user_id]
    
    async def route_message(self, message: Dict[str, Any], recipients: List[str]):
        """路由消息到指定接收者"""
        for recipient_id in recipients:
            await self.deliver_message_to_user(recipient_id, message)
    
    async def deliver_message_to_user(self, user_id: str, message: Dict[str, Any]):
        """将消息传递给特定用户"""
        if user_id in self.connections and self.connections[user_id]:
            # 用户在线，直接发送
            delivery_tasks = []
            for handler in self.connections[user_id]:
                delivery_tasks.append(asyncio.create_task(handler(message)))
            
            await asyncio.gather(*delivery_tasks)
            return True
        else:
            # 用户离线，存储消息
            if user_id not in self.offline_messages:
                self.offline_messages[user_id] = []
            self.offline_messages[user_id].append(message)
            return False