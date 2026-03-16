# SRP SmartRecruit v3.2 — Production Dockerfile
# Multi-stage build for minimal image size
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a temp layer
COPY requirements.production.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.production.txt

# ──────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Security: run as non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && rm -rf /var/lib/apt/lists/*

# Copy application code (no .env, no .git, no __pycache__)
COPY app/           ./app/
COPY templates/     ./templates/
COPY static/        ./static/
COPY system_prompts.txt ./system_prompts.txt
# Backward-compat symlink so old relative path still works
RUN ln -s /app/system_prompts.txt "/app/System prompts ALL.txt"

# Create writable directories
RUN mkdir -p uploads/resumes logs && \
    chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Start with gunicorn + uvicorn worker for production
# Falls back to uvicorn if gunicorn not installed
CMD ["python", "-m", "gunicorn", \
     "-c", "gunicorn.conf.py", \
     "--bind", "0.0.0.0:8000", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app.main:app"]
