"""
用户认证存储

提供用户数据的存储和检索接口，支持多种存储后端。
"""
import abc
import os
import json
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from rainbow_agent.auth.models import User
from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)


class UserStorage(abc.ABC):
    """用户存储抽象基类"""
    
    @abc.abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        pass
    
    @abc.abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        
        Args:
            email: 用户邮箱
            
        Returns:
            用户对象，如果不存在则返回None
        """
        pass
    
    @abc.abstractmethod
    async def get_user_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        """
        通过认证提供商和提供商用户ID获取用户
        
        Args:
            provider: 认证提供商
            provider_id: 提供商用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        pass
    
    @abc.abstractmethod
    async def create_user(self, user: User) -> User:
        """
        创建用户
        
        Args:
            user: 用户对象
            
        Returns:
            创建的用户对象
        """
        pass
    
    @abc.abstractmethod
    async def update_user(self, user: User) -> User:
        """
        更新用户
        
        Args:
            user: 用户对象
            
        Returns:
            更新后的用户对象
        """
        pass
    
    @abc.abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abc.abstractmethod
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        列出用户
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        pass
    
    def get_user_sync(self, user_id: str) -> Optional[User]:
        """
        同步获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.get_user(user_id))
    
    def get_user_by_email_sync(self, email: str) -> Optional[User]:
        """
        同步通过邮箱获取用户
        
        Args:
            email: 用户邮箱
            
        Returns:
            用户对象，如果不存在则返回None
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.get_user_by_email(email))
    
    def get_user_by_provider_sync(self, provider: str, provider_id: str) -> Optional[User]:
        """
        同步通过认证提供商和提供商用户ID获取用户
        
        Args:
            provider: 认证提供商
            provider_id: 提供商用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.get_user_by_provider(provider, provider_id))


class FileUserStorage(UserStorage):
    """文件用户存储实现"""
    
    def __init__(self, storage_dir: str = None):
        """
        初始化文件用户存储
        
        Args:
            storage_dir: 存储目录，默认为'user_data'
        """
        self.storage_dir = storage_dir or 'user_data'
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"文件用户存储初始化完成，存储目录: {self.storage_dir}")
    
    def _get_user_path(self, user_id: str) -> str:
        """
        获取用户文件路径
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户文件路径
        """
        return os.path.join(self.storage_dir, f"{user_id}.json")
    
    def _save_user(self, user: User) -> bool:
        """
        保存用户到文件
        
        Args:
            user: 用户对象
            
        Returns:
            是否保存成功
        """
        try:
            user_path = self._get_user_path(user.id)
            with open(user_path, 'w', encoding='utf-8') as f:
                json.dump(user.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存用户失败: {e}")
            return False
    
    def _load_all_users(self) -> List[User]:
        """
        加载所有用户
        
        Returns:
            用户列表
        """
        users = []
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(self.storage_dir, filename), 'r', encoding='utf-8') as f:
                            user_data = json.load(f)
                            users.append(User.from_dict(user_data))
                    except Exception as e:
                        logger.error(f"加载用户文件失败: {filename}, {e}")
        except Exception as e:
            logger.error(f"加载所有用户失败: {e}")
        return users
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        try:
            user_path = self._get_user_path(user_id)
            if not os.path.exists(user_path):
                return None
            
            with open(user_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                return User.from_dict(user_data)
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
            users = self._load_all_users()
            for user in users:
                if user.email == email:
                    return user
            return None
        except Exception as e:
            logger.error(f"通过邮箱获取用户失败: {e}")
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
            users = self._load_all_users()
            for user in users:
                if user.provider == provider and user.provider_id == provider_id:
                    return user
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
            
            # 保存用户
            success = self._save_user(user)
            if success:
                logger.info(f"用户创建成功: {user.id}")
            else:
                logger.error(f"用户创建失败: {user.id}")
            
            return user
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
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
            # 保存用户
            success = self._save_user(user)
            if success:
                logger.info(f"用户更新成功: {user.id}")
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
            user_path = self._get_user_path(user_id)
            if not os.path.exists(user_path):
                return False
            
            os.remove(user_path)
            logger.info(f"用户删除成功: {user_id}")
            return True
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
            # 加载所有用户
            users = self._load_all_users()
            
            # 应用分页
            start = offset
            end = offset + limit
            paginated_users = users[start:end] if start < len(users) else []
            
            return paginated_users
        except Exception as e:
            logger.error(f"列出用户失败: {e}")
            return []
            
    def create_user_sync(self, user: User) -> User:
        """
        同步创建用户
        
        Args:
            user: 用户对象
            
        Returns:
            创建的用户对象
        """
        try:
            # 确保用户有ID
            if not user.id:
                user.id = str(uuid.uuid4())
            
            # 保存用户
            success = self._save_user(user)
            if success:
                logger.info(f"用户创建成功: {user.id}")
            else:
                logger.error(f"用户创建失败: {user.id}")
            
            return user
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return user
            
    def update_user_sync(self, user: User) -> User:
        """
        同步更新用户
        
        Args:
            user: 用户对象
            
        Returns:
            更新后的用户对象
        """
        try:
            # 保存用户
            success = self._save_user(user)
            if success:
                logger.info(f"用户更新成功: {user.id}")
            else:
                logger.error(f"用户更新失败: {user.id}")
            
            return user
        except Exception as e:
            logger.error(f"更新用户失败: {e}")
            return user
            
    def delete_user_sync(self, user_id: str) -> bool:
        """
        同步删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            # 获取用户文件路径
            user_path = self._get_user_path(user_id)
            
            # 如果文件存在，删除它
            if os.path.exists(user_path):
                os.remove(user_path)
                logger.info(f"用户删除成功: {user_id}")
                return True
            else:
                logger.warning(f"用户不存在: {user_id}")
                return False
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            return False
            
    def list_users_sync(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        同步列出用户
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        try:
            # 加载所有用户
            users = self._load_all_users()
            
            # 应用分页
            start = offset
            end = offset + limit
            paginated_users = users[start:end] if start < len(users) else []
            
            return paginated_users
        except Exception as e:
            logger.error(f"列出用户失败: {e}")
            return []
    
    def get_all_users_sync(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        获取所有用户（同步版本）
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        return self._load_all_users()[offset:offset+limit]


class SurrealUserStorage(UserStorage):
    """SurrealDB用户存储实现
    
    基于 test_surreal_http.py 中的简洁方法实现，使用官方 SurrealDB Python 客户端的 WebSocket 连接
    和直接的 create、select、update 和 delete 方法。
    """
    
    def __init__(self, db_client=None):
        """
        初始化SurrealDB用户存储
        
        Args:
            db_client: SurrealDB客户端 (UnifiedSurrealClient 实例)
        """
        self.db = db_client
        self.table = "users"
        
        # 异步初始化数据库模式
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 尝试初始化数据库模式
        if self.db:
            try:
                loop.run_until_complete(self.init_db_schema())
                logger.info("用户数据库模式初始化成功")
                
                # 验证数据库模式
                schema_status = loop.run_until_complete(self.check_db_schema())
                logger.info(f"用户数据库模式验证结果: {schema_status}")
            except Exception as e:
                logger.warning(f"用户数据库模式初始化失败: {e}")
                
    async def check_db_schema(self):
        """验证数据库模式是否正确"""
        try:
            # 首先尝试直接查询users表是否存在
            try:
                # 使用简单的COUNT查询来检查表是否存在
                count_result = self.db.execute_sql(f"SELECT count() FROM {self.table} LIMIT 1")
                # 如果查询成功执行，表就存在
                users_table_exists = True
                logger.info(f"通过COUNT查询确认{self.table}表存在")
            except Exception as count_err:
                logger.warning(f"COUNT查询失败，可能是表不存在: {count_err}")
                users_table_exists = False
                
            # 如果简单查询失败，尝试使用INFO FOR DB（可能在某些SurrealDB版本中不可用）
            if not users_table_exists:
                try:
                    tables_result = self.db.execute_sql("INFO FOR DB")
                    if not tables_result or len(tables_result) == 0:
                        logger.warning("INFO FOR DB返回空结果，尝试替代方法验证表结构")
                    else:
                        # 解析表信息
                        db_info = tables_result[0]
                        tables = []
                        if isinstance(db_info, list) and len(db_info) > 0:
                            for item in db_info:
                                if isinstance(item, dict) and "tables" in item:
                                    tables = item.get("tables", [])
                                    break
                                    
                        # 检查users表是否存在
                        users_table_exists = any(table.get("name") == self.table for table in tables) if tables else False
                        if users_table_exists:
                            logger.info(f"通过INFO FOR DB确认{self.table}表存在")
                except Exception as info_err:
                    logger.warning(f"INFO FOR DB查询失败: {info_err}，尝试替代方法验证表结构")
            
            # 如果表不存在，尝试创建它
            if not users_table_exists:
                logger.warning(f"{self.table}表可能不存在，尝试重新初始化")
                try:
                    # 尝试重新初始化数据库模式
                    await self.init_db_schema()
                    users_table_exists = True
                    logger.info(f"已重新初始化{self.table}表结构")
                except Exception as init_err:
                    logger.error(f"重新初始化表结构失败: {init_err}")
                    return {"status": "error", "message": f"表不存在且无法创建: {init_err}"}
            
            # 尝试获取表结构信息（可能在某些SurrealDB版本中不可用）
            table_info = None
            try:
                table_info = self.db.execute_sql(f"INFO FOR TABLE {self.table}")
                logger.info(f"成功获取{self.table}表结构信息")
            except Exception as table_info_err:
                logger.warning(f"获取表结构信息失败: {table_info_err}，但表可能仍然存在")
            
            # 最后验证表是否可用
            try:
                # 尝试执行一个简单的查询来验证表是否可用
                test_query = self.db.execute_sql(f"SELECT * FROM {self.table} LIMIT 1")
                logger.info(f"表{self.table}可用，可以正常查询")
            except Exception as test_err:
                logger.error(f"表{self.table}查询测试失败: {test_err}")
                return {"status": "error", "message": f"表存在但无法查询: {test_err}"}
            
            return {
                "status": "success",
                "table_exists": users_table_exists,
                "table_info": table_info
            }
        except Exception as e:
            logger.error(f"验证数据库模式失败: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        try:
            # 处理复杂ID格式 (如果是字典格式的ID)
            if isinstance(user_id, dict) or (isinstance(user_id, str) and user_id.startswith('{')):
                # 如果是字符串形式的字典，尝试解析
                if isinstance(user_id, str):
                    try:
                        import ast
                        user_id_dict = ast.literal_eval(user_id)
                        if isinstance(user_id_dict, dict) and 'id' in user_id_dict:
                            user_id = user_id_dict['id']
                    except Exception as parse_err:
                        logger.error(f"解析用户ID失败: {parse_err}")
                        # 如果解析失败，尝试使用原始ID
                else:
                    # 如果已经是字典，直接获取ID
                    if 'id' in user_id:
                        user_id = user_id['id']
            
            # 使用SurrealDB的RecordID查询方式
            # 先尝试使用原始ID
            logger.info(f"查询用户ID: {user_id}")
            
            # 方法1: 使用Record ID方式查询
            if ':' in str(user_id):
                # 如果ID中包含冒号，直接使用
                record_id = user_id
            else:
                # 如果没有表名前缀，添加它
                record_id = f"{self.table}:{user_id}"
            
            # 方法1: 尝试使用SurrealDB的Record ID语法
            try:
                # 使用SurrealDB的Record ID语法: ⟨table:id⟩
                result = self.db.execute_sql(f"SELECT * FROM ⟨{record_id}⟩")
                logger.info(f"Record ID语法查询结果: {result}")
                if result and len(result) > 0:
                    if isinstance(result[0], list) and len(result[0]) > 0:
                        user_data = result[0][0]
                        return User.from_dict(user_data)
                    elif isinstance(result[0], dict):
                        return User.from_dict(result[0])
            except Exception as e:
                logger.warning(f"Record ID语法查询失败: {e}")
            
            # 方法2: 使用对象ID匹配查询
            uuid_part = user_id.split(':')[-1] if ':' in str(user_id) else user_id
            # 查询ID对象中的id字段匹配
            result = self.db.execute_sql(f"SELECT * FROM {self.table} WHERE id.id = '{uuid_part}'")
            
            logger.info(f"UUID部分查询结果: {result}")
            if result and len(result) > 0:
                if isinstance(result[0], list) and len(result[0]) > 0:
                    user_data = result[0][0]
                    return User.from_dict(user_data)
                elif isinstance(result[0], dict):
                    return User.from_dict(result[0])
            
            # 如果仍然失败，尝试获取所有用户并手动过滤
            try:
                all_users = self.db.execute_sql(f"SELECT * FROM {self.table}")
                if all_users and len(all_users) > 0:
                    for user_batch in all_users:
                        if isinstance(user_batch, list):
                            for user_data in user_batch:
                                if isinstance(user_data, dict):
                                    # 检查ID是否匹配
                                    if 'id' in user_data:
                                        if isinstance(user_data['id'], dict) and 'id' in user_data['id'] and user_data['id']['id'] == user_id:
                                            logger.info(f"通过手动过滤ID找到用户: {user_data}")
                                            return User.from_dict(user_data)
                                        elif user_data['id'] == user_id:
                                            logger.info(f"通过手动过滤ID找到用户: {user_data}")
                                            return User.from_dict(user_data)
                        elif isinstance(user_batch, dict):
                            # 检查ID是否匹配
                            if 'id' in user_batch:
                                if isinstance(user_batch['id'], dict) and 'id' in user_batch['id'] and user_batch['id']['id'] == user_id:
                                    logger.info(f"通过手动过滤ID找到用户: {user_batch}")
                                    return User.from_dict(user_batch)
                                elif user_batch['id'] == user_id:
                                    logger.info(f"通过手动过滤ID找到用户: {user_batch}")
                                    return User.from_dict(user_batch)
            except Exception as all_users_err:
                logger.error(f"获取所有用户失败: {all_users_err}")
            
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
            # 构建查询
            query = f"SELECT * FROM {self.table} WHERE email = '{email}'"
            logger.info(f"通过邮箱查询用户: {query}")
            
            # 执行查询
            result = self.db.execute_sql(query)
            logger.info(f"邮箱查询结果: {result}")
            
            # 处理结果
            if result and len(result) > 0:
                if isinstance(result[0], list) and len(result[0]) > 0:
                    user_data = result[0][0]
                    logger.info(f"找到用户: {user_data}")
                    return User.from_dict(user_data)
                elif isinstance(result[0], dict):
                    user_data = result[0]
                    logger.info(f"找到用户: {user_data}")
                    return User.from_dict(user_data)
            
            # 尝试使用替代查询格式
            alt_query = f"SELECT * FROM {self.table} WHERE email = '{email}';"
            logger.info(f"尝试替代邮箱查询: {alt_query}")
            alt_result = self.db.execute_sql(alt_query)
            logger.info(f"替代邮箱查询结果: {alt_result}")
            
            if alt_result and len(alt_result) > 0:
                if isinstance(alt_result[0], list) and len(alt_result[0]) > 0:
                    user_data = alt_result[0][0]
                    logger.info(f"找到用户: {user_data}")
                    return User.from_dict(user_data)
                elif isinstance(alt_result[0], dict):
                    user_data = alt_result[0]
                    logger.info(f"找到用户: {user_data}")
                    return User.from_dict(user_data)
            
            return None
        except Exception as e:
            logger.error(f"通过邮箱获取用户失败: {e}")
            
            # 如果错误是数字0，尝试直接查询数据库中的所有用户
            if str(e) == "0":
                try:
                    logger.info(f"检测到错误代码0，尝试查询所有用户并过滤")
                    all_users_query = f"SELECT * FROM {self.table} LIMIT 100"
                    all_users = self.db.execute_sql(all_users_query)
                    logger.info(f"查询到 {len(all_users) if all_users else 0} 个用户")
                    
                    if all_users and len(all_users) > 0:
                        # 手动过滤匹配的用户
                        for user_batch in all_users:
                            if isinstance(user_batch, list):
                                for user_data in user_batch:
                                    if isinstance(user_data, dict) and user_data.get('email') == email:
                                        logger.info(f"通过手动过滤找到用户: {user_data}")
                                        return User.from_dict(user_data)
                            elif isinstance(user_batch, dict) and user_batch.get('email') == email:
                                logger.info(f"通过手动过滤找到用户: {user_batch}")
                                return User.from_dict(user_batch)
                except Exception as inner_e:
                    logger.error(f"尝试查询所有用户失败: {inner_e}")
            
            return None
    
    async def get_user_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        """
        通过认证提供商获取用户
        
        Args:
            provider: 认证提供商
            provider_id: 提供商用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        try:
            # 构建查询
            query = f"SELECT * FROM {self.table} WHERE provider = '{provider}' AND provider_id = '{provider_id}'"
            logger.info(f"通过提供商查询用户: {query}")
            
            # 执行查询
            result = self.db.execute_sql(query)
            logger.info(f"提供商查询结果: {result}")
            
            # 处理结果
            if result and len(result) > 0:
                if isinstance(result[0], list) and len(result[0]) > 0:
                    user_data = result[0][0]
                    logger.info(f"找到用户: {user_data}")
                    return User.from_dict(user_data)
                elif isinstance(result[0], dict):
                    user_data = result[0]
                    logger.info(f"找到用户: {user_data}")
                    return User.from_dict(user_data)
            
            # 尝试使用替代查询格式
            alt_query = f"SELECT * FROM {self.table} WHERE provider = '{provider}' AND provider_id = '{provider_id}';"
            logger.info(f"尝试替代提供商查询: {alt_query}")
            alt_result = self.db.execute_sql(alt_query)
            logger.info(f"替代提供商查询结果: {alt_result}")
            
            if alt_result and len(alt_result) > 0:
                if isinstance(alt_result[0], list) and len(alt_result[0]) > 0:
                    user_data = alt_result[0][0]
                    logger.info(f"找到用户: {user_data}")
                    return User.from_dict(user_data)
                elif isinstance(alt_result[0], dict):
                    user_data = alt_result[0]
                    logger.info(f"找到用户: {user_data}")
                    return User.from_dict(user_data)
            
            return None
        except Exception as e:
            logger.error(f"通过提供商获取用户失败: {e}")
            
            # 如果错误是数字0，尝试直接查询数据库中的所有用户
            if str(e) == "0":
                try:
                    logger.info(f"检测到错误代码0，尝试查询所有用户并过滤")
                    all_users_query = f"SELECT * FROM {self.table} LIMIT 100"
                    all_users = self.db.execute_sql(all_users_query)
                    logger.info(f"查询到 {len(all_users) if all_users else 0} 个用户")
                    
                    if all_users and len(all_users) > 0:
                        # 手动过滤匹配的用户
                        for user_batch in all_users:
                            if isinstance(user_batch, list):
                                for user_data in user_batch:
                                    if isinstance(user_data, dict) and user_data.get('provider') == provider and user_data.get('provider_id') == provider_id:
                                        logger.info(f"通过手动过滤找到用户: {user_data}")
                                        return User.from_dict(user_data)
                            elif isinstance(user_batch, dict) and user_batch.get('provider') == provider and user_batch.get('provider_id') == provider_id:
                                logger.info(f"通过手动过滤找到用户: {user_batch}")
                                return User.from_dict(user_batch)
                except Exception as inner_e:
                    logger.error(f"尝试查询所有用户失败: {inner_e}")
            
            return None
    
    async def init_db_schema(self):
        """初始化用户数据库模式"""
        if not self.db:
            logger.error("数据库客户端不可用，无法初始化模式")
            return False
            
        try:
            # 创建用户表和必要的索引
            queries = [
                # 定义用户表和字段
                f"DEFINE TABLE {self.table} SCHEMAFULL;",
                
                # 定义必要的字段
                f"DEFINE FIELD id ON {self.table} TYPE string;",
                f"DEFINE FIELD email ON {self.table} TYPE string;",
                f"DEFINE FIELD name ON {self.table} TYPE string;",
                f"DEFINE FIELD username ON {self.table} TYPE string;",
                f"DEFINE FIELD password_hash ON {self.table} TYPE string;",
                f"DEFINE FIELD avatar_url ON {self.table} TYPE string;",
                f"DEFINE FIELD provider ON {self.table} TYPE string;",
                f"DEFINE FIELD provider_id ON {self.table} TYPE string;",
                f"DEFINE FIELD created_at ON {self.table} TYPE datetime;",
                f"DEFINE FIELD last_login ON {self.table} TYPE datetime;",
                f"DEFINE FIELD roles ON {self.table} TYPE array;",
                f"DEFINE FIELD is_active ON {self.table} TYPE bool;",
                f"DEFINE FIELD metadata ON {self.table} TYPE object;",
                
                # AI相关字段
                f"DEFINE FIELD preferences ON {self.table} TYPE object;",
                f"DEFINE FIELD ai_settings ON {self.table} TYPE object;",
                f"DEFINE FIELD interaction_history ON {self.table} TYPE array;",
                f"DEFINE FIELD embeddings ON {self.table} TYPE object;",
                f"DEFINE FIELD usage_stats ON {self.table} TYPE object;",
                f"DEFINE FIELD tags ON {self.table} TYPE array;",
                f"DEFINE FIELD timezone ON {self.table} TYPE string;",
                f"DEFINE FIELD language ON {self.table} TYPE string;",
                
                # 创建索引
                f"DEFINE INDEX email_idx ON {self.table} FIELDS email UNIQUE;",
                f"DEFINE INDEX provider_idx ON {self.table} FIELDS provider, provider_id UNIQUE;",
            ]
            
            # 执行所有查询
            for query in queries:
                try:
                    self.db.execute_sql(query)
                except Exception as e:
                    # 忽略已存在的表/字段错误
                    if "already exists" not in str(e):
                        logger.warning(f"初始化模式查询失败: {query} - {e}")
            
            return True
        except Exception as e:
            logger.error(f"初始化用户数据库模式失败: {e}")
            return False
    
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
            
            # 转换为字典
            user_dict = user.to_dict()
            
            # 修复日期时间字段 - 将ISO格式字符串转回datetime对象
            # SurrealDB需要实际的datetime对象而不是字符串
            if user.created_at:
                user_dict["created_at"] = user.created_at  # 使用原始datetime对象
            if user.last_login:
                user_dict["last_login"] = user.last_login  # 使用原始datetime对象
            
            # 添加敏感字段（不包含在to_dict中）
            if user.access_token:
                user_dict["access_token"] = user.access_token
            if user.refresh_token:
                user_dict["refresh_token"] = user.refresh_token
            if user.token_expiry:
                user_dict["token_expiry"] = user.token_expiry  # 使用原始datetime对象
            
            # 确保所有必需的字符串字段有有效值（不为None）
            # SurrealDB对字段类型有严格要求，不接受None作为字符串类型的值
            if user_dict.get("timezone") is None:
                user_dict["timezone"] = "UTC"  # 默认时区
                logger.info(f"设置默认时区: UTC")
            
            if user_dict.get("language") is None:
                user_dict["language"] = "en"  # 默认语言
                logger.info(f"设置默认语言: en")
            
            # 检查并设置其他可能为None的字符串字段
            # 对于email字段，如果为None或空，使用用户ID以避免唯一索引冲突
            if not user_dict.get("email"):
                user_dict["email"] = f"user_{user_dict['id']}@local.tmp"  # 使用临时邮箱格式避免冲突
                logger.info(f"设置临时邮箱: {user_dict['email']}")
            
            # 处理provider字段以避免唯一索引冲突
            if not user_dict.get("provider"):
                user_dict["provider"] = "local"  # 本地用户使用"local"
                logger.info(f"设置provider为: local")
            
            if not user_dict.get("provider_id"):
                user_dict["provider_id"] = user_dict['id']  # 使用用户ID作为provider_id
                logger.info(f"设置provider_id为用户ID: {user_dict['id']}")
                
            string_fields = ["name", "avatar_url"]
            for field in string_fields:
                if user_dict.get(field) is None:
                    user_dict[field] = ""  # 空字符串比None更安全
                    logger.info(f"将{field}字段从None设置为空字符串")
            
            logger.info(f"用户数据处理后: timezone={user_dict.get('timezone')}, language={user_dict.get('language')}")
            
            # 使用 create_record 方法创建用户记录
            logger.info(f"使用 create_record 创建用户: {user.id}, 数据类型: {type(user.created_at)}, {type(user.last_login)}")
            
            try:
                result = self.db.create_record(self.table, user_dict)
                logger.info(f"SurrealDB create_record 响应: {result}")
                
                # 验证创建是否成功
                if result:
                    logger.info(f"用户创建成功: {user.id}")
                    # 如果返回了用户数据，使用它更新我们的用户对象
                    if isinstance(result, dict):
                        # 更新用户对象的字段
                        for key, value in result.items():
                            if key in user_dict and key != 'id':
                                setattr(user, key, value)
                        logger.info(f"用户对象已用返回数据更新")
                else:
                    logger.warning(f"用户创建可能失败，尝试验证: {user.id}")
                    verify_query = f"SELECT * FROM {self.table} WHERE id = '{user.id}';"
                    logger.info(f"验证创建查询: {verify_query}")
                    verify_result = self.db.execute_sql(verify_query)
                    logger.info(f"SurrealDB 验证查询响应: {verify_result}")
                    
                    # 如果验证查询返回了结果，说明用户创建成功
                    if verify_result and len(verify_result) > 0 and len(verify_result[0]) > 0:
                        logger.info(f"通过验证查询确认用户创建成功: {user.id}")
            except Exception as create_error:
                logger.error(f"创建用户时出现错误: {create_error}")
                
                # 检查是否是唯一约束冲突错误
                error_str = str(create_error)
                if "index" in error_str and "already contains" in error_str:
                    logger.info("检测到唯一约束冲突，尝试获取已存在的用户")
                    
                    # 尝试通过邮箱查找用户
                    if user.email:
                        logger.info(f"通过邮箱查找已存在用户: {user.email}")
                        try:
                            # 使用异步方法获取用户
                            existing_user = await self.get_user_by_email(user.email)
                            if existing_user:
                                logger.info(f"通过邮箱找到已存在用户: {existing_user.id} - {existing_user.email}")
                                return existing_user
                        except Exception as email_err:
                            logger.error(f"通过邮箱获取已存在用户失败: {email_err}")
                    
                    # 如果邮箱查询失败，尝试通过提供商ID查找
                    if user.provider and user.provider_id:
                        logger.info(f"通过提供商查找已存在用户: {user.provider}/{user.provider_id}")
                        try:
                            # 使用异步方法获取用户
                            existing_user = await self.get_user_by_provider(user.provider, user.provider_id)
                            if existing_user:
                                logger.info(f"通过提供商找到已存在用户: {existing_user.id} - {existing_user.email}")
                                return existing_user
                        except Exception as provider_err:
                            logger.error(f"通过提供商获取已存在用户失败: {provider_err}")
                    
                    # 如果上述方法都失败，尝试直接查询所有用户并手动过滤
                    try:
                        logger.info("尝试查询所有用户并手动过滤")
                        all_users_query = f"SELECT * FROM {self.table} LIMIT 100"
                        all_users = self.db.execute_sql(all_users_query)
                        logger.info(f"查询到 {len(all_users) if all_users else 0} 个用户")
                        
                        if all_users and len(all_users) > 0:
                            # 手动过滤匹配的用户
                            for user_batch in all_users:
                                if isinstance(user_batch, list):
                                    for user_data in user_batch:
                                        if isinstance(user_data, dict):
                                            # 通过邮箱匹配
                                            if user.email and user_data.get('email') == user.email:
                                                logger.info(f"通过手动过滤邮箱找到用户: {user_data}")
                                                return User.from_dict(user_data)
                                            # 通过提供商匹配
                                            if user.provider and user.provider_id and \
                                               user_data.get('provider') == user.provider and \
                                               user_data.get('provider_id') == user.provider_id:
                                                logger.info(f"通过手动过滤提供商找到用户: {user_data}")
                                                return User.from_dict(user_data)
                                elif isinstance(user_batch, dict):
                                    # 通过邮箱匹配
                                    if user.email and user_batch.get('email') == user.email:
                                        logger.info(f"通过手动过滤邮箱找到用户: {user_batch}")
                                        return User.from_dict(user_batch)
                                    # 通过提供商匹配
                                    if user.provider and user.provider_id and \
                                       user_batch.get('provider') == user.provider and \
                                       user_batch.get('provider_id') == user.provider_id:
                                        logger.info(f"通过手动过滤提供商找到用户: {user_batch}")
                                        return User.from_dict(user_batch)
                    except Exception as all_users_err:
                        logger.error(f"查询所有用户失败: {all_users_err}")
                        
                    logger.warning("无法找到已存在的用户，尽管检测到唯一约束冲突")
                    # 创建失败但无法找到已存在用户，返回原始用户对象
                    # 这种情况下，调用者应该处理这个不完整的用户对象
            
            return user
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            import traceback
            logger.error(f"创建用户错误详情: {traceback.format_exc()}")
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
            # 转换为字典
            user_dict = user.to_dict()
            
            # 确保日期时间字段是正确的格式
            if user.created_at and not isinstance(user.created_at, str):
                user_dict['created_at'] = user.created_at
            if user.last_login and not isinstance(user.last_login, str):
                user_dict['last_login'] = datetime.now()
            
            # 确保必要字段有值
            if 'timezone' not in user_dict or not user_dict['timezone']:
                user_dict['timezone'] = 'UTC'
            
            # 使用create_record方法更新记录
            try:
                # 尝试使用create_record方法
                if hasattr(self.db, 'create_record'):
                    # 确保ID格式正确
                    record_id = user.id
                    if ':' not in record_id:
                        record_id = f"{self.table}:{record_id}"
                    
                    # 执行更新
                    logger.info(f"使用create_record更新用户: {record_id}")
                    result = self.db.create_record(self.table, user_dict)
                    
                    if result:
                        logger.info(f"更新用户成功: {result}")
                        return User.from_dict(result)
                else:
                    # 回退到SQL更新
                    logger.info(f"使用SQL更新用户: {user.id}")
                    
                    # 构建更新SQL
                    update_fields = []
                    for key, value in user_dict.items():
                        if key != 'id':  # 不更新ID字段
                            if isinstance(value, str):
                                update_fields.append(f"{key} = '{value}'")
                            elif isinstance(value, (int, float, bool)):
                                update_fields.append(f"{key} = {value}")
                            elif value is None:
                                update_fields.append(f"{key} = NULL")
                            elif isinstance(value, (list, dict)):
                                import json
                                json_value = json.dumps(value)
                                update_fields.append(f"{key} = {json_value}")
                            elif isinstance(value, datetime):
                                # 处理日期时间
                                update_fields.append(f"{key} = '{value.isoformat()}'")
                    
                    update_sql = f"UPDATE {self.table}:{user.id} SET {', '.join(update_fields)}"
                    
                    # 执行更新
                    result = self.db.execute_sql(update_sql)
                    logger.info(f"SQL更新结果: {result}")
                    
                    # 获取更新后的用户
                    updated_user = await self.get_user(user.id)
                    if updated_user:
                        return updated_user
            except Exception as update_err:
                logger.error(f"更新用户时出错: {update_err}")
            
            return user
        except Exception as e:
            logger.error(f"更新用户失败: {e}")
            return user
    
    async def delete_user(self, user_id: str) -> bool:
        """
        删除用户 - 修复版本，使用与登录系统相同的查询方式
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            logger.info(f"开始删除用户: {user_id}")
            
            # 使用与登录系统相同的方式获取所有用户，然后找到目标用户
            all_users_query = f"SELECT * FROM {self.table}"
            all_users_result = self.db.execute_sql(all_users_query)
            
            target_user = None
            target_username = None
            
            if all_users_result:
                for user_data in all_users_result:
                    if isinstance(user_data, dict):
                        # 处理SurrealDB的复杂ID格式
                        db_user_id = user_data.get('id', {})
                        if isinstance(db_user_id, dict) and 'id' in db_user_id:
                            actual_id = db_user_id['id']
                        else:
                            actual_id = str(db_user_id)
                        
                        # 找到匹配的用户
                        if actual_id == user_id:
                            target_user = user_data
                            target_username = user_data.get('username')
                            logger.info(f"找到目标用户: {target_username} (ID: {actual_id})")
                            break
            
            if not target_user or not target_username:
                logger.warning(f"未找到要删除的用户: {user_id}")
                return False
            
            # 使用用户名删除，因为这与登录系统的查询模式一致
            delete_sql = f"DELETE FROM {self.table} WHERE username = '{target_username}'"
            logger.info(f"执行删除: {delete_sql}")
            result = self.db.execute_sql(delete_sql)
            logger.info(f"删除结果: {result}")
            
            # 验证删除 - 使用与登录系统相同的查询方式
            verify_users = self.db.execute_sql(all_users_query)
            user_still_exists = False
            
            if verify_users:
                for user_data in verify_users:
                    if isinstance(user_data, dict):
                        if user_data.get('username') == target_username:
                            user_still_exists = True
                            logger.warning(f"验证失败：用户仍存在: {user_data}")
                            break
            
            if not user_still_exists:
                logger.info(f"✅ 用户删除成功: {target_username} (ID: {user_id})")
                return True
            else:
                logger.error(f"❌ 用户删除失败，验证显示用户仍存在: {target_username}")
                return False
                
        except Exception as e:
            logger.error(f"删除用户异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
            # 构建查询
            query = f"SELECT * FROM {self.table} LIMIT $limit START $offset"
            params = {"limit": limit, "offset": offset}
            
            # 执行查询
            result = await self.db.query(query, params)
            
            # 处理结果
            users = []
            if result and len(result) > 0 and len(result[0]) > 0:
                for user_data in result[0]:
                    users.append(User.from_dict(user_data))
            
            return users
        except Exception as e:
            logger.error(f"列出用户失败: {e}")
            return []
            
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
        
        # 检查数据库连接
        if not self.db:
            logger.error("数据库客户端不可用，无法创建用户")
            # 确保用户有ID
            if not user.id:
                user.id = str(uuid.uuid4())
            return user
        
        logger.info(f"开始创建用户: {user.email} (provider: {user.provider})")
        
        # 验证数据库模式是否正确
        schema_status = loop.run_until_complete(self.check_db_schema())
        logger.info(f"创建用户前数据库模式验证: {schema_status}")
        
        if schema_status.get('status') != 'success':
            logger.error(f"数据库模式验证失败，尝试重新初始化模式")
            loop.run_until_complete(self.init_db_schema())
        
        try:
            # 转换为字典并记录
            user_dict = user.to_dict()
            logger.info(f"用户数据: {user_dict}")
            
            try:
                created_user = loop.run_until_complete(self.create_user(user))
                logger.info(f"用户创建成功: {created_user.id} - {created_user.email}")
                
                # 验证用户是否真的被创建  
                verification = self.db.execute_sql(f"SELECT * FROM {self.table} WHERE id = '{created_user.id}'")
                if verification and len(verification) > 0 and len(verification[0]) > 0:
                    logger.info(f"用户验证成功: {created_user.id} 存在于数据库中")
                    logger.info(f"验证结果: {verification}")
                    return created_user
                else:
                    logger.error(f"用户验证失败: {created_user.id} 不存在于数据库中")
                    logger.error(f"验证查询结果: {verification}")
            except Exception as create_error:
                logger.error(f"创建用户时出现错误: {create_error}")
                error_str = str(create_error)
                
                # 检查是否是唯一约束冲突错误
                if "index" in error_str and "already contains" in error_str:
                    logger.info("检测到唯一约束冲突，尝试获取已存在的用户")
                    
                    # 尝试通过邮箱查找用户
                    if user.email:
                        logger.info(f"通过邮箱查找已存在用户: {user.email}")
                        try:
                            # 使用异步方法获取用户
                            existing_user = loop.run_until_complete(self.get_user_by_email(user.email))
                            if existing_user:
                                logger.info(f"通过邮箱找到已存在用户: {existing_user.id} - {existing_user.email}")
                                return existing_user
                        except Exception as email_err:
                            logger.error(f"通过邮箱获取已存在用户失败: {email_err}")
                            
                            # 如果错误是数字0，尝试直接查询
                            if str(email_err) == "0":
                                try:
                                    # 尝试替代查询格式
                                    alt_query = f"SELECT * FROM {self.table} WHERE email = '{user.email}';"
                                    logger.info(f"尝试替代邮箱查询: {alt_query}")
                                    alt_result = self.db.execute_sql(alt_query)
                                    logger.info(f"替代邮箱查询结果: {alt_result}")
                                    
                                    if alt_result and len(alt_result) > 0:
                                        if isinstance(alt_result[0], list) and len(alt_result[0]) > 0:
                                            user_data = alt_result[0][0]
                                            logger.info(f"找到用户: {user_data}")
                                            return User.from_dict(user_data)
                                        elif isinstance(alt_result[0], dict):
                                            user_data = alt_result[0]
                                            logger.info(f"找到用户: {user_data}")
                                            return User.from_dict(user_data)
                                except Exception as alt_err:
                                    logger.error(f"替代邮箱查询失败: {alt_err}")
                    
                    # 如果邮箱查询失败，尝试通过提供商ID查找
                    if user.provider and user.provider_id:
                        logger.info(f"通过提供商查找已存在用户: {user.provider}/{user.provider_id}")
                        try:
                            # 使用异步方法获取用户
                            existing_user = loop.run_until_complete(self.get_user_by_provider(user.provider, user.provider_id))
                            if existing_user:
                                logger.info(f"通过提供商找到已存在用户: {existing_user.id} - {existing_user.email}")
                                return existing_user
                        except Exception as provider_err:
                            logger.error(f"通过提供商获取已存在用户失败: {provider_err}")
                            
                            # 如果错误是数字0，尝试直接查询
                            if str(provider_err) == "0":
                                try:
                                    # 尝试替代查询格式
                                    alt_query = f"SELECT * FROM {self.table} WHERE provider = '{user.provider}' AND provider_id = '{user.provider_id}';"
                                    logger.info(f"尝试替代提供商查询: {alt_query}")
                                    alt_result = self.db.execute_sql(alt_query)
                                    logger.info(f"替代提供商查询结果: {alt_result}")
                                    
                                    if alt_result and len(alt_result) > 0:
                                        if isinstance(alt_result[0], list) and len(alt_result[0]) > 0:
                                            user_data = alt_result[0][0]
                                            logger.info(f"找到用户: {user_data}")
                                            return User.from_dict(user_data)
                                        elif isinstance(alt_result[0], dict):
                                            user_data = alt_result[0]
                                            logger.info(f"找到用户: {user_data}")
                                            return User.from_dict(user_data)
                                except Exception as alt_err:
                                    logger.error(f"替代提供商查询失败: {alt_err}")
                    
                    # 如果上述方法都失败，尝试直接查询所有用户并手动过滤
                    try:
                        logger.info("尝试查询所有用户并手动过滤")
                        all_users_query = f"SELECT * FROM {self.table} LIMIT 100"
                        all_users = self.db.execute_sql(all_users_query)
                        logger.info(f"查询到 {len(all_users) if all_users else 0} 个用户")
                        
                        if all_users and len(all_users) > 0:
                            # 手动过滤匹配的用户
                            for user_batch in all_users:
                                if isinstance(user_batch, list):
                                    for user_data in user_batch:
                                        if isinstance(user_data, dict):
                                            # 通过邮箱匹配
                                            if user.email and user_data.get('email') == user.email:
                                                logger.info(f"通过手动过滤邮箱找到用户: {user_data}")
                                                return User.from_dict(user_data)
                                            # 通过提供商匹配
                                            if user.provider and user.provider_id and \
                                               user_data.get('provider') == user.provider and \
                                               user_data.get('provider_id') == user.provider_id:
                                                logger.info(f"通过手动过滤提供商找到用户: {user_data}")
                                                return User.from_dict(user_data)
                                elif isinstance(user_batch, dict):
                                    # 通过邮箱匹配
                                    if user.email and user_batch.get('email') == user.email:
                                        logger.info(f"通过手动过滤邮箱找到用户: {user_batch}")
                                        return User.from_dict(user_batch)
                                    # 通过提供商匹配
                                    if user.provider and user.provider_id and \
                                       user_batch.get('provider') == user.provider and \
                                       user_batch.get('provider_id') == user.provider_id:
                                        logger.info(f"通过手动过滤提供商找到用户: {user_batch}")
                                        return User.from_dict(user_batch)
                    except Exception as all_users_err:
                        logger.error(f"查询所有用户失败: {all_users_err}")
                    
                    logger.warning("无法找到已存在的用户，尽管检测到唯一约束冲突")
                    # 创建失败但无法找到已存在用户，返回原始用户对象
            
            # 如果没有找到现有用户，返回原始用户
            return user
        except Exception as e:
            logger.error(f"创建用户时发生异常: {e}")
            # 确保用户有ID
            if not user.id:
                user.id = str(uuid.uuid4())
            return user
        
    def update_user_sync(self, user: User) -> User:
        """
        同步更新用户
        
        Args:
            user: 用户对象
            
        Returns:
            更新后的用户对象
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.update_user(user))
        
    def delete_user_sync(self, user_id: str) -> bool:
        """
        同步删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.delete_user(user_id))
        
    def list_users_sync(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        同步列出用户
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        try:
            # 使用execute_sql方法（它本身就是同步的）
            query = f"SELECT * FROM {self.table} LIMIT {limit}"
            result = self.db.execute_sql(query)
            
            users = []
            if result:
                # 处理可能的嵌套结果
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, list):
                            for user_data in item:
                                if isinstance(user_data, dict):
                                    try:
                                        # 确保用户数据与 User 类兼容
                                        user = User(
                                            id=user_data.get('id'),
                                            email=user_data.get('email'),
                                            name=user_data.get('name') or user_data.get('username'),
                                            provider=user_data.get('provider'),
                                            provider_id=user_data.get('provider_id'),
                                            avatar_url=user_data.get('avatar_url'),
                                            created_at=user_data.get('created_at')
                                        )
                                        # 手动设置 username 和 password_hash 属性（如果存在）
                                        if 'username' in user_data:
                                            setattr(user, 'username', user_data['username'])
                                        if 'password_hash' in user_data:
                                            setattr(user, 'password_hash', user_data['password_hash'])
                                        users.append(user)
                                    except Exception as user_err:
                                        logger.error(f"创建用户对象失败: {user_err}, 数据: {user_data}")
                        elif isinstance(item, dict):
                            try:
                                # 确保用户数据与 User 类兼容
                                user = User(
                                    id=item.get('id'),
                                    email=item.get('email'),
                                    name=item.get('name') or item.get('username'),
                                    provider=item.get('provider'),
                                    provider_id=item.get('provider_id'),
                                    avatar_url=item.get('avatar_url'),
                                    created_at=item.get('created_at')
                                )
                                # 手动设置 username 和 password_hash 属性（如果存在）
                                if 'username' in item:
                                    setattr(user, 'username', item['username'])
                                if 'password_hash' in item:
                                    setattr(user, 'password_hash', item['password_hash'])
                                users.append(user)
                            except Exception as user_err:
                                logger.error(f"创建用户对象失败: {user_err}, 数据: {item}")
            
            return users
        except Exception as e:
            logger.error(f"同步列出用户失败: {e}")
            return []
    
    def get_all_users_sync(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        获取所有用户（同步版本）
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        return self.list_users_sync(limit, offset)

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        异步列出用户
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        try:
            # SurrealDB 不支持 OFFSET 语法，只使用 LIMIT
            query = f"SELECT * FROM {self.table} LIMIT {limit}"
            result = await self.db.execute_sql(query)
            
            users = []
            if result:
                # 处理可能的嵌套结果
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, list):
                            for user_data in item:
                                if isinstance(user_data, dict):
                                    try:
                                        # 确保用户数据与 User 类兼容
                                        user = User(
                                            id=user_data.get('id'),
                                            email=user_data.get('email'),
                                            name=user_data.get('name') or user_data.get('username'),
                                            provider=user_data.get('provider'),
                                            provider_id=user_data.get('provider_id'),
                                            avatar_url=user_data.get('avatar_url'),
                                            created_at=user_data.get('created_at')
                                        )
                                        # 手动设置 username 和 password_hash 属性（如果存在）
                                        if 'username' in user_data:
                                            setattr(user, 'username', user_data['username'])
                                        if 'password_hash' in user_data:
                                            setattr(user, 'password_hash', user_data['password_hash'])
                                        users.append(user)
                                    except Exception as user_err:
                                        logger.error(f"创建用户对象失败: {user_err}, 数据: {user_data}")
                        elif isinstance(item, dict):
                            try:
                                # 确保用户数据与 User 类兼容
                                user = User(
                                    id=item.get('id'),
                                    email=item.get('email'),
                                    name=item.get('name') or item.get('username'),
                                    provider=item.get('provider'),
                                    provider_id=item.get('provider_id'),
                                    avatar_url=item.get('avatar_url'),
                                    created_at=item.get('created_at')
                                )
                                # 手动设置 username 和 password_hash 属性（如果存在）
                                if 'username' in item:
                                    setattr(user, 'username', item['username'])
                                if 'password_hash' in item:
                                    setattr(user, 'password_hash', item['password_hash'])
                                users.append(user)
                            except Exception as user_err:
                                logger.error(f"创建用户对象失败: {user_err}, 数据: {item}")
            
            return users
        except Exception as e:
            logger.error(f"列出用户失败: {e}")
            return []
    
    def get_all_users_sync(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        获取所有用户（同步版本）
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        return self.list_users_sync(limit, offset)
