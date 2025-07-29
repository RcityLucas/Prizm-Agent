"""
用户存储管理器 - 确保存储实例一致性
"""
import threading
from typing import Optional
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)

class UserStorageManager:
    """单例用户存储管理器，确保整个应用使用同一个存储实例"""
    
    _instance = None
    _lock = threading.Lock()
    _storage = None
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UserStorageManager, cls).__new__(cls)
            return cls._instance
    
    def get_storage(self):
        """获取用户存储实例"""
        if self._storage is None:
            with self._lock:
                if self._storage is None:
                    self._storage = self._create_storage()
                    logger.info(f"UserStorageManager: 创建新的存储实例 {type(self._storage).__name__}, ID: {id(self._storage)}")
        else:
            logger.info(f"UserStorageManager: 复用现有存储实例 {type(self._storage).__name__}, ID: {id(self._storage)}")
        
        return self._storage
    
    def _create_storage(self):
        """创建新的存储实例"""
        try:
            # 从统一存储系统获取数据库客户端
            from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
            
            # 创建统一存储实例
            storage_instance = UnifiedDialogueStorage()
            
            # 检查数据库可用性
            if not storage_instance or not storage_instance.shared_client:
                raise Exception("无法获取SurrealDB客户端，请检查SurrealDB是否正在运行")
            
            # 初始化SurrealDB用户存储
            from rainbow_agent.auth.storage import SurrealUserStorage
            user_storage = SurrealUserStorage(db_client=storage_instance.shared_client)
            
            logger.info(f"UserStorageManager: 存储实例创建成功")
            logger.info(f"  - 存储类型: {type(user_storage).__name__}")
            logger.info(f"  - 存储实例ID: {id(user_storage)}")
            logger.info(f"  - 数据库客户端ID: {id(storage_instance.shared_client)}")
            logger.info(f"  - 表名: {user_storage.table}")
            
            return user_storage
            
        except Exception as e:
            logger.error(f"UserStorageManager: 创建存储实例失败: {e}")
            raise e
    
    def reset_storage(self):
        """重置存储实例（用于故障恢复）"""
        with self._lock:
            logger.warning("UserStorageManager: 重置存储实例")
            self._storage = None
    
    def verify_storage_consistency(self):
        """验证存储一致性"""
        if self._storage is None:
            return False
        
        try:
            # 尝试执行简单查询验证连接
            if hasattr(self._storage, 'db') and self._storage.db:
                # 简单的数据库连接测试
                test_query = f"SELECT count() FROM {self._storage.table} LIMIT 1"
                result = self._storage.db.execute_sql(test_query)
                logger.info(f"UserStorageManager: 存储一致性验证通过, 表 {self._storage.table} 可访问")
                return True
            else:
                logger.warning("UserStorageManager: 存储实例缺少数据库连接")
                return False
        except Exception as e:
            logger.warning(f"UserStorageManager: 存储一致性验证失败: {e}")
            return False

# 全局存储管理器实例
storage_manager = UserStorageManager()

def get_user_storage():
    """获取用户存储实例的全局函数"""
    storage = storage_manager.get_storage()
    
    # 验证存储一致性
    if not storage_manager.verify_storage_consistency():
        logger.warning("存储一致性验证失败，重置存储实例")
        storage_manager.reset_storage()
        storage = storage_manager.get_storage()
    
    return storage