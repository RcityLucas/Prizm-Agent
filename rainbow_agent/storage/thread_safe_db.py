"""
线程安全的数据库连接模块

提供线程安全的数据库连接，解决多线程环境下的数据库锁定问题。
"""
import os
import sqlite3
import threading
from typing import Any

# 线程本地存储，用于管理数据库连接
_connection_local = threading.local()

def get_connection(db_path="data/sessions.sqlite"):
    """获取当前线程的数据库连接
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        SQLite连接对象
    """
    if not hasattr(_connection_local, "connection"):
        # 确保数据库目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # 创建新的连接，设置超时和隔离级别
        _connection_local.connection = sqlite3.connect(
            db_path, 
            timeout=30.0,
            isolation_level=None  # 自动提交模式
        )
        # 启用WAL模式
        _connection_local.connection.execute("PRAGMA journal_mode=WAL")
        
        # 设置行工厂，返回字典
        _connection_local.connection.row_factory = sqlite3.Row
    
    return _connection_local.connection

def close_connection():
    """关闭当前线程的数据库连接"""
    if hasattr(_connection_local, "connection"):
        _connection_local.connection.close()
        delattr(_connection_local, "connection")

def execute_query(query, params=None, db_path="data/sessions.sqlite"):
    """执行查询并返回结果
    
    Args:
        query: SQL查询语句
        params: 查询参数
        db_path: 数据库文件路径
        
    Returns:
        查询结果
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # 如果是SELECT查询，返回结果
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            # 将Row对象转换为字典
            result = []
            for row in rows:
                row_dict = {}
                for key in row.keys():
                    row_dict[key] = row[key]
                result.append(row_dict)
            return result
        # 如果是INSERT查询，返回最后插入的行ID
        elif query.strip().upper().startswith("INSERT"):
            return cursor.lastrowid
        # 其他查询，返回受影响的行数
        else:
            return cursor.rowcount
    except Exception as e:
        # 回滚事务
        conn.rollback()
        raise e
