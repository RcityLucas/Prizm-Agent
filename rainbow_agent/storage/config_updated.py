"""
Storage system configuration.

This module defines configuration options for the storage system.
It now uses the centralized configuration system while maintaining 
backward compatibility with existing code.
"""
import os
from typing import Dict, Any
from urllib.parse import urlparse

# Import the centralized configuration system
try:
    from rainbow_agent.config import config
    USE_CENTRAL_CONFIG = True
except ImportError:
    # Fallback to legacy configuration if the new system is not available
    USE_CENTRAL_CONFIG = False
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # dotenv is optional
        pass

def _get_http_url_from_ws(ws_url: str) -> str:
    """
    Derive HTTP URL from WebSocket URL.
    
    Args:
        ws_url: WebSocket URL (e.g., ws://localhost:8000/rpc)
        
    Returns:
        Corresponding HTTP URL (e.g., http://localhost:8000)
    """
    parsed = urlparse(ws_url)
    
    # Convert protocol
    if parsed.scheme == 'ws':
        scheme = 'http'
    elif parsed.scheme == 'wss':
        scheme = 'https'
    else:
        scheme = parsed.scheme
    
    # Build HTTP URL without path
    return f"{scheme}://{parsed.netloc}"

def get_surreal_config() -> Dict[str, Any]:
    """
    Get SurrealDB configuration.
    
    This function now uses the centralized configuration system if available,
    but falls back to the legacy implementation for backward compatibility.
    
    Returns:
        SurrealDB configuration dictionary, including WebSocket and HTTP URLs.
    """
    if USE_CENTRAL_CONFIG:
        # Use the centralized configuration system
        http_url = config.surreal.http_url
        
        return {
            "url": config.surreal.url,
            "http_url": http_url,
            "health_url": f"{http_url}/health" if http_url else None,
            "namespace": config.surreal.namespace,
            "database": config.surreal.database,
            "username": config.surreal.username,
            "password": config.surreal.password
        }
    else:
        # Legacy implementation for backward compatibility
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

# Storage system types
STORAGE_TYPE_SURREAL = "surreal"
