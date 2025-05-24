# rainbow_agent/core/context_builder.py
from typing import Dict, Any, List, Optional
from ..memory.memory import Memory
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ContextBuilder:
    """
    上下文构建器，负责构建LLM所需的上下文
    """
    
    def __init__(self, memory: Memory, max_context_items: int = 10):
        """
        初始化上下文构建器
        
        Args:
            memory: 记忆系统
            max_context_items: 最大上下文项数量
        """
        self.memory = memory
        self.max_context_items = max_context_items
        
    def build(self, user_input: str, input_type: str = "text") -> Dict[str, Any]:
        """
        构建上下文
        
        Args:
            user_input: 用户输入
            input_type: 输入类型
            
        Returns:
            构建好的上下文字典
        """
        # 获取相关记忆
        relevant_memories = self.memory.retrieve(user_input, limit=self.max_context_items)
        
        # 构建上下文字典
        context = {
            "user_input": user_input,
            "input_type": input_type,
            "relevant_memories": relevant_memories,
            "messages": self._format_as_messages(user_input, relevant_memories)
        }
        
        logger.info(f"上下文构建完成，包含 {len(relevant_memories)} 条相关记忆")
        return context
    
    def add_tool_result(self, context: Dict[str, Any], tool_info: Dict[str, Any], tool_result: str) -> Dict[str, Any]:
        """
        将工具结果添加到上下文
        
        Args:
            context: 原始上下文
            tool_info: 工具信息
            tool_result: 工具执行结果
            
        Returns:
            更新后的上下文
        """
        # 创建工具结果消息
        tool_message = {
            "role": "system",
            "content": f"工具 '{tool_info['tool_name']}' 执行结果:\n{tool_result}"
        }
        
        # 更新消息列表
        updated_messages = context["messages"].copy()
        updated_messages.append(tool_message)
        
        # 创建新的上下文
        updated_context = context.copy()
        updated_context["messages"] = updated_messages
        updated_context["tool_results"] = context.get("tool_results", []) + [{
            "tool_name": tool_info["tool_name"],
            "tool_args": tool_info["tool_args"],
            "result": tool_result
        }]
        
        logger.info(f"上下文更新，添加了工具 '{tool_info['tool_name']}' 的结果")
        return updated_context
    
    def _format_as_messages(self, user_input: str, memories: List[str]) -> List[Dict[str, str]]:
        """
        将上下文格式化为消息列表，适用于LLM API
        """
        messages = []
        
        # 添加系统消息
        messages.append({
            "role": "system",
            "content": "你是Rainbow Agent，一个智能助手。请根据提供的上下文和用户输入提供有帮助的回答。"
        })
        
        # 添加记忆相关信息
        if memories:
            memory_content = "以下是与当前查询相关的信息:\n\n" + "\n\n".join(memories)
            messages.append({
                "role": "system",
                "content": memory_content
            })
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        return messages