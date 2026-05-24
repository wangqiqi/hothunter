# 热点猎手 (Hotspot Hunter)

基于 **Flet + Python** 的纯本地移动端热点抓取与分析工具。

## 功能

- **双模式**：
  - **实时流热点** — 各平台当前热榜，全量抓取
  - **定制热点** — 按关键词过滤 / 百度搜索
- **自动刷新**：打开时刷新、手动刷新、整点每小时刷新（可关闭）
- **6 平台**：知乎、36氪、B站、微博、头条（实时）；百度新闻（仅定制）
- 关键词过滤 + SQLite 本地持久化（`~/.hothunter/articles.db`）
- 卡片式结果展示，点击跳转原文
- 列表多种排序（热度/标题/时间/平台）与标题、平台筛选
- 中文热词分析（正则分词 + Top10 词频）
- 历史记录回顾

## 项目结构

```
hothunter/
├── hotspot_app.py          # Flet App 入口（打包 / 本地调试）
├── pyproject.toml          # Flet 打包配置
├── scripts/
│   ├── onekey_env.sh       # 环境检查 / 安装 / 维护
│   └── onekey_start.sh     # 调试 / 打包 / 运行
├── src/
│   ├── main.py             # 桌面/开发入口
│   ├── config.py           # 平台、主题、停用词
│   ├── models.py           # Article 数据模型
│   ├── crawler/            # 各平台爬虫（6 个）
│   ├── storage/            # SQLite + CSV 导出
│   ├── analysis/           # 词频分析
│   ├── utils/              # 热度排序
│   └── ui/                 # Flet 界面
├── docs/prototype/         # HTML UI 原型
├── tests/
└── archive/
```

## 快速开始

### 一键脚本（推荐）

```bash
cd /home/jwzhou/workspace/hothunter
chmod +x scripts/onekey_env.sh scripts/onekey_start.sh

# 环境（首次或依赖变更）
./scripts/onekey_env.sh check          # 只检查，不改动
./scripts/onekey_env.sh install        # 创建 .venv + 安装依赖
./scripts/onekey_env.sh                # 无参数进入环境交互菜单

# 运行与打包
./scripts/onekey_start.sh start        # 本地调试（桌面窗口 + 热重载）
./scripts/onekey_start.sh status       # 查看状态
./scripts/onekey_start.sh build-apk    # 打包 APK → dist/apk/
./scripts/onekey_start.sh install-apk  # adb 安装到已连接手机
./scripts/onekey_start.sh              # 无参数进入运行交互菜单
```

**onekey_env.sh**：`check` `install` `sync` `upgrade` `reinstall` `doctor` `freeze` `clean`  
**onekey_start.sh**：`env`（同 install）`start` `stop` `restart` `status` `logs` `test` `clean` `build-apk` `build-aab` `build-all` `install-apk`

### 桌面开发（手动）

```bash
pip install -r requirements.txt
python hotspot_app.py
```

### 手机端（独立 APK，推荐国内分发）

1. 开发机执行 `./scripts/onekey_start.sh build-apk`
2. 将 `dist/apk/` 下 APK 传到手机安装（或 `install-apk`）
3. 首次 `build-apk` 会自动下载 JDK 17 / Android SDK，耗时较长

> **说明**：Flet App（Google Play 调试客户端）在国内应用商店不可用，正式使用请走 APK 打包。

### 运行测试

```bash
python -m pytest tests/ -q
```

## 设计文档

- [docs/DESIGN_SPEC.md](docs/DESIGN_SPEC.md) — 设计规范
- [docs/prototype/index.html](docs/prototype/index.html) — UI 原型

## 许可证

MIT
