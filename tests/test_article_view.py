"""article_view 排序与筛选测试。"""

from src.models import Article
from src.utils.article_view import apply_view, filter_articles, sort_articles


def _article(title: str, platform: str = "知乎热榜", hot: str = "", fetch_time: str = "") -> Article:
    return Article(title=title, platform=platform, url="http://x", hot_value=hot, fetch_time=fetch_time)


def test_filter_by_title_keyword():
    articles = [_article("AI 大模型"), _article("新能源政策")]
    out = filter_articles(articles, title_keyword="AI")
    assert len(out) == 1
    assert out[0].title == "AI 大模型"


def test_filter_by_platform():
    articles = [_article("a", "知乎热榜"), _article("b", "微博热搜")]
    out = filter_articles(articles, platform="微博热搜")
    assert len(out) == 1
    assert out[0].title == "b"


def test_sort_hot_asc():
    articles = [_article("a", hot="100万"), _article("b", hot="500万")]
    out = sort_articles(articles, "hot_asc")
    assert [a.title for a in out] == ["a", "b"]


def test_apply_view_combined():
    articles = [
        _article("AI 新闻", "知乎热榜", "500万"),
        _article("AI 视频", "B站热门", "100万"),
        _article("体育", "微博热搜", "200万"),
    ]
    out = apply_view(articles, sort_key="hot_desc", title_keyword="AI")
    assert len(out) == 2
    assert out[0].title == "AI 新闻"
