import json

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

alice = client.post("/auth/login", json={"email": "alice@example.com", "password": "alice-password"}).json()["access_token"]
bob = client.post("/auth/login", json={"email": "bob@example.com", "password": "bob-password"}).json()["access_token"]
ha = {"Authorization": f"Bearer {alice}"}
hb = {"Authorization": f"Bearer {bob}"}

results = {}

T = client.post("/teams", json={"name": "idor-team"}, headers=ha).json()["id"]

# THE IDOR GUARD: bob (authenticated, NOT a member) tries to invite on alice's team
r = client.post(f"/teams/{T}/invitations", json={"invitee_email": "carol@example.com"}, headers=hb)
results["idor_bob_invites"] = (r.status_code, r.json()["error"]["message"])

# bob lists invitations -> 403
r = client.get(f"/teams/{T}/invitations", headers=hb)
results["idor_bob_list"] = (r.status_code, r.json()["error"]["message"])

# alice (owner) creates invite
r = client.post(f"/teams/{T}/invitations", json={"invitee_email": "carol@example.com"}, headers=ha)
results["owner_create"] = (r.status_code, r.json().get("status"))
inv = r.json()
token = inv["token"]
inv_id = inv["id"]

# duplicate pending -> 409
r = client.post(f"/teams/{T}/invitations", json={"invitee_email": "carol@example.com"}, headers=ha)
results["dup_pending"] = (r.status_code, r.json()["error"]["message"])

# revoke by owner -> 204; then accept -> 400
r = client.delete(f"/teams/{T}/invitations/{inv_id}", headers=ha)
results["owner_revoke"] = (r.status_code,)
r = client.post(f"/teams/{T}/invitations/{token}/accept", headers=hb)
results["accept_revoked"] = (r.status_code, r.json()["error"]["message"])

# second invitation, accept twice -> second is 400 (one-time use)
r = client.post(f"/teams/{T}/invitations", json={"invitee_email": "carol@example.com"}, headers=ha)
tok2 = r.json()["token"]
r1 = client.post(f"/teams/{T}/invitations/{tok2}/accept", headers=hb)
results["accept_1"] = (r1.status_code, r1.json())
r2 = client.post(f"/teams/{T}/invitations/{tok2}/accept", headers=hb)
results["accept_2_replay"] = (r2.status_code, r2.json()["error"]["message"])

# bob revokes -> 403
r = client.post(f"/teams/{T}/invitations", json={"invitee_email": "dave@example.com"}, headers=ha)
inv3 = r.json()
r = client.delete(f"/teams/{T}/invitations/{inv3['id']}", headers=hb)
results["bob_revoke"] = (r.status_code, r.json()["error"]["message"])

with open("m4_idor_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

for k, v in results.items():
    print(f"{k}: {v}")