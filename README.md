# 热点猎手 Hotspot Hunter

**把多平台热榜装进手机 — 纯本地、可打包 APK、无需 Flet App**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/Flet-0.25-6366f1)](https://flet.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](tests/)

热点猎手是一款基于 **Python + Flet** 的移动端热点聚合工具：一次刷新，纵览知乎、微博、B 站等平台热榜；支持关键词定制、本地历史、热词分析与多种排序筛选。数据落在本机 SQLite，不依赖云端账号。

---

## 亮点

| | |
|---|---|
| **双模式抓取** | **实时流**：全平台当前热榜 · **定制**：按关键词过滤 / 百度搜索 |
| **6 大平台** | 知乎 · 36氪 · B站 · 微博 · 头条 · 百度新闻（定制） |
| **自动刷新** | 启动刷新 · 手动刷新 · 整点每小时（可关） |
| **本地优先** | SQLite 持久化 `~/.hothunter/articles.db`，历史可回看 |
| **列表掌控** | 热度 / 标题 / 时间 / 平台排序 + 标题与平台筛选 |
| **热词洞察** | 中文分词 + Top10 词频，快速感知话题密度 |
| **一键脚本** | 环境安装、本地调试、APK 打包、`adb` 安装 |
| **国内友好** | 独立 APK 分发，不依赖 Google Play 的 Flet App |

---

## 界面预览

iOS 风格移动端 UI（430px 手机壳）：**浅色 / 深色**一键切换（顶栏图标）、底栏快速导航、分组热点列表、热词标签云。主题偏好保存在 `~/.hothunter/settings.json`。

> 本地运行：`./scripts/onekey_start.sh start` 即可在桌面预览。

---

## 快速开始

### 环境要求

- Python **3.10+**
- Linux / macOS / Windows（开发）；Android（APK 运行）
- 打包 APK 时首次会自动拉取 JDK 17、Android SDK（耗时较长）

### 1. 克隆与安装

```bash
git clone https://github.com/YOUR_USERNAME/hothunter.git
cd hothunter
chmod +x scripts/onekey_env.sh scripts/onekey_start.sh

./scripts/onekey_env.sh install    # 创建 .venv 并安装依赖
```

### 2. 本地调试

```bash
./scripts/onekey_start.sh start    # 启动桌面窗口
./scripts/onekey_start.sh status   # 查看进程与端口
./scripts/onekey_start.sh stop       # 停止
```

无参数运行 `./scripts/onekey_start.sh` 或 `./scripts/onekey_env.sh` 进入**交互菜单**。

### 3. 打包安装到手机（推荐国内分发）

```bash
./scripts/onekey_start.sh build-apk      # 产物 → dist/apk/
./scripts/onekey_start.sh install-apk    # 需 adb + USB 调试
```

将 `dist/apk/` 下对应 ABI 的 APK 发给用户即可安装；无需应用商店、无需 Flet App。

### 手动运行（可选）

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python hotspot_app.py
```

---

## 脚本速查

### `onekey_env.sh` — 环境

| 命令 | 说明 |
|------|------|
| `check` | 检查 Python / venv / 依赖 |
| `install` | 创建 `.venv` 并安装依赖 |
| `sync` | 同步 `requirements.txt` |
| `doctor` | 完整诊断 |
| `upgrade` / `reinstall` | 升级或重建环境 |

### `onekey_start.sh` — 运行与打包

| 命令 | 说明 |
|------|------|
| `start` / `stop` / `restart` | 本地调试 |
| `status` / `logs` | 状态与日志 |
| `test` | `pytest` 单元测试 |
| `build-apk` / `build-aab` / `build-all` | Android 打包 |
| `install-apk` | adb 安装 |
| `clean` | 清理构建与运行时缓存 |

环境变量：`HOTHUNTER_PORT`（默认 `8550`）

---

## 支持平台

| 平台 | 实时流 | 定制热点 |
|------|:------:|:--------:|
| 知乎热榜 | ✅ | ✅ |
| 36氪 | ✅ | ✅ |
| B站热门 | ✅ | ✅ |
| 微博热搜 | ✅ | ✅ |
| 今日头条 | ✅ | ✅ |
| 百度新闻 | — | ✅（搜索） |

---

## 项目结构

```
hothunter/
├── assets/
│   ├── icon.png            # 应用图标（1024×1024）
│   └── icon_android.png    # Android adaptive 前景
├── hotspot_app.py          # 应用入口（调试 / 打包）
├── pyproject.toml          # 版本与 Flet Android 配置
├── scripts/
│   ├── onekey_env.sh       # 环境管理
│   ├── onekey_start.sh     # 调试 / 打包 / 安装
│   └── generate_icon.py    # 重新生成 assets/icon*.png
├── src/
│   ├── crawler/            # 各平台爬虫
│   ├── ui/                 # Flet 界面（对齐原型）
│   ├── storage/            # SQLite
│   ├── analysis/           # 词频分析
│   └── utils/              # 排序、筛选、调度
├── docs/
│   ├── DESIGN_SPEC.md      # 设计规范
│   └── prototype/          # HTML UI 原型
└── tests/
```

---

## 开发

```bash
./scripts/onekey_start.sh test
# 或
python -m pytest tests/ -q
```

变更记录见 [CHANGELOG.md](CHANGELOG.md)。

---

## 免责声明

本项目仅供学习与个人效率使用。请遵守各平台服务条款与 robots 协议，合理控制抓取频率；内容版权归各平台及原作者所有，本工具不托管、不分发第三方全文。

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源。

如果对你有帮助，欢迎 **Star** 支持后续迭代。
