"""Module 4 BREAK: measure POST /links latency scaling with URL length/repeats."""
import time

import httpx

BASE = "http://localhost:8000"


def login():
    with httpx.Client(base_url=BASE, timeout=30) as c:
        r = c.post("/auth/login", json={"email": "alice@example.com", "password": "alice-password"})
        return r.json()["access_token"]


def main():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    cases = {
        "normal": "http://example.com/abcdef",
        "rep_1k": "http://example.com/" + "a" * 1000,
        "rep_10k": "http://example.com/" + "a" * 10000,
        "rep_50k": "http://example.com/" + "a" * 50000,
        "rep_100k": "http://example.com/" + "a" * 100000,
    }
    with httpx.Client(base_url=BASE, timeout=60) as c:
        for name, url in cases.items():
            best = None
            for _ in range(3):
                t0 = time.perf_counter()
                r = c.post("/links", headers=headers, json={"long_url": url})
                dt = (time.perf_counter() - t0) * 1000
                best = min(best, dt) if best else dt
            print(f"{name:10s} len={len(url):6d} status={r.status_code} best={best:8.1f}ms")


if __name__ == "__main__":
    main()