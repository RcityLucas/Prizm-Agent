"""
In-memory storage implementation as a reliable fallback.

This provides the same interface as the SurrealDB storage but stores data in memory.
Useful for development and as a fallback when database connection fails.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MemoryStorage:
    """
    In-memory storage that mimics the SurrealDB interface.
    
    This provides a reliable storage solution when database connection fails.
    Data is stored in memory dictionaries with the same structure.
    """
    
    def __init__(self):
        """Initialize memory storage."""
        self.sessions = {}  # session_id -> session_data
        self.turns = {}     # turn_id -> turn_data
        self.user_sessions = {}  # user_id -> [session_ids]
        
        logger.info("Memory storage initialized")
    
    def create_session(self, user_id: str, title: str = "", metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Create a session in memory."""
        try:
            session_id = str(uuid.uuid4()).replace('-', '')
            now = datetime.now().isoformat()
            
            session_data = {
                'id': session_id,
                'user_id': user_id,
                'title': title or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                'created_at': now,
                'updated_at': now,
                'status': 'active',
                'metadata': metadata or {}
            }
            
            # Store session
            self.sessions[session_id] = session_data
            
            # Track user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)
            
            logger.info(f"Memory storage: Created session {session_id} for user {user_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create session in memory: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session from memory."""
        session = self.sessions.get(session_id)
        if session:
            logger.debug(f"Memory storage: Retrieved session {session_id}")
        else:
            logger.debug(f"Memory storage: Session {session_id} not found")
        return session
    
    def get_user_sessions(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get sessions for a user from memory."""
        session_ids = self.user_sessions.get(user_id, [])
        
        # Apply pagination
        paginated_ids = session_ids[offset:offset + limit]
        
        # Get session data
        sessions = []
        for session_id in paginated_ids:
            session = self.sessions.get(session_id)
            if session:
                sessions.append(session)
        
        logger.debug(f"Memory storage: Retrieved {len(sessions)} sessions for user {user_id}")
        return sessions
    
    def create_turn(self, session_id: str, role: str, content: str, embedding: Optional[List[float]] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Create a turn in memory."""
        try:
            turn_id = str(uuid.uuid4()).replace('-', '')
            now = datetime.now().isoformat()
            
            turn_data = {
                'id': turn_id,
                'session_id': session_id,
                'role': role,
                'content': content,
                'created_at': now,
                'updated_at': now,
                'embedding': embedding or [],
                'metadata': metadata or {}
            }
            
            # Store turn
            self.turns[turn_id] = turn_data
            
            logger.info(f"Memory storage: Created turn {turn_id} for session {session_id}")
            return turn_data
            
        except Exception as e:
            logger.error(f"Failed to create turn in memory: {e}")
            return None
    
    def get_turns(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get turns for a session from memory."""
        # Find all turns for this session
        session_turns = []
        for turn in self.turns.values():
            if turn.get('session_id') == session_id:
                session_turns.append(turn)
        
        # Sort by created_at
        session_turns.sort(key=lambda t: t.get('created_at', ''))
        
        # Apply pagination
        paginated_turns = session_turns[offset:offset + limit]
        
        logger.debug(f"Memory storage: Retrieved {len(paginated_turns)} turns for session {session_id}")
        return paginated_turns
    
    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a session in memory."""
        if session_id in self.sessions:
            # Update the session data
            self.sessions[session_id].update(update_data)
            self.sessions[session_id]['updated_at'] = datetime.now().isoformat()
            
            logger.info(f"Memory storage: Updated session {session_id}")
            return self.sessions[session_id]
        else:
            logger.warning(f"Memory storage: Session {session_id} not found for update")
            return None
    
    def count_user_sessions(self, user_id: str) -> int:
        """Count sessions for a user."""
        count = len(self.user_sessions.get(user_id, []))
        logger.debug(f"Memory storage: User {user_id} has {count} sessions")
        return count
    
    def count_turns(self, session_id: str) -> int:
        """Count turns in a session."""
        count = sum(1 for turn in self.turns.values() if turn.get('session_id') == session_id)
        logger.debug(f"Memory storage: Session {session_id} has {count} turns")
        return count


# Global memory storage instance
_memory_storage = None

def get_memory_storage() -> MemoryStorage:
    """Get the global memory storage instance."""
    global _memory_storage
    if _memory_storage is None:
        _memory_storage = MemoryStorage()
    return _memory_storage