# -----------
# "slim" is a minimal Debian variant — much smaller than the full image.
# Using 3.12-slim provides a balance between size and functionality.
# -----------
FROM python:3.12-slim

# -----------
# Metadata about who maintains the image.
# -----------
LABEL maintainer="Backend Engineering Playbook"

# -----------
# Set the working directory inside the container to /app.
# Subsequent instructions (COPY, RUN, CMD) will be run from here.
# -----------
WORKDIR /app

# -----------
# Copy only the requirements file first.
# This leverages Docker's caching mechanism to avoid re-installing dependencies
# unless requirements.txt changes.
# -----------
COPY requirements.txt .

# -----------
# Install Python dependencies.
# --no-cache-dir keeps the image smaller by not saving pip cache.
# -----------
RUN pip install --no-cache-dir -r requirements.txt

# -----------
# Copy the rest of the application code into the working directory.
# -----------
COPY app/ .

# -----------
# Specify the command to run when the container starts.
# Runs the main Flask application.
# -----------
CMD ["python", "app.py"]
