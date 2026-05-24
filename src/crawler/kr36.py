"""36氪热榜爬虫。"""

from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from src.crawler.base import fetch_html, filter_by_keyword
from src.models import Article

KR36_URL = "https://36kr.com/hot-list/catalog"


def fetch_36kr(keyword: str) -> list[Article]:
    html = fetch_html(KR36_URL)
    soup = BeautifulSoup(html, "lxml")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return []

    data = json.loads(script.string)
    articles: list[Article] = []
    hot_list = _extract_hot_items(data)

    for idx, item in enumerate(hot_list, start=1):
        title = str(item.get("title") or item.get("widgetTitle") or "").strip()
        if not title:
            continue
        url = str(item.get("route") or item.get("itemUrl") or item.get("url") or "")
        if url and not url.startswith("http"):
            url = f"https://36kr.com{url}"
        hot_value = str(item.get("hotValue") or item.get("readCount") or idx)
        snippet = str(item.get("summary") or item.get("description") or title)
        articles.append(
            Article(
                title=title,
                platform="36氪",
                url=url,
                hot_value=hot_value,
                content_snippet=snippet,
            )
        )

    return filter_by_keyword(articles, keyword)


def _extract_hot_items(data: dict) -> list[dict]:
    """从 __NEXT_DATA__ 中递归查找热榜条目。"""
    found: list[dict] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if "title" in node and ("route" in node or "itemUrl" in node or "url" in node):
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    # 去重（按 title）
    seen: set[str] = set()
    unique: list[dict] = []
    for item in found:
        title = str(item.get("title", ""))
        if title and title not in seen:
            seen.add(title)
            unique.append(item)
    return unique[:30]
