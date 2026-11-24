# ORBIT Numerical Targets

**Classification:** Engineering Targets (design envelope, not current performance claims)  
**Status:** Documented targets, not yet fully measured at maximum scale

---

## A. Global Source Discovery

| Metric | Current Measured | Single-Node | Production Cluster | Maximum Distributed Design | Classification |
|--------|-----------------|-------------|--------------------|---------------------------|----------------|
| Candidate URLs evaluated per day | Unknown | Unknown | Unknown | 1,000,000,000 | Engineering Target |
| Candidate source records per day | Unknown | Unknown | Unknown | 1,000,000 | Engineering Target |
| New validated sources per day | Unknown | Unknown | Unknown | 10,000 | Engineering Target |
| Cumulative discovery registry capacity | Unknown | Unknown | Unknown | 100,000,000 domains | Engineering Target |

**Source classifications (never count duplicates):**
1. Candidate URLs
2. Candidate domains
3. Validated domains
4. Useful sources
5. Active monitored sources
6. Sources that produce qualified demand

**Infrastructure requirements:** Distributed URL frontier, deduplication cluster, source registry database
**Estimated operating cost:** Unknown / Not Yet Measurable
**Bottlenecks:** DNS resolution rate, URL deduplication memory, per-host politeness limits
**Benchmark evidence:** None yet (Engineering Target)
**What remains unverified:** All targets at this level

---

## B. Distributed Crawling and Extraction

| Level | Pages Fetched per Day | Classification |
|-------|----------------------|----------------|
| Initial validation | 100,000 | Engineering Target |
| Production baseline | 1,000,000 | Engineering Target |
| Large distributed scale | 10,000,000 | Engineering Target |
| Maximum design envelope | 100,000,000 | Conditional Scale Target |

**Extreme-scale targets:**
- 10,000 concurrent distributed fetch workers: Conditional Scale Target
- 1 billion candidate URLs evaluated daily: Engineering Target
- 100 million fetched pages daily: Conditional Scale Target

**Infrastructure requirements:**
- Distributed workers (Kubernetes or similar)
- Distributed URL frontier (Redis Cluster)
- Per-host rate limiting
- Selective browser rendering (separate from HTTP)
- Adaptive concurrency based on CPU, memory, network, queue depth

**Estimated operating cost:** Unknown / Not Yet Measurable
**Bottlenecks:** Per-host politeness, browser rendering memory, network bandwidth, URL deduplication
**Benchmark evidence:** None yet
**What remains unverified:** All crawling targets at production scale and above

---

## C. Data and Storage Envelope

| Scenario | Average Page Size | Daily Raw Data | 30 Days Raw | Classification |
|----------|-------------------|----------------|-------------|----------------|
| Conservative | 100 KB | ~10 TB | ~300 TB | Engineering Target |
| Moderate | 500 KB | ~50 TB | ~1.5 PB | Engineering Target |
| Large | 1 MB | ~100 TB | ~3 PB | Conditional Scale Target |

**Storage architecture:**
- Hot storage: Active operational data (30 days retention)
- Warm storage: Recent content and searchable evidence (365 days)
- Cold/object storage: Historical archives (7 years)
- Compression and deduplication enabled
- Separate raw content from extracted text and structured records

**Infrastructure requirements:** Object storage (S3/MinIO), distributed file system, compressed archives
**Estimated operating cost:** Unknown / Not Yet Measurable
**Bottlenecks:** Storage I/O, compression CPU, backup bandwidth
**Benchmark evidence:** None yet

---

## D. Knowledge Graph and Entity Intelligence

| Metric | Design Envelope | Classification |
|--------|----------------|----------------|
| Domain/host identities | Up to 100 million | Engineering Target |
| Relationship edges | Up to 10 billion | Engineering Target |
| Entity types | Organization, person, product, service, community, website, opportunity | Engineering Target |

**Infrastructure requirements:** Graph database (Neo4j or alternative), graph processing cluster
**Estimated operating cost:** Unknown / Not Yet Measurable
**Bottlenecks:** Graph traversal performance, entity resolution at scale, relationship indexing
**Benchmark evidence:** None yet

---

## E. Global Language and Geographical Coverage

| Metric | Target | Classification |
|--------|--------|----------------|
| Languages in identification architecture | At least 100 | Engineering Target |
| Countries and territories | 250 | Engineering Target |
| Unicode and multilingual normalization | Required | Engineering Target |
| Language-aware search and classification | Required | Engineering Target |

**Note:** Do not claim equal coverage or accuracy across all languages without evaluation.
**Classification:** Engineering Target / Unknown per language

---

## F. Demand and Opportunity Intelligence

| Metric | Target | Classification |
|--------|--------|----------------|
| Raw demand events per day | Up to 10,000,000 | Engineering Target |
| Precision@100 | ≥ 90% | Engineering Target |
| Recall | ≥ 80% | Engineering Target |
| Evidence provenance | 100% of qualified opportunities | Engineering Target |

**Benchmark target:** Precision@100 ≥ 90%, Recall ≥ 80% on manually labeled evaluation set
**Separate scores required:** Per source category, language, and intent type
**No fabricated buyer identity, budget, deadline, or request details**

**Infrastructure requirements:** Classification pipeline, NER models, evaluation dataset
**Estimated operating cost:** Unknown / Not Yet Measurable
**Benchmark evidence:** None yet

---

## G. Competition Intelligence

| Metric | Requirement | Classification |
|--------|-------------|----------------|
| Competing providers/responses | Observable evidence only | Engineering Target |
| Existing offers | Count where publicly visible | Engineering Target |
| Market saturation indicators | Observable | Engineering Target |
| Time since publication | Observable | Engineering Target |
| Engagement/fulfillment evidence | Observable | Engineering Target |

**Never claim to know all competitors in the world.** Every competition score must disclose observable coverage, evidence, and confidence.
**Classification:** Engineering Target

---

## H. Accuracy and Data Quality Targets

| Metric | Target | Classification |
|--------|--------|----------------|
| Exact duplicate detection precision | ≥ 99.99% | Engineering Target |
| Entity resolution precision | ≥ 99% | Engineering Target |
| Entity resolution recall | ≥ 95% | Engineering Target |
| Evidence provenance | 100% | Engineering Target |
| Language identification accuracy | Measured by language | Engineering Target |

**Do not report these targets as achieved until tests prove them.**

---

## I. Performance and Reliability

| Metric | Target | Classification |
|--------|--------|----------------|
| URLs discovered per second | Measured | Measured ORBIT Benchmark (when tested) |
| URLs filtered per second | Measured | Measured ORBIT Benchmark |
| Pages fetched per second | Measured | Measured ORBIT Benchmark |
| Pages extracted per second | Measured | Measured ORBIT Benchmark |
| Events processed per second | Measured | Measured ORBIT Benchmark |
| Indexing throughput | Measured | Measured ORBIT Benchmark |
| Entity resolution throughput | Measured | Measured ORBIT Benchmark |
| Opportunity detection throughput | Measured | Measured ORBIT Benchmark |
| Queue latency | Measured | Measured ORBIT Benchmark |
| End-to-end opportunity discovery latency | Measured | Measured ORBIT Benchmark |

**Benchmark at:** 24 hours, 7 days, 30 days, 90 days where infrastructure permits.

---

## J. Non-Negotiable Reporting Classification

Every numerical claim must be classified as exactly one:

1. **Published Benchmark** — from published literature or vendor documentation
2. **Measured ORBIT Benchmark** — actually measured on ORBIT system
3. **Engineering Target** — design target, not yet measured
4. **Conditional Scale Target** — achievable only under specific conditions
5. **Unknown / Not Yet Measurable** — cannot be measured with current infrastructure

**Never mix these categories.**

**Primary business metric:** Number of unique, evidence-backed, qualified opportunities discovered, weighted by buying intent, freshness, source diversity, and visible competition.

---

**End of ORBIT Numerical Targets**
