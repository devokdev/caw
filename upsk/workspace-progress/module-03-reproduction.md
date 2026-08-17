# Module 3 — Reproduction (Debugging & Incident Response)

## Incident symptom (from module logs)
Intermittent 500 on `GET /:shortCode`, clustered on popular links; server log shows
`duplicate key value violates unique constraint "analytics_link_id_bucket_unique"`.

## Hypothesis (recorded at DECIDE: B — synthetic reproduction)
Three candidates per module: Data, Timing, Concurrency. Evidence (errors cluster on
popular links; single-hit links almost never error) points to Concurrency:
a check-then-act race where two requests both SELECT an absent row, both INSERT,
and the second crashes on the unique constraint.

## Reproduction attempt against the fork
`repro_race.py` fires N concurrent redirects at one short link:

```
Results: 10 redirects, 0 errors, 0 other ([])
No errors this run. Try again or increase CONCURRENCY.   (x4 runs)
```

Server log greps for `analytics_link_id_bucket_unique` / `duplicate key` /
`IntegrityError` during the runs: **no matches**.

## Root-cause trace
The canonical Bug #5 assumes a synchronous analytics bucket (`analytics(link_id,
timestamp_bucket, count)`) with SELECT-then-INSERT in the redirect handler. This
fork (System Design M3 checkpoint) records clicks differently and is already
atomic by construction:

- `routers/redirect.py` only resolves the link + enqueues a Celery task
  (`record_click.delay`) — no analytics write in the request path.
- `services/analytics.py:insert_click` is a **single INSERT** of a `ClickEvent`
  guarded by a unique `event_key`; duplicates are caught via `IntegrityError`
  and skipped (idempotent). There is no pre-SELECT, so the check-then-act window
  on clicks cannot exist.

So the redirect path cannot produce the reported 500 in this fork. The same race
CLASS is, however, present in code generation: `_generate_code()` previously did
`SELECT (is code free?)` then `INSERT` on `links.code` (UNIQUE) — the module's
exact two-chairs pattern, on a different table.

## Deterministic reproduction of the real TOCTOU window
`repro_code_race.py` forces the RNG so both concurrent creators compute the SAME
first candidate, then commits both. Against the old code:

```
('OK', 'aaaaaa')
('INTEGRITY', 'duplicate key value violates unique constraint "links_code_key"')
```

That is the same failure mode as the module's log line — `duplicate key value
violates unique constraint`, reproduced deterministically instead of flaky.

## Fix (atomic, no check-then-act)
`api/app/services/links_service.py:create_link` now:
1. generates a random candidate (no SELECT pre-check);
2. attempts the INSERT;
3. on `IntegrityError` rolls back and retries with a fresh code (<=10 attempts).

The unique constraint is the arbiter; the database serializes concurrent inserts
(equivalent to `INSERT ... ON CONFLICT DO NOTHING` semantics).

## Verification
- Deterministic repro (`repro_code_race.py check`) against the fixed code:

```
('OK', '8lLu6L')
('OK', 'uMOMDh')
RACE ELIMINATED: both concurrent creators succeeded with distinct codes
```

- Full suite: 72 tests, exit code 0.
- Live redirect repro still 10/10 redirects, 0 errors after server restart.

## Artifacts
- `progress/repro_race.py` — minimal concurrency repro (canonical shape).
- `progress/repro_code_race.py` — deterministic check-then-act repro + verify.
- `api/app/services/links_service.py` — atomic create_link fix.