"""
格式化工具模块

提供各种格式化功能，如对话历史格式化等
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def format_dialogue_history(history: List[Dict[str, Any]], 
                           system_prompt: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    格式化对话历史为OpenAI API所需的格式
    
    Args:
        history: 对话历史列表，每项包含role和content
        system_prompt: 可选的系统提示
        
    Returns:
        格式化后的对话消息列表
    """
    formatted_messages = []
    
    # 添加系统提示（如果有）
    if system_prompt:
        formatted_messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    # 添加对话历史
    for message in history:
        # 确保消息有必要的字段
        if "role" not in message or "content" not in message:
            logger.warning(f"跳过格式不正确的消息: {message}")
            continue
            
        # 将角色映射为OpenAI API支持的角色
        role = message["role"].lower()
        if role in ["user", "assistant", "system"]:
            # OpenAI API支持的角色，直接使用
            formatted_role = role
        elif role in ["human", "user_proxy"]:
            # 映射为用户角色
            formatted_role = "user"
        elif role in ["ai", "bot", "agent"]:
            # 映射为助手角色
            formatted_role = "assistant"
        else:
            # 默认映射为用户角色
            logger.warning(f"未知角色 '{role}'，默认映射为'user'")
            formatted_role = "user"
            
        # 添加格式化后的消息
        formatted_messages.append({
            "role": formatted_role,
            "content": message["content"]
        })
    
    return formatted_messages
