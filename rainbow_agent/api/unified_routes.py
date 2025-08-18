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
import functools
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime

from flask import Blueprint, request, jsonify, send_file, Response
from flask_login import current_user
from werkzeug.utils import secure_filename

from rainbow_agent.auth.routes import require_auth

from rainbow_agent.core.dialogue_manager import DialogueManager, DIALOGUE_TYPES
from rainbow_agent.api.unified_dialogue_processor import UnifiedDialogueProcessor
from rainbow_agent.storage.unified_session_manager import UnifiedSessionManager
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage

# Create aliases for backward compatibility
DialogueProcessor = UnifiedDialogueProcessor
SessionManager = UnifiedSessionManager
from rainbow_agent.core.multi_modal_manager import MultiModalToolManager
from rainbow_agent.memory.memory import Memory
from rainbow_agent.memory.surreal_memory import SurrealMemory
from rainbow_agent.frequency.frequency_integrator import FrequencyIntegrator
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

# 通用错误处理函数
def handle_api_error(e: Exception, status_code: int = 500) -> Response:
    """通用API错误处理函数"""

    logger.error(f"API错误: {str(e)}")

    return jsonify({
        "success": False,
        "error": str(e)
    }), status_code


# 确保组件已初始化的装饰器
def ensure_initialized(f: Callable) -> Callable:
    """确保 API 组件已初始化的装饰器"""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        init_api_components()
        return f(*args, **kwargs)
    return decorated

def init_api_components():
    """初始化API组件"""
    global dialogue_manager, session_manager, dialogue_processor, multi_modal_manager, _initialized
    
    if not _initialized:
        logger.info("初始化API组件...")
        
        # 初始化记忆系统
        try:
            memory = SurrealMemory()
            logger.info("SurrealDB记忆系统初始化成功")
        except Exception as e:
            logger.warning(f"SurrealDB记忆系统初始化失败: {e}，将使用空记忆系统")
            memory = None
        
        # 初始化会话管理器
        session_manager = SessionManager()
        
        # 初始化统一对话存储
        unified_storage = UnifiedDialogueStorage()
        
        # 初始化对话管理器
        dialogue_manager = DialogueManager(storage=unified_storage, memory=memory)
        
        # 初始化多模态工具管理器
        multi_modal_manager = MultiModalToolManager()
        
        # 初始化对话处理器
        dialogue_processor = DialogueProcessor(
            storage=unified_storage,  # UnifiedDialogueProcessor expects UnifiedDialogueStorage
            dialogue_manager=dialogue_manager
            # multi_modal_manager is not used by UnifiedDialogueProcessor
        )
        
        logger.info("API组件初始化完成，频率感知系统：{}".
                   format("已启用" if dialogue_manager.frequency_integrator else "未启用"))
        _initialized = True

# 会话管理API
@api.route('/dialogue/sessions', methods=['GET'])
@ensure_initialized
@require_auth  # 添加身份验证装饰器
def get_sessions():
    """获取会话列表"""
    try:
        # 确保用户已经通过身份验证
        logger.debug(f"Sessions check - current_user: {current_user}, is_authenticated: {current_user.is_authenticated}")
        if not current_user.is_authenticated:
            logger.warning("User not authenticated when accessing /dialogue/sessions")
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "message": "You must be logged in to access this resource"
            }), 401
        
        # 使用当前登录用户的 ID，而不是从 URL 参数获取
        user_id = current_user.id
        logger.info(f"Fetching sessions for authenticated user: {user_id}")
        
        # 获取分页参数
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        logger.debug(f"Pagination parameters: limit={limit}, offset={offset}")
        
        # 获取会话列表，使用 get_user_sessions 方法
        sessions = session_manager.get_user_sessions(user_id, limit, offset)
        logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}")
        
        # 为了兼容所有客户端，返回多种格式
        response_data = {
            "success": True,
            "data": {"sessions": sessions},
            "sessions": sessions,  # 直接提供会话列表，兼容simple_test.html
            "items": sessions,     # 兼容enhanced_index.html
            "total": len(sessions)
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in get_sessions: {str(e)}")
        return handle_api_error(e)

@api.route('/dialogue/sessions', methods=['POST'])
@ensure_initialized
@require_auth
def create_session():
    """创建新会话"""
    print("🔥 CREATE SESSION ENDPOINT CALLED!")  # Debug print
    try:
        # 解析请求数据
        data = request.json
        # 使用当前已认证用户的ID，忽略前端传递的userId
        from flask_login import current_user
        # 处理SurrealDB的复杂ID格式
        raw_user_id = current_user.id
        if isinstance(raw_user_id, dict) and 'id' in raw_user_id:
            user_id = raw_user_id['id']
        else:
            user_id = str(raw_user_id)
        title = data.get('title')
        dialogue_type = data.get('dialogueType', DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
        participants = data.get('participants')
        
        # 调试日志：记录输入参数
        logger.info(f"=== 创建会话调试信息 ===")
        logger.info(f"原始current_user.id: {raw_user_id} (类型: {type(raw_user_id)})")
        logger.info(f"处理后的user_id: {user_id} (类型: {type(user_id)})")
        logger.info(f"接收到的title: {title}")
        logger.info(f"接收到的dialogue_type: {dialogue_type}")
        logger.info(f"session_manager实例: {session_manager}")
        logger.info(f"session_manager类型: {type(session_manager)}")
        
        # 构建元数据
        metadata = {}
        if dialogue_type:
            metadata['dialogue_type'] = dialogue_type
        if participants:
            metadata['participants'] = participants
        
        logger.info(f"构建的metadata: {metadata}")
        
        # 创建会话
        logger.info(f"调用session_manager.create_session，参数: user_id={user_id}, title={title}")
        session = session_manager.create_session(
            user_id=user_id,
            title=title,
            metadata=metadata
        )
        
        logger.info(f"session_manager.create_session返回: {session}")
        if session:
            logger.info(f"返回会话的user_id: {session.get('user_id')}")
        else:
            logger.error("session_manager.create_session返回None!")
        
        # 为了兼容所有客户端，返回多种格式
        return jsonify({
            "success": True,
            "data": session,
            "session": session,  # 直接提供会话，兼容simple_test.html
            "id": session["id"],
            "title": session["title"],
            "createdAt": session["created_at"],
            "userId": session["user_id"],
            "dialogueType": session.get("metadata", {}).get("dialogue_type", dialogue_type)
        }), 201
    except Exception as e:
        return handle_api_error(e)

@api.route('/dialogue/sessions/<session_id>', methods=['GET'])
@ensure_initialized
@require_auth
def get_session(session_id):
    """获取特定会话"""
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
        return handle_api_error(e)

@api.route('/dialogue/sessions/<session_id>', methods=['PUT'])
@ensure_initialized
def update_session(session_id):
    """更新会话"""
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
        return handle_api_error(e)

@api.route('/dialogue/sessions/<session_id>', methods=['DELETE'])
@ensure_initialized
def delete_session(session_id):
    """删除会话"""
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
        return handle_api_error(e)

@api.route('/dialogue/sessions/<session_id>/turns', methods=['GET'])
@ensure_initialized
@require_auth
def get_turns(session_id):
    """获取会话轮次 - 优化版本"""
    import time
    start_time = time.time()
    
    try:
        # 首先验证会话是否属于当前用户
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "success": False,
                "error": f"会话 {session_id} 不存在"
            }), 404
        
        # 检查会话是否属于当前用户
        from flask_login import current_user
        if session.get('user_id') != current_user.id:
            return jsonify({
                "success": False,
                "error": "无权访问此会话"
            }), 403
        
        # 获取轮次 - 添加超时保护
        import asyncio
        try:
            response = asyncio.wait_for(
                dialogue_processor.get_session_history(session_id),
                timeout=30.0  # 30秒超时
            )
            response = asyncio.run(response)
            
            processing_time = time.time() - start_time
            logger.info(f"获取会话轮次耗时: {processing_time:.2f}秒")
            
            return jsonify(response), 200
            
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            logger.warning(f"获取会话轮次超时: {processing_time:.2f}秒")
            return jsonify({
                "success": False,
                "error": "请求处理超时",
                "message": "会话数据较多，请稍后重试"
            }), 408
    except Exception as e:
        return handle_api_error(e)

# 对话处理API
@api.route('/dialogue/input', methods=['POST'])
@ensure_initialized
@require_auth
def process_input():
    """处理用户输入"""
    try:
        # 解析请求数据
        data = request.json
        
        # 从数据字典中提取参数 (支持两种格式)
        user_input = data.get('content', '') or data.get('input', '')
        # 使用当前已认证用户的ID，忽略前端传递的userId
        from flask_login import current_user
        # 处理SurrealDB的复杂ID格式
        raw_user_id = current_user.id
        if isinstance(raw_user_id, dict) and 'id' in raw_user_id:
            user_id = raw_user_id['id']
        else:
            user_id = str(raw_user_id)
        session_id = data.get('sessionId')
        input_type = data.get('input_type', '') or data.get('inputType', 'text')
        context = data.get('metadata') or data.get('context')
        
        # 处理输入使用同步版本
        response = dialogue_processor.process_input_sync(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            input_type=input_type,
            context=context
        )
        status_code = 200
        
        # 检查是否启用了频率感知系统
        if hasattr(dialogue_manager, 'frequency_integrator') and dialogue_manager.frequency_integrator:
            # 使用已认证用户的ID（user_id变量已在上面定义）
            session_id = data.get('sessionId')
            
            # 异步更新用户交互计数（不阻塞响应）
            try:
                import threading
                update_thread = threading.Thread(
                    target=dialogue_manager.frequency_integrator.record_interaction,
                    args=(user_id, session_id, "user_input")
                )
                update_thread.daemon = True
                update_thread.start()
                logger.debug(f"异步更新用户交互计数: {user_id}")
            except Exception as e:
                logger.warning(f"更新用户交互计数失败: {e}")
        
        return jsonify(response), status_code
    except Exception as e:
        # 保留详细的错误信息，因为这是核心功能
        logger.error(f"处理输入失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback,
            "sessionId": request.json.get("sessionId", ""),
            "input": request.json.get("input", ""),
            "response": f"处理输入时出现错误: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }), 500

# 多模态API
@api.route('/dialogue/upload/image', methods=['POST'])
@ensure_initialized
def upload_image():
    """上传图像"""
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

# 频率感知系统API
@api.route('/frequency/expressions', methods=['GET'])
def get_pending_expressions():
    """获取待处理的主动表达"""
    init_api_components()
    
    try:
        # 解析请求参数
        user_id = request.args.get('userId')
        session_id = request.args.get('sessionId')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数: userId"
            }), 400
        
        # 如果对话管理器没有频率集成器，返回空列表
        if not dialogue_manager or not dialogue_manager.frequency_integrator:
            return jsonify({
                "success": True,
                "data": {"expressions": []},
                "expressions": [],
                "message": "频率感知系统未启用"
            })
        
        # 获取待处理的主动表达
        expressions = dialogue_manager.frequency_integrator.get_pending_expressions(user_id, session_id)
        
        return jsonify({
            "success": True,
            "data": {"expressions": expressions},
            "expressions": expressions,
            "total": len(expressions)
        })
    except Exception as e:
        logger.error(f"获取待处理的主动表达失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api.route('/frequency/settings', methods=['GET'])
def get_frequency_settings():
    """获取频率感知系统设置"""
    init_api_components()
    
    try:
        # 解析请求参数
        user_id = request.args.get('userId')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数: userId"
            }), 400
        
        # 如果对话管理器没有频率集成器，返回默认设置
        if not dialogue_manager or not dialogue_manager.frequency_integrator:
            return jsonify({
                "success": True,
                "data": {
                    "enabled": False,
                    "expressionFrequency": "medium",
                    "relationshipStage": "initial",
                    "expressionTypes": ["greeting", "farewell", "reminder"]
                },
                "message": "频率感知系统未启用"
            })
        
        # 获取用户的频率设置
        settings = dialogue_manager.frequency_integrator.get_user_settings(user_id)
        
        return jsonify({
            "success": True,
            "data": settings,
            "settings": settings
        })
    except Exception as e:
        logger.error(f"获取频率感知系统设置失败: {e}")
@api.route('/frequency/settings', methods=['POST'])
@ensure_initialized
def update_frequency_settings():
    """更新频率感知系统设置"""
    
    try:
        # 解析请求数据
        data = request.json
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数: userId"
            }), 400
        
        # 如果对话管理器没有频率集成器，返回错误
        if not dialogue_manager or not dialogue_manager.frequency_integrator:
            return jsonify({
                "success": False,
                "error": "频率感知系统未启用",
                "message": "频率感知系统未启用"
            }), 400
        
        # 更新用户的频率设置
        settings = dialogue_manager.frequency_integrator.update_user_settings(user_id, data)
        
        return jsonify({
            "success": True,
            "data": settings,
            "settings": settings,
            "message": "频率感知系统设置已更新"
        })
    except Exception as e:
        logger.error(f"更新频率感知系统设置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api.route('/frequency/trigger', methods=['POST'])
@ensure_initialized
def trigger_expression():
    """触发主动表达"""
    
    try:
        # 解析请求数据
        data = request.json
        user_id = data.get('userId')
        session_id = data.get('sessionId')
        expression_type = data.get('expressionType', 'greeting')
        
        if not user_id or not session_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数: userId 和 sessionId"
            }), 400
        
        # 如果对话管理器没有频率集成器，返回错误
        if not dialogue_manager or not dialogue_manager.frequency_integrator:
            return jsonify({
                "success": False,
                "error": "频率感知系统未启用",
                "message": "频率感知系统未启用"
            }), 400
        
        # 触发主动表达
        expression = dialogue_manager.frequency_integrator.trigger_expression(
            user_id=user_id,
            session_id=session_id,
            expression_type=expression_type
        )
        
        return jsonify({
            "success": True,
            "data": {"expression": expression},
            "expression": expression,
            "message": "主动表达已触发"
        })
    except Exception as e:
        logger.error(f"触发主动表达失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 注册API路由
def register_api_routes(app):
    """注册API路由到Flask应用"""
    app.register_blueprint(api)
    logger.info("API路由已注册")
