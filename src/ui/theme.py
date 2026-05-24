"""UI 主题常量与工具 — iOS 深色紧凑风格。"""

from __future__ import annotations

import flet as ft

from src.config import PLATFORMS, PLATFORM_NAMES, THEME

APP_MAX_WIDTH = 430
BORDER = THEME["separator"]

# 紧凑间距 / 圆角（对齐 iOS Human Interface Guidelines）
SPACE_XS = 4
SPACE_SM = 6
SPACE_MD = 10
SPACE_LG = 14
PAGE_PAD_H = 16
RADIUS_SM = 8
RADIUS_MD = 10
RADIUS_LG = 12
RADIUS_XL = 14

FONT_FAMILY = "PingFang SC, -apple-system, BlinkMacSystemFont, SF Pro Text, sans-serif"

PLATFORM_STYLE: dict[str, dict[str, str]] = {
    "zhihu": {"icon_bg": "#0066ff", "badge_bg": "#0A84FF22", "badge_fg": "#64B5FF", "short": "知乎"},
    "36kr": {"icon_bg": "#00b369", "badge_bg": "#30D15822", "badge_fg": "#6EE7A0", "short": "36氪"},
    "bilibili": {"icon_bg": "#ff6b9d", "badge_bg": "#FF375F22", "badge_fg": "#FF8DAF", "short": "B站"},
    "baidu": {"icon_bg": "#2932e5", "badge_bg": "#5E5CE622", "badge_fg": "#9B99F5", "short": "百度"},
    "weibo": {"icon_bg": "#e6162d", "badge_bg": "#FF453A22", "badge_fg": "#FF8A82", "short": "微博"},
    "toutiao": {"icon_bg": "#ff2d55", "badge_bg": "#FF375F22", "badge_fg": "#FF8DAF", "short": "头条"},
}

PLATFORM_ID_BY_NAME: dict[str, str] = {p["name"]: p["id"] for p in PLATFORMS}

WORD_TAG_LEVELS: list[tuple[str, str]] = [
    ("#0A84FF33", "#64B5FF"),
    ("#5E5CE633", "#9B99F5"),
    ("#BF5AF233", "#D9A3FF"),
    ("#FF375F33", "#FF8DAF"),
    ("#30D15833", "#6EE7A0"),
]


def platform_id(platform_label: str) -> str:
    if platform_label in PLATFORM_ID_BY_NAME:
        return PLATFORM_ID_BY_NAME[platform_label]
    for pid, name in PLATFORM_NAMES.items():
        if name in platform_label or platform_label in name:
            return pid
    return "zhihu"


def platform_short(platform_label: str) -> str:
    pid = platform_id(platform_label)
    return PLATFORM_STYLE.get(pid, {}).get("short", platform_label[:4])


def platform_badge_style(platform_label: str) -> tuple[str, str]:
    pid = platform_id(platform_label)
    style = PLATFORM_STYLE.get(pid, PLATFORM_STYLE["zhihu"])
    return style["badge_bg"], style["badge_fg"]


def grouped_surface() -> dict:
    """iOS 分组列表容器样式。"""
    return {
        "bgcolor": THEME["bg_secondary"],
        "border_radius": RADIUS_LG,
        "border": ft.border.all(0.5, BORDER),
    }


def card_shadow() -> list:
    return [
        ft.BoxShadow(
            spread_radius=0,
            blur_radius=12,
            color="#00000066",
            offset=ft.Offset(0, 2),
        )
    ]


def ios_filled_button_style() -> dict:
    return {
        "bgcolor": THEME["primary"],
        "border_radius": RADIUS_MD,
        "padding": ft.padding.symmetric(vertical=11, horizontal=14),
    }


def ios_secondary_button_style() -> dict:
    return {
        "bgcolor": THEME["bg_card"],
        "border_radius": RADIUS_MD,
        "padding": ft.padding.symmetric(vertical=11, horizontal=14),
    }
