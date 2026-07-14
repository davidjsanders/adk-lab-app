# Multi-stage Dockerfile for Router Fleet Operations Dashboard using uv
# Optimized for Cloud Run deployment with non-root security execution.

# --- Stage 1: Build Dependencies ---
FROM python:3.12.3-slim AS builder

# Install uv binary from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Create virtual environment and install dependencies using uv
RUN uv venv /opt/venv
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt --python /opt/venv

# --- Stage 2: Final Runtime Container ---
FROM python:3.12.3-slim AS runner

# Install uv binary in final stage
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install google-cloud-cli for runtime Cloud Run service management
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /etc/apt/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update && apt-get install -y --no-install-recommends google-cloud-cli \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user and home directory
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser
ENV HOME=/home/appuser

WORKDIR /app

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install gunicorn directly in final stage using uv (NOT in requirements.txt per rules)
RUN uv pip install --no-cache gunicorn --python /opt/venv

# Copy application source code & configurations
COPY app.py .
COPY routers.json .
COPY classes/ classes/
COPY helpers/ helpers/
COPY templates/ templates/
COPY static/ static/

# Ensure proper non-root file permissions
RUN chown -R appuser:appuser /app /home/appuser

# Environment defaults
ENV PORT=8090
ENV PYTHONUNBUFFERED=1

USER appuser

# Expose container port (default 8090)
EXPOSE 8090

# Serve application using gunicorn reading dynamic $PORT variable
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 16 --timeout 0 app:app
