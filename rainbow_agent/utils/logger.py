"""
日志系统工具

提供日志配置和获取功能
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional

# 全局日志配置状态
_logger_initialized = False

def setup_logger(level: str = None, log_file: str = None) -> None:
    """
    设置全局日志配置
    
    Args:
        level: 日志级别，默认使用环境变量LOG_LEVEL或INFO
        log_file: 日志文件路径，默认使用环境变量LOG_FILE
    """
    global _logger_initialized
    
    # 如果已经初始化过，则跳过
    if _logger_initialized:
        return
        
    # 获取日志级别
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    numeric_level = getattr(logging, level, logging.INFO)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # 清除已有的处理器
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    
    # 控制台输出处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # 设置日志格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(log_format)
    
    # 添加处理器到根日志记录器
    root_logger.addHandler(console_handler)
    
    # 如果配置了日志文件，则添加文件处理器
    if log_file is None:
        log_file = os.environ.get("LOG_FILE")
        
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(log_format)
        
        # 添加到根日志记录器
        root_logger.addHandler(file_handler)
    
    _logger_initialized = True
    
    # 记录初始化日志
    root_logger.info(f"日志系统初始化完成 (级别: {level})")

def get_logger(name: str, level: str = None) -> logging.Logger:
    """
    获取配置好的logger实例
    
    Args:
        name: logger名称
        level: 日志级别 (如果为None则使用环境变量设置)
        
    Returns:
        配置好的logger实例
    """
    # 获取日志级别，默认为INFO
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    numeric_level = getattr(logging, level, logging.INFO)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # 防止重复添加handler
    if not logger.handlers:
        # 控制台输出handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        # 设置日志格式
        log_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(log_format)
        
        # 添加handler到logger
        logger.addHandler(console_handler)
        
        # 如果配置了日志文件，则添加文件handler
        log_file = os.environ.get("LOG_FILE")
        if log_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 创建文件handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(log_format)
            
            # 添加到logger
            logger.addHandler(file_handler)
    
    return logger
