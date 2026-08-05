import os
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
SECRET_KEY="replace-me"
DEBUG=True
ALLOWED_HOSTS=["*"]
INSTALLED_APPS=["django.contrib.staticfiles","home"]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware"]
ROOT_URLCONF="config.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[],"APP_DIRS":True,"OPTIONS":{}}]
WSGI_APPLICATION="config.wsgi.application"
STATIC_URL="static/"
STATIC_ROOT=BASE_DIR/"staticfiles"
CELERY_BROKER_URL=os.getenv("CELERY_BROKER","redis://redis:6379/0")
