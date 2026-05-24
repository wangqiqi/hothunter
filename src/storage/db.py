"""SQLite 文章存储。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.config import HISTORY_LIMIT
from src.models import Article

DEFAULT_DB_DIR = Path.home() / ".hothunter"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "articles.db"


class ArticleStore:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    url TEXT NOT NULL,
                    hot_value TEXT,
                    publish_time TEXT,
                    content_snippet TEXT,
                    keyword TEXT,
                    fetch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_keyword_fetch_time ON articles(keyword, fetch_time DESC)"
            )

    def save_articles(self, articles: list[Article], keyword: str) -> int:
        if not articles:
            return 0
        rows = [
            (
                a.title,
                a.platform,
                a.url,
                a.hot_value,
                a.publish_time,
                a.content_snippet,
                keyword,
                a.fetch_time,
            )
            for a in articles
        ]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO articles
                (title, platform, url, hot_value, publish_time, content_snippet, keyword, fetch_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def get_history(self, keyword: str | None = None, limit: int = HISTORY_LIMIT) -> list[Article]:
        query = """
            SELECT id, title, platform, url, hot_value, publish_time,
                   content_snippet, keyword, fetch_time
            FROM articles
        """
        params: list[str | int] = []
        if keyword:
            query += " WHERE keyword = ?"
            params.append(keyword)
        query += " ORDER BY fetch_time DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Article.from_row(tuple(row)) for row in rows]

    def get_titles_by_keyword(self, keyword: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT title FROM articles WHERE keyword = ? ORDER BY fetch_time DESC",
                (keyword,),
            ).fetchall()
        return [str(row[0]) for row in rows if row[0]]
