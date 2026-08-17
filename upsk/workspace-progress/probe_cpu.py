"""Module 4 BREAK: profile POST /links with a long repeating-character URL."""
import cProfile
import io
import logging
import pstats

from fastapi.testclient import TestClient

from app.main import app

logging.getLogger("linkops").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)

LONG = "http://example.com/" + "a" * 5000 + "!"


def main():
    client = TestClient(app)
    token = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "alice-password"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pr = cProfile.Profile()
    pr.enable()
    r = client.post("/links", headers=headers, json={"long_url": LONG})
    pr.disable()

    print(f"status={r.status_code}")
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(25)
    print(s.getvalue())


if __name__ == "__main__":
    main()