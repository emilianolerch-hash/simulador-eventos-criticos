"""Tests for the simulation clock and deterioration engine."""


def test_vitals_deteriorate_in_grade_i(te, session):
    # advance past INITIAL_PRESENTATION (30s) and into GRADE_I
    te.advance(session, 35.0)
    assert session.current_state_id == "GRADE_I"
    # HR should have increased slightly from GRADE_I deterioration
    assert session.current_vitals.hr > 78.0


def test_vitals_deteriorate_more_in_grade_ii(te, session, scenario):
    te.advance(session, 30.0)   # → GRADE_I
    hr_at_grade_i = session.current_vitals.hr
    te.advance(session, 90.0)   # → GRADE_II
    te.advance(session, 10.0)   # some time in GRADE_II
    # In GRADE_II, HR deterioration is faster than GRADE_I
    assert session.current_vitals.hr > hr_at_grade_i


def test_spo2_drops_over_time_without_treatment(te, session):
    te.advance(session, 200.0)  # through INITIAL→GRADE_I→GRADE_II
    assert session.current_vitals.spo2 < 99.0


def test_sbp_drops_in_grade_ii(te, session):
    te.advance(session, 125.0)  # INITIAL(30) + GRADE_I(90) + 5s in GRADE_II
    assert session.current_state_id == "GRADE_II"
    assert session.current_vitals.sbp < 125.0


def test_spo2_clamped_at_100(te, session, sm):
    sm.transition_to(session, "RESOLVING")
    session.current_vitals = session.current_vitals.model_copy(update={"spo2": 99.8})
    te.advance(session, 60.0)
    assert session.current_vitals.spo2 <= 100.0


def test_hr_clamped_above_zero(te, session, sm):
    sm.transition_to(session, "GRADE_IV")
    session.current_vitals = session.current_vitals.model_copy(update={"hr": 0.5})
    te.advance(session, 5.0)
    assert session.current_vitals.hr >= 0.0


def test_cascade_through_all_states_to_death(te, session):
    # INITIAL(30) + GRADE_I(90) + GRADE_II(180) + GRADE_III(120) + GRADE_IV(180) = 600s
    te.advance(session, 605.0)
    assert session.is_terminal
    assert session.outcome_id == "OUTCOME_DEATH"


def test_sim_time_accumulates(te, session):
    te.advance(session, 50.0)
    te.advance(session, 50.0)
    assert abs(session.sim_time_seconds - 100.0) < 0.01


def test_advance_does_nothing_on_terminal_session(te, session, sm):
    sm.transition_to(session, "OUTCOME_DEATH")
    vitals_before = session.current_vitals.model_dump()
    te.advance(session, 9999.0)
    assert session.current_vitals.model_dump() == vitals_before
    assert session.sim_time_seconds == 0.0


def test_time_in_current_state_resets_on_transition(te, session):
    te.advance(session, 35.0)  # advances past INITIAL (30s threshold)
    assert session.current_state_id == "GRADE_I"
    assert session.time_in_current_state_seconds < 10.0  # reset to ~5s remainder
