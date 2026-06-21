"""
Simulation clock and patient deterioration.

Advances sim time in slices so that state auto-advances cascade correctly
within a single call — e.g. advance(10000) will traverse all states until
a terminal outcome is reached.

All deterioration rates come from the scenario YAML (PENDING_MEDICAL_REVIEW).
"""

from ..models.scenario import ScenarioDefinition, VitalSignsDelta
from ..models.session import SimulationSession, VitalSigns
from .state_machine import StateMachine

_MAX_ITERATIONS = 500


class TimeEngine:
    def __init__(self, scenario: ScenarioDefinition, sm: StateMachine) -> None:
        self.scenario = scenario
        self.sm = sm

    def advance(self, session: SimulationSession, seconds: float) -> None:
        """
        Advance the simulation clock by `seconds`.
        Splits time at state boundaries so deterioration is applied accurately
        per state, and cascades through auto-advances automatically.
        """
        if session.is_terminal or seconds <= 0.0:
            return

        remaining = seconds

        for _ in range(_MAX_ITERATIONS):
            if remaining <= 0.0 or session.is_terminal:
                break

            state = self.scenario.states[session.current_state_id]

            if (
                not state.is_terminal
                and state.auto_advance_to is not None
                and state.auto_advance_after_seconds is not None
            ):
                time_until_advance = max(
                    0.0,
                    state.auto_advance_after_seconds - session.time_in_current_state_seconds,
                )
                if time_until_advance == 0.0:
                    self.sm.auto_advance(session)
                    continue
                time_step = min(remaining, time_until_advance)
            else:
                time_step = remaining

            session.sim_time_seconds += time_step
            session.time_in_current_state_seconds += time_step
            remaining -= time_step

            state = self.scenario.states[session.current_state_id]
            if state.vitals_delta_per_second:
                session.current_vitals = self._apply_delta(
                    session.current_vitals, state.vitals_delta_per_second, time_step
                )

            self.sm.auto_advance(session)

    @staticmethod
    def _apply_delta(vitals: VitalSigns, delta: VitalSignsDelta, seconds: float) -> VitalSigns:
        return VitalSigns(
            hr=vitals.hr + delta.hr * seconds,
            sbp=vitals.sbp + delta.sbp * seconds,
            dbp=vitals.dbp + delta.dbp * seconds,
            spo2=vitals.spo2 + delta.spo2 * seconds,
            rr=vitals.rr + delta.rr * seconds,
            etco2=vitals.etco2 + delta.etco2 * seconds,
            temperature=vitals.temperature + delta.temperature * seconds,
        ).clamp()
