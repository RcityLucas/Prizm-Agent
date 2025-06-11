# examples/mock_memory_sync.py
"""
为演示脚本定制的记忆同步组件，与MockMemory兼容
"""
from typing import Dict, Any, List, Optional
import time
import json
import asyncio
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)

class MockMemorySync:
    """
    为演示脚本定制的记忆同步组件，与MockMemory兼容
    """
    
    def __init__(self, memory, config: Optional[Dict[str, Any]] = None):
        """
        初始化记忆同步组件
        
        Args:
            memory: 记忆系统接口
            config: 配置参数，包含同步策略、记忆类型等
        """
        self.memory = memory
        self.config = config or {}
        
        # 记忆类型前缀
        self.memory_type_prefix = self.config.get("memory_type_prefix", "frequency_sense")
        
        # 同步间隔（秒）
        self.sync_interval = self.config.get("sync_interval", 300)  # 默认5分钟
        
        # 上次同步时间
        self.last_sync_time = 0
        
        # 待同步的数据缓冲
        self.sync_buffer = []
        
        # 缓冲区大小限制
        self.buffer_size_limit = self.config.get("buffer_size_limit", 50)
        
        logger.info("记忆同步组件初始化完成")
    
    async def record_expression(self, expression_info: Dict[str, Any], user_id: str) -> bool:
        """
        记录表达信息到记忆系统
        
        Args:
            expression_info: 表达信息
            user_id: 用户ID
            
        Returns:
            是否成功记录
        """
        # 构建记忆内容
        memory_content = {
            "type": f"{self.memory_type_prefix}_expression",
            "timestamp": time.time(),
            "user_id": user_id,
            "expression_type": expression_info["content"]["type"],
            "expression_content": expression_info["final_content"],
            "priority_score": expression_info.get("priority_score", 0.5),
            "relationship_stage": expression_info.get("relationship_stage", "unknown")
        }
        
        # 添加到同步缓冲
        self.sync_buffer.append(memory_content)
        
        # 检查是否需要同步
        if len(self.sync_buffer) >= self.buffer_size_limit or \
           time.time() - self.last_sync_time >= self.sync_interval:
            return await self.sync_to_memory()
        
        return True
    
    async def record_context_sample(self, sample: Dict[str, Any], user_id: str) -> bool:
        """
        记录上下文采样信息到记忆系统
        
        Args:
            sample: 采样信息
            user_id: 用户ID
            
        Returns:
            是否成功记录
        """
        # 构建记忆内容
        memory_content = {
            "type": f"{self.memory_type_prefix}_sample",
            "timestamp": time.time(),
            "user_id": user_id,
            "priority_score": sample.get("priority_score", 0.5),
            "signals": {
                "user_activity": sample["signals"]["user_activity"].get("score", 0),
                "time_elapsed": sample["signals"]["time_elapsed"].get("score", 0),
                "conversation_context": sample["signals"]["conversation_context"].get("score", 0),
                "system_state": sample["signals"]["system_state"].get("score", 0),
                "external_events": sample["signals"]["external_events"].get("score", 0)
            }
        }
        
        # 添加到同步缓冲
        self.sync_buffer.append(memory_content)
        
        # 检查是否需要同步
        if len(self.sync_buffer) >= self.buffer_size_limit or \
           time.time() - self.last_sync_time >= self.sync_interval:
            return await self.sync_to_memory()
        
        return True
    
    async def record_user_preference(self, preference: Dict[str, Any], user_id: str) -> bool:
        """
        记录用户偏好信息到记忆系统
        
        Args:
            preference: 用户偏好信息
            user_id: 用户ID
            
        Returns:
            是否成功记录
        """
        # 构建记忆内容
        memory_content = {
            "type": f"{self.memory_type_prefix}_preference",
            "timestamp": time.time(),
            "user_id": user_id,
            "preference_type": preference.get("type", "unknown"),
            "preference_value": preference.get("value"),
            "preference_strength": preference.get("strength", 0.5)
        }
        
        # 添加到同步缓冲
        self.sync_buffer.append(memory_content)
        
        # 检查是否需要同步
        if len(self.sync_buffer) >= self.buffer_size_limit or \
           time.time() - self.last_sync_time >= self.sync_interval:
            return await self.sync_to_memory()
        
        return True
    
    async def sync_to_memory(self) -> bool:
        """
        将缓冲区中的数据同步到记忆系统
        
        Returns:
            是否成功同步
        """
        if not self.sync_buffer:
            logger.debug("同步缓冲区为空，无需同步")
            return True
        
        try:
            # 批量存储到记忆系统
            for item in self.sync_buffer:
                collection = item["type"]
                await self.memory.store(collection, item)
            
            # 清空缓冲区
            buffer_size = len(self.sync_buffer)
            self.sync_buffer = []
            
            # 更新同步时间
            self.last_sync_time = time.time()
            
            logger.info(f"成功同步{buffer_size}条记忆到记忆系统")
            return True
            
        except Exception as e:
            logger.error(f"同步记忆错误: {e}")
            return False
    
    async def retrieve_user_preferences(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        从记忆系统中检索用户偏好
        
        Args:
            user_id: 用户ID
            limit: 限制返回的记录数量
            
        Returns:
            用户偏好列表
        """
        try:
            # 构建查询
            collection = f"{self.memory_type_prefix}_preference"
            query = {"user_id": user_id}
            
            # 从记忆系统中检索
            results = await self.memory.retrieve_data(collection, query)
            
            # 限制结果数量
            preferences = results[:limit] if len(results) > limit else results
            
            logger.info(f"从记忆系统中检索到{len(preferences)}条用户偏好")
            return preferences
            
        except Exception as e:
            logger.error(f"检索用户偏好错误: {e}")
            return []
    
    async def retrieve_expression_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        从记忆系统中检索表达历史
        
        Args:
            user_id: 用户ID
            limit: 限制返回的记录数量
            
        Returns:
            表达历史列表
        """
        try:
            # 构建查询
            collection = f"{self.memory_type_prefix}_expression"
            query = {"user_id": user_id}
            
            # 从记忆系统中检索
            results = await self.memory.retrieve_data(collection, query)
            
            # 限制结果数量
            expressions = results[:limit] if len(results) > limit else results
            
            logger.info(f"从记忆系统中检索到{len(expressions)}条表达历史")
            return expressions
            
        except Exception as e:
            logger.error(f"检索表达历史错误: {e}")
            return []
    
    async def retrieve_context_samples(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        从记忆系统中检索上下文采样历史
        
        Args:
            user_id: 用户ID
            limit: 限制返回的记录数量
            
        Returns:
            上下文采样历史列表
        """
        try:
            # 构建查询
            collection = f"{self.memory_type_prefix}_sample"
            query = {"user_id": user_id}
            
            # 从记忆系统中检索
            results = await self.memory.retrieve_data(collection, query)
            
            # 限制结果数量
            samples = results[:limit] if len(results) > limit else results
            
            logger.info(f"从记忆系统中检索到{len(samples)}条上下文采样历史")
            return samples
            
        except Exception as e:
            logger.error(f"检索上下文采样历史错误: {e}")
            return []
    
    async def update_user_interaction_count(self, user_id: str, increment: int = 1) -> bool:
        """
        更新用户互动次数
        
        Args:
            user_id: 用户ID
            increment: 增加的次数
            
        Returns:
            是否成功更新
        """
        try:
            # 构建查询
            collection = "users"
            query = {"_id": user_id}
            
            # 从记忆系统中检索用户信息
            results = await self.memory.retrieve_data(collection, query)
            
            user_info = None
            if results and len(results) > 0:
                user_info = results[0]
            
            if user_info is None:
                # 创建新的用户信息
                user_info = {
                    "_id": user_id,
                    "name": "用户",
                    "interaction_count": increment,
                    "preferences": {},
                    "topics_of_interest": []
                }
                # 存储新用户信息
                await self.memory.store(collection, user_info)
            else:
                # 更新互动次数
                current_count = user_info.get("interaction_count", 0)
                user_info["interaction_count"] = current_count + increment
                # 更新用户信息
                await self.memory.update(collection, user_id, {"interaction_count": user_info["interaction_count"]})
            
            logger.info(f"成功更新用户互动次数，用户ID: {user_id}, 当前次数: {user_info['interaction_count']}")
            return True
            
        except Exception as e:
            logger.error(f"更新用户互动次数错误: {e}")
            return False
