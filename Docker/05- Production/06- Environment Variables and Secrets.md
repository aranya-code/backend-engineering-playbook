# Environment Variables and Secrets

## Overview

Applications require configuration to connect to databases, external APIs, caches, message brokers, and other services. In production, this configuration should be separated from the application code.

Docker provides several mechanisms for injecting configuration into containers without modifying the Docker image.

This separation makes applications easier to deploy across different environments while improving security and maintainability.

---

# Why Externalize Configuration?

Avoid embedding configuration directly into source code.

Bad

```python
DATABASE_HOST = "localhost"
DATABASE_PASSWORD = "password123"
```

Good

```text
DATABASE_HOST=db

DATABASE_PASSWORD=${DATABASE_PASSWORD}
```

Benefits:

- Easier deployments
- Better security
- Environment-specific configuration
- No code changes between environments

---

# Configuration vs Secrets

Configuration and secrets are related but serve different purposes.

| Configuration | Secrets |
|--------------|----------|
| Database host | Database password |
| Port numbers | API keys |
| Log level | JWT secret |
| Application name | Private certificates |
| Environment name | SSH keys |

Configuration is generally safe to expose.

Secrets must always remain confidential.

---

# Environment Variable Workflow

```text
Environment File

↓

Docker Compose

↓

Container

↓

Application
```

The application reads values at runtime rather than embedding them during the image build.

---

# Using Environment Variables

Example Docker Compose configuration

```yaml
services:

  app:

    image: myapp:1.0.0

    env_file:

      - .env.production
```

Example environment file

```text
APP_NAME=Backend API

APP_ENV=production

DATABASE_HOST=db

DATABASE_PORT=5432

REDIS_HOST=redis

LOG_LEVEL=INFO
```

---

# Accessing Variables in Python

```python
import os

DATABASE_HOST = os.getenv(
    "DATABASE_HOST",
    "localhost",
)

DATABASE_PORT = int(
    os.getenv(
        "DATABASE_PORT",
        5432,
    )
)
```

Provide sensible defaults for development where appropriate.

---

# Using Docker Compose Environment

Variables can also be defined directly.

```yaml
environment:

  APP_ENV: production

  LOG_LEVEL: INFO
```

For sensitive values, prefer external environment files or secret management.

---

# Environment Files

Development

```text
.env
```

Production

```text
.env.production
```

Staging

```text
.env.staging
```

Each environment should have its own configuration.

---

# Example Project Structure

```text
project/

│

├── .env.example

├── .env.development

├── .env.staging

├── .env.production

└── compose.yaml
```

The `.env.example` file documents required variables without exposing sensitive values.

---

# Example .env.example

```text
APP_NAME=Backend API

APP_ENV=development

DATABASE_HOST=db

DATABASE_PORT=5432

DATABASE_NAME=mydb

DATABASE_USER=myuser

DATABASE_PASSWORD=your_password

REDIS_HOST=redis

REDIS_PORT=6379
```

Developers copy:

```text
cp .env.example .env
```

and provide real values locally.

---

# Never Commit Secrets

Never commit:

```text
.env

.env.production

Private Keys

Certificates

API Tokens
```

Your `.gitignore` should contain:

```text
.env

.env.*

!.env.example
```

---

# Docker Secrets

Docker also supports secrets.

```text
Secret

↓

Docker

↓

Container

↓

Application
```

Docker Secrets are primarily intended for Docker Swarm and other orchestrated environments.

For standalone Docker Compose deployments, environment variables are commonly used.

---

# Secret Managers

In larger production environments, secrets are typically stored outside Docker.

Common options include:

- AWS Secrets Manager
- Azure Key Vault
- Google Secret Manager
- HashiCorp Vault

Applications retrieve secrets securely during startup or runtime.

---

# Runtime Configuration

Configuration should be injected when the container starts.

```text
Docker Image

↓

Container Starts

↓

Environment Variables Loaded

↓

Application Starts
```

This allows the same Docker image to run in multiple environments without rebuilding.

---

# Environment-Specific Deployment

Development

```text
APP_ENV=development
```

Staging

```text
APP_ENV=staging
```

Production

```text
APP_ENV=production
```

The application behavior changes through configuration rather than code modifications.

---

# Build-Time vs Runtime Variables

| Build-Time | Runtime |
|------------|---------|
| Dockerfile `ARG` | Environment variables |
| Used while building the image | Used while running the container |
| Not available after build (unless copied) | Available to the application |

Example

```dockerfile
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim
```

Runtime

```yaml
environment:

  APP_ENV: production
```

---

# Common Mistakes

## Hardcoding Passwords

Bad

```python
DATABASE_PASSWORD = "admin123"
```

Always load credentials from environment variables or a secret manager.

---

## Committing .env Files

Never commit real environment files.

Only commit:

```text
.env.example
```

---

## Using One Environment File Everywhere

Avoid using the same configuration for:

- Development
- Testing
- Staging
- Production

Each environment should have independent settings.

---

## Missing Default Values

When appropriate, provide safe defaults for local development.

Example

```python
os.getenv(
    "REDIS_HOST",
    "localhost",
)
```

---

## Logging Secrets

Avoid

```python
print(os.environ)
```

Application logs should never expose passwords, tokens, or private keys.

---

# Production Checklist

Before deployment:

- Environment variables externalized
- Secrets removed from source code
- `.env` files ignored by Git
- `.env.example` provided
- Runtime configuration verified
- Secret manager configured (if applicable)
- Sensitive values never logged
- Environment-specific files available

---

# Best Practices

- Separate configuration from application code.
- Store secrets outside Docker images.
- Commit only `.env.example`.
- Use different environment files for each deployment stage.
- Keep production secrets in dedicated secret management systems.
- Validate required environment variables during application startup.
- Never expose secrets in logs or error messages.
- Reuse the same Docker image across environments by changing only the runtime configuration.

---

# Key Takeaways

- Environment variables provide a flexible way to configure applications without modifying Docker images.
- Configuration and secrets should be treated differently, with secrets receiving additional protection.
- Runtime configuration enables the same container image to be deployed across development, staging, and production.
- Secret managers offer a more secure alternative to storing sensitive values in environment files.
- Proper configuration management improves security, portability, and maintainability across the entire deployment lifecycle.