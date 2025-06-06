"""
SQL Builder for SurrealDB queries.

This module provides utilities for building parameterized SQL queries for SurrealDB.
"""
from typing import Dict, Any, Tuple, List, Optional


def build_select_query(table: str, condition: Optional[str] = None, limit: int = 100, offset: int = 0) -> str:
    """
    Build a SELECT query for SurrealDB.
    
    Args:
        table: The table name
        condition: Optional WHERE condition (without 'WHERE' keyword)
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        SQL query string
    """
    query = f"SELECT * FROM {table}"
    
    if condition:
        query += f" WHERE {condition}"
    
    query += f" LIMIT {limit} START {offset};"
    
    return query


def build_parameterized_select_query(table: str, conditions: Dict[str, Any], limit: int = 100, offset: int = 0) -> Tuple[str, Dict[str, Any]]:
    """
    Build a parameterized SELECT query for SurrealDB.
    
    Args:
        table: The table name
        conditions: Dictionary of field-value pairs for WHERE conditions
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        Tuple of (SQL query string, parameters dictionary)
    """
    params = {}
    query = f"SELECT * FROM {table}"
    
    if conditions:
        where_clauses = []
        for i, (field, value) in enumerate(conditions.items()):
            param_name = f"p{i}"
            where_clauses.append(f"{field} = ${param_name}")
            params[param_name] = value
        
        query += f" WHERE {' AND '.join(where_clauses)}"
    
    query += f" LIMIT {limit} START {offset};"
    
    return query, params


def build_insert_query(table: str, data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Build a parameterized INSERT query for SurrealDB.
    
    Args:
        table: The table name
        data: Dictionary of field-value pairs to insert
        
    Returns:
        Tuple of (SQL query string, parameters dictionary)
    """
    fields = list(data.keys())
    params = {}
    
    # Handle the case where id is provided
    record_id = data.get('id')
    if record_id:
        query = f"INSERT INTO {table}:{record_id} "
    else:
        query = f"INSERT INTO {table} "
    
    # Build the field list and parameter list
    field_list = ", ".join(fields)
    param_list = []
    
    for i, field in enumerate(fields):
        param_name = f"p{i}"
        param_list.append(f"${param_name}")
        params[param_name] = data[field]
    
    param_str = ", ".join(param_list)
    
    # Complete the query
    query += f"({field_list}) VALUES ({param_str});"
    
    return query, params


def build_update_query(table: str, record_id: str, data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Build a parameterized UPDATE query for SurrealDB.
    
    Args:
        table: The table name
        record_id: Record ID to update
        data: Dictionary of field-value pairs to update
        
    Returns:
        Tuple of (SQL query string, parameters dictionary)
    """
    params = {}
    query = f"UPDATE {table}:{record_id} SET "
    
    set_clauses = []
    for i, (field, value) in enumerate(data.items()):
        if field != 'id':  # Skip the id field
            param_name = f"p{i}"
            set_clauses.append(f"{field} = ${param_name}")
            params[param_name] = value
    
    query += ", ".join(set_clauses) + ";"
    
    return query, params


def build_delete_query(table: str, record_id: str) -> str:
    """
    Build a DELETE query for SurrealDB.
    
    Args:
        table: The table name
        record_id: Record ID to delete
        
    Returns:
        SQL query string
    """
    return f"DELETE FROM {table}:{record_id};"


def build_count_query(table: str, condition: Optional[str] = None) -> str:
    """
    Build a COUNT query for SurrealDB.
    
    Args:
        table: The table name
        condition: Optional WHERE condition (without 'WHERE' keyword)
        
    Returns:
        SQL query string
    """
    query = f"SELECT count() FROM {table}"
    
    if condition:
        query += f" WHERE {condition}"
    
    query += ";"
    
    return query
