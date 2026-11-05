from fastapi.testclient import TestClient

from mvr_api.main import app


def test_saude():
    r = TestClient(app).get("/saude")
    assert r.status_code == 200
    assert r.json()["ok"] is True
