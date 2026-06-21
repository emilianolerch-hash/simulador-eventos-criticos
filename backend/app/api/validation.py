"""Endpoints del panel de validación médica."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_validator
from app.database import get_db
from app.models.db_models import ClinicalValidation, User

router = APIRouter(prefix="/admin/validations", tags=["validation"])


class ValidationOut(BaseModel):
    id: str
    scenario_id: str
    rule_ref: str
    rule_description: str
    validated_by_name: str
    validated_at: datetime
    notes: Optional[str]


class ValidateRequest(BaseModel):
    scenario_id: str
    rule_ref: str
    rule_description: str
    notes: Optional[str] = None


@router.get("", response_model=list[ValidationOut])
def list_validations(
    scenario_id: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(ClinicalValidation)
    if scenario_id:
        q = q.filter(ClinicalValidation.scenario_id == scenario_id)
    rows = q.order_by(ClinicalValidation.validated_at.desc()).all()
    return [
        ValidationOut(
            id=r.id,
            scenario_id=r.scenario_id,
            rule_ref=r.rule_ref,
            rule_description=r.rule_description,
            validated_by_name=r.validator.full_name,
            validated_at=r.validated_at,
            notes=r.notes,
        )
        for r in rows
    ]


@router.post("", response_model=ValidationOut, status_code=201)
def create_validation(
    body: ValidateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_validator),
):
    existing = (
        db.query(ClinicalValidation)
        .filter(
            ClinicalValidation.scenario_id == body.scenario_id,
            ClinicalValidation.rule_ref == body.rule_ref,
        )
        .first()
    )
    if existing:
        raise HTTPException(409, f"La regla '{body.rule_ref}' ya fue validada")
    v = ClinicalValidation(
        scenario_id=body.scenario_id,
        rule_ref=body.rule_ref,
        rule_description=body.rule_description,
        validated_by_id=user.id,
        notes=body.notes,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return ValidationOut(
        id=v.id,
        scenario_id=v.scenario_id,
        rule_ref=v.rule_ref,
        rule_description=v.rule_description,
        validated_by_name=user.full_name,
        validated_at=v.validated_at,
        notes=v.notes,
    )


@router.delete("/{validation_id}", status_code=204)
def delete_validation(
    validation_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_validator),
):
    v = db.get(ClinicalValidation, validation_id)
    if not v:
        raise HTTPException(404, "Validación no encontrada")
    db.delete(v)
    db.commit()
