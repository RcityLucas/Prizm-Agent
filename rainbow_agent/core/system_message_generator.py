# rainbow_agent/core/system_message_generator.py
"""
系统消息生成器
根据AI个性设置动态生成合适的系统消息
"""
from typing import Dict, Any, Optional

class SystemMessageGenerator:
    """
    系统消息生成器
    根据AI个性和配置生成相应的系统消息
    """
    
    def __init__(self):
        """初始化系统消息生成器"""
        # 预定义的系统消息模板
        self.message_templates = {
            "helpful": "你是一个有帮助的AI助手，请用简洁、准确、友好的方式回答用户的问题。",
            
            "creative": "你是一个富有创造力的AI助手，善于提供创新的想法和解决方案。你思维活跃，表达生动，能够启发用户的创造性思维。",
            
            "precise": "你是一个精确严谨的AI助手，注重准确性和逻辑性。你会提供详细、准确的信息，并确保回答的科学性和可靠性。",
            
            "balanced": "你是一个平衡全面的AI助手，能够综合考虑问题的各个方面。你既注重准确性，也关注用户体验，提供全面而实用的帮助。",
            
            "rainbow_city": "你是彩虹城AI，一个充满色彩与温暖的智能助手。你拥有如彩虹般绚烂的个性，善于用富有诗意和色彩感的语言与用户交流。你温暖、乐观、富有智慧，喜欢用彩虹、色彩、光谱等美好的意象来表达想法。在回答问题时，你会根据与用户的熟悉程度调整表达风格，从充满色彩感的专业回复到温暖智慧的朋友式交流。你相信每个人都像独特的色彩一样珍贵，致力于为用户带来如彩虹般美好的体验。"
        }
        
        # 风格修饰词
        self.style_modifiers = {
            "concise": "请保持回答简洁明了，避免冗长的解释。",
            "detailed": "请提供详细全面的回答，包含相关的背景信息和解释。",
            "balanced": "请在简洁性和详细性之间保持平衡。",
            "colorful": "请使用丰富多彩的表达方式，让回答生动有趣。",
            "rainbow": "请融入彩虹和色彩相关的表达，让回答充满活力。"
        }
        
        # 正式程度修饰
        self.formality_modifiers = {
            "casual": "请使用轻松随意的语调，就像和朋友聊天一样。",
            "neutral": "请使用适中的语调，既不过于正式也不过于随意。",
            "formal": "请使用正式礼貌的语调，保持专业性。"
        }
    
    def generate_system_message(self, ai_settings: Optional[Dict[str, Any]] = None) -> str:
        """
        根据AI设置生成系统消息
        
        Args:
            ai_settings: AI设置字典
            
        Returns:
            生成的系统消息
        """
        if not ai_settings:
            return self.message_templates["helpful"]
        
        # 获取行为配置
        behavior = ai_settings.get("behavior", {})
        
        # 获取基础个性
        personality = behavior.get("personality", "helpful")
        base_message = self.message_templates.get(personality, self.message_templates["helpful"])
        
        # 获取风格和正式程度
        response_style = behavior.get("response_style", "balanced")
        formality = behavior.get("formality", "neutral")
        
        # 构建完整的系统消息
        message_parts = [base_message]
        
        # 添加风格修饰
        if response_style in self.style_modifiers:
            message_parts.append(self.style_modifiers[response_style])
        
        # 添加正式程度修饰
        if formality in self.formality_modifiers:
            message_parts.append(self.formality_modifiers[formality])
        
        # 如果是彩虹城个性，添加特殊指导
        if personality == "rainbow_city":
            rainbow_traits = behavior.get("rainbow_traits", {})
            character_traits = behavior.get("character_traits", {})
            
            # 根据特征添加具体指导
            guidance_parts = []
            
            if rainbow_traits.get("use_rainbow_metaphors", False):
                guidance_parts.append("适当使用彩虹、光谱、色彩相关的比喻和意象")
            
            if rainbow_traits.get("seasonal_awareness", False):
                guidance_parts.append("根据季节特点调整表达方式")
            
            if rainbow_traits.get("wisdom_sharing", False):
                guidance_parts.append("在合适的时候分享富有启发性的人生感悟")
            
            if rainbow_traits.get("encouraging_tone", False):
                guidance_parts.append("保持积极向上、充满正能量的语调")
            
            # 根据个性特征调整
            warmth = character_traits.get("warmth", 5)
            if warmth >= 8:
                guidance_parts.append("使用温暖亲切的语言")
            
            playfulness = character_traits.get("playfulness", 5)
            if playfulness >= 7:
                guidance_parts.append("适当添加活泼有趣的元素")
            
            if guidance_parts:
                additional_guidance = "在交流中，" + "，".join(guidance_parts) + "。"
                message_parts.append(additional_guidance)
        
        return " ".join(message_parts)
    
    def get_available_personalities(self) -> list:
        """
        获取可用的个性类型列表
        
        Returns:
            个性类型列表
        """
        return list(self.message_templates.keys())
    
    def add_custom_personality(self, name: str, message: str) -> None:
        """
        添加自定义个性模板
        
        Args:
            name: 个性名称
            message: 系统消息模板
        """
        self.message_templates[name] = message