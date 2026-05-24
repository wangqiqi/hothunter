"""平台爬虫注册表。"""

from __future__ import annotations

from collections.abc import Callable

from src.crawler import baidu, bilibili, kr36, zhihu
from src.crawler.base import safe_fetch
from src.models import Article

CrawlerFunc = Callable[[str], list[Article]]

CRAWLERS: dict[str, tuple[str, CrawlerFunc]] = {
    "zhihu": ("知乎热榜", zhihu.fetch_zhihu),
    "36kr": ("36氪", kr36.fetch_36kr),
    "bilibili": ("B站热门", bilibili.fetch_bilibili),
    "baidu": ("百度新闻", baidu.fetch_baidu),
}


def fetch_platform(platform_id: str, keyword: str) -> tuple[str, list[Article], str | None]:
    if platform_id not in CRAWLERS:
        return platform_id, [], f"未知平台: {platform_id}"
    name, func = CRAWLERS[platform_id]
    return safe_fetch(name, func, keyword)


def fetch_all(platform_ids: list[str], keyword: str) -> tuple[list[Article], dict[str, str]]:
    results: list[Article] = []
    errors: dict[str, str] = {}
    for pid in platform_ids:
        name, articles, err = fetch_platform(pid, keyword)
        results.extend(articles)
        if err:
            errors[name] = err
    return results, errors
