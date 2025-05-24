# rainbow_agent/core/input_hub.py
from typing import Dict, Any, Optional
import json
from ..utils.logger import get_logger

logger = get_logger(__name__)

class InputHub:
    """
    输入处理中心，负责接收和预处理用户输入
    """
    
    def __init__(self, preprocessors=None):
        """
        初始化输入处理中心
        
        Args:
            preprocessors: 输入预处理器列表
        """
        self.preprocessors = preprocessors or []
    
    def add_preprocessor(self, preprocessor):
        """添加输入预处理器"""
        self.preprocessors.append(preprocessor)
    
    def process_input(self, user_input: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入文本
            metadata: 输入相关的元数据
            
        Returns:
            处理后的输入数据字典
        """
        if metadata is None:
            metadata = {}
            
        # 创建输入数据对象
        input_data = {
            "raw_input": user_input,
            "processed_input": user_input,
            "metadata": metadata,
            "type": self._detect_input_type(user_input)
        }
        
        # 应用所有预处理器
        for preprocessor in self.preprocessors:
            try:
                input_data = preprocessor(input_data)
            except Exception as e:
                logger.error(f"预处理器执行错误: {e}")
        
        logger.info(f"输入处理完成: {input_data['type']}")
        return input_data
    
    def _detect_input_type(self, user_input: str) -> str:
        """检测输入类型"""
        # 检测是否是JSON
        if user_input.strip().startswith('{') and user_input.strip().endswith('}'):
            try:
                json.loads(user_input)
                return "json"
            except:
                pass
                
        # 检测是否是命令
        if user_input.strip().startswith('/'):
            return "command"
            
        # 检测是否是问题
        if '?' in user_input or '？' in user_input:
            return "question"
            
        # 默认为普通文本
        return "text"