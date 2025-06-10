import re
import logging
from typing import Dict, Any, List

class KeywordFilter:
    """
    关键词过滤器，根据配置的关键词过滤文章
    支持 exact（全等）、contain（包含）、regex（正则）三种匹配方式。
    """

    def __init__(self, keywords: List[str], matching_config: Dict[str, Any]):
        """
        初始化关键词过滤器

        Args:
            keywords: 关键词列表
            matching_config: 匹配配置
        """
        self.keywords = keywords
        self.match_type = matching_config.get('type', 'contain')  # 'exact', 'contain', 'regex'
        self.case_sensitive = matching_config.get('case_sensitive', False)
        self.whole_word = matching_config.get('whole_word', False)
        self.match_any = matching_config.get('match_any', True)
        self.include_fields = matching_config.get('include_fields', ['title', 'abstract', 'keywords'])
        self.logger = logging.getLogger(__name__)

        # 预编译正则表达式（如需要）
        if self.match_type == 'regex':
            flags = 0 if self.case_sensitive else re.IGNORECASE
            self.compiled_patterns = [re.compile(k, flags) for k in self.keywords]
        else:
            self.compiled_patterns = None

    def filter_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤文章列表，保留包含关键词的文章

        Args:
            articles: 文章列表

        Returns:
            List[Dict]: 过滤后的文章列表
        """
        filtered_articles = []

        for article in articles:
            if self._article_matches_keywords(article):
                filtered_articles.append(article)

        self.logger.info(f"关键词过滤: 从 {len(articles)} 篇文章中过滤得到 {len(filtered_articles)} 篇")
        return filtered_articles

    def _article_matches_keywords(self, article: Dict[str, Any]) -> bool:
        """
        检查文章是否匹配关键词

        Args:
            article: 文章数据

        Returns:
            bool: 是否匹配
        """
        # 构建要搜索的文本
        search_text = ""
        for field in self.include_fields:
            if field in article:
                if isinstance(article[field], list):
                    search_text += " ".join(article[field]) + " "
                else:
                    search_text += str(article[field]) + " "

        # 匹配方式分支
        if self.match_type == 'regex':
            matches = [bool(p.search(search_text)) for p in self.compiled_patterns]
        else:
            # 处理大小写
            if not self.case_sensitive:
                search_text = search_text.lower()
                keywords = [k.lower() for k in self.keywords]
            else:
                keywords = self.keywords

            matches = []
            for keyword in keywords:
                if self.match_type == 'exact':
                    # 全等匹配
                    if self.whole_word:
                        pattern = r'\b' + re.escape(keyword) + r'\b'
                        match = re.search(pattern, search_text)
                        matches.append(bool(match))
                    else:
                        matches.append(keyword == search_text.strip())
                elif self.match_type == 'contain':
                    if self.whole_word:
                        pattern = r'\b' + re.escape(keyword) + r'\b'
                        match = re.search(pattern, search_text)
                        matches.append(bool(match))
                    else:
                        matches.append(keyword in search_text)
                else:
                    # 默认包含关系
                    matches.append(keyword in search_text)

        # 根据匹配模式返回结果
        if self.match_any:
            return any(matches)
        else:
            return all(matches)
