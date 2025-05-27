#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复的 API 服务器

使用线程安全的数据库连接和修复的 API 路由，解决多线程环境下的数据库锁定问题。
"""
import os
import sys
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
from rainbow_agent.api.fixed_api_routes import register_api_routes
from rainbow_agent.api.chat_routes import register_chat_routes
from rainbow_agent.api.legacy_adapter import register_legacy_api_routes
from rainbow_agent.storage.thread_safe_db import get_connection

# 配置日志
logger = get_logger(__name__)

# 创建Flask应用
app = Flask(__name__, static_folder='static')
CORS(app)  # 启用CORS，允许前端跨域请求

# 创建数据目录
os.makedirs('data', exist_ok=True)

# 初始化数据库
def init_db():
    """初始化数据库"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 创建会话表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        user_id TEXT NOT NULL,
        dialogue_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_activity_at TEXT NOT NULL,
        metadata TEXT
    )
    ''')
    
    # 创建轮次表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS turns (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        metadata TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    ''')
    
    logger.info("数据库初始化完成")

# 设置静态文件访问
@app.route('/<path:path>')
def serve_static(path):
    """提供静态文件访问"""
    return send_from_directory('static', path)

# 首页 - 提供简单的HTML界面
@app.route('/')
def index():
    """服务器首页，提供系统介绍和功能展示"""
    return send_from_directory('static', 'index.html')

@app.route('/standard')
def standard_interface():
    """标准界面，提供原始的标准界面"""
    return send_from_directory('static', 'index.html')

@app.route('/enhanced')
def enhanced_index():
    """增强版界面，提供增强版界面"""
    return send_from_directory('static', 'enhanced_index.html')

@app.route('/demo')
def demo_index():
    """演示页面"""
    return send_from_directory('static', 'demo_index.html')

@app.route('/chat-demo')
def chat_demo():
    """对话演示页面"""
    return send_from_directory('static', 'chat_demo.html')

@app.route('/session-demo')
def session_demo():
    """会话演示页面"""
    return send_from_directory('static', 'session_demo.html')

@app.route('/multimodal-demo')
def multimodal_demo():
    """多模态演示页面"""
    return send_from_directory('static', 'multimodal_demo.html')

@app.route('/tools-demo')
def tools_demo():
    """工具演示页面"""
    return send_from_directory('static', 'tools_demo.html')

@app.route('/chat')
def chat():
    """对话界面，提供简单的对话界面和文档"""
    return send_from_directory('static', 'index.html')

# 创建上传目录
os.makedirs('uploads', exist_ok=True)
logger.info("上传目录创建完成")

# 注册API路由
register_api_routes(app)
# 注册聊天路由
register_chat_routes(app)
# 注册旧版API路由
register_legacy_api_routes(app)

# 主函数
if __name__ == "__main__":
    # 初始化数据库
    init_db()
    
    # 设置端口
    port = int(os.environ.get("PORT", 5000))
    
    # 显示启动信息
    logger.info(f"Rainbow City AI Agent API服务器正在启动，端口: {port}")
    logger.info(f"静态文件目录: {os.path.abspath('static')}")
    logger.info(f"上传文件目录: {os.path.abspath('uploads')}")
    logger.info(f"数据库文件: {os.path.abspath('data/sessions.sqlite')}")
    
    # 启动服务器
    app.run(host="0.0.0.0", port=port, debug=True)
