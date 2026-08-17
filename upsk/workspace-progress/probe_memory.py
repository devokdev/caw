"""Module 4 profiling probe: memory growth (Bug #6) via tracemalloc.

Runs the real FastAPI app in-process through its TestClient (same process, so
tracemalloc sees the app's own allocations), fires 500-request batches, and
diffs tracemalloc snapshots between batches to show what grows.
"""
import logging
import tracemalloc

from fastapi.testclient import TestClient

from app.main import app
from app.services import analytics as analytics_service

logging.getLogger("linkops").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)

tracemalloc.start(10)


def snapshot_top(n=12):
    snap = tracemalloc.take_snapshot()
    top = snap.statistics("lineno")
    return [(s.size / 1024 / 1024, s.traceback.format()[0] if s.traceback else "?")
            for s in top[:n]]


def login(client):
    r = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "alice-password"},
    )
    return r.json()["access_token"]


def main():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Warm up so one-time module/import allocations settle.
    for _ in range(50):
        client.get("/links", headers=headers)

    print("--- after warmup (50 reqs) ---")
    for mb, loc in snapshot_top():
        print(f"{mb:8.3f} MB {loc}")

    for batch in (1, 2):
        for _ in range(500):
            client.get("/links", headers=headers)
        print(f"--- after +{500 * batch} reqs (total {50 + 500 * batch}) ---")
        for mb, loc in snapshot_top():
            print(f"{mb:8.3f} MB {loc}")

    print("done")


if __name__ == "__main__":
    main()