"""
旧版 API 适配器

提供与旧版前端兼容的 API 路由，将旧的请求格式转换为新的格式。
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from ..utils.logger import get_logger
from ..storage.thread_safe_db import get_connection, execute_query

# 配置日志
logger = get_logger(__name__)

# 创建Blueprint
legacy_api = Blueprint('legacy_api', __name__, url_prefix='/api')

# 对话类型映射
DIALOGUE_TYPE_MAPPING = {
    "HUMAN_AI_PRIVATE": "human_to_ai_private",
    "HUMAN_HUMAN_PRIVATE": "human_to_human_private",
    "HUMAN_HUMAN_GROUP": "human_to_human_group",
    "AI_AI": "ai_to_ai",
    "AI_SELF_REFLECTION": "ai_self_reflection",
    "HUMAN_AI_GROUP": "human_to_ai_group",
    "AI_HUMANS": "ai_to_humans"
}

@legacy_api.route('/dialogue/sessions', methods=['GET'])
def get_legacy_sessions():
    """获取会话列表（旧版 API）"""
    try:
        # 获取查询参数
        user_id = request.args.get('userId')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # 构建查询
        query = "SELECT * FROM sessions"
        params = []
        
        if user_id:
            query += " WHERE user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # 执行查询
        sessions = execute_query(query, params)
        
        # 处理元数据
        for session in sessions:
            if "metadata" in session and session["metadata"]:
                try:
                    session["metadata"] = json.loads(session["metadata"])
                    if "participants" in session["metadata"]:
                        session["participants"] = session["metadata"]["participants"]
                except:
                    pass
            
            # 添加旧版字段
            session["userId"] = session.get("user_id")
            session["dialogueType"] = session.get("dialogue_type", "").upper()
            session["createdAt"] = session.get("created_at")
            session["updatedAt"] = session.get("updated_at")
            session["lastActivityAt"] = session.get("last_activity_at")
        
        logger.info(f"旧版API: 获取会话列表成功: {len(sessions)} 条记录")
        
        return jsonify({
            "success": True,
            "data": sessions,
            "sessions": sessions,
            "count": len(sessions),
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        logger.error(f"旧版API: 获取会话列表失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

@legacy_api.route('/dialogue/sessions', methods=['POST'])
def create_legacy_session():
    """创建新会话（旧版 API）"""
    try:
        # 解析请求数据
        data = request.json
        user_id = data.get('userId', data.get('user_id', str(os.urandom(4).hex())))
        title = data.get('title', f"与{user_id}的对话")
        dialogue_type = data.get('dialogueType', data.get('dialogue_type', "HUMAN_AI_PRIVATE"))
        participants = data.get('participants')
        
        # 转换对话类型
        normalized_dialogue_type = DIALOGUE_TYPE_MAPPING.get(dialogue_type, "human_to_ai_private")
        
        # 准备转发的数据
        forwarded_data = {
            "user_id": user_id,
            "title": title,
            "dialogue_type": normalized_dialogue_type,
            "participants": participants
        }
        
        # 转发到新的 API 端点
        from flask import current_app
        with current_app.test_client() as client:
            response = client.post(
                '/api/v1/sessions',
                json=forwarded_data,
                headers={'Content-Type': 'application/json'}
            )
            
            result = json.loads(response.data)
            
            # 添加旧版字段
            if result.get("success") and "session" in result:
                session = result["session"]
                session["userId"] = session.get("user_id")
                session["dialogueType"] = session.get("dialogue_type", "").upper()
                session["createdAt"] = session.get("created_at")
                session["updatedAt"] = session.get("updated_at")
                session["lastActivityAt"] = session.get("last_activity_at")
            
            logger.info(f"旧版API: 创建会话成功: {result.get('id')}")
            
            return jsonify(result), response.status_code
    except Exception as e:
        logger.error(f"旧版API: 创建会话失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

@legacy_api.route('/dialogue/sessions/<session_id>', methods=['GET'])
def get_legacy_session(session_id):
    """获取会话详情（旧版 API）"""
    try:
        # 转发到新的 API 端点
        from flask import current_app
        with current_app.test_client() as client:
            response = client.get(f'/api/v1/sessions/{session_id}')
            
            result = json.loads(response.data)
            
            # 添加旧版字段
            if result.get("success") and "session" in result:
                session = result["session"]
                session["userId"] = session.get("user_id")
                session["dialogueType"] = session.get("dialogue_type", "").upper()
                session["createdAt"] = session.get("created_at")
                session["updatedAt"] = session.get("updated_at")
                session["lastActivityAt"] = session.get("last_activity_at")
                
                # 处理轮次
                if "turns" in session:
                    for turn in session["turns"]:
                        turn["sessionId"] = turn.get("session_id")
                        turn["createdAt"] = turn.get("created_at")
                        
                        # 创建请求消息和响应消息
                        if turn["role"] == "user":
                            turn["request_messages"] = [
                                {
                                    "role": "user",
                                    "content": turn["content"],
                                    "created_at": turn["created_at"]
                                }
                            ]
                        elif turn["role"] == "assistant":
                            turn["response_messages"] = [
                                {
                                    "role": "assistant",
                                    "content": turn["content"],
                                    "created_at": turn["created_at"]
                                }
                            ]
            
            logger.info(f"旧版API: 获取会话详情成功: {session_id}")
            
            return jsonify(result), response.status_code
    except Exception as e:
        logger.error(f"旧版API: 获取会话详情失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

@legacy_api.route('/dialogue/sessions/<session_id>/turns', methods=['GET'])
def get_legacy_turns(session_id):
    """获取会话轮次（旧版 API）"""
    try:
        # 转发到新的 API 端点
        from flask import current_app
        with current_app.test_client() as client:
            response = client.get(f'/api/v1/sessions/{session_id}/turns')
            
            result = json.loads(response.data)
            
            # 添加旧版字段
            if result.get("success") and "turns" in result:
                turns = result["turns"]
                for turn in turns:
                    turn["sessionId"] = turn.get("session_id")
                    turn["createdAt"] = turn.get("created_at")
                    
                    # 创建请求消息和响应消息
                    if turn["role"] == "user":
                        turn["request_messages"] = [
                            {
                                "role": "user",
                                "content": turn["content"],
                                "created_at": turn["created_at"]
                            }
                        ]
                    elif turn["role"] == "assistant":
                        turn["response_messages"] = [
                            {
                                "role": "assistant",
                                "content": turn["content"],
                                "created_at": turn["created_at"]
                            }
                        ]
            
            logger.info(f"旧版API: 获取会话轮次成功: {session_id}")
            
            return jsonify(result), response.status_code
    except Exception as e:
        logger.error(f"旧版API: 获取会话轮次失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

@legacy_api.route('/dialogue/input', methods=['POST'])
def process_legacy_input():
    """处理对话输入（旧版 API）"""
    try:
        # 解析请求数据
        data = request.json
        session_id = data.get('sessionId', data.get('session_id'))
        user_id = data.get('userId', data.get('user_id'))
        content = data.get('input', data.get('content'))
        input_type = data.get('type', 'text')
        
        # 验证必要参数
        if not user_id:
            return jsonify({
                "success": False,
                "error": "缺少用户ID"
            }), 400
        
        if not content:
            return jsonify({
                "success": False,
                "error": "缺少内容"
            }), 400
        
        if not session_id:
            return jsonify({
                "success": False,
                "error": "缺少会话ID"
            }), 400
        
        # 准备转发的数据
        forwarded_data = {
            "session_id": session_id,
            "user_id": user_id,
            "content": content
        }
        
        # 转发到新的 API 端点
        from flask import current_app
        with current_app.test_client() as client:
            response = client.post(
                '/api/v1/dialogue/process',
                json=forwarded_data,
                headers={'Content-Type': 'application/json'}
            )
            
            result = json.loads(response.data)
            
            # 添加旧版字段
            if result.get("success"):
                if "user_turn" in result:
                    result["user_turn"]["sessionId"] = result["user_turn"].get("session_id")
                    result["user_turn"]["createdAt"] = result["user_turn"].get("created_at")
                
                if "ai_turn" in result:
                    result["ai_turn"]["sessionId"] = result["ai_turn"].get("session_id")
                    result["ai_turn"]["createdAt"] = result["ai_turn"].get("created_at")
                
                # 添加旧版响应格式
                result["final_response"] = result.get("response")
                result["text"] = result.get("response")
            
            logger.info(f"旧版API: 处理对话输入成功: {session_id}")
            
            return jsonify(result), response.status_code
    except Exception as e:
        logger.error(f"旧版API: 处理对话输入失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

@legacy_api.route('/dialogue/tools', methods=['GET'])
def get_legacy_tools():
    """获取工具列表（旧版 API）"""
    try:
        # 创建静态工具列表
        tools = [
            {
                "id": "weather",
                "name": "天气查询",
                "description": "查询指定城市的天气情况",
                "icon": "cloud-sun"
            },
            {
                "id": "calculator",
                "name": "计算器",
                "description": "执行数学计算",
                "icon": "calculator"
            },
            {
                "id": "image_gen",
                "name": "图像生成",
                "description": "根据描述生成图像",
                "icon": "image"
            }
        ]
        
        logger.info("旧版API: 获取工具列表成功")
        
        return jsonify({
            "success": True,
            "tools": tools
        })
    except Exception as e:
        logger.error(f"旧版API: 获取工具列表失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

@legacy_api.route('/system/status_enhanced', methods=['GET'])
def get_legacy_system_status():
    """获取系统状态（旧版 API）"""
    try:
        # 创建静态系统状态信息
        status_data = {
            "status": "正常",
            "version": "v1.0.0",
            "timestamp": "2025-05-27T14:00:00.000Z",
            "components": {
                "API服务器": True,
                "会话管理": True,
                "对话处理": True,
                "数据存储": True,
                "聊天API": True
            },
            "tools_count": 3
        }
        
        logger.info("旧版API: 获取系统状态成功")
        
        return jsonify(status_data)
    except Exception as e:
        logger.error(f"旧版API: 获取系统状态失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

def register_legacy_api_routes(app):
    """注册旧版 API 路由
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(legacy_api)
    logger.info("旧版 API 路由已注册")
