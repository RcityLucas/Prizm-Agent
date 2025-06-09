"""
存储系统配置

定义存储系统的配置选项
"""
import os
from typing import Dict, Any
from urllib.parse import urlparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional
    pass

def _get_http_url_from_ws(ws_url: str) -> str:
    """从WebSocket URL推导HTTP URL
    
    Args:
        ws_url: WebSocket URL (如: ws://localhost:8000/rpc)
        
    Returns:
        对应的HTTP URL (如: http://localhost:8000)
    """
    parsed = urlparse(ws_url)
    
    # 转换协议
    if parsed.scheme == 'ws':
        scheme = 'http'
    elif parsed.scheme == 'wss':
        scheme = 'https'
    else:
        scheme = parsed.scheme
    
    # 构建HTTP URL，移除路径部分
    return f"{scheme}://{parsed.netloc}"

def get_surreal_config() -> Dict[str, Any]:
    """从环境变量获取SurrealDB配置
    
    Returns:
        SurrealDB配置字典，包含WebSocket和HTTP URL
    """
    ws_url = os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc")
    http_url = _get_http_url_from_ws(ws_url)
    
    return {
        "url": ws_url,
        "http_url": http_url,
        "health_url": f"{http_url}/health",
        "namespace": os.getenv("SURREALDB_NAMESPACE", "rainbow"),
        "database": os.getenv("SURREALDB_DATABASE", "test"),
        "username": os.getenv("SURREALDB_USERNAME", "root"),
        "password": os.getenv("SURREALDB_PASSWORD", "root")
    }

# 存储系统类型
STORAGE_TYPE_SURREAL = "surreal"
