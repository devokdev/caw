"""Module 4 probe: count SQL queries fired by GET /links (Bug #7 N+1 check)."""
import logging

from sqlalchemy import event

from app.database import engine
from app.main import app

from fastapi.testclient import TestClient

queries = []


@event.listens_for(engine, "before_cursor_execute")
def _capture(conn, cursor, statement, parameters, context, executemany):
    queries.append(statement.split("\n")[0].strip())


logging.getLogger("linkops").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)


def main():
    client = TestClient(app)
    token = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "alice-password"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    queries.clear()
    r = client.get("/links?limit=50", headers=headers)
    print(f"GET /links status={r.status_code} items={len(r.json()['items'])}")
    print(f"SQL statements fired: {len(queries)}")
    for q in queries:
        print(f"  {q[:100]}")
    queries.clear()

    r2 = client.get("/links?limit=50&offset=50", headers=headers)
    print(f"GET /links offset=50 items={len(r2.json()['items'])} SQL={len(queries)}")


if __name__ == "__main__":
    main()