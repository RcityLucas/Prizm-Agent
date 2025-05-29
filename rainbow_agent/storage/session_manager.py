"""
会话管理器

使用SurrealDB存储系统管理会话，继承自BaseManager
"""
import os
import uuid
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_manager import BaseManager
from .models import SessionModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SessionManager(BaseManager):
    """会话管理器，继承自BaseManager"""
    
    # 内存缓存
    _session_cache = {}
    
    def __init__(self, 
                 url: Optional[str] = None,
                 namespace: Optional[str] = None,
                 database: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """初始化会话管理器
        
        Args:
            url: SurrealDB服务器URL
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
        """
        super().__init__(url, namespace, database, username, password, "SessionManager")
        
        # 确保表结构存在
        self._ensure_table_structure()
        
    def _ensure_table_structure(self):
        """确保表结构存在"""
        try:
            # 创建会话表
            create_sessions_table_sql = """
            DEFINE TABLE sessions SCHEMAFULL;
            DEFINE FIELD id ON sessions TYPE string;
            DEFINE FIELD user_id ON sessions TYPE string;
            DEFINE FIELD title ON sessions TYPE string;
            DEFINE FIELD dialogue_type ON sessions TYPE string;
            DEFINE FIELD created_at ON sessions TYPE datetime;
            DEFINE FIELD updated_at ON sessions TYPE datetime;
            DEFINE FIELD last_activity_at ON sessions TYPE datetime;
            DEFINE FIELD summary ON sessions TYPE string;
            DEFINE FIELD topics ON sessions TYPE array;
            DEFINE FIELD sentiment ON sessions TYPE string;
            DEFINE FIELD metadata ON sessions TYPE object;
            """
            self.execute_sql(create_sessions_table_sql)
            logger.info("会话表结构初始化成功")
        except Exception as e:
            logger.warning(f"会话表结构初始化失败，可能已存在: {e}")
    

    
    async def create_session(self, user_id: str, title: Optional[str] = None,
                    dialogue_type: str = "human_to_ai_private",
                    summary: Optional[str] = None,
                    topics: Optional[List[str]] = None,
                    sentiment: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建新会话
        
        Args:
            user_id: 用户ID
            title: 会话标题，如果不提供则使用默认标题
            dialogue_type: 对话类型
            summary: 对话摘要
            topics: 对话主题标签列表
            sentiment: 整体情感基调
            metadata: 元数据
            
        Returns:
            创建的会话
        """
        try:
            # 创建会话模型
            session_model = SessionModel(
                user_id=user_id,
                title=title,
                dialogue_type=dialogue_type,
                summary=summary,
                topics=topics,
                sentiment=sentiment,
                metadata=metadata
            )
            
            # 转换为字典
            session_data = session_model.to_dict()
            
            # 使用SQL直接创建完整记录
            logger.info(f"使用SQL直接创建会话: {session_model.id}")
            
            # 构建SQL语句
            sql = self._build_insert_sql("sessions", session_data)
            
            # 执行SQL
            logger.info(f"创建会话SQL: {sql}")
            self.client.execute_sql(sql)
            
            # 将新创建的会话添加到内存缓存
            SessionManager._session_cache[session_model.id] = session_model
            
            # 返回创建的会话
            logger.info(f"会话创建成功: {session_model.id}")
            return session_data
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise
    
    async def get_sessions(self, user_id: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """获取会话列表
        
        Args:
            user_id: 用户ID，如果提供则只返回该用户的会话
            limit: 限制返回的会话数
            offset: 跳过的会话数
            
        Returns:
            会话列表
        """
        try:
            # 构建查询条件
            condition = f"user_id = '{user_id}'" if user_id else ""
            
            # 获取记录列表
            sessions_data = self.get_records("sessions", condition, limit, offset)
            
            # 转换为模型并添加到内存缓存
            sessions = []
            for session_data in sessions_data:
                session_model = SessionModel.from_dict(session_data)
                session_id = session_model.id
                if session_id:
                    SessionManager._session_cache[session_id] = session_model
                sessions.append(session_model.to_dict())
            
            logger.info(f"获取会话列表成功，共 {len(sessions)} 个")
            return sessions
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取特定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，如果不存在则返回None
        """
        try:
            # 先检查内存缓存
            if session_id in SessionManager._session_cache:
                logger.info(f"从内存缓存中获取会话: {session_id}")
                cached_session = SessionManager._session_cache[session_id]
                
                # 如果缓存中的是模型，转换为字典
                if isinstance(cached_session, SessionModel):
                    return cached_session.to_dict()
                elif isinstance(cached_session, dict):
                    return cached_session
                return cached_session
            
            # 如果内存缓存中没有，从数据库获取
            logger.info(f"从数据库获取会话: {session_id}")
            session_data = self.get_record("sessions", session_id)
            
            if session_data:
                # 创建会话模型
                session_model = SessionModel.from_dict(session_data)
                
                # 将会话添加到内存缓存
                SessionManager._session_cache[session_id] = session_model
                logger.info(f"会话获取成功并添加到内存缓存: {session_id}")
                return session_model.to_dict()
            else:
                logger.info(f"会话 {session_id} 不存在")
                return None
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新会话
        
        Args:
            session_id: 会话ID
            updates: 要更新的字段
            
        Returns:
            更新后的会话，如果会话不存在则返回None
        """
        try:
            # 首先检查会话是否存在
            existing_session = await self.get_session(session_id)
            if not existing_session:
                logger.info(f"会话 {session_id} 不存在，无法更新")
                return None
            
            # 添加更新时间
            if "updated_at" not in updates:
                updates["updated_at"] = datetime.now().isoformat()
            
            # 更新会话
            updated_session_data = self.update_record("sessions", session_id, updates)
            
            if updated_session_data:
                # 创建会话模型
                updated_session = SessionModel.from_dict(updated_session_data)
                
                # 更新内存缓存
                SessionManager._session_cache[session_id] = updated_session
                logger.info(f"更新会话 {session_id} 成功并更新内存缓存")
                return updated_session.to_dict()
            else:
                logger.info(f"会话 {session_id} 更新失败")
                return None
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            # 删除会话
            result = self.delete_record("sessions", session_id)
            
            # 如果删除成功，从内存缓存中移除
            if result and session_id in SessionManager._session_cache:
                del SessionManager._session_cache[session_id]
            
            if result:
                logger.info(f"删除会话 {session_id} 成功")
            else:
                logger.info(f"会话 {session_id} 不存在，无法删除")
            
            return result
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
    
    async def record_activity(self, session_id: str) -> bool:
        """记录会话活动
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否记录成功
        """
        try:
            # 更新最后活动时间
            updates = {
                "last_activity_at": datetime.now().isoformat()
            }
            
            # 更新会话
            updated_session = await self.update_session(session_id, updates)
            
            if updated_session:
                logger.info(f"记录会话 {session_id} 活动成功")
                return True
            else:
                logger.info(f"会话 {session_id} 不存在，无法记录活动")
                return False
        except Exception as e:
            logger.error(f"记录会话活动失败: {e}")
            return False
