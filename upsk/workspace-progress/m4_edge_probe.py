import json

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

alice = client.post(
    "/auth/login", json={"email": "alice@example.com", "password": "alice-password"}
).json()["access_token"]
ha = {"Authorization": f"Bearer {alice}"}

results = []

r = client.post("/teams", json={"name": "team-x-unicode"}, headers=ha)
results.append(("unicode-ish create", r.status_code, r.json()))

r = client.post("/teams", json={"name": "x" * 300}, headers=ha)
results.append(("name 300 chars", r.status_code, r.json()))

r = client.get("/teams/-1/members", headers=ha)
results.append(("negative team id", r.status_code, r.json()))

r = client.get("/teams/0/members", headers=ha)
results.append(("team id 0", r.status_code, r.json()))

r = client.post("/teams", json={"name": "   "}, headers=ha)
results.append(("whitespace name", r.status_code, r.json()))

r = client.post("/teams", json={"name": "rolecase-team"}, headers=ha)
tid = r.json()["id"]
r = client.post(f"/teams/{tid}/members", json={"email": "bob@example.com", "role": "ADMIN"}, headers=ha)
results.append(("role ADMIN uppercase", r.status_code, r.json()))

r = client.post(f"/teams/{tid}/members", json={"email": "bob@example.com", "role": "member"}, headers=ha)
results.append(("dup bob member", r.status_code, r.json()))

with open("m4_probe_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

for label, code, body in results:
    print(f"{label}: {code} {json.dumps(body, ensure_ascii=False)}")