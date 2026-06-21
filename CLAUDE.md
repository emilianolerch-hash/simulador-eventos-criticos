# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

Simulador de Eventos Críticos — aplicación web educativa para anestesiólogos.
Primer escenario: anafilaxia perioperatoria en adulto.
Ver `PLAN.md` para etapas y `ARCHITECTURE.md` para diseño técnico.

**Regla no negociable:** ningún valor clínico (dosis, umbrales, tiempos)
puede ser inventado o inferido. Todo debe tener `validation_status` explícito
en el YAML del escenario.

## Entorno

| Herramienta | Versión  |
|-------------|----------|
| Node.js     | 24.17.0  |
| Python      | 3.14.6   |
| PostgreSQL  | Etapa 5  |

## Comandos

```bash
# Tests (desde la raíz del proyecto)
python3 -m pytest tests/ -v

# Test individual
python3 -m pytest tests/test_state_machine.py::test_initial_state -v

# Backend API
cd backend && uvicorn app.main:app --reload

# Frontend (pendiente Etapa 4)
cd frontend && npm run dev
```

El `pyproject.toml` en la raíz configura `pythonpath = ["backend"]` para pytest.

## Estructura clave

```
scenarios/    ← YAML de escenarios clínicos (fuente de verdad)
clinical/     ← fuentes médicas y log de validación
backend/app/engine/   ← motor FSM determinístico
backend/app/models/   ← Pydantic schemas
frontend/src/components/  ← UI de simulación
tests/        ← pytest para el motor clínico
```

## Reglas de desarrollo

- El `ScenarioLoader` debe rechazar cualquier regla sin `validation_status`.
- El log de acciones es inmutable; nunca agregar lógica que lo modifique.
- El backend no debe llamar a APIs externas ni LLMs.
- Antes de agregar cualquier valor clínico numérico, agregar la fuente en
  `clinical/sources/` y marcarlo `PENDING_VALIDATION`.
- Las tres rutas de desenlace deben ser verificables con un test pytest
  que recorra el escenario completo con acciones predefinidas.
