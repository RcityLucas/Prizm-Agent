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
        
        logger.info(f"Unified SurrealDB client initialized: {self.ws_url}, {namespace}, {database}")
    
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
        try:
            # Try WebSocket connection first
            with self.get_connection() as db:
                logger.info(f"Executing SQL: {sql}")
                try:
                    result = db.query(sql)
                    
                    # Parse the result - SurrealDB returns a list of result objects
                    if not result:
                        logger.warning(f"SQL query returned empty result: {sql}")
                        return []
                    
                    # Extract actual data from result
                    records = []
                    for result_item in result:
                        if hasattr(result_item, 'result') and result_item.result:
                            if isinstance(result_item.result, list):
                                records.extend(result_item.result)
                            else:
                                records.append(result_item.result)
                    
                    logger.info(f"SQL query returned {len(records)} records")
                except Exception as query_error:
                    logger.error(f"SQL query execution error: {query_error}, SQL: {sql}")
                    raise query_error
                return records
                
        except Exception as e:
            logger.warning(f"WebSocket SQL execution failed, trying HTTP fallback: {e}")
            # Fallback to HTTP client
            return self.http_client.execute_sql(sql, params)
    
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
            
            logger.info(f"Creating record in {table} with data: {processed_data}")
            
            # Use direct create method like in test_surreal_http.py
            with self.get_connection() as db:
                try:
                    # Use the create method directly
                    result = db.create(table, processed_data)
                    
                    if result and len(result) > 0:
                        logger.info(f"Record created successfully in {table}: {processed_data.get('id')}")
                        return self._make_serializable(result[0] if isinstance(result, list) else result)
                    else:
                        logger.warning(f"Create returned empty result for {table}")
                        # Try to verify if record was created
                        verify_result = db.select(f"{table}:{processed_data.get('id')}")
                        if verify_result and len(verify_result) > 0:
                            logger.info(f"Record verified in {table}: {processed_data.get('id')}")
                            return self._make_serializable(verify_result[0] if isinstance(verify_result, list) else verify_result)
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
            sql = f"SELECT * FROM {table}"
            
            if condition:
                sql += f" WHERE {condition}"
            
            sql += f" LIMIT {limit}"
            
            if offset > 0:
                sql += f" START {offset}"
            
            sql += ";"
            
            return self.execute_sql(sql)
            
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
            sql = f"DELETE FROM {table} WHERE id = '{record_id}';"
            
            result = self.execute_sql(sql)
            
            logger.info(f"Record deleted successfully from {table}: {record_id}")
            return True
            
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