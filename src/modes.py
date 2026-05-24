"""抓取模式：实时流热点 vs 定制热点。"""

from __future__ import annotations

from enum import StrEnum

from src.config import DEFAULT_KEYWORD, SEARCH_ONLY_PLATFORMS


class FetchMode(StrEnum):
    """实时流：各平台原生热榜；定制：按关键词过滤/搜索。"""

    STREAM = "stream"
    CUSTOM = "custom"


# 实时流模式在数据库中的存储标识
STREAM_STORAGE_KEY = "__stream__"

MODE_LABELS: dict[FetchMode, str] = {
    FetchMode.STREAM: "实时流热点",
    FetchMode.CUSTOM: "定制热点",
}


def crawl_keyword(mode: FetchMode, user_keyword: str) -> str:
    """传给爬虫的关键词：实时模式不过滤。"""
    if mode == FetchMode.STREAM:
        return ""
    return user_keyword.strip() or DEFAULT_KEYWORD


def storage_key(mode: FetchMode, user_keyword: str) -> str:
    """写入 SQLite 的 keyword 字段。"""
    if mode == FetchMode.STREAM:
        return STREAM_STORAGE_KEY
    return user_keyword.strip() or DEFAULT_KEYWORD


def analysis_keyword(mode: FetchMode, user_keyword: str) -> str:
    """词频分析用的排除词；实时模式不排除特定主题。"""
    if mode == FetchMode.STREAM:
        return ""
    return user_keyword.strip() or DEFAULT_KEYWORD


def filter_platforms(mode: FetchMode, platform_ids: list[str]) -> tuple[list[str], list[str]]:
    """
    返回 (可用平台, 被跳过的平台名)。
    百度新闻为搜索型，仅适用于定制模式。
    """
    if mode == FetchMode.CUSTOM:
        return platform_ids, []

    skipped: list[str] = []
    usable: list[str] = []
    for pid in platform_ids:
        if pid in SEARCH_ONLY_PLATFORMS:
            skipped.append(pid)
        else:
            usable.append(pid)
    return usable, skipped
