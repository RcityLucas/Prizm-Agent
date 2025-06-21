"""
Vector-based memory retriever implementation.

This module provides a retriever that uses vector similarity to find relevant memories.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional

from langmem.core.models import Memory, MemoryQuery, RetrievedMemory
from langmem.retrievers.base import RetrieverBase, RetrieverError
from langmem.storage.base import StorageBase


logger = logging.getLogger(__name__)


class VectorRetriever(RetrieverBase):
    """
    基于向量相似度的记忆检索器。
    
    此检索器使用向量嵌入的余弦相似度来找到与查询最相关的记忆。
    它依赖于存储后端的向量搜索能力，如果存储后端支持的话。
    否则，它会在内存中执行向量相似度计算。
    """
    
    def __init__(self, storage: StorageBase):
        """
        初始化向量检索器。
        
        Args:
            storage: 存储后端实例，用于访问记忆
        """
        super().__init__(storage)
        logger.info("VectorRetriever initialized")
    
    async def retrieve(self, query: MemoryQuery, limit: int = 5) -> List[RetrievedMemory]:
        """
        根据查询检索相关记忆。
        
        Args:
            query: 查询对象，包含查询内容、嵌入向量和过滤条件
            limit: 返回结果的最大数量
            
        Returns:
            检索到的记忆列表，按相关度排序
            
        Raises:
            RetrieverError: 如果检索过程中发生错误
        """
        if not query.embedding:
            logger.warning("Query has no embedding, vector retrieval may not be effective")
            # 如果查询没有嵌入向量，使用基本的过滤查询
            try:
                memories = await self.storage.query(query.filters, limit=limit)
                # 为每个记忆计算一个默认的相关度分数（0.5）
                return [RetrievedMemory(memory=memory, relevance=0.5) for memory in memories]
            except Exception as e:
                logger.error("Failed to retrieve memories without embedding: %s", str(e))
                raise RetrieverError(f"Failed to retrieve memories: {str(e)}")
        
        try:
            # 尝试使用存储后端的向量搜索功能
            try:
                # 使用存储后端的向量搜索
                results = await self.storage.vector_search(
                    embedding=query.embedding,
                    limit=limit,
                    filters=query.filters
                )
                
                # 将结果转换为RetrievedMemory对象
                retrieved_memories = []
                for result in results:
                    memory = result["memory"]
                    # 将距离转换为相似度分数（0到1之间）
                    # 假设score是欧几里得距离，较小的距离表示较高的相似度
                    # 使用一个简单的转换公式：relevance = 1 / (1 + distance)
                    distance = result["score"]
                    relevance = 1 / (1 + distance)
                    retrieved_memories.append(RetrievedMemory(memory=memory, relevance=relevance))
                
                logger.debug("Retrieved %d memories using storage vector search", len(retrieved_memories))
                return retrieved_memories
            except (AttributeError, NotImplementedError):
                # 如果存储后端不支持向量搜索，回退到内存中的向量相似度计算
                logger.info("Storage does not support vector search, falling back to in-memory calculation")
                raise NotImplementedError("Falling back to in-memory calculation")
        except NotImplementedError:
            # 在内存中执行向量相似度计算
            try:
                # 获取所有可能的记忆
                memories = await self.storage.query(query.filters, limit=100)  # 获取更多记忆以便进行筛选
                
                # 计算每个记忆的相关度分数
                retrieved_memories = []
                for memory in memories:
                    if memory.embedding:
                        relevance = self.score_memory(memory, query)
                        retrieved_memories.append(RetrievedMemory(memory=memory, relevance=relevance))
                
                # 按相关度排序并限制结果数量
                retrieved_memories.sort(key=lambda x: x.relevance, reverse=True)
                retrieved_memories = retrieved_memories[:limit]
                
                logger.debug("Retrieved %d memories using in-memory vector calculation", len(retrieved_memories))
                return retrieved_memories
            except Exception as e:
                logger.error("Failed to retrieve memories with in-memory calculation: %s", str(e))
                raise RetrieverError(f"Failed to retrieve memories: {str(e)}")
        except Exception as e:
            logger.error("Failed to retrieve memories: %s", str(e))
            raise RetrieverError(f"Failed to retrieve memories: {str(e)}")
    
    def score_memory(self, memory: Memory, query: MemoryQuery) -> float:
        """
        计算记忆与查询的相关度分数。
        
        使用余弦相似度作为相关度度量。
        
        Args:
            memory: 要评分的记忆
            query: 查询对象
            
        Returns:
            相关度分数，范围为0到1
        """
        # 如果记忆或查询没有嵌入向量，返回最低分数
        if not memory.embedding or not query.embedding:
            return 0.0
        
        try:
            # 计算余弦相似度
            memory_vec = np.array(memory.embedding)
            query_vec = np.array(query.embedding)
            
            # 归一化向量
            memory_vec = memory_vec / np.linalg.norm(memory_vec)
            query_vec = query_vec / np.linalg.norm(query_vec)
            
            # 计算余弦相似度
            similarity = np.dot(memory_vec, query_vec)
            
            # 确保相似度在0到1之间
            similarity = max(0.0, min(1.0, similarity))
            
            return float(similarity)
        except Exception as e:
            logger.error("Failed to calculate memory score: %s", str(e))
            return 0.0
