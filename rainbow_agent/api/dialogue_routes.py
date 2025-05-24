"""
对话管理系统API路由

提供彩虹城 AI Agent 对话管理系统的API接口，包括会话、轮次和消息的管理。
支持七种对话类型和四层数据结构（消息、轮次、会话、对话）。
"""
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query, Path, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uuid
import os
import json
from datetime import datetime

from ..core.dialogue_core import DialogueCore
from ..core.input_hub import InputHub
from ..memory.memory import Memory
from ..tools.tool_invoker import ToolInvoker
from ..core.llm_caller import LLMCaller
from ..core.database import Database, DIALOGUE_TYPES, MESSAGE_TYPES
from ..utils.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/dialogue", tags=["dialogue"])

# 全局对话管理系统组件
dialogue_core = None
input_hub = None
memory = None
tool_invoker = None
llm_caller = None
db = None

# 数据模型
class MessageBase(BaseModel):
    content: str
    type: str = "text"
    sender_id: str
    sender_type: str
    metadata: Dict[str, Any] = {}

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    turn_id: str
    timestamp: datetime

    class Config:
        orm_mode = True

class ToolCallBase(BaseModel):
    tool_name: str
    tool_args: Dict[str, Any]
    status: str = "pending"

class ToolCallCreate(ToolCallBase):
    pass

class ToolCall(ToolCallBase):
    id: str
    turn_id: str
    tool_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class TurnBase(BaseModel):
    initiator_id: str
    initiator_type: str
    responder_id: str
    responder_type: str
    status: str = "pending"
    metadata: Dict[str, Any] = {}

class TurnCreate(TurnBase):
    request_messages: List[MessageCreate]

class Turn(TurnBase):
    id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    request_messages: List[Message] = []
    response_messages: List[Message] = []
    tool_calls: List[ToolCall] = []

    class Config:
        orm_mode = True

class ParticipantBase(BaseModel):
    id: str
    name: str
    type: str  # human, ai, system
    metadata: Dict[str, Any] = {}

class SessionBase(BaseModel):
    name: str
    dialogue_type: str = DIALOGUE_TYPES["HUMAN_TO_AI_PRIVATE"]
    participants: List[ParticipantBase]
    metadata: Dict[str, Any] = {}

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime

    class Config:
        orm_mode = True

class DialogueBase(BaseModel):
    title: str
    description: Optional[str] = ""
    status: str = "active"
    metadata: Dict[str, Any] = {}

class DialogueCreate(DialogueBase):
    pass

class DialogueSession(BaseModel):
    session_id: str
    sequence_number: int

class Dialogue(DialogueBase):
    id: str
    created_at: datetime
    updated_at: datetime
    sessions: List[Session] = []

    class Config:
        orm_mode = True

class InputRequest(BaseModel):
    content: Optional[str] = None
    processed_input: Optional[str] = None
    type: str = "text"
    session_id: Optional[str] = None
    user_id: str
    metadata: Dict[str, Any] = {}

class InputResponse(BaseModel):
    final_response: str
    session_id: str
    turn_id: str
    tool_results: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

# 初始化对话管理系统组件
def init_dialogue_system():
    global dialogue_core, input_hub, memory, tool_invoker, llm_caller, db
    
    if dialogue_core is None:
        # 初始化组件
        memory = Memory()
        tool_invoker = ToolInvoker()
        llm_caller = LLMCaller()
        input_hub = InputHub()
        dialogue_core = DialogueCore(memory, tool_invoker, llm_caller)
        
        # 初始化数据库
        db_path = os.path.join("data", "dialogue.sqlite")
        db = Database(db_path)
        
        logger.info("对话管理系统组件已初始化")

# 处理用户输入
@router.post("/input", response_model=InputResponse)
async def process_input(request: InputRequest):
    """
    处理用户输入，生成AI响应
    根据四层架构实现，自动创建或更新会话、轮次和消息
    """
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 使用processed_input或content作为用户输入
        user_input = request.processed_input or request.content
        
        if not user_input:
            raise HTTPException(status_code=400, detail="缺少必要参数: content或processed_input")
            
        logger.info(f"接收到用户输入: {user_input[:50]}...")
        
        # 获取或创建会话
        session_id = request.session_id
        if not session_id:
            # 创建新会话
            session_id = str(uuid.uuid4())
            session_data = {
                "id": session_id,
                "name": f"与{request.user_id}的对话",
                "dialogue_type": DIALOGUE_TYPES["HUMAN_TO_AI_PRIVATE"],
                "participants": [
                    {
                        "id": request.user_id,
                        "name": "User",
                        "type": "human",
                        "metadata": {}
                    },
                    {
                        "id": "ai",
                        "name": "AI Assistant",
                        "type": "ai",
                        "metadata": {}
                    }
                ],
                "metadata": request.metadata
            }
            db.create_session(session_data)
            logger.info(f"创建新会话: {session_id}")
        else:
            # 更新现有会话的最后活动时间
            db.update_session(session_id, {"last_activity_at": datetime.now().isoformat()})
        
        # 创建新轮次
        turn_id = str(uuid.uuid4())
        turn_data = {
            "id": turn_id,
            "session_id": session_id,
            "initiator_id": request.user_id,
            "initiator_type": "human",
            "responder_id": "ai",
            "responder_type": "ai",
            "status": "pending",
            "metadata": request.metadata,
            "start_time": datetime.now().isoformat()
        }
        db.create_turn(turn_data)
        
        # 创建用户请求消息
        message_id = str(uuid.uuid4())
        message_data = {
            "id": message_id,
            "turn_id": turn_id,
            "content": user_input,
            "type": request.type,
            "sender_id": request.user_id,
            "sender_type": "human",
            "metadata": request.metadata,
            "timestamp": datetime.now().isoformat()
        }
        db.create_message(message_data)
        
        # 使用InputHub处理输入
        input_data = input_hub.process_input(
            user_input=user_input,
            metadata={
                "type": request.type,
                "session_id": session_id,
                "turn_id": turn_id,
                "user_id": request.user_id,
                **request.metadata
            }
        )
        
        # 使用DialogueCore处理对话
        response_data = dialogue_core.process(input_data)
        
        # 记录工具调用（如果有）
        for tool_result in response_data["tool_results"]:
            tool_call_id = str(uuid.uuid4())
            tool_call_data = {
                "id": tool_call_id,
                "turn_id": turn_id,
                "tool_name": tool_result["tool_name"],
                "tool_args": tool_result["tool_args"],
                "tool_result": tool_result["result"],
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            }
            db.create_tool_call(tool_call_data)
        
        # 创建 AI 响应消息
        response_message_id = str(uuid.uuid4())
        response_message_data = {
            "id": response_message_id,
            "turn_id": turn_id,
            "content": response_data["final_response"],
            "type": "text",
            "sender_id": "ai",
            "sender_type": "ai",
            "metadata": response_data["metadata"],
            "timestamp": datetime.now().isoformat()
        }
        db.create_message(response_message_data)
        
        # 更新轮次状态为已完成
        db.update_turn(turn_id, {
            "status": "completed",
            "end_time": datetime.now().isoformat()
        })
        
        # 构建响应
        return InputResponse(
            final_response=response_data["final_response"],
            session_id=session_id,
            turn_id=turn_id,
            tool_results=response_data["tool_results"],
            metadata={
                "processing_time": response_data["metadata"]["processing_time"],
                "token_usage": response_data["metadata"]["token_usage"]
            }
        )
        
    except Exception as e:
        logger.error(f"处理用户输入时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 会话管理API
@router.get("/sessions", response_model=Dict[str, Any])
async def get_sessions(
    userId: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    获取会话列表
    """
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 从数据库获取会话列表
        sessions = db.get_sessions(userId, limit, offset)
        total = len(sessions)
        
        logger.info(f"获取会话列表: 用户={userId}, 总数={total}")
        return {
            "sessions": sessions,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"获取会话列表时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions", response_model=Session)
async def create_session(session: SessionCreate):
    """
    创建新会话
    """
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 准备会话数据
        session_id = str(uuid.uuid4())
        session_data = {
            "id": session_id,
            "name": session.name,
            "dialogue_type": session.dialogue_type,
            "participants": [
                {
                    "id": p.id,
                    "name": p.name,
                    "type": p.type,
                    "metadata": p.metadata
                } for p in session.participants
            ],
            "metadata": session.metadata
        }
        
        # 保存到数据库
        new_session = db.create_session(session_data)
        
        logger.info(f"创建新会话: {session_id}")
        return Session(
            id=new_session["id"],
            name=new_session["name"],
            dialogue_type=new_session["dialogue_type"],
            participants=[ParticipantBase(**p) for p in new_session["participants"]],
            metadata=new_session["metadata"],
            created_at=datetime.fromisoformat(new_session["created_at"]),
            updated_at=datetime.fromisoformat(new_session["updated_at"]),
            last_activity_at=datetime.fromisoformat(new_session["last_activity_at"])
        )
        
    except Exception as e:
        logger.error(f"创建会话时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}", response_model=Session)
async def get_session(session_id: str = Path(...)):
    """
    获取特定会话详情
    """
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 从数据库获取会话
        session = db.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        
        logger.info(f"获取会话详情: {session_id}")
        return Session(
            id=session["id"],
            name=session["name"],
            dialogue_type=session["dialogue_type"],
            participants=[ParticipantBase(**p) for p in session["participants"]],
            metadata=session["metadata"],
            created_at=datetime.fromisoformat(session["created_at"]),
            updated_at=datetime.fromisoformat(session["updated_at"]),
            last_activity_at=datetime.fromisoformat(session["last_activity_at"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话详情时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}", response_model=Session)
async def update_session(
    session_update: Dict[str, Any],
    session_id: str = Path(...)
):
    """
    更新特定会话
    """
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 更新数据库中的会话
        updated_session = db.update_session(session_id, session_update)
        
        if not updated_session:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        
        logger.info(f"更新会话: {session_id}")
        return Session(
            id=updated_session["id"],
            name=updated_session["name"],
            dialogue_type=updated_session["dialogue_type"],
            participants=[ParticipantBase(**p) for p in updated_session["participants"]],
            metadata=updated_session["metadata"],
            created_at=datetime.fromisoformat(updated_session["created_at"]),
            updated_at=datetime.fromisoformat(updated_session["updated_at"]),
            last_activity_at=datetime.fromisoformat(updated_session["last_activity_at"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新会话时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}", response_model=Dict[str, Any])
async def delete_session(session_id: str = Path(...)):
    """
    删除特定会话
    """
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 从数据库删除会话
        success = db.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        
        logger.info(f"删除会话: {session_id}")
        return {"success": True, "message": f"会话 {session_id} 已删除"}

# 轮次管理API
@router.get("/sessions/{session_id}/turns", response_model=Dict[str, Any])
async def get_turns(
    session_id: str = Path(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    获取会话中的轮次列表
    """
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 检查会话是否存在
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        
        # 从数据库获取轮次列表
        turns = db.get_turns(session_id, limit, offset)
        total = len(turns)
        
        logger.info(f"获取会话 {session_id} 中的轮次列表: 总数={total}")
        return {
            "turns": turns,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取轮次列表时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/turns", response_model=Turn)
async def create_turn(
    turn: TurnCreate,
    session_id: str = Path(...)
):
    """
    在会话中创建新轮次
    """
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 检查会话是否存在
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        
        # 准备轮次数据
        turn_id = str(uuid.uuid4())
        turn_data = {
            "id": turn_id,
            "session_id": session_id,
            "initiator_id": turn.initiator_id,
            "initiator_type": turn.initiator_type,
            "responder_id": turn.responder_id,
            "responder_type": turn.responder_type,
            "status": turn.status,
            "metadata": turn.metadata,
            "start_time": datetime.now().isoformat()
        }
        
        # 创建轮次
        db.create_turn(turn_data)
        
        # 创建请求消息
        for msg in turn.request_messages:
            message_id = str(uuid.uuid4())
            message_data = {
                "id": message_id,
                "turn_id": turn_id,
                "content": msg.content,
                "type": msg.type,
                "sender_id": msg.sender_id,
                "sender_type": msg.sender_type,
                "metadata": msg.metadata,
                "timestamp": datetime.now().isoformat()
            }
            db.create_message(message_data)
        
        # 获取创建后的完整轮次数据
        new_turn = db.get_turn(turn_id)
        
        logger.info(f"在会话 {session_id} 中创建新轮次: {turn_id}")
        
        # 转换为 Pydantic 模型
        result = Turn(
            id=new_turn["id"],
            session_id=new_turn["session_id"],
            initiator_id=new_turn["initiator_id"],
            initiator_type=new_turn["initiator_type"],
            responder_id=new_turn["responder_id"],
            responder_type=new_turn["responder_type"],
            status=new_turn["status"],
            metadata=new_turn["metadata"],
            start_time=datetime.fromisoformat(new_turn["start_time"]),
            end_time=datetime.fromisoformat(new_turn["end_time"]) if new_turn["end_time"] else None,
            request_messages=[
                Message(
                    id=msg["id"],
                    turn_id=msg["turn_id"],
                    content=msg["content"],
                    type=msg["type"],
                    sender_id=msg["sender_id"],
                    sender_type=msg["sender_type"],
                    metadata=msg["metadata"],
                    timestamp=datetime.fromisoformat(msg["timestamp"])
                )
                for msg in new_turn["request_messages"]
            ],
            response_messages=[
                Message(
                    id=msg["id"],
                    turn_id=msg["turn_id"],
                    content=msg["content"],
                    type=msg["type"],
                    sender_id=msg["sender_id"],
                    sender_type=msg["sender_type"],
                    metadata=msg["metadata"],
                    timestamp=datetime.fromisoformat(msg["timestamp"])
                )
                for msg in new_turn["response_messages"]
            ],
            tool_calls=[
                ToolCall(
                    id=tool["id"],
                    turn_id=tool["turn_id"],
                    tool_name=tool["tool_name"],
                    tool_args=tool["tool_args"],
                    tool_result=tool["tool_result"],
                    status=tool["status"],
                    created_at=datetime.fromisoformat(tool["created_at"]),
                    completed_at=datetime.fromisoformat(tool["completed_at"]) if tool["completed_at"] else None
                )
                for tool in new_turn.get("tool_calls", [])
            ]
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建轮次时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/turns/{turn_id}", response_model=Turn)
async def get_turn(turn_id: str = Path(...)):
    """
    获取特定轮次详情
    """
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 从数据库获取轮次
        turn = db.get_turn(turn_id)
        
        if not turn:
            raise HTTPException(status_code=404, detail=f"轮次不存在: {turn_id}")
        
        logger.info(f"获取轮次详情: {turn_id}")
        
        # 转换为 Pydantic 模型
        result = Turn(
            id=turn["id"],
            session_id=turn["session_id"],
            initiator_id=turn["initiator_id"],
            initiator_type=turn["initiator_type"],
            responder_id=turn["responder_id"],
            responder_type=turn["responder_type"],
            status=turn["status"],
            metadata=turn["metadata"],
            start_time=datetime.fromisoformat(turn["start_time"]),
            end_time=datetime.fromisoformat(turn["end_time"]) if turn["end_time"] else None,
            request_messages=[
                Message(
                    id=msg["id"],
                    turn_id=msg["turn_id"],
                    content=msg["content"],
                    type=msg["type"],
                    sender_id=msg["sender_id"],
                    sender_type=msg["sender_type"],
                    metadata=msg["metadata"],
                    timestamp=datetime.fromisoformat(msg["timestamp"])
                )
                for msg in turn["request_messages"]
            ],
            response_messages=[
                Message(
                    id=msg["id"],
                    turn_id=msg["turn_id"],
                    content=msg["content"],
                    type=msg["type"],
                    sender_id=msg["sender_id"],
                    sender_type=msg["sender_type"],
                    metadata=msg["metadata"],
                    timestamp=datetime.fromisoformat(msg["timestamp"])
                )
                for msg in turn["response_messages"]
            ],
            tool_calls=[
                ToolCall(
                    id=tool["id"],
                    turn_id=tool["turn_id"],
                    tool_name=tool["tool_name"],
                    tool_args=tool["tool_args"],
                    tool_result=tool["tool_result"],
                    status=tool["status"],
                    created_at=datetime.fromisoformat(tool["created_at"]),
                    completed_at=datetime.fromisoformat(tool["completed_at"]) if tool["completed_at"] else None
                )
                for tool in turn.get("tool_calls", [])
            ]
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取轮次详情时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 工具API
@router.get("/tools", response_model=Dict[str, Any])
async def get_tools():
    """
    获取可用工具列表
    """
    # 确保对话系统已初始化
    init_dialogue_system()
    
    try:
        # 从ToolInvoker获取可用工具
        tools = []  # 这里应该从工具调用器中获取
        
        return {
            "tools": tools,
            "total": len(tools)
        }
        
    except Exception as e:
        logger.error(f"获取工具列表时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 文件上传API（用于多模态输入）
@router.post("/upload", response_model=Dict[str, Any])
async def upload_file(file: UploadFile = File(...)):
    """
    上传文件（图片、音频等）
    """
    try:
        # 读取文件内容
        content = await file.read()
        
        # 保存文件（这里应该保存到实际存储中）
        file_id = str(uuid.uuid4())
        file_path = f"/uploads/{file_id}_{file.filename}"
        
        # 这里应该实际保存文件
        # with open(f"static{file_path}", "wb") as f:
        #     f.write(content)
        
        logger.info(f"文件上传成功: {file.filename}, 大小: {len(content)} 字节")
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "url": file_path,
            "content_type": file.content_type,
            "size": len(content)
        }
        
    except Exception as e:
        logger.error(f"文件上传时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 设置路由
def setup_dialogue_routes(app):
    """
    设置对话管理系统API路由
    
    Args:
        app: FastAPI应用实例
    """
    app.include_router(router)
    logger.info("对话管理系统API路由已设置")
