# --- Build Stage ---
FROM python:3.12.3-slim AS builder

WORKDIR /app

# Copy dependency requirements
COPY requirements.txt .

# Install dependencies globally or into a wheelhouse
RUN pip install --no-cache-dir -r requirements.txt

# --- Final Runner Stage ---
FROM python:3.12.3-slim AS runner

WORKDIR /app

# Install gunicorn in runner stage - NOT in requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy installed libraries from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Setup non-root execution for security hardening
RUN useradd -m -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

# Honor dynamic port binding specified in Cloud Run $PORT
ENV PORT=8081
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app"]
