#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unified SurrealDB API Server (更新版)

使用统一的配置系统和新的统一存储系统进行对话管理和代理交互。
支持OAuth登录和用户认证。
"""
import os
import sys
import json
import logging
import uuid
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from json import JSONEncoder

# Load environment variables from .env file
load_dotenv()

# Add project root to Python path
import pathlib
root_dir = str(pathlib.Path(__file__).absolute().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from flask_login import current_user, login_required

# 导入中央配置系统
from rainbow_agent.config.settings import get_settings

from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
from rainbow_agent.api.unified_dialogue_processor import UnifiedDialogueProcessor
from rainbow_agent.ai.openai_service import OpenAIService  # 使用更新版本的OpenAI服务
from rainbow_agent.core.dialogue_manager import DIALOGUE_TYPES
from rainbow_agent.core.dialogue_manager_with_context import EnhancedDialogueManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 自定义JSON编码器，处理SurrealDB的RecordID类型
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            # 检查对象是否有table_name和record_id属性（SurrealDB的RecordID类型特征）
            if hasattr(obj, 'table_name') and hasattr(obj, 'record_id'):
                return f"{obj.table_name}:{obj.record_id}"
            # 处理其他自定义类型
            return JSONEncoder.default(self, obj)
        except TypeError:
            # 如果无法序列化，则转换为字符串
            return str(obj)

# 导入应用模块
from rainbow_agent.app import app as rainbow_app

# Create Flask app
app = Flask(__name__, static_folder='static')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.json_encoder = CustomJSONEncoder  # 使用自定义JSON编码器
CORS(app)  # Enable CORS for frontend cross-origin requests

# 从rainbow_app复制配置
app.config.update(rainbow_app.config)

# 设置密钥
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')

# Global variables
storage = None
dialogue_processor = None
dialogue_manager = None

def init_storage():
    """Initialize unified storage system"""
    global storage, dialogue_processor, dialogue_manager
    
    try:
        if storage is None:
            logger.info("Initializing unified storage system...")
            
            # 从中央配置系统获取SurrealDB配置
            settings = get_settings()
            surreal_config = settings.get("storage", {})
            logger.info(f"SurrealDB configuration: {surreal_config}")
            
            # Initialize unified storage (uses configuration automatically)
            storage = UnifiedDialogueStorage()
            
            # Initialize dialogue processor
            dialogue_processor = UnifiedDialogueProcessor(storage=storage)
            
            # Test connection
            health = storage.health_check()
            if health["status"] == "healthy":
                logger.info("Unified storage system initialized successfully")
            else:
                logger.warning(f"Storage system health check warning: {health}")
                # Continue anyway, might just be connectivity test failure
        else:
            logger.info("Storage system already initialized")
    except Exception as e:
        logger.error(f"Unified storage system initialization failed: {e}")
        raise

def init_dialogue_system():
    """Initialize dialogue system"""
    global dialogue_manager
    
    # Ensure storage system is initialized
    init_storage()
    
    # Initialize dialogue manager if not already done
    if dialogue_manager is None:
        logger.info("Initializing dialogue manager...")
        openai_service = OpenAIService()
        
        # 使用增强型对话管理器，支持上下文处理和注入
        dialogue_manager = EnhancedDialogueManager(
            storage=storage,
            ai_service=openai_service
        )
        logger.info("Enhanced dialogue manager initialized successfully")

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    return jsonify({"error": "Internal server error"}), 500

# Static file routes
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/')
def home():
    # 如果用户已登录，重定向到聊天页面
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    # 否则重定向到登录页面
    return redirect(url_for('pages.login'))

@app.route('/enhanced')
@login_required
def enhanced_interface():
    return send_from_directory('static', 'enhanced_index.html')

@app.route('/chat')
@login_required
def chat():
    return send_from_directory('static', 'rainbow_demo.html')

@app.route('/favicon.ico')
def favicon():
    return '', 404

# API Routes

@app.route('/api/dialogue/sessions', methods=['GET'])
def get_dialogue_sessions():
    """Get dialogue sessions for a user"""
    try:
        init_storage()
        
        user_id = request.args.get('user_id', 'default_user')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        logger.info(f"Getting sessions for user: {user_id}, limit: {limit}, offset: {offset}")
        
        # Get sessions using unified storage
        sessions = storage.get_user_sessions(user_id, limit, offset)
        
        logger.info(f"Retrieved {len(sessions)} sessions")
        return jsonify({
            "success": True,
            "sessions": sessions,
            "total": len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dialogue/sessions', methods=['POST'])
def create_dialogue_session():
    """Create a new dialogue session"""
    try:
        init_storage()
        
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        title = data.get('title', '')
        dialogue_type = data.get('dialogue_type', DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
        
        logger.info(f"Creating session for user: {user_id}, title: {title}, type: {dialogue_type}")
        
        # Create session using unified storage
        session = storage.create_session(
            user_id=user_id,
            title=title,
            metadata={
                "dialogue_type": dialogue_type,
                "created_via": "api"
            }
        )
        
        if session:
            logger.info(f"Session created successfully: {session['id']}")
            return jsonify({
                "success": True,
                "session": session
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create session"
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/test', methods=['POST'])
def test_endpoint():
    """Test endpoint for debugging"""
    try:
        data = request.get_json()
        return jsonify({
            "success": True,
            "message": "Test endpoint working",
            "received": data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/dialogue/input', methods=['POST'])
def process_dialogue_input():
    """Process dialogue input and generate response"""
    try:
        init_dialogue_system()
        
        data = request.get_json()
        user_input = data.get('input', '')
        user_id = data.get('user_id', 'default_user')
        session_id = data.get('session_id')
        input_type = data.get('input_type', 'text')
        
        logger.info(f"Processing input for user: {user_id}, session: {session_id}, input: {user_input[:50]}...")
        
        # Debug: Check if dialogue_processor is properly initialized
        logger.info(f"Dialogue processor type: {type(dialogue_processor)}")
        logger.info(f"Dialogue processor storage type: {type(dialogue_processor.storage) if dialogue_processor else 'None'}")
        
        # Process input using unified dialogue processor (sync)
        try:
            result = dialogue_processor.process_input_sync(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id,
                input_type=input_type,
                context=data.get('context', {})
            )
        except Exception as proc_error:
            logger.error(f"Dialogue processor error: {proc_error}")
            # Create fallback response
            result = {
                "id": str(uuid.uuid4()),
                "input": user_input,
                "response": "抱歉，处理您的请求时遇到了技术问题，请稍后再试。",
                "sessionId": session_id or "fallback_session",
                "timestamp": datetime.now().isoformat(),
                "error": f"Processing error: {str(proc_error)}"
            }
        
        logger.info(f"Input processed successfully, response length: {len(result.get('response', ''))}")
        return jsonify({
            "success": True,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error processing dialogue input: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dialogue/sessions/<session_id>', methods=['GET'])
def get_dialogue_session(session_id):
    """Get a specific dialogue session with its turns"""
    try:
        init_storage()
        
        logger.info(f"Getting session: {session_id}")
        
        # Get session with turns using unified storage
        session_with_turns = storage.get_session_with_turns(session_id)
        
        if session_with_turns:
            logger.info(f"Session retrieved with {len(session_with_turns.get('turns', []))} turns")
            return jsonify({
                "success": True,
                "session": session_with_turns
            })
        else:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dialogue/sessions/<session_id>/turns', methods=['GET'])
def get_dialogue_turns(session_id):
    """Get turns for a specific session"""
    try:
        init_storage()
        
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        logger.info(f"Getting turns for session: {session_id}, limit: {limit}, offset: {offset}")
        
        # Get turns using unified storage
        turns = storage.get_turns(session_id, limit, offset)
        
        logger.info(f"Retrieved {len(turns)} turns")
        return jsonify({
            "success": True,
            "turns": turns,
            "total": len(turns)
        })
        
    except Exception as e:
        logger.error(f"Error getting turns: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dialogue/types', methods=['GET'])
def get_dialogue_types():
    """Get available dialogue types"""
    return jsonify({
        "success": True,
        "dialogue_types": DIALOGUE_TYPES
    })

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get system status"""
    try:
        init_storage()
        
        # Get storage health
        storage_health = storage.health_check()
        
        return jsonify({
            "success": True,
            "status": {
                "storage": storage_health,
                "system": "unified",
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.before_request
def before_request():
    """Initialize systems before each request"""
    try:
        init_storage()
    except Exception as e:
        logger.error(f"Failed to initialize storage before request: {e}")

# 注册rainbow_app的蓝图到主应用
from rainbow_agent.api.unified_routes import api
from rainbow_agent.auth.routes import auth_api
from rainbow_agent.ui.page_routes import pages

app.register_blueprint(api)
app.register_blueprint(auth_api)
app.register_blueprint(pages)

if __name__ == '__main__':
    try:
        logger.info("Starting Unified SurrealDB API Server with OAuth support...")
        
        # Initialize storage system
        init_storage()
        init_dialogue_system()
        
        # 初始化认证系统
        from rainbow_agent.api.auth_routes import init_auth_components
        init_auth_components(app)
        
        logger.info("Unified API Server initialized successfully")
        
        # 从中央配置系统获取服务器配置
        settings = get_settings()
        server_config = settings.get("server", {})
        port = server_config.get("port", 5000)
        host = server_config.get("host", "0.0.0.0")
        debug = server_config.get("debug", True)
        
        logger.info(f"Starting server on {host}:{port} (debug={debug})")
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)