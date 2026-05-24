"""平台爬虫注册表（内置 + 用户自定义）。"""

from __future__ import annotations

from collections.abc import Callable

from src.config import get_platform_names, get_search_only_platforms
from src.crawler import (
    baidu,
    baidu_hot,
    bilibili,
    douyin,
    kr36,
    netease,
    tencent,
    tieba,
    toutiao,
    weibo,
    xiaohongshu,
    zhihu,
)
from src.crawler.base import safe_fetch
from src.crawler.custom_sources import build_custom_crawlers
from src.models import Article
from src.modes import FetchMode, crawl_keyword, filter_platforms
from src.utils.hot_sort import sort_by_hot_value

CrawlerFunc = Callable[[str], list[Article]]

BUILTIN_CRAWLERS: dict[str, tuple[str, CrawlerFunc]] = {
    "zhihu": ("知乎热榜", zhihu.fetch_zhihu),
    "36kr": ("36氪", kr36.fetch_36kr),
    "bilibili": ("B站热门", bilibili.fetch_bilibili),
    "baidu": ("百度新闻", baidu.fetch_baidu),
    "baidu_hot": ("百度热搜", baidu_hot.fetch_baidu_hot),
    "weibo": ("微博热搜", weibo.fetch_weibo),
    "toutiao": ("今日头条", toutiao.fetch_toutiao),
    "douyin": ("抖音热榜", douyin.fetch_douyin),
    "tencent": ("腾讯新闻", tencent.fetch_tencent),
    "netease": ("网易热点", netease.fetch_netease),
    "tieba": ("贴吧热议", tieba.fetch_tieba),
    "xiaohongshu": ("小红书", xiaohongshu.fetch_xiaohongshu),
}


def all_crawlers() -> dict[str, tuple[str, CrawlerFunc]]:
    merged = dict(BUILTIN_CRAWLERS)
    merged.update(build_custom_crawlers())
    return merged


# 模块级缓存；修改 sources.json 后需重启 App
CRAWLERS = all_crawlers()


def reload_crawlers() -> None:
    global CRAWLERS
    CRAWLERS = all_crawlers()


def fetch_platform(platform_id: str, keyword: str) -> tuple[str, list[Article], str | None]:
    crawlers = all_crawlers()
    if platform_id not in crawlers:
        return platform_id, [], f"未知平台: {platform_id}"
    name, func = crawlers[platform_id]
    return safe_fetch(name, func, keyword)


def fetch_all(
    platform_ids: list[str],
    keyword: str,
    *,
    mode: FetchMode = FetchMode.CUSTOM,
    sort_by_hot: bool = True,
) -> tuple[list[Article], dict[str, str], dict[str, int]]:
    results: list[Article] = []
    errors: dict[str, str] = {}
    counts: dict[str, int] = {}
    names = get_platform_names()
    search_only = get_search_only_platforms()

    crawl_kw = crawl_keyword(mode, keyword)
    usable, skipped = filter_platforms(mode, platform_ids, search_only)

    for pid in skipped:
        name = names.get(pid, pid)
        errors[name] = "该平台仅支持「定制热点」模式"
        counts[name] = 0

    for pid in usable:
        name, articles, err = fetch_platform(pid, crawl_kw)
        results.extend(articles)
        counts[name] = len(articles)
        if err:
            errors[name] = err

    if sort_by_hot:
        results = sort_by_hot_value(results)

    return results, errors, counts
