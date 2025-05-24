# rainbow_agent/core/dialogue_core.py
from typing import Dict, Any, List, Optional
from ..utils.logger import get_logger
from ..memory.memory import Memory
from ..tools.tool_invoker import ToolInvoker
from .context_builder import ContextBuilder
from .llm_caller import LLMCaller
from .response_mixer import ResponseMixer

logger = get_logger(__name__)

class DialogueCore:
    """
    对话核心，协调各组件完成对话流程
    """
    
    def __init__(
        self, 
        memory: Memory,
        tool_invoker: ToolInvoker,
        llm_caller: LLMCaller,
        context_builder: Optional[ContextBuilder] = None,
        response_mixer: Optional[ResponseMixer] = None
    ):
        """
        初始化对话核心
        
        Args:
            memory: 记忆系统
            tool_invoker: 工具调用器
            llm_caller: LLM调用器
            context_builder: 上下文构建器，如果为None则创建默认实例
            response_mixer: 响应混合器，如果为None则创建默认实例
        """
        self.memory = memory
        self.tool_invoker = tool_invoker
        self.llm_caller = llm_caller
        self.context_builder = context_builder or ContextBuilder(memory)
        self.response_mixer = response_mixer or ResponseMixer()
        
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户输入，生成响应
        
        Args:
            input_data: 输入数据，由InputHub处理后的字典
            
        Returns:
            响应数据字典
        """
        user_input = input_data["processed_input"]
        input_type = input_data["type"]
        
        logger.info(f"开始处理对话，输入类型: {input_type}")
        
        # 1. 构建上下文
        context = self.context_builder.build(user_input, input_type)
        
        # 2. 判断是否需要工具调用
        tool_results = []
        should_use_tool, tool_info = self.tool_invoker.should_invoke_tool(user_input, context)
        
        # 3. 如果需要，执行工具调用
        if should_use_tool:
            logger.info(f"需要调用工具: {tool_info['tool_name']}")
            tool_result = self.tool_invoker.invoke_tool(tool_info)
            tool_results.append({
                "tool_name": tool_info["tool_name"],
                "tool_args": tool_info["tool_args"],
                "result": tool_result
            })
            
            # 4. 将工具结果添加到上下文
            context = self.context_builder.add_tool_result(context, tool_info, tool_result)
        
        # 5. 调用LLM获取响应
        llm_response = self.llm_caller.call(context)
        
        # 6. 组装最终响应
        final_response = self.response_mixer.mix(llm_response, tool_results)
        
        # 7. 记录对话
        self.memory.save(user_input, final_response)
        
        # 8. 构建响应数据
        response_data = {
            "raw_response": llm_response,
            "final_response": final_response,
            "tool_results": tool_results,
            "metadata": {
                "processing_time": self.llm_caller.last_processing_time,
                "token_usage": self.llm_caller.last_token_usage
            }
        }
        
        logger.info(f"对话处理完成，生成响应长度: {len(final_response)}")
        return response_data