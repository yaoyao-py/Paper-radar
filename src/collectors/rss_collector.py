"""
RSS数据源采集器 - 从RSS/Atom源采集文章
针对Wiley和Science等特殊RSS源进行优化
"""
import feedparser
import logging
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

class RssCollector:
    """
    RSS采集器，从RSS/Atom源采集文章
    """
    
    def __init__(self, source_id: str, source_config: Dict[str, Any]):
        """
        初始化RSS采集器
        
        Args:
            source_id: 数据源ID
            source_config: 数据源配置
        """
        self.source_id = source_id
        self.source_config = source_config
        self.logger = logging.getLogger(__name__)
        
        # 特殊源的处理配置
        self.special_sources = {
            'advanced_materials': {
                'url': 'https://advanced.onlinelibrary.wiley.com/feed/15214095/most-recent',
                'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            },
            'science': {
                'url': 'https://www.science.org/action/showFeed?type=axatoc&feed=rss&jc=science',
                'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            },
            'advanced_functional_materials': {
                'url': 'https://advanced.onlinelibrary.wiley.com/feed/16163028/most-recent',
                'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            },
            'advanced_energy_materials': {
                'url': 'https://advanced.onlinelibrary.wiley.com/feed/16146840/most-recent',
                'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            }
        }
    
    def collect(self, keywords: List[str], max_articles: int = 100) -> List[Dict[str, Any]]:
        """
        从RSS源采集文章
        
        Args:
            keywords: 关键词列表（在RSS采集中通常不用于预过滤）
            max_articles: 最大文章数
            
        Returns:
            List[Dict]: 文章列表
        """
        url = self.source_config.get('url')
        if not url:
            self.logger.error(f"RSS源 {self.source_id} 未配置URL")
            return []
        
        try:
            # 解析RSS源
            self.logger.info(f"开始采集RSS源: {self.source_id} - {url}")
            
            # 检查是否为特殊源，需要特殊处理
            if self.source_id in self.special_sources:
                feed = self._parse_special_source(url)
            else:
                feed = feedparser.parse(url)
            
            # 处理解析警告和错误
            if feed.bozo:
                self.logger.warning(f"RSS源 {self.source_id} 解析时有警告: {feed.bozo_exception}")
                # 对于特殊源，即使有警告也尝试继续处理
                if self.source_id in self.special_sources:
                    self.logger.info(f"特殊源 {self.source_id} 继续尝试处理...")
                # 检查是否是严重错误，如果没有entries则认为解析完全失败
                elif not hasattr(feed, 'entries') or len(feed.entries) == 0:
                    self.logger.error(f"RSS源 {self.source_id} 解析完全失败，无法获取任何条目")
                    return []
                else:
                    self.logger.info(f"RSS源 {self.source_id} 虽有警告但仍可获取到 {len(feed.entries)} 个条目")
            
            articles = []
            
            # 处理每个条目，增加独立的异常处理
            entries_count = len(feed.entries) if hasattr(feed, 'entries') else 0
            self.logger.info(f"RSS源 {self.source_id} 获取到 {entries_count} 个条目")
            
            for i, entry in enumerate(feed.entries[:max_articles]):
                try:
                    # 提取文章信息
                    article = self._extract_article_info(entry)
                    
                    if article:
                        # 调试：打印每条文章的published_date
                        # print(f"采集到文章: {article.get('title', '无标题')[:50]}，published_date: {article.get('published_date')}")
                        articles.append(article)
                    else:
                        self.logger.warning(f"RSS源 {self.source_id} 第 {i+1} 个条目提取失败，跳过")
                        
                except Exception as e:
                    self.logger.warning(f"RSS源 {self.source_id} 处理第 {i+1} 个条目时出错，跳过: {str(e)}")
                    continue
            
            self.logger.info(f"从RSS源 {self.source_id} 采集到 {len(articles)} 篇文章")
            return articles
            
        except Exception as e:
            self.logger.error(f"采集RSS源 {self.source_id} 失败: {str(e)}")
            return []
    
    def _parse_special_source(self, url: str):
        """
        解析特殊RSS源，使用自定义headers和重试机制
        
        Args:
            url: RSS源URL
            
        Returns:
            feedparser对象
        """
        try:
            # 获取特殊源配置
            config = self.special_sources.get(self.source_id, {})
            headers = config.get('headers', {})
            
            # 使用requests先获取内容，再用feedparser解析
            self.logger.info(f"使用特殊方式解析源: {self.source_id}")
            
            session = requests.Session()
            session.headers.update(headers)
            
            # 设置超时和重试
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # 使用feedparser解析响应内容
            feed = feedparser.parse(response.content)
            
            self.logger.info(f"特殊源 {self.source_id} 解析完成，获取到 {len(feed.entries) if hasattr(feed, 'entries') else 0} 个条目")
            return feed
            
        except requests.RequestException as e:
            self.logger.error(f"特殊源 {self.source_id} 网络请求失败: {str(e)}")
            # 回退到普通解析方式
            return feedparser.parse(url)
        except Exception as e:
            self.logger.error(f"特殊源 {self.source_id} 解析失败: {str(e)}")
            # 回退到普通解析方式
            return feedparser.parse(url)
    
    def _extract_article_info(self, entry) -> Optional[Dict[str, Any]]:
        """
        从RSS条目中提取文章信息
        
        Args:
            entry: RSS条目
            
        Returns:
            Dict: 文章信息字典
        """
        try:
            # 提取标题
            title = self._safe_get_attr(entry, 'title', '')
            
            # 提取摘要/描述
            abstract = self._extract_abstract(entry)
            
            # 提取URL
            url = self._safe_get_attr(entry, 'link', '')
            
            # 提取发布日期 - 多种方式尝试
            pub_date = self._extract_publish_date(entry)
            
            # 提取作者
            authors = self._extract_authors(entry)
            
            # 提取关键词/标签
            keywords = self._extract_keywords(entry)
            
            # 使用 'journal' 字段
            article = {
                'title': title,
                'abstract': abstract,
                'url': url,
                'published_date': pub_date,
                'authors': authors,
                'keywords': keywords,
                'journal': self.source_id
            }
            
            return article
            
        except Exception as e:
            self.logger.error(f"提取文章信息失败: {str(e)}")
            return None
    
    def _safe_get_attr(self, obj, attr_name: str, default_value: str = '') -> str:
        """
        安全获取对象属性
        
        Args:
            obj: 对象
            attr_name: 属性名
            default_value: 默认值
            
        Returns:
            str: 属性值或默认值
        """
        try:
            return getattr(obj, attr_name, default_value) or default_value
        except Exception:
            return default_value
    
    def _extract_abstract(self, entry) -> str:
        """
        提取摘要/描述，尝试多种字段
        
        Args:
            entry: RSS条目
            
        Returns:
            str: 摘要内容
        """
        try:
            # 按优先级尝试不同的摘要字段
            abstract_fields = ['summary', 'description', 'content']
            
            for field in abstract_fields:
                abstract = self._safe_get_attr(entry, field, '')
                if abstract:
                    # 如果abstract是列表，取第一个元素的value
                    if isinstance(abstract, list) and len(abstract) > 0:
                        if hasattr(abstract[0], 'value'):
                            return abstract[0].value
                        else:
                            return str(abstract[0])
                    elif isinstance(abstract, str):
                        return abstract
            
            return ''
            
        except Exception as e:
            self.logger.warning(f"提取摘要时出错: {str(e)}")
            return ''
    
    def _extract_publish_date(self, entry) -> Optional[str]:
        """
        提取发布日期，针对Wiley和Science源进行特殊处理
        
        Args:
            entry: RSS条目
            
        Returns:
            str: 发布日期字符串
        """
        try:
            # 方法1: 尝试解析时间结构体字段
            time_struct_fields = ['published_parsed', 'updated_parsed']
            for field in time_struct_fields:
                time_struct = getattr(entry, field, None)
                if time_struct:
                    try:
                        return time.strftime('%Y-%m-%d', time_struct)
                    except Exception:
                        continue
            
            # 方法2: 尝试字符串日期字段
            date_fields = [
                'dc_date',           # Dublin Core date
                'published',         # Atom published
                'pubDate',          # RSS pubDate
                'updated',          # Atom updated
                'date',             # 通用date字段
            ]
            
            for field in date_fields:
                date_value = getattr(entry, field, None)
                if date_value:
                    # 如果是时间结构，转换为字符串
                    if hasattr(date_value, 'strftime'):
                        try:
                            return date_value.strftime('%Y-%m-%d')
                        except Exception:
                            continue
                    elif isinstance(date_value, str) and date_value.strip():
                        return date_value.strip()
            
            # 方法3: 针对Wiley源的特殊处理
            if self.source_id in ['advanced_materials', 'advanced_functional_materials', 'advanced_energy_materials']:
                # 尝试从title或summary中提取日期信息
                title = getattr(entry, 'title', '')
                summary = getattr(entry, 'summary', '')
                
                # 查找日期模式
                import re
                date_pattern = r'(\d{4}-\d{2}-\d{2})'
                for text in [title, summary]:
                    if text:
                        match = re.search(date_pattern, str(text))
                        if match:
                            return match.group(1)
            
            # 方法4: 从tags中查找日期
            if hasattr(entry, 'tags'):
                try:
                    for tag in entry.tags:
                        if isinstance(tag, dict) and 'date' in tag.get('term', '').lower():
                            return tag.get('term')
                except Exception:
                    pass
            
            self.logger.warning(f"无法提取文章发布日期: {getattr(entry, 'title', '无标题')}")
            return None
            
        except Exception as e:
            self.logger.warning(f"提取发布日期时出错: {str(e)}")
            return None
    
    def _extract_authors(self, entry) -> List[str]:
        """
        提取作者信息
        
        Args:
            entry: RSS条目
            
        Returns:
            List[str]: 作者列表
        """
        authors = []
        
        try:
            # 尝试不同的作者字段
            if hasattr(entry, 'author') and entry.author:
                authors.append(str(entry.author))
            elif hasattr(entry, 'authors') and entry.authors:
                if isinstance(entry.authors, list):
                    for author in entry.authors:
                        if isinstance(author, dict):
                            name = author.get('name', str(author))
                        else:
                            name = str(author)
                        if name:
                            authors.append(name)
                else:
                    authors.append(str(entry.authors))
            elif hasattr(entry, 'dc_creator') and entry.dc_creator:
                if isinstance(entry.dc_creator, list):
                    authors.extend([str(creator) for creator in entry.dc_creator if creator])
                else:
                    authors.append(str(entry.dc_creator))
        except Exception as e:
            self.logger.warning(f"提取作者信息时出错: {str(e)}")
        
        return [author for author in authors if author.strip()]
    
    def _extract_keywords(self, entry) -> List[str]:
        """
        提取关键词/标签
        
        Args:
            entry: RSS条目
            
        Returns:
            List[str]: 关键词列表
        """
        keywords = []
        
        try:
            # 从tags中提取
            if hasattr(entry, 'tags') and entry.tags:
                for tag in entry.tags:
                    if isinstance(tag, dict) and 'term' in tag:
                        term = tag['term']
                        if term:
                            keywords.append(str(term))
            
            # 从category中提取
            if hasattr(entry, 'category') and entry.category:
                if isinstance(entry.category, list):
                    keywords.extend([str(cat) for cat in entry.category if cat])
                else:
                    keywords.append(str(entry.category))
        except Exception as e:
            self.logger.warning(f"提取关键词时出错: {str(e)}")
        
        return [keyword for keyword in keywords if keyword.strip()]
