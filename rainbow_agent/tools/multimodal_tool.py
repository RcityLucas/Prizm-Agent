"""
多模态工具支持

提供处理图像、音频等多模态输入的工具基类和实用函数
"""
from typing import Dict, Any, List, Optional, Union, Tuple
import base64
import os
import mimetypes
import json
from abc import abstractmethod
from enum import Enum

from .base import BaseTool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ModalityType(Enum):
    """模态类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    MIXED = "mixed"


class MultiModalTool(BaseTool):
    """
    多模态工具基类
    
    支持处理文本、图像、音频等多种模态的输入
    """
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        usage: str = None,
        supported_modalities: List[ModalityType] = None
    ):
        """
        初始化多模态工具
        
        Args:
            name: 工具名称
            description: 工具描述
            usage: 工具使用示例
            supported_modalities: 支持的模态类型列表，默认仅支持文本
        """
        super().__init__(name, description, usage)
        self.supported_modalities = supported_modalities or [ModalityType.TEXT]
        
    def run(self, args: Any) -> str:
        """
        执行工具逻辑
        
        Args:
            args: 工具参数，可以是字符串、字典或包含多模态内容的结构
            
        Returns:
            工具执行的结果，字符串格式
        """
        # 解析和验证输入
        parsed_input = self._parse_input(args)
        
        # 执行多模态处理
        return self._process_multimodal(parsed_input)
    
    def _parse_input(self, args: Any) -> Dict[str, Any]:
        """
        解析工具输入
        
        Args:
            args: 工具参数
            
        Returns:
            解析后的输入字典
        """
        # 如果已经是字典格式，直接使用
        if isinstance(args, dict):
            return args
        
        # 如果是字符串，尝试解析为JSON
        if isinstance(args, str):
            try:
                # 尝试解析为JSON
                parsed = json.loads(args)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                # 不是有效的JSON，作为纯文本处理
                return {"text": args, "modality": ModalityType.TEXT.value}
        
        # 默认作为文本处理
        return {"text": str(args), "modality": ModalityType.TEXT.value}
    
    @abstractmethod
    def _process_multimodal(self, input_data: Dict[str, Any]) -> str:
        """
        处理多模态输入
        
        Args:
            input_data: 解析后的输入数据
            
        Returns:
            处理结果
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema描述，支持多模态输入
        
        Returns:
            工具描述的字典
        """
        schema = {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
        
        # 根据支持的模态类型添加参数
        if ModalityType.TEXT in self.supported_modalities:
            schema["parameters"]["properties"]["text"] = {
                "type": "string",
                "description": "文本输入"
            }
        
        if ModalityType.IMAGE in self.supported_modalities:
            schema["parameters"]["properties"]["image"] = {
                "type": "string",
                "description": "图像URL或Base64编码的图像数据"
            }
        
        if ModalityType.AUDIO in self.supported_modalities:
            schema["parameters"]["properties"]["audio"] = {
                "type": "string",
                "description": "音频URL或Base64编码的音频数据"
            }
        
        if ModalityType.VIDEO in self.supported_modalities:
            schema["parameters"]["properties"]["video"] = {
                "type": "string",
                "description": "视频URL或Base64编码的视频数据"
            }
        
        if ModalityType.FILE in self.supported_modalities:
            schema["parameters"]["properties"]["file"] = {
                "type": "string",
                "description": "文件URL或Base64编码的文件数据"
            }
        
        return schema


# 多模态工具实用函数
def encode_file_to_base64(file_path: str) -> Tuple[str, str]:
    """
    将文件编码为Base64字符串
    
    Args:
        file_path: 文件路径
        
    Returns:
        (base64编码的字符串, MIME类型)
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
        
    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
        
    return encoded, mime_type


def decode_base64_to_file(base64_str: str, output_path: str, mime_type: str = None) -> str:
    """
    将Base64字符串解码并保存为文件
    
    Args:
        base64_str: Base64编码的字符串
        output_path: 输出文件路径
        mime_type: MIME类型，用于确定文件扩展名
        
    Returns:
        保存的文件路径
    """
    # 如果没有指定文件扩展名，尝试从MIME类型推断
    if mime_type and not os.path.splitext(output_path)[1]:
        ext = mimetypes.guess_extension(mime_type)
        if ext:
            output_path += ext
    
    # 确保目录存在
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # 解码并保存
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(base64_str))
    
    return output_path


def is_url(text: str) -> bool:
    """
    判断文本是否为URL
    
    Args:
        text: 要检查的文本
        
    Returns:
        是否为URL
    """
    import re
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(text))


def download_file(url: str, output_path: str) -> str:
    """
    从URL下载文件
    
    Args:
        url: 文件URL
        output_path: 输出文件路径
        
    Returns:
        保存的文件路径
    """
    import requests
    
    # 确保目录存在
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # 下载文件
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # 如果没有指定文件扩展名，尝试从Content-Type推断
    if not os.path.splitext(output_path)[1] and "Content-Type" in response.headers:
        ext = mimetypes.guess_extension(response.headers["Content-Type"].split(";")[0].strip())
        if ext:
            output_path += ext
    
    # 保存文件
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return output_path


class ImageAnalysisTool(MultiModalTool):
    """
    图像分析工具示例
    
    分析图像内容并返回描述
    """
    
    def __init__(self):
        super().__init__(
            name="image_analysis",
            description="分析图像内容并返回描述",
            usage="image_analysis({\"image\": \"图像URL或Base64编码的图像数据\"})",
            supported_modalities=[ModalityType.IMAGE, ModalityType.TEXT]
        )
    
    def _process_multimodal(self, input_data: Dict[str, Any]) -> str:
        """处理图像输入"""
        # 检查是否有图像输入
        if "image" not in input_data:
            return "错误：未提供图像"
        
        image_data = input_data["image"]
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 处理图像数据
        image_path = None
        try:
            if is_url(image_data):
                # 从URL下载图像
                image_path = download_file(image_data, os.path.join(temp_dir, "temp_image"))
            else:
                # 假设是Base64编码的图像数据
                image_path = decode_base64_to_file(image_data, os.path.join(temp_dir, "temp_image"))
            
            # 这里应该调用实际的图像分析逻辑
            # 为演示目的，返回一个模拟结果
            return f"图像分析结果：这是一张图片，大小为{os.path.getsize(image_path)}字节"
            
        except Exception as e:
            logger.error(f"图像分析错误: {e}")
            return f"图像分析失败: {str(e)}"
        finally:
            # 清理临时文件
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    pass


class AudioTranscriptionTool(MultiModalTool):
    """
    音频转写工具示例
    
    将音频转写为文本
    """
    
    def __init__(self):
        super().__init__(
            name="audio_transcription",
            description="将音频转写为文本",
            usage="audio_transcription({\"audio\": \"音频URL或Base64编码的音频数据\"})",
            supported_modalities=[ModalityType.AUDIO]
        )
    
    def _process_multimodal(self, input_data: Dict[str, Any]) -> str:
        """处理音频输入"""
        # 检查是否有音频输入
        if "audio" not in input_data:
            return "错误：未提供音频"
        
        audio_data = input_data["audio"]
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 处理音频数据
        audio_path = None
        try:
            if is_url(audio_data):
                # 从URL下载音频
                audio_path = download_file(audio_data, os.path.join(temp_dir, "temp_audio"))
            else:
                # 假设是Base64编码的音频数据
                audio_path = decode_base64_to_file(audio_data, os.path.join(temp_dir, "temp_audio"))
            
            # 这里应该调用实际的音频转写逻辑
            # 为演示目的，返回一个模拟结果
            return f"音频转写结果：这是一段音频内容的转写文本。音频大小为{os.path.getsize(audio_path)}字节"
            
        except Exception as e:
            logger.error(f"音频转写错误: {e}")
            return f"音频转写失败: {str(e)}"
        finally:
            # 清理临时文件
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
