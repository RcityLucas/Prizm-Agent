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
            return None
            
        # Log the response type and structure for debugging
        logger.debug(f"Response type: {type(response)}")
        logger.debug(f"Response content: {response}")
            
        if isinstance(response, list):
            if len(response) == 0:
                return []
                
            # SurrealDB 1.0.4 format - direct list of results
            # Check if the first item is a list (new format)
            if len(response) > 0 and isinstance(response[0], list):
                return response[0]
                
            # Handle old response format: [{"result": [...]}]
            if isinstance(response[0], dict):
                # Check for result key (old format)
                if "result" in response[0]:
                    result = response[0]["result"]
                    
                    # Handle different result formats
                    if isinstance(result, list):
                        return result
                    elif isinstance(result, dict):
                        return [result]
                # New format might just be a list of dicts
                else:
                    return response
            
            # Direct list of records
            return response
        
        # Handle direct dict response
        if isinstance(response, dict):
            # Check for status field which might indicate an error
            if "status" in response and response["status"] != "OK":
                logger.warning(f"SurrealDB response indicates error: {response}")
                return None
                
            if "result" in response:
                result = response["result"]
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict):
                    return [result]
            return [response]
            
        logger.warning(f"无法解析的响应类型: {type(response)}")
        return None
    except Exception as e:
        logger.error(f"解析SurrealDB响应时出错: {e}")
        logger.exception(e)  # 打印完整的异常堆栈
        return None
