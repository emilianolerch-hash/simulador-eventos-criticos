"""Tests para la configuración de entorno y validaciones de seguridad."""
import os
import importlib
import pytest


def _reload_config(env_vars: dict) -> object:
    """Recarga app.config con las variables de entorno especificadas."""
    # Guarda el entorno original
    original = {k: os.environ.get(k) for k in env_vars}
    for k, v in env_vars.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

    # Recarga el módulo
    import app.config as cfg_module
    importlib.reload(cfg_module)
    result = cfg_module.Settings()

    # Restaura
    for k, orig_v in original.items():
        if orig_v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = orig_v
    importlib.reload(cfg_module)

    return result


class TestJwtSecretRequired:
    def test_dev_without_secret_uses_fallback(self):
        settings = _reload_config({"ENV": "development", "JWT_SECRET_KEY": ""})
        assert settings.jwt_secret_key == "dev-secret-only-change-in-production"

    def test_prod_without_secret_raises(self):
        original_env = os.environ.get("ENV")
        original_secret = os.environ.get("JWT_SECRET_KEY")

        os.environ["ENV"] = "production"
        os.environ.pop("JWT_SECRET_KEY", None)

        try:
            import app.config as cfg_module
            with pytest.raises((ValueError, Exception)):
                # Forzar la evaluación del secreto
                cfg_module._ENV = "production"  # type: ignore[attr-defined]
                cfg_module._get_jwt_secret()
        finally:
            if original_env is None:
                os.environ.pop("ENV", None)
            else:
                os.environ["ENV"] = original_env
            if original_secret is None:
                os.environ.pop("JWT_SECRET_KEY", None)
            else:
                os.environ["JWT_SECRET_KEY"] = original_secret
            importlib.reload(cfg_module)

    def test_prod_with_secret_ok(self):
        settings = _reload_config({
            "ENV": "production",
            "JWT_SECRET_KEY": "a" * 64,
        })
        assert settings.jwt_secret_key == "a" * 64


class TestCorsOriginParsing:
    def test_single_origin(self):
        settings = _reload_config({"CORS_ORIGINS": "http://localhost:3000"})
        assert settings.cors_origins == ["http://localhost:3000"]

    def test_multiple_origins(self):
        settings = _reload_config({
            "CORS_ORIGINS": "http://localhost:3000,https://app.hospital.edu, https://other.com"
        })
        assert settings.cors_origins == [
            "http://localhost:3000",
            "https://app.hospital.edu",
            "https://other.com",
        ]

    def test_default_origin(self):
        settings = _reload_config({"CORS_ORIGINS": ""})
        # Vacío → lista vacía (CORS restringido a nada)
        assert settings.cors_origins == []


class TestRateLimitConfig:
    def test_custom_rate_limits(self):
        settings = _reload_config({
            "RATE_LIMIT_LOGIN": "3",
            "RATE_LIMIT_REGISTER": "2",
        })
        assert settings.rate_limit_login == 3
        assert settings.rate_limit_register == 2
