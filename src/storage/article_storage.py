"""
文章存储管理模块 - 管理文章存储和去重
"""
import os
import sqlite3
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class ArticleStorage:
    """
    文章存储管理类，负责文章存储和去重
    """
    
    def __init__(self, db_path: str, retention_days: int = 30):
        """
        初始化文章存储管理器
        
        Args:
            db_path: SQLite数据库路径
            retention_days: 文章保留天数
        """
        self.db_path = db_path
        self.retention_days = retention_days
        self.logger = logging.getLogger(__name__)
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库表结构"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建文章表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    abstract TEXT,
                    authors TEXT,
                    published_date TEXT,
                    journal TEXT,
                    keywords TEXT,
                    doi TEXT,
                    source_id TEXT,
                    collected_date TEXT NOT NULL,
                    sent_date TEXT
                )
            ''')
            
            conn.commit()
            self.logger.info("数据库初始化成功")
        except sqlite3.Error as e:
            self.logger.error(f"数据库初始化失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def save_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        保存文章到数据库，并返回新文章（去重后）
        
        Args:
            articles: 文章列表
            
        Returns:
            List[Dict]: 新文章列表（之前未保存过的）
        """
        new_articles = []
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for article in articles:
                # 检查文章是否已存在
                cursor.execute("SELECT id FROM articles WHERE url = ?", (article['url'],))
                result = cursor.fetchone()
                
                if result is None:
                    # 文章不存在，保存到数据库
                    collected_date = datetime.now().strftime('%Y-%m-%d')
                    
                    cursor.execute('''
                        INSERT INTO articles (
                            title, url, abstract, authors, published_date, 
                            journal, keywords, doi, source_id, collected_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article['title'],
                        article['url'],
                        article['abstract'],
                        json.dumps(article['authors']),
                        article['published_date'],
                        article['journal'],
                        json.dumps(article.get('keywords', [])),
                        article.get('doi', ''),
                        article.get('source_id', ''),
                        collected_date
                    ))
                    
                    # 添加到新文章列表
                    new_articles.append(article)
            
            conn.commit()
            self.logger.info(f"保存了 {len(new_articles)} 篇新文章")
        except sqlite3.Error as e:
            self.logger.error(f"保存文章失败: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
        
        return new_articles
    
    def mark_articles_as_sent(self, article_urls: List[str]) -> None:
        """
        标记文章为已发送
        
        Args:
            article_urls: 文章URL列表
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            sent_date = datetime.now().strftime('%Y-%m-%d')
            
            for url in article_urls:
                cursor.execute(
                    "UPDATE articles SET sent_date = ? WHERE url = ?",
                    (sent_date, url)
                )
            
            conn.commit()
            self.logger.info(f"标记了 {len(article_urls)} 篇文章为已发送")
        except sqlite3.Error as e:
            self.logger.error(f"标记文章为已发送失败: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def get_unsent_articles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取未发送的文章
        
        Args:
            limit: 最大返回数量
            
        Returns:
            List[Dict]: 未发送的文章列表
        """
        articles = []
        conn = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM articles 
                WHERE sent_date IS NULL 
                ORDER BY collected_date DESC, id DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                article = dict(row)
                # 将JSON字符串转换回列表
                article['authors'] = json.loads(article['authors'])
                article['keywords'] = json.loads(article['keywords'])
                articles.append(article)
            
            self.logger.info(f"获取了 {len(articles)} 篇未发送的文章")
        except sqlite3.Error as e:
            self.logger.error(f"获取未发送文章失败: {str(e)}")
        finally:
            if conn:
                conn.close()
        
        return articles
    
    def cleanup_old_articles(self) -> None:
        """清理过期文章"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 计算截止日期
            cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).strftime('%Y-%m-%d')
            
            # 删除过期文章
            cursor.execute(
                "DELETE FROM articles WHERE collected_date < ?",
                (cutoff_date,)
            )
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            self.logger.info(f"清理了 {deleted_count} 篇过期文章")
        except sqlite3.Error as e:
            self.logger.error(f"清理过期文章失败: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
