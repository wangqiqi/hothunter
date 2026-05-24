"""可复用 UI 组件 — iOS 深色紧凑风格。"""

from __future__ import annotations

import flet as ft

from src.config import SEARCH_ONLY_PLATFORMS, THEME
from src.models import Article
from src.ui.theme import (
    BORDER,
    PAGE_PAD_H,
    PLATFORM_STYLE,
    RADIUS_LG,
    RADIUS_MD,
    RADIUS_SM,
    SPACE_MD,
    SPACE_SM,
    SPACE_XS,
    WORD_TAG_LEVELS,
    grouped_surface,
    ios_filled_button_style,
    ios_secondary_button_style,
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
      items.append(ft.Icon(icons[icon], size=12, color=THEME["text_muted"]))
  items.append(
      ft.Text(
          text.upper(),
          size=11,
          weight=ft.FontWeight.W_600,
          color=THEME["text_muted"],
      )
  )
  return ft.Row(items, spacing=SPACE_XS)


def section_header(title: str, icon: str, count_text: str = "") -> ft.Row:
  return ft.Row(
      [
          ft.Text(title, size=17, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
          ft.Text(
              count_text,
              size=13,
              color=THEME["text_secondary"],
              visible=bool(count_text),
          ),
      ],
      alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
  )


def build_header() -> ft.Container:
  """大标题导航区 — 无渐变装饰，贴近 iOS 首屏。"""
  return ft.Container(
      content=ft.Column(
          [
              ft.Text(
                  "热点猎手",
                  size=28,
                  weight=ft.FontWeight.W_700,
                  color=THEME["text_primary"],
              ),
              ft.Text(
                  "实时流 · 定制追踪 · 整点刷新",
                  size=13,
                  color=THEME["text_secondary"],
              ),
          ],
          spacing=2,
      ),
      padding=ft.padding.only(left=PAGE_PAD_H, right=PAGE_PAD_H, top=12, bottom=8),
      border=ft.border.only(bottom=ft.BorderSide(0.5, BORDER)),
  )


def build_mode_tabs(
    current: str,
    on_stream,
    on_custom,
) -> ft.Container:
  """iOS 分段控件（UISegmentedControl）风格。"""

  def tab(label: str, value: str, on_click) -> ft.Container:
      selected = current == value
      return ft.Container(
          content=ft.Text(
              label,
              size=13,
              weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
              color=THEME["text_primary"] if selected else THEME["text_secondary"],
          ),
          padding=ft.padding.symmetric(horizontal=10, vertical=7),
          border_radius=RADIUS_SM,
          bgcolor=THEME["bg_elevated"] if selected else "transparent",
          on_click=on_click,
          ink=not selected,
          expand=True,
          alignment=ft.alignment.center,
      )

  return ft.Container(
      content=ft.Row(
          [
              tab("实时流", "stream", on_stream),
              tab("定制", "custom", on_custom),
          ],
          spacing=2,
      ),
      padding=2,
      bgcolor=THEME["bg_card"],
      border_radius=RADIUS_MD,
  )


def build_platform_chip(
    platform: dict[str, str],
    selected: bool,
    dimmed: bool,
    on_toggle,
) -> ft.Container:
  pid = platform["id"]
  style = PLATFORM_STYLE.get(pid, PLATFORM_STYLE["zhihu"])
  subtitle = "仅定制" if pid in SEARCH_ONLY_PLATFORMS else ("已选" if selected else "")

  checkbox = ft.Container(
      content=ft.Icon(ft.Icons.CHECK, size=12, color="#ffffff") if selected else None,
      width=18,
      height=18,
      border_radius=5,
      border=ft.border.all(1.5, THEME["primary"] if selected else THEME["text_muted"]),
      bgcolor=THEME["primary"] if selected else None,
      alignment=ft.alignment.center,
  )

  return ft.Container(
      content=ft.Row(
          [
              checkbox,
              ft.Container(
                  content=ft.Text(platform["icon"], size=12, weight=ft.FontWeight.W_600, color="#fff"),
                  width=24,
                  height=24,
                  border_radius=6,
                  bgcolor=style["icon_bg"],
                  alignment=ft.alignment.center,
              ),
              ft.Column(
                  [
                      ft.Text(
                          platform["name"],
                          size=13,
                          weight=ft.FontWeight.W_500,
                          color=THEME["text_primary"],
                          max_lines=1,
                          overflow=ft.TextOverflow.ELLIPSIS,
                      ),
                      ft.Text(
                          subtitle,
                          size=10,
                          color=THEME["warning"] if pid in SEARCH_ONLY_PLATFORMS else THEME["text_muted"],
                          visible=bool(subtitle),
                      ),
                  ],
                  spacing=0,
                  expand=True,
              ),
          ],
          spacing=SPACE_SM,
      ),
      padding=ft.padding.symmetric(horizontal=10, vertical=8),
      border_radius=RADIUS_MD,
      bgcolor=THEME["bg_card"] if not selected else "#0A84FF18",
      border=ft.border.all(1, THEME["primary"] if selected else BORDER),
      on_click=on_toggle,
      ink=True,
      expand=True,
      opacity=0.45 if dimmed else 1.0,
  )


def article_card_subtitle(article: Article) -> str:
  if article.publish_time and article.publish_time.strip() != article.title.strip():
      return article.publish_time.strip()
  snippet = (article.content_snippet or "").strip()
  if snippet and snippet != article.title.strip() and article.title.strip() not in snippet:
      return snippet[:72]
  return ""


def build_article_row(article: Article, on_open_url) -> ft.Container:
  """分组列表单行。"""
  badge_bg, badge_fg = platform_badge_style(article.platform)
  short_name = platform_short(article.platform)
  subtitle = article_card_subtitle(article)
  hot_text = f"{article.hot_value} 热度" if article.hot_value else ""
  meta = " · ".join(x for x in (hot_text, subtitle) if x)

  return ft.Container(
      content=ft.Row(
          [
              ft.Container(
                  content=ft.Text(short_name, size=10, weight=ft.FontWeight.W_600, color=badge_fg),
                  padding=ft.padding.symmetric(horizontal=6, vertical=2),
                  bgcolor=badge_bg,
                  border_radius=6,
              ),
              ft.Column(
                  [
                      ft.Text(
                          article.title,
                          size=15,
                          weight=ft.FontWeight.W_500,
                          color=THEME["text_primary"],
                          max_lines=2,
                          overflow=ft.TextOverflow.ELLIPSIS,
                      ),
                      ft.Text(
                          meta,
                          size=12,
                          color=THEME["text_secondary"],
                          max_lines=1,
                          overflow=ft.TextOverflow.ELLIPSIS,
                          visible=bool(meta),
                      ),
                  ],
                  spacing=2,
                  expand=True,
              ),
              ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=THEME["text_muted"]),
          ],
          spacing=SPACE_SM,
          vertical_alignment=ft.CrossAxisAlignment.CENTER,
      ),
      padding=ft.padding.symmetric(horizontal=12, vertical=10),
      on_click=lambda e, u=article.url: on_open_url(u),
      ink=True,
  )


def build_articles_group(articles: list[Article], on_open_url) -> ft.Control:
  """iOS UITableView 分组列表样式。"""
  if not articles:
      return build_empty_state("暂无结果", "刷新或调整筛选条件")
  rows: list[ft.Control] = []
  for i, article in enumerate(articles):
      rows.append(build_article_row(article, on_open_url))
      if i < len(articles) - 1:
          rows.append(
              ft.Container(
                  content=ft.Divider(height=0.5, color=BORDER),
                  padding=ft.padding.only(left=44),
              )
          )
  return ft.Container(
      content=ft.Column(rows, spacing=0),
      clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
      **grouped_surface(),
  )


def build_article_card(article: Article, on_open_url) -> ft.Container:
  """兼容旧调用 — 委托分组行。"""
  return ft.Container(
      content=build_article_row(article, on_open_url),
      **grouped_surface(),
  )


def build_word_tag(word: str, count: int, level: int) -> ft.Container:
  bg, fg = WORD_TAG_LEVELS[level % len(WORD_TAG_LEVELS)]
  return ft.Container(
      content=ft.Row(
          [
              ft.Text(word, size=12, weight=ft.FontWeight.W_500, color=fg),
              ft.Text(str(count), size=11, color=fg),
          ],
          spacing=SPACE_XS,
      ),
      padding=ft.padding.symmetric(horizontal=10, vertical=5),
      bgcolor=bg,
      border_radius=16,
  )


def build_empty_state(title: str, desc: str) -> ft.Container:
  return ft.Container(
      content=ft.Column(
          [
              ft.Icon(ft.Icons.INBOX_OUTLINED, size=32, color=THEME["text_muted"]),
              ft.Text(title, size=15, weight=ft.FontWeight.W_600, color=THEME["text_primary"]),
              ft.Text(desc, size=12, color=THEME["text_muted"], text_align=ft.TextAlign.CENTER),
          ],
          horizontal_alignment=ft.CrossAxisAlignment.CENTER,
          spacing=SPACE_SM,
      ),
      padding=ft.padding.symmetric(horizontal=PAGE_PAD_H, vertical=24),
      alignment=ft.alignment.center,
      **grouped_surface(),
  )


def build_status_bar(message: str, count_text: str, active: bool) -> ft.Container:
  return ft.Container(
      content=ft.Row(
          [
              ft.Container(
                  width=8,
                  height=8,
                  border_radius=4,
                  bgcolor=THEME["success"] if active else THEME["text_muted"],
              ),
              ft.Text(message, size=13, color=THEME["text_secondary"], expand=True),
              ft.Text(
                  count_text,
                  size=13,
                  weight=ft.FontWeight.W_500,
                  color=THEME["primary_light"],
                  visible=bool(count_text),
              ),
          ],
          spacing=SPACE_SM,
      ),
      padding=ft.padding.symmetric(horizontal=12, vertical=10),
      **grouped_surface(),
  )


def search_card(content: ft.Control) -> ft.Container:
  return ft.Container(
      content=content,
      padding=SPACE_MD,
      margin=ft.margin.only(top=-6),
      **grouped_surface(),
  )


NAV_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("hot", "热点", "explore"),
    ("history", "历史", "history"),
    ("analysis", "分析", "bar_chart"),
    ("settings", "设置", "settings"),
)

_NAV_ICONS = {
    "explore": ft.Icons.EXPLORE_OUTLINED,
    "history": ft.Icons.HISTORY,
    "bar_chart": ft.Icons.BAR_CHART_OUTLINED,
    "settings": ft.Icons.SETTINGS_OUTLINED,
}


def build_bottom_nav(active: str, on_select) -> ft.Container:
  def item(nav_id: str, label: str, icon_key: str) -> ft.Container:
      selected = active == nav_id
      color = THEME["primary"] if selected else THEME["text_muted"]
      return ft.Container(
          content=ft.Column(
              [
                  ft.Icon(_NAV_ICONS[icon_key], size=22, color=color),
                  ft.Text(
                      label,
                      size=10,
                      weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400,
                      color=color,
                  ),
              ],
              horizontal_alignment=ft.CrossAxisAlignment.CENTER,
              spacing=2,
          ),
          padding=ft.padding.symmetric(horizontal=8, vertical=6),
          on_click=lambda e, nid=nav_id: on_select(nid),
          expand=True,
      )

  return ft.Container(
      content=ft.Row(
          [item(nid, label, icon) for nid, label, icon in NAV_ITEMS],
          alignment=ft.MainAxisAlignment.SPACE_AROUND,
      ),
      bgcolor=THEME["bg_secondary"],
      border=ft.border.only(top=ft.BorderSide(0.5, BORDER)),
      padding=ft.padding.only(left=8, right=8, top=4, bottom=8),
  )


def build_back_to_top(visible: bool, on_click) -> ft.Container:
  return ft.Container(
      content=ft.IconButton(
          icon=ft.Icons.KEYBOARD_ARROW_UP_ROUNDED,
          icon_color="#ffffff",
          icon_size=22,
          bgcolor=THEME["primary"],
          style=ft.ButtonStyle(shape=ft.CircleBorder()),
          tooltip="返回顶部",
          on_click=on_click,
      ),
      visible=visible,
      animate_opacity=200,
  )


def phone_shell(content: ft.Control) -> ft.Container:
  from src.ui.theme import APP_MAX_WIDTH

  return ft.Container(
      content=content,
      width=APP_MAX_WIDTH,
      bgcolor=THEME["bg_primary"],
      border=ft.border.only(left=ft.BorderSide(0.5, BORDER), right=ft.BorderSide(0.5, BORDER)),
  )
