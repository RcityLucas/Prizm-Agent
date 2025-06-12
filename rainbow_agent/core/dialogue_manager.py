"""
对话管理系统核心模块

负责处理不同类型的对话流程，包括：
- 人类与人类私聊
- 人类与人类群聊
- 人类与AI私聊
- AI与AI对话
- AI自我对话（自我反思）
- 人类与AI群聊
- AI与多个人类群聊
"""
import logging
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from rainbow_agent.ai.openai_service import OpenAIService
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
from rainbow_agent.core.context_builder import ContextBuilder
from rainbow_agent.memory.memory import Memory
from rainbow_agent.frequency.frequency_integrator import FrequencyIntegrator
from rainbow_agent.frequency.frequency_sense_core import FrequencySenseCore
from rainbow_agent.frequency.expression_planner import ExpressionPlanner
from rainbow_agent.frequency.expression_generator import ExpressionGenerator
from rainbow_agent.frequency.expression_dispatcher import ExpressionDispatcher
from rainbow_agent.utils.logger import get_logger

# 配置日志
logger = logging.getLogger(__name__)

# 对话类型枚举
DIALOGUE_TYPES = {
    "HUMAN_HUMAN_PRIVATE": "human_human_private",  # 人类与人类私聊
    "HUMAN_HUMAN_GROUP": "human_human_group",      # 人类与人类群聊
    "HUMAN_AI_PRIVATE": "human_ai_private",        # 人类与AI私聊
    "AI_AI_DIALOGUE": "ai_ai_dialogue",            # AI与AI对话
    "AI_SELF_REFLECTION": "ai_self_reflection",    # AI自我对话（自我反思）
    "HUMAN_AI_GROUP": "human_ai_group",            # 人类与AI群聊
    "AI_MULTI_HUMAN": "ai_multi_human"             # AI与多个人类群聊
}

class DialogueManager:
    """对话管理系统核心类"""
    
    def __init__(self, 
                 storage: Optional[UnifiedDialogueStorage] = None,
                 ai_service: Optional[OpenAIService] = None,
                 memory: Optional[Memory] = None,
                 frequency_integrator: Optional[FrequencyIntegrator] = None):
        """初始化对话管理器
        
        Args:
            storage: 统一对话存储实例，如果不提供则创建新实例
            ai_service: AI服务实例，如果不提供则创建新实例
            memory: 记忆系统实例，如果不提供则为None
            frequency_integrator: 频率集成器实例，如果不提供则创建新实例
        """
        # 初始化组件
        self.storage = storage or UnifiedDialogueStorage()
        self.ai_service = ai_service or OpenAIService()
        self.memory = memory
        
        # 初始化上下文构建器
        self.context_builder = ContextBuilder(memory=self.memory) if self.memory else None
        
        # 初始化频率感知系统
        if frequency_integrator:
            self.frequency_integrator = frequency_integrator
        elif self.memory:
            # 如果有记忆系统但没有提供频率集成器，则创建一个新的
            frequency_sense_core = FrequencySenseCore(memory=self.memory)
            expression_planner = ExpressionPlanner(memory=self.memory)
            expression_generator = ExpressionGenerator(ai_service=self.ai_service)
            expression_dispatcher = ExpressionDispatcher()
            self.frequency_integrator = FrequencyIntegrator(
                frequency_sense_core=frequency_sense_core,
                expression_planner=expression_planner,
                expression_generator=expression_generator,
                expression_dispatcher=expression_dispatcher
            )
        else:
            self.frequency_integrator = None
        
        # 初始化工具调用器
        self.tool_invoker = None  # 将在后续实现
        
        logger.info("对话管理器初始化成功，频率感知系统：{}".
                   format("已启用" if self.frequency_integrator else "未启用"))
    
    async def create_session(self, 
                            user_id: str, 
                            dialogue_type: str = DIALOGUE_TYPES["HUMAN_AI_PRIVATE"],
                            title: Optional[str] = None,
                            participants: Optional[List[str]] = None) -> Dict[str, Any]:
        """创建新的对话会话
        
        Args:
            user_id: 创建会话的用户ID
            dialogue_type: 对话类型，默认为人类与AI私聊
            title: 会话标题，如果不提供则自动生成
            participants: 参与者ID列表，如果不提供则只包含创建者
            
        Returns:
            新创建的会话信息
        """
        # 生成默认标题
        if not title:
            title = f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 确保参与者列表包含创建者
        if not participants:
            participants = [user_id]
        elif user_id not in participants:
            participants.append(user_id)
        
        # 创建会话元数据
        metadata = {
            "dialogue_type": dialogue_type,
            "participants": participants,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # 调用统一存储创建会话
        try:
            session = await self.storage.create_session_async(user_id, title, metadata)
            if session and isinstance(session, dict):
                logger.info(f"成功创建会话: {session.get('id', '')}")
                return session
            else:
                logger.error("存储系统返回了无效的会话数据")
                # 返回一个模拟会话作为后备
                fallback_session = {
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'title': title,
                    'created_at': datetime.now().isoformat(),
                    'metadata': metadata
                }
                logger.warning(f"使用后备会话: {fallback_session['id']}")
                return fallback_session
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            # 返回一个模拟会话作为后备
            fallback_session = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'title': title,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata,
                'error': 'Database connection failed'
            }
            logger.warning(f"使用后备会话（数据库错误）: {fallback_session['id']}")
            return fallback_session
    
    async def process_input(self, 
                           session_id: Union[str, Dict[str, Any]], 
                           user_id: str, 
                           content: str,
                           input_type: str = "text",
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理用户输入并生成响应
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            content: 用户输入内容
            input_type: 输入类型，如text、image等
            metadata: 附加元数据
            
        Returns:
            处理结果，包含AI响应
        """
        try:
            # 确保session_id是字符串类型
            str_session_id = session_id
            if isinstance(session_id, dict):
                str_session_id = session_id.get('id', str(session_id))
                logger.info(f"Extracted session_id from dictionary in process_input: {str_session_id}")
            
            # 1. 创建用户轮次
            user_turn = await self.create_turn(str_session_id, "human", content, metadata)
            
            # 2. 获取会话历史
            session_info = await self.storage.get_session_async(str_session_id)
            if session_info and isinstance(session_info, dict):
                dialogue_type = session_info.get("metadata", {}).get("dialogue_type", DIALOGUE_TYPES["HUMAN_AI_PRIVATE"])
            else:
                logger.warning(f"无法获取会话信息，使用默认对话类型: {str_session_id}")
                dialogue_type = DIALOGUE_TYPES["HUMAN_AI_PRIVATE"]
            
            # 3. 获取对话历史
            turns = await self.storage.get_turns_async(str_session_id)
            
            # 4. 根据对话类型处理输入
            response_content, response_metadata = await self._process_by_dialogue_type(
                dialogue_type, str_session_id, user_id, content, turns, metadata
            )
            
            # 5. 创建AI轮次
            ai_turn = await self.create_turn(str_session_id, "ai", response_content, response_metadata)
            
            # 6. 更新用户信息（如果频率集成器可用）
            if self.frequency_integrator and self.memory:
                try:
                    # 更新用户交互计数
                    await self._update_user_interaction_count(user_id)
                except Exception as e:
                    logger.error(f"更新用户交互计数失败: {e}")
            
            # 7. 返回结果
            return {
                "id": str(uuid.uuid4()),
                "input": content,
                "response": response_content,
                "sessionId": str_session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": response_metadata
            }
        except Exception as e:
            logger.error(f"处理输入失败: {e}")
            # 确保session_id是字符串类型（即使在错误处理中）
            str_session_id = session_id
            if isinstance(session_id, dict):
                str_session_id = session_id.get('id', str(session_id))
            
            # 返回错误信息
            return {
                "id": str(uuid.uuid4()),
                "input": content,
                "response": f"处理输入时出现错误: {str(e)}",
                "sessionId": str_session_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def create_turn(self, 
                         session_id: str, 
                         role: str, 
                         content: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建对话轮次
        
        Args:
            session_id: 会话ID
            role: 角色，如human或ai
            content: 内容
            metadata: 元数据
            
        Returns:
            创建的轮次信息
        """
        try:
            # 调用统一存储创建轮次
            turn = await self.storage.create_turn_async(session_id, role, content, metadata=metadata)
            if turn and isinstance(turn, dict):
                logger.info(f"成功创建轮次: {turn.get('id', '')}")
                return turn
            else:
                logger.error("存储系统返回了无效的轮次数据")
                # 返回一个模拟轮次作为后备
                fallback_turn = {
                    'id': str(uuid.uuid4()),
                    'session_id': session_id,
                    'role': role,
                    'content': content,
                    'created_at': datetime.now().isoformat(),
                    'metadata': metadata or {}
                }
                logger.warning(f"使用后备轮次: {fallback_turn['id']}")
                return fallback_turn
        except Exception as e:
            logger.error(f"创建轮次失败: {e}")
            # 返回一个模拟轮次作为后备
            fallback_turn = {
                'id': str(uuid.uuid4()),
                'session_id': session_id,
                'role': role,
                'content': content,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {},
                'error': 'Database connection failed'
            }
            logger.warning(f"使用后备轮次（数据库错误）: {fallback_turn['id']}")
            return fallback_turn
    
    async def _process_by_dialogue_type(self,
                                      dialogue_type: str,
                                      session_id: str,
                                      user_id: str,
                                      content: str,
                                      turns: List[Dict[str, Any]],
                                      metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """根据对话类型处理输入
        
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
        
        # 根据对话类型处理
        if dialogue_type == DIALOGUE_TYPES["HUMAN_AI_PRIVATE"]:
            # 人类与AI私聊
            return await self._process_human_ai_private(session_id, user_id, content, turns, metadata)
        elif dialogue_type == DIALOGUE_TYPES["AI_SELF_REFLECTION"]:
            # AI自我反思
            return await self._process_ai_self_reflection(session_id, content, turns, metadata)
        elif dialogue_type in [DIALOGUE_TYPES["HUMAN_AI_GROUP"], DIALOGUE_TYPES["AI_MULTI_HUMAN"]]:
            # 群聊类型
            return await self._process_group_chat(dialogue_type, session_id, user_id, content, turns, metadata)
        elif dialogue_type == DIALOGUE_TYPES["AI_AI_DIALOGUE"]:
            # AI与AI对话
            return await self._process_ai_ai_dialogue(session_id, content, turns, metadata)
        else:
            # 其他类型暂不支持，返回默认响应
            logger.warning(f"不支持的对话类型: {dialogue_type}")
            return f"抱歉，当前不支持 {dialogue_type} 类型的对话处理。", response_metadata
    
    async def _process_human_ai_private(self,
                                      session_id: str,
                                      user_id: str,
                                      content: str,
                                      turns: List[Dict[str, Any]],
                                      metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """处理人类与AI私聊
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            content: 用户输入内容
            turns: 对话历史轮次
            metadata: 附加元数据
            
        Returns:
            (响应内容, 响应元数据)
        """
        try:
            # 使用上下文构建器构建上下文（如果可用）
            if self.context_builder:
                context = await self.context_builder.build_async(
                    user_input=content,
                    session_id=session_id,
                    user_id=user_id,
                    input_type=metadata.get("input_type", "text") if metadata else "text"
                )
                messages = context["messages"]
                
                # 记录频率信息（如果频率集成器可用）
                if self.frequency_integrator:
                    await self.frequency_integrator.record_interaction(
                        user_id=user_id,
                        session_id=session_id,
                        interaction_type="user_message",
                        content=content,
                        context=context
                    )
            else:
                # 如果上下文构建器不可用，则使用传统方法
                messages = self.ai_service.format_dialogue_history(turns)
                messages.append({"role": "user", "content": content})
            
            # 调用AI服务生成响应
            response = self.ai_service.generate_response(messages)
            
            # 构建响应元数据
            response_metadata = {
                "processed_at": datetime.now().isoformat(),
                "dialogue_type": DIALOGUE_TYPES["HUMAN_AI_PRIVATE"],
                "tools_used": [],
                "model": self.ai_service.model_name if hasattr(self.ai_service, "model_name") else "gpt-3.5-turbo"
            }
            
            # 如果频率集成器可用，添加频率相关元数据
            if self.frequency_integrator:
                frequency_data = await self.frequency_integrator.analyze_interaction(
                    user_id=user_id,
                    session_id=session_id
                )
                response_metadata["frequency_data"] = frequency_data
            
            return response, response_metadata
        except Exception as e:
            logger.error(f"AI服务生成响应失败: {e}")
            # 返回一个后备响应
            fallback_response = f"我是一个AI助手。由于技术原因，我现在无法提供智能回复，但我收到了您的消息: '{content}'"
            fallback_metadata = {
                "processed_at": datetime.now().isoformat(),
                "dialogue_type": DIALOGUE_TYPES["HUMAN_AI_PRIVATE"],
                "tools_used": [],
                "model": "fallback",
                "error": "AI service unavailable"
            }
            return fallback_response, fallback_metadata
    
    async def _process_ai_self_reflection(self,
                                        session_id: str,
                                        content: str,
                                        turns: List[Dict[str, Any]],
                                        metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """处理AI自我反思
        
        Args:
            session_id: 会话ID
            content: 输入内容
            turns: 对话历史轮次
            metadata: 附加元数据
            
        Returns:
            (响应内容, 响应元数据)
        """
        # 构建自我反思的系统提示
        reflection_messages = [
            {
                "role": "system",
                "content": "你正在进行自我反思。请分析你之前的回答，考虑其准确性、完整性和有用性，并提出改进建议。"
            }
        ]
        
        # 添加对话历史
        for turn in turns:
            role = turn.get("role", "")
            turn_content = turn.get("content", "")
            
            if role == "human":
                reflection_messages.append({"role": "user", "content": turn_content})
            elif role == "ai":
                reflection_messages.append({"role": "assistant", "content": turn_content})
        
        # 添加反思提示
        reflection_messages.append({
            "role": "user",
            "content": f"请对以上对话进行反思: {content}"
        })
        
        # 调用AI服务生成反思
        reflection = self.ai_service.generate_response(reflection_messages)
        
        # 构建响应元数据
        response_metadata = {
            "processed_at": datetime.now().isoformat(),
            "dialogue_type": DIALOGUE_TYPES["AI_SELF_REFLECTION"],
            "tools_used": [],
            "model": "gpt-3.5-turbo"  # 可以从配置中获取
        }
        
        return reflection, response_metadata
    
    async def _process_group_chat(self,
                                dialogue_type: str,
                                session_id: str,
                                user_id: str,
                                content: str,
                                turns: List[Dict[str, Any]],
                                metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """处理群聊对话
        
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
        # 获取会话信息，包括参与者
        session_info = await self.storage.get_session_async(session_id)
        participants = session_info.get("metadata", {}).get("participants", [])
        
        # 构建群聊系统提示
        if dialogue_type == DIALOGUE_TYPES["HUMAN_AI_GROUP"]:
            system_prompt = f"这是一个包含多个人类用户和AI的群聊。参与者包括: {', '.join(participants)}。请根据对话上下文和发言者的身份提供合适的回复。"
        else:  # AI_MULTI_HUMAN
            system_prompt = f"你是一个AI助手，正在与多个人类用户进行对话。参与者包括: {', '.join(participants)}。请根据对话上下文和发言者的身份提供合适的回复。"
        
        # 构建群聊消息
        group_messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # 添加对话历史，包含发言者信息
        for turn in turns:
            role = turn.get("role", "")
            turn_content = turn.get("content", "")
            turn_metadata = turn.get("metadata", {})
            speaker_id = turn_metadata.get("user_id", "unknown")
            
            if role == "human":
                # 在人类消息中添加发言者信息
                group_messages.append({
                    "role": "user", 
                    "content": f"[{speaker_id}]: {turn_content}"
                })
            elif role == "ai":
                group_messages.append({"role": "assistant", "content": turn_content})
        
        # 添加当前用户的消息
        group_messages.append({
            "role": "user",
            "content": f"[{user_id}]: {content}"
        })
        
        # 调用AI服务生成响应
        response = self.ai_service.generate_response(group_messages)
        
        # 构建响应元数据
        response_metadata = {
            "processed_at": datetime.now().isoformat(),
            "dialogue_type": dialogue_type,
            "tools_used": [],
            "model": "gpt-3.5-turbo",  # 可以从配置中获取
            "user_id": user_id  # 记录发言者ID
        }
        
        # 更新用户交互计数
        await self._update_user_interaction_count(user_id)
        
        return response, response_metadata
    
    async def _update_user_interaction_count(self, user_id: str) -> None:
        """更新用户交互计数
        
        Args:
            user_id: 用户ID
        """
        if self.frequency_integrator and self.memory:
            try:
                # 确保user_id是字符串类型
                if not isinstance(user_id, str):
                    user_id = str(user_id)
                    
                # 更新用户交互计数
                await self.frequency_integrator.update_interaction_count(user_id)
                logger.debug(f"已更新用户 {user_id} 的交互计数")
            except Exception as e:
                logger.error(f"更新用户交互计数失败: {e}")
        else:
            logger.debug("频率集成器或内存组件不可用，跳过更新用户交互计数")
    
    async def _process_ai_ai_dialogue(self,
                                    session_id: str,
                                    content: str,
                                    turns: List[Dict[str, Any]],
                                    metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """处理AI与AI对话
        
        Args:
            session_id: 会话ID
            content: 输入内容
            turns: 对话历史轮次
            metadata: 附加元数据
            
        Returns:
            (响应内容, 响应元数据)
        """
        # 获取AI角色信息
        ai_roles = metadata.get("ai_roles", ["助手A", "助手B"])
        current_ai = metadata.get("current_ai", ai_roles[0])
        next_ai = ai_roles[1] if current_ai == ai_roles[0] else ai_roles[0]
        
        # 构建AI对话系统提示
        system_prompt = f"这是一个AI之间的对话。你现在扮演{next_ai}，正在与{current_ai}进行对话。请根据对话上下文和你的角色提供合适的回复。"
        
        # 构建AI对话消息
        ai_dialogue_messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # 添加对话历史
        for turn in turns:
            role = turn.get("role", "")
            turn_content = turn.get("content", "")
            turn_metadata = turn.get("metadata", {})
            ai_role = turn_metadata.get("ai_role", ai_roles[0] if role == "ai" else "用户")
            
            # 将所有消息转换为user/assistant格式
            if len(ai_dialogue_messages) % 2 == 1:  # 奇数条消息，作为user
                ai_dialogue_messages.append({
                    "role": "user", 
                    "content": f"[{ai_role}]: {turn_content}"
                })
            else:  # 偶数条消息，作为assistant
                ai_dialogue_messages.append({
                    "role": "assistant", 
                    "content": f"[{ai_role}]: {turn_content}"
                })
        
        # 添加当前内容
        if len(ai_dialogue_messages) % 2 == 1:  # 奇数条消息，作为user
            ai_dialogue_messages.append({
                "role": "user", 
                "content": f"[{current_ai}]: {content}"
            })
        else:  # 偶数条消息，作为assistant
            ai_dialogue_messages.append({
                "role": "assistant", 
                "content": f"[{current_ai}]: {content}"
            })
        
        # 调用AI服务生成响应
        raw_response = self.ai_service.generate_response(ai_dialogue_messages)
        
        # 处理响应，移除可能的角色前缀
        response = raw_response
        for role in ai_roles:
            prefix = f"[{role}]: "
            if response.startswith(prefix):
                response = response[len(prefix):]
        
        # 构建响应元数据
        response_metadata = {
            "processed_at": datetime.now().isoformat(),
            "dialogue_type": DIALOGUE_TYPES["AI_AI_DIALOGUE"],
            "tools_used": [],
            "model": "gpt-3.5-turbo",  # 可以从配置中获取
            "ai_role": next_ai,
            "ai_roles": ai_roles,
            "current_ai": next_ai  # 更新当前AI角色
        }
        
        return response, response_metadata
