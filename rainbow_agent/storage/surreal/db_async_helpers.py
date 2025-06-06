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
        
        # 准备请求负载
        payload = {'query': sql}
        if params:
            payload['vars'] = params
            
        logger.info(f"异步执行SQL: {sql}")
        if params:
            logger.info(f"参数: {params}")
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                status = response.status
                response_text = await response.text()
                
                logger.info(f"SQL查询响应码: {status}")
                
                if status == 200:
                    result = json.loads(response_text)
                    logger.info(f"SQL查询成功: {sql}")
                    
                    # 解析响应
                    parsed_result = parse_surreal_response(result)
                    if parsed_result is not None:
                        return parsed_result
                    return []
                else:
                    logger.error(f"SQL查询失败: {status} {response.reason}")
                    logger.error(f"响应内容: {response_text}")
                    return []
    except Exception as e:
        logger.error(f"执行异步SQL查询时出错: {e}")
        return []

async def create_record_async(
    base_url: str, 
    headers: Dict[str, str], 
    table: str, 
    record_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Create a record asynchronously.
    
    Args:
        base_url: SurrealDB base URL
        headers: Request headers including authentication
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
        url = f"{base_url}/key/{full_id}"
        
        logger.info(f"异步创建记录: {full_id}")
        logger.info(f"记录数据: {record_data}")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=record_data) as response:
                status = response.status
                response_text = await response.text()
                
                logger.info(f"创建记录响应码: {status}")
                
                if status == 200:
                    logger.info(f"记录创建成功: {full_id}")
                    return record_data
                else:
                    logger.error(f"记录创建失败: {status} {response.reason}")
                    logger.error(f"响应内容: {response_text}")
                    return None
    except Exception as e:
        logger.error(f"异步创建记录时出错: {e}")
        return None

async def update_record_async(
    base_url: str, 
    headers: Dict[str, str], 
    table: str, 
    record_id: str, 
    record_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update a record asynchronously.
    
    Args:
        base_url: SurrealDB base URL
        headers: Request headers including authentication
        table: Table name
        record_id: Record ID to update
        record_data: Record data to update
        
    Returns:
        Updated record data or None on failure
    """
    try:
        full_id = f"{table}:{record_id}"
        url = f"{base_url}/key/{full_id}"
        
        logger.info(f"异步更新记录: {full_id}")
        logger.info(f"更新数据: {record_data}")
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json=record_data) as response:
                status = response.status
                response_text = await response.text()
                
                logger.info(f"更新记录响应码: {status}")
                
                if status == 200:
                    logger.info(f"记录更新成功: {full_id}")
                    return record_data
                else:
                    logger.error(f"记录更新失败: {status} {response.reason}")
                    logger.error(f"响应内容: {response_text}")
                    return None
    except Exception as e:
        logger.error(f"异步更新记录时出错: {e}")
        return None

async def delete_record_async(
    base_url: str, 
    headers: Dict[str, str], 
    table: str, 
    record_id: str
) -> bool:
    """
    Delete a record asynchronously.
    
    Args:
        base_url: SurrealDB base URL
        headers: Request headers including authentication
        table: Table name
        record_id: Record ID to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        full_id = f"{table}:{record_id}"
        url = f"{base_url}/key/{full_id}"
        
        logger.info(f"异步删除记录: {full_id}")
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                logger.info(f"删除记录响应码: {status}")
                
                if status == 200:
                    logger.info(f"记录删除成功: {full_id}")
                    return True
                else:
                    logger.error(f"记录删除失败: {status} {response.reason}")
                    logger.error(f"响应内容: {response_text}")
                    return False
    except Exception as e:
        logger.error(f"异步删除记录时出错: {e}")
        return False

async def get_record_async(
    base_url: str, 
    headers: Dict[str, str], 
    table: str, 
    record_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get a record asynchronously.
    
    Args:
        base_url: SurrealDB base URL
        headers: Request headers including authentication
        table: Table name
        record_id: Record ID to get
        
    Returns:
        Record data or None if not found or on error
    """
    try:
        full_id = f"{table}:{record_id}"
        url = f"{base_url}/key/{full_id}"
        
        logger.info(f"异步获取记录: {full_id}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                logger.info(f"获取记录响应码: {status}")
                
                if status == 200:
                    result = json.loads(response_text)
                    logger.info(f"记录获取成功: {full_id}")
                    
                    # 解析响应
                    parsed_result = parse_surreal_response(result)
                    if parsed_result and len(parsed_result) > 0:
                        return parsed_result[0]
                    return None
                else:
                    logger.error(f"记录获取失败: {status} {response.reason}")
                    logger.error(f"响应内容: {response_text}")
                    return None
    except Exception as e:
        logger.error(f"异步获取记录时出错: {e}")
        return None
