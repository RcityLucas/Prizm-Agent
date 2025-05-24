"""
会话记忆模块

保存并管理与用户的对话历史
"""
from typing import List, Dict, Any, Optional, Tuple
import time

from .base import Memory
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Message:
    """对话消息"""
    
    def __init__(self, role: str, content: str):
        """
        初始化消息
        
        Args:
            role: 消息发送者的角色 (user, assistant, system)
            content: 消息内容
        """
        self.role = role
        self.content = content
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典表示"""
        return {
            "role": self.role,
            "content": self.content
        }
    
    def __str__(self) -> str:
        return f"{self.role}: {self.content[:30]}..."


class Conversation:
    """对话会话"""
    
    def __init__(self, conversation_id: Optional[str] = None, system_message: Optional[str] = None):
        """
        初始化对话会话
        
        Args:
            conversation_id: 对话ID
            system_message: 系统消息
        """
        self.conversation_id = conversation_id or str(int(time.time()))
        self.messages: List[Message] = []
        
        # 初始化元数据（在使用add_system_message之前）
        self.metadata = {
            "created_at": time.time(),
            "last_updated": time.time()
        }
        
        # 添加系统消息（如果提供）
        if system_message:
            self.add_system_message(system_message)
        
    def add_user_message(self, content: str) -> None:
        """添加用户消息"""
        self.messages.append(Message("user", content))
        self._update_timestamp()
    
    def add_assistant_message(self, content: str) -> None:
        """添加助手消息"""
        self.messages.append(Message("assistant", content))
        self._update_timestamp()
    
    def add_system_message(self, content: str) -> None:
        """添加系统消息"""
        self.messages.append(Message("system", content))
        self._update_timestamp()
    
    def _update_timestamp(self) -> None:
        """更新时间戳"""
        self.metadata["last_updated"] = time.time()
    
    def get_messages(self, include_system: bool = True) -> List[Dict[str, str]]:
        """
        获取消息列表
        
        Args:
            include_system: 是否包含系统消息
            
        Returns:
            消息列表
        """
        if include_system:
            return [m.to_dict() for m in self.messages]
        else:
            return [m.to_dict() for m in self.messages if m.role != "system"]
    
    def get_recent_messages(self, count: int, include_system: bool = False) -> List[Dict[str, str]]:
        """
        获取最近的消息
        
        Args:
            count: 消息数量
            include_system: 是否包含系统消息
            
        Returns:
            最近的消息列表
        """
        if include_system:
            return [m.to_dict() for m in self.messages[-count:]]
        else:
            non_system = [m for m in self.messages if m.role != "system"]
            return [m.to_dict() for m in non_system[-count:]]
    
    def get_last_exchange(self) -> Tuple[Optional[Dict[str, str]], Optional[Dict[str, str]]]:
        """
        获取最后一轮对话（用户和助手的消息）
        
        Returns:
            (用户消息, 助手消息)的元组，如果不存在则为None
        """
        user_msg = None
        assistant_msg = None
        
        # 倒序查找
        for msg in reversed(self.messages):
            if not assistant_msg and msg.role == "assistant":
                assistant_msg = msg.to_dict()
            elif not user_msg and msg.role == "user":
                user_msg = msg.to_dict()
            
            if user_msg and assistant_msg:
                break
        
        return (user_msg, assistant_msg)
    
    def clear(self) -> None:
        """清除所有消息（保留系统消息）"""
        system_messages = [m for m in self.messages if m.role == "system"]
        self.messages = system_messages
        self._update_timestamp()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "conversation_id": self.conversation_id,
            "messages": [m.to_dict() for m in self.messages],
            "metadata": self.metadata
        }
    
    def summary(self) -> str:
        """生成对话摘要"""
        msg_count = len(self.messages)
        system_count = sum(1 for m in self.messages if m.role == "system")
        user_count = sum(1 for m in self.messages if m.role == "user")
        assistant_count = sum(1 for m in self.messages if m.role == "assistant")
        
        return (f"对话ID: {self.conversation_id}, "
                f"总消息: {msg_count} (系统: {system_count}, 用户: {user_count}, 助手: {assistant_count})")
    
    def __str__(self) -> str:
        return self.summary()


class ConversationMemory(Memory):
    """
    会话记忆
    
    管理用户与代理之间的对话历史
    """
    
    def __init__(self, max_conversations: int = 10, max_turns_per_conversation: Optional[int] = None):
        """
        初始化会话记忆
        
        Args:
            max_conversations: 最大会话数量
            max_turns_per_conversation: 每个会话的最大回合数
        """
        self.conversations: Dict[str, Conversation] = {}
        self.max_conversations = max_conversations
        self.max_turns = max_turns_per_conversation
        self.current_conversation_id: Optional[str] = None
    
    def add(self, content: Any, metadata: Optional[Dict[str, Any]] = None, system_name: Optional[str] = None) -> str:
        """
        添加一条记忆
        
        Args:
            content: 消息内容，应为元组(role, content_str)
            metadata: 元数据
            system_name: 系统名称（兼容旧测试）
            
        Returns:
            会话ID
        """
        if not self.current_conversation_id:
            self._create_new_conversation()
        
        conversation = self.conversations[self.current_conversation_id]
        
        # 检查内容格式
        if isinstance(content, tuple) and len(content) == 2:
            role, message_content = content
            
            # 根据角色添加消息
            if role == "user":
                conversation.add_user_message(message_content)
            elif role == "assistant":
                conversation.add_assistant_message(message_content)
            elif role == "system":
                conversation.add_system_message(message_content)
            else:
                logger.warning(f"未知角色类型: {role}")
            
            logger.debug(f"添加 {role} 消息到会话 {self.current_conversation_id[:8]}...")
            
            # 检查是否超过每个会话的最大回合数
            if self.max_turns and len(conversation.messages) > self.max_turns * 2:
                # 保留系统消息和最近的消息
                self._trim_conversation(self.current_conversation_id)
        else:
            logger.warning(f"消息格式错误: {content}")
        
        return self.current_conversation_id
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定ID的会话
        
        Args:
            memory_id: 会话ID
            
        Returns:
            会话内容
        """
        if memory_id in self.conversations:
            return self.conversations[memory_id].to_dict()
        return None
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索包含特定内容的会话
        
        Args:
            query: 查询字符串
            limit: 返回结果数量限制
            
        Returns:
            相关会话列表
        """
        query = query.lower()
        matches = []
        
        for conv_id, conversation in self.conversations.items():
            # 搜索消息内容
            matched_messages = []
            for msg in conversation.messages:
                if query in msg.content.lower():
                    matched_messages.append(msg.to_dict())
            
            if matched_messages:
                matches.append({
                    "conversation_id": conv_id,
                    "matched_messages": matched_messages[:3],  # 仅包含前3条匹配的消息
                    "total_matches": len(matched_messages),
                    "summary": conversation.summary()
                })
        
        # 按匹配消息数量排序
        matches.sort(key=lambda x: x["total_matches"], reverse=True)
        return matches[:limit]
    
    def clear(self) -> None:
        """清除所有会话"""
        self.conversations.clear()
        self.current_conversation_id = None
        logger.debug("清除所有会话")
    
    def start_new_conversation(self, system_message: Optional[str] = None) -> str:
        """
        开始新的会话
        
        Args:
            system_message: 系统消息
            
        Returns:
            新的会话ID
        """
        # 检查是否已达到最大会话数
        if len(self.conversations) >= self.max_conversations:
            self._remove_oldest_conversation()
        
        # 创建新会话
        self.current_conversation_id = str(int(time.time()))
        self.conversations[self.current_conversation_id] = Conversation(
            conversation_id=self.current_conversation_id,
            system_message=system_message
        )
        
        logger.debug(f"开始新会话: {self.current_conversation_id}")
        return self.current_conversation_id
    
    def _create_new_conversation(self, system_message: Optional[str] = None) -> str:
        """创建新的会话"""
        return self.start_new_conversation(system_message)
    
    def _remove_oldest_conversation(self) -> None:
        """移除最旧的会话"""
        if not self.conversations:
            return
        
        # 按创建时间排序
        oldest_id = min(
            self.conversations,
            key=lambda conv_id: self.conversations[conv_id].metadata["created_at"]
        )
        
        self.conversations.pop(oldest_id)
        logger.debug(f"移除最旧的会话: {oldest_id}")
    
    def _trim_conversation(self, conversation_id: str) -> None:
        """
        修剪会话，保留系统消息和最近的消息
        
        Args:
            conversation_id: 会话ID
        """
        if conversation_id not in self.conversations:
            return
        
        conversation = self.conversations[conversation_id]
        
        # 提取系统消息
        system_messages = [m for m in conversation.messages if m.role == "system"]
        
        # 提取最近的消息
        recent_messages = []
        if self.max_turns:
            non_system = [m for m in conversation.messages if m.role != "system"]
            recent_messages = non_system[-self.max_turns*2:]
        
        # 更新会话消息
        conversation.messages = system_messages + recent_messages
        conversation._update_timestamp()
        
        logger.debug(f"修剪会话 {conversation_id[:8]}..., 保留 {len(conversation.messages)} 条消息")
    
    def get_current_conversation(self) -> Optional[Conversation]:
        """获取当前会话"""
        if self.current_conversation_id and self.current_conversation_id in self.conversations:
            return self.conversations[self.current_conversation_id]
        return None
    
    def get_all_conversations(self) -> List[Dict[str, Any]]:
        """获取所有会话的摘要"""
        return [
            {
                "conversation_id": conv_id,
                "summary": conversation.summary(),
                "created_at": conversation.metadata["created_at"],
                "last_updated": conversation.metadata["last_updated"]
            }
            for conv_id, conversation in self.conversations.items()
        ]
