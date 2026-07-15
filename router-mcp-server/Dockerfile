# Stage 1: Build & Dependencies Stage
FROM python:3.12.3-slim AS builder

WORKDIR /app

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, reliable package resolution & installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/uv

# Optimize layer caching: Copy project specification files first
COPY pyproject.toml requirements.txt* ./

# Create virtualenv with uv and install dependencies + gunicorn & uvicorn
RUN /uv/bin/uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN PIP_EXTRA_INDEX_URL="https://pypi.org/simple" /uv/bin/uv pip install --no-cache-dir -r requirements.txt gunicorn uvicorn --python /opt/venv


# Stage 2: Minimal Production Runtime Stage
FROM python:3.12.3-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security adherence
RUN useradd -m -u 1000 appuser

# Copy virtualenv and application source directly owned by appuser
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
COPY --chown=appuser:appuser . .

USER appuser

# Expose dynamic PORT variable (defaults to 8080)
EXPOSE 8080

# Serve via Gunicorn using Uvicorn worker bound to $PORT
CMD exec gunicorn --bind "0.0.0.0:${PORT:-8080}" --workers 2 --threads 8 --worker-class uvicorn.workers.UvicornWorker server:app
