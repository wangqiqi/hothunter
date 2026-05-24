"""UI 主题常量与工具 — 对齐 docs/prototype/index.html。"""

from __future__ import annotations

from src.config import PLATFORMS, PLATFORM_NAMES, THEME

APP_MAX_WIDTH = 430
BORDER = "#475569"

# 平台视觉：图标底色、徽章底色、徽章文字色、短名
PLATFORM_STYLE: dict[str, dict[str, str]] = {
    "zhihu": {"icon_bg": "#0066ff", "badge_bg": "#0066ff33", "badge_fg": "#4d9fff", "short": "知乎"},
    "36kr": {"icon_bg": "#00b369", "badge_bg": "#00b36933", "badge_fg": "#34c97a", "short": "36氪"},
    "bilibili": {"icon_bg": "#ff6b9d", "badge_bg": "#ff6b9d33", "badge_fg": "#ff8db5", "short": "B站"},
    "baidu": {"icon_bg": "#2932e5", "badge_bg": "#2932e533", "badge_fg": "#6b77ff", "short": "百度"},
    "weibo": {"icon_bg": "#e6162d", "badge_bg": "#e6162d33", "badge_fg": "#ff6b7a", "short": "微博"},
    "toutiao": {"icon_bg": "#ff2d55", "badge_bg": "#ff2d5533", "badge_fg": "#ff7a93", "short": "头条"},
}

PLATFORM_ID_BY_NAME: dict[str, str] = {p["name"]: p["id"] for p in PLATFORMS}

# 热词标签 5 档配色（循环）
WORD_TAG_LEVELS: list[tuple[str, str]] = [
    ("#6366f14d", "#a5b4fc"),
    ("#8b5cf64d", "#c4b5fd"),
    ("#ec48994d", "#f9a8d4"),
    ("#3b82f64d", "#93c5fd"),
    ("#10b9814d", "#6ee7b7"),
]


def platform_id(platform_label: str) -> str:
    """平台显示名 → 内部 id。"""
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


def card_shadow():
    import flet as ft

    return [
        ft.BoxShadow(
            spread_radius=0,
            blur_radius=20,
            color="#0000004d",
            offset=ft.Offset(0, 4),
        )
    ]
