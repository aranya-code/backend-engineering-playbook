#!/bin/sh
exec gunicorn -k uvicorn.workers.UvicornWorker --workers 2 --bind 0.0.0.0:8000 main:app
