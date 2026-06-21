FROM python:3.12-slim AS base

WORKDIR /app

# System deps for psycopg2-binary + curl (requerido por el healthcheck de docker-compose)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Build context es la raíz del repo
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY scenarios/ /scenarios/

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
