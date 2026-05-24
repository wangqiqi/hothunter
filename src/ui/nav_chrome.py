"""底部导航隐现、内容区留白与窗口尺寸 — 移动端优先。"""

from __future__ import annotations

import flet as ft

# 滚动判定
SCROLL_DELTA_THRESHOLD = 8.0
SCROLL_TOP_SHOW_PX = 48.0
SCROLL_BOTTOM_SHOW_PX = 72.0

# 底栏几何（与 components.build_bottom_nav 内边距一致）
NAV_BAR_HEIGHT = 52
NAV_SAFE_BOTTOM_MIN = 8
NAV_EDGE_ZONE_HEIGHT = 56
NAV_HIDE_SLIDE_PX = 68
NAV_ANIMATION_MS = 220
BACK_TOP_GAP = 10

MOBILE_PLATFORMS = frozenset({"ios", "android"})


def is_mobile_platform(platform: str) -> bool:
    return platform in MOBILE_PLATFORMS


def configure_page_window(page: ft.Page, *, max_width: int) -> None:
    """桌面模拟手机宽屏；真机占满可视高度。"""
    page.window.width = max_width
    page.window.min_width = max_width
    page.window.max_width = max_width
    if is_mobile_platform(page.platform):
        page.window.min_height = 480
    else:
        page.window.height = 900
        page.window.min_height = 640


def scroll_content_inset(*, nav_visible: bool) -> int:
    """列表底部留白，避免被底栏或 Home 条遮挡。"""
    if nav_visible:
        return NAV_BAR_HEIGHT + NAV_SAFE_BOTTOM_MIN + 16
    return NAV_EDGE_ZONE_HEIGHT // 2 + NAV_SAFE_BOTTOM_MIN


def nav_slide_offset(*, visible: bool) -> ft.Offset:
    return ft.Offset(0, 0) if visible else ft.Offset(0, NAV_HIDE_SLIDE_PX)


def nav_opacity(*, visible: bool) -> float:
    return 1.0 if visible else 0.0


def back_top_bottom(*, nav_visible: bool) -> float:
    return float(scroll_content_inset(nav_visible=nav_visible) + BACK_TOP_GAP)


def decide_nav_visible_on_scroll(
    *,
    pixels: float,
    max_scroll_extent: float,
    scroll_delta: float | None,
    direction: str | None,
    current: bool,
) -> bool:
    """根据滚动位置与方向决定是否显示底栏。"""
    at_top = pixels <= SCROLL_TOP_SHOW_PX
    near_bottom = max_scroll_extent > 0 and pixels >= max_scroll_extent - SCROLL_BOTTOM_SHOW_PX

    if at_top or near_bottom:
        return True

    if scroll_delta is not None:
        if scroll_delta > SCROLL_DELTA_THRESHOLD:
            return False
        if scroll_delta < -SCROLL_DELTA_THRESHOLD:
            return True

    if direction in ("reverse", "up"):
        return True
    if direction in ("forward", "down"):
        return False

    return current
