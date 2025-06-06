#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SurrealDB API服务器

使用SurrealDB作为存储后端的API服务器，提供对话管理和代理交互功能。
"""
import os
import sys
import json
import logging
import uuid
from datetime import datetime

# 将项目根目录添加到Python路径
import pathlib
root_dir = str(pathlib.Path(__file__).absolute().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from rainbow_agent.storage.config import get_surreal_config
from rainbow_agent.storage.session_manager import SessionManager
from rainbow_agent.storage.turn_manager import TurnManager
from rainbow_agent.storage.async_utils import run_async
from rainbow_agent.ai.openai_service import OpenAIService
from rainbow_agent.utils.logger import get_logger
from rainbow_agent.core.dialogue_manager import DialogueManager, DIALOGUE_TYPES

# 配置日志
logger = get_logger(__name__)

# 创建Flask应用
app = Flask(__name__, static_folder='static')
CORS(app)  # 启用CORS，允许前端跨域请求

# 全局变量
session_manager = None
turn_manager = None
openai_service = None
dialogue_manager = None

# 初始化存储系统
def init_storage():
    """初始化存储系统，先尝试SurrealDB，如果失败则使用SQLite作为后备"""
    global session_manager, turn_manager
    
    try:
        if session_manager is None or turn_manager is None:
            logger.info("hu..")
            
            # 先尝试使用SurrealDB
            try:
                from rainbow_agent.storage.session_manager import SessionManager
                from rainbow_agent.storage.turn_manager import TurnManager
                from rainbow_agent.storage.config import get_surreal_config
                
                logger.info("尝试连接到 SurrealDB 存储系统...")
                
                # 获取 SurrealDB 配置
                surreal_config = get_surreal_config()
                logger.info(f"SurrealDB 配置: {surreal_config}")
                
                # 初始化会话和轮次管理器
                session_manager = SessionManager(
                    url=surreal_config["url"],
                    namespace=surreal_config["namespace"],
                    database=surreal_config["database"],
                    username=surreal_config["username"],
                    password=surreal_config["password"]
                )
                
                turn_manager = TurnManager(
                    url=surreal_config["url"],
                    namespace=surreal_config["namespace"],
                    database=surreal_config["database"],
                    username=surreal_config["username"],
                    password=surreal_config["password"]
                )
                
                # 连接到 SurrealDB is handled by the client library during initialization or first use.
                # The SessionManager/TurnManager themselves don't have a separate .connect() method.
                
                # 测试连接有效性
                try:
                    logger.info("测试 SurrealDB 连接...")
                    # 创建一个简单的测试查询
                    from rainbow_agent.storage.surreal_storage import SurrealStorage
                    test_storage = SurrealStorage(
                        url=surreal_config["url"],
                        namespace=surreal_config["namespace"],
                        database=surreal_config["database"],
                        username=surreal_config["username"],
                        password=surreal_config["password"]
                    )
                    run_async(test_storage.connect)
                    test_query = "SELECT * FROM sessions LIMIT 1;"
                    test_result = run_async(test_storage.query, test_query)
                    logger.info(f"SurrealDB 测试查询成功: {test_result}")
                    run_async(test_storage.disconnect)
                except Exception as query_error:
                    logger.warning(f"SurrealDB 测试查询失败，但仍将使用 SurrealDB: {query_error}")
                    # 不抛出异常，继续使用 SurrealDB
                
                logger.info("SurrealDB 存储系统初始化完成")
            except Exception as surreal_error:
                logger.warning(f"SurrealDB初始化失败，将切换到SQLite后备: {surreal_error}")
                
                # 如果SurrealDB失败，使用SQLite作为后备
                import sqlite3
                import threading
                from contextlib import contextmanager
                
                # 使用线程本地存储来确保每个线程有自己的连接
                thread_local = threading.local()
                
                # 创建数据库目录（如果不存在）
                os.makedirs("data", exist_ok=True)
                
                @contextmanager
                def get_connection():
                    if not hasattr(thread_local, "connection"):
                        # 创建新连接
                        thread_local.connection = sqlite3.connect(
                            "data/dialogue.db", 
                            timeout=30.0,  # 增加超时时间，防止锁死
                            isolation_level=None,  # 使用自动提交模式
                            check_same_thread=False  # 允许跨线程访问
                        )
                        
                        # 启用WAL模式，提高并发性能
                        thread_local.connection.execute("PRAGMA journal_mode=WAL;")
                        # 开启外键约束
                        thread_local.connection.execute("PRAGMA foreign_keys=ON;")
                        
                    try:
                        yield thread_local.connection
                    finally:
                        pass  # 不关闭连接，而是保持它供线程重用
                
                # 创建必要的表
                with get_connection() as conn:
                    conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        dialogue_type TEXT DEFAULT 'human_to_ai_private',
                        participants TEXT DEFAULT '[]',
                        metadata TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)
                    
                    conn.execute("""
                    CREATE TABLE IF NOT EXISTS turns (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                    );
                    """)
                    
                    logger.info("SQLite数据库表创建成功")
                
                # 创建简单的SQLite实现的SessionManager
                class SQLiteSessionManager:
                    def __init__(self):
                        logger.info("SQLite会话管理器初始化")
                    
                    async def create_session(self, user_id, title=None, dialogue_type="human_to_ai_private", participants=None):
                        session_id = str(uuid.uuid4()).replace('-', '')
                        session_title = title if title else f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        now = datetime.now().isoformat()
                        
                        if participants is None:
                            participants = [
                                {
                                    "id": user_id,
                                    "name": "用户",
                                    "type": "human"
                                },
                                {
                                    "id": "ai_assistant",
                                    "name": "Rainbow助手",
                                    "type": "ai"
                                }
                            ]
                        
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO sessions (id, title, user_id, dialogue_type, participants, created_at, updated_at, last_activity_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (session_id, session_title, user_id, dialogue_type, json.dumps(participants), now, now, now)
                            )
                        
                        return {
                            "id": session_id,
                            "title": session_title,
                            "user_id": user_id,
                            "dialogue_type": dialogue_type,
                            "participants": participants,
                            "metadata": {"dialogue_type": dialogue_type, "participants": participants, "status": "active"},
                            "created_at": now,
                            "updated_at": now,
                            "last_activity_at": now
                        }
                    
                    async def get_sessions(self, user_id=None, limit=10, offset=0):
                        with get_connection() as conn:
                            if user_id:
                                cursor = conn.execute(
                                    "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                                    (user_id, limit, offset)
                                )
                            else:
                                cursor = conn.execute(
                                    "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                                    (limit, offset)
                                )
                            
                            sessions = []
                            for row in cursor.fetchall():
                                session = {
                                    "id": row[0],
                                    "title": row[1],
                                    "user_id": row[2],
                                    "dialogue_type": row[3],
                                    "participants": json.loads(row[4]),
                                    "metadata": json.loads(row[5]) if row[5] else {},
                                    "created_at": row[6],
                                    "updated_at": row[7],
                                    "last_activity_at": row[8]
                                }
                                sessions.append(session)
                            
                            return sessions
                    
                    async def get_session(self, session_id):
                        with get_connection() as conn:
                            cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
                            row = cursor.fetchone()
                            
                            if row:
                                return {
                                    "id": row[0],
                                    "title": row[1],
                                    "user_id": row[2],
                                    "dialogue_type": row[3],
                                    "participants": json.loads(row[4]),
                                    "metadata": json.loads(row[5]) if row[5] else {},
                                    "created_at": row[6],
                                    "updated_at": row[7],
                                    "last_activity_at": row[8]
                                }
                            return None
                    
                    async def update_session(self, session_id, updates):
                        now = datetime.now().isoformat()
                        updates["updated_at"] = now
                        
                        # 构建更新SQL
                        set_clauses = []
                        values = []
                        
                        for key, value in updates.items():
                            set_clauses.append(f"{key} = ?")
                            values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
                        
                        sql = f"UPDATE sessions SET {', '.join(set_clauses)} WHERE id = ?"
                        values.append(session_id)
                        
                        with get_connection() as conn:
                            conn.execute(sql, values)
                            
                        return await self.get_session(session_id)
                    
                    async def update_session_activity(self, session_id):
                        now = datetime.now().isoformat()
                        with get_connection() as conn:
                            conn.execute(
                                "UPDATE sessions SET last_activity_at = ? WHERE id = ?",
                                (now, session_id)
                            )
                        return True
                
                # 创建简单的SQLite实现的TurnManager
                class SQLiteTurnManager:
                    def __init__(self):
                        logger.info("SQLite轮次管理器初始化")
                    
                    async def create_turn(self, session_id, role, content, metadata=None):
                        turn_id = str(uuid.uuid4()).replace('-', '')
                        now = datetime.now().isoformat()
                        metadata_json = json.dumps(metadata) if metadata else '{}'
                        
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO turns (id, session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (turn_id, session_id, role, content, metadata_json, now)
                            )
                        
                        return {
                            "id": turn_id,
                            "session_id": session_id,
                            "role": role,
                            "content": content,
                            "metadata": metadata or {},
                            "created_at": now
                        }
                    
                    async def get_turns(self, session_id):
                        with get_connection() as conn:
                            cursor = conn.execute(
                                "SELECT * FROM turns WHERE session_id = ? ORDER BY created_at ASC",
                                (session_id,)
                            )
                            
                            turns = []
                            for row in cursor.fetchall():
                                turn = {
                                    "id": row[0],
                                    "session_id": row[1],
                                    "role": row[2],
                                    "content": row[3],
                                    "metadata": json.loads(row[4]) if row[4] else {},
                                    "created_at": row[5]
                                }
                                turns.append(turn)
                            
                            return turns
                
                # 使用SQLite实现
                session_manager = SQLiteSessionManager()
                turn_manager = SQLiteTurnManager()
                logger.info("SQLite存储系统初始化完成（作为SurrealDB的后备）")
        else:
            logger.info("存储系统已初始化")
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"存储系统初始化失败: {e}\n{error_traceback}")
        raise

# 初始化对话系统
def init_dialogue_system():
    """初始化对话系统"""
    global session_manager, turn_manager, openai_service, dialogue_manager
    
    # 确保存储系统已初始化
    init_storage()
    
    # 初始化OpenAI服务（如果还没有初始化）
    if openai_service is None:
        logger.info("初始化OpenAI服务...")
        from rainbow_agent.ai.openai_service import OpenAIService
        openai_service = OpenAIService()
        logger.info("OpenAI服务初始化完成")
    else:
        logger.info("OpenAI服务已初始化")
    
    # 初始化对话管理器（如果还没有初始化）
    if dialogue_manager is None:
        logger.info("初始化对话管理器...")
        dialogue_manager = DialogueManager(
            session_manager=session_manager,
            turn_manager=turn_manager,
            ai_service=openai_service
        )
        logger.info("对话管理器初始化完成")
    else:
        logger.info("对话管理器已初始化")
        
    logger.info("对话系统初始化完成")

# 全局异常处理
@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理器"""
    logger.error(f"全局异常: {e}")
    return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

# 设置静态文件访问
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# 首页 - 提供简单的HTML界面
@app.route('/')
def home():
    """服务器首页，提供系统介绍和功能展示"""
    # 返回增强版前端界面
    return send_from_directory('static', 'index.html')

@app.route('/standard')
def standard_interface():
    """标准界面，提供原始的标准界面"""
    return send_from_directory('static', 'index.html')

@app.route('/enhanced')
def enhanced_interface():
    """增强版界面，提供增强版界面"""
    return send_from_directory('static/templates', 'enhanced_index.html')

@app.route('/chat')
def chat():
    """对话界面，提供简单的对话界面和文档"""
    return send_from_directory('static', 'index.html')

@app.route('/demo.html')
def demo_page():
    return send_from_directory('static', 'demo.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/css/enhanced_styles.css')
def enhanced_css():
    return send_from_directory('static/css', 'enhanced_styles.css')

@app.route('/js/enhanced_app.js')
def enhanced_js():
    return send_from_directory('static/js', 'enhanced_app.js')

# 工具管理API
@app.route('/api/dialogue/tools', methods=['GET'])
def get_dialogue_tools():
    """获取可用的工具列表"""
    try:
        logger.info("开始获取工具列表")
        
        # 返回模拟工具数据（后续可从工具注册表获取）
        tools = [
            {
                "id": "weather",
                "name": "天气查询",
                "description": "查询指定城市的天气信息",
                "version": "1.0",
                "provider": "OpenWeatherMap"
            },
            {
                "id": "calculator",
                "name": "计算器",
                "description": "执行数学计算",
                "version": "1.0",
                "provider": "System"
            },
            {
                "id": "image_generator",
                "name": "图像生成",
                "description": "根据描述生成图像",
                "version": "1.0",
                "provider": "DALL-E"
            }
        ]
        
        # 返回兼容多种客户端的响应格式
        response = {
            "success": True,
            "data": {"tools": tools},
            "tools": tools  # 直接提供工具列表，兼容simple_test.html
        }
        
        logger.info(f"返回工具列表: {len(tools)} 个工具")
        return jsonify(response)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"获取工具列表失败: {e}\n{error_traceback}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

# 会话管理API
@app.route('/api/dialogue/sessions', methods=['GET'])
def get_dialogue_sessions():
    """获取对话会话列表，适配增强版前端"""
    try:
        logger.info("开始获取对话会话列表")
        
        # 确保对话系统已初始化
        logger.info("正在初始化对话系统...")
        init_dialogue_system()
        logger.info("对话系统初始化完成")
        
        # 检查会话管理器是否已初始化
        if session_manager is None:
            logger.error("会话管理器未初始化")
            return jsonify({
                "error": "会话管理器未初始化",
                "items": [],
                "total": 0
            }), 500
        
        user_id = request.args.get('userId')
        limit = request.args.get('limit', default=10, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        logger.info(f"请求参数: userId={user_id}, limit={limit}, offset={offset}")
        
        # 获取会话列表
        logger.info("正在从会话管理器获取会话列表...")
        try:
            # 尝试使用对话管理器获取会话列表
            if dialogue_manager is not None:
                logger.info("使用对话管理器获取会话列表")
                sessions = run_async(session_manager.list_sessions, user_id, limit, offset)
            else:
                # 如果对话管理器不可用，使用会话管理器
                logger.info("使用会话管理器获取会话列表")
                sessions = run_async(session_manager.list_sessions, user_id, limit, offset)
        except Exception as list_error:
            logger.error(f"获取会话列表失败: {list_error}")
            # 返回空列表
            sessions = []
        
        logger.info(f"成功获取会话列表，共 {len(sessions)} 个会话")
        
        # 格式化会话数据
        formatted_sessions = []
        for session in sessions:
            logger.info(f"格式化会话数据: {session}")
            # 获取元数据
            metadata = session.get("metadata", {})
            dialogue_type = metadata.get("dialogue_type", DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
            participants = metadata.get("participants", [])
            status = metadata.get("status", "active")
            
            formatted_sessions.append({
                "id": session.get("id", ""),
                "title": session.get("title", "未命名会话"),
                "userId": session.get("user_id", ""),
                "created": session.get("created_at", ""),
                "lastActivity": session.get("updated_at", ""),
                "dialogueType": dialogue_type,
                "participants": participants,
                "status": status
            })
        
        # 返回兼容多种客户端的格式
        logger.info(f"返回会话列表: {len(formatted_sessions)} 个会话")
        return jsonify({
            "success": True,
            "data": {"sessions": formatted_sessions},
            "sessions": formatted_sessions,  # 直接提供会话列表，兼容simple_test.html
            "items": formatted_sessions,     # enhanced_index.html 期望的格式
            "total": len(formatted_sessions)  # enhanced_index.html 期望的格式
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"获取会话列表失败: {e}\n{error_traceback}")
        return jsonify({
            "error": str(e),
            "traceback": error_traceback
        }), 500

@app.route('/api/dialogue/sessions', methods=['POST'])
def create_dialogue_session():
    """创建新会话，适配增强版前端"""
    try:
        logger.info("开始创建新的对话会话")
        
        # 确保对话系统已初始化
        init_dialogue_system()
        
        # 解析请求数据
        try:
            if request.is_json:
                data = request.get_json()
                logger.info(f"成功解析JSON数据: {data}")
            else:
                # 如果请求不是JSON格式，尝试从表单数据中获取
                data = request.form.to_dict()
                logger.info(f"从表单获取数据: {data}")
        except Exception as parse_error:
            logger.error(f"解析请求数据失败: {parse_error}")
            data = {}
        
        # 如果数据为空，使用默认值
        if not data:
            logger.warning("数据为空，使用默认值")
            data = {}
            
        user_id = data.get('userId', str(uuid.uuid4()))
        title = data.get('title', f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        dialogue_type = data.get('dialogueType', DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
        participants = data.get('participants', [user_id])
        
        # 使用对话管理器创建会话
        try:
            logger.info(f"使用对话管理器创建新会话: 用户 {user_id}, 标题 {title}, 类型 {dialogue_type}")
            session = run_async(dialogue_manager.create_session,
                user_id=user_id,
                dialogue_type=dialogue_type,
                title=title,
                participants=participants
            )
            logger.info(f"成功创建会话: {session}")
        except Exception as session_error:
            logger.error(f"创建会话失败: {session_error}")
            
            # 如果对话管理器创建失败，尝试使用会话管理器直接创建
            try:
                logger.info("尝试使用会话管理器直接创建会话")
                # 准备数据
                now = datetime.now()
                session_id = str(uuid.uuid4()).replace('-', '')
                session_title = title if title else f"新对话 {now.strftime('%Y-%m-%d %H:%M')}"
                
                # 创建会话数据
                session = {
                    "id": session_id,
                    "title": session_title,
                    "user_id": user_id,
                    "name": session_title,
                    "dialogue_type": dialogue_type,
                    "participants": participants,
                    "metadata": {
                        "dialogue_type": dialogue_type,
                        "participants": participants,
                        "status": "active"
                    },
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                    "last_activity_at": now.isoformat()
                }
                
                # 保存会话
                try:
                    # 使用SurrealDB存储
                    if use_surreal_db and hasattr(session_manager, 'storage') and hasattr(session_manager.storage, 'db'):
                        logger.info(f"尝试使用SurrealDB创建会话: {session_id}")
                        # 使用session_manager创建会话
                        created_session = run_async(session_manager.create_session, user_id, session_title)
                        if created_session and 'id' in created_session:
                            logger.info(f"SurrealDB创建会话成功: {created_session}")
                            session = created_session
                        else:
                            logger.warning(f"SurrealDB创建会话返回空结果，尝试直接SQL插入")
                            # 尝试直接SQL插入
                            query = f"""
                            INSERT INTO sessions {{id: '{session_id}', title: '{session_title}', user_id: '{user_id}', created_at: '{now.isoformat()}', updated_at: '{now.isoformat()}', last_activity_at: '{now.isoformat()}'}};
                            """
                            logger.info(f"执行直接SQL插入: {query}")
                            sql_result = run_async(session_manager.storage.query, query)
                            logger.info(f"直接SQL插入结果: {sql_result}")
                    else:
                        # 使用SQLite存储
                        logger.info(f"使用SQLite存储会话: {session_id}")
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO sessions (id, title, user_id, created_at, updated_at, last_activity_at, dialogue_type, participants) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (session_id, session_title, user_id, now.isoformat(), now.isoformat(), now.isoformat(), dialogue_type, json.dumps(participants))
                            )
                except Exception as create_error:
                    logger.error(f"保存会话失败: {create_error}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # 继续使用内存中的会话对象
                    logger.info(f"返回内存中的会话对象: {session}")
                    # 尝试使用 SQLite 作为备用
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO sessions (id, title, user_id, created_at, updated_at, last_activity_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (session_id, session_title, user_id, now.isoformat(), now.isoformat(), now.isoformat())
                            )
                            logger.info(f"SQLite备用存储成功: {session_id}")
                    except Exception as sqlite_error:
                        logger.error(f"SQLite备用存储也失败: {sqlite_error}")
                        # 继续使用内存中的会话对象
                
                logger.info(f"会话管理器直接创建会话成功: {session}")
            except Exception as direct_error:
                logger.error(f"会话管理器直接创建会话失败: {direct_error}")
                
                # 返回错误信息
                return jsonify({
                    "success": False,
                    "error": str(direct_error),
                    "message": "创建会话失败"
                }), 500
        
        # 格式化响应
        formatted_session = {
            "id": session.get("id", ""),
            "title": session.get("title", ""),
            "created_at": session.get("created_at", ""),
            "updated_at": session.get("updated_at", ""),
            "user_id": session.get("user_id", ""),
            "dialogue_type": session.get("metadata", {}).get("dialogue_type", dialogue_type),
            "participants": session.get("metadata", {}).get("participants", participants),
            "status": session.get("metadata", {}).get("status", "active")
        }
        
        # 返回兼容多种客户端的响应格式
        response = {
            "success": True,
            "data": formatted_session,
            # 下面的字段直接展开，兼容simple_test.html
            **formatted_session
        }
        
        logger.info(f"返回新创建的会话: {formatted_session}")
        return jsonify(response), 201
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"创建会话失败: {e}\n{error_traceback}")
        return jsonify({
            "error": str(e),
            "traceback": error_traceback
        }), 500

@app.route('/api/dialogue/system/status', methods=['GET'])
def get_system_status_enhanced():
    """获取系统状态，适配增强版前端"""
    try:
        # 确保存储系统已初始化
        init_storage()
        
        # 构建状态响应
        status = {
            "status": "running",
            "version": "1.0.0",
            "components": {
                "storage_factory": storage_factory is not None,
                "session_manager": session_manager is not None,
                "turn_manager": turn_manager is not None,
            },
            "timestamp": datetime.now().isoformat(),
            "storage_type": "surreal"
        }
        
        return jsonify(status)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"获取系统状态失败: {e}\n{error_traceback}")
        return jsonify({
            "error": str(e),
            "traceback": error_traceback
        }), 500

# 处理用户输入API
@app.route('/api/dialogue/input', methods=['POST'])
def process_dialogue_input():
    """处理用户输入，生成AI响应并创建新的对话轮次"""
    try:
        logger.info("开始处理用户输入")
        # 确保对话系统已初始化
        init_dialogue_system()
        
        # 初始化数据变量，确保在异常处理中可用
        data = {}
        session_id = ""
        user_input = ""
        
        # 获取请求数据
        try:
            if request.is_json:
                data = request.get_json()
                logger.info(f"成功解析JSON数据: {data}")
            else:
                # 如果请求不是JSON格式，尝试从表单数据中获取
                data = request.form.to_dict()
                logger.info(f"从表单获取数据: {data}")
        except Exception as e:
            logger.error(f"解析请求数据失败: {e}")
            # 保持data为空字典
            
        # 提取必要参数，提供默认值
        session_id = data.get('sessionId')
        user_id = data.get('userId', str(uuid.uuid4()))
        user_input = data.get('input', '')
        input_type = data.get('inputType', 'text')
        model = data.get('model', 'gpt-3.5-turbo')
        metadata = data.get('metadata', {})
        
        # 验证必要参数
        if not session_id:
            logger.error("缺少sessionId参数")
            return jsonify({
                "success": False,
                "error": "缺少sessionId参数",
                "id": str(uuid.uuid4()),
                "input": user_input,
                "response": "缺少会话ID，无法处理输入",
                "sessionId": "",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        if not user_input.strip():
            logger.error("用户输入为空")
            return jsonify({
                "success": False,
                "error": "用户输入为空",
                "id": str(uuid.uuid4()),
                "input": "",
                "response": "请提供非空输入",
                "sessionId": session_id,
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # 添加模型信息到元数据
        if 'model' not in metadata:
            metadata['model'] = model
        
        # 检查会话是否存在
        try:
            session_exists = run_async(session_manager.get_session, session_id)
            if not session_exists:
                logger.error(f"会话 {session_id} 不存在")
                return jsonify({
                    "success": False,
                    "error": f"会话 {session_id} 不存在",
                    "id": str(uuid.uuid4()),
                    "input": user_input,
                    "response": f"会话 {session_id} 不存在，请先创建会话",
                    "sessionId": session_id,
                    "timestamp": datetime.now().isoformat()
                }), 404
        except Exception as session_error:
            logger.error(f"检查会话存在失败: {session_error}")
            # 继续处理，允许dialogue_manager处理这种情况
        
        # 使用对话管理器处理输入
        logger.info(f"使用对话管理器处理输入: 会话 {session_id}, 用户 {user_id}, 输入: {user_input}")
        try:
            # 直接处理输入，而不依赖异步处理
            # 这样可以避免event loop绑定问题
            # 构建简单的响应
            response_text = f"收到您的输入: {user_input}\n\n正在处理中，请稍候..."
            
            # 生成唯一ID和时间戳
            response_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # 创建用户输入轮次
            try:
                # 使用独立的SQLite事务直接插入用户输入
                user_turn_id = str(uuid.uuid4()).replace('-', '')
                
                # 先检查数据库类型
                if hasattr(turn_manager, 'db') and hasattr(turn_manager.db, 'connect'):
                    # SurrealDB实现
                    try:
                        run_async(turn_manager.create_turn_async,
                            session_id=session_id,
                            role="human",
                            content=user_input,
                            metadata={"timestamp": timestamp, "user_id": user_id}
                        )
                    except Exception as turn_error:
                        logger.warning(f"创建用户输入轮次失败: {turn_error}")
                else:
                    # SQLite实现
                    try:
                        from contextlib import contextmanager
                        import threading
                        import sqlite3
                        import json
                        
                        # 线程本地存储
                        thread_local = threading.local()
                        
                        # 获取连接函数
                        @contextmanager
                        def get_connection():
                            if not hasattr(thread_local, "connection"):
                                thread_local.connection = sqlite3.connect(
                                    "data/dialogue.db", 
                                    timeout=30.0,
                                    isolation_level=None,
                                    check_same_thread=False
                                )
                                
                            try:
                                yield thread_local.connection
                            finally:
                                pass
                        
                        # 直接插入用户轮次
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO turns (id, session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (user_turn_id, session_id, "human", user_input, json.dumps({"user_id": user_id}), timestamp)
                            )
                    except Exception as turn_error:
                        logger.warning(f"创建用户输入轮次失败 (SQLite): {turn_error}")
            except Exception as turn_creation_error:
                logger.warning(f"创建用户轮次失败: {turn_creation_error}")
            
            # 先获取会话信息
            try:
                # 优先使用 SurrealDB 获取会话历史
                session_info = None
                session_turns = []
                
                try:
                    logger.info(f"从 SurrealDB 获取会话 {session_id} 的信息")
                    session_info = run_async(session_manager.get_session, session_id)
                    
                    # 确保获取轮次时正确处理异步结果
                    try:
                        session_turns = run_async(turn_manager.get_turns, session_id)
                        # 确保session_turns是一个列表
                        if session_turns is None:
                            session_turns = []
                        elif not isinstance(session_turns, list):
                            logger.warning(f"轮次结果不是列表类型: {type(session_turns)}")
                            session_turns = []
                        logger.info(f"成功获取轮次信息: {len(session_turns)} 个轮次")
                    except Exception as turns_error:
                        logger.error(f"获取轮次失败: {turns_error}")
                        session_turns = []
                    
                    logger.info(f"成功获取会话信息: {session_info is not None}")
                except Exception as session_error:
                    logger.warning(f"从 SurrealDB 获取会话信息失败: {session_error}")
                    session_turns = []
            
                # 生成对话历史上下文
                messages = [
                    {"role": "system", "content": "You are a helpful assistant."}
                ]
                
                # 添加历史轮次，最多添加收8个回合，共6个用户消息和6个AI消息
                if session_turns:
                    history_turns = session_turns[-12:] if len(session_turns) > 12 else session_turns
                    for turn in history_turns:
                        # 确保 turn 是字典类型
                        if isinstance(turn, dict):
                            # 安全地获取角色和内容
                            role = "user" if turn.get("role") == "human" else "assistant"
                            content = turn.get("content", "")
                            messages.append({"role": role, "content": content})
                        elif isinstance(turn, str):
                            # 如果 turn 是字符串，尝试解析为 JSON
                            try:
                                import json
                                turn_dict = json.loads(turn)
                                if isinstance(turn_dict, dict):
                                    role = "user" if turn_dict.get("role") == "human" else "assistant"
                                    content = turn_dict.get("content", "")
                                    messages.append({"role": role, "content": content})
                            except Exception as json_error:
                                logger.warning(f"无法解析轮次字符串为 JSON: {json_error}")
                        else:
                            logger.warning(f"跳过非字典类型的轮次: {type(turn)}")
                            continue
                
                # 添加当前用户输入
                messages.append({"role": "user", "content": user_input})
                
                # 生成响应
                from rainbow_agent.ai.openai_service import OpenAIService
                ai_service = OpenAIService()
                response_text = ai_service.generate_response(messages)
                logger.info(f"生成AI响应成功: {response_text[:50]}...")
                
                # 优先使用 SurrealDB 创建用户轮次和AI轮次
                try:
                    # 先创建用户轮次
                    user_metadata = {
                        "timestamp": timestamp, 
                        "user_id": user_id,
                        "input_type": input_type
                    }
                    
                    user_turn = run_async(turn_manager.create_turn_async, 
                                          session_id=session_id, 
                                          role="human", 
                                          content=user_input, 
                                          metadata=user_metadata)
                    
                    logger.info(f"成功创建用户轮次: {user_turn.get('id') if user_turn else 'None'}")
                    
                    # 然后创建 AI 轮次
                    ai_metadata = {
                        "timestamp": timestamp,
                        "model": "gpt-3.5-turbo"
                    }
                    
                    ai_turn = run_async(turn_manager.create_turn_async, 
                                        session_id=session_id, 
                                        role="ai", 
                                        content=response_text, 
                                        metadata=ai_metadata)
                    
                    logger.info(f"成功创建 AI 轮次: {ai_turn.get('id') if ai_turn else 'None'}")
                    
                except Exception as turn_error:
                    logger.error(f"创建轮次失败: {turn_error}")
                    # 如果 SurrealDB 失败，尝试使用 SQLite
                    try:
                        from contextlib import contextmanager
                        import threading
                        import sqlite3
                        import json
                        
                        # 线程本地存储
                        thread_local = threading.local()
                        
                        # 获取连接函数
                        @contextmanager
                        def get_connection():
                            if not hasattr(thread_local, "connection"):
                                thread_local.connection = sqlite3.connect(
                                    "data/dialogue.db", 
                                    timeout=30.0,
                                    isolation_level=None,
                                    check_same_thread=False
                                )
                                
                            try:
                                yield thread_local.connection
                            finally:
                                pass
                        
                        # 插入用户和AI轮次
                        user_turn_id = str(uuid.uuid4()).replace('-', '')
                        ai_turn_id = str(uuid.uuid4()).replace('-', '')
                        
                        with get_connection() as conn:
                            # 插入用户轮次
                            conn.execute(
                                "INSERT INTO turns (id, session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (user_turn_id, session_id, "human", user_input, json.dumps({"user_id": user_id}), timestamp)
                            )
                            
                            # 插入AI轮次
                            conn.execute(
                                "INSERT INTO turns (id, session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (ai_turn_id, session_id, "ai", response_text, '{}', timestamp)
                            )
                            
                        logger.info("使用 SQLite 备用存储成功创建轮次")
                    except Exception as sqlite_error:
                        logger.error(f"SQLite 备用存储也失败: {sqlite_error}")
            except Exception as ai_error:
                logger.error(f"生成AI响应失败: {ai_error}")
                response_text = f"很抱歉，生成响应时出错: {str(ai_error)}"
            
            # 更新会话活动时间
            try:
                logger.info(f"更新会话 {session_id} 的活动时间")
                # 直接使用 SurrealDB 更新会话活动时间
                try:
                    # 首先尝试使用 update_session_activity 方法
                    try:
                        logger.info(f"尝试使用 update_session_activity 方法更新会话 {session_id} 的活动时间")
                        activity_updated = run_async(session_manager.update_session_activity, session_id)
                        if activity_updated:
                            logger.info(f"成功使用 update_session_activity 更新会话 {session_id} 的活动时间")
                            # 成功更新，但不要在这里返回，继续构建响应
                    except AttributeError as attr_error:
                        # 如果 SessionManager 没有 update_session_activity 方法，则尝试其他方法
                        logger.warning(f"SessionManager 没有 update_session_activity 方法: {attr_error}")
                    except Exception as activity_error:
                        logger.warning(f"update_session_activity 方法失败: {activity_error}")
                    
                    # 如果 update_session_activity 失败或不存在，尝试使用 update_session 方法
                    updates = {
                        "updated_at": timestamp,
                        "last_activity_at": timestamp
                    }
                    
                    # 直接调用 update_session
                    updated_session = run_async(session_manager.update_session, session_id, updates)
                    
                    if updated_session:
                        logger.info(f"成功更新会话 {session_id} 的活动时间: {updated_session.get('updated_at')}")
                    else:
                        logger.warning(f"更新会话 {session_id} 的活动时间失败: 无法获取更新后的会话")
                        # 尝试备用方法
                        record_result = run_async(session_manager.record_activity, session_id)
                        logger.info(f"使用 record_activity 方法的结果: {record_result}")
                except Exception as surreal_update_error:
                    logger.warning(f"SurrealDB 更新会话活动时间失败: {surreal_update_error}")
                    # 如果 SurrealDB 失败，尝试使用 SQLite
                    try:
                        # 确保有 get_connection 函数
                        if 'get_connection' not in locals():
                            from contextlib import contextmanager
                            import threading
                            import sqlite3
                            
                            # 线程本地存储
                            thread_local = threading.local()
                            
                            # 获取连接函数
                            @contextmanager
                            def get_connection():
                                if not hasattr(thread_local, "connection"):
                                    thread_local.connection = sqlite3.connect(
                                        "data/dialogue.db", 
                                        timeout=30.0,
                                        isolation_level=None,
                                        check_same_thread=False
                                    )
                                    
                                try:
                                    yield thread_local.connection
                                finally:
                                    pass
                        
                        # 使用 SQLite 更新会话活动时间
                        with get_connection() as conn:
                            conn.execute(
                                "UPDATE sessions SET updated_at = ?, last_activity_at = ? WHERE id = ?",
                                (timestamp, timestamp, session_id)
                            )
                            logger.info(f"使用 SQLite 成功更新会话 {session_id} 的活动时间")
                    except Exception as sqlite_update_error:
                        logger.error(f"SQLite 更新会话活动时间也失败: {sqlite_update_error}")
            except Exception as update_error:
                logger.warning(f"更新会话活动时间失败: {update_error}")
                import traceback
                error_traceback = traceback.format_exc()
                logger.error(f"错误详情: {error_traceback}")
            
            # 构建结果
            result = {
                "id": response_id,
                "input": user_input,
                "response": response_text,
                "final_response": response_text,  # 兼容现有前端
                "sessionId": session_id,
                "timestamp": timestamp,
                "metadata": {
                    "model": "gpt-3.5-turbo",
                    "user_id": user_id,
                    "input_type": input_type
                }
            }
                
            logger.info(f"成功处理输入: 会话 {session_id}, 响应ID: {result.get('id')}")
            
            # 返回兼容多种客户端的响应格式
            response = {
                "success": True,
                "data": result,
                # 下面的字段直接展开，兼容simple_test.html
                **result
            }
            
            return jsonify(response)
        except Exception as process_error:
            logger.error(f"处理输入失败: {process_error}")
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"错误详情: {error_traceback}")
            
            return jsonify({
                "success": False,
                "error": str(process_error),
                "id": str(uuid.uuid4()),
                "input": user_input,
                "response": f"处理输入时出现错误: {str(process_error)}",
                "sessionId": session_id,
                "timestamp": datetime.now().isoformat()
            }), 500
        

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"处理对话输入失败: {e}\n{error_traceback}")
        return jsonify({
            "id": str(uuid.uuid4()),
            "input": data.get('input', ''),
            "response": f"处理输入时出现错误: {str(e)}",
            "sessionId": data.get('sessionId', ''),
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "traceback": error_traceback
        }), 500

# 获取特定会话信息API
@app.route('/api/dialogue/sessions/<session_id>', methods=['GET'])
def get_dialogue_session(session_id):
    """获取指定会话ID的会话信息"""
    try:
        logger.info(f"开始获取会话 {session_id} 的信息")
        # 确保对话系统已初始化
        init_dialogue_system()
        
        # 从会话管理器获取会话信息
        session = run_async(session_manager.get_session, session_id)
        
        if not session:
            logger.error(f"会话 {session_id} 不存在")
            return jsonify({
                "success": False,
                "error": f"会话 {session_id} 不存在"
            }), 404
        
        # 格式化会话数据
        dialogue_type = session.get("metadata", {}).get("dialogue_type", DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
        participants = session.get("metadata", {}).get("participants", [])
        status = session.get("metadata", {}).get("status", "active")
        
        formatted_session = {
            "id": session.get("id", ""),
            "title": session.get("title", ""),
            "name": session.get("title", ""),  # 兼容旧版前端
            "created_at": session.get("created_at", ""),
            "updated_at": session.get("updated_at", ""),
            "last_activity_at": session.get("updated_at", ""),  # 兼容旧版前端
            "user_id": session.get("user_id", ""),
            "dialogue_type": dialogue_type,
            "participants": participants,
            "status": status,
            "metadata": {
                "dialogue_type": dialogue_type,
                "participants": participants,
                "status": status
            }
        }
        
        # 返回兼容多种客户端的响应格式
        response = {
            "success": True,
            "data": formatted_session,
            # 下面的字段直接展开，兼容simple_test.html
            **formatted_session
        }
        
        logger.info(f"成功获取会话 {session_id} 的信息")
        return jsonify(response)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"获取会话信息失败: {e}\n{error_traceback}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

# 获取会话轮次API
@app.route('/api/dialogue/sessions/<session_id>/turns', methods=['GET'])
def get_dialogue_turns(session_id):
    """获取指定会话的对话轮次"""
    try:
        logger.info(f"开始获取会话 {session_id} 的轮次")
        # 确保对话系统已初始化
        init_dialogue_system()
        
        # 获取会话信息，包括对话类型
        try:
            session_info = run_async(session_manager.get_session, session_id)
            dialogue_type = session_info.get("metadata", {}).get("dialogue_type", DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
            logger.info(f"会话 {session_id} 的对话类型为: {dialogue_type}")
        except Exception as session_error:
            logger.warning(f"获取会话信息失败: {session_error}，使用默认对话类型")
            dialogue_type = DIALOGUE_TYPES["HUMAN_AI_PRIVATE"]
        
        # 获取会话轮次
        logger.info(f"从轮次管理器获取会话 {session_id} 的轮次")
        turns = run_async(turn_manager.get_turns, session_id)
        logger.info(f"成功获取会话 {session_id} 的轮次，共 {len(turns)} 个轮次")
        
        # 按照创建时间排序
        turns.sort(key=lambda x: x.get("created_at", ""))
        
        # 根据对话类型格式化轮次
        formatted_turns = []
        
        if dialogue_type in [DIALOGUE_TYPES["HUMAN_AI_PRIVATE"], DIALOGUE_TYPES["HUMAN_AI_GROUP"], DIALOGUE_TYPES["AI_MULTI_HUMAN"]]:
            # 人类与AI对话类型，按照人机对话格式进行分组
            i = 0
            while i < len(turns):
                # 获取当前轮次
                current_turn = turns[i]
                
                # 如果是人类轮次，尝试查找对应的AI轮次
                if current_turn.get("role") == "human":
                    user_content = current_turn.get("content", "")
                    ai_content = ""
                    timestamp = current_turn.get("created_at", "")
                    user_id = current_turn.get("metadata", {}).get("user_id", "unknown")
                    
                    # 如果还有下一个轮次，并且是AI轮次，则将其作为响应
                    if i + 1 < len(turns) and turns[i+1].get("role") == "ai":
                        ai_turn = turns[i+1]
                        ai_content = ai_turn.get("content", "")
                        timestamp = ai_turn.get("created_at", "")
                        i += 2  # 跳过AI轮次
                    else:
                        i += 1  # 只前进一个轮次
                    
                    # 添加格式化的轮次
                    formatted_turns.append({
                        "id": current_turn.get("id"),
                        "sessionId": session_id,
                        "input": user_content,
                        "response": ai_content,
                        "timestamp": timestamp,
                        "userId": user_id,
                        "dialogueType": dialogue_type
                    })
                else:
                    # 如果是AI轮次但没有对应的人类轮次，则单独添加
                    i += 1
        elif dialogue_type == DIALOGUE_TYPES["AI_AI_DIALOGUE"]:
            # AI与AI对话类型，按照AI角色进行分组
            for turn in turns:
                role = turn.get("role", "")
                content = turn.get("content", "")
                timestamp = turn.get("created_at", "")
                metadata = turn.get("metadata", {})
                ai_role = metadata.get("ai_role", "AI")
                
                formatted_turns.append({
                    "id": turn.get("id"),
                    "sessionId": session_id,
                    "content": content,
                    "timestamp": timestamp,
                    "aiRole": ai_role,
                    "dialogueType": dialogue_type
                })
        elif dialogue_type == DIALOGUE_TYPES["AI_SELF_REFLECTION"]:
            # AI自我反思类型，直接返回所有轮次
            for turn in turns:
                role = turn.get("role", "")
                content = turn.get("content", "")
                timestamp = turn.get("created_at", "")
                
                formatted_turns.append({
                    "id": turn.get("id"),
                    "sessionId": session_id,
                    "role": role,
                    "content": content,
                    "timestamp": timestamp,
                    "dialogueType": dialogue_type
                })
        else:
            # 其他对话类型，直接返回原始轮次
            for turn in turns:
                formatted_turns.append({
                    "id": turn.get("id"),
                    "sessionId": session_id,
                    "role": turn.get("role", ""),
                    "content": turn.get("content", ""),
                    "timestamp": turn.get("created_at", ""),
                    "metadata": turn.get("metadata", {}),
                    "dialogueType": dialogue_type
                })
        
        logger.info(f"返回会话 {session_id} 的格式化轮次: {len(formatted_turns)} 个轮次")
        return jsonify({
            "items": formatted_turns,
            "total": len(formatted_turns),
            "dialogueType": dialogue_type
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"获取会话轮次失败: {e}\n{error_traceback}")
        return jsonify({
            "error": str(e),
            "traceback": error_traceback
        }), 500

# 获取支持的对话类型
@app.route('/api/dialogue-types', methods=['GET'])
def get_dialogue_types():
    """获取支持的对话类型"""
    return jsonify(DIALOGUE_TYPES), 200

# 在应用启动时初始化存储系统
# 注意：在新版Flask中，before_first_request已被弃用
# 我们使用普通的路由处理函数来初始化

# 初始化标志，确保只初始化一次
_initialized = False

@app.before_request
def before_request():
    """在每个请求前执行，确保存储系统已初始化"""
    global _initialized, session_manager, turn_manager, openai_service, dialogue_manager
    
    # 每次请求都确保存储系统已初始化
    if not _initialized:
        logger.info("API服务器初始化中...")
        
        try:
            # 初始化存储系统
            init_storage()
            
            # 初始化对话系统
            init_dialogue_system()
            
            logger.info("API服务器初始化完成")
            _initialized = True
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"API服务器初始化失败: {e}\n{error_traceback}")
            # 不设置_initialized为True，这样下一次请求会重新尝试初始化

# 主函数
if __name__ == "__main__":
    # 设置端口
    port = int(os.environ.get("PORT", 5000))
    
    # 启动服务器
    app.run(host="0.0.0.0", port=port, debug=True)
