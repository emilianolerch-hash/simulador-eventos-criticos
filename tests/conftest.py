from pathlib import Path
import pytest

from app.loader.scenario_loader import load_scenario
from app.models.session import SimulationSession, VitalSigns
from app.engine.state_machine import StateMachine
from app.engine.time_engine import TimeEngine
from app.engine.action_processor import ActionProcessor
from app.engine.outcome_evaluator import OutcomeEvaluator

SCENARIO_PATH = Path(__file__).parent.parent / "scenarios" / "anaphylaxis_perioperative_adult.yaml"


@pytest.fixture(scope="session")
def scenario():
    return load_scenario(SCENARIO_PATH)


@pytest.fixture
def session(scenario):
    iv = scenario.initial_vitals
    return SimulationSession(
        scenario_id=scenario.id,
        current_state_id=scenario.initial_state_id,
        current_vitals=VitalSigns(
            hr=iv.hr, sbp=iv.sbp, dbp=iv.dbp,
            spo2=iv.spo2, rr=iv.rr, etco2=iv.etco2,
            temperature=iv.temperature,
        ),
    )


@pytest.fixture
def sm(scenario):
    return StateMachine(scenario)


@pytest.fixture
def te(scenario, sm):
    return TimeEngine(scenario, sm)


@pytest.fixture
def ap(scenario, sm):
    return ActionProcessor(scenario, sm)


@pytest.fixture
def oe(scenario):
    return OutcomeEvaluator(scenario)
