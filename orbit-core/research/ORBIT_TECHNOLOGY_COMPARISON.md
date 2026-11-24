# ORBIT Technology Comparison

**Version:** 0.1.0  
**Status:** Completed

---

## 1. Technology Selection Summary

ORBIT selected the strongest technically justified combination based on measured suitability, license compatibility, maintenance activity, and integration complexity.

---

## 2. Comparison by Category

### 2.1 Crawling Framework

| Candidate | License | Stars | Maintenance | Scalability | ORBIT Fit | Decision |
|-----------|---------|-------|-------------|-------------|-----------|----------|
| Apache Nutch | Apache-2.0 | ~3K | Moderate | Very High | Low (too heavy) | Rejected |
| Apache StormCrawler | Apache-2.0 | ~500 | Low | High | Low (Storm dep) | Rejected |
| Scrapy | BSD | ~50K | Active | High | Medium (custom frontier needed) | Rejected |
| Crawlee | MIT | ~6K | Active | High | Low (Node.js) | Rejected |
| Katana | MIT | ~4K | Active | Medium | Low (recon-focused) | Rejected |
| **httpx + asyncio** | BSD | ~12K | Active | Very High | **High** | **Selected** |

### 2.2 Content Extraction

| Candidate | License | Stars | Maintenance | Accuracy | ORBIT Fit | Decision |
|-----------|---------|-------|-------------|----------|-----------|----------|
| **Trafilatura** | Apache-2.0 | ~4K | Active | High | **High** | **Selected** |
| Readability-lxml | Apache-2.0 | ~1K | Active | High | High | Selected (fallback) |
| Newspaper3k | Apache-2.0 | ~9K | Low | Medium | Medium | Rejected |
| BeautifulSoup | MIT | ~8K | Active | Basic | High | Selected (fallback) |

### 2.3 Distributed Queue

| Candidate | License | Stars | Maintenance | Scalability | ORBIT Fit | Decision |
|-----------|---------|-------|-------------|-------------|-----------|----------|
| RabbitMQ | MPL | ~12K | Active | High | Medium | Rejected |
| Kafka | Apache-2.0 | ~25K | Active | Very High | Low (overkill) | Rejected |
| **Redis** | BSD | ~60K | Active | High | **High** | **Selected** |
| Pulsar | Apache-2.0 | ~12K | Active | Very High | Low (overkill) | Rejected |

### 2.4 Database

| Candidate | License | Stars | Maintenance | Scalability | ORBIT Fit | Decision |
|-----------|---------|-------|-------------|-------------|-----------|----------|
| **PostgreSQL** | PostgreSQL | ~15K | Active | High | **High** | **Selected** |
| MySQL | GPL | ~12K | Active | High | Medium | Rejected |
| MongoDB | SSPL | ~25K | Active | High | Low (relational needed) | Rejected |

### 2.5 Search Engine

| Candidate | License | Stars | Maintenance | Scalability | ORBIT Fit | Decision |
|-----------|---------|-------|-------------|-------------|-----------|----------|
| **Elasticsearch** | Elastic | ~70K | Active | Very High | **High** | **Selected** |
| Meilisearch | MIT | ~30K | Active | Medium | Medium | Alternative |
| Typesense | MIT | ~10K | Active | Medium | Medium | Alternative |
| OpenSearch | Apache-2.0 | ~6K | Active | High | Medium | Alternative |

### 2.6 Graph Database

| Candidate | License | Stars | Maintenance | Scalability | ORBIT Fit | Decision |
|-----------|---------|-------|-------------|-------------|-----------|----------|
| **Neo4j** | GPLv3 | ~11K | Active | High | **High** | **Selected** |
| JanusGraph | Apache-2.0 | ~3K | Low | High | Medium | Alternative |
| AWS Neptune | Proprietary | N/A | AWS | High | Low (vendor lock-in) | Rejected |

### 2.7 Language Detection

| Candidate | License | Stars | Languages | Accuracy | ORBIT Fit | Decision |
|-----------|---------|-------|-----------|----------|-----------|----------|
| **langdetect** | Apache-2.0 | ~6K | 55+ | Good | **High** | **Selected** |
| polyglot | GPLv3 | ~2K | 100+ | Good | Low (GPL) | Rejected |
| CLD3 | BSD | ~2K | 80+ | High | Medium (C++ dep) | Alternative |

### 2.8 ML / Classification

| Candidate | License | Stars | Maintenance | ORBIT Fit | Decision |
|-----------|---------|-------|-------------|-----------|----------|
| **scikit-learn** | BSD | ~60K | Active | **High** | **Selected** |
| spaCy | MIT | ~25K | Active | Medium | Planned (Tier 3) |
| transformers | Apache-2.0 | ~120K | Active | Medium | Planned (Tier 4) |
| Stanza | Apache-2.0 | ~3K | Active | Medium | Alternative |

### 2.9 API Framework

| Candidate | License | Stars | Async | ORBIT Fit | Decision |
|-----------|---------|-------|-------|-----------|----------|
| **FastAPI** | MIT | ~70K | Yes | **High** | **Selected** |
| Flask | BSD | ~60K | No | Low | Rejected |
| Django | BSD | ~70K | Limited | Low | Rejected |

### 2.10 Browser Automation

| Candidate | License | Stars | Async | ORBIT Fit | Decision |
|-----------|---------|-------|-------|-----------|----------|
| **Playwright** | MIT | ~55K | Yes | **High** | **Planned** |
| Puppeteer | Apache-2.0 | ~75K | Yes | Medium | Rejected |
| Browsertrix | GPL | ~1K | Active | Low (GPL) | Rejected |

---

## 3. Integration Strategy

| Technology | Integration Method | Status |
|------------|-------------------|--------|
| httpx | Direct library use | Implemented |
| trafilatura | Direct library use | Implemented |
| Redis | Direct library use | Implemented (in-memory, Redis adapter planned) |
| PostgreSQL | SQLAlchemy ORM | Planned (models defined, DB not yet connected) |
| Elasticsearch | Elasticsearch client | Planned |
| Neo4j | Neo4j Python driver | Planned |
| langdetect | Direct library use | Planned (simple heuristic implemented) |
| scikit-learn | Direct library use | Planned |
| FastAPI | Direct framework use | Implemented |
| Playwright | Adapter (planned) | Not yet integrated |
| Celery | Task queue adapter | Planned |

---

## 4. Rejected with Reason

| Technology | Reason |
|------------|--------|
| Apache Nutch | Too heavy, complex operational overhead, not modular |
| Apache StormCrawler | Storm dependency, over-engineered for ORBIT's needs |
| Scrapy | Good but ORBIT needs custom distributed URL frontier and adaptive discovery |
| Crawlee | Node.js, ORBIT is Python-based |
| Katana | Focused on reconnaissance, not general crawling |
| Puppeteer | Chrome-only, heavier than needed for selective rendering |
| Browsertrix | GPL license, browser-focused rather than extraction |
| Kafka | Overkill for ORBIT's queue needs |
| MongoDB | Not ideal for relational operational data |
| AWS Neptune | Proprietary, vendor lock-in |
| Django | Too heavyweight for API-only control plane |
| Flask | Lacks async support needed for high-concurrency crawling |
| polyglot | GPL license |

---

## 5. Optional Components

| Component | Status | Reason |
|-----------|--------|--------|
| Neo4j | Optional | Graph storage, can be replaced with alternative |
| Elasticsearch | Optional | Search, can be replaced with Meilisearch/Typesense |
| Playwright | Optional | Browser rendering, only for JavaScript-heavy pages |
| scikit-learn | Optional | ML classification, ORBIT works with Tier 1 rules alone |

---

**End of ORBIT Technology Comparison**
