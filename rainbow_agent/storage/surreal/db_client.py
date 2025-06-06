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
from .sql_builder import (
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
        
        # Generate authentication headers
        self.headers = get_auth_headers(username, password, namespace, database)
        
        logger.info(f"SurrealDB HTTP client initialized: {url}, {namespace}, {database}")
    
    # ===== Synchronous Methods =====
    
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
            
            # Prepare request payload
            payload = {'query': sql}
            if params:
                payload['vars'] = params
                
            logger.info(f"Executing SQL: {sql}")
            if params:
                logger.info(f"Parameters: {params}")
                
            response = requests.post(url, headers=self.headers, json=payload)
            status = response.status_code
            
            logger.info(f"SQL query response code: {status}")
            
            if status == 200:
                result = response.json()
                logger.info(f"SQL query executed successfully: {sql}")
                
                # Parse response
                parsed_result = parse_surreal_response(result)
                return parsed_result  # Already returns empty list if parsing fails
            else:
                logger.error(f"SQL query failed: {status} {response.reason}")
                logger.error(f"Response content: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return []
    
    def create_record(self, table: str, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a record synchronously using parameterized SQL.
        
        Args:
            table: Table name
            record_data: Record data to create
            
        Returns:
            Created record data or None on failure
        """
        try:
            # Process special fields like time::now()
            processed_data = record_data.copy()
            for key, value in processed_data.items():
                if isinstance(value, str) and value == "time::now()":
                    processed_data[key] = get_current_time_iso()
            
            # Build parameterized SQL query
            sql, params = build_insert_query(table, processed_data)
            
            logger.info(f"Creating record in {table} with ID: {processed_data.get('id', 'auto-generated')}")
            
            # Execute the SQL query
            result = self.execute_sql(sql, params)
            
            if result and len(result) > 0:
                logger.info(f"Record created successfully in {table}")
                return result[0]
            else:
                logger.warning(f"No result returned after record creation in {table}")
                # Fallback to returning the processed data
                return processed_data
        except Exception as e:
            logger.error(f"Error creating record: {e}")
            return None
    
    def update_record(self, table: str, record_id: str, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a record synchronously using parameterized SQL.
        
        Args:
            table: Table name
            record_id: Record ID to update
            record_data: Record data to update
            
        Returns:
            Updated record data or None on failure
        """
        try:
            # Process special fields like time::now()
            processed_data = record_data.copy()
            for key, value in processed_data.items():
                if isinstance(value, str) and value == "time::now()":
                    processed_data[key] = get_current_time_iso()
            
            # Build parameterized SQL query
            sql, params = build_update_query(table, record_id, processed_data)
            
            logger.info(f"Updating record {table}:{record_id}")
            
            # Execute the SQL query
            result = self.execute_sql(sql, params)
            
            # Also fetch the updated record to return the complete state
            fetch_sql = f"SELECT * FROM {table}:{record_id};"
            updated_record = self.execute_sql(fetch_sql)
            
            if updated_record and len(updated_record) > 0:
                logger.info(f"Record {table}:{record_id} updated successfully")
                return updated_record[0]
            else:
                logger.warning(f"Record {table}:{record_id} not found after update")
                # Fallback to returning the processed data
                return processed_data
        except Exception as e:
            logger.error(f"Error updating record: {e}")
            return None
    
    def delete_record(self, table: str, record_id: str) -> bool:
        """
        Delete a record synchronously using parameterized SQL.
        
        Args:
            table: Table name
            record_id: Record ID to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Build SQL query
            sql = build_delete_query(table, record_id)
            
            logger.info(f"Deleting record {table}:{record_id}")
            
            # Execute the SQL query
            self.execute_sql(sql)
            
            # Verify deletion by trying to fetch the record
            fetch_sql = f"SELECT * FROM {table}:{record_id};"
            result = self.execute_sql(fetch_sql)
            
            if not result:
                logger.info(f"Record {table}:{record_id} deleted successfully")
                return True
            else:
                logger.warning(f"Record {table}:{record_id} may not have been deleted")
                return False
        except Exception as e:
            logger.error(f"Error deleting record: {e}")
            return False
    
    def get_record(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a record synchronously using parameterized SQL.
        
        Args:
            table: Table name
            record_id: Record ID to get
            
        Returns:
            Record data or None if not found or on error
        """
        try:
            # Build SQL query to fetch a specific record by ID
            sql = f"SELECT * FROM {table}:{record_id};"
            
            logger.info(f"Getting record {table}:{record_id}")
            
            # Execute the SQL query
            result = self.execute_sql(sql)
            
            # Check if we got any results
            if result and len(result) > 0:
                logger.info(f"Record {table}:{record_id} retrieved successfully")
                return result[0]  # Return the first (and should be only) result
            else:
                logger.info(f"Record {table}:{record_id} not found")
                return None
        except Exception as e:
            logger.error(f"Error getting record: {e}")
            logger.exception(e)  # Print full exception stack
            return None
            
    def get_records(self, table: str, condition: str = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get multiple records synchronously using parameterized SQL.
        
        Args:
            table: Table name
            condition: WHERE clause condition (without 'WHERE')
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of records or empty list on failure
        """
        try:
            # If we have a condition, try to parse it into a parameterized query
            if condition:
                # Parse condition into parameters
                conditions = {}
                parts = condition.split(" AND ")
                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes from the value if present
                        if value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        conditions[key] = value
                
                # Build and execute parameterized query
                sql, params = build_parameterized_select_query(table, conditions, limit, offset)
                logger.info(f"Getting records from {table} with conditions: {conditions}")
                result = self.execute_sql(sql, params)
            else:
                # No condition, use simple select query
                sql = build_select_query(table, None, limit, offset)
                logger.info(f"Getting all records from {table} (limit: {limit}, offset: {offset})")
                result = self.execute_sql(sql)
            
            logger.info(f"Retrieved {len(result)} records from {table}")
            return result
        except Exception as e:
            logger.error(f"Error getting records: {e}")
            return []
    
    # ===== Asynchronous Methods =====
    
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
        Get multiple records asynchronously using parameterized SQL.
        
        Args:
            table: Table name
            condition: WHERE clause condition (without 'WHERE')
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of records or empty list on failure
        """
        try:
            # If we have a condition, try to parse it into a parameterized query
            if condition:
                # Parse condition into parameters
                conditions = {}
                parts = condition.split(" AND ")
                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes from the value if present
                        if value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        conditions[key] = value
                
                # Build and execute parameterized query
                sql, params = build_parameterized_select_query(table, conditions, limit, offset)
                logger.info(f"Getting records asynchronously from {table} with conditions: {conditions}")
                result = await self.execute_sql_async_v_new(sql, params)
            else:
                # No condition, use simple select query
                sql = build_select_query(table, None, limit, offset)
                logger.info(f"Getting all records asynchronously from {table} (limit: {limit}, offset: {offset})")
                result = await self.execute_sql_async_v_new(sql)
            
            logger.info(f"Retrieved {len(result)} records asynchronously from {table}")
            return result
        except Exception as e:
            logger.error(f"Error getting records asynchronously: {e}")
            return []
