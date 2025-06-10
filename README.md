# PaperRadar使用说明

## 项目简介

PaperRadar是一个自动化工具，用于每天获取多个数据库和期刊中包含特定关键词的最新研究文章，并通过邮件发送给用户。该工具支持多种数据源（API、RSS、网页爬取），可以根据关键词过滤文章，避免重复推送，并支持后续扩展更多期刊和关键词。

## 功能特点

- 自动从多个数据源获取最新研究文章
- 支持API、RSS和网页爬取三种数据获取方式
- 根据配置的关键词过滤文章
- 避免重复推送已发送过的文章
- 通过邮件发送筛选后的文章（支持HTML格式）
- 支持配置多个关键词和数据源
- 支持设置为每日定时运行（通过cron或Windows计划任务）
- 完善的日志记录和错误处理


## 系统要求

- Python 3.6+
- 依赖包：requests, beautifulsoup4, feedparser, pyyaml, python-dateutil


## 安装步骤

1. 克隆或下载项目到本地
2. 安装依赖包：
```bash
pip install -r requirements.txt
```


## 配置说明

配置文件位于`config`目录下，包括：

### 1. 主配置文件 (config.yaml)

```yaml
# 邮件配置
email:
  sender: "your_email@example.com"  # 发件人邮箱
  password: "your_password"         # 邮箱密码或应用专用密码
  recipients:                       # 收件人邮箱列表
    - "recipient@example.com"
  smtp_server: "smtp.example.com"   # SMTP服务器
  smtp_port: 587                    # SMTP端口
  use_tls: true                     # 是否使用TLS加密

# 运行配置
run:
  frequency: "daily"                # 运行频率（daily, weekly）
  max_articles_per_source: 10       # 每个数据源最多获取的文章数
  max_articles_per_email: 50        # 每封邮件最多包含的文章数

# 存储配置
storage:
  database_path: "data/articles.db" # SQLite数据库路径
  retention_days: 30                # 文章保留天数

# 日志配置
logging:
  level: "INFO"                     # 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
  file: "data/logs/app.log"         # 日志文件路径
  max_size_mb: 10                   # 日志文件最大大小（MB）
  backup_count: 5                   # 保留的日志文件数量

# 代理配置（可选）
proxy:
  enabled: false                    # 是否启用代理
  http: "http://proxy.example.com:8080"
  https: "https://proxy.example.com:8080"
```


### 2. 关键词配置文件 (keywords.yaml)

```yaml
# 关键词列表
keywords:
  - "perovskite solar cell"
  - "indoor photovoltaics"
  - "wearable device"

# 关键词匹配设置
matching:
  case_sensitive: false     # 是否区分大小写
  whole_word: false         # 是否只匹配完整单词
  match_any: true           # 匹配任意一个关键词即可（true）或必须匹配所有关键词（false）
  include_fields:           # 在哪些字段中搜索关键词
    - "title"
    - "abstract"
    - "keywords"
```


### 3. 期刊和数据库配置文件 (journals.yaml)

该文件包含所有数据源的配置，分为API、RSS和网页爬取三种类型。您可以根据需要添加、修改或删除数据源。

## 使用方法

### 基本用法

```bash
python src/main.py
```

这将使用默认配置运行程序，从所有配置的数据源获取文章，过滤后通过邮件发送。

### 高级用法

```bash
# 指定配置目录
python src/main.py --config-dir /path/to/config

# 不发送邮件，仅收集和过滤文章
python src/main.py --no-email
```


## 设置定时任务

### Linux/Mac (使用cron)

1. 打开crontab编辑器：
```bash
crontab -e
```

2. 添加定时任务（每天早上8点运行）：
```
0 8 * * * cd /path/to/research_paper_tracker && python src/main.py >> data/logs/cron.log 2>&1
```


### Windows (使用计划任务)

1. 打开"任务计划程序"
2. 点击"创建基本任务"
3. 输入任务名称和描述
4. 选择"每天"作为触发器
5. 设置开始时间
6. 选择"启动程序"作为操作
7. 浏览并选择Python解释器路径
8. 在"添加参数"中输入`src/main.py`
9. 在"起始于"中输入项目目录路径
10. 完成设置

## 托管到 GitHub Actions 自动化运行

### 步骤一：添加 GitHub Actions 工作流

1. 在项目根目录下新建 `.github/workflows/daily.yml` 文件。
2. 粘贴以下内容：
```yaml
name: Daily Paper Tracker

on:
  schedule:
    - cron: '0 0 * * *'   # 每天0点UTC自动运行
  workflow_dispatch:       # 允许手动运行

jobs:
  run-tracker:
    runs-on: ubuntu-latest

    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置 Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.8'

      - name: 安装依赖
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: 运行主程序
        env:
          EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
        run: |
          python src/main.py
```

3. 推送 workflow 文件到 GitHub 仓库。

### 步骤二：配置邮箱账号和密码（Secrets）

1. 打开 GitHub 仓库页面，点击 `Settings` → `Secrets and variables` → `Actions`
2. 添加如下 Secrets：
    - `EMAIL_SENDER`：发件人邮箱（如 your_email@example.com）
    - `EMAIL_PASSWORD`：邮箱密码或应用专用密码

### 步骤三：运行和查看结果

- 每天定时自动运行，无需本地服务器。
- 也可在 GitHub Actions 页面手动点击 “Run workflow” 立即运行。
- 运行日志和状态可在 Actions 页面查看。


## 扩展指南

### 添加新的关键词

编辑`config/keywords.yaml`文件，在`keywords`列表中添加新的关键词。

### 添加新的期刊或数据库

编辑`config/journals.yaml`文件，根据数据源类型（API、RSS或网页）添加新的配置。

#### 添加API数据源示例：

```yaml
api_sources:
  new_api_source:
    name: "New API Source"
    type: "api"
    base_url: "https://api.example.com/search"
    search_params:
      query: "{keywords}"
      apiKey: "YOUR_API_KEY"
    parser: "custom_parser"
    rate_limit: 2
```


#### 添加RSS数据源示例：

```yaml
rss_sources:
  new_rss_source:
    name: "New RSS Source"
    type: "rss"
    url: "https://example.com/feed.rss"
    parser: "generic_rss_parser"
```


#### 添加网页爬取数据源示例：

```yaml
web_sources:
  new_web_source:
    name: "New Web Source"
    type: "web"
    base_url: "https://example.com/search"
    search_params:
      q: "{keywords}"
    parser: "custom_web_parser"
    rate_limit: 1
    headers:
      User-Agent: "Mozilla/5.0 ..."
    selectors:
      article_container: "div.result-item"
      title: "h2"
      abstract: "div.abstract"
      link: "h2 a"
```


### 自定义解析器

如果需要为新的数据源添加自定义解析器，可以在相应的采集器模块中添加新的解析方法。

## 故障排除

### 邮件发送失败

- 检查邮箱和密码是否正确
- 确认SMTP服务器和端口设置
- 如果使用Gmail，可能需要启用"不够安全的应用"或使用应用专用密码


### 数据采集失败

- 检查网络连接
- 确认API密钥是否有效
- 检查数据源URL是否正确
- 查看日志文件获取详细错误信息


### 没有找到匹配的文章

- 检查关键词设置
- 确认数据源配置正确
- 尝试放宽关键词匹配条件（如禁用whole_word选项）


## 日志和监控

日志文件默认保存在`data/logs/app.log`，可以通过查看日志了解程序运行状态和错误信息。

## 项目结构

```
research_paper_tracker/
├── config/                 # 配置文件目录
│   ├── config.yaml         # 主配置文件
│   ├── journals.yaml       # 期刊和数据库配置
│   └── keywords.yaml       # 关键词配置
├── src/                    # 源代码目录
│   ├── main.py             # 主程序入口
│   ├── config_manager.py   # 配置管理模块
│   ├── collectors/         # 数据采集模块
│   ├── filters/            # 过滤模块
│   ├── storage/            # 存储模块
│   ├── notifiers/          # 通知模块
│   └── utils/              # 工具模块
├── data/                   # 数据目录
│   ├── articles.db         # SQLite数据库
│   └── logs/               # 日志目录
├── requirements.txt        # 依赖包列表
└── README.md               # 使用说明
```


## 联系与支持

如有问题或需要支持，请联系lyao961013@gmail.com

---
