"""SQLAlchemy ORM models (Etapa 5 — persistencia)."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON, Boolean, DateTime, Enum, Float, ForeignKey,
    String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("anesthesiologist", "validator", name="user_role"),
        default="anesthesiologist",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    sessions: Mapped[list["DBSimulationSession"]] = relationship(back_populates="user")
    validations: Mapped[list["ClinicalValidation"]] = relationship(back_populates="validator")


class DBSimulationSession(Base):
    __tablename__ = "simulation_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    scenario_id: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    current_state_id: Mapped[str] = mapped_column(String(255), nullable=False)
    current_vitals: Mapped[dict] = mapped_column(JSON, nullable=False)
    sim_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    time_in_current_state_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False)
    outcome_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="sessions")
    action_log: Mapped[list["DBActionLogEntry"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="DBActionLogEntry.sim_time_seconds"
    )


class DBActionLogEntry(Base):
    __tablename__ = "action_log_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("simulation_sessions.id", ondelete="CASCADE"), nullable=False
    )
    entry_id: Mapped[str] = mapped_column(String(255), nullable=False)
    sim_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    action_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action_label: Mapped[str] = mapped_column(String(500), nullable=False)
    state_before: Mapped[str] = mapped_column(String(255), nullable=False)
    state_after: Mapped[str] = mapped_column(String(255), nullable=False)
    effect_summary: Mapped[str] = mapped_column(Text, nullable=False)
    vitals_before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    vitals_after: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    session: Mapped["DBSimulationSession"] = relationship(back_populates="action_log")


class ClinicalValidation(Base):
    __tablename__ = "clinical_validations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scenario_id: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    rule_description: Mapped[str] = mapped_column(Text, nullable=False)
    validated_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    validator: Mapped["User"] = relationship(back_populates="validations")
