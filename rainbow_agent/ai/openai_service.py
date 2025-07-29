"""
OpenAI 服务模块

提供与 OpenAI API 交互的功能，使用中央配置系统
"""
import logging
import json
from typing import List, Dict, Any, Optional, Union, Tuple
import asyncio
from tenacity import retry, stop_after_attempt, wait_random_exponential

from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion

from ..config.settings import get_settings
from ..utils.format_utils import format_dialogue_history

logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI 服务类，处理与 OpenAI API 的交互"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化 OpenAI 服务
        
        Args:
            api_key: OpenAI API 密钥，如果不提供则从配置系统获取
        """
        # 获取配置实例
        settings = get_settings()
        
        # 优先使用传入的API密钥，其次使用配置系统中的API密钥
        self.api_key = api_key or settings.get("api.api_key")
        
        if not self.api_key:
            logger.warning("未设置 OpenAI API 密钥，OpenAI 服务将无法使用")
            self.client = None
        else:
            # 创建 OpenAI 客户端，使用配置系统中的设置
            client_kwargs = {
                "api_key": self.api_key,
                "timeout": settings.get("api.timeout", 60)
            }
            
            # 添加代理配置（如果有）
            proxy = settings.get("api.proxy")
            if proxy:
                client_kwargs["http_client"] = {"proxy": proxy}
            
            # 添加自定义基础URL（如果有）
            base_url = settings.get("api.base_url")
            if base_url:
                client_kwargs["base_url"] = base_url
            
            # 创建客户端
            self.client = OpenAI(**client_kwargs)
            logger.info("OpenAI 服务初始化成功")
    
    def generate_response(self, 
                        messages: List[Dict[str, str]], 
                        model: Optional[str] = None,
                        temperature: Optional[float] = None,
                        max_tokens: Optional[int] = None) -> str:
        """生成 AI 回复
        
        Args:
            messages: 对话历史消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            model: 使用的模型名称，如果不提供则从配置获取
            temperature: 温度参数，控制随机性，如果不提供则从配置获取
            max_tokens: 最大生成的 token 数量，如果不提供则从配置获取
            
        Returns:
            生成的回复文本
        """
        try:
            if not self.client:
                logger.warning("未设置 API 密钥，返回默认回复")
                return "抱歉，我无法生成回复，因为未设置 OpenAI API 密钥。"
            
            # 从配置系统获取默认参数
            settings = get_settings()
            model = model or settings.get("llm.model", "gpt-3.5-turbo")
            temperature = temperature if temperature is not None else settings.get("llm.temperature", 0.7)
            max_tokens = max_tokens or settings.get("llm.max_tokens", 1000)
            
            logger.info(f"调用 OpenAI API 生成回复，模型: {model}, 消息数: {len(messages)}")
            
            # 使用新版 API 调用方式
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 提取回复文本
            reply = response.choices[0].message.content.strip()
            logger.info(f"成功生成回复，长度: {len(reply)}")
            
            return reply
        except Exception as e:
            logger.error(f"生成回复失败: {e}")
            # 返回错误信息
            return f"抱歉，生成回复时出现错误: {str(e)}"
    
    def format_dialogue_history(self, turns: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """将对话轮次格式化为 OpenAI API 所需的格式
        
        Args:
            turns: 对话轮次列表
            
        Returns:
            格式化后的消息列表
        """
        messages = []
        
        # 从配置获取系统消息
        settings = get_settings()
        system_message = settings.get("llm.system_message", "你是一个有帮助的AI助手，请用简洁、准确、友好的方式回答用户的问题。")
        
        # 添加系统消息
        messages.append({
            "role": "system",
            "content": system_message
        })
        
        # 添加对话历史
        for turn in turns:
            role = turn.get("role", "")
            content = turn.get("content", "")
            
            # 将 'human' 和 'ai' 角色映射到 OpenAI 的 'user' 和 'assistant' 角色
            if role == "human":
                messages.append({"role": "user", "content": content})
            elif role == "ai":
                messages.append({"role": "assistant", "content": content})
        
        return messages
        
    @retry(stop=stop_after_attempt(3), wait=wait_random_exponential(min=1, max=10))
    async def get_embedding_async(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """生成文本的嵌入向量（异步版本）
        
        Args:
            text: 需要生成嵌入向量的文本
            model: 使用的嵌入模型，默认为 text-embedding-3-small
            
        Returns:
            嵌入向量，通常是1536维的浮点数列表
        """
        if not self.client:
            logger.warning("未设置 API 密钥，无法生成嵌入向量")
            raise ValueError("未设置 OpenAI API 密钥，无法生成嵌入向量")
        
        # 获取配置实例
        settings = get_settings()
        
        # 创建异步客户端
        client_kwargs = {
            "api_key": self.api_key,
            "timeout": settings.get("api.timeout", 60)
        }
        
        # 添加代理配置（如果有）
        proxy = settings.get("api.proxy")
        if proxy:
            client_kwargs["http_client"] = {"proxy": proxy}
        
        # 添加自定义基础URL（如果有）
        base_url = settings.get("api.base_url")
        if base_url:
            client_kwargs["base_url"] = base_url
            
        # 创建异步客户端
        async_client = AsyncOpenAI(**client_kwargs)
        
        try:
            logger.info(f"调用 OpenAI API 生成嵌入向量，模型: {model}, 文本长度: {len(text)}")
            
            # 调用嵌入API
            response = await async_client.embeddings.create(
                model=model,
                input=text
            )
            
            # 提取嵌入向量
            embedding = response.data[0].embedding
            logger.info(f"成功生成嵌入向量，维度: {len(embedding)}")
            
            return embedding
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
            
    def get_embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """生成文本的嵌入向量（同步版本）
        
        Args:
            text: 需要生成嵌入向量的文本
            model: 使用的嵌入模型，默认为 text-embedding-3-small
            
        Returns:
            嵌入向量，通常是1536维的浮点数列表
        """
        if not self.client:
            logger.warning("未设置 API 密钥，无法生成嵌入向量")
            raise ValueError("未设置 OpenAI API 密钥，无法生成嵌入向量")
            
        try:
            logger.info(f"调用 OpenAI API 生成嵌入向量，模型: {model}, 文本长度: {len(text)}")
            
            # 调用嵌入API
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            
            # 提取嵌入向量
            embedding = response.data[0].embedding
            logger.info(f"成功生成嵌入向量，维度: {len(embedding)}")
            
            return embedding
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
