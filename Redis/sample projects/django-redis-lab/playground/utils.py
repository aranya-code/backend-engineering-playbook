"""
Utility functions used across the playground app.
"""

from __future__ import annotations

import random
import string


def generate_otp(length: int = 6) -> str:
    """
    Generate a random numeric OTP of the given length.

    Args:
        length: Number of digits (default: 6).

    Returns:
        A string of random digits (e.g., "482917").
    """
    return "".join(random.choices(string.digits, k=length))


def get_client_ip(request) -> str:
    """
    Extract the client IP address from a Django request.

    Checks X-Forwarded-For header first (for requests behind a proxy),
    then falls back to REMOTE_ADDR.

    Args:
        request: Django HttpRequest object.

    Returns:
        Client IP address as a string.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # X-Forwarded-For contains a comma-separated list; first is the client
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "127.0.0.1")
