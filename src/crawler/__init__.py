"""爬虫模块。"""

from src.crawler.registry import CRAWLERS, fetch_platform

__all__ = ["CRAWLERS", "fetch_platform"]
