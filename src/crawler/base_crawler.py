"""Base crawler module for TrendRadar.

Provides an abstract base class for all platform-specific crawlers,
defining the common interface and shared utilities.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TrendItem:
    """Represents a single trending topic or item."""

    title: str
    rank: int
    platform: str
    url: Optional[str] = None
    heat: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    crawled_at: datetime = field(default_factory=datetime.utcnow)
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize the trend item to a dictionary."""
        return {
            "title": self.title,
            "rank": self.rank,
            "platform": self.platform,
            "url": self.url,
            "heat": self.heat,
            "category": self.category,
            "description": self.description,
            "crawled_at": self.crawled_at.isoformat(),
            "extra": self.extra,
        }


class BaseCrawler(ABC):
    """Abstract base class for all TrendRadar crawlers.

    Subclasses must implement the `fetch` method to retrieve trending
    data from their respective platforms.
    """

    # Default request timeout in seconds
    DEFAULT_TIMEOUT: int = 15
    # Default delay between retries in seconds
    DEFAULT_RETRY_DELAY: int = 3
    # Maximum number of retry attempts
    MAX_RETRIES: int = 3

    def __init__(self, platform: str, timeout: int = DEFAULT_TIMEOUT):
        self.platform = platform
        self.timeout = timeout
        self._session = None
        logger.info("Initialized crawler for platform: %s", self.platform)

    @abstractmethod
    def fetch(self) -> list[TrendItem]:
        """Fetch trending items from the platform.

        Returns:
            A list of TrendItem instances representing current trends.

        Raises:
            CrawlerError: If fetching fails after all retries.
        """
        ...

    def fetch_with_retry(self) -> list[TrendItem]:
        """Attempt to fetch trends, retrying on transient failures.

        Returns:
            A list of TrendItem instances.
        """
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.debug(
                    "[%s] Fetch attempt %d/%d",
                    self.platform,
                    attempt,
                    self.MAX_RETRIES,
                )
                items = self.fetch()
                logger.info(
                    "[%s] Successfully fetched %d items on attempt %d.",
                    self.platform,
                    len(items),
                    attempt,
                )
                return items
            except Exception as exc:  # pylint: disable=broad-except
                last_exception = exc
                logger.warning(
                    "[%s] Attempt %d failed: %s",
                    self.platform,
                    attempt,
                    exc,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.DEFAULT_RETRY_DELAY)

        raise CrawlerError(
            f"[{self.platform}] All {self.MAX_RETRIES} fetch attempts failed."
        ) from last_exception

    @property
    def name(self) -> str:
        """Human-readable crawler name."""
        return self.platform.capitalize()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} platform={self.platform!r}>"


class CrawlerError(Exception):
    """Raised when a crawler fails to retrieve data."""
