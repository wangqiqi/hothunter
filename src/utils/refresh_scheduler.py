"""定时刷新：整点调度与时间计算。"""

from __future__ import annotations

from datetime import datetime, timedelta


def seconds_until_next_hour(now: datetime | None = None) -> float:
    """距离下一个整点的秒数。"""
    current = now or datetime.now()
    next_hour = current.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return max(0.0, (next_hour - current).total_seconds())


def next_hour_time(now: datetime | None = None) -> datetime:
    current = now or datetime.now()
    return current.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def format_next_hour(now: datetime | None = None) -> str:
    return next_hour_time(now).strftime("%H:%M")
