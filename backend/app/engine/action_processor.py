"""
Validates and applies user actions against the current session state.

Every applied action produces an immutable ActionLogEntry appended to the
session log. The log is never modified after appending.
"""

from ..models.scenario import ScenarioDefinition, VitalSignsDelta
from ..models.session import SimulationSession, VitalSigns, ActionLogEntry
from .state_machine import StateMachine


class ActionNotAvailableError(Exception):
    pass


class ActionProcessor:
    def __init__(self, scenario: ScenarioDefinition, sm: StateMachine) -> None:
        self.scenario = scenario
        self.sm = sm

    def apply(self, session: SimulationSession, action_id: str) -> ActionLogEntry:
        if session.is_terminal:
            raise ActionNotAvailableError("La simulación ha finalizado.")

        available = self.sm.available_actions(session)
        if action_id not in available:
            raise ActionNotAvailableError(
                f"Acción '{action_id}' no disponible en estado '{session.current_state_id}'. "
                f"Disponibles: {available}"
            )
        if action_id not in self.scenario.actions:
            raise ActionNotAvailableError(f"Acción '{action_id}' no definida en el escenario.")

        action = self.scenario.actions[action_id]
        state_before = session.current_state_id
        vitals_before = session.current_vitals.model_copy()

        if action.effect.vitals_delta_once:
            session.current_vitals = self._apply_once(
                session.current_vitals, action.effect.vitals_delta_once
            )

        if action.effect.transitions_to:
            self.sm.transition_to(session, action.effect.transitions_to)

        state_after = session.current_state_id
        parts = [action.description]
        if action.effect.transitions_to:
            parts.append(f"→ {self.scenario.states[action.effect.transitions_to].description}")
        if action.effect.notes:
            parts.append(f"Nota: {action.effect.notes}")

        entry = ActionLogEntry(
            sim_time_seconds=session.sim_time_seconds,
            action_id=action_id,
            action_label=action.label,
            state_before=state_before,
            state_after=state_after,
            vitals_before=vitals_before,
            vitals_after=session.current_vitals,
            effect_summary=" | ".join(parts),
        )
        session.action_log.append(entry)
        return entry

    @staticmethod
    def _apply_once(vitals: VitalSigns, delta: VitalSignsDelta) -> VitalSigns:
        return VitalSigns(
            hr=vitals.hr + delta.hr,
            sbp=vitals.sbp + delta.sbp,
            dbp=vitals.dbp + delta.dbp,
            spo2=vitals.spo2 + delta.spo2,
            rr=vitals.rr + delta.rr,
            etco2=vitals.etco2 + delta.etco2,
            temperature=vitals.temperature + delta.temperature,
        ).clamp()
