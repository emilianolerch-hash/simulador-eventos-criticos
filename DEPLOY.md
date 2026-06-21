# Deploy en Railway

## Prerequisitos

- Cuenta en [railway.app](https://railway.app)
- CLI de Railway instalada: `npm install -g @railway/cli`
- Repo pusheado a GitHub

---

## Paso 1 — Crear proyecto y base de datos

1. Entrá a [railway.app/new](https://railway.app/new) → **New Project**
2. Elegí **Empty Project**
3. Dentro del proyecto → **New** → **Database** → **PostgreSQL**
4. Railway crea la DB y expone `${{Postgres.DATABASE_URL}}` automáticamente

---

## Paso 2 — Servicio Backend

1. **New** → **GitHub Repo** → seleccioná este repo
2. Railway detecta el `railway.toml` en la raíz y usa `backend/Dockerfile`
3. En la pestaña **Variables** del servicio, agregá:

```
DATABASE_URL        = ${{Postgres.DATABASE_URL}}
JWT_SECRET_KEY      = <generá con: openssl rand -hex 32>
ADMIN_SECRET        = <generá con: openssl rand -hex 32>
ENV                 = production
JWT_ALGORITHM       = HS256
JWT_EXPIRE_MINUTES  = 480
CORS_ORIGINS        = https://FRONTEND_URL  ← completar en Paso 4
RATE_LIMIT_LOGIN    = 10
RATE_LIMIT_REGISTER = 5
```

4. En **Settings** → **Networking** → **Generate Domain** → copiá la URL (ej. `backend-xxxx.up.railway.app`)
5. Hacé **Deploy** — Railway corre `alembic upgrade head` y levanta uvicorn
6. Verificá: `curl https://backend-xxxx.up.railway.app/health` → debe retornar `{"status":"ok"}`

---

## Paso 3 — Servicio Frontend

1. **New** → **GitHub Repo** → mismo repo
2. En **Settings** → **Root Directory** → escribí `frontend`
   Railway detecta `frontend/railway.toml` y usa el `Dockerfile` de esa carpeta
3. En la pestaña **Variables** del servicio, agregá:

```
NEXT_PUBLIC_API_URL  = https://backend-xxxx.up.railway.app  ← URL del Paso 2
NEXT_BUILD_STANDALONE = 1
```

4. En **Settings** → **Networking** → **Generate Domain** → copiá la URL del frontend
5. Hacé **Deploy**

---

## Paso 4 — Conectar frontend y backend (CORS)

Volvé al servicio **Backend** → **Variables** y actualizá:

```
CORS_ORIGINS = https://frontend-xxxx.up.railway.app
```

Railway redeploya el backend automáticamente.

---

## Paso 5 — Crear el primer usuario validador

Una vez que ambos servicios están up, registrá un usuario y promovelo:

```bash
# 1. Registrar usuario
curl -X POST https://backend-xxxx.up.railway.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "tu@email.com", "password": "tu-pass", "full_name": "Tu Nombre"}'

# 2. Promover a validator
curl -X POST https://backend-xxxx.up.railway.app/auth/promote \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: <tu-ADMIN_SECRET>" \
  -d '{"email": "tu@email.com"}'
```

Con ese usuario podés entrar a `https://frontend-xxxx.up.railway.app/admin` y validar las reglas clínicas.

---

## Variables de entorno — resumen

| Variable | Servicio | Valor |
|---|---|---|
| `DATABASE_URL` | backend | `${{Postgres.DATABASE_URL}}` |
| `JWT_SECRET_KEY` | backend | `openssl rand -hex 32` |
| `ADMIN_SECRET` | backend | `openssl rand -hex 32` |
| `ENV` | backend | `production` |
| `CORS_ORIGINS` | backend | URL del frontend |
| `NEXT_PUBLIC_API_URL` | frontend | URL del backend |
| `NEXT_BUILD_STANDALONE` | frontend | `1` |

---

## Deploy local con Docker Compose

```bash
cp backend/.env.example backend/.env
# Editá backend/.env con tus valores

# Generar secrets
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> backend/.env
echo "ADMIN_SECRET=$(openssl rand -hex 32)" >> backend/.env

docker compose up --build
```

Frontend: http://localhost:3000  
Backend: http://localhost:8000  
Docs API: http://localhost:8000/docs
