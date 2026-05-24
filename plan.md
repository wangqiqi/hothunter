# 热点猎手 (Hotspot Hunter) 项目计划

**日期**: 2026-05-24  
**阶段**: Phase 6 — 双主题 UI + 应用图标（v0.9.0）

---

## Phase 6 任务

1. [x] 添加 `pyproject.toml`（Flet 打包配置 + 网络权限）
2. [x] 添加 `scripts/onekey_env.sh` + `onekey_start.sh`（环境 / 调试 / 打包）
3. [x] 更新 README 部署说明（APK 为主，Flet App 为辅）
4. [ ] 本地 `start` 调试 UI 验证（已加底部导航与返回顶部，待肉眼确认）
5. [ ] `build-apk` 首次构建实测
6. [ ] 手机 `install-apk` 实测
7. [x] Flet UI 对齐 HTML 原型（首版）
8. [x] 列表排序与筛选，移除 CSV 导出 UI（v0.7.0）
9. [x] onekey_start 端口占用修复（v0.7.0）
10. [x] GitHub README + MIT LICENSE（v0.8.0）
11. [x] 底部导航 + 返回顶部 + iOS 深色主题（v0.8.0）
12. [x] 浅色/深色双主题 + 分组列表样式（v0.9.0）
13. [x] 应用图标 assets + 打包/窗口接入（v0.9.0）
14. [ ] 爬虫集成测试（mock 网络）

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

工作目录：`/home/jwzhou/workspace/hothunter`
