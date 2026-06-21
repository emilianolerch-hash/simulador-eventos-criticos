"""Tests del endpoint POST /auth/promote."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)

_VALID_SECRET = settings.admin_secret


def _register(email: str | None = None) -> dict:
    email = email or f"user_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/auth/register", json={
        "email": email,
        "password": "pass1234",
        "full_name": "Test User",
    })
    assert r.status_code == 201, r.text
    return {"email": email, "data": r.json()}


class TestPromote:
    def test_promote_success(self):
        """Usuario existente con secret correcto → pasa a validator."""
        u = _register()
        assert u["data"]["user"]["role"] == "anesthesiologist"

        r = client.post(
            "/auth/promote",
            json={"email": u["email"]},
            headers={"X-Admin-Secret": _VALID_SECRET},
        )
        assert r.status_code == 200
        assert r.json()["role"] == "validator"
        assert r.json()["email"] == u["email"]

    def test_promote_wrong_secret(self):
        """Secret incorrecto → 403."""
        u = _register()
        r = client.post(
            "/auth/promote",
            json={"email": u["email"]},
            headers={"X-Admin-Secret": "wrong-secret"},
        )
        assert r.status_code == 403

    def test_promote_missing_secret(self):
        """Sin header X-Admin-Secret → 403."""
        u = _register()
        r = client.post("/auth/promote", json={"email": u["email"]})
        assert r.status_code == 403

    def test_promote_unknown_email(self):
        """Email no registrado → 404."""
        r = client.post(
            "/auth/promote",
            json={"email": "noexiste@test.com"},
            headers={"X-Admin-Secret": _VALID_SECRET},
        )
        assert r.status_code == 404

    def test_promote_already_validator(self):
        """Intentar promover a alguien que ya es validator → 409."""
        u = _register()
        headers = {"X-Admin-Secret": _VALID_SECRET}
        client.post("/auth/promote", json={"email": u["email"]}, headers=headers)

        r = client.post("/auth/promote", json={"email": u["email"]}, headers=headers)
        assert r.status_code == 409

    def test_register_always_anesthesiologist(self):
        """El registro siempre crea usuarios con rol anesthesiologist."""
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        r = client.post("/auth/register", json={
            "email": email,
            "password": "pass1234",
            "full_name": "Doctor Test",
        })
        assert r.status_code == 201
        assert r.json()["user"]["role"] == "anesthesiologist"
