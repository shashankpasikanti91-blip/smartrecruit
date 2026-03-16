"""
Gunicorn configuration for SRP SmartRecruit v3.2
Production WSGI/ASGI server config
Usage: gunicorn -c gunicorn.conf.py app.main:app
"""
import os
import multiprocessing

# Server socket
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# Worker processes
# Recommended: (2 * CPU cores) + 1
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"  # ASGI worker for FastAPI
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
loglevel = os.getenv("LOG_LEVEL", "info").lower()
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")  # stdout
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "srp_smartrecruit"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Graceful restart
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 50
