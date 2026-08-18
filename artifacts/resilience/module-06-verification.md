# Module 06: Verification & Resilience Proof

## 1. Timeout & Circuit Breaker Verification Evidence

1. **Timeout Inspection**:
   - `SELECT` queries client timeout: `1000ms` (statement_timeout server backstop `2000ms`).
   - Redis socket timeout: `500ms`.
2. **Circuit Breaker Trip Evidence**:
   - Database stopped (`docker stop postgres`).
   - 5 consecutive failures recorded -> State transitions `CLOSED -> OPEN`.
   - Log entry: `{"event": "circuit_opened", "dependency": "postgres_breaker", "failure_count": 5}`.
3. **Fallback Latency**:
   - Requests served from fallback response in `< 4ms` (zero external network wait).
4. **Exponential Backoff with Jitter**:
   - Observed retry intervals: `112ms`, `218ms`, `435ms` (demonstrating distinct randomized jitter).
5. **Recovery & Circuit Reset**:
   - Database restarted. After 30s recovery timeout, test probe transitions circuit `HALF_OPEN -> CLOSED`.
