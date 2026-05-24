"""百度贴吧热议榜。"""

from __future__ import annotations

from bs4 import BeautifulSoup

from src.crawler.base import fetch_html, filter_by_keyword
from src.models import Article

TIEBA_HOT_URL = "https://tieba.baidu.com/hottopic/browse/topicList"


def fetch_tieba(keyword: str) -> list[Article]:
    html = fetch_html(TIEBA_HOT_URL, params={"res_type": "1"}, referer="https://tieba.baidu.com")
    soup = BeautifulSoup(html, "lxml")
    articles: list[Article] = []
    seen: set[str] = set()

    for link in soup.select('a[href*="hottopic/browse/hottopic"]'):
        title = link.get_text(strip=True)
        href = link.get("href") or ""
        if not title or len(title) < 2 or title in seen:
            continue
        seen.add(title)
        if href.startswith("/"):
            href = f"https://tieba.baidu.com{href}"
        articles.append(
            Article(
                title=title,
                platform="贴吧热议",
                url=href,
                content_snippet=title,
            )
        )

    if not articles:
        for el in soup.select(".topic-text, .topic-name, .list-title"):
            title = el.get_text(strip=True)
            if title and title not in seen and len(title) >= 2:
                seen.add(title)
                articles.append(
                    Article(
                        title=title,
                        platform="贴吧热议",
                        url="https://tieba.baidu.com/hottopic/browse/topicList",
                        content_snippet=title,
                    )
                )

    return filter_by_keyword(articles[:50], keyword)
