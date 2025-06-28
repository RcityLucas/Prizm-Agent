"""
异步辅助工具模块

提供异步操作的辅助函数，如同步执行异步函数等。
"""
import asyncio
from typing import Callable, TypeVar, Any

T = TypeVar('T')

def run_async(async_func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    同步执行异步函数
    
    这个辅助函数用于在同步上下文中执行异步函数，避免重复编写事件循环相关代码。
    
    Args:
        async_func: 要执行的异步函数
        *args: 传递给异步函数的位置参数
        **kwargs: 传递给异步函数的关键字参数
        
    Returns:
        异步函数的执行结果
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(async_func(*args, **kwargs))
