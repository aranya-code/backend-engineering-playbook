"""
Settings module.
Loads configuration from environment variables with sensible defaults.
"""
import os

# Application name, defaults to "Production Deployment Demo"
APP_NAME=os.getenv("APP_NAME","Production Deployment Demo")
# Current environment (e.g., development, production)
ENVIRONMENT=os.getenv("ENVIRONMENT","production")
# Application version
VERSION=os.getenv("APP_VERSION","1.0.0")
