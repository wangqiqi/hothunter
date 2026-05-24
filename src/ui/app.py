"""Flet 主界面 — 对齐 docs/prototype 深色主题。"""

from __future__ import annotations

import threading

import flet as ft

from src.analysis.word_freq import analyze_titles
from src.config import DEFAULT_KEYWORD, PLATFORMS, THEME
from src.crawler.registry import fetch_all
from src.models import Article
from src.storage.db import ArticleStore


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

    keyword_field = ft.TextField(
        value=DEFAULT_KEYWORD,
        label="关键词",
        border_color=THEME["primary"],
        focused_border_color=THEME["primary_light"],
        bgcolor=THEME["bg_secondary"],
        color=THEME["text_primary"],
        expand=True,
    )

    status_text = ft.Text("就绪", color=THEME["text_secondary"], size=13)
    result_count = ft.Text("0 条结果", color=THEME["text_muted"], size=12)
    results_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    analysis_column = ft.Column(spacing=6)

    fetch_btn = ft.ElevatedButton(
        "开始抓取",
        icon=ft.Icons.SEARCH,
        bgcolor=THEME["primary"],
        color="#ffffff",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )
    history_btn = ft.OutlinedButton(
        "历史记录",
        icon=ft.Icons.HISTORY,
        style=ft.ButtonStyle(
            color=THEME["text_primary"],
            side=ft.BorderSide(1, THEME["bg_card"]),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    def platform_chip(platform: dict[str, str]) -> ft.Container:
        pid = platform["id"]
        selected = platform_states[pid]

        def toggle(_: ft.ControlEvent) -> None:
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
                            ft.Text("已选" if selected else "未选", size=11, color=THEME["text_muted"]),
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

    def refresh_analysis(keyword: str) -> None:
        titles = store.get_titles_by_keyword(keyword)
        words = analyze_titles(titles, keyword=keyword)
        analysis_column.controls.clear()
        if not words:
            analysis_column.controls.append(
                ft.Text("暂无分析数据，请先抓取或查看历史", color=THEME["text_muted"], size=13)
            )
        else:
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
        results_column.controls.clear()
        for article in articles:
            results_column.controls.append(build_card(article))
        result_count.value = f"{len(articles)} 条结果"
        page.update()

    def set_loading(loading: bool, message: str = "") -> None:
        fetch_btn.disabled = loading
        history_btn.disabled = loading
        status_text.value = message or ("正在抓取..." if loading else "就绪")
        page.update()

    def on_fetch_complete(articles: list[Article], errors: dict[str, str], keyword: str) -> None:
        if articles:
            store.save_articles(articles, keyword)
        show_articles(articles)
        refresh_analysis(keyword)
        parts = [f"{len(articles)} 条结果"]
        if errors:
            parts.append("部分平台失败: " + "; ".join(f"{k}: {v[:40]}" for k, v in errors.items()))
        set_loading(False, "抓取完成 — " + "，".join(parts))

    def do_fetch(_: ft.ControlEvent) -> None:
        keyword = (keyword_field.value or DEFAULT_KEYWORD).strip()
        selected = [pid for pid, on in platform_states.items() if on]
        if not selected:
            status_text.value = "请至少选择一个平台"
            page.update()
            return

        set_loading(True, f"正在抓取「{keyword}」...")

        def worker() -> None:
            articles, errors = fetch_all(selected, keyword)
            on_fetch_complete(articles, errors, keyword)

        threading.Thread(target=worker, daemon=True).start()

    def do_history(_: ft.ControlEvent) -> None:
        keyword = (keyword_field.value or "").strip()
        set_loading(True, "加载历史记录...")
        articles = store.get_history(keyword or None)
        show_articles(articles)
        refresh_analysis(keyword or DEFAULT_KEYWORD)
        set_loading(False, f"已加载历史 {len(articles)} 条")

    fetch_btn.on_click = do_fetch
    history_btn.on_click = do_history

    header = ft.Container(
        content=ft.Column(
            [
                ft.Text("热点猎手", size=26, weight=ft.FontWeight.BOLD, color="#ffffff"),
                ft.Text("本地热点抓取 · 词频分析", size=13, color="#ffffffcc"),
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

    platform_grid = ft.Column(
        [platform_chip(p) for p in PLATFORMS],
        spacing=8,
    )

    page.add(
        header,
        ft.Container(
            content=ft.Column(
                [
                    ft.Row([keyword_field], spacing=10),
                    ft.Text("选择平台", size=14, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
                    platform_grid,
                    ft.Row([fetch_btn, history_btn], spacing=10),
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

    refresh_analysis(DEFAULT_KEYWORD)
