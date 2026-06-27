# Stage 1: Builder
FROM python:3.14-alpine AS builder

COPY --from=ghcr.io/astral-sh/uv:0.7.15 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

# No build-base/musl-dev/postgresql-dev needed —
# psycopg2-binary ships a prebuilt musl wheel with libpq bundled in,
# and nothing else in this project compiles C extensions.

# Install dependencies first (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

# Strip test suites from installed packages — never needed at runtime
# Excludes django/test because simplejwt imports django.test.signals at runtime
RUN find /app/.venv/lib -type d \( -name "tests" -o -name "test" \) \
    ! -path "*/django/test" \
    | xargs rm -rf

# Strip .dist-info metadata and compiled files
RUN find /app/.venv -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type f -name "*.pyc" -delete && \
    find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Stage 2: Production
FROM python:3.14-alpine

# No apk add needed at all — psycopg2-binary's bundled libpq covers DB connectivity.
# If you later add Pillow or anything brotli-related, add those runtime libs back here.

# Create non-root user
RUN adduser -D -s /bin/sh appuser && \
    mkdir -p /app/media /app/staticfiles /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 770 /app/logs

WORKDIR /app

# Copy venv from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

RUN sed -i 's/\r$//' /app/entrypoint.prod.sh && \
    chmod +x /app/entrypoint.prod.sh

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000

VOLUME ["/app/media", "/app/logs"]

CMD ["/app/entrypoint.prod.sh"]