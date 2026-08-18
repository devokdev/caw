# Service Operations Manual & Incident Runbooks

## 1. Service Overview
**Purpose**: High-performance URL shortener and redirect routing engine. Resolves shortened aliases to target URLs, performs token bucket rate limiting, and records click analytics asynchronously.

### Dependencies
| Dependency | Type | What happens without it | Fallback Behavior |
|---|---|---|---|
| PostgreSQL | Primary Datastore | Complete read/write outage | Fast 503 response (<5ms) via circuit breaker |
| Redis | Cache & Rate Limit | Cache misses fall back to DB; degraded throughput | Bypass cache; route directly to Postgres DB |
| Geocoding Service | External HTTP API | Analytics geographic enrichment fails | Record geolocation as `unknown` |

### Endpoints
- `GET /live`: Liveness probe (process up).
- `GET /ready`: Readiness probe (checks DB and Redis connectivity).
- `GET /metrics`: Prometheus telemetry scrape endpoint.
- `POST /api/v1/urls`: Create shortened alias.
- `GET /:code`: Resolve alias to long URL (302 redirect).

### Configuration (`.env`)
- `DATABASE_URL`: Connection string (Required, restart required).
- `REDIS_URL`: Connection string (Required, restart required).
- `CIRCUIT_BREAKER_FAIL_MAX`: Default `5` (Safe to update on deploy).
- `CIRCUIT_BREAKER_RESET_TIMEOUT`: Default `30s`.

### Deployment & Rollback
```bash
# Manual deploy trigger
git push origin main

# Verification
curl -s http://localhost:8000/live
curl -s http://localhost:8000/ready

# Rollback
docker tag myservice-prod:previous myservice-prod:latest
docker restart myservice-prod
```

---

## 2. Top 3 Incident Runbooks

### Runbook 1: Database Connection Failure & Pool Exhaustion
**Alert**: `HighDBConnectionPoolUtilization` (> 90%)
**Diagnosis**:
1. Run: `docker exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"`
   - Problem: Count >= 20 (pool saturated).
   - Healthy: Count < 5.
2. Run: `curl -s http://localhost:8000/ready | jq .checks.database`
   - Problem: `"unreachable"` or `"timeout"`.
   - Healthy: `"connected"`.
**Fix**:
1. Run: `docker exec postgres psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND query_start < now() - interval '2 minutes';"`
2. Run: `docker restart myservice-prod`
**Verification**:
- Run: `curl -s http://localhost:8000/ready | jq .` (Expected: `{"ok": true}`).

---

### Runbook 2: 5xx Error Rate Spike
**Alert**: `HighErrorRate` (> 5% of total requests)
**Diagnosis**:
1. Run: `docker logs --tail 200 --since 10m myservice-prod | grep -c '500 Internal Server Error'`
   - Problem: Count > 50.
   - Healthy: Count == 0.
2. Run: `curl -s http://localhost:8000/metrics | grep http_requests_total`
**Fix**:
1. Run: `docker logs --tail 50 myservice-prod | grep -E 'Traceback|Exception'` to isolate offending commit.
2. Roll back container to prior SHA tag:
   `docker-compose down && TAG=stable docker-compose up -d`
**Verification**:
- Run: `curl -I http://localhost:8000/health/ready` (Expected: `HTTP/1.1 200 OK`).

---

### Runbook 3: High Redirect Latency (P99 > 500ms)
**Alert**: `HighLatencyP99`
**Diagnosis**:
1. Run: `redis-cli ping`
   - Problem: Timeout or `Could not connect`.
   - Healthy: `PONG`.
2. Check breaker metrics: `curl -s http://localhost:8000/metrics | grep circuit_breaker_state`
**Fix**:
1. Run: `docker restart redis`
2. Wait 15s for circuit half-open state transition and automatic recovery.
**Verification**:
- Run: `curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8000/testcode` (Expected: `< 0.05s`).
