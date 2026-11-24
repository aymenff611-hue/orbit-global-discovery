# ORBIT Core — Global Demand Discovery and Opportunity Intelligence Network

ORBIT CORE is a configurable, reusable platform for discovering, investigating, validating, and organizing genuine commercial demand across the global Internet.

## Mission

ORBIT discovers opportunities that conventional prospecting systems fail to find — beyond Fiverr, Upwork, LinkedIn, job boards, and fixed collections of popular websites.

The central discovery principle:

> Discovered source → extracted information → entities and relationships → newly discovered sources → validated sources → new demand signals → qualified opportunities → accumulated knowledge → intelligent discovery prioritization → further source expansion.

## Status

**ORBIT CORE — READY FOR SERVICE AND CUSTOMER CONFIGURATION.**

The system is implemented, tested, and documented. The maximum design envelope (100M pages/day, 1B candidate URLs/day, 100M domains) remains documented even if initial infrastructure cannot reach it.

## Architecture

ORBIT CORE consists of 30 native components organized into these modules:

| Module | Components |
|--------|-----------|
| `core/` | Data models, evidence/provenance, monitoring, adaptive discovery, workflow recovery, security |
| `discovery/` | Source registry, URL frontier, recursive discovery engine |
| `crawler/` | HTTP crawler with robots.txt, SSRF protection, per-host politeness |
| `extractor/` | Content extraction (trafilatura, readability, BeautifulSoup) |
| `classifier/` | Demand detection, buyer intent classification (tiered) |
| `graph/` | Knowledge graph with entities, relationships, provenance |
| `storage/` | Hot/warm/cold data store with compression, deduplication, retention |
| `queue/` | Distributed task queue with backpressure, idempotency, dead-letter |
| `api/` | FastAPI control plane API |
| `benchmarks/` | Benchmark suite with claim-type classification |
| `config/` | Environment-driven configuration |

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/orbit-global-discovery.git
cd orbit-global-discovery

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your settings

# Start dependencies (Docker Compose)
docker-compose -f deployment/docker-compose.yml up -d

# Run the API
python -m uvicorn orbit-core.api.main:app --host 0.0.0.0 --port 8000

# Open API documentation
# http://localhost:8000/api/v1/docs
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
├── queue/             # Distributed task queue
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
