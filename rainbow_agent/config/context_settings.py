"""
上下文增强功能配置

定义上下文增强功能的配置选项。
"""

# 上下文功能配置
CONTEXT_SETTINGS = {
    # 是否启用上下文注入
    "enable_context_injection": True,
    
    # 上下文优先级 (low, medium, high)
    # - low: 仅在没有足够对话历史时使用上下文
    # - medium: 正常使用上下文
    # - high: 上下文优先于对话历史
    "context_priority_level": "medium",
    
    # 最大上下文标记数
    "max_context_tokens": 1000,
    
    # 上下文注入位置
    # - prefix: 在提示前添加上下文
    # - system: 作为系统消息添加
    # - inline: 在对话中内联添加
    "context_injection_position": "prefix",
    
    # 是否记录上下文使用情况
    "log_context_usage": True,
    
    # 是否在响应中包含上下文元数据
    "include_context_metadata_in_response": True,
    
    # 上下文处理超时（秒）
    "context_processing_timeout": 2.0
}

# 上下文类型配置
CONTEXT_TYPE_SETTINGS = {
    "general": {
        "enabled": True,
        "priority": "medium"
    },
    "user_profile": {
        "enabled": True,
        "priority": "high"
    },
    "domain": {
        "enabled": True,
        "priority": "medium"
    },
    "system": {
        "enabled": True,
        "priority": "low"
    },
    "custom": {
        "enabled": True,
        "priority": "medium"
    }
}

# 获取上下文配置
def get_context_settings():
    """
    获取上下文配置
    
    Returns:
        上下文配置字典
    """
    return CONTEXT_SETTINGS

# 获取上下文类型配置
def get_context_type_settings(context_type=None):
    """
    获取上下文类型配置
    
    Args:
        context_type: 上下文类型，如果不提供则返回所有类型配置
        
    Returns:
        上下文类型配置字典
    """
    if context_type and context_type in CONTEXT_TYPE_SETTINGS:
        return CONTEXT_TYPE_SETTINGS[context_type]
    return CONTEXT_TYPE_SETTINGS
