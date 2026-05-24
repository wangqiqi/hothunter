"""可复用 UI 组件 — 对齐 HTML 原型。"""

from __future__ import annotations

import flet as ft

from src.config import SEARCH_ONLY_PLATFORMS, THEME
from src.models import Article
from src.ui.theme import (
    APP_MAX_WIDTH,
    BORDER,
    PLATFORM_STYLE,
    WORD_TAG_LEVELS,
    card_shadow,
    platform_badge_style,
    platform_short,
)


def section_label(text: str, icon: str | None = None) -> ft.Row:
  icons = {
      "search": ft.Icons.SEARCH,
      "grid": ft.Icons.GRID_VIEW,
      "list": ft.Icons.ARTICLE,
      "chart": ft.Icons.BAR_CHART,
  }
  items: list[ft.Control] = []
  if icon and icon in icons:
      items.append(ft.Icon(icons[icon], size=14, color=THEME["text_secondary"]))
  items.append(ft.Text(text, size=12, weight=ft.FontWeight.W_500, color=THEME["text_secondary"]))
  return ft.Row(items, spacing=6)


def section_header(title: str, icon: str, count_text: str = "") -> ft.Row:
  icons = {
      "list": ft.Icons.ARTICLE,
      "chart": ft.Icons.BAR_CHART,
  }
  return ft.Row(
      [
          ft.Row(
              [
                  ft.Icon(icons.get(icon, ft.Icons.LABEL), size=22, color=THEME["primary_light"]),
                  ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=THEME["text_primary"]),
              ],
              spacing=8,
          ),
          ft.Container(
              content=ft.Text(count_text, size=12, color=THEME["text_muted"]),
              padding=ft.padding.symmetric(horizontal=10, vertical=4),
              bgcolor=THEME["bg_card"],
              border_radius=20,
              visible=bool(count_text),
          ),
      ],
      alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
  )


def build_header() -> ft.Container:
  return ft.Container(
      content=ft.Stack(
          [
              ft.Container(
                  width=200,
                  height=200,
                  bgcolor="#ffffff1a",
                  border_radius=100,
                  right=-40,
                  top=-60,
              ),
              ft.Container(
                  width=150,
                  height=150,
                  bgcolor="#ffffff0d",
                  border_radius=75,
                  left=-30,
                  bottom=-50,
              ),
              ft.Container(
                  content=ft.Column(
                      [
                          ft.Row(
                              [
                                  ft.Icon(ft.Icons.EXPLORE, size=32, color="#ffffff"),
                                  ft.Text("热点猎手", size=26, weight=ft.FontWeight.BOLD, color="#ffffff"),
                              ],
                              spacing=10,
                          ),
                          ft.Text(
                              "实时流 · 定制追踪 · 自动刷新",
                              size=13,
                              color="#ffffffcc",
                          ),
                      ],
                      spacing=4,
                  ),
                  padding=ft.padding.only(left=20, right=20, top=20, bottom=16),
              ),
          ],
      ),
      gradient=ft.LinearGradient(
          begin=ft.alignment.top_left,
          end=ft.alignment.bottom_right,
          colors=[THEME["primary"], THEME["primary_dark"]],
      ),
      border_radius=ft.border_radius.only(bottom_left=24, bottom_right=24),
  )


def build_mode_tabs(
    current: str,
    on_stream,
    on_custom,
) -> ft.Container:
  def tab(label: str, value: str, on_click) -> ft.Container:
      selected = current == value
      return ft.Container(
          content=ft.Text(
              label,
              size=14,
              weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
              color="#ffffff" if selected else THEME["text_secondary"],
          ),
          padding=ft.padding.symmetric(horizontal=16, vertical=10),
          border_radius=10,
          bgcolor=THEME["primary"] if selected else "transparent",
          on_click=on_click,
          ink=not selected,
          expand=True,
          alignment=ft.alignment.center,
      )

  return ft.Container(
      content=ft.Row(
          [
              tab("实时流热点", "stream", on_stream),
              tab("定制热点", "custom", on_custom),
          ],
          spacing=4,
      ),
      padding=4,
      bgcolor=THEME["bg_card"],
      border_radius=12,
      border=ft.border.all(1, BORDER),
  )


def build_platform_chip(
    platform: dict[str, str],
    selected: bool,
    dimmed: bool,
    on_toggle,
) -> ft.Container:
  pid = platform["id"]
  style = PLATFORM_STYLE.get(pid, PLATFORM_STYLE["zhihu"])
  subtitle = "仅定制" if pid in SEARCH_ONLY_PLATFORMS else ("已选" if selected else "未选")
  subtitle_color = THEME["warning"] if pid in SEARCH_ONLY_PLATFORMS else THEME["text_muted"]

  checkbox = ft.Container(
      content=ft.Icon(ft.Icons.CHECK, size=14, color="#ffffff") if selected else None,
      width=22,
      height=22,
      border_radius=6,
      border=ft.border.all(2, THEME["primary"] if selected else BORDER),
      bgcolor=THEME["primary"] if selected else None,
      alignment=ft.alignment.center,
  )

  chip = ft.Container(
      content=ft.Row(
          [
              checkbox,
              ft.Container(
                  content=ft.Text(platform["icon"], size=14, weight=ft.FontWeight.BOLD, color="#fff"),
                  width=28,
                  height=28,
                  border_radius=6,
                  bgcolor=style["icon_bg"],
                  alignment=ft.alignment.center,
              ),
              ft.Column(
                  [
                      ft.Text(
                          platform["name"],
                          size=14,
                          weight=ft.FontWeight.W_600,
                          color=THEME["text_primary"],
                          max_lines=1,
                          overflow=ft.TextOverflow.ELLIPSIS,
                      ),
                      ft.Text(subtitle, size=11, color=subtitle_color),
                  ],
                  spacing=2,
                  expand=True,
              ),
          ],
          spacing=10,
      ),
      padding=14,
      border_radius=12,
      bgcolor="#6366f11a" if selected else THEME["bg_card"],
      border=ft.border.all(2, THEME["primary"] if selected else "transparent"),
      on_click=on_toggle,
      ink=True,
      expand=True,
      opacity=0.45 if dimmed else 1.0,
  )
  return chip


def article_card_subtitle(article: Article) -> str:
  if article.publish_time and article.publish_time.strip() != article.title.strip():
      return article.publish_time.strip()
  snippet = (article.content_snippet or "").strip()
  if snippet and snippet != article.title.strip() and article.title.strip() not in snippet:
      return snippet[:80]
  return ""


def build_article_card(article: Article, on_open_url) -> ft.Container:
  badge_bg, badge_fg = platform_badge_style(article.platform)
  short_name = platform_short(article.platform)
  subtitle = article_card_subtitle(article)
  hot_text = f"{article.hot_value}热度" if article.hot_value else ""

  meta_items: list[ft.Control] = []
  if hot_text:
      meta_items.append(
          ft.Row(
              [
                  ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, size=14, color=THEME["warning"]),
                  ft.Text(hot_text, size=12, color=THEME["warning"]),
              ],
              spacing=5,
          )
      )
  if subtitle:
      meta_items.append(
          ft.Row(
              [
                  ft.Icon(ft.Icons.ACCESS_TIME, size=14, color=THEME["text_secondary"]),
                  ft.Text(subtitle, size=12, color=THEME["text_secondary"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
              ],
              spacing=5,
          )
      )

  return ft.Container(
      content=ft.Column(
          [
              ft.Row(
                  [
                      ft.Container(
                          content=ft.Text(short_name, size=11, weight=ft.FontWeight.W_600, color=badge_fg),
                          padding=ft.padding.symmetric(horizontal=10, vertical=4),
                          bgcolor=badge_bg,
                          border_radius=8,
                      ),
                      ft.Text(
                          article.title,
                          size=15,
                          weight=ft.FontWeight.W_600,
                          color=THEME["text_primary"],
                          max_lines=2,
                          overflow=ft.TextOverflow.ELLIPSIS,
                          expand=True,
                      ),
                  ],
                  spacing=12,
                  vertical_alignment=ft.CrossAxisAlignment.START,
              ),
              ft.Row(meta_items, spacing=16, wrap=True) if meta_items else ft.Container(height=0),
              ft.Container(
                  content=ft.Row(
                      [
                          ft.Icon(ft.Icons.OPEN_IN_NEW, size=14, color=THEME["primary_light"]),
                          ft.Text("打开链接", size=13, weight=ft.FontWeight.W_600, color=THEME["primary_light"]),
                      ],
                      spacing=6,
                  ),
                  padding=ft.padding.symmetric(horizontal=16, vertical=10),
                  bgcolor=THEME["bg_card"],
                  border_radius=10,
                  on_click=lambda e, u=article.url: on_open_url(u),
                  ink=True,
              ),
          ],
          spacing=12,
      ),
      padding=16,
      border_radius=16,
      bgcolor=THEME["bg_secondary"],
      border=ft.border.all(1, BORDER),
  )


def build_word_tag(word: str, count: int, level: int) -> ft.Container:
  bg, fg = WORD_TAG_LEVELS[level % len(WORD_TAG_LEVELS)]
  return ft.Container(
      content=ft.Row(
          [
              ft.Text(word, size=13, weight=ft.FontWeight.W_500, color=fg),
              ft.Container(
                  content=ft.Text(str(count), size=11, color=fg),
                  padding=ft.padding.symmetric(horizontal=6, vertical=2),
                  bgcolor="#ffffff26",
                  border_radius=10,
              ),
          ],
          spacing=6,
      ),
      padding=ft.padding.symmetric(horizontal=14, vertical=8),
      bgcolor=bg,
      border_radius=20,
  )


def build_empty_state(title: str, desc: str) -> ft.Container:
  return ft.Container(
      content=ft.Column(
          [
              ft.Container(
                  content=ft.Icon(ft.Icons.INBOX_OUTLINED, size=40, color=THEME["text_muted"]),
                  width=80,
                  height=80,
                  border_radius=40,
                  bgcolor=THEME["bg_card"],
                  alignment=ft.alignment.center,
              ),
              ft.Text(title, size=16, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
              ft.Text(desc, size=13, color=THEME["text_muted"], text_align=ft.TextAlign.CENTER),
          ],
          horizontal_alignment=ft.CrossAxisAlignment.CENTER,
          spacing=8,
      ),
      padding=40,
      alignment=ft.alignment.center,
  )


def build_status_bar(message: str, count_text: str, active: bool) -> ft.Container:
  return ft.Container(
      content=ft.Row(
          [
              ft.Container(
                  width=10,
                  height=10,
                  border_radius=5,
                  bgcolor=THEME["success"] if active else THEME["text_muted"],
              ),
              ft.Text(message, size=13, color=THEME["text_secondary"], expand=True),
              ft.Text(count_text, size=13, weight=ft.FontWeight.W_600, color=THEME["primary_light"], visible=bool(count_text)),
          ],
          spacing=12,
      ),
      padding=ft.padding.symmetric(horizontal=16, vertical=14),
      bgcolor=THEME["bg_secondary"],
      border_radius=12,
      border=ft.border.all(1, BORDER),
  )


def search_card(content: ft.Control) -> ft.Container:
  return ft.Container(
      content=content,
      padding=16,
      bgcolor=THEME["bg_secondary"],
      border_radius=16,
      border=ft.border.all(1, BORDER),
      shadow=card_shadow(),
      margin=ft.margin.only(top=-12),
  )


def phone_shell(content: ft.Control) -> ft.Container:
  return ft.Container(
      content=content,
      width=APP_MAX_WIDTH,
      gradient=ft.LinearGradient(
          begin=ft.alignment.top_center,
          end=ft.alignment.bottom_center,
          colors=[THEME["bg_primary"], "#1a1f35"],
      ),
      border=ft.border.only(left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER)),
  )
