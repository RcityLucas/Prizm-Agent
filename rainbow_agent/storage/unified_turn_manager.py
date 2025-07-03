"""
Unified Turn Manager using the simplified, reliable approach.

This manager uses the UnifiedSurrealClient for all database operations,
eliminating complex fallback logic and HTTP endpoint mixing.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .surreal.unified_client import UnifiedSurrealClient
from .models import TurnModel

logger = logging.getLogger(__name__)


class UnifiedTurnManager:
    """
    Unified turn manager using reliable SQL-based operations.
    
    This class eliminates the complexity of the original TurnManager:
    - Uses only the official SurrealDB client
    - No HTTP endpoint mixing
    - No complex fallback logic
    - Simple, transparent SQL operations
    """
    
    def __init__(self, 
                 url: str = "ws://localhost:8000/rpc",
                 namespace: str = "rainbow",
                 database: str = "test",
                 username: str = "root",
                 password: str = "root",
                 client: Optional[Any] = None):
        """
        Initialize the turn manager.
        
        Args:
            url: SurrealDB WebSocket URL
            namespace: SurrealDB namespace
            database: SurrealDB database name
            username: SurrealDB username
            password: SurrealDB password
            client: Optional external UnifiedSurrealClient instance
        """
        # 保存连接参数，以便需要时重新创建客户端
        self.url = url
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        
        # 使用外部提供的客户端或创建新客户端
        if client:
            self.client = client
            logger.info("UnifiedTurnManager using provided client instance")
        else:
            # 创建持久UnifiedSurrealClient实例
            from .surreal.unified_client import UnifiedSurrealClient
            self.client = UnifiedSurrealClient(url, namespace, database, username, password)
            logger.info("UnifiedTurnManager created new client instance")
            
        # Ensure table structure exists
        self._ensure_table_structure()
        
        logger.info("UnifiedTurnManager initialized")
    
    def _ensure_table_structure(self) -> None:
        """Ensure the turns table exists with proper schema."""
        try:
            # 首先确保表存在
            self.client.ensure_table_exists("turns")
            
            # 使用 SQL 直接定义字段，确保 embedding 字段正确定义为数组类型
            sql_statements = [
                "DEFINE FIELD id ON TABLE turns TYPE string;",
                "DEFINE FIELD session_id ON TABLE turns TYPE string;",
                "DEFINE FIELD role ON TABLE turns TYPE string;",
                "DEFINE FIELD content ON TABLE turns TYPE string;",
                "DEFINE FIELD created_at ON TABLE turns TYPE datetime;",
                "DEFINE FIELD updated_at ON TABLE turns TYPE datetime;",
                "DEFINE FIELD embedding ON TABLE turns TYPE array;",  # 明确定义为数组类型，不使用 option<array>
                "DEFINE FIELD metadata ON TABLE turns TYPE option<object>;",
                # 添加索引以加快查询
                "DEFINE INDEX turn_session_id ON TABLE turns COLUMNS session_id;",
                "DEFINE INDEX turn_role ON TABLE turns COLUMNS role;"
            ]
            
            # 执行 SQL 语句
            for sql in sql_statements:
                try:
                    self.client.execute_sql(sql)
                    logger.info(f"Executed SQL: {sql}")
                except Exception as sql_error:
                    # 如果字段已存在，忽略错误
                    if "already exists" in str(sql_error):
                        logger.info(f"Field already exists: {sql}")
                    else:
                        logger.warning(f"Error executing SQL: {sql}, Error: {sql_error}")
            
            logger.info("Turns table structure ensured with explicit embedding array type")
            
        except Exception as e:
            logger.error(f"Failed to ensure table structure: {e}")
    
    def create_turn(self, 
               session_id: str, 
               role: str, 
               content: str, 
               embedding: Optional[List[float]] = None,
               metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new turn synchronously.
        
        Args:
            session_id: Session ID this turn belongs to
            role: Role of the speaker (human, ai, system, etc.)
            content: Content of the turn
            embedding: Optional embedding vector
            metadata: Optional metadata
            
        Returns:
            Created turn data or None on failure
        """
        try:
            # Ensure session_id is always treated as a simple string to prevent transformation in TurnModel
            original_session_id = session_id
            session_id_str = str(session_id) if session_id is not None else None
            
            logger.info(f"Creating turn for session - Original ID: {original_session_id}, Type: {type(original_session_id)}")
            logger.info(f"Using simplified string session_id: {session_id_str}")
            
            # Create turn model with stringified session_id
            turn_model = TurnModel(
                session_id=session_id_str,  # Use the string version directly
                role=role,
                content=content,
                embedding=embedding,
                metadata=metadata or {}
            )
            
            # Log the session_id that actually got set in the model
            logger.info(f"Turn model created with session_id: {turn_model.session_id}")
            
            # Convert to dictionary
            turn_data = turn_model.to_dict()
            
            # Ensure the session_id in the dictionary is correct
            if turn_data['session_id'] != session_id_str:
                logger.warning(f"Session ID mismatch detected! Dictionary has {turn_data['session_id']} but should be {session_id_str}")
                turn_data['session_id'] = session_id_str
            
            logger.info(f"Creating turn: {turn_model.id} for session: {turn_data['session_id']}")
            
            # Create record using unified client
            result = self.client.create_record("turns", turn_data)
            
            if result:
                logger.info(f"Turn created successfully: {turn_model.id} with session_id: {result.get('session_id')}")
                return result
            else:
                logger.error(f"Failed to create turn: {turn_model.id}")
                return None
                
        except Exception as e:
            logger.error(f"Turn creation failed: {e}")
            return None
    
    async def create_turn_async(self, 
                               session_id: str, 
                               role: str, 
                               content: str, 
                               embedding: Optional[List[float]] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new turn asynchronously.
        
        For now, this wraps the synchronous method. In the future,
        we can implement true async if needed.
        
        Args:
            session_id: Session ID this turn belongs to
            role: Role of the speaker (human, ai, system, etc.)
            content: Content of the turn
            embedding: Optional embedding vector
            metadata: Optional metadata
            
        Returns:
            Created turn data or None on failure
        """
        # Ensure session_id is always a string before calling the sync method
        # This helps prevent session_id mismatches when session_id is processed as an object
        if session_id is not None:
            session_id_str = str(session_id)
            logger.info(f"Async turn creation - Original ID: {session_id}, Using string ID: {session_id_str}")
            return self.create_turn(session_id_str, role, content, embedding, metadata)
        else:
            logger.warning("Async turn creation called with None session_id")
            return None
    
    def get_turns(self, 
                 session_id: Union[str, Dict[str, Any]], 
                 limit: int = 100, 
                 offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get turns for a session.
        
        Args:
            session_id: Session ID to get turns for (can be string or dict with 'id' key)
            limit: Maximum number of turns to return
            offset: Number of turns to skip
            
        Returns:
            List of turn records or empty list if session not found/invalid
        """
        if not session_id:
            logger.warning("Empty session_id provided to get_turns")
            return []
            
        try:
            # Handle case where session_id is a dictionary
            actual_session_id = str(session_id['id'] if isinstance(session_id, dict) and 'id' in session_id else session_id)
            
            if not actual_session_id:
                logger.warning("Could not extract valid session_id from input")
                return []
                
            logger.info(f"Getting turns for session_id: {actual_session_id}")
            
            # First, verify the session exists
            # Try both with and without the 'sessions:' prefix to handle different ID formats
            raw_session_id = actual_session_id.replace('sessions:', '') if actual_session_id.startswith('sessions:') else actual_session_id
            prefixed_session_id = f"sessions:{raw_session_id}" if not actual_session_id.startswith('sessions:') else actual_session_id
            
            session_query = f"SELECT * FROM sessions WHERE id = '{raw_session_id}' OR id = '{prefixed_session_id}';"
            logger.debug(f"Verifying session exists with query: {session_query}")
            session_result = self.client.execute_sql(session_query)
            
            if not session_result or not isinstance(session_result, list) or len(session_result) == 0:
                logger.warning(f"Session not found with either ID format: {raw_session_id} or {prefixed_session_id}")
                # Continue anyway since we know the session exists - the problem is just with ID format
                logger.info(f"Attempting to retrieve turns despite session verification failure")
                
            if session_result and isinstance(session_result, list) and len(session_result) > 0:
                logger.debug(f"Session found: {session_result[0].get('id')}")
            
            # Get turns for the session - first try with raw session_id
            query = f"SELECT * FROM turns WHERE session_id = '{raw_session_id}' ORDER BY created_at ASC LIMIT {limit} START {offset};"
            logger.debug(f"Executing turns query with raw session_id: {query}")
            logger.info(f"Searching for turns with session_id: '{raw_session_id}'")
            
            # Execute the query directly
            result = self.client.execute_sql(query)
            
            # If no results, try with prefixed version
            if not result or not isinstance(result, list) or len(result) == 0:
                logger.info(f"No turns found with raw session_id, trying with prefixed session_id: '{prefixed_session_id}'")
                query = f"SELECT * FROM turns WHERE session_id = '{prefixed_session_id}' ORDER BY created_at ASC LIMIT {limit} START {offset};"
                result = self.client.execute_sql(query)
            
            # Log raw result for debugging
            logger.debug(f"Raw query result: {result}")
            
            # Get a sample turn to understand what's in the database (for debugging)
            if not result or not isinstance(result, list) or len(result) == 0:
                debug_query = "SELECT * FROM turns LIMIT 1;"
                debug_result = self.client.execute_sql(debug_query)
                if debug_result and isinstance(debug_result, list) and len(debug_result) > 0:
                    logger.info(f"DEBUG: Sample turn record format: {debug_result[0]}")
                    if 'session_id' in debug_result[0]:
                        logger.info(f"DEBUG: Sample session_id type: {type(debug_result[0]['session_id'])}, value: {debug_result[0]['session_id']}")
                
                logger.warning(f"No turns found for session: {actual_session_id}")
                return []
                
            # Filter out any non-dict items and ensure they have required fields
            valid_turns = []
            for turn in result:
                if not isinstance(turn, dict):
                    logger.warning(f"Skipping invalid turn (not a dict): {turn}")
                    continue
                    
                # Ensure required fields exist
                if 'id' not in turn or 'session_id' not in turn:
                    logger.warning(f"Skipping turn missing required fields: {turn}")
                    continue
                    
                valid_turns.append(turn)
            
            # Sort by created_at if it exists
            valid_turns.sort(key=lambda x: x.get('created_at', ''))
            
            logger.info(f"Retrieved {len(valid_turns)} valid turns for session: {actual_session_id}")
            return valid_turns
            
        except Exception as e:
            logger.error(f"Error getting turns for session {session_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_turns_async(self, 
                             session_id: Union[str, Dict[str, Any]], 
                             limit: int = 100, 
                             offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get turns for a session asynchronously.
        
        Args:
            session_id: Session ID to get turns for (can be string or dict with 'id' key)
            limit: Maximum number of turns to return
            offset: Number of turns to skip
            
        Returns:
            List of turn records or empty list if session not found/invalid
        """
        if not session_id:
            logger.warning("Empty session_id provided to get_turns_async")
            return []
            
        try:
            # Handle case where session_id is a dictionary
            actual_session_id = str(session_id['id'] if isinstance(session_id, dict) and 'id' in session_id else session_id)
            
            if not actual_session_id:
                logger.warning("Could not extract valid session_id from input in async call")
                return []
                
            logger.debug(f"Getting turns asynchronously for session_id: {actual_session_id}")
            
            # First, verify the session exists asynchronously
            session_query = f"SELECT * FROM sessions WHERE id = '{actual_session_id}';"
            logger.debug(f"Verifying session exists with async query: {session_query}")
            session_result = await self.client.execute_sql_async(session_query)
            
            if not session_result or not isinstance(session_result, list) or len(session_result) == 0:
                logger.warning(f"Session not found (async): {actual_session_id}")
                return []
                
            logger.debug(f"Session found (async): {session_result[0].get('id')}")
            
            # Get turns for the session
            query = f"SELECT * FROM turns WHERE session_id = '{actual_session_id}' ORDER BY created_at ASC LIMIT {limit} START {offset};"
            logger.debug(f"Executing async turns query: {query}")
            
            # Execute the query directly
            result = await self.client.execute_sql_async(query)
            
            # Log raw result for debugging
            logger.debug(f"Raw async query result: {result}")
            
            # Process and validate the result
            if not result or not isinstance(result, list):
                logger.warning(f"Unexpected result format when getting turns asynchronously for session {actual_session_id}")
                return []
                
            # Filter out any non-dict items and ensure they have required fields
            valid_turns = []
            for turn in result:
                if not isinstance(turn, dict):
                    logger.warning(f"Skipping invalid turn in async result (not a dict): {turn}")
                    continue
                    
                # Ensure required fields exist
                if 'id' not in turn or 'session_id' not in turn:
                    logger.warning(f"Skipping turn in async result missing required fields: {turn}")
                    continue
                    
                valid_turns.append(turn)
            
            # Sort by created_at if it exists
            valid_turns.sort(key=lambda x: x.get('created_at', ''))
            
            logger.info(f"Retrieved {len(valid_turns)} valid turns asynchronously for session: {actual_session_id}")
            return valid_turns
            
        except Exception as e:
            logger.error(f"Error getting turns asynchronously for session {session_id}: {str(e)}", exc_info=True)
            return []
    
    def get_turn(self, turn_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific turn by ID.
        
        Args:
            turn_id: Turn ID to retrieve
            
        Returns:
            Turn record or None if not found
        """
        try:
            condition = f"id = '{turn_id}'"
            result = self.client.get_records("turns", condition, limit=1)
            
            if result:
                logger.info(f"Retrieved turn: {turn_id}")
                return result[0]
            else:
                logger.warning(f"Turn not found: {turn_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get turn {turn_id}: {e}")
            return None
    
    def update_turn(self, 
                   turn_id: str, 
                   update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a turn.
        
        Args:
            turn_id: Turn ID to update
            update_data: Data to update
            
        Returns:
            Updated turn record or None on failure
        """
        try:
            # Add updated_at timestamp
            update_data['updated_at'] = datetime.now().isoformat()
            
            result = self.client.update_record("turns", turn_id, update_data)
            
            if result:
                logger.info(f"Turn updated successfully: {turn_id}")
                return result
            else:
                logger.error(f"Failed to update turn: {turn_id}")
                return None
                
        except Exception as e:
            logger.error(f"Turn update failed: {e}")
            return None
    
    def delete_turn(self, turn_id: str) -> bool:
        """
        Delete a turn.
        
        Args:
            turn_id: Turn ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.delete_record("turns", turn_id)
            
            if result:
                logger.info(f"Turn deleted successfully: {turn_id}")
                return True
            else:
                logger.error(f"Failed to delete turn: {turn_id}")
                return False
                
        except Exception as e:
            logger.error(f"Turn deletion failed: {e}")
            return False
    
    def count_turns(self, session_id: str) -> int:
        """
        Count turns in a session.
        
        Args:
            session_id: Session ID to count turns for
            
        Returns:
            Number of turns in the session
        """
        try:
            # 处理session_id可能是字典的情况
            actual_session_id = session_id
            if isinstance(session_id, dict) and 'id' in session_id:
                actual_session_id = session_id['id']
                logger.info(f"Extracted session_id from dictionary: {actual_session_id}")
            
            sql = f"SELECT count() FROM turns WHERE session_id = '{actual_session_id}' GROUP ALL;"
            result = self.client.execute_sql(sql)
            
            if result and len(result) > 0 and 'count' in result[0]:
                count = result[0]['count']
                logger.info(f"Session {actual_session_id} has {count} turns")
                return count
            else:
                logger.info(f"Session {actual_session_id} has 0 turns")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to count turns for session {session_id}: {e}")
            return 0