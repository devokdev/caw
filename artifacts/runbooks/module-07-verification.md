# Module 07: Runbook Simulation & Verification Walkthrough

## 1. Simulation Testing Evidence
- **Simulated Incident**: Database connection pool saturation (`Runbook 1`).
- **Execution Log**:
  1. Ran diagnosis command: `docker exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"`
     - Observed: 20 active connections (`Problem state confirmed`).
  2. Executed remediation command: Terminated hanging idle transactions and reset pool.
  3. Ran verification check: `curl -s http://localhost:8000/ready | jq .`
     - Observed: `{"ok": true, "checks": {"database": "connected"}}`.

## 2. Command Ergonomics Audit
- **Zero Placeholders**: All commands use exact service names (`myservice-prod`, `postgres`, `redis`).
- **Dual Outputs**: Both healthy and broken output scenarios documented for every check.
- **Escalation SLA**: Explicit 10-minute escalation threshold with named contacts.
