"""
工具执行器 - 用于解析和执行工具调用

提供更强大的工具调用解析和执行能力，支持结构化工具调用
"""
import re
import json
from typing import List, Dict, Any, Optional, Tuple

from .base import BaseTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolExecutor:
    """工具执行器，处理工具调用的解析和执行"""
    
    def __init__(self, tools: List[BaseTool] = None):
        """
        初始化工具执行器
        
        Args:
            tools: 可用工具列表
        """
        self.tools = tools or []
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        logger.info(f"ToolExecutor initialized with {len(self.tools)} tools")
    
    def add_tool(self, tool: BaseTool) -> None:
        """
        添加工具
        
        Args:
            tool: 要添加的工具
        """
        self.tools.append(tool)
        self.tools_by_name[tool.name] = tool
        logger.info(f"Added tool: {tool.name}")
    
    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从文本中解析工具调用
        
        支持多种格式:
        1. 函数式格式: tool_name(arg1, arg2, ...)
        2. JSON格式: {"name": "tool_name", "args": {"arg1": value1, ...}}
        3. 简单文本格式: 使用工具：tool_name: arg1, arg2, ...
        4. 直接指示格式: 我需要使用工具：mock_tool 测试参数
        
        Args:
            text: 包含工具调用的文本
            
        Returns:
            解析后的工具调用信息，或None表示无工具调用
        """
        # 如果没有工具则直接返回
        if not self.tools_by_name:
            return None
            
        # 尝试按照优先级匹配所有工具名称
        for tool_name in self.tools_by_name.keys():
            # 用于直接引用工具的模式
            direct_patterns = [
                rf'我需要使用工具[:：]?\s*{tool_name}\s+(.*)',
                rf'使用工具[:：]?\s*{tool_name}\s+(.*)',
                rf'调用工具[:：]?\s*{tool_name}\s+(.*)',
                rf'工具\s*{tool_name}\s+(.*)',
                rf'[Uu]se\s+tool\s*[:：]?\s*{tool_name}\s+(.*)',
                rf'[Cc]all\s+tool\s*[:：]?\s*{tool_name}\s+(.*)'
            ]
            
            for pattern in direct_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return {
                        "tool_name": tool_name,
                        "tool_args": match.group(1).strip()
                    }
        
        # 尝试解析函数式格式
        func_pattern = r'(\w+)\s*\((.*?)\)'
        func_match = re.search(func_pattern, text)
        if func_match:
            tool_name = func_match.group(1)
            args_str = func_match.group(2)
            
            # 如果工具存在，返回解析结果
            if tool_name in self.tools_by_name:
                return {
                    "tool_name": tool_name,
                    "tool_args": args_str.strip()
                }
        
        # 尝试解析JSON格式
        try:
            # 查找可能的JSON片段
            json_pattern = r'\{[\s\S]*?\}'
            json_matches = re.finditer(json_pattern, text)
            
            for match in json_matches:
                try:
                    json_str = match.group(0)
                    tool_data = json.loads(json_str)
                    
                    if isinstance(tool_data, dict) and "name" in tool_data:
                        tool_name = tool_data["name"]
                        
                        if tool_name in self.tools_by_name:
                            # 提取参数
                            if "args" in tool_data and isinstance(tool_data["args"], dict):
                                # 将字典参数转换为适合工具使用的格式
                                args_str = json.dumps(tool_data["args"])
                            else:
                                args_str = ""
                                
                            return {
                                "tool_name": tool_name,
                                "tool_args": args_str
                            }
                except:
                    # 忽略JSON解析错误，继续查找可能的JSON
                    continue
        except:
            # 忽略整体JSON解析错误
            pass
            
        # 尝试解析简单文本格式
        simple_patterns = [
            r'使用工具[:：]\s*(\w+)[:：]\s*(.*)',
            r'调用工具[:：]\s*(\w+)[:：]\s*(.*)',
            r'工具调用[:：]\s*(\w+)[:：]\s*(.*)',
            r'[Uu]se tool:\s*(\w+)[:：]?\s*(.*)',
            r'[Cc]all tool:\s*(\w+)[:：]?\s*(.*)'
        ]
        
        for pattern in simple_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tool_name = match.group(1)
                args_str = match.group(2)
                
                if tool_name in self.tools_by_name:
                    return {
                        "tool_name": tool_name,
                        "tool_args": args_str.strip()
                    }
        
        # 未找到工具调用
        return None
    
    def execute_tool(self, tool_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        执行工具
        
        Args:
            tool_info: 工具调用信息，包含tool_name和tool_args
            
        Returns:
            (成功状态, 结果字符串)
        """
        tool_name = tool_info["tool_name"]
        tool_args = tool_info["tool_args"]
        
        if tool_name not in self.tools_by_name:
            return False, f"找不到名为 '{tool_name}' 的工具"
            
        tool = self.tools_by_name[tool_name]
        
        try:
            # 执行工具
            result = tool.run(tool_args)
            return True, result
        except Exception as e:
            logger.error(f"工具 '{tool_name}' 执行错误: {e}")
            return False, f"工具 '{tool_name}' 执行失败: {str(e)}"
            
    def format_tools_for_prompt(self) -> str:
        """
        将工具格式化为提示词格式
        
        Returns:
            工具描述字符串，可添加到提示中
        """
        if not self.tools:
            return ""
        
        tools_prompt = "你可以使用以下工具:\n\n"
        for tool in self.tools:
            tools_prompt += f"- {tool.name}: {tool.description}\n"
            tools_prompt += f"  用法: {tool.usage}\n\n"
        
        tools_prompt += "如需调用工具，请使用以下格式: 工具名称(参数)"
        
        return tools_prompt
