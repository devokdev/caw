"""Minimal reproduction: concurrent redirects on a single short link.

Module 3 (Reproduction) -- Debugging & Incident Response.
Adapted to this fork (FastAPI on :8000, httpx client).
"""
import concurrent.futures
import sys

import httpx

SHORT_CODE = sys.argv[1] if len(sys.argv) > 1 else "sQGeMv"
CONCURRENCY = int(sys.argv[2]) if len(sys.argv) > 2 else 10
BASE_URL = f"http://localhost:8000/r/{SHORT_CODE}"


def make_request():
    with httpx.Client(follow_redirects=False, timeout=10) as client:
        resp = client.get(BASE_URL)
        return resp.status_code


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = [pool.submit(make_request) for _ in range(CONCURRENCY)]
        results = [f.result() for f in futures]

    successes = [r for r in results if r in (301, 302)]
    errors = [r for r in results if r == 500]
    other = [r for r in results if r not in (301, 302, 500)]

    print(f"Results: {len(successes)} redirects, {len(errors)} errors, "
          f"{len(other)} other ({sorted(set(other))})")
    if errors:
        print("BUG REPRODUCED: 500 errors under concurrent load")
    else:
        print("No errors this run. Try again or increase CONCURRENCY.")


if __name__ == "__main__":
    main()