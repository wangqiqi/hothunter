"""从外链 HTML 提取可读正文（应用内摘要阅读）。"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from src.crawler.base import fetch_html

MAX_SUMMARY_CHARS = 12_000
_MIN_PARAGRAPH_LEN = 24


def extract_readable_text(html: str, *, max_chars: int = MAX_SUMMARY_CHARS) -> str:
    """从 HTML 抽取段落正文，过滤脚本与导航噪声。"""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer", "header", "aside"]):
        tag.decompose()

    chunks: list[str] = []
    for node in soup.select("article, main, [role='main']"):
        text = _normalize_block(node.get_text("\n", strip=True))
        if len(text) >= _MIN_PARAGRAPH_LEN:
            chunks.append(text)

    if not chunks:
        paragraphs = [
            p.get_text(" ", strip=True)
            for p in soup.find_all("p")
            if len(p.get_text(strip=True)) >= _MIN_PARAGRAPH_LEN
        ]
        chunks.append("\n\n".join(paragraphs))

    if not chunks:
        body = soup.find("body")
        if body is not None:
            fallback = _normalize_block(body.get_text("\n", strip=True))
            if fallback:
                chunks.append(fallback)

    merged = "\n\n".join(chunks).strip()
    if len(merged) > max_chars:
        merged = merged[: max_chars - 1].rstrip() + "…"
    return merged


def _normalize_block(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_article_body(url: str) -> tuple[str, str | None]:
    """拉取 URL 并提取正文。返回 (正文, 错误信息)。"""
    try:
        html = fetch_html(url)
        body = extract_readable_text(html)
        if not body.strip():
            return "", "未能从页面提取正文，可尝试「原页」或浏览器打开"
        return body, None
    except Exception as exc:  # noqa: BLE001
        return "", str(exc)
