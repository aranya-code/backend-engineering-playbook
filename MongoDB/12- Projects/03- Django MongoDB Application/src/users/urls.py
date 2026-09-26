"""URL configuration for the users application."""

from __future__ import annotations

from django.urls import path

from . import views


app_name = "users"

urlpatterns = [
    path("", views.user_list, name="user-list"),
    path("<str:user_id>/", views.user_detail, name="user-detail"),
]

"""URL configuration for the users application."""

from __future__ import annotations

from django.urls import path

from . import views


app_name = "users"

urlpatterns = [
    path("", views.user_list, name="user-list"),
    path("<str:user_id>/", views.user_detail, name="user-detail"),
]