"""
RSS采集器模块 - 处理RSS类型数据源的采集
"""
import time
import logging
import feedparser
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_collector import BaseCollector

class RssCollector(BaseCollector):
    """
    RSS采集器，处理RSS类型数据源
    """
    
    def __init__(self, source_id: str, source_config: Dict[str, Any]):
        """
        初始化RSS采集器
        
        Args:
            source_id: 数据源ID
            source_config: 数据源配置
        """
        super().__init__(source_id, source_config)
        self.url = source_config.get('url', '')
        self.parser_name = source_config.get('parser', '')
    
    def collect(self, keywords: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """
        从RSS源收集文章数据
        
        Args:
            keywords: 关键词列表（RSS采集器不使用关键词进行初始过滤，而是获取所有文章后再过滤）
            max_results: 最大结果数
            
        Returns:
            List[Dict]: 文章数据列表
        """
        self._log_collection_start(keywords)
        
        try:
            # 解析RSS源
            feed = feedparser.parse(self.url)
            
            # 根据数据源选择合适的解析器
            if 'nature' in self.parser_name:
                articles = self._parse_nature_rss(feed, max_results)
            elif 'science' in self.parser_name:
                articles = self._parse_science_rss(feed, max_results)
            elif 'wiley' in self.parser_name:
                articles = self._parse_wiley_rss(feed, max_results)
            elif 'rsc' in self.parser_name:
                articles = self._parse_rsc_rss(feed, max_results)
            elif 'acs' in self.parser_name:
                articles = self._parse_acs_rss(feed, max_results)
            else:
                # 默认解析器
                articles = self._parse_generic_rss(feed, max_results)
            
            self._log_collection_end(len(articles))
            return articles
        except Exception as e:
            self.logger.error(f"RSS源 {self.name} 采集失败: {str(e)}")
            return []
    
    def _parse_generic_rss(self, feed: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """
        通用RSS解析器
        
        Args:
            feed: feedparser解析的RSS源
            max_results: 最大结果数
            
        Returns:
            List[Dict]: 文章数据列表
        """
        articles = []
        
        # 获取源信息
        feed_title = feed.get('feed', {}).get('title', self.name)
        
        # 处理条目
        for entry in feed.get('entries', [])[:max_results]:
            title = entry.get('title', '')
            url = entry.get('link', '')
            
            # 获取摘要
            summary = entry.get('summary', '')
            if not summary and 'description' in entry:
                summary = entry.get('description', '')
            
            # 获取作者
            authors = []
            if 'authors' in entry:
                for author in entry.get('authors', []):
                    authors.append(author.get('name', ''))
            elif 'author' in entry:
                authors = [entry.get('author', '')]
            
            # 获取发布日期
            published_date = None
            if 'published_parsed' in entry and entry.get('published_parsed'):
                published_date = time.strftime('%Y-%m-%d', entry.get('published_parsed'))
            elif 'updated_parsed' in entry and entry.get('updated_parsed'):
                published_date = time.strftime('%Y-%m-%d', entry.get('updated_parsed'))
            
            # 获取标签/关键词
            keywords = []
            for tag in entry.get('tags', []):
                keywords.append(tag.get('term', ''))
            
            # 创建文章字典
            article = self._create_article_dict(
                title=title,
                url=url,
                abstract=summary,
                authors=authors,
                published_date=published_date,
                journal=feed_title,
                keywords=keywords
            )
            
            articles.append(article)
        
        return articles
    
    def _parse_nature_rss(self, feed: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """Nature期刊RSS解析器"""
        articles = []
        
        # 获取源信息
        feed_title = feed.get('feed', {}).get('title', self.name)
        
        # 处理条目
        for entry in feed.get('entries', [])[:max_results]:
            title = entry.get('title', '')
            url = entry.get('link', '')
            
            # 获取摘要
            summary = entry.get('summary', '')
            
            # 获取作者（Nature RSS通常不包含作者信息）
            authors = []
            
            # 获取发布日期
            published_date = None
            if 'published_parsed' in entry and entry.get('published_parsed'):
                published_date = time.strftime('%Y-%m-%d', entry.get('published_parsed'))
            
            # 创建文章字典
            article = self._create_article_dict(
                title=title,
                url=url,
                abstract=summary,
                authors=authors,
                published_date=published_date,
                journal=feed_title
            )
            
            articles.append(article)
        
        return articles
    
    def _parse_science_rss(self, feed: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """Science期刊RSS解析器"""
        articles = []
        
        # 获取源信息
        feed_title = feed.get('feed', {}).get('title', self.name)
        
        # 处理条目
        for entry in feed.get('entries', [])[:max_results]:
            title = entry.get('title', '')
            url = entry.get('link', '')
            
            # 获取摘要
            summary = entry.get('summary', '')
            
            # 获取作者
            authors = []
            if 'author' in entry:
                authors = [entry.get('author', '')]
            
            # 获取发布日期
            published_date = None
            if 'published_parsed' in entry and entry.get('published_parsed'):
                published_date = time.strftime('%Y-%m-%d', entry.get('published_parsed'))
            
            # 创建文章字典
            article = self._create_article_dict(
                title=title,
                url=url,
                abstract=summary,
                authors=authors,
                published_date=published_date,
                journal=feed_title
            )
            
            articles.append(article)
        
        return articles
    
    def _parse_wiley_rss(self, feed: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """Wiley期刊RSS解析器"""
        articles = []
        
        # 获取源信息
        feed_title = feed.get('feed', {}).get('title', self.name)
        
        # 处理条目
        for entry in feed.get('entries', [])[:max_results]:
            title = entry.get('title', '')
            url = entry.get('link', '')
            
            # 获取摘要
            summary = entry.get('summary', '')
            
            # 获取作者
            authors = []
            if 'author' in entry:
                author_text = entry.get('author', '')
                # Wiley通常以逗号分隔作者
                if ',' in author_text:
                    authors = [a.strip() for a in author_text.split(',')]
                else:
                    authors = [author_text]
            
            # 获取发布日期
            published_date = None
            if 'published_parsed' in entry and entry.get('published_parsed'):
                published_date = time.strftime('%Y-%m-%d', entry.get('published_parsed'))
            
            # 创建文章字典
            article = self._create_article_dict(
                title=title,
                url=url,
                abstract=summary,
                authors=authors,
                published_date=published_date,
                journal=feed_title
            )
            
            articles.append(article)
        
        return articles
    
    def _parse_rsc_rss(self, feed: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """RSC期刊RSS解析器"""
        # RSC的RSS格式与通用格式类似，可以使用通用解析器
        return self._parse_generic_rss(feed, max_results)
    
    def _parse_acs_rss(self, feed: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """ACS期刊RSS解析器"""
        articles = []
        
        # 获取源信息
        feed_title = feed.get('feed', {}).get('title', self.name)
        
        # 处理条目
        for entry in feed.get('entries', [])[:max_results]:
            title = entry.get('title', '')
            url = entry.get('link', '')
            
            # 获取摘要
            summary = entry.get('summary', '')
            
            # 获取作者
            authors = []
            if 'author' in entry:
                author_text = entry.get('author', '')
                # ACS通常以逗号或分号分隔作者
                if ',' in author_text:
                    authors = [a.strip() for a in author_text.split(',')]
                elif ';' in author_text:
                    authors = [a.strip() for a in author_text.split(';')]
                else:
                    authors = [author_text]
            
            # 获取发布日期
            published_date = None
            if 'published_parsed' in entry and entry.get('published_parsed'):
                published_date = time.strftime('%Y-%m-%d', entry.get('published_parsed'))
            
            # 获取DOI
            doi = None
            for link in entry.get('links', []):
                if link.get('rel') == 'alternate' and 'doi.org' in link.get('href', ''):
                    doi = link.get('href').split('doi.org/')[-1]
                    break
            
            # 创建文章字典
            article = self._create_article_dict(
                title=title,
                url=url,
                abstract=summary,
                authors=authors,
                published_date=published_date,
                journal=feed_title,
                doi=doi
            )
            
            articles.append(article)
        
        return articles
