"""
记忆管理器

整合和管理多种类型的记忆系统
"""
from typing import List, Dict, Any, Optional, Union
import time
import json

from .base import Memory
from .conversation import ConversationMemory
from .vector_store import VectorMemory
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """
    记忆管理器
    
    整合不同类型的记忆系统，提供统一的访问接口。
    支持多种记忆系统的注册、访问和管理。
    """
    
    _instance = None
    
    def __new__(cls):
        # 实现单例模式
        if cls._instance is None:
            cls._instance = super(MemoryManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化记忆管理器"""
        if not getattr(self, '_initialized', False):
            self.memory_systems: Dict[str, Memory] = {}
            self.default_system: Optional[str] = None
            self._initialized = True
            logger.info("初始化记忆管理器")
    
    def add_memory_system(self, name: str, memory_system: Memory, set_as_default: bool = False) -> None:
        """
        添加记忆系统
        
        Args:
            name: 记忆系统名称
            memory_system: 记忆系统实例
            set_as_default: 是否设置为默认系统
        """
        self.memory_systems[name] = memory_system
        logger.info(f"添加记忆系统: {name}")
        
        if set_as_default or self.default_system is None:
            self.default_system = name
            logger.info(f"设置默认记忆系统: {name}")
    
    def set_default_system(self, name: str) -> bool:
        """
        设置默认记忆系统
        
        Args:
            name: 记忆系统名称
            
        Returns:
            是否成功设置
        """
        if name in self.memory_systems:
            self.default_system = name
            logger.info(f"设置默认记忆系统: {name}")
            return True
        else:
            logger.warning(f"无法设置默认系统: {name} 不存在")
            return False
    
    def add(self, content: Any, metadata: Optional[Dict[str, Any]] = None, system_name: Optional[str] = None) -> str:
        """
        添加记忆
        
        Args:
            content: 记忆内容
            metadata: 记忆元数据
            system_name: 记忆系统名称，None表示使用默认系统
            
        Returns:
            记忆ID
        """
        system = self._get_system(system_name)
        return system.add(content, metadata)
    
    def get(self, memory_id: str, system_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取记忆
        
        Args:
            memory_id: 记忆ID
            system_name: 记忆系统名称，None表示使用默认系统
            
        Returns:
            记忆内容
        """
        system = self._get_system(system_name)
        return system.get(memory_id)
    
    def search(self, query: str, limit: int = 5, system_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        Args:
            query: 查询字符串
            limit: 返回结果数量限制
            system_name: 记忆系统名称，None表示使用默认系统
            
        Returns:
            相关记忆列表
        """
        system = self._get_system(system_name)
        return system.search(query, limit)
    
    def search_all(self, query: str, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        在所有记忆系统中搜索
        
        Args:
            query: 查询字符串
            limit: 每个系统返回结果的数量限制
            
        Returns:
            各系统的搜索结果
        """
        results = {}
        for name, system in self.memory_systems.items():
            results[name] = system.search(query, limit)
        return results
    
    def clear(self, system_name: Optional[str] = None) -> None:
        """
        清除记忆
        
        Args:
            system_name: 记忆系统名称，None表示清除所有系统
        """
        try:
            if system_name is None:
                # 清除所有系统
                for name, system in self.memory_systems.items():
                    system.clear()
                    logger.info(f"清除记忆系统: {name}")
                return
            
            # 清除指定系统
            system = self._get_system(system_name)
            system.clear()
            logger.info(f"清除记忆系统: {system_name}")
        except Exception as e:
            logger.error(f"清除记忆时出错: {e}")
    
    def _get_system(self, name: Optional[str] = None) -> Memory:
        """
        获取记忆系统实例
        
        Args:
            name: 系统名称，None表示使用默认系统
            
        Returns:
            记忆系统实例
            
        Raises:
            ValueError: 如果系统不存在
        """
        name = name or self.default_system
        
        if not name or name not in self.memory_systems:
            raise ValueError(f"记忆系统 '{name}' 不存在")
        
        return self.memory_systems[name]
    
    def start_new_conversation(self, system_message: Optional[str] = None, system_name: str = "conversation") -> str:
        """
        开始新的对话
        
        Args:
            system_message: 系统消息
            system_name: 记忆系统名称
            
        Returns:
            会话 ID
        """
        try:
            # 获取记忆系统并检查类型
            memory_system = self._get_conversation_system(system_name)
            
            # 开始新会话
            conversation_id = memory_system.start_new_conversation(system_message)
            logger.info(f"开始新会话: {conversation_id} (系统: {system_name})")
            return conversation_id
        except Exception as e:
            logger.error(f"开始新会话时出错: {e}")
            return ""
    
    def get_conversation_messages(self, include_system: bool = True, system_name: str = "conversation") -> List[Dict[str, str]]:
        """
        获取当前会话的消息
        
        Args:
            include_system: 是否包含系统消息
            system_name: 记忆系统名称
            
        Returns:
            消息列表
        """
        try:
            # 获取记忆系统并检查类型
            memory_system = self._get_conversation_system(system_name)
            
            # 获取当前会话
            conversation = memory_system.get_current_conversation()
            if not conversation:
                logger.info(f"没有找到当前会话 (系统: {system_name})")
                return []
                
            # 获取消息
            return conversation.get_messages(include_system)
        except Exception as e:
            logger.error(f"获取会话消息时出错: {e}")
            return []
    
    def generate_memory_summary(self) -> str:
        """
        生成记忆摘要
        
        Returns:
            记忆系统摘要
        """
        summary = []
        summary.append("## 记忆系统摘要")
        
        for name, system in self.memory_systems.items():
            is_default = "(默认)" if name == self.default_system else ""
            
            if isinstance(system, ConversationMemory):
                # 会话记忆摘要
                conversations = system.get_all_conversations()
                summary.append(f"\n### 会话记忆 {name} {is_default}")
                summary.append(f"- 总会话数: {len(conversations)}")
                
                if conversations:
                    summary.append("- 最近会话:")
                    # 按最后更新时间排序
                    recent = sorted(conversations, key=lambda x: x["last_updated"], reverse=True)[:3]
                    for conv in recent:
                        summary.append(f"  - {conv['summary']} (最后更新: {self._format_time(conv['last_updated'])})")
            
            elif isinstance(system, VectorMemory):
                # 向量记忆摘要
                summary.append(f"\n### 向量记忆 {name} {is_default}")
                summary.append(f"- 记忆数量: {len(system.memories)}")
                summary.append(f"- 容量: {system.capacity}")
                summary.append(f"- 向量模型: {'已加载' if system.model else '未加载'}")
            
            else:
                # 一般记忆摘要
                summary.append(f"\n### 记忆系统 {name} {is_default}")
                if hasattr(system, "memories"):
                    summary.append(f"- 记忆数量: {len(system.memories)}")
        
        return "\n".join(summary)
    
    def _get_conversation_system(self, system_name: str) -> ConversationMemory:
        """
        获取并检查会话记忆系统
        
        Args:
            system_name: 系统名称
            
        Returns:
            会话记忆系统
            
        Raises:
            ValueError: 如果系统不存在或不是会话系统
        """
        # 检查系统是否存在
        if system_name not in self.memory_systems:
            raise ValueError(f"记忆系统 {system_name} 不存在")
            
        # 检查是否为会话记忆系统
        memory_system = self.memory_systems[system_name]
        if not isinstance(memory_system, ConversationMemory):
            raise ValueError(f"记忆系统 {system_name} 不是会话记忆系统")
            
        return memory_system
    
    def _format_time(self, timestamp: float) -> str:
        """格式化时间戳"""
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(timestamp)  # 备用方案，如果时间戳格式有问题, time.localtime(timestamp)


class StandardMemoryManager(MemoryManager):
    """
    标准记忆管理器
    
    预配置了常用记忆系统的便捷记忆管理器。
    提供简洁易用的API用于管理会话和语义记忆。
    基于单例模式，确保全局唯一的记忆管理器。
    """
    
    def __init__(self, 
                 conversation_limit: int = 10,
                 enable_vector_memory: bool = True,
                 vector_model: str = "paraphrase-MiniLM-L6-v2",
                 save_path: Optional[str] = None):
        """
        初始化标准记忆管理器
        
        Args:
            conversation_limit: 会话记忆中的最大会话数
            enable_vector_memory: 是否启用向量记忆
            vector_model: 向量记忆的模型名称
            save_path: 向量记忆保存路径
        """
        super().__init__()
        
        # 添加会话记忆
        self.add_memory_system(
            "conversation", 
            ConversationMemory(max_conversations=conversation_limit),
            set_as_default=True
        )
        
        # 添加向量记忆（如果启用）
        if enable_vector_memory:
            vector_save_path = None
            if save_path:
                vector_save_path = f"{save_path}/vector_memory.pkl"
                
            self.add_memory_system(
                "semantic", 
                VectorMemory(
                    model_name=vector_model,
                    capacity=1000,
                    save_path=vector_save_path
                )
            )
    
    def add_user_message(self, content: str) -> None:
        """添加用户消息到会话"""
        self.add(("user", content), system_name="conversation")
    
    def add_assistant_message(self, content: str) -> None:
        """添加助手消息到会话"""
        self.add(("assistant", content), system_name="conversation")
    
    def add_system_message(self, content: str) -> None:
        """添加系统消息到会话"""
        self.add(("system", content), system_name="conversation")
    
    def add_semantic_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加语义记忆
        
        Args:
            content: 记忆内容
            metadata: 记忆元数据
            
        Returns:
            记忆ID
        """
        if "semantic" in self.memory_systems:
            return self.add(content, metadata, system_name="semantic")
        else:
            logger.warning("语义记忆系统未启用")
            return ""
    
    def search_semantic(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        语义搜索
        
        Args:
            query: 查询字符串
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        if "semantic" in self.memory_systems:
            return self.search(query, limit, system_name="semantic")
        else:
            logger.warning("语义记忆系统未启用")
            return []
    
    def get_context_for_prompt(self, query: str = "", include_conversation: bool = True) -> str:
        """
        获取用于提示的上下文
        
        Args:
            query: 当前查询，用于检索相关记忆
            include_conversation: 是否包含当前会话
            
        Returns:
            格式化的上下文字符串
        """
        context_parts = []
        
        # 添加当前会话上下文
        if include_conversation and "conversation" in self.memory_systems:
            memory_system = self.memory_systems["conversation"]
            if isinstance(memory_system, ConversationMemory):
                conversation = memory_system.get_current_conversation()
                if conversation:
                    recent_messages = conversation.get_recent_messages(10, include_system=False)
                    if recent_messages:
                        context_parts.append("## 当前会话")
                        for msg in recent_messages:
                            role = "用户" if msg["role"] == "user" else "助手"
                            context_parts.append(f"{role}: {msg['content']}")
                        context_parts.append("")
        
        # 添加语义相关记忆
        if query and "semantic" in self.memory_systems:
            relevant_memories = self.search(query, limit=3, system_name="semantic")
            if relevant_memories:
                context_parts.append("## 相关记忆")
                for i, memory in enumerate(relevant_memories, 1):
                    content = memory.get("content", "")
                    if isinstance(content, str):
                        # 如果内容太长，截断
                        if len(content) > 200:
                            content = content[:200] + "..."
                        context_parts.append(f"记忆 {i}: {content}")
                context_parts.append("")
        
        return "\n".join(context_parts)
