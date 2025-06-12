"""
对话管理器上下文增强混入类

为DialogueManager添加上下文处理和注入功能。
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .context_processor import ContextProcessor
from .context_injector import ContextInjector
from .context_types import ContextConfig

logger = logging.getLogger(__name__)


class DialogueManagerContextMixin:
    """
    对话管理器上下文增强混入类
    
    为DialogueManager添加上下文处理和注入功能，通过混入方式集成，
    避免直接修改核心类结构。
    """
    
    def __init__(self, 
                 context_processor: Optional[ContextProcessor] = None,
                 context_injector: Optional[ContextInjector] = None,
                 context_config: Optional[ContextConfig] = None,
                 *args, **kwargs):
        """
        初始化上下文增强混入类
        
        Args:
            context_processor: 上下文处理器，如果不提供则创建新实例
            context_injector: 上下文注入器，如果不提供则创建新实例
            context_config: 上下文配置，如果不提供则使用默认配置
        """
        # 调用父类初始化方法（如果有的话）
        super().__init__(*args, **kwargs)
        
        # 初始化上下文组件
        self._context_config = context_config or ContextConfig()
        self._context_processor = context_processor or ContextProcessor(self._context_config)
        self._context_injector = context_injector or ContextInjector(self._context_config)
        
        logger.info("对话管理器上下文增强功能初始化成功")
        
    def process_context(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理上下文元数据
        
        Args:
            metadata: 原始元数据
            
        Returns:
            处理后的上下文数据
        """
        if not metadata or not self._context_config.enable_injection:
            return {}
            
        try:
            return self._context_processor.process_context(metadata)
        except Exception as e:
            logger.error(f"处理上下文时出错: {e}")
            return {}
            
    def inject_context_to_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        将上下文注入到提示中
        
        Args:
            prompt: 原始提示文本
            context: 处理后的上下文数据
            
        Returns:
            注入上下文后的提示文本
        """
        if not context or not self._context_config.enable_injection:
            return prompt
            
        try:
            return self._context_injector.inject_context_to_prompt(prompt, context)
        except Exception as e:
            logger.error(f"注入上下文到提示时出错: {e}")
            return prompt
            
    def inject_context_to_messages(self, messages: List[Dict[str, str]], context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        将上下文注入到消息列表中
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            context: 处理后的上下文数据
            
        Returns:
            注入上下文后的消息列表
        """
        if not context or not self._context_config.enable_injection:
            return messages
            
        try:
            return self._context_injector.inject_context_to_messages(messages, context)
        except Exception as e:
            logger.error(f"注入上下文到消息列表时出错: {e}")
            return messages
            
    def inject_context_to_history(self, history: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """
        将上下文注入到对话历史中
        
        Args:
            history: 对话历史记录
            context: 处理后的上下文数据
            
        Returns:
            注入上下文后的对话历史
        """
        if not context or not self._context_config.enable_injection:
            return history
            
        try:
            return self._context_injector.inject_context_to_history(history, context)
        except Exception as e:
            logger.error(f"注入上下文到历史时出错: {e}")
            return history
            
    def _extract_recent_topic(self, turns: List[Dict[str, Any]]) -> Optional[str]:
        """
        从对话历史中提取最近的主题
        
        Args:
            turns: 对话历史轮次
            
        Returns:
            最近的主题，如果无法检测则返回None
        """
        if not turns:
            return None
            
        # 反向遍历对话历史，忽略简短的“继续”类指令
        continuation_phrases = ["继续", "继续讲", "请继续", "再说一点", "说下去"]
        
        # 先找到最后一条非“继续”类的用户输入
        last_meaningful_user_input = None
        for turn in reversed(turns):
            role = turn.get('role', '')
            content = turn.get('content', '')
            
            # 只处理用户输入
            if role in ['human', 'user']:
                # 如果不是简单的“继续”类指令
                if content and len(content.strip()) > 1 and not any(phrase in content for phrase in continuation_phrases):
                    last_meaningful_user_input = content
                    break
        
        # 如果找不到有意义的用户输入，尝试从最近的AI回复中提取主题
        if not last_meaningful_user_input:
            for turn in reversed(turns):
                role = turn.get('role', '')
                content = turn.get('content', '')
                
                if role in ['ai', 'assistant'] and content and len(content) > 10:
                    # 简单地取前20个字符作为主题提示
                    return content[:20] + "..."
            
        return last_meaningful_user_input
    
    def _build_prompt(self, turns: List[Dict[str, Any]]) -> str:
        """
        构建基础提示文本
        
        Args:
            turns: 对话历史轮次
            
        Returns:
            格式化后的提示文本
        """
        try:
            # 确保ai_service存在
            if not hasattr(self, 'ai_service'):
                logger.warning("ai_service不存在，无法构建提示")
                return ""
                
            # 格式化对话历史
            formatted_messages = self.ai_service.format_dialogue_history(turns)
            
            # 分析对话历史中的最近主题
            recent_topic = self._extract_recent_topic(turns)
            
            # 添加特殊指令，确保上下文连续性
            # 在系统消息中添加处理"继续"的指令
            if formatted_messages and formatted_messages[0]["role"] == "system":
                current_content = formatted_messages[0]["content"]
                continuity_instruction = "\n\n特别注意：如果用户输入\"继续\"或类似表达，请继续展开上一个话题，不要开始新话题。"
                
                # 如果检测到最近主题，添加到指令中
                if recent_topic:
                    continuity_instruction += f"\n当用户说\"继续\"时，请继续提供关于主题 '{recent_topic}' 的信息。"
                    
                formatted_messages[0]["content"] = current_content + continuity_instruction
            
            # 将格式化的消息转换为字符串
            prompt_parts = []
            for msg in formatted_messages:
                role = msg["role"]
                content = msg["content"]
                prompt_parts.append(f"{role}: {content}")
                
            return "\n\n".join(prompt_parts)
        except Exception as e:
            logger.error(f"构建基础提示时出错: {e}")
            return ""
    
    def build_prompt_with_context(self, 
                                    turns: List[Dict[str, Any]], 
                                    metadata: Optional[Dict[str, Any]]) -> str:
        """
        构建包含上下文的提示
        
        Args:
            turns: 对话历史轮次
            metadata: 元数据（可能包含上下文）
            
        Returns:
            包含上下文的提示文本
        """
        # 构建基础提示
        base_prompt = self._build_prompt(turns)
        
        # 处理上下文
        processed_context = self.process_context(metadata)
        
        # 添加对话历史上下文
        if turns and len(turns) > 0:
            # 如果元数据中没有对话历史，则从turns创建
            if not any(ctx.get('type') == 'dialogue_history' for ctx in processed_context.values() if isinstance(ctx, dict)):
                dialogue_history_context = {
                    'type': 'dialogue_history',
                    'history': []
                }
                
                # 将turns转换为标准格式
                for turn in turns:
                    if isinstance(turn, dict):
                        role = turn.get('role', 'unknown')
                        content = turn.get('content', '')
                        
                        dialogue_history_context['history'].append({
                            'role': role,
                            'content': content
                        })
                
                # 添加到处理后的上下文中
                if dialogue_history_context['history']:
                    processed_context['dialogue_history'] = dialogue_history_context
                    logger.debug(f"从turns创建对话历史上下文: {len(dialogue_history_context['history'])}轮对话")
        
        # 注入上下文
        enhanced_prompt = self.inject_context_to_prompt(base_prompt, processed_context)
        
        # 添加调试日志
        logger.debug(f"构建带上下文的提示完成，原始提示长度: {len(base_prompt)}，增强后提示长度: {len(enhanced_prompt)}")
        
        return enhanced_prompt
        
    def build_messages_with_context(self, 
                                     turns: List[Dict[str, Any]], 
                                     metadata: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        构建包含上下文的消息列表
        
        Args:
            turns: 对话历史轮次
            metadata: 元数据（可能包含上下文）
            
        Returns:
            包含上下文的消息列表
        """
        # 处理上下文
        processed_context = self.process_context(metadata)
        
        # 将对话轮次转换为消息列表格式
        messages = []
        
        # 提取最近的主题
        recent_topic = self._extract_recent_topic(turns)
        
        # 构建系统消息内容
        system_content = "你是一个有帮助的AI助手，请用简洁、准确、友好的方式回答用户的问题。"
        
        # 在系统消息中添加处理"继续"的指令
        if turns and len(turns) > 0:
            continuity_instruction = "\n\n特别注意：如果用户输入\"继续\"或类似表达，请继续展开上一个话题，不要开始新话题。"
            system_content += continuity_instruction
            
            if recent_topic:
                system_content += f"\n当用户说\"继续\"时，请继续提供关于主题 '{recent_topic}' 的信息。"
        
        # 添加系统消息
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # 添加对话历史
        for turn in turns:
            if isinstance(turn, dict):
                role = turn.get('role', '')
                content = turn.get('content', '')
                
                # 将 'human' 和 'ai' 角色映射到 OpenAI 的 'user' 和 'assistant' 角色
                if role == "human":
                    messages.append({"role": "user", "content": content})
                elif role == "ai":
                    messages.append({"role": "assistant", "content": content})
        
        # 注入上下文到消息列表
        enhanced_messages = self.inject_context_to_messages(messages, processed_context)
        
        # 添加调试日志
        logger.debug(f"构建带上下文的消息列表完成，原始消息数: {len(messages)}，增强后消息数: {len(enhanced_messages)}")
        
        return enhanced_messages
        
    def get_context_metadata(self, processed_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取上下文元数据（用于响应）
        
        Args:
            processed_context: 处理后的上下文
            
        Returns:
            上下文元数据
        """
        if not processed_context:
            return {"context_used": False}
            
        return {
            "context_used": True,
            "context_type": processed_context.get("type", "general"),
            "context_processed_at": datetime.now().isoformat()
        }
