"""Celery configuration file."""

from app.config import settings

# Broker settings
broker_url = settings.celery_broker_url
result_backend = settings.celery_result_backend

# Task settings
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

# Task execution settings
task_track_started = True
task_time_limit = 300
task_soft_time_limit = 240

# Result backend settings
result_expires = 3600

# Worker settings
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000

# Task routes (optional)
task_routes = {
    'send_welcome_email': {'queue': 'emails'},
    'send_order_confirmation': {'queue': 'emails'},
    'process_payment': {'queue': 'payments'},
    'generate_report': {'queue': 'reports'},
}

# Beat schedule (optional - for periodic tasks)
beat_schedule = {
    'cleanup-old-carts': {
        'task': 'cleanup_old_carts',
        'schedule': 3600.0,  # Every hour
    },
}
