# Module 08: Deploy & Verify - Context & Health Architecture

## 1. Deep vs Shallow Health Probes
- **Shallow (`GET /live`)**: Probes only that the uvicorn process is alive and event loop is responsive. Misses database partition, bad secrets, and downstream deadlocks.
- **Deep (`GET /ready`)**: Executes active `SELECT 1` against PostgreSQL pool and `PING` against Redis cluster. Returns 503 if any core dependency fails to respond within 500ms timeout budget.

## 2. Immediate Error Spike Response Protocol
1. Query Prometheus error rate: `rate(http_requests_total{status=~"5.."}[2m]) / rate(http_requests_total[2m])`.
2. Inspect correlated structured error logs by `request_id`.
3. If error rate > 5% within 2 minutes of deploy, trigger immediate one-command rollback:
   `TAG=previous docker-compose up -d && docker-compose ps`
