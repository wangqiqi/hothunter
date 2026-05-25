# 热点猎手 (Hotspot Hunter) 项目计划

**日期**: 2026-05-24  
**当前版本**: v0.13.0  
**阶段**: Phase 7 — 健壮性 / 边界值 / 异常处理

工作目录：`/home/jwzhou/workspace/hothunter`

---

## Phase 7：健壮性修复计划（代码审查结论）

> 来源：全项目 review（边界值、默认值、异常值、并发与配置）。  
> 原则：**先修崩溃与数据错，再修体验，最后补测试与文档。**

### P0 — 必须修（崩溃 / 数据错 / 线程安全）

| # | 任务 | 模块 | 问题摘要 | 状态 |
|---|------|------|----------|------|
| 7.1 | 后台线程 UI 更新改 `page.run_task` | `src/ui/app.py`, `src/ui/article_reader.py` | worker 内直接 `page.update()`，Flet 非线程安全 | [ ] |
| 7.2 | 抓取互斥：`threading.Lock` 或单 worker 队列 | `src/ui/app.py` | `is_fetching` 无锁，启动/整点/手动可重叠 | [ ] |
| 7.3 | 定制模式空关键词逻辑修正 | `src/ui/app.py`, `src/modes.py` | `(value or DEFAULT_KEYWORD)` 使「请输入关键词」校验失效，空输入仍抓 `AI` | [ ] |
| 7.4 | 自定义源 `sources.json` 校验 | `src/crawler/custom_sources.py`, `registry.py` | 缺 `url` 在 `build_custom_crawlers` 时 `KeyError`，import 即崩溃 | [ ] |
| 7.5 | B 站无效 URL 过滤 | `src/crawler/bilibili.py` | 无 bvid/aid 时生成 `.../avNone` | [ ] |

### P1 — 应修（数据质量 / 可维护性）

| # | 任务 | 模块 | 问题摘要 | 状态 |
|---|------|------|----------|------|
| 7.6 | 爬虫统一 URL 门禁 | `src/crawler/*.py` 或 `base.py` | 知乎/头条/36氪/贴吧等可入库 `url=""` | [ ] |
| 7.7 | `get_titles_by_keyword` 增加 LIMIT | `src/storage/db.py` | 词频分析全表拉 title，长期 OOM 风险 | [ ] |
| 7.8 | SQLite 并发：连接策略或锁 | `src/storage/db.py` | worker 写入与主线程读历史可能 `database is locked` | [ ] |
| 7.9 | 状态栏展示平台错误详情 | `src/ui/app.py` | `errors` 只显示平台名，不显示 `safe_fetch` 异常信息 | [ ] |
| 7.10 | `Article.from_row` 行长度校验 | `src/models.py` | schema 不一致时 `IndexError` | [ ] |
| 7.11 | 平台筛选精确匹配 | `src/utils/article_view.py` | `platform in a.platform` 子串误匹配 | [ ] |
| 7.12 | `baidu_hot` 响应结构防御 | `src/crawler/baidu_hot.py` | `content_blocks[0]` 非 dict 时整平台失败 | [ ] |

### P2 — 体验与加固

| # | 任务 | 模块 | 问题摘要 | 状态 |
|---|------|------|----------|------|
| 7.13 | 启动端口环境变量校验 | `src/main.py` | 非法 `HOTHUNTER_PORT` → `ValueError` 直接退出 | [ ] |
| 7.14 | `UserAgent` 懒加载 + fallback | `src/crawler/base.py` | 模块级 `UserAgent()` 失败拖垮全部请求 | [ ] |
| 7.15 | `get_history(limit)` 校验 `limit > 0` | `src/storage/db.py` | `LIMIT -1` 语义风险 | [ ] |
| 7.16 | 阅读器切换文章取消/序号加载 | `src/ui/article_reader.py` | 快速切换可能乱序更新摘要 | [ ] |
| 7.17 | 历史去重或按批清理策略 | `src/storage/db.py` | 仅 INSERT 无 dedup，库体积持续增长 | [ ] |
| 7.18 | 自定义源样式映射 | `src/ui/theme.py` | 自定义平台 badge 可能误匹配内置样式 | [ ] |
| 7.19 | `reload_crawlers()` 文档或设置页触发 | `registry.py`, UI | 改 `sources.json` 需重启，无热加载入口 | [ ] |

### Phase 7 测试补充

| # | 任务 | 说明 | 状态 |
|---|------|------|------|
| 7.T1 | `test_modes_keyword.py` | 定制空关键词 / 仅空格 / 默认词与 `storage_key` 一致 | [ ] |
| 7.T2 | `test_custom_sources_validate.py` | 缺 `url`、非法 `type` 不崩溃，跳过并记录 | [ ] |
| 7.T3 | `test_bilibili_url.py` | 无 bvid/aid 不产出条目 | [ ] |
| 7.T4 | `test_article_view_filter.py` | 平台筛选无子串误匹配 | [ ] |
| 7.T5 | `test_db_limits.py` | `get_titles_by_keyword` LIMIT、`from_row` 短行 | [ ] |

### Phase 7 验收标准

- [ ] `./scripts/onekey_start.sh start`：定制模式空关键词有明确提示且**不**静默抓 `AI`
- [ ] 故意写坏 `~/.hothunter/sources.json`（缺 `url`）：App 能启动，坏源被跳过
- [ ] 连续快速点「立即刷新」+ 等待整点：不出现双份结果覆盖
- [ ] 点击 B 站/知乎无链接条目：列表尽量不展示或阅读器友好提示
- [ ] `pytest tests/ -q` 全绿，且新增 Phase 7 相关用例

### Phase 7 发布

- [ ] 更新 `CHANGELOG.md` → v0.12.0
- [ ] `pyproject.toml` 版本号 → `0.12.0`
- [ ] `git tag v0.12.0`（用户确认后执行）

---

## Phase 6 任务（历史）

1. [x] 添加 `pyproject.toml`（Flet 打包配置 + 网络权限）
2. [x] 添加 `scripts/onekey_env.sh` + `onekey_start.sh`（环境 / 调试 / 打包）
3. [x] 更新 README 部署说明（APK 为主，Flet App 为辅）
4. [ ] 本地 `start` 调试 UI 验证（底栏隐现 + SafeArea + 返回顶部，待肉眼确认）
5. [ ] `build-apk` 首次构建实测
6. [ ] `手机 install-apk` 实测
7. [x] Flet UI 对齐 HTML 原型（首版）
8. [x] 列表排序与筛选，移除 CSV 导出 UI（v0.7.0）
9. [x] onekey_start 端口占用修复（v0.7.0）
10. [x] GitHub README + MIT LICENSE（v0.8.0）
11. [x] 底部导航 + 返回顶部 + iOS 深色主题（v0.8.0）
11b. [x] 底栏隐现（滚动/贴底/手势/悬停）+ SafeArea + 动态留白（v0.10.0）
11c. [x] 应用内阅读（摘要 + 内嵌 WebView / 浏览器兜底）（v0.11.0）
12. [x] 浅色/深色双主题 + 分组列表样式（v0.9.0）
13. [x] 应用图标 assets + 打包/窗口接入（v0.9.0）
14. [x] 必接平台 12 源 + 自定义 sources.json（v0.10.0）
15. [ ] 爬虫集成测试（mock 网络，`tests/test_crawlers_parse.py` 已部分覆盖）

---

## 一键脚本命令

### onekey_env.sh（环境）

| 命令 | 说明 |
|------|------|
| `check` | 检查 Python / venv / 依赖（只读） |
| `install` | 创建 `.venv` 并安装全部依赖 |
| `sync` | 同步 requirements.txt |
| `upgrade` / `reinstall` | 升级包 / 重建 venv |
| `doctor` | 完整诊断 |

```bash
./scripts/onekey_env.sh check
./scripts/onekey_env.sh install
```

### onekey_start.sh（运行 / 打包）

| 命令 | 说明 |
|------|------|
| `env` | 同 `onekey_env.sh install` |
| `start` | 本地 Flet 调试（热重载） |
| `stop` / `restart` | 停止 / 重启 |
| `status` | 进程、环境、构建产物 |
| `build-apk` | 打包 APK → `dist/apk/` |
| `build-aab` | 打包 AAB → `dist/aab/` |
| `build-all` | APK + AAB |
| `install-apk` | adb 安装到手机 |
| `clean` | 清理缓存 |

```bash
./scripts/onekey_start.sh env
./scripts/onekey_start.sh start      # 本地调试
./scripts/onekey_start.sh build-apk    # 打包
./scripts/onekey_start.sh install-apk  # 装到手机
```

---

## 刷新策略

| 触发方式 | 说明 |
|----------|------|
| 启动 | 打开 App 约 0.8s 后自动抓取 |
| 手动 | 点击「立即刷新」 |
| 整点 | 每小时 :00 自动抓取（Switch 可关） |

---

## 审查记录（摘要）

| 级别 | 典型项 |
|------|--------|
| 高 | UI 线程、`is_fetching` 竞态、定制关键词默认值、自定义源启动崩溃、B 站 avNone |
| 中 | 空 URL 入库、词频无 LIMIT、SQLite 锁、错误信息丢失、`from_row`、平台子串筛选 |
| 低 | 端口解析、UA 初始化、历史 dedup、阅读器竞态、自定义源热加载 |

详细条目见 Phase 7 任务表；实现时以 P0 → P1 → P2 顺序推进。
