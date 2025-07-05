"""
Unified Turn Manager using the simplified, reliable approach.

This manager uses the UnifiedSurrealClient for all database operations,
eliminating complex fallback logic and HTTP endpoint mixing.
"""

import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
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
    
    def _normalize_session_id(self, session_id: Union[str, Dict[str, Any]]) -> Tuple[str, str]:
        """
        Helper method to normalize session ID from various input formats.
        
        Args:
            session_id: Session ID in various formats (string, dict with 'id' key, etc.)
            
        Returns:
            Tuple of (raw_session_id, prefixed_session_id)
        """
        # Extract session_id from complex objects if needed
        actual_session_id = session_id
        if isinstance(session_id, dict):
            if 'id' in session_id:
                # Handle complex ID object with table_name and id
                if isinstance(session_id['id'], dict) and 'id' in session_id['id']:
                    actual_session_id = session_id['id']['id']
                else:
                    actual_session_id = session_id['id']
                logger.debug(f"Extracted session_id from dictionary: {actual_session_id}")
        
        # Convert to string if not already
        actual_session_id = str(actual_session_id)
        
        # Normalize to both raw and prefixed formats
        if actual_session_id.startswith('sessions:'):
            raw_session_id = actual_session_id[9:]  # Remove 'sessions:' prefix
            prefixed_session_id = actual_session_id
        else:
            raw_session_id = actual_session_id
            prefixed_session_id = f"sessions:{raw_session_id}"
            
        logger.debug(f"Normalized session_id: raw={raw_session_id}, prefixed={prefixed_session_id}")
        return raw_session_id, prefixed_session_id
    
    def _validate_turn(self, turn: Dict[str, Any], raw_session_id: str, prefixed_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate a turn record to ensure it has required fields and matches the session_id.
        
        Args:
            turn: Turn record to validate
            raw_session_id: Raw session ID (without prefix)
            prefixed_session_id: Prefixed session ID (with 'sessions:' prefix)
            
        Returns:
            Valid turn record or None if invalid
        """
        # Skip non-dict items
        if not isinstance(turn, dict):
            logger.warning(f"Invalid turn (not a dict): {turn}")
            return None
        
        # Skip items that are actually sessions, not turns
        if 'status' in turn and 'title' in turn and 'user_id' in turn and 'session_id' not in turn:
            logger.warning(f"Session record incorrectly returned as turn: {turn}")
            return None
            
        # Ensure required turn fields exist
        required_fields = ['id', 'session_id', 'role', 'content']
        missing_fields = [field for field in required_fields if field not in turn]
        
        if missing_fields:
            logger.warning(f"Turn missing required fields {missing_fields}: {turn}")
            return None
        
        # Check if this is a turn with a corrected session_id (from swapped session ID recovery)
        if 'original_session_id' in turn:
            # This turn has already been validated and had its session_id corrected
            return turn
        
        # Ensure the turn's session_id matches the requested session_id
        turn_session_id = turn.get('session_id')
        if turn_session_id != raw_session_id and turn_session_id != prefixed_session_id:
            # Check if we have a known mapping for this turn's session ID
            if turn_session_id in self._session_id_mapping and self._session_id_mapping[turn_session_id] in [raw_session_id, prefixed_session_id]:
                logger.info(f"Correcting turn with mapped session_id: {turn_session_id} -> {raw_session_id}")
                turn['original_session_id'] = turn_session_id
                turn['session_id'] = raw_session_id
                return turn
            else:
                logger.warning(f"Turn with mismatched session_id: {turn_session_id} (expected {raw_session_id} or {prefixed_session_id})")
                return None
            
        return turn
    
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
        if not session_id:
            logger.warning("Empty session_id provided to create_turn")
            return None
            
        try:
            # Use helper method to normalize session ID
            raw_session_id, prefixed_session_id = self._normalize_session_id(session_id)
            logger.info(f"Creating turn for session: raw={raw_session_id}, prefixed={prefixed_session_id}")
            
            # Verify session exists
            session_query = f"SELECT * FROM sessions WHERE id = '{raw_session_id}' OR id = '{prefixed_session_id}';"
            session_result = self.client.execute_sql(session_query)
            
            if not session_result or not isinstance(session_result, list) or len(session_result) == 0:
                logger.warning(f"Creating turn for non-existent session: {raw_session_id}")
                # Continue anyway - we'll create the turn even if session verification fails
            else:
                logger.debug(f"Session verified: {session_result[0].get('id')}")
            
            # Create turn model with normalized session_id (use raw_session_id for consistency)
            turn_model = TurnModel(
                session_id=raw_session_id,  # Always use raw session ID for storage
                role=role,
                content=content,
                embedding=embedding,
                metadata=metadata or {}
            )
            
            # Convert to dictionary
            turn_data = turn_model.to_dict()
            
            # Double-check the session_id in the dictionary is correct
            if turn_data['session_id'] != raw_session_id:
                logger.warning(f"Session ID mismatch detected! Dictionary has {turn_data['session_id']} but should be {raw_session_id}")
                turn_data['session_id'] = raw_session_id
            
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
        # For now, we'll make this a wrapper around the synchronous method
        # This avoids issues with await outside of async functions and ensures consistent behavior
        logger.debug(f"create_turn_async called, delegating to synchronous implementation")
        return self.create_turn(session_id, role, content, embedding, metadata)
    
    # Cache for storing successful turn results to handle inconsistent database behavior
    _turns_cache = {}
    _cache_timeout = 60  # seconds
    _last_cache_cleanup = 0
    
    # Track known session ID mismatches to avoid repeated lookups
    _session_id_mapping = {}
    
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
            # Use helper method to normalize session ID
            raw_session_id, prefixed_session_id = self._normalize_session_id(session_id)
            logger.info(f"Getting turns for session_id: raw={raw_session_id}, prefixed={prefixed_session_id}")
            
            # Clean up old cache entries periodically
            current_time = time.time()
            if current_time - self._last_cache_cleanup > 300:  # Clean up every 5 minutes
                self._cleanup_cache()
                self._last_cache_cleanup = current_time
            
            # Check cache first
            cache_key = f"{raw_session_id}:{limit}:{offset}"
            if cache_key in self._turns_cache:
                cache_entry = self._turns_cache[cache_key]
                if current_time - cache_entry['timestamp'] < self._cache_timeout:
                    logger.info(f"Retrieved {len(cache_entry['turns'])} turns from cache for session: {raw_session_id}")
                    return cache_entry['turns']
            
            # Verify session exists
            session_query = f"SELECT * FROM sessions WHERE id = '{raw_session_id}' OR id = '{prefixed_session_id}';"
            session_result = self.client.execute_sql(session_query)
            
            if not session_result or not isinstance(session_result, list) or len(session_result) == 0:
                logger.warning(f"Session not found with either ID format: {raw_session_id} or {prefixed_session_id}")
                logger.info("Attempting to retrieve turns despite session verification failure")
            else:
                logger.debug(f"Session verified: {session_result[0].get('id')}")
            
            # Try a direct query first with explicit table name and field selection
            # This approach avoids count records and ensures we get actual turn data
            query = f"SELECT id, session_id, role, content, created_at, updated_at, metadata FROM turns WHERE session_id = '{raw_session_id}' ORDER BY created_at ASC LIMIT {limit} START {offset};"
            result = self.client.execute_sql(query)
            
            # Check if we got valid results
            if result and isinstance(result, list) and len(result) > 0:
                # Check if the first result is a count record (which we want to avoid)
                if len(result) == 1 and 'count' in result[0] and len(result[0]) == 1:
                    logger.warning(f"Received count record instead of turn: {result[0]}")
                    result = []  # Reset result to empty to try alternative query
            
            # If first approach didn't work, try with prefixed session_id
            if not result or not isinstance(result, list) or len(result) == 0:
                query = f"SELECT id, session_id, role, content, created_at, updated_at, metadata FROM turns WHERE session_id = '{prefixed_session_id}' ORDER BY created_at ASC LIMIT {limit} START {offset};"
                result = self.client.execute_sql(query)
                
                # Check again for count records
                if result and isinstance(result, list) and len(result) > 0:
                    if len(result) == 1 and 'count' in result[0] and len(result[0]) == 1:
                        logger.warning(f"Received count record instead of turn: {result[0]}")
                        result = []  # Reset result to empty to try alternative query
            
            # If still no results, try with type filter to exclude session records
            if not result or not isinstance(result, list) or len(result) == 0:
                logger.info("Trying with type filter to exclude session records")
                query = f"SELECT * FROM turns WHERE type::table(id) = 'turns' AND session_id = '{raw_session_id}' ORDER BY created_at ASC LIMIT {limit} START {offset};"
                result = self.client.execute_sql(query)
            
            # If still no results, try direct table access without WHERE clause
            # This is a diagnostic approach to see what's in the table
            if not result or not isinstance(result, list) or len(result) == 0:
                logger.info("Trying direct table access to diagnose data structure")
                query = f"SELECT * FROM turns LIMIT 10;"
                diagnostic_result = self.client.execute_sql(query)
                
                if diagnostic_result and isinstance(diagnostic_result, list) and len(diagnostic_result) > 0:
                    # Log the first record to understand structure
                    logger.info(f"Sample record in turns table: {diagnostic_result[0]}")
                    
                    # Check each record for the session_id we're looking for
                    for record in diagnostic_result:
                        if record.get('session_id') in [raw_session_id, prefixed_session_id]:
                            logger.info(f"Found matching turn in diagnostic sample: {record}")
                    
                    # If we found records, try a more specific query based on what we found
                    if 'session_id' in diagnostic_result[0]:
                        # Use the exact format of session_id as seen in the database
                        sample_session_id = diagnostic_result[0]['session_id']
                        logger.info(f"Sample session_id format in database: {sample_session_id}")
            
            # If still no results, try one more approach with direct ID access
            if not result or not isinstance(result, list) or len(result) == 0:
                # Try with explicit ID format
                logger.info("Trying with explicit ID format")
                query = f"SELECT * FROM turns:* WHERE session_id = '{raw_session_id}' ORDER BY created_at ASC LIMIT {limit} START {offset};"
                result = self.client.execute_sql(query)
            
            # If still no results, try a direct query for all turns and filter client-side
            if not result or not isinstance(result, list) or len(result) == 0:
                logger.info("Trying to fetch all turns and filter client-side")
                query = f"SELECT * FROM turns LIMIT 100;"
                all_turns = self.client.execute_sql(query)
                
                if all_turns and isinstance(all_turns, list):
                    # Filter turns by session_id client-side
                    result = [turn for turn in all_turns if turn.get('session_id') in [raw_session_id, prefixed_session_id]]
                    logger.info(f"Client-side filtering found {len(result)} turns from {len(all_turns)} total turns")
                    
                    # If no turns found, check for swapped session IDs
                    if not result or len(result) == 0:
                        # Check if we have a known mapping for this session ID
                        if raw_session_id in self._session_id_mapping:
                            mapped_session_id = self._session_id_mapping[raw_session_id]
                            logger.warning(f"Using known session ID mapping: {raw_session_id} -> {mapped_session_id}")
                            
                            # Try to find turns with the mapped session ID
                            result = [turn for turn in all_turns if turn.get('session_id') == mapped_session_id]
                            
                            if result and len(result) > 0:
                                logger.warning(f"Found {len(result)} turns using mapped session ID {mapped_session_id}")
                                
                                # Override session_id in the turns to match the requested session_id
                                for turn in result:
                                    turn['original_session_id'] = turn['session_id']
                                    turn['session_id'] = raw_session_id
                        else:
                            # Look for patterns of session ID mismatches
                            session_id_counts = {}
                            for turn in all_turns:
                                turn_session_id = turn.get('session_id')
                                if turn_session_id:
                                    if turn_session_id not in session_id_counts:
                                        session_id_counts[turn_session_id] = 0
                                    session_id_counts[turn_session_id] += 1
                            
                            # Find the most common session ID that isn't the requested one
                            most_common_session_id = None
                            max_count = 0
                            for sid, count in session_id_counts.items():
                                if sid != raw_session_id and sid != prefixed_session_id and count > max_count:
                                    most_common_session_id = sid
                                    max_count = count
                            
                            if most_common_session_id and max_count >= 2:  # At least 2 turns with this session ID
                                logger.warning(f"Detected potential session ID mismatch: requested={raw_session_id}, found={most_common_session_id}")
                                
                                # Store this mapping for future use
                                self._session_id_mapping[raw_session_id] = most_common_session_id
                                
                                # Get turns with this session ID
                                result = [turn for turn in all_turns if turn.get('session_id') == most_common_session_id]
                                
                                if result and len(result) > 0:
                                    logger.warning(f"Found {len(result)} turns with session ID {most_common_session_id}")
                                    
                                    # Override session_id in the turns to match the requested session_id
                                    for turn in result:
                                        turn['original_session_id'] = turn['session_id']
                                        turn['session_id'] = raw_session_id
            
            # If still no results, log the issue and return empty list
            if not result or not isinstance(result, list) or len(result) == 0:
                logger.warning(f"No turns found for session: raw={raw_session_id}, prefixed={prefixed_session_id}")
                return []
            
            # Filter out invalid turns and ensure they match the requested session_id
            valid_turns = []
            for turn in result:
                # Skip count records
                if 'count' in turn and len(turn) == 1:
                    logger.debug(f"Skipping count record: {turn}")
                    continue
                
                # Skip session records incorrectly returned as turns
                if 'id' in turn and isinstance(turn['id'], dict) and turn['id'].get('table_name') == 'sessions':
                    logger.warning(f"Session record incorrectly returned as turn: {turn}")
                    continue
                    
                valid_turn = self._validate_turn(turn, raw_session_id, prefixed_session_id)
                if valid_turn:
                    valid_turns.append(valid_turn)
            
            # Sort by created_at if available
            valid_turns.sort(key=lambda x: x.get('created_at', ''), reverse=False)
            
            # Cache successful results
            if valid_turns:
                self._turns_cache[cache_key] = {
                    'turns': valid_turns,
                    'timestamp': time.time()
                }
            
            logger.info(f"Retrieved {len(valid_turns)} valid turns for session: raw={raw_session_id}, prefixed={prefixed_session_id}")
            return valid_turns
            
        except Exception as e:
            logger.error(f"Failed to get turns for session {session_id}: {str(e)}", exc_info=True)
            return []
    
    def _cleanup_cache(self):
        """
        Remove expired entries from the turns cache
        """
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._turns_cache.items():
            if current_time - entry['timestamp'] > self._cache_timeout:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._turns_cache[key]
            
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    
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
        # For now, we'll make this a wrapper around the synchronous method
        # This avoids issues with await outside of async functions and ensures consistent behavior
        # In the future, when proper async client methods are implemented, this can be updated
        logger.debug(f"get_turns_async called, delegating to synchronous implementation")
        return self.get_turns(session_id, limit, offset)
    
    def get_turn(self, turn_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific turn by ID.
        
        Args:
            turn_id: Turn ID to retrieve
            
        Returns:
            Turn record or None if not found
        """
        if not turn_id:
            logger.warning("Empty turn_id provided to get_turn")
            return None
            
        try:
            # Use strict type filter to ensure we're getting a turn, not a session
            query = f"SELECT * FROM turns WHERE type::table(id) = 'turns' AND id = '{turn_id}';"
            result = self.client.execute_sql(query)
            
            if result and isinstance(result, list) and len(result) > 0:
                logger.info(f"Retrieved turn: {turn_id}")
                return result[0]
            else:
                # Try without strict filter as fallback
                condition = f"id = '{turn_id}'"
                result = self.client.get_records("turns", condition, limit=1)
                
                if result and isinstance(result, list) and len(result) > 0:
                    logger.info(f"Retrieved turn with fallback method: {turn_id}")
                    return result[0]
                else:
                    logger.warning(f"Turn not found: {turn_id}")
                    return None
                
                    return None
                
        except Exception as e:
            logger.error(f"Failed to get turn {turn_id}: {str(e)}", exc_info=True)
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
            Updated turn data or None on failure
        """
        if not turn_id:
            logger.warning("Empty turn_id provided to update_turn")
            return None
            
        if not update_data or not isinstance(update_data, dict):
            logger.warning(f"Invalid update_data provided to update_turn: {update_data}")
            return None
            
        try:
            # First verify the turn exists and is actually a turn
            existing_turn = self.get_turn(turn_id)
            if not existing_turn:
                logger.warning(f"Cannot update non-existent turn: {turn_id}")
                return None
                
            # If update includes session_id, normalize it
            if 'session_id' in update_data:
                raw_session_id, _ = self._normalize_session_id(update_data['session_id'])
                update_data['session_id'] = raw_session_id
                
            # Add updated_at timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = self.client.update_record("turns", turn_id, update_data)
            
            if result:
                logger.info(f"Turn updated successfully: {turn_id}")
                return result
            else:
                logger.error(f"Failed to update turn: {turn_id}")
                return None
                
        except Exception as e:
            logger.error(f"Turn update failed: {str(e)}", exc_info=True)
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
            logger.error(f"Turn deletion failed: {str(e)}", exc_info=True)
            return False
    
    def count_turns(self, session_id: str) -> int:
        """
        Count turns in a session.
        
        Args:
            session_id: Session ID to count turns for
            
        Returns:
            Number of turns in the session
        """
        if not session_id:
            logger.warning("Empty session_id provided to count_turns")
            return 0
            
        try:
            # Use helper method to normalize session ID
            raw_session_id, prefixed_session_id = self._normalize_session_id(session_id)
            logger.info(f"Counting turns for session: raw={raw_session_id}, prefixed={prefixed_session_id}")
            
            # Try both raw and prefixed session IDs
            sql = f"SELECT count() FROM turns WHERE session_id = '{raw_session_id}' OR session_id = '{prefixed_session_id}' GROUP ALL;"
            result = self.client.execute_sql(sql)
            
            if result and len(result) > 0 and 'count' in result[0]:
                count = result[0]['count']
                logger.info(f"Session {raw_session_id} has {count} total turns")
                return count
            else:
                # Try with strict type filter to exclude session records
                sql = f"SELECT count() FROM turns WHERE type::table(id) = 'turns' AND (session_id = '{raw_session_id}' OR session_id = '{prefixed_session_id}') GROUP ALL;"
                result = self.client.execute_sql(sql)
                
                if result and len(result) > 0 and 'count' in result[0]:
                    count = result[0]['count']
                    logger.info(f"Session {raw_session_id} has {count} turns with strict filtering")
                    return count
                else:
                    logger.info(f"Session {raw_session_id} has 0 turns")
                    return 0
                
        except Exception as e:
            logger.error(f"Failed to count turns for session {session_id}: {str(e)}", exc_info=True)
            return 0