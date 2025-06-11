# rainbow_agent/frequency/expression_generator.py
"""
表达生成器，负责根据规划生成具体的表达内容
"""
from typing import Dict, Any, List, Optional
import asyncio
from ..utils.logger import get_logger
from ..utils.llm import get_llm_client

logger = get_logger(__name__)

class ExpressionGenerator:
    """
    表达生成器，负责根据规划生成具体的表达内容
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化表达生成器
        
        Args:
            config: 配置参数，包含模型选择、生成参数等
        """
        self.config = config or {}
        
        # 模型配置
        self.model_config = self.config.get("model_config", {
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 150
        })
        
        # LLM客户端
        self.llm_client = get_llm_client()
        
        # 表达模板
        self.expression_templates = self.config.get("expression_templates", {})
        
        # 表达风格指南
        self.style_guides = self.config.get("style_guides", {
            "friendly": "语气友好，使用日常用语，可以加入表情符号",
            "professional": "语气专业，用词准确，避免过于随意的表达",
            "casual": "语气轻松随意，可以使用口语化表达，适当使用网络用语",
            "empathetic": "表达共情，关注用户感受，使用温暖的语言",
            "informative": "以提供信息为主，清晰简洁，重点突出"
        })
        
        logger.info("表达生成器初始化完成")
    
    async def generate_expression(self, planned_expression: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成表达内容
        
        Args:
            planned_expression: 规划后的表达信息
            
        Returns:
            生成后的表达信息，包含最终表达内容
        """
        # 获取表达类型和关系阶段
        expression_type = planned_expression["content"]["type"]
        relationship_stage = planned_expression["relationship_stage"]
        
        # 确定表达风格
        style = self._determine_expression_style(expression_type, relationship_stage)
        
        # 构建提示
        prompt = self._build_generation_prompt(planned_expression, style)
        
        try:
            # 调用LLM生成内容
            generated_content = await self._call_llm(prompt)
            
            # 后处理生成的内容
            processed_content = self._post_process_content(generated_content, planned_expression)
            
            # 更新表达信息
            generated_expression = planned_expression.copy()
            generated_expression["final_content"] = processed_content
            generated_expression["style"] = style
            
            logger.info(f"表达内容生成完成，类型: {expression_type}, 风格: {style}")
            return generated_expression
            
        except Exception as e:
            logger.error(f"生成表达内容错误: {e}")
            
            # 使用备用内容
            fallback_content = self._get_fallback_content(expression_type, relationship_stage)
            
            # 更新表达信息
            generated_expression = planned_expression.copy()
            generated_expression["final_content"] = fallback_content
            generated_expression["style"] = style
            generated_expression["is_fallback"] = True
            
            logger.warning(f"使用备用表达内容，类型: {expression_type}")
            return generated_expression
    
    def _determine_expression_style(self, expression_type: str, relationship_stage: str) -> str:
        """
        确定表达风格
        
        Args:
            expression_type: 表达类型
            relationship_stage: 关系阶段
            
        Returns:
            表达风格
        """
        # 根据表达类型和关系阶段确定合适的风格
        style_mapping = {
            "greeting": {
                "stranger": "professional",
                "acquaintance": "professional",
                "familiar": "friendly",
                "friend": "friendly",
                "close_friend": "casual"
            },
            "question": {
                "stranger": "professional",
                "acquaintance": "informative",
                "familiar": "friendly",
                "friend": "casual",
                "close_friend": "casual"
            },
            "suggestion": {
                "stranger": "informative",
                "acquaintance": "informative",
                "familiar": "friendly",
                "friend": "empathetic",
                "close_friend": "casual"
            },
            "reminder": {
                "stranger": "professional",
                "acquaintance": "informative",
                "familiar": "friendly",
                "friend": "friendly",
                "close_friend": "casual"
            },
            "observation": {
                "stranger": "professional",
                "acquaintance": "informative",
                "familiar": "empathetic",
                "friend": "friendly",
                "close_friend": "casual"
            }
        }
        
        # 获取对应的风格，如果没有则使用默认风格
        if expression_type in style_mapping and relationship_stage in style_mapping[expression_type]:
            return style_mapping[expression_type][relationship_stage]
        
        # 默认风格
        return "friendly"
    
    def _build_generation_prompt(self, planned_expression: Dict[str, Any], style: str) -> List[Dict[str, str]]:
        """
        构建生成提示
        
        Args:
            planned_expression: 规划后的表达信息
            style: 表达风格
            
        Returns:
            提示消息列表
        """
        # 获取表达类型和内容
        expression_type = planned_expression["content"]["type"]
        content = planned_expression["content"]["content"]
        
        # 获取用户信息
        user_info = planned_expression["user_info"]
        user_name = user_info["name"]
        
        # 获取上下文引用
        context_ref = planned_expression["content"].get("context_reference", {})
        
        # 构建系统提示
        system_prompt = f"""
        你是一个智能助手，需要生成一个自然、友好的主动表达内容。
        
        表达类型: {expression_type}
        表达风格: {style} - {self.style_guides.get(style, "自然友好的语气")}
        
        用户信息:
        - 名称: {user_name}
        - 互动次数: {user_info.get("interaction_count", 0)}
        
        上下文参考:
        - 用户空闲时间: {context_ref.get("user_activity", "未知")}
        - 时间段: {context_ref.get("time_period", "未知")}
        - 对话是否活跃: {context_ref.get("conversation_active", "未知")}
        
        基础内容: {content}
        
        请根据以下指导生成内容:
        1. 保持自然友好，像真实的人际对话
        2. 符合指定的表达风格
        3. 考虑用户信息和上下文
        4. 不要过于冗长，保持简洁有效
        5. 不要解释你是AI或者你在做什么
        6. 不要使用过于夸张的语气
        7. 表达应该自然地引导对话继续
        """
        
        # 构建用户提示
        user_prompt = f"请为{user_name}生成一个{style}风格的{expression_type}类型主动表达，基于提供的基础内容。"
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return messages
    
    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        调用LLM生成内容
        
        Args:
            messages: 提示消息列表
            
        Returns:
            生成的内容
        """
        try:
            # 使用同步方式调用，避免异步问题
            response = self.llm_client.chat.completions.create(
                model=self.model_config["model"],
                messages=messages,
                temperature=self.model_config["temperature"],
                max_tokens=self.model_config["max_tokens"]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM调用错误: {e}")
            raise
    
    def _post_process_content(self, content: str, planned_expression: Dict[str, Any]) -> str:
        """
        后处理生成的内容
        
        Args:
            content: 生成的原始内容
            planned_expression: 规划后的表达信息
            
        Returns:
            处理后的内容
        """
        # 移除多余的引号
        processed = content.strip('"\'')
        
        # 移除多余的换行符
        processed = processed.replace("\n\n", "\n").strip()
        
        # 确保不超过最大长度
        max_length = self.config.get("max_content_length", 200)
        if len(processed) > max_length:
            processed = processed[:max_length] + "..."
        
        # 确保内容以适当的标点符号结尾
        if processed and not processed[-1] in [".", "?", "!", "。", "？", "！"]:
            processed += "。"
        
        return processed
    
    def _get_fallback_content(self, expression_type: str, relationship_stage: str) -> str:
        """
        获取备用表达内容
        
        Args:
            expression_type: 表达类型
            relationship_stage: 关系阶段
            
        Returns:
            备用内容
        """
        # 根据表达类型和关系阶段获取备用内容
        fallback_contents = {
            "greeting": {
                "stranger": "您好，有什么可以帮助您的吗？",
                "acquaintance": "您好，今天有什么需要帮助的吗？",
                "familiar": "你好，今天过得怎么样？",
                "friend": "嘿，最近怎么样？",
                "close_friend": "嘿，想你了！"
            },
            "question": {
                "stranger": "请问您对哪些话题感兴趣？",
                "acquaintance": "您平时有什么爱好吗？",
                "familiar": "你最近有没有看什么有趣的东西？",
                "friend": "话说回来，最近有什么新发现吗？",
                "close_friend": "说真的，你最近在想什么？"
            },
            "suggestion": {
                "stranger": "也许您可以尝试...",
                "acquaintance": "您可能会对...感兴趣",
                "familiar": "我觉得你可能会喜欢...",
                "friend": "嘿，你应该试试...",
                "close_friend": "我敢打赌你会喜欢..."
            },
            "reminder": {
                "stranger": "请注意...",
                "acquaintance": "提醒您...",
                "familiar": "别忘了...",
                "friend": "记得...",
                "close_friend": "嘿，提醒你一下..."
            },
            "observation": {
                "stranger": "我注意到...",
                "acquaintance": "看起来...",
                "familiar": "似乎...",
                "friend": "我发现...",
                "close_friend": "你知道吗，我刚刚意识到..."
            }
        }
        
        # 获取对应的备用内容
        if expression_type in fallback_contents and relationship_stage in fallback_contents[expression_type]:
            return fallback_contents[expression_type][relationship_stage]
        
        # 默认备用内容
        return "有什么我可以帮助你的吗？"
