"""
聊天 API 路由模块

提供聊天相关的 API 路由，包括使用 OpenAI API 生成聊天响应。
"""
import os
import json
import logging
import traceback
from typing import Dict, Any, List, Optional

from flask import Blueprint, request, jsonify
import openai

from ..utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# 创建Blueprint
chat_api = Blueprint('chat_api', __name__, url_prefix='/api')

# 配置OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")  # 默认使用官方API端点

# 如果设置了API密钥，则配置OpenAI客户端
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    if OPENAI_BASE_URL:
        openai.base_url = OPENAI_BASE_URL
    logger.info(f"OpenAI API已配置，基础URL: {OPENAI_BASE_URL}")
else:
    logger.warning("未设置OpenAI API密钥，聊天功能将不可用")

@chat_api.route('/chat', methods=['POST'])
def chat():
    """处理聊天请求，使用OpenAI API生成响应"""
    try:
        # 检查API密钥是否已配置
        if not OPENAI_API_KEY:
            return jsonify({
                "success": False,
                "error": "未配置OpenAI API密钥，请设置OPENAI_API_KEY环境变量"
            }), 500
        
        # 解析请求数据
        data = request.json
        logger.info(f"收到聊天请求: {json.dumps(data, ensure_ascii=False)}")
        
        # 支持多种请求格式
        messages = data.get('messages', [])
        content = data.get('content')
        prompt = data.get('prompt')
        
        # 如果没有消息列表，但有内容或提示，则创建消息列表
        if not messages and (content or prompt):
            user_content = content or prompt
            messages = [
                {"role": "system", "content": "你是一个有用的AI助手，名为Rainbow助手。"},
                {"role": "user", "content": user_content}
            ]
        
        # 获取其他参数
        model = data.get('model', 'gpt-3.5-turbo')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        # 验证消息格式
        if not messages:
            return jsonify({
                "success": False,
                "error": "消息列表为空，且未提供content或prompt"
            }), 400
        
        # 记录请求信息
        logger.info(f"处理聊天请求: 模型={model}, 消息数量={len(messages)}")
        
        # 调用OpenAI API
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 提取响应内容
            response_message = response.choices[0].message
            content = response_message.content
            
            # 将对象转换为字典，确保可序列化
            message_dict = {
                "role": response_message.role,
                "content": content
            }
            
            # 如果有工具调用，也将其转换为字典
            if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                tool_calls_list = []
                for tool_call in response_message.tool_calls:
                    tool_call_dict = {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    tool_calls_list.append(tool_call_dict)
                message_dict["tool_calls"] = tool_calls_list
            
            # 将用量信息转换为字典
            usage_dict = None
            if hasattr(response, 'usage'):
                try:
                    usage_dict = response.usage.model_dump()
                except:
                    # 兼容旧版本
                    usage_dict = {
                        "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                        "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                        "total_tokens": getattr(response.usage, 'total_tokens', 0)
                    }
            
            # 返回响应（支持多种格式）
            return jsonify({
                "success": True,
                "choices": [{
                    "message": message_dict,
                    "index": 0,
                    "finish_reason": response.choices[0].finish_reason
                }],
                "content": content,
                "text": content,
                "usage": usage_dict
            })
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return jsonify({
                "success": False,
                "error": f"OpenAI API调用失败: {str(e)}"
            }), 500
    except Exception as e:
        logger.error(f"处理聊天请求失败: {e}")
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }), 500

def register_chat_routes(app):
    """注册聊天API路由
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(chat_api)
    logger.info("聊天API路由已注册")
