"""
Unified Session Manager using the simplified, reliable approach.

This manager uses the UnifiedSurrealClient for all database operations,
eliminating complex fallback logic and HTTP endpoint mixing.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from .surreal.unified_client import UnifiedSurrealClient
from .models import SessionModel

logger = logging.getLogger(__name__)


class UnifiedSessionManager:
    """
    Unified session manager using reliable SQL-based operations.
    
    This class provides simple, transparent session management
    using only the official SurrealDB client.
    """
    
    def __init__(self, 
                 url: str = "ws://localhost:8000/rpc",
                 namespace: str = "rainbow",
                 database: str = "test",
                 username: str = "root",
                 password: str = "root",
                 client: Optional[Any] = None):
        """
        Initialize the session manager.
        
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
            logger.info("UnifiedSessionManager using provided client instance")
        else:
            # 创建持久UnifiedSurrealClient实例
            from .surreal.unified_client import UnifiedSurrealClient
            self.client = UnifiedSurrealClient(url, namespace, database, username, password)
            logger.info("UnifiedSessionManager created new client instance")
            
        # Ensure table structure exists
        self._ensure_table_structure()
        
        logger.info("UnifiedSessionManager initialized")
    
    def _ensure_table_structure(self) -> None:
        """Ensure the sessions table exists with proper schema."""
        try:
            fields = {
                "id": "string",
                "user_id": "string",
                "title": "string",
                "created_at": "datetime",
                "updated_at": "datetime",
                "status": "string",
                "metadata": "option<object>"
            }
            
            self.client.ensure_table("sessions", fields)
            logger.info("Sessions table structure ensured")
            
        except Exception as e:
            logger.error(f"Failed to ensure table structure: {e}")
    
    def create_session(self, 
                      user_id: str, 
                      title: str = "",
                      metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new session.
        
        Args:
            user_id: User ID who owns this session
            title: Session title
            metadata: Optional metadata
            
        Returns:
            Created session data or None on failure
        """
        try:
            # Create session model
            session_model = SessionModel(
                user_id=user_id,
                title=title or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                metadata=metadata or {}
            )
            
            # Convert to dictionary
            session_data = session_model.to_dict()
            
            logger.info(f"Creating session: {session_model.id} for user: {user_id}")
            
            # Create record using unified client
            result = self.client.create_record("sessions", session_data)
            
            if result:
                logger.info(f"Session created successfully: {session_model.id}")
                return result
            else:
                logger.error(f"Failed to create session: {session_model.id}")
                return None
                
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            return None
    
    async def create_session_async(self, 
                                  user_id: str, 
                                  title: str = "",
                                  metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new session asynchronously.
        
        Args:
            user_id: User ID who owns this session
            title: Session title
            metadata: Optional metadata
            
        Returns:
            Created session data or None on failure
        """
        # For now, use the synchronous method
        return self.create_session(user_id, title, metadata)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific session by ID.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Session record or None if not found
        """
        try:
            condition = f"id = '{session_id}'"
            result = self.client.get_records("sessions", condition, limit=1)
            
            if result:
                logger.info(f"Retrieved session: {session_id}")
                return result[0]
            else:
                logger.warning(f"Session not found: {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def get_session_async(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific session by ID asynchronously.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Session record or None if not found
        """
        # For now, use the synchronous method
        return self.get_session(session_id)
    
    def get_user_sessions(self, 
                         user_id: str, 
                         limit: int = 100, 
                         offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get sessions for a user.
        
        Args:
            user_id: User ID to get sessions for
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of session records
        """
        try:
            condition = f"user_id = '{user_id}'"
            
            result = self.client.get_records("sessions", condition, limit, offset)
            
            logger.info(f"Retrieved {len(result)} sessions for user: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            return []
    
    async def get_user_sessions_async(self, 
                                     user_id: str, 
                                     limit: int = 100, 
                                     offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get sessions for a user asynchronously.
        
        Args:
            user_id: User ID to get sessions for
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of session records
        """
        # For now, use the synchronous method
        return self.get_user_sessions(user_id, limit, offset)
    
    def update_session(self, 
                      session_id: str, 
                      update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a session.
        
        Args:
            session_id: Session ID to update
            update_data: Data to update
            
        Returns:
            Updated session record or None on failure
        """
        try:
            # Add updated_at timestamp
            update_data['updated_at'] = datetime.now().isoformat()
            
            result = self.client.update_record("sessions", session_id, update_data)
            
            if result:
                logger.info(f"Session updated successfully: {session_id}")
                return result
            else:
                logger.error(f"Failed to update session: {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Session update failed: {e}")
            return None
    
    async def update_session_async(self, 
                                  session_id: str, 
                                  update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a session asynchronously.
        
        Args:
            session_id: Session ID to update
            update_data: Data to update
            
        Returns:
            Updated session record or None on failure
        """
        # For now, use the synchronous method
        return self.update_session(session_id, update_data)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.delete_record("sessions", session_id)
            
            if result:
                logger.info(f"Session deleted successfully: {session_id}")
                return True
            else:
                logger.error(f"Failed to delete session: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Session deletion failed: {e}")
            return False
    
    def count_user_sessions(self, user_id: str) -> int:
        """
        Count sessions for a user.
        
        Args:
            user_id: User ID to count sessions for
            
        Returns:
            Number of sessions for the user
        """
        try:
            sql = f"SELECT count() FROM sessions WHERE user_id = '{user_id}' GROUP ALL;"
            result = self.client.execute_sql(sql)
            
            if result and len(result) > 0 and 'count' in result[0]:
                count = result[0]['count']
                logger.info(f"User {user_id} has {count} sessions")
                return count
            else:
                logger.info(f"User {user_id} has 0 sessions")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to count sessions for user {user_id}: {e}")
            return 0