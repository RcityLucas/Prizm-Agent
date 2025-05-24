"""
代理通信系统

实现代理之间的消息传递和通信功能
"""
from typing import List, Dict, Any, Optional, Union
import time
import uuid
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MessageType(Enum):
    """消息类型"""
    TASK_ASSIGNMENT = "task_assignment"   # 任务分配
    TASK_RESULT = "task_result"           # 任务结果
    QUERY = "query"                       # 查询信息
    RESPONSE = "response"                 # 回应查询
    STATUS_UPDATE = "status_update"       # 状态更新
    FEEDBACK = "feedback"                 # 反馈
    SYSTEM = "system"                     # 系统消息


class Message:
    """
    代理间的消息
    
    用于代理之间的通信和协作
    """
    
    def __init__(
        self, 
        content: str,
        msg_type: Union[MessageType, str],
        sender_id: str,
        recipient_id: Optional[str] = None,
        related_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        初始化消息
        
        Args:
            content: 消息内容
            msg_type: 消息类型
            sender_id: 发送者ID
            recipient_id: 接收者ID，为None表示广播消息
            related_task_id: 相关任务ID
            metadata: 其他元数据
        """
        self.message_id = str(uuid.uuid4())
        self.content = content
        self.msg_type = msg_type if isinstance(msg_type, MessageType) else MessageType(msg_type)
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.related_task_id = related_task_id
        self.metadata = metadata or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "message_id": self.message_id,
            "content": self.content,
            "type": self.msg_type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "related_task_id": self.related_task_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息"""
        message = cls(
            content=data["content"],
            msg_type=data["type"],
            sender_id=data["sender_id"],
            recipient_id=data.get("recipient_id"),
            related_task_id=data.get("related_task_id"),
            metadata=data.get("metadata", {})
        )
        message.message_id = data["message_id"]
        message.timestamp = data["timestamp"]
        return message
    
    def __str__(self) -> str:
        recipient = self.recipient_id if self.recipient_id else "所有人"
        return f"消息 [{self.msg_type.value}] 从 {self.sender_id} 到 {recipient}: {self.content[:30]}..."


class MessageBus:
    """
    消息总线
    
    处理代理之间的消息路由和传递
    """
    
    def __init__(self):
        """初始化消息总线"""
        self.messages: List[Message] = []
        self.subscribers: Dict[str, List[str]] = {}  # agent_id -> 订阅的消息类型列表
    
    def subscribe(self, agent_id: str, message_types: Optional[List[Union[MessageType, str]]] = None):
        """
        订阅消息
        
        Args:
            agent_id: 代理ID
            message_types: 要订阅的消息类型列表，None表示所有类型
        """
        if message_types is None:
            # 订阅所有消息类型
            self.subscribers[agent_id] = [msg_type.value for msg_type in MessageType]
        else:
            # 订阅指定消息类型
            subscribed_types = []
            for msg_type in message_types:
                if isinstance(msg_type, MessageType):
                    subscribed_types.append(msg_type.value)
                else:
                    subscribed_types.append(msg_type)
                    
            self.subscribers[agent_id] = subscribed_types
    
    def unsubscribe(self, agent_id: str):
        """
        取消订阅
        
        Args:
            agent_id: 代理ID
        """
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]
    
    def publish(self, message: Message):
        """
        发布消息
        
        Args:
            message: 要发布的消息
        """
        self.messages.append(message)
        logger.info(f"发布消息: {message}")
        
        # 消息路由处理可以在这里添加
    
    def get_messages_for_agent(self, agent_id: str, since_timestamp: Optional[float] = None) -> List[Message]:
        """
        获取发送给特定代理的消息
        
        Args:
            agent_id: 代理ID
            since_timestamp: 只返回该时间戳之后的消息
            
        Returns:
            消息列表
        """
        result = []
        for message in self.messages:
            # 消息是发给这个代理的，或者是广播消息
            is_recipient = message.recipient_id == agent_id or message.recipient_id is None
            
            # 检查代理是否订阅了这种消息类型
            is_subscribed = (agent_id in self.subscribers and 
                            message.msg_type.value in self.subscribers[agent_id])
            
            # 检查时间戳
            is_recent = since_timestamp is None or message.timestamp > since_timestamp
            
            if is_recipient and is_subscribed and is_recent:
                result.append(message)
                
        return result
    
    def get_messages_by_task(self, task_id: str) -> List[Message]:
        """
        获取与特定任务相关的所有消息
        
        Args:
            task_id: 任务ID
            
        Returns:
            消息列表
        """
        return [msg for msg in self.messages if msg.related_task_id == task_id]
    
    def clear_messages(self, older_than: Optional[float] = None):
        """
        清除消息
        
        Args:
            older_than: 清除早于该时间戳的消息，None表示清除所有消息
        """
        if older_than is None:
            self.messages = []
        else:
            self.messages = [msg for msg in self.messages if msg.timestamp >= older_than]
