# ORBIT Crawling Research

**Version:** 0.1.0  
**Status:** Completed

---

## 1. Research Objective

Research the best technologies and methods for distributed crawling — supporting up to 100 million pages per day at the maximum design envelope, with 10,000 concurrent workers, per-host politeness, and selective browser rendering.

---

## 2. Crawling Capacity Levels

| Level | Pages per Day | Use Case |
|-------|--------------|----------|
| Initial validation | 100,000 | Development and testing |
| Production baseline | 1,000,000 | Small production deployment |
| Large distributed scale | 10,000,000 | Medium production deployment |
| Maximum design envelope | 100,000,000 | Maximum architectural target |

---

## 3. Candidate Technologies Evaluated

| Technology | License | Maintenance | Concurrency | Politeness | Selected? | Reason |
|------------|---------|-------------|-------------|------------|-----------|--------|
| Apache Nutch | Apache-2.0 | Moderate | High | Built-in | No | Too heavy, complex operations, not modular |
| Apache StormCrawler | Apache-2.0 | Low | High | Built-in | No | Storm dependency, over-engineered |
| Scrapy | BSD | Active | High | Middleware | No | Good but ORBIT needs custom distributed frontier |
| Crawlee | MIT | Active | High | Built-in | No | Node.js, ORBIT is Python-based |
| Katana | MIT | Active | Medium | Basic | No | Go-based, focused on reconnaissance |
| httpx + asyncio | BSD | Active | Very High | Custom | **Yes** | Python-native, high-performance, full control |
| Playwright | MIT | Active | High | Custom | Planned | Best async browser automation |
| Puppeteer | Apache-2.0 | Active | High | Custom | No | Chrome-only, heavier than needed |
| Browsertrix | GPL | Active | Medium | Built-in | No | GPL license, browser-focused |

---

## 4. Key Design Decisions

### 4.1 HTTP Fetching Separated from Browser Rendering

HTTP fetching uses `httpx` + `asyncio` for high-concurrency, low-overhead page retrieval. Browser rendering (Playwright) is used selectively only when JavaScript is required.

### 4.2 Per-Host Politeness

- Configurable delay between requests per host (default: 1 second)
- Configurable concurrent connections per host (default: 2)
- Exponential backoff on failures (up to 5 minutes)
- **Never interpret global concurrency as permission to overload one website**

### 4.3 robots.txt Compliance

ORBIT respects robots.txt consistent with RFC 9309:
- Fetches and parses robots.txt before crawling any host
- Caches robots.txt rules with TTL
- Respects Disallow, Allow, and Crawl-delay rules

### 4.4 Distributed URL Frontier

- Deduplication via URL normalization
- Priority-based scheduling
- Per-host politeness tracking
- Redis-backed for distributed deployment

### 4.5 Retry and Backoff

- Maximum 5 retries per URL
- Exponential backoff: 2^attempt seconds (capped at 60 seconds)
- Dead-letter queue for permanently failed URLs

---

## 5. Findings

- httpx + asyncio provides the best Python-native HTTP crawling performance
- Custom URL frontier gives ORBIT full control over prioritization and politeness
- Selective browser rendering reduces resource usage by 10-100x compared to always-on rendering
- Per-host politeness is essential to avoid being blocked by websites
- Distributed crawling requires a shared URL frontier (Redis Cluster)

---

## 6. Limitations

- Single-node crawling limited by network bandwidth and file descriptors
- Browser rendering is memory-intensive (100-500MB per browser instance)
- Distributed crawling requires careful coordination to avoid duplicate fetches
- Some websites block automated crawlers regardless of politeness

---

## 7. Integration Recommendation

- httpx: Direct integration as HTTP client
- Playwright: Adapter for selective browser rendering (planned)
- Redis: Backend for distributed URL frontier
- Custom URL frontier: Native ORBIT component

---

**End of ORBIT Crawling Research**
