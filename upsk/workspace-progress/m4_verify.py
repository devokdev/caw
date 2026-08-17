import json

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

alice = client.post(
    "/auth/login", json={"email": "alice@example.com", "password": "alice-password"}
).json()["access_token"]
bob = client.post(
    "/auth/login", json={"email": "bob@example.com", "password": "bob-password"}
).json()["access_token"]
ha = {"Authorization": f"Bearer {alice}"}
hb = {"Authorization": f"Bearer {bob}"}

# Setup: alice owns team T
T = client.post("/teams", json={"name": "verify-team"}, headers=ha).json()["id"]

results = {}

# Test 1: add a user who is already a member -> 409
client.post(f"/teams/{T}/members", json={"email": "bob@example.com", "role": "member"}, headers=ha)
r = client.post(f"/teams/{T}/members", json={"email": "bob@example.com", "role": "member"}, headers=ha)
results["t1_already_member"] = (r.status_code, r.json()["error"]["message"])

# Test 2: create team with empty name -> 400
r = client.post("/teams", json={"name": ""}, headers=ha)
results["t2_empty_name"] = (r.status_code, r.json()["error"]["code"])
r = client.post("/teams", json={"name": " "}, headers=ha)
results["t2_space_name"] = (r.status_code, r.json()["error"]["code"])

# Test 3: add member without auth -> 401
r = client.post(f"/teams/{T}/members", json={"email": "bob@example.com", "role": "member"})
results["t3_no_auth"] = (r.status_code, r.json()["error"]["code"])

# Test 4: bob (member, not owner/admin) tries member actions -> 403
r = client.post(f"/teams/{T}/members", json={"email": "alice@example.com", "role": "member"}, headers=hb)
results["t4_nonowner_add"] = (r.status_code, r.json()["error"]["code"])
r = client.get(f"/teams/{T}/members", headers=hb)
results["t4_nonowner_list"] = (r.status_code, r.json()["error"]["code"])
r = client.patch(f"/teams/{T}/members/{1}/role", json={"role": "admin"}, headers=hb)
results["t4_nonowner_patch"] = (r.status_code, r.json()["error"]["code"])

# Test 5: invalid email format -> 400
r = client.post(f"/teams/{T}/members", json={"email": "not-an-email", "role": "member"}, headers=ha)
results["t5_invalid_email"] = (r.status_code, r.json()["error"]["code"])

for k, v in results.items():
    print(f"{k}: {v[0]} {v[1]}")

with open("m4_verify_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)