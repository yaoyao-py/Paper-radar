"""
日志工具模块 - 提供日志记录功能
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(log_file: str, log_level: str = 'INFO', max_size_mb: int = 10, backup_count: int = 5) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        log_file: 日志文件路径
        log_level: 日志级别
        max_size_mb: 日志文件最大大小（MB）
        backup_count: 保留的日志文件数量
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 获取日志级别
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=backup_count
    )
    file_handler.setLevel(numeric_level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger
