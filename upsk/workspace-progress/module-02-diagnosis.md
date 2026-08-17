# Module 02 Diagnosis Notes (Logging & Timezone)

Lab vehicle: checkpoint fork of the system-design URL shortener (FastAPI, native Postgres).

## Bug #3 - Log Level Misconfigured

- Symptom class: error/HTTP lines appear with no corresponding "request received" / "response sent" lines. Root cause pattern: config hardcodes a level override (WARN) that shadows the LOG_LEVEL env var because the config lookup is checked first (config value `or` env, short-circuits).
- Investigation: `LOG_LEVEL=info` present in `api/.env`. `app/config.py` defines `log_level: str = "info"` and reads it from env with NO hardcoded override in `main.py::_configure_logging` (`getattr(logging, settings.log_level.upper(), logging.INFO)`).
- Finding: the fork carries no hardcoded level override, so env is respected. Live verification: made requests against the running API; `api_err.log` shows `INFO linkops {"msg": "request received", ...}` and `INFO linkops {"msg": "response sent", ..., "status": 200}` pairs for every request - request in, processing, response out. No orphan error lines.
- Status: bug class confirmed absent / already remediated in fork (inherited from System Design hardening).

## Bug #4 - Timestamp Timezone Mismatch

- Symptom class: links created around midnight UTC intermittently 404 for a few hours then "magically" work. Root cause pattern: app logs UTC but DB stores local time (or naive), and lookups compare UTC boundaries against local values.
- Investigation:
  - DB: `SHOW timezone` -> `UTC`; migration `migrate.py` runs `ALTER DATABASE upsk_sdf SET timezone TO 'UTC'` and converts `created_at`/`expires_at`/`clicked_at` to `timestamptz`.
  - Connection: `app/database.py` passes `-c timezone=UTC` as a connection option.
  - Models: `created_at` is `DateTime(timezone=True)` with `server_default=func.now()`.
  - App-side comparisons: `datetime.now(UTC)` everywhere (security.py, schemas/link.py, routers/redirect.py, analytics.py).
- Live verification: `now()` -> `2026-08-17 17:18:38.738445+00:00` (aware, UTC); latest `created_at` -> `2026-08-17 17:07:20.482089+00:00` (aware, UTC). Log timestamps and DB timestamps both UTC and matching. No midnight boundary gap possible.
- Status: bug class confirmed absent / already remediated in fork.

## Lesson
Both bugs are the same class: two layers disagreeing on a contract (level filter vs logger, UTC vs local time). The fix discipline - normalize at the boundary (env-only config, UTC-only storage) - is already in place in this fork.