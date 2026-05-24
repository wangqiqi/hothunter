"""爬虫解析冒烟（不发起真实网络）。"""

from src.crawler.baidu_hot import fetch_baidu_hot
from src.crawler.douyin import fetch_douyin
from src.crawler.netease import fetch_netease
from src.crawler.tencent import fetch_tencent


def test_baidu_hot_parse(monkeypatch) -> None:
    sample = {
        "data": {
            "cards": [
                {
                    "component": "tabTextList",
                    "content": [{"content": [{"word": "测试词条", "hotScore": "12345", "desc": "说明"}]}],
                }
            ]
        }
    }

    monkeypatch.setattr("src.crawler.baidu_hot.fetch_json", lambda *a, **k: sample)
    items = fetch_baidu_hot("")
    assert len(items) == 1
    assert items[0].title == "测试词条"


def test_douyin_parse(monkeypatch) -> None:
    sample = {"data": {"word_list": [{"word": "抖音词", "hot_value": 999, "position": 1}]}}
    monkeypatch.setattr("src.crawler.douyin.fetch_json", lambda *a, **k: sample)
    items = fetch_douyin("")
    assert items[0].platform == "抖音热榜"


def test_tencent_parse(monkeypatch) -> None:
    sample = {
        "idlist": [
            {
                "newslist": [
                    {"id": "TIP", "title": "腾讯新闻用户最关注的热点"},
                    {"id": "20260101A01", "title": "真实新闻", "url": "https://view.inews.qq.com/a/20260101A01"},
                ]
            }
        ]
    }
    monkeypatch.setattr("src.crawler.tencent.fetch_json", lambda *a, **k: sample)
    items = fetch_tencent("")
    assert len(items) == 1
    assert items[0].title == "真实新闻"


def test_netease_parse(monkeypatch) -> None:
    body = 'artiList({"BA8D4A3Rwangning":[{"title":"网易标题","url":"https://m.163.com/x.html","priority":9}]});'
    monkeypatch.setattr("src.crawler.netease.fetch_html", lambda *a, **k: body)
    items = fetch_netease("")
    assert items[0].title == "网易标题"
