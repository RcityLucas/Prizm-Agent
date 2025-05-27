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

from rainbow_agent.utils.logger import get_logger
from rainbow_agent.api.dialogue_processor import SessionManager, DialogueProcessor
from rainbow_agent.api.unified_routes import register_api_routes
from rainbow_agent.core.dialogue_manager import DialogueManager
from rainbow_agent.core.multi_modal_manager import MultiModalToolManager

# 配置日志
logger = get_logger(__name__)

# 创建Flask应用
app = Flask(__name__, static_folder='static')
CORS(app)  # 启用CORS，允许前端跨域请求

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
            # 初始化会话管理器
            session_manager = SessionManager()
            logger.info("会话管理器初始化完成")
            
            # 初始化对话管理器
            dialogue_manager = DialogueManager()
            logger.info("对话管理器初始化完成")
            
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

# 主函数
if __name__ == "__main__":
    # 设置端口
    port = int(os.environ.get("PORT", 5000))
    
    # 启动服务器
    app.run(host="0.0.0.0", port=port, debug=True)
