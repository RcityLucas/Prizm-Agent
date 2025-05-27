"""
统一API路由模块

整合了原有的api_routes.py、dialogue_routes.py和dialogue_api.py功能，
提供统一的API接口，支持多种客户端格式，包括标准界面和增强版界面。
"""
import os
import uuid
import json
import logging
import threading
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

from rainbow_agent.core.dialogue_manager import DialogueManager, DIALOGUE_TYPES
from rainbow_agent.api.dialogue_processor import DialogueProcessor, SessionManager
from rainbow_agent.core.multi_modal_manager import MultiModalToolManager
from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# 创建Blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# 全局组件实例
dialogue_manager = None
session_manager = None
dialogue_processor = None
multi_modal_manager = None

# 初始化标志
_initialized = False

def init_api_components():
    """初始化API组件"""
    global dialogue_manager, session_manager, dialogue_processor, multi_modal_manager, _initialized
    
    if not _initialized:
        logger.info("初始化API组件...")
        
        # 初始化会话管理器
        session_manager = SessionManager()
        
        # 初始化对话管理器
        dialogue_manager = DialogueManager()
        
        # 初始化多模态管理器
        multi_modal_manager = MultiModalToolManager()
        
        # 初始化对话处理器
        dialogue_processor = DialogueProcessor(
            session_manager=session_manager,
            dialogue_manager=dialogue_manager,
            multi_modal_manager=multi_modal_manager
        )
        
        logger.info("API组件初始化完成")
        _initialized = True

# 会话管理API
@api.route('/dialogue/sessions', methods=['GET'])
def get_sessions():
    """获取会话列表"""
    init_api_components()
    
    try:
        # 解析请求参数
        user_id = request.args.get('userId')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        # 获取会话列表
        sessions = session_manager.get_sessions(user_id, limit, offset)
        
        # 为了兼容所有客户端，返回多种格式
        return jsonify({
            "success": True,
            "data": {"sessions": sessions},
            "sessions": sessions,  # 直接提供会话列表，兼容simple_test.html
            "items": sessions,     # 兼容enhanced_index.html
            "total": len(sessions)
        })
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

@api.route('/dialogue/sessions', methods=['POST'])
def create_session():
    """创建新会话"""
    init_api_components()
    
    try:
        # 解析请求数据
        data = request.json
        user_id = data.get('userId', str(uuid.uuid4()))
        title = data.get('title')
        dialogue_type = data.get('dialogueType', DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
        participants = data.get('participants')
        
        # 创建会话
        session = session_manager.create_session(
            user_id=user_id,
            title=title,
            dialogue_type=dialogue_type,
            participants=participants
        )
        
        # 为了兼容所有客户端，返回多种格式
        return jsonify({
            "success": True,
            "data": session,
            "session": session,  # 直接提供会话，兼容simple_test.html
            "id": session["id"],
            "title": session["title"],
            "createdAt": session["created_at"],
            "userId": session["user_id"],
            "dialogueType": session["dialogue_type"]
        }), 201
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

@api.route('/dialogue/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取特定会话"""
    init_api_components()
    
    try:
        # 获取会话
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "success": False,
                "error": f"会话 {session_id} 不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "data": session,
            "session": session
        })
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api.route('/dialogue/sessions/<session_id>', methods=['PUT'])
def update_session(session_id):
    """更新会话"""
    init_api_components()
    
    try:
        # 解析请求数据
        data = request.json
        
        # 更新会话
        updated_session = session_manager.update_session(session_id, data)
        
        if not updated_session:
            return jsonify({
                "success": False,
                "error": f"会话 {session_id} 不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "data": updated_session,
            "session": updated_session
        })
    except Exception as e:
        logger.error(f"更新会话失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api.route('/dialogue/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    init_api_components()
    
    try:
        # 删除会话
        success = session_manager.delete_session(session_id)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"会话 {session_id} 不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "message": f"会话 {session_id} 已删除"
        })
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api.route('/dialogue/sessions/<session_id>/turns', methods=['GET'])
def get_turns(session_id):
    """获取会话轮次"""
    init_api_components()
    
    try:
        # 获取轮次
        response, status_code = dialogue_processor.get_turns(session_id)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"获取轮次失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 对话处理API
@api.route('/dialogue/input', methods=['POST'])
def process_input():
    """处理用户输入"""
    init_api_components()
    
    try:
        # 解析请求数据
        data = request.json
        
        # 处理输入
        response, status_code = dialogue_processor.process_input(data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"处理输入失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "sessionId": request.json.get("sessionId", ""),
            "input": request.json.get("input", ""),
            "response": f"处理输入时出现错误: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }), 500

# 多模态API
@api.route('/dialogue/upload/image', methods=['POST'])
def upload_image():
    """上传图像"""
    init_api_components()
    
    try:
        # 检查是否有文件
        if 'image' not in request.files:
            return jsonify({
                "success": False,
                "error": "没有上传图像文件"
            }), 400
        
        file = request.files['image']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "没有选择文件"
            }), 400
        
        # 获取会话ID
        session_id = request.form.get('sessionId')
        if not session_id:
            return jsonify({
                "success": False,
                "error": "缺少会话ID"
            }), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_path = os.path.join('uploads', f"{file_id}_{filename}")
        
        # 确保上传目录存在
        os.makedirs('uploads', exist_ok=True)
        
        # 保存文件
        file.save(file_path)
        
        # 获取文件内容用于处理
        with open(file_path, 'rb') as f:
            image_content = f.read()
        
        # 处理图像
        image_result = multi_modal_manager.process_image(image_content)
        
        # 获取描述
        description = request.form.get('description', '')
        
        # 构建元数据
        metadata = {
            "image": {
                "path": file_path,
                "filename": filename,
                "id": file_id,
                "description": description,
                "analysis": image_result
            }
        }
        
        # 构建消息内容
        message_content = f"[上传了图片: {filename}]"
        if description:
            message_content += f"\n描述: {description}"
        
        # 处理输入
        input_data = {
            "sessionId": session_id,
            "input": message_content,
            "inputType": "image",
            "metadata": metadata
        }
        
        response, status_code = dialogue_processor.process_input(input_data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"上传图像失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

@api.route('/dialogue/upload/audio', methods=['POST'])
def upload_audio():
    """上传音频"""
    init_api_components()
    
    try:
        # 检查是否有文件
        if 'audio' not in request.files:
            return jsonify({
                "success": False,
                "error": "没有上传音频文件"
            }), 400
        
        file = request.files['audio']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "没有选择文件"
            }), 400
        
        # 获取会话ID
        session_id = request.form.get('sessionId')
        if not session_id:
            return jsonify({
                "success": False,
                "error": "缺少会话ID"
            }), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_path = os.path.join('uploads', f"{file_id}_{filename}")
        
        # 确保上传目录存在
        os.makedirs('uploads', exist_ok=True)
        
        # 保存文件
        file.save(file_path)
        
        # 获取文件内容用于处理
        with open(file_path, 'rb') as f:
            audio_content = f.read()
        
        # 处理音频
        audio_result = multi_modal_manager.process_audio(audio_content)
        
        # 提取转录文本
        transcribed_text = audio_result.get("transcription", "无法识别音频内容")
        
        # 构建元数据
        metadata = {
            "audio": {
                "path": file_path,
                "filename": filename,
                "id": file_id,
                "analysis": audio_result
            }
        }
        
        # 处理输入
        input_data = {
            "sessionId": session_id,
            "input": transcribed_text,
            "inputType": "audio",
            "metadata": metadata
        }
        
        response, status_code = dialogue_processor.process_input(input_data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"上传音频失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

# 工具API
@api.route('/dialogue/tools', methods=['GET'])
def get_tools():
    """获取可用工具列表"""
    init_api_components()
    
    try:
        # 从多模态管理器获取工具
        tools = multi_modal_manager.get_tools() if multi_modal_manager else []
        
        # 如果没有工具，返回模拟数据
        if not tools:
            tools = [
                {
                    "id": "image_analysis",
                    "name": "图像分析",
                    "description": "分析图像内容",
                    "version": "1.0",
                    "provider": "System"
                },
                {
                    "id": "audio_transcription",
                    "name": "音频转写",
                    "description": "将音频转写为文本",
                    "version": "1.0",
                    "provider": "System"
                },
                {
                    "id": "calculator",
                    "name": "计算器",
                    "description": "执行数学计算",
                    "version": "1.0",
                    "provider": "System"
                }
            ]
        
        return jsonify({
            "success": True,
            "data": {"tools": tools},
            "tools": tools,
            "total": len(tools)
        })
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 系统API
@api.route('/system/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    init_api_components()
    
    try:
        # 收集系统状态信息
        status = {
            "version": "1.0.0",
            "uptime": "获取系统运行时间",
            "sessions": {
                "total": len(session_manager.get_sessions()),
                "active": len(session_manager.get_sessions(limit=100))
            },
            "ai_service": {
                "status": "online",
                "model": "gpt-3.5-turbo"
            },
            "storage": {
                "status": "healthy",
                "type": "SQLite"
            },
            "tools": {
                "total": len(multi_modal_manager.get_tools()) if multi_modal_manager else 0,
                "status": "online"
            }
        }
        
        return jsonify({
            "success": True,
            "data": status,
            "status": status
        })
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 对话类型API
@api.route('/dialogue/types', methods=['GET'])
def get_dialogue_types():
    """获取支持的对话类型"""
    try:
        return jsonify({
            "success": True,
            "data": DIALOGUE_TYPES,
            "types": DIALOGUE_TYPES
        })
    except Exception as e:
        logger.error(f"获取对话类型失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 文件访问API
@api.route('/uploads/<path:filename>', methods=['GET'])
def get_uploaded_file(filename):
    """获取上传的文件"""
    try:
        return send_file(os.path.join('uploads', filename))
    except Exception as e:
        logger.error(f"获取文件失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404

# 注册API路由
def register_api_routes(app):
    """注册API路由到Flask应用"""
    app.register_blueprint(api)
    logger.info("API路由已注册")
