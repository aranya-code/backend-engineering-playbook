# -----------
# BUILDER STAGE
# We use a multi-stage build to keep the final image small and secure.
# This stage installs dependencies into a specific directory (--prefix).
# -----------
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
# Install dependencies into /install to easily copy them to the final image
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -----------
# RUNTIME STAGE
# This is the final image that will run our application.
# It does not include build tools or extra files from the builder stage.
# -----------
FROM python:3.12-slim
# Prevent Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure Python output is logged immediately without buffering
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl for health checks, then clean up apt cache to reduce image size
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# -----------
# SECURITY: Run as non-root user
# Creating a dedicated user and group prevents the app from running as root,
# which is a Docker security best practice.
# -----------
RUN groupadd --system appgroup && useradd --system --gid appgroup --create-home appuser

COPY app/ .
COPY scripts/start.sh /start.sh

# Make the start script executable and transfer ownership of app files to our non-root user
RUN chmod +x /start.sh && chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

EXPOSE 8000
CMD ["/start.sh"]
