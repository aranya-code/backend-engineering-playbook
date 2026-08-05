# -----------
# "slim" is a minimal Debian variant — much smaller than the full image.
# -----------
FROM python:3.12-slim

# -----------
# Environment variables to keep python from generating .pyc files
# and to enable unbuffered output.
# -----------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -----------
# Set the working directory for subsequent instructions.
# -----------
WORKDIR /app

# -----------
# Install system dependencies. Update, install, and clean up in one step to minimize image size.
# -----------
RUN apt-get update && apt-get install -y curl gcc && rm -rf /var/lib/apt/lists/*

# -----------
# Copy just the requirements file first to leverage Docker layer caching.
# -----------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------
# Copy application and script files.
# -----------
COPY app/ ./app
COPY celery_worker/ ./celery_worker
COPY scripts/ ./scripts
RUN chmod +x ./scripts/*.sh

# -----------
# Ensure the working directory is set for CMD.
# -----------
WORKDIR /app
EXPOSE 8000

# -----------
# Default command to run when starting the container.
# -----------
CMD ["sh","../scripts/start_api.sh"]
