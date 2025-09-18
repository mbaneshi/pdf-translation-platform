from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}

