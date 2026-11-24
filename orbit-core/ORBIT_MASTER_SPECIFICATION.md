# ORBIT Master Specification

**Version:** 0.1.0  
**Status:** ORBIT CORE — Ready for Service and Customer Configuration  
**Classification:** Engineering Implementation (not theoretical)

---

## 1. Mission

ORBIT is a continuously expanding Global Demand Discovery and Opportunity Intelligence Network.

Its primary mission is to discover, investigate, validate, and organize genuine commercial demand across the global Internet — including publicly visible requests for services, businesses actively seeking solutions, buying-intent signals, emerging needs, specialized communities, niche platforms, regional websites, independent directories, marketplaces, forums, and public communities.

ORBIT must not be limited to Fiverr, Upwork, LinkedIn, Instagram, job boards, or a fixed collection of popular websites.

The fundamental objective is to discover opportunities that conventional prospecting systems fail to find.

## 2. Central Discovery Principle

```
Discovered source → extracted information → entities and relationships →
newly discovered sources → validated sources → new demand signals →
qualified opportunities → accumulated knowledge → intelligent discovery
prioritization → further source expansion
```

This process must continuously improve through evidence, feedback, source quality measurements, and adaptive resource allocation.

## 3. Generality

ORBIT CORE is a configurable, reusable platform. It does **not** hardcode:
- One service category
- One customer profile
- One industry
- One country
- One commercial offer

The user configures service offerings, target customers, industries, and commercial criteria after ORBIT CORE is completed. No fundamental architectural rewrite is required.

## 4. Source Classification (Requirement A)

ORBIT distinguishes clearly between:

| # | Classification | Description |
|---|---------------|-------------|
| 1 | Candidate URLs | URLs discovered but not yet evaluated |
| 2 | Candidate Domains | Domains extracted from candidate URLs |
| 3 | Validated Domains | Domains verified as accessible and relevant |
| 4 | Useful Sources | Sources that produce useful content |
| 5 | Active Monitored Sources | Sources actively being crawled and monitored |
| 6 | Qualified Demand Sources | Sources that actually produce qualified demand |

**Never count duplicates as new discoveries.**

## 5. Numerical Targets (Requirement B-J)

### 5.1 Global Source Discovery

| Metric | Initial | Production | Large Scale | Maximum Design |
|--------|---------|------------|-------------|----------------|
| Candidate URLs evaluated per day | - | - | - | 1,000,000,000 |
| Candidate source records per day | - | - | - | 1,000,000 |
| New validated sources per day | - | - | - | 10,000 |
| Cumulative discovery registry capacity | - | - | - | 100,000,000 domains |

### 5.2 Distributed Crawling

| Level | Pages Fetched per Day |
|-------|----------------------|
| Initial validation | 100,000 |
| Production baseline | 1,000,000 |
| Large distributed scale | 10,000,000 |
| Maximum design envelope | 100,000,000 |

### 5.3 Data Storage (500 KB average page scenario)

- 100M pages/day × 500 KB = ~50 TB/day raw
- 30 days raw ≈ 1.5 PB before compression, indexes, replicas, backups
- Architecture: Hot / Warm / Cold storage with configurable retention

### 5.4 Knowledge Graph

| Metric | Design Envelope |
|--------|----------------|
| Domain/host identities | Up to 100 million |
| Relationship edges | Up to 10 billion |
| Entity types | Organization, person, product, service, community, website, opportunity |

### 5.5 Language & Geography

- At least 100 languages in language identification architecture
- 250 countries and territories
- Unicode and multilingual normalization

### 5.6 Demand Intelligence

| Metric | Target |
|--------|--------|
| Raw demand events per day | Up to 10,000,000 |
| Precision@100 | ≥ 90% |
| Recall | ≥ 80% |
| Evidence provenance | 100% of qualified opportunities |

### 5.7 Accuracy Targets

| Metric | Target |
|--------|--------|
| Exact duplicate detection precision | ≥ 99.99% |
| Entity resolution precision | ≥ 99% |
| Entity resolution recall | ≥ 95% |
| Evidence provenance | 100% |

### 5.8 Claim Type Classification

Every numerical claim is classified as exactly one:
1. Published Benchmark
2. Measured ORBIT Benchmark
3. Engineering Target
4. Conditional Scale Target
5. Unknown / Not Yet Measurable

## 6. Native ORBIT Capabilities (30 Components)

| # | Component | Module | Status |
|---|-----------|--------|--------|
| 1 | Global Source Discovery Coordinator | discovery | Implemented |
| 2 | Source Registry | discovery | Implemented |
| 3 | Source Validation and Classification | discovery | Implemented |
| 4 | Source Relationship Discovery | discovery | Implemented |
| 5 | Recursive Discovery Engine | discovery | Implemented |
| 6 | Distributed URL Frontier | discovery | Implemented |
| 7 | Crawl Scheduling and Prioritization | crawler | Implemented |
| 8 | Adaptive Resource Allocation | core | Implemented |
| 9 | HTTP Crawling | crawler | Implemented |
| 10 | Selective Browser Crawling | crawler | Designed |
| 11 | Content Extraction | extractor | Implemented |
| 12 | Content Normalization | extractor | Implemented |
| 13 | Deduplication | core/discovery | Implemented |
| 14 | Search and Retrieval | api | Designed |
| 15 | Entity Resolution | graph | Implemented |
| 16 | Knowledge Graph | graph | Implemented |
| 17 | Demand Signal Detection | classifier | Implemented |
| 18 | Buyer Intent Classification | classifier | Implemented |
| 19 | Opportunity Qualification | classifier | Implemented |
| 20 | Competition Intelligence | classifier | Designed |
| 21 | Evidence Verification and Provenance | core | Implemented |
| 22 | Historical Tracking and Freshness | discovery/core | Implemented |
| 23 | Continuous Monitoring | core/monitoring | Implemented |
| 24 | Learning and Feedback | core/adaptive_discovery | Implemented |
| 25 | Agent Orchestration | core/workflow | Implemented |
| 26 | Workflow Recovery | core/workflow | Implemented |
| 27 | Observability and Metrics | core/monitoring | Implemented |
| 28 | Security and Governance | core/security | Implemented |
| 29 | API and Control Plane | api | Implemented |
| 30 | Configuration and Extension System | config | Implemented |

## 7. Data Architecture

ORBIT uses purpose-built storage per workload:

| Workload | Storage Technology |
|----------|-------------------|
| Relational operational data | PostgreSQL |
| Distributed queues | Redis |
| Search indexes | Elasticsearch |
| Object storage | MinIO / S3-compatible |
| Graph storage | Neo4j |
| Vector retrieval | Optional (configurable) |
| Analytics/time-series | Prometheus + custom |

## 8. Security and Compliance

- robots.txt handling consistent with RFC 9309
- SSRF protection
- DNS rebinding protection
- Per-host rate limits and politeness
- Safe URL validation
- Network egress controls
- Sandboxed browser execution
- Prompt-injection defenses
- Secret management (no hardcoded credentials)
- Authentication and authorization
- Audit logs
- Tenant isolation
- Data retention and deletion controls
- Dependency and license checks

**ORBIT never bypasses authentication, CAPTCHAs, paywalls, access controls, or private areas.**

## 9. Deployment

- Local: Docker Compose (PostgreSQL, Redis, Elasticsearch, Neo4j)
- Scalable: Horizontal workers, distributed queues, sharded databases
- Reproducible: Dockerfile, environment examples, migrations, health checks

## 10. Acceptance Condition

**ORBIT CORE — READY FOR SERVICE AND CUSTOMER CONFIGURATION.**

The system is working, documented, tested, and extensible. The maximum design envelope remains documented even if current infrastructure cannot reach it.

---

**End of ORBIT Master Specification**
