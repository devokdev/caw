# Module 2 FIX — Interface Contracts

## Step 1: Where the fix belongs

The conflict: my Task 2 prompt said "owner is teams.owner_id" and "do not add a
members join table" — but Task 1's ACTUAL output created `Team.created_by`
(not `owner_id`) and a `team_members` join table with a `role` column
(admin/member/viewer). Task 1 was well-specified and built the richer model.
The bug was in Task 2's prompt, which was written from my ORIGINAL PLAN for
what Task 1 would produce, not from Task 1's actual output. Fix: revise Task 2
to build against the real schema, with the interface contract embedded
verbatim.

## Step 2: Interface contract (Task 1 → Task 2)

### Task 1 produces (actual, verified in DB):
- Table `teams`: id (BigInteger PK), name (String(100), NOT NULL),
  created_by (BigInteger FK → users.id, NOT NULL) [the OWNER], created_at
  (timestamptz, server_default now()).
- Table `team_members`: id (BigInteger PK), team_id (BigInteger FK →
  teams.id), user_id (BigInteger FK → users.id), role (String(20) NOT NULL,
  server_default 'member'), created_at. UniqueConstraint(team_id, user_id).
- Table `invitations`: id (BigInteger PK), team_id (FK → teams.id),
  inviter_id (FK → users.id), invitee_email (String(255)), token
  (String(64) UNIQUE), status (String(20), default 'pending'),
  expires_at (timestamptz), used_at (nullable), created_at.
- Owner is NOT automatically a team_members row — owner = teams.created_by.

### Task 2 expects:
- Table `team_members` exists with at minimum: team_id, user_id, role;
  role accepts 'admin' | 'member' | 'viewer'.
- The owner of a team is `teams.created_by`, not a column named `owner_id`.
- Membership check for permissions: caller is owner (teams.created_by) OR a
  team_members row with role 'admin'.
- Response schemas expose owner as `owner_id` mapped from `created_by`.

### Where both must agree:
- Roles: exactly admin | member | viewer.
- Permission rule: owner/admin manage membership; owner only changes roles /
  removes members.
- Adding a user already a member (or the owner) → 409. Unknown email → 404.
- The response `TeamResponse.owner_id` is presentational; the column is
  `created_by`.

## Step 3: Re-run the corrected Task 2 prompt

The corrected prompt embeds the contract verbatim, then re-invokes the agent.
The agent must build against `created_by` + `team_members`, with NO instruction
to invent an `owner_id` column or flat model. Re-run outcome (see
corrected-task2 run): endpoints built against real schema, tests green,
no prompt-reality divergence.

## Preventative rule (goes into every subsequent task prompt)

Every task prompt after Task 1 embeds the ACTUAL output of the upstream task
(exact table names, column names, paths, status codes) — never the plan's
assumptions. If a task discovers a schema divergence, the prompt is corrected
first, not the code silently.