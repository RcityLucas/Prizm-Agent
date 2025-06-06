"""
存储系统配置

定义存储系统的配置选项
"""
import os
from typing import Dict, Any

# 从环境变量获取SurrealDB配置
def get_surreal_config() -> Dict[str, Any]:
    """从环境变量获取SurrealDB配置
    
    Returns:
        SurrealDB配置字典
    """
    return {
        "url": os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc"),
        "namespace": os.getenv("SURREALDB_NAMESPACE", "rainbow"),
        "database": os.getenv("SURREALDB_DATABASE", "test"),  # Default to "test" if env var not set
        "username": os.getenv("SURREALDB_USERNAME", "root"),
        "password": os.getenv("SURREALDB_PASSWORD", "root")
    }

# 存储系统类型
STORAGE_TYPE_SURREAL = "surreal"
