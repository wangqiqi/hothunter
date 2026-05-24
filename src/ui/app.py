"""Flet 主界面 — 对齐 docs/prototype 深色主题。"""

from __future__ import annotations

import threading
import time

import flet as ft

from src.analysis.word_freq import analyze_titles
from src.config import DEFAULT_KEYWORD, get_platforms, get_search_only_platforms
from src.crawler.registry import fetch_all
from src.models import Article
from src.modes import FetchMode, MODE_LABELS, analysis_keyword, storage_key
from src.storage.db import ArticleStore
from src.ui import components as ui
from src.ui import nav_chrome as chrome
from src.ui.theme import (
    APP_MAX_WIDTH,
    FONT_FAMILY,
    PAGE_PAD_H,
    SPACE_MD,
    SPACE_SM,
    ThemeController,
    apply_grouped_style,
    grouped_surface,
    init_theme,
    ios_filled_button_style,
    ios_secondary_button_style,
    palette,
    style_dropdown,
    style_text_field,
)
from src.utils.article_view import ALL_PLATFORMS, DEFAULT_SORT, SORT_OPTIONS, apply_view
from src.utils.refresh_scheduler import format_next_hour, seconds_until_next_hour


def run_app(page: ft.Page) -> None:
    theme_ctrl = init_theme(ThemeController())

    page.title = "热点猎手"
    page.window.icon = "icon.png"
    page.theme_mode = theme_ctrl.flet_theme_mode()
    page.theme = ft.Theme(font_family=FONT_FAMILY)
    page.bgcolor = palette()["bg_primary"]
    page.padding = 0
    page.scroll = ft.ScrollMode.HIDDEN
    chrome.configure_page_window(page, max_width=APP_MAX_WIDTH)

    store = ArticleStore()
    platforms = get_platforms()
    platform_states: dict[str, bool] = {p["id"]: True for p in platforms}
    search_only = get_search_only_platforms()
    raw_articles: list[Article] = []
    current_keyword = DEFAULT_KEYWORD
    current_mode = FetchMode.STREAM
    is_fetching = False
    stop_scheduler = threading.Event()
    active_nav = "hot"
    nav_visible = True
    scroll_ref = ft.Ref[ft.Column]()
    bottom_nav_host = ft.Container()
    scroll_bottom_spacer = ft.Container(height=chrome.scroll_content_inset(nav_visible=True))
    bottom_nav_wrapper = ft.Container()
    back_top_slot = ft.Container()
    back_top_host: ft.Container
    header_host = ft.Container()
    phone_wrap = ft.Container()
    controls_card = ft.Container()

    def _p() -> dict[str, str]:
        return palette()

    mode_hint = ft.Text("", size=12)
    refresh_hint = ft.Text("", size=11)
    mode_tabs_host = ft.Container()

    keyword_field = ft.TextField(
        value=DEFAULT_KEYWORD,
        label="搜索关键词",
        hint_text="输入关注的主题词，如 AI、新能源",
        border_color="transparent",
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
        scale=0.9,
    )

    status_message = ft.Text("就绪", size=13, expand=True)
    status_count = ft.Text("", size=13, weight=ft.FontWeight.W_600)
    status_dot = ft.Container(width=10, height=10, border_radius=5)

    results_count_text = ft.Text("0 条结果", size=12)
    results_title = ft.Text("热点列表", size=17, weight=ft.FontWeight.W_600)
    results_header = ft.Row(
        [results_title, results_count_text],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    results_column = ft.Column(spacing=SPACE_SM)
    analysis_wrap = ft.Row(wrap=True, spacing=SPACE_SM, run_spacing=SPACE_SM)

    sort_dropdown = ft.Dropdown(
        label="排序方式",
        value=DEFAULT_SORT,
        options=[ft.dropdown.Option(key, label) for key, label in SORT_OPTIONS.items()],
        expand=True,
    )

    list_filter_field = ft.TextField(
        label="标题筛选",
        hint_text="在当前结果中按标题关键词过滤",
        border_color="transparent",
        border_radius=10,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        text_size=14,
        expand=True,
    )

    platform_filter = ft.Dropdown(
        label="平台筛选",
        value=ALL_PLATFORMS,
        options=[ft.dropdown.Option(ALL_PLATFORMS, "全部平台")]
        + [ft.dropdown.Option(p["name"], p["name"]) for p in platforms],
        expand=True,
    )

    fetch_label = ft.Text("立即刷新", size=15, weight=ft.FontWeight.W_600)
    fetch_btn = ft.Container(
        content=fetch_label,
        alignment=ft.alignment.center,
        expand=True,
        ink=True,
    )

    history_label = ft.Text("历史", size=15, weight=ft.FontWeight.W_500)
    history_btn = ft.Container(
        content=history_label,
        alignment=ft.alignment.center,
        expand=True,
        ink=True,
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
            chip.opacity = 0.45 if pid in search_only and not is_custom else 1.0

    def on_hourly_toggle(_: ft.ControlEvent) -> None:
        update_refresh_hint()
        page.update()

    hourly_refresh_switch.on_change = on_hourly_toggle

    def rebuild_platform_grid() -> None:
        platform_grid_rows.controls.clear()
        for i in range(0, len(platforms), 2):
            row_chips = [platform_chips[platforms[i]["id"]]]
            if i + 1 < len(platforms):
                row_chips.append(platform_chips[platforms[i + 1]["id"]])
            platform_grid_rows.controls.append(ft.Row(row_chips, spacing=10))

    def platform_chip(platform: dict[str, str]) -> ft.Container:
        pid = platform["id"]
        selected = platform_states[pid]

        def toggle(_: ft.ControlEvent) -> None:
            if pid in search_only and current_mode == FetchMode.STREAM:
                page.snack_bar = ft.SnackBar(ft.Text("该平台仅支持「定制热点」模式"))
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
            dimmed=pid in search_only and current_mode == FetchMode.STREAM,
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
                ft.Text("暂无分析数据，请先抓取或查看历史", color=_p()["text_muted"], size=13)
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
        p = _p()
        status_message.value = message
        status_dot.bgcolor = p["success"] if active else p["text_muted"]
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

    def on_appearance_toggle(_: ft.ControlEvent) -> None:
        theme_ctrl.toggle()
        apply_theme_styles()
        page.update()

    def apply_theme_styles() -> None:
        p = _p()
        page.theme_mode = theme_ctrl.flet_theme_mode()
        page.bgcolor = p["bg_primary"]
        phone_wrap.bgcolor = p["bg_primary"]

        mode_hint.color = p["text_secondary"]
        refresh_hint.color = p["text_muted"]
        style_text_field(keyword_field)
        style_text_field(list_filter_field)
        style_dropdown(sort_dropdown)
        style_dropdown(platform_filter)
        hourly_refresh_switch.active_color = p["primary"]
        hourly_refresh_switch.label_style = ft.TextStyle(color=p["text_secondary"], size=13)
        status_message.color = p["text_secondary"]
        status_count.color = p["primary_light"]
        results_title.color = p["text_primary"]
        results_count_text.color = p["text_muted"]
        fetch_label.color = p["on_primary"]
        history_label.color = p["text_primary"]
        for key, value in ios_filled_button_style().items():
            setattr(fetch_btn, key, value)
        for key, value in ios_secondary_button_style().items():
            setattr(history_btn, key, value)

        header_host.content = ui.build_header(on_appearance_toggle)
        rebuild_mode_tabs()
        for plat in platforms:
            platform_chips[plat["id"]] = platform_chip(plat)
        rebuild_platform_grid()
        apply_grouped_style(controls_card)
        apply_grouped_style(status_bar)
        apply_grouped_style(analysis_box)
        bottom_nav_host.content = ui.build_bottom_nav(active_nav, on_nav_select)
        if isinstance(back_top_host.content, ft.IconButton):
            back_top_host.content.icon_color = p["on_primary"]
            back_top_host.content.bgcolor = p["primary"]
        refresh_list_display()
        refresh_analysis_for_current_mode()

    back_top_host = ui.build_back_to_top(visible=False, on_click=scroll_to_top)
    nav_anim = ft.Animation(chrome.NAV_ANIMATION_MS, ft.AnimationCurve.EASE_OUT)

    def set_nav_visible(visible: bool) -> None:
        nonlocal nav_visible
        if visible == nav_visible:
            return
        nav_visible = visible
        bottom_nav_wrapper.offset = chrome.nav_slide_offset(visible=visible)
        bottom_nav_wrapper.opacity = chrome.nav_opacity(visible=visible)
        scroll_bottom_spacer.height = chrome.scroll_content_inset(nav_visible=visible)
        back_top_slot.bottom = chrome.back_top_bottom(nav_visible=visible)
        page.update()

    def reveal_nav(_: ft.ControlEvent | None = None) -> None:
        set_nav_visible(True)

    def on_bottom_hover(e: ft.HoverEvent) -> None:
        if e.data == "true":
            reveal_nav()

    def on_bottom_drag_update(e: ft.DragUpdateEvent) -> None:
        if e.delta_y < -3:
            reveal_nav()

    def on_scroll(e: ft.OnScrollEvent) -> None:
        show_btt = e.pixels > 200
        if back_top_host.visible != show_btt:
            back_top_host.visible = show_btt

        new_nav = chrome.decide_nav_visible_on_scroll(
            pixels=e.pixels,
            max_scroll_extent=e.max_scroll_extent or 0,
            scroll_delta=e.scroll_delta,
            direction=e.direction,
            current=nav_visible,
        )
        if new_nav != nav_visible:
            set_nav_visible(new_nav)
        elif back_top_host.visible != show_btt:
            page.update()

    def on_nav_select(nav_id: str) -> None:
        set_active_nav(nav_id)
        reveal_nav()
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

    for p in platforms:
        platform_chip(p)
    rebuild_platform_grid()
    rebuild_mode_tabs()

    controls_card = ui.search_card(
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

    analysis_box = ft.Container(content=analysis_wrap, padding=SPACE_MD, **grouped_surface())

    scroll_column = ft.Column(
        [
            header_host,
            ft.Container(
                content=controls_card,
                padding=ft.padding.symmetric(horizontal=PAGE_PAD_H),
                key="section-settings",
            ),
            status_bar,
            ft.Container(
                content=ft.Column(
                    [results_header, results_column],
                    spacing=SPACE_MD,
                ),
                padding=ft.padding.symmetric(horizontal=PAGE_PAD_H, vertical=6),
                key="section-hot",
            ),
            ft.Container(
                content=ft.Column(
                    [ui.section_header("热点分析", "chart", ""), analysis_box],
                    spacing=SPACE_MD,
                ),
                padding=ft.padding.symmetric(horizontal=PAGE_PAD_H, vertical=6),
                key="section-analysis",
            ),
            scroll_bottom_spacer,
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        ref=scroll_ref,
        on_scroll=on_scroll,
        on_scroll_interval=50,
    )

    bottom_nav_host.content = ui.build_bottom_nav(active_nav, on_nav_select)

    bottom_nav_wrapper.content = ft.SafeArea(
        content=bottom_nav_host,
        top=False,
        left=False,
        right=False,
        bottom=True,
        minimum_padding=ft.padding.only(bottom=chrome.NAV_SAFE_BOTTOM_MIN),
    )
    bottom_nav_wrapper.left = 0
    bottom_nav_wrapper.right = 0
    bottom_nav_wrapper.bottom = 0
    bottom_nav_wrapper.animate_offset = nav_anim
    bottom_nav_wrapper.animate_opacity = nav_anim
    bottom_nav_wrapper.offset = chrome.nav_slide_offset(visible=True)
    bottom_nav_wrapper.opacity = 1.0

    bottom_edge_zone = ft.GestureDetector(
        content=ft.Container(
            height=chrome.NAV_EDGE_ZONE_HEIGHT,
            bgcolor=ft.Colors.TRANSPARENT,
            on_hover=on_bottom_hover,
        ),
        on_vertical_drag_update=on_bottom_drag_update,
        mouse_cursor=ft.MouseCursor.BASIC,
    )

    back_top_slot.content = back_top_host
    back_top_slot.right = 16
    back_top_slot.bottom = chrome.back_top_bottom(nav_visible=True)

    shell_body = ft.Stack(
        [
            scroll_column,
            ft.Container(
                content=bottom_edge_zone,
                left=0,
                right=0,
                bottom=0,
            ),
            bottom_nav_wrapper,
            back_top_slot,
        ],
        expand=True,
    )

    phone_wrap = ui.phone_shell(shell_body)
    page.add(
        ft.Row(
            [phone_wrap],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
    )

    apply_theme_styles()
    apply_mode_ui()
    update_refresh_hint()
    set_status(f"就绪 · {MODE_LABELS[current_mode]}")
    refresh_analysis_for_current_mode()

    threading.Thread(target=startup_refresh, daemon=True).start()
    threading.Thread(target=hourly_scheduler_loop, daemon=True).start()
