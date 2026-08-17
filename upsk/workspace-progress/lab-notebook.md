# Lab Notebook - Module 10: CI/CD & Deployment

## Final Reflection & Questions

### 1. What core problem does this module solve in ci/cd & deployment (railway)?
It solves the reliability and safety of containerized environments: preventing routing traffic to the app before migrations are complete (using readiness checks), ensuring dynamic PORT binding to align with host forwarding rules, and protecting in-flight transactions from being terminated abruptly (via graceful shutdown).

### 2. Which decision in this module has the biggest impact, and why?
The `multi_service` deployment choice. By separating the API redirect hot-path, Celery worker analytics processing, Redis cache, and Postgres DB into distinct services, we prevent CPU/Memory starvation on the critical user-facing path when background workloads spike.

### 3. What evidence proves the implementation works end-to-end?
- Successfully built `bootcamp-api` container.
- Verified `/health` acts as liveness check (200 OK).
- Verified `/ready` acts as dependency readiness check (pings Postgres and Redis, failing with 503 quickly under mock failure).
- Verified SIGTERM shutdown triggers uvicorn graceful drain process.

## Final Demo Verification Outputs
```json
{
  "module_10": {
    "deploy_strategy": "multi_service",
    "migration_strategy": "startup",
    "status": "bootcamp complete"
  }
}
```
