"""
文件操作工具
"""
import os
import json
from typing import Optional, Dict, Any
import time

from .base import BaseTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FileReadTool(BaseTool):
    """
    文件读取工具
    
    允许代理读取文件内容
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化文件读取工具
        
        Args:
            base_dir: 基础目录，限制文件访问范围
        """
        super().__init__(
            name="read_file",
            description="读取文件内容",
            usage="[文件路径]"
        )
        self.base_dir = base_dir
    
    def _normalize_path(self, path: str) -> str:
        """规范化并验证路径"""
        # 如果设置了基础目录，确保路径不会超出范围
        if self.base_dir:
            norm_path = os.path.normpath(os.path.join(self.base_dir, path))
            # 确保结果路径仍然在基础目录内
            if not norm_path.startswith(self.base_dir):
                raise ValueError(f"路径 '{path}' 超出了允许的范围")
            return norm_path
        else:
            return os.path.normpath(path)
    
    def run(self, args: str) -> str:
        """
        读取文件内容
        
        Args:
            args: 文件路径
            
        Returns:
            文件内容
        """
        try:
            file_path = args.strip()
            normalized_path = self._normalize_path(file_path)
            
            if not os.path.exists(normalized_path):
                return f"错误: 文件 '{file_path}' 不存在"
            
            if not os.path.isfile(normalized_path):
                return f"错误: '{file_path}' 不是一个文件"
            
            logger.info(f"读取文件: {normalized_path}")
            
            with open(normalized_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return f"文件 '{file_path}' 的内容:\n\n{content}"
        except Exception as e:
            logger.error(f"文件读取错误: {e}")
            return f"读取文件时出错: {str(e)}"


class FileWriteTool(BaseTool):
    """
    文件写入工具
    
    允许代理写入文件内容
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化文件写入工具
        
        Args:
            base_dir: 基础目录，限制文件访问范围
        """
        super().__init__(
            name="write_file",
            description="写入内容到文件",
            usage="[文件路径]|[文件内容]"
        )
        self.base_dir = base_dir
    
    def _normalize_path(self, path: str) -> str:
        """规范化并验证路径"""
        # 与FileReadTool中相同的实现
        if self.base_dir:
            norm_path = os.path.normpath(os.path.join(self.base_dir, path))
            if not norm_path.startswith(self.base_dir):
                raise ValueError(f"路径 '{path}' 超出了允许的范围")
            return norm_path
        else:
            return os.path.normpath(path)
    
    def run(self, args: str) -> str:
        """
        写入文件内容
        
        Args:
            args: 格式为 "文件路径|文件内容"
            
        Returns:
            操作结果
        """
        try:
            # 分割参数
            if "|" not in args:
                return "错误: 参数格式应为 '文件路径|文件内容'"
            
            file_path, content = args.split("|", 1)
            file_path = file_path.strip()
            
            normalized_path = self._normalize_path(file_path)
            
            # 确保目录存在
            dir_path = os.path.dirname(normalized_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            logger.info(f"写入文件: {normalized_path}")
            
            with open(normalized_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"成功写入文件: '{file_path}'"
        except Exception as e:
            logger.error(f"文件写入错误: {e}")
            return f"写入文件时出错: {str(e)}"
