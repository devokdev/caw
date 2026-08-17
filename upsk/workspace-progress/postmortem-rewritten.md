# Postmortem — Database Outage (rewritten, blameless)

Date: 2026-03-15
Severity: SEV2 (partial auth outage, no data loss)
Status: remediated

## Summary

A migration applied to the users table dropped a serving index, causing query
timeouts on login and session paths. The failure was detected by users before
monitoring, restored by rollback within the window, and followed up with
structural gates that make this class of failure unreachable.

## Timeline (UTC)

| Time (UTC) | Event |
|---|---|
| 2026-03-15 13:58 | Migration MR merged after a required-reviewer approval (only reviewer available) |
| 2026-03-15 14:02 | Migration `alembic upgrade head` applied to production by the release tool |
| 2026-03-15 14:03 | Index on users.email dropped by migration step M-4 (schema-diff not dry-run in CI) |
| 2026-03-15 14:05 | Login p95 latency rises from 40ms to 9.8s; error rate 0.4% |
| 2026-03-15 14:09 | User reports; support tickets spike to 37 in 15 min |
| 2026-03-15 14:12 | On-call confirms query timeouts on users.email lookups; monitoring lacked an index-liveness probe |
| 2026-03-15 14:17 | Rollback: `alembic downgrade` restores the index |
| 2026-03-15 14:19 | Login p95 back to 42ms; error rate normal |
| 2026-03-15 14:31 | Affected window confirmed: 14:03–14:19 UTC (16 minutes); ~2,300 users experienced login failures |

## Root cause (systemic)

The deployment pipeline did not require migrations to pass against a staging
database with production-like data before applying to production, and the
migration tooling did not enforce a schema-diff dry-run or index-liveness
assertion in CI. A migration that dropped an index therefore reached
production unverified, because no system gate distinguished 'valid migration'
from 'migration that breaks serving queries'.

Why local testing would not have prevented it: the bug manifested only with
production-scale data and query patterns; local data was too small for the
missing index to matter. The gap is the absence of a staging gate with
production-like data, not individual diligence.

## Contributing factors (system gaps)

- CF1. The migration pipeline did not require a schema-diff dry-run or
  automated migration test against a disposable staging database before
  merge/deploy.
- CF2. The CI pipeline had no automated migration run on staging with
  production-like data volume, so index-dropping migrations were invisible.
- CF3. The code review requirement was not enforced by a mandatory-reviewer
  gate on migration files (a lone approver could merge).
- CF4. The release process had no deployment freeze policy before weekends,
  so a high-risk migration could ship on a Friday.
- CF5. Monitoring had no index-liveness/query-latency alert on the users
  table; the failure surfaced via user reports before any automated signal.

## Impact

- ~2,300 users (est. from login error-rate sampling) unable to log in.
- Duration 16 minutes (14:03–14:19 UTC).
- Login p95 degraded from 40ms to 9.8s.
- No data loss. No security exposure.

## Remediations (owned, deadlined, checkable)

| # | Action | Owner | Deadline | Checkable outcome |
|---|---|---|---|---|
| R1 | Add CI migration job running `alembic upgrade head` against a disposable staging DB (production-like seed volume) and assert schema integrity before merge | platform | 2026-03-22 | CI blocks merge on migration failure |
| R2 | Add automated schema-diff dry-run to the migration job; fail on unexpected index/constraint drops | platform | 2026-03-22 | CI reports schema diff, fails on index removal |
| R3 | Enable required-reviewers branch protection for all migration PRs (min 2 approvals) | eng-lead | 2026-03-18 | GitHub blocks merge without 2 approvals |
| R4 | Enforce a Thursday-cohort deployment freeze: no migration deploys after Thursday 12:00 UTC; Fridays reserved for rollback/recovery | eng-lead | 2026-03-18 | Release tool rejects Friday migration deploys |
| R5 | Add index-liveness + login-latency alert (p95 > 1s for 5 min → SEV2 page) | platform | 2026-03-22 | Alert fires before user reports in drill |

## Lessons learned

- Migrations are code: they must pass the same staging gate, dry-run, and
  review requirements as application code.
- The system that reports health must not depend on the thing it monitors.
- A lone approver on migration files is a structural hole, not a personal one.

## Blame check

No individual is named. Every factor and remediation changes a system gate,
not human behavior.