#!/usr/bin/env bash
# 热点猎手 — 一键环境 / 调试 / 打包脚本
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
# shellcheck source=scripts/pinned_build_env.sh
source "$ROOT_DIR/scripts/pinned_build_env.sh"

RUNTIME_DIR="$ROOT_DIR/.runtime"
PID_FILE="$RUNTIME_DIR/hothunter.pid"
LOG_FILE="$RUNTIME_DIR/hothunter.log"
VENV_DIR="$ROOT_DIR/.venv"
APP_SCRIPT="$ROOT_DIR/hotspot_app.py"
DIST_APK_DIR="$ROOT_DIR/dist/apk"
DIST_AAB_DIR="$ROOT_DIR/dist/aab"
BUILD_CACHE_DIR="$ROOT_DIR/build"
DEFAULT_PORT="${HOTHUNTER_PORT:-8550}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERR]${NC} $*" >&2; }

usage() {
    echo -e "${BOLD}热点猎手 onekey_start.sh${NC}"
    cat <<'EOF'

用法:
  ./scripts/onekey_start.sh <command>
  ./scripts/onekey_start.sh              # 进入交互菜单

命令:
  env          创建/更新虚拟环境（委托 onekey_env.sh install）
  start        本地启动 Flet 调试（热重载，后台运行）
  stop         停止本地调试进程
  restart      重启本地调试
  status       查看运行状态、环境、构建产物
  logs         跟踪调试日志
  test         运行单元测试
  clean        清理运行时与构建缓存
  check-apk    检查 APK 构建环境是否就绪（只读）
  prepare-apk  预检 + 下载依赖 + 首次完整构建（生成戳记）
  build-apk    仅编译 APK（需先 prepare-apk）
  build-aab    打包 Android AAB（输出 dist/aab/）
  build-all    同时打包 APK + AAB
  install-apk  通过 adb 安装最新 APK 到已连接手机
  help         显示本帮助

环境变量:
  HOTHUNTER_PORT   本地调试端口（默认 8550）
  PYTHON           指定 Python 解释器

示例:
  ./scripts/onekey_start.sh env && ./scripts/onekey_start.sh start
  ./scripts/onekey_start.sh prepare-apk   # 首次或依赖变更后
  ./scripts/onekey_start.sh build-apk     # 日常快速打包
  ./scripts/onekey_start.sh install-apk
EOF
}

ensure_runtime_dir() {
    mkdir -p "$RUNTIME_DIR"
}

python_bin() {
    if [[ -n "${PYTHON:-}" ]]; then
        echo "$PYTHON"
        return
    fi
    if [[ -x "$VENV_DIR/bin/python" ]]; then
        echo "$VENV_DIR/bin/python"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return
    fi
    command -v python
}

activate_venv_if_exists() {
    if [[ -f "$VENV_DIR/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
    fi
}

port_pids() {
    local port="${1:-$DEFAULT_PORT}"
    if command -v ss >/dev/null 2>&1; then
        ss -tlnp 2>/dev/null | grep -E ":${port}[[:space:]]" | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p' || true
        return
    fi
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti ":$port" 2>/dev/null || true
        return
    fi
    fuser -n tcp "$port" 2>/dev/null || true
}

port_in_use() {
    [[ -n "$(port_pids "$DEFAULT_PORT" | head -1)" ]]
}

flet_app_pids() {
    pgrep -f "hotspot_app\\.py" 2>/dev/null || true
    pgrep -f "flet run.*hotspot_app" 2>/dev/null || true
}

kill_dev_servers() {
    local pid
    for pid in $(flet_app_pids); do
        kill "$pid" 2>/dev/null || true
    done
    pkill -f "flet.*localhost:${DEFAULT_PORT}" 2>/dev/null || true
    pkill -f "flet.*tcp://localhost:${DEFAULT_PORT}" 2>/dev/null || true
    for pid in $(port_pids "$DEFAULT_PORT"); do
        kill "$pid" 2>/dev/null || true
    done
    sleep 1
    for pid in $(flet_app_pids); do
        kill -9 "$pid" 2>/dev/null || true
    done
    pkill -9 -f "flet.*localhost:${DEFAULT_PORT}" 2>/dev/null || true
    for pid in $(port_pids "$DEFAULT_PORT"); do
        kill -9 "$pid" 2>/dev/null || true
    done
}

is_running() {
    [[ -f "$PID_FILE" ]] || return 1
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null && port_in_use
}

log_mark_start() {
    echo "===== $(date -Iseconds) start port=$DEFAULT_PORT =====" >>"$LOG_FILE"
}

log_has_start_error() {
    [[ -f "$LOG_FILE" ]] || return 1
    local block
    block="$(awk '/===== .* start port=/{buf=$0; next} {buf=buf ORS $0} END{print buf}' "$LOG_FILE")"
    echo "$block" | grep -qE 'Traceback|address already in use|OSError:' 2>/dev/null
}

cmd_env() {
    "$ROOT_DIR/scripts/onekey_env.sh" install
}

cmd_start() {
    ensure_runtime_dir
    if is_running; then
        warn "已在运行 (port=$DEFAULT_PORT)，请先 stop 或 restart"
        return 0
    fi
    if port_in_use; then
        warn "端口 $DEFAULT_PORT 被占用，正在清理旧进程..."
        kill_dev_servers
        sleep 1
    fi
    activate_venv_if_exists
    local py flet_bin
    py="$(python_bin)"
    if ! "$py" -c "import flet" 2>/dev/null; then
        err "未检测到 flet，请先执行: ./scripts/onekey_env.sh install"
        exit 1
    fi
    info "启动本地调试 (port=$DEFAULT_PORT)..."
    info "日志: $LOG_FILE"
    log_mark_start
    HOTHUNTER_PORT="$DEFAULT_PORT" nohup "$py" "$APP_SCRIPT" >>"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"
    sleep 4
    if is_running && ! log_has_start_error; then
        ok "已启动 port=$DEFAULT_PORT (PID $(cat "$PID_FILE"))，桌面窗口应已弹出"
        info "查看日志: ./scripts/onekey_start.sh logs"
    else
        err "启动失败（端口未监听或日志有报错），最近日志:"
        tail -n 30 "$LOG_FILE" 2>/dev/null || true
        kill_dev_servers
        rm -f "$PID_FILE"
        exit 1
    fi
}

cmd_stop() {
    local had_service=false
    if is_running || port_in_use; then
        had_service=true
    fi
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid="$(cat "$PID_FILE")"
        if kill -0 "$pid" 2>/dev/null; then
            info "停止 wrapper PID $pid ..."
            kill "$pid" 2>/dev/null || true
        fi
    fi
    kill_dev_servers
    rm -f "$PID_FILE"
    if $had_service; then
        ok "已停止（已释放端口 $DEFAULT_PORT）"
    else
        warn "未在运行"
    fi
}

cmd_restart() {
    info "重启调试服务..."
    cmd_stop
    sleep 1
    cmd_start
}

cmd_status() {
    echo -e "${BOLD}=== 热点猎手状态 ===${NC}"
    echo "项目目录: $ROOT_DIR"
    echo

    echo -e "${BOLD}[进程]${NC}"
    if is_running; then
        ok "调试服务运行中 port=$DEFAULT_PORT flet PID(s): $(flet_app_pids | tr '\n' ' ')"
        [[ -f "$PID_FILE" ]] && echo "  wrapper PID: $(cat "$PID_FILE")"
    else
        warn "调试进程未运行"
        if port_in_use; then
            warn "端口 $DEFAULT_PORT 仍被占用: PID $(port_pids "$DEFAULT_PORT" | tr '\n' ' ')"
            echo "  建议: ./scripts/onekey_start.sh stop"
        fi
    fi
    echo

    echo -e "${BOLD}[Python / Flet]${NC}"
    local py
    py="$(python_bin)"
    echo "Python: $($py --version 2>&1)"
    if "$py" -c "import flet" 2>/dev/null; then
        echo "Flet:   $("$py" -c "import flet; print(getattr(flet, '__version__', 'installed'))")"
    else
        warn "flet 未安装，请运行 env"
    fi
    if [[ -d "$VENV_DIR" ]]; then
        ok "虚拟环境: $VENV_DIR"
    else
        warn "虚拟环境: 未创建（可运行 env）"
    fi
    echo

    echo -e "${BOLD}[构建工具]${NC}"
    if command -v java >/dev/null 2>&1; then
        echo "Java:   $(java -version 2>&1 | head -1)"
    else
        warn "Java:   未检测到（build 时会自动安装 JDK 17）"
    fi
    if command -v adb >/dev/null 2>&1; then
        echo "ADB:    $(command -v adb)"
        adb devices 2>/dev/null | tail -n +2 || true
    else
        warn "ADB:    未安装（install-apk 需要 Android platform-tools）"
    fi
    echo

    echo -e "${BOLD}[构建产物]${NC}"
    local apk_count=0 aab_count=0
    if [[ -d "$DIST_APK_DIR" ]]; then
        apk_count="$(find "$DIST_APK_DIR" -name '*.apk' 2>/dev/null | wc -l | tr -d ' ')"
    fi
    if [[ -d "$DIST_AAB_DIR" ]]; then
        aab_count="$(find "$DIST_AAB_DIR" -name '*.aab' 2>/dev/null | wc -l | tr -d ' ')"
    fi
    echo "APK: $DIST_APK_DIR ($apk_count 个文件)"
    echo "AAB: $DIST_AAB_DIR ($aab_count 个文件)"
    find "$DIST_APK_DIR" -name '*.apk' 2>/dev/null | sort || true
    echo
}

cmd_logs() {
    ensure_runtime_dir
    if [[ ! -f "$LOG_FILE" ]]; then
        warn "暂无日志: $LOG_FILE"
        return 0
    fi
    info "跟踪 $LOG_FILE (Ctrl+C 退出)"
    tail -f "$LOG_FILE"
}

cmd_test() {
    activate_venv_if_exists
    local py
    py="$(python_bin)"
    info "运行单元测试..."
    "$py" -m pytest tests/ -q
}

cmd_clean() {
    info "清理运行时与构建缓存..."
    cmd_stop 2>/dev/null || true
    rm -rf "$RUNTIME_DIR" "$BUILD_CACHE_DIR" "$DIST_APK_DIR" "$DIST_AAB_DIR"
    find "$ROOT_DIR" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
    find "$ROOT_DIR" -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
    ok "清理完成"
}

flet_build_bin() {
    activate_venv_if_exists
    local py
    py="$(python_bin)"
    if "$py" -m flet build --help >/dev/null 2>&1; then
        echo "$py -m flet build"
    else
        echo "flet build"
    fi
}

ensure_flet_build_template() {
    local tpl="$ROOT_DIR/$HH_FLET_TEMPLATE_DIR"
    if [[ -f "$tpl/cookiecutter.json" ]]; then
        return 0
    fi
    mkdir -p "$ROOT_DIR/.runtime"
    info "下载 Flet 构建模板 → $tpl"
    if git clone --depth 1 -b "$HH_FLET_TEMPLATE_REF" \
        "https://github.com/flet-dev/flet-build-template.git" "$tpl" 2>/dev/null; then
        ok "模板已就绪（GitHub）"
        return 0
    fi
    warn "GitHub 直连失败，尝试镜像..."
    rm -rf "$tpl"
    git clone --depth 1 -b "$HH_FLET_TEMPLATE_REF" \
        "https://ghproxy.net/https://github.com/flet-dev/flet-build-template.git" "$tpl" \
        || git clone --depth 1 -b "$HH_FLET_TEMPLATE_REF" \
        "https://mirror.ghproxy.com/https://github.com/flet-dev/flet-build-template.git" "$tpl" \
        || fail "无法下载 flet-build-template，请检查网络或手动克隆到 $tpl"
    ok "模板已就绪（镜像）"
}

flet_build_apk_args() {
    local tpl="$ROOT_DIR/$HH_FLET_TEMPLATE_DIR"
    ensure_flet_build_template
    printf '%s\n' --template "$tpl" --template-ref "$HH_FLET_TEMPLATE_REF"
}

require_flutter_for_build() {
    # Flet 0.25 仅与 Flutter 3.24.x 兼容；勿用 stable/3.44（Material Theme API 不兼容）
    local d chosen=""
    for d in \
        "${FLUTTER_HOME:-}" \
        "$HH_FLUTTER_HOME" \
        "$HOME/flutter/3.24.5" \
        "$HOME/flutter/3.24.0"; do
        [[ -n "$d" && -x "$d/bin/flutter" ]] || continue
        chosen="$d"
        break
    done
    if [[ -z "$chosen" ]]; then
        err "未找到 Flutter 3.24.x（Flet 0.25 打包必需）。"
        echo
        echo "  安装: git clone -b 3.24.5 --depth 1 https://github.com/flutter/flutter.git ~/flutter/3.24.5"
        echo "  环境检查: ./scripts/onekey_env.sh check"
        exit 1
    fi
    export PATH="$chosen/bin:$PATH"
    if command -v flutter >/dev/null 2>&1; then
        info "Flutter SDK: $(flutter --version 2>/dev/null | head -1)"
    fi
}

patch_flutter_sdk_gradle_mirrors() {
    local flutter_root=""
    if command -v flutter >/dev/null 2>&1; then
        flutter_root="$(dirname "$(dirname "$(command -v flutter)")")"
    fi
    [[ -n "$flutter_root" && -f "$flutter_root/packages/flutter_tools/gradle/settings.gradle.kts" ]] || return 0
    python3 - "$flutter_root/packages/flutter_tools/gradle/settings.gradle.kts" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if "maven.aliyun.com" in text:
    sys.exit(0)

mirrors = (
    "        maven { url = uri(\"https://maven.aliyun.com/repository/google\") }\n"
    "        maven { url = uri(\"https://maven.aliyun.com/repository/public\") }\n"
    "        maven { url = uri(\"https://maven.aliyun.com/repository/gradle-plugin\") }\n"
)
plugin_mgmt = (
    "pluginManagement {\n"
    "    repositories {\n"
    + mirrors
    + "        gradlePluginPortal()\n"
    "        google()\n"
    "        mavenCentral()\n"
    "    }\n"
    "}\n\n"
)
needle = "    repositories {\n        google()"
insert = "    repositories {\n" + mirrors + "        google()"
if needle not in text:
    sys.exit(0)
text = text.replace(needle, insert)
if "pluginManagement" not in text and "dependencyResolutionManagement" in text:
    text = text.replace("dependencyResolutionManagement", plugin_mgmt + "dependencyResolutionManagement", 1)
path.write_text(text, encoding="utf-8")
print(f"patched {path}")
PY
}

patch_flutter_gradle_mirrors() {
    local android_dir="$ROOT_DIR/build/flutter/android"
    [[ -d "$android_dir" ]] || return 0
    HH_AGP_VERSION="${HH_AGP_VERSION}" HH_GRADLE_VERSION="${HH_GRADLE_VERSION}" HH_KOTLIN_VERSION="${HH_KOTLIN_VERSION}" \
    HH_ANDROID_COMPILE_SDK="${HH_ANDROID_COMPILE_SDK}" \
    JAVA_HOME="${JAVA_HOME:-}" \
    python3 - "$android_dir" <<'PY'
import os
import pathlib
import re
import sys

android = pathlib.Path(sys.argv[1])
AGP = os.environ.get("HH_AGP_VERSION", "8.1.0")
GRADLE = os.environ.get("HH_GRADLE_VERSION", "8.3")
KOTLIN = os.environ.get("HH_KOTLIN_VERSION", "1.8.22")
mirror = (
    "        maven { url 'https://maven.aliyun.com/repository/google' }\n"
    "        maven { url 'https://maven.aliyun.com/repository/public' }\n"
    "        maven { url 'https://maven.aliyun.com/repository/gradle-plugin' }\n"
)
before_project = """
// Pub 插件（如 file_picker）自带 buildscript 仅指向 mavenCentral，403 时无法解析 AGP
gradle.beforeProject { project ->
    def mirrorRepos = { handler ->
        handler.maven { url 'https://maven.aliyun.com/repository/google' }
        handler.maven { url 'https://maven.aliyun.com/repository/public' }
        handler.maven { url 'https://maven.aliyun.com/repository/gradle-plugin' }
    }
    mirrorRepos(project.buildscript.repositories)
    mirrorRepos(project.repositories)
}

"""

for name in ("build.gradle", "settings.gradle"):
    path = android / name
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    changed = False
    if "maven.aliyun.com" not in text and "        google()" in text:
        text = text.replace("        google()", mirror + "        google()")
        changed = True
    if name == "build.gradle" and "gradle.beforeProject" not in text:
        anchor = "rootProject.buildDir"
        if anchor in text:
            text = text.replace(
                f"\n{anchor}",
                f"\n{before_project}{anchor}",
                1,
            )
            changed = True
    for bad_repo in ("        google()\n", "        mavenCentral()\n"):
        if "maven.aliyun.com" in text and bad_repo in text:
            text = text.replace(bad_repo, "")
            changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
        print(f"patched {path.name}")

SDK = os.environ.get("HH_ANDROID_COMPILE_SDK", "35")
app_gradle = android / "app/build.gradle"
if app_gradle.is_file():
    text = app_gradle.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r"compileSdkVersion\s+flutter\.compileSdkVersion",
        f"compileSdkVersion {SDK}",
        text,
        count=1,
    )
    if n == 0:
        new_text, n = re.subn(
            r"compileSdk\s+flutter\.compileSdkVersion",
            f"compileSdk {SDK}",
            text,
            count=1,
        )
    if n and new_text != text:
        app_gradle.write_text(new_text, encoding="utf-8")
        print(f"patched app/build.gradle compileSdk -> {SDK}")

settings = android / "settings.gradle"
if settings.is_file():
    text = settings.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r'(id "com\.android\.application" version ")([^"]+)(" apply false)',
        rf'\g<1>{AGP}\3',
        text,
        count=1,
    )
    if n and new_text != text:
        settings.write_text(new_text, encoding="utf-8")
        print(f"patched settings.gradle AGP -> {AGP}")
    text = settings.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r'(id "org\.jetbrains\.kotlin\.android" version ")([^"]+)(" apply false)',
        rf'\g<1>{KOTLIN}\3',
        text,
        count=1,
    )
    if n and new_text != text:
        settings.write_text(new_text, encoding="utf-8")
        print(f"patched settings.gradle Kotlin -> {KOTLIN}")

wrapper = android / "gradle/wrapper/gradle-wrapper.properties"
if wrapper.is_file():
    text = wrapper.read_text(encoding="utf-8")
    gradle_url = f"https\\://services.gradle.org/distributions/gradle-{GRADLE}-all.zip"
    if gradle_url not in text:
        text = re.sub(
            r"distributionUrl=.*",
            f"distributionUrl={gradle_url}",
            text,
            count=1,
        )
        wrapper.write_text(text, encoding="utf-8")
        print(f"patched gradle-wrapper -> {GRADLE}")

props = android / "gradle.properties"
if props.is_file():
    text = props.read_text(encoding="utf-8")
    flag_items = []
    jhome = os.environ.get("JAVA_HOME", "")
    if jhome:
        flag_items.append((f"org.gradle.java.home={jhome}", "org.gradle.java.home"))
    flag_items.append(
        ("android.ndk.suppressMinSdkVersionError=21", "android.ndk.suppressMinSdkVersionError")
    )
    changed = False
    for line, key in flag_items:
        if key not in text:
            text = text.rstrip() + "\n" + line + "\n"
            changed = True
    if changed:
        props.write_text(text, encoding="utf-8")
        print("patched gradle.properties")

build_gradle = android / "build.gradle"
if build_gradle.is_file():
    text = build_gradle.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r"ext\.kotlin_version = '[^']+'",
        f"ext.kotlin_version = '{KOTLIN}'",
        text,
        count=1,
    )
    if n and new_text != text:
        build_gradle.write_text(new_text, encoding="utf-8")
        print(f"patched build.gradle kotlin -> {KOTLIN}")

if settings.is_file():
    text = settings.read_text(encoding="utf-8")
    if "org.jetbrains.kotlin.android" not in text:
        text = text.replace(
            f'    id "com.android.application" version "{AGP}" apply false\n',
            f'    id "com.android.application" version "{AGP}" apply false\n'
            f'    id "org.jetbrains.kotlin.android" version "{KOTLIN}" apply false\n',
            1,
        )
        settings.write_text(text, encoding="utf-8")
        print("patched settings.gradle kotlin plugin")
PY
}

project_version() {
    python3 - "$ROOT_DIR/pyproject.toml" <<'PY'
import pathlib, re, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
print(m.group(1) if m else "0.0.0")
PY
}

# Gradle/AGP 8.x 推荐 Java 17；避免默认选到 Java 25 或仅 JRE
resolve_gradle_java_home() {
    local d
    for d in \
        "${JAVA_HOME:-}" \
        "$HH_JAVA_HOME" \
        "/usr/lib/jvm/java-21-openjdk-amd64" \
        "/usr/lib/jvm/java-1.21.0-openjdk-amd64" \
        "/usr/lib/jvm/java-17-openjdk-amd64" \
        "/usr/lib/jvm/java-1.17.0-openjdk-amd64"; do
        [[ -n "$d" && -x "$d/bin/javac" ]] || continue
        echo "$d"
        return 0
    done
    if command -v javac >/dev/null 2>&1; then
        readlink -f "$(command -v javac)" | sed 's#/bin/javac$##'
        return 0
    fi
    return 1
}

ensure_jdk_for_gradle() {
    local jdk_home
    jdk_home="$(resolve_gradle_java_home || true)"
    if [[ -n "$jdk_home" ]]; then
        export JAVA_HOME="$jdk_home"
        export PATH="$JAVA_HOME/bin:$PATH"
        info "Gradle 使用 JAVA_HOME=$JAVA_HOME ($("$JAVA_HOME/bin/java" -version 2>&1 | head -1))"
        return 0
    fi
    local jdk_dir="$ROOT_DIR/.runtime/jdk-17"
    if [[ -x "$jdk_dir/bin/javac" ]]; then
        export JAVA_HOME="$jdk_dir"
        export PATH="$JAVA_HOME/bin:$PATH"
        return 0
    fi
    warn "未找到可用 JDK（需 javac）。可执行: sudo apt install openjdk-17-jdk"
    warn "或: ./scripts/onekey_env.sh install-jdk（下载到 .runtime/jdk-17）"
    bash "$ROOT_DIR/scripts/onekey_env.sh" install-jdk || return 1
    export JAVA_HOME="$jdk_dir"
    export PATH="$JAVA_HOME/bin:$PATH"
}

export_flutter_android_build_env() {
    require_flutter_for_build
    export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
    export ANDROID_SDK_ROOT="$ANDROID_HOME"
    export SERIOUS_PYTHON_SITE_PACKAGES="${SERIOUS_PYTHON_SITE_PACKAGES:-${HH_SERIOUS_PYTHON_SITE_PACKAGES:-$ROOT_DIR/build/site-packages}}"
    if [[ ! -d "$SERIOUS_PYTHON_SITE_PACKAGES" ]]; then
        warn "未找到 $SERIOUS_PYTHON_SITE_PACKAGES，请先完成 Flet 的 Python 打包步骤"
    fi
}

sync_android_local_properties() {
    local android_dir="$ROOT_DIR/build/flutter/android"
    local props="$android_dir/local.properties"
    [[ -d "$android_dir" ]] || return 0
    local flutter_sdk=""
    if command -v flutter >/dev/null 2>&1; then
        flutter_sdk="$(dirname "$(dirname "$(command -v flutter)")")"
    fi
    mkdir -p "$android_dir"
    {
        [[ -n "$flutter_sdk" ]] && echo "flutter.sdk=$flutter_sdk"
        echo "sdk.dir=$ANDROID_HOME"
    } >"$props"
}

flutter_retry_build_apk() {
    local version
    version="$(project_version)"
    [[ -d "$ROOT_DIR/build/flutter/android" ]] || {
        err "build/flutter 不存在，请先成功执行 flet build 或检查模板: $ROOT_DIR/$HH_FLET_TEMPLATE_DIR"
        return 1
    }
    ensure_jdk_for_gradle
    export_flutter_android_build_env
    patch_flutter_sdk_gradle_mirrors
    patch_flutter_gradle_mirrors
    sync_android_local_properties
    info "重试 flutter build apk（Gradle 阿里云镜像已注入）..."
    (
        cd "$ROOT_DIR/build/flutter"
        export ANDROID_HOME ANDROID_SDK_ROOT SERIOUS_PYTHON_SITE_PACKAGES JAVA_HOME PATH
        flutter build apk --split-per-abi --build-name "${version:-0.0.0}"
    ) || return 1
    mkdir -p "$DIST_APK_DIR"
    find "$ROOT_DIR/build/flutter/build/app/outputs/flutter-apk" -name '*.apk' -exec cp -f {} "$DIST_APK_DIR/" \;
    return 0
}

apk_prepare_stamp() {
    echo "$RUNTIME_DIR/apk_prepare.stamp"
}

apk_prepare_fingerprint() {
    {
        [[ -f "$ROOT_DIR/pyproject.toml" ]] && cat "$ROOT_DIR/pyproject.toml"
        [[ -f "$ROOT_DIR/requirements.txt" ]] && cat "$ROOT_DIR/requirements.txt"
        echo "sdk=${HH_ANDROID_COMPILE_SDK}"
        echo "flet=${HH_FLET_VERSION}"
    } | sha256sum | awk '{print $1}'
}

write_apk_prepare_stamp() {
    mkdir -p "$RUNTIME_DIR"
    apk_prepare_fingerprint >"$(apk_prepare_stamp)"
    ok "APK 构建环境已就绪（戳记: $(apk_prepare_stamp)）"
}

apk_prepare_ready() {
    local stamp want
    stamp="$(apk_prepare_stamp)"
    want="$(apk_prepare_fingerprint)"
    [[ -f "$stamp" ]] && [[ "$(cat "$stamp")" == "$want" ]] \
        && [[ -d "$ROOT_DIR/build/flutter/android" ]] \
        && [[ -d "$ROOT_DIR/build/site-packages" ]]
}

ensure_android_sdk() {
    unset GRADLE_OPTS
    if [[ -f "$HOME/.gradle/init.gradle" ]] && grep -q 'maven.aliyun.com' "$HOME/.gradle/init.gradle" 2>/dev/null; then
        rm -f "$HOME/.gradle/init.gradle"
        warn "已移除 ~/.gradle/init.gradle（与 Flutter Gradle 插件冲突）"
    fi
    ensure_jdk_for_gradle
    export_flutter_android_build_env
    export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
    export ANDROID_SDK_ROOT="$ANDROID_HOME"
    export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
    if [[ ! -d "$ANDROID_HOME/platforms/android-${HH_ANDROID_COMPILE_SDK}" ]]; then
        err "未找到 Android SDK platform android-${HH_ANDROID_COMPILE_SDK}"
        echo "  安装: ./scripts/onekey_env.sh install-android-sdk"
        exit 1
    fi
}

apply_android_build_patches() {
    patch_flutter_sdk_gradle_mirrors
    patch_flutter_gradle_mirrors
    sync_android_local_properties
}

prefetch_flutter_android_deps() {
    [[ -d "$ROOT_DIR/build/flutter/android" ]] || return 0
    apply_android_build_patches
    info "预拉取 Gradle / Maven 依赖（assembleRelease，仅需成功一次）..."
    (
        cd "$ROOT_DIR/build/flutter/android"
        export ANDROID_HOME ANDROID_SDK_ROOT JAVA_HOME PATH
        chmod +x gradlew 2>/dev/null || true
        ./gradlew assembleRelease --no-daemon -q
    ) || return 1
    ok "Gradle 依赖已缓存"
}

check_build_apk_env() {
    local ok_count=0 fail_count=0
    local py sdk_root

    echo -e "${BOLD}=== APK 构建环境检查 ===${NC}"
    py="$(python_bin)"
    sdk_root="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"

    if [[ -x "$py" ]] && "$py" -c "import flet" 2>/dev/null; then
        ok "  [通过] Python venv + flet==${HH_FLET_VERSION}"
        ok_count=$((ok_count + 1))
    else
        err "  [失败] Python venv + flet==${HH_FLET_VERSION}"
        fail_count=$((fail_count + 1))
    fi

    if [[ -x "$HH_FLUTTER_HOME/bin/flutter" ]]; then
        ok "  [通过] Flutter ${HH_FLUTTER_VERSION} @ $HH_FLUTTER_HOME"
        ok_count=$((ok_count + 1))
    else
        err "  [失败] Flutter ${HH_FLUTTER_VERSION} @ $HH_FLUTTER_HOME"
        fail_count=$((fail_count + 1))
    fi

    if resolve_gradle_java_home >/dev/null; then
        ok "  [通过] JDK 21+ (javac) → $(resolve_gradle_java_home)"
        ok_count=$((ok_count + 1))
    else
        err "  [失败] JDK 21+ (javac)"
        fail_count=$((fail_count + 1))
    fi

    if [[ -d "$sdk_root/platforms/android-${HH_ANDROID_COMPILE_SDK}" ]]; then
        ok "  [通过] Android SDK platform android-${HH_ANDROID_COMPILE_SDK}"
        ok_count=$((ok_count + 1))
    else
        err "  [失败] Android SDK platform android-${HH_ANDROID_COMPILE_SDK}（运行 install-android-sdk）"
        fail_count=$((fail_count + 1))
    fi

    if [[ -f "$ROOT_DIR/$HH_FLET_TEMPLATE_DIR/cookiecutter.json" ]]; then
        ok "  [通过] Flet 模板 $ROOT_DIR/$HH_FLET_TEMPLATE_DIR"
        ok_count=$((ok_count + 1))
    else
        err "  [失败] Flet 模板（prepare-apk 会自动下载）"
        fail_count=$((fail_count + 1))
    fi

    if apk_prepare_ready; then
        ok "  [通过] APK 预构建戳记（可执行 build-apk 仅编译）"
        ok_count=$((ok_count + 1))
    else
        warn "  [待办] APK 预构建戳记 → 运行: ./scripts/onekey_start.sh prepare-apk"
        fail_count=$((fail_count + 1))
    fi

    echo
    if [[ "$fail_count" -eq 0 ]]; then
        ok "全部检查通过（$ok_count 项）"
        return 0
    fi
    warn "$fail_count 项未就绪，$ok_count 项已通过"
    return 1
}

cmd_check_apk() {
    activate_venv_if_exists
    export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
    check_build_apk_env
}

cmd_prepare_apk() {
    activate_venv_if_exists
    local py build_cmd version
    py="$(python_bin)"
    if ! "$py" -c "import flet" 2>/dev/null; then
        err "请先运行: ./scripts/onekey_env.sh install"
        exit 1
    fi

    info "阶段 1/4：环境与 SDK 检查..."
    require_flutter_for_build
    ensure_android_sdk
    ensure_flet_build_template

    info "阶段 2/4：Flutter 引擎与 Dart 依赖预缓存..."
    flutter precache --android

    mkdir -p "$DIST_APK_DIR"
    build_cmd="$(flet_build_bin)"
    export FLET_CLI_SKIP_FLUTTER_DOCTOR="${FLET_CLI_SKIP_FLUTTER_DOCTOR:-1}"
    export_flutter_android_build_env
    apply_android_build_patches

    local -a flet_extra
    flet_extra=()
    while IFS= read -r arg; do flet_extra+=("$arg"); done < <(flet_build_apk_args)

    info "阶段 3/4：Flet 生成 Flutter 工程 + Python 包 + 首次 Gradle 依赖下载..."
    warn "此阶段会下载模板、pip 包与 Maven 依赖，耗时较长；完成后 build-apk 以编译为主。"
    # shellcheck disable=SC2086
    if ! env ANDROID_HOME="$ANDROID_HOME" ANDROID_SDK_ROOT="$ANDROID_SDK_ROOT" \
        JAVA_HOME="$JAVA_HOME" SERIOUS_PYTHON_SITE_PACKAGES="$SERIOUS_PYTHON_SITE_PACKAGES" \
        PATH="$PATH" \
        $build_cmd apk "$ROOT_DIR" -v -o "$DIST_APK_DIR" "${flet_extra[@]}"; then
        warn "Flet 首次构建未完全成功，尝试补丁后重试 Gradle..."
        apply_android_build_patches
        prefetch_flutter_android_deps || true
        flutter_retry_build_apk || {
            err "prepare-apk 失败，请查看日志: $LOG_FILE 或重新运行并重定向到 .runtime/build-apk.log"
            exit 1
        }
        mkdir -p "$DIST_APK_DIR"
        find "$ROOT_DIR/build/flutter/build/app/outputs/flutter-apk" -name '*.apk' -exec cp -f {} "$DIST_APK_DIR/" \;
    fi

    info "阶段 4/4：确认 Gradle 依赖缓存..."
    apply_android_build_patches
    prefetch_flutter_android_deps || warn "Gradle 预拉取未完全成功，build-apk 可能仍需联网"

    write_apk_prepare_stamp
    ok "prepare-apk 完成。后续请使用: ./scripts/onekey_start.sh build-apk"
    find "$DIST_APK_DIR" -name '*.apk' 2>/dev/null | sort || true
}

flutter_build_apk_only() {
    local version
    version="$(project_version)"
    [[ -d "$ROOT_DIR/build/flutter/android" ]] || fail "build/flutter 不存在，请先 prepare-apk"
    export_flutter_android_build_env
    apply_android_build_patches
    info "纯编译 flutter build apk（--build-name ${version}）..."
    (
        cd "$ROOT_DIR/build/flutter"
        export ANDROID_HOME ANDROID_SDK_ROOT SERIOUS_PYTHON_SITE_PACKAGES JAVA_HOME PATH
        flutter pub get
        flutter build apk --split-per-abi --build-name "${version}"
    ) || return 1
    mkdir -p "$DIST_APK_DIR"
    find "$ROOT_DIR/build/flutter/build/app/outputs/flutter-apk" -name '*.apk' -exec cp -f {} "$DIST_APK_DIR/" \;
    return 0
}

cmd_build_apk() {
    activate_venv_if_exists
    local py
    py="$(python_bin)"
    if ! "$py" -c "import flet" 2>/dev/null; then
        err "请先运行: ./scripts/onekey_env.sh install"
        exit 1
    fi

    if ! apk_prepare_ready; then
        err "尚未完成 APK 预构建（依赖未缓存或源码已变更）。"
        echo "  请先运行: ./scripts/onekey_start.sh prepare-apk"
        echo "  或检查:   ./scripts/onekey_start.sh check-apk"
        exit 1
    fi

    require_flutter_for_build
    ensure_android_sdk
    mkdir -p "$DIST_APK_DIR"
    info "打包 APK → $DIST_APK_DIR（仅编译，不重复下载环境）"
    export FLET_CLI_SKIP_FLUTTER_DOCTOR="${FLET_CLI_SKIP_FLUTTER_DOCTOR:-1}"
    flutter_build_apk_only || exit 1
    ok "APK 构建完成:"
    find "$DIST_APK_DIR" -name '*.apk' 2>/dev/null | sort || warn "未找到 apk 文件"
}

cmd_build_aab() {
    activate_venv_if_exists
    local py build_cmd
    py="$(python_bin)"
    if ! "$py" -c "import flet" 2>/dev/null; then
        err "请先运行: ./scripts/onekey_env.sh install"
        exit 1
    fi
    require_flutter_for_build
    ensure_android_sdk
    mkdir -p "$DIST_AAB_DIR"
    build_cmd="$(flet_build_bin)"
    info "打包 AAB → $DIST_AAB_DIR"
    warn "首次构建会下载 Android SDK / JDK，请耐心等待..."
    export FLET_CLI_SKIP_FLUTTER_DOCTOR="${FLET_CLI_SKIP_FLUTTER_DOCTOR:-1}"
    # shellcheck disable=SC2086
    $build_cmd aab "$ROOT_DIR" -v -o "$DIST_AAB_DIR"
    ok "AAB 构建完成:"
    find "$DIST_AAB_DIR" -name '*.aab' 2>/dev/null | sort || warn "未找到 aab 文件，请检查日志"
}

cmd_build_all() {
    cmd_build_apk
    cmd_build_aab
}

latest_apk() {
    find "$DIST_APK_DIR" -name '*.apk' -type f 2>/dev/null | sort | tail -1
}

cmd_install_apk() {
    if ! command -v adb >/dev/null 2>&1; then
        err "未找到 adb，请安装 Android platform-tools"
        exit 1
    fi
    local apk
    apk="$(latest_apk || true)"
    if [[ -z "$apk" ]]; then
        err "未找到 APK，请先运行: ./scripts/onekey_start.sh build-apk"
        exit 1
    fi
    local devices
    devices="$(adb devices | awk 'NR>1 && $2=="device"{print $1}' | wc -l | tr -d ' ')"
    if [[ "$devices" -eq 0 ]]; then
        err "未检测到已连接的 Android 设备（USB 调试已开启？）"
        adb devices
        exit 1
    fi
    info "安装 $apk"
    adb install -r "$apk"
    ok "安装完成"
}

interactive_menu() {
    while true; do
        echo
        echo -e "${BOLD}=== 热点猎手 交互菜单 ===${NC}"
        echo " 1) env        准备/更新环境"
        echo " 2) start      本地调试启动"
        echo " 3) stop       停止"
        echo " 4) restart    重启"
        echo " 5) status     状态"
        echo " 6) logs       查看日志"
        echo " 7) test       单元测试"
        echo " 8) check-apk   检查 APK 环境"
        echo " 9) prepare-apk 预构建（下载依赖）"
        echo "10) build-apk  仅编译 APK"
        echo "11) build-aab  打包 AAB"
        echo "12) build-all  打包全部"
        echo "13) install-apk 安装到手机"
        echo "14) clean      清理"
        echo " 0) exit       退出"
        echo
        read -r -p "请选择 [0-14]: " choice
        case "$choice" in
            1|env)        cmd_env ;;
            2|start)      cmd_start ;;
            3|stop)       cmd_stop ;;
            4|restart)    cmd_restart ;;
            5|status)     cmd_status ;;
            6|logs)       cmd_logs ;;
            7|test)       cmd_test ;;
            8|check-apk)   cmd_check_apk ;;
            9|prepare-apk) cmd_prepare_apk ;;
            10|build-apk)  cmd_build_apk ;;
            11|build-aab)  cmd_build_aab ;;
            12|build-all) cmd_build_all ;;
            13|install-apk) cmd_install_apk ;;
            14|clean)     cmd_clean ;;
            0|exit|q)     ok "再见"; break ;;
            help|h|\?)    usage ;;
            *)            warn "无效选项: $choice" ;;
        esac
    done
}

main() {
    local cmd="${1:-}"
    if [[ -z "$cmd" ]]; then
        interactive_menu
        return
    fi
    case "$cmd" in
        env)          cmd_env ;;
        start)        cmd_start ;;
        stop)         cmd_stop ;;
        restart)      cmd_restart ;;
        status)       cmd_status ;;
        logs)         cmd_logs ;;
        test)         cmd_test ;;
        clean)        cmd_clean ;;
        check-apk)    cmd_check_apk ;;
        prepare-apk)  cmd_prepare_apk ;;
        build-apk)    cmd_build_apk ;;
        build-aab)    cmd_build_aab ;;
        build-all)    cmd_build_all ;;
        install-apk)  cmd_install_apk ;;
        help|-h|--help) usage ;;
        *)
            err "未知命令: $cmd"
            usage
            exit 1
            ;;
    esac
}

main "$@"
