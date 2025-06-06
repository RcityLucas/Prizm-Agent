"""
SurrealDB HTTP client implementation.
"""

import json
import logging
import requests
from typing import Dict, Any, List, Optional, Union
import asyncio
from datetime import datetime

from .db_helpers import get_auth_headers, get_current_time_iso, parse_surreal_response
from .db_queries import (
    build_select_query, 
    build_parameterized_select_query,
    build_insert_query,
    build_update_query,
    build_delete_query,
    build_count_query
)
from .db_async_helpers import (
    execute_sql_async,
    create_record_async,
    update_record_async,
    delete_record_async,
    get_record_async
)

logger = logging.getLogger(__name__)

class SurrealDBHttpClient:
    """
    SurrealDB HTTP client for database operations.
    
    This client provides both synchronous and asynchronous methods
    for interacting with SurrealDB via its HTTP API.
    """
    
    def __init__(self, url: str, namespace: str, database: str, username: str, password: str):
        """
        Initialize SurrealDB HTTP client.
        
        Args:
            url: SurrealDB base URL (e.g., http://localhost:8000)
            namespace: SurrealDB namespace
            database: SurrealDB database name
            username: SurrealDB username
            password: SurrealDB password
        """
        self.base_url = url
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        
        # 生成认证头
        self.headers = get_auth_headers(username, password, namespace, database)
        
        logger.info(f"SurrealDB HTTP客户端初始化完成: {url}, {namespace}, {database}")
    
    # ===== 同步方法 =====
    
    def execute_sql(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query synchronously.
        
        Args:
            sql: SQL query to execute
            params: Optional parameters for parameterized query
            
        Returns:
            List of records or empty list on failure
        """
        try:
            url = f"{self.base_url}/sql"
            
            # 准备请求负载
            payload = {'query': sql}
            if params:
                payload['vars'] = params
                
            logger.info(f"执行SQL: {sql}")
            if params:
                logger.info(f"参数: {params}")
                
            response = requests.post(url, headers=self.headers, json=payload)
            status = response.status_code
            
            logger.info(f"SQL查询响应码: {status}")
            
            if status == 200:
                result = response.json()
                logger.info(f"SQL查询执行成功: {sql}")
                
                # 解析响应
                parsed_result = parse_surreal_response(result)
                if parsed_result is not None:
                    return parsed_result
                return []
            else:
                logger.error(f"SQL查询失败: {status} {response.reason}")
                logger.error(f"响应内容: {response.text}")
                return []
        except Exception as e:
            logger.error(f"执行SQL查询时出错: {e}")
            return []
    
    def create_record(self, table: str, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a record synchronously.
        
        Args:
            table: Table name
            record_data: Record data to create
            
        Returns:
            Created record data or None on failure
        """
        try:
            if 'id' not in record_data:
                raise ValueError("记录数据必须包含'id'字段")
            
            record_id = record_data['id']
            full_id = f"{table}:{record_id}"
            url = f"{self.base_url}/key/{full_id}"
            
            # 处理特殊字段如time::now()
            processed_data = record_data.copy()
            for key, value in processed_data.items():
                if isinstance(value, str) and value == "time::now()":
                    processed_data[key] = get_current_time_iso()
            
            logger.info(f"创建记录: {full_id}")
            logger.info(f"记录数据: {processed_data}")
            
            response = requests.put(url, headers=self.headers, json=processed_data)
            status = response.status_code
            
            logger.info(f"创建记录响应码: {status}")
            
            if status == 200:
                logger.info(f"记录创建成功: {full_id}")
                return processed_data
            else:
                logger.error(f"记录创建失败: {status} {response.reason}")
                logger.error(f"响应内容: {response.text}")
                return None
        except Exception as e:
            logger.error(f"创建记录时出错: {e}")
            return None
    
    def update_record(self, table: str, record_id: str, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a record synchronously.
        
        Args:
            table: Table name
            record_id: Record ID to update
            record_data: Record data to update
            
        Returns:
            Updated record data or None on failure
        """
        try:
            full_id = f"{table}:{record_id}"
            url = f"{self.base_url}/key/{full_id}"
            
            # 处理特殊字段如time::now()
            processed_data = record_data.copy()
            for key, value in processed_data.items():
                if isinstance(value, str) and value == "time::now()":
                    processed_data[key] = get_current_time_iso()
            
            logger.info(f"更新记录: {full_id}")
            logger.info(f"更新数据: {processed_data}")
            
            response = requests.patch(url, headers=self.headers, json=processed_data)
            status = response.status_code
            
            logger.info(f"更新记录响应码: {status}")
            
            if status == 200:
                logger.info(f"记录更新成功: {full_id}")
                return processed_data
            else:
                logger.error(f"记录更新失败: {status} {response.reason}")
                logger.error(f"响应内容: {response.text}")
                return None
        except Exception as e:
            logger.error(f"更新记录时出错: {e}")
            return None
    
    def delete_record(self, table: str, record_id: str) -> bool:
        """
        Delete a record synchronously.
        
        Args:
            table: Table name
            record_id: Record ID to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            full_id = f"{table}:{record_id}"
            url = f"{self.base_url}/key/{full_id}"
            
            logger.info(f"删除记录: {full_id}")
            
            response = requests.delete(url, headers=self.headers)
            status = response.status_code
            
            logger.info(f"删除记录响应码: {status}")
            
            if status == 200:
                logger.info(f"记录删除成功: {full_id}")
                return True
            else:
                logger.error(f"记录删除失败: {status} {response.reason}")
                logger.error(f"响应内容: {response.text}")
                return False
        except Exception as e:
            logger.error(f"删除记录时出错: {e}")
            return False
    
    def get_record(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a record synchronously.
        
        Args:
            table: Table name
            record_id: Record ID to get
            
        Returns:
            Record data or None if not found or on error
        """
        try:
            full_id = f"{table}:{record_id}"
            url = f"{self.base_url}/key/{full_id}"
            
            logger.info(f"获取记录: {full_id}")
            
            response = requests.get(url, headers=self.headers)
            status = response.status_code
            
            logger.info(f"获取记录响应码: {status}")
            
            if status == 200:
                # Check if the response is empty or null
                if not response.text or response.text.strip() in ['null', '{}', '[]']:
                    logger.info(f"记录不存在: {full_id} (空响应)")
                    return None
                    
                result = response.json()
                logger.info(f"记录获取成功: {full_id}")
                logger.debug(f"原始响应内容: {result}")
                
                # Check if result is empty or None
                if result is None or (isinstance(result, dict) and not result):
                    logger.info(f"记录不存在: {full_id} (空结果)")
                    return None
                
                # 直接返回结果，跳过解析
                # SurrealDB HTTP API 通常直接返回记录，不需要额外解析
                if isinstance(result, dict):
                    logger.info(f"记录直接返回: {full_id}")
                    return result
                
                # 如果是列表，返回第一个元素
                if isinstance(result, list) and len(result) > 0:
                    logger.info(f"记录列表返回第一个: {full_id}")
                    return result[0]
                
                # 尝试解析响应（兼容旧代码）
                parsed_result = parse_surreal_response(result)
                if parsed_result and len(parsed_result) > 0:
                    logger.info(f"记录解析后返回: {full_id}")
                    return parsed_result[0]
                    
                logger.info(f"记录解析后为空: {full_id}")
                return None
            else:
                logger.error(f"记录获取失败: {status} {response.reason}")
                logger.error(f"响应内容: {response.text}")
                return None
        except Exception as e:
            logger.error(f"获取记录时出错: {e}")
            logger.exception(e)  # 打印完整的异常堆栈
            return None
    
    def get_records(self, table: str, condition: str = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get multiple records synchronously.
        
        Args:
            table: Table name
            condition: WHERE clause condition (without 'WHERE')
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of records or empty list on failure
        """
        try:
            # 构建SQL查询
            sql = build_select_query(table, condition, limit, offset)
            
            # 执行查询
            result = self.execute_sql(sql)
            
            # 如果直接查询失败，尝试使用参数化查询
            if not result and condition:
                logger.info(f"直接查询未返回数据，尝试参数化查询")
                
                # 解析条件为参数化查询
                conditions = {}
                if condition:
                    parts = condition.split(" AND ")
                    for part in parts:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # 移除值两侧的引号
                            if value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            
                            conditions[key] = value
                
                # 构建参数化查询
                param_sql, params = build_parameterized_select_query(table, conditions, limit, offset)
                
                # 执行参数化查询
                result = self.execute_sql(param_sql, params)
            
            # 如果参数化查询也失败，尝试使用备用查询
            if not result:
                logger.warning(f"参数化查询未返回数据，尝试使用备用查询方法")
                
                # 构建备用查询
                backup_sql = f"SELECT * FROM {table} LIMIT {limit} START {offset};"
                
                # 执行备用查询
                result = self.execute_sql(backup_sql)
            
            logger.info(f"获取记录成功: {table}, 条件: {condition}, 数量: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取记录失败: {e}")
            return []
    
    # ===== 异步方法 =====
    
    async def execute_sql_async_v_new(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query asynchronously.
        
        Args:
            sql: SQL query to execute
            params: Optional parameters for parameterized query
            
        Returns:
            List of records or empty list on failure
        """
        return await execute_sql_async(self.base_url, self.headers, sql, params)
    
    async def create_record_async(self, table: str, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a record asynchronously.
        
        Args:
            table: Table name
            record_data: Record data to create
            
        Returns:
            Created record data or None on failure
        """
        # 处理特殊字段如time::now()
        processed_data = record_data.copy()
        for key, value in processed_data.items():
            if isinstance(value, str) and value == "time::now()":
                processed_data[key] = get_current_time_iso()
        
        return await create_record_async(self.base_url, self.headers, table, processed_data)
    
    async def update_record_async(self, table: str, record_id: str, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a record asynchronously.
        
        Args:
            table: Table name
            record_id: Record ID to update
            record_data: Record data to update
            
        Returns:
            Updated record data or None on failure
        """
        # 处理特殊字段如time::now()
        processed_data = record_data.copy()
        for key, value in processed_data.items():
            if isinstance(value, str) and value == "time::now()":
                processed_data[key] = get_current_time_iso()
        
        return await update_record_async(self.base_url, self.headers, table, record_id, processed_data)
    
    async def delete_record_async(self, table: str, record_id: str) -> bool:
        """
        Delete a record asynchronously.
        
        Args:
            table: Table name
            record_id: Record ID to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        return await delete_record_async(self.base_url, self.headers, table, record_id)
    
    async def get_record_async(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a record asynchronously.
        
        Args:
            table: Table name
            record_id: Record ID to get
            
        Returns:
            Record data or None if not found or on error
        """
        return await get_record_async(self.base_url, self.headers, table, record_id)
    
    async def get_records_async(self, table: str, condition: str = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get multiple records asynchronously.
        
        Args:
            table: Table name
            condition: WHERE clause condition (without 'WHERE')
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of records or empty list on failure
        """
        try:
            # 构建SQL查询
            sql = build_select_query(table, condition, limit, offset)
            
            # 执行查询
            result = await self.execute_sql_async_v_new(sql)
            
            # 如果直接查询失败，尝试使用参数化查询
            if not result and condition:
                logger.info(f"直接查询未返回数据，尝试参数化查询")
                
                # 解析条件为参数化查询
                conditions = {}
                if condition:
                    parts = condition.split(" AND ")
                    for part in parts:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # 移除值两侧的引号
                            if value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            
                            conditions[key] = value
                
                # 构建参数化查询
                param_sql, params = build_parameterized_select_query(table, conditions, limit, offset)
                
                # 执行参数化查询
                result = await self.execute_sql_async_v_new(param_sql, params)
            
            # 如果参数化查询也失败，尝试使用备用查询
            if not result:
                logger.warning(f"参数化查询未返回数据，尝试使用备用查询方法")
                
                # 构建备用查询
                backup_sql = f"SELECT * FROM {table} LIMIT {limit} START {offset};"
                
                # 执行备用查询
                result = await self.execute_sql_async_v_new(backup_sql)
            
            logger.info(f"异步获取记录成功: {table}, 条件: {condition}, 数量: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"异步获取记录失败: {e}")
            return []
