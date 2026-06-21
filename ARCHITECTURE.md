# ARCHITECTURE.md — Simulador de Eventos Críticos

## Visión general

Sistema de dos capas desacopladas: un **motor clínico** (Python/FastAPI) que
contiene toda la lógica determinística, y un **frontend educativo**
(Next.js) que visualiza el estado y recibe acciones del usuario. Los
escenarios clínicos se definen en YAML y son ajenos al código.

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND  (Next.js + TypeScript + Tailwind)                    │
│                                                                 │
│  ┌────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ VitalSigns │  │ActionPanel  │  │Timeline  │  │Debrief   │  │
│  │  Monitor   │  │(actions by  │  │(action   │  │Report    │  │
│  │ (FC/PA/    │  │ FSM state)  │  │ log)     │  │          │  │
│  │  SpO2/FR)  │  └─────────────┘  └──────────┘  └──────────┘  │
│  └────────────┘                                                 │
│         │                   HTTP REST (JSON)                    │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND  (FastAPI + Pydantic)                                  │
│                                                                 │
│  API Layer                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  /sessions  /sessions/{id}/state  /sessions/{id}/actions │   │
│  │  /sessions/{id}/log  /sessions/{id}/debrief  /scenarios  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Engine Layer                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ StateMachine │  │  TimeEngine  │  │   ActionProcessor     │ │
│  │              │  │              │  │                       │ │
│  │ Transiciones │  │ Deterioro    │  │ Valida y aplica       │ │
│  │ determiníst. │  │ temporal     │  │ acciones del usuario  │ │
│  │ desde YAML   │  │ por estado   │  │ Actualiza estado FSM  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬────────────┘ │
│         └─────────────────┴──────────────────────┘             │
│                           │                                     │
│  ┌────────────────────────▼───────────────────────────────────┐ │
│  │              OutcomeEvaluator                              │ │
│  │  Evalúa condición de término → 3 desenlaces posibles       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Data Layer                                                     │
│  ┌──────────────────────┐   ┌──────────────────────────────┐   │
│  │   ScenarioLoader     │   │   SessionStore               │   │
│  │   (YAML → Pydantic)  │   │   (en memoria, luego PgSQL)  │   │
│  └──────────────────────┘   └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCENARIOS  (YAML)                                              │
│  anaphylaxis_perioperative_adult.yaml                           │
│  Contiene: estados, transiciones, acciones, vitales,           │
│  reglas de deterioro, fuentes, estado de validación            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Principios de diseño

### 1. Separación entre datos clínicos y lógica de ejecución

El motor clínico (`engine/`) no conoce la anafilaxia. Solo sabe ejecutar
una FSM genérica. Todo el conocimiento médico está en el YAML del escenario.
Esto permite agregar nuevos escenarios sin modificar código.

### 2. Determinismo total

Dado un estado inicial, una secuencia de acciones y un delta de tiempo, el
resultado es siempre idéntico. No hay aleatoriedad, no hay LLM en el camino
crítico. Permite reproducibilidad para debriefing y testing.

### 3. Trazabilidad clínica obligatoria

Cada regla, dosis, umbral o intervalo de tiempo en el YAML tiene un campo
`validation_status`:
- `PENDING_VALIDATION` — valor provisional, no debe usarse en práctica clínica
- `VALIDATED` — revisado por médico firmante con nombre, institución y fecha

El `ScenarioLoader` rechaza cargar un escenario si falta este campo en alguna
regla.

### 4. Log inmutable

Cada acción del usuario genera una entrada en el log con:
- `timestamp_sim` — tiempo dentro de la simulación
- `timestamp_real` — tiempo real UTC
- `action_id` — identificador de la acción
- `state_before` — estado FSM antes de la acción
- `state_after` — estado FSM resultante
- `effect_summary` — descripción en lenguaje natural del efecto

El log se usa para generar el debriefing y no puede modificarse.

---

## Máquina de estados del escenario de anafilaxia

### Diagrama de transiciones

```
                    ┌─────────────────────┐
                    │ INITIAL_PRESENTATION│
                    │ (agente desencad.)  │
                    └──────────┬──────────┘
                               │ automático t=0
                               ▼
                    ┌─────────────────────┐
                    │    GRADE_I           │ ←── Urticaria, rubor
                    │  (min 1-3)           │     Sin compromiso hemo
                    └──────────┬──────────┘
              sin tto /        │ tto correcto
              t > umbral       ▼
                    ┌─────────────────────┐
       ┌────────────│    GRADE_II          │ ←── Hipotensión leve
       │            │  (min 3-7)           │     Taquicardia
       │            └──────────┬──────────┘     Broncoespasmo leve
       │      sin tto /        │ tto correcto
       │      t > umbral       ▼
       │            ┌─────────────────────┐
       │  ┌─────────│    GRADE_III         │ ←── Colapso cardiovasc.
       │  │         │  (min 7-15)          │     Broncoespasmo severo
       │  │         └──────────┬──────────┘
       │  │    sin tto /       │ tto correcto
       │  │    t > umbral      ▼
       │  │         ┌─────────────────────┐
       │  │         │    GRADE_IV          │ ←── Paro cardíaco
       │  │         │  (paro)              │
       │  │         └──────────┬──────────┘
       │  │              RCP / │ sin RCP
       │  │              epinefrina
       │  │                    │
       │  │    ┌───────────────┴───────────────┐
       │  │    ▼                               ▼
       │  │ RESOLVING                    OUTCOME_DEATH
       │  │    │
       │  │    │ (ventana bifásica)
       │  │    ├────────────────────────────────┐
       │  │    │ sin complicación               │ reacción bifásica /
       │  │    ▼                                │ tto incompleto
       │  │ OUTCOME_FULL_RECOVERY               ▼
       │  └────────────────────────────► OUTCOME_COMPLICATIONS
       └───────────────────────────────────────┘
                    (escalada no tratada)
```

### Tres desenlaces posibles

| Desenlace | Condición | Descripción educativa |
|-----------|-----------|----------------------|
| `OUTCOME_FULL_RECOVERY` | Tratamiento correcto y oportuno | Paciente estable, sin secuelas |
| `OUTCOME_COMPLICATIONS` | Tratamiento tardío o incompleto | Alta con daño residual (p.ej. hipoxia prolongada) |
| `OUTCOME_DEATH` | Sin tratamiento / Grado IV sin RCP | Muerte perioperatoria |

---

## Schema del escenario YAML

```yaml
# scenarios/anaphylaxis_perioperative_adult.yaml
scenario:
  id: "anaphylaxis_perioperative_adult_v1"
  title: "Anafilaxia Perioperatoria — Paciente Adulto"
  version: "0.1.0-draft"
  language: "es"
  target_audience: "anesthesiologist"
  educational_disclaimer: true    # Bloquea si es false

patient:
  age: 42                         # años
  weight: 75                      # kg — PENDING_VALIDATION uso en dosis
  sex: "male"
  asa_class: "II"
  context: "Inducción anestésica para colecistectomía laparoscópica"

initial_vitals:
  hr: 78                          # lpm
  sbp: 125                        # mmHg sistólica
  dbp: 80                         # mmHg diastólica
  spo2: 99                        # %
  rr: 14                          # rpm
  etco2: 38                       # mmHg
  temperature: 36.5               # °C
  skin: "normal"

states:
  INITIAL_PRESENTATION:
    description: "El paciente recibe látex durante preparación quirúrgica."
    auto_advance_to: "GRADE_I"
    auto_advance_after_seconds: 30   # PENDING_VALIDATION
    available_actions: []

  GRADE_I:
    description: "Urticaria generalizada, rubor facial, sin compromiso hemodinámico."
    vitals_delta:                    # cambio por segundo sin tratamiento
      hr: +0.5                       # PENDING_VALIDATION
      sbp: -0.2                      # PENDING_VALIDATION
      spo2: 0
    available_actions:
      - ADMINISTER_ANTIHISTAMINE_IV
      - ADMINISTER_EPINEPHRINE_IM
      - STOP_TRIGGER
      - CALL_FOR_HELP
    auto_advance_to: "GRADE_II"
    auto_advance_after_seconds: 120  # PENDING_VALIDATION
    ...

actions:
  ADMINISTER_EPINEPHRINE_IM:
    label: "Adrenalina IM 0.3 mg (muslo lateral)"
    dose: "0.3 mg"                   # PENDING_VALIDATION — fuente: WAO 2020
    route: "IM"
    onset_seconds: 8                 # PENDING_VALIDATION
    effect_on_vitals:
      hr: +15                        # PENDING_VALIDATION
      sbp: +30                       # PENDING_VALIDATION
    transitions_to: null             # no cambia estado por sí solo
    validation_status: "PENDING_VALIDATION"
    source_ref: "WAO_ANAPHYLAXIS_2020"

clinical_sources:
  WAO_ANAPHYLAXIS_2020:
    title: "World Allergy Organization Anaphylaxis Guidance"
    version: "2020"
    year: 2020
    url: "https://www.worldallergy.org/education-and-programs/..."
    review_date: null               # pendiente de asignación
    validated_by: null

outcomes:
  OUTCOME_FULL_RECOVERY:
    label: "Recuperación completa"
    condition: "reached_RESOLVING AND no_biphasic_reaction"
  OUTCOME_COMPLICATIONS:
    label: "Complicaciones"
    condition: "treatment_delayed OR biphasic_reaction_untreated"
  OUTCOME_DEATH:
    label: "Muerte"
    condition: "grade_iv_without_cpr OR cpr_failed"

debriefing_template:
  sections:
    - id: "timeline_review"
      title: "Revisión cronológica"
    - id: "correct_actions"
      title: "Acciones correctas"
    - id: "missed_actions"
      title: "Acciones omitidas o tardías"
    - id: "protocol_comparison"
      title: "Comparación con protocolo de referencia"
    - id: "clinical_sources"
      title: "Fuentes clínicas"
```

---

## Modelo de sesión (en memoria, Etapa 0-3)

```python
# Pydantic — backend/app/models/session.py

class SimulationSession(BaseModel):
    session_id: str
    scenario_id: str
    started_at: datetime
    current_state: str
    current_vitals: VitalSigns
    sim_time_seconds: int           # tiempo simulado transcurrido
    action_log: list[ActionLogEntry]
    is_terminal: bool
    outcome: Optional[str]
```

---

## API REST — Contratos principales

### POST /sessions
```json
// Request
{ "scenario_id": "anaphylaxis_perioperative_adult_v1" }

// Response 201
{
  "session_id": "uuid",
  "state": "INITIAL_PRESENTATION",
  "vitals": { "hr": 78, "sbp": 125, "spo2": 99, ... },
  "sim_time_seconds": 0,
  "available_actions": []
}
```

### POST /sessions/{id}/actions
```json
// Request
{ "action_id": "ADMINISTER_EPINEPHRINE_IM" }

// Response 200
{
  "state": "GRADE_II",
  "vitals": { "hr": 93, "sbp": 95, "spo2": 94, ... },
  "sim_time_seconds": 185,
  "effect_summary": "Adrenalina IM administrada. FC aumenta. PA en recuperación.",
  "available_actions": ["ADMINISTER_FLUIDS_IV", "ADMINISTER_EPINEPHRINE_IV", ...]
}
```

### GET /sessions/{id}/debrief
```json
{
  "outcome": "OUTCOME_COMPLICATIONS",
  "total_sim_time_seconds": 620,
  "sections": {
    "timeline_review": [...],
    "correct_actions": ["STOP_TRIGGER", "CALL_FOR_HELP"],
    "missed_actions": ["ADMINISTER_EPINEPHRINE_IM omitida hasta minuto 6"],
    "protocol_comparison": "...",
    "clinical_sources": [...]
  }
}
```

---

## Decisiones técnicas y razones

| Decisión | Razón |
|----------|-------|
| YAML para escenarios, no código Python | Permite editar reglas clínicas sin tocar el motor; facilita revisión médica |
| FSM determinística, sin LLM en ruta crítica | Garantiza reproducibilidad y auditabilidad clínica |
| Estado en memoria en prototipo | Elimina complejidad de DB mientras el schema evoluciona; PostgreSQL en Etapa 5 |
| Polling HTTP en prototipo, no WebSocket | Suficiente para MVP; WebSocket se agrega si el tiempo real se vuelve crítico |
| `validation_status` en cada regla del YAML | Imposible olvidar marcar un valor; el loader lo valida en arranque |
| Debriefing generado por el motor, no por LLM | El feedback educativo es determinístico y auditado, no generado |

---

## Lo que NO hace esta arquitectura (intencionalmente)

- **Sin IA generativa en ruta clínica**: ninguna decisión fisiológica pasa por un LLM.
- **Sin datos de pacientes reales**: la sesión no almacena información identificable.
- **Sin networking externo en el motor clínico**: el backend no llama a APIs externas.
- **Sin roles/autenticación complejos en Etapa 0-4**: fuera de scope del prototipo.
