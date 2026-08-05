#!/bin/sh
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done

exec gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
