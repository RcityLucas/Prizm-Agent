"""
上下文类型定义模块

定义了上下文类型枚举和上下文处理器接口。
"""

from enum import Enum
from typing import Protocol, Dict, Any, Optional


class ContextType(Enum):
    """上下文类型枚举"""
    GENERAL = "general"           # 通用上下文
    USER_PROFILE = "user_profile" # 用户资料
    DOMAIN_KNOWLEDGE = "domain"   # 领域知识
    SYSTEM_STATE = "system"       # 系统状态
    CUSTOM = "custom"             # 自定义


class ContextHandler(Protocol):
    """上下文处理器接口"""
    
    def can_handle(self, context_type: str) -> bool:
        """
        判断是否可以处理指定类型的上下文
        
        Args:
            context_type: 上下文类型字符串
            
        Returns:
            是否可以处理该类型
        """
        ...
        
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理上下文
        
        Args:
            context: 原始上下文数据
            
        Returns:
            处理后的上下文数据
        """
        ...


class ContextConfig:
    """上下文配置"""
    
    def __init__(self, 
                 enable_injection: bool = True,
                 priority_level: str = "medium",
                 max_tokens: int = 1000):
        """
        初始化上下文配置
        
        Args:
            enable_injection: 是否启用上下文注入
            priority_level: 上下文优先级 (low, medium, high)
            max_tokens: 最大上下文标记数
        """
        self.enable_injection = enable_injection
        self.priority_level = priority_level
        self.max_tokens = max_tokens
