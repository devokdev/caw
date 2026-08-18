# Module 07: Break Analysis - Config Drift Diagnosis

## 1. Observed Incident & Break Condition
- **Alert**: Paged at 3 AM for `DatabaseConnectionFailure`.
- **Command Run**: `docker exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"`
- **Symptom / Error**: `Error response from daemon: No such container: postgres`.

## 2. Root Cause Diagnosis
- **Underlying Cause**: In production, container naming convention drifted from `postgres` to `postgres-primary-v15` during an infrastructure migration. The runbook contained stale container identifiers (`Scenario A: Stale Runbook / Config Drift`).
- **Impact**: On-call engineer encountered a command failure during initial triage.
