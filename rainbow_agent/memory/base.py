"""
记忆系统基础组件

定义记忆系统的接口和基础实现
"""
from typing import List, Dict, Any, Optional, Union
import uuid
import time
from abc import ABC, abstractmethod

from ..utils.logger import get_logger

logger = get_logger(__name__)


class Memory(ABC):
    """记忆系统接口"""
    
    @abstractmethod
    def add(self, content: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加一条记忆
        
        Args:
            content: 记忆内容
            metadata: 记忆元数据
            
        Returns:
            记忆ID
        """
        pass
    
    @abstractmethod
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定ID的记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            记忆内容和元数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关记忆
        
        Args:
            query: 查询字符串
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清除所有记忆"""
        pass


class MemoryItem:
    """记忆项"""
    
    def __init__(
        self, 
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None
    ):
        """
        初始化记忆项
        
        Args:
            content: 记忆内容
            metadata: 记忆元数据
            memory_id: 记忆ID，如果不提供则自动生成
        """
        self.memory_id = memory_id or str(uuid.uuid4())
        self.content = content
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count
        }
    
    def access(self) -> None:
        """更新访问信息"""
        self.last_accessed = time.time()
        self.access_count += 1


class SimpleMemory(Memory):
    """
    简单内存记忆系统
    
    一个基础的内存记忆实现，将记忆存储在内存中
    """
    
    def __init__(self):
        """初始化简单记忆系统"""
        self.memories: Dict[str, MemoryItem] = {}
    
    def add(self, content: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加一条记忆"""
        memory_item = MemoryItem(content=content, metadata=metadata)
        self.memories[memory_item.memory_id] = memory_item
        logger.debug(f"添加记忆: {memory_item.memory_id[:8]}...")
        return memory_item.memory_id
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """获取指定ID的记忆"""
        if memory_id in self.memories:
            memory_item = self.memories[memory_id]
            memory_item.access()
            return memory_item.to_dict()
        return None
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关记忆（简单实现，仅基于文本匹配）
        
        注意：这是一个非常简单的实现，仅用于示例
        生产环境应该使用更高级的搜索方法，如向量搜索
        """
        query = query.lower()
        results = []
        
        for memory_item in self.memories.values():
            content_str = str(memory_item.content).lower()
            
            # 简单文本匹配
            if query in content_str:
                memory_item.access()
                results.append(memory_item.to_dict())
        
        # 按最近访问时间排序并限制结果数量
        results.sort(key=lambda x: x["last_accessed"], reverse=True)
        return results[:limit]
    
    def clear(self) -> None:
        """清除所有记忆"""
        self.memories.clear()
        logger.debug("清除所有记忆")


class BufferedMemory(Memory):
    """
    带缓冲的记忆系统
    
    维护一个固定大小的缓冲区，超出大小时移除最不重要的记忆
    """
    
    def __init__(self, capacity: int = 100):
        """
        初始化带缓冲的记忆系统
        
        Args:
            capacity: 缓冲区容量
        """
        self.capacity = capacity
        self.memories: Dict[str, MemoryItem] = {}
    
    def add(self, content: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加一条记忆"""
        # 检查容量是否已满
        if len(self.memories) >= self.capacity:
            self._evict_least_important()
        
        # 添加新记忆
        memory_item = MemoryItem(content=content, metadata=metadata)
        self.memories[memory_item.memory_id] = memory_item
        logger.debug(f"添加记忆: {memory_item.memory_id[:8]}... (缓冲区: {len(self.memories)}/{self.capacity})")
        return memory_item.memory_id
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """获取指定ID的记忆"""
        if memory_id in self.memories:
            memory_item = self.memories[memory_id]
            memory_item.access()
            return memory_item.to_dict()
        return None
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索相关记忆（简单实现）"""
        query = query.lower()
        results = []
        
        for memory_item in self.memories.values():
            content_str = str(memory_item.content).lower()
            
            # 简单文本匹配
            if query in content_str:
                memory_item.access()
                results.append(memory_item.to_dict())
        
        # 按最近访问时间排序并限制结果数量
        results.sort(key=lambda x: x["last_accessed"], reverse=True)
        return results[:limit]
    
    def clear(self) -> None:
        """清除所有记忆"""
        self.memories.clear()
        logger.debug("清除所有记忆")
    
    def _evict_least_important(self) -> None:
        """移除最不重要的记忆"""
        if not self.memories:
            return
        
        # 根据重要性评分（简单实现：访问次数 * 0.7 + 新近度 * 0.3）
        current_time = time.time()
        memory_scores = {}
        
        for memory_id, memory in self.memories.items():
            recency = 1 / (current_time - memory.created_at + 1)  # 新近度
            access_score = memory.access_count
            
            # 重要性评分
            importance = access_score * 0.7 + recency * 0.3
            memory_scores[memory_id] = importance
        
        # 找出最不重要的记忆并移除
        least_important = min(memory_scores, key=memory_scores.get)
        self.memories.pop(least_important)
        logger.debug(f"移除最不重要的记忆: {least_important[:8]}...")
