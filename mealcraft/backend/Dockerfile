# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --upgrade pip
COPY pyproject.toml .
RUN pip install --no-cache-dir build && \
    pip install --no-cache-dir \
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

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create data directory for SQLite
RUN mkdir -p /app/data

EXPOSE 8000

# Run migrations then start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
