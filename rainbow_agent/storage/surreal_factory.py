"""
SurrealDB存储工厂

提供SurrealDB存储实例的工厂类，用于创建和管理SurrealDB连接
"""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SurrealStorage:
    """SurrealDB存储实现"""
    
    def __init__(self, db_url: str, namespace: str, database: str):
        """
        初始化SurrealDB存储
        
        Args:
            db_url: SurrealDB服务器URL
            namespace: SurrealDB命名空间
            database: SurrealDB数据库名称
        """
        self.db_url = db_url
        self.namespace = namespace
        self.database = database
        self.client = None
        logger.info(f"SurrealStorage初始化: {db_url}/{namespace}/{database}")
    
    async def connect(self) -> None:
        """连接到SurrealDB"""
        try:
            # 尝试导入surrealdb模块
            from surrealdb import Surreal
            import asyncio
            
            logger.info(f"尝试连接到SurrealDB: {self.db_url}")
            
            # 创建客户端 - 使用测试脚本中相同的连接方式（同步API）
            self.client = Surreal(self.db_url)
            
            # 连接并使用指定的命名空间和数据库 - 使用同步API
            try:
                # 使用与测试脚本相同的登录参数
                self.client.signin({"username": "root", "password": "root"})
                self.client.use(self.namespace, self.database)
                
                # 测试连接是否成功
                test_result = self.client.query("INFO FOR DB;")
                logger.info(f"成功连接到SurrealDB: {self.db_url}")
                logger.info(f"SurrealDB测试查询结果: {test_result}")
            except Exception as e:
                # 如果使用username/password失败，尝试使用user/pass
                logger.warning(f"使用username/password登录失败: {e}，尝试使用user/pass")
                self.client.signin({"user": "root", "pass": "root"})
                self.client.use(self.namespace, self.database)
                
                # 测试连接是否成功
                test_result = self.client.query("INFO FOR DB;")
                logger.info(f"成功连接到SurrealDB: {self.db_url}")
                logger.info(f"SurrealDB测试查询结果: {test_result}")
                
            # 连接成功后返回一个已完成的Future，以符合异步接口要求
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            future.set_result(True)
            return future
            
        except ImportError:
            logger.error("未安装surrealdb模块，请使用pip install surrealdb安装")
            raise
        except Exception as e:
            logger.error(f"连接SurrealDB失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    async def create(self, table: str, data: Dict[str, Any]) -> Any:
        """
        创建记录
        
        Args:
            table: 表名
            data: 记录数据
            
        Returns:
            创建的记录
        """
        if not self.client:
            await self.connect()
        
        try:
            # 使用同步API创建记录
            result = self.client.create(table, data)
            return result
        except Exception as e:
            logger.error(f"创建记录失败: {e}")
            raise
    
    async def select(self, table: str, id: str = None) -> Any:
        """
        查询记录
        
        Args:
            table: 表名
            id: 记录ID，如果为None则查询所有记录
            
        Returns:
            查询结果
        """
        if not self.client:
            await self.connect()
        
        try:
            # 使用同步API查询记录
            if id:
                result = self.client.select(f"{table}:{id}")
            else:
                result = self.client.select(table)
            return result
        except Exception as e:
            logger.error(f"查询记录失败: {e}")
            raise
    
    async def update(self, table: str, id: str, data: Dict[str, Any]) -> Any:
        """
        更新记录
        
        Args:
            table: 表名
            id: 记录ID
            data: 更新数据
            
        Returns:
            更新后的记录
        """
        if not self.client:
            await self.connect()
        
        try:
            # 使用同步API更新记录
            result = self.client.update(f"{table}:{id}", data)
            return result
        except Exception as e:
            logger.error(f"更新记录失败: {e}")
            raise
    
    async def delete(self, table: str, id: str) -> Any:
        """
        删除记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            删除结果
        """
        if not self.client:
            await self.connect()
        
        try:
            # 使用同步API删除记录
            result = self.client.delete(f"{table}:{id}")
            return result
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            raise
    
    async def query(self, query_string: str, vars: dict = None) -> Any:
        """执行查询"""
        try:
            if not self.client:
                await self.connect()
                
            # 使用同步API执行查询
            if vars:
                result = self.client.query(query_string, vars)
            else:
                result = self.client.query(query_string)
                
            return result
        except Exception as e:
            logger.error(f"查询失败: {e}")
            raise


class SurrealStorageFactory:
    """
    SurrealDB存储工厂类，用于创建和管理SurrealDB连接
    """
    
    def __init__(self, db_url: str = "ws://localhost:8000/rpc", namespace: str = "rainbow", database: str = "agent"):
        """
        初始化SurrealDB存储工厂
        
        Args:
            db_url: SurrealDB服务器URL，默认使用WebSocket连接
            namespace: SurrealDB命名空间
            database: SurrealDB数据库名称
        """
        # 确保使用WebSocket连接
        if db_url.startswith('http://') or db_url.startswith('https://'):
            db_url = db_url.replace('http://', 'ws://').replace('https://', 'wss://')
            if not db_url.endswith('/rpc'):
                db_url = f"{db_url}/rpc"
        
        logger.info(f"SurrealDB连接URL: {db_url}")
        self.db_url = db_url
        self.namespace = namespace
        self.database = database
        self.storage_instance = None
        logger.info(f"SurrealStorageFactory初始化: {db_url}/{namespace}/{database}")
    
    def get_storage(self) -> SurrealStorage:
        """
        获取存储实例
        
        Returns:
            SurrealStorage实例
        """
        if not self.storage_instance:
            self.storage_instance = SurrealStorage(self.db_url, self.namespace, self.database)
        
        return self.storage_instance
