# ORBIT Data Architecture

**Version:** 0.1.0  
**Status:** Implemented (ORBIT CORE)

---

## 1. Overview

ORBIT uses purpose-built storage per workload. No single database is forced to handle all workloads. Each storage technology is selected based on the access patterns, consistency requirements, and scale characteristics of its workload.

---

## 2. Storage Tier Architecture

### 2.1 Hot Storage (Active Operational Data)

| Characteristic | Specification |
|---------------|---------------|
| Purpose | Active operational data, frequently accessed |
| Retention | 30 days (configurable) |
| Technology | PostgreSQL (operational), Redis (caching/queue) |
| Access pattern | Read-heavy, low latency |
| Examples | Source registry, active crawl jobs, recent opportunities, configuration |

### 2.2 Warm Storage (Recent Content and Searchable Evidence)

| Characteristic | Specification |
|---------------|---------------|
| Purpose | Recent content, searchable evidence, extracted text |
| Retention | 365 days (configurable) |
| Technology | Elasticsearch, PostgreSQL (warm tables) |
| Access pattern | Search, analytics, occasional retrieval |
| Examples | Extracted page content, search indexes, evidence snapshots |

### 2.3 Cold Storage (Historical Archives)

| Characteristic | Specification |
|---------------|---------------|
| Purpose | Historical archives, long-term retention |
| Retention | 7 years (configurable) |
| Technology | Object storage (S3/MinIO), compressed archives |
| Access pattern | Rare retrieval, batch processing, compliance |
| Examples | Raw HTML archives, historical crawl data, old opportunities |

---

## 3. Storage by Workload

| Workload | Storage Technology | Schema | Retention |
|----------|-------------------|--------|-----------|
| Source registry | PostgreSQL | `sources` table | 7 years |
| URL candidates | PostgreSQL + Redis | `url_candidates` | 90 days |
| Crawl jobs | Redis (queue) + PostgreSQL | `crawl_jobs` | 30 days |
| Raw HTML | Object storage (cold) | Compressed .dat files | 7 years |
| Extracted text | Elasticsearch + PostgreSQL | Extracted documents | 365 days |
| Opportunities | PostgreSQL | `opportunities` | 7 years |
| Knowledge graph entities | Neo4j | Entity nodes | 7 years |
| Knowledge graph relationships | Neo4j | Relationship edges | 7 years |
| Evidence/provenance | PostgreSQL + Object storage | Evidence records | 7 years |
| Metrics/time-series | Prometheus + custom | Time-series | 90 days |
| Audit logs | PostgreSQL + Object storage | Audit entries | 7 years |

---

## 4. Data Models

### 4.1 Source Model

```
sources table:
- id (UUID, PK)
- source_type (enum: candidate_url, candidate_domain, validated_domain, useful_source, active_monitored_source, qualified_demand_source)
- status (enum: discovered, validating, validated, useful, active, qualified, inactive, blocked, expired)
- url (text)
- domain (text, indexed)
- host (text)
- discovered_at (timestamp)
- discovered_from (UUID, FK to sources)
- discovery_generation (integer)
- discovery_method (text)
- validated_at (timestamp)
- validation_method (text)
- validation_score (float)
- yield_score (float, 0-1)
- quality_score (float, 0-1)
- freshness_score (float, 0-1)
- last_crawled (timestamp)
- last_successful_crawl (timestamp)
- crawl_count (integer)
- failure_count (integer)
- pages_discovered (integer)
- pages_crawled (integer)
- opportunities_found (integer)
- country_code (text)
- region (text)
- language (text)
- language_confidence (float)
- related_sources (UUID array)
- parent_source (UUID, FK)
- child_sources (UUID array)
- evidence_url (text)
- evidence_snapshot (text)
- is_excluded (boolean)
- exclusion_reason (text)
- priority (integer, 1-10)
- created_at (timestamp)
- updated_at (timestamp)
```

### 4.2 Opportunity Model

```
opportunities table:
- id (UUID, PK)
- title (text)
- description (text)
- source_id (UUID, FK to sources)
- source_url (text)
- evidence_snapshot (text)
- evidence_timestamp (timestamp)
- service_category (text)
- industry (text)
- buying_intent_score (float, 0-1)
- urgency_score (float, 0-1)
- confidence_score (float, 0-1)
- requester_organization (text)
- requester_organization_confidence (float)
- requester_contact (text)
- requester_location (text)
- budget_indicated (text)
- budget_confidence (float)
- deadline (timestamp)
- requirements (text array)
- published_at (timestamp)
- discovered_at (timestamp)
- expires_at (timestamp)
- is_stale (boolean)
- is_fulfilled (boolean)
- visible_competitors (integer)
- competition_score (float, 0-1)
- competition_coverage_note (text)
- language (text)
- country_code (text)
- region (text)
- is_duplicate (boolean)
- duplicate_of (UUID, FK)
- cluster_id (text)
- status (text)
- provenance_chain (JSONB)
- created_at (timestamp)
- updated_at (timestamp)
```

### 4.3 Entity Model

```
entities table (graph nodes):
- id (UUID, PK)
- entity_type (text: organization, person, product, service, community, website, opportunity)
- name (text, indexed)
- canonical_name (text)
- aliases (text array)
- attributes (JSONB)
- country_code (text)
- language (text)
- source_ids (UUID array)
- evidence (JSONB array)
- created_at (timestamp)
- updated_at (timestamp)
```

### 4.4 Relationship Model

```
relationships table (graph edges):
- id (UUID, PK)
- source_entity_id (UUID, FK)
- target_entity_id (UUID, FK)
- relationship_type (text, indexed)
- properties (JSONB)
- valid_from (timestamp)
- valid_to (timestamp)
- source_ids (UUID array)
- evidence (JSONB array)
- confidence (float, 0-1)
- created_at (timestamp)
```

---

## 5. Data Lifecycle

### 5.1 Ingestion

```
Source discovered → Registered in Source Registry →
URL added to Frontier → Crawled → Extracted →
Stored in Hot Storage → Classified →
Opportunity created → Knowledge Graph updated →
Moved to Warm after 30 days → Moved to Cold after 365 days
```

### 5.2 Retention Policies

| Data Type | Hot | Warm | Cold | Delete |
|-----------|-----|------|------|--------|
| Source metadata | 30 days | 365 days | 7 years | Never (compliance) |
| Raw HTML | 7 days | 30 days | 7 years | 7 years |
| Extracted text | 30 days | 365 days | 7 years | 7 years |
| Opportunities | 30 days | 365 days | 7 years | Never (compliance) |
| Audit logs | 90 days | 365 days | 7 years | 7 years |
| Metrics | 7 days | 90 days | 1 year | 1 year |

### 5.3 Compression and Deduplication

- Compression: gzip for content > 1KB
- Deduplication: SHA-256 checksum-based content dedup
- Separate raw content from extracted text and structured records
- Reproducible indexing: raw content can be re-extracted and re-indexed

### 5.4 Partitioning and Sharding

- Sources: partitioned by domain hash
- Opportunities: partitioned by date (monthly)
- Crawl jobs: partitioned by queue name
- Graph: sharded by entity type (future)

### 5.5 Backup and Disaster Recovery

- PostgreSQL: Point-in-time recovery, daily snapshots
- Redis: RDB snapshots + AOF
- Elasticsearch: Snapshots to object storage
- Neo4j: Backups to object storage
- Object storage: Versioning + cross-region replication

---

## 6. Data Ownership

| Data Set | Owner | Steward |
|----------|-------|---------|
| Source registry | Discovery team | Data engineer |
| Crawl data | Crawling team | Data engineer |
| Extracted content | Extraction team | Data engineer |
| Opportunities | Classification team | Data analyst |
| Knowledge graph | Graph team | Data engineer |
| Evidence/provenance | Security team | Compliance officer |
| Metrics | Operations team | SRE |

---

## 7. Migrations

Database migrations are managed with Alembic. See `migrations/` directory.

### 7.1 Migration Strategy

- Schema changes via Alembic migrations
- Data migrations for backfills
- Zero-downtime migrations where possible
- Rollback procedures documented

### 7.2 Migration Files

```
migrations/
├── versions/
│   ├── 0001_initial_schema.py
│   ├── 0002_add_opportunity_provenance.py
│   └── ...
├── env.py
└── script.py.mako
```

---

## 8. Recovery Procedures

### 8.1 Database Recovery

1. Restore PostgreSQL from latest snapshot
2. Apply WAL logs for point-in-time recovery
3. Verify data integrity with checksums
4. Restart services

### 8.2 Object Storage Recovery

1. Restore from versioned object storage
2. Verify checksums against database records
3. Re-index search indexes from raw content if needed

### 8.3 Index Rebuild

```
# Rebuild search index from extracted content
python -m scripts.rebuild_index --source hot --target warm

# Rebuild graph from entities/relationships
python -m scripts.rebuild_graph --source postgresql --target neo4j
```

---

**End of ORBIT Data Architecture**
