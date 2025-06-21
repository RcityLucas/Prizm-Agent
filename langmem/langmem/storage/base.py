"""
Abstract base classes for storage components.

This module defines the interfaces that all storage implementations must adhere to.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from langmem.core.models import Memory


class StorageBase(ABC):
    """
    存储接口的抽象基类，定义了所有存储实现必须提供的方法。
    
    这个接口允许LangMem系统使用不同的存储后端，如SurrealDB、内存存储等，
    同时保持一致的API。
    """
    
    @abstractmethod
    async def create(self, memory: Memory) -> str:
        """
        创建新记忆并返回其ID。
        
        Args:
            memory: 要创建的记忆对象
            
        Returns:
            创建的记忆的ID
            
        Raises:
            StorageError: 如果创建过程中发生错误
        """
        pass
    
    @abstractmethod
    async def get(self, memory_id: str) -> Optional[Memory]:
        """
        根据ID获取记忆。
        
        Args:
            memory_id: 记忆的ID
            
        Returns:
            找到的记忆对象，如果不存在则返回None
            
        Raises:
            StorageError: 如果获取过程中发生错误
        """
        pass
    
    @abstractmethod
    async def update(self, memory: Memory) -> bool:
        """
        更新现有记忆。
        
        Args:
            memory: 要更新的记忆对象，必须包含有效的ID
            
        Returns:
            更新是否成功
            
        Raises:
            StorageError: 如果更新过程中发生错误
        """
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """
        删除记忆。
        
        Args:
            memory_id: 要删除的记忆的ID
            
        Returns:
            删除是否成功
            
        Raises:
            StorageError: 如果删除过程中发生错误
        """
        pass
    
    @abstractmethod
    async def query(self, filters: Dict[str, Any], limit: int = 100) -> List[Memory]:
        """
        根据过滤条件查询记忆。
        
        Args:
            filters: 过滤条件，键值对形式
            limit: 返回结果的最大数量
            
        Returns:
            符合条件的记忆列表
            
        Raises:
            StorageError: 如果查询过程中发生错误
        """
        pass
    
    @abstractmethod
    async def vector_search(self, 
                           embedding: List[float], 
                           limit: int = 10, 
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        执行向量相似度搜索。
        
        Args:
            embedding: 查询向量
            limit: 返回结果的最大数量
            filters: 可选的额外过滤条件
            
        Returns:
            包含记忆和相似度分数的列表，每项为字典，包含'memory'和'score'键
            
        Raises:
            StorageError: 如果搜索过程中发生错误
        """
        pass


class StorageError(Exception):
    """
    存储操作相关的异常类。
    """
    pass
