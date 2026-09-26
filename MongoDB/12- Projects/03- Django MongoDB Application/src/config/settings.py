"""Django settings for the MongoDB application."""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


# Security
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-development-only-change-me",
)

DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() in {
    "1",
    "true",
    "yes",
}

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]


# Application definition
INSTALLED_APPS = [
    "django.contrib.contenttypes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Django does not natively provide a MongoDB ORM backend.
# MongoDB access is handled separately through PyMongo in the application
# repository/service layer. SQLite is used only for Django framework-level
# database requirements in this standalone MongoDB application.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
}


# Internationalization
LANGUAGE_CODE = "en-us"

TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")

USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


# MongoDB configuration
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "django_mongodb_app",
)

MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")
)

MONGODB_CONNECT_TIMEOUT_MS = int(
    os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000")
)

MONGODB_SOCKET_TIMEOUT_MS = int(
    os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "10000")
)

MONGODB_MAX_POOL_SIZE = int(
    os.getenv("MONGODB_MAX_POOL_SIZE", "100")
)

MONGODB_MIN_POOL_SIZE = int(
    os.getenv("MONGODB_MIN_POOL_SIZE", "0")
)


# Production security settings
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

"""Django settings for the MongoDB application."""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


# Security
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-development-only-change-me",
)

DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() in {
    "1",
    "true",
    "yes",
}

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]


# Application definition
INSTALLED_APPS = [
    "django.contrib.contenttypes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Django does not natively provide a MongoDB ORM backend.
# MongoDB access is handled separately through PyMongo in the application
# repository/service layer. SQLite is used only for Django framework-level
# database requirements in this standalone MongoDB application.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
}


# Internationalization
LANGUAGE_CODE = "en-us"

TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")

USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


# MongoDB configuration
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017",
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "django_mongodb_app",
)

MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")
)

MONGODB_CONNECT_TIMEOUT_MS = int(
    os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000")
)

MONGODB_SOCKET_TIMEOUT_MS = int(
    os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "10000")
)

MONGODB_MAX_POOL_SIZE = int(
    os.getenv("MONGODB_MAX_POOL_SIZE", "100")
)

MONGODB_MIN_POOL_SIZE = int(
    os.getenv("MONGODB_MIN_POOL_SIZE", "0")
)


# Production security settings
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True