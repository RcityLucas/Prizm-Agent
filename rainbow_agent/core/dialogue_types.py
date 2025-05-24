# rainbow_agent/core/dialogue_types.py
from enum import Enum
from typing import Dict, Any, List, Optional

class DialogueType(Enum):
    """
    对话类型枚举
    
    定义了系统支持的七种对话类型
    """
    HUMAN_TO_HUMAN_PRIVATE = "human_to_human_private"  # 人类 ⇄ 人类 私聊
    HUMAN_TO_HUMAN_GROUP = "human_to_human_group"      # 人类 ⇄ 人类 群聊
    HUMAN_TO_AI_PRIVATE = "human_to_ai_private"        # 人类 ⇄ AI 私聊
    AI_TO_AI = "ai_to_ai"                              # AI ⇄ AI 对话
    AI_TO_SELF = "ai_to_self"                          # AI ⇄ 自我（自省/觉知）
    HUMAN_TO_AI_GROUP = "human_to_ai_group"            # 人类 ⇄ AI 群组 (LIO)
    AI_TO_MULTI_HUMAN = "ai_to_multi_human"            # AI ⇄ 多人类 群组

class DialogueTypeDetector:
    """
    对话类型检测器
    
    根据参与者和上下文判断对话类型
    """
    
    def detect(
        self, 
        initiator_type: str, 
        responder_type: str, 
        participants_count: int = 2, 
        is_group: bool = False
    ) -> DialogueType:
        """
        检测对话类型
        
        Args:
            initiator_type: 发起者类型 ("human" 或 "ai")
            responder_type: 响应者类型 ("human" 或 "ai")
            participants_count: 参与者数量
            is_group: 是否是群组对话
            
        Returns:
            DialogueType: 对话类型枚举
        """
        # 人类到人类对话
        if initiator_type == "human" and responder_type == "human":
            return DialogueType.HUMAN_TO_HUMAN_GROUP if is_group else DialogueType.HUMAN_TO_HUMAN_PRIVATE
            
        # 人类到AI对话
        if initiator_type == "human" and responder_type == "ai":
            if is_group:
                return DialogueType.HUMAN_TO_AI_GROUP
            return DialogueType.HUMAN_TO_AI_PRIVATE
            
        # AI到AI对话
        if initiator_type == "ai" and responder_type == "ai":
            # 如果发起者和响应者是同一个AI，则为自省
            if initiator_type == responder_type:
                return DialogueType.AI_TO_SELF
            return DialogueType.AI_TO_AI
            
        # AI到多人类对话
        if initiator_type == "ai" and responder_type == "human" and participants_count > 1:
            return DialogueType.AI_TO_MULTI_HUMAN
            
        # 默认为人类到AI私聊
        return DialogueType.HUMAN_TO_AI_PRIVATE