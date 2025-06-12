"""
上下文注入器模块

负责将处理后的上下文注入到AI对话中。
"""

import logging
from typing import Dict, Any, List, Optional
from .context_types import ContextConfig

logger = logging.getLogger(__name__)


class ContextInjector:
    """
    上下文注入器，负责将上下文注入到AI对话中
    """
    
    def __init__(self, config: Optional[ContextConfig] = None):
        """
        初始化上下文注入器
        
        Args:
            config: 上下文配置，如果不提供则使用默认配置
        """
        self.config = config or ContextConfig()
        
    def inject_context_to_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        将上下文注入到提示中
        
        Args:
            prompt: 原始提示文本
            context: 上下文数据
            
        Returns:
            注入上下文后的提示文本
        """
        if not context or not self.config.enable_injection:
            return prompt
            
        # 构建上下文前缀
        context_prefix = self._build_context_prefix(context)
        if not context_prefix:
            return prompt
            
        # 注入上下文
        return f"{context_prefix}\n\n{prompt}"
        
    def inject_context_to_messages(self, messages: List[Dict[str, str]], context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        将上下文注入到消息列表中
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            context: 上下文数据
            
        Returns:
            注入上下文后的消息列表
        """
        if not context or not self.config.enable_injection:
            return messages
            
        # 构建上下文前缀
        context_prefix = self._build_context_prefix(context)
        if not context_prefix:
            return messages
            
        # 创建新的消息列表
        new_messages = messages.copy()
        
        # 检查是否已有系统消息
        system_message_index = None
        for i, msg in enumerate(new_messages):
            if msg.get("role") == "system":
                system_message_index = i
                break
                
        if system_message_index is not None:
            # 更新现有的系统消息
            current_content = new_messages[system_message_index]["content"]
            new_messages[system_message_index]["content"] = f"{context_prefix}\n\n{current_content}"
        else:
            # 添加新的系统消息到列表开头
            new_messages.insert(0, {"role": "system", "content": context_prefix})
            
        return new_messages
        
    def inject_context_to_history(self, history: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """
        将上下文注入到对话历史中
        
        Args:
            history: 对话历史记录
            context: 上下文数据
            
        Returns:
            注入上下文后的对话历史
        """
        if not context or not self.config.enable_injection or not history:
            return history
            
        # 构建上下文消息
        context_message = {
            "role": "system",
            "content": self._build_context_message(context)
        }
        
        # 在历史开头插入上下文消息
        result = [context_message]
        result.extend(history)
        
        return result
        
    def _build_context_prefix(self, context: Dict[str, Any]) -> str:
        """
        构建上下文前缀
        
        Args:
            context: 上下文数据
            
        Returns:
            上下文前缀文本
        """
        try:
            # 根据上下文类型构建不同的前缀
            context_type = context.get('type', 'general')
            
            if context_type == 'user_profile':
                return self._build_user_profile_prefix(context)
            elif context_type == 'domain':
                return self._build_domain_knowledge_prefix(context)
            elif context_type == 'system':
                return self._build_system_state_prefix(context)
            elif context_type == 'dialogue_history':
                return self._build_dialogue_history_prefix(context)
            elif context_type == 'location':
                return self._build_location_prefix(context)
            else:
                return self._build_general_prefix(context)
                
        except Exception as e:
            logger.error(f"构建上下文前缀时出错: {e}")
            return ""
            
    def _build_context_message(self, context: Dict[str, Any]) -> str:
        """
        构建上下文消息
        
        Args:
            context: 上下文数据
            
        Returns:
            上下文消息文本
        """
        return self._build_context_prefix(context)
        
    def _build_general_prefix(self, context: Dict[str, Any]) -> str:
        """
        构建通用上下文前缀
        
        Args:
            context: 上下文数据
            
        Returns:
            通用上下文前缀
        """
        prefix_parts = ["系统: 请在回答时考虑以下上下文信息:"]
        
        # 移除类型字段，因为它已经被处理
        context_copy = context.copy()
        if 'type' in context_copy:
            del context_copy['type']
            
        # 添加所有其他字段
        for key, value in context_copy.items():
            if isinstance(value, dict):
                # 处理嵌套字典
                prefix_parts.append(f"- {key}:")
                for sub_key, sub_value in value.items():
                    prefix_parts.append(f"  - {sub_key}: {sub_value}")
            else:
                prefix_parts.append(f"- {key}: {value}")
                
        return "\n".join(prefix_parts)
        
    def _build_user_profile_prefix(self, context: Dict[str, Any]) -> str:
        """
        构建用户资料上下文前缀
        
        Args:
            context: 上下文数据
            
        Returns:
            用户资料上下文前缀
        """
        prefix = "系统: 用户资料信息如下:\n"
        
        # 提取用户资料信息
        user_info = context.get('user_info', {})
        preferences = context.get('preferences', {})
        
        # 添加用户基本信息
        if user_info:
            prefix += "用户信息:\n"
            for key, value in user_info.items():
                prefix += f"- {key}: {value}\n"
                
        # 添加用户偏好
        if preferences:
            prefix += "用户偏好:\n"
            for key, value in preferences.items():
                prefix += f"- {key}: {value}\n"
                
        return prefix
        
    def _build_domain_knowledge_prefix(self, context: Dict[str, Any]) -> str:
        """
        构建领域知识上下文前缀
        
        Args:
            context: 上下文数据
            
        Returns:
            领域知识上下文前缀
        """
        prefix = "系统: 请在回答时参考以下领域知识:\n"
        
        # 提取领域和知识点
        domain = context.get('domain', '通用')
        knowledge = context.get('knowledge', [])
        
        prefix += f"领域: {domain}\n"
        
        if knowledge:
            prefix += "知识点:\n"
            for item in knowledge:
                prefix += f"- {item}\n"
                
        return prefix
        
    def _build_system_state_prefix(self, context: Dict[str, Any]) -> str:
        """
        构建系统状态上下文前缀
        
        Args:
            context: 上下文数据
            
        Returns:
            系统状态上下文前缀
        """
        prefix = "系统: 当前系统状态信息如下:\n"
        
        # 提取系统状态信息
        state = context.get('state', {})
        features = context.get('features', [])
        
        # 添加状态信息
        if state:
            prefix += "状态:\n"
            for key, value in state.items():
                prefix += f"- {key}: {value}\n"
                
        # 添加可用功能
        if features:
            prefix += "可用功能:\n"
            for feature in features:
                prefix += f"- {feature}\n"
                
        return prefix
        
    def _build_dialogue_history_prefix(self, context: Dict[str, Any]) -> str:
        """
        构建对话历史上下文前缀
        
        Args:
            context: 上下文数据
            
        Returns:
            对话历史上下文前缀
        """
        prefix = "系统: 以下是对话历史，请务必根据这些历史信息提供连贯的回复。\n\n"
        prefix += "特别重要说明：当用户输入\"继续\"、\"继续讲\"或类似表达时，你必须继续讲解上一个话题的后续内容，不要开始新话题，不要重复已经说过的内容。\n\n"
        prefix += "如果用户在了解某个主题后说\"继续\"，你应该继续提供关于该主题的更多信息，而不是切换到无关话题。\n\n"
        
        # 提取对话历史
        history = context.get('history', [])
        
        if not history:
            return ""
            
        prefix += "对话历史（请特别注意最近的对话主题和内容）:\n"
        
        # 格式化对话历史
        last_topic = None
        for i, turn in enumerate(history):
            role = turn.get('role', 'unknown')
            content = turn.get('content', '')
            
            # 转换角色名称
            if role == "user":
                role_name = "用户"
                # 尝试提取用户最近讨论的主题
                if content and len(content) > 2 and not content.strip() in ["继续", "继续讲", "请继续"]:
                    last_topic = content
            elif role == "assistant":
                role_name = "AI"
            else:
                role_name = role
                
            prefix += f"{role_name}: {content}\n"
        
        # 如果检测到最近的主题，添加额外的提示
        if last_topic:
            prefix += f"\n系统: 如果用户要求继续，请继续提供关于最近主题的信息: {last_topic}\n"
            
        return prefix
        
    def _build_location_prefix(self, context: Dict[str, Any]) -> str:
        """
        构建位置上下文前缀
        
        Args:
            context: 上下文数据
            
        Returns:
            位置上下文前缀
        """
        prefix = "系统: 用户的位置信息如下:\n"
        
        # 提取位置信息
        city = context.get('city', '')
        province = context.get('province', '')
        country = context.get('country', '')
        coordinates = context.get('coordinates', {})
        
        if city:
            prefix += f"城市: {city}\n"
        if province:
            prefix += f"省份/州: {province}\n"
        if country:
            prefix += f"国家: {country}\n"
            
        if coordinates:
            lat = coordinates.get('latitude')
            lng = coordinates.get('longitude')
            if lat and lng:
                prefix += f"坐标: 纬度 {lat}, 经度 {lng}\n"
                
        return prefix
