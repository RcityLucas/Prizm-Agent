"""
增强版Rainbow City AI Agent API服务器

集成了完整的对话管理系统，支持多种对话类型和多模态交互
"""
import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import nest_asyncio

from rainbow_agent.core.dialogue_manager import DialogueManager, DIALOGUE_TYPES
from rainbow_agent.api.dialogue_api import dialogue_api, init_dialogue_api
from rainbow_agent.ai.openai_service import OpenAIService

# 应用异步补丁，允许在Flask中使用异步函数
nest_asyncio.apply()

# 配置日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__, static_folder='static')
CORS(app)  # 启用CORS，允许前端跨域请求

# 全局变量
dialogue_manager = None
openai_service = None

# 初始化对话系统
def init_dialogue_system():
    """初始化对话系统"""
    global dialogue_manager, openai_service
    
    # 初始化OpenAI服务（如果还没有初始化）
    if openai_service is None:
        logger.info("初始化OpenAI服务...")
        openai_service = OpenAIService()
        logger.info("OpenAI服务初始化完成")
    
    # 初始化对话管理器（如果还没有初始化）
    if dialogue_manager is None:
        logger.info("初始化对话管理器...")
        dialogue_manager = DialogueManager(ai_service=openai_service)
        logger.info("对话管理器初始化完成")
    
    logger.info("对话系统初始化完成")

# 注册蓝图
app.register_blueprint(dialogue_api, url_prefix='/api/dialogue')

# 辅助函数：运行异步函数
def run_async(coro):
    """运行异步函数并返回结果"""
    return asyncio.run(coro)

# 路由：首页
@app.route('/')
def index():
    """返回首页"""
    return send_from_directory('static', 'index.html')

# 路由：创建会话
@app.route('/api/sessions', methods=['POST'])
def create_session():
    """创建新的对话会话"""
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 解析请求数据
        data = request.json
        user_id = data.get('userId', str(uuid.uuid4()))
        title = data.get('title')
        dialogue_type = data.get('dialogueType', DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
        participants = data.get('participants', [user_id])
        
        # 创建会话
        session = run_async(dialogue_manager.create_session(
            user_id=user_id,
            dialogue_type=dialogue_type,
            title=title,
            participants=participants
        ))
        
        return jsonify(session), 201
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "创建会话失败"
        }), 500

# 路由：获取会话信息
@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话信息"""
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 获取会话
        session = run_async(dialogue_manager.session_manager.get_session(session_id))
        
        if not session:
            return jsonify({
                "error": "会话不存在",
                "message": f"未找到ID为 {session_id} 的会话"
            }), 404
        
        return jsonify(session), 200
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "获取会话失败"
        }), 500

# 路由：获取会话的对话轮次
@app.route('/api/sessions/<session_id>/turns', methods=['GET'])
def get_turns(session_id):
    """获取会话的对话轮次"""
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 获取轮次
        turns = run_async(dialogue_manager.turn_manager.get_turns(session_id))
        
        return jsonify(turns), 200
    except Exception as e:
        logger.error(f"获取对话轮次失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "获取对话轮次失败"
        }), 500

# 路由：处理对话输入
@app.route('/api/dialogue', methods=['POST'])
def process_dialogue_input():
    """处理用户输入，生成AI响应并创建新的对话轮次"""
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 解析请求数据
        data = request.json
        session_id = data.get('sessionId')
        user_id = data.get('userId', str(uuid.uuid4()))
        content = data.get('input', '')
        input_type = data.get('inputType', 'text')
        model = data.get('model', 'gpt-3.5-turbo')
        metadata = data.get('metadata', {})
        
        # 添加模型信息到元数据
        if 'model' not in metadata:
            metadata['model'] = model
        
        # 处理输入
        result = run_async(dialogue_manager.process_input(
            session_id=session_id,
            user_id=user_id,
            content=content,
            input_type=input_type,
            metadata=metadata
        ))
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"处理输入失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "处理输入失败",
            "id": str(uuid.uuid4()),
            "input": request.json.get('input', ''),
            "response": f"处理输入时出现错误: {str(e)}",
            "sessionId": request.json.get('sessionId', ''),
            "timestamp": datetime.now().isoformat()
        }), 500

# 路由：获取会话列表
@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """获取会话列表"""
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 解析请求参数
        user_id = request.args.get('userId')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        # 获取会话列表
        sessions = run_async(dialogue_manager.session_manager.list_sessions(user_id, limit, offset))
        
        return jsonify(sessions), 200
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "获取会话列表失败"
        }), 500

# 路由：获取支持的对话类型
@app.route('/api/dialogue-types', methods=['GET'])
def get_dialogue_types():
    """获取支持的对话类型"""
    return jsonify(DIALOGUE_TYPES), 200

# 路由：健康检查
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }), 200

# 主函数
if __name__ == '__main__':
    try:
        # 初始化对话系统
        init_dialogue_system()
        
        # 启动服务器
        port = int(os.getenv("PORT", 5000))
        logger.info(f"启动服务器，监听端口: {port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
