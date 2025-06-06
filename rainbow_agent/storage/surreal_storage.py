"""
SurrealDB存储实现

使用SurrealDB作为存储后端的实现
"""
import os
import json
import logging
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Import both the WebSocket client and our new HTTP client
from surrealdb import Surreal
from .surreal import SurrealDBHttpClient

# 自定义JSON编码器，处理datetime对象
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

from .base import BaseStorage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SurrealStorage(BaseStorage):
    """SurrealDB存储实现"""
    
    def __init__(self, 
                 url: str = "ws://localhost:8000/rpc",
                 namespace: str = "rainbow",
                 database: str = "test",
                 username: str = "root",
                 password: str = "root",
                 use_http: bool = False):
        """初始化SurrealDB存储
        
        Args:
            url: SurrealDB服务器URL
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
            use_http: 是否使用HTTP客户端而非WebSocket客户端
        """
        self.url = url
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        self.use_http = use_http
        self.db = None  # 不再在初始化时创建连接
        self.http_client = None  # HTTP客户端实例
        self._connected = False
        self._connection_lock = asyncio.Lock()  # 添加连接锁以防止并发连接问题
        logger.info(f"SurrealDB存储初始化: {url}, {namespace}, {database}, {'HTTP' if use_http else 'WebSocket'}")
    
    async def _ensure_connected(self) -> None:
        """确保已连接到SurrealDB
        
        注意：每次调用此方法都会创建全新的连接实例，以确保连接有效
        这种方式虽然效率不高，但可以解决SurrealDB客户端库的连接问题
        
        注意：在新版本的surrealdb 1.0.4中，大多数方法是同步的，但我们保留异步方法签名以保持兼容性
        """
        # 根据配置选择使用HTTP客户端或WebSocket客户端
        try:
            if self.use_http:
                # 使用HTTP客户端
                # HTTP客户端不需要每次重新创建，可以重用
                if self.http_client is None:
                    # 确保URL是HTTP格式
                    http_url = self.url
                    if http_url.startswith("ws://"):
                        http_url = "http://" + http_url[5:]
                    elif http_url.startswith("wss://"):
                        http_url = "https://" + http_url[6:]
                    
                    # 如果URL包含/rpc后缀，去掉它
                    if http_url.endswith("/rpc"):
                        http_url = http_url[:-4]
                    
                    logger.info(f"正在创建HTTP客户端: {http_url}")
                    self.http_client = SurrealDBHttpClient(
                        url=http_url,
                        namespace=self.namespace,
                        database=self.database,
                        username=self.username,
                        password=self.password
                    )
                    logger.info("HTTP客户端创建成功")
                
                # HTTP客户端不需要显式连接
                self._connected = True
                logger.info(f"已成功连接到SurrealDB(HTTP): {self.url}, {self.namespace}, {self.database}")
            else:
                # 使用WebSocket客户端
                # 如果已经有连接，先尝试关闭它
                if self.db is not None:
                    try:
                        self.db.close()
                    except Exception:
                        # 忽略关闭连接时的错误
                        pass
                
                # 创建全新的连接实例 - 使用新的连接语法
                logger.info(f"正在创建SurrealDB连接: {self.url}")
                self.db = Surreal(self.url)
                self._connected = False
                
                try:
                    # 在新版本中，连接是在初始化时自动建立的，不需要显式调用connect()
                    # 签名认证
                    logger.info("正在进行SurrealDB身份验证")
                    self.db.signin({"username": self.username, "password": self.password})
                    logger.info("SurrealDB身份验证成功")
                    
                    # 使用指定的命名空间和数据库
                    logger.info(f"正在使用命名空间和数据库: {self.namespace}, {self.database}")
                    self.db.use(self.namespace, self.database)
                    logger.info(f"成功使用命名空间和数据库: {self.namespace}, {self.database}")
                    
                    self._connected = True
                except Exception as e:
                    logger.error(f"SurrealDB连接或认证失败: {e}")
                    self.db.close()
                    raise
                
                self._connected = True
                logger.info(f"已成功连接到SurrealDB(WebSocket): {self.url}, {self.namespace}, {self.database}")
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"确保连接时出错: {e}\n{error_traceback}")
            self._connected = False
            self.db = None
            self.http_client = None
            raise
    
    async def connect(self) -> None:
        """连接到SurrealDB
        
        注意：此方法不再直接使用，而是通过_ensure_connected方法调用
        保留此方法仅为了兼容性
        """
        # 调用_ensure_connected方法创建新连接
        await self._ensure_connected()
    
    async def disconnect(self) -> None:
        """断开与SurrealDB的连接"""
        try:
            if self.use_http:
                # HTTP客户端的关闭
                if self.http_client is not None:
                    await self.http_client.close_async()
                    self.http_client = None
                    self._connected = False
                    logger.info("已断开与SurrealDB的HTTP连接")
                else:
                    logger.info("没有活动的SurrealDB HTTP连接")
            else:
                # WebSocket客户端的关闭
                if self.db is not None:
                    # 新版本中close方法是同步的
                    self.db.close()
                    self.db = None
                    self._connected = False
                    logger.info("已断开与SurrealDB的WebSocket连接")
                else:
                    logger.info("没有活动的SurrealDB WebSocket连接")
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")
            # 即使出错，也将连接标记为已断开
            self.db = None
            self.http_client = None
            self._connected = False
    
    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建记录
        
        Args:
            table: 表名
            data: 要创建的数据
            
        Returns:
            创建的记录
        """
        # 确保连接有效
        await self._ensure_connected()
        
        # 生成记录ID，如果没有提供的话
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        
        # 添加创建时间
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow().isoformat()
        
        # 添加更新时间
        if "updated_at" not in data:
            data["updated_at"] = datetime.utcnow().isoformat()
        
        try:
            if self.use_http:
                # 使用HTTP客户端创建记录
                logger.info(f"使用HTTP客户端创建记录: {table}")
                result = await self.http_client.create_record_async(table, data)
                if result:
                    logger.info(f"HTTP客户端创建记录成功: {table}:{result.get('id')}")
                    return result
                else:
                    logger.error("HTTP客户端创建记录失败: 未返回有效结果")
                    return {}
            else:
                # 使用WebSocket客户端创建记录 - 新版本中方法是同步的
                created = self.db.create(table, data)
                
                if created and len(created) > 0:
                    # 返回创建的记录
                    result = created[0]
                    logger.info(f"WebSocket客户端创建记录成功: {table}:{result.get('id')}")
                    return dict(result)
                else:
                    logger.error("WebSocket客户端创建记录失败: 未返回有效结果")
                    return {}
        except Exception as e:
            logger.error(f"创建记录失败: {e}")
            
            # 尝试使用SQL插入作为备用方法
            try:
                logger.info("尝试使用SQL插入作为备用方法")
                
                # 将数据转换为JSON字符串
                data_json = json.dumps(data, cls=DateTimeEncoder)
                
                if self.use_http:
                    # 使用HTTP客户端执行SQL
                    sql = f"INSERT INTO {table} {data_json}"
                    result = await self.http_client.execute_sql_async(sql)
                    
                    if result and len(result) > 0:
                        created_record = result[0]
                        logger.info(f"HTTP客户端使用SQL插入成功: {table}:{created_record.get('id')}")
                        return created_record
                    else:
                        logger.error("HTTP客户端使用SQL插入失败: 未返回有效结果")
                        return {}
                else:
                    # 使用WebSocket客户端执行SQL - 新版本中方法是同步的
                    sql = f"INSERT INTO {table} {data_json}"
                    result = self.db.query(sql)
                    
                    if result and len(result) > 0:
                        created_record = result[0]
                        logger.info(f"WebSocket客户端使用SQL插入成功: {table}:{created_record.get('id')}")
                        return dict(created_record)
                    else:
                        logger.error("WebSocket客户端使用SQL插入失败: 未返回有效结果")
                        return {}
            except Exception as backup_error:
                logger.error(f"备用方法也失败: {backup_error}")
                raise
    
    async def read(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """读取记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            记录数据，如果不存在则返回None
        """
        # 确保连接有效
        await self._ensure_connected()
        
        try:
            specific_id = f"{table}:{id}"
            
            if self.use_http:
                # 使用HTTP客户端读取记录
                logger.info(f"使用HTTP客户端读取记录: {specific_id}")
                result = await self.http_client.read_record_async(table, id)
                
                if result:
                    logger.info(f"HTTP客户端读取记录成功: {specific_id}")
                    return result
                else:
                    logger.info(f"HTTP客户端记录不存在: {specific_id}")
                    return None
            else:
                # 使用WebSocket客户端读取记录 - 新版本中方法是同步的
                record = self.db.select(specific_id)
                
                if record and len(record) > 0:
                    # 将ID添加回返回的数据中
                    result = record[0]
                    result["id"] = id
                    logger.info(f"WebSocket客户端读取记录成功: {specific_id}")
                    return result
                else:
                    logger.info(f"WebSocket客户端记录不存在: {specific_id}")
                    return None
        except Exception as e:
            logger.error(f"读取记录失败: {e}")
            raise
    
    async def read_many(self, table: str, query: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """读取多条记录
        
        Args:
            table: 表名
            query: 查询条件
            limit: 限制返回的记录数
            offset: 跳过的记录数
            
        Returns:
            记录列表
        """
        # 确保连接有效
        await self._ensure_connected()
        
        try:
            # 构建查询
            if query:
                # 构建WHERE子句
                where_clauses = []
                for key, value in query.items():
                    if isinstance(value, str):
                        where_clauses.append(f"{key} = '{value}'")
                    else:
                        where_clauses.append(f"{key} = {value}")
                
                where_clause = " AND ".join(where_clauses)
                query_str = f"SELECT * FROM {table} WHERE {where_clause} LIMIT {limit} START {offset}"
            else:
                query_str = f"SELECT * FROM {table} LIMIT {limit} START {offset}"
            
            try:
                # 检查表结构，使用更简单的查询方式
                try:
                    # 检查 sessions 表是否存在 - 新版本中方法是同步的
                    self.db.query("SELECT * FROM sessions LIMIT 1")
                    logger.info("sessions 表已存在")
                except Exception:
                    # 如果表不存在，创建之
                    logger.info("创建 sessions 表")
                    try:
                        self.db.query("DEFINE TABLE sessions")
                        logger.info("sessions 表创建成功")
                    except Exception as e:
                        logger.error(f"sessions 表创建失败: {e}")
                
                try:
                    # 检查 turns 表是否存在 - 新版本中方法是同步的
                    self.db.query("SELECT * FROM turns LIMIT 1")
                    logger.info("turns 表已存在")
                except Exception:
                    # 如果表不存在，创建之
                    logger.info("创建 turns 表")
                    try:
                        self.db.query("DEFINE TABLE turns")
                        logger.info("turns 表创建成功")
                    except Exception as e:
                        logger.error(f"turns 表创建失败: {e}")
            except Exception as table_error:
                logger.warning(f"检查和创建表结构失败: {table_error}")
                # 不抛出异常，继续执行
                return []
            else:
                # 执行查询 - 新版本中方法是同步的
                results = self.db.query(query_str)
                
                # 处理结果 - 新版本中返回结果的结构不同
                if results and len(results) > 0:
                    records = results[0]
                    # 确保每条记录都有ID
                    for record in records:
                        if "id" not in record:
                            # 尝试从记录中提取ID
                            full_id = record.get("id", "")
                            if isinstance(full_id, str) and ":" in full_id:
                                record["id"] = full_id.split(":", 1)[1]
                    
                    logger.info(f"读取多条记录成功: {table}, 共 {len(records)} 条")
                    return records
                else:
                    logger.info(f"没有找到记录: {table}")
                    return []
        except Exception as e:
            logger.error(f"读取多条记录失败: {e}")
            raise
    
    async def update(self, table: str, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新记录
        
        Args:
            table: 表名
            id: 记录ID
            data: 要更新的数据
            
        Returns:
            更新后的记录，如果记录不存在则返回None
        """
        # 确保连接有效
        await self._ensure_connected()
        
        try:
            specific_id = f"{table}:{id}"
            
            # 从更新数据中移除id字段
            update_data = {k: v for k, v in data.items() if k != "id"}
            
            # 更新记录 - 新版本中方法是同步的
            updated = self.db.update(specific_id, update_data)
            
            if updated and len(updated) > 0:
                # 将ID添加回返回的数据中
                result = updated[0]
                result["id"] = id
                logger.info(f"更新记录成功: {specific_id}")
                return result
            else:
                logger.info(f"记录不存在，无法更新: {specific_id}")
                return None
        except Exception as e:
            logger.error(f"更新记录失败: {e}")
            raise
    
    async def delete(self, table: str, id: str) -> bool:
        """删除记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            是否删除成功
        """
        # 确保连接有效
        await self._ensure_connected()
        
        try:
            specific_id = f"{table}:{id}"
            
            # 删除记录 - 新版本中方法是同步的
            deleted = self.db.delete(specific_id)
            
            if deleted:
                logger.info(f"删除记录成功: {specific_id}")
                return True
            else:
                logger.info(f"记录不存在，无法删除: {specific_id}")
                return False
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            raise
    
    async def query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行自定义查询
        
        Args:
            query: 查询语句
            params: 查询参数
            
        Returns:
            查询结果
        """
        # 确保连接有效
        await self._ensure_connected()
        
        try:
            # 执行查询 - 新版本中方法是同步的
            results = self.db.query(query, params)
            
            # 处理结果 - 新版本中返回结果的结构不同
            if results:
                return results
            else:
                return []
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            raise
