"""
上下文管理器

管理对话上下文，提供智能检索和上下文维护功能
"""
import os
import uuid
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta

from .surreal_http_client import SurrealDBHttpClient
from .config import get_surreal_config
from .models import SessionModel, TurnModel
from .session_manager import SessionManager
from .turn_manager import TurnManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ContextManager")

class ContextManager:
    """上下文管理器
    
    管理对话上下文，提供智能检索和上下文维护功能
    """
    
    # 内存缓存
    _context_cache = {}
    
    def __init__(self, 
                 url: Optional[str] = None,
                 namespace: Optional[str] = None,
                 database: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """初始化上下文管理器
        
        Args:
            url: SurrealDB服务器URL
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
        """
        # 获取配置
        config = get_surreal_config()
        
        # 使用传入的参数或配置值
        self.url = url or config["url"]
        self.namespace = namespace or config["namespace"]
        self.database = database or config["database"]
        self.username = username or config["username"]
        self.password = password or config["password"]
        
        # 将WebSocket URL转换为HTTP URL
        if self.url.startswith("ws://"):
            self.http_url = "http://" + self.url[5:].replace("/rpc", "")
        elif self.url.startswith("wss://"):
            self.http_url = "https://" + self.url[6:].replace("/rpc", "")
        else:
            self.http_url = self.url
        
        # 创建HTTP客户端
        self.client = SurrealDBHttpClient(
            url=self.http_url,
            namespace=self.namespace,
            database=self.database,
            username=self.username,
            password=self.password
        )
        
        # 创建会话管理器和轮次管理器
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
        
        logger.info(f"上下文管理器初始化完成: {self.http_url}, {self.namespace}, {self.database}")
    
    async def get_context(self, session_id: str, max_turns: int = 10) -> List[TurnModel]:
        """获取会话上下文
        
        Args:
            session_id: 会话ID
            max_turns: 最大轮次数
            
        Returns:
            上下文轮次列表
        """
        try:
            # 获取会话的所有轮次
            turns = self.turn_manager.get_turns_by_session(session_id)
            
            # 按创建时间排序
            turns.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else x.get('created_at', ''))
            
            # 如果轮次数量超过最大值，只返回最近的max_turns个轮次
            if len(turns) > max_turns:
                turns = turns[-max_turns:]
            
            logger.info(f"获取会话 {session_id} 的上下文成功，共 {len(turns)} 条")
            return turns
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
            # 获取会话的所有轮次
            turns = self.turn_manager.get_turns_by_session(session_id)
            
            # 如果没有嵌入向量，则返回最近的轮次
            has_embeddings = any(hasattr(turn, 'embedding') and turn.embedding for turn in turns)
            
            if not has_embeddings:
                logger.info(f"会话 {session_id} 的轮次没有嵌入向量，返回最近的 {max_results} 条")
                # 按创建时间排序
                turns.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else x.get('created_at', ''))
                return turns[-max_results:] if len(turns) > max_results else turns
            
            # TODO: 实现向量相似度搜索
            # 这里需要先获取查询的嵌入向量，然后计算与各轮次的相似度
            # 由于目前没有嵌入模型，先返回最近的轮次
            
            logger.info(f"会话 {session_id} 的相关上下文搜索功能尚未实现，返回最近的 {max_results} 条")
            # 按创建时间排序
            turns.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else x.get('created_at', ''))
            return turns[-max_results:] if len(turns) > max_results else turns
        except Exception as e:
            logger.error(f"获取会话 {session_id} 的相关上下文失败: {e}")
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
            updates = {"summary": summary}
            updated_session = await self.session_manager.update_session(session_id, updates)
            
            if updated_session:
                logger.info(f"更新会话 {session_id} 的摘要成功")
                return True
            else:
                logger.info(f"更新会话 {session_id} 的摘要失败")
                return False
        except Exception as e:
            logger.error(f"更新会话 {session_id} 的摘要失败: {e}")
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
            updates = {"topics": topics}
            updated_session = await self.session_manager.update_session(session_id, updates)
            
            if updated_session:
                logger.info(f"更新会话 {session_id} 的主题成功")
                return True
            else:
                logger.info(f"更新会话 {session_id} 的主题失败")
                return False
        except Exception as e:
            logger.error(f"更新会话 {session_id} 的主题失败: {e}")
            return False
    
    async def update_session_sentiment(self, session_id: str, sentiment: str) -> bool:
        """更新会话情感
        
        Args:
            session_id: 会话ID
            sentiment: 会话情感
            
        Returns:
            更新是否成功
        """
        try:
            # 更新会话情感
            updates = {"sentiment": sentiment}
            updated_session = await self.session_manager.update_session(session_id, updates)
            
            if updated_session:
                logger.info(f"更新会话 {session_id} 的情感成功")
                return True
            else:
                logger.info(f"更新会话 {session_id} 的情感失败")
                return False
        except Exception as e:
            logger.error(f"更新会话 {session_id} 的情感失败: {e}")
            return False
    
    async def generate_turn_embedding(self, turn_id: str, embedding_model: Any) -> bool:
        """为轮次生成嵌入向量
        
        Args:
            turn_id: 轮次ID
            embedding_model: 嵌入模型
            
        Returns:
            生成是否成功
        """
        try:
            # 获取轮次
            turn = self.turn_manager.get_turn(turn_id)
            
            if not turn:
                logger.info(f"轮次 {turn_id} 不存在，无法生成嵌入向量")
                return False
            
            # 获取轮次内容
            content = turn.content if hasattr(turn, 'content') else turn.get('content', '')
            
            if not content:
                logger.info(f"轮次 {turn_id} 没有内容，无法生成嵌入向量")
                return False
            
            # TODO: 使用嵌入模型生成嵌入向量
            # 由于目前没有嵌入模型，先生成一个随机向量作为示例
            embedding = list(np.random.rand(384).astype(float))
            
            # 更新轮次的嵌入向量
            updates = {"embedding": embedding}
            self.client.update_record("turns", turn_id, updates)
            
            logger.info(f"为轮次 {turn_id} 生成嵌入向量成功")
            return True
        except Exception as e:
            logger.error(f"为轮次 {turn_id} 生成嵌入向量失败: {e}")
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
            # 获取用户的所有会话
            condition = f"user_id = '{user_id}'"
            sessions = self.client.get_records("sessions", condition, 100, 0)
            
            if not sessions:
                logger.info(f"用户 {user_id} 没有会话，无法搜索")
                return []
            
            # 收集所有会话的轮次
            all_turns = []
            for session in sessions:
                session_id = session.get("id")
                if session_id:
                    turns = self.turn_manager.get_turns_by_session(session_id)
                    for turn in turns:
                        # 添加会话信息
                        turn_dict = turn.to_dict() if hasattr(turn, 'to_dict') else turn
                        turn_dict["session_title"] = session.get("title", "")
                        turn_dict["session_id"] = session_id
                        all_turns.append(turn_dict)
            
            # TODO: 实现向量相似度搜索
            # 这里需要先获取查询的嵌入向量，然后计算与各轮次的相似度
            # 由于目前没有嵌入模型，先使用简单的文本匹配
            
            # 简单的文本匹配
            matched_turns = []
            for turn in all_turns:
                content = turn.get("content", "")
                if query.lower() in content.lower():
                    matched_turns.append(turn)
            
            # 限制结果数量
            results = matched_turns[:max_results] if len(matched_turns) > max_results else matched_turns
            
            logger.info(f"用户 {user_id} 的跨会话搜索成功，共找到 {len(results)} 条结果")
            return results
        except Exception as e:
            logger.error(f"用户 {user_id} 的跨会话搜索失败: {e}")
            return []
