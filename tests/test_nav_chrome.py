"""底部导航隐现逻辑。"""

from src.ui import nav_chrome as chrome


def test_scroll_content_inset() -> None:
    assert chrome.scroll_content_inset(nav_visible=True) > chrome.scroll_content_inset(nav_visible=False)


def test_decide_show_at_top() -> None:
    assert chrome.decide_nav_visible_on_scroll(
        pixels=0,
        max_scroll_extent=1000,
        scroll_delta=20,
        direction="forward",
        current=False,
    )


def test_decide_hide_on_scroll_down() -> None:
    assert not chrome.decide_nav_visible_on_scroll(
        pixels=200,
        max_scroll_extent=1000,
        scroll_delta=12,
        direction="forward",
        current=True,
    )


def test_decide_show_on_scroll_up() -> None:
    assert chrome.decide_nav_visible_on_scroll(
        pixels=400,
        max_scroll_extent=1000,
        scroll_delta=-12,
        direction="reverse",
        current=False,
    )


def test_decide_show_near_bottom() -> None:
    assert chrome.decide_nav_visible_on_scroll(
        pixels=950,
        max_scroll_extent=1000,
        scroll_delta=15,
        direction="forward",
        current=False,
    )


def test_is_mobile_platform() -> None:
    assert chrome.is_mobile_platform("android")
    assert not chrome.is_mobile_platform("linux")
