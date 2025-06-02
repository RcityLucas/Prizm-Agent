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
    
    def create_session(self, 
                   user_id: str, 
                   title: Optional[str] = None,
                   dialogue_type: str = "human_to_ai_private",
                   summary: Optional[str] = None,
                   topics: Optional[List[str]] = None,
                   sentiment: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """同步创建新会话
        
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
            # 同步创建会话
            session = self.session_manager.create_session(
                user_id=user_id,
                title=title,
                dialogue_type=dialogue_type,
                summary=summary,
                topics=topics,
                sentiment=sentiment,
                metadata=metadata
            )
            
            # 获取会话ID（可能是字典、对象或字符串）
            session_id = None
            if isinstance(session, dict) and 'id' in session:
                session_id = session['id']
            elif hasattr(session, 'id'):
                session_id = session.id
            elif isinstance(session, str):
                session_id = session
                
            logger.info(f"同步创建会话成功: {session_id}")
            return session
        except Exception as e:
            logger.error(f"同步创建会话失败: {e}")
            raise
            
    async def create_session_async(self, 
                       user_id: str, 
                       title: Optional[str] = None,
                       dialogue_type: str = "human_to_ai_private",
                       summary: Optional[str] = None,
                       topics: Optional[List[str]] = None,
                       sentiment: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """异步创建新会话
        
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
            # 异步创建会话 - 确保使用异步方法
            session = await self.session_manager.create_session_async(
                user_id=user_id,
                title=title,
                dialogue_type=dialogue_type,
                summary=summary,
                topics=topics,
                sentiment=sentiment,
                metadata=metadata
            )
            
            # 获取会话ID（可能是字典、对象或字符串）
            session_id = None
            if isinstance(session, dict) and 'id' in session:
                session_id = session['id']
            elif hasattr(session, 'id'):
                session_id = session.id
            elif isinstance(session, str):
                session_id = session
                
            logger.info(f"异步创建会话成功: {session_id}")
            return session
        except Exception as e:
            logger.error(f"异步创建会话失败: {e}")
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
            
            # 获取轮次ID，处理不同的返回类型
            turn_id = None
            if isinstance(turn, dict) and 'id' in turn:
                turn_id = turn['id']
            elif hasattr(turn, 'id'):
                turn_id = turn.id
            elif isinstance(turn, str):
                turn_id = turn
            
            # 如果需要自动创建语义索引
            if auto_index and turn_id:
                try:
                    # 创建语义索引
                    index_id = self.semantic_index_manager.index_turn(turn, embedding_model)
                    if index_id:
                        logger.info(f"为轮次 {turn_id} 创建语义索引成功: {index_id}")
                except Exception as e:
                    logger.error(f"为轮次 {turn_id} 创建语义索引失败: {e}")
            
            logger.info(f"创建轮次成功: {turn_id}")
            return turn
        except Exception as e:
            logger.error(f"创建轮次失败: {e}")
            raise
            
    async def create_turn_async(self, 
                          session_id: str, 
                          role: str, 
                          content: str,
                          embedding: Optional[List[float]] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          auto_index: bool = True,
                          embedding_model: Any = None) -> Dict[str, Any]:
        """异步创建新轮次
        
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
            # 异步创建轮次
            turn = await self.turn_manager.create_turn_async(
                session_id=session_id,
                role=role,
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            
            # 获取轮次ID，处理不同的返回类型
            turn_id = None
            if isinstance(turn, dict) and 'id' in turn:
                turn_id = turn['id']
            elif hasattr(turn, 'id'):
                turn_id = turn.id
            elif isinstance(turn, str):
                turn_id = turn
            
            # 如果需要自动创建语义索引
            if auto_index and turn_id:
                try:
                    # 在异步方法中使用同步操作需要使用以下方式避免阻塞
                    # 选项一：使用run_in_executor将同步操作转换为异步
                    # 由于这只是一个辅助操作，如果失败不应影响主操作，
                    # 我们使用一个更简单的方法 - 暂时禁用语义索引这一步
                    # 在后续可以实现index_turn_async异步方法
                    logger.warning(f"异步模式下暂不支持自动创建语义索引，轮次: {turn_id}")
                    # 如果需要立即加入异步索引支持，可以使用以下代码：
                    # import asyncio
                    # loop = asyncio.get_event_loop()
                    # index_id = await loop.run_in_executor(
                    #     None, 
                    #     lambda: self.semantic_index_manager.index_turn(turn, embedding_model)
                    # )
                    # if index_id:
                    #     logger.info(f"为轮次 {turn_id} 创建语义索引成功: {index_id}")
                except Exception as e:
                    logger.error(f"为轮次 {turn_id} 创建语义索引失败: {e}")
            
            logger.info(f"异步创建轮次成功: {turn_id}")
            return turn
        except Exception as e:
            logger.error(f"异步创建轮次失败: {e}")
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
    
    async def get_turn_async(self, turn_id: str) -> Optional[Union[Dict[str, Any], TurnModel]]:
        """异步获取轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            轮次数据
        """
        try:
            # 异步获取轮次
            turn = await self.turn_manager.get_turn_async(turn_id)
            
            if turn:
                logger.info(f"异步获取轮次 {turn_id} 成功")
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
    
    async def get_turns_by_session_async(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Union[Dict[str, Any], TurnModel]]:
        """异步获取会话的轮次列表
        
        Args:
            session_id: 会话ID
            limit: 最大返回数量
            offset: 偏移量
            
        Returns:
            轮次列表
        """
        try:
            # 异步获取轮次列表
            turns = await self.turn_manager.get_turns_by_session_async(session_id, limit, offset)
            
            logger.info(f"异步获取会话 {session_id} 的轮次列表成功，共 {len(turns)} 条")
            return turns
        except Exception as e:
            logger.error(f"异步获取会话 {session_id} 的轮次列表失败: {e}")
            return []
    
    def update_turn(self, turn_id: str, updates: Dict[str, Any]) -> Optional[Union[Dict[str, Any], TurnModel]]:
        """更新轮次
        
        Args:
            turn_id: 轮次ID
            updates: 要更新的字段
            
        Returns:
            更新后的轮次，如果轮次不存在则返回None
        """
        try:
            # 更新轮次
            updated_turn = self.turn_manager.update_turn(turn_id, updates)
            
            if updated_turn:
                logger.info(f"更新轮次 {turn_id} 成功")
                # 如果更新包含内容变化且已存在语义索引，可能需要更新索引
                # 这里可以添加附加逻辑判断是否需要更新语义索引
            else:
                logger.info(f"轮次 {turn_id} 不存在，无法更新")
            
            return updated_turn
        except Exception as e:
            logger.error(f"更新轮次失败: {e}")
            return None
            
    async def update_turn_async(self, turn_id: str, updates: Dict[str, Any]) -> Optional[Union[Dict[str, Any], TurnModel]]:
        """异步更新轮次
        
        Args:
            turn_id: 轮次ID
            updates: 要更新的字段
            
        Returns:
            更新后的轮次，如果轮次不存在则返回None
        """
        try:
            # 异步更新轮次
            updated_turn = await self.turn_manager.update_turn_async(turn_id, updates)
            
            if updated_turn:
                logger.info(f"异步更新轮次 {turn_id} 成功")
                # 如果更新包含内容变化且已存在语义索引，可能需要更新索引
                # 这里可以添加附加逻辑判断是否需要更新语义索引
            else:
                logger.info(f"轮次 {turn_id} 不存在，无法异步更新")
            
            return updated_turn
        except Exception as e:
            logger.error(f"异步更新轮次失败: {e}")
            return None
    
    def delete_turn(self, turn_id: str) -> bool:
        """删除轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            是否删除成功
        """
        try:
            # 删除轮次
            result = self.turn_manager.delete_turn(turn_id)
            
            if result:
                logger.info(f"删除轮次 {turn_id} 成功")
                # 如果该轮次有语义索引，也应删除相应的索引
                try:
                    self.semantic_index_manager.delete_turn_index(turn_id)
                except Exception as index_error:
                    logger.warning(f"删除轮次的语义索引失败：{index_error}")
            else:
                logger.info(f"轮次 {turn_id} 不存在，无法删除")
            
            return result
        except Exception as e:
            logger.error(f"删除轮次失败: {e}")
            return False
    
    async def delete_turn_async(self, turn_id: str) -> bool:
        """异步删除轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            是否删除成功
        """
        try:
            # 异步删除轮次
            result = await self.turn_manager.delete_turn_async(turn_id)
            
            if result:
                logger.info(f"异步删除轮次 {turn_id} 成功")
                # 如果该轮次有语义索引，也应删除相应的索引
                try:
                    # 假设语义索引管理器有异步方法
                    if hasattr(self.semantic_index_manager, 'delete_turn_index_async'):
                        await self.semantic_index_manager.delete_turn_index_async(turn_id)
                    else:
                        # 如果没有异步方法，则使用同步方法
                        self.semantic_index_manager.delete_turn_index(turn_id)
                except Exception as index_error:
                    logger.warning(f"异步删除轮次的语义索引失败：{index_error}")
            else:
                logger.info(f"轮次 {turn_id} 不存在，无法异步删除")
            
            return result
        except Exception as e:
            logger.error(f"异步删除轮次失败: {e}")
            return False
    
    def delete_session_turns(self, session_id: str) -> int:
        """删除会话的所有轮次
        
        Args:
            session_id: 会话ID
            
        Returns:
            删除的轮次数量
        """
        try:
            # 删除会话的所有轮次
            deleted_count = self.turn_manager.delete_session_turns(session_id)
            
            if deleted_count > 0:
                logger.info(f"删除会话 {session_id} 的所有轮次成功，共 {deleted_count} 条")
                # 这里可以添加删除相关语义索引的逻辑
            else:
                logger.info(f"会话 {session_id} 没有轮次或删除失败")
            
            return deleted_count
        except Exception as e:
            logger.error(f"删除会话轮次失败: {e}")
            return 0
    
    async def delete_session_turns_async(self, session_id: str) -> int:
        """异步删除会话的所有轮次
        
        Args:
            session_id: 会话ID
            
        Returns:
            删除的轮次数量
        """
        try:
            # 异步删除会话的所有轮次
            deleted_count = await self.turn_manager.delete_session_turns_async(session_id)
            
            if deleted_count > 0:
                logger.info(f"异步删除会话 {session_id} 的所有轮次成功，共 {deleted_count} 条")
                # 这里可以添加删除相关语义索引的逻辑
            else:
                logger.info(f"会话 {session_id} 没有轮次或异步删除失败")
            
            return deleted_count
        except Exception as e:
            logger.error(f"异步删除会话轮次失败: {e}")
            return 0
    
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
