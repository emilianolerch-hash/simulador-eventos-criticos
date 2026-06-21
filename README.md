# Simulador de Eventos Críticos

Herramienta educativa para entrenamiento en anestesiología. Primer escenario: anafilaxia perioperatoria en adulto.

> **Aviso:** Esta aplicación es solo para fines educativos. NO debe usarse con pacientes reales ni como referencia clínica.

---

## Ejecución local (sin Docker)

### Requisitos

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 corriendo en `localhost:5432`

### Backend

```bash
cd backend

# Primera vez: crear la DB y correr migraciones
createdb simulador_db  # si no existe
python -m alembic upgrade head

# Configurar variables (copiar y editar)
cp .env.example .env

# Iniciar
uvicorn app.main:app --reload
# → http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Tests

```bash
# Desde la raíz del proyecto
python3 -m pytest tests/ -v

# Test individual
python3 -m pytest tests/test_state_machine.py::test_initial_state -v
```

---

## Ejecución con Docker Compose

### Requisitos

- Docker Engine 24+
- Docker Compose v2

### Primera vez

```bash
# 1. Crear el archivo de entorno
cp .env.docker.example .env.docker

# 2. Generar una clave JWT segura y pegarla en .env.docker
openssl rand -hex 32

# 3. Levantar todos los servicios
docker compose --env-file .env.docker up --build
```

Los servicios levantan en orden: `db` → `backend` (con migraciones automáticas) → `frontend`.

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Docs interactivas: http://localhost:8000/docs

### Comandos útiles

```bash
# Ver logs del backend
docker compose logs -f backend

# Correr solo la DB (útil para desarrollo local)
docker compose up db

# Detener y borrar volúmenes (borra la DB)
docker compose down -v

# Rebuild de un servicio específico
docker compose up --build backend
```

---

## Variables de entorno

| Variable | Obligatoria en prod | Default | Descripción |
|---|---|---|---|
| `JWT_SECRET_KEY` | Sí | — | Secreto JWT. Generá con `openssl rand -hex 32` |
| `ENV` | — | `development` | `production` obliga `JWT_SECRET_KEY` |
| `DATABASE_URL` | — | `postgresql://postgres@localhost:5432/simulador_db` | Conexión PostgreSQL |
| `CORS_ORIGINS` | — | `http://localhost:3000` | Origins permitidos (separados por coma) |
| `NEXT_PUBLIC_API_URL` | — | `http://localhost:8000` | URL del backend visible desde el browser |
| `RATE_LIMIT_LOGIN` | — | `10` | Requests/min por IP en `/auth/login` |
| `RATE_LIMIT_REGISTER` | — | `5` | Requests/min por IP en `/auth/register` |

---

## Estructura del proyecto

```
scenarios/          ← YAML de escenarios clínicos (fuente de verdad)
clinical/           ← Fuentes médicas y log de validación
backend/
  app/
    engine/         ← Motor FSM determinístico
    models/         ← Schemas Pydantic y ORM SQLAlchemy
    auth/           ← JWT, dependencias de autenticación
    middleware/     ← Rate limiting
    api/            ← Panel de validación clínica
  alembic/          ← Migraciones de base de datos
frontend/
  src/
    app/            ← Páginas Next.js
    components/     ← Componentes de simulación
    hooks/          ← useSimulation, useAuth
    lib/            ← API client, tipos TypeScript
tests/              ← pytest (motor + integración API)
```

---

## Roles de usuario

| Rol | Permisos |
|---|---|
| `anesthesiologist` | Crear y ejecutar simulaciones |
| `validator` | Todo lo anterior + panel de validación clínica (`/admin`) |

---

## Regla clínica

Ningún valor clínico (dosis, umbrales, tiempos) puede ser inventado. Todo valor en los YAML de escenarios debe tener `validation_status` explícito. Ver `CLAUDE.md` para reglas de desarrollo.
