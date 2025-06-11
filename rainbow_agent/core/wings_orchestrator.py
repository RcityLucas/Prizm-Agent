# rainbow_agent/core/wings_orchestrator.py
from typing import Dict, Any, Optional, List
import asyncio
from ..utils.logger import get_logger
from ..memory.memory import Memory
from ..memory.surreal_memory_adapter import SurrealMemoryAdapter
from ..storage.surreal.surreal_memory import SurrealMemory
from ..storage.surreal.storage_factory import StorageFactory
from ..tools.tool_invoker import ToolInvoker
from ..tools.tool_executor import ToolExecutor
from ..tools.registry import ToolRegistry
from .input_hub import InputHub
from .dialogue_core import DialogueCore
from .context_builder import ContextBuilder
from .llm_caller import LLMCaller
from .response_mixer import ResponseMixer

logger = get_logger(__name__)

class WingsOrchestrator:
    """
    系统协调器，负责协调各组件的工作流程
    """
    
    def __init__(
        self,
        storage_factory: Optional[StorageFactory] = None,
        model: str = "gpt-3.5-turbo",
        max_context_items: int = 10,
        session_id: Optional[str] = None
    ):
        """
        初始化系统协调器
        
        Args:
            storage_factory: 存储工厂，如果为None则创建默认实例
            model: 使用的LLM模型名称
            max_context_items: 上下文中包含的最大记忆项数量
            session_id: 会话ID，如果为None则使用默认会话
        """
        self.session_id = session_id or "default_session"
        self.storage_factory = storage_factory or StorageFactory()
        
        # 初始化组件
        self._initialize_components(model, max_context_items)
        
        logger.info(f"WingsOrchestrator初始化完成，会话ID: {self.session_id}")
    
    def _initialize_components(self, model: str, max_context_items: int):
        """初始化系统组件"""
        # 1. 初始化记忆系统
        surreal_memory = SurrealMemory(self.storage_factory)
        self.memory = SurrealMemoryAdapter(surreal_memory, self.session_id)
        
        # 2. 初始化工具系统
        tool_registry = ToolRegistry()
        tool_executor = ToolExecutor(tool_registry)
        self.tool_invoker = ToolInvoker(tool_executor)
        
        # 3. 初始化LLM调用器
        self.llm_caller = LLMCaller(model=model)
        
        # 4. 初始化上下文构建器
        self.context_builder = ContextBuilder(self.memory, max_context_items)
        
        # 5. 初始化响应混合器
        self.response_mixer = ResponseMixer()
        
        # 6. 初始化输入处理中心
        self.input_hub = InputHub()
        
        # 7. 初始化对话核心
        self.dialogue_core = DialogueCore(
            memory=self.memory,
            tool_invoker=self.tool_invoker,
            llm_caller=self.llm_caller,
            context_builder=self.context_builder,
            response_mixer=self.response_mixer
        )
    
    async def process_message(self, user_input: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理用户消息
        
        Args:
            user_input: 用户输入文本
            metadata: 输入相关的元数据
            
        Returns:
            处理结果字典
        """
        # 1. 输入处理
        input_data = self.input_hub.process_input(user_input, metadata)
        
        # 2. 对话处理
        response_data = self.dialogue_core.process(input_data)
        
        # 3. 添加会话信息
        response_data["session_id"] = self.session_id
        
        return response_data
    
    async def clear_session(self):
        """清除当前会话的记忆"""
        await self.memory.clear()
        logger.info(f"已清除会话 {self.session_id} 的记忆")
    
    async def get_session_history(self) -> List[Dict[str, Any]]:
        """获取当前会话的历史记录"""
        # 这里需要调用SurrealMemory的方法获取历史记录
        # 由于SurrealMemoryAdapter没有直接暴露这个功能，我们可以通过其他方式实现
        # 这里仅作为示例，实际实现可能需要根据SurrealMemory的API进行调整
        history = await self.memory.retrieve("", limit=100)  # 获取所有记忆
        return history
