# 研究论文追踪器需求分析

## 用户需求
1. 自动获取多个数据库和期刊中包含特定关键词的最新研究文章
2. 通过邮件发送给指定邮箱
3. 每日定时运行

## 关键词列表
- perovskite solar cell
- indoor photovoltaics
- wearable device

## 目标数据源
1. Advanced Materials (AM)
2. Nature
3. Science
4. Nature Photonics
5. Advanced Functional Materials (AFM)
6. Advanced Energy Materials (AEM)
7. Energy & Environmental Science (EES)
8. ACS Applied Materials & Interfaces (AMI)
9. arXiv
10. ScienceDirect

## 功能需求
- 每天自动爬取这些期刊或数据库
- 提取包含上述关键词的最新文章（包括标题、摘要和链接）
- 将这些信息整理后通过邮件发送给指定邮箱
- 邮件格式可以是纯文本或HTML
- 支持后续扩展更多期刊和关键词
- 可设置为每日定时运行（支持cron或Windows计划任务）
- 可选地避免重复发送已推送过的文章

## 系统限制
- 系统不支持内置的定时任务功能，需要通过外部工具（如cron或Windows计划任务）实现定时运行
- 不同数据源的API和网页结构各不相同，需要针对性处理
- 部分数据源可能需要账号访问或有访问频率限制

## 技术方案概述
1. 使用Python作为主要开发语言
2. 采用模块化设计，便于后续扩展
3. 使用配置文件管理关键词和数据源
4. 实现文章去重机制
5. 支持HTML格式邮件，提供更好的阅读体验
6. 提供详细的使用说明，包括如何设置定时任务
