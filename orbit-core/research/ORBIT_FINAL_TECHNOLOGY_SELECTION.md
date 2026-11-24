# ORBIT Final Technology Selection

**Version:** 0.1.0  
**Status:** Completed

---

## 1. Final Selected Technology Stack

| Layer | Technology | Version | License | Integration Method | Status |
|-------|-----------|---------|---------|-------------------|--------|
| API Framework | FastAPI | 0.115.0 | MIT | Direct framework use | Implemented |
| ASGI Server | uvicorn | 0.32.1 | BSD | Direct library use | Implemented |
| Data Validation | pydantic | 2.9.2 | MIT | Direct library use | Implemented |
| HTTP Client | httpx | 0.27.2 | BSD | Direct library use | Implemented |
| Async HTTP | aiohttp | 3.10.4 | Apache-2.0 | Direct library use | Implemented |
| HTML Parsing | beautifulsoup4 | 4.12.3 | MIT | Direct library use | Implemented |
| XML Processing | lxml | 5.2.2 | BSD | Direct library use | Implemented |
| Content Extraction | trafilatura | 1.6.3 | Apache-2.0 | Direct library use | Implemented |
| Content Extraction (fallback) | readability-lxml | 0.8.1 | Apache-2.0 | Direct library use | Implemented |
| Queue/Cache | redis | 5.0.1 | MIT | Direct library use | Implemented (in-memory) |
| Task Queue | celery | 5.4.0 | BSD | Adapter | Planned |
| ORM | sqlalchemy | 2.0.36 | MIT | Direct library use | Planned |
| Migrations | alembic | 1.13.1 | MIT | Direct library use | Planned |
| PostgreSQL adapter | psycopg2-binary | 2.9.9 | LGPL | Direct library use | Planned |
| Search Client | elasticsearch | 8.15.0 | Apache-2.0 | Adapter | Planned |
| Graph Client | neo4j | 5.23.0 | Apache-2.0 | Adapter | Planned |
| Language Detection | langdetect | 1.0.9 | Apache-2.0 | Direct library use | Planned (heuristic implemented) |
| ML Classification | scikit-learn | 1.5.2 | BSD | Direct library use | Planned |
| Scientific Computing | numpy | 1.26.4 | BSD | Direct library use | Planned |
| Scientific Computing | scipy | 1.13.1 | BSD | Direct library use | Planned |
| Article Extraction | newspaper3k | 0.2.8 | Apache-2.0 | Direct library use | Rejected |
| YAML Parsing | pyyaml | 6.0.2 | MIT | Direct library use | Implemented |
| JSON Schema | jsonschema | 4.21.1 | MIT | Direct library use | Planned |
| Structured Logging | structlog | 24.4.0 | Apache-2.0 | Direct library use | Implemented |
| Metrics | prometheus-client | 0.21.0 | Apache-2.0 | Direct library use | Implemented |
| CLI | typer | 0.12.3 | MIT | Direct library use | Planned |
| Rich Terminal | rich | 13.9.0 | MIT | Direct library use | Planned |
| Testing | pytest | 8.3.2 | MIT | Test framework | Planned |
| Async Testing | pytest-asyncio | 0.25.0 | MIT | Test framework | Planned |
| HTTP Mocking | responses | 0.25.0 | MIT | Test framework | Planned |
| Cryptography | cryptography | 43.0.0 | BSD | Security | Implemented |

---

## 2. Docker Images (Deployment)

| Image | Version | License | Purpose |
|-------|---------|---------|---------|
| python | 3.13-slim | PSFL | Base image |
| postgres | 15-alpine | PostgreSQL | Database |
| redis | 7-alpine | BSD | Queue/cache |
| elasticsearch | 8.15.0 | Elastic License | Search |
| neo4j | 5.23.0 | GPLv3 | Graph database (optional) |

---

## 3. Integration Strategy

| Technology | Integration Method | Adapter | Status |
|------------|-------------------|---------|--------|
| httpx | HTTP crawler uses httpx directly | HTTPCrawler class | Implemented |
| trafilatura | Content extractor uses trafilatura directly | ContentExtractor class | Implemented |
| BeautifulSoup | Fallback extractor | ContentExtractor class | Implemented |
| Redis | Queue backend | TaskQueue class | Implemented (in-memory) |
| PostgreSQL | Source/opportunity storage | Data models defined | Planned |
| Elasticsearch | Search index | Not yet integrated | Planned |
| Neo4j | Knowledge graph | KnowledgeGraph class | Implemented (in-memory) |
| langdetect | Language detection | Simple heuristic implemented | Planned |
| scikit-learn | Classification | Not yet integrated | Planned |
| FastAPI | API server | api/main.py | Implemented |
| Celery | Distributed tasks | Not yet integrated | Planned |
| Playwright | Browser rendering | Not yet integrated | Planned |

---

## 4. Rejected Candidates (with Reason)

| Category | Candidate | Reason |
|----------|-----------|--------|
| Crawling | Apache Nutch | Too heavy, complex operations |
| Crawling | Apache StormCrawler | Storm dependency, over-engineered |
| Crawling | Scrapy | Custom distributed frontier needed |
| Crawling | Crawlee | Node.js, ORBIT is Python |
| Crawling | Katana | Recon-focused, not general crawling |
| Browser | Puppeteer | Chrome-only, heavier than needed |
| Browser | Browsertrix | GPL license |
| Queue | Kafka | Overkill for ORBIT's needs |
| Queue | RabbitMQ | More complex than Redis for ORBIT |
| Queue | Pulsar | Overkill |
| Database | MySQL | PostgreSQL preferred |
| Database | MongoDB | Relational data needed |
| Graph | JanusGraph | Low maintenance activity |
| Graph | AWS Neptune | Vendor lock-in |
| Search | Meilisearch | Elasticsearch more mature |
| Search | Typesense | Elasticsearch more mature |
| Search | OpenSearch | Elasticsearch preferred |
| Language | polyglot | GPL license |
| Language | CLD3 | C++ dependency |
| API | Flask | No async support |
| API | Django | Too heavyweight |
| Orchestration | Temporal | Over-engineered |
| Orchestration | Prefect | Over-engineered |
| Orchestration | Airflow | Not for real-time discovery |

---

## 5. Optional Components

| Component | Status | Reason |
|-----------|--------|--------|
| Neo4j | Optional | Graph storage, replaceable |
| Elasticsearch | Optional | Search, replaceable |
| Playwright | Optional | Browser rendering, selective only |
| scikit-learn | Optional | ML classification, Tier 1 works without it |
| Celery | Optional | Distributed tasks, in-memory queue works for single node |

---

## 6. Technology Justification

ORBIT selected technologies based on:

1. **Technical fitness:** Each technology solves a specific ORBIT requirement
2. **License compatibility:** All core dependencies use MIT/BSD/Apache licenses
3. **Maintenance activity:** Active maintenance with recent releases
4. **Python-native:** ORBIT is Python-based; Node.js/Go solutions rejected
5. **Modularity:** Each component can be replaced without affecting others
6. **Operational simplicity:** No over-engineered solutions (no Kafka, Temporal, etc.)
7. **Scalability:** Horizontal scaling supported through distributed deployment

---

## 7. Replaceability

ORBIT is designed so that any external component can be replaced:

- Replace Neo4j with JanusGraph or another graph DB
- Replace Elasticsearch with Meilisearch or Typesense
- Replace Playwright with Puppeteer (if Chrome-only acceptable)
- Replace scikit-learn with transformers or spaCy
- Replace Redis with RabbitMQ or Kafka (if needed at extreme scale)

Each replacement requires only an adapter change, not architectural rewrite.

---

**End of ORBIT Final Technology Selection**
