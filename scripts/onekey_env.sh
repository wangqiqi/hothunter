#!/usr/bin/env bash
# 热点猎手 — 一键环境检查 / 安装 / 维护
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
# shellcheck source=scripts/pinned_build_env.sh
source "$ROOT_DIR/scripts/pinned_build_env.sh"

VENV_DIR="$ROOT_DIR/.venv"
REQ_FILE="$ROOT_DIR/requirements.txt"
PYPROJECT="$ROOT_DIR/pyproject.toml"
MIN_PYTHON="3.10"

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
fail()  { err "$*"; exit 1; }

usage() {
    echo -e "${BOLD}热点猎手 onekey_env.sh${NC}"
    cat <<'EOF'

用法:
  ./scripts/onekey_env.sh <command>
  ./scripts/onekey_env.sh              # 进入交互菜单

命令:
  check        检查 Python、虚拟环境、依赖是否就绪（不修改系统）
  install      创建 .venv 并安装全部依赖（首次推荐）
  sync         在已有 .venv 上同步 requirements.txt
  upgrade      升级 pip 与已安装包
  install-android-sdk  安装 Android SDK（build-apk 必需，默认 ~/Android/Sdk）
  install-jdk          检测系统 JDK 或下载 Temurin 17 到 .runtime（Gradle 用）
  doctor       完整环境诊断（check + 构建工具提示）
  freeze       输出当前环境 pip freeze
  clean        仅删除虚拟环境 .venv
  clear        清理多余 Android SDK / Gradle 缓存 / 构建残留，并规范 ~/.bashrc（可选 sudo）
  help         显示本帮助

环境变量:
  PYTHON       指定 Python 解释器（创建 venv 前生效）
  VENV_DIR     虚拟环境路径（默认 项目/.venv）

示例:
  ./scripts/onekey_env.sh check
  ./scripts/onekey_env.sh install && ./scripts/onekey_start.sh start
EOF
}

system_python() {
    if [[ -n "${PYTHON:-}" ]]; then
        echo "$PYTHON"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return
    fi
    command -v python
}

venv_python() {
    if [[ -x "$VENV_DIR/bin/python" ]]; then
        echo "$VENV_DIR/bin/python"
        return
    fi
    system_python
}

activate_venv_if_exists() {
    if [[ -f "$VENV_DIR/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
    fi
}

python_version_ok() {
    local py ver major minor
    py="$1"
    ver="$("$py" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null)" || return 1
    major="${ver%%.*}"
    minor="${ver#*.}"
    if [[ "$major" -lt 3 ]] || { [[ "$major" -eq 3 ]] && [[ "$minor" -lt 10 ]]; }; then
        return 1
    fi
    return 0
}

# 包名 -> import 名
import_name() {
    case "$1" in
        beautifulsoup4) echo bs4 ;;
        fake-useragent) echo fake_useragent ;;
        *) echo "${1//-/_}" ;;
    esac
}

read_requirements() {
    [[ -f "$REQ_FILE" ]] || fail "未找到 $REQ_FILE"
    grep -E '^[a-zA-Z0-9]' "$REQ_FILE" | grep -v '^#' || true
}

check_python() {
    local py="$1" issues=0
    echo -e "${BOLD}[Python]${NC}"
    if ! command -v "$py" >/dev/null 2>&1; then
        err "未找到 Python: $py"
        return 1
    fi
    echo "  路径:   $(command -v "$py" 2>/dev/null || echo "$py")"
    echo "  版本:   $($py --version 2>&1)"
    if python_version_ok "$py"; then
        ok "  版本满足 >= ${MIN_PYTHON}"
    else
        err "  需要 Python >= ${MIN_PYTHON}"
        issues=$((issues + 1))
    fi
    return "$issues"
}

check_venv() {
    local issues=0
    echo
    echo -e "${BOLD}[虚拟环境]${NC}"
    if [[ -d "$VENV_DIR" && -x "$VENV_DIR/bin/python" ]]; then
        ok "  已存在: $VENV_DIR"
        echo "  Python: $($VENV_DIR/bin/python --version 2>&1)"
    else
        warn "  未创建（运行 install）"
        issues=$((issues + 1))
    fi
    return "$issues"
}

check_packages() {
    local py="$1" line pkg imp issues=0 missing=()
    echo
    echo -e "${BOLD}[依赖包]${NC}"
    if [[ ! -f "$REQ_FILE" ]]; then
        err "  缺少 $REQ_FILE"
        return 1
    fi
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" ]] && continue
        pkg="${line%%[=<>!~]*}"
        pkg="${pkg// /}"
        [[ -z "$pkg" ]] && continue
        imp="$(import_name "$pkg")"
        if "$py" -c "import ${imp}" 2>/dev/null; then
            local ver
            ver="$("$py" -c "import importlib.metadata as m; print(m.version('${pkg}'))" 2>/dev/null \
                || "$py" -c "import ${imp}; print(getattr(${imp}, '__version__', 'ok'))" 2>/dev/null \
                || echo "ok")"
            ok "  ${pkg} (${ver})"
        else
            err "  ${pkg} — 未安装或无法 import (${imp})"
            missing+=("$pkg")
            issues=$((issues + 1))
        fi
    done < <(read_requirements)

    echo
    if "$py" -c "import flet" 2>/dev/null; then
        local fv
        fv="$("$py" -c "import flet; print(getattr(flet, '__version__', '?'))" 2>/dev/null || echo "?")"
        ok "  flet 模块版本: ${fv}"
        if "$py" -m flet --version >/dev/null 2>&1; then
            ok "  flet CLI: $($py -m flet --version 2>&1 | head -1)"
        else
            warn "  flet CLI 不可用（打包需 flet[all]，install 会安装）"
        fi
    else
        err "  flet 未安装"
        issues=$((issues + 1))
    fi

    if "$py" -c "import pytest" 2>/dev/null; then
        ok "  pytest 已安装"
    else
        warn "  pytest 未安装（test 命令需要，install 会安装）"
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo
        warn "缺失依赖: ${missing[*]}"
        info "修复: ./scripts/onekey_env.sh sync   或   install"
    fi
    return "$issues"
}

# 将常见位置的 Flutter 加入 PATH（供 build-apk 与 check 使用）
ensure_flutter_in_path() {
    if command -v flutter >/dev/null 2>&1; then
        return 0
    fi
    local d
    for d in \
        "${FLUTTER_HOME:-}" \
        "$HOME/flutter/3.24.5" \
        "$HOME/flutter/3.24.0" \
        "$HOME/flutter/stable" \
        "$HOME/flutter" \
        "$HOME/snap/flutter/common/flutter"; do
        [[ -n "$d" && -x "$d/bin/flutter" ]] || continue
        export PATH="$d/bin:$PATH"
        command -v flutter >/dev/null 2>&1 && return 0
    done
    return 1
}

flutter_install_hint() {
    cat <<'EOF'
  Flutter SDK 是 Flet 打包 APK/AAB 的必需依赖（>= 3.24，与 Flet 0.25 配套）。

  安装示例（Linux）:
    git clone https://github.com/flutter/flutter.git -b stable --depth 1 ~/flutter/stable
    echo 'export PATH="$HOME/flutter/stable/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
    flutter doctor

  接受 Android 许可（首次打包）:
    flutter doctor --android-licenses

  然后重新执行: ./scripts/onekey_start.sh build-apk
EOF
}

check_optional_tools() {
    echo
    echo -e "${BOLD}[可选 · 打包/安装]${NC}"
    ensure_flutter_in_path || true
    if command -v flutter >/dev/null 2>&1; then
        local fv
        fv="$(flutter --version 2>/dev/null | head -1)"
        ok "  Flutter: $fv"
        if [[ "$fv" != *"3.24."* ]]; then
            warn "  Flutter 应为 3.24.x（当前 PATH 可能为 stable）；打包请用: $HH_FLUTTER_HOME"
        elif [[ -x "$HH_FLUTTER_HOME/bin/flutter" ]]; then
            ok "  锁定 SDK: $HH_FLUTTER_HOME"
        fi
    else
        warn "  Flutter: 未安装（build-apk 必需）"
        flutter_install_hint | sed 's/^/    /'
    fi
    if command -v java >/dev/null 2>&1; then
        ok "  Java (PATH): $(java -version 2>&1 | head -1)"
        if command -v javac >/dev/null 2>&1; then
            ok "  javac (PATH): $(javac -version 2>&1)"
        else
            warn "  javac: 未在 PATH（Gradle 需要完整 JDK，不是 ecj）"
        fi
        local gh
        if gh="$(gradle_java_home 2>/dev/null || true)"; then
            ok "  Gradle 推荐 JAVA_HOME: $gh"
        else
            warn "  Gradle JDK: 未找到 Java 21/17（建议: sudo apt install openjdk-21-jdk）"
        fi
    else
        warn "  Java: 未安装（build-apk 需要 JDK 17+）"
    fi
  local android_home="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
    if [[ -d "$android_home/platforms" ]]; then
        ok "  Android SDK: $android_home"
    else
        warn "  Android SDK: 未安装（build-apk 必需，ANDROID_HOME）"
        echo "    安装: ./scripts/onekey_env.sh install-android-sdk"
    fi
    if command -v adb >/dev/null 2>&1; then
        ok "  ADB:  $(command -v adb)"
    else
        warn "  ADB:  未安装（install-apk 需要 platform-tools）"
    fi
}

cmd_check() {
    local py failed=0
    echo -e "${BOLD}=== 环境检查 ===${NC}"
    echo "项目: $ROOT_DIR"
    echo

    py="$(venv_python)"
    check_python "$py" || failed=1
    check_venv || failed=1

    if [[ -d "$VENV_DIR" ]]; then
        py="$VENV_DIR/bin/python"
    fi
    check_packages "$py" || failed=1
    check_optional_tools

    echo
    if [[ "$failed" -eq 0 ]]; then
        ok "环境检查通过，可运行 ./scripts/onekey_start.sh start"
        return 0
    fi
    warn "环境未就绪，建议: ./scripts/onekey_env.sh install"
    return 1
}

cmd_install() {
    info "工作目录: $ROOT_DIR"
    local syspy
    syspy="$(system_python)"
    if ! python_version_ok "$syspy"; then
        fail "系统 Python 版本过低，需要 >= ${MIN_PYTHON}，当前: $($syspy --version 2>&1)"
    fi
    if [[ ! -d "$VENV_DIR" ]]; then
        info "创建虚拟环境: $VENV_DIR"
        "$syspy" -m venv "$VENV_DIR"
    fi
    activate_venv_if_exists
    local py
    py="$VENV_DIR/bin/python"
    info "升级 pip / setuptools / wheel..."
    "$py" -m pip install -U pip setuptools wheel
    info "安装 requirements.txt ..."
    "$py" -m pip install -r "$REQ_FILE"
    info "安装开发依赖 (pytest)..."
    "$py" -m pip install pytest
    info "安装 Flet 完整工具链 (打包用)..."
    "$py" -m pip install "flet[all]==${HH_FLET_VERSION}" 2>/dev/null || "$py" -m pip install "flet==${HH_FLET_VERSION}"
    ok "安装完成: $($py --version), flet $($py -m flet --version 2>/dev/null | head -1 || echo unknown)"
    warn "首次 build-apk 会下载 JDK / Android SDK，请用 onekey_start.sh build-apk"
    echo
    cmd_check || true
}

cmd_sync() {
    if [[ ! -x "$VENV_DIR/bin/python" ]]; then
        warn "虚拟环境不存在，转为 install"
        cmd_install
        return
    fi
    activate_venv_if_exists
    local py="$VENV_DIR/bin/python"
    info "同步依赖 → $REQ_FILE"
    "$py" -m pip install -r "$REQ_FILE"
    "$py" -m pip install pytest 2>/dev/null || true
    ok "同步完成"
    cmd_check || true
}

cmd_upgrade() {
    activate_venv_if_exists
    local py
    py="$(venv_python)"
    if [[ ! -d "$VENV_DIR" ]]; then
        fail "请先 install"
    fi
    py="$VENV_DIR/bin/python"
    info "升级 pip..."
    "$py" -m pip install -U pip setuptools wheel
    info "升级 requirements 中的包..."
    "$py" -m pip install -U -r "$REQ_FILE"
    "$py" -m pip install -U pytest 2>/dev/null || true
    ok "升级完成"
    cmd_check || true
}

gradle_java_home() {
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
    return 1
}

cmd_install_jdk() {
    local sys
    if sys="$(gradle_java_home)"; then
        ok "系统已有 JDK，Gradle 建议使用: $sys"
        echo "  export JAVA_HOME=\"$sys\""
        echo "  export PATH=\"\$JAVA_HOME/bin:\$PATH\""
        "$sys/bin/javac" -version 2>&1 | sed 's/^/  /'
        return 0
    fi
    local jdk_dir="$ROOT_DIR/.runtime/jdk-17"
    if [[ -x "$jdk_dir/bin/javac" ]]; then
        ok "JDK 已存在: $jdk_dir"
        echo "  export JAVA_HOME=\"$jdk_dir\""
        echo "  export PATH=\"\$JAVA_HOME/bin:\$PATH\""
        return 0
    fi
    mkdir -p "$ROOT_DIR/.runtime"
    local tar="$ROOT_DIR/.runtime/temurin-jdk17.tar.gz"
    info "下载 Temurin JDK 17 → $jdk_dir"
    curl -fsSL -o "$tar" \
        "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse?project=jdk"
    local top
    top="$(tar -tzf "$tar" | sed -n '1{s#/.*##;p;q}')"
    rm -rf "$jdk_dir"
    tar -xzf "$tar" -C "$ROOT_DIR/.runtime"
    mv "$ROOT_DIR/.runtime/$top" "$jdk_dir"
    rm -f "$tar"
    ok "JDK 就绪: $jdk_dir"
    echo "  export JAVA_HOME=\"$jdk_dir\""
    echo "  export PATH=\"\$JAVA_HOME/bin:\$PATH\""
}

cmd_install_android_sdk() {
    local sdk_root="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
    info "安装 Android SDK → $sdk_root"
    mkdir -p "$sdk_root/cmdline-tools"
    if [[ ! -x "$sdk_root/cmdline-tools/latest/bin/sdkmanager" ]]; then
        local tmp
        tmp="$(mktemp -d)"
        curl -fsSL -o "$tmp/cmdline-tools.zip" \
            "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
        unzip -q "$tmp/cmdline-tools.zip" -d "$tmp"
        rm -rf "$sdk_root/cmdline-tools/latest"
        mkdir -p "$sdk_root/cmdline-tools"
        mv "$tmp/cmdline-tools" "$sdk_root/cmdline-tools/latest"
        rm -rf "$tmp"
        ok "已安装 command-line tools"
    else
        ok "command-line tools 已存在"
    fi
    export ANDROID_HOME="$sdk_root"
    export ANDROID_SDK_ROOT="$sdk_root"
    export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
    info "下载 platform-tools / build-tools / android-${HH_ANDROID_COMPILE_SDK:-35} ..."
    yes | sdkmanager --sdk_root="$sdk_root" \
        "platform-tools" \
        "platforms;android-${HH_ANDROID_COMPILE_SDK:-35}" \
        "build-tools;${HH_ANDROID_BUILD_TOOLS:-35.0.0}" \
        "cmdline-tools;latest" \
        "ndk;25.1.8937393" \
        || warn "sdkmanager 部分包可能已安装，继续..."
    if command -v flutter >/dev/null 2>&1; then
        info "接受 Android 许可 (flutter doctor --android-licenses)..."
        yes | flutter doctor --android-licenses >/dev/null 2>&1 || true
    fi
    ok "Android SDK 就绪: $sdk_root"
    echo "  建议加入 ~/.bashrc:"
    echo "    export ANDROID_HOME=\"$sdk_root\""
    echo "    export PATH=\"\$ANDROID_HOME/platform-tools:\$PATH\""
}

cmd_reinstall() {
    warn "将删除并重建: $VENV_DIR"
    if [[ -d "$VENV_DIR" ]]; then
        rm -rf "$VENV_DIR"
        ok "已删除旧虚拟环境"
    fi
    cmd_install
}

cmd_doctor() {
    echo -e "${BOLD}=== 环境诊断 (doctor) ===${NC}"
    cmd_check || true
    echo
    echo -e "${BOLD}[项目文件]${NC}"
    for f in "$REQ_FILE" "$PYPROJECT" "$ROOT_DIR/hotspot_app.py"; do
        if [[ -f "$f" ]]; then ok "  $(basename "$f")"; else err "  缺失 $f"; fi
    done
    echo
    echo -e "${BOLD}[磁盘]${NC}"
    if [[ -d "$VENV_DIR" ]]; then
        du -sh "$VENV_DIR" 2>/dev/null | awk '{print "  .venv 占用: " $1}' || true
    fi
    echo
    info "下一步: install → onekey_start.sh start → build-apk"
}

cmd_freeze() {
    activate_venv_if_exists
    local py
    py="$(venv_python)"
    if [[ ! -d "$VENV_DIR" ]]; then
        fail "无虚拟环境，请先 install"
    fi
    info "pip freeze ($VENV_DIR):"
    "$VENV_DIR/bin/python" -m pip freeze
}

# 规范 ~/.bashrc 中的 hothunter 构建环境变量（幂等）
ensure_bashrc_build_env() {
    local bashrc="$HOME/.bashrc"
    local marker="# hothunter build env"
    [[ -f "$bashrc" ]] || touch "$bashrc"
    if grep -qF 'flutter/stable' "$bashrc" 2>/dev/null; then
        sed -i '/flutter\/stable/d' "$bashrc"
        ok "  已从 ~/.bashrc 移除 flutter/stable 路径"
    fi
    if grep -qF "$marker" "$bashrc" 2>/dev/null; then
        ok "  ~/.bashrc 已含 hothunter 构建变量块"
        return 0
    fi
    cat >>"$bashrc" <<'EOF'

# hothunter build env (onekey_env.sh clear)
export ANDROID_BASE="${ANDROID_BASE:-$HOME/Android}"
export ANDROID_SDK_ROOT="${ANDROID_HOME:-$ANDROID_BASE/Sdk}"
export GRADLE_USER_HOME="${GRADLE_USER_HOME:-$ANDROID_BASE/.gradle}"
export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"
export HH_FLUTTER_HOME="$HOME/flutter/3.24.5"
_prepend_path "$JAVA_HOME/bin"
EOF
    ok "  已写入 ~/.bashrc: JAVA_HOME / ANDROID_SDK_ROOT / HH_FLUTTER_HOME"
}

cmd_clear() {
    local skip_build=false
    local do_apt=false
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-build) skip_build=true ;;
            --with-apt) do_apt=true ;;
            -h|--help)
                echo "用法: ./scripts/onekey_env.sh clear [--no-build] [--with-apt]"
                echo "  --no-build  保留 build/flutter/build/"
                echo "  --with-apt  sudo 卸载 openjdk-21-demo/source（需密码）"
                return 0
                ;;
        esac
        shift
    done

    echo -e "${BOLD}=== 清理多余构建环境 (clear) ===${NC}"
    local sdk_root="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
    local ndk_ver="${HH_NDK_VERSION:-25.1.8937393}"
    local compile_sdk="${HH_ANDROID_COMPILE_SDK:-35}"
    local build_tools="${HH_ANDROID_BUILD_TOOLS:-35.0.0}"

    ensure_bashrc_build_env

    # Gradle：停 daemon，删旧版本痕迹（GRADLE_USER_HOME 默认 ~/Android/.gradle）
    local gradle_home="${GRADLE_USER_HOME:-${ANDROID_BASE:-$HOME/Android}/.gradle}"
    info "停止 Gradle daemon ($gradle_home) ..."
    local gradle_bin=""
    gradle_bin="$(find "$gradle_home/wrapper/dists" -maxdepth 5 \
        -path "*/gradle-${HH_GRADLE_VERSION:-8.3}-all/*/gradle-*/bin/gradle" -executable 2>/dev/null | head -1 || true)"
    [[ -n "$gradle_bin" ]] && "$gradle_bin" --stop 2>/dev/null || true
    pkill -f 'org.gradle.launcher.daemon' 2>/dev/null || true
    for ver in 8.7 8.14; do
        [[ -d "$gradle_home/daemon/$ver" ]] && rm -rf "$gradle_home/daemon/$ver" && ok "  已删 $gradle_home/daemon/$ver"
    done
    [[ -d "$gradle_home/kotlin-profile" ]] && rm -rf "$gradle_home/kotlin-profile" && ok "  已删 $gradle_home/kotlin-profile"
    [[ -d "$gradle_home/.tmp" ]] && rm -rf "$gradle_home/.tmp" && ok "  已删 $gradle_home/.tmp"

    # Android SDK：补装锁定版本，再删多余
    if [[ -x "$sdk_root/cmdline-tools/latest/bin/sdkmanager" ]]; then
        export ANDROID_HOME="$sdk_root" ANDROID_SDK_ROOT="$sdk_root"
        export PATH="$sdk_root/cmdline-tools/latest/bin:$sdk_root/platform-tools:$PATH"
        info "确保 Android build-tools;${build_tools} ..."
        yes | sdkmanager --sdk_root="$sdk_root" \
            "build-tools;${build_tools}" \
            "platforms;android-${compile_sdk}" \
            "ndk;${ndk_ver}" 2>/dev/null \
            || warn "  sdkmanager 部分包可能已存在，继续..."
    else
        warn "  未找到 sdkmanager，跳过安装；可稍后: ./scripts/onekey_env.sh install-android-sdk"
    fi

    local p removed=0
    for p in \
        "$sdk_root/ndk/27.0.12077973" \
        "$sdk_root/platforms/android-31" \
        "$sdk_root/platforms/android-33" \
        "$sdk_root/platforms/android-34" \
        "$sdk_root/platforms/android-36" \
        "$sdk_root/build-tools/33.0.1" \
        "$sdk_root/build-tools/34.0.0"; do
        if [[ -e "$p" ]]; then
            rm -rf "$p"
            ok "  已删 $(basename "$(dirname "$p")")/$(basename "$p")"
            removed=$((removed + 1))
        fi
    done
    [[ "$removed" -eq 0 ]] && info "  Android SDK 无多余目录需删"

    # 项目 .runtime 残留
    for p in \
        "$ROOT_DIR/.runtime/temurin-jdk17.tar.gz" \
        "$ROOT_DIR/.runtime/build-apk.log" \
        "$ROOT_DIR/.runtime/build-apk-latest.log"; do
        [[ -f "$p" ]] && rm -f "$p" && ok "  已删 .runtime/$(basename "$p")"
    done

    if [[ "$skip_build" == false ]]; then
        if [[ -d "$ROOT_DIR/build/flutter/build" ]]; then
            rm -rf "$ROOT_DIR/build/flutter/build"
            ok "  已删 build/flutter/build/"
        fi
        if [[ -f "$ROOT_DIR/.runtime/apk_prepare.stamp" ]]; then
            rm -f "$ROOT_DIR/.runtime/apk_prepare.stamp"
            warn "  已删 apk_prepare.stamp → 下次需 prepare-apk"
        fi
    else
        info "  保留 build/flutter/build/（--no-build）"
    fi

    if [[ "$do_apt" == true ]]; then
        info "APT 精简 JDK 演示/源码包（需 sudo）..."
        sudo DEBIAN_FRONTEND=noninteractive apt-get remove -y --purge \
            openjdk-21-demo openjdk-21-source 2>/dev/null || warn "  apt 跳过或失败"
        sudo apt-get autoremove -y 2>/dev/null || true
    fi

    echo
    ok "clear 完成。建议: source ~/.bashrc && ./scripts/onekey_start.sh check-apk"
    if [[ -d "$sdk_root/build-tools/${build_tools}" ]]; then
        ok "  build-tools/${build_tools} 已就绪"
    else
        warn "  缺少 build-tools/${build_tools}，请: ./scripts/onekey_env.sh install-android-sdk"
    fi
}

cmd_clean() {
    if [[ -d "$VENV_DIR" ]]; then
        info "删除 $VENV_DIR"
        rm -rf "$VENV_DIR"
        ok "虚拟环境已删除"
    else
        warn "虚拟环境不存在"
    fi
}

interactive_menu() {
    while true; do
        echo
        echo -e "${BOLD}=== 热点猎手 · 环境菜单 ===${NC}"
        echo " 1) check      检查环境（只读）"
        echo " 2) install    创建 venv + 安装依赖"
        echo " 3) sync       同步 requirements"
        echo " 4) upgrade    升级已安装包"
        echo " 5) reinstall  重建虚拟环境"
        echo " 6) doctor     完整诊断"
        echo " 7) freeze     列出已装版本"
        echo " 8) clean      删除 .venv"
        echo " 9) clear      清理多余 SDK/Gradle/构建缓存"
        echo "10) help       帮助"
        echo " 0) exit       退出"
        echo
        read -r -p "请选择 [0-10]: " choice
        case "$choice" in
            1|check)      cmd_check || true ;;
            2|install)    cmd_install ;;
            3|sync)       cmd_sync ;;
            4|upgrade)    cmd_upgrade ;;
            5|reinstall)  cmd_reinstall ;;
            6|doctor)     cmd_doctor ;;
            7|freeze)     cmd_freeze ;;
            8|clean)      cmd_clean ;;
            9|clear)      cmd_clear ;;
            10|help|h)    usage ;;
            0|exit|q)     ok "再见"; break ;;
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
        check)        cmd_check ;;
        install)      cmd_install ;;
        sync)         cmd_sync ;;
        upgrade)      cmd_upgrade ;;
        reinstall)    cmd_reinstall ;;
        install-android-sdk) cmd_install_android_sdk ;;
        install-jdk)        cmd_install_jdk ;;
        doctor)       cmd_doctor ;;
        freeze)       cmd_freeze ;;
        clean)        cmd_clean ;;
        clear)        cmd_clear "${@:2}" ;;
        help|-h|--help) usage ;;
        *)
            err "未知命令: $cmd"
            usage
            exit 1
            ;;
    esac
}

main "$@"
