"""
工具版本管理系统

提供工具版本控制、兼容性检查和版本迁移功能
"""
from typing import Dict, Any, List, Optional, Union, Tuple, Set, Callable
import re
import json
import time
import semver
from datetime import datetime
from enum import Enum

from .base import BaseTool
from .tool_discovery import ToolRegistry, get_tool_registry
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VersionedTool(BaseTool):
    """
    带版本控制的工具基类
    
    支持版本号、兼容性检查和版本迁移
    """
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        usage: str = None,
        version: str = "1.0.0",
        min_compatible_version: str = "1.0.0",
        deprecated: bool = False,
        deprecation_message: str = None
    ):
        """
        初始化带版本控制的工具
        
        Args:
            name: 工具名称
            description: 工具描述
            usage: 工具使用示例
            version: 工具版本号 (遵循语义化版本规范)
            min_compatible_version: 最低兼容版本
            deprecated: 是否已弃用
            deprecation_message: 弃用消息
        """
        super().__init__(name, description, usage)
        
        # 验证版本号格式
        try:
            semver.VersionInfo.parse(version)
            semver.VersionInfo.parse(min_compatible_version)
        except ValueError as e:
            logger.warning(f"工具 {name} 的版本号格式无效: {e}，将使用默认版本号 1.0.0")
            version = "1.0.0"
            min_compatible_version = "1.0.0"
        
        self.version = version
        self.min_compatible_version = min_compatible_version
        self.deprecated = deprecated
        self.deprecation_message = deprecation_message
        self.created_at = datetime.now().isoformat()
    
    def run(self, args: Any) -> str:
        """
        执行工具逻辑
        
        Args:
            args: 工具参数
            
        Returns:
            工具执行的结果
        """
        # 检查是否已弃用
        if self.deprecated:
            warning = f"警告：工具 {self.name} (v{self.version}) 已弃用"
            if self.deprecation_message:
                warning += f"。{self.deprecation_message}"
            logger.warning(warning)
        
        # 执行实际工具逻辑
        return self._run_versioned(args)
    
    def _run_versioned(self, args: Any) -> str:
        """
        执行带版本控制的工具逻辑
        
        Args:
            args: 工具参数
            
        Returns:
            工具执行的结果
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def is_compatible_with(self, other_version: str) -> bool:
        """
        检查是否与指定版本兼容
        
        Args:
            other_version: 要检查的版本号
            
        Returns:
            是否兼容
        """
        try:
            return semver.VersionInfo.parse(other_version) >= semver.VersionInfo.parse(self.min_compatible_version)
        except ValueError:
            return False
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema描述，包含版本信息
        
        Returns:
            工具描述的字典
        """
        schema = super().get_schema()
        
        # 添加版本信息
        schema["version"] = self.version
        schema["min_compatible_version"] = self.min_compatible_version
        
        if self.deprecated:
            schema["deprecated"] = True
            if self.deprecation_message:
                schema["deprecation_message"] = self.deprecation_message
        
        return schema


class VersionStatus(Enum):
    """工具版本状态枚举"""
    ACTIVE = "active"  # 活跃版本
    DEPRECATED = "deprecated"  # 已弃用版本
    EXPERIMENTAL = "experimental"  # 实验性版本
    STABLE = "stable"  # 稳定版本
    LEGACY = "legacy"  # 遗留版本


class ToolVersionManager:
    """
    工具版本管理器
    
    管理工具的不同版本，提供版本选择和兼容性检查
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolVersionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.tool_versions: Dict[str, Dict[str, VersionedTool]] = {}  # 工具名称 -> {版本号 -> 工具实例}
        self.default_versions: Dict[str, str] = {}  # 工具名称 -> 默认版本号
        self.version_status: Dict[str, Dict[str, VersionStatus]] = {}  # 工具名称 -> {版本号 -> 状态}
        self.registry = get_tool_registry()
        
        self._initialized = True
        logger.info("工具版本管理器初始化完成")
    
    def register_tool_version(
        self, 
        tool: VersionedTool, 
        status: VersionStatus = VersionStatus.ACTIVE,
        set_as_default: bool = False
    ) -> None:
        """
        注册工具版本
        
        Args:
            tool: 要注册的工具
            status: 版本状态
            set_as_default: 是否设为默认版本
        """
        tool_name = tool.name
        version = tool.version
        
        # 初始化工具版本字典
        if tool_name not in self.tool_versions:
            self.tool_versions[tool_name] = {}
            self.version_status[tool_name] = {}
        
        # 注册工具版本
        self.tool_versions[tool_name][version] = tool
        self.version_status[tool_name][version] = status
        
        # 设置默认版本
        if set_as_default or tool_name not in self.default_versions:
            self.default_versions[tool_name] = version
        
        # 同时注册到工具注册表
        self.registry.register_tool(tool, provider=f"versioned-{version}")
        
        logger.info(f"工具 {tool_name} 版本 {version} 已注册，状态: {status.value}")
    
    def get_tool_version(self, tool_name: str, version: str = None) -> Optional[VersionedTool]:
        """
        获取指定版本的工具
        
        Args:
            tool_name: 工具名称
            version: 版本号，如果为None则返回默认版本
            
        Returns:
            工具实例，如果不存在则返回None
        """
        if tool_name not in self.tool_versions:
            return None
        
        # 如果未指定版本，使用默认版本
        if version is None:
            version = self.default_versions.get(tool_name)
            if version is None:
                return None
        
        return self.tool_versions[tool_name].get(version)
    
    def set_default_version(self, tool_name: str, version: str) -> bool:
        """
        设置工具的默认版本
        
        Args:
            tool_name: 工具名称
            version: 版本号
            
        Returns:
            是否设置成功
        """
        if tool_name not in self.tool_versions or version not in self.tool_versions[tool_name]:
            return False
        
        self.default_versions[tool_name] = version
        logger.info(f"工具 {tool_name} 的默认版本已设置为 {version}")
        return True
    
    def get_all_versions(self, tool_name: str) -> List[str]:
        """
        获取工具的所有版本
        
        Args:
            tool_name: 工具名称
            
        Returns:
            版本号列表，按版本号排序
        """
        if tool_name not in self.tool_versions:
            return []
        
        versions = list(self.tool_versions[tool_name].keys())
        # 按语义化版本排序
        versions.sort(key=lambda v: semver.VersionInfo.parse(v))
        return versions
    
    def get_latest_version(self, tool_name: str, include_experimental: bool = False) -> Optional[str]:
        """
        获取工具的最新版本
        
        Args:
            tool_name: 工具名称
            include_experimental: 是否包括实验性版本
            
        Returns:
            最新版本号，如果不存在则返回None
        """
        if tool_name not in self.tool_versions:
            return None
        
        versions = self.get_all_versions(tool_name)
        if not versions:
            return None
        
        # 过滤掉实验性版本（如果需要）
        if not include_experimental:
            versions = [v for v in versions if self.version_status[tool_name].get(v) != VersionStatus.EXPERIMENTAL]
            if not versions:
                return None
        
        # 返回最新版本
        return versions[-1]
    
    def deprecate_version(self, tool_name: str, version: str, message: str = None) -> bool:
        """
        将工具版本标记为已弃用
        
        Args:
            tool_name: 工具名称
            version: 版本号
            message: 弃用消息
            
        Returns:
            是否标记成功
        """
        if tool_name not in self.tool_versions or version not in self.tool_versions[tool_name]:
            return False
        
        # 更新状态
        self.version_status[tool_name][version] = VersionStatus.DEPRECATED
        
        # 更新工具实例
        tool = self.tool_versions[tool_name][version]
        tool.deprecated = True
        tool.deprecation_message = message
        
        # 如果是默认版本，尝试更新为最新的非弃用版本
        if self.default_versions.get(tool_name) == version:
            active_versions = [v for v in self.get_all_versions(tool_name) 
                              if self.version_status[tool_name].get(v) != VersionStatus.DEPRECATED]
            if active_versions:
                self.default_versions[tool_name] = active_versions[-1]
        
        logger.info(f"工具 {tool_name} 版本 {version} 已标记为弃用")
        return True
    
    def find_compatible_version(self, tool_name: str, target_version: str) -> Optional[str]:
        """
        查找与目标版本兼容的版本
        
        Args:
            tool_name: 工具名称
            target_version: 目标版本号
            
        Returns:
            兼容的版本号，如果不存在则返回None
        """
        if tool_name not in self.tool_versions:
            return None
        
        # 首先检查是否有完全匹配的版本
        if target_version in self.tool_versions[tool_name]:
            return target_version
        
        # 查找兼容版本
        compatible_versions = []
        for version, tool in self.tool_versions[tool_name].items():
            if tool.is_compatible_with(target_version):
                compatible_versions.append(version)
        
        if not compatible_versions:
            return None
        
        # 按版本号排序，返回最新的兼容版本
        compatible_versions.sort(key=lambda v: semver.parse(v))
        return compatible_versions[-1]
    
    def migrate_args(self, tool_name: str, from_version: str, to_version: str, args: Any) -> Any:
        """
        迁移工具参数
        
        Args:
            tool_name: 工具名称
            from_version: 源版本号
            to_version: 目标版本号
            args: 工具参数
            
        Returns:
            迁移后的参数
        """
        if (tool_name not in self.tool_versions or 
            from_version not in self.tool_versions[tool_name] or 
            to_version not in self.tool_versions[tool_name]):
            return args
        
        # 获取工具实例
        from_tool = self.tool_versions[tool_name][from_version]
        to_tool = self.tool_versions[tool_name][to_version]
        
        # 如果工具实现了迁移方法，使用它
        if hasattr(to_tool, "migrate_args_from"):
            try:
                return to_tool.migrate_args_from(from_version, args)
            except Exception as e:
                logger.error(f"参数迁移失败: {e}")
        
        # 默认不做任何迁移
        return args


# 创建全局工具版本管理器实例
global_version_manager = ToolVersionManager()


def get_version_manager() -> ToolVersionManager:
    """
    获取全局工具版本管理器
    
    Returns:
        工具版本管理器实例
    """
    return global_version_manager


class CalculatorToolV1(VersionedTool):
    """
    计算器工具 v1.0.0
    
    执行基本数学计算
    """
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行基本数学计算",
            usage="calculator(表达式)",
            version="1.0.0",
            min_compatible_version="1.0.0"
        )
    
    def _run_versioned(self, args: Any) -> str:
        """执行计算"""
        try:
            # 安全的eval实现
            result = eval(str(args), {"__builtins__": {}}, {"abs": abs, "round": round})
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"


class CalculatorToolV2(VersionedTool):
    """
    计算器工具 v2.0.0
    
    执行高级数学计算，支持更多函数
    """
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行高级数学计算，支持更多函数",
            usage="calculator({\"expression\": \"表达式\", \"precision\": 精度})",
            version="2.0.0",
            min_compatible_version="1.0.0"  # 向后兼容v1
        )
    
    def _run_versioned(self, args: Any) -> str:
        """执行计算"""
        # 解析参数
        if isinstance(args, dict):
            expression = args.get("expression", "")
            precision = args.get("precision", 2)
        else:
            expression = str(args)
            precision = 2
        
        try:
            # 导入数学函数
            import math
            
            # 创建安全的执行环境
            safe_dict = {
                "abs": abs, "round": round,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "sqrt": math.sqrt, "pow": math.pow, "log": math.log,
                "pi": math.pi, "e": math.e
            }
            
            # 执行计算
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            # 格式化结果
            if isinstance(result, (int, float)):
                result = round(result, precision)
            
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    def migrate_args_from(self, from_version: str, args: Any) -> Any:
        """
        从旧版本迁移参数
        
        Args:
            from_version: 源版本号
            args: 工具参数
            
        Returns:
            迁移后的参数
        """
        # 如果是v1版本，将字符串参数转换为字典格式
        if from_version.startswith("1."):
            if isinstance(args, str):
                return {"expression": args, "precision": 2}
        
        return args
