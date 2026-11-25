"""ORBIT Adaptive Discovery Engine.

Feedback-driven system that:
- Identifies promising sources
- Measures source yield and quality
- Discovers related sources
- Tests new discovery paths
- Estimates expected value
- Allocates crawling and research resources dynamically
- Reduces resources assigned to unproductive sources
- Increases resources assigned to high-yield sources within permitted limits
- Detects new source categories
- Avoids repeatedly rediscovering the same sources
- Tracks whether expansion is producing genuinely new useful sources

Uses measurable exploration/exploitation strategies rather than arbitrary agent decisions.
"""

import logging
import math
from typing import Optional, List, Dict, Any, Set, Tuple
from datetime import datetime, timezone, timedelta
from uuid import UUID
from dataclasses import dataclass, field
from collections import defaultdict

from core.models import Source, SourceType, SourceStatus, DiscoveryResult, utc_now
from discovery.source_registry import SourceRegistry
from discovery.url_frontier import URLFrontier
from discovery.recursive_discovery import RecursiveDiscoveryEngine

logger = logging.getLogger("orbit.core.adaptive_discovery")


@dataclass
class SourceAllocation:
    """Resource allocation for a source."""
    source_id: UUID
    source_domain: str
    crawl_budget: int  # pages per day
    concurrency: int
    priority_score: float
    yield_score: float
    last_evaluated: datetime


@dataclass
class DiscoveryPath:
    """A discovery path with measured performance."""
    path_id: str
    method: str  # sitemap, rss, dns, ct, link, etc.
    sources_tested: int
    sources_validated: int
    sources_useful: int
    opportunities_found: int
    avg_yield: float
    cost_per_source: float
    last_used: datetime


class AdaptiveDiscoveryEngine:
    """Feedback-driven adaptive discovery engine.

    Uses exploration/exploitation strategies (epsilon-greedy, UCB) to
    allocate resources between known high-yield sources and new discovery paths.
    """

    def __init__(self, registry: SourceRegistry, frontier: URLFrontier,
                 discovery_engine: RecursiveDiscoveryEngine,
                 settings=None):
        self.registry = registry
        self.frontier = frontier
        self.discovery_engine = discovery_engine
        self.settings = settings

        # Exploration/exploitation parameters
        self.exploration_weight = settings.adaptive_exploration_weight if settings else 0.3
        self.exploitation_weight = settings.adaptive_exploitation_weight if settings else 0.7
        self.min_yield_threshold = settings.adaptive_min_yield_threshold if settings else 0.05
        self.rebalance_interval = settings.adaptive_rebalance_interval_seconds if settings else 300

        # Source performance tracking
        self._source_performance: Dict[UUID, Dict[str, Any]] = {}
        self._path_performance: Dict[str, DiscoveryPath] = {}
        self._allocations: Dict[UUID, SourceAllocation] = {}

        # Discovery path methods
        self._discovery_methods: Dict[str, callable] = {}

        # Stats
        self._stats = {
            "rebalances": 0,
            "sources_promoted": 0,
            "sources_demoted": 0,
            "paths_tested": 0,
            "exploration_decisions": 0,
            "exploitation_decisions": 0,
        }

        self._last_rebalance = datetime.now(timezone.utc)

    def register_discovery_method(self, method_name: str, handler: callable):
        """Register a discovery method handler."""
        self._discovery_methods[method_name] = handler
        self._path_performance[method_name] = DiscoveryPath(
            path_id=method_name,
            method=method_name,
            sources_tested=0,
            sources_validated=0,
            sources_useful=0,
            opportunities_found=0,
            avg_yield=0.0,
            cost_per_source=0.0,
            last_used=utc_now(),
        )
        logger.info(f"Registered discovery method: {method_name}")

    def evaluate_source_performance(self, source_id: UUID) -> Dict[str, Any]:
        """Evaluate the performance of a source.

        Returns metrics including yield, quality, freshness, and cost-effectiveness.
        """
        source = self.registry.get_source(source_id)
        if not source:
            return {}

        perf = self._source_performance.get(source_id, {
            "crawls": 0,
            "successes": 0,
            "failures": 0,
            "opportunities": 0,
            "pages_crawled": 0,
            "total_cost": 0.0,
            "last_yield": 0.0,
        })

        yield_score = source.yield_score
        quality_score = source.quality_score
        freshness_score = source.freshness_score

        # Cost-effectiveness: opportunities per crawl
        cost_effectiveness = source.opportunities_found / max(source.crawl_count, 1)

        def _enum_val(x):
            return x.value if hasattr(x, 'value') else x

        return {
            "source_id": str(source_id),
            "domain": source.domain,
            "source_type": _enum_val(source.source_type),
            "status": _enum_val(source.status),
            "yield_score": yield_score,
            "quality_score": quality_score,
            "freshness_score": freshness_score,
            "crawl_count": source.crawl_count,
            "opportunities_found": source.opportunities_found,
            "cost_effectiveness": cost_effectiveness,
            "failure_rate": perf["failures"] / max(perf["crawls"], 1),
            "last_crawled": source.last_crawled.isoformat() if source.last_crawled else None,
        }

    def compute_source_priority(self, source_id: UUID) -> float:
        """Compute priority score for a source (0-1, higher = more priority).

        Combines yield, quality, freshness, and exploration bonus.
        """
        source = self.registry.get_source(source_id)
        if not source:
            return 0.0

        perf = self.evaluate_source_performance(source_id)

        # Exploitation component: known yield
        exploitation = (
            perf.get("yield_score", 0) * 0.4 +
            perf.get("quality_score", 0) * 0.3 +
            perf.get("freshness_score", 0) * 0.2 +
            min(perf.get("cost_effectiveness", 0), 1.0) * 0.1
        )

        # Exploration component: uncertainty bonus for rarely crawled sources
        crawl_count = source.crawl_count
        exploration_bonus = 1.0 / (1.0 + math.log1p(crawl_count)) if crawl_count > 0 else 1.0

        # Combined score
        priority = (self.exploitation_weight * exploitation +
                    self.exploration_weight * exploration_bonus)

        return min(priority, 1.0)

    def allocate_resources(self, total_budget: int = 1000) -> List[SourceAllocation]:
        """Allocate crawling resources across sources using adaptive strategy.

        Allocation is based only on persisted, observed source performance:
        yield_score (opportunities per crawl), quality_score, freshness_score,
        and cost-effectiveness. No artificial or manually assigned values.

        Args:
            total_budget: Total pages per day budget across all sources

        Returns:
            List of SourceAllocation objects
        """
        now = utc_now()

        # Check if rebalance is needed
        if (now - self._last_rebalance).total_seconds() < self.rebalance_interval:
            return list(self._allocations.values())

        # Consider sources at all lifecycle stages that have been crawled
        # at least once, so yield is based on real observed performance.
        all_sources = list(self.registry._sources.values())
        candidate_sources = [
            s for s in all_sources
            if s.crawl_count > 0 or s.discovery_generation == 0
        ]

        if not candidate_sources:
            self._last_rebalance = now
            return []

        # Compute priority for each source
        source_priorities = []
        for source in candidate_sources:
            priority = self.compute_source_priority(source.id)
            source_priorities.append((source, priority))

        # Sort by priority (descending)
        source_priorities.sort(key=lambda x: x[1], reverse=True)

        # Allocate budget proportionally to priority
        total_priority = sum(p for _, p in source_priorities)
        if total_priority == 0:
            # Equal allocation
            per_source = total_budget // len(source_priorities) if source_priorities else 0
            allocations = [
                SourceAllocation(
                    source_id=s.id,
                    source_domain=s.domain or "",
                    crawl_budget=per_source,
                    concurrency=max(1, per_source // 100),
                    priority_score=p,
                    yield_score=s.yield_score,
                    last_evaluated=now,
                )
                for s, p in source_priorities
            ]
        else:
            allocations = []
            remaining_budget = total_budget
            for i, (source, priority) in enumerate(source_priorities):
                if i == len(source_priorities) - 1:
                    # Last source gets remaining budget
                    budget = remaining_budget
                else:
                    budget = int(total_budget * priority / total_priority)
                    remaining_budget -= budget

                budget = max(1, budget)  # Minimum 1 page
                concurrency = max(1, budget // 50)  # 1 concurrent per 50 pages

                allocations.append(SourceAllocation(
                    source_id=source.id,
                    source_domain=source.domain or "",
                    crawl_budget=budget,
                    concurrency=concurrency,
                    priority_score=priority,
                    yield_score=source.yield_score,
                    last_evaluated=now,
                ))

        self._allocations = {a.source_id: a for a in allocations}
        self._last_rebalance = now
        self._stats["rebalances"] += 1

        logger.info(f"Allocated resources to {len(allocations)} sources, total budget={total_budget}")
        return allocations

    def record_discovery_path_result(self, method: str, sources_tested: int,
                                       sources_validated: int, sources_useful: int,
                                       opportunities_found: int, cost: float):
        """Record the result of testing a discovery path."""
        path = self._path_performance.get(method)
        if not path:
            path = DiscoveryPath(
                path_id=method,
                method=method,
                sources_tested=0,
                sources_validated=0,
                sources_useful=0,
                opportunities_found=0,
                avg_yield=0.0,
                cost_per_source=0.0,
                last_used=utc_now(),
            )
            self._path_performance[method] = path

        path.sources_tested += sources_tested
        path.sources_validated += sources_validated
        path.sources_useful += sources_useful
        path.opportunities_found += opportunities_found
        path.last_used = utc_now()

        if path.sources_tested > 0:
            path.avg_yield = path.sources_useful / path.sources_tested
            path.cost_per_source = cost / path.sources_tested

        self._stats["paths_tested"] += 1
        logger.info(f"Discovery path '{method}': {sources_useful}/{sources_tested} useful, "
                    f"{opportunities_found} opportunities")

    def get_best_discovery_paths(self, limit: int = 10) -> List[DiscoveryPath]:
        """Get the best performing discovery paths by yield."""
        paths = list(self._path_performance.values())
        paths.sort(key=lambda p: p.avg_yield, reverse=True)
        return paths[:limit]

    def should_explore(self) -> bool:
        """Decide whether to explore new paths or exploit known ones (epsilon-greedy)."""
        import random
        return random.random() < self.exploration_weight

    def select_discovery_method(self) -> Optional[str]:
        """Select a discovery method using exploration/exploitation strategy.

        Returns method name or None if no methods registered.
        """
        if not self._discovery_methods:
            return None

        if self.should_explore():
            # Explore: try a less-tested method
            self._stats["exploration_decisions"] += 1
            # Select method with fewest tests
            best_method = min(
                self._path_performance.values(),
                key=lambda p: p.sources_tested
            )
            return best_method.method
        else:
            # Exploit: use best performing method
            self._stats["exploitation_decisions"] += 1
            best_paths = self.get_best_discovery_paths(limit=1)
            if best_paths:
                return best_paths[0].method
            # Fallback to first available
            return list(self._discovery_methods.keys())[0]

    def detect_source_categories(self) -> Dict[str, List[str]]:
        """Detect new source categories based on domain patterns.

        Groups sources by TLD, country, and content patterns to identify
        new categories of sources.
        """
        categories = defaultdict(list)

        for source in self.registry._sources.values():
            if not source.domain:
                continue

            # Categorize by TLD
            parts = source.domain.split(".")
            if len(parts) >= 2:
                tld = parts[-1]
                categories[f"tld:{tld}"].append(source.domain)

            # Categorize by country code if available
            if source.country_code:
                categories[f"country:{source.country_code}"].append(source.domain)

            # Categorize by language if available
            if source.language:
                categories[f"language:{source.language}"].append(source.domain)

        return dict(categories)

    def track_expansion_effectiveness(self, cycle_results: List[DiscoveryResult]) -> Dict[str, Any]:
        """Track whether expansion is producing genuinely new useful sources.

        Analyzes discovery cycles to measure:
        - Marginal yield per generation
        - Saturation and diminishing returns
        - Source diversity
        - Duplicate rate
        """
        if not cycle_results:
            return {"status": "no_data"}

        latest = cycle_results[-1]
        analysis = {
            "total_cycles": len(cycle_results),
            "latest_cycle": {
                "candidate_urls": latest.candidate_urls,
                "validated_domains": latest.validated_domains,
                "useful_sources": latest.useful_sources,
                "qualified_demand_sources": latest.qualified_demand_sources,
                "duplicate_rate": latest.duplicate_rate,
                "source_diversity_score": latest.source_diversity_score,
                "marginal_yield": latest.marginal_yield,
            },
            "saturation_analysis": self._analyze_saturation(cycle_results),
            "diversity_trend": self._analyze_diversity_trend(cycle_results),
            "recommendation": "",
        }

        # Generate recommendation
        if latest.marginal_yield < self.min_yield_threshold:
            analysis["recommendation"] = "Marginal yield below threshold - consider new discovery methods"
        elif latest.duplicate_rate > 0.5:
            analysis["recommendation"] = "High duplicate rate - improve deduplication or explore new paths"
        elif latest.source_diversity_score < 0.3:
            analysis["recommendation"] = "Low source diversity - expand to new TLDs and regions"
        else:
            analysis["recommendation"] = "Discovery expansion is healthy"

        self._stats["sources_promoted"] = latest.useful_sources
        return analysis

    def _analyze_saturation(self, results: List[DiscoveryResult]) -> Dict[str, Any]:
        """Analyze saturation and diminishing returns."""
        if len(results) < 2:
            return {"status": "insufficient_data"}

        # Check if validated domains are growing slower over time
        recent = results[-3:] if len(results) >= 3 else results
        growth_rates = []
        for i in range(1, len(recent)):
            prev = recent[i-1].validated_domains
            curr = recent[i].validated_domains
            if prev > 0:
                growth_rates.append((curr - prev) / prev)

        avg_growth = statistics.mean(growth_rates) if growth_rates else 0
        return {
            "avg_growth_rate": avg_growth,
            "saturating": avg_growth < 0.05,  # Less than 5% growth
            "trend": "declining" if avg_growth < 0.02 else "stable" if avg_growth < 0.1 else "growing",
        }

    def _analyze_diversity_trend(self, results: List[DiscoveryResult]) -> Dict[str, Any]:
        """Analyze source diversity trend."""
        if len(results) < 2:
            return {"status": "insufficient_data"}

        diversity_scores = [r.source_diversity_score for r in results]
        return {
            "current": diversity_scores[-1],
            "trend": "improving" if diversity_scores[-1] > diversity_scores[0] else "declining",
            "min": min(diversity_scores),
            "max": max(diversity_scores),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get adaptive discovery engine statistics."""
        return dict(self._stats)

    def get_allocations(self) -> List[SourceAllocation]:
        """Get current resource allocations."""
        return list(self._allocations.values())
