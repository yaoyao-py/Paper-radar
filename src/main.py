"""
主程序入口 - 整合各模块，实现自动采集、过滤和邮件推送流程
"""
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
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

def filter_yesterday_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    只保留昨天发布的文章，兼容多种日期格式。
    """
    try:
        from dateutil.parser import parse as date_parse
    except ImportError:
        raise ImportError("请先安装 python-dateutil 包：pip install python-dateutil")

    yesterday = (datetime.now() - timedelta(days=1)).date()
    filtered = []

    for article in articles:
        pub_date = article.get('published_date')
        pub_date_obj = None

        if pub_date is None:
            continue

        # 1. 直接是 datetime 类型
        if isinstance(pub_date, datetime):
            pub_date_obj = pub_date.date()
        # 2. 是字符串，尝试多种格式解析
        elif isinstance(pub_date, str):
            try:
                pub_date_obj = date_parse(pub_date).date()
            except Exception:
                # 如果解析失败，跳过
                continue
        else:
            continue

        # 可选：调试时输出每篇文章的日期解析结果
        # print(f"解析到文章日期: {pub_date} -> {pub_date_obj}，标题: {article.get('title')}")

        if pub_date_obj == yesterday:
            filtered.append(article)

    return filtered

# def debug_article_dates(articles: List[Dict[str, Any]], source_name: str):
#     """
#     调试函数：检查每篇文章的published_date字段
#     """
#     logging.info(f"=== 调试 {source_name} 源的文章日期 ===")
#     for i, article in enumerate(articles):
#         pub_date = article.get('published_date')
#         title = article.get('title', '无标题')[:50]  # 截取前50个字符
#         logging.info(f"文章 {i+1}: published_date={pub_date}, 标题={title}")
#     logging.info(f"=== {source_name} 源调试结束 ===")

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
    # parser.add_argument('--debug-dates', action='store_true',
    #                     help='启用日期调试模式')
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
                
                # 调试API源文章日期
                # if args.debug_dates:
                #     debug_article_dates(articles, f"API-{source_id}")
                
                all_articles.extend(articles)
            except Exception as e:
                logging.error(f"从API源 {source_id} 收集文章失败: {str(e)}")
        
        # 从RSS源收集文章
        for source_id, source_config in rss_sources.items():
            try:
                collector = RssCollector(source_id, source_config)
                articles = collector.collect(keywords, max_articles_per_source)
                
                # 调试RSS源文章日期
                # if args.debug_dates:
                #     debug_article_dates(articles, f"RSS-{source_id}")
                
                all_articles.extend(articles)
            except Exception as e:
                logging.error(f"从RSS源 {source_id} 收集文章失败: {str(e)}")
        
        # 从网页源收集文章
        for source_id, source_config in web_sources.items():
            try:
                collector = WebCollector(source_id, source_config)
                articles = collector.collect(keywords, max_articles_per_source)
                
                # 调试网页源文章日期
                # if args.debug_dates:
                #     debug_article_dates(articles, f"WEB-{source_id}")
                
                all_articles.extend(articles)
            except Exception as e:
                logging.error(f"从网页源 {source_id} 收集文章失败: {str(e)}")
        
        logging.info(f"总共收集到 {len(all_articles)} 篇文章")
        
        # 过滤文章（关键词过滤）
        filtered_articles = keyword_filter.filter_articles(all_articles)
        logging.info(f"关键词过滤后剩余 {len(filtered_articles)} 篇文章")
        
        # 打印关键词过滤后剩余文章的标题和时间
        # print("\n=== 关键词过滤后剩余文章列表 ===")
        # for i, article in enumerate(filtered_articles, 1):
        #     title = article.get("title", "无标题")
        #     pub_date = article.get("published_date", "无日期")
        #     print(f"{i}. 标题: {title}")
        #     print(f"   发布时间: {pub_date}")
        #     print("-" * 80)
        
        # 只保留昨天的文章
        yesterday_articles = filter_yesterday_articles(filtered_articles)
        logging.info(f"仅保留昨天的文章后剩余 {len(yesterday_articles)} 篇文章")
        
        # 保存文章并去重
        new_articles = article_storage.save_articles(yesterday_articles)
        logging.info(f"去重后有 {len(new_articles)} 篇新文章")
        
        # 发送邮件部分 
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
        
        logging.info("程序运行完成")
        return 0
    
    except Exception as e:
        logging.exception(f"程序运行出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
