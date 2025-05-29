"""
用户配置文件管理器

管理用户配置文件，包括用户偏好、历史交互数据和个性化设置
"""
import os
import uuid
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .surreal_http_client import SurrealDBHttpClient
from .config import get_surreal_config
from .models import UserProfileModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UserProfileManager")

class UserProfileManager:
    """用户配置文件管理器
    
    管理用户配置文件，提供用户偏好和个性化设置的存储和检索功能
    """
    
    # 内存缓存
    _profile_cache = {}
    
    def __init__(self, 
                 url: Optional[str] = None,
                 namespace: Optional[str] = None,
                 database: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """初始化用户配置文件管理器
        
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
        
        logger.info(f"用户配置文件管理器初始化完成: {self.http_url}, {self.namespace}, {self.database}")
        
        # 确保表结构存在
        self._ensure_table_structure()
    
    def _ensure_table_structure(self) -> None:
        """确保表结构存在"""
        try:
            # 定义user_profiles表
            sql = """
            DEFINE TABLE user_profiles SCHEMAFULL;
            DEFINE FIELD id ON user_profiles TYPE string;
            DEFINE FIELD username ON user_profiles TYPE string;
            DEFINE FIELD email ON user_profiles TYPE string;
            DEFINE FIELD created_at ON user_profiles TYPE datetime;
            DEFINE FIELD updated_at ON user_profiles TYPE datetime;
            DEFINE FIELD preferences ON user_profiles TYPE object;
            DEFINE FIELD interaction_history ON user_profiles TYPE object;
            DEFINE FIELD frequently_asked_questions ON user_profiles TYPE array;
            DEFINE FIELD topics_of_interest ON user_profiles TYPE array;
            DEFINE FIELD metadata ON user_profiles TYPE object;
            """
            
            self.client.execute_sql(sql)
            logger.info("用户配置文件表结构初始化完成")
        except Exception as e:
            logger.warning(f"用户配置文件表结构初始化失败，可能已存在: {e}")
    
    def create_profile(self, 
                      username: str, 
                      email: Optional[str] = None,
                      preferences: Optional[Dict[str, Any]] = None,
                      topics_of_interest: Optional[List[str]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建新用户配置文件
        
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
            # 创建用户配置文件模型
            profile_model = UserProfileModel(
                username=username,
                email=email,
                preferences=preferences,
                topics_of_interest=topics_of_interest,
                metadata=metadata
            )
            
            # 转换为字典
            profile_data = profile_model.to_dict()
            
            # 使用SQL直接创建完整记录
            logger.info(f"使用SQL直接创建用户配置文件: {profile_model.id}")
            
            # 构建SQL语句
            columns = ", ".join(profile_data.keys())
            values_list = []
            
            for key, value in profile_data.items():
                if isinstance(value, str):
                    if value == "time::now()":
                        values_list.append("time::now()")
                    else:
                        escaped_value = value.replace("'", "''")
                        values_list.append(f"'{escaped_value}'")
                elif isinstance(value, (int, float, bool)):
                    values_list.append(str(value))
                elif value is None:
                    values_list.append("NULL")
                elif isinstance(value, (dict, list)):
                    import json
                    json_value = json.dumps(value)
                    values_list.append(json_value)
                else:
                    values_list.append(f"'{str(value)}'")
            
            values = ", ".join(values_list)
            sql = f"INSERT INTO user_profiles ({columns}) VALUES ({values});"
            
            # 执行SQL
            logger.info(f"创建用户配置文件SQL: {sql}")
            self.client.execute_sql(sql)
            
            # 将新创建的用户配置文件添加到内存缓存
            UserProfileManager._profile_cache[profile_model.id] = profile_model
            
            # 返回创建的用户配置文件
            logger.info(f"用户配置文件创建成功: {profile_model.id}")
            return profile_model.to_dict()
        except Exception as e:
            logger.error(f"创建用户配置文件失败: {e}")
            raise
    
    def get_profile(self, user_id: str) -> Optional[Union[Dict[str, Any], UserProfileModel]]:
        """获取用户配置文件
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户配置文件，如果不存在则返回None
        """
        try:
            # 先检查内存缓存
            if user_id in UserProfileManager._profile_cache:
                logger.info(f"从内存缓存中获取用户配置文件: {user_id}")
                cached_profile = UserProfileManager._profile_cache[user_id]
                
                # 如果缓存中的是字典，转换为模型
                if isinstance(cached_profile, dict):
                    return UserProfileModel.from_dict(cached_profile)
                return cached_profile
            
            # 如果内存缓存中没有，从数据库获取
            logger.info(f"从数据库获取用户配置文件: {user_id}")
            profile_data = self.client.get_record("user_profiles", user_id)
            
            if profile_data:
                # 创建用户配置文件模型
                profile_model = UserProfileModel.from_dict(profile_data)
                
                # 将用户配置文件添加到内存缓存
                UserProfileManager._profile_cache[user_id] = profile_model
                logger.info(f"用户配置文件获取成功并添加到内存缓存: {user_id}")
                return profile_model
            else:
                logger.info(f"用户配置文件 {user_id} 不存在")
                return None
        except Exception as e:
            logger.error(f"获取用户配置文件失败: {e}")
            return None
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Union[Dict[str, Any], UserProfileModel]]:
        """更新用户配置文件
        
        Args:
            user_id: 用户ID
            updates: 要更新的字段
            
        Returns:
            更新后的用户配置文件，如果用户配置文件不存在则返回None
        """
        try:
            # 首先检查用户配置文件是否存在
            existing_profile = self.get_profile(user_id)
            if not existing_profile:
                logger.info(f"用户配置文件 {user_id} 不存在，无法更新")
                return None
            
            # 添加更新时间
            if "updated_at" not in updates:
                updates["updated_at"] = "time::now()"
            
            # 更新用户配置文件
            self.client.update_record("user_profiles", user_id, updates)
            
            # 获取更新后的用户配置文件
            updated_profile_data = self.client.get_record("user_profiles", user_id)
            
            # 如果无法从数据库获取更新后的用户配置文件，使用内存中的用户配置文件并应用更新
            if not updated_profile_data and user_id in UserProfileManager._profile_cache:
                cached_profile = UserProfileManager._profile_cache[user_id]
                
                # 如果缓存中的是模型，转换为字典
                if isinstance(cached_profile, UserProfileModel):
                    profile_dict = cached_profile.to_dict()
                else:
                    profile_dict = cached_profile.copy() if isinstance(cached_profile, dict) else {}
                
                # 应用更新
                for key, value in updates.items():
                    if key in ["updated_at"] and value == "time::now()":
                        profile_dict[key] = datetime.now().isoformat()
                    else:
                        profile_dict[key] = value
                
                updated_profile_data = profile_dict
                logger.info(f"使用内存缓存中的用户配置文件并应用更新: {user_id}")
            
            if updated_profile_data:
                # 创建用户配置文件模型
                updated_profile = UserProfileModel.from_dict(updated_profile_data)
                
                # 更新内存缓存
                UserProfileManager._profile_cache[user_id] = updated_profile
                logger.info(f"更新用户配置文件 {user_id} 成功并更新内存缓存")
                return updated_profile
            else:
                logger.info(f"用户配置文件 {user_id} 更新失败，无法获取更新后的用户配置文件")
                return None
        except Exception as e:
            logger.error(f"更新用户配置文件失败: {e}")
            return None
    
    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """更新用户偏好
        
        Args:
            user_id: 用户ID
            preferences: 用户偏好
            
        Returns:
            更新是否成功
        """
        try:
            # 获取现有用户配置文件
            profile = self.get_profile(user_id)
            if not profile:
                logger.info(f"用户配置文件 {user_id} 不存在，无法更新偏好")
                return False
            
            # 获取现有偏好
            existing_preferences = profile.preferences if hasattr(profile, 'preferences') else profile.get('preferences', {})
            
            # 合并偏好
            merged_preferences = {**existing_preferences, **preferences}
            
            # 更新用户配置文件
            updates = {"preferences": merged_preferences}
            updated_profile = self.update_profile(user_id, updates)
            
            if updated_profile:
                logger.info(f"更新用户 {user_id} 的偏好成功")
                return True
            else:
                logger.info(f"更新用户 {user_id} 的偏好失败")
                return False
        except Exception as e:
            logger.error(f"更新用户偏好失败: {e}")
            return False
    
    def add_frequently_asked_question(self, user_id: str, question: str, answer: str) -> bool:
        """添加常见问题
        
        Args:
            user_id: 用户ID
            question: 问题
            answer: 答案
            
        Returns:
            添加是否成功
        """
        try:
            # 获取现有用户配置文件
            profile = self.get_profile(user_id)
            if not profile:
                logger.info(f"用户配置文件 {user_id} 不存在，无法添加常见问题")
                return False
            
            # 获取现有常见问题
            existing_faqs = profile.frequently_asked_questions if hasattr(profile, 'frequently_asked_questions') else profile.get('frequently_asked_questions', [])
            
            # 创建新的常见问题
            new_faq = {
                "question": question,
                "answer": answer,
                "created_at": datetime.now().isoformat()
            }
            
            # 添加到常见问题列表
            updated_faqs = existing_faqs + [new_faq]
            
            # 更新用户配置文件
            updates = {"frequently_asked_questions": updated_faqs}
            updated_profile = self.update_profile(user_id, updates)
            
            if updated_profile:
                logger.info(f"为用户 {user_id} 添加常见问题成功")
                return True
            else:
                logger.info(f"为用户 {user_id} 添加常见问题失败")
                return False
        except Exception as e:
            logger.error(f"添加常见问题失败: {e}")
            return False
    
    def add_topic_of_interest(self, user_id: str, topic: str) -> bool:
        """添加兴趣主题
        
        Args:
            user_id: 用户ID
            topic: 主题
            
        Returns:
            添加是否成功
        """
        try:
            # 获取现有用户配置文件
            profile = self.get_profile(user_id)
            if not profile:
                logger.info(f"用户配置文件 {user_id} 不存在，无法添加兴趣主题")
                return False
            
            # 获取现有兴趣主题
            existing_topics = profile.topics_of_interest if hasattr(profile, 'topics_of_interest') else profile.get('topics_of_interest', [])
            
            # 如果主题已存在，不重复添加
            if topic in existing_topics:
                logger.info(f"用户 {user_id} 已有兴趣主题 {topic}，不重复添加")
                return True
            
            # 添加到兴趣主题列表
            updated_topics = existing_topics + [topic]
            
            # 更新用户配置文件
            updates = {"topics_of_interest": updated_topics}
            updated_profile = self.update_profile(user_id, updates)
            
            if updated_profile:
                logger.info(f"为用户 {user_id} 添加兴趣主题 {topic} 成功")
                return True
            else:
                logger.info(f"为用户 {user_id} 添加兴趣主题 {topic} 失败")
                return False
        except Exception as e:
            logger.error(f"添加兴趣主题失败: {e}")
            return False
    
    def record_interaction(self, user_id: str, interaction_type: str, details: Dict[str, Any]) -> bool:
        """记录用户交互
        
        Args:
            user_id: 用户ID
            interaction_type: 交互类型
            details: 交互详情
            
        Returns:
            记录是否成功
        """
        try:
            # 获取现有用户配置文件
            profile = self.get_profile(user_id)
            if not profile:
                logger.info(f"用户配置文件 {user_id} 不存在，无法记录交互")
                return False
            
            # 获取现有交互历史
            existing_history = profile.interaction_history if hasattr(profile, 'interaction_history') else profile.get('interaction_history', {})
            
            # 获取特定类型的交互历史
            type_history = existing_history.get(interaction_type, [])
            
            # 创建新的交互记录
            new_interaction = {
                **details,
                "timestamp": datetime.now().isoformat()
            }
            
            # 添加到交互历史
            type_history.append(new_interaction)
            existing_history[interaction_type] = type_history
            
            # 更新用户配置文件
            updates = {"interaction_history": existing_history}
            updated_profile = self.update_profile(user_id, updates)
            
            if updated_profile:
                logger.info(f"为用户 {user_id} 记录 {interaction_type} 交互成功")
                return True
            else:
                logger.info(f"为用户 {user_id} 记录 {interaction_type} 交互失败")
                return False
        except Exception as e:
            logger.error(f"记录交互失败: {e}")
            return False
