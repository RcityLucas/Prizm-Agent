"""
HTTP-based SurrealDB client.

This client provides a simple HTTP interface to SurrealDB using
REST API calls. It serves as a fallback mechanism when WebSocket
connections are not available or fail.
"""

import logging
import requests
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class HTTPSurrealClient:
    """
    HTTP-based SurrealDB client.
    
    This client uses direct HTTP calls to interact with SurrealDB's REST API.
    It's designed as a fallback mechanism for the WebSocket-based client.
    """
    
    def __init__(self, url: str, namespace: str, database: str, username: str, password: str):
        """
        Initialize the HTTP client.
        
        Args:
            url: SurrealDB HTTP URL (e.g., http://localhost:8000)
            namespace: SurrealDB namespace
            database: SurrealDB database name
            username: SurrealDB username
            password: SurrealDB password
        """
        # Ensure URL has proper format
        if url.startswith('ws://'):
            self.http_url = url.replace('ws://', 'http://')
        elif url.startswith('wss://'):
            self.http_url = url.replace('wss://', 'https://')
        elif url.startswith('http://') or url.startswith('https://'):
            self.http_url = url
        else:
            # Assume it's a base URL without protocol
            self.http_url = f"http://{url}"
            
        # Remove /rpc suffix if present
        self.http_url = self.http_url.replace('/rpc', '')
        
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        
        # Create session with authentication
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({
            'Accept': 'application/json',
            'NS': namespace,
            'DB': database
        })
        
        logger.info(f"HTTP SurrealDB client initialized: {self.http_url}, {namespace}, {database}")
    
    def execute_sql(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query via HTTP.
        
        Args:
            sql: SQL query to execute
            params: Optional parameters for the query
            
        Returns:
            List of records or empty list on failure
        """
        try:
            url = f"{self.http_url}/sql"
            logger.info(f"Executing SQL via HTTP: {sql}")
            
            response = self.session.post(
                url, 
                data=sql,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                logger.error(f"HTTP SQL execution failed: {response.status_code}, {response.text}")
                return []
                
            result = response.json()
            
            # SurrealDB returns a list of results for each SQL statement
            if isinstance(result, list) and len(result) > 0:
                # Check for errors
                if 'status' in result[0] and result[0]['status'] != 'OK':
                    logger.error(f"SQL execution returned error: {result}")
                    return []
                
                # Return the result array if available
                if 'result' in result[0]:
                    return result[0]['result']
            
            return []
            
        except Exception as e:
            logger.error(f"HTTP SQL execution error: {e}")
            return []
    
    def create_record(self, table: str, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a record using HTTP POST.
        
        Args:
            table: Table name
            record_data: Record data to create
            
        Returns:
            Created record or None on failure
        """
        try:
            url = f"{self.http_url}/key/{table}"
            logger.info(f"Creating record via HTTP in table {table}")
            
            response = self.session.post(
                url,
                json=record_data
            )
            
            if response.status_code not in (200, 201):
                logger.error(f"HTTP create record failed: {response.status_code}, {response.text}")
                return None
                
            result = response.json()
            
            # SurrealDB typically returns the created record
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            
            return None
            
        except Exception as e:
            logger.error(f"HTTP create record error: {e}")
            return None
    
    def get_records(self, table: str, condition: str = "", limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get records from a table using HTTP GET.
        
        Args:
            table: Table name
            condition: WHERE condition (optional)
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of records
        """
        try:
            # Build SQL query
            sql = f"SELECT * FROM {table}"
            if condition:
                sql += f" WHERE {condition}"
            sql += f" LIMIT {limit} START {offset};"
            
            # Use execute_sql to run the query
            return self.execute_sql(sql)
            
        except Exception as e:
            logger.error(f"HTTP get records error: {e}")
            return []
    
    def update_record(self, table: str, record_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a record using HTTP PUT/PATCH.
        
        Args:
            table: Table name
            record_id: Record ID to update
            update_data: Data to update
            
        Returns:
            Updated record or None on failure
        """
        try:
            url = f"{self.http_url}/key/{table}/{record_id}"
            logger.info(f"Updating record via HTTP: {table}:{record_id}")
            
            response = self.session.patch(
                url,
                json=update_data
            )
            
            if response.status_code != 200:
                logger.error(f"HTTP update record failed: {response.status_code}, {response.text}")
                return None
                
            result = response.json()
            
            # SurrealDB typically returns the updated record
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            
            return None
            
        except Exception as e:
            logger.error(f"HTTP update record error: {e}")
            return None
    
    def delete_record(self, table: str, record_id: str) -> bool:
        """
        Delete a record using HTTP DELETE.
        
        Args:
            table: Table name
            record_id: Record ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.http_url}/key/{table}/{record_id}"
            logger.info(f"Deleting record via HTTP: {table}:{record_id}")
            
            response = self.session.delete(url)
            
            if response.status_code != 200:
                logger.error(f"HTTP delete record failed: {response.status_code}, {response.text}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"HTTP delete record error: {e}")
            return False
    
    def ensure_table_exists(self, table: str) -> bool:
        """
        Ensure a table exists via SQL.
        
        Args:
            table: Table name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create table with minimal definition if it doesn't exist
            create_sql = f"DEFINE TABLE {table} SCHEMAFULL;"
            self.execute_sql(create_sql)
            logger.info(f"Table {table} ensured via HTTP")
            return True
        except Exception as e:
            logger.error(f"HTTP ensure table exists failed: {e}")
            return False
