#!/usr/bin/env bash
# 热点猎手 — 一键环境检查 / 安装 / 维护
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

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
  doctor       完整环境诊断（check + 构建工具提示）
  freeze       输出当前环境 pip freeze
  clean        仅删除虚拟环境 .venv
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
        ok "  Flutter: $(flutter --version 2>/dev/null | head -1)"
    else
        warn "  Flutter: 未安装（build-apk 必需）"
        flutter_install_hint | sed 's/^/    /'
    fi
    if command -v java >/dev/null 2>&1; then
        ok "  Java: $(java -version 2>&1 | head -1)"
    else
        warn "  Java: 未安装（build-apk 时 Flet 会自动下载 JDK 17）"
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
    "$py" -m pip install "flet[all]==0.25.0" 2>/dev/null || "$py" -m pip install "flet==0.25.0"
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
    info "下载 platform-tools / build-tools / android-34 ..."
    yes | sdkmanager --sdk_root="$sdk_root" \
        "platform-tools" "platforms;android-34" "build-tools;34.0.0" "cmdline-tools;latest" \
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
        echo " 9) help       帮助"
        echo " 0) exit       退出"
        echo
        read -r -p "请选择 [0-9]: " choice
        case "$choice" in
            1|check)      cmd_check || true ;;
            2|install)    cmd_install ;;
            3|sync)       cmd_sync ;;
            4|upgrade)    cmd_upgrade ;;
            5|reinstall)  cmd_reinstall ;;
            6|doctor)     cmd_doctor ;;
            7|freeze)     cmd_freeze ;;
            8|clean)      cmd_clean ;;
            9|help|h)     usage ;;
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
        doctor)       cmd_doctor ;;
        freeze)       cmd_freeze ;;
        clean)        cmd_clean ;;
        help|-h|--help) usage ;;
        *)
            err "未知命令: $cmd"
            usage
            exit 1
            ;;
    esac
}

main "$@"
