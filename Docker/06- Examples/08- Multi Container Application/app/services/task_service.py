"""
Task service module for managing background tasks.
"""
from celery_worker.tasks import long_running_task
def queue_background_task(): 
    # Dispatch task to the Celery worker via message broker
    long_running_task.delay()
