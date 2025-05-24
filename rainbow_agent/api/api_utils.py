"""
API工具函数

提供API服务器使用的辅助函数，减少重复代码
"""
import logging
import traceback
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, Tuple
from datetime import datetime
from flask import jsonify

from rainbow_agent.storage.async_utils import run_async

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

T = TypeVar('T')

def api_error_handler(func: Callable) -> Callable:
    """API错误处理装饰器
    
    捕获API函数中的异常，返回统一的错误响应
    
    Args:
        func: 要装饰的API函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API错误: {e}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500
    
    # 保持原函数的名称和文档
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    
    return wrapper

def format_session(session: Dict[str, Any]) -> Dict[str, Any]:
    """格式化会话数据，适配前端需求
    
    Args:
        session: 原始会话数据
        
    Returns:
        格式化后的会话数据
    """
    # 确保id字段存在
    if "id" not in session and "_id" in session:
        session["id"] = session["_id"]
    
    # 确保必要的字段存在
    if "title" not in session:
        session["title"] = f"会话 {session.get('id', '')[:8]}"
    
    if "created_at" not in session:
        session["created_at"] = session.get("timestamp", datetime.now().isoformat())
    
    if "updated_at" not in session:
        session["updated_at"] = session.get("last_activity", session.get("created_at", datetime.now().isoformat()))
    
    # 移除内部字段
    if "_id" in session:
        del session["_id"]
    
    return session

def format_turn(turn: Dict[str, Any]) -> Dict[str, Any]:
    """格式化对话轮次数据，适配前端需求
    
    Args:
        turn: 原始轮次数据
        
    Returns:
        格式化后的轮次数据
    """
    # 确保id字段存在
    if "id" not in turn and "_id" in turn:
        turn["id"] = turn["_id"]
    
    # 适配前端期望的格式
    formatted_turn = {
        "id": turn.get("id", ""),
        "sessionId": turn.get("session_id", ""),
        "input": turn.get("user_input", ""),
        "response": turn.get("agent_response", ""),
        "timestamp": turn.get("timestamp", datetime.now().isoformat())
    }
    
    return formatted_turn

def check_required_params(data: Dict[str, Any], required_params: List[str]) -> Tuple[bool, Optional[str]]:
    """检查必要的参数是否存在
    
    Args:
        data: 请求数据
        required_params: 必要的参数列表
        
    Returns:
        (是否通过检查, 错误消息)
    """
    missing_params = [param for param in required_params if param not in data or not data[param]]
    
    if missing_params:
        return False, f"缺少必要的参数: {', '.join(missing_params)}"
    
    return True, None
