"""
存储工厂接口

使用SurrealDB作为存储后端
"""
import os
import logging
import asyncio
from typing import Dict, Any, Optional

from .config import get_surreal_config, STORAGE_TYPE_SURREAL

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局存储工厂实例
_storage_factory = None

def get_storage_factory(config: Optional[Dict[str, Any]] = None) -> "StorageFactory":
    """获取存储工厂实例
    
    获取SurrealDB存储工厂实例
    
    Args:
        config: SurrealDB配置
        
    Returns:
        SurrealDB存储工厂实例
    """
    global _storage_factory
    if _storage_factory is None:
        # 导入SurrealDB存储工厂
        from .storage_factory import StorageFactory
        surreal_config = config or get_surreal_config()
        _storage_factory = StorageFactory(surreal_config)
        logger.info("使用SurrealDB存储系统")
    
    return _storage_factory

def init_storage_factory():
    """初始化存储工厂
    
    初始化SurrealDB存储工厂，并连接到存储系统
    """
    factory = get_storage_factory()
    
    # 异步初始化SurrealDB连接
    from .storage_factory import StorageFactory
    if isinstance(factory, StorageFactory):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(factory.init_all())
    
    return factory
