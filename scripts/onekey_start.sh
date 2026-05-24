#!/usr/bin/env bash
# 热点猎手 — 一键环境 / 调试 / 打包脚本
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

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
  build-apk    打包 Android APK（输出 dist/apk/）
  build-aab    打包 Android AAB（输出 dist/aab/）
  build-all    同时打包 APK + AAB
  install-apk  通过 adb 安装最新 APK 到已连接手机
  help         显示本帮助

环境变量:
  HOTHUNTER_PORT   本地调试端口（默认 8550）
  PYTHON           指定 Python 解释器

示例:
  ./scripts/onekey_start.sh env && ./scripts/onekey_start.sh start
  ./scripts/onekey_start.sh build-apk
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

is_running() {
    [[ -f "$PID_FILE" ]] || return 1
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    [[ -n "$pid" ]] || return 1
    kill -0 "$pid" 2>/dev/null
}

cmd_env() {
    "$ROOT_DIR/scripts/onekey_env.sh" install
}

cmd_start() {
    ensure_runtime_dir
    if is_running; then
        warn "已在运行 (PID $(cat "$PID_FILE"))，请先 stop 或 restart"
        return 0
    fi
    activate_venv_if_exists
    local py flet_bin
    py="$(python_bin)"
    if ! "$py" -c "import flet" 2>/dev/null; then
        err "未检测到 flet，请先执行: ./scripts/onekey_env.sh install"
        exit 1
    fi
    flet_bin="$("$py" -m flet --help >/dev/null 2>&1 && echo "$py -m flet" || echo flet)"
    info "启动本地调试 (port=$DEFAULT_PORT, 热重载)..."
    info "日志: $LOG_FILE"
    nohup bash -c "$flet_bin run \"$APP_SCRIPT\" -p $DEFAULT_PORT -r -d" \
        >>"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"
    sleep 2
    if is_running; then
        ok "已启动 PID $(cat "$PID_FILE")，桌面窗口应已弹出"
        info "查看日志: ./scripts/onekey_start.sh logs"
    else
        err "启动失败，最近日志:"
        tail -n 30 "$LOG_FILE" 2>/dev/null || true
        rm -f "$PID_FILE"
        exit 1
    fi
}

cmd_stop() {
    if ! is_running; then
        warn "未在运行"
        rm -f "$PID_FILE"
        return 0
    fi
    local pid
    pid="$(cat "$PID_FILE")"
    info "停止 PID $pid ..."
    kill "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    ok "已停止"
}

cmd_restart() {
    cmd_stop
    cmd_start
}

cmd_status() {
    echo -e "${BOLD}=== 热点猎手状态 ===${NC}"
    echo "项目目录: $ROOT_DIR"
    echo

    echo -e "${BOLD}[进程]${NC}"
    if is_running; then
        ok "调试进程运行中 PID $(cat "$PID_FILE") port=$DEFAULT_PORT"
    else
        warn "调试进程未运行"
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

cmd_build_apk() {
    activate_venv_if_exists
    local py build_cmd
    py="$(python_bin)"
    if ! "$py" -c "import flet" 2>/dev/null; then
        err "请先运行: ./scripts/onekey_env.sh install"
        exit 1
    fi
    mkdir -p "$DIST_APK_DIR"
    build_cmd="$(flet_build_bin)"
    info "打包 APK → $DIST_APK_DIR"
    warn "首次构建会下载 Android SDK / JDK，请耐心等待..."
    # shellcheck disable=SC2086
    $build_cmd apk "$ROOT_DIR" -v -o "$DIST_APK_DIR"
    ok "APK 构建完成:"
    find "$DIST_APK_DIR" -name '*.apk' 2>/dev/null | sort || warn "未找到 apk 文件，请检查日志"
}

cmd_build_aab() {
    activate_venv_if_exists
    local py build_cmd
    py="$(python_bin)"
    if ! "$py" -c "import flet" 2>/dev/null; then
        err "请先运行: ./scripts/onekey_env.sh install"
        exit 1
    fi
    mkdir -p "$DIST_AAB_DIR"
    build_cmd="$(flet_build_bin)"
    info "打包 AAB → $DIST_AAB_DIR"
    warn "首次构建会下载 Android SDK / JDK，请耐心等待..."
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
        echo " 8) build-apk  打包 APK"
        echo " 9) build-aab  打包 AAB"
        echo "10) build-all  打包全部"
        echo "11) install-apk 安装到手机"
        echo "12) clean      清理"
        echo " 0) exit       退出"
        echo
        read -r -p "请选择 [0-12]: " choice
        case "$choice" in
            1|env)        cmd_env ;;
            2|start)      cmd_start ;;
            3|stop)       cmd_stop ;;
            4|restart)    cmd_restart ;;
            5|status)     cmd_status ;;
            6|logs)       cmd_logs ;;
            7|test)       cmd_test ;;
            8|build-apk)  cmd_build_apk ;;
            9|build-aab)  cmd_build_aab ;;
            10|build-all) cmd_build_all ;;
            11|install-apk) cmd_install_apk ;;
            12|clean)     cmd_clean ;;
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
