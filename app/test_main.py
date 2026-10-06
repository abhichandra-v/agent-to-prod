from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_readyz():
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_invoke_stub():
    r = client.post("/invoke", json={"prompt": "hello"})
    assert r.status_code == 200
    body = r.json()
    assert body["stubbed"] is True        # no key set in tests
    assert "hello" in body["output"]
