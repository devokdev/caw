# Module 08: Break & Root Cause Diagnosis

## Problem Breakdown & Diagnosis

### Issue 1: Silent Business Failure Despite Green `/ready`
- **Symptom**: `/live` and `/ready` return 200 OK, but business API (e.g. URL creation/redirection) throws 500 errors.
- **Root Cause**: The `/ready` probe was doing a shallow `SELECT 1` ping on a generic connection pool, but the business route executed an un-migrated schema query (missing column `metadata` in table `urls`) or required write privileges on a read-only replica.
- **Remediation**: Expand readiness testing or add end-to-end synthetic health checks that execute real read/write transaction flows with isolated test keys.

### Issue 2: Memory Leak Accumulation
- **Symptom**: Resident memory (RSS) steadily climbing without GC reclaiming space.
- **Root Cause**: An unbounded global dictionary/list was appending request telemetry or cache invalidation events without eviction policy (LRU / TTL).
- **Remediation**: Implement bounded `lru_cache` or move state out of in-memory Python structures to Redis with explicit `EXPIRE`.

### Issue 3: Configuration Drift / Rogue Env Injection
- **Symptom**: Runtime configuration diverges from Git-managed CI/CD pipeline repository state.
- **Root Cause**: An engineer manually modified environment variables directly on the cloud provider dashboard without committing changes to infrastructure-as-code or secret manifests.
- **Remediation**: Enforce GitOps pipeline-only updates; enable automated config drift detection that alerts whenever runtime container env hash differs from the committed deployment manifest.
