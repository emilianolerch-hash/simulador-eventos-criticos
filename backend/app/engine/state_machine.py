"""
Deterministic finite state machine.

This class only executes transition rules defined in the scenario YAML.
It makes no clinical decisions of its own.
"""

from ..models.scenario import ScenarioDefinition
from ..models.session import SimulationSession


class StateMachine:
    def __init__(self, scenario: ScenarioDefinition) -> None:
        self.scenario = scenario

    def current_state(self, session: SimulationSession):
        return self.scenario.states[session.current_state_id]

    def auto_advance(self, session: SimulationSession) -> bool:
        """Check time threshold and transition if exceeded. Returns True if transition occurred."""
        state = self.current_state(session)
        if (
            state.is_terminal
            or state.auto_advance_to is None
            or state.auto_advance_after_seconds is None
        ):
            return False
        if session.time_in_current_state_seconds < state.auto_advance_after_seconds:
            return False
        self._do_transition(session, state.auto_advance_to)
        return True

    def transition_to(self, session: SimulationSession, target_state_id: str) -> None:
        """Force an explicit transition (triggered by an action)."""
        if target_state_id not in self.scenario.states:
            raise ValueError(f"Unknown state: {target_state_id}")
        self._do_transition(session, target_state_id)

    def _do_transition(self, session: SimulationSession, target_state_id: str) -> None:
        session.current_state_id = target_state_id
        session.time_in_current_state_seconds = 0.0
        new_state = self.scenario.states[target_state_id]
        if new_state.is_terminal:
            session.is_terminal = True
            session.outcome_id = new_state.outcome_id

    def available_actions(self, session: SimulationSession) -> list[str]:
        if session.is_terminal:
            return []
        return list(self.current_state(session).available_action_ids)
