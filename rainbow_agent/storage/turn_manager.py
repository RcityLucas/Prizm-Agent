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
            logger.info(f"异步使用HTTP JSON API创建轮次: {turn_model.id}, 数据: {turn_data}")
            
            # 调用client.create_record_async方法创建记录
            result = await self.client.create_record_async("turns", turn_data)
            
            # 检查结果
            if result:
                # 将新创建的轮次添加到内存缓存
                TurnManager._turn_cache[turn_model.id] = turn_model
                
                # 验证记录是否成功存储
                try:
                    # 使用直接SQL查询验证记录是否存在
                    verify_query = f"SELECT * FROM turns WHERE id = '{turn_model.id}';"  
                    logger.info(f"验证轮次记录存储: {verify_query}")
                    
                    verify_result = await self.client.execute_sql(verify_query)
                    logger.info(f"验证查询结果: {verify_result}")
                    
                    # 检查验证结果
                    record_exists = False
                    if verify_result and isinstance(verify_result, list) and len(verify_result) > 0:
                        if isinstance(verify_result[0], dict) and 'result' in verify_result[0]:
                            if isinstance(verify_result[0]['result'], list) and len(verify_result[0]['result']) > 0:
                                record_exists = True
                    
                    if record_exists:
                        logger.info(f"轮次记录存储验证成功: {turn_model.id}")
                    else:
                        # 如果验证失败，尝试再次创建记录
                        logger.warning(f"轮次记录存储验证失败，尝试使用直接SQL创建: {turn_model.id}")
                        
                        # 使用直接SQL插入记录
                        insert_query = f"""
                        INSERT INTO turns (id, session_id, role, content, created_at, updated_at)
                        VALUES ('{turn_model.id}', '{session_id}', '{role}', '{content.replace("'", "''")}', '{turn_model.created_at}', '{turn_model.updated_at}');
                        """
                        
                        logger.info(f"执行直接SQL插入: {insert_query}")
                        insert_result = await self.client.execute_sql(insert_query)
                        logger.info(f"直接SQL插入结果: {insert_result}")
                        
                        # 再次验证
                        second_verify = await self.client.execute_sql_async_v_new(f"SELECT * FROM turns WHERE id = '{turn_model.id}';")
                        if second_verify and isinstance(second_verify, list) and len(second_verify) > 0:
                            if isinstance(second_verify[0], dict) and 'result' in second_verify[0]:
                                if isinstance(second_verify[0]['result'], list) and len(second_verify[0]['result']) > 0:
                                    logger.info(f"直接SQL插入后验证成功: {turn_model.id}")
                                else:
                                    logger.warning(f"直接SQL插入后验证仍然失败: {turn_model.id}")
                except Exception as verify_error:
                    logger.error(f"验证轮次记录时出错: {verify_error}")
                
                # 返回创建的轮次
                logger.info(f"轮次异步创建成功: {turn_model.id}")
                return turn_data
            else:
                logger.error(f"轮次异步创建失败: 无返回结果")
                # 尝试使用直接SQL插入作为备用方法
                try:
                    logger.info(f"尝试使用直接SQL插入作为备用方法")
                    insert_query = f"""
                    INSERT INTO turns (id, session_id, role, content, created_at, updated_at)
                    VALUES ('{turn_model.id}', '{session_id}', '{role}', '{content.replace("'", "''")}', '{turn_model.created_at}', '{turn_model.updated_at}');
                    """
                    
                    logger.info(f"执行直接SQL插入: {insert_query}")
                    insert_result = await self.client.execute_sql(insert_query)
                    logger.info(f"直接SQL插入结果: {insert_result}")
                    
                    # 将新创建的轮次添加到内存缓存
                    TurnManager._turn_cache[turn_model.id] = turn_model
                    
                    logger.info(f"使用备用方法创建轮次成功: {turn_model.id}")
                    return turn_data
                except Exception as backup_error:
                    logger.error(f"备用方法创建轮次失败: {backup_error}")
                    raise Exception(f"轮次异步创建失败: 无返回结果，备用方法也失败: {backup_error}")
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
        
        try:
            # 尝试使用直接SQL查询获取轮次
            try:
                # 使用直接SQL查询，确保数据能被正确存储和检索
                direct_query = f"""
                SELECT * FROM turns 
                WHERE session_id = '{session_id}'
                ORDER BY created_at ASC
                LIMIT {limit} OFFSET {offset};
                """
                
                logger.info(f"执行直接SQL查询: {direct_query}")
                direct_results = await self.client.execute_sql_async_v_new(direct_query)
                
                # 处理直接查询结果
                if direct_results and isinstance(direct_results, list) and len(direct_results) > 0:
                    # 检查是否有实际数据记录
                    if isinstance(direct_results[0], dict) and 'result' in direct_results[0]:
                        if isinstance(direct_results[0]['result'], list):
                            turns = direct_results[0]['result']
                            logger.info(f"直接SQL查询成功获取会话 {session_id} 的轮次列表，共 {len(turns)} 个")
                            return turns
            
                # 如果直接查询没有返回数据，尝试使用参数化查询
                logger.info(f"直接查询未返回数据，尝试参数化查询")
                query_str = f"""
                SELECT * FROM turns 
                WHERE session_id = $session_id
                ORDER BY created_at ASC
                LIMIT {limit} START {offset}
                """
                params = {"session_id": session_id}
                
                logger.info(f"执行参数化查询: {query_str} with params: {params}")
                results = await self.client.execute_sql_async_v_new(query_str, params=params)
                logger.info(f"参数化查询结果: {results}")
                
                # 处理参数化查询结果
                if results:
                    # 如果结果已经是列表形式的记录
                    if all(isinstance(item, dict) and 'id' in item for item in results):
                        logger.info(f"获取会话 {session_id} 的轮次列表成功，共 {len(results)} 个")
                        return results
                    
                    # 如果结果是包含元数据的响应
                    if isinstance(results, list) and len(results) > 0:
                        if isinstance(results[0], dict) and 'result' in results[0]:
                            # 如果result字段包含实际记录列表
                            if isinstance(results[0]['result'], list):
                                turns = results[0]['result']
                                logger.info(f"获取会话 {session_id} 的轮次列表成功，共 {len(turns)} 个")
                                return turns
                            # 如果result字段包含单个记录
                            elif isinstance(results[0]['result'], dict) and not ('query' in results[0]['result'] and 'vars' in results[0]['result']):
                                turns = [results[0]['result']]
                                logger.info(f"获取会话 {session_id} 的轮次列表成功，共 1 个")
                                return turns
                            # 如果result字段只包含查询元数据
                            else:
                                # 尝试使用另一种方式查询
                                logger.warning(f"SurrealDB查询只返回了元数据，尝试使用备用查询方法")
                                backup_query = f"RETURN SELECT * FROM turns WHERE session_id = '{session_id}';"
                                backup_results = await self.client.execute_sql_async_v_new(backup_query)
                                
                                if backup_results and isinstance(backup_results, list) and len(backup_results) > 0:
                                    if isinstance(backup_results[0], dict) and 'result' in backup_results[0]:
                                        if isinstance(backup_results[0]['result'], list):
                                            turns = backup_results[0]['result']
                                            logger.info(f"备用查询成功获取会话 {session_id} 的轮次列表，共 {len(turns)} 个")
                                            return turns
            
                # 如果所有查询方法都未返回数据
                logger.info(f"会话 {session_id} 没有轮次")
                return []
                
            except Exception as query_error:
                logger.error(f"查询会话 {session_id} 的轮次失败: {query_error}")
                
                # 最后尝试使用HTTP API直接获取所有turns记录
                try:
                    logger.info(f"尝试使用HTTP API获取所有turns记录")
                    all_turns_query = "SELECT * FROM turns;"
                    all_turns = await self.client.execute_sql_async_v_new(all_turns_query)
                    
                    if all_turns and isinstance(all_turns, list) and len(all_turns) > 0:
                        if isinstance(all_turns[0], dict) and 'result' in all_turns[0]:
                            if isinstance(all_turns[0]['result'], list):
                                # 过滤出当前会话的轮次
                                session_turns = [turn for turn in all_turns[0]['result'] 
                                               if isinstance(turn, dict) and turn.get('session_id') == session_id]
                                
                                if session_turns:
                                    logger.info(f"通过获取所有turns记录成功找到会话 {session_id} 的轮次，共 {len(session_turns)} 个")
                                    return session_turns
                except Exception as all_turns_error:
                    logger.error(f"获取所有turns记录失败: {all_turns_error}")
                
                return []
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
            
    async def create_turn_async(self, *args, **kwargs) -> Union[str, Dict[str, Any]]:
        """异步创建轮次
        
        支持两种调用方式:
        1. create_turn_async(turn_model: TurnModel)
        2. create_turn_async(session_id: str, role: str, content: str, ...)
        
        Args:
            turn_model: 轮次模型
            或
            session_id: 会话 ID
            role: 角色 (human/ai)
            content: 内容
            embedding: 可选，向量嵌入
            metadata: 可选，元数据
            
        Returns:
            轮次ID或轮次数据字典
        """
        try:
            # 检查调用方式
            if len(args) == 1 and isinstance(args[0], TurnModel):
                # 方式 1: 直接传入 TurnModel 对象
                turn_model = args[0]
                return_dict = False
            elif 'turn_model' in kwargs and isinstance(kwargs['turn_model'], TurnModel):
                # 方式 1: 作为命名参数传入 TurnModel 对象
                turn_model = kwargs['turn_model']
                return_dict = False
            else:
                # 方式 2: 传入单独的参数
                # 检查必要参数
                session_id = kwargs.get('session_id')
                role = kwargs.get('role')
                content = kwargs.get('content')
                embedding = kwargs.get('embedding')
                metadata = kwargs.get('metadata')
                
                if not session_id or not role or not content:
                    raise ValueError("缺少必要参数: session_id, role, content")
                
                # 创建 TurnModel 对象
                turn_model = TurnModel(
                    session_id=session_id,
                    role=role,
                    content=content,
                    embedding=embedding,
                    metadata=metadata
                )
                return_dict = True  # 原始方法返回字典
            
            # 使用HTTP JSON API创建轮次
            logger.info(f"异步使用HTTP JSON API创建轮次: {turn_model.id}, 数据: {turn_model.dict()}")
            try:
                await self.client.create_record_async('turns', turn_model.dict())
                
                # 验证轮次记录是否存储成功
                logger.info(f"验证轮次记录存储: SELECT * FROM turns WHERE id = '{turn_model.id}';")
                try:
                    # 使用异步方法而不是同步方法
                    verify_result = await self.client.execute_sql_async_v_new(f"SELECT * FROM turns WHERE id = '{turn_model.id}';")
                    logger.info(f"验证结果: {verify_result}")
                    
                    # 检查验证结果是否包含实际数据
                    if not verify_result or not any(isinstance(r, dict) and r.get('id') == turn_model.id for r in verify_result if isinstance(r, dict)):
                        logger.warning(f"通过HTTP API创建的轮次无法验证，尝试使用直接SQL插入")
                        raise Exception("验证失败，需要使用SQL插入")
                        
                except Exception as verify_error:
                    logger.error(f"验证轮次记录时出错: {verify_error}")
                    raise Exception(f"验证失败: {verify_error}")
                    
            except Exception as api_error:
                # 如果HTTP API创建失败，尝试使用直接SQL插入
                logger.warning(f"HTTP API创建轮次失败，尝试使用直接SQL插入: {api_error}")
                
                # 构建SQL插入语句
                turn_data = turn_model.dict()
                fields = []
                values = []
                
                for key, value in turn_data.items():
                    fields.append(key)
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, (int, float)):
                        values.append(str(value))
                    elif isinstance(value, bool):
                        values.append("true" if value else "false")
                    elif isinstance(value, dict):
                        import json
                        values.append(f"'{json.dumps(value)}'")
                    elif isinstance(value, str) and value == "time::now()":
                        values.append("time::now()")
                    else:
                        values.append(f"'{str(value)}'")
                
                fields_str = ", ".join(fields)
                values_str = ", ".join(values)
                
                # 构建完整的插入语句
                insert_query = f"INSERT INTO turns ({fields_str}) VALUES ({values_str});"
                logger.info(f"执行直接SQL插入: {insert_query}")
                
                # 执行SQL插入
                insert_result = await self.client.execute_sql_async_v_new(insert_query)
                logger.info(f"直接SQL插入结果: {insert_result}")
                
                # 再次验证
                verify_query = f"SELECT * FROM turns WHERE id = '{turn_model.id}';"
                second_verify = await self.client.execute_sql_async_v_new(verify_query)
                if second_verify and isinstance(second_verify, list) and len(second_verify) > 0:
                    if isinstance(second_verify[0], dict) and 'result' in second_verify[0]:
                        if isinstance(second_verify[0]['result'], list) and len(second_verify[0]['result']) > 0:
                            logger.info(f"SQL插入验证成功: {second_verify}")
                        else:
                            logger.warning(f"SQL插入验证返回空结果: {second_verify}")
                    else:
                        logger.warning(f"SQL插入验证返回未知格式: {second_verify}")
                else:
                    logger.warning(f"SQL插入验证失败: {second_verify}")
            
            # 将新创建的轮次添加到内存缓存
            TurnManager._turn_cache[turn_model.id] = turn_model
            
            logger.info(f"轮次异步创建成功: {turn_model.id}")
            
            # 根据调用方式返回不同的结果
            if return_dict:
                return turn_model.dict()  # 返回字典，与原始方法保持一致
            else:
                return turn_model.id  # 返回轮次ID
        except Exception as e:
            logger.error(f"轮次异步创建失败: {e}")
            if return_dict:
                return {}
            else:
                return ""
    
    def delete_session_turns(self, session_id: str) -> int:
        """删除会话的所有轮次
        
        Args:
{{ ... }}
            
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
