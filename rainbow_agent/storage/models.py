"""
存储模型定义

此模块定义了用于对话存储系统的数据模型，包括会话、轮次和用户画像等。
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


class SessionModel:
    """会话模型"""
    
    def __init__(
        self,
        user_id: str,
        title: Optional[str] = None,
        dialogue_type: str = "human_to_ai_private",
        summary: Optional[str] = None,
        topics: Optional[List[str]] = None,
        sentiment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化会话模型
        
        Args:
            user_id: 用户ID
            title: 会话标题，如果不提供则自动生成
            dialogue_type: 对话类型
            summary: 对话摘要
            topics: 对话主题标签列表
            sentiment: 整体情感基调
            metadata: 其他元数据
        """
        self.id = str(uuid.uuid4()).replace('-', '')
        self.user_id = user_id
        self.title = title if title else f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.dialogue_type = dialogue_type
        self.created_at = "time::now()"
        self.updated_at = "time::now()"
        self.last_activity_at = "time::now()"
        self.summary = summary
        self.topics = topics or []
        self.sentiment = sentiment
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            会话数据字典
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "dialogue_type": self.dialogue_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_activity_at": self.last_activity_at,
            "summary": self.summary,
            "topics": self.topics,
            "sentiment": self.sentiment,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionModel':
        """从字典创建会话模型
        
        Args:
            data: 会话数据字典
            
        Returns:
            会话模型实例
        """
        session = cls(
            user_id=data.get("user_id", ""),
            title=data.get("title"),
            dialogue_type=data.get("dialogue_type", "human_to_ai_private"),
            summary=data.get("summary"),
            topics=data.get("topics", []),
            sentiment=data.get("sentiment"),
            metadata=data.get("metadata", {})
        )
        session.id = data.get("id", session.id)
        
        # 处理时间字段
        if "created_at" in data and not isinstance(data["created_at"], str):
            session.created_at = data["created_at"]
        if "updated_at" in data and not isinstance(data["updated_at"], str):
            session.updated_at = data["updated_at"]
        if "last_activity_at" in data and not isinstance(data["last_activity_at"], str):
            session.last_activity_at = data["last_activity_at"]
            
        return session


class TurnModel:
    """对话轮次模型
    
    用于存储单次对话轮次的内容和元数据
    """
    
    def __init__(
        self,
        session_id: str,
        role: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化轮次模型
        
        Args:
            session_id: 所属会话ID
            role: 发言者角色 (human/ai)
            content: 对话内容
            embedding: 内容向量
            metadata: 其他元数据
        """
        self.id = str(uuid.uuid4()).replace('-', '')
        self.session_id = session_id
        self.role = role
        self.content = content
        self.created_at = "time::now()"
        self.updated_at = "time::now()"
        self.embedding = embedding or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            轮次数据字典
        """
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'embedding': self.embedding,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TurnModel':
        """从字典创建实例
        
        Args:
            data: 轮次数据字典
            
        Returns:
            TurnModel实例
        """
        return cls(
            session_id=data['session_id'],
            role=data['role'],
            content=data['content'],
            embedding=data.get('embedding'),
            metadata=data.get('metadata')
        )


class UserProfileModel:
    """用户画像模型"""
    
    def __init__(
        self,
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None,
        facts: Optional[List[Dict[str, Any]]] = None,
        frequently_asked_topics: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化用户画像模型
        
        Args:
            user_id: 用户ID
            preferences: 用户偏好
            facts: 用户提到的事实
            frequently_asked_topics: 用户常问的主题
            metadata: 其他元数据
        """
        self.id = user_id
        self.created_at = "time::now()"
        self.updated_at = "time::now()"
        self.preferences = preferences or {
            "topics_of_interest": [],
            "communication_style": "neutral",
            "response_length": "medium"
        }
        self.facts = facts or []
        self.frequently_asked_topics = frequently_asked_topics or []
        self.metadata = metadata or {
            "total_sessions": 0,
            "total_messages": 0,
            "average_session_length": 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            用户画像数据字典
        """
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "preferences": self.preferences,
            "facts": self.facts,
            "frequently_asked_topics": self.frequently_asked_topics,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfileModel':
        """从字典创建用户画像模型
        
        Args:
            data: 用户画像数据字典
            
        Returns:
            用户画像模型实例
        """
        profile = cls(
            user_id=data.get("id", ""),
            preferences=data.get("preferences", {}),
            facts=data.get("facts", []),
            frequently_asked_topics=data.get("frequently_asked_topics", []),
            metadata=data.get("metadata", {})
        )
        
        # 处理时间字段
        if "created_at" in data and not isinstance(data["created_at"], str):
            profile.created_at = data["created_at"]
        if "updated_at" in data and not isinstance(data["updated_at"], str):
            profile.updated_at = data["updated_at"]
            
        return profile
