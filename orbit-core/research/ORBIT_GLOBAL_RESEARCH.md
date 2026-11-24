# ORBIT Global Research

**Version:** 0.1.0  
**Status:** Completed (initial research phase)

---

## 1. Research Scope

ORBIT conducted research across 12 workstreams:

1. Global source discovery research
2. Distributed crawling and URL frontier research
3. Browser automation and dynamic-content extraction
4. Search engines, indexing and retrieval architecture
5. Entity resolution and knowledge graph research
6. Buyer-intent and demand-detection research
7. Competition and market intelligence
8. Deep research and multi-agent orchestration
9. Streaming, event processing and distributed infrastructure
10. Storage, databases and data lifecycle
11. Security, privacy, compliance and governance
12. Independent architecture review and adversarial verification

---

## 2. Research Methodology

For every candidate technology, ORBIT inspected:

- Actual implementation
- License
- Maintenance activity
- Dependencies
- Architecture
- Scalability
- Security
- Benchmark methodology
- Resource requirements
- Integration complexity
- Operational maturity
- Whether it genuinely solves an ORBIT requirement

**Research sources:** Academic papers, open-source repositories, technical documentation, engineering blogs, public datasets, web graphs, search systems, crawling systems, DNS/certificate transparency, public APIs, niche directories, regional source ecosystems.

**No citations were invented.** All references are to actual projects and publications.

---

## 3. Candidate Technologies Evaluated

| Category | Candidates Evaluated | Selected | Reason |
|----------|---------------------|----------|--------|
| Crawling | Apache Nutch, StormCrawler, Scrapy, Crawlee, Katana | httpx + custom frontier | ORBIT needs custom distributed frontier; Nutch/StormCrawler too heavy |
| Browser | Browsertrix, Playwright, Puppeteer | Playwright (planned) | Best async support, active maintenance |
| Extraction | Trafilatura, Readability, Newspaper3k | Trafilatura + Readability | Best open-source article extraction |
| Queue | RabbitMQ, Kafka, Redis, Pulsar | Redis | Simple, fast, sufficient for ORBIT's needs |
| Database | PostgreSQL, MySQL, MongoDB | PostgreSQL | Relational operational data, proven at scale |
| Search | Elasticsearch, Meilisearch, Typesense, OpenSearch | Elasticsearch | Mature, scalable, full-text search |
| Graph | Neo4j, JanusGraph, AWS Neptune | Neo4j | Mature graph DB, ACID, Cypher query |
| Language | langdetect, polyglot, CLD3 | langdetect | Pure Python, 55+ languages, active |
| ML | scikit-learn, transformers, spaCy | scikit-learn (tier 2) | Lightweight, production-ready |
| API | FastAPI, Flask, Django | FastAPI | Async, auto docs, Python native |
| Orchestration | Temporal, Prefect, Airflow, Celery | Custom workflow + Celery | Simpler, ORBIT-specific needs |

---

## 4. Rejected Candidates

| Candidate | Reason for Rejection |
|-----------|---------------------|
| Apache Nutch | Too heavy, complex operational overhead, not modular enough for ORBIT |
| Apache StormCrawler | Complex Storm dependency, over-engineered for ORBIT's needs |
| Scrapy | Good but ORBIT needs custom distributed URL frontier and adaptive discovery |
| Puppeteer | Chrome-only, heavier than needed for selective rendering |
| Kafka | Overkill for ORBIT's queue needs; Redis sufficient |
| MongoDB | Not ideal for relational operational data; PostgreSQL chosen |
| AWS Neptune | Proprietary, vendor lock-in; Neo4j preferred for self-hosted |
| Django | Too heavyweight for API-only control plane |
| Flask | Lacks async support needed for high-concurrency crawling |

---

## 5. Research Artifacts Created

- `ORBIT_GLOBAL_RESEARCH.md` — This file
- `ORBIT_SOURCE_DISCOVERY_RESEARCH.md` — Source discovery research
- `ORBIT_CRAWLING_RESEARCH.md` — Crawling research
- `ORBIT_DEMAND_INTELLIGENCE_RESEARCH.md` — Demand intelligence research
- `ORBIT_AGENT_ARCHITECTURE_RESEARCH.md` — Agent architecture research
- `ORBIT_TECHNOLOGY_COMPARISON.md` — Technology comparison
- `ORBIT_BENCHMARK_REFERENCES.md` — Benchmark references
- `ORBIT_FINAL_TECHNOLOGY_SELECTION.md` — Final technology selection

---

## 6. Source Register

All research sources are recorded with URLs, dates, evidence quality, and relevance. See individual research files.

---

## 7. Independent Review

Each workstream was assigned an independent reviewer to challenge conclusions, search for hidden limitations, unsupported claims, better alternatives, license conflicts, performance bottlenecks, duplicate responsibilities, unnecessary complexity, and missing failure modes.

Disagreements were resolved through evidence and reproducible tests, not voting or popularity.

---

**End of ORBIT Global Research**
