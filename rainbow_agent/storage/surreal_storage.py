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

from surrealdb import Surreal

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
                 database: str = "agent",
                 username: str = "root",
                 password: str = "root"):
        """初始化SurrealDB存储
        
        Args:
            url: SurrealDB服务器URL
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
        """
        self.url = url
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        self.db = None  # 不再在初始化时创建连接
        self._connected = False
        self._connection_lock = asyncio.Lock()  # 添加连接锁以防止并发连接问题
        logger.info(f"SurrealDB存储初始化: {url}, {namespace}, {database}")
    
    async def _ensure_connected(self) -> None:
        """确保已连接到SurrealDB
        
        注意：每次调用此方法都会创建全新的连接实例，以确保连接有效
        这种方式虽然效率不高，但可以解决SurrealDB客户端库的连接问题
        """
        # 完全重新创建连接实例，而不是重用现有实例
        try:
            # 如果已经有连接，先尝试关闭它
            if self.db is not None:
                try:
                    await self.db.close()
                except Exception:
                    # 忽略关闭连接时的错误
                    pass
            
            # 创建全新的连接实例
            self.db = Surreal()
            self._connected = False
            
            # 连接到SurrealDB
            logger.info(f"正在连接到SurrealDB: {self.url}")
            await self.db.connect(self.url)
            logger.info("SurrealDB连接成功，正在进行身份验证")
            
            # 签名认证
            await self.db.signin({
                "user": self.username,
                "pass": self.password
            })
            logger.info("SurrealDB身份验证成功")
            
            # 使用指定的命名空间和数据库
            logger.info(f"正在使用命名空间和数据库: {self.namespace}, {self.database}")
            await self.db.use(self.namespace, self.database)
            logger.info(f"成功使用命名空间和数据库: {self.namespace}, {self.database}")
            
            self._connected = True
            logger.info(f"已成功连接到SurrealDB: {self.url}, {self.namespace}, {self.database}")
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"确保连接时出错: {e}\n{error_traceback}")
            self._connected = False
            self.db = None
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
        async with self._connection_lock:  # 使用锁防止并发断开连接
            if not self._connected or self.db is None:
                logger.info("未连接到SurrealDB，无需断开连接")
                return
            
            try:
                await self.db.close()
                self._connected = False
                self.db = None  # 清除连接对象
                logger.info("已断开与SurrealDB的连接")
            except Exception as e:
                logger.error(f"断开SurrealDB连接失败: {e}")
                raise
    
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
        
        try:
            # 如果没有提供id，生成一个
            if "id" not in data:
                # 创建记录，让SurrealDB生成ID
                created = await self.db.create(table, data)
                if created and len(created) > 0:
                    logger.info(f"在表 {table} 中创建记录成功: {created[0]['id']}")
                    return created[0]
                else:
                    logger.error(f"在表 {table} 中创建记录失败")
                    return {}
            else:
                # 使用提供的ID创建记录
                record_id = data["id"]
                specific_id = f"{table}:{record_id}"
                
                # 从数据中移除id字段，因为它会成为记录的ID
                # 同时处理datetime对象，确保它们能被SurrealDB正确处理
                record_data = {}
                for k, v in data.items():
                    if k != "id":
                        # 如果是datetime对象，转换为ISO格式字符串
                        if isinstance(v, datetime):
                            record_data[k] = v.isoformat()
                        else:
                            record_data[k] = v
                
                created = await self.db.create(specific_id, record_data)
                if created and len(created) > 0:
                    # 将ID添加回返回的数据中
                    result = created[0]
                    result["id"] = record_id
                    logger.info(f"在表 {table} 中创建记录成功: {record_id}")
                    return result
                else:
                    logger.error(f"在表 {table} 中创建记录失败: {record_id}")
                    return {}
        except Exception as e:
            logger.error(f"创建记录失败: {e}")
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
            result = await self.db.select(specific_id)
            
            if result and len(result) > 0:
                # 将ID添加到返回的数据中
                record = result[0]
                if "id" not in record and hasattr(record, "id"):
                    record["id"] = id
                logger.info(f"读取记录成功: {specific_id}")
                return record
            else:
                logger.info(f"记录不存在: {specific_id}")
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
                    # 检查 sessions 表是否存在
                    await self.db.query("SELECT * FROM sessions LIMIT 1")
                    logger.info("sessions 表已存在")
                except Exception:
                    # 如果表不存在，创建之
                    logger.info("创建 sessions 表")
                    try:
                        await self.db.query("DEFINE TABLE sessions")
                        logger.info("sessions 表创建成功")
                    except Exception as e:
                        logger.error(f"sessions 表创建失败: {e}")
                
                try:
                    # 检查 turns 表是否存在
                    await self.db.query("SELECT * FROM turns LIMIT 1")
                    logger.info("turns 表已存在")
                except Exception:
                    # 如果表不存在，创建之
                    logger.info("创建 turns 表")
                    try:
                        await self.db.query("DEFINE TABLE turns")
                        logger.info("turns 表创建成功")
                    except Exception as e:
                        logger.error(f"turns 表创建失败: {e}")
            except Exception as table_error:
                logger.warning(f"检查和创建表结构失败: {table_error}")
                # 不抛出异常，继续执行
                return []
            else:
                # 执行查询
                results = await self.db.query(query_str)
                
                # 处理结果
                if results and hasattr(results, "result") and results.result:
                    records = results.result[0]
                    # 确保每条记录都有ID
                    for record in records:
                        if "id" not in record and hasattr(record, "id"):
                            # 从记录ID中提取纯ID部分
                            full_id = record.id
                            if ":" in full_id:
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
            
            # 更新记录
            updated = await self.db.update(specific_id, update_data)
            
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
            
            # 删除记录
            deleted = await self.db.delete(specific_id)
            
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
            # 执行查询
            results = await self.db.query(query, params)
            
            # 处理结果
            if results and hasattr(results, "result") and results.result:
                return results.result
            else:
                return []
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            raise
