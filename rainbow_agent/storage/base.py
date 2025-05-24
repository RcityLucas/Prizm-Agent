"""
存储系统基础接口

定义了存储系统的基本接口，所有具体存储实现都应该继承这个基类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union


class BaseStorage(ABC):
    """存储系统基础接口"""
    
    @abstractmethod
    async def connect(self) -> None:
        """连接到存储系统"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开与存储系统的连接"""
        pass
    
    @abstractmethod
    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建记录"""
        pass
    
    @abstractmethod
    async def read(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """读取记录"""
        pass
    
    @abstractmethod
    async def read_many(self, table: str, query: Dict[str, Any] = None, 
                        limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """读取多条记录"""
        pass
    
    @abstractmethod
    async def update(self, table: str, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新记录"""
        pass
    
    @abstractmethod
    async def delete(self, table: str, id: str) -> bool:
        """删除记录"""
        pass
    
    @abstractmethod
    async def query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行自定义查询"""
        pass
