"""ORBIT Distributed URL Frontier.

Manages the distributed URL frontier with deduplication, prioritization,
scheduling, and per-host politeness constraints.
"""

import logging
import heapq
import time
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone, timedelta
from uuid import UUID
from collections import defaultdict

from core.models import URLCandidate, Source, SourceType, SourceStatus, utc_now

logger = logging.getLogger("orbit.discovery.url_frontier")


class HostPoliteness:
    """Per-host crawl delay and concurrency tracking."""

    def __init__(self, host: str, delay_seconds: float = 1.0, max_concurrent: int = 2):
        self.host = host
        self.delay_seconds = delay_seconds
        self.max_concurrent = max_concurrent
        self.last_crawl_time: Optional[datetime] = None
        self.current_concurrent = 0
        self.total_crawled = 0
        self.total_failures = 0
        self.consecutive_failures = 0
        self.backoff_until: Optional[datetime] = None

    def can_crawl(self) -> bool:
        """Check if a URL from this host can be crawled now."""
        if self.backoff_until and datetime.now(timezone.utc) < self.backoff_until:
            return False
        if self.current_concurrent >= self.max_concurrent:
            return False
        if self.last_crawl_time is not None:
            elapsed = (datetime.now(timezone.utc) - self.last_crawl_time).total_seconds()
            if elapsed < self.delay_seconds:
                return False
        return True

    def record_start(self):
        """Record that a crawl is starting."""
        self.current_concurrent += 1
        self.last_crawl_time = datetime.now(timezone.utc)

    def record_end(self, success: bool):
        """Record that a crawl ended."""
        self.current_concurrent = max(0, self.current_concurrent - 1)
        self.total_crawled += 1
        if success:
            self.consecutive_failures = 0
            self.backoff_until = None
        else:
            self.total_failures += 1
            self.consecutive_failures += 1
            # Exponential backoff on consecutive failures
            if self.consecutive_failures >= 3:
                backoff_seconds = min(300, 2 ** min(self.consecutive_failures, 8))
                self.backoff_until = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)


class URLFrontier:
    """Distributed URL frontier with deduplication, prioritization, and host politeness."""

    def __init__(self, settings=None):
        self.settings = settings
        self._queue: List[tuple] = []  # (priority_score, insertion_counter, URLCandidate)
        self._counter = 0  # For stable sorting
        self._seen_urls: Dict[str, UUID] = {}  # normalized URL -> candidate ID
        self._host_politeness: Dict[str, HostPoliteness] = {}
        self._stats = {
            "urls_added": 0,
            "urls_popped": 0,
            "duplicates_rejected": 0,
            "hosts_blocked": 0,
        }
        self._in_processing: Set[UUID] = set()

    def add(self, candidate: URLCandidate) -> bool:
        """Add a URL candidate to the frontier. Returns False if duplicate."""
        from urllib.parse import urlparse

        normalized = self._normalize_url(candidate.url)

        if normalized in self._seen_urls:
            self._stats["duplicates_rejected"] += 1
            return False

        self._seen_urls[normalized] = candidate.id

        # Compute priority score (lower = higher priority)
        priority_score = self._compute_priority_score(candidate)

        heapq.heappush(self._queue, (priority_score, self._counter, candidate))
        self._counter += 1
        self._stats["urls_added"] += 1
        logger.debug(f"Added URL to frontier: {candidate.url} (priority={priority_score:.2f})")
        return True

    def pop(self, host_concurrency_check: bool = True) -> Optional[URLCandidate]:
        """Pop the highest priority URL that can be crawled now.

        If the top URL's host is not ready (politeness), it's temporarily
        deferred and the next candidate is tried.
        """
        now = datetime.now(timezone.utc)
        deferred = []

        while self._queue:
            _, _, candidate = heapq.heappop(self._queue)
            from urllib.parse import urlparse
            host = urlparse(candidate.url).hostname or "unknown"

            # Check if already being processed
            if candidate.id in self._in_processing:
                continue

            # Check host politeness
            if host_concurrency_check:
                politeness = self._get_host_politeness(host)
                if not politeness.can_crawl():
                    deferred.append((_, _, candidate))  # Defer for now
                    continue

                politeness.record_start()
                self._in_processing.add(candidate.id)

            self._stats["urls_popped"] += 1
            # Restore deferred items
            for item in deferred:
                heapq.heappush(self._queue, item)

            return candidate

        # Restore all deferred items
        for item in deferred:
            heapq.heappush(self._queue, item)

        return None

    def mark_completed(self, candidate: URLCandidate, success: bool):
        """Mark a URL as completed and update host politeness."""
        from urllib.parse import urlparse
        host = urlparse(candidate.url).hostname or "unknown"

        self._in_processing.discard(candidate.id)

        politeness = self._get_host_politeness(host)
        politeness.record_end(success)

    def _get_host_politeness(self, host: str) -> HostPoliteness:
        """Get or create host politeness tracker."""
        if host not in self._host_politeness:
            delay = self.settings.crawl_per_host_delay_seconds if self.settings else 1.0
            max_concurrent = self.settings.crawl_per_host_concurrency if self.settings else 2
            self._host_politeness[host] = HostPoliteness(
                host=host,
                delay_seconds=delay,
                max_concurrent=max_concurrent,
            )
        return self._host_politeness[host]

    def _compute_priority_score(self, candidate: URLCandidate) -> float:
        """Compute priority score (lower = higher priority).

        Factors:
        - Explicit priority (1-10, lower number = higher priority)
        - Estimated value (0-1, higher = higher priority)
        - Age (newer = higher priority)
        """
        base = float(candidate.priority)  # 1-10
        value_penalty = (1.0 - candidate.estimated_value) * 5.0  # 0-5
        # Age factor: newer URLs get slight priority boost
        age_hours = (datetime.now(timezone.utc) - candidate.discovered_at).total_seconds() / 3600
        age_factor = min(age_hours * 0.1, 5.0)  # Cap at 5

        return base + value_penalty + age_factor

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        url = url.strip().lower()
        if url.endswith("/") and len(url) > 1:
            url = url[:-1]
        return url

    def get_stats(self) -> Dict[str, Any]:
        """Get frontier statistics."""
        return {
            **self._stats,
            "queue_size": len(self._queue),
            "in_processing": len(self._in_processing),
            "unique_urls": len(self._seen_urls),
            "active_hosts": len(self._host_politeness),
        }

    def __len__(self) -> int:
        return len(self._queue)
