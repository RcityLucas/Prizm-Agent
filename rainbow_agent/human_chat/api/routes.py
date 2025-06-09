from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit, join_room, leave_room
import logging
from typing import Dict, List, Any, Optional
import traceback

from rainbow_agent.human_chat.chat_manager import HumanChatManager
from rainbow_agent.auth.utils import get_current_user_id, auth_required

# 创建蓝图
human_chat_bp = Blueprint('human_chat', __name__, url_prefix='/api/human-chat')
logger = logging.getLogger(__name__)

# 获取聊天管理器实例
def get_chat_manager():
    """获取聊天管理器实例
    如果应用上下文中没有，则创建一个新实例
    """
    if not hasattr(current_app, 'human_chat_manager'):
        current_app.human_chat_manager = HumanChatManager()
    return current_app.human_chat_manager

# HTTP API路由
@human_chat_bp.route('/sessions', methods=['POST'])
@auth_required
async def create_chat_session():
    """创建聊天会话"""
    try:
        data = request.json
        user_id = get_current_user_id()
        
        # 验证必要参数
        if not data or 'participants' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required parameters: participants"
            }), 400
        
        participants = data.get('participants', [])
        title = data.get('title')
        is_group = data.get('is_group', False)
        metadata = data.get('metadata', {})
        
        # 确保创建者在参与者列表中
        if user_id not in participants:
            participants.append(user_id)
        
        # 创建会话
        chat_manager = get_chat_manager()
        session = await chat_manager.create_session(
            creator_id=user_id,
            participants=participants,
            title=title,
            is_group=is_group,
            metadata=metadata
        )
        
        return jsonify({
            "success": True,
            "session": session
        }), 201
        
    except Exception as e:
        logger.error(f"创建聊天会话失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@human_chat_bp.route('/sessions', methods=['GET'])
@auth_required
async def get_user_sessions():
    """获取用户的所有会话"""
    try:
        user_id = get_current_user_id()
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        chat_manager = get_chat_manager()
        sessions = await chat_manager.get_user_sessions(user_id, limit, offset)
        
        return jsonify({
            "success": True,
            "sessions": sessions
        })
        
    except Exception as e:
        logger.error(f"获取用户会话失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@human_chat_bp.route('/sessions/<session_id>', methods=['GET'])
@auth_required
async def get_session(session_id):
    """获取会话详情"""
    try:
        user_id = get_current_user_id()
        
        chat_manager = get_chat_manager()
        session = await chat_manager.get_session(session_id, user_id)
        
        if not session:
            return jsonify({
                "success": False,
                "error": "Session not found or you don't have permission"
            }), 404
        
        return jsonify({
            "success": True,
            "session": session
        })
        
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@human_chat_bp.route('/sessions/<session_id>/messages', methods=['POST'])
@auth_required
async def send_message(session_id):
    """发送消息"""
    try:
        data = request.json
        user_id = get_current_user_id()
        
        # 验证必要参数
        if not data or 'content' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: content"
            }), 400
        
        content = data.get('content')
        content_type = data.get('content_type', 'text')
        metadata = data.get('metadata', {})
        
        # 发送消息
        chat_manager = get_chat_manager()
        message = await chat_manager.send_message(
            session_id=session_id,
            sender_id=user_id,
            content=content,
            content_type=content_type,
            metadata=metadata
        )
        
        return jsonify({
            "success": True,
            "message": message
        }), 201
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"发送消息失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@human_chat_bp.route('/sessions/<session_id>/messages', methods=['GET'])
@auth_required
async def get_messages(session_id):
    """获取会话消息"""
    try:
        user_id = get_current_user_id()
        limit = request.args.get('limit', 50, type=int)
        before_id = request.args.get('before_id')
        
        chat_manager = get_chat_manager()
        messages = await chat_manager.get_messages(session_id, user_id, limit, before_id)
        
        return jsonify({
            "success": True,
            "messages": messages
        })
        
    except Exception as e:
        logger.error(f"获取会话消息失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@human_chat_bp.route('/messages/<message_id>/read', methods=['POST'])
@auth_required
async def mark_message_read(message_id):
    """标记消息为已读"""
    try:
        user_id = get_current_user_id()
        
        chat_manager = get_chat_manager()
        result = await chat_manager.mark_as_read(message_id, user_id)
        
        return jsonify({
            "success": result
        })
        
    except Exception as e:
        logger.error(f"标记消息已读失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@human_chat_bp.route('/sessions/<session_id>/typing', methods=['POST'])
@auth_required
async def notify_typing(session_id):
    """通知用户正在输入"""
    try:
        user_id = get_current_user_id()
        
        chat_manager = get_chat_manager()
        await chat_manager.notify_typing(session_id, user_id)
        
        return jsonify({
            "success": True
        })
        
    except Exception as e:
        logger.error(f"通知用户正在输入失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# WebSocket事件处理
def register_socketio_events(socketio):
    """注册Socket.IO事件处理器
    
    Args:
        socketio: Flask-SocketIO实例
    """
    
    @socketio.on('connect')
    def handle_connect():
        """处理连接事件"""
        try:
            user_id = get_current_user_id()
            if not user_id:
                return False  # 拒绝未认证的连接
                
            logger.info(f"用户 {user_id} WebSocket连接成功")
            
            # 注册用户连接
            chat_manager = get_chat_manager()
            chat_manager.register_connection(user_id)
            
            # 更新用户在线状态
            chat_manager.presence_service.set_user_online(user_id)
            
            return True
        except Exception as e:
            logger.error(f"WebSocket连接处理失败: {e}\n{traceback.format_exc()}")
            return False
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """处理断开连接事件"""
        try:
            user_id = get_current_user_id()
            if not user_id:
                return
                
            logger.info(f"用户 {user_id} WebSocket断开连接")
            
            # 注销用户连接
            chat_manager = get_chat_manager()
            chat_manager.unregister_connection(user_id)
            
            # 更新用户离线状态
            chat_manager.presence_service.set_user_offline(user_id)
        except Exception as e:
            logger.error(f"WebSocket断开连接处理失败: {e}\n{traceback.format_exc()}")
    
    @socketio.on('join_session')
    def handle_join_session(data):
        """处理加入会话事件"""
        try:
            user_id = get_current_user_id()
            if not user_id:
                return
                
            session_id = data.get('session_id')
            if not session_id:
                emit('error', {'message': 'Missing session_id'}, room=request.sid)
                return
                
            # 加入会话房间
            join_room(f"session_{session_id}")
            logger.info(f"用户 {user_id} 加入会话 {session_id} 的房间")
            
            # 通知其他参与者
            chat_manager = get_chat_manager()
            chat_manager.notify_user_joined(session_id, user_id)
        except Exception as e:
            logger.error(f"加入会话处理失败: {e}\n{traceback.format_exc()}")
            emit('error', {'message': str(e)}, room=request.sid)
    
    @socketio.on('leave_session')
    def handle_leave_session(data):
        """处理离开会话事件"""
        try:
            user_id = get_current_user_id()
            if not user_id:
                return
                
            session_id = data.get('session_id')
            if not session_id:
                emit('error', {'message': 'Missing session_id'}, room=request.sid)
                return
                
            # 离开会话房间
            leave_room(f"session_{session_id}")
            logger.info(f"用户 {user_id} 离开会话 {session_id} 的房间")
        except Exception as e:
            logger.error(f"离开会话处理失败: {e}\n{traceback.format_exc()}")
            emit('error', {'message': str(e)}, room=request.sid)
    
    @socketio.on('typing')
    def handle_typing(data):
        """处理正在输入事件"""
        try:
            user_id = get_current_user_id()
            if not user_id:
                return
                
            session_id = data.get('session_id')
            if not session_id:
                emit('error', {'message': 'Missing session_id'}, room=request.sid)
                return
                
            # 通知其他参与者
            chat_manager = get_chat_manager()
            chat_manager.notify_typing(session_id, user_id)
        except Exception as e:
            logger.error(f"处理正在输入事件失败: {e}\n{traceback.format_exc()}")
            emit('error', {'message': str(e)}, room=request.sid)