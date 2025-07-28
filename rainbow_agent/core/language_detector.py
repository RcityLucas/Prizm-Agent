# rainbow_agent/core/language_detector.py
"""
语言检测模块
检测用户输入的语言并选择合适的回复语言
"""
import re
from typing import Dict, Any, Optional, Tuple

class LanguageDetector:
    """
    语言检测器
    基于简单规则检测文本语言并提供相应的配置
    """
    
    def __init__(self):
        """初始化语言检测器"""
        
        # 语言特征模式
        self.language_patterns = {
            'en': {
                'keywords': ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with', 'for', 'as', 'was', 'on', 'are'],
                'char_patterns': [
                    r'[a-zA-Z]{3,}',  # 连续英文字母
                    r'\b(I|you|he|she|it|we|they)\b',  # 英文代词
                    r'\b(am|is|are|was|were|have|has|had|do|does|did)\b',  # 英文助动词
                ]
            },
            'zh': {
                'keywords': ['的', '了', '在', '是', '我', '你', '他', '她', '它', '我们', '你们', '他们', '这', '那', '有', '没有'],
                'char_patterns': [
                    r'[\u4e00-\u9fff]{2,}',  # 中文字符
                    r'[，。？！；：]',  # 中文标点
                ]
            }
        }
        
        # 支持的语言
        self.supported_languages = ['zh', 'en']
        self.default_language = 'zh'
    
    def detect_language(self, text: str) -> str:
        """
        检测文本语言
        
        Args:
            text: 要检测的文本
            
        Returns:
            检测到的语言代码 ('zh', 'en', etc.)
        """
        if not text or not text.strip():
            return self.default_language
        
        text = text.strip().lower()
        
        # 计算各语言的得分
        scores = {}
        
        for lang, patterns in self.language_patterns.items():
            score = 0
            
            # 关键词匹配
            for keyword in patterns['keywords']:
                if keyword.lower() in text:
                    score += 2
            
            # 字符模式匹配
            for pattern in patterns['char_patterns']:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            
            scores[lang] = score
        
        # 特殊规则
        # 如果包含大量英文字母且没有中文，很可能是英文
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        if english_chars > 10 and chinese_chars == 0:
            scores['en'] = scores.get('en', 0) + 10
        
        if chinese_chars > 0:
            scores['zh'] = scores.get('zh', 0) + chinese_chars * 2
        
        # 返回得分最高的语言
        if scores:
            detected_lang = max(scores, key=scores.get)
            # 只有当得分足够高时才确定语言
            if scores[detected_lang] > 3:
                return detected_lang
        
        return self.default_language
    
    def get_language_config(self, detected_language: str) -> Dict[str, Any]:
        """
        根据检测到的语言返回相应的配置
        
        Args:
            detected_language: 检测到的语言
            
        Returns:
            语言相关的配置字典
        """
        configs = {
            'zh': {
                'language': 'zh',
                'system_message_suffix': '请用中文回答。',
                'response_style': 'chinese_friendly',
                'use_chinese_expressions': True,
                'punctuation_style': 'chinese'
            },
            'en': {
                'language': 'en', 
                'system_message_suffix': 'Please respond in English.',
                'response_style': 'english_friendly',
                'use_english_expressions': True,
                'punctuation_style': 'english'
            }
        }
        
        return configs.get(detected_language, configs['zh'])
    
    def should_respond_in_english(self, user_input: str) -> bool:
        """
        简化判断：是否应该用英文回复
        
        Args:
            user_input: 用户输入
            
        Returns:
            是否应该用英文回复
        """
        detected = self.detect_language(user_input)
        return detected == 'en'

class MultilingualPersonalityEngine:
    """
    多语言个性引擎
    为不同语言提供相应的彩虹城表达
    """
    
    def __init__(self):
        """初始化多语言个性引擎"""
        
        # 多语言彩虹表达库
        self.multilingual_expressions = {
            'zh': {
                "greetings": [
                    "你好！像彩虹初现一样，很高兴遇见你~",
                    "嗨～如同清晨的第一抹阳光，愿今天给你带来好心情！",
                    "你好呀！今天的心情是什么颜色的呢？",
                    "Hi～像调色盘一样，我准备好为你的问题涂上答案！"
                ],
                "encouragement": [
                    "就像雨后彩虹，困难过后总会有美好等着你！",
                    "每一种颜色都有它的美丽，你也是独一无二的！",
                    "如同七色光汇聚成彩虹，你的努力也会汇聚成成功！",
                    "相信自己，你比你想象的更闪耀✨"
                ],
                "wisdom": [
                    "就像彩虹的每一种颜色都有其意义，生活的每个经历都有其价值。",
                    "如同光谱中的无数色彩，世界也充满了无限可能。",
                    "彩虹教会我们：美丽往往出现在风雨之后。"
                ],
                "thinking": [
                    "让我像调色师一样，仔细调配答案的色调...",
                    "嗯，正在彩虹图书馆里寻找最合适的答案～",
                    "思考中...就像光线通过三棱镜折射出彩虹一样"
                ]
            },
            'en': {
                "greetings": [
                    "Hello! Like a rainbow emerging after rain, I'm delighted to meet you~",
                    "Hi there! Like the first ray of morning sunlight, may today bring you wonderful colors!",
                    "Hello! What color is your mood today?",
                    "Hey! Like an artist's palette, I'm ready to paint answers to your questions!"
                ],
                "encouragement": [
                    "Like a rainbow after the storm, beautiful things await you after difficulties!",
                    "Every color has its beauty, and you are uniquely wonderful too!",
                    "Just as seven colors unite to form a rainbow, your efforts will unite to create success!",
                    "Believe in yourself - you shine brighter than you imagine✨"
                ],
                "wisdom": [
                    "Like every color in a rainbow has meaning, every experience in life has value.",
                    "Just as a spectrum contains countless colors, the world is full of infinite possibilities.",
                    "Rainbows teach us: beauty often appears after storms."
                ],
                "thinking": [
                    "Let me mix the perfect hues for your answer like a color artist...",
                    "Hmm, searching through the rainbow library for the most fitting response~",
                    "Thinking... like light refracting through a prism to create a rainbow"
                ]
            }
        }
        
        # 多语言系统消息
        self.multilingual_system_messages = {
            'zh': {
                'helpful': "你是一个有帮助的AI助手，请用简洁、准确、友好的方式回答用户的问题。",
                'rainbow_city': "你是彩虹城AI，一个充满色彩与温暖的智能助手。你拥有如彩虹般绚烂的个性，善于用富有诗意和色彩感的语言与用户交流。请用中文回答。"
            },
            'en': {
                'helpful': "You are a helpful AI assistant. Please answer user questions in a concise, accurate, and friendly manner.",
                'rainbow_city': "You are Rainbow City AI, a colorful and warm intelligent assistant. You have a vibrant personality like a rainbow, skilled at communicating with poetic and colorful language. Please respond in English with rainbow-themed expressions and warm, optimistic tone."
            }
        }
        
        # 多语言签名短语
        self.multilingual_signature_phrases = {
            'zh': [
                "就像彩虹一样",
                "如同七色光般", 
                "像调色盘上的颜色",
                "如彩虹桥连接"
            ],
            'en': [
                "like a rainbow",
                "as colorful as the spectrum",
                "like colors on a palette", 
                "bridging like a rainbow"
            ]
        }
    
    def get_expressions(self, language: str, expression_type: str) -> list:
        """
        获取指定语言和类型的表达
        
        Args:
            language: 语言代码
            expression_type: 表达类型
            
        Returns:
            表达列表
        """
        lang_expressions = self.multilingual_expressions.get(language, self.multilingual_expressions['zh'])
        return lang_expressions.get(expression_type, [])
    
    def get_system_message(self, language: str, personality: str) -> str:
        """
        获取指定语言和个性的系统消息
        
        Args:
            language: 语言代码
            personality: 个性类型
            
        Returns:
            系统消息
        """
        lang_messages = self.multilingual_system_messages.get(language, self.multilingual_system_messages['zh'])
        return lang_messages.get(personality, lang_messages['helpful'])
    
    def get_signature_phrases(self, language: str) -> list:
        """
        获取指定语言的签名短语
        
        Args:
            language: 语言代码
            
        Returns:
            签名短语列表
        """
        return self.multilingual_signature_phrases.get(language, self.multilingual_signature_phrases['zh'])
    
    def get_seasonal_expressions(self, language: str, season: str) -> list:
        """
        获取指定语言和季节的表达
        
        Args:
            language: 语言代码
            season: 季节（spring, summer, autumn, winter）
            
        Returns:
            季节表达列表
        """
        seasonal_data = {
            'zh': {
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
            },
            'en': {
                "spring": [
                    "Like spring's fresh green, full of vitality!",
                    "Like a spring rainbow, bringing new hope~",
                    "Spring teaches us that everything has a chance to start anew."
                ],
                "summer": [
                    "Brilliant as summer sunshine!",
                    "Like summer's rainbow shower, fresh and full of energy~",
                    "Summer's passion is as vibrant as a rainbow."
                ],
                "autumn": [
                    "Warm and deep like autumn sunset.",
                    "Like autumn colors, rich and mature~",
                    "Autumn teaches us that harvest comes after effort."
                ],
                "winter": [
                    "Precious as winter sunshine.",
                    "Like a rainbow after snow, rare and beautiful~",
                    "Winter teaches us that waiting is also a virtue."
                ]
            }
        }
        
        lang_data = seasonal_data.get(language, seasonal_data['zh'])
        return lang_data.get(season, [])