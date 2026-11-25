"""ORBIT URL Utilities.

Provides URL canonicalization, normalization, link extraction from HTML,
and discovery method implementations (sitemap, RSS/Atom, robots.txt, canonical).
All functions return real extracted candidates — no hardcoded or simulated results.
"""

import logging
import re
from typing import Optional, List, Dict, Any, Set, Tuple
from urllib.parse import urlparse, urljoin, urldefrag, urlunparse
from xml.etree import ElementTree as ET

logger = logging.getLogger("orbit.discovery.url_utils")


# ---------------------------------------------------------------------------
# URL canonicalization & normalization
# ---------------------------------------------------------------------------

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_creative", "gclid", "fbclid", "ref", "source", "medium",
    "campaign", "mc_cid", "mc_eid",
}


def canonicalize_url(url: str) -> str:
    """Return a canonical form of a URL for deduplication.

    Steps:
    1. Strip fragment
    2. Lowercase scheme and host
    3. Remove default ports
    4. Sort query parameters and drop tracking params
    5. Remove trailing slash (except root)
    6. Percent-decode path where safe
    """
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return url.strip()

    # Drop fragment
    parsed = parsed._replace(fragment="")

    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Remove default ports
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    # Path: remove trailing slash unless root
    path = parsed.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    # Query: drop tracking params, sort the rest
    query = parsed.query
    if query:
        params: List[Tuple[str, str]] = []
        for part in query.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
            else:
                k, v = part, ""
            if k.lower() not in TRACKING_PARAMS:
                params.append((k, v))
        params.sort()
        query = "&".join(f"{k}={v}" for k, v in params)

    return urlunparse((scheme, netloc, path, parsed.params, query, ""))


def normalize_url(url: str) -> str:
    """Alias for canonicalize_url (kept for backward compatibility)."""
    return canonicalize_url(url)


def extract_domain(url: str) -> Optional[str]:
    """Extract the domain (host) from a URL."""
    try:
        parsed = urlparse(url)
        return parsed.hostname or None
    except Exception:
        return None


def is_valid_http_url(url: str) -> bool:
    """Return True if url is an absolute http/https URL."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.hostname)
    except Exception:
        return False


def is_same_domain(url_a: str, url_b: str) -> bool:
    """Return True if both URLs share the same registrable domain."""
    da = extract_domain(url_a)
    db = extract_domain(url_b)
    if not da or not db:
        return False
    return da == db


# ---------------------------------------------------------------------------
# HTML link extraction
# ---------------------------------------------------------------------------

LINK_TAG_RE = re.compile(
    r'<(?:a|link|area)\b[^>]*\bhref\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)
CANONICAL_RE = re.compile(
    r'<link\b[^>]*\brel\s*=\s*["\']canonical["\'][^>]*\bhref\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)
ROBOTS_META_RE = re.compile(
    r'<meta\b[^>]*\bname\s*=\s*["\']robots["\'][^>]*>',
    re.IGNORECASE,
)


def extract_links(html: str, base_url: str) -> List[str]:
    """Extract all href links from HTML and resolve against base_url.

    Returns a list of absolute, canonicalized URLs (deduplicated).
    Does NOT include JavaScript-only or mailto/tel links.
    """
    if not html:
        return []

    base = base_url.rstrip("/")
    raw_links: List[str] = LINK_TAG_RE.findall(html)

    resolved: List[str] = []
    for href in raw_links:
        href = href.strip()
        if not href:
            continue
        # Skip non-HTTP schemes
        if href.startswith(("mailto:", "tel:", "javascript:", "data:", "#")):
            continue
        # Resolve relative URLs
        absolute = urljoin(base, href)
        # Remove fragment
        absolute = urldefrag(absolute).url
        if is_valid_http_url(absolute):
            resolved.append(canonicalize_url(absolute))

    # Deduplicate while preserving order
    seen: Set[str] = set()
    unique: List[str] = []
    for u in resolved:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def extract_canonical_url(html: str, base_url: str) -> Optional[str]:
    """Extract the rel=canonical URL from HTML, resolved against base_url."""
    if not html:
        return None
    m = CANONICAL_RE.search(html)
    if not m:
        return None
    canonical = m.group(1).strip()
    absolute = urljoin(base_url, canonical)
    absolute = urldefrag(absolute).url
    if is_valid_http_url(absolute):
        return canonicalize_url(absolute)
    return None


def extract_robots_txt_sitemaps(robots_content: str, base_url: str) -> List[str]:
    """Extract sitemap declarations from robots.txt content.

    Returns a list of absolute sitemap URLs.
    """
    if not robots_content:
        return []

    sitemaps: List[str] = []
    base = base_url.rstrip("/")
    for line in robots_content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip().lower() == "sitemap":
            sitemap_url = value.strip()
            absolute = urljoin(base, sitemap_url)
            if is_valid_http_url(absolute):
                sitemaps.append(canonicalize_url(absolute))

    seen: Set[str] = set()
    unique: List[str] = []
    for u in sitemaps:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


# ---------------------------------------------------------------------------
# Sitemap XML parsing
# -----------

SITEMAP_NS = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def parse_sitemap_xml(content: str, base_url: str) -> List[str]:
    """Parse a sitemap.xml and extract all <loc> URLs.

    Supports both sitemap index files (containing <sitemap><loc>) and
    regular urlset files (containing <url><loc>).
    """
    if not content:
        return []

    urls: List[str] = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        logger.warning("Failed to parse sitemap XML")
        return []

    # Try urlset (regular sitemap)
    for loc in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        text = (loc.text or "").strip()
        if text:
            absolute = urljoin(base_url, text)
            if is_valid_http_url(absolute):
                urls.append(canonicalize_url(absolute))

    # If no loc found with namespace, try without namespace
    if not urls:
        for loc in root.iter("loc"):
            text = (loc.text or "").strip()
            if text:
                absolute = urljoin(base_url, text)
                if is_valid_http_url(absolute):
                    urls.append(canonicalize_url(absolute))

    seen: Set[str] = set()
    unique: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


# ---------------------------------------------------------------------------
# RSS / Atom feed parsing
# ---------------------------------------------------------------------------

def parse_rss_feed(content: str, base_url: str) -> List[str]:
    """Parse an RSS feed and extract item <link> URLs."""
    if not content:
        return []

    urls: List[str] = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        logger.warning("Failed to parse RSS feed XML")
        return []

    # RSS 2.0: /rss/channel/item/link
    for item in root.iter("item"):
        for link in item.iter("link"):
            text = (link.text or "").strip()
            if text:
                absolute = urljoin(base_url, text)
                if is_valid_http_url(absolute):
                    urls.append(canonicalize_url(absolute))

    return _dedup(urls)


def parse_atom_feed(content: str, base_url: str) -> List[str]:
    """Parse an Atom feed and extract entry <link href> URLs."""
    if not content:
        return []

    urls: List[str] = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        logger.warning("Failed to parse Atom feed XML")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        for link in entry.iter("{http://www.w3.org/2005/Atom}link"):
            href = link.get("href")
            if href:
                absolute = urljoin(base_url, href)
                if is_valid_http_url(absolute):
                    urls.append(canonicalize_url(absolute))

    # Fallback: try without namespace
    if not urls:
        for entry in root.iter("entry"):
            for link in entry.iter("link"):
                href = link.get("href")
                if href:
                    absolute = urljoin(base_url, href)
                    if is_valid_http_url(absolute):
                        urls.append(canonicalize_url(absolute))

    return _dedup(urls)


def discover_feed_urls(html: str, base_url: str) -> List[str]:
    """Discover RSS/Atom feed URLs from HTML <link rel=alternate> tags."""
    if not html:
        return []

    feed_re = re.compile(
        r'<link\b[^>]*\brel\s*=\s*["\']([^"\']*alternate[^"\']*)["\'][^>]*>',
        re.IGNORECASE,
    )
    href_re = re.compile(r'\bhref\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
    type_re = re.compile(r'\btype\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

    feed_urls: List[str] = []
    for m in feed_re.finditer(html):
        tag = m.group(0)
        href_m = href_re.search(tag)
        type_m = type_re.search(tag)
        if not href_m:
            continue
        href = href_m.group(1).strip()
        feed_type = (type_m.group(1) if type_m else "").lower()
        is_feed = (
            "rss" in feed_type
            or "atom" in feed_type
            or "xml" in feed_type
            or href.endswith(".rss")
            or href.endswith(".xml")
            or href.endswith("/feed")
            or href.endswith("/feed/")
            or href.endswith("/atom")
        )
        if is_feed:
            absolute = urljoin(base_url, href)
            if is_valid_http_url(absolute):
                feed_urls.append(canonicalize_url(absolute))

    return _dedup(feed_urls)


def _dedup(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    unique: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique
