# ORBIT Operations

**Version:** 0.1.0  
**Status:** Implemented (ORBIT CORE)

---

## 1. Overview

This document covers operational procedures for ORBIT CORE including deployment, monitoring, backup, recovery, and day-to-day operations.

---

## 2. Deployment

### 2.1 Local Development (Docker Compose)

```bash
# Start all services
docker-compose -f deployment/docker-compose.yml up -d

# Check status
docker-compose -f deployment/docker-compose.yml ps

# View logs
docker-compose -f deployment/docker-compose.yml logs -f orbit-api

# Stop all services
docker-compose -f deployment/docker-compose.yml down
```

### 2.2 Production Deployment

For production, deploy each component horizontally:
- API: Multiple FastAPI replicas behind load balancer
- Crawler: Multiple worker nodes
- URL Frontier: Redis Cluster
- Database: PostgreSQL with replicas
- Search: Elasticsearch cluster
- Graph: Neo4j cluster
- Object storage: S3 or MinIO with replication

---

## 3. Configuration

Configuration is via environment variables (see `.env.example`). Key categories:

| Category | Example Variables |
|----------|------------------|
| API | ORBIT_API_HOST, ORBIT_API_PORT, ORBIT_API_WORKERS |
| Discovery | ORBIT_DISCOVERY_MAX_CANDIDATES_PER_DAY, ORBIT_DISCOVERY_ENABLE_RECURSIVE |
| Crawling | ORBIT_CRAWL_MAX_CONCURRENT_WORKERS, ORBIT_CRAWL_PER_HOST_CONCURRENCY |
| Storage | ORBIT_STORAGE_HOT_RETENTION_DAYS, ORBIT_STORAGE_COMPRESSION_ENABLED |
| Queue | ORBIT_QUEUE_BROKER_URL, ORBIT_QUEUE_RESULT_BACKEND |
| Database | ORBIT_DATABASE_URL |
| Search | ORBIT_SEARCH_ENGINE_URL |
| Graph | ORBIT_GRAPH_URI, ORBIT_GRAPH_USER, ORBIT_GRAPH_PASSWORD |
| Security | ORBIT_SECURITY_ENABLE_SSRF_PROTECTION, ORBIT_SECURITY_AUDIT_LOG_ENABLED |
| Adaptive | ORBIT_ADAPTIVE_EXPLORATION_WEIGHT, ORBIT_ADAPTIVE_MIN_YIELD_THRESHOLD |

No code changes required for ordinary configuration changes.

---

## 4. Health Checks

### 4.1 API Health Endpoint

```bash
curl http://localhost:8000/api/v1/health
```

Returns:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "components": {
    "registry": "ok",
    "frontier": "ok",
    "discovery_engine": "ok",
    "crawler": "ok",
    "detector": "ok"
  }
}
```

### 4.2 Docker Health Check

The Dockerfile includes a HEALTHCHECK that calls the API health endpoint every 30 seconds.

---

## 5. Monitoring and Metrics

ORBIT collects metrics through the `MetricsCollector` class in `core/monitoring.py`. Key metrics:

- Crawl success/failure rates
- Extraction success rates
- Detection confidence distributions
- Queue depths
- Resource consumption (CPU, memory, disk, network)
- Error rates by component

### 5.1 Viewing Stats

```bash
curl http://localhost:8000/api/v1/stats
```

---

## 6. Backup Procedures

### 6.1 Database Backup (PostgreSQL)

```bash
# Full backup
docker exec orbit-db pg_dumpall -U orbit > backup_$(date +%F).sql

# Restore
docker exec -i orbit-db psql -U orbit < backup_2024-01-01.sql
```

### 6.2 Redis Backup

```bash
# Redis saves RDB snapshots automatically
# Manual save
docker exec orbit-redis redis-cli BGSAVE
```

### 6.3 Elasticsearch Backup

```bash
# Create snapshot repository and snapshot (via API)
curl -X PUT "localhost:9200/_snapshot/orbit_backup" -H 'Content-Type: application/json' -d '{"type": "fs", "settings": {"location": "/mnt/backups"}}'
curl -X PUT "localhost:9200/_snapshot/orbit_backup/snapshot_1?wait_for_completion=true"
```

### 6.4 Neo4j Backup

```bash
# Neo4j backup
neo4j-admin backup --to=/mnt/backups/neo4j
```

### 6.5 Object Storage Backup

Object storage (MinIO/S3) should have versioning and cross-region replication enabled.

---

## 7. Recovery Procedures

### 7.1 Database Recovery

1. Stop application services
2. Restore PostgreSQL from backup
3. Apply WAL logs if point-in-time recovery needed
4. Restart services
5. Verify data integrity

### 7.2 Worker Failure Recovery

ORBIT's Workflow Manager automatically reclaims stale tasks from failed workers:
- Tasks running > 1 hour without heartbeat are reclaimed
- Tasks are re-queued with retry count incremented
- Dead-letter handling for permanently failed tasks

### 7.3 Index Rebuild

If search indexes are corrupted:
```bash
python -m scripts.rebuild_index --source hot --target warm
```

### 7.4 Disaster Recovery

1. Restore infrastructure (servers, network)
2. Restore databases from backups
3. Restore object storage from backups
4. Rebuild search indexes from raw content
5. Restart ORBIT services
6. Verify health endpoints

---

## 8. Log Management

ORBIT uses structured logging via Python's `logging` module with `structlog`. Logs include:
- Component name
- Timestamp
- Log level
- Structured fields (key-value pairs)

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### 8.1 Viewing Logs

```bash
# Docker Compose
docker-compose -f deployment/docker-compose.yml logs -f orbit-api

# Specific service
docker-compose -f deployment/docker-compose.yml logs -f orbit-worker
```

---

## 9. Maintenance Tasks

### 9.1 Retention Policy

Run retention policy to move data between tiers and delete expired content:

```bash
python -m storage.data_store --run-retention
```

### 9.2 Resource Rebalancing

Run adaptive discovery rebalancing to reallocate crawl resources:

```bash
python -m core.adaptive_discovery --rebalance
```

### 9.3 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 10. Troubleshooting

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| API not responding | Service not running | Check `docker-compose ps`, restart |
| High crawl failure rate | Per-host limits too strict | Increase `ORBIT_CRAWL_PER_HOST_CONCURRENCY` |
| Low discovery yield | Poor seed sources | Add more diverse seed sources |
| Queue depth growing | Workers not keeping up | Add more worker nodes |
| Extraction failures | Malformed HTML | Check extraction logs, adjust extractor |
| High memory usage | Browser rendering | Reduce `ORBIT_CRAWL_BROWSER_MAX_CONCURRENT` |

---

## 11. Contact

For operational issues, see `ORBIT_DEPLOYMENT.md` and the runbooks in `scripts/`.

---

**End of ORBIT Operations**
