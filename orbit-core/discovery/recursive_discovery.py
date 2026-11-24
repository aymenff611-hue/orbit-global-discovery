"""ORBIT Recursive Discovery Engine.

Implements the central discovery principle:
Discovered source → extracted information → entities and relationships →
newly discovered sources → validated sources → new demand signals →
qualified opportunities → accumulated knowledge → intelligent discovery
prioritization → further source expansion.

Uses measurable exploration/exploitation strategies rather than arbitrary
agent decisions.
"""

import logging
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone
from uuid import UUID
from collections import defaultdict

from core.models import (
    Source, SourceType, SourceStatus, URLCandidate, Opportunity,
    Entity, Relationship, DiscoveryResult, utc_now
)
from discovery.source_registry import SourceRegistry
from discovery.url_frontier import URLFrontier

logger = logging.getLogger("orbit.discovery.recursive_discovery")


class DiscoveryCycle:
    """Results of a single discovery expansion cycle."""

    def __init__(self, cycle_id: UUID):
        self.cycle_id = cycle_id
        self.seed_sources: int = 0
        self.candidate_urls: int = 0
        self.candidate_domains: int = 0
        self.validated_domains: int = 0
        self.useful_sources: int = 0
        self.active_sources: int = 0
        self.qualified_demand_sources: int = 0
        self.new_opportunities: int = 0
        self.duplicate_urls: int = 0
        self.unique_domains: Set[str] = set()
        self.timestamp: datetime = utc_now()


class RecursiveDiscoveryEngine:
    """Feedback-driven recursive discovery engine.

    Identifies promising sources, measures yield and quality, discovers
    related sources, tests new discovery paths, estimates expected value,
    and allocates crawling resources dynamically.
    """

    def __init__(self, registry: SourceRegistry, frontier: URLFrontier,
                 settings=None):
        self.registry = registry
        self.frontier = frontier
        self.settings = settings
        self._cycles: List[DiscoveryCycle] = []
        self._source_methods: Dict[str, int] = defaultdict(int)  # method -> success count
        self._source_yield: Dict[UUID, float] = {}  # source_id -> yield score

    def run_cycle(self, seed_sources: List[Source],
                  max_generations: int = 3,
                  max_new_urls: int = 10000) -> DiscoveryResult:
        """Run a single recursive discovery cycle.

        Args:
            seed_sources: Initial sources to expand from
            max_generations: Maximum discovery generations to explore
            max_new_urls: Maximum new URLs to add in this cycle

        Returns:
            DiscoveryResult with metrics for this cycle
        """
        cycle = DiscoveryCycle(UUID(int=0))  # Will be assigned
        cycle.seed_sources = len(seed_sources)

        current_generation_sources = list(seed_sources)
        all_discovered_urls: Set[str] = set()

        for generation in range(max_generations):
            logger.info(f"Discovery generation {generation + 1}/{max_generations}: "
                        f"processing {len(current_generation_sources)} sources")

            next_generation_sources: List[Source] = []
            generation_urls = 0

            for source in current_generation_sources:
                # Discover new URLs from this source
                discovered = self._discover_from_source(source, max_new_urls // max_generations)

                for url_candidate in discovered:
                    if url_candidate.url not in all_discovered_urls:
                        added = self.frontier.add(url_candidate)
                        if added:
                            all_discovered_urls.add(url_candidate.url)
                            generation_urls += 1
                        else:
                            cycle.duplicate_urls += 1

                # Try to validate promising candidate domains
                validated = self._attempt_validation(source)
                if validated:
                    next_generation_sources.append(validated)

            cycle.candidate_urls += generation_urls
            current_generation_sources = next_generation_sources

            if not current_generation_sources:
                logger.info("No new sources to expand, ending cycle early")
                break

        # Populate cycle metrics
        cycle.candidate_domains = len(self.registry._domains)
        cycle.validated_domains = len([
            s for s in self.registry._sources.values()
            if s.source_type == SourceType.VALIDATED_DOMAIN
        ])
        cycle.useful_sources = len([
            s for s in self.registry._sources.values()
            if s.source_type == SourceType.USEFUL_SOURCE
        ])
        cycle.active_sources = len([
            s for s in self.registry._sources.values()
            if s.status == SourceStatus.ACTIVE
        ])
        cycle.qualified_demand_sources = len([
            s for s in self.registry._sources.values()
            if s.source_type == SourceType.QUALIFIED_DEMAND_SOURCE
        ])

        self._cycles.append(cycle)

        # Compute derived metrics
        total_urls = cycle.candidate_urls
        unique_rate = 1.0 - (cycle.duplicate_urls / max(total_urls, 1))
        diversity_score = self._compute_source_diversity()

        result = DiscoveryResult(
            cycle_id=cycle.cycle_id,
            seed_sources=cycle.seed_sources,
            candidate_urls=cycle.candidate_urls,
            candidate_domains=cycle.candidate_domains,
            validated_domains=cycle.validated_domains,
            useful_sources=cycle.useful_sources,
            active_sources=cycle.active_sources,
            qualified_demand_sources=cycle.qualified_demand_sources,
            new_opportunities=cycle.new_opportunities,
            duplicate_rate=1.0 - unique_rate,
            source_diversity_score=diversity_score,
            expansion_rate=self._compute_expansion_rate(),
            marginal_yield=self._compute_marginal_yield(),
            timestamp=utc_now(),
        )

        logger.info(f"Discovery cycle complete: {cycle.candidate_urls} URLs, "
                    f"{cycle.validated_domains} validated domains, "
                    f"{cycle.useful_sources} useful sources")
        return result

    def _discover_from_source(self, source: Source, limit: int) -> List[URLCandidate]:
        """Discover new URLs from a source.

        This is an abstract method that should be implemented by specific
        discovery methods (sitemap, RSS, link following, DNS, CT, etc.).
        The base implementation returns an empty list and should be extended.
        """
        # Base implementation: no discovery method registered
        # Subclasses or plugin adapters implement specific methods
        logger.debug(f"No discovery method registered for source {source.id}")
        return []

    def _attempt_validation(self, source: Source) -> Optional[Source]:
        """Attempt to validate a source and promote it if valid."""
        # Base implementation: validation is performed by separate validator
        # This engine tracks yield and decides which sources to expand
        if source.source_type == SourceType.CANDIDATE_DOMAIN:
            # Promote to validated if there's evidence
            # Actual validation performed by SourceValidation component
            return source
        return None

    def register_discovery_method(self, method_name: str, handler):
        """Register a discovery method handler.

        Handler should accept (source, limit) and return List[URLCandidate].
        """
        self._discovery_methods[method_name] = handler
        logger.info(f"Registered discovery method: {method_name}")

    def _compute_source_diversity(self) -> float:
        """Compute source diversity score (0-1, higher = more diverse)."""
        if not self.registry._domains:
            return 0.0

        # Count TLDs and registrars as diversity proxy
        tlds = set()
        for domain in self.registry._domains:
            parts = domain.split(".")
            if len(parts) >= 2:
                tlds.add(parts[-1])

        # Normalize by expected maximum (approx 1500 TLDs)
        return min(len(tlds) / 1500.0, 1.0)

    def _compute_expansion_rate(self) -> float:
        """Compute expansion rate (new sources per cycle)."""
        if len(self._cycles) < 2:
            return 0.0
        recent = self._cycles[-1]
        previous = self._cycles[-2]
        if previous.candidate_domains == 0:
            return 0.0
        return (recent.candidate_domains - previous.candidate_domains) / previous.candidate_domains

    def _compute_marginal_yield(self) -> float:
        """Compute marginal yield per discovery generation."""
        if not self._cycles:
            return 0.0
        latest = self._cycles[-1]
        if latest.candidate_urls == 0:
            return 0.0
        return latest.qualified_demand_sources / latest.candidate_urls

    def get_high_value_sources(self, min_yield: float = 0.1,
                               limit: int = 100) -> List[Source]:
        """Get sources with the highest expected value for expansion."""
        return self.registry.get_high_yield_sources(min_yield=min_yield, limit=limit)

    def get_cycle_history(self) -> List[DiscoveryCycle]:
        """Get history of all discovery cycles."""
        return list(self._cycles)
