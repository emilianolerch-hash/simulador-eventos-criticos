"""FastAPI dependencies for authentication."""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.database import get_db
from app.models.db_models import User

_bearer = HTTPBearer(auto_error=False)


def _get_user_from_token(
    creds: Optional[HTTPAuthorizationCredentials],
    db: Session,
) -> Optional[User]:
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            return None
        return db.get(User, user_id)
    except JWTError:
        return None


def get_current_user_optional(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    return _get_user_from_token(creds, db)


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    user = _get_user_from_token(creds, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_validator(user: User = Depends(get_current_user)) -> User:
    if user.role != "validator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de validador médico",
        )
    return user
