"""CSV 导出。"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from src.models import Article

EXPORT_DIR = Path.home() / ".hothunter" / "exports"

CSV_FIELDS = [
    "title",
    "platform",
    "url",
    "hot_value",
    "publish_time",
    "content_snippet",
    "keyword",
    "fetch_time",
]


def export_articles_csv(articles: list[Article], keyword: str = "", path: Path | str | None = None) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(path) if path else EXPORT_DIR / f"hothunter_{datetime.now():%Y%m%d_%H%M%S}.csv"

    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for article in articles:
            row = article.to_dict()
            row["keyword"] = keyword or article.keyword
            writer.writerow({k: row.get(k, "") for k in CSV_FIELDS})

    return out_path
