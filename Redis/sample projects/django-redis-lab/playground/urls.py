"""
URL routing for the playground app.
"""

from django.urls import path

from . import views

urlpatterns = [
    # Products
    path("products/", views.product_list, name="product-list"),
    path("products/<int:product_id>/", views.product_detail, name="product-detail"),

    # Shopping Cart
    path("cart/", views.cart, name="cart"),

    # OTP & Login
    path("otp/", views.otp_request, name="otp-request"),
    path("login/", views.login, name="login"),

    # Leaderboard
    path("leaderboard/", views.leaderboard, name="leaderboard"),

    # Pub/Sub
    path("publish/", views.publish, name="publish"),

    # Streams
    path("stream/", views.stream, name="stream"),

    # Cache Management
    path("cache/clear/", views.cache_clear, name="cache-clear"),

    # Analytics
    path("analytics/", views.analytics, name="analytics"),
]
