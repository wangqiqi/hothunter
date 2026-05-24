# 热点猎手 (Hotspot Hunter)

基于 **Flet + Python** 的纯本地移动端热点抓取与分析工具。

## 功能

- 多平台热点抓取：知乎热榜、36氪、B站热门、百度新闻
- 关键词过滤 + SQLite 本地持久化
- 卡片式结果展示，点击跳转原文
- 中文热词分析（正则分词 + Top10 词频）
- 历史记录回顾

## 项目结构

```
hothunter/
├── hotspot_app.py          # 手机 Flet App 入口（Open File）
├── src/
│   ├── main.py             # 桌面/开发入口
│   ├── config.py           # 平台、主题、停用词
│   ├── models.py           # Article 数据模型
│   ├── crawler/            # 各平台爬虫
│   ├── storage/            # SQLite 存储
│   ├── analysis/           # 词频分析
│   └── ui/                 # Flet 界面
├── docs/prototype/         # HTML UI 原型
├── tests/
└── archive/
```

## 快速开始

### 桌面开发

```bash
cd /home/jwzhou/workspace/hothunter
pip install -r requirements.txt
python hotspot_app.py
# 或
python src/main.py
```

### 手机端（Flet App）

1. 安装 Flet App（Android / iOS）
2. 将 `hotspot_app.py` 及整个项目文件夹传到手机
3. Flet App → Open File → 选择 `hotspot_app.py`

## 数据存储

SQLite 数据库默认路径：`~/.hothunter/articles.db`

## 设计文档

- [DESIGN_SPEC.md](DESIGN_SPEC.md) — 设计规范
- [docs/prototype/index.html](docs/prototype/index.html) — UI 原型

## 许可证

MIT
