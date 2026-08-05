"""
Hello World Container — app.py
================================
A minimal Python script that prints system information to the console.
This is the application that gets packaged into a Docker image.

Purpose:
    - Demonstrate that the container runs an isolated environment
      (its own hostname, OS, Python version — different from your host).
    - Show how environment variables (APP_NAME) pass from `docker run -e`
      into the running container via os.getenv().

Usage:
    Locally  : python app.py
    In Docker: docker run hello-docker
"""

import os          # Access environment variables set via `docker run -e`
import platform    # Retrieve OS, Python version, and hostname info
from datetime import datetime  # Get the current date and time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# os.getenv(key, default) reads an environment variable.
# If APP_NAME is not set (i.e., you ran `docker run hello-docker` without -e),
# it falls back to the default value "Hello Docker".
#
# To override:  docker run -e APP_NAME="My App" hello-docker
app_name = os.getenv("APP_NAME", "Hello Docker")

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
# Print a formatted banner with system details.
# Inside a Docker container, these values will differ from your host machine:
#   - Hostname  → the container's short ID (e.g., "f92a34493393")
#   - OS        → "Linux" (because the container runs a Linux kernel)
#   - Python    → the version baked into the base image (3.12.x)
print("=" * 60)
print(f"  {app_name}")
print("=" * 60)
print(f"  Current Time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Operating System  : {platform.system()} {platform.release()}")
print(f"  Python Version    : {platform.python_version()}")
print(f"  Hostname          : {platform.node()}")
print("-" * 60)
print("  Congratulations!")
print("  Your first Docker container is running successfully.")
print("=" * 60)
