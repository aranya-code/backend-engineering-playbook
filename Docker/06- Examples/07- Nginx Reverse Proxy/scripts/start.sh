#!/bin/sh
# Use exec to replace the shell with the gunicorn process (better signal handling)
# Run Gunicorn as the process manager, using Uvicorn workers for ASGI support
# Bind to all interfaces (0.0.0.0) on port 8000
exec gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
