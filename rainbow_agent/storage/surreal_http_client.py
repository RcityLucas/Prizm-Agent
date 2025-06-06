"""
SurrealDB HTTP客户端

使用HTTP API与SurrealDB交互的客户端，提供更稳定的数据库操作
这是一个兼容层，实际实现已移至模块化结构中
"""
import logging
from typing import Dict, List, Any, Optional, Union
import warnings

# 从新的模块化结构导入
from .surreal.db_client import SurrealDBHttpClient as ModularSurrealDBClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 显示一次性警告
warnings.warn(
    "SurrealDBHttpClient 已移至模块化结构，请使用 'from rainbow_agent.storage.surreal import SurrealDBHttpClient'",
    DeprecationWarning,
    stacklevel=2
)

class SurrealDBHttpClient(ModularSurrealDBClient):
    """SurrealDB HTTP API客户端 (兼容层)

    此类继承自新的模块化SurrealDBHttpClient实现，
    提供与旧版本相同的接口以保持兼容性。

    新代码应直接使用：
    from rainbow_agent.storage.surreal import SurrealDBHttpClient
    """

    def __init__(self, 
                 url: str = "http://localhost:8000",
                 namespace: str = "rainbow",
                 database: str = "test",
                 username: str = "root",
                 password: str = "root"):
        """初始化SurrealDB HTTP客户端

        Args:
            url: SurrealDB服务器URL (HTTP格式)
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
        """
        # 确保URL是HTTP格式
        if url.startswith("ws://"):
            url = "http://" + url[5:]
        elif url.startswith("wss://"):
            url = "https://" + url[6:]
        
        # 如果URL包含/rpc后缀，去掉它
        if url.endswith("/rpc"):
            url = url[:-4]
        
        # 调用新的模块化实现的初始化方法
        super().__init__(url, namespace, database, username, password)
        
        logger.info(f"SurrealDB HTTP客户端初始化完成: {self.base_url}, {namespace}, {database}")

    def close(self) -> None:
        """关闭客户端连接"""
        logger.info("关闭SurrealDB HTTP客户端连接")
        super().close()

    def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """执行SQL查询
        
        Args:
            sql: SQL查询语句
            
        Returns:
            查询结果
        """
        return super().execute_sql(sql)

    def get_record(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """获取记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            记录数据，如果不存在则返回None
        """
        return super().get_record(table, id)

    async def get_record_async(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """异步获取单条记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            记录数据，如果不存在则返回None
        """
        return await super().get_record_async(table, id)

    def get_records(self, table: str, condition: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取多条记录
        
        Args:
            table: 表名
            condition: 查询条件，例如 "name = 'John'"
            limit: 返回结果数量限制
            offset: 结果偏移量
            
        Returns:
            记录列表
        """
        return super().get_records(table, condition, limit, offset)

    async def get_records_async(self, table: str, condition: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """异步获取多条记录
        
        Args:
            table: 表名
            condition: 查询条件，例如 "name = 'John'"
            limit: 返回结果数量限制
            offset: 结果偏移量
            
        Returns:
            记录列表
        """
        return await super().get_records_async(table, condition, limit, offset)

    def create_record(self, table: str, record_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """使用HTTP JSON API创建记录
        
        Args:
            table: 表名
            record_data: 记录数据（必须包含id字段）
            
        Returns:
            创建的记录
        """
        return super().create_record(table, record_data)

    async def create_record_async(self, table: str, record_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """异步使用HTTP JSON API创建记录
        
        Args:
            table: 表名
            record_data: 记录数据（必须包含id字段）
            
        Returns:
            创建的记录
        """
        return await super().create_record_async(table, record_data)

    def update_record(self, table: str, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新记录
        
        Args:
            table: 表名
            id: 记录ID
            data: 要更新的数据
            
        Returns:
            更新后的记录
        """
        return super().update_record(table, id, data)

    async def update_record_async(self, table: str, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """异步更新记录
        
        Args:
            table: 表名
            id: 记录ID
            data: 要更新的数据
            
        Returns:
            更新后的记录
        """
        return await super().update_record_async(table, id, data)

    def delete_record(self, table: str, id: str) -> bool:
        """删除记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            是否删除成功
        """
        return super().delete_record(table, id)

    async def delete_record_async(self, table: str, id: str) -> bool:
        """异步删除记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            是否删除成功
        """
        return await super().delete_record_async(table, id)

    def count_records(self, table: str, condition: Optional[str] = None) -> int:
        """计算记录数量
        
        Args:
            table: 表名
            condition: 查询条件，例如 "name = 'John'"
            
        Returns:
            记录数量
        """
        return super().count_records(table, condition)

    async def count_records_async(self, table: str, condition: Optional[str] = None) -> int:
        """异步计算记录数量
        
        Args:
            table: 表名
            condition: 查询条件，例如 "name = 'John'"
            
        Returns:
            记录数量
        """
        return await super().count_records_async(table, condition)

    def create_table(self, table: str, schema: Dict[str, str]) -> bool:
        """创建表
        
        Args:
            table: 表名
            schema: 表结构，键为字段名，值为字段类型
            
        Returns:
            是否创建成功
        """
        return super().create_table(table, schema)

    async def create_table_async(self, table: str, schema: Dict[str, str]) -> bool:
        """异步创建表
        
        Args:
            table: 表名
            schema: 表结构，键为字段名，值为字段类型
            
        Returns:
            是否创建成功
        """
        return await super().create_table_async(table, schema)

    def query(self, sql: str) -> List[Dict[str, Any]]:
        """执行查询
        
        Args:
            sql: SQL查询语句
            
        Returns:
            查询结果
        """
        return super().query(sql)

    async def query_async(self, sql: str) -> List[Dict[str, Any]]:
        """异步执行查询
        
        Args:
            sql: SQL查询语句
            
        Returns:
            查询结果
        """
        return await super().query_async(sql)

    async def execute_sql_async_v_new(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """异步执行参数化SQL查询
        
        Args:
            sql: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果
        """
        return await super().execute_sql_async_v_new(sql, params)

    async def close_async(self) -> None:
        """异步关闭客户端连接"""
        logger.info("异步关闭SurrealDB HTTP客户端连接")
        await super().close_async()
        
    def get_records(self, table: str, condition: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取记录列表
        
        Args:
            table: 表名
            condition: 条件表达式
            limit: 限制返回的记录数
            offset: 跳过的记录数
            
        Returns:
            记录列表
        """
        # 构建SQL
        sql = f"SELECT * FROM {table}"
        if condition:
            sql += f" WHERE {condition}"
        sql += f" LIMIT {limit} START {offset};"
        
        try:
            result = self.execute_sql(sql)
            
            # 打印原始响应以进行调试
            logger.info(f"查询原始响应: {result}")
            
            # 检查结果 - 处理多种可能的响应格式
            records = []
            
            # 如果结果为空，直接返回空列表
            if not result:
                logger.info(f"查询结果为空: {table}")
                return []
            
            if isinstance(result, list):
                # 处理情况 1: [{"result": [...], "status": "OK"}]
                if len(result) > 0 and isinstance(result[0], dict) and "result" in result[0]:
                    if result[0]["status"] == "OK":
                        # 如果result字段是列表，直接使用
                        if isinstance(result[0]["result"], list):
                            records = result[0]["result"]
                            # 过滤掉空记录
                            records = [r for r in records if r]
                            logger.info(f"获取记录成功(格式1): {table}, 数量: {len(records)}")
                            return records
                        # 如果result字段是单个对象，包装为列表
                        elif result[0]["result"] and isinstance(result[0]["result"], dict):
                            records = [result[0]["result"]]
                            logger.info(f"获取记录成功(格式1.1): {table}, 数量: 1")
                            return records
                        # 如果result字段是空的，尝试其他方法
                
                # 处理情况 2: 尝试直接使用SQL查询
                try:
                    # 使用更直接的SQL查询方式
                    direct_sql = f"SELECT * FROM {table}"
                    if condition:
                        direct_sql += f" WHERE {condition};"
                    else:
                        direct_sql += ";"  # 确保SQL语句以分号结束
                    
                    logger.info(f"尝试直接SQL查询: {direct_sql}")
                    direct_result = self.query(direct_sql)
                    
                    if direct_result and isinstance(direct_result, list) and len(direct_result) > 0:
                        # 过滤掉空记录
                        records = [r for r in direct_result if r]
                        logger.info(f"直接SQL查询成功: {table}, 数量: {len(records)}")
                        return records
                except Exception as e:
                    logger.warning(f"直接SQL查询失败: {e}")
                
                # 处理情况 3: 检查每个结果项
                for item in result:
                    if isinstance(item, dict):
                        # 如果是包含result字段的字典
                        if "result" in item and item.get("status") == "OK":
                            if isinstance(item["result"], list) and item["result"]:
                                records.extend([r for r in item["result"] if r])
                            elif item["result"] and isinstance(item["result"], dict):
                                records.append(item["result"])
                        # 如果是直接的记录字典（包含id字段）
                        elif "id" in item:
                            records.append(item)
                    # 如果是直接的字符串ID
                    elif isinstance(item, str) and ":" in item:
                        # 尝试获取该ID的记录
                        try:
                            record_parts = item.split(":")
                            if len(record_parts) == 2:
                                record_table, record_id = record_parts
                                if record_table == table:
                                    record = self.get_record(table, record_id)
                                    if record:
                                        records.append(record)
                        except Exception as e:
                            logger.warning(f"获取记录ID失败: {e}")
                
                if records:
                    logger.info(f"获取记录成功(格式3): {table}, 数量: {len(records)}")
                    return records
            
            # 如果以上方法都失败，尝试使用备用方法
            try:
                # 尝试使用RETURN语句
                backup_sql = f"RETURN SELECT * FROM {table}"
                if condition:
                    backup_sql += f" WHERE {condition};"
                else:
                    backup_sql += ";"  # 确保SQL语句以分号结束
                
                logger.info(f"尝试备用SQL查询: {backup_sql}")
                backup_result = self.execute_sql(backup_sql)
                
                if backup_result and isinstance(backup_result, list) and len(backup_result) > 0:
                    if isinstance(backup_result[0], dict) and "result" in backup_result[0]:
                        if isinstance(backup_result[0]["result"], list):
                            records = [r for r in backup_result[0]["result"] if r]
                            logger.info(f"备用SQL查询成功: {table}, 数量: {len(records)}")
                            return records
            except Exception as e:
                logger.warning(f"备用SQL查询失败: {e}")
            
            logger.info(f"获取记录成功: {table}, 条件: {condition}, 数量: {len(records)}")
            return records
        except Exception as e:
            logger.error(f"获取记录失败: {e}")
            return []
            
    async def get_records_async(self, table: str, condition: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """异步获取记录列表
        
        Args:
            table: 表名
            condition: 条件表达式
            limit: 限制返回的记录数
            offset: 跳过的记录数
            
        Returns:
            记录列表
        """
        return await super().get_records_async(table, condition, limit, offset)
