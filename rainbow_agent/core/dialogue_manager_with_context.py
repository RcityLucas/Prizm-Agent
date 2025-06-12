"""
带上下文增强功能的对话管理器

这个模块扩展了原有的对话管理器，添加了上下文处理和注入功能。
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from rainbow_agent.core.dialogue_manager import DialogueManager, DIALOGUE_TYPES
from rainbow_agent.context import DialogueManagerContextMixin
from rainbow_agent.context.context_types import ContextConfig
from rainbow_agent.config.context_settings import get_context_settings

# 配置日志
logger = logging.getLogger(__name__)


class EnhancedDialogueManager(DialogueManager, DialogueManagerContextMixin):
    """
    增强型对话管理器
    
    扩展原有对话管理器，添加上下文处理和注入功能。
    """
    
    def __init__(self, *args, **kwargs):
        """
        初始化增强型对话管理器
        
        扩展原有初始化方法，添加上下文处理组件。
        """
        # 获取上下文配置
        context_settings = get_context_settings()
        
        # 参数名称映射
        config_params = {
            "enable_injection": context_settings.get("enable_context_injection", True),
            "priority_level": context_settings.get("context_priority_level", "medium"),
            "max_tokens": context_settings.get("max_context_tokens", 1000)
        }
        
        # 创建上下文配置
        context_config = ContextConfig(**config_params)
        
        # 调用父类初始化
        DialogueManager.__init__(self, *args, **kwargs)
        DialogueManagerContextMixin.__init__(self, context_config=context_config)
        
        logger.info("增强型对话管理器初始化成功，上下文注入功能：{}".
                   format("已启用" if context_config.enable_injection else "未启用"))
    
    async def _process_by_dialogue_type(self,
                                      dialogue_type: str,
                                      session_id: str,
                                      user_id: str,
                                      content: str,
                                      turns: List[Dict[str, Any]],
                                      metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        根据对话类型处理输入
        
        重写原有方法，添加上下文处理和注入功能。
        
        Args:
            dialogue_type: 对话类型
            session_id: 会话ID
            user_id: 用户ID
            content: 用户输入内容
            turns: 对话历史轮次
            metadata: 附加元数据
            
        Returns:
            (响应内容, 响应元数据)
        """
        # 默认响应元数据
        response_metadata = {
            "processed_at": datetime.now().isoformat(),
            "dialogue_type": dialogue_type,
            "tools_used": []
        }
        
        # 处理上下文
        processed_context = self.process_context(metadata)
        
        # 根据对话类型处理
        if dialogue_type == DIALOGUE_TYPES["HUMAN_AI_PRIVATE"]:
            # 人类与AI私聊
            if processed_context and self._context_config.enable_injection:
                # 使用上下文增强功能
                logger.info(f"使用上下文增强功能处理会话 {session_id}")
                
                # 构建带上下文的消息列表
                messages = self.build_messages_with_context(turns, processed_context)
                
                # 调用AI服务
                response = await self.ai_service.generate_response(messages)
                
                # 添加上下文元数据
                context_metadata = self.get_context_metadata(processed_context)
                response_metadata.update(context_metadata)
                
                # 更新用户交互计数
                await self._update_user_interaction_count(user_id)
                
                return response, response_metadata
            else:
                # 使用原有处理方法
                return await super()._process_human_ai_private(session_id, user_id, content, turns, metadata)
        
        elif dialogue_type == DIALOGUE_TYPES["AI_SELF_REFLECTION"]:
            # AI自我反思
            if processed_context and self._context_config.enable_injection:
                # 使用上下文增强功能处理AI自我反思
                # 这里可以根据需要实现上下文增强的AI自我反思处理逻辑
                pass
            
            # 使用原有处理方法
            return await super()._process_ai_self_reflection(session_id, content, turns, metadata)
        
        elif dialogue_type in [DIALOGUE_TYPES["HUMAN_AI_GROUP"], DIALOGUE_TYPES["AI_MULTI_HUMAN"]]:
            # 群聊对话
            if processed_context and self._context_config.enable_injection:
                # 使用上下文增强功能处理群聊对话
                # 这里可以根据需要实现上下文增强的群聊处理逻辑
                pass
            
            # 使用原有处理方法
            return await super()._process_group_chat(dialogue_type, session_id, user_id, content, turns, metadata)
        
        elif dialogue_type == DIALOGUE_TYPES["AI_AI_DIALOGUE"]:
            # AI与AI对话
            if processed_context and self._context_config.enable_injection:
                # 使用上下文增强功能处理AI与AI对话
                # 这里可以根据需要实现上下文增强的AI与AI对话处理逻辑
                pass
            
            # 使用原有处理方法
            return await super()._process_ai_ai_dialogue(session_id, content, turns, metadata)
        
        else:
            # 其他对话类型，使用原有处理方法
            return await super()._process_by_dialogue_type(dialogue_type, session_id, user_id, content, turns, metadata)
    
    async def _process_human_ai_private(self,
                                      session_id: str,
                                      user_id: str,
                                      content: str,
                                      turns: List[Dict[str, Any]],
                                      metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        处理人类与AI私聊
        
        重写原有方法，添加上下文处理和注入功能。
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            content: 用户输入内容
            turns: 对话历史轮次
            metadata: 附加元数据
            
        Returns:
            (响应内容, 响应元数据)
        """
        # 处理上下文
        processed_context = self.process_context(metadata)
        
        if processed_context and self._context_config.enable_injection:
            # 使用上下文增强功能
            logger.info(f"使用上下文增强功能处理人类与AI私聊 {session_id}")
            
            # 构建带上下文的消息列表
            messages = self.build_messages_with_context(turns, processed_context)
            
            # 调用AI服务
            response = await self.ai_service.generate_response(messages)
            
            # 构建响应元数据
            response_metadata = {
                "processed_at": datetime.now().isoformat(),
                "dialogue_type": DIALOGUE_TYPES["HUMAN_AI_PRIVATE"],
                "tools_used": [],
                "model": "gpt-3.5-turbo",  # 可以从配置中获取
                "user_id": user_id  # 记录发言者ID
            }
            
            # 添加上下文元数据
            context_metadata = self.get_context_metadata(processed_context)
            response_metadata.update(context_metadata)
            
            # 更新用户交互计数
            await self._update_user_interaction_count(user_id)
            
            return response, response_metadata
        else:
            # 使用原有处理方法
            return await super()._process_human_ai_private(session_id, user_id, content, turns, metadata)
    
    # 其他方法可以根据需要重写，添加上下文处理和注入功能
