"""
SQL query builders for SurrealDB operations.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from .db_helpers import format_value_for_sql

logger = logging.getLogger(__name__)

def build_select_query(table: str, condition: str = None, limit: int = 100, offset: int = 0) -> str:
    """
    Build a SELECT query for SurrealDB.
    
    Args:
        table: Table name
        condition: WHERE clause condition (without 'WHERE')
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        SQL query string
    """
    sql = f"SELECT * FROM {table}"
    if condition:
        sql += f" WHERE {condition}"
    sql += f" LIMIT {limit} START {offset};"
    return sql

def build_parameterized_select_query(
    table: str, 
    conditions: Dict[str, Any] = None, 
    limit: int = 100, 
    offset: int = 0,
    order_by: str = None,
    order_direction: str = "ASC"
) -> Tuple[str, Dict[str, Any]]:
    """
    Build a parameterized SELECT query for SurrealDB.
    
    Args:
        table: Table name
        conditions: Dictionary of field:value pairs for WHERE clause
        limit: Maximum number of records to return
        offset: Number of records to skip
        order_by: Field to order by
        order_direction: Order direction (ASC or DESC)
        
    Returns:
        Tuple of (SQL query string, parameters dict)
    """
    sql = f"SELECT * FROM {table}"
    params = {}
    
    if conditions:
        where_clauses = []
        for i, (field, value) in enumerate(conditions.items()):
            param_name = f"param_{i}"
            where_clauses.append(f"{field} = ${param_name}")
            params[param_name] = value
        
        sql += f" WHERE {' AND '.join(where_clauses)}"
    
    if order_by:
        sql += f" ORDER BY {order_by} {order_direction}"
    
    sql += f" LIMIT {limit} START {offset}"
    
    return sql, params

def build_insert_query(table: str, data: Dict[str, Any]) -> str:
    """
    Build an INSERT query for SurrealDB.
    
    Args:
        table: Table name
        data: Dictionary of field:value pairs to insert
        
    Returns:
        SQL query string
    """
    fields = []
    values = []
    
    for key, value in data.items():
        fields.append(key)
        values.append(format_value_for_sql(value))
    
    fields_str = ", ".join(fields)
    values_str = ", ".join(values)
    
    return f"INSERT INTO {table} ({fields_str}) VALUES ({values_str});"

def build_update_query(table: str, record_id: str, data: Dict[str, Any]) -> str:
    """
    Build an UPDATE query for SurrealDB.
    
    Args:
        table: Table name
        record_id: Record ID to update
        data: Dictionary of field:value pairs to update
        
    Returns:
        SQL query string
    """
    set_clauses = []
    
    for key, value in data.items():
        set_clauses.append(f"{key} = {format_value_for_sql(value)}")
    
    set_clause = ", ".join(set_clauses)
    return f"UPDATE {table}:{record_id} SET {set_clause};"

def build_delete_query(table: str, record_id: str) -> str:
    """
    Build a DELETE query for SurrealDB.
    
    Args:
        table: Table name
        record_id: Record ID to delete
        
    Returns:
        SQL query string
    """
    return f"DELETE FROM {table}:{record_id};"

def build_count_query(table: str, condition: str = None) -> str:
    """
    Build a COUNT query for SurrealDB.
    
    Args:
        table: Table name
        condition: WHERE clause condition (without 'WHERE')
        
    Returns:
        SQL query string
    """
    sql = f"SELECT count() FROM {table}"
    if condition:
        sql += f" WHERE {condition}"
    sql += ";"
    return sql

def build_table_definition_query(table: str, fields: List[Dict[str, Any]]) -> str:
    """
    Build a table definition query for SurrealDB.
    
    Args:
        table: Table name
        fields: List of field definitions with name, type, etc.
        
    Returns:
        SQL query string
    """
    query = f"DEFINE TABLE {table} SCHEMAFULL;\n"
    
    for field in fields:
        field_name = field["name"]
        field_type = field["type"]
        query += f"DEFINE FIELD {field_name} ON {table} TYPE {field_type};\n"
        
        if field.get("assert"):
            query += f"DEFINE FIELD {field_name} ON {table} ASSERT {field['assert']};\n"
    
    return query
