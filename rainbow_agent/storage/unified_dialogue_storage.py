"""
Unified Dialogue Storage System using simplified, reliable approach.

This system replaces the complex DialogueStorageSystem with a simple,
transparent interface using the unified managers.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .unified_session_manager import UnifiedSessionManager
from .unified_turn_manager import UnifiedTurnManager
from .memory_storage import get_memory_storage
from .config import get_surreal_config

logger = logging.getLogger(__name__)


class UnifiedDialogueStorage:
    """
    Unified dialogue storage system.
    
    This class provides a simple, unified interface for all dialogue storage
    operations, using the reliable unified managers that eliminate complex
    HTTP endpoint mixing and fallback logic.
    """
    
    def __init__(self, 
                 url: Optional[str] = None,
                 namespace: Optional[str] = None,
                 database: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize the unified dialogue storage system.
        
        Args:
            url: SurrealDB WebSocket URL (optional, uses config if not provided)
            namespace: SurrealDB namespace (optional, uses config if not provided)
            database: SurrealDB database name (optional, uses config if not provided)
            username: SurrealDB username (optional, uses config if not provided)
            password: SurrealDB password (optional, uses config if not provided)
        """
        # Get configuration
        config = get_surreal_config()
        
        # Use provided values or fall back to config
        self.url = url or config["url"]
        self.namespace = namespace or config["namespace"]
        self.database = database or config["database"]
        self.username = username or config["username"]
        self.password = password or config["password"]
        self.health_url = config["health_url"]
        
        # Initialize managers with configuration
        self.session_manager = UnifiedSessionManager(
            self.url, self.namespace, self.database, self.username, self.password
        )
        self.turn_manager = UnifiedTurnManager(
            self.url, self.namespace, self.database, self.username, self.password
        )
        
        # Initialize memory storage as fallback
        self.memory_storage = get_memory_storage()
        
        # Test database connectivity
        try:
            # First check if the HTTP endpoint is accessible
            import requests
            response = requests.get(self.health_url, timeout=2)
            if response.status_code == 200:
                # Try a simple operation to check if database is working
                test_sessions = self.session_manager.get_user_sessions("__connectivity_test__", limit=1)
                # Check if the result is valid (not a SQL string response)
                if isinstance(test_sessions, list) and (len(test_sessions) == 0 or all(isinstance(s, dict) and 'sql' not in s for s in test_sessions)):
                    self.db_available = True
                    logger.info("UnifiedDialogueStorage initialized with SurrealDB connectivity")
                else:
                    logger.warning("SurrealDB returning invalid responses, using memory storage fallback")
                    self.db_available = False
            else:
                logger.warning("SurrealDB health check failed, using memory storage fallback")
                self.db_available = False
        except Exception as e:
            logger.warning(f"SurrealDB not available, using memory storage fallback: {e}")
            self.db_available = False
        
        logger.info("UnifiedDialogueStorage initialized")
    
    # ===== Session Operations =====
    
    def create_session(self, 
                      user_id: str, 
                      title: str = "",
                      metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new dialogue session.
        
        Args:
            user_id: User ID who owns this session
            title: Session title
            metadata: Optional metadata
            
        Returns:
            Created session data or None on failure
        """
        if self.db_available:
            try:
                result = self.session_manager.create_session(user_id, title, metadata)
                if result:
                    return result
                else:
                    logger.warning("SurrealDB session creation failed, falling back to memory")
                    self.db_available = False
            except Exception as e:
                logger.warning(f"SurrealDB session creation error, falling back to memory: {e}")
                self.db_available = False
        
        # Use memory storage fallback
        return self.memory_storage.create_session(user_id, title, metadata)
    
    async def create_session_async(self, 
                                  user_id: str, 
                                  title: str = "",
                                  metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Create a new dialogue session asynchronously."""
        if self.db_available:
            try:
                result = await self.session_manager.create_session_async(user_id, title, metadata)
                if result:
                    return result
                else:
                    logger.warning("SurrealDB async session creation failed, falling back to memory")
                    self.db_available = False
            except Exception as e:
                logger.warning(f"SurrealDB async session creation error, falling back to memory: {e}")
                self.db_available = False
        
        # Use memory storage fallback
        return self.memory_storage.create_session(user_id, title, metadata)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        if self.db_available:
            try:
                result = self.session_manager.get_session(session_id)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"SurrealDB get session error, falling back to memory: {e}")
                self.db_available = False
        
        # Use memory storage fallback
        return self.memory_storage.get_session(session_id)
    
    async def get_session_async(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID asynchronously."""
        if self.db_available:
            try:
                result = await self.session_manager.get_session_async(session_id)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"SurrealDB get session async error, falling back to memory: {e}")
                self.db_available = False
        
        # Use memory storage fallback
        return self.memory_storage.get_session(session_id)
    
    def get_user_sessions(self, 
                         user_id: str, 
                         limit: int = 100, 
                         offset: int = 0) -> List[Dict[str, Any]]:
        """Get sessions for a user."""
        if self.db_available:
            try:
                result = self.session_manager.get_user_sessions(user_id, limit, offset)
                if result is not None:  # Allow empty list as valid result
                    return result
            except Exception as e:
                logger.warning(f"SurrealDB get user sessions error, falling back to memory: {e}")
                self.db_available = False
        
        # Use memory storage fallback
        return self.memory_storage.get_user_sessions(user_id, limit, offset)
    
    async def get_user_sessions_async(self, 
                                     user_id: str, 
                                     limit: int = 100, 
                                     offset: int = 0) -> List[Dict[str, Any]]:
        """Get sessions for a user asynchronously."""
        if self.db_available:
            try:
                result = await self.session_manager.get_user_sessions_async(user_id, limit, offset)
                if result is not None:  # Allow empty list as valid result
                    return result
            except Exception as e:
                logger.warning(f"SurrealDB get user sessions async error, falling back to memory: {e}")
                self.db_available = False
        
        # Use memory storage fallback
        return self.memory_storage.get_user_sessions(user_id, limit, offset)
    
    def update_session(self, 
                      session_id: str, 
                      update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a session."""
        return self.session_manager.update_session(session_id, update_data)
    
    async def update_session_async(self, 
                                  session_id: str, 
                                  update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a session asynchronously."""
        return await self.session_manager.update_session_async(session_id, update_data)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        return self.session_manager.delete_session(session_id)
    
    # ===== Turn Operations =====
    
    def create_turn(self, 
                   session_id: str, 
                   role: str, 
                   content: str, 
                   embedding: Optional[List[float]] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new dialogue turn.
        
        Args:
            session_id: Session ID this turn belongs to
            role: Role of the speaker (human, ai, system, etc.)
            content: Content of the turn
            embedding: Optional embedding vector
            metadata: Optional metadata
            
        Returns:
            Created turn data or None on failure
        """
        if self.db_available:
            try:
                result = self.turn_manager.create_turn(session_id, role, content, embedding, metadata)
                if result:
                    return result
                else:
                    logger.warning("SurrealDB turn creation failed, falling back to memory")
                    self.db_available = False
            except Exception as e:
                logger.warning(f"SurrealDB turn creation error, falling back to memory: {e}")
                self.db_available = False
        
        # Use memory storage fallback
        return self.memory_storage.create_turn(session_id, role, content, embedding, metadata)
    
    async def create_turn_async(self, 
                               session_id: str, 
                               role: str, 
                               content: str, 
                               embedding: Optional[List[float]] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Create a new dialogue turn asynchronously."""
        if self.db_available:
            try:
                result = await self.turn_manager.create_turn_async(session_id, role, content, embedding, metadata)
                if result:
                    return result
                else:
                    logger.warning("SurrealDB async turn creation failed, falling back to memory")
                    self.db_available = False
            except Exception as e:
                logger.warning(f"SurrealDB async turn creation error, falling back to memory: {e}")
                self.db_available = False
        
        # Use memory storage fallback
        return self.memory_storage.create_turn(session_id, role, content, embedding, metadata)
    
    def get_turn(self, turn_id: str) -> Optional[Dict[str, Any]]:
        """Get a turn by ID."""
        return self.turn_manager.get_turn(turn_id)
    
    def get_turns(self, 
                 session_id: str, 
                 limit: int = 100, 
                 offset: int = 0) -> List[Dict[str, Any]]:
        """Get turns for a session."""
        if self.db_available:
            try:
                result = self.turn_manager.get_turns(session_id, limit, offset)
                if result is not None:  # Allow empty list as valid result
                    return result
            except Exception as e:
                logger.warning(f"SurrealDB get turns error, falling back to memory: {e}")
                self.db_available = False
        
        # Use memory storage fallback
        return self.memory_storage.get_turns(session_id, limit, offset)
    
    async def get_turns_async(self, 
                             session_id: str, 
                             limit: int = 100, 
                             offset: int = 0) -> List[Dict[str, Any]]:
        """Get turns for a session asynchronously."""
        if self.db_available:
            try:
                result = await self.turn_manager.get_turns_async(session_id, limit, offset)
                if result is not None:  # Allow empty list as valid result
                    return result
            except Exception as e:
                logger.warning(f"SurrealDB get turns async error, falling back to memory: {e}")
                self.db_available = False
        
        # Use memory storage fallback
        return self.memory_storage.get_turns(session_id, limit, offset)
    
    def update_turn(self, 
                   turn_id: str, 
                   update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a turn."""
        return self.turn_manager.update_turn(turn_id, update_data)
    
    def delete_turn(self, turn_id: str) -> bool:
        """Delete a turn."""
        return self.turn_manager.delete_turn(turn_id)
    
    # ===== Convenience Methods =====
    
    def get_session_with_turns(self, 
                              session_id: str, 
                              turn_limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        Get a session with its turns.
        
        Args:
            session_id: Session ID to retrieve
            turn_limit: Maximum number of turns to include
            
        Returns:
            Session data with turns included, or None if not found
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return None
            
            turns = self.get_turns(session_id, limit=turn_limit)
            session['turns'] = turns
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session with turns: {e}")
            return None
    
    async def get_session_with_turns_async(self, 
                                          session_id: str, 
                                          turn_limit: int = 100) -> Optional[Dict[str, Any]]:
        """Get a session with its turns asynchronously."""
        try:
            session = await self.get_session_async(session_id)
            if not session:
                return None
            
            turns = await self.get_turns_async(session_id, limit=turn_limit)
            session['turns'] = turns
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session with turns async: {e}")
            return None
    
    def count_user_sessions(self, user_id: str) -> int:
        """Count sessions for a user."""
        return self.session_manager.count_user_sessions(user_id)
    
    def count_session_turns(self, session_id: str) -> int:
        """Count turns in a session."""
        return self.turn_manager.count_turns(session_id)
    
    # ===== Health Check =====
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the storage system.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Try a simple query to test connectivity
            test_sessions = self.session_manager.get_user_sessions("test_user", limit=1)
            
            return {
                "status": "healthy",
                "connection": "ok",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "connection": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }