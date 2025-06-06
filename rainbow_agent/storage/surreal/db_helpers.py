"""
Helper functions for SurrealDB client operations.
"""

import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_auth_headers(username: str, password: str, namespace: str, database: str) -> Dict[str, str]:
    """
    Generate authentication headers for SurrealDB requests.
    
    Args:
        username: SurrealDB username
        password: SurrealDB password
        namespace: SurrealDB namespace
        database: SurrealDB database name
        
    Returns:
        Dictionary of headers with authentication information
    """
    # 生成基本认证头
    auth_str = f"{username}:{password}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    
    # 构建完整的头部信息
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_auth}",
        # SurrealDB v1.x 格式
        "ns": namespace,
        "db": database,
        # SurrealDB v2.x 格式
        "Surreal-NS": namespace,
        "Surreal-DB": database
    }
    
    return headers

def get_current_time_iso() -> str:
    """
    Get current time in ISO 8601 format.
    
    Returns:
        Current time as ISO 8601 string
    """
    return datetime.utcnow().isoformat() + "Z"

def format_value_for_sql(value: Any) -> str:
    """
    Format a Python value for use in SQL queries.
    
    Args:
        value: The value to format
        
    Returns:
        SQL-safe string representation of the value
    """
    if value is None:
        return "NULL"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, dict):
        import json
        # Escape single quotes in JSON string
        json_str = json.dumps(value).replace("'", "''")
        return f"'{json_str}'"
    elif isinstance(value, str):
        if value == "time::now()":
            return "time::now()"
        else:
            # Escape single quotes in string by doubling them
            escaped_value = value.replace("'", "''")
            return f"'{escaped_value}'"
    else:
        # For other types, convert to string and escape
        escaped_str = str(value).replace("'", "''")
        return f"'{escaped_str}'"

def parse_surreal_response(response: Any) -> Optional[list]:
    """
    Parse SurrealDB response into a usable format.
    
    Args:
        response: Raw response from SurrealDB
        
    Returns:
        List of records or None if parsing fails
    """
    try:
        if not response:
            logger.debug("Response is empty or None")
            return []
            
        # Log the response type and structure for debugging
        logger.debug(f"Response type: {type(response)}")
        if isinstance(response, (list, dict)):
            logger.debug(f"Response structure: {response}")
        
        # Case 1: Response is a list
        if isinstance(response, list):
            if not response:  # Empty list
                return []
            
            # Case 1.1: Response is a list of results (most common)
            # Example: [{"result": [...]}, {"status": "OK"}]
            if isinstance(response[0], dict) and "result" in response[0]:
                result = response[0]["result"]
                if isinstance(result, list):
                    return [r for r in result if r]  # Filter out None/empty values
                elif result:  # Single result
                    return [result]
                else:
                    return []
            
            # Case 1.2: Response is a direct list of records
            # Example: [{...}, {...}, ...]
            if all(isinstance(item, dict) for item in response):
                return [r for r in response if r]  # Filter out None/empty values
            
            # Case 1.3: First item is itself a list (nested result)
            # Example: [[{...}, {...}], ...]
            if response and isinstance(response[0], list):
                return [r for r in response[0] if r]  # Filter out None/empty values
            
            # Case 1.4: Mixed content - try to extract dicts
            records = []
            for item in response:
                if isinstance(item, dict):
                    records.append(item)
                elif isinstance(item, list) and item:
                    records.extend([r for r in item if isinstance(r, dict)])
            
            return records
        
        # Case 2: Response is a dictionary
        if isinstance(response, dict):
            # Case 2.1: Response contains a result key with records
            if "result" in response:
                result = response["result"]
                if isinstance(result, list):
                    return [r for r in result if r]  # Filter out None/empty values
                elif result:  # Single result
                    return [result]
                else:
                    return []
            
            # Case 2.2: Response is a single record (contains id or other expected fields)
            # Just return it as a single-item list
            return [response]
        
        # Case 3: Unexpected response type
        logger.warning(f"Unexpected response type: {type(response)}")
        return []
    except Exception as e:
        logger.error(f"Error parsing SurrealDB response: {e}")
        logger.exception(e)
        return []
