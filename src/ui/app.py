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
from src.ui.theme import (
    APP_MAX_WIDTH,
    BORDER,
    FONT_FAMILY,
    PAGE_PAD_H,
    RADIUS_LG,
    SPACE_MD,
    SPACE_SM,
    grouped_surface,
    ios_filled_button_style,
    ios_secondary_button_style,
)
from src.utils.article_view import ALL_PLATFORMS, DEFAULT_SORT, SORT_OPTIONS, apply_view
from src.utils.refresh_scheduler import format_next_hour, seconds_until_next_hour


def run_app(page: ft.Page) -> None:
    page.title = "热点猎手"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(font_family=FONT_FAMILY)
    page.bgcolor = THEME["bg_primary"]
    page.padding = 0
    page.scroll = ft.ScrollMode.HIDDEN
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
    active_nav = "hot"
    scroll_ref = ft.Ref[ft.Column]()
    bottom_nav_host = ft.Container()
    back_top_host: ft.Container

    mode_hint = ft.Text("", color=THEME["text_secondary"], size=12)
    refresh_hint = ft.Text("", color=THEME["text_muted"], size=11)
    mode_tabs_host = ft.Container()

    keyword_field = ft.TextField(
        value=DEFAULT_KEYWORD,
        label="搜索关键词",
        hint_text="输入关注的主题词，如 AI、新能源",
        border_color="transparent",
        focused_border_color=THEME["primary"],
        bgcolor=THEME["bg_card"],
        color=THEME["text_primary"],
        text_size=15,
        border_radius=10,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        expand=True,
        visible=False,
        disabled=True,
    )

    hourly_refresh_switch = ft.Switch(
        label="整点自动刷新",
        value=True,
        active_color=THEME["primary"],
        label_style=ft.TextStyle(color=THEME["text_secondary"], size=13),
        scale=0.9,
    )

    status_message = ft.Text("就绪", size=13, color=THEME["text_secondary"], expand=True)
    status_count = ft.Text("", size=13, weight=ft.FontWeight.W_600, color=THEME["primary_light"])
    status_dot = ft.Container(width=10, height=10, border_radius=5, bgcolor=THEME["text_muted"])

    results_count_text = ft.Text("0 条结果", size=12, color=THEME["text_muted"])
    results_header = ft.Row(
        [
            ft.Text("热点列表", size=17, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
            results_count_text,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    results_column = ft.Column(spacing=SPACE_SM)
    analysis_wrap = ft.Row(wrap=True, spacing=SPACE_SM, run_spacing=SPACE_SM)

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
        border_radius=10,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        text_size=14,
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

    fetch_btn = ft.Container(
        content=ft.Text("立即刷新", size=15, weight=ft.FontWeight.W_600, color="#ffffff"),
        alignment=ft.alignment.center,
        expand=True,
        ink=True,
        **ios_filled_button_style(),
    )

    history_btn = ft.Container(
        content=ft.Text("历史", size=15, weight=ft.FontWeight.W_500, color=THEME["text_primary"]),
        alignment=ft.alignment.center,
        expand=True,
        ink=True,
        **ios_secondary_button_style(),
    )

    platform_chips: dict[str, ft.Container] = {}
    platform_grid_rows = ft.Column(spacing=SPACE_SM)

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
            results_column.controls.append(ui.build_articles_group(viewed, open_url))
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

    def load_history() -> None:
        nonlocal current_keyword
        user_kw = (keyword_field.value or DEFAULT_KEYWORD).strip()
        current_keyword = user_kw
        db_key = storage_key(current_mode, user_kw)
        set_loading(True, "加载历史记录...")

        articles = store.get_history(db_key)
        set_raw_articles(articles)
        refresh_analysis_for_current_mode()
        set_loading(False, f"已加载 {MODE_LABELS[current_mode]} 历史 {len(articles)} 条")

    def do_history(_: ft.ControlEvent) -> None:
        load_history()

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

    def scroll_to_section(key: str | None = None, *, offset: float | None = None) -> None:
        col = scroll_ref.current
        if col is None:
            return
        if key:
            col.scroll_to(key=key, duration=350, curve=ft.AnimationCurve.EASE_OUT)
        elif offset is not None:
            col.scroll_to(offset=offset, duration=350, curve=ft.AnimationCurve.EASE_OUT)

    def set_active_nav(nav_id: str) -> None:
        nonlocal active_nav
        active_nav = nav_id
        bottom_nav_host.content = ui.build_bottom_nav(active_nav, on_nav_select)

    def scroll_to_top(_: ft.ControlEvent) -> None:
        scroll_to_section(offset=0)
        set_active_nav("hot")
        page.update()

    back_top_host = ui.build_back_to_top(visible=False, on_click=scroll_to_top)

    def on_scroll(e: ft.OnScrollEvent) -> None:
        show = e.pixels > 200
        if back_top_host.visible != show:
            back_top_host.visible = show
            page.update()

    def on_nav_select(nav_id: str) -> None:
        set_active_nav(nav_id)
        if nav_id == "hot":
            scroll_to_section("section-hot")
        elif nav_id == "history":
            load_history()
            scroll_to_section("section-hot")
        elif nav_id == "analysis":
            scroll_to_section("section-analysis")
        elif nav_id == "settings":
            scroll_to_section("section-settings")
        page.update()

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
                ft.Row([fetch_btn, history_btn], spacing=SPACE_SM),
                ui.section_label("列表排序与筛选", "list"),
                sort_dropdown,
                ft.Row([list_filter_field], spacing=SPACE_SM),
                platform_filter,
            ],
            spacing=SPACE_MD,
        )
    )

    status_bar = ft.Container(
        content=ft.Row([status_dot, status_message, status_count], spacing=SPACE_SM),
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        margin=ft.margin.symmetric(horizontal=PAGE_PAD_H),
        **grouped_surface(),
    )

    scroll_column = ft.Column(
        [
            ui.build_header(),
            ft.Container(
                content=controls_section,
                padding=ft.padding.symmetric(horizontal=PAGE_PAD_H),
                key="section-settings",
            ),
            status_bar,
            ft.Container(
                content=ft.Column(
                    [
                        results_header,
                        results_column,
                    ],
                    spacing=SPACE_MD,
                ),
                padding=ft.padding.symmetric(horizontal=PAGE_PAD_H, vertical=6),
                key="section-hot",
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ui.section_header("热点分析", "chart", ""),
                        ft.Container(
                            content=analysis_wrap,
                            padding=SPACE_MD,
                            **grouped_surface(),
                        ),
                    ],
                    spacing=SPACE_MD,
                ),
                padding=ft.padding.symmetric(horizontal=PAGE_PAD_H, vertical=6),
                key="section-analysis",
            ),
            ft.Container(height=56),
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        ref=scroll_ref,
        on_scroll=on_scroll,
        on_scroll_interval=50,
    )

    bottom_nav_host.content = ui.build_bottom_nav(active_nav, on_nav_select)

    shell_body = ft.Stack(
        [
            ft.Column(
                [scroll_column, bottom_nav_host],
                spacing=0,
                expand=True,
            ),
            ft.Container(
                content=back_top_host,
                right=16,
                bottom=72,
            ),
        ],
        expand=True,
    )

    page.add(
        ft.Row(
            [ui.phone_shell(shell_body)],
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
