"""今日头条热榜爬虫。"""

from __future__ import annotations

from src.crawler.base import fetch_json, filter_by_keyword, format_hot_count
from src.models import Article

TOUTIAO_API = "https://www.toutiao.com/hot-event/hot-board/"


def fetch_toutiao(keyword: str) -> list[Article]:
    payload = fetch_json(
        TOUTIAO_API,
        params={"origin": "toutiao_pc"},
        referer="https://www.toutiao.com",
    )
    articles: list[Article] = []

    for item in payload.get("data") or []:
        title = str(item.get("Title") or "").strip()
        if not title:
            continue

        url = str(item.get("Url") or item.get("Schema") or "")
        hot_value = format_hot_count(item.get("HotValue"))
        label = str(item.get("LabelDesc") or item.get("Label") or "")

        articles.append(
            Article(
                title=title,
                platform="今日头条",
                url=url,
                hot_value=hot_value,
                publish_time=label,
                content_snippet=title,
            )
        )

    return filter_by_keyword(articles, keyword)
