# -----------
# BASE IMAGE
# -----------
# "slim" is a minimal Debian variant — much smaller than the full image.
FROM python:3.12-slim

# -----------
# ENVIRONMENT VARIABLES
# -----------
# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure output is sent directly to terminal (useful for Docker logs)
ENV PYTHONUNBUFFERED=1

# -----------
# WORKDIR
# -----------
# Set the working directory inside the container
WORKDIR /app

# -----------
# SYSTEM DEPENDENCIES
# -----------
# Install curl for healthchecks and clean up apt cache to keep image small
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# -----------
# PYTHON DEPENDENCIES
# -----------
# Copy requirements first to leverage Docker cache for pip install
COPY requirements.txt .
# Install dependencies without caching to keep image small
RUN pip install --no-cache-dir -r requirements.txt

# -----------
# APPLICATION CODE
# -----------
# Copy application files
COPY app/ .
# Copy startup script and make it executable
COPY scripts/start.sh /start.sh
RUN chmod +x /start.sh

# -----------
# PORT & COMMAND
# -----------
# Expose the port the app runs on
EXPOSE 8000

# Run the startup script when container starts
CMD ["/start.sh"]
