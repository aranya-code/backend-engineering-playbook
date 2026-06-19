# Use an official Python runtime as the base image.
# The 'slim' variant is preferred over 'alpine' for Python to avoid C-extension build 
# issues, while still remaining much smaller than the standard image.
FROM python:3.12-slim

# Set environment variables:
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk.
# PYTHONUNBUFFERED: Ensures stdout/stderr streams are sent straight to the terminal 
#                   (crucial for real-time Docker logging).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a dedicated, non-root user to run the application.
# Running applications as root inside a container is a major security risk.
RUN addgroup --system django && adduser --system --ingroup django django

# Set the working directory inside the container.
WORKDIR /app

# Copy ONLY the requirements file first.
# This leverages Docker's layer caching. If your application code changes but your 
# dependencies don't, Docker will use the cached layer for this step, saving build time.
COPY requirements-docker.txt .

# Upgrade pip and install dependencies.
# --no-cache-dir ensures pip doesn't save the downloaded packages, keeping the image small.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-docker.txt

# Copy the rest of the application code into the container.
# IMPORTANT: Ensure you have a .dockerignore file to prevent copying local virtual 
# environments, .git folders, and sensitive local .env files.
COPY . .

# Change ownership of the /app directory to the non-root user.
# If collectstatic creates new files, the django user needs permission to write here.
RUN chown -R django:django /app

# Switch to the non-root user for all subsequent commands.
USER django

# Expose the port the application will listen on.
# This acts as documentation; you still need to publish the port when running the container.
EXPOSE 8000

# Define the command to run the application.
# NOTE: Using 'runserver' is strictly for development. 
# For a production environment, you should use a WSGI server like Gunicorn.
# e.g., CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
CMD sh -c "python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"