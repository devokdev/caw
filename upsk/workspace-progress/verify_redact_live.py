from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

r = client.post("/teams", json={"name": "x"})
print("401 no token:", r.status_code, r.json())

r = client.post("/teams", json={"name": "x"}, headers={"Authorization": "Bearer garbage"})
print("401 garbage:", r.status_code, r.json())