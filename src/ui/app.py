"""Flet 主界面 — 对齐 docs/prototype 深色主题。"""

from __future__ import annotations

import threading
import time

import flet as ft

from src.analysis.word_freq import analyze_titles
from src.config import DEFAULT_KEYWORD, PLATFORMS, SEARCH_ONLY_PLATFORMS, THEME
from src.crawler.registry import fetch_all
from src.models import Article
from src.modes import FetchMode, MODE_LABELS, analysis_keyword, storage_key
from src.storage.db import ArticleStore
from src.ui import components as ui
from src.ui.theme import APP_MAX_WIDTH, BORDER
from src.utils.article_view import ALL_PLATFORMS, DEFAULT_SORT, SORT_OPTIONS, apply_view
from src.utils.refresh_scheduler import format_next_hour, seconds_until_next_hour


def run_app(page: ft.Page) -> None:
    page.title = "热点猎手"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = THEME["bg_primary"]
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.window.width = APP_MAX_WIDTH
    page.window.height = 900
    page.window.min_width = APP_MAX_WIDTH
    page.window.max_width = APP_MAX_WIDTH

    store = ArticleStore()
    platform_states: dict[str, bool] = {p["id"]: True for p in PLATFORMS}
    raw_articles: list[Article] = []
    current_keyword = DEFAULT_KEYWORD
    current_mode = FetchMode.STREAM
    is_fetching = False
    stop_scheduler = threading.Event()

    mode_hint = ft.Text("", color=THEME["text_muted"], size=12)
    refresh_hint = ft.Text("", color=THEME["text_muted"], size=12)
    mode_tabs_host = ft.Container()

    keyword_field = ft.TextField(
        value=DEFAULT_KEYWORD,
        label="搜索关键词",
        hint_text="输入关注的主题词，如 AI、新能源",
        border_color="transparent",
        focused_border_color=THEME["primary"],
        bgcolor=THEME["bg_card"],
        color=THEME["text_primary"],
        text_size=16,
        border_radius=12,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        expand=True,
        visible=False,
        disabled=True,
    )

    hourly_refresh_switch = ft.Switch(
        label="整点自动刷新（每小时）",
        value=True,
        active_color=THEME["primary"],
        label_style=ft.TextStyle(color=THEME["text_secondary"], size=13),
    )

    status_message = ft.Text("就绪", size=13, color=THEME["text_secondary"], expand=True)
    status_count = ft.Text("", size=13, weight=ft.FontWeight.W_600, color=THEME["primary_light"])
    status_dot = ft.Container(width=10, height=10, border_radius=5, bgcolor=THEME["text_muted"])

    results_count_text = ft.Text("0 条结果", size=12, color=THEME["text_muted"])
    results_header = ft.Row(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.ARTICLE, size=22, color=THEME["primary_light"]),
                    ft.Text("热点列表", size=18, weight=ft.FontWeight.BOLD, color=THEME["text_primary"]),
                ],
                spacing=8,
            ),
            ft.Container(
                content=results_count_text,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                bgcolor=THEME["bg_card"],
                border_radius=20,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    results_column = ft.Column(spacing=12)
    analysis_wrap = ft.Row(wrap=True, spacing=10, run_spacing=10)

    sort_dropdown = ft.Dropdown(
        label="排序方式",
        value=DEFAULT_SORT,
        options=[ft.dropdown.Option(key, label) for key, label in SORT_OPTIONS.items()],
        border_color=BORDER,
        focused_border_color=THEME["primary"],
        bgcolor=THEME["bg_card"],
        color=THEME["text_primary"],
        expand=True,
    )

    list_filter_field = ft.TextField(
        label="标题筛选",
        hint_text="在当前结果中按标题关键词过滤",
        border_color="transparent",
        focused_border_color=THEME["primary"],
        bgcolor=THEME["bg_card"],
        color=THEME["text_primary"],
        border_radius=12,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
        expand=True,
    )

    platform_filter = ft.Dropdown(
        label="平台筛选",
        value=ALL_PLATFORMS,
        options=[ft.dropdown.Option(ALL_PLATFORMS, "全部平台")]
        + [ft.dropdown.Option(p["name"], p["name"]) for p in PLATFORMS],
        border_color=BORDER,
        focused_border_color=THEME["primary"],
        bgcolor=THEME["bg_card"],
        color=THEME["text_primary"],
        expand=True,
    )

    fetch_btn_content = ft.Row(
        [
            ft.Icon(ft.Icons.REFRESH, size=20, color="#ffffff"),
            ft.Text("立即刷新", size=15, weight=ft.FontWeight.W_600, color="#ffffff"),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
    )
    fetch_btn = ft.Container(
        content=fetch_btn_content,
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=[THEME["primary"], THEME["primary_dark"]],
        ),
        border_radius=14,
        padding=ft.padding.symmetric(vertical=16, horizontal=20),
        expand=True,
        ink=True,
    )

    history_btn = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.HISTORY, size=20, color=THEME["text_primary"]),
                ft.Text("历史", size=15, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=THEME["bg_card"],
        border=ft.border.all(2, BORDER),
        border_radius=14,
        padding=ft.padding.symmetric(vertical=16, horizontal=20),
        expand=True,
        ink=True,
    )

    platform_chips: dict[str, ft.Container] = {}
    platform_grid_rows = ft.Column(spacing=10)

    def rebuild_mode_tabs() -> None:
        mode_tabs_host.content = ui.build_mode_tabs(
            current_mode.value,
            on_stream=lambda _: set_mode(FetchMode.STREAM),
            on_custom=lambda _: set_mode(FetchMode.CUSTOM),
        )

    def set_mode(mode: FetchMode) -> None:
        nonlocal current_mode
        current_mode = mode
        rebuild_mode_tabs()
        apply_mode_ui()
        refresh_analysis_for_current_mode()
        page.update()

    def update_refresh_hint() -> None:
        if hourly_refresh_switch.value:
            refresh_hint.value = f"打开时自动刷新 · 下次整点 {format_next_hour()}"
        else:
            refresh_hint.value = "打开时自动刷新 · 整点刷新已关闭"

    def apply_mode_ui() -> None:
        is_custom = current_mode == FetchMode.CUSTOM
        keyword_field.visible = is_custom
        keyword_field.disabled = not is_custom
        mode_hint.value = (
            "抓取各平台当前热榜，全量展示，无需关键词"
            if not is_custom
            else "按关键词过滤热榜内容；百度新闻将直接搜索该词"
        )
        for pid, chip in platform_chips.items():
            search_only = pid in SEARCH_ONLY_PLATFORMS
            chip.opacity = 0.45 if search_only and not is_custom else 1.0

    def on_hourly_toggle(_: ft.ControlEvent) -> None:
        update_refresh_hint()
        page.update()

    hourly_refresh_switch.on_change = on_hourly_toggle

    def rebuild_platform_grid() -> None:
        platform_grid_rows.controls.clear()
        for i in range(0, len(PLATFORMS), 2):
            row_chips = [platform_chips[PLATFORMS[i]["id"]]]
            if i + 1 < len(PLATFORMS):
                row_chips.append(platform_chips[PLATFORMS[i + 1]["id"]])
            platform_grid_rows.controls.append(ft.Row(row_chips, spacing=10))

    def platform_chip(platform: dict[str, str]) -> ft.Container:
        pid = platform["id"]
        selected = platform_states[pid]

        def toggle(_: ft.ControlEvent) -> None:
            if pid in SEARCH_ONLY_PLATFORMS and current_mode == FetchMode.STREAM:
                page.snack_bar = ft.SnackBar(ft.Text("百度新闻仅支持「定制热点」模式"))
                page.snack_bar.open = True
                page.update()
                return
            platform_states[pid] = not platform_states[pid]
            new_chip = platform_chip(platform)
            platform_chips[pid] = new_chip
            rebuild_platform_grid()
            page.update()

        chip = ui.build_platform_chip(
            platform,
            selected=platform_states[pid],
            dimmed=pid in SEARCH_ONLY_PLATFORMS and current_mode == FetchMode.STREAM,
            on_toggle=toggle,
        )
        platform_chips[pid] = chip
        return chip

    def open_url(url: str) -> None:
        if url:
            page.launch_url(url)

    def refresh_analysis_for_current_mode() -> None:
        user_kw = (keyword_field.value or DEFAULT_KEYWORD).strip()
        db_key = storage_key(current_mode, user_kw)
        analyze_kw = analysis_keyword(current_mode, user_kw)
        titles = store.get_titles_by_keyword(db_key)
        words = analyze_titles(titles, keyword=analyze_kw)
        analysis_wrap.controls.clear()
        if not words:
            analysis_wrap.controls.append(
                ft.Text("暂无分析数据，请先抓取或查看历史", color=THEME["text_muted"], size=13)
            )
        else:
            for idx, (word, count) in enumerate(words):
                analysis_wrap.controls.append(ui.build_word_tag(word, count, idx))

    def refresh_list_display() -> None:
        viewed = apply_view(
            raw_articles,
            sort_key=sort_dropdown.value or DEFAULT_SORT,
            title_keyword=list_filter_field.value or "",
            platform=platform_filter.value or ALL_PLATFORMS,
        )
        results_column.controls.clear()
        if not raw_articles:
            hint = (
                "尝试勾选更多热榜平台"
                if current_mode == FetchMode.STREAM
                else "尝试更换关键词或勾选更多平台"
            )
            results_column.controls.append(ui.build_empty_state("暂无结果", hint))
        elif not viewed:
            results_column.controls.append(
                ui.build_empty_state("无匹配结果", "调整筛选条件或清空标题筛选")
            )
        else:
            for article in viewed:
                results_column.controls.append(ui.build_article_card(article, open_url))
        total = len(raw_articles)
        shown = len(viewed)
        if shown == total:
            results_count_text.value = f"{total} 条结果"
        else:
            results_count_text.value = f"{shown} / {total} 条"
        page.update()

    def set_raw_articles(articles: list[Article]) -> None:
        nonlocal raw_articles
        raw_articles = articles
        refresh_list_display()

    def on_view_change(_: ft.ControlEvent) -> None:
        refresh_list_display()

    def set_status(message: str, *, active: bool = False, count: str = "") -> None:
        status_message.value = message
        status_dot.bgcolor = THEME["success"] if active else THEME["text_muted"]
        status_count.value = count
        status_count.visible = bool(count)

    def set_loading(loading: bool, message: str = "") -> None:
        fetch_btn.opacity = 0.7 if loading else 1.0
        fetch_btn.disabled = loading
        history_btn.disabled = loading
        set_status(
            message or f"就绪 · {MODE_LABELS[current_mode]}",
            active=loading,
            count=results_count_text.value if not loading else "",
        )
        page.update()

    def format_counts(counts: dict[str, int]) -> str:
        return " · ".join(f"{name} {n}条" for name, n in counts.items())

    def on_fetch_complete(
        articles: list[Article],
        errors: dict[str, str],
        counts: dict[str, int],
        db_key: str,
        *,
        reason: str,
    ) -> None:
        nonlocal is_fetching
        is_fetching = False
        if articles:
            store.save_articles(articles, db_key)
        set_raw_articles(articles)
        refresh_analysis_for_current_mode()
        update_refresh_hint()
        parts = [format_counts(counts), f"共 {len(articles)} 条"]
        if errors:
            parts.append("提示: " + "; ".join(f"{k}" for k in errors))
        set_loading(False, f"{reason} · {MODE_LABELS[current_mode]} — " + "，".join(parts))

    def trigger_fetch(*, reason: str = "手动") -> bool:
        nonlocal is_fetching, current_keyword

        if is_fetching:
            return False

        user_kw = (keyword_field.value or DEFAULT_KEYWORD).strip()
        current_keyword = user_kw
        db_key = storage_key(current_mode, user_kw)

        if current_mode == FetchMode.CUSTOM and not user_kw:
            if reason != "启动":
                set_status("定制模式请输入关键词")
                page.update()
            return False

        selected = [pid for pid, on in platform_states.items() if on]
        if not selected:
            if reason != "启动":
                set_status("请至少选择一个平台")
                page.update()
            return False

        is_fetching = True
        label = f"「{user_kw}」" if current_mode == FetchMode.CUSTOM else "全站热榜"
        set_loading(True, f"{reason}刷新中 · {label}...")

        def worker() -> None:
            nonlocal is_fetching
            try:
                articles, errors, counts = fetch_all(
                    selected,
                    user_kw,
                    mode=current_mode,
                    sort_by_hot=False,
                )
                on_fetch_complete(articles, errors, counts, db_key, reason=reason)
            except Exception as exc:  # noqa: BLE001
                is_fetching = False
                set_loading(False, f"{reason}刷新失败: {exc}")

        threading.Thread(target=worker, daemon=True).start()
        return True

    def do_fetch(_: ft.ControlEvent) -> None:
        trigger_fetch(reason="手动")

    def do_history(_: ft.ControlEvent) -> None:
        nonlocal current_keyword
        user_kw = (keyword_field.value or DEFAULT_KEYWORD).strip()
        current_keyword = user_kw
        db_key = storage_key(current_mode, user_kw)
        set_loading(True, "加载历史记录...")

        articles = store.get_history(db_key)
        set_raw_articles(articles)
        refresh_analysis_for_current_mode()
        set_loading(False, f"已加载 {MODE_LABELS[current_mode]} 历史 {len(articles)} 条")

    def hourly_scheduler_loop() -> None:
        while not stop_scheduler.is_set():
            wait_sec = seconds_until_next_hour()
            if stop_scheduler.wait(wait_sec):
                break
            if hourly_refresh_switch.value:
                trigger_fetch(reason="整点")

    def startup_refresh() -> None:
        time.sleep(0.8)
        trigger_fetch(reason="启动")

    fetch_btn.on_click = do_fetch
    history_btn.on_click = do_history
    sort_dropdown.on_change = on_view_change
    list_filter_field.on_change = on_view_change
    platform_filter.on_change = on_view_change

    def on_page_close(_: ft.ControlEvent) -> None:
        stop_scheduler.set()

    page.on_close = on_page_close

    for p in PLATFORMS:
        platform_chip(p)
    rebuild_platform_grid()
    rebuild_mode_tabs()

    controls_section = ui.search_card(
        ft.Column(
            [
                ui.section_label("抓取模式", "grid"),
                mode_tabs_host,
                mode_hint,
                ui.section_label("搜索关键词", "search"),
                keyword_field,
                ui.section_label("选择平台", "grid"),
                platform_grid_rows,
                hourly_refresh_switch,
                refresh_hint,
                ft.Row([fetch_btn, history_btn], spacing=12),
                ui.section_label("列表排序与筛选", "list"),
                sort_dropdown,
                ft.Row([list_filter_field], spacing=10),
                platform_filter,
            ],
            spacing=14,
        )
    )

    status_bar = ft.Container(
        content=ft.Row([status_dot, status_message, status_count], spacing=12),
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
        bgcolor=THEME["bg_secondary"],
        border_radius=12,
        border=ft.border.all(1, BORDER),
        margin=ft.margin.symmetric(horizontal=20),
    )

    main_column = ft.Column(
        [
            ui.build_header(),
            ft.Container(
                content=controls_section,
                padding=ft.padding.symmetric(horizontal=20),
            ),
            status_bar,
            ft.Container(
                content=ft.Column(
                    [
                        results_header,
                        results_column,
                        ui.section_header("热点分析", "chart", ""),
                        ft.Container(
                            content=analysis_wrap,
                            padding=16,
                            bgcolor=THEME["bg_secondary"],
                            border_radius=16,
                            border=ft.border.all(1, BORDER),
                        ),
                        ft.Container(height=24),
                    ],
                    spacing=16,
                ),
                padding=ft.padding.symmetric(horizontal=20, vertical=8),
            ),
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
    )

    page.add(
        ft.Row(
            [ui.phone_shell(main_column)],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
    )

    apply_mode_ui()
    update_refresh_hint()
    set_status(f"就绪 · {MODE_LABELS[current_mode]}")
    refresh_analysis_for_current_mode()

    threading.Thread(target=startup_refresh, daemon=True).start()
    threading.Thread(target=hourly_scheduler_loop, daemon=True).start()
