"""爬虫公共工具：请求、延时、关键词过滤。"""

from __future__ import annotations

import re
import time
from typing import Callable

import requests
from fake_useragent import UserAgent

from src.config import REQUEST_DELAY_SEC
from src.models import Article

_ua = UserAgent()


def get_headers() -> dict[str, str]:
    return {
        "User-Agent": _ua.random,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }


def fetch_html(url: str, *, params: dict[str, str] | None = None) -> str:
    time.sleep(REQUEST_DELAY_SEC)
    response = requests.get(url, headers=get_headers(), params=params, timeout=15)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def fetch_json(url: str, *, params: dict[str, str] | None = None) -> dict:
    time.sleep(REQUEST_DELAY_SEC)
    response = requests.get(url, headers=get_headers(), params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def keyword_match(text: str, keyword: str) -> bool:
    if not keyword.strip():
        return True
    return keyword.lower() in text.lower()


def filter_by_keyword(articles: list[Article], keyword: str) -> list[Article]:
    if not keyword.strip():
        return articles
    return [a for a in articles if keyword_match(f"{a.title} {a.content_snippet}", keyword)]


def safe_fetch(name: str, func: Callable[[str], list[Article]], keyword: str) -> tuple[str, list[Article], str | None]:
    try:
        return name, func(keyword), None
    except Exception as exc:  # noqa: BLE001 — 单平台失败不影响其他平台
        return name, [], str(exc)


def format_hot_count(value: int | float | str | None) -> str:
    if value is None or value == "":
        return ""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if num >= 100_000_000:
        return f"{num / 100_000_000:.1f}亿"
    if num >= 10_000:
        return f"{num / 10_000:.1f}万"
    return str(int(num))


def extract_chinese_snippet(text: str, limit: int = 80) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned[:limit]
