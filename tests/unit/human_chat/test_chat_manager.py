import unittest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime

from rainbow_agent.human_chat.chat_manager import HumanChatManager
from rainbow_agent.human_chat.message_router import MessageRouter
from rainbow_agent.human_chat.presence_service import PresenceService
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage


class TestHumanChatManager(unittest.TestCase):
    """HumanChatManager单元测试"""

    def setUp(self):
        """测试前准备"""
        # 创建模拟对象
        self.mock_storage = MagicMock(spec=UnifiedDialogueStorage)
        self.mock_message_router = MagicMock(spec=MessageRouter)
        self.mock_presence_service = MagicMock(spec=PresenceService)
        
        # 创建HumanChatManager实例
        self.chat_manager = HumanChatManager(
            storage=self.mock_storage,
            message_router=self.mock_message_router,
            presence_service=self.mock_presence_service
        )
        
        # 设置测试数据
        self.creator_id = "user1"
        self.recipient_id = "user2"
        self.session_id = "session123"
        self.message_id = "message123"
        self.content = "Hello, world!"
        
        # 设置模拟返回值
        self.mock_session = {
            "id": self.session_id,
            "title": "Test Session",
            "metadata": {
                "dialogue_type": "human_human_private",
                "participants": [self.creator_id, self.recipient_id],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active"
            }
        }
        
        self.mock_message = {
            "id": self.message_id,
            "session_id": self.session_id,
            "content": self.content,
            "role": "human",
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "sender_id": self.creator_id,
                "message_type": "text",
                "human_chat": True,
                "read_at": {}
            }
        }
        
        # 配置模拟对象的行为
        self.mock_storage.create_session_async.return_value = self.mock_session
        self.mock_storage.get_session_async.return_value = self.mock_session
        self.mock_storage.create_turn_async.return_value = self.mock_message
        self.mock_storage.get_turn_async.return_value = self.mock_message
        self.mock_storage.list_sessions_async.return_value = [self.mock_session]
        self.mock_storage.list_turns_async.return_value = [self.mock_message]
        
        self.mock_presence_service.is_user_online.return_value = True

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.chat_manager)
        self.assertEqual(self.chat_manager.storage, self.mock_storage)
        self.assertEqual(self.chat_manager.message_router, self.mock_message_router)
        self.assertEqual(self.chat_manager.presence_service, self.mock_presence_service)

    def test_create_private_chat(self):
        """测试创建私聊会话"""
        # 运行异步测试
        session = asyncio.run(self.chat_manager.create_private_chat(
            self.creator_id, self.recipient_id, "Test Private Chat"
        ))
        
        # 验证结果
        self.assertEqual(session, self.mock_session)
        self.mock_storage.create_session_async.assert_called_once()
        self.mock_message_router.deliver_message_to_user.assert_called_once()

    def test_create_group_chat(self):
        """测试创建群聊会话"""
        # 运行异步测试
        session = asyncio.run(self.chat_manager.create_group_chat(
            self.creator_id, [self.recipient_id], "Test Group Chat"
        ))
        
        # 验证结果
        self.assertEqual(session, self.mock_session)
        self.mock_storage.create_session_async.assert_called_once()
        self.mock_message_router.deliver_message_to_user.assert_called_once()

    def test_send_message(self):
        """测试发送消息"""
        # 运行异步测试
        message = asyncio.run(self.chat_manager.send_message(
            self.session_id, self.creator_id, self.content
        ))
        
        # 验证结果
        self.assertEqual(message, self.mock_message)
        self.mock_storage.get_session_async.assert_called_once_with(self.session_id)
        self.mock_storage.create_turn_async.assert_called_once()
        self.mock_storage.update_session_async.assert_called_once()
        self.mock_message_router.route_message.assert_called_once()

    def test_mark_as_read(self):
        """测试标记消息已读"""
        # 运行异步测试
        result = asyncio.run(self.chat_manager.mark_as_read(
            self.message_id, self.recipient_id
        ))
        
        # 验证结果
        self.assertTrue(result)
        self.mock_storage.get_turn_async.assert_called_once_with(self.message_id)
        self.mock_storage.get_session_async.assert_called_once()
        self.mock_storage.update_turn_async.assert_called_once()
        self.mock_message_router.deliver_message_to_user.assert_called_once()

    def test_get_user_sessions(self):
        """测试获取用户会话列表"""
        # 运行异步测试
        sessions = asyncio.run(self.chat_manager.get_user_sessions(self.creator_id))
        
        # 验证结果
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["id"], self.session_id)
        self.mock_storage.list_sessions_async.assert_called_once()
        self.mock_storage.list_turns_async.assert_called()

    def test_get_session_details(self):
        """测试获取会话详情"""
        # 运行异步测试
        session_details = asyncio.run(self.chat_manager.get_session_details(
            self.session_id, self.creator_id
        ))
        
        # 验证结果
        self.assertEqual(session_details["id"], self.session_id)
        self.mock_storage.get_session_async.assert_called_once_with(self.session_id)
        self.mock_presence_service.is_user_online.assert_called()

    def test_get_session_messages(self):
        """测试获取会话消息"""
        # 运行异步测试
        messages = asyncio.run(self.chat_manager.get_session_messages(
            self.session_id, self.creator_id
        ))
        
        # 验证结果
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["id"], self.message_id)
        self.mock_storage.get_session_async.assert_called_once_with(self.session_id)
        self.mock_storage.list_turns_async.assert_called_once_with(self.session_id)

    def test_notify_typing(self):
        """测试通知用户正在输入"""
        # 运行异步测试
        result = asyncio.run(self.chat_manager.notify_typing(
            self.session_id, self.creator_id
        ))
        
        # 验证结果
        self.assertTrue(result)
        self.mock_storage.get_session_async.assert_called_once_with(self.session_id)
        self.mock_message_router.route_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
