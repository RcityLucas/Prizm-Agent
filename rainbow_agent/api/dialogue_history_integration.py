"""
对话历史整合模块

确保对话API正确地整合历史对话上下文到回答中。
"""

import logging
from typing import Dict, Any, List, Optional

from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)


class DialogueHistoryIntegrator:
    """
    对话历史整合器
    
    负责确保对话API正确地整合历史对话上下文到回答中。
    """
    
    def __init__(self, max_history_turns: int = 10):
        """
        初始化对话历史整合器
        
        Args:
            max_history_turns: 最大历史轮次数
        """
        self.max_history_turns = max_history_turns
        logger.info(f"对话历史整合器初始化成功，最大历史轮次: {max_history_turns}")
    
    def prepare_dialogue_context(self, 
                               session_id: str, 
                               turns: List[Dict[str, Any]], 
                               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        准备对话上下文
        
        将对话历史整合到元数据中，确保对话管理器能够使用历史对话上下文。
        
        Args:
            session_id: 会话ID
            turns: 对话历史轮次
            metadata: 原始元数据
            
        Returns:
            包含对话历史的元数据
        """
        # 确保元数据是字典
        if metadata is None:
            metadata = {}
        
        # 如果元数据中已经有context字段，确保它是字典
        if "context" not in metadata:
            metadata["context"] = {}
        elif not isinstance(metadata["context"], dict):
            metadata["context"] = {}
        
        # 将对话历史添加到上下文中
        if turns:
            # 限制历史轮次数量
            recent_turns = turns[-self.max_history_turns:] if len(turns) > self.max_history_turns else turns
            
            # 格式化轮次为符合ContextInjector期望的对话历史格式
            # 创建正确的对话历史上下文结构
            dialogue_history_context = {
                'type': 'dialogue_history',  # 确保类型正确
                'history': []
            }
            
            for turn in recent_turns:
                role = turn.get("role", "unknown")
                content = turn.get("content", "")
                
                # 转换角色名称以符合OpenAI格式
                if role == "human":
                    role = "user"
                elif role == "ai":
                    role = "assistant"
                
                dialogue_history_context['history'].append({
                    "role": role,
                    "content": content
                })
            
            # 添加到上下文中，确保键名与ContextInjector期望的一致
            metadata["context"]["dialogue_history"] = dialogue_history_context
            metadata["context"]["session_id"] = session_id
            
            logger.info(f"对话历史已整合到上下文中，会话ID: {session_id}, 历史轮次数: {len(dialogue_history_context['history'])}")
        
        logger.debug(f"已准备对话上下文，会话ID: {session_id}, 历史轮次数: {len(turns) if turns else 0}")
        return metadata
    
    def ensure_history_in_prompt(self, prompt: str, turns: List[Dict[str, Any]]) -> str:
        """
        确保对话历史在提示中
        
        如果提示中没有包含对话历史，则添加对话历史。
        
        Args:
            prompt: 原始提示
            turns: 对话历史轮次
            
        Returns:
            包含对话历史的提示
        """
        # 如果没有历史轮次，直接返回原始提示
        if not turns:
            return prompt
        
        # 限制历史轮次数量
        recent_turns = turns[-self.max_history_turns:] if len(turns) > self.max_history_turns else turns
        
        # 检查提示中是否已经包含对话历史
        if "对话历史:" in prompt or "Dialogue History:" in prompt:
            return prompt
        
        # 构建对话历史文本
        history_text = "\n对话历史:\n"
        for turn in recent_turns:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")
            
            # 转换角色名称
            if role == "user":
                role_name = "用户"
            elif role == "assistant":
                role_name = "AI"
            else:
                role_name = role
                
            history_text += f"{role_name}: {content}\n"
        
        # 在提示开头添加对话历史
        enhanced_prompt = history_text + "\n" + prompt
        
        return enhanced_prompt
