import os
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
SECRET_KEY="demo"
DEBUG=True
ALLOWED_HOSTS=["*"]
INSTALLED_APPS=["django.contrib.staticfiles","home"]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware"]
ROOT_URLCONF="config.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[],"APP_DIRS":True,"OPTIONS":{}}]
WSGI_APPLICATION="config.wsgi.application"
DATABASES={"default":{"ENGINE":"django.db.backends.postgresql","NAME":os.getenv("POSTGRES_DB"),"USER":os.getenv("POSTGRES_USER"),"PASSWORD":os.getenv("POSTGRES_PASSWORD"),"HOST":os.getenv("POSTGRES_HOST"),"PORT":os.getenv("POSTGRES_PORT")}}
STATIC_URL="static/"
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
