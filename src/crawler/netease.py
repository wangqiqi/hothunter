"""网易新闻热点（JSONP 热文榜）。"""

from __future__ import annotations

import json
import re

from src.crawler.base import fetch_html, filter_by_keyword
from src.models import Article

NETEASE_HOT_URL = "https://3g.163.com/touch/reconstruct/article/list/BA8D4A3Rwangning/0-20.html"
_JSONP_RE = re.compile(r"artiList\((.*)\)\s*;?\s*$", re.DOTALL)


def fetch_netease(keyword: str) -> list[Article]:
    text = fetch_html(NETEASE_HOT_URL, referer="https://news.163.com")
    match = _JSONP_RE.search(text.strip())
    if not match:
        return []
    payload = json.loads(match.group(1))
    items = payload.get("BA8D4A3Rwangning") or []
    articles: list[Article] = []

    for item in items:
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        if not title or not url:
            continue
        articles.append(
            Article(
                title=title,
                platform="网易热点",
                url=url,
                hot_value=str(item.get("priority") or ""),
                publish_time=str(item.get("source") or ""),
                content_snippet=str(item.get("digest") or title)[:80],
            )
        )

    return filter_by_keyword(articles, keyword)
