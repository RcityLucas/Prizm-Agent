"""
Unified SurrealDB client using the official SurrealDB Python library.

This client provides a simple, reliable interface to SurrealDB using 
the official WebSocket-based connection and SQL queries, with HTTP fallback.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from surrealdb import Surreal
from contextlib import contextmanager
from datetime import datetime
import uuid
import asyncio
from .http_client import HTTPSurrealClient

logger = logging.getLogger(__name__)


class UnifiedSurrealClient:
    """
    Unified SurrealDB client using the official library.
    
    This client uses the proven approach from test_surreal_http.py:
    - WebSocket connection via official SurrealDB library
    - SQL queries using db.query() method
    - Simple, reliable operations without complex HTTP handling
    """
    
    def __init__(self, url: str, namespace: str, database: str, username: str, password: str):
        """
        Initialize the unified client.
        
        Args:
            url: SurrealDB WebSocket URL (e.g., ws://localhost:8000/rpc)
            namespace: SurrealDB namespace
            database: SurrealDB database name
            username: SurrealDB username
            password: SurrealDB password
        """
        # Convert HTTP URL to WebSocket URL if needed
        if url.startswith('http://'):
            self.ws_url = url.replace('http://', 'ws://') + '/rpc'
        elif url.startswith('https://'):
            self.ws_url = url.replace('https://', 'wss://') + '/rpc'
        elif url.startswith('ws://') or url.startswith('wss://'):
            self.ws_url = url
        else:
            # Assume it's a base URL without protocol
            self.ws_url = f"ws://{url}/rpc"
            
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        
        # Initialize HTTP client as fallback
        self.http_client = HTTPSurrealClient(url, namespace, database, username, password)
        
        # 创建持久连接
        self.persistent_db = None
        self._init_persistent_connection()
        
        logger.info(f"Unified SurrealDB client initialized: {self.ws_url}, {namespace}, {database}")
        
    def _init_persistent_connection(self):
        """
        初始化持久连接
        """
        try:
            logger.info(f"创建持久连接到SurrealDB: {self.ws_url}")
            self.persistent_db = Surreal(self.ws_url)
            self.persistent_db.signin({"username": self.username, "password": self.password})
            self.persistent_db.use(self.namespace, self.database)
            logger.info("SurrealDB持久连接创建成功")
        except Exception as e:
            logger.error(f"创建SurrealDB持久连接失败: {e}")
            self.persistent_db = None
            
    @contextmanager
    def get_async_connection(self):
        """
        Get a SurrealDB connection for async operations using context manager.
        
        This is similar to get_connection but for async usage.
        """
        db = None
        try:
            logger.info(f"Connecting to SurrealDB asynchronously at {self.ws_url}")
            db = Surreal(self.ws_url)
            logger.info(f"Signing in asynchronously with username: {self.username}")
            db.signin({"username": self.username, "password": self.password})
            logger.info(f"Using namespace: {self.namespace}, database: {self.database}")
            db.use(self.namespace, self.database)
            logger.info("SurrealDB async connection established successfully")
            yield db
        except Exception as e:
            logger.error(f"Async database connection error: {e}, type: {type(e)}")
            # Print more details about the error
            import traceback
            logger.error(f"Async connection error details: {traceback.format_exc()}")
            raise
        finally:
            if db:
                try:
                    db.close()
                    logger.info("SurrealDB async connection closed")
                except Exception as close_error:
                    logger.error(f"Failed to close async SurrealDB connection: {close_error}")
    
    @contextmanager
    def get_connection(self):
        """
        Get a SurrealDB connection using context manager.
        
        This follows the official pattern from test_surreal_http.py.
        """
        db = None
        try:
            logger.info(f"Connecting to SurrealDB at {self.ws_url}")
            db = Surreal(self.ws_url)
            logger.info(f"Signing in with username: {self.username}")
            db.signin({"username": self.username, "password": self.password})
            logger.info(f"Using namespace: {self.namespace}, database: {self.database}")
            db.use(self.namespace, self.database)
            logger.info("SurrealDB connection established successfully")
            yield db
        except Exception as e:
            logger.error(f"Database connection error: {e}, type: {type(e)}")
            # Print more details about the error
            import traceback
            logger.error(f"Connection error details: {traceback.format_exc()}")
            raise
        finally:
            if db:
                try:
                    db.close()
                    logger.info("SurrealDB connection closed")
                except Exception as close_error:
                    logger.warning(f"Error closing SurrealDB connection: {close_error}")
    
    def execute_sql(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query synchronously.
        
        Args:
            sql: SQL query to execute
            params: Optional parameters (not used in current implementation)
            
        Returns:
            List of records or empty list on failure
        """
        # 记录详细的查询信息，包括查询类型和条件
        if "WHERE" in sql:
            logger.info(f"执行带条件的SQL查询: {sql}")
            # 提取WHERE条件部分进行单独记录
            where_clause = sql.split("WHERE")[1].split("LIMIT")[0].strip()
            logger.info(f"WHERE条件: {where_clause}")
        else:
            logger.info(f"执行无条件的SQL查询: {sql}")
            
        # 最多重试3次
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # 优先使用持久连接执行查询
                if self.persistent_db:
                    try:
                        logger.debug(f"使用持久连接执行SQL: {sql}")
                        result = self.persistent_db.query(sql)
                        
                        if not result:
                            logger.warning(f"SQL查询返回空结果: {sql}")
                            return []
                        
                        # 转换SurrealDB对象为可序列化的Python类型
                        serializable_result = self._make_serializable(result)
                        
                        # 记录查询结果的详细信息
                        result_count = len(serializable_result)
                        logger.info(f"SQL查询成功返回 {result_count} 条记录")
                        
                        # 如果结果包含记录，记录第一条记录的关键字段用于调试
                        if result_count > 0:
                            sample_record = serializable_result[0]
                            # 检查记录类型，确保它是一个字典
                            if isinstance(sample_record, dict):
                                # 记录记录的ID和user_id字段（如果存在）
                                record_id = sample_record.get('id', 'unknown')
                                user_id = sample_record.get('user_id', 'not_present')
                                logger.info(f"样本记录 - ID: {record_id}, user_id: {user_id}")
                                
                                # 如果是带WHERE条件的查询，验证结果是否符合条件
                                if "WHERE" in sql and "user_id" in sql:
                                    logger.info(f"验证查询结果是否符合user_id条件")
                                    for i, record in enumerate(serializable_result[:5]):  # 只检查前5条记录
                                        if isinstance(record, dict):
                                            record_user_id = record.get('user_id', 'not_present')
                                            logger.info(f"记录 {i+1} - user_id: {record_user_id}")
                            else:
                                # 如果不是字典，记录实际类型
                                logger.info(f"样本记录不是字典，而是 {type(sample_record).__name__}: {sample_record}")
                        
                        return serializable_result
                    except Exception as e:
                        if "Cannot operate on a closed database" in str(e):
                            logger.warning(f"持久连接已关闭，尝试重新连接 (重试 {retry_count+1}/{max_retries}): {e}")
                            # 重新初始化持久连接
                            self._init_persistent_connection()
                            retry_count += 1
                            last_error = e
                            continue
                        else:
                            logger.warning(f"持久连接执行SQL失败: {e}，尝试临时连接")
                
                # 如果持久连接不可用或执行失败，使用临时连接
                with self.get_connection() as db:
                    logger.debug(f"使用临时连接执行SQL: {sql}")
                    result = db.query(sql)
                    
                    if not result:
                        logger.warning(f"SQL查询返回空结果: {sql}")
                        return []
                    
                    # 转换SurrealDB对象为可序列化的Python类型
                    serializable_result = self._make_serializable(result)
                    
                    # 记录查询结果的详细信息
                    result_count = len(serializable_result)
                    logger.info(f"SQL查询(临时连接)成功返回 {result_count} 条记录")
                    
                    # 如果结果包含记录，记录第一条记录的关键字段用于调试
                    if result_count > 0:
                        sample_record = serializable_result[0]
                        # 检查记录类型，确保它是一个字典
                        if isinstance(sample_record, dict):
                            # 记录记录的ID和user_id字段（如果存在）
                            record_id = sample_record.get('id', 'unknown')
                            user_id = sample_record.get('user_id', 'not_present')
                            logger.info(f"样本记录(临时连接) - ID: {record_id}, user_id: {user_id}")
                        else:
                            # 如果不是字典，记录实际类型
                            logger.info(f"样本记录(临时连接)不是字典，而是 {type(sample_record).__name__}: {sample_record}")
                    
                    return serializable_result
                    
            except Exception as e:
                if "Cannot operate on a closed database" in str(e):
                    logger.warning(f"数据库连接已关闭，尝试重新连接 (重试 {retry_count+1}/{max_retries}): {e}")
                    # 重新初始化持久连接
                    self._init_persistent_connection()
                    retry_count += 1
                    last_error = e
                else:
                    # 如果WebSocket失败，尝试HTTP回退
                    logger.warning(f"WebSocket查询失败，尝试HTTP回退: {e}")
                    try:
                        result = self.http_client.execute_sql(sql)
                        logger.info(f"HTTP回退查询成功返回 {len(result)} 条记录")
                        return result
                    except Exception as http_error:
                        logger.error(f"HTTP回退也失败了: {http_error}")
                        last_error = http_error
                        retry_count += 1
        
        # 如果所有重试都失败
        if last_error:
            logger.error(f"在 {max_retries} 次重试后执行SQL仍然失败: {last_error}")
            raise last_error
    
    def create_record(self, table: str, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a record using direct db.create() method.
        
        Args:
            table: Table name
            record_data: Record data to create
            
        Returns:
            Created record or None on failure
        """
        try:
            # Generate ID if not provided
            if 'id' not in record_data:
                record_data['id'] = str(uuid.uuid4())
                
            # Handle special time::now() values and ensure proper datetime handling
            processed_data = {}
            for key, value in record_data.items():
                if isinstance(value, str) and value == 'time::now()':
                    # Use Python's datetime for time::now()
                    from datetime import datetime
                    # For SurrealDB, use datetime object directly instead of string
                    processed_data[key] = datetime.now()
                else:
                    processed_data[key] = value
            
            # 特别检查嵌入向量字段，确保它被正确处理
            if 'embedding' in processed_data:
                embedding_data = processed_data['embedding']
                logger.info(f"Embedding data type: {type(embedding_data)}, length: {len(embedding_data) if isinstance(embedding_data, list) else 'not a list'}, first few values: {embedding_data[:5] if isinstance(embedding_data, list) and len(embedding_data) > 0 else 'empty or not a list'}")
                
                # 如果嵌入向量是空列表，保持为空列表，与 simpleChat_with_vectors.py 保持一致
                if isinstance(embedding_data, list) and len(embedding_data) == 0:
                    logger.info("Empty embedding list detected, keeping as empty list [] for SurrealDB compatibility")
                    # 不做任何修改，保持为空列表
                    
                # 如果嵌入向量是非空列表，确保它被正确处理
                elif isinstance(embedding_data, list) and len(embedding_data) > 0:
                    # 确保所有元素都是浮点数，避免类型问题
                    processed_data['embedding'] = [float(x) for x in embedding_data]
                    logger.info(f"Processed embedding to ensure all elements are floats, length: {len(processed_data['embedding'])}, first few: {processed_data['embedding'][:5]}")
                elif not isinstance(embedding_data, list) and embedding_data is not None:
                    # 如果不是列表但也不是None，尝试转换为列表
                    try:
                        processed_data['embedding'] = list(embedding_data)
                        logger.info(f"Converted non-list embedding to list: {len(processed_data['embedding'])} elements")
                    except Exception as e:
                        logger.error(f"Failed to convert embedding to list: {e}, keeping original")
                elif embedding_data is None:
                    # 如果是None，初始化为空列表
                    processed_data['embedding'] = []
                    logger.info("None embedding detected, initializing as empty list []")
            
            logger.info(f"Creating record in {table} with data keys: {list(processed_data.keys())}")
            
            # 不再使用 SQL INSERT，直接使用 db.create 方法
            # 这部分代码已被上面的代码替代，删除重复的处理逻辑
            # 确保嵌入向量数据已经在上面的代码块中正确处理
            with self.get_connection() as db:
                try:
                    # Use the create method directly
                    result = db.create(table, processed_data)
                    
                    if result and len(result) > 0:
                        logger.info(f"Record created successfully in {table}: {processed_data.get('id')}")
                        created_record = self._make_serializable(result[0] if isinstance(result, list) else result)
                        
                        # 检查返回的记录中是否包含嵌入向量
                        if 'embedding' in processed_data and 'embedding' in created_record:
                            logger.info(f"Embedding in created record: type={type(created_record['embedding'])}, length={len(created_record['embedding']) if isinstance(created_record['embedding'], list) else 'not a list'}")
                        else:
                            logger.warning(f"Embedding field missing in created record. Original had embedding: {'embedding' in processed_data}, Created has embedding: {'embedding' in created_record}")
                            
                        return created_record
                    else:
                        logger.warning(f"Create returned empty result for {table}")
                        # Try to verify if record was created
                        verify_result = db.select(f"{table}:{processed_data.get('id')}")
                        if verify_result and len(verify_result) > 0:
                            logger.info(f"Record verified in {table}: {processed_data.get('id')}")
                            verified_record = self._make_serializable(verify_result[0] if isinstance(verify_result, list) else verify_result)
                            
                            # 检查验证的记录中是否包含嵌入向量
                            if 'embedding' in processed_data and 'embedding' in verified_record:
                                logger.info(f"Embedding in verified record: type={type(verified_record['embedding'])}, length={len(verified_record['embedding']) if isinstance(verified_record['embedding'], list) else 'not a list'}")
                            else:
                                logger.warning(f"Embedding field missing in verified record. Original had embedding: {'embedding' in processed_data}, Verified has embedding: {'embedding' in verified_record}")
                                
                            return verified_record
                        else:
                            logger.error(f"Failed to create record in {table}")
                            return None
                except Exception as create_error:
                    logger.error(f"Error during db.create: {create_error}")
                    import traceback
                    logger.error(f"Create error details: {traceback.format_exc()}")
                    return None
        except Exception as e:
            logger.error(f"Create record failed: {e}, table: {table}, record_id: {record_data.get('id')}")
            import traceback
            logger.error(f"Create record error details: {traceback.format_exc()}")
            return None
    
    def get_records(self, table: str, condition: str = "", limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get records from a table.
        
        Args:
            table: Table name
            condition: WHERE condition (optional)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of records
        """
        try:
            # Sanitize table name to prevent SQL injection
            table = table.strip('`').replace('`', '')
            
            # Build the SQL query
            sql = f"SELECT * FROM `{table}`"
            
            # Add WHERE clause if condition is provided
            if condition and condition.strip():
                # Log the condition for debugging
                logger.info(f"Filtering records with condition: {condition}")
                sql += f" WHERE {condition}"
            else:
                logger.info(f"No condition provided, returning all records from {table}")
            
            # Add LIMIT clause
            sql += f" LIMIT {limit}"
            
            # Add offset if provided
            if offset > 0:
                sql += f" START {offset}"
            
            sql += ";"
            
            # Log the full SQL query for debugging
            logger.info(f"Executing SQL query: {sql}")
            
            # Execute the query
            result = self.execute_sql(sql)
            logger.info(f"Query returned {len(result)} records")
            return result
            
        except Exception as e:
            logger.warning(f"WebSocket get records failed, trying HTTP fallback: {e}")
            return self.http_client.get_records(table, condition, limit, offset)
    
    def update_record(self, table: str, record_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a record using SQL UPDATE.
        
        Args:
            table: Table name
            record_id: Record ID to update
            update_data: Data to update
            
        Returns:
            Updated record or None on failure
        """
        try:
            # Build SET clause
            set_clauses = []
            
            for key, value in update_data.items():
                if isinstance(value, str):
                    escaped_value = value.replace("'", "''")
                    set_clauses.append(f"{key} = '{escaped_value}'")
                elif isinstance(value, (int, float)):
                    set_clauses.append(f"{key} = {value}")
                elif isinstance(value, bool):
                    set_clauses.append(f"{key} = {'true' if value else 'false'}")
                elif value is None:
                    set_clauses.append(f"{key} = NULL")
                else:
                    import json
                    json_str = json.dumps(value).replace("'", "''")
                    set_clauses.append(f"{key} = '{json_str}'")
            
            set_clause = ', '.join(set_clauses)
            sql = f"UPDATE {table} SET {set_clause} WHERE id = '{record_id}'; SELECT * FROM {table} WHERE id = '{record_id}';"
            
            result = self.execute_sql(sql)
            
            if result:
                logger.info(f"Record updated successfully in {table}: {record_id}")
                return result[0] if result else None
            else:
                logger.error(f"Failed to update record in {table}: {record_id}")
                return None
                
        except Exception as e:
            logger.error(f"Update record failed: {e}")
            return None
    
    async def execute_sql_async(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query asynchronously.
        
        Args:
            sql: SQL query to execute
            params: Optional parameters (not used in current implementation)
            
        Returns:
            List of records or empty list on failure
        """
        logger.debug(f"使用持久连接执行SQL: {sql}")
        try:
            # 使用持久连接执行SQL (sync for now, will be wrapped in async executor)
            if self.persistent_db is None:
                self._init_persistent_connection()
                if self.persistent_db is None:
                    logger.error("持久连接不可用，无法执行异步SQL查询")
                    return []
            
            # Execute query in a separate thread to not block the async event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.persistent_db.query(sql))
            
            # Extract result data
            if not result:
                logger.warning(f"SQL查询返回空结果: {sql}")
                return []
                
            # Try to extract records from the result
            if hasattr(result, 'result'):
                records = result.result
            elif isinstance(result, list):
                records = result
            else:
                logger.warning(f"SQL查询结果格式异常: {type(result)}")
                return []
                
            # Convert SurrealDB objects to serializable Python types
            serializable_records = self._make_serializable(records)
            
            logger.debug(f"异步SQL执行成功，返回结果数: {len(serializable_records)}")
            return serializable_records
            
        except Exception as e:
            logger.error(f"执行异步SQL查询失败: {sql}, 错误: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
            
    def delete_record(self, table: str, record_id: str) -> bool:
        """
        Delete a record using SQL DELETE.
        
        Args:
            table: Table name
            record_id: Record ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # 准备不同格式的记录ID进行尝试
            original_id = record_id
            prefixed_id = f"{table}:{record_id}" if not record_id.startswith(f"{table}:") else record_id
            raw_id = record_id.split(":")[-1] if ":" in record_id else record_id
            
            logger.info(f"Attempting to delete record with multiple ID formats:")
            logger.info(f"  - Original ID: {original_id}")
            logger.info(f"  - Prefixed ID: {prefixed_id}")
            logger.info(f"  - Raw ID: {raw_id}")
            
            # 列出所有会话记录，查找匹配的ID
            list_sql = f"SELECT * FROM {table} LIMIT 100;"
            logger.info(f"[LIST] Executing SQL: {list_sql}")
            all_records = self.execute_sql(list_sql)
            logger.info(f"Found {len(all_records) if all_records else 0} records in {table}")
            
            # 查找匹配的记录
            matching_records = []
            
            if all_records:
                for record in all_records:
                    # 检查嵌套ID结构
                    nested_id = record.get('id', {})
                    if isinstance(nested_id, dict):
                        # 处理嵌套ID结构：{'table_name': 'sessions', 'id': 'xxxx'}
                        record_raw_id = nested_id.get('id', '')
                        if record_raw_id == raw_id or raw_id in record_raw_id:
                            logger.info(f"Found matching record with nested ID: {record}")
                            matching_records.append(record)
                    elif isinstance(nested_id, str):
                        # 处理字符串ID
                        if raw_id in nested_id:
                            logger.info(f"Found matching record with string ID: {record}")
                            matching_records.append(record)
            
            if not matching_records:
                logger.warning(f"No matching records found in {table} for ID {record_id}")
                return False
            
            logger.info(f"Found {len(matching_records)} matching records")
            
            # 尝试删除所有匹配的记录
            success = False
            for record in matching_records:
                # 获取记录的完整ID
                nested_id = record.get('id', {})
                
                if isinstance(nested_id, dict):
                    # 处理嵌套ID结构
                    record_table = nested_id.get('table_name', table)
                    record_id_value = nested_id.get('id', '')
                    
                    # 尝试使用嵌套ID结构进行删除
                    delete_sql1 = f"DELETE FROM {record_table} WHERE id.id = '{record_id_value}';"
                    logger.info(f"[DELETE NESTED ID] Executing SQL: {delete_sql1}")
                    self.execute_sql(delete_sql1)
                    
                    # 尝试使用完整对象进行删除
                    delete_sql2 = f"DELETE FROM {record_table} WHERE id = {{\"table_name\": \"{record_table}\", \"id\": \"{record_id_value}\"}};"
                    logger.info(f"[DELETE OBJECT ID] Executing SQL: {delete_sql2}")
                    try:
                        self.execute_sql(delete_sql2)
                    except Exception as e:
                        logger.warning(f"Object ID deletion failed (expected): {e}")
                    
                    # 尝试使用记录的完整ID进行删除
                    full_id = f"{record_table}:{record_id_value}"
                    delete_sql3 = f"DELETE {full_id};"
                    logger.info(f"[DELETE FULL ID] Executing SQL: {delete_sql3}")
                    self.execute_sql(delete_sql3)
                    
                elif isinstance(nested_id, str):
                    # 处理字符串ID
                    delete_sql = f"DELETE FROM {table} WHERE id = '{nested_id}';"
                    logger.info(f"[DELETE STRING ID] Executing SQL: {delete_sql}")
                    self.execute_sql(delete_sql)
                    
                    # 直接删除
                    delete_sql2 = f"DELETE {nested_id};"
                    logger.info(f"[DELETE DIRECT] Executing SQL: {delete_sql2}")
                    self.execute_sql(delete_sql2)
                
                # 验证删除结果
                if isinstance(nested_id, dict):
                    record_id_value = nested_id.get('id', '')
                    verify_sql = f"SELECT * FROM {table} WHERE id.id = '{record_id_value}';"
                elif isinstance(nested_id, str):
                    verify_sql = f"SELECT * FROM {table} WHERE id = '{nested_id}';"
                else:
                    continue
                    
                logger.info(f"[VERIFY] Executing SQL: {verify_sql}")
                verify_result = self.execute_sql(verify_sql)
                
                if not verify_result or len(verify_result) == 0:
                    logger.info(f"Successfully deleted record: {record}")
                    success = True
                else:
                    logger.warning(f"Failed to delete record: {record}")
            
            # 最后再次验证是否还有匹配的记录
            final_verify_sql = f"SELECT * FROM {table} WHERE id.id = '{raw_id}';"
            logger.info(f"[FINAL VERIFY] Executing SQL: {final_verify_sql}")
            final_result = self.execute_sql(final_verify_sql)
            
            if final_result and len(final_result) > 0:
                logger.warning(f"Records still exist after deletion attempts: {final_result}")
                success = False
            else:
                logger.info(f"No matching records found after deletion")
                success = True
            
            return success
            
        except Exception as e:
            logger.error(f"Delete record failed: {e}")
            return False
    
    def ensure_table_exists(self, table: str) -> bool:
        """
        Ensure a table exists without specifying fields.
        This is a simpler version that just makes sure the table can be used.
        
        Args:
            table: Table name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First check if table exists by querying it
            check_sql = f"SELECT count() FROM {table} LIMIT 1;"
            try:
                self.execute_sql(check_sql)
                # If we get here, table exists
                logger.info(f"Table {table} already exists")
                return True
            except Exception as check_error:
                # Table might not exist, try to create it
                logger.info(f"Table {table} might not exist, creating it: {check_error}")
                pass
            
            # Create table with minimal definition if it doesn't exist
            create_sql = f"DEFINE TABLE {table} SCHEMAFULL;"
            self.execute_sql(create_sql)
            logger.info(f"Table {table} created successfully")
            return True
        except Exception as e:
            logger.error(f"Ensure table exists failed for {table}: {e}")
            return False

    def _make_serializable(self, data: Any) -> Any:
        """
        Convert SurrealDB objects to serializable Python types.
        
        Args:
            data: The data to convert
            
        Returns:
            JSON serializable data
        """
        if data is None:
            return None
            
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = self._make_serializable(value)
            return result
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        elif hasattr(data, 'table_name') and hasattr(data, 'record_id'):
            # Handle SurrealDB RecordID objects
            return f"{data.table_name}:{data.record_id}"
        elif hasattr(data, '__dict__'):
            # Handle other objects with __dict__
            return self._make_serializable(data.__dict__)
        else:
            # Return primitive types as is
            # 记录非标准类型的数据
            if not isinstance(data, (str, int, float, bool)):
                logger.debug(f"非标准数据类型: {type(data).__name__}")
            return data
    
    def ensure_table(self, table: str, fields: Dict[str, str]) -> bool:
        """
        Ensure a table exists with the specified fields.
        
        Args:
            table: Table name
            fields: Dictionary of field_name -> field_type
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First ensure table exists
            self.ensure_table_exists(table)
            
            # Then define fields
            sql_statements = []
            
            for field_name, field_type in fields.items():
                sql_statements.append(f"DEFINE FIELD {field_name} ON {table} TYPE {field_type};")
            
            if sql_statements:
                sql = " ".join(sql_statements)
                self.execute_sql(sql)
                
            logger.info(f"Table {table} ensured with fields: {fields}")
            return True
            
        except Exception as e:
            logger.error(f"Ensure table failed: {e}")
            return False