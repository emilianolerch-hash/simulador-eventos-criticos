"""Tests de rate limiting para endpoints de autenticación."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.router import _login_limiter, _register_limiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiters():
    """Limpia los contadores entre tests para evitar interferencias."""
    _login_limiter.clear()
    _register_limiter.clear()
    yield
    _login_limiter.clear()
    _register_limiter.clear()


def _unique_email() -> str:
    return f"ratelimit_{uuid.uuid4().hex[:8]}@test.com"


class TestLoginRateLimit:
    def test_repeated_login_triggers_429(self):
        """Más de RATE_LIMIT_LOGIN (default 10) requests en 60s → 429."""
        email = _unique_email()
        payload = {"email": email, "password": "wrong"}

        responses = []
        for _ in range(12):
            r = client.post("/auth/login", json=payload)
            responses.append(r.status_code)

        assert 429 in responses, f"Esperaba 429 en los primeros 12 intentos, recibí: {responses}"

    def test_below_limit_no_429(self):
        """Dentro del límite → nunca 429."""
        email = _unique_email()
        payload = {"email": email, "password": "wrong"}

        # El límite default es 10; hacemos solo 5
        responses = [client.post("/auth/login", json=payload).status_code for _ in range(5)]
        assert 429 not in responses, f"No esperaba 429 en 5 intentos: {responses}"


class TestRegisterRateLimit:
    def test_repeated_register_triggers_429(self):
        """Más de RATE_LIMIT_REGISTER (default 5) requests → 429."""
        responses = []
        for _ in range(7):
            payload = {
                "email": _unique_email(),
                "password": "pass123",
                "full_name": "Test User",
            }
            r = client.post("/auth/register", json=payload)
            responses.append(r.status_code)

        assert 429 in responses, f"Esperaba 429, recibí: {responses}"
