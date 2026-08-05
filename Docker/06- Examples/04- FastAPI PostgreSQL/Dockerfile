# -----------
# We use the slim version of Python to keep the image small
# while still providing a full Debian environment
# -----------
FROM python:3.12-slim

# -----------
# Prevent Python from writing .pyc files to disk
# -----------
ENV PYTHONDONTWRITEBYTECODE=1

# -----------
# Prevent Python from buffering stdout and stderr
# -----------
ENV PYTHONUNBUFFERED=1

# -----------
# Set the working directory inside the container
# -----------
WORKDIR /app

# -----------
# Install system dependencies required for PostgreSQL (libpq-dev)
# gcc is needed to compile some Python packages
# -----------
RUN apt-get update && apt-get install -y gcc libpq-dev curl netcat-openbsd && rm -rf /var/lib/apt/lists/*

# -----------
# Copy just the requirements first to leverage Docker cache
# If requirements.txt doesn't change, this step is skipped
# -----------
COPY requirements.txt .

# -----------
# Install Python dependencies
# -----------
RUN pip install --no-cache-dir -r requirements.txt

# -----------
# Copy the application source code
# -----------
COPY app/ .

# -----------
# Copy the database wait script
# -----------
COPY scripts/wait_for_db.sh /wait_for_db.sh
RUN chmod +x /wait_for_db.sh

# -----------
# Expose the port the app runs on
# -----------
EXPOSE 8000

# -----------
# Start the wait script which eventually starts the app
# -----------
CMD ["/wait_for_db.sh"]
