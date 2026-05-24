"""UI 主题 — iOS 风格浅色 / 深色双模式。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import flet as ft

from src.config import PLATFORMS, PLATFORM_NAMES

AppearanceMode = Literal["dark", "light"]

APP_MAX_WIDTH = 430

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

SETTINGS_PATH = Path.home() / ".hothunter" / "settings.json"

THEME_DARK: dict[str, str] = {
    "primary": "#0A84FF",
    "primary_light": "#409CFF",
    "primary_dark": "#0066CC",
    "primary_tint": "#0A84FF18",
    "bg_primary": "#000000",
    "bg_secondary": "#1C1C1E",
    "bg_card": "#2C2C2E",
    "bg_elevated": "#3A3A3C",
    "text_primary": "#FFFFFF",
    "text_secondary": "#98989D",
    "text_muted": "#636366",
    "separator": "#38383A",
    "success": "#30D158",
    "warning": "#FF9F0A",
    "danger": "#FF453A",
    "on_primary": "#FFFFFF",
    "shadow": "#00000066",
}

THEME_LIGHT: dict[str, str] = {
    "primary": "#007AFF",
    "primary_light": "#007AFF",
    "primary_dark": "#0051D5",
    "primary_tint": "#007AFF1A",
    "bg_primary": "#FFFFFF",
    "bg_secondary": "#F2F2F7",
    "bg_card": "#FFFFFF",
    "bg_elevated": "#FFFFFF",
    "text_primary": "#000000",
    "text_secondary": "#3C3C43",
    "text_muted": "#8E8E93",
    "separator": "#C6C6C8",
    "success": "#34C759",
    "warning": "#FF9500",
    "danger": "#FF3B30",
    "on_primary": "#FFFFFF",
    "shadow": "#0000001A",
}

THEMES: dict[AppearanceMode, dict[str, str]] = {
    "dark": THEME_DARK,
    "light": THEME_LIGHT,
}

WORD_TAG_LEVELS: dict[AppearanceMode, list[tuple[str, str]]] = {
    "dark": [
        ("#0A84FF33", "#64B5FF"),
        ("#5E5CE633", "#9B99F5"),
        ("#BF5AF233", "#D9A3FF"),
        ("#FF375F33", "#FF8DAF"),
        ("#30D15833", "#6EE7A0"),
    ],
    "light": [
        ("#007AFF26", "#005EB8"),
        ("#5856D626", "#3634A3"),
        ("#AF52DE26", "#8944AB"),
        ("#FF2D5526", "#C41E3A"),
        ("#34C75926", "#248A3D"),
    ],
}

PLATFORM_STYLE: dict[str, dict[str, str]] = {
    "zhihu": {"icon_bg": "#0066ff", "badge_bg": "#007AFF22", "badge_fg": "#0066CC", "short": "知乎"},
    "36kr": {"icon_bg": "#00b369", "badge_bg": "#34C75922", "badge_fg": "#248A3D", "short": "36氪"},
    "bilibili": {"icon_bg": "#ff6b9d", "badge_bg": "#FF2D5522", "badge_fg": "#C41E3A", "short": "B站"},
    "baidu": {"icon_bg": "#2932e5", "badge_bg": "#5856D622", "badge_fg": "#3634A3", "short": "百度"},
    "baidu_hot": {"icon_bg": "#2932e5", "badge_bg": "#5856D622", "badge_fg": "#3634A3", "short": "热搜"},
    "weibo": {"icon_bg": "#e6162d", "badge_bg": "#FF3B3022", "badge_fg": "#C41E20", "short": "微博"},
    "toutiao": {"icon_bg": "#ff2d55", "badge_bg": "#FF2D5522", "badge_fg": "#C41E3A", "short": "头条"},
    "douyin": {"icon_bg": "#111111", "badge_bg": "#00000033", "badge_fg": "#555555", "short": "抖音"},
    "tencent": {"icon_bg": "#12b7f5", "badge_bg": "#12b7f522", "badge_fg": "#0d8ecf", "short": "腾讯"},
    "netease": {"icon_bg": "#c20c0c", "badge_bg": "#c20c0c22", "badge_fg": "#a00a0a", "short": "网易"},
    "tieba": {"icon_bg": "#4879bd", "badge_bg": "#4879bd22", "badge_fg": "#3a6199", "short": "贴吧"},
    "xiaohongshu": {"icon_bg": "#ff2442", "badge_bg": "#ff244222", "badge_fg": "#cc1c35", "short": "小红书"},
}

PLATFORM_ID_BY_NAME: dict[str, str] = {p["name"]: p["id"] for p in PLATFORMS}

_controller: ThemeController | None = None


class ThemeController:
    def __init__(self, mode: AppearanceMode | None = None) -> None:
        self._mode: AppearanceMode = mode or load_appearance()

    @property
    def mode(self) -> AppearanceMode:
        return self._mode

    def is_dark(self) -> bool:
        return self._mode == "dark"

    def colors(self) -> dict[str, str]:
        return THEMES[self._mode]

    def flet_theme_mode(self) -> ft.ThemeMode:
        return ft.ThemeMode.DARK if self.is_dark() else ft.ThemeMode.LIGHT

    def set_mode(self, mode: AppearanceMode) -> None:
        if mode not in THEMES:
            raise ValueError(f"unknown appearance: {mode}")
        self._mode = mode
        save_appearance(mode)

    def toggle(self) -> AppearanceMode:
        self.set_mode("light" if self.is_dark() else "dark")
        return self._mode


def init_theme(controller: ThemeController | None = None) -> ThemeController:
    global _controller
    _controller = controller or ThemeController()
    return _controller


def get_theme() -> ThemeController:
    if _controller is None:
        return init_theme()
    return _controller


def palette() -> dict[str, str]:
    return get_theme().colors()


def border_color() -> str:
    return palette()["separator"]


def word_tag_levels() -> list[tuple[str, str]]:
    return WORD_TAG_LEVELS[get_theme().mode]


def load_appearance() -> AppearanceMode:
    try:
        if SETTINGS_PATH.is_file():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            mode = data.get("appearance", "dark")
            if mode in THEMES:
                return mode  # type: ignore[return-value]
    except (json.JSONDecodeError, OSError):
        pass
    return "dark"


def save_appearance(mode: AppearanceMode) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if SETTINGS_PATH.is_file():
        try:
            existing = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}
    existing["appearance"] = mode
    SETTINGS_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


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
    p = palette()
    return {
        "bgcolor": p["bg_secondary"],
        "border_radius": RADIUS_LG,
        "border": ft.border.all(0.5, p["separator"]),
    }


def ios_filled_button_style() -> dict:
    p = palette()
    return {
        "bgcolor": p["primary"],
        "border_radius": RADIUS_MD,
        "padding": ft.padding.symmetric(vertical=11, horizontal=14),
    }


def ios_secondary_button_style() -> dict:
    p = palette()
    return {
        "bgcolor": p["bg_card"],
        "border_radius": RADIUS_MD,
        "padding": ft.padding.symmetric(vertical=11, horizontal=14),
        "border": ft.border.all(0.5, p["separator"]),
    }


def apply_grouped_style(container: ft.Container) -> None:
    for key, value in grouped_surface().items():
        setattr(container, key, value)


def style_text_field(field: ft.TextField) -> None:
    p = palette()
    field.bgcolor = p["bg_card"]
    field.color = p["text_primary"]
    field.focused_border_color = p["primary"]
    field.border_color = "transparent"


def style_dropdown(dropdown: ft.Dropdown) -> None:
    p = palette()
    dropdown.bgcolor = p["bg_card"]
    dropdown.color = p["text_primary"]
    dropdown.border_color = p["separator"]
    dropdown.focused_border_color = p["primary"]


# 兼容旧代码：config.THEME
def legacy_theme_dict() -> dict[str, str]:
    return palette()
