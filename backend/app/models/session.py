"""
Runtime state for an active simulation session.

The action_log is append-only. Entries are never modified after creation.
"""

from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field


class VitalSigns(BaseModel):
    hr: float           # bpm
    sbp: float          # mmHg systolic
    dbp: float          # mmHg diastolic
    spo2: float         # %
    rr: float           # breaths/min
    etco2: float        # mmHg
    temperature: float  # °C

    def clamp(self) -> "VitalSigns":
        return VitalSigns(
            hr=max(0.0, min(300.0, self.hr)),
            sbp=max(0.0, min(250.0, self.sbp)),
            dbp=max(0.0, min(200.0, self.dbp)),
            spo2=max(0.0, min(100.0, self.spo2)),
            rr=max(0.0, min(60.0, self.rr)),
            etco2=max(0.0, min(80.0, self.etco2)),
            temperature=max(30.0, min(45.0, self.temperature)),
        )


class ActionLogEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid4()))
    sim_time_seconds: float
    real_time_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action_id: str
    action_label: str
    state_before: str
    state_after: str
    vitals_before: Optional[VitalSigns] = None
    vitals_after: Optional[VitalSigns] = None
    effect_summary: str


class SimulationSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    scenario_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_state_id: str
    current_vitals: VitalSigns
    sim_time_seconds: float = 0.0
    time_in_current_state_seconds: float = 0.0
    action_log: list[ActionLogEntry] = Field(default_factory=list)
    is_terminal: bool = False
    outcome_id: Optional[str] = None
