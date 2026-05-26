"""
Basic smoke test for the WhatsApp webhook.

Usage:
    pytest tests/test_webhook.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Fixtures ────────────────────────────────────────────────────────────────

TEXT_MESSAGE_PAYLOAD = {
    "messages": [
        {
            "from": "2348012345678",
            "id": "test_msg_001",
            "type": "text",
            "text": {"body": "Hello I need a 2 bedroom flat in Ajah, budget 1.5m"},
        }
    ]
}

STATUS_PAYLOAD = {
    "statuses": [
        {"id": "msg_abc", "status": "delivered", "timestamp": "1716000000"}
    ]
}

IMAGE_MESSAGE_PAYLOAD = {
    "messages": [
        {
            "from": "2348012345678",
            "id": "img_msg_001",
            "type": "image",
            "image": {"id": "some_image_id"},
        }
    ]
}


# ── Tests ───────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data


class TestWebhookVerification:
    def test_get_webhook_returns_active(self):
        response = client.get("/webhook/whatsapp")
        assert response.status_code == 200
        assert "active" in response.json()["status"]


class TestInboundMessageParsing:
    def test_text_message_returns_ok(self):
        response = client.post("/webhook/whatsapp", json=TEXT_MESSAGE_PAYLOAD)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_status_update_returns_ok(self):
        """Delivery receipts should be silently acknowledged."""
        response = client.post("/webhook/whatsapp", json=STATUS_PAYLOAD)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_image_message_returns_ok(self):
        """Non-text messages should be gracefully ignored."""
        response = client.post("/webhook/whatsapp", json=IMAGE_MESSAGE_PAYLOAD)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_empty_payload_returns_ok(self):
        response = client.post("/webhook/whatsapp", json={})
        assert response.status_code == 200

    def test_malformed_json_returns_ok(self):
        """Even totally invalid JSON should return 200 to prevent 360dialog retries."""
        response = client.post(
            "/webhook/whatsapp",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
