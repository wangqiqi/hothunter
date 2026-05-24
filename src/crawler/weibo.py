"""微博热搜爬虫。"""

from __future__ import annotations

from urllib.parse import quote

from src.crawler.base import fetch_json, filter_by_keyword, format_hot_count
from src.models import Article

WEIBO_API = "https://weibo.com/ajax/side/hotSearch"


def fetch_weibo(keyword: str) -> list[Article]:
    payload = fetch_json(WEIBO_API, referer="https://weibo.com")
    realtime = (payload.get("data") or {}).get("realtime") or []
    articles: list[Article] = []

    for item in realtime:
        word = str(item.get("word") or item.get("note") or "").strip()
        if not word or word.startswith("#"):
            continue

        num = item.get("num") or item.get("raw_hot") or 0
        label = str(item.get("label_name") or item.get("icon_desc") or "")
        rank = item.get("rank") or item.get("realpos") or ""
        url = f"https://s.weibo.com/weibo?q={quote(word)}&Refer=top"

        articles.append(
            Article(
                title=word,
                platform="微博热搜",
                url=url,
                hot_value=format_hot_count(num),
                publish_time=label,
                content_snippet=f"排名 {rank}" if rank else word,
            )
        )

    return filter_by_keyword(articles, keyword)
