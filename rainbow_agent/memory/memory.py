"""
记忆系统的核心实现
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
import json
import os
import numpy as np
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class Memory(ABC):
    """
    记忆系统基类
    
    所有记忆系统实现必须继承此类
    """
    
    @abstractmethod
    def save(self, user_input: str, assistant_response: str, vector: Optional[List[float]] = None) -> None:
        """
        保存对话记录到记忆系统
        
        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            vector: 可选的向量表示，用于向量检索
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
        
    @abstractmethod
    def retrieve_by_vector(self, query_vector: List[float], limit: int = 5) -> List[str]:
        """
        使用向量相似度从记忆系统中检索相关记忆
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        pass
        
    @abstractmethod
    def retrieve_hybrid(self, query: str, query_vector: Optional[List[float]] = None, 
                      limit: int = 5, vector_weight: float = 0.5) -> List[str]:
        """
        混合检索方法，结合关键词和向量相似度
        
        Args:
            query: 查询文本
            query_vector: 查询向量，如果为None则仅使用关键词检索
            limit: 返回结果数量限制
            vector_weight: 向量相似度的权重 (0-1)，越高越重视向量相似度
            
        Returns:
            相关记忆列表
        """
        pass


class SimpleMemory(Memory):
    """
    简单的基于列表的记忆系统
    
    适用于短期对话，不需要持久化存储
    支持向量检索功能
    """
    
    def __init__(self, max_items: int = 100):
        """
        初始化简单记忆系统
        
        Args:
            max_items: 最大保存条目数
        """
        self.memories = []
        self.max_items = max_items
    
    def save(self, user_input: str, assistant_response: str, vector: Optional[List[float]] = None) -> None:
        """保存到内存记忆系统"""
        timestamp = datetime.now().isoformat()
        memory_item = {
            "timestamp": timestamp,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "vector": vector if vector is not None else []
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
        
    def retrieve_by_vector(self, query_vector: List[float], limit: int = 5) -> List[str]:
        """
        使用向量相似度从记忆系统中检索相关记忆
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        # 过滤出带有向量的记忆
        memories_with_vectors = [m for m in self.memories if m.get('vector') and len(m['vector']) > 0]
        
        if not memories_with_vectors:
            return []
            
        # 计算余弦相似度
        similarities = []
        query_vector_np = np.array(query_vector)
        
        for memory in memories_with_vectors:
            memory_vector = np.array(memory['vector'])
            # 余弦相似度计算
            similarity = np.dot(query_vector_np, memory_vector) / (
                np.linalg.norm(query_vector_np) * np.linalg.norm(memory_vector)
            ) if np.linalg.norm(memory_vector) > 0 else 0
            
            similarities.append((memory, similarity))
        
        # 按相似度降序排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 取前 limit 个记忆
        top_memories = [item[0] for item in similarities[:limit]]
        
        # 格式化返回的记忆
        formatted_memories = []
        for memory in top_memories:
            formatted = (
                f"时间: {memory['timestamp']}\n"
                f"用户: {memory['user_input']}\n"
                f"助手: {memory['assistant_response']}"
            )
            formatted_memories.append(formatted)
        
        return formatted_memories
        
    def retrieve_hybrid(self, query: str, query_vector: Optional[List[float]] = None, 
                       limit: int = 5, vector_weight: float = 0.5) -> List[str]:
        """
        混合检索方法，结合关键词和向量相似度
        
        Args:
            query: 查询文本
            query_vector: 查询向量，如果为None则仅使用关键词检索
            limit: 返回结果数量限制
            vector_weight: 向量相似度的权重 (0-1)，越高越重视向量相似度
            
        Returns:
            相关记忆列表
        """
        # 如果没有提供向量，直接使用关键词检索
        if query_vector is None or len(query_vector) == 0:
            return self.retrieve(query, limit)
            
        # 关键词相关度计算 (简单实现，使用字符串匹配)
        keyword_scores = []
        for memory in self.memories:
            # 简单的关键词匹配分数
            user_input = memory['user_input'].lower()
            assistant_response = memory['assistant_response'].lower()
            query_lower = query.lower()
            
            # 计算匹配分数 (简单实现)
            if query_lower in user_input or query_lower in assistant_response:
                keyword_score = 1.0
            else:
                # 计算关键词匹配的比例
                words = query_lower.split()
                if not words:
                    keyword_score = 0.0
                else:
                    matches = sum(1 for word in words if word in user_input or word in assistant_response)
                    keyword_score = matches / len(words)
            
            keyword_scores.append((memory, keyword_score))
        
        # 向量相似度计算
        vector_scores = []
        query_vector_np = np.array(query_vector)
        
        for memory in self.memories:
            memory_vector = memory.get('vector', [])
            if not memory_vector or len(memory_vector) == 0:
                vector_scores.append((memory, 0.0))
                continue
                
            memory_vector_np = np.array(memory_vector)
            # 余弦相似度计算
            similarity = np.dot(query_vector_np, memory_vector_np) / (
                np.linalg.norm(query_vector_np) * np.linalg.norm(memory_vector_np)
            ) if np.linalg.norm(memory_vector_np) > 0 else 0
            
            vector_scores.append((memory, similarity))
        
        # 组合分数
        combined_scores = []
        for i, (memory, keyword_score) in enumerate(keyword_scores):
            _, vector_score = vector_scores[i]
            combined_score = (1 - vector_weight) * keyword_score + vector_weight * vector_score
            combined_scores.append((memory, combined_score))
        
        # 按组合分数降序排序
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 取前 limit 个记忆
        top_memories = [item[0] for item in combined_scores[:limit]]
        
        # 格式化返回的记忆
        formatted_memories = []
        for memory in top_memories:
            formatted = (
                f"时间: {memory['timestamp']}\n"
                f"用户: {memory['user_input']}\n"
                f"助手: {memory['assistant_response']}"
            )
            formatted_memories.append(formatted)
        
        return formatted_memories


# SurrealMemory类已移动到 rainbow_agent/storage/memory.py
