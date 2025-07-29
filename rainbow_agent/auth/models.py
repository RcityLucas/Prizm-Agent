"""
用户认证模型

定义用户模型和相关数据结构，用于OAuth认证和用户管理。
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from flask_login import UserMixin

class User(UserMixin):
    """用户模型，用于Flask-Login认证和AI个性化"""
    
    def __init__(self, 
                 id: str = None, 
                 email: str = None, 
                 name: str = None,
                 avatar_url: str = None,
                 provider: str = None,
                 provider_id: str = None,
                 access_token: str = None,
                 refresh_token: str = None,
                 token_expiry: datetime = None,
                 created_at: datetime = None,
                 last_login: datetime = None,
                 roles: List[str] = None,
                 is_active: bool = True,
                 metadata: Dict[str, Any] = None,
                 # AI相关字段
                 preferences: Dict[str, Any] = None,
                 ai_settings: Dict[str, Any] = None,
                 interaction_history: List[Dict[str, Any]] = None,
                 embeddings: Dict[str, List[float]] = None,
                 usage_stats: Dict[str, Any] = None,
                 tags: List[str] = None,
                 timezone: str = None,
                 language: str = None):
        """
        初始化用户
        
        Args:
            id: 用户ID
            email: 用户邮箱
            name: 用户名
            avatar_url: 头像URL
            provider: 认证提供商（google, github）
            provider_id: 提供商用户ID
            access_token: OAuth访问令牌
            refresh_token: OAuth刷新令牌
            token_expiry: 令牌过期时间
            created_at: 创建时间
            last_login: 最后登录时间
            roles: 用户角色列表
            is_active: 用户是否激活
            metadata: 其他元数据
            preferences: 用户偏好设置，如主题、界面布局等
            ai_settings: AI相关设置，如模型选择、参数配置等
            interaction_history: 用户交互历史摘要
            embeddings: 用户特征向量，用于个性化推荐
            usage_stats: 使用统计信息
            tags: 用户标签
            timezone: 用户时区
            language: 用户语言偏好
        """
        self.id = id or str(uuid.uuid4())
        self.email = email
        self.name = name
        self.avatar_url = avatar_url
        self.provider = provider
        self.provider_id = provider_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = token_expiry
        self.created_at = created_at or datetime.now()
        self.last_login = last_login or datetime.now()
        self.roles = roles or ["user"]
        self._is_active = is_active
        self.metadata = metadata or {}
        
        # AI相关字段初始化
        self.preferences = preferences or {}
        self.ai_settings = ai_settings or {
            "model": "default",
            "temperature": 0.7,
            "max_tokens": 2000,
            "use_vector_search": True,
            "personalization_level": "medium"
        }
        self.interaction_history = interaction_history or []
        self.embeddings = embeddings or {}
        self.usage_stats = usage_stats or {
            "total_conversations": 0,
            "total_messages": 0,
            "last_active_date": datetime.now().isoformat(),
            "feature_usage": {}
        }
        self.tags = tags or []
        self.timezone = timezone
        self.language = language or "zh-CN"
        
        # Additional attributes that might be set externally
        self.username = None
        self.password_hash = None
    
    def get_id(self) -> str:
        """获取用户ID，用于Flask-Login"""
        # 确保返回字符串格式的ID
        if isinstance(self.id, dict):
            return str(self.id.get('id', self.id))
        return str(self.id)
    
    @property
    def is_active(self) -> bool:
        """用户是否激活，用于Flask-Login"""
        return self._is_active
    
    @property
    def is_authenticated(self) -> bool:
        """用户是否已认证，用于Flask-Login"""
        return True
    
    @property
    def is_anonymous(self) -> bool:
        """用户是否匿名，用于Flask-Login"""
        return False
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        if hasattr(self, 'username') and self.username:
            return self.username
        elif self.name:
            return self.name
        elif self.email:
            return self.email.split('@')[0]
        else:
            return f"User {self.id[:8] if self.id else 'Unknown'}"
    
    def has_role(self, role: str) -> bool:
        """
        检查用户是否有指定角色
        
        Args:
            role: 角色名称
            
        Returns:
            是否有该角色
        """
        return role in self.roles
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将用户对象转换为字典
        
        Returns:
            用户字典
        """
        # 确保ID是字符串格式
        user_id = self.id
        if isinstance(user_id, dict):
            user_id = str(user_id.get('id', user_id))
        
        result = {
            "id": str(user_id),  # 确保ID是字符串
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "provider": self.provider,
            "provider_id": self.provider_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "roles": self.roles,
            "is_active": self._is_active,
            "metadata": self.metadata,
            # AI相关字段
            "preferences": self.preferences,
            "ai_settings": self.ai_settings,
            "interaction_history": self.interaction_history,
            "embeddings": self.embeddings,
            "usage_stats": self.usage_stats,
            "tags": self.tags,
            "timezone": self.timezone,
            "language": self.language
        }
        
        # Include additional attributes if they exist
        if hasattr(self, 'username') and self.username is not None:
            result["username"] = self.username
        if hasattr(self, 'password_hash') and self.password_hash is not None:
            result["password_hash"] = self.password_hash
            
        return result
    
    def to_json(self) -> str:
        """
        将用户对象转换为JSON字符串
        
        Returns:
            用户JSON字符串
        """
        user_dict = self.to_dict()
        return json.dumps(user_dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        从字典创建用户对象
        
        Args:
            data: 用户字典
            
        Returns:
            用户对象
        """
        # 处理SurrealDB RecordID格式
        if isinstance(data.get('id'), dict):
            id_obj = data['id']
            # 处理各种可能的ID格式
            if 'id' in id_obj:
                data['id'] = str(id_obj['id'])
            elif 'record_id' in id_obj:
                data['id'] = str(id_obj['record_id'])
            else:
                # 如果没有明确的ID字段，转换整个对象为字符串
                data['id'] = str(id_obj)
        elif data.get('id') is not None:
            # 确保ID是字符串格式
            data['id'] = str(data['id'])
        
        # 处理日期时间字段
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if isinstance(data.get('last_login'), str):
            data['last_login'] = datetime.fromisoformat(data['last_login'])
            
        if isinstance(data.get('token_expiry'), str):
            data['token_expiry'] = datetime.fromisoformat(data['token_expiry'])
        
        # Handle additional attributes not in constructor
        username = data.pop('username', None)
        password_hash = data.pop('password_hash', None)
        
        user = cls(**data)
        
        # Set additional attributes after construction
        if username is not None:
            user.username = username
        if password_hash is not None:
            user.password_hash = password_hash
            
        return user
    
    @classmethod
    def from_json(cls, json_str: str) -> 'User':
        """
        从JSON字符串创建用户对象
        
        Args:
            json_str: 用户JSON字符串
            
        Returns:
            用户对象
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
