"""
位置上下文处理器

专门处理位置类型的上下文，用于基于位置的个性化对话体验。
"""

import logging
from typing import Dict, Any

from rainbow_agent.context.context_types import ContextType

logger = logging.getLogger(__name__)


class LocationHandler:
    """
    位置上下文处理器
    
    处理位置类型的上下文，提取和规范化位置信息，
    用于基于位置的个性化对话体验。
    """
    
    def can_handle(self, context_type: str) -> bool:
        """
        判断是否可以处理指定类型的上下文
        
        Args:
            context_type: 上下文类型字符串
            
        Returns:
            是否可以处理该类型
        """
        return context_type == "location" or context_type == ContextType.GENERAL.value
        
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理位置上下文
        
        Args:
            context: 原始上下文数据
            
        Returns:
            处理后的位置上下文
        """
        if not context:
            return {}
            
        processed = {
            "type": "location"
        }
        
        # 直接提取位置字段
        if "location" in context:
            processed["location"] = self._process_location_data(context["location"])
        
        # 从通用上下文中提取位置信息
        elif context.get("type") == ContextType.GENERAL.value:
            for key in ["location", "city", "province", "country", "coordinates"]:
                if key in context:
                    processed[key] = context[key]
        
        logger.debug(f"处理位置上下文: {processed}")
        return processed
        
    def _process_location_data(self, location_data: Any) -> Dict[str, Any]:
        """
        处理位置数据
        
        Args:
            location_data: 原始位置数据
            
        Returns:
            处理后的位置数据
        """
        if isinstance(location_data, str):
            # 如果是字符串，假设是城市名
            return {"city": location_data}
        elif isinstance(location_data, dict):
            # 如果是字典，保留有用的位置信息
            processed = {}
            for key in ["city", "province", "country", "latitude", "longitude", "address"]:
                if key in location_data:
                    processed[key] = location_data[key]
            return processed
        else:
            return {}
