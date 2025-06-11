# rainbow_agent/frequency/memory_sync.py
"""
记忆同步组件，负责将频率感知系统的状态和决策记录到记忆系统中
"""
from typing import Dict, Any, List, Optional
import time
import json
from ..utils.logger import get_logger
from ..memory.memory import Memory

logger = get_logger(__name__)

class MemorySync:
    """
    记忆同步组件，负责将频率感知系统的状态和决策记录到记忆系统中，
    并从记忆系统中检索相关信息用于频率感知决策
    """
    
    def __init__(self, memory: Memory, config: Optional[Dict[str, Any]] = None):
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
            "type": f"{self.memory_type_prefix}_user_preference",
            "timestamp": time.time(),
            "user_id": user_id,
            "preference_type": preference.get("type", "general"),
            "preference_value": preference.get("value"),
            "confidence": preference.get("confidence", 0.5)
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
            # 批量存储记忆
            for memory_content in self.sync_buffer:
                memory_type = memory_content["type"]
                user_id = memory_content["user_id"]
                
                # 构建记忆ID
                memory_id = f"{memory_type}:{user_id}:{int(time.time() * 1000)}"
                
                # 将记忆内容转换为JSON字符串
                memory_json = json.dumps(memory_content)
                
                # 存储到记忆系统
                await self.memory.store(
                    memory_id,
                    memory_json,
                    memory_type=memory_type,
                    metadata={
                        "user_id": user_id,
                        "timestamp": memory_content["timestamp"]
                    }
                )
            
            # 清空缓冲区
            self.sync_buffer = []
            
            # 更新同步时间
            self.last_sync_time = time.time()
            
            logger.info(f"成功同步{len(self.sync_buffer)}条记忆到记忆系统")
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
            query = f"{self.memory_type_prefix}_user_preference:user_id:{user_id}"
            
            # 从记忆系统中检索
            results = await self.memory.retrieve(query, limit=limit)
            
            # 解析结果
            preferences = []
            for result in results:
                if isinstance(result, str):
                    try:
                        # 尝试解析JSON
                        preference = json.loads(result)
                        preferences.append(preference)
                    except:
                        logger.warning(f"无法解析用户偏好记忆: {result}")
                elif isinstance(result, dict):
                    preferences.append(result)
            
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
            query = f"{self.memory_type_prefix}_expression:user_id:{user_id}"
            
            # 从记忆系统中检索
            results = await self.memory.retrieve(query, limit=limit)
            
            # 解析结果
            expressions = []
            for result in results:
                if isinstance(result, str):
                    try:
                        # 尝试解析JSON
                        expression = json.loads(result)
                        expressions.append(expression)
                    except:
                        logger.warning(f"无法解析表达历史记忆: {result}")
                elif isinstance(result, dict):
                    expressions.append(result)
            
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
            query = f"{self.memory_type_prefix}_sample:user_id:{user_id}"
            
            # 从记忆系统中检索
            results = await self.memory.retrieve(query, limit=limit)
            
            # 解析结果
            samples = []
            for result in results:
                if isinstance(result, str):
                    try:
                        # 尝试解析JSON
                        sample = json.loads(result)
                        samples.append(sample)
                    except:
                        logger.warning(f"无法解析上下文采样记忆: {result}")
                elif isinstance(result, dict):
                    samples.append(result)
            
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
            query = f"user_info:{user_id}"
            
            # 从记忆系统中检索用户信息
            results = await self.memory.retrieve(query, limit=1)
            
            user_info = None
            if results and len(results) > 0:
                # 解析用户信息
                if isinstance(results[0], str):
                    try:
                        user_info = json.loads(results[0])
                    except:
                        logger.warning(f"无法解析用户信息: {results[0]}")
                elif isinstance(results[0], dict):
                    user_info = results[0]
            
            if user_info is None:
                # 创建新的用户信息
                user_info = {
                    "id": user_id,
                    "name": "用户",
                    "interaction_count": increment,
                    "preferences": {},
                    "topics_of_interest": []
                }
            else:
                # 更新互动次数
                current_count = user_info.get("interaction_count", 0)
                user_info["interaction_count"] = current_count + increment
            
            # 存储更新后的用户信息
            await self.memory.store(
                f"user_info:{user_id}",
                json.dumps(user_info),
                memory_type="user_info",
                metadata={"user_id": user_id}
            )
            
            logger.info(f"成功更新用户互动次数，用户ID: {user_id}, 当前次数: {user_info['interaction_count']}")
            return True
            
        except Exception as e:
            logger.error(f"更新用户互动次数错误: {e}")
            return False
