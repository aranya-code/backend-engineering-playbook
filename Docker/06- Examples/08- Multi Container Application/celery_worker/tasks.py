import time
from .celery_app import app
@app.task
def long_running_task():
 print('Task started'); time.sleep(5); print('Task completed')
