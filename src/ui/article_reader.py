"""应用内文章阅读：摘要页 + 移动端/macOS 内嵌 WebView。"""

from __future__ import annotations

import threading
from collections.abc import Callable

import flet as ft

from src.models import Article
from src.ui.theme import PAGE_PAD_H, RADIUS_MD, SPACE_MD, SPACE_SM, border_color, palette
from src.utils.article_content import fetch_article_body

_EMBED_PLATFORMS = frozenset({"android", "ios", "macos"})


def supports_embedded_web(platform: str) -> bool:
    return platform in _EMBED_PLATFORMS


class ArticleReader:
    """全屏阅读层，覆盖主界面，支持返回与模式切换。"""

    def __init__(
        self,
        page: ft.Page,
        *,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        self._page = page
        self._on_close = on_close
        self._article: Article | None = None
        self._mode = "summary"
        self._supports_web = supports_embedded_web(page.platform)

        self._title_text = ft.Text("", size=16, weight=ft.FontWeight.W_600, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, expand=True)
        self._meta_text = ft.Text("", size=12)
        self._summary_body = ft.Text("", size=15, selectable=True)
        self._summary_scroll = ft.Column([self._summary_body], scroll=ft.ScrollMode.AUTO, expand=True)
        self._loading = ft.ProgressRing(width=28, height=28)
        self._status_text = ft.Text("正在加载摘要…", size=13)
        self._summary_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Row([self._loading, self._status_text], spacing=SPACE_SM, alignment=ft.MainAxisAlignment.CENTER),
                    self._summary_scroll,
                ],
                spacing=SPACE_MD,
                expand=True,
            ),
            padding=ft.padding.symmetric(horizontal=PAGE_PAD_H, vertical=SPACE_MD),
            expand=True,
            visible=True,
        )

        self._webview: ft.WebView | None = None
        self._web_panel = ft.Container(expand=True, visible=False)
        if self._supports_web:
            self._webview = ft.WebView("", expand=True, javascript_enabled=True)
            self._web_panel.content = self._webview

        self._mode_summary_tab = ft.Container(on_click=lambda _: self.set_mode("summary"), expand=True)
        self._mode_web_tab = ft.Container(on_click=lambda _: self.set_mode("web"), expand=True)

        self._overlay = ft.Container(
            content=ft.Column(
                [
                    self._build_toolbar(),
                    self._build_mode_bar(),
                    ft.Container(
                        content=ft.Stack([self._summary_panel, self._web_panel]),
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            visible=False,
            expand=True,
            bgcolor=palette()["bg_primary"],
        )

    @property
    def control(self) -> ft.Container:
        return self._overlay

    @property
    def is_open(self) -> bool:
        return bool(self._overlay.visible)

    def apply_theme(self) -> None:
        p = palette()
        self._overlay.bgcolor = p["bg_primary"]
        self._title_text.color = p["text_primary"]
        self._meta_text.color = p["text_secondary"]
        self._summary_body.color = p["text_primary"]
        self._status_text.color = p["text_muted"]
        if self._webview is not None:
            self._webview.bgcolor = p["bg_primary"]
        self._rebuild_mode_tabs()

    def open(self, article: Article) -> None:
        self._article = article
        self._mode = "summary"
        self._overlay.visible = True
        self._title_text.value = article.title
        meta_parts = [x for x in (article.platform, article.hot_value, article.publish_time) if x]
        self._meta_text.value = " · ".join(meta_parts)
        snippet = (article.content_snippet or "").strip()
        if snippet:
            self._summary_body.value = f"{snippet}\n\n——\n正在加载完整正文…"
            self._summary_scroll.visible = True
        else:
            self._summary_body.value = ""
            self._summary_scroll.visible = False
        self._status_text.value = "正在加载摘要…"
        self._loading.visible = True
        self._apply_mode_visibility()
        self._rebuild_mode_tabs()
        self._page.update()

        if self._webview is not None and article.url:
            self._webview.url = article.url

        threading.Thread(target=self._load_summary, args=(article.url,), daemon=True).start()

    def close(self) -> None:
        self._overlay.visible = False
        self._article = None
        if self._on_close is not None:
            self._on_close()
        self._page.update()

    def set_mode(self, mode: str) -> None:
        if mode == "web" and not self._supports_web:
            self.open_external()
            return
        self._mode = mode
        self._apply_mode_visibility()
        self._rebuild_mode_tabs()
        self._page.update()

    def open_external(self) -> None:
        if self._article and self._article.url:
            self._page.launch_url(
                self._article.url,
                web_popup_window=True,
                window_width=430,
                window_height=900,
            )

    def copy_link(self) -> None:
        if self._article and self._article.url:
            self._page.set_clipboard(self._article.url)
            self._page.snack_bar = ft.SnackBar(ft.Text("链接已复制"))
            self._page.snack_bar.open = True
            self._page.update()

    def _load_summary(self, url: str) -> None:
        body, err = fetch_article_body(url)
        if not self.is_open or self._article is None or self._article.url != url:
            return
        self._loading.visible = False
        self._summary_scroll.visible = True
        if err:
            snippet = (self._article.content_snippet or "").strip()
            fallback = f"{snippet}\n\n——\n无法拉取完整正文：{err}" if snippet else f"无法加载摘要：{err}"
            self._summary_body.value = fallback
            self._status_text.value = "摘要加载失败，可切换原页或浏览器打开"
        else:
            self._summary_body.value = body
            self._status_text.value = ""
        self._page.update()

    def _apply_mode_visibility(self) -> None:
        is_summary = self._mode == "summary"
        self._summary_panel.visible = is_summary
        self._web_panel.visible = not is_summary and self._supports_web

    def _build_toolbar(self) -> ft.Container:
        p = palette()
        return ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                        icon_color=p["primary"],
                        tooltip="返回列表",
                        on_click=lambda _: self.close(),
                    ),
                    ft.Column(
                        [self._title_text, self._meta_text],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CONTENT_COPY_OUTLINED,
                        icon_color=p["text_secondary"],
                        tooltip="复制链接",
                        on_click=lambda _: self.copy_link(),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_BROWSER_OUTLINED,
                        icon_color=p["text_secondary"],
                        tooltip="在浏览器打开",
                        on_click=lambda _: self.open_external(),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=4, right=4, top=4, bottom=4),
            border=ft.border.only(bottom=ft.BorderSide(0.5, border_color())),
        )

    def _build_mode_bar(self) -> ft.Container:
        self._rebuild_mode_tabs()
        return ft.Container(
            content=ft.Row([self._mode_summary_tab, self._mode_web_tab], spacing=4),
            padding=ft.padding.symmetric(horizontal=PAGE_PAD_H, vertical=SPACE_SM),
        )

    def _rebuild_mode_tabs(self) -> None:
        p = palette()

        def tab(label: str, mode: str, host: ft.Container) -> None:
            selected = self._mode == mode
            host.content = ft.Text(
                label,
                size=13,
                weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
                color=p["text_primary"] if selected else p["text_muted"],
                text_align=ft.TextAlign.CENTER,
            )
            host.padding = ft.padding.symmetric(horizontal=12, vertical=8)
            host.border_radius = RADIUS_MD
            host.bgcolor = p["bg_elevated"] if selected else "transparent"
            host.alignment = ft.alignment.center

        tab("摘要", "summary", self._mode_summary_tab)
        web_label = "原页" if self._supports_web else "原页（浏览器）"
        tab(web_label, "web", self._mode_web_tab)
        self._mode_web_tab.visible = True
