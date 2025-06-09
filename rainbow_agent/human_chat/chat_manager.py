from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import logging
import uuid
import asyncio
from functools import wraps

from .models import ChatSessionModel, ChatMessageModel
from .message_router import MessageRouter
from .presence_service import PresenceService
from .notification import NotificationService
from .cache_manager import CacheManager
from .websocket_optimizer import WebSocketOptimizer
from .db_query_optimizer import DBQueryOptimizer
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage

logger = logging.getLogger(__name__)

class HumanChatManager:
    """人类对话管理器"""
    
    def __init__(
        self,
        storage: Optional[UnifiedDialogueStorage] = None,
        message_router: Optional[MessageRouter] = None,
        presence_service: Optional[PresenceService] = None,
        cache_ttl: int = 300  # 缓存生存时间（秒）
    ):
        self.storage = storage or UnifiedDialogueStorage()
        self.message_router = message_router or MessageRouter()
        self.presence_service = presence_service or PresenceService()
        self.cache = CacheManager(ttl_seconds=cache_ttl)
        self.websocket_optimizer = WebSocketOptimizer()
        self.db_optimizer = DBQueryOptimizer()
        
        # 批量操作锁
        self._batch_locks = {}
        
        logger.info(f"人类对话管理器初始化成功，缓存TTL={cache_ttl}秒")
    
    async def create_private_chat(self, creator_id: str, recipient_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """创建私聊会话"""
        # 生成默认标题
        if not title:
            title = f"与 {recipient_id} 的私聊"
        
        # 创建会话元数据
        metadata = {
            "dialogue_type": "human_human_private",
            "participants": [creator_id, recipient_id],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # 调用统一存储创建会话
        session = await self.storage.create_session_async(creator_id, title, metadata)
        
        if session:
            logger.info(f"成功创建私聊会话: {session.get('id', '')}")
            
            # 通知接收者有新会话
            notification = {
                "type": "new_chat",
                "session_id": session.get("id"),
                "creator_id": creator_id,
                "title": title,
                "timestamp": datetime.now().isoformat()
            }
            await self.message_router.deliver_message_to_user(recipient_id, notification)
            
            return session
        else:
            logger.error("创建私聊会话失败")
            raise Exception("创建私聊会话失败")
    
    async def create_group_chat(self, creator_id: str, member_ids: List[str], title: Optional[str] = None) -> Dict[str, Any]:
        """创建群聊会话"""
        # 生成默认标题
        if not title:
            title = f"群聊 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 确保创建者在成员列表中
        all_members = list(set(member_ids + [creator_id]))
        
        # 创建会话元数据
        metadata = {
            "dialogue_type": "human_human_group",
            "participants": all_members,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "creator_id": creator_id,
            "status": "active"
        }
        
        # 调用统一存储创建会话
        session = await self.storage.create_session_async(creator_id, title, metadata)
        
        if session:
            logger.info(f"成功创建群聊会话: {session.get('id', '')}")
            
            # 通知所有成员有新群聊
            notification = {
                "type": "new_group_chat",
                "session_id": session.get("id"),
                "creator_id": creator_id,
                "title": title,
                "members": all_members,
                "timestamp": datetime.now().isoformat()
            }
            
            # 通知除创建者外的所有成员
            for member_id in all_members:
                if member_id != creator_id:
                    await self.message_router.deliver_message_to_user(member_id, notification)
            
            return session
        else:
            logger.error("创建群聊会话失败")
            raise Exception("创建群聊会话失败")
    
    async def send_message(self, session_id: str, sender_id: str, content: str, 
                          message_type: str = "text", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送消息"""
        # 获取会话信息
        session = await self.storage.get_session_async(session_id)
        if not session:
            logger.error(f"会话不存在: {session_id}")
            raise Exception(f"会话不存在: {session_id}")
        
        # 检查发送者是否在会话参与者中
        participants = session.get("metadata", {}).get("participants", [])
        if sender_id not in participants:
            logger.error(f"用户 {sender_id} 不是会话 {session_id} 的参与者")
            raise Exception(f"用户不是会话参与者")
        
        # 创建消息
        message_metadata = {
            "sender_id": sender_id,
            "message_type": message_type,
            "human_chat": True,  # 标记为人类对话
            **(metadata or {})
        }
        
        # 使用DB优化器批量处理
        stored_message = await self.db_optimizer.create_message(
            self.storage,
            session_id=session_id,
            role="human",  # 使用human作为角色，保持与现有系统兼容
            content=content,
            metadata=message_metadata
        )
        
        if stored_message:
            logger.info(f"消息已存储: {stored_message.get('id', '')}")
            
            # 更新会话最后活动时间
            await self.storage.update_session_async(
                session_id, 
                {"metadata.updated_at": datetime.now().isoformat()}
            )
            
            # 准备要发送的消息数据
            message_to_send = {
                "type": "chat_message",
                "message_id": stored_message.get("id"),
                "session_id": session_id,
                "sender_id": sender_id,
                "content": content,
                "message_type": message_type,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # 获取接收者列表（除发送者外的所有参与者）
            recipients = [p for p in participants if p != sender_id]
            
            # 使用WebSocket优化器批量发送消息
            for recipient in recipients:
                self.websocket_optimizer.queue_message(recipient, message_to_send)
            
            # 如果是重要消息类型，立即发送
            if message_type in ["system", "urgent", "notification"]:
                for recipient in recipients:
                    await self.websocket_optimizer.send_immediate(recipient)
            
            return stored_message
        else:
            logger.error("消息存储失败")
            raise Exception("消息存储失败")
    
    async def mark_as_read(self, message_id: str, user_id: str) -> bool:
        """标记消息为已读"""
        # 获取消息
        message = await self.storage.get_turn_async(message_id)
        if not message:
            logger.error(f"消息不存在: {message_id}")
            return False
        
        # 检查用户是否是会话参与者
        session_id = message.get("session_id")
        session = await self.storage.get_session_async(session_id)
        participants = session.get("metadata", {}).get("participants", [])
        
        if user_id not in participants:
            logger.error(f"用户 {user_id} 不是会话 {session_id} 的参与者")
            return False
        
        # 更新消息元数据，添加已读时间
        read_at_key = f"metadata.read_at.{user_id}"
        await self.storage.update_turn_async(
            message_id, 
            {read_at_key: datetime.now().isoformat()}
        )
        
        # 通知发送者消息已读
        sender_id = message.get("metadata", {}).get("sender_id")
        if sender_id and sender_id != user_id:
            read_notification = {
                "type": "message_read",
                "message_id": message_id,
                "session_id": session_id,
                "reader_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            await self.message_router.deliver_message_to_user(sender_id, read_notification)
        
        return True
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有会话列表"""
        # 尝试从缓存获取会话列表
        cache_key = f"user_sessions:{user_id}"
        cached_sessions = self.cache.get(cache_key)
        if cached_sessions:
            logger.info(f"从缓存获取用户会话列表: {user_id}")
            return cached_sessions
            
        # 查询用户参与的所有会话
        sessions = await self.db_optimizer.get_sessions(self.storage)
        
        # 过滤出用户参与的人类对话会话
        user_sessions = []
        for session in sessions:
            metadata = session.get("metadata", {})
            participants = metadata.get("participants", [])
            dialogue_type = metadata.get("dialogue_type", "")
            
            # 只返回人类对话类型且用户是参与者的会话
            if user_id in participants and dialogue_type.startswith("human_human"):
                # 格式化会话信息
                formatted_session = {
                    "id": session.get("id"),
                    "title": session.get("title"),
                    "is_group": dialogue_type == "human_human_group",
                    "participants": participants,
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at"),
                    "last_message": None,  # 将在下面填充
                    "unread_count": 0  # 将在下面填充
                }
                
                # 获取最后一条消息
                last_message = await self._get_last_message(session.get("id"))
                if last_message:
                    formatted_session["last_message"] = {
                        "id": last_message.get("id"),
                        "content": last_message.get("content"),
                        "sender_id": last_message.get("metadata", {}).get("sender_id"),
                        "created_at": last_message.get("created_at")
                    }
                
                # 计算未读消息数
                unread_count = await self._count_unread_messages(session.get("id"), user_id)
                formatted_session["unread_count"] = unread_count
                
                user_sessions.append(formatted_session)
        
        # 按最后更新时间排序，最新的在前面
        user_sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
        
        # 缓存结果
        self.cache.set(cache_key, user_sessions)
        
        return user_sessions
    
    async def get_session_messages(self, session_id: str, user_id: str, limit: int = 20, before_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取会话消息列表"""
        # 尝试从缓存获取会话消息
        cache_key = f"session_messages:{session_id}:{before_id}:{limit}"
        cached_messages = self.cache.get(cache_key)
        if cached_messages:
            logger.info(f"从缓存获取会话消息: {session_id}")
            return cached_messages
            
        # 从数据库获取会话
        session = await self.storage.get_session_async(session_id)
        if not session:
            logger.error(f"会话 {session_id} 不存在")
            raise Exception(f"会话不存在")
        
        # 检查用户是否是会话参与者
        metadata = session.get("metadata", {})
        participants = metadata.get("participants", [])
        if user_id not in participants:
            logger.error(f"用户 {user_id} 不是会话 {session_id} 的参与者")
            raise Exception(f"用户不是会话参与者")
        
        # 使用DB优化器批量获取会话消息
        turns = await self.db_optimizer.get_messages(self.storage, session_id)
        
        # 过滤出人类对话消息
        human_chat_messages = []
        for turn in turns:
            # 只处理标记为人类对话的消息
            if turn.get("metadata", {}).get("human_chat", False):
                human_chat_messages.append(turn)
        
        # 按时间排序，最新的在前面
        human_chat_messages.sort(key=lambda m: m.get("created_at", ""), reverse=True)
        
        # 分页处理
        if before_id:
            # 找到指定消息的索引
            before_index = next((i for i, m in enumerate(human_chat_messages) if m.get("id") == before_id), None)
            if before_index is not None:
                # 获取指定消息之前的消息
                human_chat_messages = human_chat_messages[before_index + 1:before_index + 1 + limit]
            else:
                # 如果找不到指定消息，返回最新的消息
                human_chat_messages = human_chat_messages[:limit]
        else:
            # 如果没有指定before_id，返回最新的消息
            human_chat_messages = human_chat_messages[:limit]
        
        # 格式化消息
        formatted_messages = []
        for message in human_chat_messages:
            formatted_message = {
                "id": message.get("id"),
                "session_id": session_id,
                "sender_id": message.get("metadata", {}).get("sender_id"),
                "content": message.get("content"),
                "content_type": message.get("metadata", {}).get("message_type", "text"),
                "created_at": message.get("created_at"),
                "read_by": message.get("metadata", {}).get("read_at", {}),
                "metadata": {k: v for k, v in message.get("metadata", {}).items() if k not in ["sender_id", "message_type", "human_chat", "read_at"]}
            }
            formatted_messages.append(formatted_message)
        
        # 反转顺序，使最早的消息在前面
        formatted_messages.reverse()
        
        # 缓存结果
        self.cache.set(cache_key, formatted_messages)
        
        return formatted_messages
    
    async def notify_typing(self, session_id: str, user_id: str) -> bool:
        """通知用户正在输入"""
        # 获取会话信息
        session = await self.storage.get_session_async(session_id)
        if not session:
            logger.error(f"会话不存在: {session_id}")
            return False
        
        # 检查用户是否是会话参与者
        metadata = session.get("metadata", {})
        participants = metadata.get("participants", [])
        if user_id not in participants:
            logger.error(f"用户 {user_id} 不是会话 {session_id} 的参与者")
            return False
        
        # 准备通知数据
        typing_notification = {
            "type": "typing",
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 获取接收者列表（除发送者外的所有参与者）
        recipients = [p for p in participants if p != user_id]
        
        # 使用WebSocket优化器发送通知
        for recipient in recipients:
            self.websocket_optimizer.queue_message(recipient, typing_notification)
            # 立即发送打字通知，不等待批处理
            await self.websocket_optimizer.send_immediate(recipient)
        
        return True
    
    async def _get_last_message(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话的最后一条消息"""
        # 尝试从缓存获取最后一条消息
        cache_key = f"last_message:{session_id}"
        cached_message = self.cache.get(cache_key)
        if cached_message:
            return cached_message
            
        # 获取会话的所有消息
        turns = await self.storage.list_turns_async(session_id)
        
        # 过滤出人类对话消息
        human_chat_messages = [turn for turn in turns if turn.get("metadata", {}).get("human_chat", False)]
        
        # 如果没有消息，返回None
        if not human_chat_messages:
            return None
        
        # 按时间排序，找出最新的消息
        human_chat_messages.sort(key=lambda m: m.get("created_at", ""), reverse=True)
        last_message = human_chat_messages[0] if human_chat_messages else None
        
        # 缓存结果
        if last_message:
            self.cache.set(cache_key, last_message)
            
        return last_message
    
    async def _count_unread_messages(self, session_id: str, user_id: str) -> int:
        """计算用户在会话中的未读消息数"""
        # 尝试从缓存获取未读消息数
        cache_key = f"unread_count:{session_id}:{user_id}"
        cached_count = self.cache.get(cache_key)
        if cached_count is not None:
            return cached_count
            
        # 获取会话的所有消息
        turns = await self.storage.list_turns_async(session_id)
        
        # 过滤出人类对话消息
        human_chat_messages = [turn for turn in turns if turn.get("metadata", {}).get("human_chat", False)]
        
        # 计算未读消息数
        unread_count = 0
        for message in human_chat_messages:
            # 跳过用户自己发送的消息
            if message.get("metadata", {}).get("sender_id") == user_id:
                continue
                
            # 检查消息是否已读
            read_at = message.get("metadata", {}).get("read_at", {})
            if user_id not in read_at:
                unread_count += 1
        
        # 缓存结果
        self.cache.set(cache_key, unread_count)
        
        return unread_count
