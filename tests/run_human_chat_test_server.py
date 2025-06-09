import os
import sys
from flask import Flask, send_file, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入必要的模块
from rainbow_agent.human_chat.chat_manager import HumanChatManager
from rainbow_agent.human_chat.message_router import MessageRouter
from rainbow_agent.human_chat.presence_service import PresenceService
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage

# 创建Flask应用
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 创建模拟存储
class MockStorage(UnifiedDialogueStorage):
    def __init__(self):
        self.sessions = {}
        self.turns = {}
        self.session_counter = 0
        self.turn_counter = 0
    
    async def create_session_async(self, title, metadata):
        session_id = f"session_{self.session_counter}"
        self.session_counter += 1
        
        session = {
            "id": session_id,
            "title": title,
            "metadata": metadata,
            "created_at": "2025-06-09T14:00:00Z",
            "updated_at": "2025-06-09T14:00:00Z"
        }
        
        self.sessions[session_id] = session
        return session
    
    async def get_session_async(self, session_id):
        return self.sessions.get(session_id)
    
    async def update_session_async(self, session_id, updates):
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            self.sessions[session_id]["updated_at"] = "2025-06-09T14:00:00Z"
            return self.sessions[session_id]
        return None
    
    async def list_sessions_async(self, filter_dict=None):
        if not filter_dict:
            return list(self.sessions.values())
        
        result = []
        for session in self.sessions.values():
            match = True
            for key, value in filter_dict.items():
                if key == "metadata":
                    for meta_key, meta_value in value.items():
                        if meta_key not in session.get("metadata", {}) or session["metadata"][meta_key] != meta_value:
                            match = False
                            break
                elif key not in session or session[key] != value:
                    match = False
                    break
            
            if match:
                result.append(session)
        
        return result
    
    async def create_turn_async(self, session_id, role, content, metadata):
        turn_id = f"turn_{self.turn_counter}"
        self.turn_counter += 1
        
        turn = {
            "id": turn_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata,
            "created_at": "2025-06-09T14:00:00Z"
        }
        
        if session_id not in self.turns:
            self.turns[session_id] = []
        
        self.turns[session_id].append(turn)
        return turn
    
    async def get_turn_async(self, turn_id):
        for turns in self.turns.values():
            for turn in turns:
                if turn["id"] == turn_id:
                    return turn
        return None
    
    async def update_turn_async(self, turn_id, updates):
        for session_id, turns in self.turns.items():
            for i, turn in enumerate(turns):
                if turn["id"] == turn_id:
                    self.turns[session_id][i].update(updates)
                    return self.turns[session_id][i]
        return None
    
    async def list_turns_async(self, session_id, filter_dict=None, limit=None, before_id=None):
        if session_id not in self.turns:
            return []
        
        turns = self.turns[session_id]
        
        if filter_dict:
            filtered_turns = []
            for turn in turns:
                match = True
                for key, value in filter_dict.items():
                    if key == "metadata":
                        for meta_key, meta_value in value.items():
                            if meta_key not in turn.get("metadata", {}) or turn["metadata"][meta_key] != meta_value:
                                match = False
                                break
                    elif key not in turn or turn[key] != value:
                        match = False
                        break
                
                if match:
                    filtered_turns.append(turn)
            
            turns = filtered_turns
        
        if before_id:
            before_index = None
            for i, turn in enumerate(turns):
                if turn["id"] == before_id:
                    before_index = i
                    break
            
            if before_index is not None:
                turns = turns[:before_index]
        
        if limit:
            turns = turns[-limit:]
        
        return turns

# 创建模拟消息路由器
class MockMessageRouter:
    def __init__(self, socketio):
        self.socketio = socketio
        self.user_connections = {}
    
    def register_user_connection(self, user_id, connection_id):
        self.user_connections[user_id] = connection_id
    
    def unregister_user_connection(self, user_id):
        if user_id in self.user_connections:
            del self.user_connections[user_id]
    
    def route_message(self, message):
        if "session_id" in message and "metadata" in message and "sender_id" in message["metadata"]:
            session_id = message["session_id"]
            sender_id = message["metadata"]["sender_id"]
            
            # 获取会话信息
            chat_manager.storage.get_session_async(session_id).add_done_callback(
                lambda f: self._handle_session_info(f.result(), message)
            )
    
    def _handle_session_info(self, session, message):
        if not session:
            return
        
        participants = session["metadata"].get("participants", [])
        sender_id = message["metadata"]["sender_id"]
        
        # 向所有参与者发送消息
        for user_id in participants:
            if user_id != sender_id and user_id in self.user_connections:
                self.socketio.emit('new_message', message, room=self.user_connections[user_id])
    
    def deliver_message_to_user(self, user_id, message_type, data):
        if user_id in self.user_connections:
            self.socketio.emit(message_type, data, room=self.user_connections[user_id])

# 创建模拟在线状态服务
class MockPresenceService:
    def __init__(self):
        self.online_users = set()
    
    def register_user_online(self, user_id):
        self.online_users.add(user_id)
    
    def register_user_offline(self, user_id):
        if user_id in self.online_users:
            self.online_users.remove(user_id)
    
    def is_user_online(self, user_id):
        return user_id in self.online_users

# 创建服务实例
storage = MockStorage()
message_router = MockMessageRouter(socketio)
presence_service = MockPresenceService()
chat_manager = HumanChatManager(storage, message_router, presence_service)

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
    future = chat_manager.create_private_chat(user_id, recipient_id, title)
    
    # 等待异步操作完成
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    session = loop.run_until_complete(future)
    
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
    
    # 创建群聊会话
    future = chat_manager.create_group_chat(user_id, member_ids, title)
    
    # 等待异步操作完成
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    session = loop.run_until_complete(future)
    
    return jsonify({"session": session})

# API路由: 获取用户会话列表
@app.route('/api/human-chat/sessions', methods=['GET'])
def get_user_sessions():
    user_id = request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
    
    # 获取用户会话列表
    future = chat_manager.get_user_sessions(user_id)
    
    # 等待异步操作完成
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    sessions = loop.run_until_complete(future)
    
    return jsonify({"sessions": sessions})

# API路由: 获取会话详情
@app.route('/api/human-chat/sessions/<session_id>', methods=['GET'])
def get_session_details(session_id):
    user_id = request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
    
    # 获取会话详情
    future = chat_manager.get_session_details(session_id, user_id)
    
    # 等待异步操作完成
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    session = loop.run_until_complete(future)
    
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
    
    # 发送消息
    future = chat_manager.send_message(session_id, user_id, content, content_type)
    
    # 等待异步操作完成
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    message = loop.run_until_complete(future)
    
    return jsonify({"message": message})

# API路由: 获取会话消息
@app.route('/api/human-chat/sessions/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    user_id = request.headers.get('X-User-ID')
    
    limit = request.args.get('limit', 50, type=int)
    before_id = request.args.get('before_id')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
    
    # 获取会话消息
    future = chat_manager.get_session_messages(session_id, user_id, limit, before_id)
    
    # 等待异步操作完成
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    messages = loop.run_until_complete(future)
    
    return jsonify({"messages": messages})

# API路由: 标记消息已读
@app.route('/api/human-chat/messages/<message_id>/read', methods=['POST'])
def mark_message_as_read(message_id):
    user_id = request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
    
    # 标记消息已读
    future = chat_manager.mark_as_read(message_id, user_id)
    
    # 等待异步操作完成
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(future)
    
    return jsonify({"success": result})

# API路由: 通知正在输入
@app.route('/api/human-chat/sessions/<session_id>/typing', methods=['POST'])
def notify_typing(session_id):
    user_id = request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400
    
    # 通知正在输入
    future = chat_manager.notify_typing(session_id, user_id)
    
    # 等待异步操作完成
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(future)
    
    return jsonify({"success": result})

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
            # 注销用户连接
            message_router.unregister_user_connection(user_id)
            presence_service.register_user_offline(user_id)
            del user_connections[user_id]
            break

# WebSocket事件: 注册用户
@socketio.on('register_user')
def handle_register_user(data):
    user_id = data.get('user_id')
    
    if not user_id:
        return
    
    # 注册用户连接
    user_connections[user_id] = request.sid
    message_router.register_user_connection(user_id, request.sid)
    presence_service.register_user_online(user_id)
    
    print(f'User {user_id} registered with connection {request.sid}')

# 启动服务器
if __name__ == '__main__':
    print("测试服务器启动中...")
    print("访问 http://localhost:5000 进行测试")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
