"""
Tests para la especificación clínica perioperative_anaphylaxis.yaml.

Verifican:
1. El YAML carga y valida sin errores.
2. Ninguna regla clínica carece de fuente ni estado de validación.
3. Los tres desenlaces están presentes.
4. El disclaimer educativo está activo.
5. Todas las referencias usadas están definidas.
6. Todas las acciones críticas tienen fuente.
7. Los medicamentos tienen al menos una fuente.
8. El log de validación reconoce su estado provisional.
"""

from pathlib import Path
import pytest
from app.loader.clinical_scenario_loader import load_clinical_scenario, ClinicalScenarioLoadError
from app.models.clinical_scenario import ValidationStatus, ClinicalScenarioSpec

CLINICAL_PATH = Path(__file__).parent.parent / "clinical" / "scenarios" / "perioperative_anaphylaxis.yaml"


@pytest.fixture(scope="session")
def clinical(tmp_path_factory):
    return load_clinical_scenario(CLINICAL_PATH)


# ── carga ─────────────────────────────────────────────────────────────────────

def test_clinical_scenario_loads(clinical):
    assert clinical is not None
    assert isinstance(clinical, ClinicalScenarioSpec)


def test_scenario_id(clinical):
    assert clinical.metadata.id == "perioperative_anaphylaxis_v1"


def test_educational_disclaimer(clinical):
    assert clinical.metadata.educational_disclaimer is True


# ── desenlaces ───────────────────────────────────────────────────────────────

def test_has_three_outcomes(clinical):
    assert len(clinical.outcomes) >= 3


def test_full_recovery_outcome_exists(clinical):
    assert "OUTCOME_FULL_RECOVERY" in clinical.outcomes


def test_cardiac_arrest_recovery_outcome_exists(clinical):
    assert "OUTCOME_CARDIAC_ARREST_WITH_RECOVERY" in clinical.outcomes


def test_death_outcome_exists(clinical):
    assert "OUTCOME_DEATH" in clinical.outcomes


def test_all_outcomes_have_educational_message(clinical):
    for oid, outcome in clinical.outcomes.items():
        assert outcome.educational_message, f"Outcome '{oid}' carece de educational_message"


# ── fuentes y validación en acciones críticas ─────────────────────────────────

def test_all_critical_actions_have_source_ref(clinical):
    missing = [ca.id for ca in clinical.critical_actions if not ca.source_ref]
    assert missing == [], f"Acciones críticas sin source_ref: {missing}"


def test_all_critical_actions_have_validation_status(clinical):
    for ca in clinical.critical_actions:
        assert ca.validation_status in ValidationStatus, \
            f"Acción crítica '{ca.id}' sin validation_status válido"


def test_all_critical_actions_have_time_window_validation(clinical):
    for ca in clinical.critical_actions:
        assert ca.time_window_validation_status in ValidationStatus, \
            f"Acción crítica '{ca.id}' sin time_window_validation_status"


# ── fuentes y validación en acciones incorrectas ─────────────────────────────

def test_all_incorrect_actions_have_validation_status(clinical):
    for ia in clinical.incorrect_actions:
        assert ia.validation_status in ValidationStatus, \
            f"Acción incorrecta '{ia.id}' sin validation_status"


def test_all_incorrect_actions_have_teaching_point(clinical):
    for ia in clinical.incorrect_actions:
        assert ia.teaching_point, f"Acción incorrecta '{ia.id}' sin teaching_point"


# ── tiempos límite ───────────────────────────────────────────────────────────

def test_all_time_limits_have_source_ref(clinical):
    missing = [tl.id for tl in clinical.time_limits if not tl.source_ref]
    assert missing == [], f"Tiempos límite sin source_ref: {missing}"


def test_all_time_limits_have_validation_status(clinical):
    for tl in clinical.time_limits:
        assert tl.validation_status in ValidationStatus, \
            f"Tiempo límite '{tl.id}' sin validation_status"


# ── medicamentos ─────────────────────────────────────────────────────────────

def test_all_medications_have_at_least_one_source(clinical):
    for mid, med in clinical.medications.items():
        assert med.source_refs, f"Medicamento '{mid}' sin source_refs"


def test_all_medication_doses_have_source_ref(clinical):
    for mid, med in clinical.medications.items():
        for route, dose in med.doses.items():
            assert dose.source_ref, \
                f"Medicamento '{mid}' dosis '{route}' sin source_ref"


def test_all_medication_doses_have_validation_status(clinical):
    for mid, med in clinical.medications.items():
        for route, dose in med.doses.items():
            assert dose.validation_status in ValidationStatus, \
                f"Medicamento '{mid}' dosis '{route}' sin validation_status"


def test_all_contraindications_have_source_ref(clinical):
    for mid, med in clinical.medications.items():
        for i, contra in enumerate(med.contraindications):
            assert contra.source_ref, \
                f"Medicamento '{mid}' contraindicación[{i}] sin source_ref"


def test_all_contraindications_have_validation_status(clinical):
    for mid, med in clinical.medications.items():
        for i, contra in enumerate(med.contraindications):
            assert contra.validation_status in ValidationStatus, \
                f"Medicamento '{mid}' contraindicación[{i}] sin validation_status"


# ── reglas fisiológicas ───────────────────────────────────────────────────────

def test_all_physiological_rules_have_validation_status(clinical):
    for rule in clinical.physiological_progression:
        assert rule.validation_status in ValidationStatus, \
            f"Regla fisiológica '{rule.id}' sin validation_status"


def test_all_physiological_rules_have_clinical_basis(clinical):
    for rule in clinical.physiological_progression:
        assert rule.clinical_basis, \
            f"Regla fisiológica '{rule.id}' sin clinical_basis"


# ── transiciones ─────────────────────────────────────────────────────────────

def test_all_transitions_have_validation_status(clinical):
    for t in clinical.transitions:
        assert t.validation_status in ValidationStatus, \
            f"Transición '{t.from_state}→{t.to_state}' sin validation_status"


def test_all_transitions_have_clinical_basis(clinical):
    for t in clinical.transitions:
        assert t.clinical_basis, \
            f"Transición '{t.from_state}→{t.to_state}' sin clinical_basis"


# ── estados clínicos ─────────────────────────────────────────────────────────

def test_clinical_states_have_validation_status(clinical):
    for sid, state in clinical.clinical_states.items():
        assert state.validation_status in ValidationStatus, \
            f"Estado '{sid}' sin validation_status"


def test_clinical_states_have_vital_signs_description(clinical):
    for sid, state in clinical.clinical_states.items():
        assert state.vital_signs_description, \
            f"Estado '{sid}' sin vital_signs_description"


# ── criterios de puntuación ───────────────────────────────────────────────────

def test_scoring_criteria_have_validation_status(clinical):
    for sc in clinical.scoring_criteria:
        assert sc.validation_status in ValidationStatus, \
            f"Criterio de puntuación '{sc.id}' sin validation_status"


def test_scoring_criteria_have_max_points(clinical):
    for sc in clinical.scoring_criteria:
        assert sc.max_points > 0, \
            f"Criterio '{sc.id}' tiene max_points = 0"


# ── debriefing ────────────────────────────────────────────────────────────────

def test_debriefing_points_have_validation_status(clinical):
    for dp in clinical.debriefing_structure:
        assert dp.validation_status in ValidationStatus, \
            f"Punto de debriefing '{dp.id}' sin validation_status"


def test_debriefing_has_key_topics(clinical):
    dp_ids = {dp.id for dp in clinical.debriefing_structure}
    assert "DEBRIEF_RECOGNITION" in dp_ids, "Falta punto de debriefing sobre reconocimiento"
    assert "DEBRIEF_FIRST_DRUG" in dp_ids, "Falta punto de debriefing sobre elección de fármaco"


# ── referencias ───────────────────────────────────────────────────────────────

def test_key_references_present(clinical):
    assert "NAP6_2018" in clinical.references
    assert "WAO_2020" in clinical.references
    assert "ACLS_AHA_2020" in clinical.references


def test_all_references_have_title(clinical):
    for rid, ref in clinical.references.items():
        assert ref.title, f"Referencia '{rid}' sin título"


def test_all_references_have_year(clinical):
    for rid, ref in clinical.references.items():
        assert ref.year is not None, f"Referencia '{rid}' sin año"


def test_all_source_refs_point_to_defined_references(clinical):
    """
    Verifica que el validador del modelo ya garantice esto —
    este test es la verificación explícita post-carga.
    """
    defined = set(clinical.references.keys())

    all_refs: list[tuple[str, str]] = []

    all_refs.append(("trigger", clinical.trigger.source_ref))

    for mid, med in clinical.medications.items():
        for r in med.source_refs:
            all_refs.append((f"medication:{mid}", r))
        for route, dose in med.doses.items():
            all_refs.append((f"medication:{mid}:dose:{route}", dose.source_ref))
        for i, contra in enumerate(med.contraindications):
            all_refs.append((f"medication:{mid}:contra:{i}", contra.source_ref))

    for ca in clinical.critical_actions:
        all_refs.append((f"critical_action:{ca.id}", ca.source_ref))

    for tl in clinical.time_limits:
        all_refs.append((f"time_limit:{tl.id}", tl.source_ref))

    undefined = [
        (ctx, ref) for ctx, ref in all_refs
        if ref and ref not in defined
    ]
    assert undefined == [], f"Referencias indefinidas: {undefined}"


# ── estado de validación general ──────────────────────────────────────────────

def test_overall_validation_status_is_pending(clinical):
    assert clinical.validation_log.overall_status == ValidationStatus.PENDING_MEDICAL_REVIEW


def test_validation_log_has_pending_items(clinical):
    assert len(clinical.validation_log.pending_items) > 0, \
        "El log de validación debe listar ítems pendientes"


def test_no_reviewer_assigned_yet(clinical):
    assert clinical.validation_log.reviewer is None, \
        "El reviewer debe ser null hasta que un médico firme la revisión"


# ── carga fallida esperada ─────────────────────────────────────────────────────

def test_load_nonexistent_file_raises():
    with pytest.raises(ClinicalScenarioLoadError, match="no encontrado"):
        load_clinical_scenario(Path("/tmp/nonexistent_scenario.yaml"))
