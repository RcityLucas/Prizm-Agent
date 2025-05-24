"""
会话管理器

使用SurrealDB存储系统管理会话
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


class SessionManager:
    """会话管理器"""
    
    def __init__(self, 
                 url: str = "ws://localhost:8000/rpc",
                 namespace: str = "rainbow",
                 database: str = "agent",
                 username: str = "root",
                 password: str = "root"):
        """初始化会话管理器
        
        Args:
            url: SurrealDB服务器URL
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
        """
        self.storage = SurrealStorage(url, namespace, database, username, password)
        logger.info("会话管理器初始化完成")
    
    async def connect(self) -> None:
        """连接到存储系统"""
        await self.storage.connect()
    
    async def disconnect(self) -> None:
        """断开与存储系统的连接"""
        await self.storage.disconnect()
    
    async def create_session(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """创建新会话
        
        Args:
            user_id: 用户ID
            title: 会话标题，如果不提供则使用默认标题
            
        Returns:
            创建的会话
        """
        logger.info(f"开始创建新会话: user_id={user_id}, title={title}")
        
        try:
            # 生成会话ID - 使用不带连字符的UUID，避免SurrealDB解析问题
            session_id = str(uuid.uuid4()).replace('-', '')
            
            # 创建会话数据
            now = datetime.now()  # 使用datetime对象
            now_iso = now.isoformat()  # 只在需要字符串时使用
            session_title = title if title else f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # 使用SurrealDB的简化结构
            session_data = {
                "id": session_id,  # 只使用UUID作为ID，表名由storage.create方法添加
                "title": session_title,
                "user_id": user_id,
                "timestamp": now,
                "last_activity": datetime.now(),  # 使用datetime对象而不是字符串
                # 保留原始数据结构以兼容现有代码
                "name": session_title,
                "dialogue_type": "human_to_ai_private",
                "participants": [
                    {
                        "id": user_id,
                        "name": "用户",
                        "type": "human"
                    },
                    {
                        "id": "ai_assistant",
                        "name": "Rainbow助手",
                        "type": "ai"
                    }
                ],
                "metadata": {},
                "created_at": now,
                "updated_at": now,
                "last_activity_at": now
            }
            
            logger.info(f"准备创建会话数据: {session_data}")
            
            # 创建会话 - 使用多种方法尝试创建会话
            # 方法1: 使用storage.create方法
            try:
                # 创建一个简化的会话数据，减少可能的错误
                simple_session_data = {
                    "id": session_id,
                    "title": session_title,
                    "user_id": user_id,
                    "created_at": now.isoformat()
                }
                created_session = await self.storage.create("sessions", simple_session_data)
                logger.info(f"创建新会话成功: {created_session}")
                return created_session
            except Exception as create_error:
                logger.error(f"方法1创建会话失败: {create_error}")
                
                # 方法2: 尝试使用原始 SQL 查询创建
                try:
                    logger.info("尝试使用原始 SQL 查询创建会话...")
                    # 使用非常简单的查询，减少错误可能性
                    query_str = f"CREATE sessions:{session_id} SET title = '{session_title}', user_id = '{user_id}';"                
                    result = await self.storage.query(query_str)
                    logger.info(f"使用原始 SQL 查询创建会话成功: {result}")
                    
                    # 返回创建的会话数据
                    if result and len(result) > 0 and result[0] and len(result[0]) > 0:
                        return result[0][0]
                except Exception as query_error:
                    logger.error(f"方法2使用原始 SQL 查询创建会话失败: {query_error}")
                
                # 方法3: 如果前两种方法都失败，返回一个内存中的会话对象
                logger.warning("所有创建方法失败，返回内存中的会话对象")
                return {
                    "id": session_id,
                    "title": session_title,
                    "user_id": user_id,
                    "timestamp": now.isoformat(),
                    "created_at": now.isoformat(),
                    "in_memory_only": True  # 标记这是一个内存中的会话对象
                }
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"创建会话失败: {e}\n{error_traceback}")
            raise Exception(f"创建会话失败: {e}\n{error_traceback}")
    
    async def get_sessions(self, user_id: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """获取会话列表
        
        Args:
            user_id: 用户ID，如果提供则只返回该用户的会话
            limit: 限制返回的会话数
            offset: 跳过的会话数
            
        Returns:
            会话列表
        """
        logger.info(f"开始获取会话列表: user_id={user_id}, limit={limit}, offset={offset}")
        
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
            # 初始化会话表
            try:
                # 创建会话表（如果不存在）
                create_table_query = """
                DEFINE TABLE sessions SCHEMAFULL;
                DEFINE FIELD title ON sessions TYPE string;
                DEFINE FIELD user_id ON sessions TYPE string;
                DEFINE FIELD timestamp ON sessions TYPE datetime;
                DEFINE FIELD last_activity ON sessions TYPE datetime;
                """
                logger.info("尝试创建会话表...")
                await self.storage.query(create_table_query)
                logger.info("会话表创建成功")
            except Exception as table_error:
                # 如果表已存在，忽略错误
                logger.warning(f"创建会话表时出错，可能表已存在: {table_error}")
            
            # 构建查询条件
            if user_id:
                logger.info(f"正在查询用户 {user_id} 的会话...")
                # 在SurrealDB中，我们需要使用自定义查询来查找特定用户的会话
                # 简化查询，使用user_id字段而不是participants数组
                query_str = f"""
                SELECT * FROM sessions 
                WHERE user_id = '{user_id}'
                LIMIT {limit} START {offset}
                """
                logger.info(f"执行查询: {query_str}")
                
                try:
                    results = await self.storage.query(query_str)
                    logger.info(f"查询结果: {results}")
                    
                    if results and len(results) > 0 and results[0]:
                        sessions = results[0]
                        logger.info(f"获取用户 {user_id} 的会话列表成功，共 {len(sessions)} 个")
                        return sessions
                    else:
                        logger.info(f"用户 {user_id} 没有会话")
                        # 创建一个测试会话，以便前端可以测试
                        logger.info(f"为用户 {user_id} 创建测试会话...")
                        try:
                            test_session = await self.create_session(user_id, "测试会话")
                            logger.info(f"测试会话创建成功: {test_session}")
                            return [test_session]
                        except Exception as create_error:
                            logger.error(f"创建测试会话失败: {create_error}")
                            return []
                except Exception as query_error:
                    logger.error(f"执行查询失败: {query_error}")
                    return []
            else:
                # 获取所有会话
                logger.info("正在获取所有会话...")
                try:
                    sessions = await self.storage.read_many("sessions", {}, limit, offset)
                    logger.info(f"获取所有会话列表成功，共 {len(sessions)} 个")
                    
                    if not sessions or len(sessions) == 0:
                        # 如果没有会话，创建一个测试会话
                        logger.info("没有会话，创建测试会话...")
                        try:
                            test_session = await self.create_session("test_user", "测试会话")
                            logger.info(f"测试会话创建成功: {test_session}")
                            return [test_session]
                        except Exception as create_error:
                            logger.error(f"创建测试会话失败: {create_error}")
                            return []
                    
                    return sessions
                except Exception as read_error:
                    logger.error(f"读取会话失败: {read_error}")
                    return []
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"获取会话列表失败: {e}\n{error_traceback}")
            # 返回空列表而不是抛出异常
            return []
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取特定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，如果不存在则返回None
        """
        try:
            session = await self.storage.read("sessions", session_id)
            if session:
                logger.info(f"获取会话 {session_id} 成功")
            else:
                logger.info(f"会话 {session_id} 不存在")
            return session
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            raise
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新会话
        
        Args:
            session_id: 会话ID
            updates: 要更新的字段
            
        Returns:
            更新后的会话，如果会话不存在则返回None
        """
        try:
            # 添加更新时间
            if "updated_at" not in updates:
                updates["updated_at"] = datetime.now().isoformat()
            
            # 更新会话
            updated_session = await self.storage.update("sessions", session_id, updates)
            
            if updated_session:
                logger.info(f"更新会话 {session_id} 成功")
                return updated_session
            else:
                logger.info(f"会话 {session_id} 不存在，无法更新")
                return None
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            raise
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            result = await self.storage.delete("sessions", session_id)
            if result:
                logger.info(f"删除会话 {session_id} 成功")
            else:
                logger.info(f"会话 {session_id} 不存在，无法删除")
            return result
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            raise
    
    async def record_activity(self, session_id: str) -> bool:
        """记录会话活动
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否记录成功
        """
        try:
            # 更新最后活动时间
            updates = {
                "last_activity_at": datetime.now().isoformat()
            }
            
            # 更新会话
            updated_session = await self.storage.update("sessions", session_id, updates)
            
            if updated_session:
                logger.info(f"记录会话 {session_id} 活动成功")
                return True
            else:
                logger.info(f"会话 {session_id} 不存在，无法记录活动")
                return False
        except Exception as e:
            logger.error(f"记录会话活动失败: {e}")
            raise
