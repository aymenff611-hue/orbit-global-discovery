# ORBIT Core — Global Demand Discovery and Opportunity Intelligence Network

ORBIT CORE is a configurable, reusable platform for discovering, investigating, validating, and organizing genuine commercial demand across the global Internet.

## Mission

ORBIT discovers opportunities that conventional prospecting systems fail to find — beyond Fiverr, Upwork, LinkedIn, job boards, and fixed collections of popular websites.

The central discovery principle:

> Discovered source → extracted information → entities and relationships → newly discovered sources → validated sources → new demand signals → qualified opportunities → accumulated knowledge → intelligent discovery prioritization → further source expansion.

## Status

**ORBIT CORE — IMPLEMENTED AND TESTED.**

Core discovery pipeline, source registry, URL frontier, recursive discovery engine,
HTTP crawler, content extraction, demand detection, knowledge graph, and adaptive
discovery are implemented and verified with unit tests and end-to-end tests.

Real discovery validation (genuine HTML link extraction, sitemap/RSS/Atom/robots.txt
discovery, recursive expansion across 3+ generations, adaptive discovery with measured
metrics, JavaScript-rendered page handling, multi-language Arabic/English support) is
verified in `tests/real_discovery_test.py` (54 assertions, all passing).

A realistic controlled pilot measuring throughput, yield, extraction, detection,
false positives, evidence completeness, and resource consumption is in
`tests/realistic_pilot_test.py`.

The maximum design envelope (100M pages/day, 1B candidate URLs/day, 100M domains)
remains an engineering target — not yet measured at scale.

## Architecture

ORBIT CORE consists of native components organized into these modules:

| Module | Components |
|--------|-----------|
| `core/` | Data models, evidence/provenance, monitoring, adaptive discovery, workflow recovery, security |
| `discovery/` | Source registry, URL frontier, recursive discovery engine, real discovery methods (link, sitemap, feed, canonical, relationships), URL utilities |
| `crawler/` | HTTP crawler with robots.txt, SSRF protection, per-host politeness; browser crawler |
| `extractor/` | Content extraction (trafilatura, readability, BeautifulSoup) |
| `classifier/` | Demand detection, buyer intent classification (tiered), competition intelligence |
| `graph/` | Knowledge graph with entities, relationships, provenance |
| `storage/` | Hot/warm/cold data store with compression, deduplication, retention |
| `taskq/` | Distributed task queue with backpressure, idempotency, dead-letter |
| `api/` | FastAPI control plane API |
| `benchmarks/` | Benchmark suite with claim-type classification |
| `config/` | Environment-driven configuration |
| `tests/` | Unit tests, e2e pipeline test, real discovery test, realistic pilot test |

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/aymenff611-hue/orbit-global-discovery.git
cd orbit-core

# Install dependencies
pip install pydantic pydantic-settings httpx scikit-learn numpy trafilatura \
    readability-lxml beautifulsoup4

# Run unit tests
python -m pytest tests/test_core.py -v

# Run real discovery validation test (requires local HTTP server on port 8889)
python3 -m http.server 8889 --directory tests/real_discovery_sites &
python3 tests/real_discovery_test.py

# Run realistic controlled pilot
python3 tests/realistic_pilot_test.py

# Run the API
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Open API documentation
# http://localhost:8000/docs
```

### Docker

```bash
docker-compose -f deployment/docker-compose.yml up -d
```

## Configuration

ORBIT is configured entirely through environment variables (see `.env.example`). No code changes are required for ordinary configuration changes:

- Service categories
- Target customer types
- Industries
- Geographies
- Languages
- Buying-intent definitions
- Opportunity scoring weights
- Source priorities
- Exclusion rules
- Competition criteria

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | System health check |
| `/api/v1/stats` | GET | System statistics |
| `/api/v1/sources` | GET/POST | Source management |
| `/api/v1/sources/{id}` | GET | Get source by ID |
| `/api/v1/urls` | POST | Add URL candidate |
| `/api/v1/urls/next` | GET | Get next URL to crawl |
| `/api/v1/frontier/stats` | GET | URL frontier statistics |
| `/api/v1/discovery/cycle` | POST | Run discovery cycle |
| `/api/v1/crawl` | POST | Submit crawl job |
| `/api/v1/crawl/fetch` | POST | Fetch a URL |
| `/api/v1/detect` | POST | Detect demand/buyer intent |
| `/api/v1/opportunities` | GET/POST | Opportunity management |
| `/api/v1/benchmarks` | GET | Benchmark results |

## Benchmarking

Every numerical claim in ORBIT is classified as one of:

1. **Published Benchmark** — from published literature/vendor docs
2. **Measured ORBIT Benchmark** — actually measured on ORBIT
3. **Engineering Target** — design target, not yet measured
4. **Conditional Scale Target** — achievable only under specific conditions
5. **Unknown / Not Yet Measurable**

Run the benchmark suite:

```bash
python -m benchmarks.benchmark_suite
```

Results are exported as JSON and human-readable reports.

## Security

ORBIT implements:
- robots.txt compliance (RFC 9309)
- SSRF protection
- DNS rebinding protection
- Per-host rate limits and politeness
- Safe URL validation
- Audit logging
- Tenant isolation
- Prompt-injection defenses

**ORBIT never bypasses authentication, CAPTCHAs, paywalls, or private areas.**

## Repository Structure

```
orbit-core/
├── core/              # Core ORBIT components
├── discovery/         # Source discovery
├── crawler/           # HTTP and browser crawling
├── extractor/         # Content extraction
├── classifier/        # Demand detection & intent
├── graph/             # Knowledge graph
├── storage/           # Data lifecycle storage
├── taskq/             # Distributed task queue (renamed from queue/)
├── api/               # Control plane API
├── benchmarks/        # Benchmark suite
├── config/            # Configuration
├── tests/             # Tests
├── deployment/        # Docker Compose
├── docker/            # Dockerfile
├── migrations/        # Database migrations
├── scripts/           # Operational scripts
└── research/          # Research artifacts
```

## License

See `ORBIT_LICENSES.md` for dependency license information.

## Contact

For questions about ORBIT CORE configuration and deployment, see `ORBIT_OPERATIONS.md` and `ORBIT_DEPLOYMENT.md`.
