# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 2: Build Python dependencies
FROM python:3.12-slim AS backend-builder

WORKDIR /build

RUN pip install --upgrade pip
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir \
        fastapi>=0.115 \
        "uvicorn[standard]>=0.30" \
        "sqlalchemy[asyncio]>=2.0" \
        "aiosqlite>=0.20" \
        "alembic>=1.13" \
        "pydantic>=2.0" \
        "pydantic-settings>=2.0" \
        "anthropic>=0.40" \
        "jinja2>=3.1" \
        "rapidfuzz>=3.0" \
        "python-multipart>=0.0.9"

# Stage 3: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

COPY backend/app/ ./app/
COPY backend/alembic/ ./alembic/
COPY backend/alembic.ini .

COPY --from=frontend-builder /app/dist ./static

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
