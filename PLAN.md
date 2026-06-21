# PLAN.md — Simulador de Eventos Críticos

## Contexto

Aplicación web educativa para médicos anestesiólogos. Primer prototipo:
escenario de anafilaxia perioperatoria en adulto. Sin IA generativa en esta
fase. Sin base de datos todavía (PostgreSQL se agrega en Etapa 4).

**Principio no negociable:** ninguna regla clínica puede ser inventada por
el modelo de lenguaje. Toda regla lleva estado `PENDING_VALIDATION` hasta que
un médico la revise y firme.

---

## Entorno confirmado

| Herramienta | Versión     |
|-------------|-------------|
| Node.js     | 24.17.0     |
| npm         | 11.13.0     |
| Python      | 3.14.6      |
| pip         | 26.1.2      |
| PostgreSQL   | pendiente   |
| Docker      | por confirmar |

---

## Estructura de carpetas propuesta

```
simulador-eventos-criticos/
├── CLAUDE.md
├── PLAN.md
├── ARCHITECTURE.md
├── README.md
│
├── frontend/                        # Next.js + TypeScript + Tailwind
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx             # Pantalla de selección de escenario
│   │   │   ├── simulation/
│   │   │   │   └── [id]/page.tsx    # Simulación activa
│   │   │   └── debrief/
│   │   │       └── [sessionId]/page.tsx  # Debriefing post-escenario
│   │   ├── components/
│   │   │   ├── VitalSigns.tsx       # Monitor de signos vitales
│   │   │   ├── PatientStatus.tsx    # Estado clínico textual
│   │   │   ├── ActionPanel.tsx      # Acciones disponibles para el usuario
│   │   │   ├── Timeline.tsx         # Log cronológico de acciones
│   │   │   └── DebriefReport.tsx    # Informe estructurado final
│   │   ├── lib/
│   │   │   ├── api.ts               # Cliente HTTP al backend
│   │   │   └── types.ts             # Tipos TypeScript compartidos
│   │   └── hooks/
│   │       └── useSimulation.ts     # Estado reactivo de la sesión
│   ├── package.json
│   └── tailwind.config.ts
│
├── backend/                         # FastAPI + Pydantic
│   ├── app/
│   │   ├── main.py                  # Punto de entrada FastAPI
│   │   ├── engine/
│   │   │   ├── state_machine.py     # FSM determinística
│   │   │   ├── time_engine.py       # Deterioro temporal del paciente
│   │   │   ├── action_processor.py  # Aplica acciones del usuario al estado
│   │   │   └── outcome_evaluator.py # Determina desenlace final
│   │   ├── models/
│   │   │   ├── scenario.py          # Schema Pydantic del escenario YAML
│   │   │   ├── session.py           # Estado de una sesión de simulación
│   │   │   ├── action.py            # Entrada del log de acciones
│   │   │   └── outcome.py           # Modelo de desenlace
│   │   ├── api/
│   │   │   ├── simulation.py        # Endpoints /session, /action, /state
│   │   │   └── scenarios.py         # Endpoint /scenarios (listado)
│   │   └── loader/
│   │       └── scenario_loader.py   # Carga y valida YAML de escenarios
│   ├── requirements.txt
│   └── pyproject.toml
│
├── clinical/                        # Reglas clínicas y fuentes
│   ├── sources/
│   │   └── anaphylaxis_sources.yaml # Fuentes con título, versión, año, URL
│   └── validation/
│       └── validation_log.md        # Registro de qué fue revisado y por quién
│
├── scenarios/                       # Definiciones de escenarios (YAML)
│   └── anaphylaxis_perioperative_adult.yaml
│
└── tests/                           # pytest
    ├── conftest.py
    ├── test_state_machine.py
    ├── test_time_engine.py
    ├── test_action_processor.py
    └── test_anaphylaxis_scenario.py
```

---

## Etapas de implementación

### Etapa 0 — Andamiaje (sin lógica clínica)
**Objetivo:** repositorio arriba, dependencias instaladas, CI básica.

- [ ] Inicializar proyecto Next.js con TypeScript y Tailwind
- [ ] Inicializar proyecto FastAPI con Pydantic y uvicorn
- [ ] Crear `pyproject.toml` y `requirements.txt`
- [ ] Configurar pytest con `conftest.py` vacío
- [ ] Verificar que `npm run dev` y `uvicorn` arrancan sin errores
- [ ] Actualizar `CLAUDE.md` con comandos reales

Criterio de salida: ambos servidores corren; tests vacíos pasan.

---

### Etapa 1 — Modelo de datos clínico y schema del escenario
**Objetivo:** definir con precisión el formato del escenario YAML y los
modelos Pydantic antes de implementar lógica.

- [ ] Diseñar schema YAML del escenario (estados, transiciones, acciones,
      signos vitales iniciales, reglas de deterioro)
- [ ] Crear `scenarios/anaphylaxis_perioperative_adult.yaml` con todos los
      valores marcados `# PENDING_VALIDATION`
- [ ] Crear `clinical/sources/anaphylaxis_sources.yaml` con las fuentes
      iniciales (NAP6, WAO Guidelines, etc.) con los campos requeridos
- [ ] Implementar modelos Pydantic en `backend/app/models/`
- [ ] Implementar `scenario_loader.py` con validación estricta
- [ ] Tests: cargar el YAML y validar contra el schema

Criterio de salida: el YAML carga, valida y produce objetos Pydantic sin
errores. Todas las reglas tienen estado explícito.

---

### Etapa 2 — Motor clínico (FSM + tiempo)
**Objetivo:** núcleo de la simulación funcionando, sin frontend.

- [ ] Implementar `state_machine.py`:
  - Estados del escenario de anafilaxia (ver sección estados abajo)
  - Transiciones determinísticas basadas en acciones y tiempo
- [ ] Implementar `time_engine.py`:
  - Tick configurable (ej. 1 segundo simulado = N ms reales)
  - Función de deterioro por estado sin tratamiento
  - Cálculo de variables fisiológicas derivadas (PA, FC, SpO2)
- [ ] Implementar `action_processor.py`:
  - Lista de acciones válidas por estado
  - Efecto de cada acción sobre el estado del paciente
  - Log inmutable de cada acción con timestamp simulado
- [ ] Implementar `outcome_evaluator.py`:
  - Desenlace 1: Resolución completa (tratamiento correcto y oportuno)
  - Desenlace 2: Daño residual / complicación (tratamiento tardío o incompleto)
  - Desenlace 3: Muerte (sin tratamiento o tratamiento crítico omitido)
- [ ] Tests unitarios para cada módulo
- [ ] Tests de integración: recorrer el escenario completo con acciones
      predefinidas y verificar desenlace

Criterio de salida: se puede ejecutar el escenario completo desde pytest
con tres rutas distintas y obtener el desenlace esperado en cada una.

---

### Etapa 3 — API REST
**Objetivo:** exponer el motor clínico como servicio HTTP.

- [ ] `POST /sessions` — inicia sesión, retorna `session_id` y estado inicial
- [ ] `GET /sessions/{id}/state` — estado actual del paciente
- [ ] `POST /sessions/{id}/actions` — aplica una acción, retorna nuevo estado
- [ ] `GET /sessions/{id}/log` — log completo de acciones
- [ ] `POST /sessions/{id}/advance-time` — avanza el reloj simulado
- [ ] `GET /sessions/{id}/outcome` — desenlace si la sesión terminó
- [ ] `GET /sessions/{id}/debrief` — debriefing estructurado
- [ ] `GET /scenarios` — lista de escenarios disponibles
- [ ] Tests de endpoints con `httpx` y `pytest`

Criterio de salida: todos los endpoints responden correctamente; las
sesiones son stateful en memoria (sin DB todavía).

---

### Etapa 4 — Frontend básico
**Objetivo:** interfaz funcional conectada al backend.

- [ ] Pantalla de selección de escenario (`/`)
- [ ] Monitor de signos vitales en tiempo real (FC, PA, SpO2, FR, temperatura)
- [ ] Panel de acciones disponibles (botones con las acciones del estado actual)
- [ ] Timeline de acciones realizadas
- [ ] Estado textual del paciente (descripción clínica)
- [ ] Avance de tiempo con botón o automático
- [ ] Pantalla de desenlace
- [ ] Pantalla de debriefing con:
  - Resumen de la sesión (tiempo total, acciones tomadas)
  - Análisis de acciones correctas, tardías y omitidas
  - Comparación con protocolo de referencia
  - Fuentes clínicas utilizadas

Criterio de salida: un médico puede completar el escenario de anafilaxia
de inicio a fin en el navegador.

---

### Etapa 5 — Persistencia y validación médica
**Objetivo:** reemplazar estado en memoria por PostgreSQL; habilitar
flujo de revisión clínica.

- [ ] Esquema de base de datos (sesiones, logs, usuarios)
- [ ] Migración con Alembic
- [ ] Autenticación básica (sin roles complejos aún)
- [ ] Panel de validación: marcar reglas como `VALIDATED` con firma y fecha
- [ ] Exportar sesión como PDF para portafolio docente

---

## Estados del escenario de anafilaxia (borrador clínico)

> Todos los valores numéricos son PENDING_VALIDATION

```
INITIAL_PRESENTATION
  → El paciente recibe el agente desencadenante
  → Signos: normal / leve inquietud

GRADE_I_REACTION          (minuto 1-3)
  → Urticaria, rubor, sin compromiso hemodinámico
  → Transición automática a GRADE_II si no hay acción en T min

GRADE_II_REACTION         (minuto 3-7)
  → Hipotensión leve, taquicardia, broncoespasmo leve
  → Requiere epinefrina IM o IV (dosis PENDING_VALIDATION)

GRADE_III_REACTION        (minuto 7-15)
  → Colapso cardiovascular, broncoespasmo severo, pérdida de consciencia
  → Requiere epinefrina IV, fluidoterapia agresiva, posición Trendelenburg

GRADE_IV_REACTION         (paro cardíaco)
  → RCP, epinefrina según protocolo ACLS (PENDING_VALIDATION)

RESOLVING
  → Respuesta al tratamiento, signos mejorando
  → Puede reaparecer (reacción bifásica, PENDING_VALIDATION)

OUTCOME_FULL_RECOVERY
OUTCOME_COMPLICATIONS
OUTCOME_DEATH
```

---

## Riesgos identificados

### Riesgos clínicos (alta prioridad)

| Riesgo | Descripción | Mitigación |
|--------|-------------|-----------|
| **RC-01** | Dosis incorrectas enseñadas como correctas | Marcar PENDING_VALIDATION; bloquear deploy hasta revisión médica |
| **RC-02** | Reglas de deterioro no fisiológicas | FSM determinística basada en fuentes; ningún valor inferido por LLM |
| **RC-03** | Omisión de contraindicaciones relevantes | Checklist por droga en el YAML; revisión obligatoria antes de Etapa 4 |
| **RC-04** | Reacción bifásica ignorada en el modelo | Incluir estado BIPHASIC_RISK con ventana temporal (PENDING_VALIDATION) |
| **RC-05** | Confusión entre uso educativo y clínico | Disclaimer permanente en UI; no guardar datos de pacientes reales |

### Riesgos técnicos

| Riesgo | Descripción | Mitigación |
|--------|-------------|-----------|
| **RT-01** | Estado en memoria no persiste entre reinicios | Aceptable en Etapa 0-3; PostgreSQL en Etapa 5 |
| **RT-02** | Desincronización entre tick de tiempo y UI | Usar polling HTTP en prototipo; WebSocket más adelante |
| **RT-03** | Schema YAML evoluciona y rompe escenarios viejos | Versión explícita en el YAML; migración de schema con tests |
| **RT-04** | FSM demasiado rígida para escenarios complejos | Diseñar el schema con nodos de transición genéricos desde el inicio |
| **RT-05** | Python 3.14 puede tener incompatibilidades con libs | Fijar versiones en `requirements.txt`; probar inmediatamente |

---

## Fuentes clínicas candidatas (a validar)

1. **NAP6** — Sixth National Audit Project (RCoA/AAGBI), 2018
2. **WAO Anaphylaxis Guidelines** — World Allergy Organization, 2020
3. **ACAAI/AAAAI Joint Task Force** — Practice Parameter, 2015 (actualización pendiente)
4. **UpToDate: Anaphylaxis: Emergency treatment** — versión a confirmar
5. **ACLS Guidelines** — AHA, 2020 (para grado IV / paro cardíaco)

> Todas deben registrarse en `clinical/sources/anaphylaxis_sources.yaml`
> con campos: `title`, `version`, `year`, `url`, `review_date`, `validated_by`.

---

## Definición de "listo para Etapa siguiente"

Cada etapa requiere:
1. Tests pasan (`pytest` y/o `npm test`)
2. Sin valores clínicos sin estado explícito (`PENDING_VALIDATION` o `VALIDATED`)
3. Sin TODOs de seguridad clínica abiertos
4. Revisión manual del output de la etapa anterior
