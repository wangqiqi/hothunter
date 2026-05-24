"""可复用 UI 组件 — iOS 风格，随浅色/深色主题切换。"""

from __future__ import annotations

import flet as ft

from src.config import get_search_only_platforms
from src.models import Article
from src.ui.theme import (
    PAGE_PAD_H,
    PLATFORM_STYLE,
    RADIUS_MD,
    RADIUS_SM,
    SPACE_MD,
    SPACE_SM,
    SPACE_XS,
    border_color,
    grouped_surface,
    palette,
    platform_badge_style,
    platform_short,
    word_tag_levels,
)


def section_label(text: str, icon: str | None = None) -> ft.Row:
  p = palette()
  icons = {
      "search": ft.Icons.SEARCH,
      "grid": ft.Icons.GRID_VIEW,
      "list": ft.Icons.ARTICLE,
      "chart": ft.Icons.BAR_CHART,
  }
  items: list[ft.Control] = []
  if icon and icon in icons:
      items.append(ft.Icon(icons[icon], size=12, color=p["text_muted"]))
  items.append(
      ft.Text(text.upper(), size=11, weight=ft.FontWeight.W_600, color=p["text_muted"])
  )
  return ft.Row(items, spacing=SPACE_XS)


def section_header(title: str, icon: str, count_text: str = "") -> ft.Row:
  p = palette()
  return ft.Row(
      [
          ft.Text(title, size=17, weight=ft.FontWeight.W_600, color=p["text_primary"]),
          ft.Text(
              count_text,
              size=13,
              color=p["text_secondary"],
              visible=bool(count_text),
          ),
      ],
      alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
  )


def build_results_header_row(
    title_control: ft.Control,
    count_control: ft.Control,
    toolbar: ft.Control,
) -> ft.Column:
  """热点列表标题区：首行标题+条数，次行排序/筛选（避免 expand 撑满整屏）。"""
  return ft.Column(
      [
          ft.Row(
              [title_control, count_control],
              alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
          ),
          toolbar,
      ],
      spacing=SPACE_SM,
      tight=True,
  )


def build_header(on_appearance_toggle) -> ft.Container:
  """大标题 + 浅色/深色切换。"""
  p = palette()
  from src.ui.theme import get_theme

  theme = get_theme()
  return ft.Container(
      content=ft.Row(
          [
              ft.Column(
                  [
                      ft.Text(
                          "热点猎手",
                          size=28,
                          weight=ft.FontWeight.W_700,
                          color=p["text_primary"],
                      ),
                      ft.Text(
                          "实时流 · 定制追踪 · 整点刷新",
                          size=13,
                          color=p["text_secondary"],
                      ),
                  ],
                  spacing=2,
                  expand=True,
              ),
              ft.IconButton(
                  icon=ft.Icons.DARK_MODE_OUTLINED if theme.is_dark() else ft.Icons.LIGHT_MODE_OUTLINED,
                  icon_color=p["primary"],
                  tooltip="切换浅色 / 深色",
                  on_click=on_appearance_toggle,
              ),
          ],
          vertical_alignment=ft.CrossAxisAlignment.CENTER,
      ),
      padding=ft.padding.only(left=PAGE_PAD_H, right=PAGE_PAD_H - 4, top=12, bottom=8),
      border=ft.border.only(bottom=ft.BorderSide(0.5, border_color())),
  )


def build_mode_tabs(current: str, on_stream, on_custom) -> ft.SegmentedButton:
  """iOS 分段控件（Flet SegmentedButton，固定高度，不撑满父级 Column）。"""
  p = palette()

  def on_change(e: ft.ControlEvent) -> None:
      btn = e.control
      if not btn.selected:
          return
      choice = next(iter(btn.selected))
      if choice == "stream":
          on_stream(e)
      else:
          on_custom(e)

  return ft.SegmentedButton(
      selected={current},
      allow_empty_selection=False,
      segments=[
          ft.Segment(value="stream", label=ft.Text("实时流")),
          ft.Segment(value="custom", label=ft.Text("定制")),
      ],
      on_change=on_change,
      style=ft.ButtonStyle(
          color={
              ft.ControlState.SELECTED: p["on_primary"],
              ft.ControlState.DEFAULT: p["text_secondary"],
          },
          bgcolor={
              ft.ControlState.SELECTED: p["primary"],
              ft.ControlState.DEFAULT: p["bg_card"],
          },
          padding=ft.padding.symmetric(horizontal=14, vertical=10),
          shape=ft.RoundedRectangleBorder(radius=RADIUS_SM),
      ),
  )


def build_collapsible_section_header(
    title: str,
    *,
    icon: str | None = None,
    summary: str = "",
    expanded: bool,
    on_toggle,
) -> ft.Container:
  """可折叠区块标题（如选择平台）。"""
  p = palette()
  chevron = ft.Icons.EXPAND_MORE if expanded else ft.Icons.CHEVRON_RIGHT
  row_items: list[ft.Control] = []
  if icon:
      icons = {"grid": ft.Icons.GRID_VIEW, "search": ft.Icons.SEARCH}
      if icon in icons:
          row_items.append(ft.Icon(icons[icon], size=14, color=p["text_muted"]))
  row_items.append(
      ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=p["text_muted"])
  )
  if summary:
      row_items.append(
          ft.Text(summary, size=12, color=p["text_secondary"], expand=True, text_align=ft.TextAlign.RIGHT)
      )
  row_items.append(ft.Icon(chevron, size=20, color=p["text_muted"]))
  return ft.Container(
      content=ft.Row(row_items, spacing=SPACE_XS, alignment=ft.MainAxisAlignment.START),
      on_click=on_toggle,
      ink=True,
      padding=ft.padding.only(bottom=4),
  )


def build_platform_chip(
    platform: dict[str, str],
    selected: bool,
    dimmed: bool,
    on_toggle,
) -> ft.Container:
  p = palette()
  pid = platform["id"]
  style = PLATFORM_STYLE.get(pid, PLATFORM_STYLE["zhihu"])
  subtitle = "仅定制" if pid in get_search_only_platforms() else ("已选" if selected else "")

  checkbox = ft.Container(
      content=ft.Icon(ft.Icons.CHECK, size=12, color=p["on_primary"]) if selected else None,
      width=18,
      height=18,
      border_radius=5,
      border=ft.border.all(1.5, p["primary"] if selected else p["text_muted"]),
      bgcolor=p["primary"] if selected else None,
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
                          color=p["text_primary"],
                          max_lines=1,
                          overflow=ft.TextOverflow.ELLIPSIS,
                      ),
                      ft.Text(
                          subtitle,
                          size=10,
                          color=p["warning"] if pid in get_search_only_platforms() else p["text_muted"],
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
      bgcolor=p["bg_card"] if not selected else p["primary_tint"],
      border=ft.border.all(1, p["primary"] if selected else border_color()),
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


def build_article_row(article: Article, on_open_article) -> ft.Container:
  p = palette()
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
                          color=p["text_primary"],
                          max_lines=2,
                          overflow=ft.TextOverflow.ELLIPSIS,
                      ),
                      ft.Text(
                          meta,
                          size=12,
                          color=p["text_secondary"],
                          max_lines=1,
                          overflow=ft.TextOverflow.ELLIPSIS,
                          visible=bool(meta),
                      ),
                  ],
                  spacing=2,
                  expand=True,
              ),
              ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=p["text_muted"]),
          ],
          spacing=SPACE_SM,
          vertical_alignment=ft.CrossAxisAlignment.CENTER,
      ),
      padding=ft.padding.symmetric(horizontal=12, vertical=10),
      on_click=lambda e, a=article: on_open_article(a),
      ink=True,
  )


def build_articles_group(articles: list[Article], on_open_article) -> ft.Control:
  if not articles:
      return build_empty_state("暂无结果", "刷新或调整筛选条件")
  rows: list[ft.Control] = []
  sep = border_color()
  for i, article in enumerate(articles):
      rows.append(build_article_row(article, on_open_article))
      if i < len(articles) - 1:
          rows.append(
              ft.Container(
                  content=ft.Divider(height=0.5, color=sep),
                  padding=ft.padding.only(left=44),
              )
          )
  return ft.Container(
      content=ft.Column(rows, spacing=0),
      clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
      **grouped_surface(),
  )


def build_article_card(article: Article, on_open_article) -> ft.Container:
  return ft.Container(content=build_article_row(article, on_open_article), **grouped_surface())


def build_word_tag(word: str, count: int, level: int) -> ft.Container:
  levels = word_tag_levels()
  bg, fg = levels[level % len(levels)]
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
  p = palette()
  return ft.Container(
      content=ft.Column(
          [
              ft.Icon(ft.Icons.INBOX_OUTLINED, size=32, color=p["text_muted"]),
              ft.Text(title, size=15, weight=ft.FontWeight.W_600, color=p["text_primary"]),
              ft.Text(desc, size=12, color=p["text_muted"], text_align=ft.TextAlign.CENTER),
          ],
          horizontal_alignment=ft.CrossAxisAlignment.CENTER,
          spacing=SPACE_SM,
      ),
      padding=ft.padding.symmetric(horizontal=PAGE_PAD_H, vertical=24),
      alignment=ft.alignment.center,
      **grouped_surface(),
  )


def build_status_bar(message: str, count_text: str, active: bool) -> ft.Container:
  p = palette()
  return ft.Container(
      content=ft.Row(
          [
              ft.Container(
                  width=8,
                  height=8,
                  border_radius=4,
                  bgcolor=p["success"] if active else p["text_muted"],
              ),
              ft.Text(message, size=13, color=p["text_secondary"], expand=True),
              ft.Text(
                  count_text,
                  size=13,
                  weight=ft.FontWeight.W_500,
                  color=p["primary_light"],
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
  p = palette()
  shadow_color = p.get("shadow", "#00000040")

  def item(nav_id: str, label: str, icon_key: str) -> ft.Container:
      selected = active == nav_id
      color = p["primary"] if selected else p["text_muted"]
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
      bgcolor=p["bg_secondary"],
      border=ft.border.only(top=ft.BorderSide(0.5, border_color())),
      padding=ft.padding.only(left=8, right=8, top=4, bottom=8),
      shadow=ft.BoxShadow(
          spread_radius=0,
          blur_radius=12,
          color=shadow_color,
          offset=ft.Offset(0, -2),
      ),
  )


def build_back_to_top(visible: bool, on_click) -> ft.Container:
  p = palette()
  return ft.Container(
      content=ft.IconButton(
          icon=ft.Icons.KEYBOARD_ARROW_UP_ROUNDED,
          icon_color=p["on_primary"],
          icon_size=22,
          bgcolor=p["primary"],
          style=ft.ButtonStyle(shape=ft.CircleBorder()),
          tooltip="返回顶部",
          on_click=on_click,
      ),
      visible=visible,
      animate_opacity=200,
  )


def phone_shell(content: ft.Control) -> ft.Container:
  from src.ui.theme import APP_MAX_WIDTH

  p = palette()
  return ft.Container(
      content=content,
      width=APP_MAX_WIDTH,
      expand=True,
      bgcolor=p["bg_primary"],
      border=ft.border.only(
          left=ft.BorderSide(0.5, border_color()),
          right=ft.BorderSide(0.5, border_color()),
      ),
  )
