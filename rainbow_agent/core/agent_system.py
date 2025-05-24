"""
代理系统 - 集成工具链、ReAct代理和工具选择器

提供统一的接口，集成工具链、ReAct代理和工具选择器等功能，
为彩虹城AI Agent提供强大的代理能力。
"""
from typing import Dict, Any, List, Tuple, Optional, Union
import json
import time

from ..tools.tool_invoker import ToolInvoker
from ..tools.base import BaseTool
from ..tools.tool_chain import ToolChain, ConditionalToolChain, BranchingToolChain
from .react_agent import ReActAgent
from .tool_selector import ToolSelector, SelectionStrategy
from ..utils.llm import get_llm_client
from ..utils.logger import get_logger

logger = get_logger(__name__)

class AgentSystem:
    """
    代理系统，集成工具链、ReAct代理和工具选择器
    
    提供统一的接口，使彩虹城AI Agent能够使用这些增强功能
    """
    
    def __init__(
        self,
        tools: List[BaseTool] = None,
        llm_client = None,
        agent_model: str = "gpt-4",
        decision_model: str = "gpt-3.5-turbo",
        tool_selection_strategy: SelectionStrategy = SelectionStrategy.HYBRID,
        use_cache: bool = True,
        cache_ttl: int = 3600,
        max_iterations: int = 10,
        confidence_threshold: float = 0.6,
        verbose: bool = False
    ):
        """
        初始化代理系统
        
        Args:
            tools: 可用工具列表
            llm_client: LLM客户端
            agent_model: 代理使用的模型
            decision_model: 决策使用的模型
            tool_selection_strategy: 工具选择策略
            use_cache: 是否使用缓存
            cache_ttl: 缓存有效期（秒）
            max_iterations: 最大迭代次数
            confidence_threshold: 置信度阈值
            verbose: 是否输出详细日志
        """
        self.llm_client = llm_client or get_llm_client()
        
        # 创建工具调用器
        self.tool_invoker = ToolInvoker(
            tools=tools,
            llm_client=self.llm_client,
            decision_model=decision_model,
            use_llm_for_decision=True,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
            tool_selection_strategy=tool_selection_strategy,
            confidence_threshold=confidence_threshold
        )
        
        # 创建ReAct代理
        self.react_agent = ReActAgent(
            tool_invoker=self.tool_invoker,
            llm_client=self.llm_client,
            agent_model=agent_model,
            planning_model=agent_model,
            max_iterations=max_iterations,
            verbose=verbose
        )
        
        # 工具选择器直接使用工具调用器中的选择器
        self.tool_selector = self.tool_invoker.tool_selector
        
        # 其他属性
        self.verbose = verbose
        self.tools = tools or []
        
        logger.info("AgentSystem初始化完成")
    
    def add_tool(self, tool: BaseTool) -> None:
        """
        添加工具
        
        Args:
            tool: 要添加的工具
        """
        self.tools.append(tool)
        self.tool_invoker.tools.append(tool)
        self.tool_invoker.tools_by_name[tool.name] = tool
        self.tool_selector.add_tool(tool)
        
        logger.info(f"工具 '{tool.name}' 已添加到代理系统")
    
    def add_tools(self, tools: List[BaseTool]) -> None:
        """
        批量添加工具
        
        Args:
            tools: 要添加的工具列表
        """
        for tool in tools:
            self.add_tool(tool)
    
    def register_tool_chain(self, chain: Union[ToolChain, ConditionalToolChain, BranchingToolChain]) -> None:
        """
        注册工具链
        
        Args:
            chain: 要注册的工具链
        """
        self.tool_invoker.register_tool_chain(chain)
    
    def process_query(self, query: str, context: Dict[str, Any] = None, use_react: bool = True) -> Dict[str, Any]:
        """
        处理用户查询
        
        Args:
            query: 用户查询
            context: 上下文信息
            use_react: 是否使用ReAct代理，如果为False则使用普通工具调用
            
        Returns:
            处理结果
        """
        context = context or {}
        start_time = time.time()
        
        if use_react:
            # 使用ReAct代理处理查询
            logger.info(f"使用ReAct代理处理查询: {query}")
            result = self.react_agent.run(query, context)
            
            # 添加元数据
            result["processing_time"] = time.time() - start_time
            result["use_react"] = True
            
            return result
        else:
            # 使用普通工具调用
            logger.info(f"使用普通工具调用处理查询: {query}")
            
            # 判断是否需要调用工具
            should_use_tool, tool_info = self.tool_invoker.should_invoke_tool(query, context)
            
            if should_use_tool and tool_info:
                # 调用工具
                tool_name = tool_info["tool_name"]
                tool_result = self.tool_invoker.invoke_tool(tool_info)
                
                return {
                    "answer": tool_result,
                    "tool_used": tool_name,
                    "processing_time": time.time() - start_time,
                    "use_react": False
                }
            else:
                # 不需要工具，直接返回
                return {
                    "answer": "无需工具调用",
                    "tool_used": None,
                    "processing_time": time.time() - start_time,
                    "use_react": False
                }
    
    def select_best_tools(self, query: str, context: Dict[str, Any] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        选择最合适的工具
        
        Args:
            query: 用户查询
            context: 上下文信息
            top_k: 返回的工具数量
            
        Returns:
            工具信息列表，每个元素包含工具名称、描述、置信度和选择理由
        """
        context = context or {}
        
        # 使用工具选择器选择工具
        tool_results = self.tool_selector.select_tools(query, context, top_k)
        
        # 转换为易于使用的格式
        results = []
        for tool, confidence, reason in tool_results:
            results.append({
                "tool_name": tool.name,
                "description": tool.description,
                "usage": tool.usage,
                "confidence": confidence,
                "reason": reason
            })
        
        return results
    
    def needs_planning(self, query: str) -> bool:
        """
        判断查询是否需要多步规划
        
        Args:
            query: 用户查询
            
        Returns:
            是否需要规划
        """
        return self.react_agent._needs_planning(query)
    
    def create_plan(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        为查询创建多步规划
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            规划信息，包含目标和步骤
        """
        context = context or {}
        
        # 创建规划
        plan = self.react_agent._create_plan(query, context)
        
        return {
            "goal": plan.goal,
            "steps": plan.steps,
            "total_steps": len(plan.steps)
        }
