"""
Rainbow Agent 的核心代理类 - 重构版

基于新的组件架构，提供更灵活、可扩展的AI代理功能，包括流式输出、智能工具调用决策、上下文构建和响应处理。
"""
from typing import List, Dict, Any, Optional, Union
import time
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# 导入新组件
from .core.input_hub import InputHub
from .core.dialogue_core import DialogueCore
from .core.context_builder import ContextBuilder
from .core.llm_caller import LLMCaller
from .core.response_mixer import ResponseMixer

# 导入原有组件
from .memory.memory import Memory, SimpleMemory
from .tools.base import BaseTool
from .tools.tool_executor import ToolExecutor
from .tools.tool_invoker import ToolInvoker
from .utils.llm import get_llm_client
from .utils.logger import get_logger

logger = get_logger(__name__)

class RainbowAgent:
    """
    Rainbow Agent - 一个灵活的AI代理实现
    
    提供与大型语言模型交互、工具使用、记忆管理和流式输出的功能。
    支持同步和异步操作，以及超时控制和错误恢复。
    """
    
    def __init__(
        self,
        name: str = "Rainbow Agent",
        system_prompt: str = "你是一个智能AI助手，可以回答用户的各种问题。",
        tools: List[BaseTool] = None,
        memory: Optional[Memory] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tool_calls: int = 5,
        max_tokens: Optional[int] = None,
        timeout: int = 60,  # 超时时间（秒）
        stream: bool = False,  # 是否使用流式输出
        retry_attempts: int = 2,  # 失败重试次数
        session_id: str = None  # 会话ID，用于关联SurrealDB存储
    ):
        """
    初始化Rainbow Agent

    Args:
        name: 代理的名称
        system_prompt: 系统提示词，用于定义代理的行为和能力
        tools: 代理可以使用的工具列表
        memory: 代理的记忆系统
        model: 使用的LLM模型名称
        temperature: 生成温度，越低越确定性
        max_tool_calls: 单次响应中的最大工具调用次数
        max_tokens: 输出的最大token数量
        timeout: API调用超时时间（秒）
        stream: 是否使用流式输出
        retry_attempts: API调用失败时的重试次数
        session_id: 会话ID，用于关联SurrealDB存储
    """
        # 保存基本参数
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.memory = memory if memory else SimpleMemory()  # 默认使用简单记忆系统
        self.model = model
        self.temperature = temperature
        self.max_tool_calls = max_tool_calls
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.stream = stream
        self.retry_attempts = retry_attempts
        self.session_id = session_id  # 添加会话ID属性
        self.conversation_history = []
        
        # 初始化组件
        self.input_hub = InputHub()
        self.llm_caller = LLMCaller(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            retry_attempts=retry_attempts
        )
        
        # 保持向后兼容性
        self.llm_client = self.llm_caller.llm_client
        self.tool_executor = ToolExecutor(self.tools)
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.executor = ThreadPoolExecutor(max_workers=10)  # 用于并行执行工具
        
        # 初始化新组件
        self.tool_invoker = ToolInvoker(
            tools=self.tools,
            llm_client=self.llm_client,
            timeout=timeout
        )
        self.context_builder = ContextBuilder(self.memory)
        self.response_mixer = ResponseMixer()
        
        # 初始化对话核心
        self.dialogue_core = DialogueCore(
            memory=self.memory,
            tool_invoker=self.tool_invoker,
            llm_caller=self.llm_caller,
            context_builder=self.context_builder,
            response_mixer=self.response_mixer
        )
        
        # 保持向后兼容性 - 工具调用模式
        self.tool_patterns = [
            r'使用工具[:：]\s*(\w+)[:：]?\s*(.*)',  # 使用工具：name: args
            r'调用工具[:：]\s*(\w+)[:：]?\s*(.*)',  # 调用工具：name: args
            r'工具[:：]\s*(\w+)[:：]?\s*(.*)',      # 工具：name: args
            r'(\w+)\(([^)]*)\)',                  # name(args)
            r'\[工具:(\w+)\]\s*(.*)',             # [工具:name] args
        ]
        
        logger.info(f"Agent '{name}' initialized with model {model}")
    
    def add_tool(self, tool: BaseTool):
        """添加工具到代理"""
        self.tools.append(tool)
        self.tool_executor.add_tool(tool)
        self.tools_by_name[tool.name] = tool
        
        # 同时更新工具调用器
        self.tool_invoker.tools.append(tool)
        self.tool_invoker.tools_by_name[tool.name] = tool
        self.tool_invoker.tool_executor.add_tool(tool)
        
        logger.info(f"Tool '{tool.name}' added to agent '{self.name}'")
    
    def _format_tools_for_prompt(self) -> str:
        """将工具格式化为提示词格式"""
        if not self.tools:
            return ""
            
        tools_prompt = "你可以使用以下工具来帮助回答问题:\n\n"
        for tool in self.tools:
            tools_prompt += f"- {tool.name}: {tool.description}\n"
        
        tools_prompt += "\n使用工具的格式: 使用工具：[工具名称]：[工具参数]\n"
        tools_prompt += "例如: 使用工具：search：人工智能的历史\n"
        
        return tools_prompt
    
    def _build_prompt(self, user_input: str) -> List[Dict[str, str]]:
        """构建完整的提示词"""
        messages = []
        
        # 系统消息
        system_message = self.system_prompt
        if self.tools:
            system_message += "\n\n" + self._format_tools_for_prompt()
        
        messages.append({"role": "system", "content": system_message})
        
        # 添加记忆/历史
        relevant_memories = self.memory.retrieve(user_input)
        if relevant_memories:
            memory_prompt = "这是与当前查询相关的信息:\n\n" + "\n\n".join(relevant_memories)
            messages.append({"role": "system", "content": memory_prompt})
        
        # 添加对话历史 - 限制历史长度以避免超出上下文窗口
        max_history_items = 10  # 最多保留最近的5轮对话（10条消息）
        if len(self.conversation_history) > max_history_items:
            messages.extend(self.conversation_history[-max_history_items:])
        else:
            messages.extend(self.conversation_history)
        
        # 添加用户输入
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _should_use_tool(self, response: str) -> Optional[Dict[str, Any]]:
        """
        分析是否需要使用工具
        
        使用多种模式匹配响应中的工具调用
        """
        try:
            for pattern in self.tool_patterns:
                matches = re.findall(pattern, response)
                if matches:
                    for match in matches:
                        tool_name, tool_args = match
                        tool_name = tool_name.strip()
                        if tool_name in self.tools_by_name:
                            return {
                                "tool_name": tool_name,
                                "tool_args": tool_args.strip()
                            }
            
            # 如果没有匹配到预定义模式，尝试使用工具执行器的解析方法
            return self.tool_executor.parse_tool_call(response)
        except Exception as e:
            logger.error(f"Error parsing tool usage: {e}")
            return None
    
    def _execute_tool(self, tool_info: Dict[str, Any]) -> str:
        """执行工具并返回结果"""
        tool_name = tool_info["tool_name"]
        tool_args = tool_info["tool_args"]
        
        # 使用工具名称映射直接获取工具
        if tool_name not in self.tools_by_name:
            return f"错误: 找不到名为 '{tool_name}' 的工具"
            
        tool = self.tools_by_name[tool_name]
        
        try:
            # 尝试执行工具，添加超时控制
            future = self.executor.submit(tool.run, tool_args)
            result = future.result(timeout=self.timeout)
            return f"工具 '{tool_name}' 执行结果:\n{result}"
        except TimeoutError:
            logger.error(f"Tool '{tool_name}' execution timed out after {self.timeout}s")
            return f"工具 '{tool_name}' 执行超时 (>{self.timeout}秒)"
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution error: {e}")
            return f"工具 '{tool_name}' 执行失败: {str(e)}"
    
    def run(self, user_input: str, metadata: Optional[Dict[str, Any]] = None) -> Union[str, Dict[str, Any]]:
        """
        运行代理，处理用户输入并返回响应
        
        Args:
            user_input: 用户输入的文本
            metadata: 输入相关的元数据，如输入时间、用户ID等
            
        Returns:
            代理的响应（字符串或结构化对象）
        """
        start_time = time.time()
        
        # 使用新的组件架构处理请求
        try:
            # 1. 输入处理
            input_data = self.input_hub.process_input(user_input, metadata)
            
            # 2. 对话核心处理
            response_data = self.dialogue_core.process(input_data)
            
            # 记录对话历史（保持向后兼容性）
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response_data["final_response"]})
            
            elapsed_time = time.time() - start_time
            logger.info(f"代理 '{self.name}' 完成处理，用时 {elapsed_time:.2f}秒")
            
            # 构建向后兼容的响应格式
            if response_data.get("tool_results"):
                tool_results_compat = []
                for tool_result in response_data["tool_results"]:
                    tool_results_compat.append({
                        "tool": tool_result["tool_name"],
                        "args": tool_result["tool_args"],
                        "result": tool_result["result"]
                    })
                
                return {
                    "response": response_data["final_response"],
                    "tool_calls": len(tool_results_compat),
                    "tool_results": tool_results_compat,
                    "elapsed_time": elapsed_time
                }
            else:
                return response_data["final_response"]
                
        except Exception as e:
            logger.error(f"代理执行错误: {e}")
            
            # 尝试使用传统方法作为备份（向后兼容）
            try:
                return self._run_legacy(user_input)
            except Exception as backup_error:
                logger.error(f"备份方法也失败: {backup_error}")
                return f"发生错误: {str(e)}"
    
    def _run_legacy(self, user_input: str) -> Union[str, Dict[str, Any]]:
        """
        使用传统方法运行代理（向后兼容）
        
        Args:
            user_input: 用户输入的文本
            
        Returns:
            代理的响应（字符串或结构化对象）
        """
        start_time = time.time()
        # 构建提示词
        messages = self._build_prompt(user_input)
        
        # 跟踪工具调用次数和结果
        tool_calls_count = 0
        tool_results = []
        
        # 调用LLM
        for attempt in range(self.retry_attempts + 1):
            try:
                # 准备API调用参数
                completion_args = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": self.stream,
                }
                
                if self.max_tokens:
                    completion_args["max_tokens"] = self.max_tokens
                
                # 处理流式输出
                if self.stream:
                    # 流式处理逻辑
                    response_chunks = []
                    for chunk in self.llm_client.chat.completions.create(**completion_args):
                        if chunk.choices and chunk.choices[0].delta.content:
                            response_chunks.append(chunk.choices[0].delta.content)
                            # 这里可以添加回调函数来实时处理每个块
                    assistant_response = "".join(response_chunks)
                else:
                    # 非流式处理
                    response = self.llm_client.chat.completions.create(**completion_args)
                    assistant_response = response.choices[0].message.content
                
                # 记录对话
                self.conversation_history.append({"role": "user", "content": user_input})
                
                # 递归处理工具调用，直到没有更多工具调用或达到限制
                current_response = assistant_response
                while tool_calls_count < self.max_tool_calls:
                    # 检查是否需要使用工具
                    tool_info = self._should_use_tool(current_response)
                    if not tool_info:
                        break
                        
                    # 执行工具
                    tool_result = self._execute_tool(tool_info)
                    
                    # 记录工具调用和结果
                    tool_calls_count += 1
                    tool_results.append({
                        "tool": tool_info["tool_name"],
                        "args": tool_info["tool_args"],
                        "result": tool_result
                    })
                    
                    # 将工具结果添加到对话历史
                    self.conversation_history.append({"role": "system", "content": tool_result})
                    
                    # 构建新的提示以包含工具结果
                    follow_up_prompt = f"根据工具 '{tool_info['tool_name']}' 的结果，继续您的回答。结果如下:\n{tool_result}"
                    
                    # 获取更新的响应
                    updated_messages = messages.copy()
                    updated_messages.append({"role": "system", "content": tool_result})
                    updated_messages.append({"role": "user", "content": follow_up_prompt})
                    
                    try:
                        if self.stream:
                            # 流式处理
                            response_chunks = []
                            for chunk in self.llm_client.chat.completions.create(
                                model=self.model,
                                messages=updated_messages,
                                temperature=self.temperature,
                                stream=True
                            ):
                                if chunk.choices and chunk.choices[0].delta.content:
                                    response_chunks.append(chunk.choices[0].delta.content)
                            current_response = "".join(response_chunks)
                        else:
                            # 非流式处理
                            updated_response = self.llm_client.chat.completions.create(
                                model=self.model,
                                messages=updated_messages,
                                temperature=self.temperature,
                            )
                            current_response = updated_response.choices[0].message.content
                    except Exception as e:
                        logger.error(f"工具结果处理错误: {e}")
                        # 如果处理工具结果时出错，使用原始响应
                        break
                
                # 添加最终助手响应到对话历史
                self.conversation_history.append({"role": "assistant", "content": current_response})
                
                # 保存对话到记忆系统
                self.memory.save(user_input, current_response)
                
                elapsed_time = time.time() - start_time
                logger.info(f"代理 '{self.name}' 完成处理，用时 {elapsed_time:.2f}秒，工具调用次数: {tool_calls_count}")
                
                # 返回结构化响应
                if tool_results:
                    return {
                        "response": current_response,
                        "tool_calls": tool_calls_count,
                        "tool_results": tool_results,
                        "elapsed_time": elapsed_time
                    }
                else:
                    return current_response
                
            except Exception as e:
                logger.error(f"代理执行错误 (尝试 {attempt+1}/{self.retry_attempts+1}): {e}")
                if attempt < self.retry_attempts:
                    # 指数退避重试
                    retry_delay = 2 ** attempt
                    logger.info(f"将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    return f"发生错误: {str(e)}"