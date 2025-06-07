"""
HTTP-based SurrealDB client as fallback for WebSocket issues.

This client uses HTTP API which is working correctly.
"""

import logging
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class HTTPSurrealClient:
    """
    HTTP-based SurrealDB client.
    
    Uses the working HTTP API instead of problematic WebSocket connection.
    """
    
    def __init__(self, base_url: str, namespace: str, database: str, username: str, password: str):
        """Initialize HTTP client."""
        self.base_url = base_url.replace('ws://', 'http://').replace('/rpc', '')
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        
        logger.info(f"HTTP SurrealDB client initialized: {self.base_url}, {namespace}, {database}")
    
    def execute_sql(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute SQL query via HTTP API."""
        try:
            # Add USE statement at the beginning
            full_sql = f"USE NS {self.namespace} DB {self.database}; {sql}"
            
            response = requests.post(
                f"{self.base_url}/sql",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                auth=(self.username, self.password),
                json={"sql": full_sql},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"SQL query successful: {sql}")
                
                # Extract records from result
                records = []
                for item in result:
                    if item.get('status') == 'OK':
                        # If there's a result field, use it
                        if 'result' in item and item['result'] is not None:
                            if isinstance(item['result'], list):
                                records.extend(item['result'])
                            elif isinstance(item['result'], dict):
                                records.append(item['result'])
                        # If there's no explicit result field but there are other fields (like ID), use the item itself
                        elif any(key not in ['status', 'time', 'sql'] for key in item.keys()):
                            # This appears to be a record itself
                            clean_record = {k: v for k, v in item.items() if k not in ['status', 'time', 'sql']}
                            if clean_record:
                                records.append(clean_record)
                
                return records
            else:
                logger.error(f"SQL query failed: {response.status_code} {response.text}")
                return []
        
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return []
    
    def create_record(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a record in the specified table."""
        try:
            record_id = data.get('id', str(uuid.uuid4()).replace('-', ''))
            
            # Build SET clause
            set_clauses = []
            for key, value in data.items():
                if key != 'id':
                    if isinstance(value, str) and value == 'time::now()':
                        set_clauses.append(f"{key} = time::now()")
                    elif isinstance(value, str):
                        set_clauses.append(f'{key} = "{value}"')
                    elif isinstance(value, dict):
                        set_clauses.append(f'{key} = {json.dumps(value)}')
                    elif isinstance(value, list):
                        set_clauses.append(f'{key} = {json.dumps(value)}')
                    else:
                        set_clauses.append(f'{key} = {value}')
            
            sql = f"CREATE {table}:{record_id} SET {', '.join(set_clauses)};"
            logger.info(f"Creating record: {sql}")
            
            result = self.execute_sql(sql)
            
            if result:
                logger.info(f"Record created successfully: {table}:{record_id}")
                return result[0] if result else None
            else:
                logger.error(f"Failed to create record in {table}")
                return None
                
        except Exception as e:
            logger.error(f"Record creation failed: {e}")
            return None
    
    def get_records(self, table: str, condition: str = "", limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get records from a table with optional conditions."""
        try:
            sql = f"SELECT * FROM {table}"
            if condition:
                sql += f" WHERE {condition}"
            sql += f" LIMIT {limit}"
            if offset > 0:
                sql += f" START {offset}"
            sql += ";"
            
            result = self.execute_sql(sql)
            logger.debug(f"Retrieved {len(result)} records from {table}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get records from {table}: {e}")
            return []
    
    def update_record(self, table: str, record_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record."""
        try:
            set_clauses = []
            for key, value in update_data.items():
                if isinstance(value, str) and value == 'time::now()':
                    set_clauses.append(f"{key} = time::now()")
                elif isinstance(value, str):
                    set_clauses.append(f'{key} = "{value}"')
                elif isinstance(value, dict):
                    set_clauses.append(f'{key} = {json.dumps(value)}')
                elif isinstance(value, list):
                    set_clauses.append(f'{key} = {json.dumps(value)}')
                else:
                    set_clauses.append(f'{key} = {value}')
            
            sql = f"UPDATE {table}:{record_id} SET {', '.join(set_clauses)};"
            result = self.execute_sql(sql)
            
            if result:
                logger.info(f"Record updated successfully: {table}:{record_id}")
                return result[0] if result else None
            else:
                logger.error(f"Failed to update record: {table}:{record_id}")
                return None
                
        except Exception as e:
            logger.error(f"Record update failed: {e}")
            return None
    
    def delete_record(self, table: str, record_id: str) -> bool:
        """Delete a record."""
        try:
            sql = f"DELETE {table}:{record_id};"
            result = self.execute_sql(sql)
            
            logger.info(f"Record deleted: {table}:{record_id}")
            return True
            
        except Exception as e:
            logger.error(f"Record deletion failed: {e}")
            return False
    
    def ensure_table(self, table: str, fields: Dict[str, str]) -> None:
        """Ensure table exists with the specified schema."""
        try:
            sql_parts = [f"DEFINE TABLE {table} SCHEMAFULL"]
            
            for field_name, field_type in fields.items():
                sql_parts.append(f"DEFINE FIELD {field_name} ON {table} TYPE {field_type}")
            
            sql = "; ".join(sql_parts) + ";"
            
            result = self.execute_sql(sql)
            logger.info(f"Table {table} ensured with fields: {fields}")
            
        except Exception as e:
            logger.error(f"Failed to ensure table {table}: {e}")