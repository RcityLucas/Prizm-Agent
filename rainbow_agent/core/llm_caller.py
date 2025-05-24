# rainbow_agent/core/llm_caller.py
from typing import Dict, Any, List, Optional
import time
from ..utils.llm import get_llm_client
from ..utils.logger import get_logger

logger = get_logger(__name__)

class LLMCaller:
    """
    LLM调用器，负责调用语言模型API
    """
    
    def __init__(
        self, 
        model: str = "gpt-3.5-turbo", 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        retry_attempts: int = 2
    ):
        """
        初始化LLM调用器
        
        Args:
            model: 使用的模型名称
            temperature: 生成温度
            max_tokens: 最大生成token数
            timeout: 超时时间（秒）
            retry_attempts: 重试次数
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.llm_client = get_llm_client()
        
        # 记录上次调用信息
        self.last_processing_time = 0
        self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    def call(self, context: Dict[str, Any], stream: bool = False) -> str:
        """
        调用LLM获取响应
        
        Args:
            context: 上下文信息
            stream: 是否使用流式输出
            
        Returns:
            LLM生成的响应文本
        """
        messages = context["messages"]
        start_time = time.time()
        
        # 准备API调用参数
        completion_args = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": stream,
        }
        
        if self.max_tokens:
            completion_args["max_tokens"] = self.max_tokens
        
        # 重试机制
        for attempt in range(self.retry_attempts + 1):
            try:
                logger.info(f"调用LLM，模型: {self.model}，尝试: {attempt+1}/{self.retry_attempts+1}")
                
                # 处理流式输出
                if stream:
                    response_chunks = []
                    for chunk in self.llm_client.chat.completions.create(**completion_args):
                        if chunk.choices and chunk.choices[0].delta.content:
                            response_chunks.append(chunk.choices[0].delta.content)
                    response_text = "".join(response_chunks)
                else:
                    # 非流式处理
                    response = self.llm_client.chat.completions.create(**completion_args)
                    response_text = response.choices[0].message.content
                    
                    # 记录token使用情况
                    if hasattr(response, 'usage'):
                        self.last_token_usage = {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        }
                
                # 记录处理时间
                self.last_processing_time = time.time() - start_time
                
                logger.info(f"LLM响应成功，用时: {self.last_processing_time:.2f}秒")
                return response_text
                
            except Exception as e:
                logger.error(f"LLM调用错误 (尝试 {attempt+1}/{self.retry_attempts+1}): {e}")
                if attempt < self.retry_attempts:
                    # 指数退避重试
                    retry_delay = 2 ** attempt
                    logger.info(f"将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    return f"抱歉，我遇到了技术问题: {str(e)}"