"""
彩虹城AI对话系统 - 频率感知系统模块

该模块负责实现AI的频率感知和主动表达能力，包括环境信号收集、
表达决策、内容生成和调度等功能。
频率感知系统包，负责处理AI主动表达的频率和内容
"""

from .context_sampler import ContextSampler
from .frequency_sense_core import FrequencySenseCore
from .expression_planner import ExpressionPlanner
from .expression_generator import ExpressionGenerator
from .expression_dispatcher import ExpressionDispatcher
from .memory_sync import MemorySync
from .prompt_log import PromptLog
from .frequency_integrator import FrequencyIntegrator

__all__ = [
    'ContextSampler',
    'FrequencySenseCore',
    'ExpressionPlanner',
    'ExpressionGenerator',
    'ExpressionDispatcher',
    'MemorySync',
    'PromptLog',
    'FrequencyIntegrator'
]
