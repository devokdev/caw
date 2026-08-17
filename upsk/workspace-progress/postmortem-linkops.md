# Blameless Postmortem — linkops URL Shortener Service

Date: 2026-08-18
Severity: SEV1 (auth bypass + data exposure), SEV2 (recurring availability)
Scope: broad — all ten bugs across System Design + Debugging & Incident Response
Status: remediated; structural follow-ups pending

## What happened (timeline, UTC)

| Time | Event |
|---|---|
| 14:22–14:32 | Attacker with auth-bypass access deletes 12 links across 8 accounts from IP 203.0.113.42 |
| 14:20 | Last known-good state for PITR recovery of the deleted rows |
| 15:10 | Post-incident audit query finds the deletions; data-loss investigation begins |
| 15:14 | PITR restore of all 12 links from the 06:00 daily backup + WAL replay; verified resolving |
| (separate) | Repeated availability incidents: cache staleness on redirect, CPU spike on long URLs, analytics stall |

Contributing incidents (all ten bugs observed during training):
1. M1 config/env contract mismatch (wrong env var in one layer).
2. M2 log injection via control characters in sanitized fields.
3. M3 code-generation race: SELECT-then-INSERT on unique links.code → IntegrityError under concurrency.
4. M3 redirect-cache stale-populate-after-invalidate → deleted/updated link served stale target.
5. M4 DB connection lifecycle: acquire-without-guaranteed-release in cache helpers.
6. M4 N+1-style multi-statement page query (fork hardened: 3 statements).
7. M4 CPU/resource exhaustion: unbounded long_url input, linear CPU/memory scaling.
8. M5 auth bypass (Bug #8): middleware accepted empty/missing Authorization header.
9. M6 deleted link still redirected for up to the 5-minute cache TTL.
10. M6 queue retry storm → shared connection pool exhaustion → API unavailability.

## Why the system allowed it (contributing factors — systems language)

- CF1. **The auth middleware did not reject falsy/empty Authorization headers.** The middleware contract was checked by no integration test covering empty string, null, undefined, and malformed JWT values.
- CF2. **The unique-constraint contract on `links.code` was protected by a check-then-act sequence.** The create path SELECTed for a free code, then INSERTed; nothing enforced the assumption that the code stays free between the two steps.
- CF3. **The redirect cache contract had no invalidation generation token.** A stale populate after an invalidate could re-serve old data; the cache reader could not distinguish a current entry from a stale one.
- CF4. **Redis cache clients were acquired without a guaranteed release path.** The acquire-without-finally pattern left connections undisposed on error exits.
- CF5. **The URL validation contract assumed input boundedness.** `long_url` had no max length, so CPU/memory grew linearly with attacker-controlled payload size.
- CF6. **The worker and the API shared one SQLAlchemy pool.** A failing job with `autoretry_for` could hold all pooled connections while the API waited on the same pool — no pool isolation and no bounded retry guard against a persistent failure.
- CF7. **The analytics dedup contract lived in the DB unique `event_key`, but the boundary was undocumented.** The M3 cache invalidation could plausibly be mistaken for clearing analytics state; namespace ownership was not written down.
- CF8. **The `ready` check did not verify queue/worker liveness.** If the broker was up but the worker dead, redirects succeeded while analytics silently stalled — a circular dependency between the health reporting path and the pipeline it monitors.
- CF9. **Hard delete had no guardrail.** `delete_link` destroys rows with no confirmation, dry-run, or bulk-operation cap — a single destructive command has no structural upper bound.
- CF10. **No integration-test gate existed for most of these contracts.** Bugs 3, 4, 7, 8, 10 all sat in code paths with thin or absent integration coverage; each surfaced only under conditions tests never exercised.

## What we change (remediations — every item is structural and executable)

| # | Remediation | Owner | Deadline | Checkable outcome |
|---|---|---|---|---|
| R1 | Add integration tests for auth middleware covering empty string, null, undefined, and malformed JWT Authorization headers; assert 401 | auth-owner | 2026-08-22 | CI required check |
| R2 | Enforce unique-code creation atomically: INSERT with retry-on-IntegrityError (≤10 attempts), no SELECT pre-check | backend-owner | 2026-08-20 | test asserting concurrent creates never collide |
| R3 | Add invalidation generation token to redirect cache: INCR on invalidate, reject version-mismatch on read | infra-owner | 2026-08-19 | regression test: stale-populate-after-invalidate rejected |
| R4 | Close all Redis clients in `finally` in every cache helper | infra-owner | 2026-08-19 | probe asserting CLIENT LIST returns to baseline |
| R5 | Cap `long_url` at 2048 chars via schema `Field(max_length=2048)` | backend-owner | 2026-08-19 | test: 2049-char URL → 422 string_too_long |
| R6 | Isolate the worker's connection pool from the API's; keep bounded retries with exponential backoff and a circuit breaker on persistent failures | platform-owner | 2026-08-25 | load test: failing job storm does not starve API |
| R7 | Document NAMESPACE OWNERSHIP in cache module: redirect:* reserved; analytics dedup stays in DB unique event_key, or uses analytics:dedup:* prefix if moved to Redis | infra-owner | 2026-08-19 | unit test asserting invalidation never touches analytics keys |
| R8 | Extend `ready` to probe queue worker liveness (broker + heartbeat), returning 503 when the worker is dead | platform-owner | 2026-08-25 | chaos test: worker killed → ready 503 |
| R9 | Add a bulk-delete cap and a confirm/dry-run guard to the delete path; enforce max scope per call | backend-owner | 2026-08-22 | test: bulk delete beyond cap rejected |
| R10 | Make integration tests a merge requirement (required CI status) and add a monitoring alert on DB pool utilization >80% sustained | eng-lead | 2026-08-25 | CI + alert defined in repo |

Top 3 by impact: R1, R3, R6 — they address the two SEV1/SEV2 classes and the availability cascade.

## Impact (measured)

- Auth bypass (Bug #8): 12 links across 8 accounts deleted by the attacker in
  a 10-minute window (14:22–14:32 UTC); restored 15:14 UTC from daily backup +
  WAL (PITR), verified resolving. No permanent data loss.
- Availability class (Bug #10): API unavailability under queue retry storm —
  all API requests requiring the DB park on the shared pool until the storm
  abates; user-visible symptom is timeouts, duration proportional to retry
  window.
- Cache staleness (Bug #9): deleted/updated links redirected to stale targets
  for up to the 5-minute cache TTL per affected code.
- No security exposure beyond the 12 links; no other data classes touched.

## The one lesson

**A service is reliable only where its contracts are enforced by the system, not by attention.** The largest single impact: make every cross-layer contract (auth header validity, cache freshness, unique codes, pool isolation, bounded input, queue liveness) an enforced, testable invariant. If the whole team absorbed one rule, it is this: when you change one layer, enumerate and re-verify every consumer of the state you just mutated.

## Blame check

Every contributing factor names a system, a contract, or a missing gate — no individual is named. The remediation items change the system; none ask a human to "be more careful."