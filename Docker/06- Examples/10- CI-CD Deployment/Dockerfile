# -----------
# "slim" is a minimal Debian variant — much smaller than the full image.
# -----------
FROM python:3.12-slim

# -----------
# Prevent Python from writing .pyc files to disk
# -----------
ENV PYTHONDONTWRITEBYTECODE=1

# -----------
# Prevent Python from buffering stdout/stderr
# -----------
ENV PYTHONUNBUFFERED=1

# -----------
# Set the working directory inside the container
# -----------
WORKDIR /app

# -----------
# Install system dependencies (curl for healthcheck) and clean up apt cache to reduce image size
# -----------
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# -----------
# Copy requirements first to leverage Docker layer caching
# -----------
COPY requirements.txt .

# -----------
# Install Python dependencies without caching to keep image size small
# -----------
RUN pip install --no-cache-dir -r requirements.txt

# -----------
# Copy the application code into the container
# -----------
COPY app/ .

# -----------
# Copy the startup script to the root directory
# -----------
COPY scripts/start.sh /start.sh

# -----------
# Make the startup script executable
# -----------
RUN chmod +x /start.sh

# -----------
# Document that the container listens on port 8000
# -----------
EXPOSE 8000

# -----------
# Command to run when the container starts
# -----------
CMD ["/start.sh"]
