"""应用配置：平台、停用词、主题色。"""

from __future__ import annotations

from typing import TypedDict


class PlatformMeta(TypedDict):
    id: str
    name: str
    icon: str


# 内置平台（必接清单 — 见 docs/PLATFORMS.md）
BUILTIN_PLATFORMS: list[PlatformMeta] = [
    {"id": "weibo", "name": "微博热搜", "icon": "微"},
    {"id": "zhihu", "name": "知乎热榜", "icon": "知"},
    {"id": "baidu_hot", "name": "百度热搜", "icon": "搜"},
    {"id": "douyin", "name": "抖音热榜", "icon": "抖"},
    {"id": "toutiao", "name": "今日头条", "icon": "条"},
    {"id": "bilibili", "name": "B站热门", "icon": "B"},
    {"id": "tencent", "name": "腾讯新闻", "icon": "腾"},
    {"id": "netease", "name": "网易热点", "icon": "易"},
    {"id": "tieba", "name": "贴吧热议", "icon": "吧"},
    {"id": "36kr", "name": "36氪", "icon": "氪"},
    {"id": "baidu", "name": "百度新闻", "icon": "闻"},
    {"id": "xiaohongshu", "name": "小红书", "icon": "红"},
]

# 仅定制模式（搜索型 / 无公开热榜）
BUILTIN_SEARCH_ONLY: frozenset[str] = frozenset({"baidu", "xiaohongshu"})


def get_platforms() -> list[PlatformMeta]:
    """内置 + ~/.hothunter/sources.json 自定义源。"""
    from src.crawler.custom_sources import custom_platform_metas

    return list(BUILTIN_PLATFORMS) + custom_platform_metas()


def get_search_only_platforms() -> frozenset[str]:
    from src.crawler.custom_sources import custom_search_only_ids

    return BUILTIN_SEARCH_ONLY | custom_search_only_ids()


def get_platform_names() -> dict[str, str]:
    return {p["id"]: p["name"] for p in get_platforms()}


# 兼容旧 import
PLATFORMS = BUILTIN_PLATFORMS
SEARCH_ONLY_PLATFORMS = BUILTIN_SEARCH_ONLY
PLATFORM_NAMES = {p["id"]: p["name"] for p in BUILTIN_PLATFORMS}

DEFAULT_KEYWORD = "AI"
REQUEST_DELAY_SEC = 1.0
HISTORY_LIMIT = 100
WORD_FREQ_TOP_N = 10

STOPWORDS: frozenset[str] = frozenset(
    {
        "的",
        "了",
        "是",
        "在",
        "和",
        "与",
        "有",
        "我",
        "也",
        "不",
        "这",
        "那",
        "你",
        "他",
        "她",
        "它",
        "们",
        "一个",
        "什么",
        "如何",
        "为什么",
        "可以",
        "已经",
        "进行",
        "通过",
        "关于",
        "以及",
        "或者",
        "因为",
        "所以",
        "但是",
        "如果",
        "这个",
        "那个",
        "没有",
        "可能",
        "成为",
        "表示",
        "认为",
        "报道",
        "消息",
        "新闻",
        "热点",
        "发布",
        "宣布",
        "今日",
        "昨日",
        "最新",
    }
)

# 界面配色见 src/ui/theme.py（支持浅色 / 深色，运行时 palette() 获取当前色板）
