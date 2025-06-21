"""
Abstract base classes for retriever components.

This module defines the interfaces that all retriever implementations must adhere to.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from langmem.core.models import Memory, MemoryQuery, RetrievedMemory
from langmem.storage.base import StorageBase


class RetrieverBase(ABC):
    """
    检索器接口的抽象基类，定义了所有检索实现必须提供的方法。
    
    检索器负责根据查询从存储中检索相关记忆，并可能应用不同的检索策略，
    如向量相似度、时间衰减、重要性评分等。
    """
    
    def __init__(self, storage: StorageBase):
        """
        初始化检索器。
        
        Args:
            storage: 存储后端实例，用于访问记忆
        """
        self.storage = storage
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def score_memory(self, memory: Memory, query: MemoryQuery) -> float:
        """
        计算记忆与查询的相关度分数。
        
        Args:
            memory: 要评分的记忆
            query: 查询对象
            
        Returns:
            相关度分数，通常为0到1之间的浮点数
        """
        pass


class RetrieverError(Exception):
    """
    检索操作相关的异常类。
    """
    pass
