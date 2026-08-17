import json

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== EXISTING /links 401 (no token) ===")
r = client.get("/links")
print(r.status_code, json.dumps(r.json()))

print("=== TEAM /teams 401 (no token) ===")
r = client.post("/teams", json={"name": "x"})
print(r.status_code, json.dumps(r.json()))

print("=== EXISTING /links 401 (garbage token) ===")
r = client.get("/links", headers={"Authorization": "Bearer garbage"})
print(r.status_code, json.dumps(r.json()))

print("=== TEAM /teams 401 (garbage token) ===")
r = client.post("/teams", json={"name": "x"}, headers={"Authorization": "Bearer garbage"})
print(r.status_code, json.dumps(r.json()))