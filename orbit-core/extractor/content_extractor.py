"""ORBIT Content Extraction.

Extracts readable text and structured data from crawled pages.
Separates raw content from extracted text. Supports both static HTML
and selective JavaScript rendering.
"""

import logging
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timezone

from core.models import Source, Opportunity, utc_now

logger = logging.getLogger("orbit.extractor.content_extractor")


@dataclass
class ExtractedContent:
    """Result of content extraction."""
    url: str
    raw_html: Optional[str]
    extracted_text: str
    title: Optional[str]
    language: Optional[str]
    language_confidence: Optional[float]
    encoding: Optional[str]
    content_type: Optional[str]
    size_bytes: int
    extraction_method: str  # trafilatura, readability, bs4, browser
    extracted_at: datetime
    links: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.metadata is None:
            self.metadata = {}


class ContentExtractor:
    """Extracts content from crawled pages using multiple methods.

    Tier 1: Trafilatura (fast, good for articles)
    Tier 2: Readability (good fallback)
    Tier 3: BeautifulSoup (basic text extraction)
    """

    def __init__(self, settings=None):
        self.settings = settings
        self._stats = {
            "pages_extracted": 0,
            "extractions_by_method": {},
            "failures": 0,
        }

    def extract(self, url: str, html: str,
                use_browser: bool = False,
                browser_rendered_html: Optional[str] = None) -> ExtractedContent:
        """Extract content from a page.

        Tries multiple extraction methods in order of cost/quality.
        """
        self._stats["pages_extracted"] += 1

        # Try trafilatura first (best for articles, fast)
        try:
            import trafilatura
            result = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )
            if result and len(result.strip()) > 50:
                self._stats["extractions_by_method"]["trafilatura"] = \
                    self._stats["extractions_by_method"].get("trafilatura", 0) + 1
                return self._build_result(
                    url=url,
                    raw_html=html,
                    extracted_text=result,
                    method="trafilatura",
                    browser_used=use_browser,
                )
        except Exception as e:
            logger.debug(f"Trafilatura extraction failed for {url}: {e}")

        # Try readability-lxml
        try:
            from readability import Document
            doc = Document(html)
            title = doc.title()
            content = doc.summary(html_partial=False)
            # Strip HTML tags from summary
            import re
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
            if text and len(text) > 50:
                self._stats["extractions_by_method"]["readability"] = \
                    self._stats["extractions_by_method"].get("readability", 0) + 1
                return self._build_result(
                    url=url,
                    raw_html=html,
                    extracted_text=text,
                    title=title,
                    method="readability",
                    browser_used=use_browser,
                )
        except Exception as e:
            logger.debug(f"Readability extraction failed for {url}: {e}")

        # Fallback: BeautifulSoup basic extraction
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # Remove script and style elements
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            title = soup.title.string.strip() if soup.title else None
            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r'\s+', ' ', text).strip()
            if text and len(text) > 50:
                self._stats["extractions_by_method"]["beautifulsoup"] = \
                    self._stats["extractions_by_method"].get("beautifulsoup", 0) + 1
                return self._build_result(
                    url=url,
                    raw_html=html,
                    extracted_text=text,
                    title=title,
                    method="beautifulsoup",
                    browser_used=use_browser,
                )
        except Exception as e:
            logger.debug(f"BeautifulSoup extraction failed for {url}: {e}")

        # All extraction methods failed
        self._stats["failures"] += 1
        logger.warning(f"All extraction methods failed for {url}")
        return self._build_result(
            url=url,
            raw_html=html,
            extracted_text="",
            method="failed",
            browser_used=use_browser,
        )

    def _build_result(self, url: str, raw_html: Optional[str],
                      extracted_text: str, method: str,
                      browser_used: bool,
                      title: Optional[str] = None) -> ExtractedContent:
        """Build an ExtractedContent result."""
        # Detect language (simple heuristic)
        language, confidence = self._detect_language_simple(extracted_text)

        return ExtractedContent(
            url=url,
            raw_html=raw_html,
            extracted_text=extracted_text,
            title=title,
            language=language,
            language_confidence=confidence,
            encoding="utf-8",
            content_type="text/html",
            size_bytes=len(raw_html.encode("utf-8")) if raw_html else 0,
            extraction_method=method,
            extracted_at=utc_now(),
        )

    def _detect_language_simple(self, text: str) -> tuple:
        """Simple language detection heuristic."""
        if not text or len(text) < 10:
            return None, None

        # Count Arabic characters
        arabic_count = len(re.findall(r'[\u0600-\u06FF]', text))
        # Count CJK characters
        cjk_count = len(re.findall(r'[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]', text))
        # Count Cyrillic
        cyrillic_count = len(re.findall(r'[\u0400-\u04FF]', text))

        total = len(text)
        if total == 0:
            return None, None

        if arabic_count / total > 0.1:
            return "ar", min(arabic_count / total, 1.0)
        if cjk_count / total > 0.1:
            return "zh", min(cjk_count / total, 1.0)
        if cyrillic_count / total > 0.1:
            return "ru", min(cyrillic_count / total, 1.0)

        # Default to English for Latin script
        return "en", 0.5

    def get_stats(self) -> dict:
        return dict(self._stats)


# Add browser_used field to ExtractedContent (monkey-patch for dataclass)
ExtractedContent.browser_used = False
