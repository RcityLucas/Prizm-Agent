#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rainbow City AI Agent API服务器

统一的API服务器，整合了原有的多个服务器实现，提供对话管理和代理交互功能。
支持会话管理、轮次管理、消息处理和多模态支持。
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
from flask_socketio import SocketIO, emit

from rainbow_agent.utils.logger import get_logger
from rainbow_agent.api.dialogue_processor import SessionManager, DialogueProcessor
from rainbow_agent.api.unified_routes import register_api_routes
from rainbow_agent.core.dialogue_manager import DialogueManager
from rainbow_agent.core.dialogue_manager_with_context import EnhancedDialogueManager
from rainbow_agent.core.multi_modal_manager import MultiModalToolManager
from rainbow_agent.memory.memory import Memory
from rainbow_agent.memory.surreal_memory import SurrealMemory
from rainbow_agent.frequency.frequency_integrator import FrequencyIntegrator

# 配置日志
logger = get_logger(__name__)

# 创建Flask应用
app = Flask(__name__, static_folder='static')
CORS(app)  # 启用CORS，允许前端跨域请求

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 全局变量
session_manager = None
dialogue_manager = None
dialogue_processor = None
multi_modal_manager = None

# 初始化标志
_initialized = False

def init_components():
    """初始化系统组件"""
    global session_manager, dialogue_manager, dialogue_processor, multi_modal_manager, _initialized
    
    if not _initialized:
        logger.info("初始化系统组件...")
        
        try:
            # 首先初始化会话管理器
            session_manager = SessionManager()
            logger.info("会话管理器初始化完成")
            
            # 初始化记忆系统
            try:
                # 首先尝试使用SurrealMemory适配器，它会处理SurrealDB连接失败的情况
                logger.info("尝试使用SurrealMemory适配器，使用WebSocket连接...")
                # 指定WebSocket URL连接到SurrealDB
                memory = SurrealMemory(db_url="ws://localhost:8000/rpc")
                logger.info("SurrealDB记忆系统初始化成功（带备用支持）")
            except ImportError as ie:
                # 如果找不到SurrealMemory适配器，尝试直接使用存储模块中的SurrealMemory
                logger.warning(f"找不到SurrealMemory适配器: {ie}")
                try:
                    logger.info("尝试从存储模块初始化SurrealMemory...")
                    from rainbow_agent.storage.memory import SurrealMemory as StorageSurrealMemory
                    from rainbow_agent.storage.surreal_factory import SurrealStorageFactory
                    # 创建存储工厂，使用WebSocket连接
                    factory = SurrealStorageFactory(db_url="ws://localhost:8000/rpc")
                    memory = StorageSurrealMemory(factory)
                    logger.info("从存储模块初始化SurrealDB记忆系统成功")
                except Exception as e:
                    logger.warning(f"初始化SurrealDB记忆系统失败: {e}")
                    from rainbow_agent.memory.memory import SimpleMemory
                    memory = SimpleMemory()
                    logger.info("已降级到SimpleMemory作为备用")
            except Exception as e:
                logger.warning(f"初始化记忆系统时发生意外错误: {e}")
                import traceback
                logger.warning(traceback.format_exc())
                from rainbow_agent.memory.memory import SimpleMemory
                memory = SimpleMemory()
                logger.info("由于意外错误，已降级到SimpleMemory作为备用")

            # 初始化频率感知组件
            try:
                # 初始化频率感知集成器，提供必要的memory和output_callback参数
                async def output_callback(content, metadata):
                    """处理频率感知系统的输出回调"""
                    try:
                        user_id = metadata.get('user_id', 'unknown')
                        session_id = metadata.get('session_id')
                        expression_type = metadata.get('expression_type', 'general')
                        
                        # 构建表达数据
                        expression_data = {
                            'content': content,
                            'type': expression_type,
                            'timestamp': datetime.now().isoformat(),
                            'metadata': metadata
                        }
                        
                        # 发送表达
                        return send_proactive_expression(user_id, expression_data)
                    except Exception as e:
                        logger.error(f"处理频率感知输出失败: {e}")
                        return False
                
                # 创建频率感知集成器实例，传入必要参数
                frequency_integrator = FrequencyIntegrator(
                    memory=memory,
                    output_callback=output_callback
                )
                logger.info("频率感知系统初始化成功")
                
                # 设置配置标志
                app.config['FREQUENCY_AWARE'] = True
            except Exception as e:
                logger.warning(f"频率感知系统初始化失败: {e}，将禁用频率感知功能")
                import traceback
                logger.warning(traceback.format_exc())
                app.config['FREQUENCY_AWARE'] = False

            # 初始化对话管理器 - 使用支持上下文的增强版对话管理器
            try:
                # 首先尝试使用增强版对话管理器
                dialogue_manager = EnhancedDialogueManager(memory=memory, frequency_integrator=frequency_integrator)
                logger.info("增强版对话管理器（支持上下文）初始化成功")
            except Exception as e:
                logger.warning(f"增强版对话管理器初始化失败: {e}，将使用基础版对话管理器")
                dialogue_manager = DialogueManager(memory=memory, frequency_integrator=frequency_integrator)
                logger.info("基础版对话管理器初始化完成")
            
            # 初始化多模态管理器
            multi_modal_manager = MultiModalToolManager()
            logger.info("多模态管理器初始化完成")
            
            # 初始化对话处理器
            dialogue_processor = DialogueProcessor(
                session_manager=session_manager,
                dialogue_manager=dialogue_manager,
                multi_modal_manager=multi_modal_manager
            )
            logger.info("对话处理器初始化完成")
            
            # 将组件存储在app.config中，以便在其他地方使用
            app.config['DIALOGUE_MANAGER'] = dialogue_manager
            app.config['MEMORY'] = memory
            app.config['FREQUENCY_INTEGRATOR'] = frequency_integrator
            # 从frequency_integrator获取expression_planner
            app.config['EXPRESSION_PLANNER'] = frequency_integrator.expression_planner if hasattr(frequency_integrator, 'expression_planner') else None
            app.config['FREQUENCY_AWARE'] = True
            
            # 检查频率感知系统是否初始化成功
            frequency_system_status = "已启用" if hasattr(dialogue_manager, 'frequency_integrator') and dialogue_manager.frequency_integrator else "未启用"
            logger.info(f"频率感知系统状态: {frequency_system_status}")
            
            # 如果频率感知系统启用，设置定时任务检查主动表达
            if hasattr(dialogue_manager, 'frequency_integrator') and dialogue_manager.frequency_integrator:
                # 创建定时任务线程
                import threading
                import time
                
                def check_proactive_expressions():
                    """定期检查并发送主动表达"""
                    while True:
                        try:
                            # 获取所有已注册的用户
                            for user_id in user_socket_map.keys():
                                # 获取用户的主动表达
                                expressions = dialogue_manager.frequency_integrator.get_pending_expressions(user_id)
                                
                                # 发送主动表达
                                for expression in expressions:
                                    send_proactive_expression(user_id, expression)
                        except Exception as e:
                            logger.error(f"检查主动表达失败: {e}")
                        
                        # 等待一段时间
                        time.sleep(30)  # 每30秒检查一次
                
                # 启动定时任务线程
                proactive_thread = threading.Thread(target=check_proactive_expressions)
                proactive_thread.daemon = True
                proactive_thread.start()
                logger.info("主动表达检查线程已启动")
            
            # 启动主动表达检查线程
            import threading
            import time
            
            def check_proactive_expressions():
                """定期检查并发送主动表达"""
                logger.info("开始定期检查主动表达...")
                while True:
                    try:
                        # 获取所有需要发送主动表达的用户
                        expression_planner = app.config.get('EXPRESSION_PLANNER')
                        if expression_planner:
                            # 检查每个用户是否有待发送的主动表达
                            for user_id in user_socket_map.keys():
                                expressions = expression_planner.get_pending_expressions(user_id)
                                if expressions:
                                    logger.info(f"用户 {user_id} 有 {len(expressions)} 个待发送的主动表达")
                                    # 发送主动表达
                                    for expression in expressions:
                                        send_proactive_expression(user_id, expression)
                    except Exception as e:
                        logger.error(f"检查主动表达失败: {e}")
                    
                    # 等待一段时间
                    time.sleep(30)  # 每30秒检查一次
            
            # 启动定时任务线程
            if app.config.get('FREQUENCY_AWARE', False):
                proactive_thread = threading.Thread(target=check_proactive_expressions)
                proactive_thread.daemon = True
                proactive_thread.start()
                logger.info("主动表达检查线程已启动")
            
            logger.info("系统组件初始化完成")
            _initialized = True
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"系统组件初始化失败: {e}\n{error_traceback}")
            # 不设置_initialized为True，这样下一次请求会重新尝试初始化
    
    return _initialized

# 全局异常处理
@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理器"""
    logger.error(f"服务器错误: {e}")
    return jsonify({"error": str(e), "success": False}), 500

# 设置静态文件访问
@app.route('/<path:path>')
def serve_static(path):
    """提供静态文件访问"""
    return send_from_directory('static', path)

# 首页 - 提供简单的HTML界面
@app.route('/')
def home():
    """服务器首页，提供系统介绍和功能展示"""
    return send_from_directory('static', 'index.html')

@app.route('/standard')
def standard_interface():
    """标准界面，提供原始的标准界面"""
    return send_from_directory('static', 'index.html')

@app.route('/enhanced')
def enhanced_interface():
    """增强版界面，提供增强版界面"""
    return send_from_directory('static', 'enhanced_index.html')

@app.route('/chat')
def chat():
    """对话界面，提供简单的对话界面和文档"""
    return send_from_directory('static', 'index.html')

# 在应用启动时初始化系统组件
@app.before_request
def before_request():
    """在每个请求前执行，确保系统组件已初始化"""
    init_components()

# 注册API路由
register_api_routes(app)

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    """处理客户端连接事件"""
    logger.info(f"客户端已连接: {request.sid}")
    emit('connected', {'status': 'connected', 'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接事件"""
    logger.info(f"客户端已断开连接: {request.sid}")

@socketio.on('register_user')
def handle_register_user(data):
    """注册用户，将用户ID与SocketIO会话关联"""
    user_id = data.get('userId')
    if user_id:
        # 存储用户ID与SocketIO会话ID的映射关系
        user_socket_map[user_id] = request.sid
        logger.info(f"用户注册: {user_id} -> {request.sid}")
        emit('registered', {'status': 'success', 'userId': user_id})
    else:
        emit('registered', {'status': 'error', 'message': '缺少userId参数'})

# 用于存储用户ID与SocketIO会话ID的映射关系
user_socket_map = {}

# 发送主动表达的函数
def send_proactive_expression(user_id, expression):
    """向特定用户发送主动表达"""
    if user_id in user_socket_map:
        sid = user_socket_map[user_id]
        socketio.emit('proactive_expression', expression, room=sid)
        logger.info(f"已向用户 {user_id} 发送主动表达: {expression['type']}")
        return True
    else:
        logger.warning(f"用户 {user_id} 未连接，无法发送主动表达")
        return False

# 主函数
if __name__ == "__main__":
    # 设置端口
    port = int(os.environ.get("PORT", 5000))
    
    # 启动SocketIO服务器
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
