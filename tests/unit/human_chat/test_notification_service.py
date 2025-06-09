import unittest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime

from rainbow_agent.human_chat.notification import NotificationService


class TestNotificationService(unittest.TestCase):
    """NotificationService单元测试"""

    def setUp(self):
        """测试前准备"""
        # 创建模拟的socketio实例
        self.mock_socketio = MagicMock()
        self.mock_socketio.emit = MagicMock()
        
        # 创建NotificationService实例
        self.notification_service = NotificationService(socketio=self.mock_socketio)
        
        # 设置测试数据
        self.user_id = "user1"
        self.session_id = "session123"
        self.message_id = "message123"
        self.notification = {
            "type": "chat_message",
            "message_id": self.message_id,
            "session_id": self.session_id,
            "sender_id": "user2",
            "content": "Hello, world!",
            "timestamp": datetime.now().isoformat()
        }
        
        # 模拟用户连接
        self.notification_service.user_connections[self.user_id] = "connection123"

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.notification_service)
        self.assertEqual(self.notification_service.socketio, self.mock_socketio)
        self.assertEqual(self.notification_service.user_connections, {self.user_id: "connection123"})
        self.assertEqual(self.notification_service.offline_notifications, {})

    def test_register_connection(self):
        """测试注册用户连接"""
        # 测试数据
        user_id = "user2"
        connection_id = "connection456"
        
        # 执行测试
        self.notification_service.register_connection(user_id, connection_id)
        
        # 验证结果
        self.assertEqual(self.notification_service.user_connections.get(user_id), connection_id)

    def test_unregister_connection(self):
        """测试注销用户连接"""
        # 执行测试
        self.notification_service.unregister_connection(self.user_id)
        
        # 验证结果
        self.assertNotIn(self.user_id, self.notification_service.user_connections)

    def test_is_user_connected(self):
        """测试检查用户是否连接"""
        # 执行测试 - 已连接用户
        is_connected = self.notification_service.is_user_connected(self.user_id)
        
        # 验证结果
        self.assertTrue(is_connected)
        
        # 执行测试 - 未连接用户
        is_connected = self.notification_service.is_user_connected("non_existent_user")
        
        # 验证结果
        self.assertFalse(is_connected)

    def test_send_notification(self):
        """测试发送通知"""
        # 执行测试
        self.notification_service.send_notification(self.user_id, self.notification)
        
        # 验证结果
        self.mock_socketio.emit.assert_called_once_with(
            "notification", 
            self.notification, 
            room=self.notification_service.user_connections[self.user_id]
        )

    def test_store_offline_notification(self):
        """测试存储离线通知"""
        # 测试数据
        offline_user_id = "offline_user"
        
        # 执行测试
        self.notification_service.store_offline_notification(offline_user_id, self.notification)
        
        # 验证结果
        self.assertIn(offline_user_id, self.notification_service.offline_notifications)
        self.assertEqual(len(self.notification_service.offline_notifications[offline_user_id]), 1)
        self.assertEqual(self.notification_service.offline_notifications[offline_user_id][0], self.notification)

    def test_deliver_offline_notifications(self):
        """测试发送离线通知"""
        # 测试数据
        offline_user_id = "offline_user"
        self.notification_service.offline_notifications[offline_user_id] = [self.notification]
        self.notification_service.user_connections[offline_user_id] = "connection_offline"
        
        # 执行测试
        self.notification_service.deliver_offline_notifications(offline_user_id)
        
        # 验证结果
        self.mock_socketio.emit.assert_called_once()
        self.assertNotIn(offline_user_id, self.notification_service.offline_notifications)

    def test_notify_all_in_session(self):
        """测试通知会话中的所有用户"""
        # 测试数据
        participants = [self.user_id, "user2", "user3"]
        self.notification_service.user_connections["user2"] = "connection2"
        
        # 执行测试
        self.notification_service.notify_all_in_session(
            self.session_id, 
            participants, 
            "test_event", 
            {"data": "test_data"}
        )
        
        # 验证结果
        # 应该调用两次emit（两个在线用户）
        self.assertEqual(self.mock_socketio.emit.call_count, 2)
        # 一个离线用户应该有离线通知
        self.assertIn("user3", self.notification_service.offline_notifications)


if __name__ == "__main__":
    unittest.main()
