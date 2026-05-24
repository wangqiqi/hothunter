"""小红书 — 无稳定公开热榜 API，定制模式提供搜索入口。"""

from __future__ import annotations

from urllib.parse import quote

from src.models import Article


def fetch_xiaohongshu(keyword: str) -> list[Article]:
    """实时流返回空；定制模式生成可打开的搜索聚合项。"""
    kw = keyword.strip()
    if not kw:
        return []
    url = f"https://www.xiaohongshu.com/search_result?keyword={quote(kw)}"
    return [
        Article(
            title=f"小红书搜索：{kw}",
            platform="小红书",
            url=url,
            content_snippet="小红书无公开热榜接口，点击跳转站内搜索（需在浏览器/APP 中打开）",
        )
    ]
