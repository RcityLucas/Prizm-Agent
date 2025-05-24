"""
Rainbow Agent API服务器
统一的API服务器，提供一致的接口行为
"""
import os
import logging
import asyncio
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
import sqlite3
import uuid

from fastapi import FastAPI, HTTPException, Request, Depends, Form, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from rainbow_agent.api.api_routes import router as dialogue_router
from rainbow_agent.core.dialogue_manager import DialogueManager
from rainbow_agent.ai.openai_service import OpenAIService
from rainbow_agent.core.multi_modal_manager import MultiModalToolManager
from rainbow_agent.storage.session_manager import SessionManager
from rainbow_agent.storage.turn_manager import TurnManager

# 配置日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Rainbow Agent API",
    description="Rainbow Agent对话管理系统API",
    version="1.0.0",
    docs_url="/api/docs",  # 修改Swagger文档路径
    redoc_url="/api/redoc",  # 修改ReDoc文档路径
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 全局组件
dialogue_manager = None
multi_modal_manager = None

# 线程本地存储，用于解决SQLite多线程问题
thread_local = threading.local()

def get_connection():
    """获取当前线程的数据库连接"""
    if not hasattr(thread_local, "connection"):
        # 添加超时参数，避免数据库锁定问题
        conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), "db", "rainbow.db"),
            timeout=30.0,
            isolation_level=None,  # 自动提交模式
            check_same_thread=False  # 允许在其他线程中使用
        )
        
        # 启用WAL模式，提高并发性能
        conn.execute("PRAGMA journal_mode=WAL")
        
        thread_local.connection = conn
    return thread_local.connection

def init_system():
    """初始化系统组件"""
    global dialogue_manager, multi_modal_manager
    
    try:
        logger.info("初始化系统组件...")
        
        # 确保数据库目录存在
        os.makedirs(os.path.join(os.path.dirname(__file__), "db"), exist_ok=True)
        
        # 初始化会话管理器（使用线程安全的连接）
        session_manager = SessionManager(get_connection)
        
        # 初始化轮次管理器（使用线程安全的连接）
        turn_manager = TurnManager(get_connection)
        
        # 初始化OpenAI服务
        openai_service = OpenAIService()
        
        # 初始化对话管理器
        dialogue_manager = DialogueManager(
            session_manager=session_manager,
            turn_manager=turn_manager,
            ai_service=openai_service
        )
        
        # 初始化多模态管理器
        multi_modal_manager = MultiModalToolManager()
        
        logger.info("系统组件初始化成功")
        
    except Exception as e:
        logger.error(f"初始化系统组件失败: {e}")
        raise

# 注册对话API路由
app.include_router(dialogue_router)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 根路由
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页"""
    with open("static/enhanced_index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

# 测试API页面
@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """返回测试API页面"""
    with open("static/test_api.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    init_system()
    logger.info("API服务器启动成功")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    # 关闭所有数据库连接
    if hasattr(thread_local, "connection"):
        thread_local.connection.close()
    logger.info("API服务器关闭")

# 主函数
if __name__ == "__main__":
    # 运行FastAPI应用
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
