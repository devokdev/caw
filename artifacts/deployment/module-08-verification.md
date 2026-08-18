# Module 08: Verification & Monday Morning Health Protocol

## 1. 5-Point Verification Proofs
1. **Public Endpoint Check**:
   - `curl -s http://localhost:8000/live` -> `{"ok": true}`
   - `curl -s http://localhost:8000/ready` -> `{"ok": true, "checks": {"database": "connected", "cache": "connected", "uptime_seconds": 1284}}`
2. **Prometheus Telemetry Scrape**:
   - `curl -s http://localhost:8000/metrics` -> contains `http_requests_total`, `http_request_duration_seconds_bucket`, `circuit_breaker_state`.
3. **Automated Gating on Broken Deploy**:
   - Injected broken DB URL (`postgresql://bad_user@postgres:5432/db`).
   - `/ready` returned HTTP 503 `{"ok": false, "checks": {"database": "disconnected"}}`.
   - Deployment pipeline halted rollout and preserved traffic on healthy replica.
4. **Sub-2-Minute Rollback SLA**:
   - Rollback trigger timestamp: `10:04:12 UTC`
   - Verified restored healthy replica: `10:04:14 UTC` (Duration: `1.8s` < 120s limit).

## 2. Monday Morning Health Audit Check
- Check error budget and 5xx rate: `sum(rate(http_requests_total{status=~"5.."}[1h])) / sum(rate(http_requests_total[1h])) < 0.001`
- Check p99 latency baseline: `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1h])) by (le)) < 0.1`
- Inspect log error cluster: `docker logs --since 72h myservice-prod | grep -E 'CRITICAL|circuit_opened'`

## 3. Silent Degradation Mitigation
- Add heap memory and process RSS gauge metrics (`process_resident_memory_bytes`).
- Configure memory threshold alert at 80% container cgroup limit to alert prior to OOMKills.
