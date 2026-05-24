"""热度数值解析与排序。"""

from __future__ import annotations

import re

from src.models import Article

_HOT_PATTERN = re.compile(
    r"([\d,.]+)\s*(亿|万)?",
)


def parse_hot_value(text: str) -> float:
    """将热度字符串转为可比较的数值。"""
    if not text:
        return 0.0

    cleaned = text.strip().replace(",", "")
    # 优先匹配带单位的片段
    for match in _HOT_PATTERN.finditer(cleaned):
        num_str, unit = match.group(1), match.group(2) or ""
        try:
            num = float(num_str)
        except ValueError:
            continue
        if unit == "亿":
            return num * 100_000_000
        if unit == "万":
            return num * 10_000
        if num > 0:
            return num

    return 0.0


def sort_by_hot_value(articles: list[Article]) -> list[Article]:
    return sorted(articles, key=lambda a: parse_hot_value(a.hot_value), reverse=True)
