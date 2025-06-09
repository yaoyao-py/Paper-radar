"""
辅助函数模块 - 提供通用辅助函数
"""
import re
import time
import random
from typing import Dict, Any, List, Optional

def clean_text(text: str) -> str:
    """
    清理文本，移除多余空白字符
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
    
    # 替换多个空白字符为单个空格
    text = re.sub(r'\s+', ' ', text)
    # 移除首尾空白
    return text.strip()

def generate_unique_id(prefix: str = "") -> str:
    """
    生成唯一ID
    
    Args:
        prefix: ID前缀
        
    Returns:
        str: 唯一ID
    """
    timestamp = int(time.time() * 1000)
    random_num = random.randint(1000, 9999)
    return f"{prefix}{timestamp}{random_num}"

def truncate_text(text: str, max_length: int = 200, add_ellipsis: bool = True) -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        add_ellipsis: 是否添加省略号
        
    Returns:
        str: 截断后的文本
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length].rstrip()
    if add_ellipsis:
        truncated += "..."
    
    return truncated

def format_date(date_str: Optional[str], output_format: str = "%Y-%m-%d") -> Optional[str]:
    """
    格式化日期字符串
    
    Args:
        date_str: 日期字符串
        output_format: 输出格式
        
    Returns:
        str or None: 格式化后的日期字符串，格式化失败时返回None
    """
    if not date_str:
        return None
    
    # 常见日期格式列表
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
        "%d %B %Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ"
    ]
    
    for fmt in date_formats:
        try:
            dt = time.strptime(date_str, fmt)
            return time.strftime(output_format, dt)
        except ValueError:
            continue
    
    return None
