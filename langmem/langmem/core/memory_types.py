"""
Memory type definitions for the LangMem package.

This module defines the different types of memories that can be stored in the system,
along with their characteristics and behaviors.
"""

from enum import Enum, auto
from typing import Dict, Any


class MemoryType(str, Enum):
    """
    记忆类型枚举，定义系统支持的不同类型的记忆。
    
    使用str作为基类使得这些枚举值可以直接用作字符串，
    同时保持类型安全和IDE自动完成功能。
    """
    DEFAULT = "default"  # 默认记忆类型
    FACT = "fact"  # 事实性记忆，如用户偏好、背景信息等
    CONVERSATION = "conversation"  # 对话记忆，包含用户和AI的对话内容
    EVENT = "event"  # 事件记忆，记录重要事件
    EMOTIONAL = "emotional"  # 情感记忆，与情感相关的信息
    RELATIONSHIP = "relationship"  # 关系记忆，记录实体间的关系


class MemoryTypeProperties:
    """
    记忆类型属性管理器，定义不同类型记忆的特性和行为。
    """
    
    # 记忆类型的默认属性
    DEFAULT_PROPERTIES = {
        "retention_period": 30,  # 默认保留30天
        "importance_threshold": 0.3,  # 默认重要性阈值
        "retrieval_weight": 1.0,  # 默认检索权重
    }
    
    # 不同记忆类型的特定属性
    TYPE_PROPERTIES = {
        MemoryType.DEFAULT: DEFAULT_PROPERTIES,
        MemoryType.FACT: {
            "retention_period": 365,  # 事实记忆保留更长时间
            "importance_threshold": 0.2,  # 事实记忆更容易被保留
            "retrieval_weight": 1.2,  # 事实记忆在检索时有更高权重
        },
        MemoryType.CONVERSATION: {
            "retention_period": 14,  # 对话记忆保留较短时间
            "importance_threshold": 0.4,  # 对话记忆需要更高重要性才被保留
            "retrieval_weight": 0.9,  # 对话记忆在检索时有稍低权重
        },
        MemoryType.EVENT: {
            "retention_period": 180,  # 事件记忆保留较长时间
            "importance_threshold": 0.25,  # 事件记忆较容易被保留
            "retrieval_weight": 1.1,  # 事件记忆在检索时有较高权重
        },
        MemoryType.EMOTIONAL: {
            "retention_period": 90,  # 情感记忆保留中等时间
            "importance_threshold": 0.3,  # 情感记忆有中等保留阈值
            "retrieval_weight": 1.3,  # 情感记忆在检索时有较高权重
        },
        MemoryType.RELATIONSHIP: {
            "retention_period": 365,  # 关系记忆保留较长时间
            "importance_threshold": 0.2,  # 关系记忆较容易被保留
            "retrieval_weight": 1.2,  # 关系记忆在检索时有较高权重
        },
    }
    
    @classmethod
    def get_properties(cls, memory_type: str) -> Dict[str, Any]:
        """
        获取指定记忆类型的属性。
        
        Args:
            memory_type: 记忆类型，可以是MemoryType枚举值或字符串
            
        Returns:
            记忆类型的属性字典
        """
        # 如果memory_type是MemoryType枚举，转换为字符串
        if isinstance(memory_type, MemoryType):
            memory_type = memory_type.value
            
        # 尝试获取指定类型的属性，如果不存在则返回默认属性
        try:
            return cls.TYPE_PROPERTIES.get(
                MemoryType(memory_type), 
                cls.DEFAULT_PROPERTIES
            )
        except ValueError:
            # 如果memory_type不是有效的MemoryType枚举值，返回默认属性
            return cls.DEFAULT_PROPERTIES
    
    @classmethod
    def get_retention_period(cls, memory_type: str) -> int:
        """
        获取指定记忆类型的保留期限（天）。
        
        Args:
            memory_type: 记忆类型
            
        Returns:
            保留期限（天）
        """
        return cls.get_properties(memory_type)["retention_period"]
    
    @classmethod
    def get_importance_threshold(cls, memory_type: str) -> float:
        """
        获取指定记忆类型的重要性阈值。
        
        Args:
            memory_type: 记忆类型
            
        Returns:
            重要性阈值（0到1之间的浮点数）
        """
        return cls.get_properties(memory_type)["importance_threshold"]
    
    @classmethod
    def get_retrieval_weight(cls, memory_type: str) -> float:
        """
        获取指定记忆类型的检索权重。
        
        Args:
            memory_type: 记忆类型
            
        Returns:
            检索权重（通常为0到2之间的浮点数）
        """
        return cls.get_properties(memory_type)["retrieval_weight"]
