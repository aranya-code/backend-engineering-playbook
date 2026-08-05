# =============================================================================
# Dockerfile — Hello World Container
# =============================================================================
# This Dockerfile packages a simple Python script into a Docker image.
# It demonstrates the minimal steps required to go from source code to
# a runnable container: choose a base image, set a working directory,
# copy your code in, and define the default command.
# =============================================================================

# ---------------------------------------------------------------------------
# 1. BASE IMAGE
# ---------------------------------------------------------------------------
# Start from the official Python 3.12 "slim" image.
# "slim" is a minimal Debian variant — much smaller than the full image
# (~150 MB vs ~1 GB) while still including pip, setuptools, and a C compiler.
# Always pin a specific version (3.12) instead of using "latest" so your
# builds are reproducible.
FROM python:3.12-slim

# ---------------------------------------------------------------------------
# 2. METADATA
# ---------------------------------------------------------------------------
# LABEL adds key-value metadata to the image. It has no effect on how the
# container runs — it is purely informational and shows up in `docker inspect`.
LABEL maintainer="Backend Engineering Playbook"
LABEL description="A minimal Hello World container for learning Docker basics."

# ---------------------------------------------------------------------------
# 3. WORKING DIRECTORY
# ---------------------------------------------------------------------------
# WORKDIR sets the default directory for all subsequent instructions
# (RUN, CMD, COPY, etc.) and for interactive shells opened with `docker exec`.
# If the directory does not exist, Docker creates it automatically.
WORKDIR /app

# ---------------------------------------------------------------------------
# 4. COPY SOURCE CODE
# ---------------------------------------------------------------------------
# COPY <src> <dest> copies files from the build context (your local machine)
# into the image filesystem. Here we copy everything inside the local "app/"
# folder into the container's /app directory (set by WORKDIR above).
# The "." means "current WORKDIR" — so app/app.py becomes /app/app.py.
COPY app/ .

# ---------------------------------------------------------------------------
# 5. DEFAULT COMMAND
# ---------------------------------------------------------------------------
# CMD defines the command that runs when a container starts.
# The exec form ["executable", "arg1"] is preferred over the shell form
# because it runs the process directly (PID 1) without wrapping it in
# /bin/sh -c, which ensures proper signal handling (e.g., SIGTERM on
# `docker stop` goes straight to the Python process).
CMD ["python", "app.py"]
