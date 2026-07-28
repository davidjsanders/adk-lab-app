# --- Build Stage ---
FROM python:3.12.3-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

# --- Final Runner Stage ---
FROM python:3.12.3-slim AS runner

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1

# Install gunicorn and uvicorn - NOT in requirements.txt
RUN pip install --no-cache-dir gunicorn uvicorn

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8080
CMD exec gunicorn --bind "0.0.0.0:${PORT}" --workers 2 --threads 4 --worker-class uvicorn.workers.UvicornWorker app.fast_api_app:app
