"""
存储模块
提供统一的存储接口和多种存储实现
"""
from .thread_safe_db import get_connection, execute_query, close_connection
