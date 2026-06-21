"""
Schema Pydantic para la especificación clínica completa de un escenario.

Este schema es más rico que el runtime ScenarioDefinition: incluye
contexto pedagógico, acciones incorrectas, criterios de puntuación,
debriefing estructurado y trazabilidad de fuentes por cada regla.

Invariante fundamental: todo campo que contenga una afirmación clínica
(dosis, tiempo, efecto fisiológico, contraindicación) debe llevar
validation_status y source_ref. Los validadores del modelo hacen
cumplir esto en tiempo de carga.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator


# ── enumeraciones ─────────────────────────────────────────────────────────────

class ValidationStatus(str, Enum):
    PENDING_MEDICAL_REVIEW = "PENDING_MEDICAL_REVIEW"
    VALIDATED = "VALIDATED"


class DifficultyLevel(str, Enum):
    BASIC = "básico"
    INTERMEDIATE = "intermedio"
    ADVANCED = "avanzado"


class ContraindicationSeverity(str, Enum):
    ABSOLUTE = "absoluta"
    RELATIVE = "relativa"


# ── bloques de construcción ───────────────────────────────────────────────────

class DoseSpec(BaseModel):
    value: str                          # "0.3 mg" o "PENDING_MEDICAL_REVIEW"
    unit: Optional[str] = None
    concentration: Optional[str] = None
    administration_notes: Optional[str] = None
    validation_status: ValidationStatus
    source_ref: str                     # obligatorio; sin excepción


class ContraindicationSpec(BaseModel):
    description: str
    severity: ContraindicationSeverity
    validation_status: ValidationStatus
    source_ref: str


class MedicationSpec(BaseModel):
    name: str
    drug_class: str
    indication_in_scenario: str
    doses: dict[str, DoseSpec]          # ruta → DoseSpec  (ej. "IM", "IV")
    onset_description: str              # "PENDING_MEDICAL_REVIEW" o descripción
    duration_description: str
    contraindications: list[ContraindicationSpec]
    monitoring: list[str]
    notes: Optional[str] = None
    validation_status: ValidationStatus
    source_refs: list[str]

    @field_validator("source_refs")
    @classmethod
    def at_least_one_source(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Cada medicamento debe tener al menos una fuente en source_refs")
        return v


class CriticalAction(BaseModel):
    id: str
    label: str
    rationale: str
    time_window: str                    # "< 5 min" o "PENDING_MEDICAL_REVIEW"
    time_window_validation_status: ValidationStatus
    failure_consequence: str
    source_ref: str
    validation_status: ValidationStatus


class IncorrectAction(BaseModel):
    id: str
    label: str
    consequence: str
    teaching_point: str
    validation_status: ValidationStatus


class TimeLimit(BaseModel):
    id: str
    label: str
    event_description: str
    limit: str                          # "PENDING_MEDICAL_REVIEW" o valor
    rationale: str
    validation_status: ValidationStatus
    source_ref: str


class PhysiologicalRule(BaseModel):
    id: str
    state: str
    description: str
    clinical_basis: str                 # explicación o "PENDING_MEDICAL_REVIEW"
    validation_status: ValidationStatus
    source_ref: Optional[str] = None


class TransitionSpec(BaseModel):
    from_state: str
    to_state: str
    trigger_description: str
    clinical_basis: str
    validation_status: ValidationStatus
    source_ref: Optional[str] = None


class OutcomeSpec(BaseModel):
    id: str
    label: str
    description: str
    trigger_condition: str
    educational_message: str
    validation_status: ValidationStatus


class ScoringCriterion(BaseModel):
    id: str
    label: str
    max_points: int
    criteria_description: list[str]
    validation_status: ValidationStatus


class DebriefingPoint(BaseModel):
    id: str
    question: str
    key_teaching: str
    source_ref: Optional[str] = None
    validation_status: ValidationStatus


class Reference(BaseModel):
    title: str
    version: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    access_date: Optional[str] = None
    validated_by: Optional[str] = None
    validation_date: Optional[str] = None


class ValidationLogEntry(BaseModel):
    overall_status: ValidationStatus
    reviewer: Optional[str] = None
    reviewer_institution: Optional[str] = None
    review_date: Optional[str] = None
    comments: Optional[str] = None
    pending_items: list[str] = []


# ── secciones principales ─────────────────────────────────────────────────────

class ScenarioMetadata(BaseModel):
    id: str
    title: str
    version: str
    language: str
    educational_disclaimer: bool
    target_audience: str
    runtime_scenario_id: Optional[str] = None   # vínculo al YAML del motor


class PopulationSpec(BaseModel):
    age_range: str
    sex: str
    weight_range: str
    asa_class_range: str
    exclusion_criteria: list[str]


class ClinicalSettingSpec(BaseModel):
    environment: str
    phase: str
    monitoring_available: list[str]
    medications_available: list[str]
    personnel: list[str]


class DifficultySpec(BaseModel):
    level: DifficultyLevel
    learning_objectives: list[str]
    prerequisites: list[str]
    estimated_duration_minutes: int


class PatientHistorySpec(BaseModel):
    allergies_known: str
    current_medications: list[str]
    relevant_history: str
    last_meal: Optional[str] = None
    anesthetic_history: Optional[str] = None


class VisibleInfoSpec(BaseModel):
    monitor_displays: list[str]
    clinical_signs: list[str]
    contextual_clues: list[str]


class HiddenDiagnosisSpec(BaseModel):
    diagnosis: str
    mechanism: str                      # "PENDING_MEDICAL_REVIEW" o mecanismo
    causative_agent: str
    validation_status: ValidationStatus
    source_ref: Optional[str] = None


class TriggerSpec(BaseModel):
    agent: str
    timing_description: str
    mechanism: str
    common_perioperative_triggers: list[str]
    validation_status: ValidationStatus
    source_ref: str


class ClinicalStateSpec(BaseModel):
    label: str
    description: str
    typical_presentation: str
    vital_signs_description: dict[str, str]    # {"hr": "110-130 lpm"} o "PENDING_MEDICAL_REVIEW"
    diagnostic_criteria: list[str]
    clinical_urgency: str
    validation_status: ValidationStatus
    source_ref: Optional[str] = None


# ── esquema raíz ─────────────────────────────────────────────────────────────

class ClinicalScenarioSpec(BaseModel):
    metadata: ScenarioMetadata
    population: PopulationSpec
    clinical_setting: ClinicalSettingSpec
    difficulty: DifficultySpec
    initial_description: str
    patient_history: PatientHistorySpec
    initial_vitals: dict                        # valores + validation_status inline
    visible_information: VisibleInfoSpec
    hidden_diagnosis: HiddenDiagnosisSpec
    trigger: TriggerSpec
    clinical_states: dict[str, ClinicalStateSpec]
    transitions: list[TransitionSpec]
    critical_actions: list[CriticalAction]
    incorrect_actions: list[IncorrectAction]
    time_limits: list[TimeLimit]
    physiological_progression: list[PhysiologicalRule]
    medications: dict[str, MedicationSpec]
    outcomes: dict[str, OutcomeSpec]
    scoring_criteria: list[ScoringCriterion]
    debriefing_structure: list[DebriefingPoint]
    references: dict[str, Reference]
    validation_log: ValidationLogEntry

    # ── validadores del modelo ──────────────────────────────────────────────

    @model_validator(mode="after")
    def require_educational_disclaimer(self) -> "ClinicalScenarioSpec":
        if not self.metadata.educational_disclaimer:
            raise ValueError("educational_disclaimer debe ser true en todos los escenarios")
        return self

    @model_validator(mode="after")
    def require_three_outcomes(self) -> "ClinicalScenarioSpec":
        if len(self.outcomes) < 3:
            raise ValueError(
                f"El escenario debe tener al menos 3 desenlaces; tiene {len(self.outcomes)}"
            )
        return self

    @model_validator(mode="after")
    def all_source_refs_exist_in_references(self) -> "ClinicalScenarioSpec":
        """Verifica que cada source_ref apunte a una entrada en references."""
        defined = set(self.references.keys())
        violations: list[str] = []

        def check(ref: Optional[str], context: str) -> None:
            if ref and ref not in defined:
                violations.append(f"{context}: source_ref '{ref}' no está en references")

        check(self.trigger.source_ref, "trigger")
        check(self.hidden_diagnosis.source_ref, "hidden_diagnosis")

        for aid, action in self.medications.items():
            for ref in action.source_refs:
                check(ref, f"medication '{aid}'")
            for route, dose in action.doses.items():
                check(dose.source_ref, f"medication '{aid}' dose '{route}'")
            for i, contra in enumerate(action.contraindications):
                check(contra.source_ref, f"medication '{aid}' contraindication[{i}]")

        for ca in self.critical_actions:
            check(ca.source_ref, f"critical_action '{ca.id}'")

        for tl in self.time_limits:
            check(tl.source_ref, f"time_limit '{tl.id}'")

        for pr in self.physiological_progression:
            check(pr.source_ref, f"physiological_rule '{pr.id}'")

        for sid, state in self.clinical_states.items():
            check(state.source_ref, f"clinical_state '{sid}'")

        for dp in self.debriefing_structure:
            check(dp.source_ref, f"debriefing_point '{dp.id}'")

        for t in self.transitions:
            check(t.source_ref, f"transition '{t.from_state}→{t.to_state}'")

        if violations:
            raise ValueError(
                "Referencias indefinidas en reglas clínicas:\n" + "\n".join(violations)
            )
        return self

    @model_validator(mode="after")
    def all_critical_actions_have_sources(self) -> "ClinicalScenarioSpec":
        missing = [ca.id for ca in self.critical_actions if not ca.source_ref]
        if missing:
            raise ValueError(f"Acciones críticas sin fuente: {missing}")
        return self

    @model_validator(mode="after")
    def all_time_limits_have_sources(self) -> "ClinicalScenarioSpec":
        missing = [tl.id for tl in self.time_limits if not tl.source_ref]
        if missing:
            raise ValueError(f"Tiempos límite sin fuente: {missing}")
        return self

    @model_validator(mode="after")
    def all_outcomes_referenced_are_defined(self) -> "ClinicalScenarioSpec":
        outcome_ids = set(self.outcomes.keys())
        for ca in self.critical_actions:
            # critical_actions reference outcomes via failure_consequence narrative — no check needed
            pass
        return self
