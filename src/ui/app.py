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
from src.storage.export import export_articles_csv
from src.utils.refresh_scheduler import format_next_hour, seconds_until_next_hour


def run_app(page: ft.Page) -> None:
    page.title = "热点猎手"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = THEME["bg_primary"]
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.window.width = 430
    page.window.height = 900

    store = ArticleStore()
    platform_states: dict[str, bool] = {p["id"]: True for p in PLATFORMS}
    current_articles: list[Article] = []
    current_keyword = DEFAULT_KEYWORD
    current_mode = FetchMode.STREAM
    is_fetching = False
    stop_scheduler = threading.Event()

    mode_hint = ft.Text("", color=THEME["text_muted"], size=12)
    refresh_hint = ft.Text("", color=THEME["text_muted"], size=12)

    keyword_field = ft.TextField(
        value=DEFAULT_KEYWORD,
        label="关键词",
        hint_text="输入关注的主题词，如 AI、新能源",
        border_color=THEME["primary"],
        focused_border_color=THEME["primary_light"],
        bgcolor=THEME["bg_secondary"],
        color=THEME["text_primary"],
        expand=True,
        visible=False,
        disabled=True,
    )

    mode_group = ft.RadioGroup(
        value=FetchMode.STREAM,
        content=ft.Row(
            [
                ft.Radio(value=FetchMode.STREAM, label=MODE_LABELS[FetchMode.STREAM], fill_color=THEME["primary"]),
                ft.Radio(value=FetchMode.CUSTOM, label=MODE_LABELS[FetchMode.CUSTOM], fill_color=THEME["primary"]),
            ],
            spacing=16,
        ),
    )

    hourly_refresh_switch = ft.Switch(
        label="整点自动刷新（每小时）",
        value=True,
        active_color=THEME["primary"],
        label_style=ft.TextStyle(color=THEME["text_secondary"], size=13),
    )

    status_text = ft.Text("就绪 · 实时流模式", color=THEME["text_secondary"], size=13)
    result_count = ft.Text("0 条结果", color=THEME["text_muted"], size=12)
    results_column = ft.Column(spacing=10)
    analysis_column = ft.Column(spacing=6)

    sort_by_hot_switch = ft.Switch(
        label="按热度排序",
        value=True,
        active_color=THEME["primary"],
        label_style=ft.TextStyle(color=THEME["text_secondary"], size=13),
    )

    fetch_btn = ft.ElevatedButton(
        "立即刷新",
        icon=ft.Icons.REFRESH,
        bgcolor=THEME["primary"],
        color="#ffffff",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
        expand=True,
    )
    history_btn = ft.OutlinedButton(
        "历史记录",
        icon=ft.Icons.HISTORY,
        style=ft.ButtonStyle(
            color=THEME["text_primary"],
            side=ft.BorderSide(1, THEME["bg_card"]),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        expand=True,
    )
    export_btn = ft.OutlinedButton(
        "导出 CSV",
        icon=ft.Icons.DOWNLOAD,
        style=ft.ButtonStyle(
            color=THEME["text_primary"],
            side=ft.BorderSide(1, THEME["bg_card"]),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        expand=True,
    )

    platform_chips: dict[str, ft.Container] = {}

    def update_refresh_hint() -> None:
        if hourly_refresh_switch.value:
            refresh_hint.value = f"打开时自动刷新 · 下次整点 {format_next_hour()}"
        else:
            refresh_hint.value = "打开时自动刷新 · 整点刷新已关闭"

    def apply_mode_ui() -> None:
        nonlocal current_mode
        current_mode = FetchMode(mode_group.value or FetchMode.STREAM)
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

    def on_mode_change(_: ft.ControlEvent) -> None:
        apply_mode_ui()
        refresh_analysis_for_current_mode()
        page.update()

    def on_hourly_toggle(_: ft.ControlEvent) -> None:
        update_refresh_hint()
        page.update()

    mode_group.on_change = on_mode_change
    hourly_refresh_switch.on_change = on_hourly_toggle

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
            chip.border = ft.border.all(2, THEME["primary"] if platform_states[pid] else THEME["bg_card"])
            chip.bgcolor = THEME["bg_card"] if platform_states[pid] else THEME["bg_secondary"]
            page.update()

        chip = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text(platform["icon"], size=16, weight=ft.FontWeight.BOLD, color="#fff"),
                        width=36,
                        height=36,
                        border_radius=10,
                        bgcolor=THEME["primary_dark"],
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Text(platform["name"], size=13, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
                            ft.Text(
                                "仅定制" if pid in SEARCH_ONLY_PLATFORMS else ("已选" if selected else "未选"),
                                size=11,
                                color=THEME["warning"] if pid in SEARCH_ONLY_PLATFORMS else THEME["text_muted"],
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            padding=12,
            border_radius=14,
            bgcolor=THEME["bg_card"] if selected else THEME["bg_secondary"],
            border=ft.border.all(2, THEME["primary"] if selected else THEME["bg_card"]),
            on_click=toggle,
            ink=True,
        )
        platform_chips[pid] = chip
        return chip

    def build_card(article: Article) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(article.title, size=15, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(article.platform, size=11, color="#fff"),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                bgcolor=THEME["primary_dark"],
                                border_radius=8,
                            ),
                            ft.Text(
                                f"热度: {article.hot_value}" if article.hot_value else "热度: —",
                                size=12,
                                color=THEME["text_secondary"],
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        article.publish_time or article.content_snippet[:60],
                        size=12,
                        color=THEME["text_muted"],
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.TextButton(
                        "打开链接",
                        icon=ft.Icons.OPEN_IN_NEW,
                        style=ft.ButtonStyle(color=THEME["primary_light"]),
                        on_click=lambda _, u=article.url: page.launch_url(u) if u else None,
                    ),
                ],
                spacing=6,
            ),
            padding=16,
            border_radius=16,
            bgcolor=THEME["bg_card"],
            border=ft.border.all(1, THEME["bg_secondary"]),
        )

    def refresh_analysis_for_current_mode() -> None:
        user_kw = (keyword_field.value or DEFAULT_KEYWORD).strip()
        db_key = storage_key(current_mode, user_kw)
        analyze_kw = analysis_keyword(current_mode, user_kw)
        titles = store.get_titles_by_keyword(db_key)
        words = analyze_titles(titles, keyword=analyze_kw)
        analysis_column.controls.clear()
        if not words:
            analysis_column.controls.append(
                ft.Text("暂无分析数据，请先抓取或查看历史", color=THEME["text_muted"], size=13)
            )
        else:
            title = "热词分析（全站）" if current_mode == FetchMode.STREAM else f"热词分析（排除「{analyze_kw}」）"
            analysis_column.controls.append(ft.Text(title, size=12, color=THEME["text_muted"]))
            for word, count in words:
                analysis_column.controls.append(
                    ft.Row(
                        [
                            ft.Text(word, size=14, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
                            ft.Text(f"{count} 次", size=13, color=THEME["success"]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                )

    def show_articles(articles: list[Article]) -> None:
        nonlocal current_articles
        current_articles = articles
        results_column.controls.clear()
        if not articles:
            hint = (
                "尝试勾选更多热榜平台"
                if current_mode == FetchMode.STREAM
                else "尝试更换关键词或勾选更多平台"
            )
            results_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=THEME["text_muted"]),
                            ft.Text("暂无结果", size=15, color=THEME["text_secondary"]),
                            ft.Text(hint, size=12, color=THEME["text_muted"]),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for article in articles:
                results_column.controls.append(build_card(article))
        result_count.value = f"{len(articles)} 条结果"
        export_btn.disabled = not articles
        page.update()

    def set_loading(loading: bool, message: str = "") -> None:
        fetch_btn.disabled = loading
        history_btn.disabled = loading
        export_btn.disabled = loading or not current_articles
        status_text.value = message or f"就绪 · {MODE_LABELS[current_mode]}"
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
        show_articles(articles)
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
                status_text.value = "定制模式请输入关键词"
                page.update()
            return False

        selected = [pid for pid, on in platform_states.items() if on]
        if not selected:
            if reason != "启动":
                status_text.value = "请至少选择一个平台"
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
                    sort_by_hot=bool(sort_by_hot_switch.value),
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

        from src.utils.hot_sort import sort_by_hot_value

        articles = store.get_history(db_key)
        if sort_by_hot_switch.value:
            articles = sort_by_hot_value(articles)
        show_articles(articles)
        refresh_analysis_for_current_mode()
        set_loading(False, f"已加载 {MODE_LABELS[current_mode]} 历史 {len(articles)} 条")

    def do_export(_: ft.ControlEvent) -> None:
        if not current_articles:
            page.snack_bar = ft.SnackBar(ft.Text("没有可导出的数据"))
            page.snack_bar.open = True
            page.update()
            return
        export_label = storage_key(current_mode, current_keyword)
        path = export_articles_csv(current_articles, keyword=export_label)
        page.snack_bar = ft.SnackBar(ft.Text(f"已导出: {path}"))
        page.snack_bar.open = True
        page.update()

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
    export_btn.on_click = do_export

    def on_page_close(_: ft.ControlEvent) -> None:
        stop_scheduler.set()

    page.on_close = on_page_close

    header = ft.Container(
        content=ft.Column(
            [
                ft.Text("热点猎手", size=26, weight=ft.FontWeight.BOLD, color="#ffffff"),
                ft.Text("实时流 · 定制追踪 · 自动刷新", size=13, color="#ffffffcc"),
            ],
            spacing=4,
        ),
        padding=ft.padding.only(left=20, right=20, top=20, bottom=16),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[THEME["primary"], THEME["primary_dark"]],
        ),
        border_radius=ft.border_radius.only(bottom_left=24, bottom_right=24),
    )

    platform_grid = ft.Column([platform_chip(p) for p in PLATFORMS], spacing=8)

    page.add(
        header,
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("抓取模式", size=14, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
                    mode_group,
                    mode_hint,
                    keyword_field,
                    ft.Text("选择平台", size=14, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
                    platform_grid,
                    sort_by_hot_switch,
                    hourly_refresh_switch,
                    refresh_hint,
                    ft.Row([fetch_btn, history_btn], spacing=10),
                    ft.Row([export_btn], spacing=10),
                    status_text,
                    ft.Divider(color=THEME["bg_card"], height=1),
                    ft.Row(
                        [
                            ft.Text("热点列表", size=18, weight=ft.FontWeight.BOLD, color=THEME["text_primary"]),
                            result_count,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    results_column,
                    ft.Text("热点分析", size=18, weight=ft.FontWeight.BOLD, color=THEME["text_primary"]),
                    analysis_column,
                ],
                spacing=14,
            ),
            padding=20,
        ),
    )

    apply_mode_ui()
    update_refresh_hint()
    export_btn.disabled = True
    refresh_analysis_for_current_mode()

    threading.Thread(target=startup_refresh, daemon=True).start()
    threading.Thread(target=hourly_scheduler_loop, daemon=True).start()
