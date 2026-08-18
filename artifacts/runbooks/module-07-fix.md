# Module 07: Fix & Runbook Hardening

## 1. Divergence Resolution
- Updated database diagnosis command from stale container reference `postgres` to standard environment identifier:
  `docker exec $(docker ps --filter "ancestor=postgres" --format "{{.ID}}") psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"`
- Added explicit health-endpoint fallback check:
  `curl -s http://localhost:8000/ready | jq .checks.database`

## 2. Re-Verification Evidence
- Re-executed full Runbook 1 cycle with updated command string:
  1. Tested container dynamic discovery query: successfully resolved postgres container ID.
  2. Executed activity monitor query: returned `count: 1` active session.
  3. Re-verified readiness check: HTTP 200 OK.
