"""
Application settings configuration.

Loads environment variables to configure the application behavior.
Provides default values if environment variables are not set.
"""
import os

# The name of the application
APP_NAME=os.getenv("APP_NAME","CI/CD Deployment Demo")

# The environment the application is running in (e.g., development, production)
ENVIRONMENT=os.getenv("ENVIRONMENT","production")

# Identifies the CI/CD pipeline that deployed the application
PIPELINE=os.getenv("PIPELINE","GitHub Actions")

# The current version of the application
VERSION=os.getenv("APP_VERSION","1.0.0")
