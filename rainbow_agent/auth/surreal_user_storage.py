"""
SurrealDB用户存储

使用SurrealDB实现用户数据的持久化存储
"""
import abc
import asyncio
import logging
import uuid
from typing import List, Optional

from rainbow_agent.auth.models import User
from rainbow_agent.auth.storage import UserStorage
from rainbow_agent.storage.surreal_factory import SurrealStorageFactory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SurrealUserStorage(UserStorage):
    """使用SurrealDB实现的用户存储"""
    
    def __init__(self, db_url: str = "ws://localhost:8000/rpc", namespace: str = "rainbow", database: str = "agent"):
        """
        初始化SurrealDB用户存储
        
        Args:
            db_url: SurrealDB服务器URL
            namespace: SurrealDB命名空间
            database: SurrealDB数据库名称
        """
        self.factory = SurrealStorageFactory(db_url, namespace, database)
        self.db = self.factory.get_storage()
        self.table_name = "users"
        logger.info(f"SurrealUserStorage初始化: {db_url}/{namespace}/{database}/{self.table_name}")
        
        # 立即连接到数据库
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.db.connect())
            loop.run_until_complete(self._ensure_schema())
            logger.info("SurrealUserStorage: 数据库连接和模式初始化完成")
        except Exception as e:
            logger.error(f"SurrealUserStorage: 初始化失败: {e}")
            raise
    
    async def _ensure_schema(self):
        """确保用户表结构存在"""
        try:
            # 创建用户表和索引
            schema_query = """
            DEFINE TABLE users SCHEMAFULL;
            DEFINE FIELD id ON users TYPE string;
            DEFINE FIELD name ON users TYPE string;
            DEFINE FIELD username ON users TYPE string;
            DEFINE FIELD email ON users TYPE string;
            DEFINE FIELD provider ON users TYPE string;
            DEFINE FIELD provider_id ON users TYPE string;
            DEFINE FIELD avatar_url ON users TYPE string OPTIONAL;
            DEFINE FIELD password_hash ON users TYPE string OPTIONAL;
            
            -- 创建索引以加快查询
            DEFINE INDEX users_email ON users FIELDS email UNIQUE;
            DEFINE INDEX users_username ON users FIELDS username UNIQUE;
            DEFINE INDEX users_provider ON users FIELDS provider, provider_id UNIQUE;
            """
            
            await self.db.query(schema_query)
            logger.info("用户表结构创建成功")
        except Exception as e:
            logger.warning(f"创建用户表结构失败（可能已存在）: {e}")
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        try:
            result = await self.db.select(self.table_name, user_id)
            if result and len(result) > 0:
                user_data = result[0]
                return User.from_dict(user_data)
            return None
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        
        Args:
            email: 用户邮箱
            
        Returns:
            用户对象，如果不存在则返回None
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE email = $email LIMIT 1"
            result = await self.db.query(query, {"email": email})
            
            if result and len(result) > 0 and len(result[0]) > 0:
                user_data = result[0][0]
                return User.from_dict(user_data)
            return None
        except Exception as e:
            logger.error(f"通过邮箱获取用户失败: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        通过用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户对象，如果不存在则返回None
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE username = $username OR name = $username LIMIT 1"
            result = await self.db.query(query, {"username": username})
            
            if result and len(result) > 0 and len(result[0]) > 0:
                user_data = result[0][0]
                return User.from_dict(user_data)
            return None
        except Exception as e:
            logger.error(f"通过用户名获取用户失败: {e}")
            return None
    
    async def get_user_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        """
        通过认证提供商和提供商用户ID获取用户
        
        Args:
            provider: 认证提供商
            provider_id: 提供商用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE provider = $provider AND provider_id = $provider_id LIMIT 1"
            result = await self.db.query(query, {"provider": provider, "provider_id": provider_id})
            
            if result and len(result) > 0 and len(result[0]) > 0:
                user_data = result[0][0]
                return User.from_dict(user_data)
            return None
        except Exception as e:
            logger.error(f"通过提供商获取用户失败: {e}")
            return None
    
    async def create_user(self, user: User) -> User:
        """
        创建用户
        
        Args:
            user: 用户对象
            
        Returns:
            创建的用户对象
        """
        try:
            # 确保用户有ID
            if not user.id:
                user.id = str(uuid.uuid4())
            
            # 确保username属性存在
            if not hasattr(user, 'username') and hasattr(user, 'name'):
                setattr(user, 'username', user.name)
            
            # 转换为字典并创建记录
            user_dict = user.to_dict()
            
            # 确保所有必要字段都存在
            for field in ['id', 'name', 'username', 'email', 'provider', 'provider_id']:
                if field not in user_dict or not user_dict[field]:
                    if field == 'username' and 'name' in user_dict and user_dict['name']:
                        user_dict['username'] = user_dict['name']
                    elif field == 'email' and 'username' in user_dict and user_dict['username']:
                        user_dict['email'] = f"{user_dict['username']}@local.user"
                    else:
                        logger.warning(f"用户缺少必要字段: {field}")
            
            # 创建记录
            result = await self.db.create(self.table_name, user_dict)
            
            if result and len(result) > 0:
                logger.info(f"用户创建成功: {user.id}")
                # 确保返回的用户对象包含所有属性
                created_user = User.from_dict(result[0])
                
                # 复制特殊属性
                for attr in ['username', 'password_hash']:
                    if hasattr(user, attr):
                        setattr(created_user, attr, getattr(user, attr))
                
                return created_user
            else:
                logger.error(f"用户创建失败，无返回结果: {user.id}")
                return user
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return user
    
    async def update_user(self, user: User) -> User:
        """
        更新用户
        
        Args:
            user: 用户对象
            
        Returns:
            更新后的用户对象
        """
        try:
            # 转换为字典并更新记录
            user_dict = user.to_dict()
            result = await self.db.update(self.table_name, user.id, user_dict)
            
            if result and len(result) > 0:
                logger.info(f"用户更新成功: {user.id}")
                return User.from_dict(result[0])
            else:
                logger.error(f"用户更新失败: {user.id}")
                return user
        except Exception as e:
            logger.error(f"更新用户失败: {e}")
            return user
    
    async def delete_user(self, user_id: str) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            result = await self.db.delete(self.table_name, user_id)
            success = result is not None and len(result) > 0
            logger.info(f"用户删除{'成功' if success else '失败'}: {user_id}")
            return success
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            return False
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        列出用户
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        try:
            query = f"SELECT * FROM {self.table_name} LIMIT {limit} START {offset}"
            result = await self.db.query(query)
            
            if result and len(result) > 0 and len(result[0]) > 0:
                users = []
                for user_data in result[0]:
                    users.append(User.from_dict(user_data))
                return users
            return []
        except Exception as e:
            logger.error(f"列出用户失败: {e}")
            return []
    
    async def get_all_users(self) -> List[User]:
        """
        获取所有用户
        
        Returns:
            所有用户列表
        """
        try:
            query = f"SELECT * FROM {self.table_name}"
            result = await self.db.query(query)
            
            if result and len(result) > 0 and len(result[0]) > 0:
                users = []
                for user_data in result[0]:
                    user = User.from_dict(user_data)
                    users.append(user)
                return users
            return []
        except Exception as e:
            logger.error(f"获取所有用户失败: {e}")
            return []
    
    def get_all_users_sync(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        同步获取所有用户
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.list_users(limit, offset))
    
    def create_user_sync(self, user: User) -> User:
        """
        同步创建用户
        
        Args:
            user: 用户对象
            
        Returns:
            创建的用户对象
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.create_user(user))
