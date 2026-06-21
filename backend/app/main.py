from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth.deps import get_current_user_optional
from .auth.router import router as auth_router
from .api.validation import router as validation_router
from .database import Base, engine, get_db
from .engine.action_processor import ActionNotAvailableError, ActionProcessor
from .engine.outcome_evaluator import OutcomeEvaluator
from .engine.state_machine import StateMachine
from .engine.time_engine import TimeEngine
from .loader.scenario_loader import ScenarioLoadError, load_all_scenarios
from .models.db_models import DBActionLogEntry, DBSimulationSession, User
from .models.session import ActionLogEntry, SimulationSession, VitalSigns

_SCENARIOS_DIR = Path(__file__).parent.parent.parent / "scenarios"
_scenarios: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    try:
        loaded = load_all_scenarios(_SCENARIOS_DIR)
        _scenarios.update(loaded)
    except ScenarioLoadError as exc:
        print(f"[ERROR] No se pudieron cargar los escenarios: {exc}")
    yield


app = FastAPI(
    title="Simulador de Eventos Críticos",
    description="Aplicación educativa para anestesiólogos. NO usar en pacientes reales.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(validation_router)


# ── DB ↔ Pydantic helpers ─────────────────────────────────────────────────────

def _db_to_pydantic(db_session: DBSimulationSession) -> SimulationSession:
    entries = [
        ActionLogEntry(
            entry_id=e.entry_id,
            sim_time_seconds=e.sim_time_seconds,
            action_id=e.action_id,
            action_label=e.action_label,
            state_before=e.state_before,
            state_after=e.state_after,
            effect_summary=e.effect_summary,
            vitals_before=VitalSigns(**e.vitals_before) if e.vitals_before else None,
            vitals_after=VitalSigns(**e.vitals_after) if e.vitals_after else None,
        )
        for e in db_session.action_log
    ]
    return SimulationSession(
        session_id=db_session.id,
        scenario_id=db_session.scenario_id,
        started_at=db_session.started_at,
        current_state_id=db_session.current_state_id,
        current_vitals=VitalSigns(**db_session.current_vitals),
        sim_time_seconds=db_session.sim_time_seconds,
        time_in_current_state_seconds=db_session.time_in_current_state_seconds,
        is_terminal=db_session.is_terminal,
        outcome_id=db_session.outcome_id,
        action_log=entries,
    )


def _save_session(db: Session, db_row: DBSimulationSession, session: SimulationSession) -> None:
    db_row.current_state_id = session.current_state_id
    db_row.current_vitals = session.current_vitals.model_dump()
    db_row.sim_time_seconds = session.sim_time_seconds
    db_row.time_in_current_state_seconds = session.time_in_current_state_seconds
    db_row.is_terminal = session.is_terminal
    db_row.outcome_id = session.outcome_id
    db.flush()

    existing_ids = {e.entry_id for e in db_row.action_log}
    for entry in session.action_log:
        if entry.entry_id not in existing_ids:
            db.add(DBActionLogEntry(
                session_id=db_row.id,
                entry_id=entry.entry_id,
                sim_time_seconds=entry.sim_time_seconds,
                action_id=entry.action_id,
                action_label=entry.action_label,
                state_before=entry.state_before,
                state_after=entry.state_after,
                effect_summary=entry.effect_summary,
                vitals_before=entry.vitals_before.model_dump() if entry.vitals_before else None,
                vitals_after=entry.vitals_after.model_dump() if entry.vitals_after else None,
            ))
    db.commit()


def _get_db_session(session_id: str, db: Session) -> DBSimulationSession:
    row = db.get(DBSimulationSession, session_id)
    if not row:
        raise HTTPException(404, f"Sesión '{session_id}' no encontrada")
    return row


def _session_view(session: SimulationSession, effect_summary: Optional[str] = None) -> dict:
    scenario = _scenarios[session.scenario_id]
    sm = StateMachine(scenario)
    state_def = scenario.states[session.current_state_id]
    view = {
        "session_id": session.session_id,
        "state": session.current_state_id,
        "state_description": state_def.description,
        "vitals": session.current_vitals.model_dump(),
        "sim_time_seconds": round(session.sim_time_seconds, 1),
        "is_terminal": session.is_terminal,
        "outcome_id": session.outcome_id,
        "available_actions": sm.available_actions(session),
    }
    if effect_summary is not None:
        view["effect_summary"] = effect_summary
    return view


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "loaded_scenarios": list(_scenarios.keys())}


@app.get("/scenarios")
def list_scenarios():
    return [{"id": s.id, "title": s.title, "version": s.version} for s in _scenarios.values()]


@app.get("/scenarios/{scenario_id}")
def get_scenario_detail(scenario_id: str):
    scenario = _scenarios.get(scenario_id)
    if not scenario:
        raise HTTPException(404, f"Escenario '{scenario_id}' no encontrado")
    return {
        "id": scenario.id,
        "title": scenario.title,
        "version": scenario.version,
        "patient": scenario.patient.model_dump(),
        "actions": {
            aid: {
                "label": a.label,
                "description": a.description,
                "category": a.category,
                "notes": a.effect.notes,
                "transitions_to": a.effect.transitions_to,
            }
            for aid, a in scenario.actions.items()
        },
    }


class CreateSessionRequest(BaseModel):
    scenario_id: str


@app.post("/sessions", status_code=201)
def create_session(
    body: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    scenario = _scenarios.get(body.scenario_id)
    if not scenario:
        raise HTTPException(404, f"Escenario '{body.scenario_id}' no encontrado")
    iv = scenario.initial_vitals
    vitals_dict = {
        "hr": iv.hr, "sbp": iv.sbp, "dbp": iv.dbp,
        "spo2": iv.spo2, "rr": iv.rr, "etco2": iv.etco2,
        "temperature": iv.temperature,
    }
    db_row = DBSimulationSession(
        scenario_id=scenario.id,
        user_id=current_user.id if current_user else None,
        current_state_id=scenario.initial_state_id,
        current_vitals=vitals_dict,
    )
    db.add(db_row)
    db.commit()
    db.refresh(db_row)
    session = _db_to_pydantic(db_row)
    return _session_view(session)


@app.get("/sessions/{session_id}/state")
def get_state(session_id: str, db: Session = Depends(get_db)):
    db_row = _get_db_session(session_id, db)
    return _session_view(_db_to_pydantic(db_row))


class ApplyActionRequest(BaseModel):
    action_id: str


@app.post("/sessions/{session_id}/actions")
def apply_action(session_id: str, body: ApplyActionRequest, db: Session = Depends(get_db)):
    db_row = _get_db_session(session_id, db)
    session = _db_to_pydantic(db_row)
    scenario = _scenarios[session.scenario_id]
    sm = StateMachine(scenario)
    processor = ActionProcessor(scenario, sm)
    try:
        entry = processor.apply(session, body.action_id)
    except ActionNotAvailableError as exc:
        raise HTTPException(400, str(exc))
    _save_session(db, db_row, session)
    view = _session_view(session, effect_summary=entry.effect_summary)
    return view


class AdvanceTimeRequest(BaseModel):
    seconds: float = 10.0


@app.post("/sessions/{session_id}/advance-time")
def advance_time(session_id: str, body: AdvanceTimeRequest, db: Session = Depends(get_db)):
    if body.seconds <= 0:
        raise HTTPException(400, "seconds debe ser positivo")
    db_row = _get_db_session(session_id, db)
    session = _db_to_pydantic(db_row)
    scenario = _scenarios[session.scenario_id]
    sm = StateMachine(scenario)
    te = TimeEngine(scenario, sm)
    te.advance(session, body.seconds)
    _save_session(db, db_row, session)
    return _session_view(session)


@app.get("/sessions/{session_id}/log")
def get_log(session_id: str, db: Session = Depends(get_db)):
    db_row = _get_db_session(session_id, db)
    session = _db_to_pydantic(db_row)
    return {
        "session_id": session_id,
        "total_entries": len(session.action_log),
        "action_log": [e.model_dump(mode="json") for e in session.action_log],
    }


def _get_debrief_dict(session_id: str, db: Session) -> dict:
    db_row = _get_db_session(session_id, db)
    session = _db_to_pydantic(db_row)
    scenario = _scenarios[session.scenario_id]
    evaluator = OutcomeEvaluator(scenario)
    return evaluator.build_debrief(session)


@app.get("/sessions/{session_id}/debrief")
def get_debrief(session_id: str, db: Session = Depends(get_db)):
    return _get_debrief_dict(session_id, db)


# PDF endpoint
import io
from fastapi.responses import StreamingResponse
from .api.pdf import _build_pdf

@app.get("/sessions/{session_id}/pdf")
def get_pdf(session_id: str, db: Session = Depends(get_db)):
    debrief = _get_debrief_dict(session_id, db)
    pdf_bytes = _build_pdf(debrief)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="debrief_{session_id[:8]}.pdf"'
        },
    )
