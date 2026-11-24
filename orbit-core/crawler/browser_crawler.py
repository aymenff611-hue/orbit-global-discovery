"""ORBIT Selective Browser Crawling.

Provides selective JavaScript rendering for pages that require it.
Integrates with Playwright when available, otherwise degrades gracefully.
Only renders when necessary based on content analysis.
"""

import logging
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("orbit.crawler.browser_crawler")


@dataclass
class BrowserRenderResult:
    """Result of browser rendering."""
    url: str
    rendered_html: Optional[str]
    success: bool
    error: Optional[str] = None
    render_time_ms: Optional[float] = None
    javascript_required: bool = False


class BrowserCrawler:
    """Selective browser crawler that renders JavaScript only when necessary.

    Uses Playwright when available. Falls back to HTTP-only extraction
    when browser is not available or not needed.
    """

    def __init__(self, settings=None):
        self.settings = settings
        self.max_concurrent = settings.crawl_browser_max_concurrent if settings else 10
        self.render_only_when_necessary = settings.crawl_browser_render_only_when_necessary if settings else True
        self._playwright_available = self._check_playwright()
        self._stats = {
            "pages_rendered": 0,
            "pages_skipped": 0,
            "render_failures": 0,
            "javascript_detected": 0,
        }

    def _check_playwright(self) -> bool:
        """Check if Playwright is available."""
        try:
            import playwright  # noqa: F401
            return True
        except ImportError:
            logger.warning("Playwright not installed. Browser rendering disabled.")
            return False

    def is_javascript_required(self, html: str, url: str = "") -> bool:
        """Determine if a page requires JavaScript rendering.

        Heuristics:
        - Presence of common JS framework indicators
        - Very little text content relative to script tags
        - Common SPA patterns
        """
        if not html:
            return False

        # Check for script-heavy pages
        script_count = len(re.findall(r'<script[^>]*>', html, re.IGNORECASE))
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        text_length = len(text)

        # If lots of scripts but little text, likely needs JS
        if script_count > 5 and text_length < 500:
            return True

        # Check for common SPA frameworks
        spa_indicators = [
            'ng-app', 'ng-controller',          # Angular
            'data-reactroot', '__NEXT_DATA__',   # React/Next.js
            'data-v-', 'vue-app',                # Vue
            'data-svelte',                       # Svelte
        ]
        for indicator in spa_indicators:
            if indicator.lower() in html.lower():
                return True

        # Check for common lazy-load patterns
        if re.search(r'(?i)(lazy.load|require\.js|system\.js|import\(\))', html):
            return True

        return False

    async def render(self, url: str, html: str) -> BrowserRenderResult:
        """Render a page using browser if JavaScript is required.

        Args:
            url: The page URL
            html: The HTML fetched via HTTP

        Returns:
            BrowserRenderResult with rendered HTML or original HTML
        """
        # Determine if rendering is necessary
        js_required = self.is_javascript_required(html, url)

        if not js_required and self.render_only_when_necessary:
            self._stats["pages_skipped"] += 1
            return BrowserRenderResult(
                url=url,
                rendered_html=html,
                success=True,
                javascript_required=False,
            )

        if not self._playwright_available:
            self._stats["render_failures"] += 1
            logger.warning(f"Browser rendering requested but Playwright not available for {url}")
            return BrowserRenderResult(
                url=url,
                rendered_html=html,
                success=False,
                error="Playwright not available",
                javascript_required=js_required,
            )

        # Attempt Playwright rendering
        try:
            import asyncio
            from playwright.async_api import async_playwright

            start_time = __import__('time').time()

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_content(html, wait_until="networkidle")
                rendered = await page.content()
                await browser.close()

            elapsed = (__import__('time').time() - start_time) * 1000

            self._stats["pages_rendered"] += 1
            self._stats["javascript_detected"] += 1

            return BrowserRenderResult(
                url=url,
                rendered_html=rendered,
                success=True,
                render_time_ms=elapsed,
                javascript_required=True,
            )

        except Exception as e:
            self._stats["render_failures"] += 1
            logger.error(f"Browser rendering failed for {url}: {e}")
            return BrowserRenderResult(
                url=url,
                rendered_html=html,
                success=False,
                error=str(e),
                javascript_required=js_required,
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get browser crawler statistics."""
        return dict(self._stats)

    def is_available(self) -> bool:
        """Check if browser rendering is available."""
        return self._playwright_available


__all__ = ["BrowserCrawler", "BrowserRenderResult"]
