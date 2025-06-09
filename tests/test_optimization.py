import sys
import os
import asyncio
import unittest
import time
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rainbow_agent.human_chat.cache_manager import CacheManager
from rainbow_agent.human_chat.websocket_optimizer import WebSocketOptimizer
from rainbow_agent.human_chat.db_query_optimizer import DBQueryOptimizer

class MockStorage:
    """模拟存储类，用于测试"""
    
    def __init__(self):
        self.sessions = {}
        self.messages = {}
        self.call_count = {"get_session": 0, "get_turn": 0, "update_turn": 0}
    
    async def get_session_async(self, session_id):
        self.call_count["get_session"] += 1
        # 模拟数据库延迟
        await asyncio.sleep(0.01)
        return self.sessions.get(session_id)
    
    async def get_turn_async(self, message_id):
        self.call_count["get_turn"] += 1
        # 模拟数据库延迟
        await asyncio.sleep(0.01)
        return self.messages.get(message_id)
    
    async def update_turn_async(self, message_id, update_data):
        self.call_count["update_turn"] += 1
        # 模拟数据库延迟
        await asyncio.sleep(0.01)
        if message_id not in self.messages:
            return False
        
        # 更新消息
        for key, value in update_data.items():
            parts = key.split(".")
            target = self.messages[message_id]
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value
        
        return True
    
    async def list_turns_async(self, session_id):
        # 返回指定会话的所有消息
        return [msg for msg in self.messages.values() if msg.get("session_id") == session_id]
    
    def add_session(self, session_id, session_data):
        self.sessions[session_id] = session_data
    
    def add_message(self, message_id, message_data):
        self.messages[message_id] = message_data


class TestCacheManager(unittest.TestCase):
    """测试缓存管理器"""
    
    def setUp(self):
        self.cache = CacheManager(ttl_seconds=1)  # 设置短TTL便于测试过期
    
    def test_session_cache(self):
        # 测试会话缓存
        session_id = "test_session_1"
        session_data = {"id": session_id, "title": "Test Session"}
        
        # 设置缓存
        self.cache.set_session(session_id, session_data)
        
        # 获取缓存
        cached_session = self.cache.get_session(session_id)
        self.assertEqual(cached_session, session_data)
        
        # 测试过期
        time.sleep(1.1)  # 等待过期
        expired_session = self.cache.get_session(session_id)
        self.assertIsNone(expired_session)
    
    def test_message_cache(self):
        # 测试消息缓存
        message_id = "test_message_1"
        message_data = {"id": message_id, "content": "Hello"}
        
        # 设置缓存
        self.cache.set_message(message_id, message_data)
        
        # 获取缓存
        cached_message = self.cache.get_message(message_id)
        self.assertEqual(cached_message, message_data)
        
        # 测试过期
        time.sleep(1.1)  # 等待过期
        expired_message = self.cache.get_message(message_id)
        self.assertIsNone(expired_message)
    
    def test_user_sessions_cache(self):
        # 测试用户会话列表缓存
        user_id = "test_user_1"
        sessions_data = [{"id": "session1"}, {"id": "session2"}]
        
        # 设置缓存
        self.cache.set_user_sessions(user_id, sessions_data)
        
        # 获取缓存
        cached_sessions = self.cache.get_user_sessions(user_id)
        self.assertEqual(cached_sessions, sessions_data)
        
        # 测试过期
        time.sleep(1.1)  # 等待过期
        expired_sessions = self.cache.get_user_sessions(user_id)
        self.assertIsNone(expired_sessions)
    
    def test_session_messages_cache(self):
        # 测试会话消息列表缓存
        session_id = "test_session_1"
        messages_data = [{"id": "msg1"}, {"id": "msg2"}]
        
        # 设置缓存
        self.cache.set_session_messages(session_id, messages_data)
        
        # 获取缓存
        cached_messages = self.cache.get_session_messages(session_id)
        self.assertEqual(cached_messages, messages_data)
        
        # 测试过期
        time.sleep(1.1)  # 等待过期
        expired_messages = self.cache.get_session_messages(session_id)
        self.assertIsNone(expired_messages)
    
    def test_invalidate_cache(self):
        # 测试缓存失效
        session_id = "test_session_1"
        message_id = "test_message_1"
        user_id = "test_user_1"
        
        # 设置各种缓存
        self.cache.set_session(session_id, {"id": session_id})
        self.cache.set_message(message_id, {"id": message_id})
        self.cache.set_user_sessions(user_id, [{"id": session_id}])
        self.cache.set_session_messages(session_id, [{"id": message_id}])
        
        # 验证缓存存在
        self.assertIsNotNone(self.cache.get_session(session_id))
        self.assertIsNotNone(self.cache.get_message(message_id))
        self.assertIsNotNone(self.cache.get_user_sessions(user_id))
        self.assertIsNotNone(self.cache.get_session_messages(session_id))
        
        # 失效会话缓存
        self.cache.invalidate_session(session_id)
        self.assertIsNone(self.cache.get_session(session_id))
        
        # 失效消息缓存
        self.cache.invalidate_message(message_id)
        self.assertIsNone(self.cache.get_message(message_id))
        
        # 失效用户会话列表缓存
        self.cache.invalidate_user_sessions(user_id)
        self.assertIsNone(self.cache.get_user_sessions(user_id))
        
        # 失效会话消息列表缓存
        self.cache.invalidate_session_messages(session_id)
        self.assertIsNone(self.cache.get_session_messages(session_id))


class TestWebSocketOptimizer(unittest.TestCase):
    """测试WebSocket优化器"""
    
    def setUp(self):
        self.optimizer = WebSocketOptimizer(batch_interval_ms=100, max_batch_size=3)
    
    def test_user_registration(self):
        # 测试用户注册和注销
        user_id = "test_user_1"
        
        # 注册用户
        self.optimizer.register_user(user_id)
        self.assertTrue(self.optimizer.is_user_active(user_id))
        
        # 注销用户
        self.optimizer.unregister_user(user_id)
        self.assertFalse(self.optimizer.is_user_active(user_id))
    
    def test_message_queuing(self):
        # 测试消息队列
        user_id = "test_user_1"
        self.optimizer.register_user(user_id)
        
        # 添加消息到队列
        message1 = {"type": "chat_message", "content": "Hello"}
        message2 = {"type": "chat_message", "content": "World"}
        
        # 队列未满，不需要立即发送
        self.assertFalse(self.optimizer.queue_message(user_id, message1))
        self.assertFalse(self.optimizer.queue_message(user_id, message2))
        
        # 添加第三条消息，队列已满，需要立即发送
        message3 = {"type": "chat_message", "content": "!"}
        self.assertTrue(self.optimizer.queue_message(user_id, message3))
        
        # 获取待发送消息
        pending_messages = self.optimizer.get_pending_messages(user_id)
        self.assertEqual(len(pending_messages), 3)
        
        # 队列应该被清空
        self.assertEqual(len(self.optimizer.get_pending_messages(user_id)), 0)
    
    def test_immediate_messages(self):
        # 测试需要立即发送的消息类型
        user_id = "test_user_1"
        self.optimizer.register_user(user_id)
        
        # 添加typing消息，应该立即发送
        typing_message = {"type": "typing", "user_id": user_id}
        self.assertTrue(self.optimizer.queue_message(user_id, typing_message))
    
    def test_message_optimization(self):
        # 测试消息优化
        message = {
            "content": "A" * 2000,  # 长内容
            "debug_info": "这个字段应该被移除",
            "important_field": "这个字段应该保留"
        }
        
        optimized = self.optimizer.optimize_message(message)
        
        # 检查内容是否被截断
        self.assertTrue(len(optimized["content"]) < len(message["content"]))
        self.assertTrue("content_truncated" in optimized)
        
        # 检查debug_info是否被移除
        self.assertFalse("debug_info" in optimized)
        
        # 检查important_field是否被保留
        self.assertEqual(optimized["important_field"], message["important_field"])
    
    def test_batch_creation(self):
        # 测试批处理消息创建
        messages = [
            {"type": "chat_message", "content": "Message 1"},
            {"type": "chat_message", "content": "Message 2"}
        ]
        
        batch = self.optimizer.create_batch_message(messages)
        
        # 检查批处理消息格式
        self.assertEqual(batch["type"], "batch")
        self.assertEqual(batch["count"], 2)
        self.assertEqual(len(batch["messages"]), 2)


class TestDBQueryOptimizer(unittest.TestCase):
    """测试数据库查询优化器"""
    
    def setUp(self):
        self.optimizer = DBQueryOptimizer(batch_size=2, batch_wait_ms=100)
        self.storage = MockStorage()
        
        # 添加测试数据
        self.storage.add_session("session1", {"id": "session1", "title": "Session 1"})
        self.storage.add_session("session2", {"id": "session2", "title": "Session 2"})
        self.storage.add_session("session3", {"id": "session3", "title": "Session 3"})
        
        self.storage.add_message("msg1", {
            "id": "msg1", 
            "session_id": "session1", 
            "content": "Message 1",
            "metadata": {"human_chat": True, "sender_id": "user1"}
        })
        self.storage.add_message("msg2", {
            "id": "msg2", 
            "session_id": "session1", 
            "content": "Message 2",
            "metadata": {"human_chat": True, "sender_id": "user2"}
        })
        self.storage.add_message("msg3", {
            "id": "msg3", 
            "session_id": "session2", 
            "content": "Message 3",
            "metadata": {"human_chat": True, "sender_id": "user1"}
        })
    
    async def test_batch_get_sessions(self):
        # 测试批量获取会话
        session_ids = ["session1", "session2", "session3"]
        
        # 重置调用计数
        self.storage.call_count["get_session"] = 0
        
        # 批量获取会话
        results = await self.optimizer.batch_get_sessions(session_ids, self.storage)
        
        # 验证结果
        self.assertEqual(len(results), 3)
        self.assertEqual(results["session1"]["title"], "Session 1")
        self.assertEqual(results["session2"]["title"], "Session 2")
        self.assertEqual(results["session3"]["title"], "Session 3")
        
        # 验证调用次数（应该是3次，因为批量大小为2）
        self.assertEqual(self.storage.call_count["get_session"], 3)
    
    async def test_batch_get_messages(self):
        # 测试批量获取消息
        message_ids = ["msg1", "msg2", "msg3"]
        
        # 重置调用计数
        self.storage.call_count["get_turn"] = 0
        
        # 批量获取消息
        results = await self.optimizer.batch_get_messages(message_ids, self.storage)
        
        # 验证结果
        self.assertEqual(len(results), 3)
        self.assertEqual(results["msg1"]["content"], "Message 1")
        self.assertEqual(results["msg2"]["content"], "Message 2")
        self.assertEqual(results["msg3"]["content"], "Message 3")
        
        # 验证调用次数（应该是3次，因为批量大小为2）
        self.assertEqual(self.storage.call_count["get_turn"], 3)
    
    async def test_batch_update_messages(self):
        # 测试批量更新消息
        updates = [
            ("msg1", {"metadata.read_at.user2": datetime.now().isoformat()}),
            ("msg2", {"metadata.read_at.user1": datetime.now().isoformat()}),
            ("msg3", {"metadata.read_at.user2": datetime.now().isoformat()})
        ]
        
        # 重置调用计数
        self.storage.call_count["update_turn"] = 0
        
        # 批量更新消息
        results = await self.optimizer.batch_update_messages(updates, self.storage)
        
        # 验证结果
        self.assertEqual(len(results), 3)
        self.assertTrue(results["msg1"])
        self.assertTrue(results["msg2"])
        self.assertTrue(results["msg3"])
        
        # 验证调用次数（应该是3次，因为批量大小为2）
        self.assertEqual(self.storage.call_count["update_turn"], 3)
    
    async def test_optimize_messages_query(self):
        # 测试优化消息查询
        session_id = "session1"
        limit = 10
        
        # 执行优化查询
        messages = await self.optimizer.optimize_messages_query(session_id, limit, None, self.storage)
        
        # 验证结果
        self.assertEqual(len(messages), 2)  # session1有2条消息
    
    async def test_query_decorator(self):
        # 测试查询装饰器
        
        # 创建一个测试查询函数
        @self.optimizer.optimize_query_decorator
        async def test_query(session_id):
            return await self.storage.get_session_async(session_id)
        
        # 执行查询
        result = await test_query("session1")
        
        # 验证结果
        self.assertEqual(result["title"], "Session 1")


async def run_tests():
    # 运行所有测试
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestCacheManager))
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestWebSocketOptimizer))
    
    # 运行同步测试
    test_runner = unittest.TextTestRunner()
    test_result = test_runner.run(test_suite)
    
    # 运行异步测试
    db_optimizer_test = TestDBQueryOptimizer()
    db_optimizer_test.setUp()
    await db_optimizer_test.test_batch_get_sessions()
    await db_optimizer_test.test_batch_get_messages()
    await db_optimizer_test.test_batch_update_messages()
    await db_optimizer_test.test_optimize_messages_query()
    await db_optimizer_test.test_query_decorator()
    
    print("\n所有测试完成！")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(run_tests())
