"""
Integration tests: three complete end-to-end paths through the scenario.

Each test simulates a real session from start to a terminal outcome.
"""


# ─────────────────────────────────────────────────────────────────
# PATH 1 — Full recovery
# Physician recognizes reaction early and administers epinephrine IM in GRADE_I
# ─────────────────────────────────────────────────────────────────

def test_full_recovery_outcome(te, ap, session):
    # Advance through INITIAL_PRESENTATION (30s) → GRADE_I
    te.advance(session, 35.0)
    assert session.current_state_id == "GRADE_I"

    # Correct early response
    ap.apply(session, "STOP_TRIGGER")
    ap.apply(session, "CALL_FOR_HELP")
    ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")  # → RESOLVING

    assert session.current_state_id == "RESOLVING"
    assert not session.is_terminal

    # Patient stabilizes
    te.advance(session, 305.0)  # RESOLVING auto-advances after 300s

    assert session.is_terminal
    assert session.outcome_id == "OUTCOME_FULL_RECOVERY"


def test_full_recovery_log_has_key_actions(te, ap, session):
    te.advance(session, 35.0)
    ap.apply(session, "STOP_TRIGGER")
    ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")
    te.advance(session, 305.0)

    logged_ids = {e.action_id for e in session.action_log}
    assert "STOP_TRIGGER" in logged_ids
    assert "ADMINISTER_EPINEPHRINE_IM" in logged_ids


def test_full_recovery_total_sim_time(te, ap, session):
    te.advance(session, 35.0)
    ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")
    te.advance(session, 305.0)
    # 35s until treatment + 300s resolving ≈ 335s
    assert session.sim_time_seconds >= 335.0
    assert session.sim_time_seconds < 400.0


# ─────────────────────────────────────────────────────────────────
# PATH 2 — Cardiac arrest with recovery
# No treatment until cardiac arrest; CPR performed in GRADE_IV
# ─────────────────────────────────────────────────────────────────

def test_cardiac_arrest_with_recovery_outcome(te, ap, session):
    # Let patient deteriorate: INITIAL(30) + G_I(90) + G_II(180) + G_III(120) = 420s → GRADE_IV
    te.advance(session, 425.0)
    assert session.current_state_id == "GRADE_IV"
    assert not session.is_terminal

    # Perform CPR → RESOLVING_AFTER_CPR
    ap.apply(session, "START_CPR")
    assert session.current_state_id == "RESOLVING_AFTER_CPR"

    # Wait for stabilization
    te.advance(session, 305.0)

    assert session.is_terminal
    assert session.outcome_id == "OUTCOME_CARDIAC_ARREST_WITH_RECOVERY"


def test_cardiac_arrest_vitals_at_grade_iv(te, session):
    te.advance(session, 425.0)
    # After deterioration through all grades, vitals should be severely compromised
    assert session.current_vitals.sbp < 80.0
    assert session.current_vitals.spo2 < 90.0


def test_cardiac_arrest_recovery_log_has_cpr(te, ap, session):
    te.advance(session, 425.0)
    ap.apply(session, "START_CPR")
    te.advance(session, 305.0)

    logged_ids = {e.action_id for e in session.action_log}
    assert "START_CPR" in logged_ids


# ─────────────────────────────────────────────────────────────────
# PATH 3 — Death
# No actions taken at any point
# ─────────────────────────────────────────────────────────────────

def test_death_outcome_without_treatment(te, session):
    # INITIAL(30) + G_I(90) + G_II(180) + G_III(120) + G_IV(180) = 600s → OUTCOME_DEATH
    te.advance(session, 605.0)

    assert session.is_terminal
    assert session.outcome_id == "OUTCOME_DEATH"


def test_death_outcome_action_log_is_empty(te, session):
    te.advance(session, 605.0)
    assert len(session.action_log) == 0


def test_death_vitals_severely_compromised(te, session):
    te.advance(session, 605.0)
    assert session.current_vitals.hr == 0.0 or session.current_vitals.sbp < 20.0


# ─────────────────────────────────────────────────────────────────
# Debriefing tests
# ─────────────────────────────────────────────────────────────────

def test_debrief_full_recovery_identifies_correct_actions(te, ap, oe, session):
    te.advance(session, 35.0)
    ap.apply(session, "STOP_TRIGGER")
    ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")
    te.advance(session, 305.0)

    report = oe.build_debrief(session)
    assert report["outcome_id"] == "OUTCOME_FULL_RECOVERY"
    assert "Adrenalina IM (primera línea)" in report["sections"]["correct_actions"]
    assert "Suspender agente desencadenante" in report["sections"]["correct_actions"]


def test_debrief_death_shows_all_missed(te, oe, session):
    te.advance(session, 605.0)
    report = oe.build_debrief(session)
    assert report["outcome_id"] == "OUTCOME_DEATH"
    assert len(report["sections"]["missed_actions"]) > 0
    assert len(report["sections"]["correct_actions"]) == 0


def test_debrief_includes_clinical_sources(te, ap, oe, session):
    te.advance(session, 35.0)
    ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")
    te.advance(session, 305.0)

    report = oe.build_debrief(session)
    source_ids = {s["id"] for s in report["sections"]["clinical_sources"]}
    assert "WAO_ANAPHYLAXIS_2020" in source_ids
    assert "NAP6_2018" in source_ids


def test_debrief_in_progress_when_not_terminal(oe, session):
    report = oe.build_debrief(session)
    assert report["status"] == "in_progress"


def test_debrief_timeline_has_entries(te, ap, oe, session):
    te.advance(session, 35.0)
    ap.apply(session, "CALL_FOR_HELP")
    ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")
    te.advance(session, 305.0)

    report = oe.build_debrief(session)
    assert len(report["sections"]["timeline"]) == 2
    assert report["sections"]["timeline"][0]["action"] == "Llamar ayuda / Activar código azul"


# ─────────────────────────────────────────────────────────────────
# Scenario YAML integrity
# ─────────────────────────────────────────────────────────────────

def test_scenario_loads_without_error(scenario):
    assert scenario.id == "anaphylaxis_perioperative_adult_v1"


def test_scenario_has_educational_disclaimer(scenario):
    assert scenario.educational_disclaimer is True


def test_all_states_have_validation_status(scenario):
    from app.models.scenario import ValidationStatus
    for sid, state in scenario.states.items():
        assert state.validation_status in ValidationStatus, \
            f"State '{sid}' missing valid validation_status"


def test_all_action_effects_have_validation_status(scenario):
    from app.models.scenario import ValidationStatus
    for aid, action in scenario.actions.items():
        assert action.effect.validation_status in ValidationStatus, \
            f"Action '{aid}' missing valid validation_status"
