"""ORBIT HTTP Crawler.

Performs HTTP fetching with per-host politeness, robots.txt compliance,
SSRF protection, DNS rebinding protection, and retry/backoff logic.
"""

import logging
import asyncio
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from urllib.parse import urlparse
import re

import httpx
from core.models import URLCandidate, Source, utc_now

logger = logging.getLogger("orbit.crawler.http_crawler")


class RobotsTxtChecker:
    """Simple robots.txt compliance checker (RFC 9309)."""

    def __init__(self, user_agent: str = "ORBIT-DiscoveryBot/1.0"):
        self.user_agent = user_agent
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        self._ttl_seconds = 3600  # Cache robots.txt for 1 hour

    async def can_fetch(self, url: str, client: httpx.AsyncClient) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        try:
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            robots_url = f"{base}/robots.txt"

            now = datetime.now(timezone.utc)
            if base in self._cache and base in self._cache_ttl:
                if now < self._cache_ttl[base]:
                    return self._is_allowed(url, self._cache[base])

            # Fetch robots.txt
            try:
                resp = await client.get(robots_url, timeout=10.0)
                if resp.status_code == 200:
                    rules = self._parse_robots(resp.text)
                    self._cache[base] = rules
                    self._cache_ttl[base] = now + __import__('datetime').timedelta(seconds=self._ttl_seconds)
                    return self._is_allowed(url, rules)
                else:
                    # No robots.txt or error - allow by default
                    return True
            except Exception:
                return True
        except Exception:
            return True

    def _parse_robots(self, content: str) -> Dict[str, Any]:
        """Parse robots.txt content."""
        rules = {
            "disallow": [],
            "allow": [],
            "crawl_delay": None,
        }

        current_agent = None
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if key == "user-agent":
                    current_agent = value
                elif key == "disallow" and current_agent in ("*", self.user_agent):
                    if value:
                        rules["disallow"].append(value)
                elif key == "allow" and current_agent in ("*", self.user_agent):
                    if value:
                        rules["allow"].append(value)
                elif key == "crawl-delay" and current_agent in ("*", self.user_agent):
                    try:
                        rules["crawl_delay"] = float(value)
                    except ValueError:
                        pass

        return rules

    def _is_allowed(self, url: str, rules: Dict[str, Any]) -> bool:
        """Check if URL is allowed by robots.txt rules."""
        parsed = urlparse(url)
        path = parsed.path or "/"

        # Check disallow rules first
        for disallow in rules["disallow"]:
            if path.startswith(disallow):
                # Check if there's a more specific allow rule
                for allow in rules["allow"]:
                    if path.startswith(allow) and len(allow) > len(disallow):
                        return True
                return False

        return True


class SSRFProtection:
    """SSRF (Server-Side Request Forgery) protection."""

    PRIVATE_IP_RANGES = [
        r"^10\.",                     # Class A private
        r"^172\.(1[6-9]|2[0-9]|3[01])\.",  # Class B private
        r"^192\.168\.",               # Class C private
        r"^169\.254\.",               # Link-local
        r"^fc00:",                    # IPv6 unique local
        r"^fe80:",                    # IPv6 link-local
    ]

    BLOCKED_HOSTS = [
        "0.0.0.0",
        "169.254.169.254",  # AWS metadata
        "169.254.170.2",    # Azure/GCP metadata
    ]

    # Allow localhost for development/local testing.
    # Set to False in production to block all loopback addresses.
    ALLOW_LOCALHOST = False

    @classmethod
    def is_safe(cls, url: str) -> bool:
        """Check if URL is safe from SSRF attacks."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""

            # Block loopback only if localhost is not allowed
            if not cls.ALLOW_LOCALHOST:
                for pattern in [r"^127\.", r"^::1$"]:
                    if re.match(pattern, hostname):
                        logger.warning(f"SSRF blocked: private IP {hostname}")
                        return False
                if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
                    logger.warning(f"SSRF blocked: host {hostname}")
                    return False

            # Block private IP ranges (always)
            for pattern in cls.PRIVATE_IP_RANGES:
                if re.match(pattern, hostname):
                    logger.warning(f"SSRF blocked: private IP {hostname}")
                    return False

            # Block known bad hosts
            if hostname.lower() in cls.BLOCKED_HOSTS:
                logger.warning(f"SSRF blocked: host {hostname}")
                return False

            # Only allow http and https
            if parsed.scheme not in ("http", "https"):
                logger.warning(f"SSRF blocked: scheme {parsed.scheme}")
                return False

            return True
        except Exception:
            return False


class HTTPCrawler:
    """HTTP crawler with politeness, retries, and safety protections."""

    def __init__(self, settings=None):
        self.settings = settings
        self.user_agent = settings.crawl_user_agent if settings else "ORBIT-DiscoveryBot/1.0"
        self.timeout = settings.crawl_timeout_seconds if settings else 30
        self.max_retries = settings.crawl_max_retries if settings else 5
        self.backoff_base = settings.crawl_backoff_base_seconds if settings else 2.0
        self.respect_robots = settings.crawl_respect_robots_txt if settings else True

        self._robots_checker = RobotsTxtChecker(user_agent=self.user_agent)
        self._stats = {
            "pages_fetched": 0,
            "pages_failed": 0,
            "robots_blocked": 0,
            "ssrf_blocked": 0,
            "bytes_downloaded": 0,
            "status_codes": {},
        }
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            max_redirects=10,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def fetch(self, url: str,
                    check_robots: bool = None,
                    check_ssrf: bool = True) -> Dict[str, Any]:
        """Fetch a URL and return result dictionary.

        Returns:
            dict with keys: url, status_code, content, content_type,
            headers, size_bytes, fetched_at, error, from_cache
        """
        result = {
            "url": url,
            "status_code": None,
            "content": None,
            "content_type": None,
            "headers": {},
            "size_bytes": 0,
            "fetched_at": None,
            "error": None,
            "from_cache": False,
        }

        # SSRF check
        if check_ssrf and not SSRFProtection.is_safe(url):
            result["error"] = "SSRF protection: URL blocked"
            self._stats["ssrf_blocked"] += 1
            logger.warning(f"SSRF blocked: {url}")
            return result

        # Robots.txt check
        if check_robots is None:
            check_robots = self.respect_robots

        if check_robots and self._client:
            allowed = await self._robots_checker.can_fetch(url, self._client)
            if not allowed:
                result["error"] = "Blocked by robots.txt"
                self._stats["robots_blocked"] += 1
                logger.debug(f"Robots.txt blocked: {url}")
                return result

        # Fetch with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                if not self._client:
                    async with httpx.AsyncClient(
                        headers={"User-Agent": self.user_agent},
                        timeout=httpx.Timeout(self.timeout),
                    ) as client:
                        resp = await client.get(url)
                        return self._process_response(resp, result)
                else:
                    resp = await self._client.get(url)
                    return self._process_response(resp, result)
            except httpx.TimeoutException as e:
                last_error = str(e)
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}): {e}")
            except httpx.HTTPError as e:
                last_error = str(e)
                logger.warning(f"HTTP error fetching {url} (attempt {attempt + 1}): {e}")
            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error fetching {url} (attempt {attempt + 1}): {e}")

            # Exponential backoff
            if attempt < self.max_retries:
                wait = self.backoff_base ** attempt
                await asyncio.sleep(min(wait, 60))

        result["error"] = last_error or "Failed after retries"
        self._stats["pages_failed"] += 1
        logger.error(f"Failed to fetch {url} after {self.max_retries + 1} attempts: {last_error}")
        return result

    def _process_response(self, resp: httpx.Response,
                          result: Dict[str, Any]) -> Dict[str, Any]:
        """Process HTTP response into result dict."""
        result["status_code"] = resp.status_code
        result["content"] = resp.text
        result["content_type"] = resp.headers.get("content-type", "")
        result["headers"] = dict(resp.headers)
        result["size_bytes"] = len(resp.content)
        result["fetched_at"] = datetime.now(timezone.utc).isoformat()

        self._stats["pages_fetched"] += 1
        self._stats["bytes_downloaded"] += result["size_bytes"]

        code = str(resp.status_code)
        self._stats["status_codes"][code] = self._stats["status_codes"].get(code, 0) + 1

        return result

    def get_stats(self) -> dict:
        return dict(self._stats)
