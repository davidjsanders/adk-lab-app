# Multi-stage Dockerfile for Router Emulator using uv
# Optimized for Cloud Run deployment with non-root security execution.

# --- Stage 1: Build Dependencies ---
FROM python:3.12.3-slim AS builder

# Install uv binary from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Create virtual environment and install dependencies using uv
RUN uv venv /opt/venv
COPY pyproject.toml requirements.txt* ./
RUN uv pip install --no-cache -r requirements.txt --python /opt/venv

# --- Stage 2: Final Runtime Container ---
FROM python:3.12.3-slim AS runner

# Install uv binary in final stage
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dejavu fonts to enable high-quality rendering of PNG cards
RUN apt-get update && \
    apt-get install -y --no-install-recommends fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

# Create non-root system user and home directory
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser
ENV HOME=/home/appuser

WORKDIR /app

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install gunicorn directly in final stage using uv (NOT in requirements.txt per rules)
RUN uv pip install --no-cache gunicorn --python /opt/venv

# Copy application source code
COPY . .

# Ensure proper non-root file permissions for app and home directory
RUN chown -R appuser:appuser /app /home/appuser

# Environment defaults
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

USER appuser

# Expose container port (default 8080)
EXPOSE 8080

# Serve application using gunicorn dynamically reading $PORT variable
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 16 --timeout 0 app:app
