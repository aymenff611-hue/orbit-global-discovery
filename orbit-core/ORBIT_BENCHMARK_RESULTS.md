# ORBIT Benchmark Results

**Version:** 0.1.0  
**Status:** Initial — No benchmarks measured yet  
**Classification:** All targets are Engineering Targets (not yet measured)

---

## 1. Overview

This document records benchmark results as they are measured. Initially, all targets are classified as Engineering Targets. As benchmarks are executed, results will be moved to Measured ORBIT Benchmark classification with actual values.

**Rule:** No benchmark result is reported as achieved until tests prove it.

---

## 2. Current Benchmark Status (All Unmeasured)

| Category | Metric | Target Value | Current Status | Classification |
|----------|--------|--------------|----------------|----------------|
| Source discovery | URLs discovered/sec | — | Not measured | Engineering Target |
| Source discovery | Domains discovered/day | — | Not measured | Engineering Target |
| Source validation | Validation accuracy | — | Not measured | Engineering Target |
| Source expansion | New sources/generation | — | Not measured | Engineering Target |
| Unique source yield | Unique domains/crawl batch | — | Not measured | Engineering Target |
| Crawling | Pages fetched/sec | — | Not measured | Engineering Target |
| Crawling | Pages/day (production) | 1,000,000 | Not measured | Engineering Target |
| Crawling | Pages/day (max design) | 100,000,000 | Not measured | Conditional Scale Target |
| Extraction | Pages extracted/sec | — | Not measured | Engineering Target |
| Browser rendering | Overhead per page (ms) | — | Not measured | Engineering Target |
| Duplicate detection | Precision | ≥ 99.99% | Not measured | Engineering Target |
| Entity resolution | Precision | ≥ 99% | Not measured | Engineering Target |
| Entity resolution | Recall | ≥ 95% | Not measured | Engineering Target |
| Search latency | p95 latency (ms) | — | Not measured | Engineering Target |
| Indexing | Items indexed/sec | — | Not measured | Engineering Target |
| Knowledge graph | Entities processed/sec | — | Not measured | Engineering Target |
| Demand detection | Precision@100 | ≥ 90% | Not measured | Engineering Target |
| Demand detection | Recall | ≥ 80% | Not measured | Engineering Target |
| Opportunity qualification | Opportunities/sec | — | Not measured | Engineering Target |
| Evidence completeness | % with traceable evidence | 100% | Not measured | Engineering Target |
| Competition scoring | Coverage disclosure | Required | Not measured | Engineering Target |
| Multilingual accuracy | Per-language accuracy | — | Not measured | Engineering Target |
| Resource consumption | CPU per million pages | — | Not measured | Engineering Target |
| Resource consumption | Memory per million pages | — | Not measured | Engineering Target |
| Cost efficiency | Cost per million pages | — | Not measured | Engineering Target |
| Cost efficiency | Cost per validated source | — | Not measured | Engineering Target |
| Failure recovery | Recovery time (sec) | — | Not measured | Engineering Target |
| Long-running stability | 24h stability | Required | Not measured | Engineering Target |
| Long-running stability | 7d stability | Required | Not measured | Engineering Target |
| Long-running stability | 30d stability | Required | Not measured | Engineering Target |
| Long-running stability | 90d stability | Required | Not measured | Engineering Target |

---

## 3. Benchmark Execution Plan

Benchmarks will be executed in the following order:

### Phase 1: Single-Node Validation (Immediate)

- Source discovery throughput (synthetic URLs)
- Crawling throughput (local test server)
- Extraction throughput (sample HTML pages)
- Duplicate detection precision (synthetic corpus)
- Entity resolution precision/recall (labeled dataset)

### Phase 2: Multi-Node Scale Testing (When cluster available)

- Crawling at 100K, 1M, 10M pages/day
- Concurrent worker scaling (1 to 100 workers)
- Queue latency under load
- Failure recovery testing

### Phase 3: Production-Scale Validation (When authorized)

- 100M pages/day at maximum design envelope
- 1B candidate URLs/day evaluation
- 90-day long-running stability

---

## 4. Benchmark Tooling

The benchmark suite is implemented in `benchmarks/benchmark_suite.py`. It provides:

- `record()` — Record a metric with claim type classification
- Category-specific benchmark methods
- JSON export (`to_json()`)
- Human-readable report (`generate_human_readable_report()`)
- Claim type classification for every metric

### 4.1 Example Usage

```python
from benchmarks.benchmark_suite import BenchmarkSuite, ClaimType

suite = BenchmarkSuite()

suite.benchmark_crawling_throughput(
    pages_fetched=10000,
    duration_seconds=3600,
)

suite.record(
    name="duplicate_detection_precision",
    category="deduplication",
    value=0.9999,
    unit="ratio",
    claim_type=ClaimType.ENGINEERING_TARGET,
    notes="Target: >= 99.99%",
)

print(suite.generate_human_readable_report())
suite.to_json("benchmarks/results.json")
```

---

## 5. Claim Type Definitions

| # | Classification | Meaning |
|---|---------------|---------|
| 1 | Published Benchmark | From published literature or vendor documentation |
| 2 | Measured ORBIT Benchmark | Actually measured on ORBIT system |
| 3 | Engineering Target | Design target, not yet measured |
| 4 | Conditional Scale Target | Achievable only under specific conditions |
| 5 | Unknown / Not Yet Measurable | Cannot be measured with current infrastructure |

**Never mix these categories.**

---

## 6. Results Archive

When benchmarks are executed, results will be stored here:
- `benchmarks/results.json` — Machine-readable results
- This document — Human-readable summary

---

**End of ORBIT Benchmark Results**
