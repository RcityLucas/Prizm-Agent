"""
Flask路由处理模块

为surreal_api_server.py提供路由处理功能
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from flask import request, jsonify, send_from_directory, Blueprint

from rainbow_agent.core.dialogue_manager import DIALOGUE_TYPES
from rainbow_agent.storage.async_utils import run_async
from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# 创建蓝图
dialogue_bp = Blueprint('dialogue', __name__, url_prefix='/api/dialogue')
sessions_bp = Blueprint('sessions', __name__, url_prefix='/api/sessions')
tools_bp = Blueprint('tools', __name__, url_prefix='/api/tools')

# 全局变量，将在注册路由时设置
session_manager = None
turn_manager = None
dialogue_manager = None
multi_modal_manager = None

def init_route_handlers(components):
    """
    初始化路由处理器
    
    Args:
        components: 系统组件字典
    """
    global session_manager, turn_manager, dialogue_manager, multi_modal_manager
    
    session_manager = components.get('session_manager')
    turn_manager = components.get('turn_manager')
    dialogue_manager = components.get('dialogue_manager')
    multi_modal_manager = components.get('multi_modal_manager')
    
    logger.info("路由处理器初始化完成")

# 工具路由
@tools_bp.route('/dialogue-tools', methods=['GET'])
def get_dialogue_tools():
    """获取可用的工具列表"""
    try:
        # 构建工具列表
        tools = [
            {
                "id": "web_search",
                "name": "网络搜索",
                "description": "搜索互联网获取信息",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    }
                }
            },
            {
                "id": "calculator",
                "name": "计算器",
                "description": "执行数学计算",
                "parameters": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式"
                    }
                }
            },
            {
                "id": "weather",
                "name": "天气查询",
                "description": "获取指定地点的天气信息",
                "parameters": {
                    "location": {
                        "type": "string",
                        "description": "地点名称"
                    }
                }
            },
            {
                "id": "image_generator",
                "name": "图像生成",
                "description": "根据描述生成图像",
                "parameters": {
                    "prompt": {
                        "type": "string",
                        "description": "图像描述"
                    },
                    "style": {
                        "type": "string",
                        "description": "图像风格",
                        "enum": ["realistic", "cartoon", "sketch", "oil_painting"]
                    }
                }
            }
        ]
        
        # 如果有多模态管理器，添加多模态工具
        if multi_modal_manager:
            multi_modal_tools = multi_modal_manager.get_tools()
            tools.extend(multi_modal_tools)
        
        return jsonify({
            "tools": tools,
            "count": len(tools)
        })
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "获取工具列表失败"
        }), 500

# 会话路由
@sessions_bp.route('/', methods=['GET'])
def get_dialogue_sessions():
    """获取对话会话列表，适配增强版前端"""
    try:
        # 获取查询参数
        user_id = request.args.get('userId')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        logger.info(f"获取会话列表: user_id={user_id}, limit={limit}, offset={offset}")
        
        # 从会话管理器获取会话列表
        sessions = run_async(session_manager.get_sessions, user_id, limit, offset)
        
        # 格式化会话数据
        formatted_sessions = []
        for session in sessions:
            # 获取对话类型和参与者
            metadata = session.get("metadata", {})
            dialogue_type = metadata.get("dialogue_type", DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
            participants = metadata.get("participants", [])
            status = metadata.get("status", "active")
            
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
                "status": status
            }
            
            formatted_sessions.append(formatted_session)
        
        # 返回会话列表
        return jsonify({
            "items": formatted_sessions,
            "total": len(formatted_sessions),
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"获取会话列表失败: {e}\n{error_traceback}")
        return jsonify({
            "error": str(e),
            "traceback": error_traceback
        }), 500

@sessions_bp.route('/', methods=['POST'])
def create_dialogue_session():
    """创建新会话，适配增强版前端"""
    try:
        # 获取请求数据
        data = request.json
        
        # 提取必要字段
        user_id = data.get('userId')
        title = data.get('title')
        dialogue_type = data.get('dialogueType', DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
        participants = data.get('participants', [])
        
        # 验证必要字段
        if not user_id:
            return jsonify({
                "error": "缺少必要字段: userId",
                "message": "创建会话失败: 缺少用户ID"
            }), 400
        
        logger.info(f"创建新会话: user_id={user_id}, title={title}, dialogue_type={dialogue_type}")
        
        # 创建会话
        session = run_async(
            dialogue_manager.create_session,
            user_id=user_id,
            title=title,
            dialogue_type=dialogue_type,
            participants=participants
        )
        
        # 格式化会话数据
        metadata = session.get("metadata", {})
        dialogue_type = metadata.get("dialogue_type", DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
        participants = metadata.get("participants", [])
        status = metadata.get("status", "active")
        
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
            "status": status
        }
        
        # 返回创建的会话
        return jsonify(formatted_session), 201
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"创建会话失败: {e}\n{error_traceback}")
        return jsonify({
            "error": str(e),
            "traceback": error_traceback
        }), 500

@sessions_bp.route('/<session_id>', methods=['GET'])
def get_dialogue_session(session_id):
    """获取指定会话ID的会话信息"""
    try:
        logger.info(f"开始获取会话 {session_id} 的信息")
        
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

@sessions_bp.route('/<session_id>/turns', methods=['GET'])
def get_dialogue_turns(session_id):
    """获取指定会话的对话轮次"""
    try:
        logger.info(f"开始获取会话 {session_id} 的轮次")
        
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

# 对话输入路由
@dialogue_bp.route('/input', methods=['POST'])
def process_dialogue_input():
    """处理用户输入，生成AI响应并创建新的对话轮次"""
    try:
        # 获取请求数据
        data = request.json
        
        # 提取必要字段
        session_id = data.get('sessionId')
        user_id = data.get('userId', 'anonymous')
        content = data.get('input', '')
        input_type = data.get('inputType', 'text')
        model = data.get('model', 'gpt-3.5-turbo')
        
        # 验证必要字段
        if not session_id:
            return jsonify({
                "error": "缺少必要字段: sessionId",
                "message": "处理输入失败: 缺少会话ID"
            }), 400
        
        if not content:
            return jsonify({
                "error": "缺少必要字段: input",
                "message": "处理输入失败: 缺少输入内容"
            }), 400
        
        logger.info(f"处理用户输入: session_id={session_id}, user_id={user_id}, input_type={input_type}")
        
        # 处理多模态输入
        if input_type != 'text' and multi_modal_manager:
            try:
                # 处理多模态内容
                if input_type == 'image':
                    processed_content = multi_modal_manager.process_image(content)
                elif input_type == 'audio':
                    processed_content = multi_modal_manager.process_audio(content)
                else:
                    processed_content = content
                
                # 更新内容
                content = processed_content
                logger.info(f"多模态处理成功: {input_type}")
            except Exception as modal_error:
                logger.error(f"多模态处理失败: {modal_error}")
                # 继续使用原始内容
        
        # 构建元数据
        metadata = {
            "user_id": user_id,
            "input_type": input_type,
            "model": model,
            "client_timestamp": data.get('timestamp', datetime.now().isoformat())
        }
        
        # 处理用户输入
        result = run_async(
            dialogue_manager.process_input,
            session_id=session_id,
            user_id=user_id,
            content=content,
            input_type=input_type,
            metadata=metadata
        )
        
        # 返回处理结果
        return jsonify(result)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"处理用户输入失败: {e}\n{error_traceback}")
        return jsonify({
            "error": str(e),
            "traceback": error_traceback,
            "id": data.get('id', ''),
            "input": data.get('input', ''),
            "response": f"处理输入时出现错误: {str(e)}",
            "sessionId": data.get('sessionId', ''),
            "timestamp": datetime.now().isoformat()
        }), 500

# 对话类型路由
@dialogue_bp.route('/dialogue-types', methods=['GET'])
def get_dialogue_types():
    """获取支持的对话类型"""
    return jsonify(DIALOGUE_TYPES), 200

# 系统状态路由
@dialogue_bp.route('/system-status', methods=['GET'])
def get_system_status_enhanced():
    """获取系统状态，适配增强版前端"""
    try:
        # 获取会话数量
        sessions_count = len(run_async(session_manager.get_sessions))
        
        # 构建系统状态
        status = {
            "status": "ok",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "sessions_count": sessions_count,
            "storage_type": "SurrealDB" if hasattr(session_manager, "storage") else "SQLite",
            "features": {
                "multi_modal": multi_modal_manager is not None,
                "dialogue_types": list(DIALOGUE_TYPES.keys()),
                "tools": True
            }
        }
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# 静态文件路由
def serve_static(path):
    """提供静态文件访问"""
    return send_from_directory('static', path)

# 首页路由
def home():
    """服务器首页，提供系统介绍和功能展示"""
    return send_from_directory('static', 'index.html')

def standard_interface():
    """标准界面，提供原始的标准界面"""
    return send_from_directory('static', 'standard_interface.html')

def enhanced_interface():
    """增强版界面，提供增强版界面"""
    return send_from_directory('static', 'enhanced_interface.html')

def chat():
    """对话界面，提供简单的对话界面和文档"""
    return send_from_directory('static', 'chat.html')

def register_routes(app):
    """
    注册所有路由
    
    Args:
        app: Flask应用实例
    """
    # 注册蓝图
    app.register_blueprint(dialogue_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(tools_bp)
    
    # 注册静态文件路由
    app.route('/static/<path:path>')(serve_static)
    
    # 注册首页路由
    app.route('/')(home)
    app.route('/standard')(standard_interface)
    app.route('/enhanced')(enhanced_interface)
    app.route('/chat')(chat)
    
    logger.info("所有路由注册完成")
