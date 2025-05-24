"""
对话API模块

提供对话管理系统的HTTP API接口
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from flask import Blueprint, request, jsonify
from rainbow_agent.core.dialogue_manager import DialogueManager, DIALOGUE_TYPES

# 配置日志
logger = logging.getLogger(__name__)

# 创建Blueprint
dialogue_api = Blueprint('dialogue_api', __name__)

# 全局对话管理器实例
dialogue_manager = None

def init_dialogue_api():
    """初始化对话API模块"""
    global dialogue_manager
    
    if dialogue_manager is None:
        logger.info("初始化对话管理器...")
        dialogue_manager = DialogueManager()
        logger.info("对话管理器初始化完成")
    else:
        logger.info("对话管理器已初始化")
    
    return dialogue_manager

@dialogue_api.route('/sessions', methods=['POST'])
async def create_session():
    """创建新的对话会话"""
    try:
        # 确保对话管理器已初始化
        if dialogue_manager is None:
            init_dialogue_api()
        
        # 解析请求数据
        data = request.json
        user_id = data.get('userId', str(uuid.uuid4()))
        title = data.get('title')
        dialogue_type = data.get('dialogueType', DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
        participants = data.get('participants', [user_id])
        
        # 创建会话
        session = await dialogue_manager.create_session(
            user_id=user_id,
            dialogue_type=dialogue_type,
            title=title,
            participants=participants
        )
        
        return jsonify(session), 201
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "创建会话失败"
        }), 500

@dialogue_api.route('/sessions/<session_id>', methods=['GET'])
async def get_session(session_id):
    """获取会话信息"""
    try:
        # 确保对话管理器已初始化
        if dialogue_manager is None:
            init_dialogue_api()
        
        # 获取会话
        session = await dialogue_manager.session_manager.get_session(session_id)
        
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

@dialogue_api.route('/sessions/<session_id>/turns', methods=['GET'])
async def get_turns(session_id):
    """获取会话的对话轮次"""
    try:
        # 确保对话管理器已初始化
        if dialogue_manager is None:
            init_dialogue_api()
        
        # 获取轮次
        turns = await dialogue_manager.turn_manager.get_turns(session_id)
        
        return jsonify(turns), 200
    except Exception as e:
        logger.error(f"获取对话轮次失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "获取对话轮次失败"
        }), 500

@dialogue_api.route('/sessions/<session_id>/process', methods=['POST'])
async def process_input():
    """处理用户输入并生成响应"""
    try:
        # 确保对话管理器已初始化
        if dialogue_manager is None:
            init_dialogue_api()
        
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
        result = await dialogue_manager.process_input(
            session_id=session_id,
            user_id=user_id,
            content=content,
            input_type=input_type,
            metadata=metadata
        )
        
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

@dialogue_api.route('/sessions/<session_id>/turns', methods=['POST'])
async def create_turn(session_id):
    """创建对话轮次"""
    try:
        # 确保对话管理器已初始化
        if dialogue_manager is None:
            init_dialogue_api()
        
        # 解析请求数据
        data = request.json
        role = data.get('role', 'human')
        content = data.get('content', '')
        metadata = data.get('metadata', {})
        
        # 创建轮次
        turn = await dialogue_manager.create_turn(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata
        )
        
        return jsonify(turn), 201
    except Exception as e:
        logger.error(f"创建轮次失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "创建轮次失败"
        }), 500

@dialogue_api.route('/sessions', methods=['GET'])
async def list_sessions():
    """获取会话列表"""
    try:
        # 确保对话管理器已初始化
        if dialogue_manager is None:
            init_dialogue_api()
        
        # 解析请求参数
        user_id = request.args.get('userId')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        # 获取会话列表
        sessions = await dialogue_manager.session_manager.list_sessions(user_id, limit, offset)
        
        return jsonify(sessions), 200
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "获取会话列表失败"
        }), 500

@dialogue_api.route('/dialogue-types', methods=['GET'])
def get_dialogue_types():
    """获取支持的对话类型"""
    return jsonify(DIALOGUE_TYPES), 200
