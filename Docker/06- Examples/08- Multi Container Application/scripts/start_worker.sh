#!/bin/sh
exec celery -A celery_worker.celery_app worker --loglevel=info
