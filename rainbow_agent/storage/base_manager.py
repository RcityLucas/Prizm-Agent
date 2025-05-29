"""
基础管理器

为所有管理器类提供基础功能，减少代码重复
"""
import os
import uuid
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .surreal_http_client import SurrealDBHttpClient
from .config import get_surreal_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BaseManager")

class BaseManager:
    """基础管理器类
    
    提供所有管理器共享的基础功能，如数据库连接和通用操作
    """
    
    def __init__(self, 
                 url: Optional[str] = None,
                 namespace: Optional[str] = None,
                 database: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 logger_name: str = "BaseManager"):
        """初始化基础管理器
        
        Args:
            url: SurrealDB服务器URL
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
            logger_name: 日志记录器名称
        """
        # 获取配置
        config = get_surreal_config()
        
        # 使用传入的参数或配置值
        self.url = url or config["url"]
        self.namespace = namespace or config["namespace"]
        self.database = database or config["database"]
        self.username = username or config["username"]
        self.password = password or config["password"]
        
        # 设置日志记录器
        self.logger = logging.getLogger(logger_name)
        
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
        
        self.logger.info(f"{logger_name}初始化完成: {self.http_url}, {self.namespace}, {self.database}")
    
    def _format_value_for_sql(self, value: Any) -> str:
        """格式化值以用于SQL语句
        
        Args:
            value: 要格式化的值
            
        Returns:
            格式化后的值
        """
        if isinstance(value, str):
            if value == "time::now()":
                return "time::now()"
            else:
                escaped_value = value.replace("'", "''")
                return f"'{escaped_value}'"
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif value is None:
            return "NULL"
        elif isinstance(value, (dict, list)):
            json_value = json.dumps(value)
            return json_value
        else:
            return f"'{str(value)}'"
    
    def _build_insert_sql(self, table: str, data: Dict[str, Any]) -> str:
        """构建插入SQL语句
        
        Args:
            table: 表名
            data: 要插入的数据
            
        Returns:
            SQL语句
        """
        columns = ", ".join(data.keys())
        values_list = [self._format_value_for_sql(value) for value in data.values()]
        values = ", ".join(values_list)
        return f"INSERT INTO {table} ({columns}) VALUES ({values});"
    
    def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建记录
        
        Args:
            table: 表名
            data: 记录数据
            
        Returns:
            创建的记录
        """
        try:
            # 构建SQL语句
            sql = self._build_insert_sql(table, data)
            
            # 执行SQL
            self.logger.info(f"创建记录SQL: {sql}")
            self.client.execute_sql(sql)
            
            # 返回创建的记录
            self.logger.info(f"记录创建成功: {data.get('id', '')}")
            return data
        except Exception as e:
            self.logger.error(f"创建记录失败: {e}")
            raise
    
    def get_record(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """获取记录
        
        Args:
            table: 表名
            record_id: 记录ID
            
        Returns:
            记录数据，如果不存在则返回None
        """
        try:
            # 获取记录
            record = self.client.get_record(table, record_id)
            
            if record:
                self.logger.info(f"获取记录 {record_id} 成功")
            else:
                self.logger.info(f"记录 {record_id} 不存在")
            
            return record
        except Exception as e:
            self.logger.error(f"获取记录失败: {e}")
            return None
    
    def update_record(self, table: str, record_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新记录
        
        Args:
            table: 表名
            record_id: 记录ID
            updates: 要更新的字段
            
        Returns:
            更新后的记录，如果记录不存在则返回None
        """
        try:
            # 更新记录
            self.client.update_record(table, record_id, updates)
            
            # 获取更新后的记录
            updated_record = self.client.get_record(table, record_id)
            
            if updated_record:
                self.logger.info(f"更新记录 {record_id} 成功")
            else:
                self.logger.info(f"记录 {record_id} 更新失败")
            
            return updated_record
        except Exception as e:
            self.logger.error(f"更新记录失败: {e}")
            return None
    
    def get_records(self, table: str, condition: str = "", limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取记录列表
        
        Args:
            table: 表名
            condition: 查询条件
            limit: 最大返回数量
            offset: 偏移量
            
        Returns:
            记录列表
        """
        try:
            # 获取记录列表
            records = self.client.get_records(table, condition, limit, offset)
            
            self.logger.info(f"获取记录列表成功，共 {len(records)} 条")
            return records
        except Exception as e:
            self.logger.error(f"获取记录列表失败: {e}")
            return []
    
    def delete_record(self, table: str, record_id: str) -> bool:
        """删除记录
        
        Args:
            table: 表名
            record_id: 记录ID
            
        Returns:
            删除是否成功
        """
        try:
            # 删除记录
            self.client.delete_record(table, record_id)
            
            self.logger.info(f"删除记录 {record_id} 成功")
            return True
        except Exception as e:
            self.logger.error(f"删除记录失败: {e}")
            return False
    
    def execute_sql(self, sql: str) -> Any:
        """执行SQL语句
        
        Args:
            sql: SQL语句
            
        Returns:
            执行结果
        """
        try:
            # 执行SQL
            result = self.client.execute_sql(sql)
            
            self.logger.info(f"执行SQL成功: {sql[:100]}...")
            return result
        except Exception as e:
            self.logger.error(f"执行SQL失败: {e}")
            raise
