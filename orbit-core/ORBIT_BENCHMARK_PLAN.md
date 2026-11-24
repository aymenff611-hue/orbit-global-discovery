# ORBIT Benchmark Plan

**Version:** 0.1.0  
**Status:** Planned (not yet fully executed)

---

## 1. Overview

ORBIT includes a dedicated benchmark suite that measures complete system performance across all required categories. Every numerical claim is classified as exactly one of:

1. **Published Benchmark** — from published literature/vendor documentation
2. **Measured ORBIT Benchmark** — actually measured on ORBIT system
3. **Engineering Target** — design target, not yet measured
4. **Conditional Scale Target** — achievable only under specific conditions
5. **Unknown / Not Yet Measurable** — cannot be measured with current infrastructure

---

## 2. Required Benchmark Categories

| Category | Metrics | Classification |
|----------|---------|----------------|
| Source discovery | URLs discovered per second, domains discovered per day | Measured ORBIT Benchmark (when tested) |
| Source validation | Validation accuracy, false positive rate | Measured ORBIT Benchmark |
| Source expansion | New sources per generation, expansion rate | Measured ORBIT Benchmark |
| Unique source yield | Unique domains per crawl batch | Measured ORBIT Benchmark |
| URL discovery | URLs discovered per second | Measured ORBIT Benchmark |
| Crawling | Pages fetched per second, bytes per second | Measured ORBIT Benchmark |
| Extraction | Pages extracted per second, extraction success rate | Measured ORBIT Benchmark |
| Browser rendering | Rendering overhead (ms per page), success rate | Measured ORBIT Benchmark |
| Duplicate detection | Precision, recall | Measured ORBIT Benchmark (target ≥99.99%) |
| Entity resolution | Precision, recall | Measured ORBIT Benchmark (target ≥99%/≥95%) |
| Search latency | p50, p95, p99 latency | Measured ORBIT Benchmark |
| Indexing throughput | Items indexed per second | Measured ORBIT Benchmark |
| Knowledge graph | Entities/relationships processed per second | Measured ORBIT Benchmark |
| Demand detection | Precision, recall, F1 | Measured ORBIT Benchmark (target ≥90%/≥80%) |
| Buyer intent | Precision, recall, calibration | Measured ORBIT Benchmark |
| Opportunity qualification | Opportunities qualified per second | Measured ORBIT Benchmark |
| Evidence completeness | % of opportunities with traceable evidence | Measured ORBIT Benchmark (target 100%) |
| Competition scoring | Score accuracy, coverage disclosure | Measured ORBIT Benchmark |
| Multilingual accuracy | Language identification accuracy per language | Measured ORBIT Benchmark |
| Resource consumption | CPU, memory, disk, network per million pages | Measured ORBIT Benchmark |
| Cost efficiency | Cost per million pages, cost per validated source | Engineering Target |
| Failure recovery | Recovery time, data loss | Measured ORBIT Benchmark |
| Long-running stability | 24h, 7d, 30d, 90d stability | Engineering Target |

---

## 3. Benchmark Methodology

### 3.1 Test Environment

- Controlled test environment (synthetic workloads)
- No testing against public websites without authorization
- Synthetic pages with known characteristics
- Local infrastructure (single node for initial benchmarks)

### 3.2 Measurement Procedure

1. Warm up the system
2. Run benchmark for fixed duration or fixed workload
3. Collect metrics (throughput, latency, errors, resource usage)
4. Calculate statistics (mean, median, p95, p99)
5. Classify results according to claim type
6. Document conditions and limitations

### 3.3 Benchmark Durations

- 24 hours: Initial validation
- 7 days: Production baseline stability
- 30 days: Long-running stability
- 90 days: Extended stability (where resources permit)

---

## 4. Discovery Expansion Experiments

### 4.1 Test Configurations

| Test Type | Seed Set Size | Characteristics |
|-----------|---------------|-----------------|
| Small seed | 10-50 domains | Manual selection |
| Medium seed | 100-500 domains | Diverse TLDs |
| Diverse seed | 500-1000 domains | Multiple countries, languages |
| Regional seed | 100-500 domains | Specific region |
| Industry-specific | 100-500 domains | Specific industry |
| Multilingual | 200-1000 domains | Multiple languages |
| Hidden-source | 50-200 domains | Obscure, niche sources |

### 4.2 Metrics Measured

- New candidate sources
- New validated sources
- New useful sources
- Unique domains
- Discovery depth
- Expansion rate
- Duplicate rate
- Source diversity score
- Marginal yield per generation
- Saturation and diminishing returns

### 4.3 Test Timeline

- 24 hours: Initial expansion measurement
- 7 days: Medium-term expansion
- 30 days: Long-term expansion (where resources permit)
- 90 days: Extended expansion (where resources permit)

**Never confuse repeatedly finding the same websites with genuine network expansion.**

---

## 5. Demand Intelligence Evaluation

### 5.1 Labeled Evaluation Dataset

Contains manually labeled examples:

- Genuine purchase requests
- Service requests
- General discussions with no buying intent
- Spam
- Old requests
- Fulfilled requests
- Fake requests
- Ambiguous intent
- Duplicate requests
- Multilingual requests
- Requests with missing budget or identity information

### 5.2 Metrics Measured

- Precision
- Recall
- F1 score
- Calibration
- Evidence quality

**Every important opportunity must be traceable to its original public evidence.**

---

## 6. Load and Resilience Tests

| Test | Description |
|------|-------------|
| Increasing worker counts | Scale from 1 to N workers |
| Queue backlogs | Test behavior with deep queues |
| Network interruptions | Simulate network failures |
| Slow websites | Test with delayed responses |
| Malformed pages | Test with invalid HTML |
| Browser failures | Test browser crash recovery |
| Database interruptions | Test DB failover |
| Indexing failures | Test index recovery |
| Worker crashes | Test worker failure recovery |
| Duplicate message delivery | Test idempotency |
| Recovery and replay | Test replay from dead-letter |
| Resource exhaustion | Test memory/disk exhaustion |

**Do not run extreme targets against public websites without authorization and a controlled operating plan.**

---

## 7. Benchmark Report Output

### 7.1 Machine-Readable Report

JSON format with all metrics, classifications, conditions, and timestamps.

### 7.2 Human-Readable Report

Markdown report with tables, claim type definitions, and recommendations.

### 7.3 Report Location

- `ORBIT_BENCHMARK_RESULTS.md` — Human-readable results
- `benchmarks/results.json` — Machine-readable results

---

## 8. Current Benchmark Status

| Category | Status | Classification |
|----------|--------|----------------|
| Source discovery | Not yet measured | Engineering Target |
| Crawling | Not yet measured | Engineering Target |
| Extraction | Not yet measured | Engineering Target |
| Duplicate detection | Not yet measured | Engineering Target |
| Entity resolution | Not yet measured | Engineering Target |
| Demand detection | Not yet measured | Engineering Target |
| Evidence completeness | Not yet measured | Engineering Target |
| Resource consumption | Not yet measured | Engineering Target |
| Failure recovery | Not yet measured | Engineering Target |

---

**End of ORBIT Benchmark Plan**
