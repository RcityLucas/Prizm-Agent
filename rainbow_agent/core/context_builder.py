# rainbow_agent/core/context_builder.py
from typing import Dict, Any, List, Optional, Tuple, Union
import asyncio
import json
import numpy as np
from datetime import datetime

from ..memory.memory import Memory
from ..memory.surreal_memory import SurrealMemory
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ContextBuilder:
    """
    上下文构建器，负责构建LLM所需的上下文
    """
    
    def __init__(self, memory: Memory, max_context_items: int = 10, max_history_turns: int = 10, 
                 use_vector_search: bool = False, vector_weight: float = 0.7):
        """
        初始化上下文构建器
        
        Args:
            memory: 记忆管理器
            max_context_items: 最大上下文项数量
            max_history_turns: 最大历史轮次数量
            use_vector_search: 是否使用向量检索
            vector_weight: 向量相似度的权重 (0-1)，越高越重视向量相似度
        """
        self.memory = memory
        self.max_context_items = max_context_items
        self.max_history_turns = max_history_turns
        self.use_vector_search = use_vector_search
        self.vector_weight = vector_weight
        
        # 向量化模型
        self.embedding_model = None
        
    async def build_async(self, user_input: str, session_id: str, user_id: str, 
                         input_type: str = "text", query_vector: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        异步构建上下文
        
        Args:
            user_input: 用户输入
            session_id: 会话ID
            user_id: 用户ID
            input_type: 输入类型
            query_vector: 可选的查询向量，如果提供则使用向量检索
            
        Returns:
            构建好的上下文字典
        """
        # 并行获取相关记忆、对话历史和用户信息
        tasks = [
            self._get_relevant_memories_async(user_input, query_vector),
            self._get_conversation_history_async(session_id),
            self._get_user_info_async(user_id)
        ]
        
        results = await asyncio.gather(*tasks)
        relevant_memories, conversation_history, user_info = results
        
        # 确定关系阶段
        relationship_stage = self._determine_relationship_stage(user_info)
        
        # 构建上下文字典
        context = {
            "user_input": user_input,
            "input_type": input_type,
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "relevant_memories": relevant_memories,
            "conversation_history": conversation_history,
            "user_info": user_info,
            "relationship_stage": relationship_stage,
            "messages": self._format_as_messages(user_input, relevant_memories, conversation_history, user_info, relationship_stage)
        }
        
        logger.info(f"上下文构建完成，包含 {len(relevant_memories)} 条相关记忆，{len(conversation_history)} 轮对话历史")
        return context
        
    def build(self, user_input: str, input_type: str = "text", query_vector: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        构建上下文（同步版本，向后兼容）
        
        Args:
            user_input: 用户输入
            input_type: 输入类型
            query_vector: 可选的查询向量，如果提供则使用向量检索
            
        Returns:
            构建好的上下文字典
        """
        # 获取相关记忆 (同步方式)
        if self.use_vector_search and query_vector:
            if hasattr(self.memory, 'retrieve_hybrid'):
                formatted_memories = self.memory.retrieve_hybrid(user_input, query_vector, 
                                                              limit=self.max_context_items, 
                                                              vector_weight=self.vector_weight)
            elif hasattr(self.memory, 'retrieve_by_vector'):
                formatted_memories = self.memory.retrieve_by_vector(query_vector, limit=self.max_context_items)
            else:
                formatted_memories = self.memory.retrieve(user_input, limit=self.max_context_items)
        else:
            formatted_memories = self.memory.retrieve(user_input, limit=self.max_context_items)
        
        # 构建上下文字典
        context = {
            "user_input": user_input,
            "input_type": input_type,
            "relevant_memories": formatted_memories,
            "messages": self._format_as_messages(user_input, formatted_memories)
        }
        
        logger.info(f"上下文构建完成，包含 {len(formatted_memories)} 条相关记忆")
        return context
    
    def add_tool_result(self, context: Dict[str, Any], tool_info: Dict[str, Any], tool_result: str) -> Dict[str, Any]:
        """
        将工具结果添加到上下文
        
        Args:
            context: 原始上下文
            tool_info: 工具信息
            tool_result: 工具执行结果
            
        Returns:
            更新后的上下文
        """
        # 创建工具结果消息
        tool_message = {
            "role": "system",
            "content": f"工具 '{tool_info['tool_name']}' 执行结果:\n{tool_result}"
        }
        
        # 更新消息列表
        updated_messages = context["messages"].copy()
        updated_messages.append(tool_message)
        
        # 创建新的上下文
        updated_context = context.copy()
        updated_context["messages"] = updated_messages
        updated_context["tool_results"] = context.get("tool_results", []) + [{
            "tool_name": tool_info["tool_name"],
            "tool_args": tool_info["tool_args"],
            "result": tool_result
        }]
        
        logger.info(f"上下文更新，添加了工具 '{tool_info['tool_name']}' 的结果")
        return updated_context
    
    async def _get_relevant_memories_async(self, user_input: str, query_vector: Optional[List[float]] = None) -> List[str]:
        """
        异步获取相关记忆
        
        Args:
            user_input: 用户输入
            query_vector: 可选的查询向量，如果提供则使用向量检索
            
        Returns:
            相关记忆列表
        """
        try:
            # 检查是否支持异步检索
            if hasattr(self.memory, 'retrieve_async'):
                # 使用异步方法检索相关记忆
                formatted_memories = await self.memory.retrieve_async(user_input, limit=self.max_context_items)
            else:
                # 如果不支持异步，则使用同步方法在异步上下文中执行
                loop = asyncio.get_event_loop()
                formatted_memories = await loop.run_in_executor(
                    None, 
                    lambda: self.memory.retrieve(user_input, limit=self.max_context_items)
                )
            
            logger.info(f"检索到 {len(formatted_memories)} 条相关记忆")
            return formatted_memories
        except Exception as e:
            logger.error(f"获取相关记忆失败: {e}")
            return []
    
    async def _get_conversation_history_async(self, session_id: str) -> List[Dict[str, Any]]:
        """
        异步获取对话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            对话历史列表
        """
        try:
            if hasattr(self.memory, 'get_conversation_history_async'):
                return await self.memory.get_conversation_history_async(session_id, limit=self.max_history_turns)
            elif hasattr(self.memory, 'get_turns_async'):
                return await self.memory.get_turns_async(session_id, limit=self.max_history_turns)
            else:
                # 如果没有异步方法，返回空列表
                logger.warning("记忆系统不支持获取对话历史")
                return []
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []
    
    async def _get_user_info_async(self, user_id: str) -> Dict[str, Any]:
        """
        异步获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典
        """
        try:
            # 创建记忆查询对象，使用过滤器查找用户信息
            query = LangMemMemoryQuery(
                content=f"user_info:{user_id}",
                filters={
                    "memory_type": "user_profile",
                    "user_id": user_id
                }
            )
            
            # 使用LangMem的记忆管理器检索用户信息
            retrieved_memories = await self.memory.retrieve_memories(query, limit=1)
            
            if retrieved_memories and len(retrieved_memories) > 0:
                # 如果找到用户信息，解析并返回
                user_memory = retrieved_memories[0].memory
                if user_memory.metadata and 'user_info' in user_memory.metadata:
                    return user_memory.metadata['user_info']
                elif user_memory.content:
                    # 尝试解析内容为JSON
                    try:
                        return json.loads(user_memory.content)
                    except:
                        pass
            
            # 返回默认用户信息
            return {
                "id": user_id,
                "name": "用户",
                "interaction_count": 0,
                "preferences": {},
                "first_interaction": datetime.now().isoformat(),
                "last_interaction": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return {
                "id": user_id,
                "name": "用户",
                "interaction_count": 0,
                "preferences": {}
            }
    
    def _determine_relationship_stage(self, user_info: Dict[str, Any]) -> str:
        """
        根据用户信息确定关系阶段
        
        Args:
            user_info: 用户信息
            
        Returns:
            关系阶段
        """
        interaction_count = user_info.get("interaction_count", 0)
        
        if interaction_count <= 5:
            return "initial"
        elif interaction_count <= 20:
            return "developing"
        elif interaction_count <= 50:
            return "established"
        else:
            return "close"
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        获取文本的向量表示
        
        Args:
            text: 输入文本
            
        Returns:
            文本的向量表示，如果模型未加载则返回None
        """
        try:
            if self.embedding_model is None:
                # 延迟加载向量化模型
                try:
                    from sentence_transformers import SentenceTransformer
                    self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                    logger.info("向量化模型加载成功")
                except ImportError:
                    logger.warning("无法加载 sentence_transformers 库，请安装: pip install sentence-transformers")
                    return None
                except Exception as e:
                    logger.error(f"加载向量化模型失败: {e}")
                    return None
            
            # 生成向量表示
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"生成文本向量表示失败: {e}")
            return None
    
    def _format_as_messages(self, user_input: str, memories: List[str], 
                           conversation_history: List[Dict[str, Any]] = None,
                           user_info: Dict[str, Any] = None,
                           relationship_stage: str = None) -> List[Dict[str, str]]:
        """
        将上下文格式化为消息列表，适用于LLM API
        
        Args:
            user_input: 用户输入
            memories: 相关记忆
            conversation_history: 对话历史
            user_info: 用户信息
            relationship_stage: 关系阶段
            
        Returns:
            消息列表
        """
        messages = []
        
        # 添加系统消息
        system_content = "你是Rainbow Agent，一个智能助手。请根据提供的上下文和用户输入提供有帮助的回答。"
        
        # 添加用户信息和关系阶段
        if user_info and relationship_stage:
            user_name = user_info.get("name", "用户")
            interaction_count = user_info.get("interaction_count", 0)
            system_content += f"\n\n当前用户: {user_name}\n互动次数: {interaction_count}\n关系阶段: {relationship_stage}"
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # 添加记忆相关信息
        if memories:
            memory_content = "以下是与当前查询相关的信息:\n\n" + "\n\n".join(memories)
            messages.append({
                "role": "system",
                "content": memory_content
            })
        
        # 添加对话历史
        if conversation_history:
            for turn in conversation_history:
                role = "assistant" if turn.get("role") == "ai" else "user"
                content = turn.get("content", "")
                if content:  # 只添加非空消息
                    messages.append({"role": role, "content": content})
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        return messages