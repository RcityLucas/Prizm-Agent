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

# 配置日志
logger = get_logger(__name__)

# 创建Flask应用
app = Flask(__name__, static_folder='static')
CORS(app)  # 启用CORS，允许前端跨域请求

# 全局变量
session_manager = None
turn_manager = None
openai_service = None

# 初始化SurrealDB存储系统
def init_storage():
    """初始化SurrealDB存储系统"""
    global session_manager, turn_manager
    
    try:
        if session_manager is None or turn_manager is None:
            logger.info("开始初始化SurrealDB存储系统...")
            
            # 直接创建会话和轮次管理器实例
            from rainbow_agent.storage.session_manager import SessionManager
            from rainbow_agent.storage.turn_manager import TurnManager
            
            session_manager = SessionManager()
            turn_manager = TurnManager()
            
            # 确保异步连接到SurrealDB
            # 这里不再需要调用storage_factory.init_all
            # 因为SessionManager和TurnManager会在需要时自动连接
            
            logger.info("SurrealDB存储系统初始化完成")
        else:
            logger.info("SurrealDB存储系统已初始化")
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"SurrealDB存储系统初始化失败: {e}\n{error_traceback}")
        raise

# 初始化对话系统
def init_dialogue_system():
    """初始化对话系统"""
    global session_manager, turn_manager, openai_service
    
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
    return send_from_directory('static', 'index.html')

@app.route('/chat')
def chat():
    """对话界面，提供简单的对话界面和文档"""
    return send_from_directory('static/templates', 'index.html')


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
        sessions = run_async(session_manager.get_sessions, user_id, limit, offset)
        logger.info(f"成功获取会话列表，共 {len(sessions)} 个会话")
        
        # 格式化会话数据
        formatted_sessions = []
        for session in sessions:
            logger.info(f"格式化会话数据: {session}")
            formatted_sessions.append({
                "id": session.get("id"),
                "title": session.get("title", "未命名会话"),
                "userId": session.get("user_id", ""),
                "created": session.get("timestamp", ""),
                "lastActivity": session.get("last_activity", "")
            })
        
        # 返回符合增强版前端期望的格式
        logger.info(f"返回会话列表: {len(formatted_sessions)} 个会话")
        return jsonify({
            "items": formatted_sessions,
            "total": len(formatted_sessions)
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
        logger.info("开始创建新会话")
        # 确保对话系统已初始化
        init_dialogue_system()
        
        # 获取请求数据
        try:
            if request.is_json:
                data = request.get_json()
                logger.info(f"成功解析JSON数据: {data}")
            else:
                # 如果请求不是JSON格式，尝试从表单数据中获取
                data = request.form.to_dict()
                if not data:
                    # 如果表单数据也为空，尝试从请求体中解析JSON
                    try:
                        data = json.loads(request.data.decode('utf-8'))
                        logger.info(f"从请求体解析JSON数据: {data}")
                    except json.JSONDecodeError as json_err:
                        logger.error(f"JSON解析错误: {json_err}, 请求体: {request.data}")
                        data = {}
                else:
                    logger.info(f"从表单获取数据: {data}")
        except Exception as parse_error:
            logger.error(f"解析请求数据失败: {parse_error}")
            data = {}
        
        logger.info(f"最终解析的数据: {data}")
        
        # 如果数据为空，使用默认值
        if not data:
            logger.warning("数据为空，使用默认值")
            data = {}
        
        user_id = data.get('userId', 'test_user')
        title = data.get('title', f'新对话 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        logger.info(f"准备创建新会话: user_id={user_id}, title={title}")
        
        # 直接调用session_manager.create_session方法
        session = run_async(session_manager.create_session, user_id, title)
        
        # 格式化会话数据
        formatted_session = {
            "id": session.get("id"),
            "title": session.get("title", "未命名会话"),
            "userId": session.get("user_id", ""),
            "created": session.get("timestamp", ""),
            "lastActivity": session.get("last_activity", "")
        }
        
        logger.info(f"创建新会话成功: {formatted_session}")
        return jsonify(formatted_session), 201
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
        
        # 获取请求数据
        try:
            if request.is_json:
                data = request.get_json()
                logger.info(f"成功解析JSON数据: {data}")
            else:
                # 如果请求不是JSON格式，尝试从表单数据中获取
                data = request.form.to_dict()
                if not data:
                    # 如果表单数据也为空，尝试从请求体中解析JSON
                    try:
                        data = json.loads(request.data.decode('utf-8'))
                        logger.info(f"从请求体解析JSON数据: {data}")
                    except json.JSONDecodeError as json_err:
                        logger.error(f"JSON解析错误: {json_err}, 请求体: {request.data}")
                        data = {}
                else:
                    logger.info(f"从表单获取数据: {data}")
        except Exception as parse_error:
            logger.error(f"解析请求数据失败: {parse_error}")
            data = {}
        
        logger.info(f"最终解析的数据: {data}")
        
        # 如果数据为空，返回错误
        if not data:
            logger.error("数据为空，无法处理用户输入")
            return jsonify({
                "error": "无法解析请求数据，请确保发送正确的JSON格式"
            }), 400
        
        # 获取会话ID和用户输入
        session_id = data.get('sessionId')
        user_input = data.get('input')
        
        if not session_id or not user_input:
            logger.error(f"缺少必要的参数: sessionId={session_id}, input={user_input}")
            return jsonify({
                "error": "缺少必要的参数: sessionId 和 input"
            }), 400
        
        logger.info(f"处理用户输入: session_id={session_id}, input={user_input}")
        
        # 获取历史对话轮次
        try:
            # 获取最近的对话轮次（最多10轮）
            logger.info(f"获取会话 {session_id} 的历史对话轮次")
            turns = run_async(turn_manager.get_turns, session_id, limit=10)
            logger.info(f"获取到 {len(turns)} 轮对话历史")
        except Exception as history_error:
            logger.error(f"获取对话历史失败: {history_error}")
            turns = []
        
        # 添加当前用户输入到对话历史
        current_turn = {"role": "human", "content": user_input}
        all_turns = turns + [current_turn]
        
        # 格式化对话历史为OpenAI API所需的格式
        messages = openai_service.format_dialogue_history(all_turns)
        
        # 调用OpenAI API生成回复
        try:
            logger.info("调用OpenAI API生成回复")
            # 直接同步调用generate_response方法，因为它现在是同步的
            response = openai_service.generate_response(messages)
            logger.info(f"成功生成回复，长度: {len(response)}")
        except Exception as ai_error:
            logger.error(f"生成回复失败: {ai_error}")
            response = f"抱歉，生成回复时出现错误: {str(ai_error)}"
        
        try:
            # 创建用户轮次
            logger.info("创建用户轮次")
            user_turn = run_async(
                turn_manager.create_turn,
                session_id=session_id,
                role="human",
                content=user_input
            )
            logger.info(f"用户轮次创建成功: {user_turn}")
            
            # 创建AI轮次
            logger.info("创建AI轮次")
            ai_turn = run_async(
                turn_manager.create_turn,
                session_id=session_id,
                role="ai",
                content=response
            )
            logger.info(f"AI轮次创建成功: {ai_turn}")
            
            # 格式化轮次数据
            formatted_turn = {
                "id": ai_turn.get("id"),
                "sessionId": ai_turn.get("session_id"),
                "input": user_input,
                "response": ai_turn.get("content", ""),
                "timestamp": ai_turn.get("created_at", ""),
                "model": "gpt-3.5-turbo"  # 添加模型信息
            }
            
            logger.info(f"处理用户输入成功: {session_id}")
            return jsonify(formatted_turn)
        except Exception as turn_error:
            logger.error(f"创建轮次失败: {turn_error}")
            import traceback
            turn_error_traceback = traceback.format_exc()
            logger.error(f"轮次错误详情: {turn_error_traceback}")
            return jsonify({
                "error": f"创建轮次失败: {str(turn_error)}",
                "traceback": turn_error_traceback
            }), 500
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"处理用户输入失败: {e}\n{error_traceback}")
        return jsonify({
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
        
        # 获取会话轮次
        logger.info(f"从轮次管理器获取会话 {session_id} 的轮次")
        turns = run_async(turn_manager.get_turns, session_id)
        logger.info(f"成功获取会话 {session_id} 的轮次，共 {len(turns)} 个轮次")
        
        # 按照创建时间排序
        turns.sort(key=lambda x: x.get("created_at", ""))
        
        # 将轮次按照人机对话格式进行分组和格式化
        formatted_turns = []
        i = 0
        while i < len(turns):
            # 获取当前轮次
            current_turn = turns[i]
            
            # 如果是人类轮次，尝试查找对应的AI轮次
            if current_turn.get("role") == "human":
                user_content = current_turn.get("content", "")
                ai_content = ""
                timestamp = current_turn.get("created_at", "")
                
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
                    "timestamp": timestamp
                })
            else:
                # 如果是AI轮次但没有对应的人类轮次，则单独添加
                i += 1
        
        logger.info(f"返回会话 {session_id} 的格式化轮次: {len(formatted_turns)} 个轮次")
        return jsonify({
            "items": formatted_turns,
            "total": len(formatted_turns)
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"获取会话轮次失败: {e}\n{error_traceback}")
        return jsonify({
            "error": str(e),
            "traceback": error_traceback
        }), 500

# 在应用启动时初始化存储系统
# 注意：在新版Flask中，before_first_request已被弃用
# 我们使用普通的路由处理函数来初始化

# 初始化标志，确保只初始化一次
_initialized = False

@app.before_request
def before_request():
    """在每个请求前执行，确保存储系统已初始化"""
    global _initialized, storage_factory, session_manager, turn_manager
    
    # 每次请求都确保存储系统已初始化
    if not _initialized:
        logger.info("API服务器初始化中...")
        
        try:
            # 初始化存储系统
            storage_factory = init_storage_factory()
            
            # 初始化会话和轮次管理器
            session_manager = storage_factory.get_session_manager()
            turn_manager = storage_factory.get_turn_manager()
            
            # 异步连接到SurrealDB
            run_async(storage_factory.init_all)
            
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
