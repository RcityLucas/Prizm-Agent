"""
工具注册表 - 管理和自动加载所有可用工具

提供插件式的工具管理系统，允许动态注册和发现工具
"""
import os
import importlib
import inspect
from typing import Dict, List, Type, Any, Optional

from .base import BaseTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """
    工具注册表，管理可用工具
    
    提供工具的注册、发现和实例化功能。
    使用单例模式确保全局唯一的工具注册表。
    """
    
    _instance = None
    
    def __new__(cls):
        # 实现单例模式
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # 仅初始化一次
        if not getattr(self, '_initialized', False):
            # 存储工具类
            self.tool_classes: Dict[str, Type[BaseTool]] = {}
            # 存储工具实例
            self.available_tools: Dict[str, BaseTool] = {}
            # 存储分类信息
            self.categories: Dict[str, List[str]] = {}
            self._initialized = True
    
    def register(self, tool_class: Type[BaseTool]) -> None:
        """
        注册工具类
        
        Args:
            tool_class: 要注册的工具类
        """
        tool_name = tool_class.__name__
        self.tool_classes[tool_name] = tool_class
        logger.info(f"注册工具类: {tool_name}")
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        注册工具实例
        
        Args:
            tool: 要注册的工具实例
        """
        self.available_tools[tool.name] = tool
        logger.info(f"注册工具实例: {tool.name}")
    
    def get_tool_class(self, name: str) -> Optional[Type[BaseTool]]:
        """
        获取工具类
        
        Args:
            name: 工具类名
            
        Returns:
            工具类或None（如果不存在）
        """
        return self.tool_classes.get(name)
    
    def get_tool(self, name: str) -> BaseTool:
        """
        获取工具实例
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例
            
        Raises:
            KeyError: 如果工具不存在
        """
        if name not in self.available_tools:
            raise KeyError(f"工具 '{name}' 不存在")
        return self.available_tools[name]
        
    def list_tools(self) -> List[BaseTool]:
        """
        列出所有已注册的工具实例
        
        Returns:
            工具实例列表
        """
        return list(self.available_tools.values())
        
    def register_from_module(self, module_name: str) -> List[BaseTool]:
        """
        从模块中注册工具类
        
        Args:
            module_name: 模块名称
            
        Returns:
            注册的工具实例列表
        """
        registered_tools = []
        
        try:
            # 尝试导入指定模块
            logger.info(f"从模块 {module_name} 注册工具")
            
            try:
                # 先尝试作为完整的模块路径导入
                module = importlib.import_module(module_name)
            except ImportError:
                # 如果失败，尝试作为相对路径导入
                module = importlib.import_module(f"rainbow_agent.tools.{module_name}")
                
            # 查找模块中的工具类
            for item_name in dir(module):
                item = getattr(module, item_name)
                
                # 检查是否是BaseTool的子类，但不是BaseTool本身
                if (inspect.isclass(item) and 
                    issubclass(item, BaseTool) and 
                    item is not BaseTool):
                    
                    # 注册工具类
                    self.register(item)
                    
                    # 创建工具实例
                    try:
                        tool_instance = item()
                        self.register_tool(tool_instance)
                        registered_tools.append(tool_instance)
                    except Exception as e:
                        logger.error(f"创建工具实例 {item_name} 时出错: {e}")
                
            return registered_tools
            
        except Exception as e:
            logger.error(f"从模块注册工具时出错: {e}")
            return []
    
    def create_tool(self, class_name: str, **kwargs) -> Optional[BaseTool]:
        """
        创建工具实例
        
        Args:
            class_name: 工具类名
            **kwargs: 传递给工具构造函数的参数
            
        Returns:
            工具实例或None（如果创建失败）
        """
        tool_class = self.get_tool_class(class_name)
        if not tool_class:
            logger.warning(f"未找到工具类: {class_name}")
            return None
            
        try:
            return tool_class(**kwargs)
        except Exception as e:
            logger.error(f"创建工具 {class_name} 实例时出错: {e}")
            return None
    
    def get_available_tools(self) -> List[str]:
        """
        获取所有可用工具名称
        
        Returns:
            工具类名列表
        """
        return list(self.tool_classes.keys())
    
    def get_categories(self) -> Dict[str, List[str]]:
        """
        按类别分组获取工具
        
        Returns:
            类别到工具名称列表的映射
        """
        # 使用缓存的类别信息
        if not self.categories:
            for name, tool_class in self.tool_classes.items():
                category = getattr(tool_class, "category", "通用")
                
                if category not in self.categories:
                    self.categories[category] = []
                    
                self.categories[category].append(name)
                
        return self.categories
        
    def auto_discover(self, tools_path: Optional[str] = None) -> None:
        """
        自动发现并注册工具目录下的所有工具
        
        Args:
            tools_path: 工具模块路径，如果为None则使用当前目录
        """
        if tools_path is None:
            # 使用当前目录（工具目录）
            tools_path = os.path.dirname(os.path.abspath(__file__))
        
        # 扫描目录下的所有py文件和子目录
        self._discover_in_directory(tools_path)
        
        # 如果存在功能分类目录，分别扫描
        subdirs = ['file', 'web', 'data', 'code']
        for subdir in subdirs:
            subdir_path = os.path.join(tools_path, subdir)
            if os.path.isdir(subdir_path):
                self._discover_in_directory(subdir_path)
    
    def _discover_in_directory(self, directory_path: str) -> None:
        """在指定目录中发现工具"""
        # 扫描目录下的所有py文件
        try:
            for file_name in os.listdir(directory_path):
                # 跳过特殊文件和目录
                if (file_name.startswith("_") or 
                    file_name == "base.py" or 
                    file_name == "registry.py" or 
                    file_name == "executor.py" or
                    not file_name.endswith(".py")):
                    continue
                    
                module_name = file_name[:-3]  # 去掉.py后缀
                try:
                    # 确定模块路径
                    relative_path = os.path.relpath(directory_path, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    module_path = relative_path.replace(os.path.sep, '.') + '.' + module_name
                    module_path = module_path.lstrip('.')
                    
                    # 导入模块
                    module = importlib.import_module(module_path)
                    
                    # 查找模块中的工具类
                    for item_name in dir(module):
                        item = getattr(module, item_name)
                        
                        # 检查是否是BaseTool的子类，但不是BaseTool本身
                        if (inspect.isclass(item) and 
                            issubclass(item, BaseTool) and 
                            item is not BaseTool):
                            self.register(item)
                            
                except Exception as e:
                    logger.error(f"加载工具模块 {module_name} 时出错: {e}")
        except Exception as e:
            logger.error(f"扫描目录 {directory_path} 时出错: {e}")
    
    def __str__(self) -> str:
        """返回工具注册表的字符串表示"""
        categories = self.get_categories()
        result = ["可用工具:"]
        
        for category, tools in categories.items():
            result.append(f"\n[{category}]")
            for tool_name in tools:
                tool_class = self.tool_classes[tool_name]
                description = getattr(tool_class, "__doc__", "").strip() or "没有描述"
                result.append(f"  - {tool_name}: {description}")
                
        return "\n".join(result)


# 创建全局工具注册表实例
tool_registry = ToolRegistry()

# 延迟自动发现直到真正需要时，优化启动性能
def discover_tools():
    """延迟发现工具，仅在需要时执行"""
    if not getattr(tool_registry, '_discovered', False):
        tool_registry.auto_discover()
        setattr(tool_registry, '_discovered', True)
    return tool_registry
