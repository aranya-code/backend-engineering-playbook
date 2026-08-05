from celery import Celery
app=Celery('multi',broker='redis://redis:6379/0')
app.autodiscover_tasks(['celery_worker'])
