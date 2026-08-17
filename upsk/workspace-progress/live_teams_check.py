import os

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

login = client.post(
    "/auth/login", json={"email": "alice@example.com", "password": "alice-password"}
)
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

r = client.post("/teams", json={"name": "review-team"}, headers=headers)
print("create_team:", r.status_code, r.json())

team_id = r.json()["id"]

r2 = client.post(
    f"/teams/{team_id}/members",
    json={"email": "bob@example.com", "role": "admin"},
    headers=headers,
)
print("add_member:", r2.status_code, r2.json())

r3 = client.get(f"/teams/{team_id}/members", headers=headers)
print("list_members:", r3.status_code, r3.json())

r4 = client.patch(
    f"/teams/{team_id}/members/{r2.json()['user_id']}/role",
    json={"role": "member"},
    headers=headers,
)
print("update_role:", r4.status_code, r4.json())

r5 = client.delete(f"/teams/{team_id}/members/{r2.json()['user_id']}", headers=headers)
print("delete_member:", r5.status_code)

client.post("/teams", json={"name": "review-team-cleanup"}, headers=headers)