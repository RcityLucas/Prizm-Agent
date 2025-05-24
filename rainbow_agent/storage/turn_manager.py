"""
轮次管理器

使用SurrealDB存储系统管理对话轮次
"""
import os
import uuid
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from .surreal_storage import SurrealStorage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TurnManager:
    """轮次管理器"""
    
    def __init__(self, 
                 url: str = "ws://localhost:8000/rpc",
                 namespace: str = "rainbow",
                 database: str = "agent",
                 username: str = "root",
                 password: str = "root"):
        """初始化轮次管理器
        
        Args:
            url: SurrealDB服务器URL
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
        """
        self.storage = SurrealStorage(url, namespace, database, username, password)
        logger.info("轮次管理器初始化完成")
    
    async def connect(self) -> None:
        """连接到存储系统"""
        await self.storage.connect()
    
    async def disconnect(self) -> None:
        """断开与存储系统的连接"""
        await self.storage.disconnect()
    
    async def create_turn(self, session_id: str, role: str, content: str, 
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建新轮次
        
        Args:
            session_id: 会话ID
            role: 角色 (human/ai)
            content: 内容
            metadata: 元数据
            
        Returns:
            创建的轮次
        """
        try:
            # 生成轮次ID - 使用不带连字符的UUID，避免SurrealDB解析问题
            turn_id = str(uuid.uuid4()).replace('-', '')
            
            # 方法1: 使用简化的数据和字符串时间戳
            try:
                # 创建简化的轮次数据，使用字符串时间戳
                now = datetime.now()
                simple_turn_data = {
                    "id": turn_id,
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "created_at": now.isoformat()  # 使用ISO格式字符串
                }
                
                created_turn = await self.storage.create("turns", simple_turn_data)
                logger.info(f"创建新轮次成功 (方法1): {turn_id}, 会话: {session_id}")
                return created_turn
            except Exception as e1:
                logger.error(f"方法1创建轮次失败: {e1}")
                
                # 方法2: 尝试使用原始 SQL 查询
                try:
                    logger.info("尝试使用原始 SQL 查询创建轮次...")
                    # 使用非常简单的查询，减少错误可能性
                    now_str = now.isoformat()
                    query_str = f"CREATE turns:{turn_id} SET session_id = '{session_id}', role = '{role}', content = '{content}', created_at = '{now_str}';"                
                    result = await self.storage.query(query_str)
                    logger.info(f"使用原始 SQL 查询创建轮次成功: {result}")
                    
                    # 返回创建的轮次数据
                    if result and len(result) > 0 and result[0] and len(result[0]) > 0:
                        return result[0][0]
                except Exception as e2:
                    logger.error(f"方法2使用原始 SQL 查询创建轮次失败: {e2}")
                
                # 方法3: 如果前两种方法都失败，返回一个内存中的轮次对象
                logger.warning("所有创建方法失败，返回内存中的轮次对象")
                return {
                    "id": turn_id,
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "metadata": metadata or {},
                    "created_at": now.isoformat(),
                    "in_memory_only": True  # 标记这是一个内存中的轮次对象
                }
        except Exception as e:
            logger.error(f"创建轮次失败: {e}")
            # 返回一个最简单的内存对象，确保用户体验不中断
            return {
                "id": str(uuid.uuid4()).replace('-', ''),
                "session_id": session_id,
                "role": role,
                "content": content,
                "created_at": datetime.now().isoformat(),
                "in_memory_only": True
            }
    
    async def get_turns(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取会话的轮次列表
        
        Args:
            session_id: 会话ID
            limit: 限制返回的轮次数
            offset: 跳过的轮次数
            
        Returns:
            轮次列表
        """
        logger.info(f"开始获取会话 {session_id} 的轮次列表")
        
        # 首先确保存储已连接
        if not hasattr(self.storage, '_connected') or not self.storage._connected:
            logger.warning("存储未连接，尝试连接...")
            try:
                await self.connect()
                logger.info("存储连接成功")
            except Exception as conn_error:
                logger.error(f"存储连接失败: {conn_error}")
                # 返回空列表而不是抛出异常
                return []
        
        try:
            # 初始化轮次表
            try:
                # 创建轮次表（如果不存在）
                create_table_query = """
                DEFINE TABLE turns SCHEMAFULL;
                DEFINE FIELD session_id ON turns TYPE string;
                DEFINE FIELD role ON turns TYPE string;
                DEFINE FIELD content ON turns TYPE string;
                DEFINE FIELD created_at ON turns TYPE datetime;
                """
                logger.info("尝试创建轮次表...")
                await self.storage.query(create_table_query)
                logger.info("轮次表创建成功")
            except Exception as table_error:
                # 如果表已存在，忽略错误
                logger.warning(f"创建轮次表时出错，可能表已存在: {table_error}")
            
            # 尝试使用SurrealQL查询
            try:
                logger.info(f"正在查询会话 {session_id} 的轮次...")
                query_str = f"""
                SELECT * FROM turns 
                WHERE session_id = '{session_id}'
                ORDER BY created_at ASC
                LIMIT {limit} START {offset}
                """
                logger.info(f"执行查询: {query_str}")
                
                results = await self.storage.query(query_str)
                logger.info(f"查询结果: {results}")
                
                if results and len(results) > 0 and results[0]:
                    turns = results[0]
                    logger.info(f"获取会话 {session_id} 的轮次列表成功，共 {len(turns)} 个")
                    return turns
                else:
                    logger.info(f"会话 {session_id} 没有轮次")
                    return []
            except Exception as query_error:
                logger.error(f"执行查询失败，尝试使用read_many: {query_error}")
                # 如果查询失败，尝试使用read_many
                # 构建查询
                query = {"session_id": session_id}
                
                # 获取轮次
                logger.info(f"使用read_many获取会话 {session_id} 的轮次")
                turns = await self.storage.read_many("turns", query, limit, offset)
                
                # 按创建时间排序
                turns.sort(key=lambda x: x.get("created_at", ""))
                
                logger.info(f"获取会话 {session_id} 的轮次列表成功，共 {len(turns)} 个")
                return turns
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"获取轮次列表失败: {e}\n{error_traceback}")
            # 返回空列表而不是抛出异常
            return []
    
    async def get_turn(self, turn_id: str) -> Optional[Dict[str, Any]]:
        """获取特定轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            轮次数据，如果不存在则返回None
        """
        try:
            turn = await self.storage.read("turns", turn_id)
            if turn:
                logger.info(f"获取轮次 {turn_id} 成功")
            else:
                logger.info(f"轮次 {turn_id} 不存在")
            return turn
        except Exception as e:
            logger.error(f"获取轮次失败: {e}")
            raise
    
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
            updated_turn = await self.storage.update("turns", turn_id, updates)
            
            if updated_turn:
                logger.info(f"更新轮次 {turn_id} 成功")
                return updated_turn
            else:
                logger.info(f"轮次 {turn_id} 不存在，无法更新")
                return None
        except Exception as e:
            logger.error(f"更新轮次失败: {e}")
            raise
    
    async def delete_turn(self, turn_id: str) -> bool:
        """删除轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            是否删除成功
        """
        try:
            result = await self.storage.delete("turns", turn_id)
            if result:
                logger.info(f"删除轮次 {turn_id} 成功")
            else:
                logger.info(f"轮次 {turn_id} 不存在，无法删除")
            return result
        except Exception as e:
            logger.error(f"删除轮次失败: {e}")
            raise
    
    async def delete_session_turns(self, session_id: str) -> int:
        """删除会话的所有轮次
        
        Args:
            session_id: 会话ID
            
        Returns:
            删除的轮次数量
        """
        try:
            # 在SurrealDB中，我们需要使用自定义查询来删除特定会话的所有轮次
            query_str = f"DELETE FROM turns WHERE session_id = '{session_id}'"
            result = await self.storage.query(query_str)
            
            # 计算删除的轮次数量
            deleted_count = 0
            if result and len(result) > 0:
                deleted_count = len(result[0])
            
            logger.info(f"删除会话 {session_id} 的所有轮次成功，共 {deleted_count} 个")
            return deleted_count
        except Exception as e:
            logger.error(f"删除会话轮次失败: {e}")
            raise
