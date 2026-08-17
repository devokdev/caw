# Module 01 Diagnosis Notes

Lab vehicle: checkpoint fork of the system-design URL shortener (FastAPI, native Postgres at localhost:5432). Docker/Redis unavailable on this machine, so the lab runs on the native stack (API on port 8000, not 3000).

## Bug 1 - The Service Will Not Start

- Symptom: API crashes on startup. Traceback: `pydantic_core.ValidationError ... database_url Field required` while the loaded env dict contained `db_url`. The app's Settings model requires `DATABASE_URL`; the .env file only defined `DB_URL`.
- Hypothesis A: The database is not running / not reachable.
  - Command: `psql -h localhost -p 5432 -U postgres -d upsk_sdf -c "SELECT 1"` and `Get-Service postgresql-x64-16`
  - Observation: Postgres service `Running`; query returns `1`. DB is healthy -> Hypothesis A DISPROVEN.
- Hypothesis B: The database connection string / env var name does not match what the app reads (config contract mismatch).
  - Command: compare `api/.env` keys vs `api/app/config.py` field `database_url` (pydantic BaseSettings maps `database_url` <- `DATABASE_URL`)
  - Observation: .env defines `DB_URL`, not `DATABASE_URL`; pydantic therefore reports `database_url Field required` at import time -> Hypothesis B CONFIRMED. The startup error described a missing/incorrect DB config, but the real cause was an env-var name mismatch, not the database.
- Fix: rename the .env variable `DB_URL` back to `DATABASE_URL` so the runtime env contract matches the code (established convention wins).
- Verification proof: restart API; `curl -s http://localhost:8000/health` -> `{"ok":true}`; app boots cleanly.

## Bug 2 - Pagination Is Broken (duplicate items across page boundary)

- Symptom: the last item on page 1 (offset 4) also appears as the first item on page 2 (offset 5). Observed: page 1 ends with `wjQcVY`, page 2 starts with `wjQcVY`.
- Hypothesis A: The OFFSET calculation is wrong (off-by-one / overlap injected into the offset).
  - Command: `curl -s "http://localhost:8000/links?offset=0&limit=5"` and `offset=5&limit=5`; inspect `list_links` offset math
  - Observation: `offset - 1` when offset>0 caused page 2 to re-read page 1's last row -> overlap by exactly one record -> Hypothesis A CONFIRMED.
- Hypothesis B: The sort order is unstable, so the same row lands in different positions across queries.
  - Command: run the page-1 and page-2 queries back-to-back, compare ORDER BY; check determinism
  - Observation: ORDER BY `created_at DESC, id DESC` is deterministic (id tiebreaker present) -> Hypothesis B DISPROVEN. No reordering between identical queries.
- Fix: correct the offset computation so page N starts at `(N-1)*pageSize` with no overlap (remove the injected `offset-1` shift); keep the deterministic sort.
- Verification proof: request pages with limit=5 across all 10 links -> collected 10 items, 10 unique, 0 duplicates; overlaps p1/p2 = 0 and p2/p3 = 0.

## Bug 3 - Intermittent Pagination Duplicates Under Concurrent Inserts

- Symptom: while records are inserted concurrently, paging across `GET /links` intermittently returns the same link on two pages (or skips one). The Bug 2 off-by-one fix was correct, so something else pagination depends on is wrong.
- Hypothesis A: OFFSET math is still wrong.
  - Command: re-inspect `list_links` offset/limit
  - Observation: offset math is `offset(offset).limit(limit)` with no `offset-1` shift -> correct -> Hypothesis A DISPROVEN (confirms the module's clue).
- Hypothesis B: The sort order is not a total order. Pagination is only stable if rows have a deterministic global ordering; `ORDER BY created_at DESC` alone is non-unique when rows tie on `created_at` (concurrent inserts can share a timestamp), so the DB is free to return tied rows in a different order between queries and a tie can straddle a page boundary -> intermittent duplicates.
  - Command: remove the `id` tiebreaker (inject the bug), force ties by updating a batch of rows to the same `created_at`, then page with limit=5 collecting all IDs (`scripts/repro_pagination.py`).
  - Observation: first traversal detected duplicates immediately: `total=111 collected=111 dups=[12,46,45,44,43,...] missing={16,72..95}` -> Hypothesis B CONFIRMED.
- Root cause: offset pagination relies on (1) correct offset math, (2) LIMIT, and (3) a **deterministic, unique sort key**. Without a unique tiebreaker (`id`), ties in the sort column make page boundaries non-deterministic under concurrent inserts.
- Fix: restore the deterministic total order `ORDER BY created_at DESC, id DESC` (the id tiebreaker guarantees a unique position for every row).
- Verification proof: with the tiebreaker restored, re-run the tie-injection repro across 3 rounds x 10 traversals (plus 3 more rounds) -> all traversals clean, no duplicates, every page boundary stable.

## FIX step - Deterministic Ordering Is Required (root-cause class)

- The module's FIX step confirms the bug class: pagination with NO ORDER BY is non-deterministic ordering -> results may be reordered by concurrent inserts or internal data reorganization -> silent duplicates/skips. Fix: add deterministic ordering (ORDER BY id).
- Reproduction on this fork: our native Postgres returns stable append/heap order for a small table, so a bare no-ORDER-BY query cannot be forced to reorder at this scale (reorg test: UPDATE-all + VACUUM across 20 rounds -> page-0 content never changed). This is exactly the module's warning: such bugs "pass all tests in development... and only break in production" under load. The reproducible manifestation on this machine is the Bug 3 unstable-sort variant (ties without a unique tiebreaker), which failed immediately under forced ties.
- Fix applied: `list_links` now orders by `Link.id.desc()` (deterministic total order) instead of relying on physical row order.
- Verification proof (fixed state): same-query-twice under a concurrent-inserter thread -> 0/40 rounds returned a different order; atomic 3-page partition check (inserts paused during reads) -> 0/30 rounds with duplicates, every item exactly once; pytest -> 15 passed.
