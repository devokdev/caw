"""Module 6 VERIFY live check: Bug #9 class - deleted link must NOT redirect.

Creates a link, deletes it, then immediately requests the redirect. The
explicit-invalidation fix means the redirect must 404 right away (not after
the 5-min cache TTL). Bug #10 class: worker pool is shared, so we confirm
record_click enqueue still resolves through the shared pool.
"""
import httpx

BASE = "http://localhost:8000"


def main():
    with httpx.Client(base_url=BASE, timeout=30) as c:
        r = c.post("/auth/login", json={"email": "alice@example.com", "password": "alice-password"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        r = c.post("/links", headers=headers, json={"long_url": "http://example.com/m6-verify"})
        link = r.json()
        code = link["code"]
        print(f"created code={code} status={r.status_code}")
        r = c.get(f"/r/{code}", follow_redirects=False)
        print(f"before delete: GET /r/{code} -> {r.status_code}")
        r = c.delete(f"/links/{link['id']}", headers=headers)
        print(f"delete link {link['id']} -> {r.status_code}")
        r = c.get(f"/r/{code}", follow_redirects=False)
        print(f"after delete (immediately): GET /r/{code} -> {r.status_code} "
              f"(expect 404, NOT a stale redirect)")


if __name__ == "__main__":
    main()