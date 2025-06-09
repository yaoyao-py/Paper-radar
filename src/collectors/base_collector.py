"""
基础采集器模块 - 定义数据采集的基础接口
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseCollector(ABC):
    """
    数据采集器基类，定义通用接口和方法
    """
    
    def __init__(self, source_id: str, source_config: Dict[str, Any]):
        """
        初始化基础采集器
        
        Args:
            source_id: 数据源ID
            source_config: 数据源配置
        """
        self.source_id = source_id
        self.source_config = source_config
        self.name = source_config.get('name', source_id)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    @abstractmethod
    def collect(self, keywords: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """
        收集文章数据
        
        Args:
            keywords: 关键词列表
            max_results: 最大结果数
            
        Returns:
            List[Dict]: 文章数据列表，每篇文章为一个字典
        """
        pass
    
    def _create_article_dict(self, 
                            title: str, 
                            url: str, 
                            abstract: Optional[str] = None,
                            authors: Optional[List[str]] = None,
                            published_date: Optional[str] = None,
                            journal: Optional[str] = None,
                            keywords: Optional[List[str]] = None,
                            doi: Optional[str] = None) -> Dict[str, Any]:
        """
        创建标准化的文章数据字典
        
        Args:
            title: 文章标题
            url: 文章URL
            abstract: 文章摘要
            authors: 作者列表
            published_date: 发布日期
            journal: 期刊名称
            keywords: 文章关键词
            doi: DOI标识符
            
        Returns:
            Dict: 标准化的文章数据字典
        """
        return {
            'title': title,
            'url': url,
            'abstract': abstract or '',
            'authors': authors or [],
            'published_date': published_date,
            'journal': journal or self.name,
            'keywords': keywords or [],
            'doi': doi,
            'source_id': self.source_id
        }
    
    def _log_collection_start(self, keywords: List[str]) -> None:
        """记录开始收集数据的日志"""
        self.logger.info(f"开始从 {self.name} 收集数据，关键词: {', '.join(keywords)}")
    
    def _log_collection_end(self, count: int) -> None:
        """记录收集数据完成的日志"""
        self.logger.info(f"从 {self.name} 收集数据完成，获取到 {count} 篇文章")
