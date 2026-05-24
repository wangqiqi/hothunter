"""知乎热榜爬虫（官方 hot-list-web API）。"""

from __future__ import annotations

from src.crawler.base import fetch_json, filter_by_keyword
from src.models import Article

ZHIHU_API = "https://www.zhihu.com/api/v3/feed/topstory/hot-list-web"


def fetch_zhihu(keyword: str) -> list[Article]:
    payload = fetch_json(
        ZHIHU_API,
        params={"limit": "50", "desktop": "true"},
        referer="https://www.zhihu.com/hot",
    )
    articles: list[Article] = []

    for item in payload.get("data") or []:
        target = item.get("target") or {}
        title_area = target.get("title_area") or {}
        title = str(title_area.get("text") or "").strip()
        if not title:
            continue

        link = target.get("link") or {}
        url = str(link.get("url") or "")

        metrics = target.get("metrics_area") or {}
        hot_value = str(metrics.get("text") or "")

        excerpt = target.get("excerpt_area") or {}
        snippet = str(excerpt.get("text") or title)

        articles.append(
            Article(
                title=title,
                platform="知乎热榜",
                url=url,
                hot_value=hot_value,
                content_snippet=snippet,
            )
        )

    return filter_by_keyword(articles, keyword)
