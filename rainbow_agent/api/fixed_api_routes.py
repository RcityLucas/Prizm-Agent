"""
修复的 API 路由模块

提供修复后的 API 路由，使用线程安全的数据库连接，解决多线程环境下的数据库锁定问题。
"""
import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

from ..storage.thread_safe_db import get_connection, execute_query
from ..utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# 创建Blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# 对话类型
DIALOGUE_TYPES = [
    "human_to_human_private",  # 人类与人类私聊
    "human_to_human_group",    # 人类与人类群聊
    "human_to_ai_private",     # 人类与AI私聊
    "ai_to_ai",               # AI与AI对话
    "ai_self_reflection",      # AI自我反思
    "human_to_ai_group",       # 人类与AI群聊
    "ai_to_humans"             # AI与多个人类群聊
]

# 测试路由
@api_v1.route('/test', methods=['GET'])
def test():
    """测试API是否正常工作"""
    return jsonify({
        "success": True,
        "message": "API V1 测试成功",
        "time": datetime.now().isoformat()
    })

# 获取对话类型
@api_v1.route('/dialogue_types', methods=['GET'])
def get_dialogue_types():
    """获取支持的对话类型"""
    return jsonify({
        "success": True,
        "dialogue_types": DIALOGUE_TYPES
    })

# 创建会话
@api_v1.route('/sessions', methods=['POST'])
def create_session():
    """创建新会话"""
    try:
        # 解析请求数据
        data = request.json
        user_id = data.get('user_id', data.get('userId', str(uuid.uuid4())))
        title = data.get('title', f"与{user_id}的对话")
        dialogue_type = data.get('dialogue_type', data.get('dialogueType', "human_to_ai_private"))
        participants = data.get('participants')
        
        # 验证对话类型
        if dialogue_type not in DIALOGUE_TYPES:
            return jsonify({
                "success": False,
                "error": f"无效的对话类型: {dialogue_type}",
                "valid_types": DIALOGUE_TYPES
            }), 400
        
        # 准备会话数据
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        
        # 默认参与者
        if not participants:
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
        
        # 创建会话数据
        session_data = {
            "id": session_id,
            "title": title,
            "user_id": user_id,
            "dialogue_type": dialogue_type,
            "created_at": now,
            "updated_at": now,
            "last_activity_at": now,
            "metadata": json.dumps({
                "participants": participants
            })
        }
        
        # 插入会话
        conn = get_connection()
        cursor = conn.cursor()
        
        # 构建SQL
        fields = ", ".join(session_data.keys())
        placeholders = ", ".join(["?" for _ in session_data.keys()])
        values = list(session_data.values())
        
        cursor.execute(f"INSERT INTO sessions ({fields}) VALUES ({placeholders})", values)
        
        # 添加参与者字段
        session_data["participants"] = participants
        
        logger.info(f"创建会话成功: {session_id}")
        
        # 为了兼容所有客户端，返回多种格式
        return jsonify({
            "success": True,
            "data": session_data,
            "session": session_data,
            "id": session_data["id"],
            "title": session_data["title"],
            "createdAt": session_data.get("created_at", now),
            "userId": session_data["user_id"],
            "dialogueType": session_data["dialogue_type"]
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

# 获取会话列表
@api_v1.route('/sessions', methods=['GET'])
def get_sessions():
    """获取会话列表"""
    try:
        # 获取查询参数
        user_id = request.args.get('user_id')
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
        
        logger.info(f"获取会话列表成功: {len(sessions)} 条记录")
        
        return jsonify({
            "success": True,
            "data": sessions,
            "sessions": sessions,
            "count": len(sessions),
            "limit": limit,
            "offset": offset
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

# 获取会话详情
@api_v1.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话详情"""
    try:
        # 查询会话
        query = "SELECT * FROM sessions WHERE id = ?"
        sessions = execute_query(query, [session_id])
        
        if not sessions:
            return jsonify({
                "success": False,
                "error": f"会话不存在: {session_id}"
            }), 404
        
        session = sessions[0]
        
        # 处理元数据
        if "metadata" in session and session["metadata"]:
            try:
                session["metadata"] = json.loads(session["metadata"])
                if "participants" in session["metadata"]:
                    session["participants"] = session["metadata"]["participants"]
            except:
                pass
        
        # 查询轮次
        query = "SELECT * FROM turns WHERE session_id = ? ORDER BY created_at ASC"
        turns = execute_query(query, [session_id])
        
        # 处理轮次元数据
        for turn in turns:
            if "metadata" in turn and turn["metadata"]:
                try:
                    turn["metadata"] = json.loads(turn["metadata"])
                except:
                    pass
        
        session["turns"] = turns
        
        logger.info(f"获取会话详情成功: {session_id}")
        
        return jsonify({
            "success": True,
            "data": session,
            "session": session
        })
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

# 处理对话
@api_v1.route('/dialogue/process', methods=['POST'])
def process_dialogue():
    """处理对话输入并生成响应"""
    try:
        # 解析请求数据
        data = request.json
        session_id = data.get('session_id')
        user_id = data.get('user_id', data.get('userId'))
        content = data.get('content')
        auto_create_session = data.get('auto_create_session', True)
        
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
        
        # 如果没有提供会话ID且允许自动创建会话
        if not session_id and auto_create_session:
            # 创建新会话
            session_id = f"sess_{uuid.uuid4().hex[:8]}"
            now = datetime.now().isoformat()
            
            # 默认参与者
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
            
            # 会话数据
            session_data = {
                "id": session_id,
                "title": f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "user_id": user_id,
                "dialogue_type": "human_to_ai_private",
                "created_at": now,
                "updated_at": now,
                "last_activity_at": now,
                "metadata": json.dumps({
                    "participants": participants
                })
            }
            
            # 插入会话
            conn = get_connection()
            cursor = conn.cursor()
            
            # 构建SQL
            fields = ", ".join(session_data.keys())
            placeholders = ", ".join(["?" for _ in session_data.keys()])
            values = list(session_data.values())
            
            cursor.execute(f"INSERT INTO sessions ({fields}) VALUES ({placeholders})", values)
            
            logger.info(f"自动创建会话成功: {session_id}")
        elif not session_id:
            return jsonify({
                "success": False,
                "error": "缺少会话ID"
            }), 400
        
        # 创建用户轮次
        user_turn_id = f"turn_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        
        user_turn_data = {
            "id": user_turn_id,
            "session_id": session_id,
            "role": "user",
            "content": content,
            "created_at": now,
            "metadata": json.dumps({
                "user_id": user_id
            })
        }
        
        # 插入用户轮次
        conn = get_connection()
        cursor = conn.cursor()
        
        fields = ", ".join(user_turn_data.keys())
        placeholders = ", ".join(["?" for _ in user_turn_data.keys()])
        values = list(user_turn_data.values())
        
        cursor.execute(f"INSERT INTO turns ({fields}) VALUES ({placeholders})", values)
        
        # 生成AI响应
        ai_response = f"AI 助手响应: {content}"
        
        # 创建AI轮次
        ai_turn_id = f"turn_{uuid.uuid4().hex[:8]}"
        
        ai_turn_data = {
            "id": ai_turn_id,
            "session_id": session_id,
            "role": "assistant",
            "content": ai_response,
            "created_at": now,
            "metadata": json.dumps({
                "model": "gpt-3.5-turbo"
            })
        }
        
        # 插入AI轮次
        fields = ", ".join(ai_turn_data.keys())
        placeholders = ", ".join(["?" for _ in ai_turn_data.keys()])
        values = list(ai_turn_data.values())
        
        cursor.execute(f"INSERT INTO turns ({fields}) VALUES ({placeholders})", values)
        
        # 更新会话最后活动时间
        cursor.execute(
            "UPDATE sessions SET last_activity_at = ? WHERE id = ?",
            (now, session_id)
        )
        
        logger.info(f"处理对话成功: {session_id}")
        
        # 返回响应
        return jsonify({
            "success": True,
            "session_id": session_id,
            "user_turn": {
                **user_turn_data,
                "metadata": json.loads(user_turn_data["metadata"])
            },
            "ai_turn": {
                **ai_turn_data,
                "metadata": json.loads(ai_turn_data["metadata"])
            },
            "response": ai_response
        })
    except Exception as e:
        logger.error(f"处理对话失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

# 获取会话轮次
@api_v1.route('/sessions/<session_id>/turns', methods=['GET'])
def get_turns(session_id):
    """获取会话轮次"""
    try:
        # 查询轮次
        query = "SELECT * FROM turns WHERE session_id = ? ORDER BY created_at ASC"
        turns = execute_query(query, [session_id])
        
        # 处理轮次元数据
        for turn in turns:
            if "metadata" in turn and turn["metadata"]:
                try:
                    turn["metadata"] = json.loads(turn["metadata"])
                except:
                    pass
        
        logger.info(f"获取会话轮次成功: {session_id}, {len(turns)} 条记录")
        
        return jsonify({
            "success": True,
            "data": turns,
            "turns": turns,
            "count": len(turns)
        })
    except Exception as e:
        logger.error(f"获取会话轮次失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

# 创建轮次
@api_v1.route('/sessions/<session_id>/turns', methods=['POST'])
def create_turn(session_id):
    """创建轮次"""
    try:
        # 解析请求数据
        data = request.json
        role = data.get('role')
        content = data.get('content')
        metadata = data.get('metadata', {})
        
        # 验证必要参数
        if not role:
            return jsonify({
                "success": False,
                "error": "缺少角色"
            }), 400
        
        if not content:
            return jsonify({
                "success": False,
                "error": "缺少内容"
            }), 400
        
        # 验证会话是否存在
        query = "SELECT * FROM sessions WHERE id = ?"
        sessions = execute_query(query, [session_id])
        
        if not sessions:
            return jsonify({
                "success": False,
                "error": f"会话不存在: {session_id}"
            }), 404
        
        # 创建轮次
        turn_id = f"turn_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        
        turn_data = {
            "id": turn_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": now,
            "metadata": json.dumps(metadata)
        }
        
        # 插入轮次
        conn = get_connection()
        cursor = conn.cursor()
        
        fields = ", ".join(turn_data.keys())
        placeholders = ", ".join(["?" for _ in turn_data.keys()])
        values = list(turn_data.values())
        
        cursor.execute(f"INSERT INTO turns ({fields}) VALUES ({placeholders})", values)
        
        # 更新会话最后活动时间
        cursor.execute(
            "UPDATE sessions SET last_activity_at = ? WHERE id = ?",
            (now, session_id)
        )
        
        logger.info(f"创建轮次成功: {turn_id}")
        
        # 返回响应
        return jsonify({
            "success": True,
            "data": {
                **turn_data,
                "metadata": metadata
            },
            "turn": {
                **turn_data,
                "metadata": metadata
            }
        }), 201
    except Exception as e:
        logger.error(f"创建轮次失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

def register_api_routes(app):
    """注册API路由
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(api_v1)
    logger.info("API V1路由已注册")
