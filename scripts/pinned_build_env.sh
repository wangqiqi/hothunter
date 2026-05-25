# 热点猎手 — 锁定 Android 打包工具链（单一来源，勿随意升级）
# 依据: Flet 0.25.x + Flutter 3.24.x 社区验证组合
# 参考: https://github.com/flet-dev/flet/issues/4564

# Python / Flet
export HH_FLET_VERSION="${HH_FLET_VERSION:-0.25.2}"
export HH_SERIOUS_PYTHON_VERSION="${HH_SERIOUS_PYTHON_VERSION:-0.8.2}"
export HH_FILE_PICKER_VERSION="${HH_FILE_PICKER_VERSION:-8.1.4}"

# Flutter（禁止使用 ~/flutter/stable 即 3.27+ / 3.44+）
export HH_FLUTTER_VERSION="${HH_FLUTTER_VERSION:-3.24.5}"
export HH_FLUTTER_HOME="${HH_FLUTTER_HOME:-$HOME/flutter/3.24.5}"

# Android Gradle（与 Flutter 3.24.5 模板一致）
export HH_AGP_VERSION="${HH_AGP_VERSION:-8.1.0}"
export HH_GRADLE_VERSION="${HH_GRADLE_VERSION:-8.3}"
export HH_KOTLIN_VERSION="${HH_KOTLIN_VERSION:-1.8.22}"
# 固定 API 35（flutter_plugin_android_lifecycle 要求），勿用环境变量覆盖
export HH_ANDROID_COMPILE_SDK=35
export HH_ANDROID_BUILD_TOOLS=35.0.0
export HH_NDK_VERSION="${HH_NDK_VERSION:-25.1.8937393}"

# JDK：Gradle 需完整 JDK；优先 21（17 headless 在部分环境无 JAVA_COMPILER）
export HH_JAVA_HOME="${HH_JAVA_HOME:-/usr/lib/jvm/java-21-openjdk-amd64}"

# serious_python Android 打包
export HH_SERIOUS_PYTHON_SITE_PACKAGES="${HH_SERIOUS_PYTHON_SITE_PACKAGES:-}"
export HH_FLET_TEMPLATE_DIR="${HH_FLET_TEMPLATE_DIR:-.runtime/flet-build-template}"
export HH_FLET_TEMPLATE_REF="${HH_FLET_TEMPLATE_REF:-0.25.0}"
