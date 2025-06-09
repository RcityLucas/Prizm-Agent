import logging
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime
import json
import asyncio

logger = logging.getLogger(__name__)

class NotificationService:
    """通知服务，负责处理实时消息通知和推送通知
    
    该服务提供以下功能：
    1. 实时消息通知：通过WebSocket向在线用户发送通知
    2. 离线消息通知：为离线用户存储通知，等待用户上线时发送
    3. 会话事件通知：如新会话创建、用户加入/退出会话等
    4. 消息状态通知：如消息已读、已送达等
    """
    
    def __init__(self):
        # 连接管理 {user_id: connection}
        self.connections = {}
        # 通知处理器 {notification_type: handler_function}
        self.notification_handlers = {}
        # 离线通知队列 {user_id: [notifications]}
        self.offline_notifications = {}
        # 最大离线通知数量
        self.max_offline_notifications = 100
        
        logger.info("通知服务初始化完成")
    
    def register_connection(self, user_id: str, connection: Any) -> None:
        """注册用户连接
        
        Args:
            user_id: 用户ID
            connection: 用户连接对象（如WebSocket连接）
        """
        self.connections[user_id] = connection
        logger.info(f"用户 {user_id} 已连接")
        
        # 处理离线通知
        self._process_offline_notifications(user_id)
    
    def unregister_connection(self, user_id: str) -> None:
        """注销用户连接
        
        Args:
            user_id: 用户ID
        """
        if user_id in self.connections:
            del self.connections[user_id]
            logger.info(f"用户 {user_id} 已断开连接")
    
    def register_handler(self, notification_type: str, handler: Callable) -> None:
        """注册通知处理器
        
        Args:
            notification_type: 通知类型
            handler: 处理函数
        """
        self.notification_handlers[notification_type] = handler
        logger.info(f"已注册 {notification_type} 类型的通知处理器")
    
    async def send_notification(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """发送通知给指定用户
        
        Args:
            user_id: 接收通知的用户ID
            notification: 通知内容
            
        Returns:
            是否成功发送
        """
        # 添加时间戳
        if "timestamp" not in notification:
            notification["timestamp"] = datetime.now().isoformat()
        
        # 检查用户是否在线
        if user_id in self.connections:
            # 用户在线，直接发送
            try:
                connection = self.connections[user_id]
                await self._send_to_connection(connection, notification)
                logger.info(f"已向用户 {user_id} 发送通知: {notification['type']}")
                return True
            except Exception as e:
                logger.error(f"向用户 {user_id} 发送通知失败: {e}")
                # 连接可能已断开，存储为离线通知
                self._store_offline_notification(user_id, notification)
                return False
        else:
            # 用户离线，存储通知
            self._store_offline_notification(user_id, notification)
            logger.info(f"用户 {user_id} 离线，通知已存储")
            return False
    
    async def broadcast_notification(self, user_ids: List[str], notification: Dict[str, Any]) -> Dict[str, bool]:
        """向多个用户广播通知
        
        Args:
            user_ids: 接收通知的用户ID列表
            notification: 通知内容
            
        Returns:
            用户ID到发送结果的映射
        """
        results = {}
        for user_id in user_ids:
            results[user_id] = await self.send_notification(user_id, notification)
        return results
    
    async def notify_session_created(self, session: Dict[str, Any], participants: List[str]) -> None:
        """通知会话创建
        
        Args:
            session: 会话信息
            participants: 参与者列表
        """
        creator_id = session.get("creator_id") or session.get("metadata", {}).get("creator_id")
        
        # 构建通知
        notification = {
            "type": "session_created",
            "session_id": session.get("id"),
            "title": session.get("title"),
            "creator_id": creator_id,
            "participants": participants,
            "is_group": len(participants) > 2,
            "timestamp": datetime.now().isoformat()
        }
        
        # 向除创建者外的所有参与者发送通知
        recipients = [p for p in participants if p != creator_id]
        await self.broadcast_notification(recipients, notification)
    
    async def notify_message_sent(self, message: Dict[str, Any], recipients: List[str]) -> None:
        """通知消息发送
        
        Args:
            message: 消息信息
            recipients: 接收者列表
        """
        # 构建通知
        notification = {
            "type": "new_message",
            "message_id": message.get("id"),
            "session_id": message.get("session_id"),
            "sender_id": message.get("metadata", {}).get("sender_id"),
            "content": message.get("content"),
            "content_type": message.get("metadata", {}).get("content_type", "text"),
            "timestamp": datetime.now().isoformat()
        }
        
        # 向所有接收者发送通知
        await self.broadcast_notification(recipients, notification)
    
    async def notify_message_read(self, message_id: str, session_id: str, reader_id: str, sender_id: str) -> None:
        """通知消息已读
        
        Args:
            message_id: 消息ID
            session_id: 会话ID
            reader_id: 读取消息的用户ID
            sender_id: 消息发送者ID
        """
        # 构建通知
        notification = {
            "type": "message_read",
            "message_id": message_id,
            "session_id": session_id,
            "reader_id": reader_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 只通知消息发送者
        await self.send_notification(sender_id, notification)
    
    async def notify_user_typing(self, session_id: str, user_id: str, participants: List[str]) -> None:
        """通知用户正在输入
        
        Args:
            session_id: 会话ID
            user_id: 正在输入的用户ID
            participants: 会话参与者列表
        """
        # 构建通知
        notification = {
            "type": "user_typing",
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 向除了正在输入的用户外的所有参与者发送通知
        recipients = [p for p in participants if p != user_id]
        await self.broadcast_notification(recipients, notification)
    
    def _store_offline_notification(self, user_id: str, notification: Dict[str, Any]) -> None:
        """存储离线通知
        
        Args:
            user_id: 用户ID
            notification: 通知内容
        """
        if user_id not in self.offline_notifications:
            self.offline_notifications[user_id] = []
        
        # 限制离线通知数量
        if len(self.offline_notifications[user_id]) >= self.max_offline_notifications:
            # 移除最旧的通知
            self.offline_notifications[user_id].pop(0)
        
        self.offline_notifications[user_id].append(notification)
    
    async def _process_offline_notifications(self, user_id: str) -> None:
        """处理用户的离线通知
        
        Args:
            user_id: 用户ID
        """
        if user_id not in self.offline_notifications or not self.offline_notifications[user_id]:
            return
        
        if user_id not in self.connections:
            logger.warning(f"用户 {user_id} 没有活跃连接，无法处理离线通知")
            return
        
        connection = self.connections[user_id]
        notifications = self.offline_notifications[user_id]
        
        # 批量发送离线通知
        try:
            # 先发送一个摘要通知
            summary = {
                "type": "offline_notifications_summary",
                "count": len(notifications),
                "timestamp": datetime.now().isoformat()
            }
            await self._send_to_connection(connection, summary)
            
            # 然后逐个发送详细通知
            for notification in notifications:
                await self._send_to_connection(connection, notification)
                # 短暂延迟，避免客户端过载
                await asyncio.sleep(0.05)
            
            # 清空离线通知
            self.offline_notifications[user_id] = []
            logger.info(f"已向用户 {user_id} 发送 {len(notifications)} 条离线通知")
        except Exception as e:
            logger.error(f"处理用户 {user_id} 的离线通知失败: {e}")
    
    async def _send_to_connection(self, connection: Any, data: Dict[str, Any]) -> None:
        """向连接发送数据
        
        Args:
            connection: 连接对象
            data: 要发送的数据
        """
        # 根据连接类型发送数据
        # 这里假设连接是WebSocket
        try:
            if hasattr(connection, "send_json"):
                await connection.send_json(data)
            elif hasattr(connection, "send_text"):
                await connection.send_text(json.dumps(data))
            else:
                logger.error(f"不支持的连接类型: {type(connection)}")
        except Exception as e:
            logger.error(f"发送数据失败: {e}")
            raise e