# Log de Validación Clínica — Anafilaxia Perioperatoria

**Escenario:** `anaphylaxis_perioperative_adult_v1`
**Estado general:** `PENDING_MEDICAL_REVIEW`
**Última actualización:** 2026-06-21

> Ninguna regla tiene estado `VALIDATED` hasta que un médico especialista
> la revise y firme en el panel de administración (`/admin`).
> Este log refleja el estado actual y registra las fuentes candidatas
> para cada regla pendiente.

---

## Resumen de estado

| Total de reglas | Validadas | Pendientes |
|:---:|:---:|:---:|
| 14 | 0 | 14 |

---

## Reglas pendientes de validación

### Dosis de medicamentos

| ID de regla | Descripción | Valor provisional | Fuentes candidatas | Estado |
|---|---|---|---|---|
| `action:ADMINISTER_EPINEPHRINE_IM:dose` | Adrenalina IM — dosis adulto (muslo lateral) | 0.3 mg | NAP6, WAO_2020, ACAAI_AAAAI_2015 | ⬜ PENDIENTE |
| `action:ADMINISTER_EPINEPHRINE_IV:dose` | Adrenalina IV bolo lento — colapso hemodinámico | 0.1 mg | NAP6, WAO_2020 | ⬜ PENDIENTE |
| `action:ADMINISTER_EPINEPHRINE_CPR:dose` | Adrenalina IV durante RCP — protocolo ACLS | 1 mg | AHA_ACLS_2020 | ⬜ PENDIENTE |
| `action:ADMINISTER_FLUIDS_IV:dose` | Solución salina — expansión de volumen | 500 mL IV rápido | NAP6, WAO_2020, AUSTRALASIAN_ANAPHYLAXIS_2021 | ⬜ PENDIENTE |
| `action:ADMINISTER_ANTIHISTAMINE_IV:dose` | Difenhidramina IV | 50 mg | WAO_2020, ACAAI_AAAAI_2015 | ⬜ PENDIENTE |
| `action:ADMINISTER_CORTICOSTEROID:dose` | Metilprednisolona IV | 1 mg/kg | WAO_2020, ACAAI_AAAAI_2015 | ⬜ PENDIENTE |

### Tiempos de progresión entre estados

| ID de regla | Descripción | Valor provisional | Fuentes candidatas | Estado |
|---|---|---|---|---|
| `state:INITIAL_PRESENTATION:auto_advance_after_seconds` | Tiempo presentación inicial → Grado I | 30 s | NAP6 | ⬜ PENDIENTE |
| `state:GRADE_I:auto_advance_after_seconds` | Tiempo en Grado I sin tratamiento → Grado II | 90 s | NAP6 | ⬜ PENDIENTE |
| `state:GRADE_II:auto_advance_after_seconds` | Tiempo en Grado II sin tratamiento → Grado III | 180 s | NAP6 | ⬜ PENDIENTE |
| `state:GRADE_III:auto_advance_after_seconds` | Tiempo en Grado III sin tratamiento → Grado IV | 120 s | NAP6 | ⬜ PENDIENTE |
| `state:GRADE_IV:auto_advance_after_seconds` | Tiempo en Grado IV sin RCP → muerte | 180 s | AHA_ACLS_2020 | ⬜ PENDIENTE |

### Deltas fisiológicos (deterioro sin tratamiento)

| ID de regla | Descripción | Valor provisional | Fuentes candidatas | Estado |
|---|---|---|---|---|
| `vitals:GRADE_I:hr_delta_per_second` | Delta FC en Grado I | +0.15 lpm/s | NAP6 | ⬜ PENDIENTE |
| `vitals:GRADE_II:sbp_delta_per_second` | Delta PAS en Grado II | −0.5 mmHg/s | NAP6 | ⬜ PENDIENTE |
| `vitals:GRADE_III:spo2_delta_per_second` | Delta SpO₂ en Grado III | −0.35 %/s | NAP6 | ⬜ PENDIENTE |

---

## Notas para el revisor médico

### Sobre las dosis de epinefrina
- La dosis IM de 0.3 mg es consistente con guías WAO y ACAAI para adultos
  (concentración habitual 1:1000). Verificar si aplica la presentación
  disponible en Argentina (autoinyector vs. ampolla).
- La dosis IV de 0.1 mg es para uso hospitalario con monitoreo continuo.
  Confirmar si la vía y dosis son adecuadas para contexto perioperatorio.

### Sobre los tiempos de progresión
- Los valores son ficticios/estimados para propósitos educativos.
  El NAP6 provee datos poblacionales (mediana de tiempo hasta colapso),
  no una curva de progresión individual. El revisor debe confirmar si
  los tiempos son pedagógicamente razonables y clínicamente plausibles.

### Sobre los deltas fisiológicos
- Los valores numéricos de deterioro por segundo fueron estimados para
  producir una simulación visualmente coherente. No corresponden a
  mediciones publicadas. El revisor debe confirmar si la velocidad de
  deterioro es consistente con la presentación clínica típica.

### Sobre antihistamínicos y corticosteroides
- WAO_2020 advierte que difenhidramina y corticosteroides son tratamientos
  de segunda línea. No deben presentarse al alumno como equivalentes
  a la epinefrina. Verificar que el escenario refleje esta jerarquía.

---

## Registro de validaciones realizadas

*Sin validaciones aún. Las validaciones se registran automáticamente
en la base de datos al ser firmadas por un validador desde el panel `/admin`.*

---

## Historial de cambios de este log

| Fecha | Acción | Autor |
|---|---|---|
| 2026-06-21 | Creación del log con 14 reglas pendientes e identificación de fuentes candidatas | Sistema |
