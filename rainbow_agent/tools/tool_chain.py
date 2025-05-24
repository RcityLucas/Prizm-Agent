"""
工具链 - 用于组合多个工具按顺序执行

借鉴LangChain的链式概念，允许多个工具按顺序或条件执行，
支持工具组合和结果缓存，提高工具调用的灵活性和效率。
"""
from typing import List, Dict, Any, Optional, Union, Callable
import json
import hashlib
import time
from .base import BaseTool
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ToolChain:
    """
    工具链，用于组合多个工具按顺序执行
    """
    
    def __init__(self, name: str, description: str, tools: List[BaseTool] = None, 
                 use_cache: bool = True, cache_ttl: int = 3600):
        """
        初始化工具链
        
        Args:
            name: 工具链名称
            description: 工具链描述
            tools: 工具链中的工具列表
            use_cache: 是否使用缓存
            cache_ttl: 缓存有效期（秒）
        """
        self.name = name
        self.description = description
        self.tools = tools or []
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.results_cache = {}  # 缓存结构: {cache_key: (result, timestamp)}
        
        logger.info(f"工具链 '{name}' 初始化完成，包含 {len(self.tools)} 个工具")
    
    def add_tool(self, tool: BaseTool) -> None:
        """
        添加工具到工具链
        
        Args:
            tool: 要添加的工具
        """
        self.tools.append(tool)
        logger.info(f"工具 '{tool.name}' 已添加到工具链 '{self.name}'")
    
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
    
    def execute(self, input_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行工具链
        
        Args:
            input_data: 输入数据，将作为第一个工具的输入
            context: 上下文信息，可用于条件执行
            
        Returns:
            工具链执行结果，包含每个工具的结果
        """
        if not self.tools:
            return {"error": "工具链为空"}
            
        results = []
        current_input = input_data
        context = context or {}
        
        try:
            for i, tool in enumerate(self.tools):
                logger.info(f"执行工具链 '{self.name}' 中的第 {i+1}/{len(self.tools)} 个工具: '{tool.name}'")
                
                # 尝试从缓存获取结果
                cached_result = self._get_from_cache(tool.name, current_input)
                if cached_result is not None:
                    result = cached_result
                else:
                    # 执行工具
                    result = tool.run(current_input)
                    # 缓存结果
                    self._add_to_cache(tool.name, current_input, result)
                
                # 记录结果
                results.append({
                    "tool_name": tool.name,
                    "input": current_input,
                    "output": result
                })
                
                # 更新输入为当前工具的输出
                current_input = result
            
            logger.info(f"工具链 '{self.name}' 执行完成")
            
            return {
                "chain_name": self.name,
                "final_result": current_input,
                "steps": results
            }
            
        except Exception as e:
            logger.error(f"工具链 '{self.name}' 执行错误: {e}")
            return {
                "chain_name": self.name,
                "error": str(e),
                "steps": results
            }

class ConditionalToolChain(ToolChain):
    """
    条件工具链，支持基于条件的工具执行
    """
    
    def __init__(self, name: str, description: str, 
                 condition_func: Callable[[Any, Dict[str, Any]], bool] = None, 
                 **kwargs):
        """
        初始化条件工具链
        
        Args:
            name: 工具链名称
            description: 工具链描述
            condition_func: 条件函数，决定是否执行工具链
            **kwargs: 传递给ToolChain的其他参数
        """
        super().__init__(name, description, **kwargs)
        self.condition_func = condition_func or (lambda input_data, context: True)
        
    def execute(self, input_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行条件工具链
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            工具链执行结果
        """
        context = context or {}
        
        # 检查条件
        if not self.condition_func(input_data, context):
            logger.info(f"条件工具链 '{self.name}' 条件不满足，跳过执行")
            return {
                "chain_name": self.name,
                "skipped": True,
                "reason": "条件不满足"
            }
        
        # 条件满足，执行工具链
        return super().execute(input_data, context)

class BranchingToolChain:
    """
    分支工具链，支持基于条件选择不同的执行路径
    """
    
    def __init__(self, name: str, description: str, 
                 branches: Dict[str, Dict[str, Any]] = None,
                 default_branch: str = None):
        """
        初始化分支工具链
        
        Args:
            name: 工具链名称
            description: 工具链描述
            branches: 分支配置，格式为 {分支名: {
                "condition": 条件函数,
                "chain": 工具链对象
            }}
            default_branch: 默认分支名称
        """
        self.name = name
        self.description = description
        self.branches = branches or {}
        self.default_branch = default_branch
        
        logger.info(f"分支工具链 '{name}' 初始化完成，包含 {len(self.branches)} 个分支")
    
    def add_branch(self, branch_name: str, condition: Callable[[Any, Dict[str, Any]], bool], 
                   chain: ToolChain) -> None:
        """
        添加分支
        
        Args:
            branch_name: 分支名称
            condition: 条件函数
            chain: 工具链对象
        """
        self.branches[branch_name] = {
            "condition": condition,
            "chain": chain
        }
        logger.info(f"分支 '{branch_name}' 已添加到分支工具链 '{self.name}'")
    
    def set_default_branch(self, branch_name: str) -> None:
        """
        设置默认分支
        
        Args:
            branch_name: 分支名称
        """
        if branch_name not in self.branches:
            raise ValueError(f"分支 '{branch_name}' 不存在")
            
        self.default_branch = branch_name
        logger.info(f"分支工具链 '{self.name}' 默认分支设置为 '{branch_name}'")
    
    def execute(self, input_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行分支工具链
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            选定分支的执行结果
        """
        context = context or {}
        
        # 查找满足条件的分支
        for branch_name, branch_config in self.branches.items():
            condition = branch_config["condition"]
            if condition(input_data, context):
                logger.info(f"分支工具链 '{self.name}' 选择分支 '{branch_name}'")
                chain = branch_config["chain"]
                result = chain.execute(input_data, context)
                return {
                    "chain_name": self.name,
                    "branch": branch_name,
                    "result": result
                }
        
        # 如果没有满足条件的分支，使用默认分支
        if self.default_branch and self.default_branch in self.branches:
            logger.info(f"分支工具链 '{self.name}' 使用默认分支 '{self.default_branch}'")
            chain = self.branches[self.default_branch]["chain"]
            result = chain.execute(input_data, context)
            return {
                "chain_name": self.name,
                "branch": self.default_branch,
                "result": result
            }
        
        # 没有满足条件的分支且没有默认分支
        logger.warning(f"分支工具链 '{self.name}' 没有满足条件的分支且没有默认分支")
        return {
            "chain_name": self.name,
            "error": "没有满足条件的分支且没有默认分支"
        }
