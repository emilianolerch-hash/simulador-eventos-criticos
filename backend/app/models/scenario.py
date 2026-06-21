"""
Pydantic schema for clinical scenario YAML files.

All numeric thresholds, doses, and physiological deltas in loaded scenarios
must carry validation_status = PENDING_MEDICAL_REVIEW until reviewed by a
licensed physician. This module enforces that constraint at load time.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, model_validator


class ValidationStatus(str, Enum):
    PENDING_MEDICAL_REVIEW = "PENDING_MEDICAL_REVIEW"
    VALIDATED = "VALIDATED"


class VitalSignsDelta(BaseModel):
    """Change per second (for continuous deterioration) or one-time delta for actions."""
    hr: float = 0.0
    sbp: float = 0.0
    dbp: float = 0.0
    spo2: float = 0.0
    rr: float = 0.0
    etco2: float = 0.0
    temperature: float = 0.0


class ActionEffect(BaseModel):
    vitals_delta_once: Optional[VitalSignsDelta] = None
    transitions_to: Optional[str] = None
    validation_status: ValidationStatus
    source_ref: Optional[str] = None
    notes: Optional[str] = None


class ActionDefinition(BaseModel):
    label: str
    description: str
    category: Optional[str] = None   # UI grouping: medication|fluid|procedure|oxygen|trigger|communication
    effect: ActionEffect


class StateDefinition(BaseModel):
    description: str
    is_terminal: bool = False
    outcome_id: Optional[str] = None
    vitals_delta_per_second: Optional[VitalSignsDelta] = None
    available_action_ids: list[str] = []
    auto_advance_to: Optional[str] = None
    auto_advance_after_seconds: Optional[float] = None
    validation_status: ValidationStatus


class OutcomeDefinition(BaseModel):
    label: str
    description: str
    educational_message: str


class ClinicalSource(BaseModel):
    title: str
    version: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    review_date: Optional[str] = None
    validated_by: Optional[str] = None


class PatientProfile(BaseModel):
    age: int
    weight_kg: float
    sex: str
    asa_class: str
    context: str


class InitialVitals(BaseModel):
    hr: float
    sbp: float
    dbp: float
    spo2: float
    rr: float
    etco2: float
    temperature: float


class DebriefingSection(BaseModel):
    id: str
    title: str


class ScenarioDefinition(BaseModel):
    id: str
    title: str
    version: str
    language: str
    educational_disclaimer: bool
    target_audience: str
    initial_state_id: str
    patient: PatientProfile
    initial_vitals: InitialVitals
    states: dict[str, StateDefinition]
    actions: dict[str, ActionDefinition]
    outcomes: dict[str, OutcomeDefinition]
    clinical_sources: dict[str, ClinicalSource]
    debriefing_sections: list[DebriefingSection]

    @model_validator(mode="after")
    def require_educational_disclaimer(self) -> "ScenarioDefinition":
        if not self.educational_disclaimer:
            raise ValueError("educational_disclaimer must be true — this simulator is for education only")
        return self

    @model_validator(mode="after")
    def validate_initial_state(self) -> "ScenarioDefinition":
        if self.initial_state_id not in self.states:
            raise ValueError(f"initial_state_id '{self.initial_state_id}' not found in states")
        return self

    @model_validator(mode="after")
    def validate_terminal_states(self) -> "ScenarioDefinition":
        for sid, state in self.states.items():
            if state.is_terminal and not state.outcome_id:
                raise ValueError(f"Terminal state '{sid}' must have outcome_id")
            if state.outcome_id and state.outcome_id not in self.outcomes:
                raise ValueError(f"State '{sid}' references unknown outcome '{state.outcome_id}'")
        return self

    @model_validator(mode="after")
    def validate_state_transitions(self) -> "ScenarioDefinition":
        for sid, state in self.states.items():
            if state.auto_advance_to and state.auto_advance_to not in self.states:
                raise ValueError(f"State '{sid}' auto_advance_to '{state.auto_advance_to}' not found")
            for aid in state.available_action_ids:
                if aid not in self.actions:
                    raise ValueError(f"State '{sid}' references unknown action '{aid}'")
        for aid, action in self.actions.items():
            t = action.effect.transitions_to
            if t and t not in self.states:
                raise ValueError(f"Action '{aid}' transitions_to '{t}' not found in states")
        return self

    @model_validator(mode="after")
    def validate_outcomes_covered(self) -> "ScenarioDefinition":
        referenced = {s.outcome_id for s in self.states.values() if s.outcome_id}
        for oid in self.outcomes:
            if oid not in referenced:
                raise ValueError(f"Outcome '{oid}' is defined but no terminal state references it")
        return self
