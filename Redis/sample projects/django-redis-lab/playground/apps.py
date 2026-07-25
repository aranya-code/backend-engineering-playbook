"""Playground app configuration."""

from django.apps import AppConfig


class PlaygroundConfig(AppConfig):
    """Configuration for the playground app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "playground"
    verbose_name = "Redis Playground"
