"""
Celery application configuration.

This module configures Celery to use Redis as the message broker.
It auto-discovers tasks from all installed Django apps.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Load Celery settings from Django settings, using the CELERY_ prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in all installed apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:
    """Debug task that prints the current request info."""
    print(f"Request: {self.request!r}")
