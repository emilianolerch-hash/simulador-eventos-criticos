"""
Reads session state and generates the structured debriefing report.

Does not modify session state.
Key actions for debriefing are defined per-scenario and marked PENDING_MEDICAL_REVIEW.
"""

from ..models.scenario import ScenarioDefinition
from ..models.session import SimulationSession

# Actions considered "key" for debriefing purposes — PENDING_MEDICAL_REVIEW
_KEY_ACTIONS = {
    "STOP_TRIGGER": "Suspender agente desencadenante",
    "CALL_FOR_HELP": "Solicitar ayuda / Activar código azul",
    "ADMINISTER_EPINEPHRINE_IM": "Adrenalina IM (primera línea)",
    "ADMINISTER_EPINEPHRINE_IV": "Adrenalina IV (colapso hemodinámico)",
    "ADMINISTER_FLUIDS_IV": "Expansión de volumen IV",
    "START_CPR": "Iniciar RCP",
}


class OutcomeEvaluator:
    def __init__(self, scenario: ScenarioDefinition) -> None:
        self.scenario = scenario

    def get_outcome(self, session: SimulationSession):
        if not session.is_terminal or not session.outcome_id:
            return None
        return self.scenario.outcomes.get(session.outcome_id)

    def build_debrief(self, session: SimulationSession) -> dict:
        outcome = self.get_outcome(session)
        if not outcome:
            return {"status": "in_progress", "session_id": session.session_id}

        taken = {e.action_id for e in session.action_log}
        correct = [label for aid, label in _KEY_ACTIONS.items() if aid in taken]
        missed = [label for aid, label in _KEY_ACTIONS.items() if aid not in taken]

        return {
            "session_id": session.session_id,
            "outcome_id": session.outcome_id,
            "outcome_label": outcome.label,
            "outcome_description": outcome.description,
            "educational_message": outcome.educational_message,
            "total_sim_time_seconds": round(session.sim_time_seconds, 1),
            "total_actions_taken": len(session.action_log),
            "sections": {
                "correct_actions": correct,
                "missed_actions": missed,
                "timeline": [
                    {
                        "t": round(e.sim_time_seconds, 1),
                        "action": e.action_label,
                        "state_before": e.state_before,
                        "state_after": e.state_after,
                        "summary": e.effect_summary,
                    }
                    for e in session.action_log
                ],
                "clinical_sources": [
                    {"id": sid, **src.model_dump()}
                    for sid, src in self.scenario.clinical_sources.items()
                ],
            },
            "disclaimer": "PENDING_MEDICAL_REVIEW — Valores educativos no validados clínicamente.",
        }
