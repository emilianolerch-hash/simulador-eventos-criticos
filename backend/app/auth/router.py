"""Auth endpoints: register, login, me, promote."""
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional

from app.auth.deps import get_current_user
from app.auth.jwt import create_access_token, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.middleware.rate_limit import make_limiter
from app.models.db_models import User

router = APIRouter(prefix="/auth", tags=["auth"])

_login_limiter = make_limiter(settings.rate_limit_login)
_register_limiter = make_limiter(settings.rate_limit_register)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/register", response_model=TokenOut, status_code=201)
def register(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
    _: None = Depends(_register_limiter),
):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(409, "El email ya está registrado")
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role="anesthesiologist",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.role)
    return TokenOut(
        access_token=token,
        user=UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role),
    )


@router.post("/login", response_model=TokenOut)
def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
    _: None = Depends(_login_limiter),
):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Credenciales incorrectas")
    token = create_access_token(user.id, user.role)
    return TokenOut(
        access_token=token,
        user=UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role)


class PromoteRequest(BaseModel):
    email: EmailStr


@router.post("/promote", response_model=UserOut)
def promote_to_validator(
    body: PromoteRequest,
    x_admin_secret: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """Promueve un usuario existente al rol 'validator'. Requiere X-Admin-Secret."""
    if not x_admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin secret inválido")
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario '{body.email}' no encontrado")
    if user.role == "validator":
        raise HTTPException(status_code=409, detail="El usuario ya es validador")
    user.role = "validator"
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role)
