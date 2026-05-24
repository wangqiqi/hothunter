"""抓取模式单元测试。"""

from src.modes import (
    FetchMode,
    STREAM_STORAGE_KEY,
    analysis_keyword,
    crawl_keyword,
    filter_platforms,
    storage_key,
)


def test_stream_mode_no_keyword_filter():
    assert crawl_keyword(FetchMode.STREAM, "AI") == ""
    assert storage_key(FetchMode.STREAM, "AI") == STREAM_STORAGE_KEY
    assert analysis_keyword(FetchMode.STREAM, "AI") == ""


def test_custom_mode_uses_keyword():
    assert crawl_keyword(FetchMode.CUSTOM, "新能源") == "新能源"
    assert storage_key(FetchMode.CUSTOM, "新能源") == "新能源"


def test_stream_mode_skips_baidu():
    usable, skipped = filter_platforms(FetchMode.STREAM, ["zhihu", "baidu", "weibo"])
    assert usable == ["zhihu", "weibo"]
    assert skipped == ["baidu"]


def test_custom_mode_keeps_all_platforms():
    usable, skipped = filter_platforms(FetchMode.CUSTOM, ["zhihu", "baidu"])
    assert usable == ["zhihu", "baidu"]
    assert skipped == []
