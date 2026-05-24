"""整点刷新时间计算单元测试。"""

from datetime import datetime

from src.utils.refresh_scheduler import format_next_hour, next_hour_time, seconds_until_next_hour


def test_seconds_until_next_hour():
    now = datetime(2026, 5, 24, 14, 30, 45)
    assert seconds_until_next_hour(now) == 29 * 60 + 15


def test_next_hour_at_boundary():
    now = datetime(2026, 5, 24, 15, 0, 0)
    assert seconds_until_next_hour(now) == 3600
    assert format_next_hour(now) == "16:00"
    assert next_hour_time(now).hour == 16
