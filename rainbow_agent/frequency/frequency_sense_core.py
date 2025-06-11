# rainbow_agent/frequency/frequency_sense_core.py
"""
频率感知核心，负责根据上下文信息进行表达决策
"""
from typing import Dict, Any, List, Optional, Tuple
import time
import random
from ..utils.logger import get_logger
from ..utils.llm import get_llm_client
from .context_sampler import ContextSampler

logger = get_logger(__name__)

class FrequencySenseCore:
    """
    频率感知核心，负责AI自主决策是否表达、何时表达以及表达什么
    """
    
    def __init__(
        self, 
        context_sampler: Optional[ContextSampler] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化频率感知核心
        
        Args:
            context_sampler: 上下文采样器，如果为None则创建默认实例
            config: 配置参数，包含决策阈值、冷却时间等
        """
        self.context_sampler = context_sampler or ContextSampler()
        self.config = config or {}
        
        # 决策阈值，高于此值时会触发表达
        self.expression_threshold = self.config.get("expression_threshold", 0.7)
        
        # 表达冷却时间（秒），避免过于频繁的表达
        self.cooldown_time = self.config.get("cooldown_time", 300)  # 默认5分钟
        
        # 上次表达时间
        self.last_expression_time = 0
        
        # 表达历史
        self.expression_history = []
        
        # 最大历史记录数
        self.max_history_size = self.config.get("max_history_size", 50)
        
        # LLM客户端
        self.llm_client = get_llm_client()
        
        # 表达类型权重
        self.expression_type_weights = self.config.get("expression_type_weights", {
            "greeting": 0.2,
            "question": 0.3,
            "suggestion": 0.25,
            "reminder": 0.15,
            "observation": 0.1
        })
        
        logger.info("频率感知核心初始化完成")
    
    async def decide_expression(self, context: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        决定是否进行表达以及表达内容
        
        Args:
            context: 当前上下文信息
            
        Returns:
            (should_express, expression_info)
            should_express: 是否应该表达
            expression_info: 表达信息，包含类型、内容、优先级等
        """
        # 采样当前上下文
        signals = self.context_sampler.sample(context)
        
        # 检查冷却时间
        current_time = time.time()
        if current_time - self.last_expression_time < self.cooldown_time:
            logger.debug("表达冷却中，跳过决策")
            return False, None
        
        # 判断是否应该表达
        should_express = self._should_express(signals)
        
        if not should_express:
            logger.debug("决策结果：不表达")
            return False, None
        
        # 决定表达时机
        expression_timing = self._decide_timing(signals)
        
        # 决定表达内容
        expression_content = await self._decide_content(context, signals)
        
        # 更新上次表达时间
        self.last_expression_time = current_time
        
        # 构建表达信息
        expression_info = {
            "timing": expression_timing,
            "content": expression_content,
            "priority": signals["priority_score"],
            "timestamp": current_time
        }
        
        # 更新表达历史
        self._update_expression_history(expression_info)
        
        logger.info(f"决策结果：表达，类型: {expression_content['type']}, 优先级: {signals['priority_score']:.2f}")
        return True, expression_info
    
    def _should_express(self, signals: Dict[str, Any]) -> bool:
        """
        判断是否应该表达
        
        Args:
            signals: 上下文信号
            
        Returns:
            是否应该表达
        """
        # 获取优先级评分
        priority_score = signals["priority_score"]
        
        # 基础判断：优先级评分超过阈值
        if priority_score >= self.expression_threshold:
            return True
        
        # 随机因素：即使低于阈值，也有小概率表达
        # 概率随评分增加而增加
        random_threshold = 0.1 + (priority_score * 0.3)
        if random.random() < random_threshold:
            return True
        
        return False
    
    def _decide_timing(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        决定表达时机
        
        Args:
            signals: 上下文信号
            
        Returns:
            表达时机信息
        """
        # 获取优先级评分
        priority_score = signals["priority_score"]
        
        # 用户空闲时间
        idle_time = signals["signals"]["user_activity"]["idle_time"]
        
        # 根据优先级和空闲时间决定表达方式
        if priority_score > 0.9 or signals["signals"]["external_events"]["has_high_priority"]:
            # 高优先级：立即表达
            timing_type = "immediate"
            delay = 0
        elif idle_time > 1800:  # 30分钟无活动
            # 用户长时间无活动：适当延迟
            timing_type = "delayed"
            delay = random.randint(10, 30)  # 10-30秒延迟
        else:
            # 普通情况：根据优先级决定延迟
            timing_type = "scheduled"
            max_delay = int(120 * (1 - priority_score))  # 优先级越高，延迟越短
            delay = random.randint(5, max_delay)
        
        return {
            "type": timing_type,
            "delay": delay,
            "scheduled_time": time.time() + delay
        }
    
    async def _decide_content(self, context: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        决定表达内容
        
        Args:
            context: 当前上下文
            signals: 上下文信号
            
        Returns:
            表达内容信息
        """
        # 决定表达类型
        expression_type = self._select_expression_type(signals)
        
        # 根据类型生成表达内容
        content = await self._generate_expression_content(expression_type, context, signals)
        
        return {
            "type": expression_type,
            "content": content,
            "context_reference": {
                "user_activity": signals["signals"]["user_activity"]["idle_time"],
                "time_period": signals["signals"]["time_elapsed"]["time_period"],
                "conversation_active": signals["signals"]["conversation_context"]["is_active_conversation"]
            }
        }
    
    def _select_expression_type(self, signals: Dict[str, Any]) -> str:
        """
        选择表达类型
        
        Args:
            signals: 上下文信号
            
        Returns:
            表达类型
        """
        # 特殊情况处理
        if signals["signals"]["external_events"]["has_high_priority"]:
            return "reminder"
        
        if signals["signals"]["user_activity"]["idle_time"] > 3600:  # 1小时无活动
            return random.choice(["greeting", "question"])
        
        if signals["signals"]["conversation_context"]["has_open_questions"]:
            return "suggestion"
        
        # 加权随机选择
        types = list(self.expression_type_weights.keys())
        weights = list(self.expression_type_weights.values())
        
        return random.choices(types, weights=weights, k=1)[0]
    
    async def _generate_expression_content(
        self, 
        expression_type: str, 
        context: Dict[str, Any], 
        signals: Dict[str, Any]
    ) -> str:
        """
        生成表达内容
        
        Args:
            expression_type: 表达类型
            context: 当前上下文
            signals: 上下文信号
            
        Returns:
            表达内容
        """
        # 构建提示
        prompt = self._build_expression_prompt(expression_type, context, signals)
        
        try:
            # 调用LLM生成内容
            response = await self._call_llm(prompt)
            return response
        except Exception as e:
            logger.error(f"生成表达内容错误: {e}")
            # 返回备用内容
            return self._get_fallback_content(expression_type)
    
    def _build_expression_prompt(self, expression_type: str, context: Dict[str, Any], signals: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        构建表达提示
        
        Args:
            expression_type: 表达类型
            context: 当前上下文
            signals: 上下文信号
            
        Returns:
            提示消息列表
        """
        # 获取用户信息
        user_name = context.get("user_name", "用户")
        recent_topics = signals["signals"]["conversation_context"].get("recent_topics", [])
        time_period = signals["signals"]["time_elapsed"]["time_period"]
        
        # 基础系统提示
        system_prompt = f"""
        你是一个智能助手，需要生成一个自然、友好的主动表达内容。
        表达类型: {expression_type}
        时间段: {time_period}
        最近的对话主题: {', '.join(recent_topics) if recent_topics else '无'}
        
        请根据以下指导生成内容:
        - 保持简短自然，像朋友间的对话
        - 不要过于正式或机械
        - 不要使用过于夸张的语气
        - 不要自我介绍或解释你是AI
        - 表达应该自然地引导对话继续
        """
        
        # 根据表达类型添加特定指导
        if expression_type == "greeting":
            system_prompt += f"""
            生成一个适合当前时间段的问候语。
            如果是早晨，可以问候并询问计划；
            如果是下午，可以关心用户的状态；
            如果是晚上，可以询问用户的一天。
            """
        elif expression_type == "question":
            system_prompt += f"""
            生成一个开放性问题，基于最近的对话主题或用户兴趣。
            问题应该能够引发思考和延续对话。
            """
        elif expression_type == "suggestion":
            system_prompt += f"""
            基于最近的对话或用户兴趣，提出一个有帮助的建议。
            建议应该具体且实用。
            """
        elif expression_type == "reminder":
            system_prompt += f"""
            生成一个友好的提醒，可以是关于时间、待办事项或之前提到的事情。
            提醒应该温和且有帮助。
            """
        elif expression_type == "observation":
            system_prompt += f"""
            分享一个关于当前情境、最近对话或用户兴趣的观察。
            观察应该有见地且能引发对话。
            """
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请为{user_name}生成一个自然的{expression_type}类型的主动表达。"}
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
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=100
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM调用错误: {e}")
            raise
    
    def _get_fallback_content(self, expression_type: str) -> str:
        """
        获取备用表达内容
        
        Args:
            expression_type: 表达类型
            
        Returns:
            备用内容
        """
        fallback_contents = {
            "greeting": "你好，最近怎么样？",
            "question": "你对什么话题感兴趣呢？",
            "suggestion": "也许我们可以聊聊最近的新闻？",
            "reminder": "别忘了休息一下眼睛哦。",
            "observation": "今天的对话很有意思。"
        }
        
        return fallback_contents.get(expression_type, "有什么我可以帮助你的吗？")
    
    def _update_expression_history(self, expression_info: Dict[str, Any]):
        """
        更新表达历史
        
        Args:
            expression_info: 表达信息
        """
        self.expression_history.append(expression_info)
        
        # 限制历史记录大小
        if len(self.expression_history) > self.max_history_size:
            self.expression_history = self.expression_history[-self.max_history_size:]
    
    def get_expression_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取表达历史
        
        Args:
            limit: 限制返回的历史记录数量
            
        Returns:
            表达历史记录
        """
        if limit is None or limit >= len(self.expression_history):
            return self.expression_history
        return self.expression_history[-limit:]
