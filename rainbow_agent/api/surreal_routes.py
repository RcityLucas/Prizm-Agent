"""
SurrealDB API路由

提供使用SurrealDB作为存储后端的API路由，包括会话、轮次和对话管理。
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query, Path, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from ..storage.storage_factory import StorageFactory
from ..storage.config import get_surreal_config
from ..storage.memory import SurrealMemory
from ..storage.async_utils import run_async
from .api_utils import api_error_handler, format_session, format_turn, check_required_params
from ..utils.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/dialogue", tags=["dialogue"])

# 全局存储工厂实例
storage_factory = None
session_manager = None
turn_manager = None

# 初始化存储系统
def init_storage():
    """初始化SurrealDB存储系统"""
    global storage_factory, session_manager, turn_manager
    
    if storage_factory is None:
        # 从环境变量获取SurrealDB配置
        surreal_config = get_surreal_config()
        
        # 创建存储工厂
        storage_factory = StorageFactory(surreal_config)
        
        # 初始化所有存储实例
        run_async(storage_factory.init_all)
        
        # 初始化会话和轮次管理器
        session_manager = storage_factory.get_session_manager()
        turn_manager = storage_factory.get_turn_manager()
        
        logger.info("SurrealDB存储系统初始化完成")
    
    return storage_factory

# 会话管理API
@router.get("/sessions", response_model=Dict[str, Any])
@api_error_handler
def get_dialogue_sessions(
    userId: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """获取对话会话列表，适配增强版前端"""
    # 确保存储系统已初始化
    init_storage()
    
    # 获取会话列表
    sessions = run_async(session_manager.get_sessions, userId, limit, offset)
    
    # 格式化会话数据
    formatted_sessions = [format_session(session) for session in sessions]
    
    # 返回符合增强版前端期望的格式
    logger.info(f"返回会话列表: {len(formatted_sessions)} 个会话")
    return {
        "items": formatted_sessions,
        "total": len(formatted_sessions)
    }

@router.post("/sessions", response_model=Dict[str, Any])
@api_error_handler
def create_dialogue_session(session: Dict[str, Any]):
    """创建新会话，适配增强版前端"""
    # 确保存储系统已初始化
    init_storage()
    
    user_id = session.get('userId', '')
    title = session.get('title', f'新对话 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 创建新会话
    session_data = {
        "user_id": user_id,
        "title": title,
        "timestamp": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat()
    }
    
    # 创建会话
    session = run_async(session_manager.create_session, session_data)
    
    # 格式化会话数据
    formatted_session = format_session(session)
    
    logger.info(f"创建新会话成功: {formatted_session['id']}")
    return formatted_session

@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
@api_error_handler
def get_dialogue_session(session_id: str = Path(...)):
    """获取会话详情，适配增强版前端"""
    # 确保存储系统已初始化
    init_storage()
    
    # 获取会话详情
    session = run_async(session_manager.get_session, session_id)
    
    if not session:
        return JSONResponse(status_code=404, content={"error": "会话不存在"})
    
    # 格式化会话数据
    formatted_session = format_session(session)
    
    logger.info(f"获取会话详情成功: {session_id}")
    return formatted_session

@router.get("/sessions/{session_id}/turns", response_model=Dict[str, Any])
@api_error_handler
def get_dialogue_turns(
    session_id: str = Path(...),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """获取会话轮次，适配增强版前端"""
    # 确保存储系统已初始化
    init_storage()
    
    # 检查会话是否存在
    session = run_async(session_manager.get_session, session_id)
    
    if not session:
        return JSONResponse(status_code=404, content={"error": "会话不存在"})
    
    # 获取会话轮次
    turns = run_async(turn_manager.get_turns, session_id, limit, offset)
    
    # 格式化轮次数据
    formatted_turns = [format_turn(turn) for turn in turns]
    
    logger.info(f"获取会话 {session_id} 的轮次成功，共 {len(formatted_turns)} 条")
    return {
        "items": formatted_turns,
        "total": len(formatted_turns)
    }

@router.post("/input", response_model=Dict[str, Any])
@api_error_handler
def dialogue_input(data: Dict[str, Any]):
    """处理对话输入，适配增强版前端"""
    # 确保存储系统已初始化
    init_storage()
    
    # 检查必要参数
    valid, error_msg = check_required_params(data, ['sessionId', 'input'])
    if not valid:
        return JSONResponse(status_code=400, content={"error": error_msg})
    
    session_id = data['sessionId']
    user_input = data['input']
    
    # 检查会话是否存在
    session = run_async(session_manager.get_session, session_id)
    
    if not session:
        return JSONResponse(status_code=404, content={"error": "会话不存在"})
    
    # 这里应该调用代理处理用户输入
    # 在实际实现中，这部分应该由主服务器处理，这里只是定义API路由
    
    # 创建轮次数据（示例）
    turn_data = {
        "session_id": session_id,
        "user_input": user_input,
        "agent_response": "这是一个示例响应，实际实现应该由代理生成",
        "timestamp": datetime.now().isoformat()
    }
    
    # 保存轮次
    turn_id = run_async(turn_manager.create_turn, turn_data)
    
    # 更新会话的最后活动时间
    run_async(session_manager.update_session, session_id, {
        "last_activity": datetime.now().isoformat()
    })
    
    # 格式化响应
    response_data = {
        "id": turn_id,
        "sessionId": session_id,
        "input": user_input,
        "response": turn_data["agent_response"],
        "timestamp": turn_data["timestamp"]
    }
    
    return response_data

@router.get("/tools", response_model=Dict[str, Any])
@api_error_handler
def get_dialogue_tools():
    """获取可用工具列表，适配增强版前端"""
    # 这里应该返回可用工具列表
    # 在实际实现中，这部分应该由主服务器处理，这里只是定义API路由
    
    tools_data = [
        {
            "name": "weather",
            "description": "查询指定城市的天气信息",
            "parameters": [
                {
                    "name": "city",
                    "type": "string",
                    "description": "城市名称",
                    "required": True
                }
            ]
        },
        {
            "name": "calculator",
            "description": "进行数学计算",
            "parameters": [
                {
                    "name": "expression",
                    "type": "string",
                    "description": "数学表达式",
                    "required": True
                }
            ]
        }
    ]
    
    return tools_data

@router.get("/system/status", response_model=Dict[str, Any])
@api_error_handler
def get_system_status():
    """获取系统状态，适配增强版前端"""
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
    
    return status

# 设置路由
def setup_surreal_routes(app):
    """
    设置SurrealDB API路由
    
    Args:
        app: FastAPI应用实例
    """
    app.include_router(router)
    logger.info("SurrealDB API路由已设置")
