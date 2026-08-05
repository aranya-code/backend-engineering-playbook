#!/bin/sh
# Start the application using Gunicorn with Uvicorn workers.
# This setup is recommended for production FastAPI apps.
# The number of workers is configurable via the GUNICORN_WORKERS environment variable (default: 2).
# 'exec' replaces the shell process with gunicorn, so it correctly receives OS signals (like SIGTERM).
exec gunicorn -k uvicorn.workers.UvicornWorker --workers ${GUNICORN_WORKERS:-2} --bind 0.0.0.0:8000 main:app
