"""
存储系统配置

定义存储系统的配置选项
"""
import os
from typing import Dict, Any

# 默认的SurrealDB配置
DEFAULT_SURREAL_CONFIG = {
    "url": "ws://localhost:8000/rpc",
    "namespace": "rainbow",
    "database": "test",
    "username": "root",
    "password": "root"
}

# 从环境变量获取SurrealDB配置
def get_surreal_config() -> Dict[str, Any]:
    """从环境变量获取SurrealDB配置
    
    Returns:
        SurrealDB配置字典
    """
    return {
        "url": os.getenv("SURREALDB_URL", DEFAULT_SURREAL_CONFIG["url"]),
        "namespace": os.getenv("SURREALDB_NAMESPACE", DEFAULT_SURREAL_CONFIG["namespace"]),
        "database": os.getenv("SURREALDB_DATABASE", DEFAULT_SURREAL_CONFIG["database"]),
        "username": os.getenv("SURREALDB_USERNAME", DEFAULT_SURREAL_CONFIG["username"]),
        "password": os.getenv("SURREALDB_PASSWORD", DEFAULT_SURREAL_CONFIG["password"])
    }

# 存储系统类型
STORAGE_TYPE_SURREAL = "surreal"
