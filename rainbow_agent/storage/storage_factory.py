"""
存储工厂

用于创建和管理各种存储实例
"""
import os
import logging
from typing import Dict, Any, Optional

from .surreal_storage import SurrealStorage
from .session_manager import SessionManager
from .turn_manager import TurnManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StorageFactory:
    """存储工厂"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化存储工厂
        
        Args:
            config: 存储配置
        """
        self.config = config or {
            "url": "ws://localhost:8000/rpc",
            "namespace": "rainbow",
            "database": "agent",
            "username": "root",
            "password": "root"
        }
        
        # 存储实例缓存
        self._storage_cache = {}
        self._session_manager = None
        self._turn_manager = None
        
        logger.info("存储工厂初始化完成")
    
    def get_storage(self, name: str = "default") -> SurrealStorage:
        """获取存储实例
        
        Args:
            name: 存储实例名称
            
        Returns:
            存储实例
        """
        if name not in self._storage_cache:
            storage = SurrealStorage(
                url=self.config.get("url", "ws://localhost:8000/rpc"),
                namespace=self.config.get("namespace", "rainbow"),
                database=self.config.get("database", "agent"),
                username=self.config.get("username", "root"),
                password=self.config.get("password", "root")
            )
            self._storage_cache[name] = storage
            logger.info(f"创建存储实例: {name}")
        
        return self._storage_cache[name]
    
    def get_session_manager(self) -> SessionManager:
        """获取会话管理器
        
        Returns:
            会话管理器
        """
        if self._session_manager is None:
            self._session_manager = SessionManager(
                url=self.config.get("url", "ws://localhost:8000/rpc"),
                namespace=self.config.get("namespace", "rainbow"),
                database=self.config.get("database", "agent"),
                username=self.config.get("username", "root"),
                password=self.config.get("password", "root")
            )
            logger.info("创建会话管理器")
        
        return self._session_manager
    
    def get_turn_manager(self) -> TurnManager:
        """获取轮次管理器
        
        Returns:
            轮次管理器
        """
        if self._turn_manager is None:
            self._turn_manager = TurnManager(
                url=self.config.get("url", "ws://localhost:8000/rpc"),
                namespace=self.config.get("namespace", "rainbow"),
                database=self.config.get("database", "agent"),
                username=self.config.get("username", "root"),
                password=self.config.get("password", "root")
            )
            logger.info("创建轮次管理器")
        
        return self._turn_manager
    
    async def init_all(self) -> None:
        """初始化所有存储实例
        
        连接到所有存储实例
        """
        # 初始化会话管理器
        session_manager = self.get_session_manager()
        await session_manager.connect()
        
        # 初始化轮次管理器
        turn_manager = self.get_turn_manager()
        await turn_manager.connect()
        
        logger.info("所有存储实例初始化完成")
    
    async def close_all(self) -> None:
        """关闭所有存储实例
        
        断开与所有存储实例的连接
        """
        # 关闭会话管理器
        if self._session_manager:
            await self._session_manager.disconnect()
        
        # 关闭轮次管理器
        if self._turn_manager:
            await self._turn_manager.disconnect()
        
        # 关闭所有存储实例
        for name, storage in self._storage_cache.items():
            await storage.disconnect()
        
        logger.info("所有存储实例已关闭")


# 全局存储工厂实例
storage_factory = None


def get_storage_factory(config: Optional[Dict[str, Any]] = None) -> StorageFactory:
    """获取全局存储工厂实例
    
    Args:
        config: 存储配置
        
    Returns:
        存储工厂实例
    """
    global storage_factory
    if storage_factory is None:
        storage_factory = StorageFactory(config)
    return storage_factory
