"""
Rainbow Agent 集成关系网络的增强版代理

将关系管理系统与代理核心功能无缝集成，提供基于关系的上下文感知响应
"""
from typing import List, Dict, Any, Optional, Callable, Union, Tuple, Generator
import logging
import time
import json
import uuid
from datetime import datetime

from .agent import RainbowAgent
from .memory.memory import Memory
from .tools.base import BaseTool
from .relationship import (
    RelationshipSystem,
    RelationshipManager,
    RelationshipStatus,
    RelationshipIntensity,
    default_system as default_relationship_system
)
from .utils.logger import get_logger

logger = get_logger(__name__)


class RelationshipAwareAgent(RainbowAgent):
    """
    关系感知代理 - 集成关系网络的增强版Rainbow Agent
    
    提供基于关系状态的上下文感知响应，动态调整交互风格和内容
    """
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: List[BaseTool] = None,
        memory: Optional[Memory] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tool_calls: int = 5,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        stream: bool = False,
        retry_attempts: int = 2,
        relationship_system: Optional[RelationshipSystem] = None,
        entity_id: Optional[str] = None,
        entity_type: str = "ai"
    ):
        """
        初始化关系感知代理
        
        Args:
            name: 代理的名称
            system_prompt: 系统提示词，用于定义代理的行为和能力
            tools: 代理可以使用的工具列表
            memory: 代理的记忆系统
            model: 使用的LLM模型名称
            temperature: 生成温度，越低越确定性
            max_tool_calls: 单次响应中的最大工具调用次数
            max_tokens: 输出的最大token数量
            timeout: API调用超时时间（秒）
            stream: 是否使用流式输出
            retry_attempts: API调用失败时的重试次数
            relationship_system: 关系系统实例，如果为None则使用默认系统
            entity_id: 代理的实体ID，如果为None则使用代理名称
            entity_type: 代理的实体类型，默认为"ai"
        """
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            tools=tools,
            memory=memory,
            model=model,
            temperature=temperature,
            max_tool_calls=max_tool_calls,
            max_tokens=max_tokens,
            timeout=timeout,
            stream=stream,
            retry_attempts=retry_attempts
        )
        
        # 设置关系系统
        self.relationship_system = relationship_system or default_relationship_system
        
        # 设置代理实体信息
        self.entity_id = entity_id or f"agent_{name}_{str(uuid.uuid4())[:8]}"
        self.entity_type = entity_type
        
        # 添加关系工具
        self._add_relationship_tools()
        
        logger.info(f"关系感知代理 '{name}' (ID: {self.entity_id}) 初始化完成")
    
    def _add_relationship_tools(self):
        """添加关系管理工具到代理"""
        # 获取关系系统提供的工具
        relationship_tools = self.relationship_system.get_tools()
        
        # 添加工具到代理
        for tool in relationship_tools:
            self.add_tool(tool)
            
        logger.info(f"已添加 {len(relationship_tools)} 个关系工具到代理 '{self.name}'")
    
    def _get_relationship_context(self, user_id: str) -> Dict[str, Any]:
        """
        获取与用户的关系上下文
        
        Args:
            user_id: 用户ID
            
        Returns:
            关系上下文信息
        """
        return self.relationship_system.get_relationship_context(
            entity_id=self.entity_id,
            connected_to_id=user_id
        )
    
    def _get_relationship_prompt(self, user_id: str) -> str:
        """
        获取基于关系的提示词
        
        Args:
            user_id: 用户ID
            
        Returns:
            关系提示词
        """
        return self.relationship_system.get_relationship_prompt(
            entity_id=self.entity_id,
            connected_to_id=user_id
        )
    
    def _update_relationship(
        self, 
        user_id: str, 
        message: str, 
        emotional_resonance: bool = False,
        collaboration_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        更新与用户的关系
        
        Args:
            user_id: 用户ID
            message: 消息内容
            emotional_resonance: 是否有情感共鸣
            collaboration_data: 协作数据
            
        Returns:
            更新结果
        """
        metadata = {
            "emotional_resonance": emotional_resonance
        }
        
        if collaboration_data:
            metadata["collaboration"] = collaboration_data
        
        return self.relationship_system.process_message(
            message=message,
            sender_id=self.entity_id,
            sender_type=self.entity_type,
            receiver_id=user_id,
            receiver_type="human",
            metadata=metadata
        )
    
    def _build_prompt(self, user_input: str, user_id: str = "user") -> List[Dict[str, str]]:
        """
        构建包含关系上下文的提示词
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            
        Returns:
            提示消息列表
        """
        # 获取基础提示词
        messages = super()._build_prompt(user_input)
        
        # 获取关系上下文
        relationship_context = self._get_relationship_context(user_id)
        
        # 如果存在关系，添加关系提示词
        if relationship_context.get("exists", False):
            relationship_prompt = self._get_relationship_prompt(user_id)
            
            # 在系统消息后添加关系提示
            for i, msg in enumerate(messages):
                if msg["role"] == "system":
                    # 在原系统消息后添加关系提示
                    messages[i]["content"] += f"\n\n{relationship_prompt}"
                    break
            
            # 添加关系数据作为系统消息
            rel_data = {
                "relationship_level": relationship_context.get("relationship_level", "stranger"),
                "total_interactions": relationship_context.get("total_interaction_rounds", 0),
                "active_days": relationship_context.get("active_days", 0),
                "relationship_intensity": relationship_context.get("ris", 0)
            }
            
            relationship_data_msg = (
                "当前关系数据:\n"
                f"- 关系等级: {rel_data['relationship_level']}\n"
                f"- 互动次数: {rel_data['total_interactions']}\n"
                f"- 活跃天数: {rel_data['active_days']}\n"
                f"- 关系强度: {rel_data['relationship_intensity']:.2f}"
            )
            
            messages.insert(1, {"role": "system", "content": relationship_data_msg})
        
        return messages
    
    def run(self, user_input: str, user_id: str = "user", detect_emotion: bool = True) -> Union[str, Dict[str, Any]]:
        """
        运行代理，处理用户输入并返回响应
        
        Args:
            user_input: 用户输入
            user_id: 用户ID，用于关系管理
            detect_emotion: 是否检测情感
            
        Returns:
            代理响应
        """
        # 构建包含关系上下文的提示词
        messages = self._build_prompt(user_input, user_id)
        
        # 使用父类的核心逻辑处理请求
        start_time = time.time()
        response = super().run(user_input)
        
        # 分析响应中的情感共鸣
        emotional_resonance = False
        if detect_emotion and isinstance(response, str):
            # 简单的情感检测逻辑，实际应用中可以使用更复杂的算法
            emotional_keywords = [
                "理解", "感同身受", "共鸣", "支持", "鼓励", "安慰", 
                "欣赏", "认同", "感谢", "感动", "喜悦", "开心"
            ]
            emotional_resonance = any(keyword in response for keyword in emotional_keywords)
        
        # 更新关系
        collaboration_data = None
        if isinstance(response, dict) and "tool_results" in response:
            # 检查是否有协作相关的工具调用
            tool_calls = response.get("tool_results", [])
            diary_count = sum(1 for t in tool_calls if "diary" in t.get("tool", "").lower())
            co_creation_count = sum(1 for t in tool_calls if "create" in t.get("tool", "").lower())
            
            if diary_count > 0 or co_creation_count > 0:
                collaboration_data = {
                    "diary_count": diary_count,
                    "co_creation_count": co_creation_count,
                    "gift_count": 0  # 默认为0，可以根据实际情况调整
                }
        
        # 更新关系数据
        update_result = self._update_relationship(
            user_id=user_id,
            message=user_input,
            emotional_resonance=emotional_resonance,
            collaboration_data=collaboration_data
        )
        
        # 记录关系更新
        logger.info(f"更新与用户 {user_id} 的关系: {json.dumps(update_result, ensure_ascii=False)}")
        
        # 返回响应
        return response
    
    def get_relationship_summary(self, user_id: str) -> Dict[str, Any]:
        """
        获取与用户的关系摘要
        
        Args:
            user_id: 用户ID
            
        Returns:
            关系摘要
        """
        return self.relationship_system.get_relationship_summary(user_id)
    
    def execute_relationship_tasks(self, user_id: str) -> Dict[str, Any]:
        """
        执行与用户相关的关系任务
        
        Args:
            user_id: 用户ID
            
        Returns:
            任务执行结果
        """
        # 查找关系ID
        rel_id = self.relationship_system.relationship_manager.find_relationship(
            self.entity_id, user_id
        )
        
        if not rel_id:
            return {"error": f"未找到与用户 {user_id} 的关系"}
        
        # 生成关系任务
        task_ids = self.relationship_system.task_manager.generate_tasks_for_relationship(rel_id)
        
        # 获取可执行任务
        executable_tasks = self.relationship_system.get_executable_tasks()
        
        # 异步执行任务
        import asyncio
        
        async def execute_tasks_async():
            return await self.relationship_system.execute_tasks()
        
        # 运行异步任务
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(execute_tasks_async())
        
        return {
            "relationship_id": rel_id,
            "generated_tasks": len(task_ids),
            "executable_tasks": len(executable_tasks),
            "execution_results": results
        }
