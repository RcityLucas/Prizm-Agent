import os
import sys
from datetime import datetime
import uuid
from flask import Flask, send_file, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room

# 创建Flask应用
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 模拟数据存储
class MockStorage:
    def __init__(self):
        self.sessions = {}
        self.messages = {}
    
    def create_session(self, creator_id, participants, title=None, is_group=False):
        session_id = str(uuid.uuid4())[:8]
        
        session = {
            "id": session_id,
            "title": title or f"会话 {session_id}",
            "creator_id": creator_id,
            "participants": participants,
            "is_group": is_group,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_message": None,
            "unread_count": {}
        }
        
        self.sessions[session_id] = session
        self.messages[session_id] = []
        
        return session
    
    def get_session(self, session_id):
        return self.sessions.get(session_id)
    
    def get_user_sessions(self, user_id):
        return [session for session in self.sessions.values() 
                if user_id in session["participants"]]
    
    def create_message(self, session_id, sender_id, content, content_type="text"):
        if session_id not in self.sessions:
            return None
        
        message_id = str(uuid.uuid4())[:8]
        
        message = {
            "id": message_id,
            "session_id": session_id,
            "sender_id": sender_id,
            "content": content,
            "content_type": content_type,
            "created_at": datetime.now().isoformat(),
            "read_by": {sender_id: datetime.now().isoformat()}
        }
        
        self.messages[session_id].append(message)
        
        # 更新会话的最后一条消息
        self.sessions[session_id]["last_message"] = message
        self.sessions[session_id]["updated_at"] = message["created_at"]
        
        # 更新未读计数
        for participant in self.sessions[session_id]["participants"]:
            if participant != sender_id:
                if participant not in self.sessions[session_id]["unread_count"]:
                    self.sessions[session_id]["unread_count"][participant] = 0
                self.sessions[session_id]["unread_count"][participant] += 1
        
        return message
    
    def get_session_messages(self, session_id, limit=50, before_id=None):
        if session_id not in self.messages:
            return []
        
        messages = self.messages[session_id]
        
        if before_id:
            index = next((i for i, msg in enumerate(messages) if msg["id"] == before_id), None)
            if index is not None:
                messages = messages[:index]
        
        return messages[-limit:] if limit else messages
    
    def mark_message_as_read(self, message_id, user_id):
        for session_id, messages in self.messages.items():
            for message in messages:
                if message["id"] == message_id:
                    message["read_by"][user_id] = datetime.now().isoformat()
                    
                    # 重置未读计数
                    if user_id in self.sessions[session_id]["unread_count"]:
                        self.sessions[session_id]["unread_count"][user_id] = 0
                    
                    return True
        
        return False

# 创建模拟存储实例
storage = MockStorage()

# 用户连接管理
user_connections = {}

# 路由: 提供前端测试页面
@app.route('/')
def index():
    return send_file('human_chat_frontend_test.html')

# API路由: 创建私聊会话
@app.route('/api/human-chat/sessions/private', methods=['POST'])
def create_private_chat():
    data = request.json
    user_id = request.headers.get('X-User-ID')
    
    recipient_id = data.get('recipient_id')
    title = data.get('title')
    
    if not user_id or not recipient_id:
        return jsonify({"error": "Missing required parameters"}), 400
    
    # 创建私聊会话
    session = storage.create_session(
        creator_id=user_id,
        participants=[user_id, recipient_id],
        title=title,
        is_group=False
    )
    
    # 通知接收者
    if recipient_id in user_connections:
        socketio.emit('session_update', session, room=user_connections[recipient_id])
    
    return jsonify({"session": session})

# API路由: 创建群聊会话
@app.route('/api/human-chat/sessions/group', methods=['POST'])
def create_group_chat():
    data = request.json
    user_id = request.headers.get('X-User-ID')
    
    member_ids = data.get('member_ids', [])
    title = data.get('title')
    
    if not user_id or not member_ids:
        return jsonify({"error": "Missing required parameters"}), 400
    
    # 确保创建者在参与者列表中
    participants = list(set([user_id] + member_ids))
    
    # 创建群聊会话
    session = storage.create_session(
        creator_id=user_id,
        participants=participants,
        title=title,
        is_group=True
    )
    
    # 通知所有参与者
    for participant_id in participants:
        if participant_id != user_id and participant_id in user_connections:
            socketio.emit('session_update', session, room=user_connections[participant_id])
    
    return jsonify({"session": session})

# API路由: 获取用户会话列表
@app.route('/api/human-chat/sessions', methods=['GET'])
def get_user_sessions():
    user_id = request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
    
    # 获取用户会话列表
    sessions = storage.get_user_sessions(user_id)
    
    # 按最后更新时间排序
    sessions.sort(key=lambda s: s["updated_at"], reverse=True)
    
    return jsonify({"sessions": sessions})

# API路由: 获取会话详情
@app.route('/api/human-chat/sessions/<session_id>', methods=['GET'])
def get_session_details(session_id):
    user_id = request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
    
    # 获取会话详情
    session = storage.get_session(session_id)
    
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    # 检查用户是否是会话参与者
    if user_id not in session["participants"]:
        return jsonify({"error": "Unauthorized"}), 403
    
    # 添加参与者在线状态
    session["participant_status"] = {
        participant_id: participant_id in user_connections
        for participant_id in session["participants"]
    }
    
    return jsonify({"session": session})

# API路由: 发送消息
@app.route('/api/human-chat/sessions/<session_id>/messages', methods=['POST'])
def send_message(session_id):
    data = request.json
    user_id = request.headers.get('X-User-ID')
    
    content = data.get('content')
    content_type = data.get('content_type', 'text')
    
    if not user_id or not content:
        return jsonify({"error": "Missing required parameters"}), 400
    
    # 获取会话
    session = storage.get_session(session_id)
    
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    # 检查用户是否是会话参与者
    if user_id not in session["participants"]:
        return jsonify({"error": "Unauthorized"}), 403
    
    # 创建消息
    message = storage.create_message(
        session_id=session_id,
        sender_id=user_id,
        content=content,
        content_type=content_type
    )
    
    # 通知其他参与者
    for participant_id in session["participants"]:
        if participant_id != user_id and participant_id in user_connections:
            socketio.emit('new_message', message, room=user_connections[participant_id])
    
    return jsonify({"message": message})

# API路由: 获取会话消息
@app.route('/api/human-chat/sessions/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    user_id = request.headers.get('X-User-ID')
    
    limit = request.args.get('limit', 50, type=int)
    before_id = request.args.get('before_id')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
    
    # 获取会话
    session = storage.get_session(session_id)
    
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    # 检查用户是否是会话参与者
    if user_id not in session["participants"]:
        return jsonify({"error": "Unauthorized"}), 403
    
    # 获取会话消息
    messages = storage.get_session_messages(session_id, limit, before_id)
    
    return jsonify({"messages": messages})

# API路由: 标记消息已读
@app.route('/api/human-chat/messages/<message_id>/read', methods=['POST'])
def mark_message_as_read(message_id):
    user_id = request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
    
    # 标记消息已读
    result = storage.mark_message_as_read(message_id, user_id)
    
    if not result:
        return jsonify({"error": "Message not found"}), 404
    
    # 通知消息发送者
    for session_id, messages in storage.messages.items():
        for message in messages:
            if message["id"] == message_id:
                sender_id = message["sender_id"]
                if sender_id != user_id and sender_id in user_connections:
                    socketio.emit('message_read', {
                        "message_id": message_id,
                        "user_id": user_id,
                        "session_id": session_id
                    }, room=user_connections[sender_id])
                break
    
    return jsonify({"success": True})

# API路由: 通知正在输入
@app.route('/api/human-chat/sessions/<session_id>/typing', methods=['POST'])
def notify_typing(session_id):
    user_id = request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
    
    # 获取会话
    session = storage.get_session(session_id)
    
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    # 检查用户是否是会话参与者
    if user_id not in session["participants"]:
        return jsonify({"error": "Unauthorized"}), 403
    
    # 通知其他参与者
    for participant_id in session["participants"]:
        if participant_id != user_id and participant_id in user_connections:
            socketio.emit('typing', {
                "session_id": session_id,
                "user_id": user_id
            }, room=user_connections[participant_id])
    
    return jsonify({"success": True})

# WebSocket事件: 用户连接
@socketio.on('connect')
def handle_connect():
    print('Client connected')

# WebSocket事件: 用户断开连接
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    
    # 找到对应的用户ID
    for user_id, sid in user_connections.items():
        if sid == request.sid:
            del user_connections[user_id]
            print(f'User {user_id} disconnected')
            break

# WebSocket事件: 注册用户
@socketio.on('register_user')
def handle_register_user(data):
    user_id = data.get('user_id')
    
    if not user_id:
        return
    
    # 注册用户连接
    user_connections[user_id] = request.sid
    
    print(f'User {user_id} registered with connection {request.sid}')

# 启动服务器
if __name__ == '__main__':
    print("测试服务器启动中...")
    print("访问 http://localhost:5000 进行测试")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)