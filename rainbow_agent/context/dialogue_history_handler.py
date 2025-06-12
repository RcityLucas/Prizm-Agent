"""
对话历史上下文处理器

专门处理对话历史类型的上下文，用于保持对话连贯性。
"""

import logging
from typing import Dict, Any, List

from rainbow_agent.context.context_types import ContextType

logger = logging.getLogger(__name__)


class DialogueHistoryHandler:
    """
    对话历史上下文处理器
    
    处理对话历史类型的上下文，提取和规范化对话历史信息，
    用于保持对话的连贯性和上下文理解。
    """
    
    def can_handle(self, context_type: str) -> bool:
        """
        判断是否可以处理指定类型的上下文
        
        Args:
            context_type: 上下文类型字符串
            
        Returns:
            是否可以处理该类型
        """
        return context_type == "dialogue_history" or context_type == ContextType.GENERAL.value
        
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理对话历史上下文
        
        Args:
            context: 原始上下文数据
            
        Returns:
            处理后的对话历史上下文
        """
        if not context:
            return {}
            
        processed = {
            "type": "dialogue_history"
        }
        
        # 提取对话历史
        if "history" in context:
            processed["history"] = self._process_history(context["history"])
        elif "dialogue_history" in context:
            processed["history"] = self._process_history(context["dialogue_history"])
        
        # 从通用上下文中提取对话历史
        elif context.get("type") == ContextType.GENERAL.value and "history" in context:
            processed["history"] = self._process_history(context["history"])
        
        logger.debug(f"处理对话历史上下文: {processed}")
        return processed
        
    def _process_history(self, history: Any) -> List[Dict[str, Any]]:
        """
        处理对话历史数据
        
        Args:
            history: 原始对话历史数据
            
        Returns:
            处理后的对话历史列表
        """
        if not isinstance(history, list):
            return []
            
        # 处理历史记录，最多保留最近的10轮对话
        recent_history = history[-10:] if len(history) > 10 else history
        
        processed = []
        for item in recent_history:
            if isinstance(item, dict):
                # 复制历史项，确保包含必要的字段
                processed_item = {}
                for key, value in item.items():
                    if key.lower() not in ["password", "token", "secret", "credential"]:
                        processed_item[key] = value
                
                # 确保每个历史项都有role和content字段
                if "role" not in processed_item:
                    processed_item["role"] = "unknown"
                if "content" not in processed_item:
                    processed_item["content"] = ""
                    
                processed.append(processed_item)
                
        return processed
