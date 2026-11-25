"""ORBIT Real Source Discovery Methods.

Implements genuine source discovery methods that extract real candidates
from fetched page content:

- HTML link following (extracts <a href>, <link>, <area> tags)
- Sitemap XML discovery (parses sitemap.xml, robots.txt sitemap declarations)
- RSS / Atom feed discovery (parses feed XML, discovers feed URLs from HTML)
- Robots.txt sitemap declarations
- Canonical URL discovery (rel=canonical)
- Source relationship discovery (tracks parent-child relationships)

All methods return real extracted candidates — no hardcoded or simulated results.
"""

import logging
from typing import Optional, List, Dict, Any, Set, Callable
from urllib.parse import urlparse

from core.models import Source, SourceType, SourceStatus, URLCandidate, utc_now
from discovery.source_registry import SourceRegistry
from discovery.url_frontier import URLFrontier
from discovery import url_utils

logger = logging.getLogger("orbit.discovery.discovery_methods")

# Optional domain resolver: maps a URL to a logical domain (for testing with
# virtual hosts all served from localhost). Defaults to the real hostname.
DomainResolver = Callable[[str], str]


def _default_domain_resolver(url: str) -> str:
    hostname = urlparse(url).hostname
    return hostname or "localhost"


class LinkDiscovery:
    """HTML link following discovery method.

    Fetches a page, parses its HTML, extracts all links, normalizes them,
    filters invalid/duplicate URLs, identifies new domains, and registers
    newly discovered sources.
    """

    def __init__(self, registry: SourceRegistry, frontier: URLFrontier,
                 crawler=None, max_links_per_page: int = 100,
                 domain_resolver: Optional[DomainResolver] = None):
        self.registry = registry
        self.frontier = frontier
        self.crawler = crawler
        self.max_links_per_page = max_links_per_page
        self.domain_resolver = domain_resolver or _default_domain_resolver
        self._stats = {
            "pages_processed": 0,
            "links_extracted": 0,
            "new_domains_found": 0,
            "new_sources_registered": 0,
            "urls_added_to_frontier": 0,
            "duplicates_rejected": 0,
        }

    async def discover_from_source(self, source: Source,
                                    limit: int = 100) -> List[URLCandidate]:
        """Discover URLs from a source by fetching its page and extracting links.

        Args:
            source: The Source to discover from (must have a URL).
            limit: Maximum number of URLs to return.

        Returns:
            List of URLCandidate objects with real extracted links.
        """
        if not source.url:
            logger.debug(f"Source {source.id} has no URL, skipping link discovery")
            return []

        url_str = str(source.url)
        logger.info(f"Link discovery from {url_str}")

        self._stats["pages_processed"] += 1

        # Fetch the page
        html = None
        if self.crawler:
            try:
                result = await self.crawler.fetch(url_str, check_ssrf=False)
                if result.get("error"):
                    logger.warning(f"Failed to fetch {url_str}: {result['error']}")
                    return []
                html = result.get("content", "")
            except Exception as e:
                logger.error(f"Error fetching {url_str}: {e}")
                return []

        if not html:
            logger.warning(f"No HTML content for {url_str}")
            return []

        # Extract links from HTML
        links = url_utils.extract_links(html, url_str)
        self._stats["links_extracted"] += len(links)
        logger.info(f"Extracted {len(links)} links from {url_str}")

        # Also extract canonical URL
        canonical_url = url_utils.extract_canonical_url(html, url_str)
        if canonical_url and canonical_url not in links:
            links.insert(0, canonical_url)

        # Discover feed URLs from HTML
        feed_urls = url_utils.discover_feed_urls(html, url_str)
        for feed_url in feed_urls:
            if feed_url not in links:
                links.append(feed_url)

        candidates: List[URLCandidate] = []
        seen_domains: Set[str] = set()

        for link in links[:limit]:
            # Use domain resolver to get logical domain (supports virtual hosts)
            domain = self.domain_resolver(link)
            if not domain:
                continue

            # Check if this is a new domain
            is_new_domain = domain not in self.registry._domains
            if is_new_domain:
                seen_domains.add(domain)
                self._stats["new_domains_found"] += 1
                logger.info(f"New domain discovered: {domain} (from {url_str})")

            # Create candidate
            candidate = URLCandidate(
                url=link,
                domain=domain,
                discovery_method="link_following",
                source_id=source.id,
                priority=3,
                estimated_value=0.5 if is_new_domain else 0.3,
            )
            candidates.append(candidate)

            # Register as a new source if it's a new domain
            if is_new_domain:
                new_source = Source(
                    source_type=SourceType.CANDIDATE_DOMAIN,
                    url=link,
                    domain=domain,
                    host=domain,
                    discovery_method="link_following",
                    discovery_generation=source.discovery_generation + 1,
                    discovered_from=source.id,
                    priority=5,
                )
                registered = self.registry.register_source(new_source)
                if registered.id != new_source.id:
                    # Source already existed (duplicate)
                    self._stats["duplicates_rejected"] += 1
                else:
                    self._stats["new_sources_registered"] += 1
                    # Link parent-child relationship
                    source.child_sources.add(registered.id)
                    registered.parent_source = source.id

            # Add to frontier
            added = self.frontier.add(candidate)
            if added:
                self._stats["urls_added_to_frontier"] += 1

        self._stats["pages_processed"] += 1
        logger.info(f"Link discovery from {url_str}: {len(candidates)} candidates, "
                    f"{len(seen_domains)} new domains")
        return candidates

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)


class SitemapDiscovery:
    """Sitemap XML discovery method.

    Fetches sitemap.xml from a domain, parses it, and extracts all URLs.
    Also checks robots.txt for sitemap declarations.
    """

    def __init__(self, registry: SourceRegistry, frontier: URLFrontier,
                 crawler=None, max_urls_per_sitemap: int = 500,
                 domain_resolver: Optional[DomainResolver] = None):
        self.registry = registry
        self.frontier = frontier
        self.crawler = crawler
        self.max_urls_per_sitemap = max_urls_per_sitemap
        self.domain_resolver = domain_resolver or _default_domain_resolver
        self._stats = {
            "sitemaps_fetched": 0,
            "sitemaps_parsed": 0,
            "urls_extracted": 0,
            "new_domains_found": 0,
            "new_sources_registered": 0,
            "urls_added_to_frontier": 0,
            "robots_sitemaps_found": 0,
        }

    async def discover_from_source(self, source: Source,
                                    limit: int = 500) -> List[URLCandidate]:
        """Discover URLs from sitemap.xml and robots.txt sitemap declarations.

        Args:
            source: The Source to discover from.
            limit: Maximum number of URLs to return.

        Returns:
            List of URLCandidate objects from sitemap URLs.
        """
        if not source.url:
            return []

        base_url = str(source.url)
        parsed = urlparse(base_url)

        # Determine the path base for robots.txt: use the source URL's
        # directory so virtual-host test setups work (all on localhost).
        source_dir = parsed.path.rsplit("/", 1)[0] if "/" in parsed.path else ""
        if source_dir and not source_dir.endswith("/"):
            source_dir = source_dir + "/"
        base = f"{parsed.scheme}://{parsed.netloc}{source_dir}"

        candidates: List[URLCandidate] = []
        seen_urls: Set[str] = set()

        # Try common sitemap locations (relative to domain root and source dir)
        sitemap_urls = [
            f"{parsed.scheme}://{parsed.netloc}/sitemap.xml",
            f"{parsed.scheme}://{parsed.netloc}/sitemap_index.xml",
            f"{base}sitemap.xml",
            f"{base}sitemap_index.xml",
        ]

        # Also check robots.txt for sitemap declarations
        if self.crawler:
            try:
                robots_result = await self.crawler.fetch(
                    f"{base}robots.txt", check_ssrf=False
                )
                if not robots_result.get("error") and robots_result.get("content"):
                    robots_sitemaps = url_utils.extract_robots_txt_sitemaps(
                        robots_result["content"], base
                    )
                    self._stats["robots_sitemaps_found"] = len(robots_sitemaps)
                    sitemap_urls.extend(robots_sitemaps)
                    logger.info(f"Found {len(robots_sitemaps)} sitemaps in robots.txt for {base}")
            except Exception as e:
                logger.debug(f"Error fetching robots.txt for {base}: {e}")

        # Fetch and parse each sitemap
        for sitemap_url in sitemap_urls[:5]:  # Limit to avoid excessive fetching
            if sitemap_url in seen_urls:
                continue
            seen_urls.add(sitemap_url)

            try:
                result = await self.crawler.fetch(sitemap_url, check_ssrf=False)
                if result.get("error"):
                    logger.debug(f"Sitemap not available: {sitemap_url}: {result['error']}")
                    continue

                self._stats["sitemaps_fetched"] += 1
                content = result.get("content", "")
                if not content:
                    continue

                # Parse sitemap XML
                sitemap_links = url_utils.parse_sitemap_xml(content, sitemap_url)
                self._stats["sitemaps_parsed"] += 1
                logger.info(f"Parsed {len(sitemap_links)} URLs from sitemap {sitemap_url}")

                for link in sitemap_links:
                    if len(candidates) >= limit:
                        break

                    domain = self.domain_resolver(link)
                    if not domain:
                        continue

                    is_new_domain = domain not in self.registry._domains
                    if is_new_domain:
                        self._stats["new_domains_found"] += 1
                        logger.info(f"New domain from sitemap: {domain}")

                    candidate = URLCandidate(
                        url=link,
                        domain=domain,
                        discovery_method="sitemap",
                        source_id=source.id,
                        priority=4,
                        estimated_value=0.6 if is_new_domain else 0.4,
                    )
                    candidates.append(candidate)

                    # Register new source for new domains
                    if is_new_domain:
                        new_source = Source(
                            source_type=SourceType.CANDIDATE_DOMAIN,
                            url=link,
                            domain=domain,
                            host=domain,
                            discovery_method="sitemap",
                            discovery_generation=source.discovery_generation + 1,
                            discovered_from=source.id,
                            priority=5,
                        )
                        registered = self.registry.register_source(new_source)
                        if registered.id == new_source.id:
                            self._stats["new_sources_registered"] += 1
                            source.child_sources.add(registered.id)
                            registered.parent_source = source.id
                        else:
                            self._stats["duplicates_rejected"] += 1

                    # Add to frontier
                    added = self.frontier.add(candidate)
                    if added:
                        self._stats["urls_added_to_frontier"] += 1

                self._stats["urls_extracted"] += len(sitemap_links)

            except Exception as e:
                logger.error(f"Error processing sitemap {sitemap_url}: {e}")

        logger.info(f"Sitemap discovery from {base_url}: {len(candidates)} candidates")
        return candidates

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)


class FeedDiscovery:
    """RSS / Atom feed discovery method.

    Discovers feed URLs from HTML (alternate links), fetches feeds,
    parses them, and extracts item/link URLs as candidates.
    """

    def __init__(self, registry: SourceRegistry, frontier: URLFrontier,
                 crawler=None, max_items_per_feed: int = 100,
                 domain_resolver: Optional[DomainResolver] = None):
        self.registry = registry
        self.frontier = frontier
        self.crawler = crawler
        self.max_items_per_feed = max_items_per_feed
        self.domain_resolver = domain_resolver or _default_domain_resolver
        self._stats = {
            "feeds_discovered": 0,
            "feeds_fetched": 0,
            "items_extracted": 0,
            "new_domains_found": 0,
            "new_sources_registered": 0,
            "urls_added_to_frontier": 0,
        }

    async def discover_from_source(self, source: Source,
                                    limit: int = 100) -> List[URLCandidate]:
        """Discover URLs from RSS/Atom feeds associated with a source.

        Args:
            source: The Source to discover from.
            limit: Maximum number of URLs to return.

        Returns:
            List of URLCandidate objects from feed items.
        """
        if not source.url:
            return []

        base_url = str(source.url)
        candidates: List[URLCandidate] = []
        seen_urls: Set[str] = set()

        # First, fetch the page to discover feed URLs
        feed_urls: List[str] = []
        if self.crawler:
            try:
                result = await self.crawler.fetch(base_url, check_ssrf=False)
                if not result.get("error") and result.get("content"):
                    feed_urls = url_utils.discover_feed_urls(
                        result["content"], base_url
                    )
                    self._stats["feeds_discovered"] = len(feed_urls)
                    logger.info(f"Discovered {len(feed_urls)} feed URLs from {base_url}")
            except Exception as e:
                logger.debug(f"Error discovering feeds from {base_url}: {e}")

        # Also try common feed locations
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        common_feeds = [
            f"{base}/feed",
            f"{base}/feed/",
            f"{base}/rss",
            f"{base}/rss.xml",
            f"{base}/atom.xml",
            f"{base}/feed.xml",
        ]
        for feed_url in common_feeds:
            if feed_url not in feed_urls:
                feed_urls.append(feed_url)

        # Fetch and parse each feed
        for feed_url in feed_urls[:5]:
            if feed_url in seen_urls:
                continue
            seen_urls.add(feed_url)

            try:
                result = await self.crawler.fetch(feed_url, check_ssrf=False)
                if result.get("error"):
                    logger.debug(f"Feed not available: {feed_url}: {result['error']}")
                    continue

                self._stats["feeds_fetched"] += 1
                content = result.get("content", "")
                if not content:
                    continue

                # Try RSS first, then Atom
                feed_links = url_utils.parse_rss_feed(content, feed_url)
                if not feed_links:
                    feed_links = url_utils.parse_atom_feed(content, feed_url)

                logger.info(f"Parsed {len(feed_links)} items from feed {feed_url}")

                for link in feed_links[:self.max_items_per_feed]:
                    if len(candidates) >= limit:
                        break

                    if link in seen_urls:
                        continue
                    seen_urls.add(link)

                    domain = self.domain_resolver(link)
                    if not domain:
                        continue

                    is_new_domain = domain not in self.registry._domains
                    if is_new_domain:
                        self._stats["new_domains_found"] += 1

                    candidate = URLCandidate(
                        url=link,
                        domain=domain,
                        discovery_method="rss" if "rss" in feed_url.lower() else "atom",
                        source_id=source.id,
                        priority=4,
                        estimated_value=0.5 if is_new_domain else 0.3,
                    )
                    candidates.append(candidate)

                    # Register new source for new domains
                    if is_new_domain:
                        new_source = Source(
                            source_type=SourceType.CANDIDATE_DOMAIN,
                            url=link,
                            domain=domain,
                            host=domain,
                            discovery_method="feed",
                            discovery_generation=source.discovery_generation + 1,
                            discovered_from=source.id,
                            priority=5,
                        )
                        registered = self.registry.register_source(new_source)
                        if registered.id == new_source.id:
                            self._stats["new_sources_registered"] += 1
                            source.child_sources.add(registered.id)
                            registered.parent_source = source.id
                        else:
                            self._stats["duplicates_rejected"] += 1

                    # Add to frontier
                    added = self.frontier.add(candidate)
                    if added:
                        self._stats["urls_added_to_frontier"] += 1

                self._stats["items_extracted"] += len(feed_links)

            except Exception as e:
                logger.error(f"Error processing feed {feed_url}: {e}")

        logger.info(f"Feed discovery from {base_url}: {len(candidates)} candidates")
        return candidates

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)


class CanonicalDiscovery:
    """Canonical URL discovery method.

    Extracts rel=canonical URLs from pages to identify the preferred
    URL for a page, useful for deduplication and source consolidation.
    """

    def __init__(self, registry: SourceRegistry, frontier: URLFrontier,
                 crawler=None, domain_resolver: Optional[DomainResolver] = None):
        self.registry = registry
        self.frontier = frontier
        self.crawler = crawler
        self.domain_resolver = domain_resolver or _default_domain_resolver
        self._stats = {
            "pages_processed": 0,
            "canonicals_found": 0,
            "new_domains_found": 0,
            "new_sources_registered": 0,
        }

    async def discover_from_source(self, source: Source,
                                    limit: int = 50) -> List[URLCandidate]:
        """Discover canonical URLs from a source page.

        Args:
            source: The Source to discover from.
            limit: Maximum number of URLs to return.

        Returns:
            List of URLCandidate objects for canonical URLs.
        """
        if not source.url:
            return []

        url_str = str(source.url)
        candidates: List[URLCandidate] = []

        if self.crawler:
            try:
                result = await self.crawler.fetch(url_str, check_ssrf=False)
                if result.get("error"):
                    return []
                html = result.get("content", "")
            except Exception as e:
                logger.error(f"Error fetching {url_str}: {e}")
                return []
        else:
            return []

        self._stats["pages_processed"] += 1

        canonical_url = url_utils.extract_canonical_url(html, url_str)
        if canonical_url:
            self._stats["canonicals_found"] += 1
            domain = self.domain_resolver(canonical_url)
            if domain:
                is_new_domain = domain not in self.registry._domains
                if is_new_domain:
                    self._stats["new_domains_found"] += 1

                candidate = URLCandidate(
                    url=canonical_url,
                    domain=domain,
                    discovery_method="canonical",
                    source_id=source.id,
                    priority=2,
                    estimated_value=0.7,
                )
                candidates.append(candidate)

                if is_new_domain:
                    new_source = Source(
                        source_type=SourceType.CANDIDATE_DOMAIN,
                        url=canonical_url,
                        domain=domain,
                        host=domain,
                        discovery_method="canonical",
                        discovery_generation=source.discovery_generation + 1,
                        discovered_from=source.id,
                        priority=5,
                    )
                    registered = self.registry.register_source(new_source)
                    if registered.id == new_source.id:
                        self._stats["new_sources_registered"] += 1
                        source.child_sources.add(registered.id)
                        registered.parent_source = source.id

                added = self.frontier.add(candidate)
                if added:
                    pass  # counted in frontier stats

        logger.info(f"Canonical discovery from {url_str}: {len(candidates)} candidates")
        return candidates

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)


class RelationshipDiscovery:
    """Source relationship discovery method.

    Tracks parent-child source relationships discovered during crawling.
    Records which sources lead to which other sources, building a
    discovery graph for provenance tracking.
    """

    def __init__(self, registry: SourceRegistry):
        self.registry = registry
        self._stats = {
            "relationships_recorded": 0,
            "parent_child_pairs": 0,
        }

    def record_relationship(self, parent_source: Source,
                            child_source: Source,
                            discovery_method: str) -> bool:
        """Record a parent-child relationship between sources.

        Args:
            parent_source: The source that led to the discovery.
            child_source: The newly discovered source.
            discovery_method: The method used (link, sitemap, rss, etc.).

        Returns:
            True if the relationship was newly recorded.
        """
        if not parent_source.id or not child_source.id:
            return False

        # Check if relationship already exists
        if child_source.id in parent_source.child_sources:
            return False

        # Record bidirectional relationship
        parent_source.child_sources.add(child_source.id)
        child_source.parent_source = parent_source.id
        child_source.related_sources.add(parent_source.id)
        parent_source.related_sources.add(child_source.id)

        self._stats["relationships_recorded"] += 1
        self._stats["parent_child_pairs"] += 1
        logger.debug(f"Recorded relationship: {parent_source.domain} -> "
                     f"{child_source.domain} via {discovery_method}")
        return True

    def get_discovery_graph(self, source_id) -> Dict[str, Any]:
        """Get the discovery subgraph rooted at a source."""
        source = self.registry.get_source(source_id)
        if not source:
            return {}

        return {
            "source_id": str(source.id),
            "domain": source.domain,
            "discovery_method": source.discovery_method,
            "generation": source.discovery_generation,
            "children": [
                {
                    "source_id": str(cid),
                    "domain": self.registry._sources.get(cid, type("obj", (object,), {"domain": "unknown"})).domain,
                }
                for cid in source.child_sources
                if cid in self.registry._sources
            ],
            "parent": str(source.parent_source) if source.parent_source else None,
        }

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)
