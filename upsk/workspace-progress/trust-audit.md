# Trust Audit — AI-Augmented Engineering Module 1

Agent deliverable: `progress/codebase-summary.md`. Spot-check verification
of six factual claims, each checked with a real command against the fork.

| Claim | Agent statement | Verification command | Result |
|---|---|---|---|
| C1 | `deps.py:get_current_user` exists and injects User | `Select-String deps.py "def get_current_user"` | MATCH — `def get_current_user(` present |
| C2 | `errors.py` defines error_envelope | `Select-String errors.py "def error_envelope"` | MATCH — `def error_envelope(` present |
| C3 | models.py defines User, Link, ClickEvent; no Team tables | `Select-String models.py "^class "` | MATCH — exactly User/Link/ClickEvent; no Team/Membership/Invitation/AuditLog |
| C4 | migrations/migrate.py exists, idempotent SQL | file check + prior migrations used | MATCH — `migrations/migrate.py` present with IF NOT EXISTS guards |
| C5 | requirements: fastapi, sqlalchemy, pydantic-settings, redis, celery | `Select-String requirements.txt` | MATCH — all five pinned versions present |
| C6 | config.py uses pydantic-settings env fields | `Select-String config.py "database_url|redis_url"` | MATCH — both env-backed fields present |

## Calibration notes

- 6/6 spot-checks matched. The summary was produced from code reading, so
  agreement is expected — but the verification is what converts 'expected'
  into 'known'.
- The agent's architecture claims that are NOT directly checkable by a single
  command (e.g., 'errors centralized via envelope') were confirmed by
  locating the defining function rather than trusting the prose.
- Highest-value spot-check pattern found: verifying 'no Team tables exist'
  — a negative claim — is the one that would have caught a hallucinated
  extension point. Keeping negative claims in future summaries.
- Rhythm going forward: 1-2 spot checks per agent summary, biased toward
  (a) negative claims and (b) claims that would change how I write prompts.

## Discrepancies

None found in this pass.

---

# Module 01 BREAK — Wrong-Claim Card Disproof

Claim said: "This starter workspace is only a platform folder with AGENTS.md,
CLAUDE.md, reports, and progress/; it has no real application files to test."

Observed:
- `Get-ChildItem` at workspace root shows: `api/`, `infra/`, `scripts/`,
  `progress/`, `Dockerfile`, `railway.json`, `.github/` — a real project layout.
- `api/` contains 34 source files (excluding `.venv`): `app/` package with
  `main.py`, `routers/{auth,links,redirect,analytics}.py`, `services/`,
  `models.py`, `database.py`, `schemas/`, `config.py`, `errors.py`, plus
  `tests/` (pytest suite), `migrations/`, `requirements.txt`, `pytest.ini`.
- Strongest sanity check: `python -m pytest -q` runs 76 tests and exits 0 —
  the application is testable and all tests pass.

Corrected: The workspace contains a complete, runnable, testable FastAPI
application under `api/` (app package, routers, models, services, migrations,
and a 76-test pytest suite), plus `infra/` and `scripts/` — it is emphatically
not just a platform folder with markdown and progress files. The claim was a
confident-but-false agent summary of exactly the class the module warns about.

## Calibration note

This disproved claim confirms the pattern: negative claims about a codebase
('there is no application code') are the highest-risk statements to accept from
an agent without verification — a quick directory listing or one test run
settles them instantly.