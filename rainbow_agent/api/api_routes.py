"""
API路由模块

统一的API路由层，处理所有前端请求，确保一致的接口行为
支持多种客户端格式，包括simple_test.html, test_api.html和enhanced_index.html
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from pydantic import BaseModel
from datetime import datetime

from rainbow_agent.core.dialogue_manager import DialogueManager, DIALOGUE_TYPES
from rainbow_agent.ai.openai_service import OpenAIService
from rainbow_agent.storage.session_manager import SessionManager
from rainbow_agent.storage.turn_manager import TurnManager
from rainbow_agent.core.multi_modal_manager import MultiModalToolManager

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/dialogue")

# 全局依赖注入
dialogue_manager = DialogueManager()
multi_modal_manager = MultiModalToolManager()

# 数据模型
class SessionCreate(BaseModel):
    """会话创建请求模型"""
    userId: str
    title: Optional[str] = None
    dialogueType: Optional[str] = DIALOGUE_TYPES["HUMAN_AI_PRIVATE"]
    participants: Optional[List[Dict[str, str]]] = None

class UserInput(BaseModel):
    """用户输入请求模型"""
    sessionId: str
    input: str
    inputType: Optional[str] = "text"
    metadata: Optional[Dict[str, Any]] = None

class ApiResponse(BaseModel):
    """标准API响应模型"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

# API端点
@router.get("/types")
async def get_dialogue_types() -> ApiResponse:
    """获取支持的对话类型"""
    try:
        types_data = {
            "types": [
                {"id": type_id, "name": type_name} 
                for type_id, type_name in DIALOGUE_TYPES.items()
            ]
        }
        return ApiResponse(success=True, data=types_data)
    except Exception as e:
        logger.error(f"获取对话类型失败: {e}")
        return ApiResponse(success=False, error=str(e))

@router.get("/tools")
async def get_tools() -> ApiResponse:
    """获取可用工具列表"""
    try:
        # 这里应该从工具注册表获取工具列表
        # 暂时返回模拟数据
        tools = [
            {
                "id": "weather",
                "name": "天气查询",
                "description": "查询指定城市的天气信息",
                "version": "1.0",
                "provider": "OpenWeatherMap"
            },
            {
                "id": "calculator",
                "name": "计算器",
                "description": "执行数学计算",
                "version": "1.0",
                "provider": "System"
            },
            {
                "id": "image_generator",
                "name": "图像生成",
                "description": "根据描述生成图像",
                "version": "1.0",
                "provider": "DALL-E"
            }
        ]
        
        # 为了兼容所有客户端，返回两种格式
        return JSONResponse({
            "success": True, 
            "data": {"tools": tools},
            "tools": tools  # 直接提供工具列表，兼容simple_test.html
        })
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        return JSONResponse({
            "success": False, 
            "error": str(e),
            "traceback": error_traceback
        }, status_code=500)

@router.get("/sessions")
async def get_sessions(userId: Optional[str] = None) -> ApiResponse:
    """获取会话列表"""
    try:
        sessions = await dialogue_manager.session_manager.get_sessions(userId)
        
        # 为了兼容所有客户端，返回多种格式
        response_data = {
            "success": True,
            "data": {"sessions": sessions},
            "sessions": sessions,  # 直接提供会话列表，兼容simple_test.html
            "items": sessions,     # enhanced_index.html 期望的格式
            "total": len(sessions) # enhanced_index.html 期望的格式
        }
        return JSONResponse(response_data)
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        return JSONResponse({
            "success": False, 
            "error": str(e),
            "traceback": error_traceback
        }, status_code=500)

@router.post("/sessions")
async def create_session(session_data: Optional[SessionCreate] = None, request: Request = None) -> ApiResponse:
    """创建新会话"""
    try:
        # 尝试获取请求数据，兼容多种客户端格式
        data = {}
        
        # 如果通过Pydantic模型接收
        if session_data:
            data = session_data.dict()
        # 否则尝试从请求体解析JSON
        else:
            try:
                data = await request.json()
            except Exception:
                # 如果不是JSON，尝试从表单获取
                try:
                    form_data = await request.form()
                    data = dict(form_data)
                except Exception:
                    # 如果都失败，使用默认值
                    pass
        
        # 获取必要参数，提供默认值
        user_id = data.get('userId', str(uuid.uuid4()))
        title = data.get('title', f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        dialogue_type = data.get('dialogueType', DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
        
        # 处理参与者数据
        participants = data.get('participants', [user_id])
        participant_ids = []
        
        # 如果participants是字典列表，提取ID
        if participants and isinstance(participants, list):
            if all(isinstance(p, dict) for p in participants):
                participant_ids = [p.get("id") for p in participants if "id" in p]
            else:
                participant_ids = participants
        # 如果participants是字符串，转换为列表
        elif participants and isinstance(participants, str):
            participant_ids = [participants]
        # 如果没有提供，使用user_id
        else:
            participant_ids = [user_id]
            
        # 确保至少有一个参与者
        if not participant_ids:
            participant_ids = [user_id]
            
        logger.info(f"创建会话: 用户={user_id}, 标题={title}, 类型={dialogue_type}, 参与者={participant_ids}")
        
        # 调用对话管理器创建会话
        session = await dialogue_manager.create_session(
            user_id=user_id,
            dialogue_type=dialogue_type,
            title=title,
            participants=participant_ids
        )
        
        # 返回多种格式，兼容所有客户端
        return JSONResponse({
            "success": True,
            "data": session,
            **session  # 直接将会话数据展开，兼容simple_test.html
        })
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        return JSONResponse({
            "success": False, 
            "error": str(e),
            "traceback": error_traceback
        }, status_code=500)

@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> ApiResponse:
    """获取特定会话"""
    try:
        session = await dialogue_manager.session_manager.get_session(session_id)
        if not session:
            return ApiResponse(success=False, error="会话不存在")
        return ApiResponse(success=True, data=session)
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        return ApiResponse(success=False, error=str(e))

@router.get("/sessions/{session_id}/turns")
async def get_session_turns(session_id: str) -> ApiResponse:
    """获取会话轮次"""
    try:
        turns = await dialogue_manager.turn_manager.get_turns(session_id)
        return ApiResponse(success=True, data={"turns": turns})
    except Exception as e:
        logger.error(f"获取会话轮次失败: {e}")
        return ApiResponse(success=False, error=str(e))

@router.post("/input")
async def process_text_input(input_data: UserInput) -> ApiResponse:
    """处理文本输入"""
    try:
        result = await dialogue_manager.process_input(
            session_id=input_data.sessionId,
            user_id="user",  # 这里应该从认证中获取用户ID
            content=input_data.input,
            input_type=input_data.inputType,
            metadata=input_data.metadata
        )
        return ApiResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"处理文本输入失败: {e}")
        return ApiResponse(success=False, error=str(e))

@router.post("/input/image")
async def process_image_input(
    sessionId: str = Form(...),
    image: UploadFile = File(...),
    description: Optional[str] = Form(None)
) -> ApiResponse:
    """处理图像输入"""
    try:
        # 处理上传的图像
        image_content = await image.read()
        
        # 使用MultiModalToolManager处理图像
        image_result = await multi_modal_manager.process_image(image_content)
        
        # 构建元数据
        metadata = {
            "image_info": image_result,
            "filename": image.filename,
            "description": description
        }
        
        # 创建包含图像的消息
        message_content = f"[上传了图片: {image.filename}]"
        if description:
            message_content += f"\n描述: {description}"
            
        # 处理输入
        result = await dialogue_manager.process_input(
            session_id=sessionId,
            user_id="user",  # 这里应该从认证中获取用户ID
            content=message_content,
            input_type="image",
            metadata=metadata
        )
        
        return ApiResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"处理图像输入失败: {e}")
        return ApiResponse(success=False, error=str(e))

@router.post("/input/audio")
async def process_audio_input(
    sessionId: str = Form(...),
    audio: UploadFile = File(...)
) -> ApiResponse:
    """处理音频输入"""
    try:
        # 处理上传的音频
        audio_content = await audio.read()
        
        # 使用MultiModalToolManager处理音频
        audio_result = await multi_modal_manager.process_audio(audio_content)
        
        # 提取转录文本
        transcribed_text = audio_result.get("transcription", "无法识别音频内容")
        
        # 构建元数据
        metadata = {
            "audio_info": audio_result,
            "filename": audio.filename
        }
        
        # 处理输入
        result = await dialogue_manager.process_input(
            session_id=sessionId,
            user_id="user",  # 这里应该从认证中获取用户ID
            content=transcribed_text,
            input_type="audio",
            metadata=metadata
        )
        
        return ApiResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"处理音频输入失败: {e}")
        return ApiResponse(success=False, error=str(e))

@router.get("/system/status")
async def get_system_status() -> ApiResponse:
    """获取系统状态"""
    try:
        # 收集系统状态信息
        status = {
            "version": "1.0.0",
            "uptime": "获取系统运行时间",
            "sessions": {
                "total": await dialogue_manager.session_manager.count_sessions(),
                "active": await dialogue_manager.session_manager.count_active_sessions()
            },
            "ai_service": {
                "status": "online",
                "model": "gpt-3.5-turbo"
            },
            "storage": {
                "status": "healthy",
                "type": "SQLite"
            }
        }
        return ApiResponse(success=True, data=status)
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return ApiResponse(success=False, error=str(e))
