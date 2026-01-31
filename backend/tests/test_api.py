from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "healthy"


def test_chat_history_requires_auth_or_demo():
    response = client.get("/api/chat/history")
    assert response.status_code in (200, 401)
    if response.status_code == 200:
        payload = response.json()
        assert payload.get("success") is True
