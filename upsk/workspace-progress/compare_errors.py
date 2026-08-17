import json

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

login = client.post(
    "/auth/login", json={"email": "alice@example.com", "password": "alice-password"}
)
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== EXISTING endpoint error: POST /links with bad payload ===")
r = client.post("/links", json={"long_url": "not-a-url"}, headers=headers)
print(r.status_code, json.dumps(r.json()))

print("=== EXISTING endpoint error: GET /links/999999 (404) ===")
r = client.get("/links/999999", headers=headers)
print(r.status_code, json.dumps(r.json()))

print("=== TEAM endpoint error: POST /teams with empty name ===")
r = client.post("/teams", json={"name": ""}, headers=headers)
print(r.status_code, json.dumps(r.json()))

print("=== TEAM endpoint error: POST /teams with missing name ===")
r = client.post("/teams", json={}, headers=headers)
print(r.status_code, json.dumps(r.json()))

print("=== TEAM endpoint error: GET /teams/999999/members (404) ===")
r = client.get("/teams/999999/members", headers=headers)
print(r.status_code, json.dumps(r.json()))

print("=== TEAM endpoint error: POST /teams/1/members bad role (validation) ===")
r = client.post("/teams/1/members", json={"email": "bob@example.com", "role": "owner"}, headers=headers)
print(r.status_code, json.dumps(r.json()))

print("=== TEAM endpoint error: add nonexistent user (404) ===")
r = client.post("/teams/1/members", json={"email": "nobody@example.com", "role": "member"}, headers=headers)
print(r.status_code, json.dumps(r.json()))