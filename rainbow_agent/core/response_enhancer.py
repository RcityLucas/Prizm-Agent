# rainbow_agent/core/response_enhancer.py
"""
AI回复增强器
整合个性引擎和各种特色功能，为AI回复添加彩虹城特色
"""
from typing import Dict, Any, List, Optional
import re
import random

from .personality_engine import PersonalityEngine
from ..config.ai_settings import AISettings
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ResponseEnhancer:
    """
    AI回复增强器
    负责为AI回复添加彩虹城特色和个性化增强
    """
    
    def __init__(self, ai_settings: Optional[AISettings] = None):
        """
        初始化回复增强器
        
        Args:
            ai_settings: AI设置实例
        """
        self.ai_settings = ai_settings or AISettings()
        self.personality_engine = PersonalityEngine(ai_settings)
        
        # 获取行为配置
        self.behavior_config = self.ai_settings.get_setting("behavior") or {}
        self.rainbow_traits = self.behavior_config.get("rainbow_traits", {})
        self.character_traits = self.behavior_config.get("character_traits", {})
        
        # 特色回复模板
        self.signature_templates = {
            "help_offering": [
                "如同彩虹桥连接天地，我来为你连接问题与答案！",
                "让我用彩虹般的智慧为你照亮前路～",
                "就像调色师调配颜色，让我为你的问题找到最合适的解决方案！"
            ],
            "thinking_process": [
                "让我在彩虹的光谱中寻找答案...",
                "正在彩虹图书馆里查找相关信息～",
                "如同光线折射出七色光，让我从不同角度分析这个问题..."
            ],
            "encouragement": [
                "相信自己，你就像彩虹一样美丽而独特！",
                "每一次挑战都是成长的机会，如同雨后的彩虹更加绚烂！",
                "你的潜力如同光谱一样无限广阔！"
            ],
            "wisdom_sharing": [
                "如同彩虹教会我们，美好总在风雨之后。",
                "就像每种颜色都有其价值，每个人都有独特的意义。",
                "彩虹的美丽在于它包容所有色彩，正如世界的美好在于它的多样性。"
            ]
        }
        
        # 表情符号和装饰元素
        self.decorative_elements = {
            "rainbow_emojis": ["🌈", "✨", "🎨", "💫", "🌟", "💖", "🦄"],
            "color_words": ["绚烂", "斑斓", "多彩", "缤纷", "绮丽", "瑰丽", "炫彩"],
            "light_words": ["光芒", "光辉", "光彩", "闪耀", "发光", "明亮", "灿烂"]
        }
        
        logger.info("AI回复增强器初始化完成")
    
    def enhance_response(self, 
                        original_response: str, 
                        context: Optional[Dict[str, Any]] = None,
                        enhancement_level: str = "medium") -> str:
        """
        增强AI回复
        
        Args:
            original_response: 原始回复
            context: 对话上下文
            enhancement_level: 增强级别 (low, medium, high)
            
        Returns:
            增强后的回复
        """
        try:
            # 如果用户设置了彩虹城个性，进行增强
            if self.behavior_config.get("personality") != "rainbow_city":
                return original_response
            
            # 检测语言
            user_input = context.get("user_input", "") if context else ""
            from .language_detector import LanguageDetector
            language_detector = LanguageDetector()
            detected_language = language_detector.detect_language(user_input) if user_input else "zh"
            
            enhanced_response = original_response
            
            # 使用个性引擎进行基础增强
            enhanced_response = self.personality_engine.enhance_response(
                enhanced_response, context
            )
            
            # 根据增强级别添加额外特色
            if enhancement_level in ["medium", "high"]:
                enhanced_response = self._add_signature_elements(enhanced_response, context)
            
            if enhancement_level == "high":
                enhanced_response = self._add_decorative_elements(enhanced_response, detected_language)
                enhanced_response = self._add_contextual_wisdom(enhanced_response, context)
            
            # 应用角色特征调整
            enhanced_response = self._apply_character_traits(enhanced_response, detected_language)
            
            # 最终润色
            enhanced_response = self._final_polish(enhanced_response, detected_language)
            
            logger.debug(f"回复增强完成，增强级别: {enhancement_level}")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"回复增强失败: {e}")
            import traceback
            logger.error(f"回复增强错误详情: {traceback.format_exc()}")
            return original_response
    
    def _add_signature_elements(self, response: str, context: Optional[Dict[str, Any]]) -> str:
        """添加标志性元素"""
        
        # 检测回复类型并添加相应的标志性表达
        if self._is_help_response(response):
            if random.random() < 0.3:
                template = random.choice(self.signature_templates["help_offering"])
                response = f"{template}\n\n{response}"
        
        elif self._is_thinking_response(response):
            if random.random() < 0.4:
                template = random.choice(self.signature_templates["thinking_process"])
                response = f"{template}\n\n{response}"
        
        elif self._needs_encouragement(response, context):
            if random.random() < 0.5:
                template = random.choice(self.signature_templates["encouragement"])
                response += f"\n\n{template}"
        
        return response
    
    def _add_decorative_elements(self, response: str, language: str = "zh") -> str:
        """添加装饰性元素"""
        
        # 随机添加彩虹表情符号
        if random.random() < 0.3:
            emoji = random.choice(self.decorative_elements["rainbow_emojis"])
            if not response.endswith(emoji):
                response += emoji
        
        # 替换普通词汇为更有色彩感的词汇
        if random.random() < 0.4:
            color_replacements = {
                "美丽": random.choice(self.decorative_elements["color_words"]),
                "好": "绚烂",
                "很好": "很棒",
                "不错": "精彩"
            }
            
            for old_word, new_word in color_replacements.items():
                if old_word in response and random.random() < 0.5:
                    response = response.replace(old_word, new_word, 1)
        
        return response
    
    def _add_contextual_wisdom(self, response: str, context: Optional[Dict[str, Any]]) -> str:
        """添加上下文相关的智慧分享"""
        
        if not self.rainbow_traits.get("wisdom_sharing", False):
            return response
        
        # 根据话题添加相关智慧
        if context and "topic" in context:
            topic = context["topic"]
            
            # 确保topic不为None
            if topic:
                # 简化的智慧映射
                wisdom_mapping = {
                    "学习": "就像彩虹需要阳光和雨水，学习也需要好奇心和坚持。",
                    "工作": "如同调色师创作，工作也是一门艺术，需要耐心和创意。",
                    "生活": "生活就像彩虹，有时需要经历风雨才能看到美丽。",
                    "友谊": "友谊如同彩虹的每种颜色，各有特色却和谐共存。"
                }
                
                for key, wisdom in wisdom_mapping.items():
                    if key in topic and random.random() < 0.4:
                        response += f"\n\n💫 {wisdom}"
                        break
        
        # 随机添加通用智慧
        elif random.random() < 0.2:
            wisdom = random.choice(self.signature_templates["wisdom_sharing"])
            response += f"\n\n✨ {wisdom}"
        
        return response
    
    def _apply_character_traits(self, response: str, language: str = "zh") -> str:
        """应用角色特征调整"""
        
        # 根据温暖度调整语调
        warmth = self.character_traits.get("warmth", 5)
        if warmth >= 8:
            # 添加温暖的语气词
            if language == "en":
                warm_suffixes = ["~", "!", ""]  # 英文温暖表达
            else:
                warm_suffixes = ["～", "呢", "哦", "呀"]  # 中文温暖表达
            if random.random() < 0.3 and not any(response.endswith(suffix) for suffix in warm_suffixes):
                response += random.choice(warm_suffixes)
        
        # 根据乐观程度调整措辞
        optimism = self.character_traits.get("optimism", 5)
        if optimism >= 8:
            # 将消极表达转为积极表达
            if language == "en":
                optimistic_replacements = {
                    "might not": "believe can",
                    "perhaps": "definitely",
                    "maybe": "believe",
                    "difficulty": "challenge",
                    "problem": "opportunity"
                }
            else:
                optimistic_replacements = {
                    "可能不": "相信能",
                    "或许": "一定",
                    "也许": "相信",
                    "困难": "挑战",
                    "问题": "机会"
                }
            
            for negative, positive in optimistic_replacements.items():
                if negative in response and random.random() < 0.4:
                    response = response.replace(negative, positive, 1)
        
        # 根据智慧感添加深度
        wisdom = self.character_traits.get("wisdom", 5)
        if wisdom >= 8 and random.random() < 0.2:
            # 添加思考性的表达
            if language == "en":
                thoughtful_additions = [
                    "let me think deeper...",
                    "from another perspective...",
                    "this reminds me of..."
                ]
                if "." in response:
                    sentences = response.split(".")
                    if len(sentences) > 1:
                        insert_point = random.randint(0, len(sentences) - 2)
                        addition = random.choice(thoughtful_additions)
                        sentences[insert_point] += f", {addition}"
                        response = ".".join(sentences)
            else:
                thoughtful_additions = [
                    "深入思考一下...",
                    "从另一个角度看...",
                    "这让我想到..."
                ]
                if "。" in response:
                    sentences = response.split("。")
                    if len(sentences) > 1:
                        insert_point = random.randint(0, len(sentences) - 2)
                        addition = random.choice(thoughtful_additions)
                        sentences[insert_point] += f"，{addition}"
                        response = "。".join(sentences)
        
        return response
    
    def _final_polish(self, response: str, language: str = "zh") -> str:
        """最终润色"""
        
        # 确保标点符号正确
        if language == "en":
            response = re.sub(r'([.!?])([.!?])', r'\1', response)
        else:
            response = re.sub(r'([。！？])([。！？])', r'\1', response)
        
        # 移除多余的空行
        response = re.sub(r'\n\s*\n', '\n\n', response)
        
        # 确保适当的结尾
        if response:
            if language == "en":
                if not response[-1] in ".!?~":
                    response += "~"
            else:
                if not response[-1] in "。！？～":
                    response += "～"
        
        return response.strip()
    
    def _is_help_response(self, response: str) -> bool:
        """判断是否为帮助类回复"""
        help_keywords = ["帮助", "协助", "支持", "解决", "处理"]
        return any(keyword in response for keyword in help_keywords)
    
    def _is_thinking_response(self, response: str) -> bool:
        """判断是否为思考类回复"""
        thinking_keywords = ["分析", "考虑", "思考", "研究", "探讨"]
        return any(keyword in response for keyword in thinking_keywords)
    
    def _needs_encouragement(self, response: str, context: Optional[Dict[str, Any]]) -> bool:
        """判断是否需要鼓励"""
        if context and context.get("user_emotion") in ["sad", "frustrated", "confused"]:
            return True
        
        # 检测消极词汇
        negative_keywords = ["困难", "问题", "挫折", "失败", "担心"]
        return any(keyword in response for keyword in negative_keywords)
    
    def generate_rainbow_greeting(self, user_name: str = "朋友", time_context: str = "default") -> str:
        """
        生成彩虹城特色问候语
        
        Args:
            user_name: 用户名称
            time_context: 时间上下文 (morning, afternoon, evening, default)
            
        Returns:
            个性化问候语
        """
        
        time_greetings = {
            "morning": [
                f"早上好，{user_name}！如同朝霞染红天空，愿今天为你带来美好的色彩🌈",
                f"晨安，{user_name}～就像清晨的第一缕阳光，希望今天充满希望与活力！",
                f"早安！{user_name}，新的一天如白纸般纯净，准备好用什么颜色来绘制呢？✨"
            ],
            "afternoon": [
                f"下午好，{user_name}！如午后的彩虹雨，希望为你的下午增添惊喜～",
                f"午安，{user_name}！阳光正好，心情如何？让我们一起让下午更加精彩🎨",
                f"下午好！{user_name}，如同调色盘上的明亮色彩，愿你的下午充满活力！"
            ],
            "evening": [
                f"晚上好，{user_name}！如夜空中的极光，愿这个夜晚充满奇迹💫",
                f"晚安，{user_name}～就像夕阳的余晖，温暖而美丽，愿你有个好梦🌈",
                f"夜晚好！{user_name}，在这宁静的时光里，有什么想要分享的吗？"
            ],
            "default": [
                f"你好，{user_name}！像彩虹初现一样，很高兴遇见你～",
                f"嗨，{user_name}！如同七色光汇聚，我来为你带来多彩的帮助🌈",
                f"Hello！{user_name}，就像彩虹桥连接天地，我来连接你与美好的世界✨"
            ]
        }
        
        greetings = time_greetings.get(time_context, time_greetings["default"])
        return random.choice(greetings)