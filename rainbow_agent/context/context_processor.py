"""
上下文处理器模块

负责处理、转换和准备上下文数据。
"""

import logging
from typing import Dict, Any, Optional, List
from .context_types import ContextType, ContextConfig

logger = logging.getLogger(__name__)


class ContextProcessor:
    """
    上下文处理器，负责转换和准备上下文
    """
    
    def __init__(self, config: Optional[ContextConfig] = None):
        """
        初始化上下文处理器
        
        Args:
            config: 上下文配置，如果不提供则使用默认配置
        """
        self.config = config or ContextConfig()
        self._handlers = {}  # 类型处理器映射
        
    def register_handler(self, context_type: str, handler):
        """
        注册上下文类型处理器
        
        Args:
            context_type: 上下文类型
            handler: 处理器实例
        """
        self._handlers[context_type] = handler
        logger.debug(f"注册上下文处理器: {context_type}")
        
    def process_context(self, raw_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理原始上下文，返回规范化的上下文
        
        Args:
            raw_context: 原始上下文数据
            
        Returns:
            处理后的上下文数据
        """
        if not raw_context:
            return {}
            
        # 提取上下文类型
        context_type = raw_context.get('type', ContextType.GENERAL.value)
        
        # 验证上下文
        if not self._validate_context(raw_context):
            logger.warning(f"上下文验证失败: {raw_context}")
            return {}
            
        # 使用对应处理器处理
        if context_type in self._handlers:
            try:
                processed = self._handlers[context_type].process(raw_context)
                logger.debug(f"使用专用处理器处理上下文: {context_type}")
                return processed
            except Exception as e:
                logger.error(f"处理上下文时出错: {e}")
                return self._get_safe_context(raw_context)
        
        # 默认处理
        return self._get_safe_context(raw_context)
        
    def filter_context(self, context: Dict[str, Any], context_type: str) -> Dict[str, Any]:
        """
        根据上下文类型过滤上下文内容
        
        Args:
            context: 上下文数据
            context_type: 目标上下文类型
            
        Returns:
            过滤后的上下文
        """
        if not context or 'type' not in context:
            return {}
            
        if context.get('type') == context_type:
            return context
            
        return {}
        
    def _validate_context(self, context: Dict[str, Any]) -> bool:
        """
        验证上下文数据
        
        Args:
            context: 上下文数据
            
        Returns:
            是否有效
        """
        # 基本验证：确保是字典且不为空
        if not context or not isinstance(context, dict):
            return False
            
        # 更多验证规则可以在这里添加
        
        return True
        
    def _get_safe_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取安全的上下文数据（移除潜在的不安全内容）
        
        Args:
            context: 原始上下文
            
        Returns:
            安全的上下文
        """
        # 创建一个副本以避免修改原始数据
        safe_context = context.copy()
        
        # 移除可能的不安全字段
        for key in ['_internal', 'credentials', 'auth', 'password', 'token']:
            if key in safe_context:
                del safe_context[key]
                
        return safe_context
