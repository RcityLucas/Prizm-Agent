"""
用户资料上下文处理器

专门处理用户资料类型的上下文，用于个性化对话体验。
"""

import logging
from typing import Dict, Any

from rainbow_agent.context.context_types import ContextType

logger = logging.getLogger(__name__)


class UserProfileHandler:
    """
    用户资料上下文处理器
    
    处理用户资料类型的上下文，提取和规范化用户信息，
    用于个性化对话体验。
    """
    
    def can_handle(self, context_type: str) -> bool:
        """
        判断是否可以处理指定类型的上下文
        
        Args:
            context_type: 上下文类型字符串
            
        Returns:
            是否可以处理该类型
        """
        return context_type == ContextType.USER_PROFILE.value
        
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户资料上下文
        
        Args:
            context: 原始上下文数据
            
        Returns:
            处理后的用户资料上下文
        """
        if not context:
            return {}
            
        processed = {
            "type": ContextType.USER_PROFILE.value
        }
        
        # 提取基本用户信息
        if "user_info" in context:
            processed["user_info"] = self._process_user_info(context["user_info"])
            
        # 提取用户偏好
        if "preferences" in context:
            processed["preferences"] = self._process_preferences(context["preferences"])
            
        # 提取用户位置
        if "location" in context:
            processed["location"] = self._process_location(context["location"])
            
        # 提取用户历史行为
        if "history" in context:
            processed["history"] = self._process_history(context["history"])
            
        logger.debug(f"处理用户资料上下文: {processed}")
        return processed
        
    def _process_user_info(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户基本信息
        
        Args:
            user_info: 原始用户信息
            
        Returns:
            处理后的用户信息
        """
        if not isinstance(user_info, dict):
            return {}
            
        # 复制基本信息，过滤敏感字段
        processed = {}
        for key, value in user_info.items():
            # 过滤敏感字段
            if key.lower() not in ["password", "token", "secret", "credential"]:
                processed[key] = value
                
        return processed
        
    def _process_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户偏好
        
        Args:
            preferences: 原始用户偏好
            
        Returns:
            处理后的用户偏好
        """
        if not isinstance(preferences, dict):
            return {}
            
        # 复制偏好信息
        return preferences.copy()
        
    def _process_location(self, location: Any) -> Dict[str, Any]:
        """
        处理用户位置信息
        
        Args:
            location: 原始位置信息
            
        Returns:
            处理后的位置信息
        """
        if isinstance(location, str):
            # 如果是字符串，假设是城市名
            return {"city": location}
        elif isinstance(location, dict):
            # 如果是字典，保留有用的位置信息
            processed = {}
            for key in ["city", "province", "country", "latitude", "longitude"]:
                if key in location:
                    processed[key] = location[key]
            return processed
        else:
            return {}
            
    def _process_history(self, history: Any) -> list:
        """
        处理用户历史行为
        
        Args:
            history: 原始历史行为数据
            
        Returns:
            处理后的历史行为列表
        """
        if not isinstance(history, list):
            return []
            
        # 处理历史记录，最多保留最近的10条
        recent_history = history[-10:] if len(history) > 10 else history
        
        processed = []
        for item in recent_history:
            if isinstance(item, dict):
                # 复制历史项，过滤敏感字段
                processed_item = {}
                for key, value in item.items():
                    if key.lower() not in ["password", "token", "secret", "credential"]:
                        processed_item[key] = value
                processed.append(processed_item)
                
        return processed
