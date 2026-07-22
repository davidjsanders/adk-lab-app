# Multi-stage Dockerfile for router-ops-agent adhering to Google Cloud Run standards

# Stage 1: Build & Dependencies
FROM python:3.12.3-slim AS builder

RUN pip install --no-cache-dir uv==0.8.13

WORKDIR /app

COPY pyproject.toml README.md uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY agent_engine ./agent_engine
COPY run_a2a.py ./
RUN uv sync --frozen --no-dev
RUN uv pip install gunicorn "uvicorn[standard]"
RUN find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Stage 2: Final Runtime Image
FROM python:3.12.3-slim AS runner

WORKDIR /app

# Create non-root user for security compliance
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY --chown=appuser:appgroup --from=builder /app /app

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV HOME=/app

USER appuser

EXPOSE 8080

CMD ["sh", "-c", "exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT} app.fast_api_app:app"]
