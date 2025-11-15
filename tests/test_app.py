from fastapi.testclient import TestClient
from agile_ci_demo.app import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_create_and_get_item():
    item = {"id": 1, "title": "Read agile guide"}
    r = client.post("/items", json=item)
    assert r.status_code == 201

    r2 = client.get("/items/1")
    assert r2.status_code == 200
    assert r2.json()["title"] == "Read agile guide"
    assert r2.json()["done"] is False

def test_conflict_on_duplicate():
    item = {"id": 2, "title": "Duplicate"}
    client.post("/items", json=item)
    r = client.post("/items", json=item)
    assert r.status_code == 409

def test_mark_done():
    item = {"id": 3, "title": "Finish demo"}
    client.post("/items", json=item)
    r = client.patch("/items/3/done")
    assert r.status_code == 200
    assert r.json()["done"] is True
