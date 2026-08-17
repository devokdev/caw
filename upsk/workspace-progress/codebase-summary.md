# AI-Augmented Engineering — Agent Deliverable: Codebase Summary & Extension Points

## Codebase summary

- Framework: FastAPI (Python 3.11), uvicorn ASGI server, SQLAlchemy 2.x ORM with
  declarative models, async Redis (redis.asyncio) for the redirect cache,
  Celery (kombu/redis broker) for the analytics click queue.
- App layout: `api/app/main.py` (app factory, exception envelope, health/ready),
  `api/app/routers/{auth,links,redirect,analytics}.py`, `api/app/services/`
  (cache, analytics, links_service), `api/app/schemas/` (pydantic),
  `api/app/models.py`, `api/app/database.py` (single engine + SessionLocal),
  `api/app/security.py` (JWT), `api/app/errors.py` (envelope + redaction),
  `api/app/ratelimit.py` (in-memory fixed-window).
- Auth: JWT Bearer (HS256 via `security.py`), dependency `deps.py:get_current_user`
  injects the current User; protected endpoints return 401 with an
  `error_envelope` JSON when the token is missing/invalid. Roles are NOT modeled
  yet — only users exist.
- Data model: `User` (email/password hash), `Link` (code unique, long_url,
  created_by FK, tags, expires_at, soft fields), `ClickEvent` (link_id FK,
  unique event_key, ip_hash, UA, referrer, clicked_at). No Team/Membership/
  Invitation/AuditLog tables exist.
- Migrations: `api/migrations/migrate.py` (SQL-based, adds columns/indexes
  idempotently).
- Tests: pytest, FastAPI TestClient, ~76 tests; `pytest.ini` present.
- Config: `api/app/config.py` pydantic-settings reading `.env` (database_url,
  redis_url, jwt_secret, redirect_cache_ttl_seconds=300, etc.).
- Queues/worker: `api/app/worker.py` Celery app, `services/analytics.py` tasks
  (record_click idempotent on event_key, purge_old_clicks).

## Extension points for the Team Collaboration scenario

1. **Team & membership tables** — add to `models.py` + migration:
   `Team` (id, name, created_by, created_at), `TeamMember` (team_id, user_id,
   role ENUM/text: owner/admin/member, unique(team_id,user_id)).
2. **Invitation flow** — `Invitation` (id, team_id, inviter_id, invitee_email,
   token unique, expires_at, used_at, accepted_by, created_at). Hard constraint:
   token must be one-time-use + expiry + acceptance only by the invitee
   (prevents replay/unauthorized acceptance). Endpoints under a new
   `app/routers/teams.py` following the links.py pattern (Depends(get_current_user),
   rate limit, schema validation).
3. **Role enforcement** — a reusable dependency `require_role(role)` chained after
   `get_current_user`, checking membership row; explicit and verifiable on every
   protected action (create team, invite, change role, delete).
4. **Comment threads + @mentions** — `Comment` (id, thread_id, author_id, body,
   mentions as JSON or M2M). Later module; defer.
5. **Real-time activity feed** — needs ordered delivery + reconnect consistency;
   candidates: Redis Streams (order + consumer groups) or DB table + long-poll.
   Later module; defer.
6. **Audit log** — `AuditLog` (id, actor_id, action, target_type, target_id,
   before/after JSON, ip, created_at) appended on sensitive actions (invite,
   accept, role change, delete). Insert in the same transaction as the action.
7. **Routing pattern to follow** — new router mounted in `main.py` include_router
   block; errors via `error_envelope`; schemas with pydantic Field constraints;
   rate limit on invite endpoint to blunt replay/abuse.
8. **Config** — new settings (invite token TTL, audit retention) added to
   `config.py` pydantic-settings with env-backed defaults.

## Verification claims (to be spot-checked)

- C1: `deps.py:get_current_user` exists and injects User; protected routes use it.
- C2: `errors.py` defines `error_envelope`; main.py registers exception handlers.
- C3: models.py defines User/Link/ClickEvent; no Team tables.
- C4: migrations/migrate.py exists and is idempotent SQL.
- C5: requirements.txt lists fastapi, sqlalchemy, pydantic-settings, celery, redis.
- C6: `config.py` uses pydantic-settings with env fields (database_url, redis_url).