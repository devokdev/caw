"""Module 4 VERIFY: 2000-request memory growth check (Bug #6)."""
import logging
import tracemalloc

from fastapi.testclient import TestClient

from app.main import app

logging.getLogger("linkops").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)

tracemalloc.start(10)


def traced_mb():
    current, _ = tracemalloc.get_traced_memory()
    return current / 1024 / 1024


def main():
    client = TestClient(app)
    token = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "alice-password"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(50):
        client.get("/links", headers=headers)

    start = traced_mb()
    print(f"traced memory after warmup (50 reqs): {start:.2f} MB")
    for _ in range(2000):
        client.get("/links", headers=headers)
    end = traced_mb()
    print(f"traced memory after +2000 reqs:       {end:.2f} MB")
    print(f"Delta: {end - start:+.2f} MB")
    print("OK: delta small (< 50MB)" if (end - start) < 50 else "LEAK SUSPECTED")


if __name__ == "__main__":
    main()