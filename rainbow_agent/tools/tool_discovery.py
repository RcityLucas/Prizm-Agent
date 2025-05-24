"""
动态工具发现系统

提供运行时发现、加载和注册工具的功能
"""
import os
import sys
import importlib
import inspect
import pkgutil
import json
from typing import Dict, Any, List, Optional, Union, Set, Type, Callable
import time
import threading
import hashlib

from .base import BaseTool
from .multimodal_tool import MultiModalTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """
    工具注册表
    
    管理已注册的工具和工具提供者
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.tools: Dict[str, BaseTool] = {}  # 工具名称 -> 工具实例
        self.tool_classes: Dict[str, Type[BaseTool]] = {}  # 工具类名 -> 工具类
        self.providers: Dict[str, str] = {}  # 工具名称 -> 提供者
        self.discovery_paths: Set[str] = set()  # 工具发现路径
        self.discovery_lock = threading.Lock()  # 用于线程安全的发现过程
        
        self._initialized = True
        logger.info("工具注册表初始化完成")
    
    def register_tool(self, tool: BaseTool, provider: str = "core") -> None:
        """
        注册工具
        
        Args:
            tool: 要注册的工具
            provider: 工具提供者
        """
        if tool.name in self.tools:
            logger.warning(f"工具 '{tool.name}' 已存在，将被覆盖")
        
        self.tools[tool.name] = tool
        self.providers[tool.name] = provider
        logger.info(f"工具 '{tool.name}' 已注册 (提供者: {provider})")
    
    def register_tool_class(self, tool_class: Type[BaseTool], provider: str = "core") -> None:
        """
        注册工具类
        
        Args:
            tool_class: 要注册的工具类
            provider: 工具提供者
        """
        class_name = tool_class.__name__
        self.tool_classes[class_name] = tool_class
        logger.info(f"工具类 '{class_name}' 已注册 (提供者: {provider})")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，如果不存在则返回None
        """
        return self.tools.get(name)
    
    def get_tool_class(self, class_name: str) -> Optional[Type[BaseTool]]:
        """
        获取工具类
        
        Args:
            class_name: 工具类名
            
        Returns:
            工具类，如果不存在则返回None
        """
        return self.tool_classes.get(class_name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        获取所有工具
        
        Returns:
            工具列表
        """
        return list(self.tools.values())
    
    def get_tools_by_provider(self, provider: str) -> List[BaseTool]:
        """
        获取指定提供者的工具
        
        Args:
            provider: 工具提供者
            
        Returns:
            工具列表
        """
        return [tool for name, tool in self.tools.items() if self.providers.get(name) == provider]
    
    def add_discovery_path(self, path: str) -> None:
        """
        添加工具发现路径
        
        Args:
            path: 要添加的路径
        """
        if os.path.isdir(path):
            self.discovery_paths.add(path)
            logger.info(f"已添加工具发现路径: {path}")
        else:
            logger.warning(f"路径不存在或不是目录: {path}")
    
    def discover_tools(self, auto_register: bool = True) -> Dict[str, List[str]]:
        """
        发现工具
        
        Args:
            auto_register: 是否自动注册发现的工具
            
        Returns:
            发现的工具，按提供者分组
        """
        with self.discovery_lock:
            discovered = {}
            
            for path in self.discovery_paths:
                if not os.path.exists(path):
                    continue
                
                # 确保路径在Python路径中
                if path not in sys.path:
                    sys.path.append(path)
                
                # 遍历目录
                for root, dirs, files in os.walk(path):
                    # 跳过__pycache__目录
                    if "__pycache__" in root:
                        continue
                    
                    # 检查Python文件
                    for file in files:
                        if file.endswith(".py") and not file.startswith("__"):
                            file_path = os.path.join(root, file)
                            provider = os.path.relpath(root, path).replace(os.sep, ".")
                            
                            # 加载模块
                            try:
                                module_name = file[:-3]  # 去掉.py后缀
                                module_path = f"{provider}.{module_name}" if provider != "." else module_name
                                
                                # 动态导入模块
                                spec = importlib.util.spec_from_file_location(module_path, file_path)
                                if spec:
                                    module = importlib.util.module_from_spec(spec)
                                    spec.loader.exec_module(module)
                                    
                                    # 查找模块中的工具类
                                    tool_classes = []
                                    for name, obj in inspect.getmembers(module):
                                        if (inspect.isclass(obj) and 
                                            issubclass(obj, BaseTool) and 
                                            obj != BaseTool and 
                                            obj != MultiModalTool):
                                            tool_classes.append(obj)
                                    
                                    if tool_classes:
                                        if provider not in discovered:
                                            discovered[provider] = []
                                        
                                        for tool_class in tool_classes:
                                            discovered[provider].append(tool_class.__name__)
                                            
                                            # 自动注册
                                            if auto_register:
                                                self.register_tool_class(tool_class, provider)
                                                
                                                # 如果工具类可以实例化，也注册实例
                                                try:
                                                    tool_instance = tool_class()
                                                    self.register_tool(tool_instance, provider)
                                                except Exception as e:
                                                    logger.warning(f"无法实例化工具类 {tool_class.__name__}: {e}")
                            except Exception as e:
                                logger.error(f"加载模块 {file_path} 时出错: {e}")
            
            return discovered
    
    def reload_tools(self) -> Dict[str, List[str]]:
        """
        重新加载工具
        
        Returns:
            重新加载的工具，按提供者分组
        """
        # 清空现有工具
        self.tools = {}
        self.tool_classes = {}
        self.providers = {}
        
        # 重新发现工具
        return self.discover_tools(auto_register=True)


class ToolDiscoveryService:
    """
    工具发现服务
    
    提供定期扫描和动态加载工具的功能
    """
    
    def __init__(
        self, 
        registry: ToolRegistry = None,
        scan_interval: int = 300,  # 默认5分钟扫描一次
        auto_scan: bool = True
    ):
        """
        初始化工具发现服务
        
        Args:
            registry: 工具注册表
            scan_interval: 扫描间隔（秒）
            auto_scan: 是否自动扫描
        """
        self.registry = registry or ToolRegistry()
        self.scan_interval = scan_interval
        self.auto_scan = auto_scan
        self.scanning = False
        self.scan_thread = None
        self.last_scan_time = 0
        self.file_hashes = {}  # 文件路径 -> 哈希值
        
        logger.info("工具发现服务初始化完成")
    
    def start(self) -> None:
        """启动工具发现服务"""
        if self.scanning:
            logger.warning("工具发现服务已在运行")
            return
        
        self.scanning = True
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        logger.info("工具发现服务已启动")
    
    def stop(self) -> None:
        """停止工具发现服务"""
        self.scanning = False
        if self.scan_thread:
            self.scan_thread.join(timeout=1.0)
        logger.info("工具发现服务已停止")
    
    def _scan_loop(self) -> None:
        """扫描循环"""
        while self.scanning:
            try:
                self.scan_for_changes()
            except Exception as e:
                logger.error(f"工具扫描错误: {e}")
            
            # 等待下一次扫描
            for _ in range(self.scan_interval):
                if not self.scanning:
                    break
                time.sleep(1)
    
    def scan_for_changes(self) -> Dict[str, List[str]]:
        """
        扫描工具变化
        
        Returns:
            变化的工具，按提供者分组
        """
        self.last_scan_time = time.time()
        changed_files = self._check_file_changes()
        
        if changed_files:
            logger.info(f"检测到 {len(changed_files)} 个工具文件变化，重新加载工具")
            return self.registry.reload_tools()
        
        return {}
    
    def _check_file_changes(self) -> List[str]:
        """
        检查文件变化
        
        Returns:
            变化的文件列表
        """
        changed_files = []
        
        for path in self.registry.discovery_paths:
            if not os.path.exists(path):
                continue
            
            for root, _, files in os.walk(path):
                # 跳过__pycache__目录
                if "__pycache__" in root:
                    continue
                
                # 检查Python文件
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        file_path = os.path.join(root, file)
                        
                        # 计算文件哈希
                        try:
                            current_hash = self._calculate_file_hash(file_path)
                            
                            # 检查是否变化
                            if file_path in self.file_hashes:
                                if self.file_hashes[file_path] != current_hash:
                                    changed_files.append(file_path)
                                    self.file_hashes[file_path] = current_hash
                            else:
                                self.file_hashes[file_path] = current_hash
                        except Exception as e:
                            logger.error(f"计算文件哈希时出错: {e}")
        
        return changed_files
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件哈希值
        """
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    
    def add_discovery_path(self, path: str) -> None:
        """
        添加工具发现路径
        
        Args:
            path: 要添加的路径
        """
        self.registry.add_discovery_path(path)
    
    def manual_scan(self) -> Dict[str, List[str]]:
        """
        手动扫描工具
        
        Returns:
            发现的工具，按提供者分组
        """
        self.last_scan_time = time.time()
        return self.registry.discover_tools(auto_register=True)


# 创建全局工具注册表和发现服务实例
global_tool_registry = ToolRegistry()
global_discovery_service = ToolDiscoveryService(registry=global_tool_registry, auto_scan=False)


def initialize_tool_discovery(discovery_paths: List[str] = None, auto_scan: bool = True) -> None:
    """
    初始化工具发现系统
    
    Args:
        discovery_paths: 工具发现路径列表
        auto_scan: 是否自动扫描
    """
    # 添加发现路径
    if discovery_paths:
        for path in discovery_paths:
            global_tool_registry.add_discovery_path(path)
    
    # 默认添加内置工具路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    global_tool_registry.add_discovery_path(current_dir)
    
    # 初始扫描
    global_discovery_service.manual_scan()
    
    # 启动自动扫描
    if auto_scan:
        global_discovery_service.auto_scan = True
        global_discovery_service.start()
    
    logger.info("工具发现系统初始化完成")


def get_tool_registry() -> ToolRegistry:
    """
    获取全局工具注册表
    
    Returns:
        工具注册表实例
    """
    return global_tool_registry


def get_discovery_service() -> ToolDiscoveryService:
    """
    获取全局工具发现服务
    
    Returns:
        工具发现服务实例
    """
    return global_discovery_service
