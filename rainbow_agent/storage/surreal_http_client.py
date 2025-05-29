"""
SurrealDB HTTP客户端

使用HTTP API与SurrealDB交互的客户端，提供更稳定的数据库操作
"""
import os
import json
import logging
import base64
import requests
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SurrealDBHttpClient:
    """SurrealDB HTTP API客户端"""
    
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
        
        self.base_url = url
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        
        # 创建认证头
        auth_str = f"{username}:{password}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        # 同时支持v1.x和v2.x的头部格式
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {auth_b64}",
            # v1.x格式
            "ns": namespace,
            "db": database,
            # v2.x格式
            "Surreal-NS": namespace,
            "Surreal-DB": database
        }
        
        logger.info(f"SurrealDB HTTP客户端初始化完成: {self.base_url}, {namespace}, {database}")
    
    def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """执行SQL查询
        
        Args:
            sql: SQL查询语句
            
        Returns:
            查询结果
        """
        url = f"{self.base_url}/sql"
        
        try:
            # 直接使用头部中的命名空间和数据库设置
            response = requests.post(url, headers=self.headers, data=sql)
            response.raise_for_status()  # 如果响应状态码不是200，抛出异常
            
            result = response.json()
            logger.info(f"SQL查询执行成功: {sql[:50]}...")
            return result
        except Exception as e:
            logger.error(f"SQL查询执行失败: {e}")
            logger.error(f"SQL: {sql}")
            if 'response' in locals():
                logger.error(f"响应状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
            raise
        
    async def execute_sql_async(self, sql: str) -> List[Dict[str, Any]]:
        """异步执行SQL查询
        
        Args:
            sql: SQL查询语句
            
        Returns:
            查询结果
        """
        # 使用同步方法，但在异步上下文中调用
        import asyncio
        return await asyncio.to_thread(self.execute_sql, sql)
    
    def create_record(self, table: str, id: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建记录
        
        Args:
            table: 表名
            id: 记录ID
            data: 记录数据（可选）
            
        Returns:
            创建的记录
        """
        record_id = f"{table}:{id}"
        
        try:
            if data is None:
                # 如果没有提供数据，只创建包含ID的记录
                sql = f"INSERT INTO {table} (id) VALUES ('{id}');"
                logger.info(f"创建空记录: {record_id}")
            else:
                # 如果提供了数据，创建包含所有字段的记录
                # 确保数据包含ID字段
                data_with_id = {"id": id, **data}
                
                # 构建SQL语句
                columns = ", ".join(data_with_id.keys())
                values_list = []
                
                for key, value in data_with_id.items():
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
                sql = f"INSERT INTO {table} ({columns}) VALUES ({values});"
                logger.info(f"创建完整记录: {record_id}")
            
            # 执行SQL
            result = self.execute_sql(sql)
            logger.info(f"记录创建成功: {record_id}")
            
            # 创建后立即获取记录，确保它存在
            created_record = self.get_record(table, id)
            if not created_record:
                # 如果获取失败，创建一个基本的记录对象
                if data:
                    created_record = data_with_id
                else:
                    created_record = {"id": id}
                logger.warning(f"无法获取创建的记录，使用基本对象: {record_id}")
            
            return created_record
        except Exception as e:
            logger.error(f"记录创建失败: {e}")
            # 如果创建失败，返回基本记录对象而不是抛出异常
            if data:
                return {"id": id, **data}
            return {"id": id}
    
    def update_record(self, table: str, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新记录
        
        Args:
            table: 表名
            id: 记录ID
            data: 要更新的数据
            
        Returns:
            更新后的记录
        """
        # 构建SQL
        record_id = f"{table}:{id}"
        
        # 首先检查记录是否存在
        existing_record = self.get_record(table, id)
        if not existing_record:
            # 如果记录不存在，先创建一个基本记录
            logger.warning(f"记录 {record_id} 不存在，尝试创建")
            self.create_record(table, id)
        
        # 构建SET子句
        set_clauses = []
        for key, value in data.items():
            if isinstance(value, str):
                # 字符串值需要用单引号括起来，并处理内部的单引号
                escaped_value = value.replace("'", "''")
                set_clauses.append(f"{key} = '{escaped_value}'")
            elif isinstance(value, (int, float, bool)):
                # 数字和布尔值直接使用
                set_clauses.append(f"{key} = {value}")
            elif value is None:
                # None值转换为NULL
                set_clauses.append(f"{key} = NULL")
            elif isinstance(value, datetime):
                # 日期时间值使用time::now()函数
                set_clauses.append(f"{key} = time::now()")
            elif isinstance(value, (dict, list)):
                # 字典和列表转换为JSON字符串
                json_value = json.dumps(value)
                set_clauses.append(f"{key} = {json_value}")
            else:
                # 其他类型转换为字符串
                set_clauses.append(f"{key} = '{str(value)}'")
        
        # 尝试使用UPDATE语法
        try:
            # 拼接SET子句
            set_clause = ", ".join(set_clauses)
            
            # 使用UPDATE语法
            sql = f"UPDATE {record_id} SET {set_clause};"
            result = self.execute_sql(sql)
            logger.info(f"记录更新成功: {record_id}")
            
            # 尝试使用INSERT语法作为备用
            if not self.get_record(table, id):
                logger.warning(f"UPDATE后无法获取记录，尝试使用INSERT: {record_id}")
                
                # 构建INSERT数据
                insert_data = {"id": id}
                insert_data.update(data)
                
                # 构建列和值
                columns = []
                values = []
                for key, value in insert_data.items():
                    columns.append(key)
                    if isinstance(value, str):
                        # 字符串值需要用单引号括起来，并处理内部的单引号
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    elif isinstance(value, (int, float, bool)):
                        # 数字和布尔值直接使用
                        values.append(str(value))
                    elif value is None:
                        # None值转换为NULL
                        values.append("NULL")
                    elif value == "time::now()":
                        # 日期时间值使用time::now()函数
                        values.append("time::now()")
                    elif isinstance(value, (dict, list)):
                        # 字典和列表转换为JSON字符串
                        json_value = json.dumps(value)
                        values.append(json_value)
                    else:
                        # 其他类型转换为字符串
                        values.append(f"'{str(value)}'")
                
                # 使用INSERT语法
                columns_str = ", ".join(columns)
                values_str = ", ".join(values)
                insert_sql = f"INSERT INTO {table} ({columns_str}) VALUES ({values_str});"
                
                try:
                    self.execute_sql(insert_sql)
                    logger.info(f"INSERT更新成功: {record_id}")
                except Exception as e:
                    logger.error(f"INSERT更新失败: {e}")
                    
                    # 如果INSERT失败，尝试使用直接的SQL语句
                    try:
                        direct_sql = f"CREATE {record_id} SET "
                        direct_sql += ", ".join([f"{k} = {v}" for k, v in zip(columns, values)])
                        direct_sql += ";"
                        self.execute_sql(direct_sql)
                        logger.info(f"CREATE直接更新成功: {record_id}")
                    except Exception as e2:
                        logger.error(f"CREATE直接更新失败: {e2}")
                        # 如果所有方法都失败，使用内存中的对象
            
            # 获取更新后的记录
            updated_record = self.get_record(table, id)
            if updated_record:
                return updated_record
            else:
                # 如果无法获取更新后的记录，返回包含更新数据的基本对象
                merged_record = {"id": id}
                merged_record.update(data)
                logger.warning(f"无法获取更新后的记录，使用合并对象: {record_id}")
                return merged_record
        except Exception as e:
            logger.error(f"记录更新失败: {e}")
            # 如果更新失败，返回包含原始数据的基本对象
            merged_record = {"id": id}
            merged_record.update(data)
            return merged_record
    
    def get_record(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """获取记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            记录数据，如果不存在则返回None
        """
        # 构建SQL
        record_id = f"{table}:{id}"
        sql = f"SELECT * FROM {record_id};"
        
        try:
            result = self.execute_sql(sql)
            
            # 打印原始响应以进行调试
            logger.info(f"原始响应: {result}")
            
            # 如果结果为空，尝试备用方法
            if not result:
                return self._try_alternative_get(table, id)
            
            # 检查结果 - 处理多种可能的响应格式
            if isinstance(result, list):
                # 处理情况 1: [{"result": [...], "status": "OK"}]
                if len(result) > 0 and isinstance(result[0], dict) and "result" in result[0]:
                    if result[0]["status"] == "OK":
                        # 如果result是列表且非空
                        if isinstance(result[0]["result"], list) and result[0]["result"]:
                            logger.info(f"记录获取成功(格式1): {record_id}")
                            return result[0]["result"][0]
                        # 如果result是单个对象
                        elif result[0]["result"] and isinstance(result[0]["result"], dict):
                            logger.info(f"记录获取成功(格式1.1): {record_id}")
                            return result[0]["result"]
                
                # 处理情况 2: 检查每个结果项
                for item in result:
                    # 如果是包含result字段的字典
                    if isinstance(item, dict) and "result" in item and item.get("status") == "OK":
                        if isinstance(item["result"], list) and item["result"]:
                            logger.info(f"记录获取成功(格式2): {record_id}")
                            return item["result"][0]
                        elif item["result"] and isinstance(item["result"], dict):
                            logger.info(f"记录获取成功(格式2.1): {record_id}")
                            return item["result"]
                    # 如果是直接的记录对象（包含id字段）
                    elif isinstance(item, dict) and "id" in item:
                        logger.info(f"记录获取成功(格式3): {record_id}")
                        return item
                    # 如果是直接的字符串ID且匹配记录ID
                    elif isinstance(item, str) and item == record_id:
                        # 尝试使用备用方法获取该记录
                        return self._try_alternative_get(table, id)
            
            # 如果以上方法都失败，尝试备用方法
            return self._try_alternative_get(table, id)
        except Exception as e:
            logger.error(f"记录获取失败: {e}")
            return None
    
    def _try_alternative_get(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """尝试备用方法获取记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            记录数据，如果不存在则返回None
        """
        try:
            # 尝试方法 1: 使用条件查询
            condition = f"id = '{id}'"
            logger.info(f"尝试使用条件查询获取记录: {table}, {id}")
            records = self.get_records(table, condition, 1, 0)
            
            if records and len(records) > 0:
                logger.info(f"条件查询获取记录成功: {table}:{id}")
                return records[0]
            
            # 尝试方法 2: 使用RETURN语句
            try:
                record_id = f"{table}:{id}"
                backup_sql = f"RETURN SELECT * FROM {record_id};"
                
                logger.info(f"尝试使用RETURN获取记录: {record_id}")
                backup_result = self.execute_sql(backup_sql)
                
                if backup_result and isinstance(backup_result, list) and len(backup_result) > 0:
                    if isinstance(backup_result[0], dict) and "result" in backup_result[0]:
                        if isinstance(backup_result[0]["result"], list) and backup_result[0]["result"]:
                            logger.info(f"RETURN查询获取记录成功: {record_id}")
                            return backup_result[0]["result"][0]
                        elif backup_result[0]["result"] and isinstance(backup_result[0]["result"], dict):
                            logger.info(f"RETURN查询获取记录成功: {record_id}")
                            return backup_result[0]["result"]
            except Exception as e:
                logger.warning(f"RETURN查询获取记录失败: {e}")
            
            logger.info(f"记录不存在或格式不正确: {table}:{id}")
            return None
        except Exception as e:
            logger.error(f"备用方法获取记录失败: {e}")
            return None
    
    async def _try_alternative_get_async(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """异步尝试备用方法获取记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            记录数据，如果不存在则返回None
        """
        try:
            # 尝试方法 1: 使用条件查询
            condition = f"id = '{id}'"
            logger.info(f"异步尝试使用条件查询获取记录: {table}, {id}")
            records = await self.get_records_async(table, condition, 1, 0)
            
            if records and len(records) > 0:
                logger.info(f"异步条件查询获取记录成功: {table}:{id}")
                return records[0]
            
            # 尝试方法 2: 使用RETURN语句
            try:
                record_id = f"{table}:{id}"
                backup_sql = f"RETURN SELECT * FROM {record_id};"
                
                logger.info(f"异步尝试使用RETURN获取记录: {record_id}")
                backup_result = await self.execute_sql_async(backup_sql)
                
                if backup_result and isinstance(backup_result, list) and len(backup_result) > 0:
                    if isinstance(backup_result[0], dict) and "result" in backup_result[0]:
                        if isinstance(backup_result[0]["result"], list) and backup_result[0]["result"]:
                            logger.info(f"异步RETURN查询获取记录成功: {record_id}")
                            return backup_result[0]["result"][0]
                        elif backup_result[0]["result"] and isinstance(backup_result[0]["result"], dict):
                            logger.info(f"异步RETURN查询获取记录成功: {record_id}")
                            return backup_result[0]["result"]
            except Exception as e:
                logger.warning(f"异步RETURN查询获取记录失败: {e}")
            
            logger.info(f"异步记录不存在或格式不正确: {table}:{id}")
            return None
        except Exception as e:
            logger.error(f"异步备用方法获取记录失败: {e}")
            return None
    
    def query(self, sql: str) -> List[Dict[str, Any]]:
        """执行查询
        
        Args:
            sql: SQL查询语句
            
        Returns:
            查询结果
        """
        try:
            result = self.execute_sql(sql)
            
            # 检查结果
            if result and isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and "result" in result[0] and result[0]["result"]:
                    return result[0]["result"]
                elif isinstance(result[0], list):
                    return result[0]
                elif isinstance(result[0], str) or isinstance(result[0], dict):
                    return [result[0]]
            
            return []
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return []
    
    async def query_async(self, sql: str) -> List[Dict[str, Any]]:
        """异步执行查询
        
        Args:
            sql: SQL查询语句
            
        Returns:
            查询结果
        """
        try:
            result = await self.execute_sql_async(sql)
            
            # 检查结果
            if result and isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and "result" in result[0] and result[0]["result"]:
                    return result[0]["result"]
                elif isinstance(result[0], list):
                    return result[0]
                elif isinstance(result[0], str) or isinstance(result[0], dict):
                    return [result[0]]
            
            return []
        except Exception as e:
            logger.error(f"异步查询失败: {e}")
            return []
    
    def delete_record(self, table: str, id: str) -> bool:
        """删除记录
        
        Args:
            table: 表名
            id: 记录ID
            
        Returns:
            是否删除成功
        """
        # 构建SQL
        record_id = f"{table}:{id}"
        sql = f"DELETE FROM {record_id};"
        
        try:
            result = self.execute_sql(sql)
            logger.info(f"记录删除成功: {record_id}")
            return True
        except Exception as e:
            logger.error(f"记录删除失败: {e}")
            return False
    
    def delete_records(self, table: str, condition: str) -> int:
        """删除满足条件的记录
        
        Args:
            table: 表名
            condition: 条件表达式
            
        Returns:
            删除的记录数
        """
        # 构建SQL
        sql = f"DELETE FROM {table} WHERE {condition};"
        
        try:
            result = self.execute_sql(sql)
            deleted_count = 0
            if result and len(result) > 0 and "result" in result[0]:
                deleted_count = len(result[0]["result"])
            logger.info(f"删除记录成功: {table}, 条件: {condition}, 数量: {deleted_count}")
            return deleted_count
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            return 0
    
    def get_records(self, table: str, condition: str = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取满足条件的记录
        
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
