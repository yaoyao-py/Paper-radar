"""
API采集器模块 - 处理API类型数据源的采集
"""
import time
import requests
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from urllib.parse import quote

from .base_collector import BaseCollector

class ApiCollector(BaseCollector):
    """
    API采集器，处理API类型数据源
    """
    
    def __init__(self, source_id: str, source_config: Dict[str, Any]):
        """
        初始化API采集器
        
        Args:
            source_id: 数据源ID
            source_config: 数据源配置
        """
        super().__init__(source_id, source_config)
        self.base_url = source_config.get('base_url', '')
        self.search_params = source_config.get('search_params', {})
        self.rate_limit = source_config.get('rate_limit', 1)  # 默认每秒1次请求
        self.parser_name = source_config.get('parser', '')
    
    def collect(self, keywords: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """
        从API收集文章数据
        
        Args:
            keywords: 关键词列表
            max_results: 最大结果数
            
        Returns:
            List[Dict]: 文章数据列表
        """
        self._log_collection_start(keywords)
        
        # 根据数据源选择合适的解析器
        if self.source_id == 'arxiv':
            articles = self._collect_from_arxiv(keywords, max_results)
        elif self.source_id == 'springer':
            articles = self._collect_from_springer(keywords, max_results)
        elif self.source_id == 'elsevier':
            articles = self._collect_from_elsevier(keywords, max_results)
        else:
            self.logger.warning(f"未知的API数据源: {self.source_id}")
            articles = []
        
        self._log_collection_end(len(articles))
        return articles
    
    def _collect_from_arxiv(self, keywords: List[str], max_results: int) -> List[Dict[str, Any]]:
        """从arXiv API收集数据"""
        # 构建查询字符串
        query = ' OR '.join([f'all:"{keyword}"' for keyword in keywords])
        
        # 构建请求参数
        params = self.search_params.copy()
        params['search_query'] = query
        params['max_results'] = max_results
        
        try:
            # 发送请求
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # 解析XML响应
            return self._parse_arxiv_response(response.text)
        except requests.RequestException as e:
            self.logger.error(f"arXiv API请求失败: {str(e)}")
            return []
    
    def _parse_arxiv_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """解析arXiv API的XML响应"""
        articles = []
        
        try:
            # 定义命名空间
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # 解析XML
            root = ET.fromstring(xml_content)
            
            # 提取文章信息
            for entry in root.findall('.//atom:entry', namespaces):
                title = entry.find('./atom:title', namespaces).text.strip()
                url = entry.find('./atom:id', namespaces).text.strip()
                
                # 获取摘要
                abstract = entry.find('./atom:summary', namespaces)
                abstract_text = abstract.text.strip() if abstract is not None else ''
                
                # 获取作者
                authors = []
                for author in entry.findall('./atom:author/atom:name', namespaces):
                    authors.append(author.text.strip())
                
                # 获取发布日期
                published = entry.find('./atom:published', namespaces)
                published_date = published.text[:10] if published is not None else None
                
                # 获取DOI（如果有）
                doi = None
                for link in entry.findall('./atom:link', namespaces):
                    if link.get('title') == 'doi':
                        doi = link.get('href')
                        break
                
                # 创建文章字典
                article = self._create_article_dict(
                    title=title,
                    url=url,
                    abstract=abstract_text,
                    authors=authors,
                    published_date=published_date,
                    journal='arXiv',
                    doi=doi
                )
                
                articles.append(article)
            
            return articles
        except Exception as e:
            self.logger.error(f"解析arXiv响应失败: {str(e)}")
            return []
    
    def _collect_from_springer(self, keywords: List[str], max_results: int) -> List[Dict[str, Any]]:
        """从Springer Nature API收集数据"""
        # 构建查询字符串
        query = ' OR '.join([f'"{keyword}"' for keyword in keywords])
        
        # 构建请求参数
        params = self.search_params.copy()
        params['q'] = query
        params['p'] = max_results
        
        try:
            # 发送请求
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # 解析JSON响应
            data = response.json()
            return self._parse_springer_response(data)
        except requests.RequestException as e:
            self.logger.error(f"Springer API请求失败: {str(e)}")
            return []
        except ValueError as e:
            self.logger.error(f"解析Springer JSON响应失败: {str(e)}")
            return []
    
    def _parse_springer_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析Springer API的JSON响应"""
        articles = []
        
        try:
            # 提取文章列表
            records = data.get('records', [])
            
            for record in records:
                title = record.get('title', '')
                url = record.get('url', [{}])[0].get('value', '')
                abstract = record.get('abstract', '')
                
                # 获取作者
                authors = []
                for creator in record.get('creators', []):
                    authors.append(creator.get('creator', ''))
                
                # 获取发布日期
                published_date = record.get('publicationDate', '')
                
                # 获取期刊名称
                journal = record.get('publicationName', '')
                
                # 获取DOI
                doi = record.get('doi', '')
                
                # 获取关键词
                keywords = []
                for subject in record.get('subjects', []):
                    keywords.append(subject.get('subject', ''))
                
                # 创建文章字典
                article = self._create_article_dict(
                    title=title,
                    url=url,
                    abstract=abstract,
                    authors=authors,
                    published_date=published_date,
                    journal=journal,
                    keywords=keywords,
                    doi=doi
                )
                
                articles.append(article)
            
            return articles
        except Exception as e:
            self.logger.error(f"解析Springer响应失败: {str(e)}")
            return []
    
    def _collect_from_elsevier(self, keywords: List[str], max_results: int) -> List[Dict[str, Any]]:
        """从Elsevier API收集数据"""
        # 构建查询字符串
        query = ' OR '.join([f'"{keyword}"' for keyword in keywords])
        
        # 构建请求参数
        params = self.search_params.copy()
        params['query'] = query
        params['count'] = max_results
        
        # 构建请求头
        headers = {
            'Accept': 'application/json'
        }
        
        try:
            # 发送请求
            response = requests.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            
            # 解析JSON响应
            data = response.json()
            return self._parse_elsevier_response(data)
        except requests.RequestException as e:
            self.logger.error(f"Elsevier API请求失败: {str(e)}")
            return []
        except ValueError as e:
            self.logger.error(f"解析Elsevier JSON响应失败: {str(e)}")
            return []
    
    def _parse_elsevier_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析Elsevier API的JSON响应"""
        articles = []
        
        try:
            # 提取文章列表
            results = data.get('results', [])
            
            for result in results:
                title = result.get('title', '')
                url = result.get('link', '')
                abstract = result.get('description', '')
                
                # 获取作者
                authors = []
                for author in result.get('authors', []):
                    authors.append(author.get('name', ''))
                
                # 获取发布日期
                published_date = result.get('publicationDate', '')
                
                # 获取期刊名称
                journal = result.get('sourceTitle', '')
                
                # 获取DOI
                doi = result.get('doi', '')
                
                # 创建文章字典
                article = self._create_article_dict(
                    title=title,
                    url=url,
                    abstract=abstract,
                    authors=authors,
                    published_date=published_date,
                    journal=journal,
                    doi=doi
                )
                
                articles.append(article)
            
            return articles
        except Exception as e:
            self.logger.error(f"解析Elsevier响应失败: {str(e)}")
            return []
    
    def _respect_rate_limit(self) -> None:
        """遵循API速率限制"""
        if self.rate_limit > 0:
            time.sleep(1.0 / self.rate_limit)
