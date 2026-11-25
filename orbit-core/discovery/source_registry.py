"""ORBIT Source Registry.

Manages the lifecycle of sources from candidate URL to qualified demand source.
Implements Requirement A: clear distinction between source types.
Never counts duplicates as new discoveries.
"""

import logging
from typing import Optional, List, Set, Dict, Any
from datetime import datetime, timezone
from uuid import UUID

from core.models import (
    Source, SourceType, SourceStatus, URLCandidate, Opportunity,
    Entity, Relationship, utc_now
)

logger = logging.getLogger("orbit.discovery.source_registry")


class SourceRegistry:
    """Central registry for all sources in the ORBIT network.

    Maintains the source lifecycle:
    CANDIDATE_URL → CANDIDATE_DOMAIN → VALIDATED_DOMAIN → USEFUL_SOURCE →
    ACTIVE_MONITORED_SOURCE → QUALIFIED_DEMAND_SOURCE
    """

    def __init__(self, storage_backend=None):
        self.storage = storage_backend
        self._sources: Dict[UUID, Source] = {}
        self._domains: Dict[str, Set[UUID]] = {}  # domain -> source IDs
        self._url_index: Dict[str, UUID] = {}  # url -> source ID (dedup)
        self._stats = {
            "candidate_urls": 0,
            "candidate_domains": 0,
            "validated_domains": 0,
            "useful_sources": 0,
            "active_sources": 0,
            "qualified_demand_sources": 0,
            "duplicates_rejected": 0,
        }

    def register_candidate_url(self, url: str, source_id: Optional[UUID] = None,
                                discovery_method: Optional[str] = None,
                                parent_source: Optional[UUID] = None,
                                priority: int = 5) -> URLCandidate:
        """Register a new candidate URL. Returns duplicate if already seen."""
        # Normalize URL for dedup
        normalized_url = self._normalize_url(url)

        if normalized_url in self._url_index:
            existing_id = self._url_index[normalized_url]
            self._stats["duplicates_rejected"] += 1
            logger.debug(f"Duplicate URL rejected: {url}")
            # Return existing candidate marked as duplicate
            existing = self._sources.get(existing_id)
            if existing:
                return URLCandidate(
                    id=existing_id,
                    url=url,
                    source_id=existing.id,
                    is_duplicate=True,
                    duplicate_of=existing_id,
                    discovery_method=discovery_method,
                    priority=priority,
                )
            return URLCandidate(
                id=existing_id,
                url=url,
                is_duplicate=True,
                duplicate_of=existing_id,
            )

        candidate = URLCandidate(
            id=source_id or UUID(int=0),  # Will be assigned
            url=url,
            discovery_method=discovery_method,
            priority=priority,
        )
        self._url_index[normalized_url] = candidate.id
        self._stats["candidate_urls"] += 1
        logger.info(f"Registered candidate URL: {url} (method={discovery_method})")
        return candidate

    def register_source(self, source: Source) -> Source:
        """Register a new source in the registry. Enforces type/status consistency."""
        # Dedup by domain
        if source.domain:
            domain_key = source.domain.lower()
            if domain_key in self._domains:
                # Check if this domain already has a source of equal or higher type
                existing_ids = self._domains[domain_key]
                for existing_id in existing_ids:
                    existing = self._sources.get(existing_id)
                    if existing:
                        existing_type = existing.source_type.value if hasattr(existing.source_type, 'value') else existing.source_type
                        new_type_val = source.source_type.value if hasattr(source.source_type, 'value') else source.source_type
                        if existing_type >= new_type_val:
                            logger.debug(f"Domain {domain_key} already registered at {existing_type}")
                            self._stats["duplicates_rejected"] += 1
                            return existing

        # Store source
        self._sources[source.id] = source
        self.updated_at = utc_now()

        # Index by domain
        if source.domain:
            domain_key = source.domain.lower()
            if domain_key not in self._domains:
                self._domains[domain_key] = set()
            self._domains[domain_key].add(source.id)

        # Update stats
        self._update_stats()
        source_type_val = source.source_type.value if hasattr(source.source_type, 'value') else source.source_type
        status_val = source.status.value if hasattr(source.status, 'value') else source.status
        logger.info(f"Registered source: {source.domain or source.url} "
                    f"type={source_type_val} status={status_val}")
        return source

    def get_source(self, source_id: UUID) -> Optional[Source]:
        """Retrieve a source by ID."""
        return self._sources.get(source_id)

    def get_source_by_url(self, url: str) -> Optional[Source]:
        """Retrieve a source by URL."""
        from urllib.parse import urlparse
        normalized = url.strip().lower()
        if normalized.endswith("/") and len(normalized) > 1:
            normalized = normalized[:-1]
        for source in self._sources.values():
            if source.url:
                source_url = str(source.url).strip().lower()
                if source_url.endswith("/") and len(source_url) > 1:
                    source_url = source_url[:-1]
                if source_url == normalized:
                    return source
        return None

    def get_sources_by_domain(self, domain: str) -> List[Source]:
        """Get all sources for a domain."""
        domain_key = domain.lower()
        ids = self._domains.get(domain_key, set())
        return [self._sources[sid] for sid in ids if sid in self._sources]

    def promote_source(self, source_id: UUID, new_type: SourceType,
                        new_status: SourceStatus, validation_method: Optional[str] = None,
                        validation_score: Optional[float] = None) -> Optional[Source]:
        """Promote a source to a higher type/status in the lifecycle."""
        source = self._sources.get(source_id)
        if not source:
            logger.warning(f"Source {source_id} not found for promotion")
            return None

        source.source_type = new_type
        source.status = new_status
        source.updated_at = utc_now()

        if new_type in (SourceType.VALIDATED_DOMAIN, SourceType.USEFUL_SOURCE,
                         SourceType.ACTIVE_MONITORED_SOURCE, SourceType.QUALIFIED_DEMAND_SOURCE):
            source.validated_at = utc_now()
            source.validation_method = validation_method
            source.validation_score = validation_score

        self._update_stats()
        new_type_val = new_type.value if hasattr(new_type, 'value') else new_type
        new_status_val = new_status.value if hasattr(new_status, 'value') else new_status
        logger.info(f"Promoted source {source_id} to {new_type_val}/{new_status_val}")
        return source

    def record_crawl(self, source_id: UUID, success: bool, pages_found: int = 0,
                      opportunities_found: int = 0):
        """Record a crawl result for a source."""
        source = self._sources.get(source_id)
        if not source:
            return
        source.crawl_count += 1
        source.last_crawled = utc_now()
        if success:
            source.last_successful_crawl = utc_now()
            source.pages_crawled += pages_found
            source.opportunities_found += opportunities_found
        else:
            source.failure_count += 1
        source.updated_at = utc_now()

        # Recalculate yield score
        if source.crawl_count > 0:
            source.yield_score = source.opportunities_found / max(source.crawl_count, 1)

    def record_opportunity(self, source_id: UUID):
        """Record that a source produced a qualified opportunity.

        Persists the opportunity count and recalculates yield_score
        so that adaptive resource allocation reflects actual observed
        source performance (not artificial counters).
        """
        source = self._sources.get(source_id)
        if source:
            source.opportunities_found += 1
            source.updated_at = utc_now()
            # Recalculate yield from real observed data
            source.yield_score = source.opportunities_found / max(source.crawl_count, 1)

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return dict(self._stats)

    def get_sources_by_type(self, source_type: SourceType) -> List[Source]:
        """Get all sources of a given type."""
        return [s for s in self._sources.values() if s.source_type == source_type]

    def get_sources_by_status(self, status: SourceStatus) -> List[Source]:
        """Get all sources of a given status."""
        return [s for s in self._sources.values() if s.status == status]

    def get_high_yield_sources(self, min_yield: float = 0.1, limit: int = 100) -> List[Source]:
        """Get sources with yield above threshold, sorted by yield."""
        candidates = [s for s in self._sources.values()
                      if s.yield_score >= min_yield and s.status in
                      (SourceStatus.USEFUL, SourceStatus.ACTIVE, SourceStatus.QUALIFIED)]
        return sorted(candidates, key=lambda s: s.yield_score, reverse=True)[:limit]

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        url = url.strip().lower()
        # Remove trailing slash
        if url.endswith("/") and len(url) > 1:
            url = url[:-1]
        # Remove common tracking parameters (simplified)
        return url

    def _update_stats(self):
        """Update internal statistics counters."""
        self._stats["candidate_domains"] = len(self._domains)
        self._stats["validated_domains"] = len([
            s for s in self._sources.values()
            if s.source_type in (SourceType.VALIDATED_DOMAIN, SourceType.USEFUL_SOURCE,
                                  SourceType.ACTIVE_MONITORED_SOURCE, SourceType.QUALIFIED_DEMAND_SOURCE)
        ])
        self._stats["useful_sources"] = len([
            s for s in self._sources.values()
            if s.source_type in (SourceType.USEFUL_SOURCE, SourceType.ACTIVE_MONITORED_SOURCE,
                                  SourceType.QUALIFIED_DEMAND_SOURCE)
        ])
        self._stats["active_sources"] = len([
            s for s in self._sources.values()
            if s.status == SourceStatus.ACTIVE
        ])
        self._stats["qualified_demand_sources"] = len([
            s for s in self._sources.values()
            if s.source_type == SourceType.QUALIFIED_DEMAND_SOURCE
        ])

    def __len__(self) -> int:
        return len(self._sources)

    def __contains__(self, source_id: UUID) -> bool:
        return source_id in self._sources
