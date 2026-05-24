"""CSV 导出单元测试。"""

import csv
from pathlib import Path

from src.models import Article
from src.storage.export import export_articles_csv


def test_export_articles_csv(tmp_path: Path):
    articles = [
        Article(
            title="测试标题",
            platform="知乎热榜",
            url="https://example.com",
            hot_value="100万",
            keyword="AI",
        )
    ]
    out = export_articles_csv(articles, keyword="AI", path=tmp_path / "out.csv")
    assert out.exists()
    with out.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["title"] == "测试标题"
    assert rows[0]["keyword"] == "AI"
