import json, urllib.request

BASE = "http://127.0.0.1:8000"

def req(method, path, token=None, body=None):
    r = urllib.request.Request(BASE + path, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", "Bearer " + token)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(r, data=data) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def login(email, pw):
    s, b = req("POST", "/auth/login", body={"email": email, "password": pw})
    return json.loads(b)["access_token"]

alice = login("alice@example.com", "alice-password")
bob = login("bob@example.com", "bob-password")

results = {}
s, b = req("POST", "/teams", alice, {"name": "Trajectory-Test-Team"})
team = json.loads(b)
tid = team["id"]
results["create_team"] = (s, team["name"])

s, b = req("POST", f"/teams/{tid}/members", alice, {"email": "bob@example.com", "role": "member"})
results["add_bob"] = (s, json.loads(b).get("role"))

s, b = req("GET", f"/teams/{tid}/members", alice)
members = json.loads(b)
results["alice_reads_members"] = (s, any(m["email"] == "bob@example.com" for m in members["items"]))

s, b = req("POST", f"/teams/{tid}/invitations", alice, {"invitee_email": "carol@example.com", "role": "member"})
results["create_invite"] = (s, json.loads(b).get("status"))

with open(r"C:\Users\karta\Desktop\New folder\m5_trajectory_results.json", "w") as f:
    json.dump(results, f, indent=2)
for k, v in results.items():
    print(f"{k}: {v}")