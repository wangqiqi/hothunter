"""热度解析单元测试。"""

from src.models import Article
from src.utils.hot_sort import parse_hot_value, sort_by_hot_value


def test_parse_hot_value_units():
    assert parse_hot_value("965 万热度") == 9_650_000
    assert parse_hot_value("136.5万播放") == 1_365_000
    assert parse_hot_value("1.2亿") == 120_000_000
    assert parse_hot_value("1522974") == 1_522_974


def test_sort_by_hot_value_desc():
    articles = [
        Article(title="a", platform="x", url="", hot_value="100万"),
        Article(title="b", platform="x", url="", hot_value="200万"),
        Article(title="c", platform="x", url="", hot_value="50万"),
    ]
    sorted_articles = sort_by_hot_value(articles)
    assert [a.title for a in sorted_articles] == ["b", "a", "c"]
