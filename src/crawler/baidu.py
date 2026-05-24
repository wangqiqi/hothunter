"""百度新闻搜索爬虫。"""

from __future__ import annotations

from bs4 import BeautifulSoup

from src.crawler.base import fetch_html, filter_by_keyword
from src.models import Article

BAIDU_NEWS_URL = "https://www.baidu.com/s"


def fetch_baidu(keyword: str) -> list[Article]:
    search_word = keyword.strip() or "热点"
    html = fetch_html(
        BAIDU_NEWS_URL,
        params={"tn": "news", "word": search_word, "rn": "20", "cl": "2"},
        referer="https://www.baidu.com",
    )
    soup = BeautifulSoup(html, "lxml")
    articles: list[Article] = []

    for item in soup.select(".result, .result-op, .c-container"):
        title_el = item.select_one("h3 a, a.news-title, .c-title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        url = title_el.get("href") or ""
        if not title or not url:
            continue

        source_el = item.select_one(".c-color-gray, .news-source, .c-author")
        publish_time = source_el.get_text(strip=True) if source_el else ""

        snippet_el = item.select_one(".c-summary, .c-span-last, .news-desc")
        snippet = snippet_el.get_text(strip=True) if snippet_el else title

        articles.append(
            Article(
                title=title,
                platform="百度新闻",
                url=url,
                hot_value="",
                publish_time=publish_time,
                content_snippet=snippet,
            )
        )

    return filter_by_keyword(articles, search_word if keyword.strip() else "")
