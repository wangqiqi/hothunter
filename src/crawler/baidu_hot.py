"""百度热搜榜（top.baidu.com）。"""

from __future__ import annotations

from urllib.parse import quote

from src.crawler.base import fetch_json, filter_by_keyword, format_hot_count
from src.models import Article

BAIDU_HOT_API = "https://top.baidu.com/api/board"


def fetch_baidu_hot(keyword: str) -> list[Article]:
    payload = fetch_json(
        BAIDU_HOT_API,
        params={"platform": "wise", "tab": "realtime"},
        referer="https://top.baidu.com/board",
    )
    articles: list[Article] = []

    for card in (payload.get("data") or {}).get("cards") or []:
        if card.get("component") != "tabTextList":
            continue
        content_blocks = card.get("content") or []
        if not content_blocks:
            continue
        items = (content_blocks[0].get("content") or []) if content_blocks else []
        for item in items:
            word = str(item.get("word") or item.get("query") or "").strip()
            if not word:
                continue
            hot = item.get("hotScore") or item.get("hot_score") or item.get("index") or ""
            desc = str(item.get("desc") or "").strip()
            url = f"https://www.baidu.com/s?wd={quote(word)}"
            articles.append(
                Article(
                    title=word,
                    platform="百度热搜",
                    url=url,
                    hot_value=format_hot_count(hot) if hot != "" else "",
                    content_snippet=desc or word,
                )
            )
        break

    return filter_by_keyword(articles, keyword)
