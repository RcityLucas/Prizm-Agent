import sys
import os
import asyncio
import unittest
import time
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入优化组件
from rainbow_agent.human_chat.cache_manager import CacheManager
from rainbow_agent.human_chat.websocket_optimizer import WebSocketOptimizer
from rainbow_agent.human_chat.db_query_optimizer import DBQueryOptimizer

class MockStorage:
    """Mock storage class for testing"""
    
    def __init__(self, ttl_seconds: int = 2):
        self.sessions = {}
        self.messages = {}
        self.call_count = {"get_session": 0, "get_turn": 0, "update_turn": 0}
    
    async def get_session_async(self, session_id):
        self.call_count["get_session"] += 1
        # Simulate database delay
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


# 测试CacheManager
def test_cache_manager():
    print("\n===== Testing CacheManager =====")
    cache = CacheManager(ttl_seconds=1)  # 设置短TTL便于测试过期
    
    # 测试会话缓存
    session_id = "test_session_1"
    session_data = {"id": session_id, "title": "Test Session"}
    
    # 设置缓存
    cache.set_session(session_id, session_data)
    
    # 获取缓存
    cached_session = cache.get_session(session_id)
    assert cached_session == session_data, "会话缓存获取失败"
    print("[OK] Session cache test passed")
    
    # 测试消息缓存
    message_id = "test_message_1"
    message_data = {"id": message_id, "content": "Hello"}
    
    # 设置缓存
    cache.set_message(message_id, message_data)
    
    # 获取缓存
    cached_message = cache.get_message(message_id)
    assert cached_message == message_data, "消息缓存获取失败"
    print("[OK] Message cache test passed")
    
    # 测试用户会话列表缓存
    user_id = "test_user_1"
    sessions_data = [{"id": "session1"}, {"id": "session2"}]
    
    # 设置缓存
    cache.set_user_sessions(user_id, sessions_data)
    
    # 获取缓存
    cached_sessions = cache.get_user_sessions(user_id)
    assert cached_sessions == sessions_data, "用户会话列表缓存获取失败"
    print("[OK] User sessions cache test passed")
    
    # 测试会话消息列表缓存
    session_id = "test_session_1"
    messages_data = [{"id": "msg1"}, {"id": "msg2"}]
    
    # 设置缓存
    cache.set_session_messages(session_id, messages_data)
    
    # 获取缓存
    cached_messages = cache.get_session_messages(session_id)
    assert cached_messages == messages_data, "会话消息列表缓存获取失败"
    print("[OK] Session messages cache test passed")
    
    # 测试缓存过期
    print("Waiting for cache to expire...")
    time.sleep(2)  # Wait longer for expiration
    
    # 验证缓存已过期
    assert cache.get_session(session_id) is None, "Session cache did not expire"
    assert cache.get_message(message_id) is None, "Message cache did not expire"
    assert cache.get_user_sessions(user_id) is None, "User sessions cache did not expire"
    assert cache.get_session_messages(session_id) is None, "Session messages cache did not expire"
    print("[OK] Cache expiration test passed")
    
    # 测试缓存失效
    # 重新设置缓存
    cache.set_session(session_id, session_data)
    cache.set_message(message_id, message_data)
    cache.set_user_sessions(user_id, sessions_data)
    cache.set_session_messages(session_id, messages_data)
    
    # 手动使缓存失效
    cache.invalidate_session(session_id)
    cache.invalidate_message(message_id)
    cache.invalidate_user_sessions(user_id)
    cache.invalidate_session_messages(session_id)
    
    # 验证缓存已失效
    assert cache.get_session(session_id) is None, "Session cache invalidation failed"
    assert cache.get_message(message_id) is None, "Message cache invalidation failed"
    assert cache.get_user_sessions(user_id) is None, "User sessions cache invalidation failed"
    assert cache.get_session_messages(session_id) is None, "Session messages cache invalidation failed"
    print("[OK] Cache invalidation test passed")
    
    # 测试缓存统计
    stats = cache.get_stats()
    assert "session_cache_size" in stats, "Cache stats incomplete"
    assert "message_cache_size" in stats, "Cache stats incomplete"
    assert "user_sessions_cache_size" in stats, "Cache stats incomplete"
    assert "session_messages_cache_size" in stats, "Cache stats incomplete"
    print("[OK] Cache stats test passed")
    
    print("CacheManager all tests passed!")


# 测试WebSocketOptimizer
def test_websocket_optimizer():
    print("\n===== Testing WebSocketOptimizer =====")
    optimizer = WebSocketOptimizer(batch_interval_ms=100, max_batch_size=3)
    
    # 测试用户注册和注销
    user_id = "test_user_1"
    
    # 注册用户
    optimizer.register_user(user_id)
    assert optimizer.is_user_active(user_id), "用户注册失败"
    print("[OK] 用户注册测试通过")
    
    # 测试消息队列
    message1 = {"type": "chat_message", "content": "Hello"}
    message2 = {"type": "chat_message", "content": "World"}
    
    # 队列未满，不需要立即发送
    assert not optimizer.queue_message(user_id, message1), "消息队列逻辑错误"
    assert not optimizer.queue_message(user_id, message2), "消息队列逻辑错误"
    print("[OK] 消息队列测试通过")
    
    # 添加第三条消息，队列已满，需要立即发送
    message3 = {"type": "chat_message", "content": "!"}
    assert optimizer.queue_message(user_id, message3), "消息队列满时应返回True"
    print("[OK] 消息队列满时测试通过")
    
    # 获取待发送消息
    pending_messages = optimizer.get_pending_messages(user_id)
    assert len(pending_messages) == 3, f"待发送消息数量错误，期望3，实际{len(pending_messages)}"
    print("[OK] 获取待发送消息测试通过")
    
    # 测试队列清空
    assert len(optimizer.get_pending_messages(user_id)) == 0, "消息队列未被清空"
    print("[OK] 消息队列清空测试通过")
    
    # 测试需要立即发送的消息类型
    typing_message = {"type": "typing", "user_id": user_id}
    assert optimizer.queue_message(user_id, typing_message), "typing消息应立即发送"
    print("[OK] 立即发送消息类型测试通过")
    
    # 测试消息优化
    long_message = {
        "content": "A" * 2000,  # 长内容
        "debug_info": "这个字段应该被移除",
        "important_field": "这个字段应该保留"
    }
    
    optimized = optimizer.optimize_message(long_message)
    
    # 检查内容是否被截断
    assert len(optimized["content"]) < len(long_message["content"]), "长内容未被截断"
    assert "content_truncated" in optimized, "未标记内容被截断"
    
    # 检查debug_info是否被移除
    assert "debug_info" not in optimized, "debug_info未被移除"
    
    # 检查important_field是否被保留
    assert optimized["important_field"] == long_message["important_field"], "important_field未被保留"
    print("[OK] 消息优化测试通过")
    
    # 测试批处理消息创建
    messages = [
        {"type": "chat_message", "content": "Message 1"},
        {"type": "chat_message", "content": "Message 2"}
    ]
    
    batch = optimizer.create_batch_message(messages)
    
    # 检查批处理消息格式
    assert batch["type"] == "batch", "批处理消息类型错误"
    assert batch["count"] == 2, "批处理消息数量错误"
    assert len(batch["messages"]) == 2, "批处理消息列表长度错误"
    print("[OK] 批处理消息创建测试通过")
    
    # 测试注销用户
    optimizer.unregister_user(user_id)
    assert not optimizer.is_user_active(user_id), "用户注销失败"
    print("[OK] 用户注销测试通过")
    
    # 测试统计信息
    stats = optimizer.get_stats()
    assert "active_users" in stats, "统计信息不完整"
    assert "total_queued_messages" in stats, "统计信息不完整"
    print("[OK] 统计信息测试通过")
    
    print("WebSocketOptimizer 所有测试通过！")


# 测试DBQueryOptimizer
async def test_db_query_optimizer():
    print("\n===== Testing DBQueryOptimizer =====")
    optimizer = DBQueryOptimizer(batch_size=2, batch_wait_ms=100)
    storage = MockStorage()
    
    # 添加测试数据
    storage.add_session("session1", {"id": "session1", "title": "Session 1"})
    storage.add_session("session2", {"id": "session2", "title": "Session 2"})
    storage.add_session("session3", {"id": "session3", "title": "Session 3"})
    
    storage.add_message("msg1", {
        "id": "msg1", 
        "session_id": "session1", 
        "content": "Message 1",
        "metadata": {"human_chat": True, "sender_id": "user1"}
    })
    storage.add_message("msg2", {
        "id": "msg2", 
        "session_id": "session1", 
        "content": "Message 2",
        "metadata": {"human_chat": True, "sender_id": "user2"}
    })
    storage.add_message("msg3", {
        "id": "msg3", 
        "session_id": "session2", 
        "content": "Message 3",
        "metadata": {"human_chat": True, "sender_id": "user1"}
    })
    
    # 测试批量获取会话
    session_ids = ["session1", "session2", "session3"]
    
    # 重置调用计数
    storage.call_count["get_session"] = 0
    
    # 批量获取会话
    results = await optimizer.batch_get_sessions(session_ids, storage)
    
    # 验证结果
    assert len(results) == 3, f"批量获取会话结果数量错误，期望3，实际{len(results)}"
    assert results["session1"]["title"] == "Session 1", "批量获取会话结果错误"
    assert results["session2"]["title"] == "Session 2", "批量获取会话结果错误"
    assert results["session3"]["title"] == "Session 3", "批量获取会话结果错误"
    print("[OK] 批量获取会话测试通过")
    
    # 测试批量获取消息
    message_ids = ["msg1", "msg2", "msg3"]
    
    # 重置调用计数
    storage.call_count["get_turn"] = 0
    
    # 批量获取消息
    results = await optimizer.batch_get_messages(message_ids, storage)
    
    # 验证结果
    assert len(results) == 3, f"批量获取消息结果数量错误，期望3，实际{len(results)}"
    assert results["msg1"]["content"] == "Message 1", "批量获取消息结果错误"
    assert results["msg2"]["content"] == "Message 2", "批量获取消息结果错误"
    assert results["msg3"]["content"] == "Message 3", "批量获取消息结果错误"
    print("[OK] 批量获取消息测试通过")
    
    # 测试批量更新消息
    updates = [
        ("msg1", {"metadata.read_at.user2": datetime.now().isoformat()}),
        ("msg2", {"metadata.read_at.user1": datetime.now().isoformat()}),
        ("msg3", {"metadata.read_at.user2": datetime.now().isoformat()})
    ]
    
    # 重置调用计数
    storage.call_count["update_turn"] = 0
    
    # 批量更新消息
    results = await optimizer.batch_update_messages(updates, storage)
    
    # 验证结果
    assert len(results) == 3, f"批量更新消息结果数量错误，期望3，实际{len(results)}"
    assert results["msg1"], "批量更新消息结果错误"
    assert results["msg2"], "批量更新消息结果错误"
    assert results["msg3"], "批量更新消息结果错误"
    print("[OK] 批量更新消息测试通过")
    
    # 测试优化消息查询
    session_id = "session1"
    limit = 10
    
    # 执行优化查询
    messages = await optimizer.optimize_messages_query(session_id, limit, None, storage)
    
    # 验证结果
    assert len(messages) == 2, f"优化消息查询结果数量错误，期望2，实际{len(messages)}"
    print("[OK] 优化消息查询测试通过")
    
    # 测试查询装饰器
    @optimizer.optimize_query_decorator
    async def test_query(session_id):
        return await storage.get_session_async(session_id)
    
    # 执行查询
    result = await test_query("session1")
    
    # 验证结果
    assert result["title"] == "Session 1", "查询装饰器结果错误"
    print("[OK] 查询装饰器测试通过")
    
    print("DBQueryOptimizer 所有测试通过！")


async def main():
    # 运行同步测试
    test_cache_manager()
    test_websocket_optimizer()
    
    # 运行异步测试
    await test_db_query_optimizer()
    
    print("\n===== All optimization component tests completed =====")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
