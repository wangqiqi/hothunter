"""知乎热榜爬虫。"""

from __future__ import annotations

from bs4 import BeautifulSoup

from src.crawler.base import fetch_html, filter_by_keyword, format_hot_count
from src.models import Article

ZHIHU_URL = "https://www.zhihu.com/hot"


def fetch_zhihu(keyword: str) -> list[Article]:
    html = fetch_html(ZHIHU_URL)
    soup = BeautifulSoup(html, "lxml")
    articles: list[Article] = []

    for item in soup.select(".HotList-item, .HotItem"):
        title_el = item.select_one(".HotItem-title, h2")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        anchor = item.select_one("a[href]")
        url = ""
        if anchor and anchor.get("href"):
            href = anchor["href"]
            url = href if href.startswith("http") else f"https://www.zhihu.com{href}"

        hot_el = item.select_one(".HotItem-metrics, .HotList-itemMetrics")
        hot_value = hot_el.get_text(strip=True) if hot_el else ""

        excerpt_el = item.select_one(".HotItem-excerpt")
        snippet = excerpt_el.get_text(strip=True) if excerpt_el else title

        articles.append(
            Article(
                title=title,
                platform="知乎热榜",
                url=url,
                hot_value=hot_value or format_hot_count(len(articles) + 1),
                content_snippet=snippet,
            )
        )

    return filter_by_keyword(articles, keyword)
