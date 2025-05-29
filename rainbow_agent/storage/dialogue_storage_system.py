"""
对话存储系统

集成会话管理、轮次管理、上下文管理、用户配置文件管理和语义索引管理，
提供统一的接口来管理对话数据。
"""
import os
import uuid
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

from .base_manager import BaseManager
from .config import get_surreal_config
from .models import SessionModel, TurnModel, UserProfileModel
from .session_manager import SessionManager
from .turn_manager import TurnManager
from .context_manager import ContextManager
from .user_profile_manager import UserProfileManager
from .semantic_index_manager import SemanticIndexManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DialogueStorageSystem")

class DialogueStorageSystem(BaseManager):
    """对话存储系统
    
    集成会话管理、轮次管理、上下文管理、用户配置文件管理和语义索引管理，
    提供统一的接口来管理对话数据。
    """
    
    def __init__(self, 
                 url: Optional[str] = None,
                 namespace: Optional[str] = None,
                 database: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 embedding_dimension: int = 384):
        """初始化对话存储系统
        
        Args:
            url: SurrealDB服务器URL
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
            embedding_dimension: 嵌入向量维度
        """
        # 初始化基类
        super().__init__(url, namespace, database, username, password, "DialogueStorageSystem")
        
        self.embedding_dimension = embedding_dimension
        
        # 初始化各个管理器
        self.session_manager = SessionManager(
            url=self.url,
            namespace=self.namespace,
            database=self.database,
            username=self.username,
            password=self.password
        )
        
        self.turn_manager = TurnManager(
            url=self.url,
            namespace=self.namespace,
            database=self.database,
            username=self.username,
            password=self.password
        )
        
        # 初始化上下文管理器
        # 注意：如果上下文管理器也需要重构，这里需要更新
        self.context_manager = ContextManager(
            url=self.url,
            namespace=self.namespace,
            database=self.database,
            username=self.username,
            password=self.password
        )
        
        # 初始化用户配置文件管理器
        # 注意：如果用户配置文件管理器也需要重构，这里需要更新
        self.user_profile_manager = UserProfileManager(
            url=self.url,
            namespace=self.namespace,
            database=self.database,
            username=self.username,
            password=self.password
        )
        
        # 初始化语义索引管理器
        # 注意：如果语义索引管理器也需要重构，这里需要更新
        self.semantic_index_manager = SemanticIndexManager(
            url=self.url,
            namespace=self.namespace,
            database=self.database,
            username=self.username,
            password=self.password,
            embedding_dimension=self.embedding_dimension
        )
        
        logger.info(f"对话存储系统初始化完成: {self.url}, {self.namespace}, {self.database}")
    
    async def create_session(self, 
                           user_id: str, 
                           title: Optional[str] = None,
                           dialogue_type: str = "human_to_ai_private",
                           summary: Optional[str] = None,
                           topics: Optional[List[str]] = None,
                           sentiment: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建新会话
        
        Args:
            user_id: 用户ID
            title: 会话标题
            dialogue_type: 对话类型
            summary: 会话摘要
            topics: 会话主题列表
            sentiment: 会话情感
            metadata: 元数据
            
        Returns:
            创建的会话
        """
        try:
            # 创建会话
            session = await self.session_manager.create_session(
                user_id=user_id,
                title=title,
                dialogue_type=dialogue_type,
                summary=summary,
                topics=topics,
                sentiment=sentiment,
                metadata=metadata
            )
            
            logger.info(f"创建会话成功: {session.get('id') if isinstance(session, dict) else session.id}")
            return session
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise
    
    def create_turn(self, 
                  session_id: str, 
                  role: str, 
                  content: str,
                  embedding: Optional[List[float]] = None,
                  metadata: Optional[Dict[str, Any]] = None,
                  auto_index: bool = True,
                  embedding_model: Any = None) -> Dict[str, Any]:
        """创建新轮次
        
        Args:
            session_id: 会话ID
            role: 角色 (user/assistant)
            content: 内容
            embedding: 嵌入向量
            metadata: 元数据
            auto_index: 是否自动创建语义索引
            embedding_model: 嵌入模型
            
        Returns:
            创建的轮次
        """
        try:
            # 创建轮次
            turn = self.turn_manager.create_turn(
                session_id=session_id,
                role=role,
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            
            # 如果需要自动创建语义索引
            if auto_index:
                try:
                    # 创建语义索引
                    index_id = self.semantic_index_manager.index_turn(turn, embedding_model)
                    if index_id:
                        logger.info(f"为轮次 {turn.get('id') if isinstance(turn, dict) else turn.id} 创建语义索引成功: {index_id}")
                except Exception as e:
                    logger.error(f"为轮次创建语义索引失败: {e}")
            
            logger.info(f"创建轮次成功: {turn.get('id') if isinstance(turn, dict) else turn.id}")
            return turn
        except Exception as e:
            logger.error(f"创建轮次失败: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Union[Dict[str, Any], SessionModel]]:
        """获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据
        """
        try:
            # 获取会话
            session = await self.session_manager.get_session(session_id)
            
            if session:
                logger.info(f"获取会话 {session_id} 成功")
            else:
                logger.info(f"会话 {session_id} 不存在")
            
            return session
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
    
    def get_turn(self, turn_id: str) -> Optional[Union[Dict[str, Any], TurnModel]]:
        """获取轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            轮次数据
        """
        try:
            # 获取轮次
            turn = self.turn_manager.get_turn(turn_id)
            
            if turn:
                logger.info(f"获取轮次 {turn_id} 成功")
            else:
                logger.info(f"轮次 {turn_id} 不存在")
            
            return turn
        except Exception as e:
            logger.error(f"获取轮次失败: {e}")
            return None
    
    def get_turns_by_session(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Union[Dict[str, Any], TurnModel]]:
        """获取会话的轮次列表
        
        Args:
            session_id: 会话ID
            limit: 最大返回数量
            offset: 偏移量
            
        Returns:
            轮次列表
        """
        try:
            # 获取轮次列表
            turns = self.turn_manager.get_turns_by_session(session_id, limit, offset)
            
            logger.info(f"获取会话 {session_id} 的轮次列表成功，共 {len(turns)} 条")
            return turns
        except Exception as e:
            logger.error(f"获取会话 {session_id} 的轮次列表失败: {e}")
            return []
    
    async def get_context(self, session_id: str, max_turns: int = 10) -> List[TurnModel]:
        """获取会话上下文
        
        Args:
            session_id: 会话ID
            max_turns: 最大轮次数
            
        Returns:
            上下文轮次列表
        """
        try:
            # 获取上下文
            context = await self.context_manager.get_context(session_id, max_turns)
            
            logger.info(f"获取会话 {session_id} 的上下文成功，共 {len(context)} 条")
            return context
        except Exception as e:
            logger.error(f"获取会话 {session_id} 的上下文失败: {e}")
            return []
    
    async def get_relevant_context(self, session_id: str, query: str, max_results: int = 5) -> List[TurnModel]:
        """获取与查询相关的上下文
        
        Args:
            session_id: 会话ID
            query: 查询文本
            max_results: 最大结果数
            
        Returns:
            相关上下文列表
        """
        try:
            # 获取相关上下文
            context = await self.context_manager.get_relevant_context(session_id, query, max_results)
            
            logger.info(f"获取会话 {session_id} 的相关上下文成功，共 {len(context)} 条")
            return context
        except Exception as e:
            logger.error(f"获取会话 {session_id} 的相关上下文失败: {e}")
            return []
    
    def create_user_profile(self, 
                          username: str, 
                          email: Optional[str] = None,
                          preferences: Optional[Dict[str, Any]] = None,
                          topics_of_interest: Optional[List[str]] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建用户配置文件
        
        Args:
            username: 用户名
            email: 电子邮件
            preferences: 用户偏好
            topics_of_interest: 兴趣主题
            metadata: 元数据
            
        Returns:
            创建的用户配置文件
        """
        try:
            # 创建用户配置文件
            profile = self.user_profile_manager.create_profile(
                username=username,
                email=email,
                preferences=preferences,
                topics_of_interest=topics_of_interest,
                metadata=metadata
            )
            
            logger.info(f"创建用户配置文件成功: {profile.get('id') if isinstance(profile, dict) else profile.id}")
            return profile
        except Exception as e:
            logger.error(f"创建用户配置文件失败: {e}")
            raise
    
    def get_user_profile(self, user_id: str) -> Optional[Union[Dict[str, Any], UserProfileModel]]:
        """获取用户配置文件
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户配置文件
        """
        try:
            # 获取用户配置文件
            profile = self.user_profile_manager.get_profile(user_id)
            
            if profile:
                logger.info(f"获取用户配置文件 {user_id} 成功")
            else:
                logger.info(f"用户配置文件 {user_id} 不存在")
            
            return profile
        except Exception as e:
            logger.error(f"获取用户配置文件失败: {e}")
            return None
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """更新用户偏好
        
        Args:
            user_id: 用户ID
            preferences: 用户偏好
            
        Returns:
            更新是否成功
        """
        try:
            # 更新用户偏好
            success = self.user_profile_manager.update_preferences(user_id, preferences)
            
            if success:
                logger.info(f"更新用户 {user_id} 的偏好成功")
            else:
                logger.info(f"更新用户 {user_id} 的偏好失败")
            
            return success
        except Exception as e:
            logger.error(f"更新用户偏好失败: {e}")
            return False
    
    def search_semantic_index(self, query: str, embedding_model: Any, limit: int = 5, user_id: Optional[str] = None, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """语义搜索
        
        Args:
            query: 查询文本
            embedding_model: 嵌入模型
            limit: 最大结果数
            user_id: 用户ID（可选，用于限制搜索范围）
            session_id: 会话ID（可选，用于限制搜索范围）
            
        Returns:
            搜索结果列表
        """
        try:
            # 语义搜索
            results = self.semantic_index_manager.search(
                query=query,
                embedding_model=embedding_model,
                limit=limit,
                user_id=user_id,
                session_id=session_id
            )
            
            logger.info(f"语义搜索成功，共找到 {len(results)} 条结果")
            return results
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []
    
    async def update_session_summary(self, session_id: str, summary: str) -> bool:
        """更新会话摘要
        
        Args:
            session_id: 会话ID
            summary: 会话摘要
            
        Returns:
            更新是否成功
        """
        try:
            # 更新会话摘要
            success = await self.context_manager.update_session_summary(session_id, summary)
            
            if success:
                logger.info(f"更新会话 {session_id} 的摘要成功")
            else:
                logger.info(f"更新会话 {session_id} 的摘要失败")
            
            return success
        except Exception as e:
            logger.error(f"更新会话摘要失败: {e}")
            return False
    
    async def update_session_topics(self, session_id: str, topics: List[str]) -> bool:
        """更新会话主题
        
        Args:
            session_id: 会话ID
            topics: 会话主题列表
            
        Returns:
            更新是否成功
        """
        try:
            # 更新会话主题
            success = await self.context_manager.update_session_topics(session_id, topics)
            
            if success:
                logger.info(f"更新会话 {session_id} 的主题成功")
            else:
                logger.info(f"更新会话 {session_id} 的主题失败")
            
            return success
        except Exception as e:
            logger.error(f"更新会话主题失败: {e}")
            return False
    
    def record_user_interaction(self, user_id: str, interaction_type: str, details: Dict[str, Any]) -> bool:
        """记录用户交互
        
        Args:
            user_id: 用户ID
            interaction_type: 交互类型
            details: 交互详情
            
        Returns:
            记录是否成功
        """
        try:
            # 记录用户交互
            success = self.user_profile_manager.record_interaction(user_id, interaction_type, details)
            
            if success:
                logger.info(f"为用户 {user_id} 记录 {interaction_type} 交互成功")
            else:
                logger.info(f"为用户 {user_id} 记录 {interaction_type} 交互失败")
            
            return success
        except Exception as e:
            logger.error(f"记录用户交互失败: {e}")
            return False
    
    async def search_across_sessions(self, user_id: str, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """跨会话搜索
        
        Args:
            user_id: 用户ID
            query: 查询文本
            max_results: 最大结果数
            
        Returns:
            搜索结果列表
        """
        try:
            # 跨会话搜索
            results = await self.context_manager.search_across_sessions(user_id, query, max_results)
            
            logger.info(f"用户 {user_id} 的跨会话搜索成功，共找到 {len(results)} 条结果")
            return results
        except Exception as e:
            logger.error(f"用户 {user_id} 的跨会话搜索失败: {e}")
            return []
    
    def bulk_index_turns(self, turns: List[Union[Dict[str, Any], TurnModel]], embedding_model: Any = None) -> List[str]:
        """批量为轮次创建语义索引
        
        Args:
            turns: 轮次列表
            embedding_model: 嵌入模型（可选）
            
        Returns:
            成功创建的索引条目ID列表
        """
        try:
            # 批量创建语义索引
            index_ids = self.semantic_index_manager.bulk_index_turns(turns, embedding_model)
            
            logger.info(f"批量创建语义索引成功，共 {len(index_ids)} 条")
            return index_ids
        except Exception as e:
            logger.error(f"批量创建语义索引失败: {e}")
            return []
