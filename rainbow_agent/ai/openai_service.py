"""
OpenAI 服务模块

提供与 OpenAI API 交互的功能
"""
import os
import logging
from typing import Dict, Any, List, Optional

# 导入新版本的 OpenAI 客户端
from openai import OpenAI

# 配置日志
logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI 服务类，处理与 OpenAI API 的交互"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化 OpenAI 服务
        
        Args:
            api_key: OpenAI API 密钥，如果不提供则从环境变量获取
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("未设置 OPENAI_API_KEY 环境变量，OpenAI 服务将无法使用")
            self.client = None
        else:
            # 创建 OpenAI 客户端
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI 服务初始化成功")
    
    def generate_response(self, 
                        messages: List[Dict[str, str]], 
                        model: str = "gpt-3.5-turbo",
                        temperature: float = 0.7,
                        max_tokens: int = 1000) -> str:
        """生成 AI 回复
        
        Args:
            messages: 对话历史消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            model: 使用的模型名称
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成的 token 数量
            
        Returns:
            生成的回复文本
        """
        try:
            if not self.client:
                logger.warning("未设置 API 密钥，返回默认回复")
                return "抱歉，我无法生成回复，因为未设置 OpenAI API 密钥。"
            
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
        
        # 添加系统消息
        messages.append({
            "role": "system",
            "content": "你是一个有帮助的AI助手，请用简洁、准确、友好的方式回答用户的问题。"
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
