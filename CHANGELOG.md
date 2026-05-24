# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.6.0] - 2026-05-24

### Added

- `scripts/onekey_env.sh`：环境 check / install / sync / upgrade / doctor 等交互命令
- `pyproject.toml`：Flet Android 打包配置（网络权限、split_per_abi）
- `scripts/onekey_start.sh`：一键 start / stop / build-apk / install-apk 等（`env` 委托 onekey_env）
- 构建产物目录 `dist/apk/`、`dist/aab/`
- `src/ui/theme.py`、`src/ui/components.py`：对齐 HTML 原型的主题与组件

### Changed

- README：以 APK 打包为国内主推分发方式，补充 `onekey_env` / `onekey_start` 脚本说明
- **UI 重构**：430px 居中手机壳、渐变顶栏、搜索卡片、双列平台、彩色徽章、热词标签云、状态栏
- 设计规范移至 `docs/DESIGN_SPEC.md`

## [0.5.0] - 2026-05-24

### Added

- 启动时自动刷新（打开 App 后约 0.8s）
- 整点每小时自动刷新，Switch 可开关
- 状态栏显示刷新来源（启动/手动/整点）及下次整点时间
- `src/utils/refresh_scheduler.py` 整点调度工具

### Changed

- 「开始抓取」改为「立即刷新」
- 刷新进行中时跳过重复触发

## [0.4.0] - 2026-05-24

### Added

- **双抓取模式**：实时流热点 / 定制热点（`src/modes.py`）
- UI 模式切换（RadioGroup）、模式说明、百度「仅定制」提示
- 实时流历史与词频独立存储（`keyword=__stream__`）
- 4 个模式相关单元测试

### Changed

- 默认进入「实时流热点」模式
- `fetch_all` 支持 `mode` 参数，实时模式自动跳过百度搜索型平台

## [0.3.0] - 2026-05-24

### Added

- 微博热搜、今日头条热榜爬虫
- 热度数值解析与按热度排序（`src/utils/hot_sort.py`）
- CSV 导出（`src/storage/export.py`，默认 `~/.hothunter/exports/`）
- UI：导出按钮、按热度排序开关、空结果提示、分平台抓取计数

### Fixed

- 知乎：改用 `hot-list-web` API，解决 403
- 36氪：改用 Gateway POST API，解决页面无 `__NEXT_DATA__` 问题
- B站/百度：补充 Referer 请求头

### Changed

- `fetch_all` 返回各平台条数统计，默认按热度降序
- 平台扩展至 6 个（知乎、36氪、B站、百度、微博、头条）

## [0.2.0] - 2026-05-24

### Added

- 核心代码 MVP：爬虫、存储、分析、Flet UI
- `src/config.py` 平台配置与深色主题色
- `src/models.py` Article 数据模型
- `src/storage/db.py` SQLite CRUD（save / history / titles）
- `src/crawler/` 知乎、36氪、B站、百度四套爬虫 + 注册表
- `src/analysis/word_freq.py` 中文词频 Top10
- `src/ui/app.py` Flet 主界面（对齐原型深色主题）
- 入口：`src/main.py`、`hotspot_app.py`（手机 Flet App 可直接打开）
- `docs/prototype/index.html` UI 原型归档位置

### Changed

- `index.html` 从根目录移至 `docs/prototype/`
- 更新 README 项目结构与快速开始说明
- 更新 plan.md Phase 2 任务进度

## [0.1.0] - 2026-05-24

### Added

- 项目脚手架初始化（src 模块化目录、requirements、.gitignore）
- 设计文档整理为 DESIGN_SPEC.md
- plan.md 任务规划
- README.md 项目说明

### Changed

- 原始长设计文档精简整理（去除冗余、结构化中文规范）
