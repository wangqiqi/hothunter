"""36氪热榜爬虫（Gateway API）。"""

from __future__ import annotations

from src.crawler.base import fetch_json_post, filter_by_keyword, format_hot_count
from src.models import Article

KR36_API = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"


def fetch_36kr(keyword: str) -> list[Article]:
    payload = fetch_json_post(
        KR36_API,
        {"partner_id": "wap", "param": {"siteId": 1, "platformId": 2}},
        referer="https://36kr.com/",
    )
    hot_list = (payload.get("data") or {}).get("hotRankList") or []
    articles: list[Article] = []

    for idx, item in enumerate(hot_list, start=1):
        material = item.get("templateMaterial") or {}
        title = str(material.get("widgetTitle") or "").strip()
        if not title:
            continue

        item_id = item.get("itemId") or material.get("itemId")
        route = str(item.get("route") or "")
        if route.startswith("http"):
            url = route
        elif route:
            url = f"https://36kr.com/{route}"
        elif item_id:
            url = f"https://36kr.com/p/{item_id}"
        else:
            url = ""

        read_count = material.get("statRead") or material.get("statFormat") or idx
        publish_time = str(material.get("publishTime") or item.get("publishTime") or "")
        author = str(material.get("authorName") or "")

        articles.append(
            Article(
                title=title,
                platform="36氪",
                url=url,
                hot_value=format_hot_count(read_count),
                publish_time=publish_time,
                content_snippet=author or title,
            )
        )

    return filter_by_keyword(articles, keyword)
