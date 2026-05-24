# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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
