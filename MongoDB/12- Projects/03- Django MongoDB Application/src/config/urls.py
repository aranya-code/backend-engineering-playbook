"""URL configuration for the Django MongoDB application."""

from __future__ import annotations

from django.urls import path

from app.views import health_check


urlpatterns = [
    path("health/", health_check, name="health-check"),
]

"""URL configuration for the Django MongoDB application."""

from __future__ import annotations

from django.urls import path

from app.views import health_check


urlpatterns = [
    path("health/", health_check, name="health-check"),
]