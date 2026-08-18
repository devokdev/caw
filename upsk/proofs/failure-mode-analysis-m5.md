# Module 05 — Failure Mode Analysis

Default failure stance (decision): **fail_open** — with per-dependency refinement.
- Postgres = **fail_closed** (never fabricate a redirect; cache miss during DB outage → 500/503)
- Redis cache = **fail_open** (fall back to Postgres; speed degrades, correctness preserved)
- Redis rate-limit = **fail_open** (bounded risk; log loudly)
- Celery/click analytics = **fail_open** (drop analytics, redirect still 302)

## Chunk 1 — Dependency Inventory

| Dependency | Connection Method | Configured Timeout | Retry Behavior |
|---|---|---|---|
| Postgres (source of truth) | TCP via psycopg2 pool, `pool_pre_ping=True` | `connect_timeout=5` (connect only). **NO statement/query timeout** — gap | `pool_pre_ping` re-validates stale connections; no app-level retry/backoff |
| Redis (redirect cache) | TCP, `redis.asyncio.from_url` | `socket_timeout=0.5`, `socket_connect_timeout=0.5` | None on purpose — fails fast, caller falls back to Postgres |
| Redis (Celery broker) | TCP via kombu (redis transport) | inherited 0.5s socket timeouts | `_enqueue_click` catches send failure → drop analytics, redirect preserved |
| Rate-limit storage | In-memory (InMemoryStorage, process-local) | N/A (no external call) | N/A — limits are per-process, safe for single worker |
| DNS | OS resolver → Docker embedded DNS (127.0.0.11) | **No explicit control** (libc/embedded DNS defaults) | libc retries; **gap** — resolves per-connection, no fallback IP |
| File system | Docker json-file log driver, OS writes | N/A | None — **gap** (no log rotation configured, no disk metric/alert) |
| Runtime (memory/CPU) | Python process in container | **No memory limit in compose** — gap | Container restart policy on OOM only if limit set |

PAUSE: How many have an explicit timeout? Only Postgres connect (5s) and Redis (0.5s). DNS, filesystem, runtime, and — critically — **DB query execution have none**. Every "?" is a potential 2 AM page.

## Chunk 2 — Failure Mode Table

| Dependency | Failure Mode | Probability | User Impact | Current Handling | Desired Handling |
|---|---|---|---|---|---|
| Postgres | Connection refused / down (maintenance, restart) | Medium | Every DB-touching request errors; total outage for cache misses | `/ready` → 503 (correct fail-closed). Redirect: 500 after ~4s (connect_timeout + DNS), `unhandled error` logged with request_id | Return 503 (not 500) with retry-after; retry connection with backoff; fire an alert on `/ready` flip |
| Postgres | Slow / blocked (lock, long query, vacuum) | High | Requests HANG indefinitely (no statement_timeout) → threads pile up → pool exhaustion → cascade to ALL endpoints | **None — hangs** (proven: ACCESS EXCLUSIVE lock made redirect wait 14.7s with no cutoff) | Statement timeout (~2s), log slow query, return 504 when exceeded; lock-timeout on writes |
| Postgres | Query plan change / missing index | High | Per-request latency spikes, timeouts | None (no slow-query log, no EXPLAIN tracking) | Statement timeout + slow-query logging (log queries > threshold with params redacted) |
| Postgres | Connection pool exhaustion | Medium | All requests block waiting for a pool slot | `pool_pre_ping` only; no max_overflow guard tuning | Pool size + overflow bounds; queue timeout; alert on pool wait |
| Redis | Down / unreachable | Medium | Every request hits Postgres → slower, DB pressure | Graceful: `socket_timeout=0.5` → warning log → fall back to DB; correctness preserved | Already correct; add disk/DB-load alert for the fallback storm |
| Redis | Stale cache | High | Stale redirects served (minor for URL shortener; critical if URLs change) | Version stamp `redirect:ver:` generation token checked before serving; TTL-based expiry; invalidation on update/delete | Already correct; alert if invalidation count spikes |
| Celery broker (Redis) | Down | Low-Medium | Click analytics silently lost | `_enqueue_click` catches → warning log "analytics dropped (graceful degradation)"; redirect still 302 | Add retry with backoff + dead-letter; alert on enqueue failure count |
| DNS | Resolution failure (embedded DNS blip, hostname typo) | Low-Medium | CRYPTIC errors: "could not translate host name" — looks like a network outage; requests fail ~4-8s | No fallback; error bubbles as `unhandled error` 500 | Verify hostnames at deploy; document "could not translate host name" as DNS not DB; alert on resolution failure |
| File system | Disk full (log rotation not configured) | Low-Medium | Logs silently stop; Postgres may crash; app behavior degrades silently | None — silent failure | Disk usage metric + alert at 80%; configure log rotation |
| Runtime | OOM (memory leak, unbounded cache) | Low-Medium | Process killed; container restarts (if restart policy); in-flight requests lost | No memory limit set; `restart: unless-stopped` would restart | Set container memory limit; memory metric; alert at 80% |
| Network | Partition (some deps reachable, others not) | Low | Reads work, writes fail; partial availability | Depends which dependency; cache/analytics degrade, DB fails closed | Documented per-dep; circuit breaker pattern for slow deps |
| Clock skew | Clock drift on api vs db | Low | JWT expiries wrong, timestamps misordered | N/A (single host, Docker) | Use UTC everywhere (`-c timezone=UTC` already set); NTP sync |

PAUSE: Count "Current Handling = none/crash/hang": Postgres slow (hang), query plan (none), DNS (none), filesystem (silent), runtime (none), pool exhaustion (block). That is 6 distinct scenarios with no graceful behavior — that number is the risk surface.

## Chunk 3 — Simulation Drills (actually performed)

### Simulation 1: Database stopped
`docker stop linkops-postgres` → hit API.

| | Observation |
|---|---|
| User sees | `/ready` → **503** in **8.0s**; `/r/test123` (cache flushed) → **500** in **4.0s** |
| Logs | `readiness db check failed` + `unhandled error`: `(psycopg2.OperationalError) could not translate host name "postgres" to address: Name or service not known` with request_id |
| Time to notice | Would require someone watching `/ready`; no alert fires automatically on 503. `ServiceDown` alert would NOT catch this (api process still up). Metrics show 500 spike but nothing surfaces it |
| vs table | Matches "Connection refused" row: correct 503 for readiness, but redirect returns 500 (should be 503) and takes 4s; DNS layer added ~3s to the 5s connect timeout. After `docker start` → `/ready` 200 immediately |

### Simulation 2: Slow dependency — DB blocked (not down)
`docker exec -d linkops-postgres psql -c "BEGIN; LOCK TABLE links IN ACCESS EXCLUSIVE MODE; SELECT pg_sleep(45);"` then `FLUSHALL` redis → hit API.

| | Observation |
|---|---|
| User sees | Redirect request **hung**: curl `--max-time 15` aborted after **15s**; a later curl waited **14.7s** then returned (lock had released). No timeout kicked in — the server-side query kept waiting in `pg_stat_activity` (pid 40 blocked by the lock) |
| Logs | Nothing until the query finally completed or a client abort; then generic `request failed`/`unhandled error` |
| Time to notice | Indefinite — **no statement timeout exists**. A slow/blocked DB looks like "working"; threads pile up → pool exhaustion → all endpoints hang |
| vs table | Confirms "Slow / blocked" row = worst row in the table. **Down fails fast (4s, loud). Slow hangs forever (silent).** This is the fraud-check story verbatim |

### Gap vs. Simulation (what to fix)

| Simulation | Expected | Actual | Gap |
|---|---|---|---|
| Database stopped | Service returns 503 fast | 503 (ready) / **500** (redirect) after 4-8s | Redirect returns 500 not 503; latency from DNS + connect; no automatic alert on readiness flip |
| Slow DB (blocked) | Fails fast with timeout | **Hangs indefinitely** (14.7s+ observed, cut off only by client) | **No statement_timeout configured** — the single most important fix; also no slow-query logging |

### Simulation 3 (BREAK injection — partial failure: reads work, writes fail)
`ALTER SYSTEM SET default_transaction_read_only = on; SELECT pg_reload_conf();`

| | Observation |
|---|---|
| User sees | **Reads work**: `GET /r/test123` → 302. **Writes fail**: `POST /links` → **500** `internal_error` (dev envelope leaked `cannot execute INSERT in a read-only transaction`, request_id captured). `/live` stays 200 — service is "up" per monitoring |
| Logs | `request failed` + `unhandled error` with full SQL trace: `ReadOnlySqlTransaction cannot execute INSERT in a read-only transaction` |
| Root cause | Primary DB in **read-only mode** — the classic failover-to-read-replica / promotion-mistake scenario. `SHOW default_transaction_read_only` → `on` confirmed it |
| Handling | Writes must fail **fast and loud** (they did — instant 500) but should return **503 with retry-after**, not generic 500, so clients know the primary is unavailable rather than a bug. Reads correctly keep working |
| Restored | `ALTER SYSTEM SET default_transaction_read_only = off` + reload → `POST /links` → **201** again |

Transient vs permanent classification: connection refused / lock contention / read-only failover window = **transient** (retry with backoff helps once primary promoted). Missing table / invalid credentials / bad schema = **permanent** (fail fast, alert, never retry — the M4 `UndefinedTable` drill proved retrying a missing table is futile).

## Chunk 4 — FIX (handling implemented + re-simulated)

### New failure mode table row
| Dependency | Failure Mode | Probability | User Impact | Current Handling (observed) | Desired Handling (implemented) |
|---|---|---|---|---|---|
| Postgres | Read-only primary (failover/replica promotion) | Medium | Reads work, writes fail with confusing 500 | Generic `internal_error` 500 (old behavior) | **503 `database_unavailable` + Retry-After: 5 + specific log** |

### Fixes implemented
1. **`api/app/database.py`**: added `-c statement_timeout=2000` to connection options — closes the #1 risk (slow/blocked DB hang).
2. **`api/app/main.py`**: new `@app.exception_handler(InternalError)` → logs `database write rejected: primary unavailable or read-only (transient)` with `error_type` (e.g. `ReadOnlySqlTransaction`) and request_id, returns **503** `{"error":{"code":"database_unavailable",...}}` with `Retry-After: 5` — meaningful message, no stack trace, correct transient status.

### Re-simulation (same failure re-injected)
`ALTER SYSTEM SET default_transaction_read_only = on` + reload:

| Check | Before fix | After fix |
|---|---|---|
| Read `GET /r/test123` | 302 | 302 (unchanged) |
| Write `POST /links` | 500 `internal_error` + leaked SQL trace | **503** `{"error":{"code":"database_unavailable","message":"service temporarily unavailable: database is not accepting writes","request_id":"f39ef018"}}` + `Retry-After: 5` |
| Log | generic `unhandled error` | `database write rejected: primary unavailable or read-only (transient)`, `error_type: ReadOnlySqlTransaction`, request_id present |
| Restored | POST → 201 | POST → 201 |

### Bonus re-simulation — slow DB (top-risk row) after statement_timeout fix
Re-injected the ACCESS EXCLUSIVE lock on `links` + redis flush:
- **Before**: request hung indefinitely (>15s, cut off only by client `--max-time`).
- **After**: request aborted in **2.1s** with `QueryCanceled: canceling statement due to statement timeout` logged (request_id 644c72da). The pool-exhaustion cascade is now bounded: at most ~2s per query instead of unbounded hang.