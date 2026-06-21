"""Configuración centralizada. Todas las variables de entorno pasan por aquí."""
import os
import warnings
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_ENV: Literal["development", "production"] = os.environ.get("ENV", "development")  # type: ignore[assignment]

_JWT_SECRET_FALLBACK = "dev-secret-only-change-in-production"


def _get_jwt_secret() -> str:
    val = os.environ.get("JWT_SECRET_KEY", "")
    if not val:
        if _ENV == "production":
            raise ValueError(
                "JWT_SECRET_KEY es obligatorio en ENV=production. "
                "Generá uno con: openssl rand -hex 32"
            )
        warnings.warn(
            "JWT_SECRET_KEY no configurada — usando fallback de desarrollo. "
            "NO usar en producción.",
            stacklevel=2,
        )
        return _JWT_SECRET_FALLBACK
    return val


def _parse_cors_origins(raw: str) -> list[str]:
    return [o.strip() for o in raw.split(",") if o.strip()]


class Settings:
    env: str = _ENV
    jwt_secret_key: str = _get_jwt_secret()
    jwt_algorithm: str = os.environ.get("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.environ.get("JWT_EXPIRE_MINUTES", "480"))

    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres@localhost:5432/simulador_db",
    )

    cors_origins: list[str] = _parse_cors_origins(
        os.environ.get("CORS_ORIGINS", "http://localhost:3000")
    )

    # Rate limiting (requests per minute per IP)
    rate_limit_login: int = int(os.environ.get("RATE_LIMIT_LOGIN", "10"))
    rate_limit_register: int = int(os.environ.get("RATE_LIMIT_REGISTER", "5"))


settings = Settings()
