"""
网页采集器模块 - 处理网页类型数据源的采集
"""
import time
import logging
import requests
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from .base_collector import BaseCollector

class WebCollector(BaseCollector):
    """
    网页采集器，处理需要网页爬取的数据源
    """
    
    def __init__(self, source_id: str, source_config: Dict[str, Any]):
        """
        初始化网页采集器
        
        Args:
            source_id: 数据源ID
            source_config: 数据源配置
        """
        super().__init__(source_id, source_config)
        self.base_url = source_config.get('base_url', '')
        self.search_params = source_config.get('search_params', {})
        self.rate_limit = source_config.get('rate_limit', 1)  # 默认每秒1次请求
        self.headers = source_config.get('headers', {})
        self.selectors = source_config.get('selectors', {})
    
    def collect(self, keywords: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """
        从网页收集文章数据
        
        Args:
            keywords: 关键词列表
            max_results: 最大结果数
            
        Returns:
            List[Dict]: 文章数据列表
        """
        self._log_collection_start(keywords)
        
        # 根据数据源选择合适的爬取方法
        if self.source_id == 'sciencedirect':
            articles = self._collect_from_sciencedirect(keywords, max_results)
        else:
            # 默认通用网页爬取
            articles = self._collect_generic(keywords, max_results)
        
        self._log_collection_end(len(articles))
        return articles
    
    def _collect_from_sciencedirect(self, keywords: List[str], max_results: int) -> List[Dict[str, Any]]:
        """从ScienceDirect网页收集数据"""
        articles = []
        
        # 构建查询字符串
        query = ' OR '.join([f'"{keyword}"' for keyword in keywords])
        
        # 构建请求参数
        params = self.search_params.copy()
        params['qs'] = query.replace('{keywords}', query)
        params['show'] = max_results
        
        try:
            # 发送请求
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章信息
            article_containers = soup.select(self.selectors.get('article_container', 'div.result-item'))
            
            for container in article_containers[:max_results]:
                # 提取标题
                title_elem = container.select_one(self.selectors.get('title', 'h2'))
                title = title_elem.text.strip() if title_elem else ''
                
                # 提取链接
                link_elem = container.select_one(self.selectors.get('link', 'h2 a'))
                url = link_elem.get('href', '') if link_elem else ''
                if url and not url.startswith('http'):
                    url = 'https://www.sciencedirect.com' + url
                
                # 提取摘要
                abstract_elem = container.select_one(self.selectors.get('abstract', 'div.abstract-text'))
                abstract = abstract_elem.text.strip() if abstract_elem else ''
                
                # 提取作者
                authors_elem = container.select_one(self.selectors.get('authors', 'div.Authors'))
                authors_text = authors_elem.text.strip() if authors_elem else ''
                authors = [a.strip() for a in authors_text.split(',') if a.strip()]
                
                # 提取日期
                date_elem = container.select_one(self.selectors.get('date', 'div.publication-date'))
                published_date = date_elem.text.strip() if date_elem else None
                
                # 创建文章字典
                article = self._create_article_dict(
                    title=title,
                    url=url,
                    abstract=abstract,
                    authors=authors,
                    published_date=published_date,
                    journal='ScienceDirect'
                )
                
                articles.append(article)
            
            return articles
        except requests.RequestException as e:
            self.logger.error(f"ScienceDirect网页请求失败: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"解析ScienceDirect网页失败: {str(e)}")
            return []
    
    def _collect_generic(self, keywords: List[str], max_results: int) -> List[Dict[str, Any]]:
        """通用网页爬取方法"""
        articles = []
        
        # 构建查询字符串
        query = ' OR '.join([f'"{keyword}"' for keyword in keywords])
        
        # 构建请求参数
        params = {}
        for key, value in self.search_params.items():
            if isinstance(value, str) and '{keywords}' in value:
                params[key] = value.replace('{keywords}', query)
            else:
                params[key] = value
        
        try:
            # 发送请求
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章信息
            article_containers = soup.select(self.selectors.get('article_container', 'div.article'))
            
            for container in article_containers[:max_results]:
                # 提取标题
                title_elem = container.select_one(self.selectors.get('title', 'h2'))
                title = title_elem.text.strip() if title_elem else ''
                
                # 提取链接
                link_elem = container.select_one(self.selectors.get('link', 'a'))
                url = link_elem.get('href', '') if link_elem else ''
                
                # 提取摘要
                abstract_elem = container.select_one(self.selectors.get('abstract', 'div.abstract'))
                abstract = abstract_elem.text.strip() if abstract_elem else ''
                
                # 提取作者
                authors_elem = container.select_one(self.selectors.get('authors', 'div.authors'))
                authors_text = authors_elem.text.strip() if authors_elem else ''
                authors = [a.strip() for a in authors_text.split(',') if a.strip()]
                
                # 提取日期
                date_elem = container.select_one(self.selectors.get('date', 'div.date'))
                published_date = date_elem.text.strip() if date_elem else None
                
                # 创建文章字典
                article = self._create_article_dict(
                    title=title,
                    url=url,
                    abstract=abstract,
                    authors=authors,
                    published_date=published_date,
                    journal=self.name
                )
                
                articles.append(article)
            
            return articles
        except requests.RequestException as e:
            self.logger.error(f"{self.name}网页请求失败: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"解析{self.name}网页失败: {str(e)}")
            return []
    
    def _respect_rate_limit(self) -> None:
        """遵循网站速率限制"""
        if self.rate_limit > 0:
            time.sleep(1.0 / self.rate_limit)
