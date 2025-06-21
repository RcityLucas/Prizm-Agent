"""
Core memory manager implementation.

This module defines the MemoryManager class, which is the central component
of the LangMem package, coordinating storage, retrieval, and processing of memories.
"""

from typing import List, Dict, Any, Optional, Union, Callable
import logging

from langmem.core.models import Memory, MemoryQuery, RetrievedMemory
from langmem.storage.base import StorageBase
from langmem.retrievers.base import RetrieverBase


logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器，LangMem系统的核心组件。
    
    MemoryManager协调存储、检索和处理组件，提供统一的API来管理记忆。
    它负责记忆的添加、检索、更新和删除，以及与嵌入向量生成相关的功能。
    """
    
    def __init__(
        self,
        storage: StorageBase,
        retriever: RetrieverBase,
        embedding_provider: Optional[Any] = None,
    ):
        """
        初始化记忆管理器。
        
        Args:
            storage: 存储后端实例
            retriever: 检索器实例
            embedding_provider: 可选的嵌入向量生成器，如果提供，将用于自动生成嵌入向量
        """
        self.storage = storage
        self.retriever = retriever
        self.embedding_provider = embedding_provider
        logger.info("MemoryManager initialized with %s storage and %s retriever",
                   storage.__class__.__name__, retriever.__class__.__name__)
    
    async def add_memory(
        self,
        content: str,
        memory_type: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> str:
        """
        添加新记忆。
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            metadata: 额外元数据
            embedding: 预计算的嵌入向量，如果为None且embedding_provider可用，将自动生成
            
        Returns:
            创建的记忆的ID
            
        Raises:
            ValueError: 如果content为空
            RuntimeError: 如果embedding为None且embedding_provider不可用
        """
        if not content:
            raise ValueError("Memory content cannot be empty")
        
        # 如果没有提供嵌入向量且有嵌入向量生成器，则生成嵌入向量
        if embedding is None and self.embedding_provider is not None:
            try:
                embedding = await self._generate_embedding(content)
                logger.debug("Generated embedding for memory with length %d", len(embedding))
            except Exception as e:
                logger.error("Failed to generate embedding: %s", str(e))
                # 如果生成嵌入向量失败，仍然继续但使用空列表
                embedding = []
        elif embedding is None:
            logger.warning("No embedding provided and no embedding_provider available")
            embedding = []
        
        # 创建记忆对象
        memory = Memory(
            content=content,
            embedding=embedding,
            memory_type=memory_type,
            metadata=metadata or {},
        )
        
        # 存储记忆并返回ID
        memory_id = await self.storage.create(memory)
        logger.info("Created memory with ID %s and type %s", memory_id, memory_type)
        return memory_id
    
    async def retrieve_memories(
        self,
        query: Union[str, MemoryQuery],
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedMemory]:
        """
        检索与查询相关的记忆。
        
        Args:
            query: 查询内容，可以是字符串或MemoryQuery对象
            limit: 返回结果的最大数量
            filters: 额外的过滤条件
            
        Returns:
            检索到的记忆列表，按相关度排序
            
        Raises:
            ValueError: 如果query为空
        """
        # 如果query是字符串，转换为MemoryQuery对象
        if isinstance(query, str):
            if not query:
                raise ValueError("Query content cannot be empty")
            
            # 如果有嵌入向量生成器，为查询生成嵌入向量
            embedding = None
            if self.embedding_provider is not None:
                try:
                    embedding = await self._generate_embedding(query)
                except Exception as e:
                    logger.error("Failed to generate embedding for query: %s", str(e))
            
            # 创建查询对象
            query_obj = MemoryQuery(
                content=query,
                embedding=embedding,
                filters=filters or {},
            )
        else:
            # 如果已经是MemoryQuery对象，直接使用
            query_obj = query
            # 如果提供了额外的filters，合并到查询对象的filters中
            if filters:
                query_obj.filters.update(filters)
        
        # 使用检索器检索记忆
        retrieved_memories = await self.retriever.retrieve(query_obj, limit)
        logger.info("Retrieved %d memories for query", len(retrieved_memories))
        return retrieved_memories
    
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        根据ID获取记忆。
        
        Args:
            memory_id: 记忆的ID
            
        Returns:
            找到的记忆对象，如果不存在则返回None
        """
        memory = await self.storage.get(memory_id)
        if memory:
            logger.debug("Retrieved memory with ID %s", memory_id)
        else:
            logger.debug("Memory with ID %s not found", memory_id)
        return memory
    
    async def update_memory(self, memory: Memory) -> bool:
        """
        更新现有记忆。
        
        Args:
            memory: 要更新的记忆对象，必须包含有效的ID
            
        Returns:
            更新是否成功
            
        Raises:
            ValueError: 如果memory.id为None
        """
        if memory.id is None:
            raise ValueError("Memory ID cannot be None for update operation")
        
        # 如果内容已更改且嵌入向量生成器可用，重新生成嵌入向量
        existing_memory = await self.storage.get(memory.id)
        if (existing_memory and 
            existing_memory.content != memory.content and 
            self.embedding_provider is not None):
            try:
                memory.embedding = await self._generate_embedding(memory.content)
                logger.debug("Regenerated embedding for updated memory")
            except Exception as e:
                logger.error("Failed to regenerate embedding: %s", str(e))
        
        # 更新记忆
        success = await self.storage.update(memory)
        if success:
            logger.info("Updated memory with ID %s", memory.id)
        else:
            logger.warning("Failed to update memory with ID %s", memory.id)
        return success
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆。
        
        Args:
            memory_id: 要删除的记忆的ID
            
        Returns:
            删除是否成功
        """
        success = await self.storage.delete(memory_id)
        if success:
            logger.info("Deleted memory with ID %s", memory_id)
        else:
            logger.warning("Failed to delete memory with ID %s", memory_id)
        return success
    
    async def _generate_embedding(self, content: str) -> List[float]:
        """
        为内容生成嵌入向量。
        
        Args:
            content: 要生成嵌入向量的内容
            
        Returns:
            生成的嵌入向量
            
        Raises:
            RuntimeError: 如果embedding_provider不可用或生成失败
        """
        if self.embedding_provider is None:
            raise RuntimeError("No embedding provider available")
        
        # 根据embedding_provider的类型，调用不同的方法生成嵌入向量
        if hasattr(self.embedding_provider, "get_embedding"):
            # 同步方法
            return self.embedding_provider.get_embedding(content)
        elif hasattr(self.embedding_provider, "get_embedding_async"):
            # 异步方法
            return await self.embedding_provider.get_embedding_async(content)
        else:
            # 尝试直接调用
            try:
                result = self.embedding_provider(content)
                # 如果结果是协程，等待它
                if hasattr(result, "__await__"):
                    return await result
                return result
            except Exception as e:
                raise RuntimeError(f"Failed to generate embedding: {str(e)}")
