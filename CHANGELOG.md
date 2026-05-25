# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.15.0] - 2026-05-25

### Changed

- `docs/prototype/index.html`：按 Flet 实际界面重写静态原型（iOS 主题、实时流/定制模式、12 平台、分组列表、底栏与阅读层示意）
- `scripts/onekey_env.sh`：`clear` 与 `~/.bashrc` 使用 `ANDROID_BASE` / `GRADLE_USER_HOME`（默认 `~/Android/.gradle`），与锁定构建环境一致

## [0.14.0] - 2026-05-25

### Added

- `scripts/pinned_build_env.sh`：锁定 Flet / Flutter / AGP / Gradle / JDK 版本
- `docs/BUILD_ENV.md`：Android 打包环境矩阵与排错说明
- `prepare-apk` / `check-apk`：构建前环境检查与依赖预下载；`build-apk` 改为仅编译（需 prepare 戳记）
- 本地 Flet 模板 `.runtime/flet-build-template`，避免 GitHub 克隆失败清空 `build/flutter`
- `onekey_env.sh clear`：清理多余 Android SDK / Gradle 缓存 / 构建残留，并规范 `~/.bashrc` 构建变量

### Changed

- Python/Flet 固定为 **0.25.2**；`pyproject.toml` 增加 `serious_python`、`flet`、`file_picker` pubspec 覆盖
- Android **compileSdk 35**；SDK 安装目标为 `platforms;android-35`
- Android 构建链：**Flutter 3.24.5** + AGP 8.1.0 + Gradle 8.3 + Kotlin 1.8.22 + **JDK 21**
- Gradle 仓库仅走阿里云镜像（移除 `google()`/`mavenCentral()` 直连，避免 dl.google.com TLS/403）
- `onekey_env.sh`：`install-android-sdk` 安装 NDK 与 API 35；`clear` 保留锁定 SDK 仅删多余组件

## [0.13.0] - 2026-05-25

### Added

- `onekey_env.sh install-android-sdk`：一键安装 Android SDK（command-line tools、platform-34、build-tools）
- `scripts/gradle/aliyun-init.gradle`：Gradle 阿里云镜像说明（勿写入 `~/.gradle/init.gradle`）

### Changed

- `onekey_start.sh`：优先 Flutter 3.24.x；`build-apk` / `build-aab` 前置 Android SDK 检查
- Flet 打包失败时自动注入 Gradle 阿里云镜像并重试 `flutter build apk`
- 移除与 Flutter plugin-loader 冲突的 `~/.gradle/init.gradle`
- `lxml` 升级至 5.3.0；`pyproject.toml` 增加 `file_picker` 8.1.4 覆盖以兼容 Flet 0.25 + Flutter 3.24

## [0.12.0] - 2026-05-24

### Changed

- 抓取模式切换改为 `SegmentedButton`（选中主色底 + 白字，对比更清晰）
- 「选择平台」默认收起，标题行展示已选数量
- 列表排序、标题筛选、平台筛选移至「热点列表」标题区
- `onekey_env.sh` / `onekey_start.sh`：Flutter 路径探测与 `build-apk` 前置检查；README 补充 Flutter 说明

### Fixed

- 修复模式 Tab / 关键词框 `expand` 在 Column 内纵向撑满、界面只剩两块灰区域的问题

## [0.11.0] - 2026-05-24

### Added

- **应用内阅读**：点击条目进入全屏阅读层（自动摘要 + Android/iOS/macOS 内嵌「原页」WebView），支持返回、复制链接、浏览器打开
- `src/utils/article_content.py`、`src/ui/article_reader.py`、`tests/test_article_content.py`

### Fixed

- 修复 v0.10.0 列表点击回调与 `open_article` 签名不一致导致无法打开阅读页的问题

## [0.10.0] - 2026-05-24

### Added

- **必接平台扩展**：百度热搜、抖音、腾讯新闻、网易热点、贴吧热议（内置共 12 源，见 `docs/PLATFORMS.md`）
- **自定义媒体源**：`~/.hothunter/sources.json` 支持 JSON API / RSS（`sources.example.json`、`docs/CUSTOM_SOURCES.md`）
- 底部导航 **隐现交互**（下滑隐藏、上滑/回顶/近底/贴底热区唤出），桌面悬停底缘与移动端上滑手势
- `src/ui/nav_chrome.py`：滚动判定、内容留白、窗口尺寸（真机占满高度）
- `tests/test_crawlers_parse.py`、`tests/test_custom_sources.py`、`tests/test_nav_chrome.py`

### Changed

- 底栏改为 `Stack` 浮层 + `SafeArea`，列表底部留白随显隐动态调整
- `phone_shell` 纵向 `expand`，桌面仍固定 430×900 手机框
- 爬虫注册表合并内置源与用户自定义源（`src/crawler/registry.py`）

## [0.9.0] - 2026-05-24

### Added

- 应用图标 `assets/icon*.png`（雷达 + 火焰，1024×1024）及 `scripts/generate_icon.py`
- **浅色 / 深色双主题**：顶栏按钮一键切换，偏好写入 `~/.hothunter/settings.json`
- `tests/test_theme.py` 主题切换单元测试

### Changed

- 桌面窗口 / 任务栏 / APK 打包统一使用 `assets/icon.png`（`page.window.icon` + Flet adaptive icon）
- 热点列表改为 iOS 分组 UITableView 样式（单行 + 分隔线 + 右箭头）
- 顶栏去渐变装饰，按钮改为系统蓝实心 / 次级填充样式

## [0.8.0] - 2026-05-24

### Added

- 底部快速导航（热点 / 历史 / 分析 / 设置）与「返回顶部」浮动按钮
- [LICENSE](LICENSE)（MIT）
- GitHub 公开版 [README.md](README.md)（徽章、亮点、平台表、免责声明）

### Changed

- UI 主题切换为 **iOS 深色紧凑风格**（`src/config.py`、`src/ui/theme.py`）
- 紧凑间距与圆角 token，优化卡片与导航布局

## [0.7.0] - 2026-05-24

### Added

- 列表排序与筛选：热度升降、标题 A-Z、抓取时间、按平台（`src/utils/article_view.py`）
- 标题关键词、单平台过滤，结果计数显示 `筛选数 / 总数`

### Removed

- UI 移除「导出 CSV」按钮

### Changed

- `onekey_start.sh`：启动前清理 8550 端口占用，改用 `python hotspot_app.py`，增强启动校验
- `src/main.py`：支持 `HOTHUNTER_PORT` 环境变量

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
