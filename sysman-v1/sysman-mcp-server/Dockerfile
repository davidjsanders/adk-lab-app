# --- Build Stage ---
FROM python:3.12.3-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# --- Final Runner Stage ---
FROM python:3.12.3-slim AS runner

WORKDIR /app

# Install gunicorn and uvicorn - NOT in requirements.txt
RUN pip install --no-cache-dir gunicorn uvicorn

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN useradd -m -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8002
CMD exec gunicorn --bind "0.0.0.0:${PORT}" --workers 2 --threads 4 --worker-class uvicorn.workers.UvicornWorker server:app
