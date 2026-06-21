"""Tests for action validation, application, and logging."""

import pytest
from app.engine.action_processor import ActionNotAvailableError


def _go_to_grade_i(te, session):
    te.advance(session, 35.0)
    assert session.current_state_id == "GRADE_I"


def test_action_unavailable_in_wrong_state(ap, session):
    # In INITIAL_PRESENTATION there are no available actions
    with pytest.raises(ActionNotAvailableError):
        ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")


def test_action_unavailable_after_session_ends(ap, sm, session):
    sm.transition_to(session, "OUTCOME_DEATH")
    with pytest.raises(ActionNotAvailableError, match="finalizado"):
        ap.apply(session, "START_CPR")


def test_valid_action_is_logged(ap, te, session):
    _go_to_grade_i(te, session)
    ap.apply(session, "CALL_FOR_HELP")
    assert len(session.action_log) == 1
    assert session.action_log[0].action_id == "CALL_FOR_HELP"


def test_log_captures_state_before_and_after(ap, te, session):
    _go_to_grade_i(te, session)
    entry = ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")
    assert entry.state_before == "GRADE_I"
    assert entry.state_after == "RESOLVING"


def test_log_captures_vitals_before_and_after(ap, te, session):
    _go_to_grade_i(te, session)
    hr_before = session.current_vitals.hr
    entry = ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")
    assert entry.vitals_before.hr == hr_before
    assert entry.vitals_after.hr > hr_before  # epinephrine raises HR


def test_epinephrine_im_transitions_to_resolving(ap, te, session):
    _go_to_grade_i(te, session)
    ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")
    assert session.current_state_id == "RESOLVING"


def test_epinephrine_im_increases_sbp(ap, te, session):
    _go_to_grade_i(te, session)
    sbp_before = session.current_vitals.sbp
    ap.apply(session, "ADMINISTER_EPINEPHRINE_IM")
    assert session.current_vitals.sbp > sbp_before


def test_fluids_iv_does_not_change_state(ap, te, session):
    te.advance(session, 125.0)  # → GRADE_II
    assert session.current_state_id == "GRADE_II"
    ap.apply(session, "ADMINISTER_FLUIDS_IV")
    assert session.current_state_id == "GRADE_II"


def test_start_cpr_transitions_to_resolving_after_cpr(ap, sm, session):
    sm.transition_to(session, "GRADE_IV")
    ap.apply(session, "START_CPR")
    assert session.current_state_id == "RESOLVING_AFTER_CPR"


def test_action_log_is_immutable_entries(ap, te, session):
    _go_to_grade_i(te, session)
    ap.apply(session, "CALL_FOR_HELP")
    original_id = session.action_log[0].entry_id
    ap.apply(session, "STOP_TRIGGER")
    # First entry unchanged
    assert session.action_log[0].entry_id == original_id


def test_multiple_actions_accumulate_in_log(ap, te, session):
    _go_to_grade_i(te, session)
    ap.apply(session, "CALL_FOR_HELP")
    ap.apply(session, "STOP_TRIGGER")
    assert len(session.action_log) == 2


def test_log_sim_time_is_recorded(ap, te, session):
    te.advance(session, 35.0)  # ~35s in
    ap.apply(session, "CALL_FOR_HELP")
    assert session.action_log[0].sim_time_seconds >= 30.0
