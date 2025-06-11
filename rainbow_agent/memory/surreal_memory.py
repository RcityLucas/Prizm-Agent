"""
SurrealDB记忆系统

实现基于SurrealDB的记忆系统，继承自Memory基类
"""
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import asyncio

from .memory import Memory, SimpleMemory
from ..storage.surreal_factory import SurrealStorageFactory
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SurrealMemory(Memory):
    """
    SurrealDB记忆系统
    
    使用SurrealDB存储和检索对话记忆
    """
    
    def __init__(self, db_url: str = "http://localhost:8000", namespace: str = "rainbow", database: str = "agent"):
        """
        初始化SurrealDB记忆系统
        
        Args:
            db_url: SurrealDB服务器URL
            namespace: SurrealDB命名空间
            database: SurrealDB数据库名称
        """
        self.fallback_memory = None
        self.using_fallback = False
        self.db_url = db_url
        self.namespace = namespace
        self.database = database
        
        try:
            logger.info(f"尝试初始化SurrealDB记忆系统，连接到 {db_url}/{namespace}/{database}")
            
            # 创建SurrealDB存储工厂
            self.storage_factory = SurrealStorageFactory(db_url, namespace, database)
            
            # 创建内部存储实例
            from ..storage.memory import SurrealMemory as StorageSurrealMemory
            self.storage = StorageSurrealMemory(self.storage_factory)
            
            # 测试连接是否正常 - 使用一个简单的查询
            # 这里不使用get方法，因为它可能会在表不存在时失败
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 使用存储工厂直接执行一个简单的查询
            storage = self.storage_factory.get_storage()
            test_conn = loop.run_until_complete(storage.connect())
            test_query = loop.run_until_complete(storage.query("INFO FOR DB;"))
            
            logger.info(f"SurrealDB记忆系统初始化成功，连接到 {db_url}/{namespace}/{database}")
            logger.info(f"SurrealDB连接测试成功: {test_query}")
        except Exception as e:
            logger.warning(f"SurrealDB记忆系统初始化失败: {e}，将使用SimpleMemory作为备用")
            import traceback
            logger.warning(traceback.format_exc())
            
            # 创建备用内存存储
            self.fallback_memory = SimpleMemory(max_items=1000)
            self.using_fallback = True
            logger.info("已切换到SimpleMemory备用存储")
    
    def save(self, user_input: str, assistant_response: str, session_id: str = "default") -> None:
        """
        保存对话记录到记忆系统
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            session_id: 会话ID
        """
        timestamp = datetime.now().isoformat()
        memory_item = {
            "timestamp": timestamp,
            "user_input": user_input,
            "assistant_response": assistant_response
        }
        
        try:
            if self.using_fallback:
                # 使用备用内存存储
                self.fallback_memory.save(user_input, assistant_response)
                logger.info(f"对话记录已保存到备用内存存储，会话 {session_id}")
            else:
                # 使用SurrealDB存储实例保存记忆
                self.storage.add(session_id, memory_item)
                logger.info(f"对话记录已保存到SurrealDB，会话 {session_id}")
        except Exception as e:
            logger.error(f"保存对话记录失败: {e}")
            # 如果SurrealDB保存失败，尝试使用备用存储
            if not self.using_fallback:
                logger.warning("切换到备用内存存储")
                if self.fallback_memory is None:
                    self.fallback_memory = SimpleMemory(max_items=1000)
                self.using_fallback = True
                self.fallback_memory.save(user_input, assistant_response)
                logger.info(f"对话记录已保存到备用内存存储，会话 {session_id}")
    
    def retrieve(self, query: str, limit: int = 5, session_id: str = "default") -> List[str]:
        """
        从记忆系统中检索相关记忆
        
        Args:
            query: 查询文本
            limit: 返回结果数量限制
            session_id: 会话ID
            
        Returns:
            相关记忆列表
        """
        try:
            if self.using_fallback:
                # 使用备用内存存储检索
                return self.fallback_memory.retrieve(query, limit)
            
            # 尝试使用SurrealDB存储实例检索
            # 如果有查询文本，使用search方法
            if query and query.strip():
                raw_memories = self.storage.search(session_id, query, limit)
            else:
                # 否则使用get方法获取最近的记忆
                raw_memories = self.storage.get(session_id, limit)
            
            # 格式化返回的记忆
            formatted_memories = []
            for memory in raw_memories:
                # 检查记忆格式是否符合预期
                if "user_input" in memory and "assistant_response" in memory:
                    formatted = (
                        f"用户: {memory['user_input']}\n"
                        f"助手: {memory['assistant_response']}"
                    )
                    formatted_memories.append(formatted)
            
            logger.info(f"从会话 {session_id} 检索到 {len(formatted_memories)} 条记忆")
            return formatted_memories
        except Exception as e:
            logger.error(f"检索记忆失败: {e}")
            # 如果SurrealDB检索失败，尝试使用备用存储
            if not self.using_fallback:
                logger.warning("切换到备用内存存储")
                if self.fallback_memory is None:
                    self.fallback_memory = SimpleMemory(max_items=1000)
                self.using_fallback = True
                return self.fallback_memory.retrieve(query, limit)
            return []
    
    def clear(self, session_id: str = "default") -> None:
        """
        清除指定会话的所有记忆
        
        Args:
            session_id: 会话ID
        """
        try:
            self.storage.clear(session_id)
            logger.info(f"已清除会话 {session_id} 的所有记忆")
        except Exception as e:
            logger.error(f"清除记忆失败: {e}")
    
    async def save_async(self, user_input: str, assistant_response: str, session_id: str = "default") -> None:
        """
        异步保存对话记录到记忆系统
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            session_id: 会话ID
        """
        # 创建一个新的事件循环来运行同步方法
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: self.save(user_input, assistant_response, session_id)
        )
    
    async def retrieve_async(self, query: str, limit: int = 5, session_id: str = "default") -> List[str]:
        """
        异步从记忆系统中检索相关记忆
        
        Args:
            query: 查询文本
            limit: 返回结果数量限制
            session_id: 会话ID
            
        Returns:
            相关记忆列表
        """
        # 创建一个新的事件循环来运行同步方法
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.retrieve(query, limit, session_id)
        )
