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
from .unified_turn_vector_manager import UnifiedTurnVectorManager
from .memory_storage import get_memory_storage
from rainbow_agent.config.settings import get_settings
from ..utils.vector_utils import cosine_similarity, sort_by_similarity

logger = logging.getLogger(__name__)


class UnifiedDialogueStorage:
    """
    Unified dialogue storage system.
    
    This class provides a simple, unified interface for all dialogue storage
    operations, using the reliable unified managers that eliminate complex
    HTTP endpoint mixing and fallback logic.
    """
    
    def __init__(self, 
                 url: str = "ws://localhost:8000/rpc",
                 namespace: str = "rainbow",
                 database: str = "test",
                 username: str = "root",
                 password: str = "root"):
        """
        Initialize the unified dialogue storage.
        
        Args:
            url: SurrealDB WebSocket URL
            namespace: SurrealDB namespace
            database: SurrealDB database name
            username: SurrealDB username
            password: SurrealDB password
        """
        self.url = url
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        
        # 从中央配置系统获取SurrealDB配置
        settings = get_settings()
        storage_config = settings.get("storage", {})
        
        # 如果提供了参数，则使用参数值，否则使用配置中的值
        self.url = url if url != "ws://localhost:8000/rpc" else storage_config.get("url", url)
        self.namespace = namespace if namespace != "rainbow" else storage_config.get("namespace", namespace)
        self.database = database if database != "test" else storage_config.get("database", database)
        self.username = username if username != "root" else storage_config.get("username", username)
        self.password = password if password != "root" else storage_config.get("password", password)
        
        # 获取健康检查URL
        self.health_url = storage_config.get("health_url", self.url.replace("ws://", "http://").replace("/rpc", "/health"))
        
        # 创建一个共享的UnifiedSurrealClient实例
        from .surreal.unified_client import UnifiedSurrealClient
        self.shared_client = UnifiedSurrealClient(
            self.url, self.namespace, self.database, self.username, self.password
        )
        
        # 初始化管理器并直接传递共享客户端实例
        self.session_manager = UnifiedSessionManager(
            url=self.url, namespace=self.namespace, database=self.database, 
            username=self.username, password=self.password,
            client=self.shared_client
        )
        self.turn_manager = UnifiedTurnManager(
            url=self.url, namespace=self.namespace, database=self.database, 
            username=self.username, password=self.password,
            client=self.shared_client
        )
        # 初始化向量管理器
        self.turn_vector_manager = UnifiedTurnVectorManager(
            url=self.url, namespace=self.namespace, database=self.database, 
            username=self.username, password=self.password,
            client=self.shared_client
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
        db_used = False
        db_result = None
        db_error = None
        
        # First try using database (don't check self.db_available to allow retry even after previous failure)
        try:
            logger.debug(f"Attempting to get turns from database for session_id: {session_id}")
            db_result = await self.turn_manager.get_turns_async(session_id, limit, offset)
            if db_result is not None:  # Allow empty list as valid result
                logger.info(f"Successfully retrieved {len(db_result)} turns from database for session: {session_id}")
                # DB access is working, ensure flag is set to True
                self.db_available = True
                db_used = True
                return db_result
        except Exception as e:
            db_error = str(e)
            logger.warning(f"SurrealDB get turns async error: {e}")
            # Don't set self.db_available = False here to avoid permanently disabling DB
        
        # Only if database access failed, use memory storage fallback
        if not db_used:
            logger.warning(f"Using memory storage fallback for session: {session_id} (DB error: {db_error})")
            memory_turns = self.memory_storage.get_turns(session_id, limit, offset)
            
            # Ensure strict session_id matching in memory fallback
            filtered_turns = [turn for turn in memory_turns if turn.get('session_id') == session_id]
            
            if len(filtered_turns) != len(memory_turns):
                logger.warning(f"Memory storage returned turns from other sessions! Filtered {len(memory_turns)-len(filtered_turns)} invalid turns.")
            
            return filtered_turns
    
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
    
    # ===== Vector Search =====
    
    async def search_similar_turns(self, 
                                  query_embedding: List[float], 
                                  session_id: Optional[str] = None,
                                  top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索与查询向量相似的对话轮次
        
        Args:
            query_embedding: 查询嵌入向量
            session_id: 会话ID，如果为None则搜索所有会话
            top_k: 返回的最相似结果数量
            
        Returns:
            按相似度降序排序的对话轮次列表，每个轮次增加一个"similarity"字段
        """
        if self.db_available:
            try:
                result = await self.turn_vector_manager.search_similar_turns(
                    query_embedding=query_embedding,
                    session_id=session_id,
                    top_k=top_k
                )
                if result is not None:  # Allow empty list as valid result
                    return result
            except Exception as e:
                logger.warning(f"SurrealDB vector search error, falling back to memory: {e}")
                self.db_available = False
        
        # 如果数据库不可用，尝试从内存存储中搜索（如果内存存储支持）
        # 注意：标准内存存储可能不支持向量搜索，这里只是一个框架
        logger.warning("数据库不可用，内存存储可能不支持向量搜索")
        return []
    
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

    async def init_db(self) -> bool:
        """初始化数据库"""
        try:
            # 初始化会话和轮次管理器
            await self.session_manager.connect()
            await self.turn_manager.connect()
            await self.turn_vector_manager.connect()
            
            # 初始化向量存储模式
            await self.init_vector_storage_schema()
            
            return True
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            return False
            
    async def init_vector_storage_schema(self) -> bool:
        """初始化向量存储模式
        
        确保turns表有正确的嵌入向量字段和索引
        
        Returns:
            初始化是否成功
        """
        try:
            return await self.turn_vector_manager.init_vector_storage_schema()
        except Exception as e:
            logger.error(f"初始化向量存储模式失败: {e}")
            return False