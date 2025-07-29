"""
全局存储单例模块

确保整个应用使用同一个存储实例，避免注册和登录连接不一致问题。
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 全局存储实例
_global_storage_instance = None
_global_user_storage = None

def get_global_storage():
    """
    获取全局存储实例（单例模式）
    
    Returns:
        UnifiedDialogueStorage实例
    """
    global _global_storage_instance
    
    if _global_storage_instance is None:
        logger.info("创建全局存储实例（单例）")
        from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
        _global_storage_instance = UnifiedDialogueStorage()
        logger.info(f"全局存储实例创建完成，实例ID: {id(_global_storage_instance)}")
        logger.info(f"全局数据库客户端ID: {id(_global_storage_instance.shared_client)}")
    else:
        logger.debug(f"复用全局存储实例，实例ID: {id(_global_storage_instance)}")
    
    return _global_storage_instance

def get_global_user_storage():
    """
    获取全局用户存储实例（单例模式）
    
    Returns:
        SurrealUserStorage实例
    """
    global _global_user_storage
    
    if _global_user_storage is None:
        logger.info("创建全局用户存储实例（单例）")
        from rainbow_agent.auth.storage import SurrealUserStorage
        storage_instance = get_global_storage()
        _global_user_storage = SurrealUserStorage(db_client=storage_instance.shared_client)
        logger.info(f"全局用户存储实例创建完成，实例ID: {id(_global_user_storage)}")
        logger.info(f"使用数据库客户端ID: {id(storage_instance.shared_client)}")
    else:
        logger.debug(f"复用全局用户存储实例，实例ID: {id(_global_user_storage)}")
    
    return _global_user_storage

def reset_global_storage():
    """重置全局存储实例（用于测试或重启）"""
    global _global_storage_instance, _global_user_storage
    logger.info("重置全局存储实例")
    _global_storage_instance = None
    _global_user_storage = None
