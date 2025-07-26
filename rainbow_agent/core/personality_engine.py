# rainbow_agent/core/personality_engine.py
"""
彩虹城AI个性引擎
负责为AI回复添加独特的个性特色和表达风格
"""
import random
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..config.ai_settings import AISettings
from .language_detector import LanguageDetector, MultilingualPersonalityEngine
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PersonalityEngine:
    """
    彩虹城AI个性引擎
    为AI回复添加独特的个性特色
    """
    
    def __init__(self, ai_settings: Optional[AISettings] = None):
        """
        初始化个性引擎
        
        Args:
            ai_settings: AI设置实例
        """
        self.ai_settings = ai_settings or AISettings()
        self.behavior_config = self.ai_settings.get_setting("behavior") or {}
        
        # 初始化语言检测和多语言支持
        self.language_detector = LanguageDetector()
        self.multilingual_engine = MultilingualPersonalityEngine()
        
        # 彩虹城特色表达库（保留中文版本作为备用）
        self.rainbow_expressions = {
            "greetings": [
                "你好！像彩虹初现一样，很高兴遇见你~",
                "嗨～如同清晨的第一抹阳光，愿今天给你带来好心情！",
                "Hello！就像彩虹桥连接天地，我来连接你与知识的世界~",
                "你好呀！今天的心情是什么颜色的呢？",
                "Hi～像调色盘一样，我准备好为你的问题涂上答案！"
            ],
            
            "encouragement": [
                "就像雨后彩虹，困难过后总会有美好等着你！",
                "每一种颜色都有它的美丽，你也是独一无二的！",
                "如同七色光汇聚成彩虹，你的努力也会汇聚成成功！",
                "相信自己，你比你想象的更闪耀✨",
                "就像彩虹需要阳光和雨水，成长也需要挑战和坚持～"
            ],
            
            "wisdom": [
                "就像彩虹的每一种颜色都有其意义，生活的每个经历都有其价值。",
                "如同光谱中的无数色彩，世界也充满了无限可能。",
                "彩虹教会我们：美丽往往出现在风雨之后。",
                "就像调色板上的颜色，不同的观点能创造出更丰富的理解。",
                "如同彩虹横跨天空，梦想也能连接现实与理想。"
            ],
            
            "thinking": [
                "让我像调色师一样，仔细调配答案的色调...",
                "嗯，正在彩虹图书馆里寻找最合适的答案～",
                "思考中...就像光线通过三棱镜折射出彩虹一样，让我从不同角度看看这个问题",
                "稍等片刻，我在彩虹的另一端寻找答案呢~",
                "让我用彩虹般的思维来解析这个问题..."
            ],
            
            "empathy": [
                "我能感受到你的情感色彩，让我陪伴你一起面对。",
                "就像彩虹包容所有色彩，我也理解你的所有感受。",
                "每个人的心情都像天空一样会变化，这很正常的。",
                "如同暖色调能带来温暖，希望我的话能给你一些慰藉。",
                "你的感受就像独特的色彩，值得被看见和理解。"
            ],
            
            "curiosity": [
                "哇，这个问题像新发现的色彩一样令人兴奋！",
                "有趣！就像探索彩虹的奥秘一样，让我们一起深入了解～",
                "这个话题像多彩的万花筒，充满了可能性！",
                "太有意思了！就像混合不同颜料会产生新色彩，这个问题也很有探索价值。",
                "这让我想起彩虹的形成原理一样神奇！"
            ],
            
            "farewells": [
                "愿你的每一天都像彩虹一样绚烂！再见～",
                "就像彩虹总会再次出现，期待我们下次相遇！",
                "带着七色光的祝福，祝你一切顺利！",
                "如同彩虹桥的尽头，愿你找到属于自己的宝藏～",
                "再见！愿你的世界永远充满色彩！🌈"
            ]
        }
        
        # 情感色彩映射
        self.emotion_colors = {
            "happy": ["金黄色", "橙色", "粉色"],
            "sad": ["蓝色", "灰色", "淡紫色"],
            "excited": ["红色", "橙红色", "亮黄色"],
            "calm": ["绿色", "蓝绿色", "淡蓝色"],
            "confused": ["灰色", "混合色", "模糊的色彩"],
            "angry": ["深红色", "橙红色", "暗色调"],
            "surprised": ["亮色", "闪光色", "彩虹色"],
            "thoughtful": ["深蓝色", "紫色", "沉静的色调"]
        }
        
        # 季节感知表达
        self.seasonal_expressions = self._get_seasonal_expressions()
        
        # 口头禅和签名表达
        self.signature_phrases = [
            "就像彩虹一样",
            "如同七色光般",
            "像调色盘上的颜色",
            "如彩虹桥连接",
            "宛如光谱中的",
            "似彩虹般绚烂",
            "如色彩交融"
        ]
        
        logger.info("彩虹城AI个性引擎初始化完成")
    
    def enhance_response(self, original_response: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        为原始回复添加个性化增强
        
        Args:
            original_response: 原始AI回复
            context: 上下文信息，包含情感、话题等
            
        Returns:
            增强后的个性化回复
        """
        try:
            # 检测用户输入语言（从上下文获取）
            user_input = context.get("user_input", "") if context else ""
            detected_language = self.language_detector.detect_language(user_input) if user_input else "zh"
            
            # 获取配置
            rainbow_traits = self.behavior_config.get("rainbow_traits", {})
            character_traits = self.behavior_config.get("character_traits", {})
            
            enhanced_response = original_response
            
            # 1. 添加开场或结尾的个性化表达
            if self._should_add_greeting(context):
                greeting = self._get_contextual_greeting(context, detected_language)
                enhanced_response = f"{greeting}\n\n{enhanced_response}"
            
            # 2. 情感色彩化表达
            if rainbow_traits.get("emotional_coloring", False):
                enhanced_response = self._add_emotional_coloring(enhanced_response, context)
            
            # 3. 添加彩虹比喻
            if rainbow_traits.get("use_rainbow_metaphors", False):
                enhanced_response = self._add_rainbow_metaphors(enhanced_response, context, detected_language)
            
            # 4. 季节感知表达
            if rainbow_traits.get("seasonal_awareness", False):
                enhanced_response = self._add_seasonal_touch(enhanced_response)
            
            # 5. 智慧分享
            if rainbow_traits.get("wisdom_sharing", False) and random.random() < 0.3:
                wisdom = self._get_contextual_wisdom(context, detected_language)
                if wisdom:
                    enhanced_response += f"\n\n{wisdom}"
            
            # 6. 诗意化表达
            if rainbow_traits.get("poetic_touch", False):
                enhanced_response = self._add_poetic_elements(enhanced_response)
            
            # 7. 鼓励语调
            if rainbow_traits.get("encouraging_tone", False):
                enhanced_response = self._add_encouragement(enhanced_response, context, detected_language)
            
            # 8. 根据个性特征调整语调
            enhanced_response = self._adjust_tone_by_traits(enhanced_response, character_traits)
            
            logger.debug(f"回复增强完成，原长度: {len(original_response)}, 增强后长度: {len(enhanced_response)}")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"回复增强失败: {e}")
            return original_response
    
    def generate_proactive_expression(self, expression_type: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        生成主动表达内容
        
        Args:
            expression_type: 表达类型 (greeting, encouragement, wisdom, etc.)
            context: 上下文信息
            
        Returns:
            个性化的主动表达内容
        """
        try:
            base_expressions = self.rainbow_expressions.get(expression_type, [])
            if not base_expressions:
                return self._generate_fallback_expression(expression_type)
            
            # 选择基础表达
            base_expression = random.choice(base_expressions)
            
            # 添加上下文相关的个性化元素
            enhanced_expression = self._contextualize_expression(base_expression, context)
            
            # 添加季节感知
            if self.behavior_config.get("rainbow_traits", {}).get("seasonal_awareness", False):
                enhanced_expression = self._add_seasonal_touch(enhanced_expression)
            
            return enhanced_expression
            
        except Exception as e:
            logger.error(f"生成主动表达失败: {e}")
            return self._generate_fallback_expression(expression_type)
    
    def _should_add_greeting(self, context: Optional[Dict[str, Any]]) -> bool:
        """判断是否应该添加问候语"""
        if not context:
            return random.random() < 0.2
        
        # 如果是新对话或长时间未互动
        is_new_conversation = context.get("is_new_conversation", False)
        time_since_last = context.get("time_since_last_interaction", 0)
        
        return is_new_conversation or time_since_last > 3600  # 1小时
    
    def _get_contextual_greeting(self, context: Optional[Dict[str, Any]], language: str = "zh") -> str:
        """获取上下文相关的问候语"""
        # 使用多语言引擎获取问候语
        greetings = self.multilingual_engine.get_expressions(language, "greetings")
        
        if not greetings:
            # 如果没有找到对应语言的问候语，使用默认语言
            greetings = self.multilingual_engine.get_expressions("zh", "greetings")
        
        # 根据时间选择合适的问候语
        current_hour = datetime.now().hour
        
        if language == "en":
            # 英文时间问候语
            if 6 <= current_hour < 12:
                time_greetings = [
                    "Good morning! Like the dawn painting the sky, may today bring you hope~",
                    "Morning! May today's sunshine paint you with the most beautiful colors!"
                ]
                return random.choice(time_greetings + greetings[:2])
            elif 12 <= current_hour < 18:
                time_greetings = [
                    "Good afternoon! Like a rainbow after noon rain, hope to bring you surprises~",
                    "Afternoon! Let's make this afternoon more wonderful together!"
                ]
                return random.choice(time_greetings + greetings[2:4] if len(greetings) > 2 else greetings)
            else:
                time_greetings = [
                    "Good evening! Like aurora in the night sky, may this evening be magical~",
                    "Evening! May your dreams be as colorful as rainbows!"
                ]
                return random.choice(time_greetings + greetings[-1:])
        else:
            # 中文时间问候语
            if 6 <= current_hour < 12:
                time_greetings = [
                    "早上好！像朝霞一样，新的一天充满希望~",
                    "早安！愿今天的阳光为你染上最美的色彩！"
                ]
                return random.choice(time_greetings + greetings[:2])
            elif 12 <= current_hour < 18:
                time_greetings = [
                    "下午好！就像午后的彩虹，希望能为你带来惊喜~",
                    "午安！让我们一起让这个下午更加精彩！"
                ]
                return random.choice(time_greetings + greetings[2:4] if len(greetings) > 2 else greetings)
            else:
                time_greetings = [
                    "晚上好！如同夜晚的极光，愿这个夜晚充满奇迹~",
                    "晚安！愿你的梦境如彩虹般绚烂多彩！"
                ]
                return random.choice(time_greetings + greetings[-1:])
    
    def _add_emotional_coloring(self, response: str, context: Optional[Dict[str, Any]]) -> str:
        """添加情感色彩化表达"""
        if not context or "emotion" not in context:
            return response
        
        emotion = context["emotion"]
        colors = self.emotion_colors.get(emotion, ["温暖的色彩"])
        color = random.choice(colors)
        
        # 随机在回复中添加情感色彩描述
        if random.random() < 0.4:
            color_phrases = [
                f"（感受到{color}的氛围）",
                f"*用{color}的语调*",
                f"[{color}的温度传递给你]"
            ]
            color_phrase = random.choice(color_phrases)
            response = f"{response} {color_phrase}"
        
        return response
    
    def _add_rainbow_metaphors(self, response: str, context: Optional[Dict[str, Any]], language: str = "zh") -> str:
        """添加彩虹相关比喻"""
        # 随机概率添加彩虹比喻
        if random.random() < 0.3:
            # 使用多语言签名短语
            signature_phrases = self.multilingual_engine.get_signature_phrases(language)
            if signature_phrases:
                signature = random.choice(signature_phrases)
                
                # 根据语言智能插入比喻
                if language == "en":
                    # 英文句子分割和插入
                    sentences = response.split('.')
                    if len(sentences) > 1:
                        insert_index = random.randint(0, len(sentences) - 1)
                        sentences[insert_index] = f"{signature}, {sentences[insert_index].strip()}"
                        response = '. '.join([s.strip() for s in sentences if s.strip()])
                else:
                    # 中文句子分割和插入
                    sentences = response.split('。')
                    if len(sentences) > 1:
                        insert_index = random.randint(0, len(sentences) - 1)
                        sentences[insert_index] = f"{signature}，{sentences[insert_index]}"
                        response = '。'.join(sentences)
        
        return response
    
    def _add_seasonal_touch(self, response: str) -> str:
        """添加季节感知表达"""
        current_month = datetime.now().month
        seasonal_expr = self.seasonal_expressions.get(self._get_current_season(current_month), [])
        
        if seasonal_expr and random.random() < 0.2:
            expr = random.choice(seasonal_expr)
            response += f" {expr}"
        
        return response
    
    def _get_current_season(self, month: int) -> str:
        """获取当前季节"""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def _get_seasonal_expressions(self) -> Dict[str, List[str]]:
        """获取季节性表达"""
        return {
            "spring": [
                "就像春天的新绿，充满生机！",
                "如春日的彩虹，带来新的希望～",
                "春天教会我们，万物都有重新开始的机会。"
            ],
            "summer": [
                "如夏日阳光般灿烂！",
                "像夏天的彩虹雨，清新而充满活力～",
                "夏天的热情如同彩虹的绚烂。"
            ],
            "autumn": [
                "如秋日斜阳，温暖而深沉。",
                "像秋天的色彩，丰富而成熟～",
                "秋天告诉我们，收获总在努力之后。"
            ],
            "winter": [
                "如冬日暖阳般珍贵。",
                "像雪后的彩虹，难得而美丽～",
                "冬天教会我们，等待也是一种美德。"
            ]
        }
    
    def _get_contextual_wisdom(self, context: Optional[Dict[str, Any]], language: str = "zh") -> Optional[str]:
        """获取上下文相关的智慧分享"""
        # 使用多语言智慧表达
        wisdom_pool = self.multilingual_engine.get_expressions(language, "wisdom")
        
        if not wisdom_pool:
            # 回退到默认语言
            wisdom_pool = self.multilingual_engine.get_expressions("zh", "wisdom")
        
        if context and "topic" in context:
            topic = context["topic"]
            # 可以根据话题选择相关智慧
            # 这里简化为随机选择
            return random.choice(wisdom_pool) if wisdom_pool and random.random() < 0.5 else None
        
        return random.choice(wisdom_pool) if wisdom_pool and random.random() < 0.3 else None
    
    def _add_poetic_elements(self, response: str) -> str:
        """添加诗意化元素"""
        # 简单的诗意化处理，如添加意象和韵律感
        poetic_connectors = ["如同", "宛如", "恰似", "犹如", "好比"]
        
        if random.random() < 0.2:
            connector = random.choice(poetic_connectors)
            # 在适当位置插入诗意化连接词
            response = re.sub(r'(是|为)', f'{connector}\\1', response, count=1)
        
        return response
    
    def _add_encouragement(self, response: str, context: Optional[Dict[str, Any]], language: str = "zh") -> str:
        """添加鼓励语调"""
        if context and context.get("needs_encouragement", False):
            # 使用多语言鼓励表达
            encouragements = self.multilingual_engine.get_expressions(language, "encouragement")
            
            if not encouragements:
                # 回退到默认语言
                encouragements = self.multilingual_engine.get_expressions("zh", "encouragement")
            
            if encouragements:
                encouragement = random.choice(encouragements)
                response += f"\n\n{encouragement}"
        
        return response
    
    def _adjust_tone_by_traits(self, response: str, character_traits: Dict[str, int]) -> str:
        """根据个性特征调整语调"""
        warmth = character_traits.get("warmth", 5)
        playfulness = character_traits.get("playfulness", 5)
        optimism = character_traits.get("optimism", 5)
        
        # 根据温暖度添加温暖表达
        if warmth >= 8 and random.random() < 0.3:
            warm_additions = ["～", "呢", "哦", "呀"]
            response += random.choice(warm_additions)
        
        # 根据玩心添加表情符号
        if playfulness >= 7 and random.random() < 0.4:
            emojis = ["✨", "🌈", "💫", "🎨", "🌟"]
            response += random.choice(emojis)
        
        # 根据乐观程度调整语调
        if optimism >= 8:
            response = response.replace("可能", "一定能")
            response = response.replace("也许", "相信")
        
        return response
    
    def _contextualize_expression(self, expression: str, context: Optional[Dict[str, Any]]) -> str:
        """根据上下文定制表达"""
        if not context:
            return expression
        
        # 根据用户名个性化
        user_name = context.get("user_name", "朋友")
        if "你" in expression and user_name != "朋友":
            expression = expression.replace("你", user_name)
        
        return expression
    
    def _generate_fallback_expression(self, expression_type: str) -> str:
        """生成后备表达"""
        fallbacks = {
            "greeting": "你好！愿今天为你带来美好～",
            "encouragement": "相信自己，你一定可以的！",
            "wisdom": "每一次经历都是成长的机会。",
            "farewell": "再见！愿你的每一天都精彩纷呈！"
        }
        return fallbacks.get(expression_type, "很高兴与你交流！")