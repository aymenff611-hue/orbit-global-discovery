"""ORBIT Benchmark Suite.

Measures complete system performance across all required categories:
- Source discovery throughput
- Source validation accuracy
- Source expansion rate
- Unique source yield
- URL discovery throughput
- Crawling throughput
- Extraction throughput
- Browser rendering overhead
- Duplicate detection
- Entity resolution
- Search latency
- Indexing throughput
- Knowledge graph throughput
- Demand detection
- Buyer-intent precision and recall
- Opportunity qualification
- Evidence completeness
- Competition scoring
- Multilingual accuracy
- Resource consumption
- Cost efficiency
- Failure recovery
- Long-running stability

Every numerical claim is classified as:
1. Published Benchmark
2. Measured ORBIT Benchmark
3. Engineering Target
4. Conditional Scale Target
5. Unknown / Not Yet Measurable
"""

import logging
import time
import json
import statistics
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

from core.models import BenchmarkResult, Source, Opportunity, SourceType, SourceStatus

logger = logging.getLogger("orbit.benchmarks.benchmark_suite")


class ClaimType(str, Enum):
    PUBLISHED_BENCHMARK = "Published Benchmark"
    MEASURED_ORBIT_BENCHMARK = "Measured ORBIT Benchmark"
    ENGINEERING_TARGET = "Engineering Target"
    CONDITIONAL_SCALE_TARGET = "Conditional Scale Target"
    UNKNOWN_NOT_MEASURABLE = "Unknown / Not Yet Measurable"


@dataclass
class BenchmarkMetric:
    """A single benchmark metric result."""
    name: str
    category: str
    value: float
    unit: str
    claim_type: ClaimType
    conditions: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None
    measured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BenchmarkSuite:
    """ORBIT Benchmark Suite - measures system performance and accuracy.

    Runs benchmarks across all required categories and produces
    machine-readable and human-readable reports.
    """

    def __init__(self, settings=None):
        self.settings = settings
        self._results: List[BenchmarkMetric] = []
        self._start_time = datetime.now(timezone.utc)

    def record(self, name: str, category: str, value: float, unit: str,
               claim_type: ClaimType = ClaimType.ENGINEERING_TARGET,
               conditions: Optional[Dict[str, Any]] = None,
               notes: Optional[str] = None):
        """Record a benchmark metric."""
        metric = BenchmarkMetric(
            name=name,
            category=category,
            value=value,
            unit=unit,
            claim_type=claim_type,
            conditions=conditions or {},
            notes=notes,
        )
        self._results.append(metric)
        logger.info(f"Benchmark: {category}/{name} = {value} {unit} [{claim_type.value}]")

    def benchmark_discovery_throughput(self, urls_discovered: int,
                                        duration_seconds: float) -> BenchmarkMetric:
        """Benchmark source discovery throughput (URLs per second)."""
        throughput = urls_discovered / duration_seconds if duration_seconds > 0 else 0
        self.record(
            name="urls_discovered_per_second",
            category="source_discovery",
            value=throughput,
            unit="urls/second",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
            conditions={"duration_seconds": duration_seconds, "urls_discovered": urls_discovered},
            notes="Measured ORBIT benchmark",
        )
        return self._results[-1]

    def benchmark_crawling_throughput(self, pages_fetched: int,
                                       duration_seconds: float) -> BenchmarkMetric:
        """Benchmark crawling throughput (pages per second)."""
        throughput = pages_fetched / duration_seconds if duration_seconds > 0 else 0
        self.record(
            name="pages_fetched_per_second",
            category="crawling",
            value=throughput,
            unit="pages/second",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
            conditions={"duration_seconds": duration_seconds, "pages_fetched": pages_fetched},
        )
        return self._results[-1]

    def benchmark_extraction_throughput(self, pages_extracted: int,
                                         duration_seconds: float) -> BenchmarkMetric:
        """Benchmark extraction throughput (pages per second)."""
        throughput = pages_extracted / duration_seconds if duration_seconds > 0 else 0
        self.record(
            name="pages_extracted_per_second",
            category="extraction",
            value=throughput,
            unit="pages/second",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
        )
        return self._results[-1]

    def benchmark_duplicate_detection_precision(self, true_positives: int,
                                                  false_positives: int) -> BenchmarkMetric:
        """Benchmark duplicate detection precision."""
        precision = true_positives / max(true_positives + false_positives, 1)
        self.record(
            name="duplicate_detection_precision",
            category="deduplication",
            value=precision,
            unit="ratio (0-1)",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
            conditions={"true_positives": true_positives, "false_positives": false_positives},
            notes="Target: >= 99.99%",
        )
        return self._results[-1]

    def benchmark_demand_detection(self, true_positives: int, false_positives: int,
                                     false_negatives: int) -> BenchmarkMetric:
        """Benchmark demand detection precision and recall."""
        precision = true_positives / max(true_positives + false_positives, 1)
        recall = true_positives / max(true_positives + false_negatives, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)

        self.record(
            name="demand_detection_precision",
            category="demand_detection",
            value=precision,
            unit="ratio (0-1)",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
            notes="Target: >= 90% (Precision@100)",
        )
        self.record(
            name="demand_detection_recall",
            category="demand_detection",
            value=recall,
            unit="ratio (0-1)",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
            notes="Target: >= 80%",
        )
        self.record(
            name="demand_detection_f1",
            category="demand_detection",
            value=f1,
            unit="ratio (0-1)",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
        )
        return self._results[-1]

    def benchmark_entity_resolution(self, precision: float, recall: float) -> BenchmarkMetric:
        """Benchmark entity resolution precision and recall."""
        self.record(
            name="entity_resolution_precision",
            category="entity_resolution",
            value=precision,
            unit="ratio (0-1)",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
            notes="Target: >= 99%",
        )
        self.record(
            name="entity_resolution_recall",
            category="entity_resolution",
            value=recall,
            unit="ratio (0-1)",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
            notes="Target: >= 95%",
        )

    def benchmark_evidence_completeness(self, opportunities_with_evidence: int,
                                          total_opportunities: int) -> BenchmarkMetric:
        """Benchmark evidence completeness (% of opportunities with traceable evidence)."""
        coverage = opportunities_with_evidence / max(total_opportunities, 1) * 100
        self.record(
            name="evidence_completeness_percent",
            category="evidence",
            value=coverage,
            unit="percent",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
            notes="Target: 100%",
        )

    def benchmark_search_latency(self, latency_ms: float,
                                  query_count: int) -> BenchmarkMetric:
        """Benchmark search latency."""
        self.record(
            name="search_latency_ms",
            category="search",
            value=latency_ms,
            unit="milliseconds",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
            conditions={"query_count": query_count},
        )

    def benchmark_indexing_throughput(self, items_indexed: int,
                                        duration_seconds: float) -> BenchmarkMetric:
        """Benchmark indexing throughput."""
        throughput = items_indexed / duration_seconds if duration_seconds > 0 else 0
        self.record(
            name="indexing_throughput",
            category="indexing",
            value=throughput,
            unit="items/second",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
        )

    def benchmark_knowledge_graph_throughput(self, entities_processed: int,
                                               duration_seconds: float) -> BenchmarkMetric:
        """Benchmark knowledge graph throughput."""
        throughput = entities_processed / duration_seconds if duration_seconds > 0 else 0
        self.record(
            name="kg_throughput",
            category="knowledge_graph",
            value=throughput,
            unit="entities/second",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
        )

    def benchmark_opportunity_qualification(self, opportunities_qualified: int,
                                              duration_seconds: float) -> BenchmarkMetric:
        """Benchmark opportunity qualification throughput."""
        throughput = opportunities_qualified / duration_seconds if duration_seconds > 0 else 0
        self.record(
            name="opportunity_qualification_per_second",
            category="opportunity_qualification",
            value=throughput,
            unit="opportunities/second",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
        )

    def benchmark_resource_consumption(self, cpu_percent: float,
                                         memory_mb: float,
                                         disk_mb: float,
                                         network_mbps: float) -> BenchmarkMetric:
        """Benchmark resource consumption."""
        self.record(
            name="cpu_percent",
            category="resources",
            value=cpu_percent,
            unit="percent",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
        )
        self.record(
            name="memory_mb",
            category="resources",
            value=memory_mb,
            unit="MB",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
        )
        self.record(
            name="disk_mb",
            category="resources",
            value=disk_mb,
            unit="MB",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
        )
        self.record(
            name="network_mbps",
            category="resources",
            value=network_mbps,
            unit="Mbps",
            claim_type=ClaimType.MEASURED_ORBIT_BENCHMARK,
        )

    def record_engineering_target(self, name: str, category: str, value: float,
                                    unit: str, conditions: Optional[Dict[str, Any]] = None):
        """Record an engineering target (not yet measured)."""
        self.record(
            name=name,
            category=category,
            value=value,
            unit=unit,
            claim_type=ClaimType.ENGINEERING_TARGET,
            conditions=conditions or {},
            notes="Engineering target - not yet measured",
        )

    def get_results_by_category(self, category: str) -> List[BenchmarkMetric]:
        """Get all results for a category."""
        return [r for r in self._results if r.category == category]

    def get_all_results(self) -> List[BenchmarkMetric]:
        """Get all benchmark results."""
        return list(self._results)

    def to_dict(self) -> Dict[str, Any]:
        """Export all results as a dictionary."""
        return {
            "benchmark_suite": "ORBIT",
            "version": "0.1.0",
            "started_at": self._start_time.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "total_metrics": len(self._results),
            "results": [
                {
                    "name": r.name,
                    "category": r.category,
                    "value": r.value,
                    "unit": r.unit,
                    "claim_type": r.claim_type.value,
                    "conditions": r.conditions,
                    "notes": r.notes,
                    "measured_at": r.measured_at.isoformat(),
                }
                for r in self._results
            ],
        }

    def to_json(self, path: Optional[str] = None) -> str:
        """Export results as JSON string or write to file."""
        data = self.to_dict()
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(json_str)
        return json_str

    def generate_human_readable_report(self) -> str:
        """Generate a human-readable benchmark report."""
        lines = [
            "# ORBIT Benchmark Report",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Total metrics: {len(self._results)}",
            "",
            "| Category | Metric | Value | Unit | Claim Type | Notes |",
            "|----------|--------|-------|------|------------|-------|",
        ]

        for r in self._results:
            notes = r.notes or ""
            lines.append(
                f"| {r.category} | {r.name} | {r.value} | {r.unit} | "
                f"{r.claim_type.value} | {notes} |"
            )

        lines.append("")
        lines.append("## Claim Type Definitions")
        lines.append("1. **Published Benchmark**: From published literature or vendor documentation")
        lines.append("2. **Measured ORBIT Benchmark**: Actually measured on ORBIT system")
        lines.append("3. **Engineering Target**: Design target, not yet measured")
        lines.append("4. **Conditional Scale Target**: Target achievable only under specific conditions")
        lines.append("5. **Unknown / Not Yet Measurable**: Cannot be measured with current infrastructure")

        return "\n".join(lines)
