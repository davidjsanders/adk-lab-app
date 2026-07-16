# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Stage 1: Build virtual environment and dependencies
FROM python:3.12.3-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv==0.8.13

COPY pyproject.toml README.md uv.lock* ./
RUN uv sync --frozen --no-dev
RUN uv pip install gunicorn uvicorn

# Stage 2: Final minimal runtime image with non-root user
FROM python:3.12.3-slim AS runner

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY --from=builder /app/.venv /app/.venv
COPY ./app ./app
COPY ./pyproject.toml ./README.md ./

# Ensure non-root appuser owns the application files and home directory
RUN chown -R appuser:appgroup /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HOME=/app

USER appuser

EXPOSE 8080

CMD exec gunicorn -k uvicorn.workers.UvicornWorker --bind "0.0.0.0:${PORT:-8080}" app.fast_api_app:app
