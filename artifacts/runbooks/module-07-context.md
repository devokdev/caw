# Module 07: Runbooks & Operational Docs - Context Analysis

## 1. Environment & Dependency Inventory (Explicit Recall)
- **Environment Variables**:
  - `DATABASE_URL` (Required, no defaults)
  - `REDIS_URL` (Required)
  - `JWT_SECRET` (Min 32 characters, no placeholders)
  - `APP_ENV` (`production` / `development`)
  - `LOG_LEVEL` (`INFO` / `DEBUG`)
  - `PORT` (Default: `8000`)
- **External Dependencies**:
  - PostgreSQL 15+ (Transactional persistence, short-code lookups)
  - Redis 7+ (Rate-limiting token bucket and redirect cache)

## 2. Immediate 3 AM Triage Protocol (3 Exact Commands)
1. `docker logs --tail 200 --since 15m myservice-prod | grep -E 'ERROR|CRITICAL|circuit_opened'`
2. `curl -s http://localhost:8000/health/deep | jq .`
3. `curl -s http://localhost:8000/metrics | grep -E 'http_requests_total|db_pool_active'`
