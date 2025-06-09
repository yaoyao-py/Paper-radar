"""
主程序入口 - 整合各模块，实现自动采集、过滤和邮件推送流程
"""
import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_manager import ConfigManager
from src.collectors.api_collector import ApiCollector
from src.collectors.rss_collector import RssCollector
from src.collectors.web_collector import WebCollector
from src.filters.keyword_filter import KeywordFilter
from src.storage.article_storage import ArticleStorage
from src.notifiers.email_notifier import EmailNotifier

def filter_today_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """只保留今天发布的文章"""
    today = datetime.now().date()
    filtered = []
    for article in articles:
        pub_date = article.get('published_date')
        # 兼容字符串和datetime对象
        if isinstance(pub_date, str):
            try:
                pub_date_obj = datetime.strptime(pub_date[:10], "%Y-%m-%d").date()
            except Exception:
                continue
        elif isinstance(pub_date, datetime):
            pub_date_obj = pub_date.date()
        else:
            continue
        if pub_date_obj == today:
            filtered.append(article)
    return filtered

def main():
    """主程序入口"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='研究论文追踪器')
    parser.add_argument('--config-dir', type=str, default='config',
                        help='配置文件目录路径')
    parser.add_argument('--no-email', action='store_true',
                        help='不发送邮件，仅收集和过滤文章')
    args = parser.parse_args()
    
    # 获取配置目录的绝对路径
    config_dir = os.path.abspath(args.config_dir)
    
    try:
        # 加载配置
        config_manager = ConfigManager(config_dir)
        if not config_manager.load_all_configs():
            print("加载配置失败，程序退出")
            return 1
        
        # 获取配置
        run_config = config_manager.get_run_config()
        storage_config = config_manager.get_storage_config()
        email_config = config_manager.get_email_config()
        
        # 初始化存储
        db_path = storage_config.get('database_path', 'data/articles.db')
        retention_days = storage_config.get('retention_days', 30)
        article_storage = ArticleStorage(db_path, retention_days)
        
        # 清理过期文章
        article_storage.cleanup_old_articles()
        
        # 获取关键词
        keywords = config_manager.get_keywords()
        if not keywords:
            logging.error("未配置关键词，程序退出")
            return 1
        
        # 初始化关键词过滤器
        keyword_matching_config = config_manager.get_keyword_matching_config()
        keyword_filter = KeywordFilter(keywords, keyword_matching_config)
        
        # 获取数据源配置
        api_sources = config_manager.get_api_sources()
        rss_sources = config_manager.get_rss_sources()
        web_sources = config_manager.get_web_sources() if hasattr(config_manager, 'get_web_sources') else {}

        # 设置最大文章数
        max_articles_per_source = run_config.get('max_articles_per_source', 100)
        
        # 收集所有文章
        all_articles = []
        
        # 从API源收集文章
        for source_id, source_config in api_sources.items():
            try:
                collector = ApiCollector(source_id, source_config)
                articles = collector.collect(keywords, max_articles_per_source)
                all_articles.extend(articles)
            except Exception as e:
                logging.error(f"从API源 {source_id} 收集文章失败: {str(e)}")
        
        # 从RSS源收集文章
        for source_id, source_config in rss_sources.items():
            try:
                collector = RssCollector(source_id, source_config)
                articles = collector.collect(keywords, max_articles_per_source)
                all_articles.extend(articles)
            except Exception as e:
                logging.error(f"从RSS源 {source_id} 收集文章失败: {str(e)}")
        
        # 从网页源收集文章
        for source_id, source_config in web_sources.items():
            try:
                collector = WebCollector(source_id, source_config)
                articles = collector.collect(keywords, max_articles_per_source)
                all_articles.extend(articles)
            except Exception as e:
                logging.error(f"从网页源 {source_id} 收集文章失败: {str(e)}")
        
        logging.info(f"总共收集到 {len(all_articles)} 篇文章")
        
        # 过滤文章（关键词过滤）
        filtered_articles = keyword_filter.filter_articles(all_articles)
        logging.info(f"关键词过滤后剩余 {len(filtered_articles)} 篇文章")
        
        # 只保留今天的文章
        today_articles = filter_today_articles(filtered_articles)
        logging.info(f"仅保留今天的文章后剩余 {len(today_articles)} 篇文章")
        
        # 保存文章并去重
        new_articles = article_storage.save_articles(today_articles)
        logging.info(f"去重后有 {len(new_articles)} 篇新文章")
        
        # 发送邮件
        if not args.no_email and new_articles:
            # 初始化邮件通知器
            email_notifier = EmailNotifier(email_config)
            
            # 获取最大邮件文章数
            max_articles_per_email = run_config.get('max_articles_per_email', 50)
            
            # 限制邮件中的文章数量
            articles_to_send = new_articles[:max_articles_per_email]
            
            # 发送邮件
            if email_notifier.send_articles_email(articles_to_send):
                # 标记文章为已发送
                article_urls = [article['url'] for article in articles_to_send]
                article_storage.mark_articles_as_sent(article_urls)
                logging.info(f"成功发送 {len(articles_to_send)} 篇文章")
            else:
                logging.error("发送邮件失败")
        elif args.no_email:
            logging.info("已禁用邮件发送")
        else:
            logging.info("没有新文章需要发送")
        
        return 0
    
    except Exception as e:
        logging.exception(f"程序运行出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
