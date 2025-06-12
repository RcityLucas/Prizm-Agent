"""
对话管理器上下文增强模块

为DialogueManager添加上下文处理和注入功能。
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..context.context_processor import ContextProcessor
from ..context.context_injector import ContextInjector
from ..context.context_types import ContextConfig

logger = logging.getLogger(__name__)


class DialogueManagerContextMixin:
    """
    对话管理器上下文增强混入类
    
    为DialogueManager添加上下文处理和注入功能。
    """
    
    def __init__(self, 
                 context_processor: Optional[ContextProcessor] = None,
                 context_injector: Optional[ContextInjector] = None,
                 context_config: Optional[ContextConfig] = None):
        """
        初始化上下文增强混入类
        
        Args:
            context_processor: 上下文处理器，如果不提供则创建新实例
            context_injector: 上下文注入器，如果不提供则创建新实例
            context_config: 上下文配置，如果不提供则使用默认配置
        """
        self._context_config = context_config or ContextConfig()
        self._context_processor = context_processor or ContextProcessor(self._context_config)
        self._context_injector = context_injector or ContextInjector(self._context_config)
        
        logger.info("对话管理器上下文增强功能初始化成功")
        
    def process_context(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理上下文元数据
        
        Args:
            metadata: 原始元数据
            
        Returns:
            处理后的上下文数据
        """
        if not metadata or not self._context_config.enable_injection:
            return {}
            
        try:
            return self._context_processor.process_context(metadata)
        except Exception as e:
            logger.error(f"处理上下文时出错: {e}")
            return {}
            
    def inject_context_to_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        将上下文注入到提示中
        
        Args:
            prompt: 原始提示文本
            context: 处理后的上下文数据
            
        Returns:
            注入上下文后的提示文本
        """
        if not context or not self._context_config.enable_injection:
            return prompt
            
        try:
            return self._context_injector.inject_context_to_prompt(prompt, context)
        except Exception as e:
            logger.error(f"注入上下文到提示时出错: {e}")
            return prompt
            
    def inject_context_to_history(self, history: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """
        将上下文注入到对话历史中
        
        Args:
            history: 对话历史记录
            context: 处理后的上下文数据
            
        Returns:
            注入上下文后的对话历史
        """
        if not context or not self._context_config.enable_injection:
            return history
            
        try:
            return self._context_injector.inject_context_to_history(history, context)
        except Exception as e:
            logger.error(f"注入上下文到历史时出错: {e}")
            return history
            
    def build_prompt_with_context(self, 
                                 turns: List[Dict[str, Any]], 
                                 metadata: Optional[Dict[str, Any]]) -> str:
        """
        构建包含上下文的提示
        
        Args:
            turns: 对话历史轮次
            metadata: 元数据（可能包含上下文）
            
        Returns:
            包含上下文的提示文本
        """
        # 构建基础提示
        base_prompt = self._build_prompt(turns)
        
        # 处理上下文
        processed_context = self.process_context(metadata)
        
        # 注入上下文
        return self.inject_context_to_prompt(base_prompt, processed_context)
        
    def get_context_metadata(self, processed_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取上下文元数据（用于响应）
        
        Args:
            processed_context: 处理后的上下文
            
        Returns:
            上下文元数据
        """
        if not processed_context:
            return {"context_used": False}
            
        return {
            "context_used": True,
            "context_type": processed_context.get("type", "general"),
            "context_processed_at": datetime.now().isoformat()
        }
