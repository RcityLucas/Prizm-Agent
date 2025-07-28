"""
AI设置模块

提供AI行为和性能的配置选项，允许用户自定义AI的行为方式。
"""
from typing import Dict, Any, List, Optional, Union
import json
import os
from pathlib import Path

class AISettings:
    """AI设置管理类"""
    
    # 默认设置
    DEFAULT_SETTINGS = {
        # 记忆与检索设置
        "memory": {
            "use_vector_search": False,        # 是否使用向量检索
            "vector_weight": 0.7,              # 向量相似度权重 (0.0-1.0)
            "max_context_items": 10,           # 上下文最大项数
            "max_history_turns": 10,           # 历史对话最大轮次
            "store_user_messages": True,       # 是否存储用户消息
            "store_ai_messages": True,         # 是否存储AI消息
        },
        
        # AI模型设置
        "model": {
            "provider": "openai",              # AI提供商 (openai, azure, local)
            "model_name": "gpt-3.5-turbo",     # 模型名称
            "temperature": 0.7,                # 温度 (0.0-2.0)
            "top_p": 1.0,                      # Top P (0.0-1.0)
            "max_tokens": 2000,                # 最大生成令牌数
            "presence_penalty": 0.0,           # 存在惩罚 (-2.0-2.0)
            "frequency_penalty": 0.0,          # 频率惩罚 (-2.0-2.0)
        },
        
        # 对话行为设置
        "behavior": {
            "personality": "rainbow_city",     # 个性 (helpful, creative, precise, balanced, rainbow_city)
            "response_style": "balanced",      # 回复风格 (concise, detailed, balanced, colorful, rainbow)
            "formality": "neutral",            # 正式程度 (casual, neutral, formal)
            "empathy_level": "medium",         # 共情程度 (low, medium, high)
            "humor_level": "medium",           # 幽默程度 (low, medium, high)
            "creativity_level": "medium",      # 创造力程度 (low, medium, high)
            
            # 彩虹城AI特色设置
            "rainbow_traits": {
                "use_rainbow_metaphors": True,      # 使用彩虹和色彩相关比喻
                "seasonal_awareness": True,         # 季节感知和相关表达
                "emotional_coloring": True,         # 情感色彩化表达
                "wisdom_sharing": True,             # 分享人生智慧和感悟
                "cultural_blend": True,             # 融合多元文化表达
                "poetic_touch": True,               # 诗意化表达
                "encouraging_tone": True,           # 鼓励和正能量语调
                "memory_weaving": True,             # 编织记忆和故事
            },
            
            # 个性化特征配置
            "character_traits": {
                "curiosity": 8,          # 好奇心 (1-10)
                "warmth": 9,            # 温暖度 (1-10) 
                "playfulness": 7,       # 玩心 (1-10)
                "wisdom": 8,            # 智慧感 (1-10)
                "optimism": 9,          # 乐观程度 (1-10)
                "patience": 9,          # 耐心程度 (1-10)
                "authenticity": 8,      # 真实感 (1-10)
                "adaptability": 8,      # 适应性 (1-10)
            },
        },
        
        # 工具使用设置
        "tools": {
            "allow_tool_use": True,            # 是否允许使用工具
            "auto_tool_selection": True,       # 是否自动选择工具
            "allowed_tools": ["all"],          # 允许使用的工具列表
            "tool_use_threshold": 0.7,         # 工具使用阈值 (0.0-1.0)
        },
        
        # 多模态设置
        "multimodal": {
            "enable_image_understanding": True,  # 是否启用图像理解
            "enable_audio_processing": True,     # 是否启用音频处理
            "image_detail_level": "high",        # 图像细节级别 (low, medium, high)
        },
        
        # 安全设置
        "safety": {
            "content_filtering": "medium",     # 内容过滤级别 (low, medium, high)
            "block_sensitive_topics": True,    # 是否阻止敏感话题
            "sensitive_topics": [              # 敏感话题列表
                "politics", "religion", "adult_content"
            ],
        },
        
        # 系统设置
        "system": {
            "log_conversations": True,         # 是否记录对话
            "log_level": "info",               # 日志级别 (debug, info, warning, error)
            "auto_update_settings": False,     # 是否自动更新设置
        }
    }
    
    def __init__(self, user_id: str = "default", settings_dir: Optional[str] = None):
        """
        初始化AI设置
        
        Args:
            user_id: 用户ID
            settings_dir: 设置文件目录
        """
        self.user_id = user_id
        self.settings_dir = settings_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "settings"
        )
        
        # 确保设置目录存在
        Path(self.settings_dir).mkdir(parents=True, exist_ok=True)
        
        # 加载用户设置
        self.settings = self._load_settings()
    
    def _get_settings_path(self) -> str:
        """获取设置文件路径"""
        return os.path.join(self.settings_dir, f"{self.user_id}_ai_settings.json")
    
    def _load_settings(self) -> Dict[str, Any]:
        """加载设置"""
        settings_path = self._get_settings_path()
        
        # 如果设置文件存在，加载它
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                
                # 合并用户设置与默认设置
                merged_settings = self._merge_settings(self.DEFAULT_SETTINGS, user_settings)
                return merged_settings
            except Exception as e:
                print(f"加载设置失败: {e}，将使用默认设置")
                return self.DEFAULT_SETTINGS.copy()
        else:
            # 如果设置文件不存在，使用默认设置
            return self.DEFAULT_SETTINGS.copy()
    
    def _merge_settings(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归合并设置，保留用户设置，但确保所有默认键都存在
        """
        result = default.copy()
        
        for key, value in user.items():
            # 如果键存在于默认设置中且两者都是字典，递归合并
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                # 否则使用用户设置
                result[key] = value
        
        return result
    
    def save_settings(self) -> bool:
        """保存设置到文件"""
        try:
            settings_path = self._get_settings_path()
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存设置失败: {e}")
            return False
    
    def get_settings(self) -> Dict[str, Any]:
        """获取完整设置"""
        return self.settings
    
    def get_setting(self, category: str, key: Optional[str] = None) -> Any:
        """
        获取特定类别或键的设置
        
        Args:
            category: 设置类别
            key: 设置键，如果为None则返回整个类别
            
        Returns:
            设置值
        """
        if category not in self.settings:
            return None
        
        if key is None:
            return self.settings[category]
        
        # 确保key是字符串类型
        if isinstance(key, str) and key in self.settings[category]:
            return self.settings[category][key]
        
        return None
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """
        更新设置
        
        Args:
            settings: 要更新的设置
            
        Returns:
            是否更新成功
        """
        try:
            # 递归更新设置，使用深度合并
            self.settings = self._merge_settings(self.settings, settings)
            
            # 保存更新后的设置
            return self.save_settings()
        except Exception as e:
            print(f"更新设置失败: {e}")
            return False
    
    def reset_settings(self, category: Optional[str] = None) -> bool:
        """
        重置设置为默认值
        
        Args:
            category: 要重置的类别，如果为None则重置所有设置
            
        Returns:
            是否重置成功
        """
        try:
            if category is None:
                # 重置所有设置
                self.settings = self.DEFAULT_SETTINGS.copy()
            elif category in self.settings and category in self.DEFAULT_SETTINGS:
                # 重置特定类别
                self.settings[category] = self.DEFAULT_SETTINGS[category].copy()
            else:
                return False
            
            # 保存重置后的设置
            return self.save_settings()
        except Exception as e:
            print(f"重置设置失败: {e}")
            return False
    
    def apply_settings_to_components(self, components: Dict[str, Any]) -> None:
        """
        将设置应用到组件
        
        Args:
            components: 组件字典，键为组件名，值为组件实例
        """
        # 应用记忆设置
        if "memory" in self.settings and "context_builder" in components:
            memory_settings = self.settings["memory"]
            context_builder = components["context_builder"]
            
            if hasattr(context_builder, "use_vector_search"):
                context_builder.use_vector_search = memory_settings.get("use_vector_search", False)
            
            if hasattr(context_builder, "vector_weight"):
                context_builder.vector_weight = memory_settings.get("vector_weight", 0.7)
            
            if hasattr(context_builder, "max_context_items"):
                context_builder.max_context_items = memory_settings.get("max_context_items", 10)
            
            if hasattr(context_builder, "max_history_turns"):
                context_builder.max_history_turns = memory_settings.get("max_history_turns", 10)
        
        # 应用对话管理器设置
        if "dialogue_manager" in components:
            dialogue_manager = components["dialogue_manager"]
            
            # 应用记忆设置
            if "memory" in self.settings:
                memory_settings = self.settings["memory"]
                
                if hasattr(dialogue_manager, "use_vector_search"):
                    dialogue_manager.use_vector_search = memory_settings.get("use_vector_search", False)
                
                if hasattr(dialogue_manager, "vector_weight"):
                    dialogue_manager.vector_weight = memory_settings.get("vector_weight", 0.7)
            
            # 应用模型设置
            if "model" in self.settings and hasattr(dialogue_manager, "ai_service"):
                model_settings = self.settings["model"]
                ai_service = dialogue_manager.ai_service
                
                if hasattr(ai_service, "model_name"):
                    ai_service.model_name = model_settings.get("model_name", "gpt-3.5-turbo")
                
                if hasattr(ai_service, "temperature"):
                    ai_service.temperature = model_settings.get("temperature", 0.7)
                
                if hasattr(ai_service, "max_tokens"):
                    ai_service.max_tokens = model_settings.get("max_tokens", 2000)
        
        # 应用多模态设置
        if "multimodal" in self.settings and "multi_modal_manager" in components:
            multimodal_settings = self.settings["multimodal"]
            multi_modal_manager = components["multi_modal_manager"]
            
            if hasattr(multi_modal_manager, "enable_image_understanding"):
                multi_modal_manager.enable_image_understanding = multimodal_settings.get("enable_image_understanding", True)
            
            if hasattr(multi_modal_manager, "enable_audio_processing"):
                multi_modal_manager.enable_audio_processing = multimodal_settings.get("enable_audio_processing", True)
