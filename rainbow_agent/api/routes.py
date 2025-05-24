"""
API路由模块

提供与外部服务和前端集成的API路由。
使用标准OpenAI API。
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..utils.llm import chat_completion, is_api_available, get_llm_client
from ..config.settings import get_settings
from ..utils.logger import get_logger
from ..api.team_service import process_query

# 获取配置和日志记录器
settings = get_settings()
logger = get_logger(__name__)

# 创建路由器
router = APIRouter(prefix="/api", tags=["api"])


# 请求和响应模型
class ChatMessage(BaseModel):
    role: str = Field(..., description="消息角色: 'system', 'user', 或 'assistant'")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="聊天消息历史")
    model: Optional[str] = Field(None, description="要使用的模型")
    temperature: Optional[float] = Field(None, description="生成温度,范围0-1")
    max_tokens: Optional[int] = Field(None, description="最大输出标记数")


class ChatResponse(BaseModel):
    content: str = Field(..., description="生成的响应内容")
    model: str = Field(..., description="使用的模型")
    usage: Optional[Dict[str, Any]] = Field(None, description="令牌使用情况")
    duration: float = Field(..., description="生成用时(秒)")


# 健康检查端点
@router.get("/health")
async def health_check():
    """API健康检查端点"""
    return {"status": "ok", "version": "1.0.0"}


# 聊天完成端点
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天完成API端点
    
    接收聊天消息历史，返回模型生成的响应
    """
    try:
        # 准备消息
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # 调用聊天完成
        response = chat_completion(
            messages, 
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # 返回响应
        return response
    except Exception as e:
        logger.error(f"处理聊天请求时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# API状态端点
@router.get("/status")
async def api_status():
    """
    API服务状态检查
    
    提供API连接和配置信息
    """
    # 检测API可用性
    api_available = is_api_available()
    
    # 获取API基础URL和其他设置
    base_url = settings.get("api.base_url")
    
    # 获取可用模型列表
    available_models = ["gpt-3.5-turbo", "gpt-4"]  # 默认模型
    try:
        # 如果API可用，获取实际可用模型
        if api_available:
            client = get_llm_client()
            models_response = client.models.list()
            available_models = [model.id for model in models_response.data]
    except Exception as e:
        logger.warning(f"无法获取可用模型列表: {e}")
    
    return {
        "status": "ok",
        "openai_api": {
            "connected": api_available,
            "base_url": base_url,
            "available_models": available_models,
            "default_model": settings.get("llm.model")
        },
        "version": "1.0.0"
    }


# Rainbow前端专用模型

class RainbowRequest(BaseModel):
    prompt: str = Field(..., description="用户输入提示")
    system_prompt: Optional[str] = Field(None, description="系统提示（可选）")
    model: Optional[str] = Field(None, description="模型名称（可选）")
    temperature: Optional[float] = Field(None, description="生成温度（可选）")
    history: Optional[List[Dict[str, str]]] = Field([], description="历史消息记录（可选）")


class RainbowResponse(BaseModel):
    content: str = Field(..., description="生成的响应内容")
    model: str = Field(..., description="使用的模型")
    success: bool = Field(..., description="请求是否成功")


# Rainbow前端专用模型 - 增强版
class RainbowTeamResponse(BaseModel):
    content: str = Field(..., description="生成的响应内容")
    teamContributions: List[Dict[str, str]] = Field(..., description="团队成员贡献")
    success: bool = Field(True, description="请求是否成功")
    model: Optional[str] = Field(None, description="使用的模型")


# Rainbow前端专用端点 - 团队协作版
@router.post("/rainbow", response_model=RainbowTeamResponse)
async def rainbow_chat(request: RainbowRequest):
    """
    Rainbow前端专用端点
    
    接收前端提交的提示和参数，返回生成的响应
    使用团队协作像系统进行多专家协同应答
    """
    try:
        logger.info(f"接收到Rainbow请求: {request.prompt[:50]}...")
        
        # 如果历史消息很多，只保留最近的10条
        history = request.history or []
        if len(history) > 10:
            history = history[-10:]
            logger.info(f"历史消息过多，截取最近的10条")
            
        # 使用团队服务处理查询
        team_response = process_query(
            query=request.prompt,
            system_prompt=request.system_prompt,
            max_tokens=2000  # 设置默认的输出限制
        )
        
        # 生成响应
        response = {
            "content": team_response.get("content", "抱歉，处理您的请求时出现问题"),
            "teamContributions": team_response.get("teamContributions", []),
            "model": request.model or settings.get("llm.model", "gpt-3.5-turbo"),
            "success": True
        }
        
        logger.info(f"团队响应生成成功，包含{len(response['teamContributions'])}个贡献")
        return response
        
    except Exception as e:
        logger.error(f"处理Rainbow请求时出错: {e}")
        # 返回错误响应
        return JSONResponse(
            status_code=500,
            content={
                "content": f"发生错误: {str(e)}",
                "teamContributions": [
                    {"expert": "系统监控", "contribution": f"检测到错误: {str(e)}"}
                ],
                "model": request.model or settings.get("llm.model", "gpt-3.5-turbo"),
                "success": False
            }
        )


# 原来的简单接口 - 不使用团队协作
@router.post("/chat_simple", response_model=RainbowResponse)
async def simple_chat(request: RainbowRequest):
    """
    简单版聊天接口
    
    不使用团队协作，直接调用OpenAI API
    """
    try:
        # 准备消息列表
        messages = []
        
        # 添加系统提示（如果有）
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
            
        # 添加历史消息（如果有）
        if request.history and len(request.history) > 0:
            messages.extend(request.history)
        
        # 添加当前用户提示
        messages.append({"role": "user", "content": request.prompt})
        
        # 调用聊天完成API
        response = chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature
        )
        
        # 返回响应
        return {
            "content": response["content"],
            "model": response["model"],
            "success": True
        }
        
    except Exception as e:
        logger.error(f"处理简单聊天请求时出错: {e}")
        # 返回错误响应
        return JSONResponse(
            status_code=500,
            content={
                "content": f"发生错误: {str(e)}",
                "model": request.model or settings.get("llm.model", "gpt-3.5-turbo"),
                "success": False
            }
        )


def setup_routes(app):
    """
    设置API路由
    
    Args:
        app: FastAPI应用实例
    """
    app.include_router(router)
    logger.info("API路由已设置")
