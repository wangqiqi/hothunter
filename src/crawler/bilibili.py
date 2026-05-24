"""B站热门爬虫。"""

from __future__ import annotations

from src.crawler.base import fetch_json, filter_by_keyword, format_hot_count
from src.models import Article

BILIBILI_URL = "https://api.bilibili.com/x/web-interface/popular"


def fetch_bilibili(keyword: str) -> list[Article]:
    payload = fetch_json(BILIBILI_URL, params={"ps": "20", "pn": "1"})
    data = payload.get("data") or {}
    items = data.get("list") or []
    articles: list[Article] = []

    for item in items:
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        bvid = item.get("bvid") or ""
        aid = item.get("aid")
        url = f"https://www.bilibili.com/video/{bvid}" if bvid else f"https://www.bilibili.com/video/av{aid}"
        stat = item.get("stat") or {}
        play = stat.get("view") or stat.get("play") or 0
        desc = str(item.get("desc") or title)
        rcmd = item.get("rcmd_reason") or {}
        reason = rcmd.get("content") if isinstance(rcmd, dict) else ""
        publish_time = str(reason) if reason else ""

        articles.append(
            Article(
                title=title,
                platform="B站热门",
                url=url,
                hot_value=f"{format_hot_count(play)}播放",
                publish_time=publish_time,
                content_snippet=desc,
            )
        )

    return filter_by_keyword(articles, keyword)
