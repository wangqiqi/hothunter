"""自定义媒体源配置。"""

import json

from src.crawler.custom_sources import build_custom_crawlers, custom_platform_metas
from src.crawler.registry import all_crawlers


def test_custom_json_source(tmp_path, monkeypatch) -> None:
    path = tmp_path / "sources.json"
    path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "id": "test_hot",
                        "name": "测试榜",
                        "icon": "测",
                        "enabled": True,
                        "type": "json",
                        "url": "https://example.com/hot",
                        "items_path": "items",
                        "title_field": "title",
                        "url_field": "url",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("src.crawler.custom_sources.SOURCES_PATH", path)

    metas = custom_platform_metas()
    assert len(metas) == 1
    assert metas[0]["id"] == "test_hot"

    crawlers = build_custom_crawlers()
    assert "test_hot" in crawlers
    assert "test_hot" in all_crawlers()
