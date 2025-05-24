"""
记忆系统的核心实现
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class Memory(ABC):
    """
    记忆系统基类
    
    所有记忆系统实现必须继承此类
    """
    
    @abstractmethod
    def save(self, user_input: str, assistant_response: str) -> None:
        """
        保存对话记录到记忆系统
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
        """
        pass
    
    @abstractmethod
    def retrieve(self, query: str, limit: int = 5) -> List[str]:
        """
        从记忆系统中检索相关记忆
        
        Args:
            query: 查询文本
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        pass


class SimpleMemory(Memory):
    """
    简单的基于列表的记忆系统
    
    适用于短期对话，不需要持久化存储
    """
    
    def __init__(self, max_items: int = 100):
        """
        初始化简单记忆系统
        
        Args:
            max_items: 最大保存条目数
        """
        self.memories = []
        self.max_items = max_items
    
    def save(self, user_input: str, assistant_response: str) -> None:
        """保存到内存记忆系统"""
        timestamp = datetime.now().isoformat()
        memory_item = {
            "timestamp": timestamp,
            "user_input": user_input,
            "assistant_response": assistant_response
        }
        
        self.memories.append(memory_item)
        
        # 保持记忆列表在最大长度以内
        if len(self.memories) > self.max_items:
            self.memories = self.memories[-self.max_items:]
    
    def retrieve(self, query: str, limit: int = 5) -> List[str]:
        """检索相关记忆 (简单实现: 返回最近的n条)"""
        recent_memories = self.memories[-limit:] if self.memories else []
        
        # 格式化返回的记忆
        formatted_memories = []
        for memory in recent_memories:
            formatted = (
                f"时间: {memory['timestamp']}\n"
                f"用户: {memory['user_input']}\n"
                f"助手: {memory['assistant_response']}"
            )
            formatted_memories.append(formatted)
        
        return formatted_memories


# SurrealMemory类已移动到 rainbow_agent/storage/memory.py
