#!/bin/sh
exec celery -A config worker --loglevel=info
