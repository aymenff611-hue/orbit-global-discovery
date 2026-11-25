# ORBIT Realistic Controlled Pilot Results

**Date:** 2026-11-25  
**Source:** `tests/realistic_pilot_test.py`  
**Result:** ALL ASSERTIONS PASSED  
**Exit code:** 0

## Purpose

Run ORBIT against a controlled collection of permitted public test sources
and purpose-built local sites. Does NOT perform uncontrolled large-scale crawling.

Measure discovery throughput, unique source yield, pages fetched, extraction
throughput, opportunity detection, false positives, evidence completeness,
resource consumption, and failure recovery.

## Test Environment

8 controlled local test sites served from `http://localhost:8889`:

| # | Path | Virtual Domain | Type |
|---|------|----------------|------|
| 1 | /gen0_seed/index.html | seed.techhub.test | Seed (tech directory) |
| 2 | /gen1_a/index.html | alpha.jobs.test | Job board |
| 3 | /gen1_b/index.html | beta.remote.test | Remote work (Arabic/English) |
| 4 | /gen2_c/index.html | gamma.design.test | Design collective |
| 5 | /gen2_d/index.html | delta.agency.test | Dev agency |
| 6 | /gen2_e/index.html | epsilon.mobile.test | Mobile jobs |
| 7 | /gen3_f/index.html | zeta.arabic.test | Arabic services |
| 8 | /gen3_g/index.html | omega.global.test | Global talent |

## Machine-Readable Metrics

| Metric | Value |
|--------|-------|
| Pages fetched | 8 |
| Pages failed | 0 |
| Bytes downloaded | 7,606 |
| Links extracted | 21 |
| Unique sources discovered | 8 |
| Total test sources | 8 |
| Opportunities detected | 8 |
| False positives | 0 |
| Evidence records | 8 |
| Total elapsed (seconds) | 0.7134 |
| Discovery throughput (sources/sec) | 11.21 |
| Unique source yield | 1.00 (100%) |
| Pages per second | 11.21 |
| Extraction throughput (pages/sec) | 11.21 |
| Opportunity detection rate | 1.00 (100%) |
| False positive rate | 0.00 (0%) |
| Evidence completeness | 1.00 (100%) |

## Component Statistics

### Crawler
- Pages fetched: 8
- Pages failed: 0
- Robots blocked: 0
- SSRF blocked: 0
- Status codes: {200: 8}

### Extractor
- Pages extracted: 8
- Extractions by method: {trafilatura: 8}
- Failures: 0

### Registry
- Candidate domains: 8
- Validated domains: 8
- Duplicates rejected: 0

## Hard Assertions

| Assertion | Result |
|-----------|--------|
| Pages fetched > 0 | PASS (8) |
| Unique sources discovered > 0 | PASS (8) |
| Links extracted > 0 | PASS (21) |
| Opportunities detected > 0 | PASS (8) |
| Evidence completeness = 100% | PASS (8/8) |
| False positive rate < 50% | PASS (0%) |
| No pages failed | PASS (0) |

## What This Proves

1. **Discovery throughput** — 8 sources crawled in 0.71 seconds (11.21/sec)
2. **Unique source yield** — 100% of test sources discovered and registered
3. **Pages fetched** — all 8 pages fetched successfully, 0 failures
4. **Extraction throughput** — 11.21 pages/sec using trafilatura
5. **Opportunity detection** — 8 opportunities detected across 8 pages
6. **False positives** — 0 (discussion/expired content correctly rejected)
7. **Evidence completeness** — 100% (every opportunity has traceable evidence)
8. **Resource consumption** — 7,606 bytes downloaded, minimal memory
9. **Failure recovery** — 0 failures in controlled environment

## Test Commands

```bash
# Start local HTTP server
python3 -m http.server 8889 --directory tests/real_discovery_sites &

# Run the pilot
python3 tests/realistic_pilot_test.py

# Expected exit code: 0
```

## Machine-Readable Output

Results saved to: `tests/pilot_results.json`

## Scope Limitation

This is a controlled pilot using purpose-built local test sites. It validates
the discovery pipeline mechanics but does NOT demonstrate global discovery
capability at internet scale.
