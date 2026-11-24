# ORBIT Licenses

**Version:** 0.1.0  
**Status:** Implemented (ORBIT CORE)

---

## 1. ORBIT Core License

ORBIT CORE is released under the MIT License. See `LICENSE` file.

---

## 2. Third-Party Dependencies

ORBIT CORE depends on the following open-source projects. All licenses are verified for compatibility.

### Python Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| FastAPI | 0.115.0 | MIT | API framework |
| uvicorn | 0.32.1 | BSD | ASGI server |
| pydantic | 2.9.2 | MIT | Data validation |
| httpx | 0.27.2 | BSD | HTTP client |
| aiohttp | 3.10.4 | Apache-2.0 | Async HTTP |
| beautifulsoup4 | 4.12.3 | MIT | HTML parsing |
| lxml | 5.2.2 | BSD | XML/HTML processing |
| trafilatura | 1.6.3 | Apache-2.0 | Content extraction |
| readability-lxml | 0.8.1 | Apache-2.0 | Content extraction |
| redis | 5.0.1 | MIT | Redis client |
| celery | 5.4.0 | BSD | Task queue |
| sqlalchemy | 2.0.36 | MIT | ORM |
| alembic | 1.13.1 | MIT | Migrations |
| psycopg2-binary | 2.9.9 | LGPL | PostgreSQL adapter |
| elasticsearch | 8.15.0 | Apache-2.0 | Search client |
| neo4j | 5.23.0 | Apache-2.0 | Graph client |
| langdetect | 1.0.9 | Apache-2.0 | Language detection |
| scikit-learn | 1.5.2 | BSD | ML |
| numpy | 1.26.4 | BSD | Numerical computing |
| scipy | 1.13.1 | BSD | Scientific computing |
| newspaper3k | 0.2.8 | Apache-2.0 | Article extraction |
| pyyaml | 6.0.2 | MIT | YAML parsing |
| jsonschema | 4.21.1 | MIT | JSON Schema validation |
| structlog | 24.4.0 | Apache-2.0 | Structured logging |
| prometheus-client | 0.21.0 | Apache-2.0 | Metrics |
| typer | 0.12.3 | MIT | CLI |
| rich | 13.9.0 | MIT | Rich terminal |
| pytest | 8.3.2 | MIT | Testing |
| cryptography | 43.0.0 | BSD | Cryptography |

### Docker Images

| Image | Version | License | Purpose |
|-------|---------|---------|---------|
| python | 3.13-slim | PSFL | Base image |
| postgres | 15-alpine | PostgreSQL | Database |
| redis | 7-alpine | BSD | Queue/cache |
| elasticsearch | 8.15.0 | Elastic License | Search |
| neo4j | 5.23.0 | GPLv3 | Graph database |

---

## 3. License Compliance

All dependencies are verified for:
- License compatibility with ORBIT's MIT license
- No copyleft restrictions that would require ORBIT to be open-sourced (except GPLv3 Neo4j which is optional)
- No known license conflicts

**Optional components:** Neo4j (GPLv3) is optional — ORBIT can work with alternative graph storage.

---

## 4. External Project Integration

For every external project integrated:
- [x] Versions pinned
- [x] License compatibility verified
- [x] Dependencies isolated
- [x] Clear adapters created
- [x] Data contracts documented
- [x] Integration tests planned
- [x] No invasive forks unless justified

---

**End of ORBIT Licenses**
