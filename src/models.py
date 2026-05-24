"""数据模型。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Article:
    title: str
    platform: str
    url: str
    hot_value: str = ""
    publish_time: str = ""
    content_snippet: str = ""
    keyword: str = ""
    fetch_time: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> Article:
        return cls(
            id=row[0],
            title=row[1],
            platform=row[2],
            url=row[3],
            hot_value=row[4] or "",
            publish_time=row[5] or "",
            content_snippet=row[6] or "",
            keyword=row[7] or "",
            fetch_time=row[8] or "",
        )
