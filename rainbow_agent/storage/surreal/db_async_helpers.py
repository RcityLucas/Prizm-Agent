"""
Asynchronous operation helpers for SurrealDB client.
"""

import json
import logging
import aiohttp
from typing import Dict, Any, List, Optional, Union

from .db_helpers import parse_surreal_response

logger = logging.getLogger(__name__)

async def execute_sql_async(
    base_url: str, 
    headers: Dict[str, str], 
    sql: str, 
    params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute SQL query asynchronously.
    
    Args:
        base_url: SurrealDB base URL
        headers: Request headers including authentication
        sql: SQL query to execute
        params: Optional parameters for parameterized query
        
    Returns:
        List of records or empty list on failure
    """
    try:
        url = f"{base_url}/sql"
        
        # Prepare request payload
        payload = {'query': sql}
        if params:
            payload['vars'] = params
            
        logger.info(f"Executing SQL async: {sql}")
        if params:
            logger.info(f"Parameters: {params}")
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                status = response.status
                response_text = await response.text()
                
                logger.info(f"SQL query response code: {status}")
                
                if status == 200:
                    result = json.loads(response_text)
                    logger.info(f"SQL query successful: {sql}")
                    
                    # Parse response
                    parsed_result = parse_surreal_response(result)
                    return parsed_result  # Already returns empty list if parsing fails
                else:
                    logger.error(f"SQL query failed: {status} {response.reason}")
                    logger.error(f"Response content: {response_text}")
                    # Raise exception for better error handling
                    raise Exception(f"SQL query failed with status {status}: {response_text}")
    except Exception as e:
        logger.error(f"Error executing async SQL query: {e}")
        # Re-raise to allow proper error handling in calling code
        raise

async def create_record_async(
    base_url: str, 
    headers: Dict[str, str], 
    table: str, 
    record_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a record asynchronously using parameterized SQL.
    
    Args:
        base_url: SurrealDB base URL
        headers: Request headers including authentication
        table: Table name
        record_data: Record data to create
        
    Returns:
        Created record data
        
    Raises:
        ValueError: If required data is missing
        Exception: If the database operation fails
    """
    try:
        from .sql_builder import build_insert_query
        
        # Replace any time::now() with ISO timestamp
        for key, value in record_data.items():
            if isinstance(value, str) and value == "time::now()":
                from .db_helpers import get_current_time_iso
                record_data[key] = get_current_time_iso()
        
        # Build parameterized SQL query
        sql, params = build_insert_query(table, record_data)
        
        logger.info(f"Creating record in {table} with ID: {record_data.get('id', 'auto-generated')}")
        
        # Execute the SQL query
        result = await execute_sql_async(base_url, headers, sql, params)
        
        if result and len(result) > 0:
            logger.info(f"Record created successfully in {table}")
            return result[0]
        else:
            raise Exception(f"Failed to create record in {table}: No result returned")
            
    except Exception as e:
        logger.error(f"Error creating record async: {e}")
        raise

async def update_record_async(
    base_url: str, 
    headers: Dict[str, str], 
    table: str, 
    record_id: str, 
    record_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update a record asynchronously using parameterized SQL.
    
    Args:
        base_url: SurrealDB base URL
        headers: Request headers including authentication
        table: Table name
        record_id: Record ID to update
        record_data: Record data to update
        
    Returns:
        Updated record data
        
    Raises:
        ValueError: If required data is missing
        Exception: If the database operation fails
    """
    try:
        from .sql_builder import build_update_query
        
        # Replace any time::now() with ISO timestamp
        for key, value in record_data.items():
            if isinstance(value, str) and value == "time::now()":
                from .db_helpers import get_current_time_iso
                record_data[key] = get_current_time_iso()
        
        # Build parameterized SQL query
        sql, params = build_update_query(table, record_id, record_data)
        
        logger.info(f"Updating record {table}:{record_id}")
        
        # Execute the SQL query
        result = await execute_sql_async(base_url, headers, sql, params)
        
        # Also fetch the updated record to return the complete state
        fetch_sql = f"SELECT * FROM {table}:{record_id};"
        updated_record = await execute_sql_async(base_url, headers, fetch_sql)
        
        if updated_record and len(updated_record) > 0:
            logger.info(f"Record {table}:{record_id} updated successfully")
            return updated_record[0]
        else:
            raise Exception(f"Failed to update record {table}:{record_id}: Record not found after update")
            
    except Exception as e:
        logger.error(f"Error updating record async: {e}")
        raise

async def delete_record_async(
    base_url: str, 
    headers: Dict[str, str], 
    table: str, 
    record_id: str
) -> bool:
    """
    Delete a record asynchronously using parameterized SQL.
    
    Args:
        base_url: SurrealDB base URL
        headers: Request headers including authentication
        table: Table name
        record_id: Record ID to delete
        
    Returns:
        True if deletion was successful
        
    Raises:
        Exception: If the database operation fails
    """
    try:
        from .sql_builder import build_delete_query
        
        # Build SQL query
        sql = build_delete_query(table, record_id)
        
        logger.info(f"Deleting record {table}:{record_id}")
        
        # Execute the SQL query
        await execute_sql_async(base_url, headers, sql)
        
        logger.info(f"Record {table}:{record_id} deleted successfully")
        return True
            
    except Exception as e:
        logger.error(f"Error deleting record async: {e}")
        raise

async def get_record_async(
    base_url: str, 
    headers: Dict[str, str], 
    table: str, 
    record_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get a record asynchronously using parameterized SQL.
    
    Args:
        base_url: SurrealDB base URL
        headers: Request headers including authentication
        table: Table name
        record_id: Record ID to get
        
    Returns:
        Record data or None if not found
        
    Raises:
        Exception: If the database operation fails
    """
    try:
        # Build SQL query
        sql = f"SELECT * FROM {table}:{record_id};"
        
        logger.info(f"Getting record {table}:{record_id}")
        
        # Execute the SQL query
        result = await execute_sql_async(base_url, headers, sql)
        
        if result and len(result) > 0:
            logger.info(f"Record {table}:{record_id} retrieved successfully")
            return result[0]
        else:
            logger.info(f"Record {table}:{record_id} not found")
            return None
            
    except Exception as e:
        logger.error(f"Error getting record async: {e}")
        raise
