"""
Tests de integración para los endpoints REST de FastAPI.
Usa TestClient (sincrónico) con el lifespan completo para cargar escenarios.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

SCENARIO_ID = "anaphylaxis_perioperative_adult_v1"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sid(client):
    """Sesión fresca para cada test."""
    r = client.post("/sessions", json={"scenario_id": SCENARIO_ID})
    assert r.status_code == 201
    return r.json()["session_id"]


# ── /health ───────────────────────────────────────────────────────────────────

def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_lists_loaded_scenario(client):
    assert SCENARIO_ID in client.get("/health").json()["loaded_scenarios"]


# ── /scenarios ────────────────────────────────────────────────────────────────

def test_list_scenarios_returns_list(client):
    r = client.get("/scenarios")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert any(s["id"] == SCENARIO_ID for s in r.json())


def test_scenario_detail_structure(client):
    r = client.get(f"/scenarios/{SCENARIO_ID}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == SCENARIO_ID
    assert "patient" in data
    assert "actions" in data


def test_scenario_detail_patient_fields(client):
    data = client.get(f"/scenarios/{SCENARIO_ID}").json()
    p = data["patient"]
    assert p["age"] == 42
    assert p["asa_class"] == "II"


def test_scenario_detail_all_actions_have_category(client):
    data = client.get(f"/scenarios/{SCENARIO_ID}").json()
    missing = [aid for aid, a in data["actions"].items() if not a.get("category")]
    assert missing == [], f"Acciones sin category: {missing}"


def test_scenario_detail_known_actions_present(client):
    data = client.get(f"/scenarios/{SCENARIO_ID}").json()
    for expected in ["ADMINISTER_EPINEPHRINE_IM", "STOP_TRIGGER", "START_CPR", "ADMINISTER_O2_100"]:
        assert expected in data["actions"], f"Acción {expected} ausente"


def test_scenario_detail_o2_action_category(client):
    data = client.get(f"/scenarios/{SCENARIO_ID}").json()
    assert data["actions"]["ADMINISTER_O2_100"]["category"] == "oxygen"


def test_scenario_detail_unknown_scenario(client):
    r = client.get("/scenarios/does_not_exist")
    assert r.status_code == 404


# ── /sessions ────────────────────────────────────────────────────────────────

def test_create_session_returns_201(client):
    r = client.post("/sessions", json={"scenario_id": SCENARIO_ID})
    assert r.status_code == 201


def test_create_session_initial_state(client):
    r = client.post("/sessions", json={"scenario_id": SCENARIO_ID})
    data = r.json()
    assert data["state"] == "INITIAL_PRESENTATION"
    assert data["available_actions"] == []
    assert data["is_terminal"] is False
    assert data["vitals"]["hr"] == 78.0


def test_create_session_unknown_scenario(client):
    r = client.post("/sessions", json={"scenario_id": "fake"})
    assert r.status_code == 404


# ── /sessions/{id}/state ─────────────────────────────────────────────────────

def test_get_state_initial(client, sid):
    r = client.get(f"/sessions/{sid}/state")
    assert r.status_code == 200
    assert r.json()["state"] == "INITIAL_PRESENTATION"


def test_get_state_unknown_session(client):
    r = client.get("/sessions/nonexistent/state")
    assert r.status_code == 404


# ── /sessions/{id}/advance-time ──────────────────────────────────────────────

def test_advance_time_to_grade_i(client, sid):
    r = client.post(f"/sessions/{sid}/advance-time", json={"seconds": 35})
    assert r.status_code == 200
    data = r.json()
    assert data["state"] == "GRADE_I"
    assert "ADMINISTER_EPINEPHRINE_IM" in data["available_actions"]
    assert "ADMINISTER_O2_100" in data["available_actions"]


def test_advance_time_negative_rejected(client, sid):
    r = client.post(f"/sessions/{sid}/advance-time", json={"seconds": -5})
    assert r.status_code == 400


def test_advance_time_large_jump_reaches_death(client):
    sid = client.post("/sessions", json={"scenario_id": SCENARIO_ID}).json()["session_id"]
    r = client.post(f"/sessions/{sid}/advance-time", json={"seconds": 700})
    assert r.status_code == 200
    data = r.json()
    assert data["is_terminal"] is True
    assert data["outcome_id"] == "OUTCOME_DEATH"


def test_advance_time_on_terminal_session_does_not_change_state(client):
    sid = client.post("/sessions", json={"scenario_id": SCENARIO_ID}).json()["session_id"]
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 700})
    state_before = client.get(f"/sessions/{sid}/state").json()
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 100})
    state_after = client.get(f"/sessions/{sid}/state").json()
    assert state_before["vitals"] == state_after["vitals"]


# ── /sessions/{id}/actions ───────────────────────────────────────────────────

def test_apply_action_in_initial_state_rejected(client, sid):
    r = client.post(f"/sessions/{sid}/actions", json={"action_id": "CALL_FOR_HELP"})
    assert r.status_code == 400


def test_apply_call_for_help_in_grade_i(client, sid):
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 35})
    r = client.post(f"/sessions/{sid}/actions", json={"action_id": "CALL_FOR_HELP"})
    assert r.status_code == 200
    data = r.json()
    assert "effect_summary" in data
    assert data["state"] == "GRADE_I"   # CALL_FOR_HELP does not change state


def test_apply_epinephrine_im_transitions_to_resolving(client, sid):
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 35})
    r = client.post(f"/sessions/{sid}/actions", json={"action_id": "ADMINISTER_EPINEPHRINE_IM"})
    assert r.status_code == 200
    assert r.json()["state"] == "RESOLVING"


def test_apply_o2_in_grade_i(client, sid):
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 35})
    r = client.post(f"/sessions/{sid}/actions", json={"action_id": "ADMINISTER_O2_100"})
    assert r.status_code == 200
    assert r.json()["state"] == "GRADE_I"   # O2 doesn't change state


def test_apply_cpr_transitions_to_resolving_after_cpr(client):
    sid = client.post("/sessions", json={"scenario_id": SCENARIO_ID}).json()["session_id"]
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 425})
    assert client.get(f"/sessions/{sid}/state").json()["state"] == "GRADE_IV"
    r = client.post(f"/sessions/{sid}/actions", json={"action_id": "START_CPR"})
    assert r.status_code == 200
    assert r.json()["state"] == "RESOLVING_AFTER_CPR"


# ── /sessions/{id}/log ───────────────────────────────────────────────────────

def test_log_empty_initially(client, sid):
    r = client.get(f"/sessions/{sid}/log")
    assert r.status_code == 200
    assert r.json()["total_entries"] == 0


def test_log_records_actions(client, sid):
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 35})
    client.post(f"/sessions/{sid}/actions", json={"action_id": "CALL_FOR_HELP"})
    client.post(f"/sessions/{sid}/actions", json={"action_id": "STOP_TRIGGER"})
    r = client.get(f"/sessions/{sid}/log")
    data = r.json()
    assert data["total_entries"] == 2
    assert data["action_log"][0]["action_id"] == "CALL_FOR_HELP"


def test_log_entry_has_required_fields(client, sid):
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 35})
    client.post(f"/sessions/{sid}/actions", json={"action_id": "CALL_FOR_HELP"})
    entry = client.get(f"/sessions/{sid}/log").json()["action_log"][0]
    for field in ("action_id", "action_label", "state_before", "state_after", "sim_time_seconds"):
        assert field in entry, f"Log entry falta campo: {field}"


# ── /sessions/{id}/debrief ───────────────────────────────────────────────────

def test_debrief_in_progress(client, sid):
    r = client.get(f"/sessions/{sid}/debrief")
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"


def test_debrief_full_recovery(client):
    sid = client.post("/sessions", json={"scenario_id": SCENARIO_ID}).json()["session_id"]
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 35})
    client.post(f"/sessions/{sid}/actions", json={"action_id": "ADMINISTER_EPINEPHRINE_IM"})
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 305})
    r = client.get(f"/sessions/{sid}/debrief")
    assert r.status_code == 200
    data = r.json()
    assert data["outcome_id"] == "OUTCOME_FULL_RECOVERY"
    assert "sections" in data
    assert "clinical_sources" in data["sections"]


def test_debrief_death_has_missed_actions(client):
    sid = client.post("/sessions", json={"scenario_id": SCENARIO_ID}).json()["session_id"]
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 700})
    data = client.get(f"/sessions/{sid}/debrief").json()
    assert data["outcome_id"] == "OUTCOME_DEATH"
    assert len(data["sections"]["missed_actions"]) > 0
    assert data["sections"]["correct_actions"] == []


def test_debrief_has_disclaimer(client):
    sid = client.post("/sessions", json={"scenario_id": SCENARIO_ID}).json()["session_id"]
    client.post(f"/sessions/{sid}/advance-time", json={"seconds": 700})
    data = client.get(f"/sessions/{sid}/debrief").json()
    assert "PENDING_MEDICAL_REVIEW" in data["disclaimer"]
