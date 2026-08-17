"""Deterministic reproduction of the silent cache-race (module 3 BREAK).

Canonical Bug #5 part 2 (stale last_accessed_at) is structurally absent in
this fork: clicks are event-sourced rows with their own clicked_at, and
analytics derives last_clicked_at as max(clicked_at) -- no shared timestamp
column to corrupt.

The SAME race class (a concurrent read-then-write that leaves silently stale
state, no errors, no wrong counts) does exist in the redirect cache:
_resolve_with_cache reads the DB, then populates the cache. update_link
commits the new URL, then invalidates the cache. Interleave them and a stale
populate can land AFTER the invalidation, so the cache serves the OLD URL.

Deterministic interleaving:
  R: read old_url from DB (redirect cache miss path)
  W: update link to new_url + invalidate cache   (committed)
  R: set_redirect_target(old_url)                (lands after invalidation)
  => subsequent GET /r/{code} serves old_url for up to TTL -- silently.
"""
import asyncio
import sys

import httpx
import psycopg2

from app.database import SessionLocal
from app.services import cache as cache_service
from app.services import links_service

DB_URL = "postgresql://postgres:postgres@localhost:5432/upsk_sdf"


def read_db_url(db, code: str):
    return links_service.get_link_by_code(db, code).long_url


def make_link(db, marker: str):
    from app.schemas.link import CreateLinkRequest

    link = links_service.create_link(
        db, CreateLinkRequest(long_url=f"https://example.com/{marker}-old"), owner_id=1
    )
    return link


def main():
    db = SessionLocal()
    marker = "cache-race-x"
    link = make_link(db, marker)
    code = link.code
    old_url = read_db_url(db, code)
    print(f"link {code}: old_url={old_url}")

    # R1: redirect path reads DB (cache miss) but has NOT written cache yet.
    version_before_read = asyncio.run(cache_service.get_redirect_version(code))
    db_url_before = read_db_url(db, code)
    print(f"R reads DB (version={version_before_read}) -> {db_url_before}")

    # W: admin update commits new_url then invalidates.
    from app.schemas.link import CreateLinkRequest

    updated = links_service.update_link(
        db, link.id, 1, f"https://example.com/{marker}-new", None
    )
    asyncio.run(cache_service.invalidate_redirect_target(code))
    print(f"W commits new_url={updated.long_url}, invalidated cache")

    # R2: the stale redirect path tries to write the OLD url it read earlier,
    # guarded by the version captured before its DB read.
    asyncio.run(
        cache_service.set_redirect_target(
            code, link.id, db_url_before, expected_version=version_before_read
        )
    )
    print(f"R attempts stale write (expected_version={version_before_read}) -> {db_url_before}")

    # Observe: what does the live redirect endpoint serve now?
    with httpx.Client(follow_redirects=False, timeout=10) as client:
        resp = client.get(f"http://localhost:8000/r/{code}")
    served = resp.headers.get("location")
    expected = updated.long_url
    print(f"GET /r/{code} -> {resp.status_code} location={served}")
    print(f"expected: {expected}")
    if served == expected:
        print("OK: serving new URL")
    else:
        print("SILENT DATA CORRUPTION: serving stale URL (race reproduced)")
        sys.exit(1) if len(sys.argv) > 1 and sys.argv[1] == "fail-on-stale" else None

    asyncio.run(cache_service.invalidate_redirect_target(code))
    db.close()


if __name__ == "__main__":
    main()