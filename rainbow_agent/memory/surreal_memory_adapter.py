"""
SurrealDB记忆适配器

将SurrealMemory适配到Memory接口，确保兼容性
"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from .memory import Memory
from ..storage.memory import SurrealMemory as BaseSurrealMemory
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SurrealMemoryAdapter(Memory):
    """
    SurrealDB记忆适配器
    
    将现有的SurrealMemory适配到Memory接口，确保兼容性
    """
    
    def __init__(self, surreal_memory: BaseSurrealMemory, session_id: str):
        """
        初始化SurrealMemory适配器
        
        Args:
            surreal_memory: 现有的SurrealMemory实例
            session_id: 会话ID
        """
        self.memory = surreal_memory
        self.session_id = session_id
        logger.info(f"SurrealMemoryAdapter初始化完成，会话ID: {session_id}")
    
    def save(self, user_input: str, assistant_response: str) -> None:
        """
        保存对话记录到记忆系统
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
        """
        timestamp = datetime.now().isoformat()
        memory_item = {
            "timestamp": timestamp,
            "user_input": user_input,
            "assistant_response": assistant_response
        }
        
        # 使用现有SurrealMemory的add方法
        self.memory.add(self.session_id, memory_item)
        logger.info(f"对话记录已保存到会话 {self.session_id}")
    
    def retrieve(self, query: str, limit: int = 5) -> List[str]:
        """
        从记忆系统中检索相关记忆
        
        Args:
            query: 查询文本
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        # 如果有查询文本，使用search方法
        if query and query.strip():
            raw_memories = self.memory.search(self.session_id, query, limit)
        else:
            # 否则使用get方法获取最近的记忆
            raw_memories = self.memory.get(self.session_id, limit)
        
        # 格式化返回的记忆
        formatted_memories = []
        for memory in raw_memories:
            # 检查记忆格式是否符合预期
            if "user_input" in memory and "assistant_response" in memory:
                formatted = (
                    f"用户: {memory['user_input']}\n"
                    f"助手: {memory['assistant_response']}"
                )
                formatted_memories.append(formatted)
        
        logger.info(f"从会话 {self.session_id} 检索到 {len(formatted_memories)} 条记忆")
        return formatted_memories
