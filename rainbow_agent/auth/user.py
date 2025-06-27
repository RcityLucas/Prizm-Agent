"""
用户模型模块

定义用户模型和用户存储接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
import json
import os


class User:
    """用户模型类"""
    
    def __init__(self, 
                 id: str = None,
                 name: str = None,
                 email: str = None,
                 provider: str = None,
                 provider_id: str = None,
                 avatar_url: str = None,
                 access_token: str = None,
                 refresh_token: str = None,
                 token_expiry: datetime = None,
                 roles: List[str] = None,
                 created_at: datetime = None,
                 last_login: datetime = None,
                 metadata: Dict[str, Any] = None):
        """
        初始化用户对象
        
        Args:
            id: 用户ID
            name: 用户名称
            email: 用户邮箱
            provider: 认证提供商（google, github等）
            provider_id: 提供商用户ID
            avatar_url: 头像URL
            access_token: 访问令牌
            refresh_token: 刷新令牌
            token_expiry: 令牌过期时间
            roles: 用户角色列表
            created_at: 创建时间
            last_login: 最后登录时间
            metadata: 其他元数据
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.email = email
        self.provider = provider
        self.provider_id = provider_id
        self.avatar_url = avatar_url
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = token_expiry
        self.roles = roles or ["user"]
        self.created_at = created_at or datetime.now()
        self.last_login = last_login or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将用户对象转换为字典
        
        Returns:
            用户字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "provider": self.provider,
            "provider_id": self.provider_id,
            "avatar_url": self.avatar_url,
            "roles": self.roles,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        从字典创建用户对象
        
        Args:
            data: 用户数据字典
            
        Returns:
            用户对象
        """
        # 处理日期时间字段
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
            
        last_login = data.get('last_login')
        if last_login and isinstance(last_login, str):
            last_login = datetime.fromisoformat(last_login)
            
        token_expiry = data.get('token_expiry')
        if token_expiry and isinstance(token_expiry, str):
            token_expiry = datetime.fromisoformat(token_expiry)
        
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            email=data.get('email'),
            provider=data.get('provider'),
            provider_id=data.get('provider_id'),
            avatar_url=data.get('avatar_url'),
            access_token=data.get('access_token'),
            refresh_token=data.get('refresh_token'),
            token_expiry=token_expiry,
            roles=data.get('roles'),
            created_at=created_at,
            last_login=last_login,
            metadata=data.get('metadata')
        )
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        更新用户信息
        
        Args:
            data: 要更新的用户数据
        """
        for key, value in data.items():
            if hasattr(self, key) and key != 'id':  # 不允许更新ID
                setattr(self, key, value)
        
        # 更新最后登录时间
        if 'last_login' not in data:
            self.last_login = datetime.now()


class UserStorage(ABC):
    """用户存储接口"""
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def get_user_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        """
        通过提供商ID获取用户
        
        Args:
            provider: 认证提供商
            provider_id: 提供商用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        
        Args:
            email: 用户邮箱
            
        Returns:
            用户对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """
        创建用户
        
        Args:
            user: 用户对象
            
        Returns:
            创建的用户对象
        """
        pass
    
    @abstractmethod
    async def update_user(self, user: User) -> User:
        """
        更新用户
        
        Args:
            user: 用户对象
            
        Returns:
            更新后的用户对象
        """
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        获取用户列表
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户对象列表
        """
        pass


class FileUserStorage(UserStorage):
    """基于文件的用户存储实现"""
    
    def __init__(self, data_dir: str = "data/users"):
        """
        初始化文件用户存储
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def _get_user_path(self, user_id: str) -> str:
        """
        获取用户文件路径
        
        Args:
            user_id: 用户ID
            
        Returns:
            文件路径
        """
        return os.path.join(self.data_dir, f"{user_id}.json")
    
    def _save_user(self, user: User) -> None:
        """
        保存用户到文件
        
        Args:
            user: 用户对象
        """
        user_path = self._get_user_path(user.id)
        
        # 保存敏感信息
        user_data = user.to_dict()
        user_data["access_token"] = user.access_token
        user_data["refresh_token"] = user.refresh_token
        user_data["token_expiry"] = user.token_expiry.isoformat() if user.token_expiry else None
        
        with open(user_path, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
    
    async def get_user(self, user_id: str) -> Optional[User]:
        user_path = self._get_user_path(user_id)
        
        if not os.path.exists(user_path):
            return None
        
        try:
            with open(user_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            return User.from_dict(user_data)
        except Exception:
            return None
    
    async def get_user_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        # 遍历所有用户文件查找匹配的提供商ID
        for filename in os.listdir(self.data_dir):
            if not filename.endswith('.json'):
                continue
                
            try:
                with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                    
                if user_data.get('provider') == provider and user_data.get('provider_id') == provider_id:
                    return User.from_dict(user_data)
            except Exception:
                continue
                
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        # 遍历所有用户文件查找匹配的邮箱
        for filename in os.listdir(self.data_dir):
            if not filename.endswith('.json'):
                continue
                
            try:
                with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                    
                if user_data.get('email') == email:
                    return User.from_dict(user_data)
            except Exception:
                continue
                
        return None
    
    async def create_user(self, user: User) -> User:
        self._save_user(user)
        return user
    
    async def update_user(self, user: User) -> User:
        self._save_user(user)
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        user_path = self._get_user_path(user_id)
        
        if not os.path.exists(user_path):
            return False
        
        try:
            os.remove(user_path)
            return True
        except Exception:
            return False
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        users = []
        
        # 获取所有用户文件
        user_files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
        
        # 应用分页
        paginated_files = user_files[offset:offset + limit]
        
        # 加载用户数据
        for filename in paginated_files:
            try:
                with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                users.append(User.from_dict(user_data))
            except Exception:
                continue
                
        return users


class SurrealUserStorage(UserStorage):
    """基于SurrealDB的用户存储实现 (已弃用)
    
    警告: 此类已被弃用，请使用 rainbow_agent.auth.storage.SurrealUserStorage
    """
    
    def __init__(self, db_connection=None):
        """
        初始化SurrealDB用户存储
        
        警告: 此类已被弃用，请使用 rainbow_agent.auth.storage.SurrealUserStorage
        
        Args:
            db_connection: SurrealDB连接
        """
        import warnings
        warnings.warn(
            "SurrealUserStorage in user.py is deprecated. "
            "Use rainbow_agent.auth.storage.SurrealUserStorage instead.",
            DeprecationWarning, stacklevel=2
        )
        self.db = db_connection
