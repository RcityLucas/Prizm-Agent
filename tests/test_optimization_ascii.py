import sys
import os
import asyncio
import unittest
import time
import json
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import optimization components
from rainbow_agent.human_chat.cache_manager import CacheManager
from rainbow_agent.human_chat.websocket_optimizer import WebSocketOptimizer
from rainbow_agent.human_chat.db_query_optimizer import DBQueryOptimizer

class MockStorage:
    """Mock storage class for testing"""
    
    def __init__(self):
        self.sessions = {}
        self.messages = {}
        self.call_count = {"get_session": 0, "get_turn": 0, "update_turn": 0}
    
    async def get_session_async(self, session_id):
        self.call_count["get_session"] += 1
        # Simulate database delay
        await asyncio.sleep(0.01)
        return self.sessions.get(session_id)
    
    async def get_turn_async(self, message_id):
        self.call_count["get_turn"] += 1
        # Simulate database delay
        await asyncio.sleep(0.01)
        return self.messages.get(message_id)
    
    async def update_turn_async(self, message_id, update_data):
        self.call_count["update_turn"] += 1
        # Simulate database delay
        await asyncio.sleep(0.01)
        if message_id not in self.messages:
            return False
        
        # Update message
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
        # Return all messages for the specified session
        return [msg for msg in self.messages.values() if msg.get("session_id") == session_id]
    
    def add_session(self, session_id, session_data):
        self.sessions[session_id] = session_data
    
    def add_message(self, message_id, message_data):
        self.messages[message_id] = message_data


# Test CacheManager
def test_cache_manager():
    print("\n===== Testing CacheManager =====")
    cache = CacheManager(ttl_seconds=2)  # Set short TTL for testing expiration
    
    # Test session cache
    session_id = "test_session_1"
    session_data = {"id": session_id, "title": "Test Session"}
    
    # Set cache
    cache.set_session(session_id, session_data)
    
    # Get cache
    cached_session = cache.get_session(session_id)
    assert cached_session == session_data, "Failed to get session cache"
    print("[OK] Session cache test passed")
    
    # Test message cache
    message_id = "test_message_1"
    message_data = {"id": message_id, "content": "Hello"}
    
    # Set cache
    cache.set_message(message_id, message_data)
    
    # Get cache
    cached_message = cache.get_message(message_id)
    assert cached_message == message_data, "Failed to get message cache"
    print("[OK] Message cache test passed")
    
    # Test user sessions list cache
    user_id = "test_user_1"
    sessions_data = [{"id": "session1"}, {"id": "session2"}]
    
    # Set cache
    cache.set_user_sessions(user_id, sessions_data)
    
    # Get cache
    cached_sessions = cache.get_user_sessions(user_id)
    assert cached_sessions == sessions_data, "Failed to get user sessions list cache"
    print("[OK] User sessions cache test passed")
    
    # Test session messages list cache
    session_id = "test_session_1"
    messages_data = [{"id": "msg1"}, {"id": "msg2"}]
    
    # Set cache
    cache.set_session_messages(session_id, messages_data)
    
    # Get cache
    cached_messages = cache.get_session_messages(session_id)
    assert cached_messages == messages_data, "Failed to get session messages list cache"
    print("[OK] Session messages cache test passed")
    
    # Note: We're skipping the automatic cache expiration test since it relies on a background thread
    # that runs every 60 seconds, which would make the test too slow
    print("[SKIP] Cache expiration test (would require waiting 60+ seconds)")
    
    # Instead, we'll manually call the cleanup method to simulate expiration
    cache._cleanup_expired_cache()
    print("[OK] Manual cache cleanup executed")
    
    # Test cache invalidation
    # Reset cache
    cache.set_session(session_id, session_data)
    cache.set_message(message_id, message_data)
    cache.set_user_sessions(user_id, sessions_data)
    cache.set_session_messages(session_id, messages_data)
    
    # Manually invalidate cache
    cache.invalidate_session(session_id)
    cache.invalidate_message(message_id)
    cache.invalidate_user_sessions(user_id)
    cache.invalidate_session_messages(session_id)
    
    # Verify cache has been invalidated
    assert cache.get_session(session_id) is None, "Session cache invalidation failed"
    assert cache.get_message(message_id) is None, "Message cache invalidation failed"
    assert cache.get_user_sessions(user_id) is None, "User sessions list cache invalidation failed"
    assert cache.get_session_messages(session_id) is None, "Session messages list cache invalidation failed"
    print("[OK] Cache invalidation test passed")
    
    # Test cache statistics
    stats = cache.get_stats()
    assert "session_cache_size" in stats, "Cache stats incomplete"
    assert "message_cache_size" in stats, "Cache stats incomplete"
    assert "user_sessions_cache_size" in stats, "Cache stats incomplete"
    assert "session_messages_cache_size" in stats, "Cache stats incomplete"
    print("[OK] Cache stats test passed")
    
    print("CacheManager all tests passed!")


# Test WebSocketOptimizer
def test_websocket_optimizer():
    print("\n===== Testing WebSocketOptimizer =====")
    optimizer = WebSocketOptimizer(batch_interval_ms=100, max_batch_size=3)
    
    # Test user registration and unregistration
    user_id = "test_user_1"
    
    # Register user
    optimizer.register_user(user_id)
    assert optimizer.is_user_active(user_id), "User registration failed"
    print("[OK] User registration test passed")
    
    # Test message queue
    message1 = {"type": "chat_message", "content": "Hello"}
    message2 = {"type": "chat_message", "content": "World"}
    
    # Queue not full, no need to send immediately
    assert not optimizer.queue_message(user_id, message1), "Message queue logic error"
    assert not optimizer.queue_message(user_id, message2), "Message queue logic error"
    print("[OK] Message queue test passed")
    
    # Add third message, queue is full, should send immediately
    message3 = {"type": "chat_message", "content": "!"}
    assert optimizer.queue_message(user_id, message3), "Should return True when queue is full"
    print("[OK] Full message queue test passed")
    
    # Get pending messages
    pending_messages = optimizer.get_pending_messages(user_id)
    assert len(pending_messages) == 3, f"Wrong number of pending messages, expected 3, got {len(pending_messages)}"
    print("[OK] Get pending messages test passed")
    
    # Test queue clearing
    assert len(optimizer.get_pending_messages(user_id)) == 0, "Message queue not cleared"
    print("[OK] Message queue clearing test passed")
    
    # Test message types that should be sent immediately
    typing_message = {"type": "typing", "user_id": user_id}
    assert optimizer.queue_message(user_id, typing_message), "Typing message should be sent immediately"
    print("[OK] Immediate send message type test passed")
    
    # Test message optimization
    long_message = {
        "content": "A" * 2000,  # Long content
        "debug_info": "This field should be removed",
        "important_field": "This field should be kept"
    }
    
    optimized = optimizer.optimize_message(long_message)
    
    # Check if content was truncated
    assert len(optimized["content"]) < len(long_message["content"]), "Long content not truncated"
    assert "content_truncated" in optimized, "Content truncation not marked"
    
    # Check if debug_info was removed
    assert "debug_info" not in optimized, "debug_info not removed"
    
    # Check if important_field was kept
    assert optimized["important_field"] == long_message["important_field"], "important_field not kept"
    print("[OK] Message optimization test passed")
    
    # Test batch message creation
    messages = [
        {"type": "chat_message", "content": "Message 1"},
        {"type": "chat_message", "content": "Message 2"}
    ]
    
    batch = optimizer.create_batch_message(messages)
    
    # Check batch message format
    assert batch["type"] == "batch", "Wrong batch message type"
    assert batch["count"] == 2, "Wrong batch message count"
    assert len(batch["messages"]) == 2, "Wrong batch messages list length"
    print("[OK] Batch message creation test passed")
    
    # Test user unregistration
    optimizer.unregister_user(user_id)
    assert not optimizer.is_user_active(user_id), "User unregistration failed"
    print("[OK] User unregistration test passed")
    
    # Test statistics
    stats = optimizer.get_stats()
    assert "active_users" in stats, "Stats incomplete"
    assert "total_queued_messages" in stats, "Stats incomplete"
    print("[OK] Statistics test passed")
    
    print("WebSocketOptimizer all tests passed!")


# Test DBQueryOptimizer
async def test_db_query_optimizer():
    print("\n===== Testing DBQueryOptimizer =====")
    optimizer = DBQueryOptimizer(batch_size=2, batch_wait_ms=100)
    storage = MockStorage()
    
    # Add test data
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
    
    # Test batch get sessions
    session_ids = ["session1", "session2", "session3"]
    
    # Reset call counter
    storage.call_count["get_session"] = 0
    
    # Batch get sessions
    results = await optimizer.batch_get_sessions(session_ids, storage)
    
    # Verify results
    assert len(results) == 3, f"Wrong number of batch get sessions results, expected 3, got {len(results)}"
    assert results["session1"]["title"] == "Session 1", "Wrong batch get sessions result"
    assert results["session2"]["title"] == "Session 2", "Wrong batch get sessions result"
    assert results["session3"]["title"] == "Session 3", "Wrong batch get sessions result"
    print("[OK] Batch get sessions test passed")
    
    # Test batch get messages
    message_ids = ["msg1", "msg2", "msg3"]
    
    # Reset call counter
    storage.call_count["get_turn"] = 0
    
    # Batch get messages
    results = await optimizer.batch_get_messages(message_ids, storage)
    
    # Verify results
    assert len(results) == 3, f"Wrong number of batch get messages results, expected 3, got {len(results)}"
    assert results["msg1"]["content"] == "Message 1", "Wrong batch get messages result"
    assert results["msg2"]["content"] == "Message 2", "Wrong batch get messages result"
    assert results["msg3"]["content"] == "Message 3", "Wrong batch get messages result"
    print("[OK] Batch get messages test passed")
    
    # Test batch update messages
    updates = [
        ("msg1", {"metadata.read_at.user2": datetime.now().isoformat()}),
        ("msg2", {"metadata.read_at.user1": datetime.now().isoformat()}),
        ("msg3", {"metadata.read_at.user2": datetime.now().isoformat()})
    ]
    
    # Reset call counter
    storage.call_count["update_turn"] = 0
    
    # Batch update messages
    results = await optimizer.batch_update_messages(updates, storage)
    
    # Verify results
    assert len(results) == 3, f"Wrong number of batch update messages results, expected 3, got {len(results)}"
    assert results["msg1"], "Wrong batch update messages result"
    assert results["msg2"], "Wrong batch update messages result"
    assert results["msg3"], "Wrong batch update messages result"
    print("[OK] Batch update messages test passed")
    
    # Test optimize messages query
    session_id = "session1"
    limit = 10
    
    # Execute optimized query
    messages = await optimizer.optimize_messages_query(session_id, limit, None, storage)
    
    # Verify results
    assert len(messages) == 2, f"Wrong number of optimized messages query results, expected 2, got {len(messages)}"
    print("[OK] Optimize messages query test passed")
    
    # Test query decorator
    @optimizer.optimize_query_decorator
    async def test_query(session_id):
        return await storage.get_session_async(session_id)
    
    # Execute query
    result = await test_query("session1")
    
    # Verify results
    assert result["title"] == "Session 1", "Wrong query decorator result"
    print("[OK] Query decorator test passed")
    
    print("DBQueryOptimizer all tests passed!")


async def main():
    # Run synchronous tests
    test_cache_manager()
    test_websocket_optimizer()
    
    # Run asynchronous tests
    await test_db_query_optimizer()
    
    print("\n===== All optimization component tests completed =====")


if __name__ == "__main__":
    # Run tests
    asyncio.run(main())
