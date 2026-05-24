# 热点猎手 (Hotspot Hunter) 项目计划

**日期**: 2026-05-24
**目标**: 合理整理设计文档，初始化项目脚手架，git 初始化

## 任务列表 (必须 >5 条，先写入 plan.md 审核)

1. 审核并整理用户提供的设计文档，生成结构化、精简的 `DESIGN_SPEC.md`（中文，合理分章节，去冗余，突出核心）。
2. 在根目录创建标准 Python/Flet 项目脚手架目录结构（src 布局、docs、tests、archive 等）。
3. 创建 `requirements.txt`（Flet, beautifulsoup4, fake-useragent, requests 等，带版本）。
4. 创建 `README.md`（项目简介、快速开始、功能列表）。
5. 初始化 git 仓库（`git init`），创建 `.gitignore`，并准备首次提交（但提交前必须更新 CHANGELOG.md）。
6. 创建 `CHANGELOG.md`（逆序，初始版本）。
7. （可选）创建基础代码框架文件（如 main.py 占位）。
8. 所有变更记录到 plan.md 和 CHANGELOG.md，符合用户规则 6,7,10。

## 执行规则提醒
- 每次 Shell/编辑前确认绝对路径 `/home/jwzhou/workspace/hothunter`
- 回答使用中文
- 任务完成后总结完成项 + 剩余项
- 提交前先更新 CHANGELOG.md 并打 tag
- 归档文件用 `archive/YYYYMMDD_HHMMSS_功能_模块说明.md`
- 不在其他项目目录执行 git

## 当前状态
- 工作目录: `/home/jwzhou/workspace/hothunter`
- 已完成：
  1. 整理设计文档 → DESIGN_SPEC.md（精简结构化）
  2. 创建 src/ docs/ tests/ archive/ 脚手架目录
  3. requirements.txt + .gitignore + README.md
  4. CHANGELOG.md (v0.1.0 初始)
  5. git init 完成
- 剩余任务：创建基础 main.py 占位、首次 git commit（需先打 tag）、用户确认后继续实现爬虫等
- 所有操作均在 `/home/jwzhou/workspace/hothunter` 绝对路径执行

**plan 已执行部分，等待用户反馈继续或调整！**