# 研究论文追踪器项目结构设计

## 目录结构
```
research_paper_tracker/
├── config/
│   ├── config.yaml          # 主配置文件
│   ├── journals.yaml        # 期刊和数据库配置
│   └── keywords.yaml        # 关键词配置
├── src/
│   ├── __init__.py
│   ├── main.py              # 主程序入口
│   ├── config_manager.py    # 配置管理模块
│   ├── collectors/          # 数据采集模块
│   │   ├── __init__.py
│   │   ├── base_collector.py    # 基础采集器类
│   │   ├── api_collector.py     # API采集器
│   │   ├── rss_collector.py     # RSS采集器
│   │   └── web_collector.py     # 网页采集器
│   ├── filters/             # 过滤模块
│   │   ├── __init__.py
│   │   └── keyword_filter.py    # 关键词过滤器
│   ├── processors/          # 数据处理模块
│   │   ├── __init__.py
│   │   └── article_processor.py # 文章处理器
│   ├── storage/             # 存储模块
│   │   ├── __init__.py
│   │   └── article_storage.py   # 文章存储管理
│   ├── notifiers/           # 通知模块
│   │   ├── __init__.py
│   │   └── email_notifier.py    # 邮件通知器
│   └── utils/               # 工具模块
│       ├── __init__.py
│       ├── logger.py            # 日志工具
│       └── helpers.py           # 辅助函数
├── data/
│   ├── articles.db          # SQLite数据库（存储已处理文章）
│   └── logs/                # 日志目录
├── requirements.txt         # 依赖包列表
└── README.md                # 使用说明
```

## 模块设计

### 1. 配置管理模块 (config_manager.py)
- 负责加载和解析配置文件
- 提供统一的配置访问接口
- 支持配置热更新

### 2. 数据采集模块 (collectors/)
- **基础采集器 (base_collector.py)**：定义通用接口和方法
- **API采集器 (api_collector.py)**：处理各种API调用（arXiv、Springer Nature等）
- **RSS采集器 (rss_collector.py)**：处理RSS订阅源
- **网页采集器 (web_collector.py)**：处理需要网页爬取的数据源

### 3. 过滤模块 (filters/)
- **关键词过滤器 (keyword_filter.py)**：根据配置的关键词过滤文章

### 4. 数据处理模块 (processors/)
- **文章处理器 (article_processor.py)**：统一处理不同来源的文章数据

### 5. 存储模块 (storage/)
- **文章存储管理 (article_storage.py)**：管理文章存储和去重

### 6. 通知模块 (notifiers/)
- **邮件通知器 (email_notifier.py)**：生成和发送邮件通知

### 7. 工具模块 (utils/)
- **日志工具 (logger.py)**：提供日志记录功能
- **辅助函数 (helpers.py)**：提供通用辅助函数

## 数据流程
1. 主程序加载配置
2. 根据配置初始化各个采集器
3. 采集器获取原始数据
4. 过滤器根据关键词过滤文章
5. 处理器统一处理文章格式
6. 存储模块检查去重并保存文章
7. 通知模块生成并发送邮件通知

## 扩展性设计
- 采用插件式架构，便于添加新的数据源
- 配置文件分离，便于修改关键词和期刊列表
- 统一的数据结构，便于处理不同来源的数据
- 模块化设计，便于替换或升级单个组件
