# 热点猎手 (Hotspot Hunter) 项目计划

**日期**: 2026-05-24  
**阶段**: Phase 2 — 目录整理 + 核心代码脚手架 + 可运行 MVP

---

## Phase 1（已完成）

- [x] 设计文档整理 → `DESIGN_SPEC.md`
- [x] 项目脚手架目录（src/docs/tests/archive）
- [x] requirements.txt / README / CHANGELOG / .gitignore
- [x] git init + v0.1.0 tag

---

## Phase 2 任务列表

1. [x] 整理文件位置：`index.html` → `docs/prototype/index.html`
2. [x] 创建 `src/config.py`（平台配置、停用词、主题色）
3. [x] 创建 `src/models.py`（Article 数据结构）
4. [x] 实现 `src/storage/db.py`（SQLite CRUD）
5. [x] 实现 `src/crawler/`（base + 知乎/36氪/B站/百度）
6. [x] 实现 `src/analysis/word_freq.py`（中文词频 Top10）
7. [x] 实现 `src/ui/app.py`（Flet UI，对齐原型深色主题）
8. [x] 创建入口 `src/main.py` + 根目录 `hotspot_app.py`
9. [x] 更新 README.md、CHANGELOG.md（v0.2.0）
10. [x] git commit + tag v0.2.0

---

## Phase 3（待办）

- [ ] 各平台爬虫真实环境联调与选择器/API 修正
- [ ] 热度数值排序、导出 CSV
- [ ] 更多平台（微博、头条）
- [ ] Flet 手机端实测与 UI 微调

---

## 执行规则

- 工作目录：`/home/jwzhou/workspace/hothunter`
- 提交前更新 CHANGELOG，提交信息与 CHANGELOG 一致

---

## 当前状态

**Phase 2 已完成** — 可运行 MVP 就绪，Phase 3 待联调优化
