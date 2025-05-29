"""
增强版轮次管理器

使用HTTP API与SurrealDB交互，提供更稳定的轮次管理功能。
集成了对话存储与上下文管理系统，支持高级轮次管理功能。
"""
import os
import uuid
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .surreal_http_client import SurrealDBHttpClient
from .config import get_surreal_config
from .models import TurnModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedTurnManager:
    """增强版轮次管理器"""
    
    # 创建内存缓存，用于存储创建的轮次
    _turn_cache = {}
    
    def __init__(self, 
                 url: Optional[str] = None,
                 namespace: Optional[str] = None,
                 database: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """初始化增强版轮次管理器
        
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
        
        logger.info(f"增强版轮次管理器初始化完成: {self.http_url}, {self.namespace}, {self.database}")
        
        # 确保表结构存在
        self._ensure_table_structure()
    
    def _ensure_table_structure(self) -> None:
        """确保表结构存在"""
        try:
            # 定义turns表
            sql = """
            DEFINE TABLE turns SCHEMAFULL;
            DEFINE FIELD id ON turns TYPE string;
            DEFINE FIELD session_id ON turns TYPE string;
            DEFINE FIELD role ON turns TYPE string;
            DEFINE FIELD content ON turns TYPE string;
            DEFINE FIELD created_at ON turns TYPE datetime;
            DEFINE FIELD embedding ON turns TYPE array;
            DEFINE FIELD metadata ON turns TYPE object;
            """
            
            self.client.execute_sql(sql)
            logger.info("轮次表结构初始化完成")
        except Exception as e:
            logger.warning(f"轮次表结构初始化失败，可能已存在: {e}")
    
    def create_turn(self, session_id: str, role: str, content: str, 
              embedding: Optional[List[float]] = None,
              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建新轮次
        
        Args:
            session_id: 会话ID
            role: 角色 (user/assistant)
            content: 内容
            embedding: 消息内容的向量表示
            metadata: 元数据
            
        Returns:
            创建的轮次
        """
        try:
            # 创建轮次模型
            turn_model = TurnModel(
                session_id=session_id,
                role=role,
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            
            # 转换为字典
            turn_data = turn_model.to_dict()
            
            # 使用SQL直接创建完整记录
            logger.info(f"使用SQL直接创建轮次: {turn_model.id}")
            
            # 构建SQL语句
            columns = ", ".join(turn_data.keys())
            values_list = []
            
            for key, value in turn_data.items():
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
            sql = f"INSERT INTO turns ({columns}) VALUES ({values});"
            
            # 执行SQL
            logger.info(f"创建轮次SQL: {sql}")
            self.client.execute_sql(sql)
            
            # 获取创建的轮次
            turn = self.client.get_record("turns", turn_id)
            
            # 如果无法获取轮次，使用原始数据
            if not turn:
                # 将时间字符串替换为实际时间
                turn_data["created_at"] = datetime.now().isoformat()
                turn = turn_data
                logger.warning(f"无法获取创建的轮次，使用原始数据: {turn_id}")
            
            # 将轮次添加到内存缓存中
            if session_id not in EnhancedTurnManager._turn_cache:
                EnhancedTurnManager._turn_cache[session_id] = {}
            EnhancedTurnManager._turn_cache[session_id][turn_id] = turn
            
            logger.info(f"创建新轮次成功: {turn_id}, 会话: {session_id}")
            return turn
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"创建轮次失败: {e}\n{error_traceback}")
            
            # 即使失败，也创建一个基本的轮次对象并添加到缓存中
            turn_id = str(uuid.uuid4()).replace('-', '')
            turn = {
                "id": turn_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            if session_id not in EnhancedTurnManager._turn_cache:
                EnhancedTurnManager._turn_cache[session_id] = {}
            EnhancedTurnManager._turn_cache[session_id][turn_id] = turn
            
            logger.warning(f"创建轮次失败，但已添加到内存缓存: {turn_id}")
            return turn
    
    def get_turns_by_session(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Union[Dict[str, Any], TurnModel]]:
        """根据会话ID获取轮次列表
        
        Args:
            session_id: 会话ID
            limit: 最大返回数量
            offset: 偏移量
            
        Returns:
            轮次列表
        """
        try:
            # 构建查询条件
            condition = f"session_id = '{session_id}'"
            
            # 执行查询
            turns_data = self.client.get_records("turns", condition, limit, offset)
            
            # 转换为模型并添加到内存缓存
            turn_models = []
            for turn_data in turns_data:
                turn_model = TurnModel.from_dict(turn_data)
                turn_id = turn_model.id
                if turn_id:
                    EnhancedTurnManager._turn_cache[turn_id] = turn_model
                turn_models.append(turn_model)
            
            logger.info(f"获取会话 {session_id} 的轮次列表成功，共 {len(turn_models)} 条")
            return turn_models
        except Exception as e:
            logger.error(f"获取会话 {session_id} 的轮次列表失败: {e}")
            return []
    
    def get_turn(self, turn_id: str) -> Optional[Union[Dict[str, Any], TurnModel]]:
        """获取特定轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            轮次数据，如果不存在则返回None
        """
        try:
            # 先检查内存缓存
            if turn_id in EnhancedTurnManager._turn_cache:
                logger.info(f"从内存缓存中获取轮次: {turn_id}")
                cached_turn = EnhancedTurnManager._turn_cache[turn_id]
                
                # 如果缓存中的是字典，转换为模型
                if isinstance(cached_turn, dict):
                    return TurnModel.from_dict(cached_turn)
                return cached_turn
            
            # 如果内存缓存中没有，从数据库获取
            logger.info(f"从数据库获取轮次: {turn_id}")
            turn_data = self.client.get_record("turns", turn_id)
            
            if turn_data:
                # 创建轮次模型
                turn_model = TurnModel.from_dict(turn_data)
                
                # 将轮次添加到内存缓存
                EnhancedTurnManager._turn_cache[turn_id] = turn_model
                logger.info(f"轮次获取成功并添加到内存缓存: {turn_id}")
                return turn_model
            else:
                logger.info(f"轮次 {turn_id} 不存在")
                return None
        except Exception as e:
            logger.error(f"获取轮次失败: {e}")
            return None
    
    async def update_turn(self, turn_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新轮次
        
        Args:
            turn_id: 轮次ID
            updates: 要更新的字段
            
        Returns:
            更新后的轮次，如果轮次不存在则返回None
        """
        try:
            # 更新轮次
            result = self.client.update_record("turns", turn_id, updates)
            
            # 获取更新后的轮次
            updated_turn = self.client.get_record("turns", turn_id)
            
            if updated_turn:
                logger.info(f"更新轮次 {turn_id} 成功")
                return updated_turn
            else:
                logger.info(f"轮次 {turn_id} 不存在，无法更新")
                return None
        except Exception as e:
            logger.error(f"更新轮次失败: {e}")
            return None
    
    async def delete_turn(self, turn_id: str) -> bool:
        """删除轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            是否删除成功
        """
        try:
            result = self.client.delete_record("turns", turn_id)
            if result:
                logger.info(f"删除轮次 {turn_id} 成功")
            else:
                logger.info(f"轮次 {turn_id} 不存在，无法删除")
            return result
        except Exception as e:
            logger.error(f"删除轮次失败: {e}")
            return False
    
    async def delete_session_turns(self, session_id: str) -> int:
        """删除会话的所有轮次
        
        Args:
            session_id: 会话ID
            
        Returns:
            删除的轮次数量
        """
        try:
            # 删除特定会话的所有轮次
            condition = f"session_id = '{session_id}'"
            deleted_count = self.client.delete_records("turns", condition)
            
            logger.info(f"删除会话 {session_id} 的所有轮次成功，共 {deleted_count} 个")
            return deleted_count
        except Exception as e:
            logger.error(f"删除会话轮次失败: {e}")
            return 0
