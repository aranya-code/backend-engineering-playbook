import time
from celery import shared_task
@shared_task
def long_running_task():
    print("Background task started...")
    time.sleep(5)
    print("Task completed.")
