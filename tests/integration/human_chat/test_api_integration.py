import unittest
import json
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime

from flask import Flask
from flask_socketio import SocketIO

from rainbow_agent.human_chat.api.routes import register_routes, register_socketio_events
from rainbow_agent.human_chat.chat_manager import HumanChatManager
from rainbow_agent.human_chat.notification import NotificationService


class TestHumanChatAPIIntegration(unittest.TestCase):
    """人类对话API集成测试"""

    def setUp(self):
        """测试前准备"""
        # 创建Flask应用
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # 创建SocketIO实例
        self.socketio = SocketIO(self.app, async_mode='threading')
        
        # 创建模拟的HumanChatManager
        self.mock_chat_manager = MagicMock(spec=HumanChatManager)
        
        # 创建模拟的NotificationService
        self.mock_notification_service = MagicMock(spec=NotificationService)
        
        # 设置模拟返回值
        self.session_id = "session123"
        self.user_id = "user1"
        self.recipient_id = "user2"
        self.message_id = "message123"
        
        self.mock_session = {
            "id": self.session_id,
            "title": "Test Session",
            "is_group": False,
            "participants": [self.user_id, self.recipient_id],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.mock_message = {
            "id": self.message_id,
            "session_id": self.session_id,
            "sender_id": self.user_id,
            "content": "Hello, world!",
            "content_type": "text",
            "created_at": datetime.now().isoformat()
        }
        
        # 配置模拟对象的行为
        self.mock_chat_manager.create_private_chat.return_value = asyncio.Future()
        self.mock_chat_manager.create_private_chat.return_value.set_result(self.mock_session)
        
        self.mock_chat_manager.create_group_chat.return_value = asyncio.Future()
        self.mock_chat_manager.create_group_chat.return_value.set_result(self.mock_session)
        
        self.mock_chat_manager.send_message.return_value = asyncio.Future()
        self.mock_chat_manager.send_message.return_value.set_result(self.mock_message)
        
        self.mock_chat_manager.mark_as_read.return_value = asyncio.Future()
        self.mock_chat_manager.mark_as_read.return_value.set_result(True)
        
        self.mock_chat_manager.get_user_sessions.return_value = asyncio.Future()
        self.mock_chat_manager.get_user_sessions.return_value.set_result([self.mock_session])
        
        self.mock_chat_manager.get_session_details.return_value = asyncio.Future()
        self.mock_chat_manager.get_session_details.return_value.set_result(self.mock_session)
        
        self.mock_chat_manager.get_session_messages.return_value = asyncio.Future()
        self.mock_chat_manager.get_session_messages.return_value.set_result([self.mock_message])
        
        self.mock_chat_manager.notify_typing.return_value = asyncio.Future()
        self.mock_chat_manager.notify_typing.return_value.set_result(True)
        
        # 注册路由和事件处理器
        with patch('rainbow_agent.human_chat.api.routes.get_chat_manager', return_value=self.mock_chat_manager), \
             patch('rainbow_agent.human_chat.api.routes.get_notification_service', return_value=self.mock_notification_service), \
             patch('rainbow_agent.human_chat.api.routes.get_current_user_id', return_value=self.user_id):
            register_routes(self.app)
            register_socketio_events(self.socketio)

    def test_create_private_chat(self):
        """测试创建私聊会话API"""
        # 准备请求数据
        data = {
            "recipient_id": self.recipient_id,
            "title": "Test Private Chat"
        }
        
        # 发送请求
        with patch('rainbow_agent.human_chat.api.routes.get_current_user_id', return_value=self.user_id):
            response = self.client.post(
                '/api/human-chat/sessions/private',
                data=json.dumps(data),
                content_type='application/json'
            )
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["session"]["id"], self.session_id)

    def test_create_group_chat(self):
        """测试创建群聊会话API"""
        # 准备请求数据
        data = {
            "member_ids": [self.recipient_id],
            "title": "Test Group Chat"
        }
        
        # 发送请求
        with patch('rainbow_agent.human_chat.api.routes.get_current_user_id', return_value=self.user_id):
            response = self.client.post(
                '/api/human-chat/sessions/group',
                data=json.dumps(data),
                content_type='application/json'
            )
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["session"]["id"], self.session_id)

    def test_get_user_sessions(self):
        """测试获取用户会话列表API"""
        # 发送请求
        with patch('rainbow_agent.human_chat.api.routes.get_current_user_id', return_value=self.user_id):
            response = self.client.get('/api/human-chat/sessions')
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(len(response_data["sessions"]), 1)
        self.assertEqual(response_data["sessions"][0]["id"], self.session_id)

    def test_get_session_details(self):
        """测试获取会话详情API"""
        # 发送请求
        with patch('rainbow_agent.human_chat.api.routes.get_current_user_id', return_value=self.user_id):
            response = self.client.get(f'/api/human-chat/sessions/{self.session_id}')
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["session"]["id"], self.session_id)

    def test_send_message(self):
        """测试发送消息API"""
        # 准备请求数据
        data = {
            "content": "Hello, world!",
            "content_type": "text"
        }
        
        # 发送请求
        with patch('rainbow_agent.human_chat.api.routes.get_current_user_id', return_value=self.user_id):
            response = self.client.post(
                f'/api/human-chat/sessions/{self.session_id}/messages',
                data=json.dumps(data),
                content_type='application/json'
            )
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["message"]["id"], self.message_id)

    def test_get_session_messages(self):
        """测试获取会话消息API"""
        # 发送请求
        with patch('rainbow_agent.human_chat.api.routes.get_current_user_id', return_value=self.user_id):
            response = self.client.get(f'/api/human-chat/sessions/{self.session_id}/messages')
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(len(response_data["messages"]), 1)
        self.assertEqual(response_data["messages"][0]["id"], self.message_id)

    def test_mark_message_as_read(self):
        """测试标记消息已读API"""
        # 发送请求
        with patch('rainbow_agent.human_chat.api.routes.get_current_user_id', return_value=self.user_id):
            response = self.client.post(f'/api/human-chat/messages/{self.message_id}/read')
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertTrue(response_data["success"])

    def test_notify_typing(self):
        """测试通知正在输入API"""
        # 发送请求
        with patch('rainbow_agent.human_chat.api.routes.get_current_user_id', return_value=self.user_id):
            response = self.client.post(f'/api/human-chat/sessions/{self.session_id}/typing')
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertTrue(response_data["success"])


if __name__ == "__main__":
    unittest.main()
