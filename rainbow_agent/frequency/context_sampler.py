# rainbow_agent/frequency/context_sampler.py
"""
上下文采样器，负责收集环境信号和上下文信息
"""
from typing import Dict, Any, List, Optional
import time
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ContextSampler:
    """
    上下文采样器，负责收集环境信号和上下文信息，为频率感知系统提供决策依据
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化上下文采样器
        
        Args:
            config: 配置参数，包含信号优先级、采样频率等
        """
        self.config = config or {}
        self.signal_priorities = self.config.get("signal_priorities", {
            "user_activity": 10,
            "time_elapsed": 6,
            "conversation_context": 8,
            "system_state": 5,
            "external_events": 7
        })
        
        # 上次采样时间
        self.last_sample_time = time.time()
        # 上次用户活动时间
        self.last_user_activity_time = time.time()
        # 采样历史
        self.sample_history = []
        # 最大历史记录数
        self.max_history_size = self.config.get("max_history_size", 50)
        
        logger.info("上下文采样器初始化完成")
    
    def sample(self, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        采样当前上下文信息
        
        Args:
            current_context: 当前上下文信息，包含对话状态、用户输入等
            
        Returns:
            采样结果，包含各类环境信号和优先级评分
        """
        current_time = time.time()
        
        # 更新用户活动时间
        if current_context.get("user_input"):
            self.last_user_activity_time = current_time
        
        # 收集各类信号
        signals = {
            "timestamp": current_time,
            "datetime": datetime.now().isoformat(),
            "signals": {
                "user_activity": self._sample_user_activity(current_context, current_time),
                "time_elapsed": self._sample_time_elapsed(current_time),
                "conversation_context": self._sample_conversation_context(current_context),
                "system_state": self._sample_system_state(),
                "external_events": self._sample_external_events(current_context)
            }
        }
        
        # 计算综合优先级评分
        priority_score = self._calculate_priority_score(signals["signals"])
        signals["priority_score"] = priority_score
        
        # 更新采样历史
        self._update_sample_history(signals)
        
        # 更新上次采样时间
        self.last_sample_time = current_time
        
        logger.debug(f"上下文采样完成，优先级评分: {priority_score}")
        return signals
    
    def _sample_user_activity(self, context: Dict[str, Any], current_time: float) -> Dict[str, Any]:
        """采样用户活动信号"""
        idle_time = current_time - self.last_user_activity_time
        
        # 检测用户输入类型
        input_type = context.get("input_type", "unknown")
        
        # 检测用户情绪（如果有情绪分析结果）
        user_emotion = context.get("user_emotion", "neutral")
        
        return {
            "idle_time": idle_time,
            "input_type": input_type,
            "user_emotion": user_emotion,
            "has_question": "?" in context.get("user_input", ""),
            "input_length": len(context.get("user_input", "")),
            "score": self._calculate_user_activity_score(idle_time, input_type, user_emotion)
        }
    
    def _sample_time_elapsed(self, current_time: float) -> Dict[str, Any]:
        """采样时间流逝信号"""
        elapsed_since_last_sample = current_time - self.last_sample_time
        
        # 获取当前时间信息
        now = datetime.now()
        hour_of_day = now.hour
        
        # 判断是否是特殊时间段（早晨、中午、晚上等）
        time_period = "morning" if 5 <= hour_of_day < 12 else \
                     "afternoon" if 12 <= hour_of_day < 18 else \
                     "evening" if 18 <= hour_of_day < 22 else "night"
        
        return {
            "elapsed_since_last_sample": elapsed_since_last_sample,
            "hour_of_day": hour_of_day,
            "time_period": time_period,
            "is_weekend": now.weekday() >= 5,
            "score": self._calculate_time_elapsed_score(elapsed_since_last_sample, time_period)
        }
    
    def _sample_conversation_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """采样对话上下文信号"""
        # 获取对话历史长度
        history_length = len(context.get("conversation_history", []))
        
        # 获取最近的对话主题（如果有）
        recent_topics = context.get("recent_topics", [])
        
        # 检测对话是否活跃
        is_active_conversation = history_length > 0 and \
                               (time.time() - self.last_user_activity_time) < 300  # 5分钟内有活动
        
        return {
            "history_length": history_length,
            "recent_topics": recent_topics,
            "is_active_conversation": is_active_conversation,
            "has_open_questions": context.get("has_open_questions", False),
            "score": self._calculate_conversation_context_score(
                history_length, is_active_conversation, context.get("has_open_questions", False)
            )
        }
    
    def _sample_system_state(self) -> Dict[str, Any]:
        """采样系统状态信号"""
        # 这里可以添加系统资源使用情况、错误状态等
        # 简化实现，实际应用中可以扩展
        return {
            "cpu_usage": 0.5,  # 模拟值
            "memory_usage": 0.4,  # 模拟值
            "has_errors": False,
            "score": 0.5  # 默认中等优先级
        }
    
    def _sample_external_events(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """采样外部事件信号"""
        # 检查是否有通知、提醒等外部事件
        notifications = context.get("notifications", [])
        reminders = context.get("reminders", [])
        
        # 计算外部事件优先级
        has_high_priority = any(n.get("priority", "normal") == "high" for n in notifications)
        
        return {
            "has_notifications": len(notifications) > 0,
            "has_reminders": len(reminders) > 0,
            "notification_count": len(notifications),
            "reminder_count": len(reminders),
            "has_high_priority": has_high_priority,
            "score": self._calculate_external_events_score(notifications, reminders)
        }
    
    def _calculate_user_activity_score(self, idle_time: float, input_type: str, user_emotion: str) -> float:
        """计算用户活动信号评分"""
        # 空闲时间评分（空闲时间越长，评分越高）
        idle_score = min(1.0, idle_time / 3600)  # 最多1小时计为满分
        
        # 输入类型评分
        type_score = 0.8 if input_type == "question" else \
                    0.6 if input_type == "command" else \
                    0.4
        
        # 情绪评分
        emotion_score = 0.9 if user_emotion in ["excited", "happy"] else \
                       0.7 if user_emotion in ["neutral"] else \
                       0.5 if user_emotion in ["sad", "confused"] else \
                       0.8  # 其他情绪
        
        # 综合评分
        return (idle_score * 0.5 + type_score * 0.3 + emotion_score * 0.2)
    
    def _calculate_time_elapsed_score(self, elapsed_time: float, time_period: str) -> float:
        """计算时间流逝信号评分"""
        # 时间流逝评分
        elapsed_score = min(1.0, elapsed_time / 7200)  # 最多2小时计为满分
        
        # 时间段评分
        period_score = 0.8 if time_period == "morning" else \
                      0.7 if time_period == "afternoon" else \
                      0.9 if time_period == "evening" else \
                      0.3  # night
        
        # 综合评分
        return (elapsed_score * 0.7 + period_score * 0.3)
    
    def _calculate_conversation_context_score(self, history_length: int, is_active: bool, has_open_questions: bool) -> float:
        """计算对话上下文信号评分"""
        # 历史长度评分
        history_score = min(1.0, history_length / 20)  # 最多20条历史记录计为满分
        
        # 活跃度评分
        active_score = 0.8 if is_active else 0.3
        
        # 开放问题评分
        question_score = 0.9 if has_open_questions else 0.5
        
        # 综合评分
        return (history_score * 0.3 + active_score * 0.4 + question_score * 0.3)
    
    def _calculate_external_events_score(self, notifications: List[Dict[str, Any]], reminders: List[Dict[str, Any]]) -> float:
        """计算外部事件信号评分"""
        if not notifications and not reminders:
            return 0.1
        
        # 通知评分
        notification_score = min(1.0, len(notifications) / 5)  # 最多5条通知计为满分
        
        # 提醒评分
        reminder_score = min(1.0, len(reminders) / 3)  # 最多3条提醒计为满分
        
        # 优先级评分
        priority_score = 0.9 if any(n.get("priority", "normal") == "high" for n in notifications) else \
                        0.6 if any(n.get("priority", "normal") == "medium" for n in notifications) else \
                        0.3
        
        # 综合评分
        return (notification_score * 0.4 + reminder_score * 0.3 + priority_score * 0.3)
    
    def _calculate_priority_score(self, signals: Dict[str, Dict[str, Any]]) -> float:
        """计算综合优先级评分"""
        total_score = 0
        total_weight = 0
        
        for signal_type, signal_data in signals.items():
            if signal_type in self.signal_priorities:
                weight = self.signal_priorities[signal_type]
                score = signal_data.get("score", 0.5)
                total_score += weight * score
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.5
    
    def _update_sample_history(self, sample: Dict[str, Any]):
        """更新采样历史"""
        self.sample_history.append(sample)
        
        # 限制历史记录大小
        if len(self.sample_history) > self.max_history_size:
            self.sample_history = self.sample_history[-self.max_history_size:]
    
    def get_sample_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """获取采样历史"""
        if limit is None or limit >= len(self.sample_history):
            return self.sample_history
        return self.sample_history[-limit:]
