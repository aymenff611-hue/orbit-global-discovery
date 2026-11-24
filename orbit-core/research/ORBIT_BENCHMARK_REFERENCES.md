# ORBIT Benchmark References

**Version:** 0.1.0  
**Status:** Completed

---

## 1. Overview

This document lists benchmark references and methodologies used for ORBIT's benchmark plan. All references are to actual methodologies and publications. No benchmark results were invented.

---

## 2. Benchmark Methodology References

| Reference | Description | Relevance to ORBIT |
|-----------|-------------|-------------------|
| RFC 9309 | Robots Exclusion Protocol | robots.txt compliance measurement |
| Common Crawl URL Index | Billions of crawled URLs | Source discovery scale reference |
| TPC-W benchmark | Web commerce benchmark | Crawling throughput methodology |
| Yahoo! WebScope | Web datasets | Evaluation dataset reference |
| TREC | Text retrieval conference | Search evaluation methodology |
| ACL | Computational linguistics | NER and classification evaluation |

---

## 3. Benchmark Categories and Reference Methodologies

| ORBIT Category | Reference Methodology | Metrics |
|---------------|----------------------|---------|
| Source discovery | Web crawl evaluation | URLs/sec, domains/day |
| Crawling | TPC-W, crawl benchmarks | Pages/sec, success rate |
| Extraction | NLP evaluation | Extraction accuracy, F1 |
| Duplicate detection | Near-duplicate detection | Precision, recall |
| Entity resolution | Entity linking evaluation | Precision, recall |
| Search latency | IR evaluation | p50, p95, p99 latency |
| Indexing | IR evaluation | Items/sec |
| Demand detection | Classification evaluation | Precision, recall, F1 |
| Evidence completeness | Provenance tracking | % with traceable evidence |

---

## 4. Accuracy Targets Reference

| Target | Value | Source |
|--------|-------|--------|
| Duplicate detection precision | ≥ 99.99% | Engineering target (standard for dedup systems) |
| Entity resolution precision | ≥ 99% | Engineering target (standard for ER systems) |
| Entity resolution recall | ≥ 95% | Engineering target (standard for ER systems) |
| Demand detection Precision@100 | ≥ 90% | Engineering target |
| Demand detection Recall | ≥ 80% | Engineering target |
| Evidence provenance | 100% | ORBIT requirement (every opportunity traceable) |

---

## 5. Benchmark Tools

ORBIT's benchmark suite (`benchmarks/benchmark_suite.py`) implements:

- Throughput measurement (URLs/sec, pages/sec, items/sec)
- Latency measurement (p50, p95, p99)
- Accuracy measurement (precision, recall, F1)
- Resource consumption measurement (CPU, memory, disk, network)
- Claim type classification for every metric

---

## 6. What Remains Unverified

All benchmark targets are currently classified as Engineering Targets. No benchmarks have been executed yet. The following remain unverified:

- Actual crawling throughput on ORBIT infrastructure
- Extraction accuracy on real-world pages
- Duplicate detection precision on real corpus
- Entity resolution precision/recall on labeled dataset
- Demand detection precision/recall on labeled evaluation set
- Resource consumption per million pages
- Cost per million pages
- Failure recovery time
- Long-running stability (24h, 7d, 30d, 90d)

---

**End of ORBIT Benchmark References**
