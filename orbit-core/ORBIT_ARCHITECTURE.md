# ORBIT Architecture

**Version:** 0.1.0  
**Status:** Implemented (ORBIT CORE)

---

## 1. Overview

ORBIT CORE is a horizontally scalable, modular platform for global demand discovery and opportunity intelligence. The architecture separates independent workloads into distinct modules that communicate through durable queues and well-defined APIs.

**Key design principles:**
- Horizontal scaling through independent workers
- Separation of discovery, fetching, rendering, parsing, classification, indexing, and qualification
- Durable queues with backpressure, idempotency, retry, and dead-letter handling
- No single database for all workloads — purpose-built storage per workload
- Configurable, reusable platform (no hardcoded domains, industries, or offers)

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORBIT CONTROL PLANE (API)                        │
│  REST API • Health • Source Mgmt • Discovery • Crawl • Detection   │
└─────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────────┐
│                    DURABLE QUEUE LAYER (Redis)                      │
│  Discovery Queue • Crawl Queue • Extract Queue • Classify Queue    │
│  Index Queue • Graph Queue • Dead Letter • Retry Queue              │
└─────────────────────────────────────────────────────────────────────┘
                              │
┌──────────────┬──────────────┬──────────────┬──────────────┬────────┐
│ DISCOVERY    │ CRAWLING     │ EXTRACTION   │ CLASSIFY     │ GRAPH  │
│              │              │              │              │        │
│ Source       │ HTTP Crawler │ Content      │ Demand       │ Entity │
│ Registry     │ (politness)  │ Extractor    │ Detector     │ Res.   │
│ URL Frontier │ Browser      │ Normalizer   │ Intent       & Rel.  │
│ Recursive    │ Rendering    │ Dedup        │ Classifier   │ KG     │
│ Engine       │ (selective)  │              │              │        │
└──────────────┴──────────────┴──────────────┴──────────────┴────────┘
                              │
┌──────────────┬──────────────┬──────────────┬──────────────┬────────┐
│ STORAGE      │ MONITORING   │ SECURITY     │ WORKFLOW     │ ADAPT. │
│              │              │              │              │        │
│ Hot/Warm/    │ Metrics      │ SSRF         │ Recovery     │ Discovery│
│ Cold Store   │ Health       │ Rate Limit   │ Checkpoint   │ Engine │
│ Data Store   │ Audit Logs   │ URL Validator│ Workflow     │        │
│              │              │ Audit        │ Manager      │        │
└──────────────┴──────────────┴──────────────┴──────────────┴────────┘
```

---

## 3. Module Architecture

### 3.1 Discovery Module

**Components:**
- Source Registry — lifecycle management from candidate URL to qualified demand source
- URL Frontier — distributed, deduplicated, prioritized URL queue with per-host politeness
- Recursive Discovery Engine — feedback-driven expansion across generations
- Source Validation — validates domains and classifies source type

**Data flow:**
```
Seed Sources → Discovery Methods (sitemap, RSS, DNS, CT, links) →
URL Frontier → Crawl Queue → Extraction → Classification →
Opportunity → Knowledge Graph → Adaptive Discovery (re-prioritize)
```

### 3.2 Crawling Module

**Components:**
- HTTP Crawler — async HTTP fetching with retries, backoff, robots.txt
- SSRF Protection — blocks private IPs, localhost, metadata services
- DNS Rebinding Protection — prevents DNS rebinding attacks
- Per-Host Politeness — configurable delay and concurrency per host
- Selective Browser Rendering — only when JavaScript is required

**Design constraint:** Never interpret global concurrency as permission to overload one website. Per-host limits are strictly enforced.

### 3.3 Extraction Module

**Tiered extraction:**
1. Trafilatura — fast, article-optimized
2. Readability-lxml — fallback for complex layouts
3. BeautifulSoup — basic text extraction
4. Browser rendering — for JavaScript-heavy pages (selective)

**Output:** Raw HTML + extracted text + metadata (title, language, links)

### 3.4 Classification Module

**Tiered processing:**
1. Tier 1: Deterministic filters and rules (keywords, patterns)
2. Tier 2: Lightweight classifiers (statistical/ML — extensible)
3. Tier 3: Specialized extraction models (NER for orgs, budgets, dates)
4. Tier 4: Larger reasoning models for ambiguous cases
5. Tier 5: Deep research agents for important opportunities

**Never send every page to an expensive reasoning model.**

### 3.5 Graph Module

**Components:**
- Entity storage (organizations, persons, products, services, communities, websites, opportunities)
- Relationship storage with provenance and temporal validity
- Entity resolution (basic name matching — extensible to ML-based)

### 3.6 Storage Module

**Hot / Warm / Cold tiers:**
- Hot: Active operational data (30 days default)
- Warm: Recent content and searchable evidence (365 days default)
- Cold: Historical archives (7 years default)

**Features:** Compression, deduplication, retention policies, separate raw/extracted/structured

### 3.7 Queue Module

**Features:**
- Durable task queues with priority ordering
- Backpressure when queue depth exceeds thresholds
- Idempotency via idempotency keys
- Exponential backoff retry policies
- Dead-letter handling for permanently failed tasks
- Worker failure recovery (reclaim stale tasks)

### 3.8 API Module (Control Plane)

**FastAPI-based REST API:**
- Source management (CRUD, list, filter)
- URL frontier management (add, pop, stats)
- Discovery cycle execution
- Crawl job submission
- Demand detection
- Opportunity management
- Health checks and metrics
- Benchmark results

### 3.9 Adaptive Discovery Engine

**Exploration/exploitation strategy:**
- Epsilon-greedy selection between exploration (new paths) and exploitation (known high-yield)
- UCB-inspired priority scoring
- Dynamic resource allocation based on source yield
- Source category detection (TLD, country, language patterns)
- Expansion effectiveness tracking (marginal yield, saturation, diversity)

---

## 4. Data Flow

```
1. Seed sources registered in Source Registry
2. Discovery Engine expands sources via registered methods
3. URL Frontier deduplicates and prioritizes URLs
4. Crawler fetches pages (respecting robots.txt, per-host limits)
5. Extractor extracts text and metadata
6. Classifier detects demand and buyer intent (tiered)
7. Qualified opportunities created with evidence provenance
8. Knowledge Graph stores entities and relationships
9. Adaptive Discovery re-prioritizes sources based on yield
10. Monitoring collects metrics and health checks
```

---

## 5. Scaling Strategy

| Component | Scaling Approach |
|-----------|-----------------|
| API | Horizontal (multiple FastAPI workers behind load balancer) |
| Crawler | Horizontal workers, each with own URL Frontier partition |
| URL Frontier | Redis Cluster with sharded URL space |
| Extraction | Worker pool, selective browser rendering on dedicated nodes |
| Classification | Worker pool, GPU optional for tier 3-4 models |
| Storage | Hot: SSD, Warm: HDD/Object, Cold: Object storage (S3/MinIO) |
| Graph | Neo4j cluster or sharded graph |
| Queue | Redis Cluster with multiple queue partitions |

---

## 6. Failure Handling

- Worker crashes → Task reclaimed and re-queued
- Network interruptions → Retry with exponential backoff
- Slow websites → Per-host timeout and backoff
- Malformed pages → Extraction failure logged, pipeline continues
- Database interruptions → Connection retry, failover to replica
- Indexing failures → Dead-letter queue, manual replay

---

## 7. Technology Selection Summary

| Layer | Technology | Reason |
|-------|-----------|--------|
| API | FastAPI | Async, automatic docs, Python native |
| Crawler | httpx + asyncio | High-performance async HTTP |
| Extraction | trafilatura + readability | Best open-source article extraction |
| Queue | Redis | Durable, fast, pub/sub |
| Database | PostgreSQL | Relational operational data |
| Search | Elasticsearch | Full-text search, analytics |
| Graph | Neo4j | Entity-relationship storage |
| Container | Docker + Docker Compose | Reproducible deployment |

**Rejected candidates:** Apache Nutch (too heavy for ORBIT's modular needs), Apache StormCrawler (complex operational overhead), Scrapy (good but ORBIT needs custom distributed frontier), Puppeteer (Chrome-only, heavier than needed for selective rendering)

---

## 8. Integration Points

External projects are integrated through adapters:
- httpx → HTTP crawling adapter
- trafilatura → Content extraction adapter
- Redis → Queue adapter
- Elasticsearch → Search adapter
- Neo4j → Graph adapter

All integrations: pinned versions, license verified, clear adapters, documented data contracts.

---

**End of ORBIT Architecture**
