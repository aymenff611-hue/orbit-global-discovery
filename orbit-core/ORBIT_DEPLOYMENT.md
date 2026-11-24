# ORBIT Deployment

**Version:** 0.1.0  
**Status:** Implemented (ORBIT CORE)

---

## 1. Overview

ORBIT CORE provides reproducible deployment options from local development to production-scale clusters. The maximum design envelope (100M pages/day, 1B candidate URLs/day, 100M domains) is documented even if initial infrastructure cannot reach it.

---

## 2. Deployment Options

| Option | Use Case | Scale |
|--------|----------|-------|
| Docker Compose | Local development, single-node testing | Up to 1M pages/day |
| Kubernetes | Production clusters | Up to 10M pages/day |
| Distributed cluster | Maximum design envelope | Up to 100M pages/day |

---

## 3. Local Development (Docker Compose)

### 3.1 Prerequisites

- Docker 20+
- Docker Compose 2+
- 4GB+ RAM
- 20GB+ disk space

### 3.2 Start Services

```bash
cd /workspace/orbit-core

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose -f deployment/docker-compose.yml up -d

# Verify health
curl http://localhost:8000/api/v1/health
```

### 3.3 Service Ports

| Service | Port | Description |
|---------|------|-------------|
| ORBIT API | 8000 | Main REST API |
| PostgreSQL | 5432 | Operational database |
| Redis | 6379 | Queue and cache |
| Elasticsearch | 9200 | Search index |
| Neo4j | 7474, 7687 | Graph database (HTTP, Bolt) |

### 3.4 Stop Services

```bash
docker-compose -f deployment/docker-compose.yml down
```

### 3.5 View Logs

```bash
docker-compose -f deployment/docker-compose.yml logs -f orbit-api
```

---

## 4. Production Deployment (Kubernetes)

For production, deploy ORBIT components horizontally using Kubernetes manifests (to be provided in `deployment/kubernetes/`).

### 4.1 Architecture

```
┌─────────────────┐
│   Load Balancer │
└────────┬────────┘
         │
┌────────▼────────┐
│  ORBIT API Pods │ (3+ replicas)
└────────┬────────┘
         │
┌────────▼────────┐
│   Redis Cluster │ (3+ nodes)
└────────┬────────┘
         │
┌────────▼────────┐
│  ORBIT Workers  │ (N+ replicas, auto-scaling)
└────────┬────────┘
         │
┌────────▼────────┐
│  PostgreSQL     │ (primary + replicas)
│  Elasticsearch  │ (cluster)
│  Neo4j          │ (cluster)
│  MinIO/S3       │ (object storage)
└─────────────────┘
```

### 4.2 Resource Profiles

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| ORBIT API | 2 cores | 4GB | 10GB |
| ORBIT Worker | 4 cores | 8GB | 50GB |
| Redis | 2 cores | 4GB | 20GB |
| PostgreSQL | 4 cores | 16GB | 500GB |
| Elasticsearch | 8 cores | 32GB | 1TB |
| Neo4j | 4 cores | 16GB | 500GB |

---

## 5. Docker Build

```bash
# Build the ORBIT image
docker build -t orbit-core:latest -f docker/Dockerfile .

# Run the container
docker run -p 8000:8000 \
  -e ORBIT_DATABASE_URL=postgresql://... \
  -e ORBIT_QUEUE_BROKER_URL=redis://... \
  orbit-core:latest
```

---

## 6. Environment Variables

See `.env.example` for the complete list. Required minimum for production:

| Variable | Description |
|----------|-------------|
| ORBIT_DATABASE_URL | PostgreSQL connection string |
| ORBIT_QUEUE_BROKER_URL | Redis connection string |
| ORBIT_SEARCH_ENGINE_URL | Elasticsearch URL |
| ORBIT_GRAPH_URI | Neo4j Bolt URL |
| ORBIT_API_SECRET_KEY | API secret (change in production) |

---

## 7. Scaling Considerations

### 7.1 Horizontal Scaling

- Add more ORBIT Worker containers for crawling
- Add more API replicas behind load balancer
- Scale Redis Cluster for URL frontier
- Scale Elasticsearch for search index

### 7.2 Vertical Scaling

- Increase worker memory for browser rendering
- Increase database connections for high concurrency
- Increase Elasticsearch heap for large indexes

### 7.3 Maximum Design Envelope

The maximum design envelope (100M pages/day, 1B candidate URLs/day) requires:
- 100+ concurrent fetch workers
- Distributed URL frontier with sharding
- Multiple Elasticsearch nodes
- Object storage for cold archives
- Dedicated network bandwidth

**This is a design target, not a claim of current performance.**

---

## 8. Database Migrations

```bash
# Inside the API container or locally
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Check current revision
alembic current
```

Migration files are in `migrations/versions/`.

---

## 9. Backup and Disaster Recovery

See `ORBIT_OPERATIONS.md` for backup procedures.

### 9.1 Backup Schedule

| Component | Schedule | Retention |
|-----------|----------|-----------|
| PostgreSQL | Daily | 30 days |
| Redis | Daily | 7 days |
| Elasticsearch | Daily | 30 days |
| Neo4j | Daily | 30 days |
| Object storage | Continuous (versioning) | 7 years |

---

## 10. Upgrade Procedures

1. Review `ORBIT_LICENSES.md` for dependency changes
2. Backup all data
3. Apply database migrations (`alembic upgrade head`)
4. Deploy new container images
5. Verify health endpoints
6. Monitor metrics for anomalies

---

## 11. Resource Estimation

| Scale | Pages/Day | Workers | Servers | Est. Cost/Month* |
|-------|-----------|---------|---------|------------------|
| Development | 100K | 2-4 | 1 | $100-200 |
| Production | 1M | 10-20 | 3-5 | $1,000-3,000 |
| Large Scale | 10M | 50-100 | 10-20 | $10,000-30,000 |
| Maximum Design | 100M | 500-1000 | 50-100 | $50,000-150,000 |

*Estimates vary by region, provider, and usage patterns. Actual costs not yet measured.

---

**End of ORBIT Deployment**
