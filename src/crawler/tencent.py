"""腾讯新闻热榜。"""

from __future__ import annotations

from src.crawler.base import fetch_json, filter_by_keyword
from src.models import Article

TENCENT_HOT_API = "https://r.inews.qq.com/gw/event/hot_ranking_list"


def fetch_tencent(keyword: str) -> list[Article]:
    payload = fetch_json(
        TENCENT_HOT_API,
        params={"page_size": "50"},
        referer="https://news.qq.com",
    )
    articles: list[Article] = []

    for block in payload.get("idlist") or []:
        for item in block.get("newslist") or []:
            title = str(item.get("title") or "").strip()
            if not title or title.startswith("腾讯新闻用户"):
                continue
            news_id = str(item.get("id") or "")
            url = str(item.get("url") or "").strip()
            if not url and news_id and not news_id.startswith("TIP"):
                url = f"https://view.inews.qq.com/a/{news_id}"
            if not url:
                continue
            articles.append(
                Article(
                    title=title,
                    platform="腾讯新闻",
                    url=url,
                    hot_value=str(item.get("readCount") or item.get("hotEvent") or ""),
                    publish_time=str(item.get("pubTime") or item.get("publish_time") or ""),
                    content_snippet=str(item.get("abstract") or title)[:80],
                )
            )

    return filter_by_keyword(articles, keyword)
