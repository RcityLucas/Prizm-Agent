from datetime import datetime
import uuid
from typing import Dict, Any, List, Optional

class ChatSessionModel:
    """人类对话会话模型"""
    
    def __init__(
        self,
        title: str,
        creator_id: str,
        participants: List[str],
        is_group: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4()).replace('-', '')
        self.title = title
        self.creator_id = creator_id
        self.participants = participants
        self.is_group = is_group
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.last_message_id = None
        self.last_message_time = None
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'creator_id': self.creator_id,
            'participants': self.participants,
            'is_group': self.is_group,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_message_id': self.last_message_id,
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatSessionModel':
        """从字典创建实例"""
        session = cls(
            title=data.get('title', ''),
            creator_id=data.get('creator_id', ''),
            participants=data.get('participants', []),
            is_group=data.get('is_group', False),
            metadata=data.get('metadata', {})
        )
        session.id = data.get('id', session.id)
        
        # 处理日期时间字段
        if 'created_at' in data:
            if isinstance(data['created_at'], str):
                session.created_at = datetime.fromisoformat(data['created_at'])
            else:
                session.created_at = data['created_at']
                
        if 'updated_at' in data:
            if isinstance(data['updated_at'], str):
                session.updated_at = datetime.fromisoformat(data['updated_at'])
            else:
                session.updated_at = data['updated_at']
        
        session.last_message_id = data.get('last_message_id')
        
        if 'last_message_time' in data and data['last_message_time']:
            if isinstance(data['last_message_time'], str):
                session.last_message_time = datetime.fromisoformat(data['last_message_time'])
            else:
                session.last_message_time = data['last_message_time']
        
        return session

class ChatMessageModel:
    """人类对话消息模型"""
    
    def __init__(
        self,
        session_id: str,
        sender_id: str,
        content: str,
        content_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4()).replace('-', '')
        self.session_id = session_id
        self.sender_id = sender_id
        self.content = content
        self.content_type = content_type  # text, image, file, etc.
        self.created_at = datetime.now()
        self.delivered_at = None
        self.read_by = {}  # 记录每个接收者的阅读时间 {user_id: timestamp}
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'sender_id': self.sender_id,
            'content': self.content,
            'content_type': self.content_type,
            'created_at': self.created_at.isoformat(),
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_by': {user_id: time.isoformat() for user_id, time in self.read_by.items()},
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessageModel':
        """从字典创建实例"""
        message = cls(
            session_id=data.get('session_id', ''),
            sender_id=data.get('sender_id', ''),
            content=data.get('content', ''),
            content_type=data.get('content_type', 'text'),
            metadata=data.get('metadata', {})
        )
        message.id = data.get('id', message.id)
        
        # 处理日期时间字段
        if 'created_at' in data:
            if isinstance(data['created_at'], str):
                message.created_at = datetime.fromisoformat(data['created_at'])
            else:
                message.created_at = data['created_at']
                
        if 'delivered_at' in data and data['delivered_at']:
            if isinstance(data['delivered_at'], str):
                message.delivered_at = datetime.fromisoformat(data['delivered_at'])
            else:
                message.delivered_at = data['delivered_at']
        
        # 处理已读信息
        read_by = data.get('read_by', {})
        if read_by:
            for user_id, time_str in read_by.items():
                if isinstance(time_str, str):
                    message.read_by[user_id] = datetime.fromisoformat(time_str)
                else:
                    message.read_by[user_id] = time_str
        
        return message