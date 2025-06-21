"""
Core data models for the LangMem package.

This module defines the basic data structures used throughout the LangMem package,
including Memory, MemoryQuery, and RetrievedMemory.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Memory(BaseModel):
    """
    记忆模型，代表系统中存储的一条记忆。
    
    Attributes:
        id: 记忆的唯一标识符，如果为None则由存储系统生成
        content: 记忆的文本内容
        embedding: 记忆内容的向量嵌入表示
        memory_type: 记忆类型，如"default"、"fact"、"conversation"等
        created_at: 记忆创建时间
        metadata: 与记忆相关的额外元数据
    """
    id: Optional[str] = None
    content: str
    embedding: Optional[List[float]] = None
    memory_type: str = "default"  # default, fact, conversation, etc.
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryQuery(BaseModel):
    """
    记忆查询模型，用于检索相关记忆。
    
    Attributes:
        content: 查询的文本内容
        embedding: 查询内容的向量嵌入表示
        filters: 用于过滤记忆的条件
    """
    content: str
    embedding: Optional[List[float]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)


class RetrievedMemory(BaseModel):
    """
    检索到的记忆模型，包含记忆本身和相关度分数。
    
    Attributes:
        memory: 检索到的记忆对象
        relevance: 与查询的相关度分数，范围通常为0到1
    """
    memory: Memory
    relevance: float  # 相关度分数，通常为0到1之间的值
