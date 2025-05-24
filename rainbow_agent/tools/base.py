"""
工具系统的基础定义
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseTool(ABC):
    """
    所有工具的基类
    
    所有工具必须继承此类并实现必要的方法
    """
    
    def __init__(self, name: str, description: str, usage: str = None, version: str = "1.0", author: str = "Rainbow Team", tags: list = None):
        """
        初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述，将显示在代理的提示中
            usage: 工具使用示例，帮助代理正确使用此工具
            version: 工具版本号
            author: 工具作者
            tags: 工具标签，用于分类和筛选
        """
        self.name = name
        self.description = description
        self.usage = usage or f"{name} <参数>"
        self.version = version
        self.author = author
        self.tags = tags or []
    
    @abstractmethod
    def run(self, args: Any) -> str:
        """
        执行工具逻辑
        
        Args:
            args: 工具参数，可以是字符串或解析后的对象
            
        Returns:
            工具执行的结果，字符串格式
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}\n用法: {self.usage}"
        
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema描述，用于与LLM集成
        
        Returns:
            工具描述的字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "parameters": {
                "type": "object",
                "properties": {
                    "args": {
                        "type": "string",
                        "description": f"参数，格式: {self.usage}"
                    }
                },
                "required": ["args"]
            }
        }
