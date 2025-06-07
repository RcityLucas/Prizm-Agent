"""
Unified Dialogue Processor using the new storage system.

This processor replaces the complex SQLite-based dialogue_processor.py
with a simple, SurrealDB-based implementation using unified storage.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from rainbow_agent.core.dialogue_manager import DialogueManager, DIALOGUE_TYPES
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage

# 配置日志
logger = logging.getLogger(__name__)


class UnifiedDialogueProcessor:
    """
    统一对话处理器
    
    使用新的统一存储系统处理对话，消除了复杂的SQLite逻辑
    和多种数据库交互方式的混用。
    """
    
    def __init__(self, 
                 storage: Optional[UnifiedDialogueStorage] = None,
                 dialogue_manager: Optional[DialogueManager] = None):
        """
        初始化统一对话处理器
        
        Args:
            storage: 统一存储实例
            dialogue_manager: 对话管理器实例
        """
        self.storage = storage or UnifiedDialogueStorage()
        self.dialogue_manager = dialogue_manager or DialogueManager(storage=self.storage)
        
        logger.info("UnifiedDialogueProcessor initialized")
    
    async def process_input(self, 
                           user_input: str,
                           user_id: str = "default_user",
                           session_id: Optional[str] = None,
                           input_type: str = "text",
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理用户输入并生成响应
        
        Args:
            user_input: 用户输入内容
            user_id: 用户ID
            session_id: 会话ID，如果不提供则自动创建
            input_type: 输入类型（text, image, audio等）
            context: 额外上下文信息
            
        Returns:
            包含响应和元数据的字典
        """
        try:
            # 1. 确保有会话ID
            if not session_id:
                session_id = await self._get_or_create_session(user_id, context)
            
            # 2. 处理输入并生成响应
            result = await self.dialogue_manager.process_input(
                session_id=session_id,
                user_id=user_id,
                content=user_input,
                input_type=input_type,
                metadata=context
            )
            
            # 3. 返回结果
            logger.info(f"Successfully processed input for user {user_id} in session {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process input: {e}")
            return {
                "id": str(uuid.uuid4()),
                "input": user_input,
                "response": f"处理输入时出现错误: {str(e)}",
                "sessionId": session_id or "unknown",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def process_input_sync(self, 
                          user_input: str,
                          user_id: str = "default_user",
                          session_id: Optional[str] = None,
                          input_type: str = "text",
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理用户输入并生成响应 (同步版本)
        
        Args:
            user_input: 用户输入内容
            user_id: 用户ID
            session_id: 会话ID，如果不提供则自动创建
            input_type: 输入类型（text, image, audio等）
            context: 额外上下文信息
            
        Returns:
            包含响应和元数据的字典
        """
        import asyncio
        return asyncio.run(self.process_input(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            input_type=input_type,
            context=context
        ))
    
    async def _get_or_create_session(self, 
                                    user_id: str, 
                                    context: Optional[Dict[str, Any]] = None) -> str:
        """
        获取或创建会话
        
        Args:
            user_id: 用户ID
            context: 上下文信息
            
        Returns:
            会话ID
        """
        try:
            # 尝试获取用户的最近会话
            recent_sessions = await self.storage.get_user_sessions_async(user_id, limit=1)
            
            if recent_sessions:
                # 如果有最近会话，使用它
                session = recent_sessions[0]
                if isinstance(session, dict) and 'id' in session:
                    session_id = session['id']
                    logger.info(f"Using existing session {session_id} for user {user_id}")
                    return session_id
                else:
                    logger.error(f"Existing session has invalid structure: {session}")
                    logger.error(f"Session type: {type(session)}, keys: {list(session.keys()) if isinstance(session, dict) else 'Not a dict'}")
                    # Fall through to create new session
            
            # 创建新会话 (moved outside of else block)
            dialogue_type = DIALOGUE_TYPES["HUMAN_AI_PRIVATE"]
            if context and "dialogue_type" in context:
                dialogue_type = context["dialogue_type"]
            
            session = await self.dialogue_manager.create_session(
                user_id=user_id,
                dialogue_type=dialogue_type,
                title=f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            if session:
                # Defensive check for session structure
                if isinstance(session, dict) and 'id' in session:
                    session_id = session['id']
                    logger.info(f"Created new session {session_id} for user {user_id}")
                    return session_id
                else:
                    logger.error(f"Session created but has invalid structure: {session}")
                    logger.error(f"Session type: {type(session)}, keys: {list(session.keys()) if isinstance(session, dict) else 'Not a dict'}")
                    raise Exception(f"Created session has invalid structure: {session}")
            else:
                raise Exception("Failed to create new session")
                    
        except Exception as e:
            logger.error(f"Failed to get or create session: {e}")
            raise
    
    async def get_session_history(self, 
                                 session_id: str, 
                                 limit: int = 100) -> Dict[str, Any]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            limit: 返回的最大轮次数量
            
        Returns:
            会话历史数据
        """
        try:
            session_with_turns = await self.storage.get_session_with_turns_async(session_id, limit)
            
            if session_with_turns:
                logger.info(f"Retrieved session history for {session_id}")
                return session_with_turns
            else:
                logger.warning(f"Session not found: {session_id}")
                return {
                    "error": "Session not found",
                    "session_id": session_id
                }
                
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return {
                "error": str(e),
                "session_id": session_id
            }
    
    async def get_user_sessions(self, 
                               user_id: str, 
                               limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取用户的会话列表
        
        Args:
            user_id: 用户ID
            limit: 返回的最大会话数量
            
        Returns:
            用户会话列表
        """
        try:
            sessions = await self.storage.get_user_sessions_async(user_id, limit)
            logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}")
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    async def create_new_session(self, 
                                user_id: str, 
                                title: str = "",
                                dialogue_type: str = DIALOGUE_TYPES["HUMAN_AI_PRIVATE"]) -> Dict[str, Any]:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            title: 会话标题
            dialogue_type: 对话类型
            
        Returns:
            新创建的会话信息
        """
        try:
            session = await self.dialogue_manager.create_session(
                user_id=user_id,
                dialogue_type=dialogue_type,
                title=title or f"New Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            if session:
                logger.info(f"Created new session {session['id']} for user {user_id}")
                return session
            else:
                raise Exception("Failed to create session")
                
        except Exception as e:
            logger.error(f"Failed to create new session: {e}")
            return {
                "error": str(e),
                "user_id": user_id
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            系统健康状态
        """
        try:
            storage_health = self.storage.health_check()
            
            return {
                "status": "healthy" if storage_health["status"] == "healthy" else "unhealthy",
                "storage": storage_health,
                "timestamp": datetime.now().isoformat(),
                "processor": "unified"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "processor": "unified"
            }


# 全局实例，用于API路由
_unified_processor = None

def get_unified_processor() -> UnifiedDialogueProcessor:
    """获取全局统一对话处理器实例"""
    global _unified_processor
    if _unified_processor is None:
        _unified_processor = UnifiedDialogueProcessor()
    return _unified_processor