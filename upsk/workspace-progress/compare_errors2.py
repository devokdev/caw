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

# Use team 2 (created earlier by alice, owner_id=1)
tid = 2

print("=== 403: bob (not owner) lists members ===")
r = client.get(f"/teams/{tid}/members", headers=hb)
print(r.status_code, json.dumps(r.json()))

print("=== 403: bob tries to change role (owner-only) ===")
r = client.patch(f"/teams/{tid}/members/1/role", json={"role": "admin"}, headers=hb)
print(r.status_code, json.dumps(r.json()))

print("=== 409: alice adds herself (owner) ===")
r = client.post(f"/teams/{tid}/members", json={"email": "alice@example.com", "role": "member"}, headers=ha)
print(r.status_code, json.dumps(r.json()))

print("=== 404: add nonexistent user to real team 2 ===")
r = client.post(f"/teams/{tid}/members", json={"email": "nobody@example.com", "role": "member"}, headers=ha)
print(r.status_code, json.dumps(r.json()))

print("=== 400: invalid email ===")
r = client.post(f"/teams/{tid}/members", json={"email": "not-an-email", "role": "member"}, headers=ha)
print(r.status_code, json.dumps(r.json()))

print("=== 401: no token ===")
r = client.post("/teams", json={"name": "x"})
print(r.status_code, json.dumps(r.json()))