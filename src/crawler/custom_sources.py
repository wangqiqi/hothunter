"""用户自定义媒体源 — 读取 ~/.hothunter/sources.json。"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin

from src.config import PlatformMeta
from src.crawler.base import fetch_html, fetch_json, filter_by_keyword
from src.models import Article

SOURCES_PATH = Path.home() / ".hothunter" / "sources.json"
EXAMPLE_PATH = Path(__file__).resolve().parents[2] / "sources.example.json"

CrawlerFunc = Callable[[str], list[Article]]


def _get_path(data: dict[str, Any], path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not part:
            continue
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _make_json_fetcher(spec: dict[str, Any]) -> CrawlerFunc:
    url = str(spec["url"])
    method = str(spec.get("method", "GET")).upper()
    referer = spec.get("referer") or None
    items_path = str(spec.get("items_path", "data"))
    title_field = str(spec.get("title_field", "title"))
    url_field = str(spec.get("url_field", "url"))
    hot_field = spec.get("hot_field")
    platform_name = str(spec.get("name", "自定义源"))

    def fetch(keyword: str) -> list[Article]:
        if method == "POST":
            from src.crawler.base import fetch_json_post

            payload = spec.get("body") or {}
            data = fetch_json_post(url, payload, referer=referer)
        else:
            params = spec.get("params") or {}
            data = fetch_json(url, params={str(k): str(v) for k, v in params.items()}, referer=referer)
        items = _get_path(data, items_path) if items_path else data
        if not isinstance(items, list):
            return []
        articles: list[Article] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get(title_field) or "").strip()
            link = str(item.get(url_field) or "").strip()
            if not title:
                continue
            if link and not link.startswith("http"):
                link = urljoin(url, link)
            hot = str(item.get(hot_field) or "") if hot_field else ""
            articles.append(
                Article(
                    title=title,
                    platform=platform_name,
                    url=link or url,
                    hot_value=hot,
                    content_snippet=str(item.get("snippet") or item.get("desc") or title)[:80],
                )
            )
        return filter_by_keyword(articles, keyword)

    return fetch


def _make_rss_fetcher(spec: dict[str, Any]) -> CrawlerFunc:
    feed_url = str(spec["url"])
    platform_name = str(spec.get("name", "RSS"))

    def fetch(keyword: str) -> list[Article]:
        xml_text = fetch_html(feed_url)
        root = ET.fromstring(xml_text)
        articles: list[Article] = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            desc = (item.findtext("description") or title).strip()
            if not title:
                continue
            articles.append(
                Article(
                    title=title,
                    platform=platform_name,
                    url=link or feed_url,
                    content_snippet=desc[:80],
                )
            )
        return filter_by_keyword(articles[:50], keyword)

    return fetch


def load_custom_source_specs() -> list[dict[str, Any]]:
    if not SOURCES_PATH.is_file():
        return []
    try:
        data = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    sources = data.get("sources")
    if not isinstance(sources, list):
        return []
    return [s for s in sources if isinstance(s, dict) and s.get("enabled", True)]


def custom_platform_metas() -> list[PlatformMeta]:
    metas: list[PlatformMeta] = []
    for spec in load_custom_source_specs():
        sid = str(spec.get("id") or "").strip()
        name = str(spec.get("name") or "").strip()
        if not sid or not name:
            continue
        metas.append(
            {
                "id": sid,
                "name": name if name.endswith("（自定义）") else f"{name}（自定义）",
                "icon": str(spec.get("icon") or "源")[:1],
            }
        )
    return metas


def build_custom_crawlers() -> dict[str, tuple[str, CrawlerFunc]]:
    crawlers: dict[str, tuple[str, CrawlerFunc]] = {}
    for spec in load_custom_source_specs():
        sid = str(spec.get("id") or "").strip()
        name = str(spec.get("name") or sid).strip()
        stype = str(spec.get("type") or "json").lower()
        if not sid:
            continue
        if stype == "rss":
            func = _make_rss_fetcher(spec)
        elif stype == "json":
            func = _make_json_fetcher(spec)
        else:
            continue
        display = name if "自定义" in name else f"{name}（自定义）"
        crawlers[sid] = (display, func)
    return crawlers


def custom_search_only_ids() -> frozenset[str]:
    ids: set[str] = set()
    for spec in load_custom_source_specs():
        if spec.get("stream", True) is False:
            sid = str(spec.get("id") or "").strip()
            if sid:
                ids.add(sid)
    return frozenset(ids)
