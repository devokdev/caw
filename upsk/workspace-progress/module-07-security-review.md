# Module 07 — Comprehensive Security & Architecture Review

**Skill:** AI-Augmented Engineering | **Decision:** B — AI-assisted scan + manual critical path

## Scope

Full system-level review of every endpoint, model, and service produced by AI agents across Modules 02–06: auth, links, redirect, analytics, teams, invitations, comments, mentions, notifications, audit log, cache, rate limiting, background jobs. Verified empirically against the running service (all 119 tests + live probes).

---

## Security Review

### 1. Auth Check Audit (endpoint map)

| ENDPOINT | AUTH CHECK | AUTHORIZATION CHECK | STATUS |
|---|---|---|---|
| POST /auth/login | rate-limited (IP) | — (public login) | OK |
| POST /links | `get_current_user` | any authenticated user (owner) | OK |
| GET /links | `get_current_user` | owner-scoped query (`created_by`) | OK |
| GET /links/search | `get_current_user` | owner-scoped query | OK |
| GET /links/{id} | `get_current_user` | `get_link(db,id,user.id)` owner check | OK |
| PATCH /links/{id} | `get_current_user` | `get_link` owner check | OK |
| DELETE /links/{id} | `get_current_user` | `get_link` owner check | OK |
| GET /links/{id}/analytics | `get_current_user` + rate limit | `get_link` owner check | OK |
| GET /r/{code} | rate-limited (IP) | public redirect | OK |
| POST /teams | `get_current_user` | any authenticated user | OK |
| POST /teams/{id}/members | `get_current_user` | `require_owner_or_admin` | OK |
| GET /teams/{id}/members | `get_current_user` | `require_owner_or_admin` | OK |
| PATCH /teams/{id}/members/{uid}/role | `get_current_user` | `require_owner` | OK |
| DELETE /teams/{id}/members/{uid} | `get_current_user` | `require_owner` | OK |
| POST /teams/{id}/invitations | `get_current_user` | `require_owner_or_admin` | OK |
| POST /teams/{id}/invitations/{token}/accept | `get_current_user` | token + email-match + pending + unexpired | OK |
| GET /teams/{id}/invitations | `get_current_user` | `require_owner_or_admin` | OK |
| DELETE /teams/{id}/invitations/{iid} | `get_current_user` | `require_owner` | OK |
| GET /teams/{id}/audit | `get_current_user` | `require_owner_or_admin` | OK |
| GET /audit | `get_current_user` | owner/admin teams + own actions | FIXED |
| POST /links/{id}/comments | `get_current_user` | `get_link(db,id,user.id)` owner check | FIXED |
| GET /links/{id}/comments | `get_current_user` | `get_link(db,id,user.id)` owner check | FIXED |
| PATCH /comments/{id} | `get_current_user` | author check (`author_id == caller`) | OK |
| DELETE /comments/{id} | `get_current_user` | author check | OK |
| GET /mentions/parse | `get_current_user` | any authenticated user | OK |
| GET /notifications | `get_current_user` | `Notification.user_id == caller` | OK |
| PATCH /notifications/{id}/read | `get_current_user` | `Notification.user_id == caller` | OK |

### 2. Input Validation Audit

| ENDPOINT | FIELD | VALIDATION | STATUS |
|---|---|---|---|
| POST /links | long_url | scheme http/https, host present, no userinfo, no control chars, max 2048 | OK |
| POST /links | expires_at | tz-normalized, must be future | OK |
| POST /links | tags | max 50, each max 50 chars | OK |
| POST /teams | name | trimmed, 1–100 chars | OK |
| POST /teams/{id}/members | email | EmailStr | OK |
| POST /teams/{id}/members | role | Literal admin/member/viewer | OK |
| PATCH role | role | Literal admin/member/viewer | OK |
| POST /teams/{id}/invitations | email | EmailStr | OK |
| POST comments | body | trimmed, 1–4000 chars | OK |
| GET /links/search | q | max 200 chars | OK |
| GET /mentions/parse | text | no constraint — parse-only, harmless | OK |

### 3. IDOR Check

| ENDPOINT | RESOURCE ID | OWNERSHIP CHECK | STATUS |
|---|---|---|---|
| GET/PATCH/DELETE /links/{id} | linkId | `get_link` (owner) | OK |
| GET /links/{id}/analytics | linkId | `get_link` (owner) | OK |
| GET /links/{id}/comments | linkId | `get_link` (owner) | FIXED (was missing) |
| POST /links/{id}/comments | linkId | `get_link` (owner) | FIXED (was missing) |
| PATCH/DELETE /comments/{id} | commentId | `_authorize_comment` author check | OK |
| GET /teams/{id}/audit | teamId | `require_owner_or_admin` | OK |
| GET /audit | — | owner/admin + own actions | FIXED (was member-wide) |
| GET /notifications | — | user-scoped | OK |
| PATCH /notifications/{id}/read | notifId | user match | OK |
| GET /teams/{id}/members | teamId | `require_owner_or_admin` | OK |

### 4. Secrets Audit
No hardcoded keys, tokens, DB credentials, or signing secrets in any generated file. JWT secret is validated by `Settings._validate_jwt_secret` (>=32 chars, rejects placeholders). `config.py` default `"replace-me-locally"` is rejected by the validator unless overridden — safe to ship. No stack traces in API responses (central `error_envelope` + redaction; unhandled exceptions return generic 500). Request logs redact bearer tokens, passwords, secrets via `errors.redact()`. **OK.**

### 5. Dependency Audit
All dependencies are well-known, actively maintained, and pinned: fastapi, sqlalchemy 2.0, pydantic/pydantic-settings, pyjwt, redis, celery, psycopg2-binary, uvicorn, email-validator, python-dotenv. No unnecessary "default-choice" deps; celery is justified by the async analytics pipeline. No known-vulnerability scan artifacts in repo (no lockfile audit run available offline). **OK.**

---

## Architecture Review

### 1. Pattern Consistency
- All routers use FastAPI `APIRouter` + `Depends(get_current_user)` + `Depends(get_db)`; consistent with original auth/links routers.
- DB access: services use SQLAlchemy 2.0 `select()` style matching `links_service`. No raw SQL introduced. **OK.**
- Error handling: single `error_envelope` shape via global exception handlers; no divergent formats found. **OK.**
- Services layer: teams, comments, mentions, audit all expose public service functions; routers stay thin. **OK.**

### 2. Naming Consistency
- Tables: `comments`, `notifications`, `audit_log` — consistent plural/snake_case with `teams`, `links`, `click_events`. **OK.**
- Functions: `create_comment`, `list_comments`, `update_comment`, `delete_comment` mirror `create_team`, `list_members`, etc. **OK.**
- Audit actions use `{resourceType}.{action}` (e.g. `comment.created`, `team.member_added`) — matches the system-level contract written in Module 6. **OK.**

### 3. Error Handling Consistency
All 4xx/5xx flow through the global handlers → `{"error": {"code", "message", "request_id"}}`. Comment/audit/team errors raise `HTTPException` with status + detail, consistent with links. **OK.**

### 4. Test Coverage Map

| FEATURE | UNIT | INTEGRATION | AUTH | EDGE CASES | CRITICAL GAP |
|---|---|---|---|---|---|
| Auth/JWT | Yes | Yes | Yes | Yes (tamper, expiry, garbage) | — |
| Links CRUD/validation | Yes | Yes | Yes | Yes (control chars, userinfo, past expiry) | — |
| Redirect/cache invalidation | Yes | Yes | Yes | Yes (stale populate, delete/update invalidate) | — |
| Analytics/retention | Yes | Yes | n/a | Yes (dedup, purge) | — |
| Teams/roles/invitations | Yes | Yes | Yes | Yes (dup, wrong-email, reuse) | — |
| Comments/mentions/notifications | Yes | Yes | Yes | Partial | @mention w/ unknown handle (resolved = no-op, OK) |
| Audit log | Yes | Yes | Yes | Yes | — |
| Rate limiting | Yes | Yes | n/a | Yes | in-memory store = per-process only (documented) |
| **Security review fixes** | **Yes** | **Yes** | **Yes** | **Yes** | **closed** |

---

## Findings (prioritized)

### F1 — CRITICAL — Security — Comment IDOR
**Description:** `POST /links/{link_id}/comments` and `GET /links/{link_id}/comments` performed no ownership check on the target link. Any authenticated user could create and read comments on any other user's links by enumerating link IDs.
**Impact:** Confidential comment data read by strangers; comment spam/abuse on any user's resources; the classic "fetch by id without verifying access" IDOR pattern.
**Proof:** Live probe — bob@example.com created a comment on alice's link (HTTP 201) and listed its comments (HTTP 200).
**Fix:** Routes now call `links_service.get_link(db, link_id, user.id)` (owner-verified lookup) before create/list; foreign users and nonexistent links return 404. Regression tests: `test_comment_on_others_link_forbidden`, `test_comment_on_nonexistent_link_not_found`, `test_owner_still_can_comment_and_list`.

### F2 — HIGH — Security/Data Integrity — Expired links still redirect
**Description:** `get_link_by_code` did not filter on `expires_at`, so a link past its expiry continued to redirect (302) forever. The cache could also serve expired targets up to TTL.
**Impact:** Expiry is a core product guarantee (used for temporary/shared links); broken expiry undermines the delete/expire contract and can serve content that should be gone.
**Proof:** Live probe — set a link's `expires_at` in the past; `/r/{code}` returned 302 to the long URL.
**Fix:** `get_link_by_code` now excludes `expires_at <= now`; cache payloads embed expiry and `get_redirect_target` refuses expired payloads (treated as a miss → DB lookup → 404). Regression test: `test_expired_link_does_not_redirect`.

### F3 — MEDIUM — Security — Audit log over-exposure via /audit
**Description:** `GET /audit` exposed every audit entry for any team the caller merely belonged to (any role, incl. viewer/member), while the scoped `GET /teams/{id}/audit` correctly required owner/admin. Audit `details` include PII such as `invitee_email` (e.g. `team.invitation_created`).
**Impact:** Non-admin members could read invitee email addresses and the full team activity trail — an authorization inconsistency leaking PII.
**Proof:** Live probe — bob (member) saw `team.invitation_created` with `details: {"invitee_email": "bob@example.com"}` via `/audit`; now 0 such entries.
**Fix:** `/audit` now includes team entries only for teams where the caller is owner or admin (matches scoped endpoint), plus the caller's own actions. Regression tests: `test_plain_member_does_not_see_team_audit_via_audit`, `test_owner_sees_team_audit_via_audit`.

### F4 — LOW — Architecture — Rate limiter is in-process only
**Description:** `InMemoryStorage` is single-process; multi-worker deployments bypass per-IP limits.
**Impact:** Login/redirect rate limits not global across instances.
**Fix plan (future):** Swap to Redis-backed `RateLimitStorage` (interface already defined). Documented as known constraint.

### F5 — LOW — Data Integrity — Comment references not FK-constrained
**Description:** `Comment.target_id` is a plain BigInteger; deleting a link leaves orphan comments.
**Impact:** Orphaned comments/audit rows after link deletion.
**Fix plan (future):** Add FK/cascade policy or a soft-delete tombstone; currently mitigated by owner-verified reads.

### F6 — LOW — Test Coverage — Mention notification payload assertions thin
**Description:** Notification `payload` structure (actor_id, comment_id) is asserted only via action presence, not payload shape.
**Impact:** Payload regressions could slip.
**Fix plan (future):** Assert `payload` fields in the mention integration test.

---

## Verification

- 119 tests pass (`python -m pytest`, api dir).
- Live probes after deploy:
  - `POST /links/12866/comments` as bob → 404 (was 201)
  - `GET /links/12866/comments` as bob → 404 (was 200)
  - `POST /links/12866/comments` as alice → 201 (owner unaffected)
  - `/r/{expired}` → 404 (was 302)
  - bob `/audit` → 0 invitee-PII entries (was leaking)
- New regression file: `api/tests/test_module7_security.py` (6 tests).