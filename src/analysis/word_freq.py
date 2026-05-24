"""基于正则的中文词频统计。"""

from __future__ import annotations

import re
from collections import Counter

from src.config import STOPWORDS, WORD_FREQ_TOP_N

CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fa5]{2,}")


def extract_words(text: str, *, exclude: set[str] | None = None) -> list[str]:
    exclude = exclude or set()
    cleaned = text
    for sw in sorted(STOPWORDS, key=len, reverse=True):
        cleaned = cleaned.replace(sw, " ")
    words = CHINESE_PATTERN.findall(cleaned)
    return [w for w in words if w not in STOPWORDS and w not in exclude and len(w) >= 2]


def analyze_titles(titles: list[str], keyword: str = "", top_n: int = WORD_FREQ_TOP_N) -> list[tuple[str, int]]:
    exclude = {keyword.strip()} if keyword.strip() else set()
    # 也排除关键词中的每个连续中文片段
    for part in CHINESE_PATTERN.findall(keyword):
        exclude.add(part)

    counter: Counter[str] = Counter()
    for title in titles:
        counter.update(extract_words(title, exclude=exclude))

    return counter.most_common(top_n)
