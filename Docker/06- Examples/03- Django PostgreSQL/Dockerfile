# -----------
# WHAT: Use the official Python 3.12 slim image.
# WHY: "slim" is a minimal Debian variant — much smaller than the full image but contains necessary tools.
# -----------
FROM python:3.12-slim

# -----------
# WHAT: Prevent Python from writing .pyc files to disk.
# WHY: Reduces container size and avoids permission issues with compiled bytecode.
# -----------
ENV PYTHONDONTWRITEBYTECODE=1

# -----------
# WHAT: Prevent Python from buffering standard output and error.
# WHY: Ensures logs are displayed in the terminal immediately, useful for Docker logs.
# -----------
ENV PYTHONUNBUFFERED=1

# -----------
# WHAT: Set the working directory to /app.
# WHY: All subsequent commands will be run in this directory, keeping the container organized.
# -----------
WORKDIR /app

# -----------
# WHAT: Install system dependencies.
# WHY: gcc and libpq-dev are needed to compile the psycopg database adapter. netcat-openbsd is for the wait_for_db script.
# -----------
RUN apt-get update && apt-get install -y gcc libpq-dev netcat-openbsd && rm -rf /var/lib/apt/lists/*

# -----------
# WHAT: Copy the requirements file into the container.
# WHY: Doing this before copying the rest of the application code allows Docker to cache the pip install step.
# -----------
COPY requirements.txt .

# -----------
# WHAT: Install Python dependencies.
# WHY: --no-cache-dir keeps the image smaller by not saving the downloaded packages.
# -----------
RUN pip install --no-cache-dir -r requirements.txt

# -----------
# WHAT: Copy the Django application code.
# WHY: Moves your source code into the container's working directory.
# -----------
COPY app/ .

# -----------
# WHAT: Copy the wait script.
# WHY: Needed to wait for the database container to be ready before starting Django.
# -----------
COPY scripts/wait_for_db.sh /wait_for_db.sh

# -----------
# WHAT: Make the wait script executable.
# WHY: Ensures the script can be run during container startup.
# -----------
RUN chmod +x /wait_for_db.sh

# -----------
# WHAT: Expose port 8000.
# WHY: Documents that the container will listen on this port (though mapping is still needed in compose).
# -----------
EXPOSE 8000

# -----------
# WHAT: Define the default command to run when the container starts.
# WHY: Executes the wait script, which then starts the Django server.
# -----------
CMD ["/wait_for_db.sh"]
