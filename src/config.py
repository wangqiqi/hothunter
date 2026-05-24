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
]

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

# 对齐 docs/prototype/index.html 深色主题
THEME = {
    "primary": "#6366f1",
    "primary_light": "#818cf8",
    "primary_dark": "#4f46e5",
    "bg_primary": "#0f172a",
    "bg_secondary": "#1e293b",
    "bg_card": "#334155",
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
}
