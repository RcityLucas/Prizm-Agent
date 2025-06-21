"""
SurrealDB storage adapter for LangMem.

This module provides a storage implementation that uses SurrealDB as the backend.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Union

from langmem.core.models import Memory
from langmem.storage.base import StorageBase, StorageError

try:
    import surrealdb
    from surrealdb.ws import Surreal
except ImportError:
    raise ImportError(
        "SurrealDB client is not installed. "
        "Please install it with `pip install surrealdb`."
    )

logger = logging.getLogger(__name__)


class SurrealAdapter(StorageBase):
    """
    SurrealDB存储适配器，使用SurrealDB作为记忆存储后端。
    
    此适配器使用SurrealDB的WebSocket客户端连接到SurrealDB服务器，
    并提供记忆的存储、检索和查询功能。
    """
    
    def __init__(
        self,
        url: str = "ws://localhost:8000/rpc",
        namespace: str = "test",
        database: str = "test",
        username: Optional[str] = None,
        password: Optional[str] = None,
        table_name: str = "memories",
    ):
        """
        初始化SurrealDB适配器。
        
        Args:
            url: SurrealDB服务器的WebSocket URL
            namespace: SurrealDB命名空间
            database: SurrealDB数据库名称
            username: 可选的用户名，用于身份验证
            password: 可选的密码，用于身份验证
            table_name: 存储记忆的表名
        """
        self.url = url
        self.namespace = namespace
        self.database = database
        self.username = username
        self.password = password
        self.table_name = table_name
        self.client = None
        logger.info(
            "SurrealAdapter initialized with URL %s, namespace %s, database %s, table %s",
            url, namespace, database, table_name
        )
    
    async def connect(self) -> None:
        """
        连接到SurrealDB服务器。
        
        如果已经连接，则不执行任何操作。
        
        Raises:
            StorageError: 如果连接失败
        """
        if self.client is not None:
            return
        
        try:
            self.client = Surreal(self.url)
            await self.client.connect()
            
            # 设置命名空间和数据库
            await self.client.use(self.namespace, self.database)
            
            # 如果提供了用户名和密码，进行身份验证
            if self.username and self.password:
                await self.client.signin({"user": self.username, "pass": self.password})
            
            # 确保表结构存在
            await self._ensure_table_structure()
            
            logger.info("Connected to SurrealDB at %s", self.url)
        except Exception as e:
            logger.error("Failed to connect to SurrealDB: %s", str(e))
            raise StorageError(f"Failed to connect to SurrealDB: {str(e)}")
    
    async def _ensure_table_structure(self) -> None:
        """
        确保记忆表存在并具有正确的结构。
        
        Raises:
            StorageError: 如果创建表结构失败
        """
        try:
            # 定义表为SCHEMALESS，这样可以存储任意结构的记忆
            # 同时定义embedding字段为array类型，以支持向量搜索
            query = f"""
            DEFINE TABLE {self.table_name} SCHEMALESS;
            DEFINE FIELD embedding ON TABLE {self.table_name} TYPE array;
            DEFINE FIELD content ON TABLE {self.table_name} TYPE string;
            DEFINE FIELD memory_type ON TABLE {self.table_name} TYPE string;
            DEFINE FIELD created_at ON TABLE {self.table_name} TYPE datetime;
            DEFINE FIELD metadata ON TABLE {self.table_name} TYPE object;
            """
            await self.client.query(query)
            logger.info("Ensured table structure for %s", self.table_name)
        except Exception as e:
            logger.error("Failed to ensure table structure: %s", str(e))
            raise StorageError(f"Failed to ensure table structure: {str(e)}")
    
    async def create(self, memory: Memory) -> str:
        """
        在SurrealDB中创建新记忆。
        
        Args:
            memory: 要创建的记忆对象
            
        Returns:
            创建的记忆的ID
            
        Raises:
            StorageError: 如果创建失败
        """
        await self._ensure_connected()
        
        try:
            # 将Memory对象转换为字典
            memory_dict = memory.model_dump()
            
            # 移除id字段，让SurrealDB生成ID
            if "id" in memory_dict:
                del memory_dict["id"]
            
            # 创建记录
            result = await self.client.create(self.table_name, memory_dict)
            
            # 从结果中提取ID
            if result and len(result) > 0 and "id" in result[0]:
                # SurrealDB返回的ID格式为"table_name:id"，我们只需要"id"部分
                full_id = result[0]["id"]
                memory_id = full_id.split(":", 1)[1] if ":" in full_id else full_id
                logger.debug("Created memory with ID %s", memory_id)
                return memory_id
            else:
                logger.error("Failed to create memory: unexpected result format")
                raise StorageError("Failed to create memory: unexpected result format")
        except Exception as e:
            logger.error("Failed to create memory: %s", str(e))
            raise StorageError(f"Failed to create memory: {str(e)}")
    
    async def get(self, memory_id: str) -> Optional[Memory]:
        """
        根据ID从SurrealDB获取记忆。
        
        Args:
            memory_id: 记忆的ID
            
        Returns:
            找到的记忆对象，如果不存在则返回None
            
        Raises:
            StorageError: 如果获取失败
        """
        await self._ensure_connected()
        
        try:
            # 构建完整的记录ID
            full_id = f"{self.table_name}:{memory_id}"
            
            # 获取记录
            result = await self.client.select(full_id)
            
            # 如果没有找到记录，返回None
            if not result:
                logger.debug("Memory with ID %s not found", memory_id)
                return None
            
            # 将结果转换为Memory对象
            memory_dict = result
            
            # 确保id字段只包含ID部分，而不是完整的"table_name:id"
            if "id" in memory_dict and isinstance(memory_dict["id"], str):
                memory_dict["id"] = memory_dict["id"].split(":", 1)[1] if ":" in memory_dict["id"] else memory_dict["id"]
            
            # 创建并返回Memory对象
            memory = Memory(**memory_dict)
            logger.debug("Retrieved memory with ID %s", memory_id)
            return memory
        except Exception as e:
            logger.error("Failed to get memory with ID %s: %s", memory_id, str(e))
            raise StorageError(f"Failed to get memory with ID {memory_id}: {str(e)}")
    
    async def update(self, memory: Memory) -> bool:
        """
        在SurrealDB中更新现有记忆。
        
        Args:
            memory: 要更新的记忆对象，必须包含有效的ID
            
        Returns:
            更新是否成功
            
        Raises:
            ValueError: 如果memory.id为None
            StorageError: 如果更新失败
        """
        if memory.id is None:
            raise ValueError("Memory ID cannot be None for update operation")
        
        await self._ensure_connected()
        
        try:
            # 将Memory对象转换为字典
            memory_dict = memory.model_dump()
            
            # 构建完整的记录ID
            full_id = f"{self.table_name}:{memory.id}"
            
            # 从字典中移除id字段，因为它已经在记录ID中
            if "id" in memory_dict:
                del memory_dict["id"]
            
            # 更新记录
            result = await self.client.update(full_id, memory_dict)
            
            # 检查更新是否成功
            success = result is not None and len(result) > 0
            if success:
                logger.debug("Updated memory with ID %s", memory.id)
            else:
                logger.warning("Failed to update memory with ID %s: no record affected", memory.id)
            return success
        except Exception as e:
            logger.error("Failed to update memory with ID %s: %s", memory.id, str(e))
            raise StorageError(f"Failed to update memory with ID {memory.id}: {str(e)}")
    
    async def delete(self, memory_id: str) -> bool:
        """
        从SurrealDB中删除记忆。
        
        Args:
            memory_id: 要删除的记忆的ID
            
        Returns:
            删除是否成功
            
        Raises:
            StorageError: 如果删除失败
        """
        await self._ensure_connected()
        
        try:
            # 构建完整的记录ID
            full_id = f"{self.table_name}:{memory_id}"
            
            # 删除记录
            result = await self.client.delete(full_id)
            
            # 检查删除是否成功
            success = result is not None
            if success:
                logger.debug("Deleted memory with ID %s", memory_id)
            else:
                logger.warning("Failed to delete memory with ID %s: no record affected", memory_id)
            return success
        except Exception as e:
            logger.error("Failed to delete memory with ID %s: %s", memory_id, str(e))
            raise StorageError(f"Failed to delete memory with ID {memory_id}: {str(e)}")
    
    async def query(self, filters: Dict[str, Any], limit: int = 100) -> List[Memory]:
        """
        根据过滤条件从SurrealDB查询记忆。
        
        Args:
            filters: 过滤条件，键值对形式
            limit: 返回结果的最大数量
            
        Returns:
            符合条件的记忆列表
            
        Raises:
            StorageError: 如果查询失败
        """
        await self._ensure_connected()
        
        try:
            # 构建查询条件
            conditions = []
            params = {}
            
            for key, value in filters.items():
                # 对于复杂的过滤条件，可能需要更复杂的处理
                param_name = f"p_{key.replace('.', '_')}"
                conditions.append(f"{key} = ${param_name}")
                params[param_name] = value
            
            # 构建完整的查询
            where_clause = " AND ".join(conditions) if conditions else "true"
            query = f"SELECT * FROM {self.table_name} WHERE {where_clause} LIMIT {limit}"
            
            # 执行查询
            result = await self.client.query(query, params)
            
            # 处理结果
            if result and "result" in result and result["result"]:
                memories = []
                for item in result["result"][0]:
                    # 确保id字段只包含ID部分，而不是完整的"table_name:id"
                    if "id" in item and isinstance(item["id"], str):
                        item["id"] = item["id"].split(":", 1)[1] if ":" in item["id"] else item["id"]
                    
                    # 创建Memory对象
                    memory = Memory(**item)
                    memories.append(memory)
                
                logger.debug("Retrieved %d memories with filters %s", len(memories), filters)
                return memories
            else:
                logger.debug("No memories found with filters %s", filters)
                return []
        except Exception as e:
            logger.error("Failed to query memories with filters %s: %s", filters, str(e))
            raise StorageError(f"Failed to query memories: {str(e)}")
    
    async def vector_search(
        self,
        embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        在SurrealDB中执行向量相似度搜索。
        
        Args:
            embedding: 查询向量
            limit: 返回结果的最大数量
            filters: 可选的额外过滤条件
            
        Returns:
            包含记忆和相似度分数的列表，每项为字典，包含'memory'和'score'键
            
        Raises:
            StorageError: 如果搜索失败
        """
        await self._ensure_connected()
        
        try:
            # 构建过滤条件
            filter_conditions = []
            params = {"embedding": embedding}
            
            if filters:
                for key, value in filters.items():
                    param_name = f"p_{key.replace('.', '_')}"
                    filter_conditions.append(f"{key} = ${param_name}")
                    params[param_name] = value
            
            # 构建完整的查询
            where_clause = " AND ".join(filter_conditions) if filter_conditions else "true"
            
            # 使用向量相似度函数进行查询
            # 注意：这里使用欧几里得距离作为相似度度量，可以根据需要更改
            query = f"""
            SELECT *,
                   vector::distance(embedding, $embedding) as score
            FROM {self.table_name}
            WHERE {where_clause} AND embedding != []
            ORDER BY score ASC
            LIMIT {limit}
            """
            
            # 执行查询
            result = await self.client.query(query, params)
            
            # 处理结果
            if result and "result" in result and result["result"]:
                results = []
                for item in result["result"][0]:
                    # 提取分数
                    score = item.pop("score") if "score" in item else 1.0
                    
                    # 确保id字段只包含ID部分，而不是完整的"table_name:id"
                    if "id" in item and isinstance(item["id"], str):
                        item["id"] = item["id"].split(":", 1)[1] if ":" in item["id"] else item["id"]
                    
                    # 创建Memory对象
                    memory = Memory(**item)
                    
                    # 添加到结果列表
                    results.append({"memory": memory, "score": score})
                
                logger.debug("Retrieved %d memories from vector search", len(results))
                return results
            else:
                logger.debug("No memories found from vector search")
                return []
        except Exception as e:
            logger.error("Failed to perform vector search: %s", str(e))
            raise StorageError(f"Failed to perform vector search: {str(e)}")
    
    async def _ensure_connected(self) -> None:
        """
        确保已连接到SurrealDB服务器。
        
        如果尚未连接，则尝试连接。
        
        Raises:
            StorageError: 如果连接失败
        """
        if self.client is None:
            await self.connect()
        
        # 可以添加额外的连接检查逻辑，如ping操作
