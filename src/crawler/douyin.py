"""抖音热榜。"""

from __future__ import annotations

from urllib.parse import quote

from src.crawler.base import fetch_json, filter_by_keyword, format_hot_count
from src.models import Article

DOUYIN_HOT_API = "https://www.douyin.com/aweme/v1/web/hot/search/list/"


def fetch_douyin(keyword: str) -> list[Article]:
    payload = fetch_json(DOUYIN_HOT_API, referer="https://www.douyin.com")
    word_list = (payload.get("data") or {}).get("word_list") or []
    articles: list[Article] = []

    for item in word_list:
        word = str(item.get("word") or "").strip()
        if not word:
            continue
        hot = item.get("hot_value") or item.get("hot_value_raw") or ""
        rank = item.get("position") or item.get("rank") or ""
        url = f"https://www.douyin.com/search/{quote(word)}"
        articles.append(
            Article(
                title=word,
                platform="抖音热榜",
                url=url,
                hot_value=format_hot_count(hot),
                content_snippet=f"排名 {rank}" if rank else word,
            )
        )

    return filter_by_keyword(articles, keyword)
