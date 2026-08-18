# Module 08 BREAK Trace: "works on my machine, fails in CI"

## Symptom

The Module 07 role-escalation suite (`test_module7_role_escalation.py`, 11
tests) and the Module 08 integration test reference three users: alice, bob,
**carol**. Locally everything is green (147 passed). In CI, the database starts
empty and is seeded only by `api/migrations/migrate.py`. A test that needs a
user who does not exist fails with "user not found" (404 / 400).

## Root cause

`migrate.py` seeded exactly two dev users:

```
DEV_USERS = [
    {"email": "alice@example.com", "password": "alice-password"},
    {"email": "bob@example.com", "password": "bob-password"},
]
```

`carol@example.com` existed on my machine only because I created her manually
during Module 07 (needed a third non-owner user to prove the viewer/admin/member
role boundaries). The test suite was then written against a database that
contained carol. The AI-era version of this failure: the test generator looked
at the populated local database, saw three users, and wrote tests assuming all
three exist. It had no concept of environment independence — it wrote for the
environment it could see, which was mine.

## The environment-dependent assumption

- **Assumption:** `carol@example.com` / `carol-password` exists and can log in.
- **Where:** `test_module7_role_escalation.py` (11 tests use carol),
  `test_module8_permissions.py` (carol as invitee/member), and any
  three-user scenario.
- **Why it held locally:** I manually created carol in the running Postgres.
- **Why it breaks in CI:** CI runs `python migrations/migrate.py` on a fresh
  database. Before the fix, that seeded only alice and bob.

## Fix (already applied in BUILD)

`api/migrations/migrate.py` DEV_USERS now seeds all three users:

```
DEV_USERS = [
    {"email": "alice@example.com", "password": "alice-password"},
    {"email": "bob@example.com", "password": "bob-password"},
    {"email": "carol@example.com", "password": "carol-password"},
]
```

The migration is the single source of truth for seed data. Any user a test
depends on must be created by the migration, never by hand. The CI pipeline
runs migrations before pytest, so a fresh database now contains carol and the
role-boundary tests pass.

## Guard for the future

Rule: **a test may only reference data that the migration seeds or that the
test itself creates.** Before adding a new fixture user to a test, add it to
`DEV_USERS` in `migrate.py`. Verify environment independence by running the
suite against a database created only by migrations (which is exactly what CI
does).