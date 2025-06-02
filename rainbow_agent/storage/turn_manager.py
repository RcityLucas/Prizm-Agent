"""
轮次管理器

使用SurrealDB存储系统管理对话轮次，继承自BaseManager
"""
import os
import uuid
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .base_manager import BaseManager
from .models import TurnModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TurnManager(BaseManager):
    """轮次管理器，继承自BaseManager"""
    
    # 内存缓存
    _turn_cache = {}
    
    def __init__(self, 
                 url: Optional[str] = None,
                 namespace: Optional[str] = None,
                 database: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """初始化轮次管理器
        
        Args:
            url: SurrealDB服务器URL
            namespace: 命名空间
            database: 数据库名
            username: 用户名
            password: 密码
        """
        super().__init__(url, namespace, database, username, password, "TurnManager")
        
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
            
            self.execute_sql(sql)
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
            
            # 使用HTTP JSON API创建记录
            logger.info(f"使用HTTP JSON API创建轮次: {turn_model.id}")
            
            # 调用client.create_record方法创建记录
            result = self.client.create_record("turns", turn_data)
            
            # 检查结果
            if result:
                # 将新创建的轮次添加到内存缓存
                TurnManager._turn_cache[turn_model.id] = turn_model
                
                # 返回创建的轮次
                logger.info(f"轮次创建成功: {turn_model.id}")
                return turn_data
            else:
                logger.error(f"创建轮次失败: 无返回结果")
                raise Exception("创建轮次失败: 无返回结果")
        except Exception as e:
            logger.error(f"创建轮次失败: {e}")
            raise
            
    async def create_turn_async(self, session_id: str, role: str, content: str, 
                        embedding: Optional[List[float]] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """异步创建新轮次
        
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
            
            # 使用HTTP JSON API创建记录
            logger.info(f"异步使用HTTP JSON API创建轮次: {turn_model.id}")
            
            # 调用client.create_record_async方法创建记录
            result = await self.client.create_record_async("turns", turn_data)
            
            # 检查结果
            if result:
                # 将新创建的轮次添加到内存缓存
                TurnManager._turn_cache[turn_model.id] = turn_model
                
                # 返回创建的轮次
                logger.info(f"轮次异步创建成功: {turn_model.id}")
                return turn_data
            else:
                logger.error(f"轮次异步创建失败: 无返回结果")
                raise Exception("轮次异步创建失败: 无返回结果")
        except Exception as e:
            logger.error(f"轮次异步创建失败: {e}")
            raise
    
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
            # 使用HTTP JSON API查询数据
            logger.info(f"使用HTTP JSON API获取会话 {session_id} 的轮次列表")
            query = {"session_id": session_id}
            
            # 执行查询
            turns_data = self.client.query_records("turns", query, limit=limit, offset=offset)
            
            # 转换为模型并添加到内存缓存
            turn_models = []
            for turn_data in turns_data:
                turn_model = TurnModel.from_dict(turn_data)
                turn_id = turn_model.id
                if turn_id:
                    TurnManager._turn_cache[turn_id] = turn_model
                turn_models.append(turn_model)
            
            logger.info(f"获取会话 {session_id} 的轮次列表成功，共 {len(turn_models)} 条")
            return turn_models
        except Exception as e:
            logger.error(f"获取会话 {session_id} 的轮次列表失败: {e}")
            return []
            
    async def get_turns_by_session_async(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Union[Dict[str, Any], TurnModel]]:
        """异步根据会话ID获取轮次列表
        
        Args:
            session_id: 会话ID
            limit: 最大返回数量
            offset: 偏移量
            
        Returns:
            轮次列表
        """
        try:
            # 使用HTTP JSON API异步查询数据
            logger.info(f"使用HTTP JSON API异步获取会话 {session_id} 的轮次列表")
            query = {"session_id": session_id}
            
            # 异步执行查询
            turns_data = await self.client.query_records_async("turns", query, limit=limit, offset=offset)
            
            # 转换为模型并添加到内存缓存
            turn_models = []
            for turn_data in turns_data:
                turn_model = TurnModel.from_dict(turn_data)
                turn_id = turn_model.id
                if turn_id:
                    TurnManager._turn_cache[turn_id] = turn_model
                turn_models.append(turn_model)
            
            logger.info(f"异步获取会话 {session_id} 的轮次列表成功，共 {len(turn_models)} 条")
            return turn_models
        except Exception as e:
            logger.error(f"异步获取会话 {session_id} 的轮次列表失败: {e}")
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
            if turn_id in TurnManager._turn_cache:
                logger.info(f"从内存缓存中获取轮次: {turn_id}")
                cached_turn = TurnManager._turn_cache[turn_id]
                
                # 如果缓存中的是字典，转换为模型
                if isinstance(cached_turn, dict):
                    return TurnModel.from_dict(cached_turn)
                return cached_turn
            
            # 如果内存缓存中没有，使用HTTP JSON API从数据库获取
            logger.info(f"使用HTTP JSON API从数据库获取轮次: {turn_id}")
            turn_data = self.client.get_record("turns", turn_id)
            
            if turn_data:
                # 创建轮次模型
                turn_model = TurnModel.from_dict(turn_data)
                
                # 将轮次添加到内存缓存
                TurnManager._turn_cache[turn_id] = turn_model
                logger.info(f"轮次获取成功并添加到内存缓存: {turn_id}")
                return turn_model
            else:
                logger.info(f"轮次 {turn_id} 不存在")
                return None
        except Exception as e:
            logger.error(f"获取轮次失败: {e}")
            return None
            
    async def get_turn_async(self, turn_id: str) -> Optional[Union[Dict[str, Any], TurnModel]]:
        """异步获取特定轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            轮次数据，如果不存在则返回None
        """
        try:
            # 先检查内存缓存
            if turn_id in TurnManager._turn_cache:
                logger.info(f"从内存缓存中异步获取轮次: {turn_id}")
                cached_turn = TurnManager._turn_cache[turn_id]
                
                # 如果缓存中的是字典，转换为模型
                if isinstance(cached_turn, dict):
                    return TurnModel.from_dict(cached_turn)
                return cached_turn
            
            # 如果内存缓存中没有，使用HTTP JSON API从数据库获取
            logger.info(f"使用HTTP JSON API异步从数据库获取轮次: {turn_id}")
            turn_data = await self.client.get_record_async("turns", turn_id)
            
            if turn_data:
                # 创建轮次模型
                turn_model = TurnModel.from_dict(turn_data)
                
                # 将轮次添加到内存缓存
                TurnManager._turn_cache[turn_id] = turn_model
                logger.info(f"轮次异步获取成功并添加到内存缓存: {turn_id}")
                return turn_model
            else:
                logger.info(f"轮次 {turn_id} 不存在")
                return None
        except Exception as e:
            logger.error(f"异步获取轮次失败: {e}")
            return None
    
    def update_turn(self, turn_id: str, updates: Dict[str, Any]) -> Optional[Union[Dict[str, Any], TurnModel]]:
        """更新轮次
        
        Args:
            turn_id: 轮次ID
            updates: 要更新的字段
            
        Returns:
            更新后的轮次，如果轮次不存在则返回None
        """
        try:
            # 首先检查轮次是否存在
            existing_turn = self.get_turn(turn_id)
            if not existing_turn:
                logger.info(f"轮次 {turn_id} 不存在，无法更新")
                return None
            
            # 使用HTTP JSON API更新轮次
            logger.info(f"使用HTTP JSON API更新轮次: {turn_id}")
            updated_turn_data = self.client.update_record("turns", turn_id, updates)
            
            if updated_turn_data:
                # 创建轮次模型
                updated_turn = TurnModel.from_dict(updated_turn_data)
                
                # 更新内存缓存
                TurnManager._turn_cache[turn_id] = updated_turn
                logger.info(f"更新轮次 {turn_id} 成功并更新内存缓存")
                return updated_turn
            else:
                logger.info(f"轮次 {turn_id} 更新失败")
                return None
        except Exception as e:
            logger.error(f"更新轮次失败: {e}")
            return None
            
    async def update_turn_async(self, turn_id: str, updates: Dict[str, Any]) -> Optional[Union[Dict[str, Any], TurnModel]]:
        """异步更新轮次
        
        Args:
            turn_id: 轮次ID
            updates: 要更新的字段
            
        Returns:
            更新后的轮次，如果轮次不存在则返回None
        """
        try:
            # 首先异步检查轮次是否存在
            existing_turn = await self.get_turn_async(turn_id)
            if not existing_turn:
                logger.info(f"轮次 {turn_id} 不存在，无法异步更新")
                return None
            
            # 使用HTTP JSON API异步更新轮次
            logger.info(f"使用HTTP JSON API异步更新轮次: {turn_id}")
            updated_turn_data = await self.client.update_record_async("turns", turn_id, updates)
            
            if updated_turn_data:
                # 创建轮次模型
                updated_turn = TurnModel.from_dict(updated_turn_data)
                
                # 更新内存缓存
                TurnManager._turn_cache[turn_id] = updated_turn
                logger.info(f"异步更新轮次 {turn_id} 成功并更新内存缓存")
                return updated_turn
            else:
                logger.info(f"轮次 {turn_id} 异步更新失败")
                return None
        except Exception as e:
            logger.error(f"异步更新轮次失败: {e}")
            return None
    
    def delete_turn(self, turn_id: str) -> bool:
        """删除轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            是否删除成功
        """
        try:
            # 使用HTTP JSON API删除轮次
            logger.info(f"使用HTTP JSON API删除轮次: {turn_id}")
            result = self.client.delete_record("turns", turn_id)
            
            # 如果删除成功，从内存缓存中移除
            if result and turn_id in TurnManager._turn_cache:
                del TurnManager._turn_cache[turn_id]
            
            if result:
                logger.info(f"删除轮次 {turn_id} 成功")
            else:
                logger.info(f"轮次 {turn_id} 不存在，无法删除")
            
            return result
        except Exception as e:
            logger.error(f"删除轮次失败: {e}")
            return False
            
    async def delete_turn_async(self, turn_id: str) -> bool:
        """异步删除轮次
        
        Args:
            turn_id: 轮次ID
            
        Returns:
            是否删除成功
        """
        try:
            # 使用HTTP JSON API异步删除轮次
            logger.info(f"使用HTTP JSON API异步删除轮次: {turn_id}")
            result = await self.client.delete_record_async("turns", turn_id)
            
            # 如果删除成功，从内存缓存中移除
            if result and turn_id in TurnManager._turn_cache:
                del TurnManager._turn_cache[turn_id]
            
            if result:
                logger.info(f"异步删除轮次 {turn_id} 成功")
            else:
                logger.info(f"轮次 {turn_id} 不存在，无法异步删除")
            
            return result
        except Exception as e:
            logger.error(f"异步删除轮次失败: {e}")
            return False
    
    def delete_session_turns(self, session_id: str) -> int:
        """删除会话的所有轮次
        
        Args:
            session_id: 会话ID
            
        Returns:
            删除的轮次数量
        """
        try:
            # 先获取会话的所有轮次
            turns = self.get_turns_by_session(session_id)
            turn_ids = [turn.id if hasattr(turn, 'id') else turn.get('id') for turn in turns]
            
            # 使用HTTP JSON API删除每个轮次
            deleted_count = 0
            for turn_id in turn_ids:
                if turn_id:
                    if self.delete_turn(turn_id):
                        deleted_count += 1
            
            logger.info(f"删除会话 {session_id} 的所有轮次成功，共 {deleted_count} 个")
            return deleted_count
        except Exception as e:
            logger.error(f"删除会话轮次失败: {e}")
            return 0
            
    async def delete_session_turns_async(self, session_id: str) -> int:
        """异步删除会话的所有轮次
        
        Args:
            session_id: 会话ID
            
        Returns:
            删除的轮次数量
        """
        try:
            # 先异步获取会话的所有轮次
            # 注意：这里假设我们已经实现了get_turns_by_session_async
            # 如果没有，可以先使用同步的get_turns_by_session或实现异步版本
            turns = await self.get_turns_by_session_async(session_id) if hasattr(self, 'get_turns_by_session_async') else self.get_turns_by_session(session_id)
            turn_ids = [turn.id if hasattr(turn, 'id') else turn.get('id') for turn in turns]
            
            # 使用HTTP JSON API异步删除每个轮次
            deleted_count = 0
            for turn_id in turn_ids:
                if turn_id:
                    if await self.delete_turn_async(turn_id):
                        deleted_count += 1
            
            logger.info(f"异步删除会话 {session_id} 的所有轮次成功，共 {deleted_count} 个")
            return deleted_count
        except Exception as e:
            logger.error(f"异步删除会话轮次失败: {e}")
            return 0
