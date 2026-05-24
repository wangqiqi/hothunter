"""应用配置：平台、停用词、主题色。"""

from __future__ import annotations

from typing import TypedDict


class PlatformMeta(TypedDict):
    id: str
    name: str
    icon: str


PLATFORMS: list[PlatformMeta] = [
    {"id": "zhihu", "name": "知乎热榜", "icon": "知"},
    {"id": "36kr", "name": "36氪", "icon": "氪"},
    {"id": "bilibili", "name": "B站热门", "icon": "B"},
    {"id": "baidu", "name": "百度新闻", "icon": "度"},
    {"id": "weibo", "name": "微博热搜", "icon": "微"},
    {"id": "toutiao", "name": "今日头条", "icon": "条"},
]

# 仅定制模式可用（搜索型，非原生热榜）
SEARCH_ONLY_PLATFORMS: frozenset[str] = frozenset({"baidu"})

PLATFORM_NAMES: dict[str, str] = {p["id"]: p["name"] for p in PLATFORMS}

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
