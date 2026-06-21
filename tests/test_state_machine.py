"""Tests for the deterministic state machine."""

import pytest
from app.engine.state_machine import StateMachine


def test_initial_state(session, scenario):
    assert session.current_state_id == "INITIAL_PRESENTATION"
    assert not session.is_terminal
    assert session.outcome_id is None


def test_no_actions_in_initial_presentation(sm, session):
    assert sm.available_actions(session) == []


def test_auto_advance_not_triggered_before_threshold(sm, session):
    session.time_in_current_state_seconds = 29.9
    advanced = sm.auto_advance(session)
    assert not advanced
    assert session.current_state_id == "INITIAL_PRESENTATION"


def test_auto_advance_triggers_at_threshold(sm, session):
    session.time_in_current_state_seconds = 30.0
    advanced = sm.auto_advance(session)
    assert advanced
    assert session.current_state_id == "GRADE_I"
    assert session.time_in_current_state_seconds == 0.0


def test_grade_i_has_expected_actions(sm, session):
    sm.transition_to(session, "GRADE_I")
    actions = sm.available_actions(session)
    assert "ADMINISTER_EPINEPHRINE_IM" in actions
    assert "STOP_TRIGGER" in actions
    assert "CALL_FOR_HELP" in actions


def test_grade_iv_has_cpr_action(sm, session):
    sm.transition_to(session, "GRADE_IV")
    actions = sm.available_actions(session)
    assert "START_CPR" in actions


def test_terminal_state_has_no_actions(sm, session):
    sm.transition_to(session, "OUTCOME_DEATH")
    assert sm.available_actions(session) == []


def test_terminal_state_sets_outcome(sm, session):
    sm.transition_to(session, "OUTCOME_DEATH")
    assert session.is_terminal
    assert session.outcome_id == "OUTCOME_DEATH"


def test_all_three_terminal_outcomes_exist(scenario):
    outcomes = set(scenario.outcomes.keys())
    assert "OUTCOME_FULL_RECOVERY" in outcomes
    assert "OUTCOME_CARDIAC_ARREST_WITH_RECOVERY" in outcomes
    assert "OUTCOME_DEATH" in outcomes


def test_transition_to_unknown_state_raises(sm, session):
    with pytest.raises(ValueError, match="Unknown state"):
        sm.transition_to(session, "NONEXISTENT_STATE")


def test_auto_advance_does_not_trigger_in_terminal_state(sm, session):
    sm.transition_to(session, "OUTCOME_FULL_RECOVERY")
    session.time_in_current_state_seconds = 99999.0
    advanced = sm.auto_advance(session)
    assert not advanced
    assert session.current_state_id == "OUTCOME_FULL_RECOVERY"
