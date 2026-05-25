# 热点猎手 — 锁定构建环境

本仓库 **Flet 0.25.x** 仅与 **Flutter 3.24.x** 兼容；使用 `~/flutter/stable`（3.27+ / 3.44+）会导致 `TabBarTheme` / `CardTheme` 等 Material API 编译失败。

## 推荐版本矩阵

| 层级 | 锁定版本 | 说明 |
|------|----------|------|
| Python | 3.10+（开发） | `.venv` |
| Flet | **0.25.2** | `pip install flet[all]==0.25.2` |
| Flutter | **3.24.5** | `~/flutter/3.24.5`，**不要**用 stable |
| Android Gradle Plugin | **8.1.0** | 与 Flutter 3.24.5 模板一致 |
| Gradle | **8.3** | wrapper |
| Kotlin | **1.8.22** | settings + build.gradle |
| JDK | **21**（OpenJDK） | `JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64` |
| Android SDK | API **34** | `platforms;android-34` |
| NDK | **25.1.8937393** | serious_python / app |
| file_picker | **8.1.4** | `pyproject.toml` override |
| serious_python | **0.8.2** | 嵌入 Python 3.12 |

## 一键命令（推荐流程）

```bash
./scripts/onekey_env.sh install
./scripts/onekey_env.sh install-android-sdk   # 含 android-35
./scripts/onekey_env.sh clear                 # 清理多余 SDK/Gradle/构建缓存，规范 ~/.bashrc
./scripts/onekey_start.sh check-apk           # 只检查，不构建
./scripts/onekey_start.sh prepare-apk         # 预检 + 下载依赖 + 写戳记（首次必跑）
./scripts/onekey_start.sh build-apk            # 仅 flutter 编译，不重复拉环境
```

- `prepare-apk`：模板、Python 包、Gradle/Maven、Flutter 引擎一次下载完毕。
- `build-apk`：要求存在 `.runtime/apk_prepare.stamp` 且源码未变；只做 `flutter build apk`。
- 修改 `pyproject.toml` / `requirements.txt` 后需重新 `prepare-apk`。

## 环境变量（脚本自动设置）

见 `scripts/pinned_build_env.sh`。手动调试 Gradle 时需：

```bash
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH="$HOME/flutter/3.24.5/bin:$JAVA_HOME/bin:$PATH"
export ANDROID_HOME=~/Android/Sdk
export SERIOUS_PYTHON_SITE_PACKAGES="$(pwd)/build/site-packages"
```

## 国内网络

- Maven Central 可能 403：构建脚本会向根 `build.gradle` 与 Flutter SDK 注入 **阿里云 Maven**。
- **不要**写入 `~/.gradle/init.gradle`（与 Flutter plugin-loader 冲突）。

## 参考

- [Flet #4564 — build apk + Flutter 3.24](https://github.com/flet-dev/flet/issues/4564)
- [Flet #4629 — Flutter 3.27 不兼容](https://github.com/flet-dev/flet/issues/4629)
- [serious_python README — SERIOUS_PYTHON_SITE_PACKAGES](https://github.com/flet-dev/serious-python)
