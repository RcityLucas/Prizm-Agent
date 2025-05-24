# rainbow_agent/tools/tool_invoker.py
from typing import Dict, Any, List, Tuple, Optional, Union
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from .base import BaseTool
from .tool_executor import ToolExecutor
from .tool_chain import ToolChain, ConditionalToolChain, BranchingToolChain
from ..core.tool_selector import ToolSelector, SelectionStrategy
from ..utils.llm import get_llm_client
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ToolInvoker:
    """
    工具调用器，负责决策是否调用工具以及执行工具调用
    
    支持单个工具调用和工具链调用，提供缓存和组合能力
    """
    
    def __init__(
        self, 
        tools: List[BaseTool] = None,
        llm_client = None,
        decision_model: str = "gpt-3.5-turbo",
        timeout: int = 30,
        use_llm_for_decision: bool = True,
        use_cache: bool = True,
        cache_ttl: int = 3600,
        tool_selection_strategy: SelectionStrategy = SelectionStrategy.HYBRID,
        confidence_threshold: float = 0.6
    ):
        """
        初始化工具调用器
        
        Args:
            tools: 可用工具列表
            llm_client: LLM客户端，用于工具调用决策
            decision_model: 用于决策的模型
            timeout: 工具执行超时时间（秒）
            use_llm_for_decision: 是否使用LLM进行工具调用决策
            use_cache: 是否使用缓存
            cache_ttl: 缓存有效期（秒）
        """
        self.tools = tools or []
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.llm_client = llm_client or get_llm_client()
        self.decision_model = decision_model
        self.timeout = timeout
        self.use_llm_for_decision = use_llm_for_decision
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.confidence_threshold = confidence_threshold
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.tool_executor = ToolExecutor(self.tools)
        
        # 创建工具选择器
        self.tool_selector = ToolSelector(
            tools=self.tools,
            strategy=tool_selection_strategy,
            llm_client=self.llm_client,
            model=self.decision_model,
            confidence_threshold=self.confidence_threshold
        )
        
        # 工具链相关
        self.tool_chains = {}
        self.results_cache = {}  # 缓存结构: {cache_key: (result, timestamp)}
        
        logger.info(f"ToolInvoker初始化完成，加载了 {len(self.tools)} 个工具")
    
    def should_invoke_tool(self, user_input: str, context: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        判断是否应该调用工具
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            (是否调用工具, 工具调用信息)
        """
        # 如果没有工具，直接返回False
        if not self.tools:
            return False, None
        
        # 使用规则快速过滤
        if self._rule_based_filter(user_input):
            logger.info("基于规则判断不需要工具调用")
            return False, None
        
        # 检查是否有明确的工具调用格式
        tool_info = self.tool_executor.parse_tool_call(user_input)
        if tool_info:
            logger.info(f"从用户输入中检测到工具调用: {tool_info['tool_name']}")
            return True, tool_info
        
        # 使用工具选择器进行智能选择
        if self.use_llm_for_decision:
            try:
                # 使用工具选择器选择最合适的工具
                selected_tool, confidence, reason = self.tool_selector.select_tool(user_input, context)
                
                if selected_tool and confidence >= self.confidence_threshold:
                    logger.info(f"工具选择器选择了工具: {selected_tool.name}, 置信度: {confidence:.2f}")
                    
                    # 提取工具参数
                    tool_args = self._extract_args_for_tool(user_input, selected_tool.name)
                    
                    return True, {"tool_name": selected_tool.name, "tool_args": tool_args}
                else:
                    # 备选：使用传统LLM决策
                    decision = self._llm_tool_decision(user_input, context)
                    if decision["should_use_tool"]:
                        tool_name = decision["tool_name"]
                        tool_args = decision["tool_args"]
                        
                        # 验证工具是否存在
                        if tool_name in self.tools_by_name:
                            logger.info(f"LLM决策需要使用工具: {tool_name}")
                            return True, {"tool_name": tool_name, "tool_args": tool_args}
            except Exception as e:
                logger.error(f"工具选择错误: {e}")
                # 出错时尝试传统方法
                try:
                    decision = self._llm_tool_decision(user_input, context)
                    if decision["should_use_tool"]:
                        return True, {"tool_name": decision["tool_name"], "tool_args": decision["tool_args"]}
                except Exception as e2:
                    logger.error(f"备选LLM决策也失败: {e2}")
        
        logger.info("判断不需要工具调用")
        return False, None
    
    def invoke_tool(self, tool_info: Dict[str, Any]) -> str:
        """
        执行工具调用
        
        Args:
            tool_info: 工具调用信息
            
        Returns:
            工具执行结果
        """
        tool_name = tool_info["tool_name"]
        tool_args = tool_info["tool_args"]
        
        # 验证工具是否存在
        if tool_name not in self.tools_by_name:
            return f"错误: 找不到名为 '{tool_name}' 的工具"
            
        # 尝试从缓存获取结果
        cached_result = self._get_from_cache(tool_name, tool_args)
        if cached_result is not None:
            return cached_result
            
        tool = self.tools_by_name[tool_name]
        
        try:
            # 尝试执行工具，添加超时控制
            logger.info(f"开始执行工具 '{tool_name}'，参数: {tool_args}")
            future = self.executor.submit(tool.run, tool_args)
            result = future.result(timeout=self.timeout)
            logger.info(f"工具 '{tool_name}' 执行成功")
            
            # 缓存结果
            self._add_to_cache(tool_name, tool_args, result)
            
            return result
        except TimeoutError:
            error_msg = f"工具 '{tool_name}' 执行超时 (>{self.timeout}秒)"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"工具 '{tool_name}' 执行失败: {str(e)}"
            logger.error(f"工具 '{tool_name}' 执行错误: {e}")
            return error_msg
    
    def _rule_based_filter(self, user_input: str) -> bool:
        """使用规则快速过滤不需要工具的查询"""
        # 简单问候语不需要工具
        greeting_patterns = ["你好", "早上好", "晚上好", "谢谢", "感谢"]
        for pattern in greeting_patterns:
            if pattern in user_input.lower():
                return True
        
        # 非常短的输入可能不需要工具
        if len(user_input.strip()) < 5:
            return True
            
        return False
    
    def _llm_tool_decision(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM判断是否需要工具及使用哪个工具"""
        # 构建工具描述
        tools_description = self._format_tools_description()
        
        # 构建提示词
        prompt = f"""
        用户查询: {user_input}
        
        请判断是否需要使用工具来回答这个查询。如果需要，请指定使用哪个工具以及工具参数。
        
        可用工具:
        {tools_description}
        
        回答格式:
        {{
            "should_use_tool": true/false,
            "tool_name": "工具名称",
            "tool_args": "工具参数",
            "reasoning": "推理过程"
        }}
        
        只有当工具能明显帮助回答用户查询时才使用工具。
        """
        
        # 调用LLM
        response = self.llm_client.chat.completions.create(
            model=self.decision_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        # 解析响应
        try:
            content = response.choices[0].message.content
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group(0))
                return decision
        except Exception as e:
            logger.error(f"解析工具决策错误: {e}")
        
        # 默认不使用工具
        return {"should_use_tool": False, "reasoning": "无法解析决策"}
    
    def _format_tools_description(self) -> str:
        """格式化工具描述"""
        descriptions = []
        for tool in self.tools:
            descriptions.append(f"- {tool.name}: {tool.description}\n  用法: {tool.usage}")
        return "\n".join(descriptions)
        
    def _extract_args_for_tool(self, user_input: str, tool_name: str) -> Any:
        """
        从用户输入中提取工具参数
        
        Args:
            user_input: 用户输入
            tool_name: 工具名称
            
        Returns:
            提取的参数
        """
        # 尝试使用工具执行器解析
        tool_info = self.tool_executor.parse_tool_call(user_input)
        if tool_info and tool_info["tool_name"] == tool_name:
            return tool_info["tool_args"]
        
        # 使用LLM提取参数
        try:
            tool = self.tools_by_name.get(tool_name)
            if not tool:
                return ""
                
            prompt = f"""
            请从用户输入中提取使用"{tool_name}"工具所需的参数。
            
            工具描述: {tool.description}
            工具用法: {tool.usage}
            
            用户输入: {user_input}
            
            请提取出适合这个工具的参数，并以适当的格式返回（字符串或JSON）。
            如果无法提取参数，请返回空字符串。
            只返回参数，不要包含其他内容。
            """
            
            response = self.llm_client.chat.completions.create(
                model=self.decision_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            args = response.choices[0].message.content.strip()
            return args
        except Exception as e:
            logger.error(f"提取参数错误: {e}")
            return ""
    
    # 工具链相关方法
    def register_tool_chain(self, chain: Union[ToolChain, ConditionalToolChain, BranchingToolChain]) -> None:
        """
        注册工具链
        
        Args:
            chain: 要注册的工具链
        """
        self.tool_chains[chain.name] = chain
        logger.info(f"工具链 '{chain.name}' 已注册")
    
    def get_tool_chain(self, chain_name: str) -> Optional[Union[ToolChain, ConditionalToolChain, BranchingToolChain]]:
        """
        获取工具链
        
        Args:
            chain_name: 工具链名称
            
        Returns:
            工具链对象，如果不存在则返回None
        """
        return self.tool_chains.get(chain_name)
    
    def invoke_tool_chain(self, chain_name: str, input_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行工具链
        
        Args:
            chain_name: 工具链名称
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            工具链执行结果
        """
        chain = self.get_tool_chain(chain_name)
        if not chain:
            return {"error": f"找不到名为 '{chain_name}' 的工具链"}
        
        try:
            logger.info(f"开始执行工具链 '{chain_name}'")
            result = chain.execute(input_data, context or {})
            logger.info(f"工具链 '{chain_name}' 执行完成")
            return result
        except Exception as e:
            logger.error(f"工具链 '{chain_name}' 执行错误: {e}")
            return {"error": f"工具链 '{chain_name}' 执行失败: {str(e)}"}
    
    # 缓存相关方法
    def _generate_cache_key(self, tool_name: str, args: Any) -> str:
        """
        生成缓存键
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            
        Returns:
            缓存键
        """
        # 将参数转换为字符串并计算哈希值
        import hashlib
        args_str = str(args)
        return f"{tool_name}:{hashlib.md5(args_str.encode()).hexdigest()}"
    
    def _get_from_cache(self, tool_name: str, args: Any) -> Optional[str]:
        """
        从缓存中获取结果
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            
        Returns:
            缓存的结果，如果没有缓存或缓存过期则返回None
        """
        if not self.use_cache:
            return None
            
        cache_key = self._generate_cache_key(tool_name, args)
        if cache_key in self.results_cache:
            result, timestamp = self.results_cache[cache_key]
            # 检查缓存是否过期
            if time.time() - timestamp <= self.cache_ttl:
                logger.info(f"工具 '{tool_name}' 命中缓存")
                return result
            else:
                # 删除过期缓存
                del self.results_cache[cache_key]
                
        return None
    
    def _add_to_cache(self, tool_name: str, args: Any, result: str) -> None:
        """
        添加结果到缓存
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            result: 工具执行结果
        """
        if not self.use_cache:
            return
            
        cache_key = self._generate_cache_key(tool_name, args)
        self.results_cache[cache_key] = (result, time.time())
        logger.info(f"工具 '{tool_name}' 结果已缓存")