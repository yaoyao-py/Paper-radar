"""
邮件通知模块 - 生成和发送邮件通知
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional

class EmailNotifier:
    """
    邮件通知器，负责生成和发送邮件通知
    """
    
    def __init__(self, email_config: Dict[str, Any]):
        """
        初始化邮件通知器
        
        Args:
            email_config: 邮件配置
        """
        self.sender = email_config.get('sender', '')
        self.password = email_config.get('password', '')
        self.recipients = email_config.get('recipients', [])
        self.smtp_server = email_config.get('smtp_server', '')
        self.smtp_port = email_config.get('smtp_port', 587)
        self.use_tls = email_config.get('use_tls', True)
        self.logger = logging.getLogger(__name__)
    
    def send_articles_email(self, articles: List[Dict[str, Any]], subject: Optional[str] = None) -> bool:
        """
        发送包含文章列表的邮件
        
        Args:
            articles: 文章列表
            subject: 邮件主题，默认为自动生成
            
        Returns:
            bool: 是否发送成功
        """
        if not articles:
            self.logger.info("没有文章需要发送，跳过邮件发送")
            return True
        
        # 生成邮件主题
        if subject is None:
            subject = f"最新研究文章更新 - {len(articles)} 篇文章"
        
        # 生成邮件内容
        html_content = self._generate_html_content(articles)
        text_content = self._generate_text_content(articles)
        
        # 发送邮件
        return self._send_email(subject, html_content, text_content)
    
    def _generate_html_content(self, articles: List[Dict[str, Any]]) -> str:
        """
        生成HTML格式的邮件内容
        
        Args:
            articles: 文章列表
            
        Returns:
            str: HTML格式的邮件内容
        """
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                }
                .article {
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #eee;
                }
                .article:last-child {
                    border-bottom: none;
                }
                .title {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                .journal {
                    color: #666;
                    font-style: italic;
                    margin-bottom: 5px;
                }
                .authors {
                    color: #444;
                    margin-bottom: 5px;
                }
                .abstract {
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
                .meta {
                    color: #777;
                    font-size: 0.9em;
                }
                a {
                    color: #0066cc;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <h1>最新研究文章更新</h1>
            <p>以下是根据您的关键词找到的最新研究文章：</p>
        """
        
        # 添加文章信息
        for article in articles:
            html += f"""
            <div class="article">
                <div class="title"><a href="{article['url']}">{article['title']}</a></div>
                <div class="journal">{article['journal']}</div>
            """
            
            if article['authors']:
                authors_text = ", ".join(article['authors'])
                html += f'<div class="authors">{authors_text}</div>'
            
            if article.get('published_date'):
                html += f'<div class="meta">发布日期: {article["published_date"]}</div>'
            
            if article.get('doi'):
                html += f'<div class="meta">DOI: {article["doi"]}</div>'
            
            if article['abstract']:
                html += f'<div class="abstract">{article["abstract"]}</div>'
            
            html += '</div>'
        
        html += """
            <p>此邮件由研究论文追踪器自动生成。</p>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_content(self, articles: List[Dict[str, Any]]) -> str:
        """
        生成纯文本格式的邮件内容
        
        Args:
            articles: 文章列表
            
        Returns:
            str: 纯文本格式的邮件内容
        """
        text = "最新研究文章更新\n\n"
        text += "以下是根据您的关键词找到的最新研究文章：\n\n"
        
        # 添加文章信息
        for i, article in enumerate(articles, 1):
            text += f"{i}. {article['title']}\n"
            text += f"   链接: {article['url']}\n"
            text += f"   期刊: {article['journal']}\n"
            
            if article['authors']:
                authors_text = ", ".join(article['authors'])
                text += f"   作者: {authors_text}\n"
            
            if article.get('published_date'):
                text += f"   发布日期: {article['published_date']}\n"
            
            if article.get('doi'):
                text += f"   DOI: {article['doi']}\n"
            
            if article['abstract']:
                text += f"   摘要: {article['abstract'][:200]}...\n"
            
            text += "\n"
        
        text += "此邮件由研究论文追踪器自动生成。"
        
        return text
    
    def _send_email(self, subject: str, html_content: str, text_content: str) -> bool:
        """
        发送邮件
        
        Args:
            subject: 邮件主题
            html_content: HTML格式的邮件内容
            text_content: 纯文本格式的邮件内容
            
        Returns:
            bool: 是否发送成功
        """
        if not self.sender or not self.password or not self.recipients or not self.smtp_server:
            self.logger.error("邮件配置不完整，无法发送邮件")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            
            # 添加纯文本和HTML内容
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)
            
            # 连接SMTP服务器并发送邮件
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.ehlo()
            
            if self.use_tls:
                server.starttls()
                server.ehlo()
            
            server.login(self.sender, self.password)
            server.sendmail(self.sender, self.recipients, msg.as_string())
            server.quit()
            
            self.logger.info(f"成功发送邮件到 {', '.join(self.recipients)}")
            return True
        except Exception as e:
            self.logger.error(f"发送邮件失败: {str(e)}")
            return False
