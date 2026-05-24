"""列表展示层：排序与筛选（不影响抓取逻辑）。"""

from __future__ import annotations

from src.models import Article
from src.utils.hot_sort import parse_hot_value, sort_by_hot_value

SORT_OPTIONS: dict[str, str] = {
    "hot_desc": "热度从高到低",
    "hot_asc": "热度从低到高",
    "title": "标题 A-Z",
    "time_desc": "抓取时间最新",
    "platform": "按平台分组",
}

DEFAULT_SORT = "hot_desc"
ALL_PLATFORMS = "all"


def filter_articles(
    articles: list[Article],
    *,
    title_keyword: str = "",
    platform: str = ALL_PLATFORMS,
) -> list[Article]:
    """对已有结果做客户端筛选。"""
    result = articles
    platform = (platform or ALL_PLATFORMS).strip()
    title_keyword = (title_keyword or "").strip()

    if platform != ALL_PLATFORMS:
        result = [a for a in result if a.platform == platform or platform in a.platform]

    if title_keyword:
        kw = title_keyword.casefold()
        result = [a for a in result if kw in a.title.casefold()]

    return result


def sort_articles(articles: list[Article], sort_key: str) -> list[Article]:
    if sort_key == "hot_desc":
        return sort_by_hot_value(articles)
    if sort_key == "hot_asc":
        return sorted(articles, key=lambda a: parse_hot_value(a.hot_value))
    if sort_key == "title":
        return sorted(articles, key=lambda a: a.title.casefold())
    if sort_key == "time_desc":
        return sorted(articles, key=lambda a: a.fetch_time, reverse=True)
    if sort_key == "platform":
        return sorted(articles, key=lambda a: (a.platform, -parse_hot_value(a.hot_value)))
    return list(articles)


def apply_view(
    articles: list[Article],
    *,
    sort_key: str = DEFAULT_SORT,
    title_keyword: str = "",
    platform: str = ALL_PLATFORMS,
) -> list[Article]:
    filtered = filter_articles(articles, title_keyword=title_keyword, platform=platform)
    return sort_articles(filtered, sort_key)
