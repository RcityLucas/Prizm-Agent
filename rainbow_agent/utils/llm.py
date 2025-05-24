"""
LLM客户端工具

提供与OpenAI API交互的工具函数。
"""
import os
import time
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
import openai
import requests
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config.settings import get_settings
from .logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# 加载环境变量
load_dotenv()


def get_llm_client() -> OpenAI:
    """
    获取配置好的OpenAI客户端
    
    使用标准OpenAI API。
    
    Returns:
        OpenAI客户端实例
    """
    # 获取API密钥
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("未设置OPENAI_API_KEY环境变量，请确保设置了有效的API密钥")
    
    # 初始化客户端参数
    client_kwargs = {
        "api_key": api_key,
        "timeout": settings.get("api.timeout", 60),
        "max_retries": settings.get("api.max_retries", 3)
    }
    
    # 设置代理 - 首先检查配置文件中的代理设置，然后是系统环境变量
    # 1. 优先使用配置文件指定的代理
    proxy = settings.get("api.proxy")
    
    # 2. 如果配置文件中没有设置，则尝试使用系统环境变量中的代理
    if not proxy:
        # 检查系统环境变量中的HTTP/HTTPS代理设置
        if os.environ.get("HTTP_PROXY"):
            proxy = os.environ.get("HTTP_PROXY")
            logger.info(f"使用系统 HTTP 代理: {proxy}")
        elif os.environ.get("http_proxy"):
            proxy = os.environ.get("http_proxy")
            logger.info(f"使用系统 http 代理: {proxy}")
        elif os.environ.get("HTTPS_PROXY"):
            proxy = os.environ.get("HTTPS_PROXY")
            logger.info(f"使用系统 HTTPS 代理: {proxy}")
        elif os.environ.get("https_proxy"):
            proxy = os.environ.get("https_proxy")
            logger.info(f"使用系统 https 代理: {proxy}")
    
    # 3. 如果找到了代理设置，则应用到客户端
    if proxy:
        import httpx
        client_kwargs["http_client"] = httpx.Client(proxies={"http://": proxy, "https://": proxy})
        logger.info(f"使用HTTP代理: {proxy}")
    
    # 设置自定义基础URL（如果提供）
    base_url = settings.get("api.base_url")
    if base_url and base_url != "https://api.openai.com/v1":
        client_kwargs["base_url"] = base_url
        logger.info(f"使用自定义API基础URL: {base_url}")
    
    # 初始化客户端
    try:
        client = OpenAI(**client_kwargs)
        return client
    except Exception as e:
        logger.error(f"初始化OpenAI客户端时出错: {e}")
        # 尝试使用最小配置
        return OpenAI(api_key=api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def create_embedding(text: str, model: str = "text-embedding-ada-002") -> List[float]:
    """
    为文本创建嵌入向量
    
    使用自动重试机制增强可靠性。
    
    Args:
        text: 输入文本
        model: 使用的嵌入模型
        
    Returns:
        嵌入向量
    """
    client = get_llm_client()
    
    try:
        # 检查文本的有效性
        if not text or not isinstance(text, str):
            logger.warning(f"无效的嵌入文本: {type(text)}")
            return [0.0] * 1536  # 返回零向量作为备选
            
        # 清理文本
        text = text.strip()
        if not text:
            return [0.0] * 1536
        
        # 生成嵌入向量
        response = client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"创建嵌入时出错: {e}")
        # 重新抛出异常以触发重试
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def chat_completion(messages: List[Dict[str, str]], model: str = None, temperature: float = None, 
                    max_tokens: int = None) -> Dict[str, Any]:
    """
    调用聊天完成API生成响应
    
    支持自动重试和错误处理。
    
    Args:
        messages: 消息列表，每个消息包含'role'和'content'
        model: 模型名称，如果为None则使用配置文件中的默认值
        temperature: 温度参数，如果为None则使用配置文件中的默认值
        max_tokens: 最大输出标记数，如果为None则使用配置文件中的默认值
        
    Returns:
        完成响应的字典
    """
    client = get_llm_client()
    
    # 获取模型参数，如果没有指定则使用默认值
    model = model or settings.get("llm.model", "gpt-3.5-turbo")
    temperature = temperature if temperature is not None else settings.get("llm.temperature", 0.7)
    max_tokens = max_tokens or settings.get("llm.max_tokens", 2000)
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 规范化消息格式
        normalized_messages = []
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                logger.warning(f"无效的消息格式: {msg}")
                continue
                
            # 添加有效消息
            normalized_messages.append({
                "role": msg["role"],
                "content": str(msg["content"])
            })
        
        if not normalized_messages:
            logger.error("消息列表为空或格式不正确")
            return {"error": "消息格式错误"}
        
        # 调用API
        response = client.chat.completions.create(
            model=model,
            messages=normalized_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 记录完成时间
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"生成完成，使用模型: {model}, 用时: {duration:.2f}秒")
        
        # 返回结果
        return {
            "content": response.choices[0].message.content,
            "model": model,
            "usage": response.usage.model_dump() if hasattr(response, 'usage') else None,
            "duration": duration
        }
        
    except Exception as e:
        logger.error(f"调用聊天完成API时出错: {e}")
        # 重新抛出异常以触发重试
        raise


def is_api_available() -> bool:
    """
    检测 OpenAI API 是否可用
    
    Returns:
        API 服务是否可用
    """
    try:
        # 获取 API 密钥
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("未设置 OPENAI_API_KEY 环境变量")
            return False
            
        # 尝试连接 OpenAI API
        timeout = settings.get("api.timeout", 5)  # 设置较短的超时时间进行检测
        client = get_llm_client()
        
        # 检查可用模型 - 这会验证API连接性
        client.models.list(timeout=timeout)
        return True
    except Exception as e:
        logger.warning(f"OpenAI API 连接性检测失败: {e}")
        return False
