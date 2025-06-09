# 避免循环导入问题
from rainbow_agent.human_chat.message_router import MessageRouter
from rainbow_agent.human_chat.notification import NotificationService
from rainbow_agent.human_chat.presence_service import PresenceService
from rainbow_agent.human_chat.models import ChatSessionModel, ChatMessageModel
from rainbow_agent.human_chat.cache_manager import CacheManager
from rainbow_agent.human_chat.websocket_optimizer import WebSocketOptimizer
from rainbow_agent.human_chat.db_query_optimizer import DBQueryOptimizer

# 现在已经修复了缩进问题，可以导入HumanChatManager
from rainbow_agent.human_chat.chat_manager import HumanChatManager
# from rainbow_agent.human_chat.api import human_chat_bp, register_socketio_events

__all__ = [
    'MessageRouter',
    'NotificationService',
    'PresenceService',
    'ChatSessionModel',
    'ChatMessageModel',
    'CacheManager',
    'WebSocketOptimizer',
    'DBQueryOptimizer'
    # 'HumanChatManager',
    # 'human_chat_bp',
    # 'register_socketio_events'
]
