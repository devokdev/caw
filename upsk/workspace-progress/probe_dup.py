"""Module 6 BREAK: reproduce the reported 'duplicate analytics for re-created
links' scenario against the fork.

Reported symptom: delete a link, re-create with the same short code, analytics
job processes twice, click counts double. Hypothesis for THIS fork: the click
idempotency lives in the Postgres unique(event_key), not in a Redis dedup key
that cache invalidation touches -- so the cache.del() in the delete handler
cannot destroy dedup state, and counts stay correct.
"""
import httpx

BASE = "http://localhost:8000"


def login():
    with httpx.Client(base_url=BASE, timeout=30) as c:
        r = c.post("/auth/login", json={"email": "alice@example.com", "password": "alice-password"})
        return r.json()["access_token"]


def main():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=BASE, timeout=30) as c:
        r = c.post("/links", headers=headers, json={"long_url": "https://dup.example/a"})
        link = r.json()
        code = link["code"]
        print(f"created link id={link['id']} code={code}")

        r1 = c.get(f"/r/{code}", follow_redirects=False)
        r2 = c.get(f"/r/{code}", follow_redirects=False)
        print(f"clicked twice before delete: {r1.status_code} {r2.status_code}")

        a1 = c.get(f"/links/{link['id']}/analytics", headers=headers).json()
        print(f"analytics before delete: total_clicks={a1['total_clicks']}")

        r = c.delete(f"/links/{link['id']}", headers=headers)
        print(f"deleted link id={link['id']}: {r.status_code}")

        r = c.post("/links", headers=headers, json={"long_url": "https://dup.example/b"})
        link2 = r.json()
        code2 = link2["code"]
        print(f"re-created link id={link2['id']} code={code2} (same code as before: {code2 == code})")

        r1 = c.get(f"/r/{code2}", follow_redirects=False)
        r2 = c.get(f"/r/{code2}", follow_redirects=False)
        print(f"clicked twice after recreate: {r1.status_code} {r2.status_code}")

        a2 = c.get(f"/links/{link2['id']}/analytics", headers=headers).json()
        print(f"analytics after recreate: total_clicks={a2['total_clicks']} (expect 2, not 4)")

        a_old = c.get(f"/links/{link['id']}/analytics", headers=headers)
        print(f"old deleted link analytics request: {a_old.status_code}")


if __name__ == "__main__":
    main()