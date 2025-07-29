"""
SurrealDB记忆系统

实现基于SurrealDB的记忆系统，继承自Memory基类
"""
from typing import List, Dict, Any, Optional
import json
import numpy as np
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
    
    def save(self, user_input: str, assistant_response: str, vector: Optional[List[float]] = None, session_id: str = "default") -> None:
        """
        保存对话记录到记忆系统
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            vector: 可选的向量表示，用于向量检索
            session_id: 会话ID
        """
        timestamp = datetime.now().isoformat()
        memory_item = {
            "timestamp": timestamp,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "vector": vector if vector is not None else []
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
    
    async def save_async(self, user_input: str, assistant_response: str, vector: Optional[List[float]] = None, session_id: str = "default") -> None:
        """
        异步保存对话记录到记忆系统
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            vector: 可选的向量表示，用于向量检索
            session_id: 会话ID
        """
        # 创建一个新的事件循环来运行同步方法
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: self.save(user_input, assistant_response, vector, session_id)
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
        
    def retrieve_by_vector(self, query_vector: List[float], limit: int = 5, session_id: str = "default") -> List[str]:
        """
        使用向量相似度从记忆系统中检索相关记忆
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量限制
            session_id: 会话ID
            
        Returns:
            相关记忆列表
        """
        try:
            if self.using_fallback:
                # 使用备用内存存储检索
                return self.fallback_memory.retrieve_by_vector(query_vector, limit)
            
            # 获取所有记忆
            raw_memories = self.storage.get(session_id, 100)  # 获取较多的记忆以便计算相似度
            
            # 过滤出带有向量的记忆
            memories_with_vectors = [m for m in raw_memories if m.get('vector') and len(m['vector']) > 0]
            
            if not memories_with_vectors:
                logger.warning(f"会话 {session_id} 中没有找到带有向量的记忆")
                return []
                
            # 计算余弦相似度
            similarities = []
            query_vector_np = np.array(query_vector)
            
            for memory in memories_with_vectors:
                memory_vector = np.array(memory['vector'])
                # 余弦相似度计算
                similarity = np.dot(query_vector_np, memory_vector) / (
                    np.linalg.norm(query_vector_np) * np.linalg.norm(memory_vector)
                ) if np.linalg.norm(memory_vector) > 0 else 0
                
                similarities.append((memory, similarity))
            
            # 按相似度降序排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # 取前 limit 个记忆
            top_memories = [item[0] for item in similarities[:limit]]
            
            # 格式化返回的记忆
            formatted_memories = []
            for memory in top_memories:
                # 检查记忆格式是否符合预期
                if "user_input" in memory and "assistant_response" in memory:
                    formatted = (
                        f"用户: {memory['user_input']}\n"
                        f"助手: {memory['assistant_response']}"
                    )
                    formatted_memories.append(formatted)
            
            logger.info(f"从会话 {session_id} 检索到 {len(formatted_memories)} 条向量相关记忆")
            return formatted_memories
        except Exception as e:
            logger.error(f"检索向量记忆失败: {e}")
            # 如果SurrealDB检索失败，尝试使用备用存储
            if not self.using_fallback:
                logger.warning("切换到备用内存存储")
                if self.fallback_memory is None:
                    self.fallback_memory = SimpleMemory(max_items=1000)
                self.using_fallback = True
                return self.fallback_memory.retrieve_by_vector(query_vector, limit)
            return []
    
    async def retrieve_by_vector_async(self, query_vector: List[float], limit: int = 5, session_id: str = "default") -> List[str]:
        """
        异步使用向量相似度从记忆系统中检索相关记忆
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量限制
            session_id: 会话ID
            
        Returns:
            相关记忆列表
        """
        # 创建一个新的事件循环来运行同步方法
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.retrieve_by_vector(query_vector, limit, session_id)
        )
    
    def retrieve_hybrid(self, query: str, query_vector: Optional[List[float]] = None, 
                       limit: int = 5, vector_weight: float = 0.5, session_id: str = "default") -> List[str]:
        """
        混合检索方法，结合关键词和向量相似度
        
        Args:
            query: 查询文本
            query_vector: 查询向量，如果为None则仅使用关键词检索
            limit: 返回结果数量限制
            vector_weight: 向量相似度的权重 (0-1)，越高越重视向量相似度
            session_id: 会话ID
            
        Returns:
            相关记忆列表
        """
        try:
            if self.using_fallback:
                # 使用备用内存存储检索
                return self.fallback_memory.retrieve_hybrid(query, query_vector, limit, vector_weight)
            
            # 如果没有提供向量，直接使用关键词检索
            if query_vector is None or len(query_vector) == 0:
                return self.retrieve(query, limit, session_id)
                
            # 获取所有记忆
            raw_memories = self.storage.get(session_id, 100)  # 获取较多的记忆以便计算相似度
            
            if not raw_memories:
                logger.warning(f"会话 {session_id} 中没有找到记忆")
                return []
            
            # 关键词相关度计算 (使用现有的search方法)
            keyword_matches = self.storage.search(session_id, query, 100)
            keyword_scores = {}
            for i, memory in enumerate(keyword_matches):
                # 根据排序位置计算分数，越靠前分数越高
                score = 1.0 - (i / len(keyword_matches)) if keyword_matches else 0.0
                memory_id = memory.get('id', str(i))
                keyword_scores[memory_id] = score
            
            # 向量相似度计算
            vector_scores = {}
            memories_with_vectors = [m for m in raw_memories if m.get('vector') and len(m['vector']) > 0]
            
            if memories_with_vectors and query_vector:
                query_vector_np = np.array(query_vector)
                
                for memory in memories_with_vectors:
                    memory_vector = np.array(memory['vector'])
                    memory_id = memory.get('id', str(id(memory)))
                    
                    # 余弦相似度计算
                    similarity = np.dot(query_vector_np, memory_vector) / (
                        np.linalg.norm(query_vector_np) * np.linalg.norm(memory_vector)
                    ) if np.linalg.norm(memory_vector) > 0 else 0
                    
                    vector_scores[memory_id] = similarity
            
            # 组合分数
            combined_scores = []
            for memory in raw_memories:
                memory_id = memory.get('id', str(id(memory)))
                keyword_score = keyword_scores.get(memory_id, 0.0)
                vector_score = vector_scores.get(memory_id, 0.0)
                
                # 计算组合分数
                combined_score = (1 - vector_weight) * keyword_score + vector_weight * vector_score
                combined_scores.append((memory, combined_score))
            
            # 按组合分数降序排序
            combined_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 取前 limit 个记忆
            top_memories = [item[0] for item in combined_scores[:limit]]
            
            # 格式化返回的记忆
            formatted_memories = []
            for memory in top_memories:
                # 检查记忆格式是否符合预期
                if "user_input" in memory and "assistant_response" in memory:
                    formatted = (
                        f"用户: {memory['user_input']}\n"
                        f"助手: {memory['assistant_response']}"
                    )
                    formatted_memories.append(formatted)
            
            logger.info(f"从会话 {session_id} 检索到 {len(formatted_memories)} 条混合相关记忆")
            return formatted_memories
        except Exception as e:
            logger.error(f"混合检索记忆失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            # 如果SurrealDB检索失败，尝试使用备用存储
            if not self.using_fallback:
                logger.warning("切换到备用内存存储")
                if self.fallback_memory is None:
                    self.fallback_memory = SimpleMemory(max_items=1000)
                self.using_fallback = True
                return self.fallback_memory.retrieve_hybrid(query, query_vector, limit, vector_weight)
            return []
    
    async def retrieve_hybrid_async(self, query: str, query_vector: Optional[List[float]] = None, 
                                 limit: int = 5, vector_weight: float = 0.5, session_id: str = "default") -> List[str]:
        """
        异步混合检索方法
        
        Args:
            query: 查询文本
            query_vector: 查询向量
            limit: 返回结果数量限制
            vector_weight: 向量相似度的权重
            session_id: 会话ID
            
        Returns:
            相关记忆列表
        """
        # 创建一个新的事件循环来运行同步方法
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.retrieve_hybrid(query, query_vector, limit, vector_weight, session_id)
        )
