"""
Unified Turn Manager using the simplified, reliable approach.

This manager uses the UnifiedSurrealClient for all database operations,
eliminating complex fallback logic and HTTP endpoint mixing.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
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
            fields = {
                "id": "string",
                "session_id": "string",
                "role": "string", 
                "content": "string",
                "created_at": "datetime",
                "updated_at": "datetime",
                "embedding": "option<array>",
                "metadata": "option<object>"
            }
            
            self.client.ensure_table("turns", fields)
            logger.info("Turns table structure ensured")
            
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
            # Create turn model
            turn_model = TurnModel(
                session_id=session_id,
                role=role,
                content=content,
                embedding=embedding,
                metadata=metadata or {}
            )
            
            # Convert to dictionary
            turn_data = turn_model.to_dict()
            
            logger.info(f"Creating turn: {turn_model.id} for session: {session_id}")
            
            # Create record using unified client
            result = self.client.create_record("turns", turn_data)
            
            if result:
                logger.info(f"Turn created successfully: {turn_model.id}")
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
        # For now, use the synchronous method
        # In the future, we can implement true async using asyncio.to_thread
        return self.create_turn(session_id, role, content, embedding, metadata)
    
    def get_turns(self, 
                 session_id: str, 
                 limit: int = 100, 
                 offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get turns for a session.
        
        Args:
            session_id: Session ID to get turns for
            limit: Maximum number of turns to return
            offset: Number of turns to skip
            
        Returns:
            List of turn records
        """
        try:
            # 处理session_id可能是字典的情况
            actual_session_id = session_id
            if isinstance(session_id, dict) and 'id' in session_id:
                actual_session_id = session_id['id']
                logger.info(f"Extracted session_id from dictionary: {actual_session_id}")
            
            condition = f"session_id = '{actual_session_id}'"
            
            # 获取记录并按created_at字段排序
            result = self.client.get_records("turns", condition, limit, offset)
            
            # 确保按照创建时间排序
            if result:
                result.sort(key=lambda x: x.get('created_at', ''))
                logger.info(f"Retrieved and sorted {len(result)} turns for session: {actual_session_id}")
            else:
                logger.info(f"Retrieved {len(result)} turns for session: {actual_session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get turns for session {session_id}: {e}")
            return []
    
    async def get_turns_async(self, 
                             session_id: str, 
                             limit: int = 100, 
                             offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get turns for a session asynchronously.
        
        Args:
            session_id: Session ID to get turns for
            limit: Maximum number of turns to return
            offset: Number of turns to skip
            
        Returns:
            List of turn records
        """
        # For now, use the synchronous method
        return self.get_turns(session_id, limit, offset)
    
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