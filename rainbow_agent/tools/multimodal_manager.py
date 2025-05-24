"""
多模态工具管理系统

集成多模态支持、动态工具发现和工具版本管理功能
"""
from typing import Dict, Any, List, Optional, Union, Set, Type, Callable
import os
import json

from .base import BaseTool
from .multimodal_tool import MultiModalTool, ModalityType
from .tool_discovery import ToolRegistry, ToolDiscoveryService, get_tool_registry, initialize_tool_discovery
from .tool_versioning import VersionedTool, ToolVersionManager, VersionStatus, get_version_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MultiModalToolManager:
    """
    多模态工具管理器
    
    集成多模态支持、动态工具发现和工具版本管理功能
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MultiModalToolManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.tool_registry = get_tool_registry()
        self.version_manager = get_version_manager()
        self.discovery_service = None
        
        self._initialized = True
        logger.info("多模态工具管理器初始化完成")
    
    def initialize(self, discovery_paths: List[str] = None, auto_scan: bool = True) -> None:
        """
        初始化多模态工具管理系统
        
        Args:
            discovery_paths: 工具发现路径列表
            auto_scan: 是否自动扫描
        """
        # 初始化工具发现系统
        initialize_tool_discovery(discovery_paths, auto_scan)
        self.discovery_service = ToolDiscoveryService(registry=self.tool_registry, auto_scan=auto_scan)
        
        logger.info("多模态工具管理系统初始化完成")
    
    def register_tool(self, tool: Union[BaseTool, MultiModalTool, VersionedTool], 
                     provider: str = "core", 
                     version_status: VersionStatus = None,
                     set_as_default: bool = False) -> None:
        """
        注册工具
        
        Args:
            tool: 要注册的工具
            provider: 工具提供者
            version_status: 版本状态（仅适用于VersionedTool）
            set_as_default: 是否设为默认版本（仅适用于VersionedTool）
        """
        # 根据工具类型进行不同的注册
        if isinstance(tool, VersionedTool):
            # 注册到版本管理器
            self.version_manager.register_tool_version(
                tool, 
                status=version_status or VersionStatus.ACTIVE,
                set_as_default=set_as_default
            )
        else:
            # 注册到工具注册表
            self.tool_registry.register_tool(tool, provider)
    
    def get_tool(self, name: str, version: str = None) -> Optional[BaseTool]:
        """
        获取工具
        
        Args:
            name: 工具名称
            version: 版本号（如果适用）
            
        Returns:
            工具实例，如果不存在则返回None
        """
        # 首先尝试从版本管理器获取
        if version:
            tool = self.version_manager.get_tool_version(name, version)
            if tool:
                return tool
        
        # 然后从注册表获取
        return self.tool_registry.get_tool(name)
    
    def get_all_tools(self, include_versioned: bool = True) -> List[BaseTool]:
        """
        获取所有工具
        
        Args:
            include_versioned: 是否包括版本化工具
            
        Returns:
            工具列表
        """
        tools = self.tool_registry.get_all_tools()
        
        # 过滤掉版本化工具（如果需要）
        if not include_versioned:
            tools = [tool for tool in tools if not isinstance(tool, VersionedTool)]
        
        return tools
    
    def get_tools_by_modality(self, modality: ModalityType) -> List[MultiModalTool]:
        """
        获取支持指定模态的工具
        
        Args:
            modality: 模态类型
            
        Returns:
            工具列表
        """
        tools = []
        
        for tool in self.tool_registry.get_all_tools():
            if isinstance(tool, MultiModalTool) and modality in tool.supported_modalities:
                tools.append(tool)
        
        return tools
    
    def scan_for_tools(self) -> Dict[str, List[str]]:
        """
        扫描工具
        
        Returns:
            发现的工具，按提供者分组
        """
        if self.discovery_service:
            return self.discovery_service.manual_scan()
        return {}
    
    def format_tools_for_prompt(self, include_versioned: bool = True) -> str:
        """
        将工具格式化为提示词格式
        
        Args:
            include_versioned: 是否包括版本化工具
            
        Returns:
            工具描述字符串，可添加到提示中
        """
        tools = self.get_all_tools(include_versioned=include_versioned)
        
        if not tools:
            return ""
        
        tools_prompt = "你可以使用以下工具:\n\n"
        
        for tool in tools:
            if isinstance(tool, VersionedTool):
                tools_prompt += f"- {tool.name} (v{tool.version}): {tool.description}\n"
            else:
                tools_prompt += f"- {tool.name}: {tool.description}\n"
                
            tools_prompt += f"  用法: {tool.usage}\n"
            
            # 添加多模态支持信息
            if isinstance(tool, MultiModalTool):
                modalities = [m.value for m in tool.supported_modalities]
                tools_prompt += f"  支持的模态: {', '.join(modalities)}\n"
            
            # 添加版本信息
            if isinstance(tool, VersionedTool):
                if tool.deprecated:
                    status = "已弃用"
                    if tool.deprecation_message:
                        status += f" ({tool.deprecation_message})"
                else:
                    status = "活跃"
                tools_prompt += f"  版本状态: {status}\n"
            
            tools_prompt += "\n"
        
        tools_prompt += "如需调用工具，请使用以下格式: 工具名称(参数)"
        
        return tools_prompt
        
    def process_image(self, image_path_or_url: str) -> Dict[str, Any]:
        """
        处理图像输入
        
        Args:
            image_path_or_url: 图像路径或URL
            
        Returns:
            图像分析结果
        """
        # 获取支持图像处理的工具
        image_tools = self.get_tools_by_modality(ModalityType.IMAGE)
        
        if not image_tools:
            logger.warning("没有找到支持图像处理的工具")
            return {
                "success": False,
                "message": "没有找到支持图像处理的工具",
                "image_path": image_path_or_url
            }
        
        # 使用第一个可用的图像工具
        image_tool = image_tools[0]
        
        try:
            # 准备输入数据
            input_data = {
                "image": image_path_or_url,
                "modality": ModalityType.IMAGE.value
            }
            
            # 执行工具
            result = image_tool.run(input_data)
            
            # 尝试解析JSON结果
            try:
                if isinstance(result, str):
                    result_data = json.loads(result)
                else:
                    result_data = result
            except json.JSONDecodeError:
                result_data = {"description": result}
            
            return {
                "success": True,
                "result": result_data,
                "tool": image_tool.name,
                "image_path": image_path_or_url
            }
            
        except Exception as e:
            logger.error(f"处理图像时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "image_path": image_path_or_url
            }
    
    def process_audio(self, audio_path_or_url: str) -> Dict[str, Any]:
        """
        处理音频输入
        
        Args:
            audio_path_or_url: 音频路径或URL
            
        Returns:
            音频处理结果
        """
        # 获取支持音频处理的工具
        audio_tools = self.get_tools_by_modality(ModalityType.AUDIO)
        
        if not audio_tools:
            logger.warning("没有找到支持音频处理的工具")
            return {
                "success": False,
                "message": "没有找到支持音频处理的工具",
                "audio_path": audio_path_or_url
            }
        
        # 使用第一个可用的音频工具
        audio_tool = audio_tools[0]
        
        try:
            # 准备输入数据
            input_data = {
                "audio": audio_path_or_url,
                "modality": ModalityType.AUDIO.value
            }
            
            # 执行工具
            result = audio_tool.run(input_data)
            
            # 尝试解析JSON结果
            try:
                if isinstance(result, str):
                    result_data = json.loads(result)
                else:
                    result_data = result
            except json.JSONDecodeError:
                result_data = {"transcription": result}
            
            return {
                "success": True,
                "result": result_data,
                "tool": audio_tool.name,
                "audio_path": audio_path_or_url
            }
            
        except Exception as e:
            logger.error(f"处理音频时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_path": audio_path_or_url
            }


# 创建全局多模态工具管理器实例
global_multimodal_manager = MultiModalToolManager()


def get_multimodal_manager() -> MultiModalToolManager:
    """
    获取全局多模态工具管理器
    
    Returns:
        多模态工具管理器实例
    """
    return global_multimodal_manager
