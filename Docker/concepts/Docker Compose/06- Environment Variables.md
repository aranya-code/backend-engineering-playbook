# Environment Variables in Docker Compose

## Overview

Environment variables are used to pass configuration values into containers without hardcoding them into application code or Docker images.

They make applications:

- Flexible
- Reusable
- Portable
- Easier to manage

Environment variables are commonly used for:

```text
Database Hosts

Passwords

Ports

API Keys

Application Settings
```

---

# What are Environment Variables?

## Definition

Environment variables are key-value pairs available to processes running inside a container.

Example:

```text
DB_HOST=mysql

DB_PORT=3306

APP_ENV=production
```

Applications read these values during runtime.

---

# Why Use Environment Variables?

Without environment variables:

```python
DB_HOST = "mysql"
DB_PORT = "3306"
```

Configuration is hardcoded.

---

# With Environment Variables

```python
DB_HOST = os.getenv("DB_HOST")
```

Configuration becomes dynamic.

---

# Environment Variable Architecture

```text
Compose File

      │

      ▼

Environment Variables

      │

      ▼

Container

      │

      ▼

Application
```

---

# Defining Environment Variables

Example:

```yaml
services:

  app:

    environment:

      DB_HOST: mysql

      DB_PORT: 3306
```

---

# Alternative Syntax

Docker Compose supports list format.

Example:

```yaml
environment:

  - DB_HOST=mysql

  - DB_PORT=3306
```

---

# Comparison

## Dictionary Format

```yaml
environment:

  DB_HOST: mysql
```

Recommended.

---

## List Format

```yaml
environment:

  - DB_HOST=mysql
```

Also valid.

---

# Example Application

```yaml
services:

  web:

    image: nginx

    environment:

      APP_ENV: production

      LOG_LEVEL: info
```

---

# Database Example

```yaml
services:

  mysql:

    image: mysql

    environment:

      MYSQL_ROOT_PASSWORD: password

      MYSQL_DATABASE: appdb
```

---

# Common Database Variables

MySQL:

```text
MYSQL_ROOT_PASSWORD

MYSQL_DATABASE

MYSQL_USER

MYSQL_PASSWORD
```

---

# PostgreSQL Variables

```text
POSTGRES_DB

POSTGRES_USER

POSTGRES_PASSWORD
```

---

# Viewing Environment Variables

Inside container:

```bash
docker exec -it <container-id> sh
```

View:

```bash
env
```

or

```bash
printenv
```

---

# Environment Variable Flow

```text
Compose File

      │

      ▼

Container Startup

      │

      ▼

Variables Injected

      │

      ▼

Application Reads Values
```

---

# Variable Substitution

Docker Compose supports variable substitution.

Example:

```yaml
environment:

  DB_HOST: ${DB_HOST}
```

---

# Environment File

Create:

```text
.env
```

Contents:

```text
DB_HOST=mysql

DB_PORT=3306

APP_ENV=production
```

---

# Using .env Files

Compose automatically loads:

```text
.env
```

from the project directory.

---

# Example

.env:

```text
APP_PORT=8080
```

Compose:

```yaml
ports:

  - "${APP_PORT}:80"
```

Result:

```text
8080:80
```

---

# Default Values

Example:

```yaml
environment:

  APP_ENV: ${APP_ENV:-development}
```

Meaning:

```text
Use APP_ENV

Otherwise use development
```

---

# Required Variables

Example:

```yaml
environment:

  DB_HOST: ${DB_HOST?required}
```

If missing:

```text
Compose Error
```

---

# Multiple Environment Files

Specify file:

```bash
docker compose --env-file prod.env up
```

---

# Environment Variables vs Secrets

## Environment Variables

```text
Easy

Flexible

Visible Inside Container
```

---

## Docker Secrets

```text
Encrypted

More Secure

Recommended for Sensitive Data
```

---

# Avoid Storing Passwords

Avoid:

```yaml
environment:

  DB_PASSWORD: password123
```

Use:

```text
Docker Secrets
```

for production.

---

# Passing Host Variables

Host:

```bash
export APP_ENV=production
```

Compose:

```yaml
environment:

  APP_ENV: ${APP_ENV}
```

---

# Environment Variable Precedence

Highest Priority:

```text
Command Line
```

Then:

```text
Compose File
```

Then:

```text
.env File
```

Then:

```text
Default Values
```

---

# Complete Example

.env:

```text
DB_HOST=mysql

DB_PORT=3306

APP_ENV=production
```

Compose:

```yaml
services:

  app:

    image: myapp

    environment:

      DB_HOST: ${DB_HOST}

      DB_PORT: ${DB_PORT}

      APP_ENV: ${APP_ENV}
```

---

# Verify Configuration

Render configuration:

```bash
docker compose config
```

---

# Troubleshooting

## Variable Not Found

Check:

```text
.env File Exists?
```

---

## Wrong Value Loaded

Verify:

```bash
docker compose config
```

---

## Application Cannot Read Variable

Verify:

```bash
printenv
```

inside container.

---

# Best Practices

## Use .env Files

Keep configuration separate.

---

## Avoid Hardcoding Values

Use variables instead.

---

## Use Secrets for Passwords

Avoid storing credentials in Compose files.

---

## Use Default Values

Prevent deployment failures.

---

## Validate Configuration

```bash
docker compose config
```

before deployment.

---

# Common Commands

## Start Application

```bash
docker compose up
```

---

## Use Custom Environment File

```bash
docker compose --env-file prod.env up
```

---

## View Variables

```bash
printenv
```

---

## Render Final Configuration

```bash
docker compose config
```

---

# Common Interview Questions

## What are Environment Variables in Docker Compose?

Environment variables are key-value pairs passed into containers to provide runtime configuration.

---

## Which Section Defines Variables?

```yaml
environment:
```

---

## What is the Purpose of the .env File?

To store reusable configuration values loaded automatically by Docker Compose.

---

## How Do You Reference Variables?

```yaml
${VARIABLE_NAME}
```

---

## How Do You Set a Default Value?

```yaml
${VARIABLE:-default}
```

---

## Are Environment Variables Secure for Passwords?

Not ideal.

Docker Secrets are preferred for sensitive data.

---

# Interview One-Liner

Docker Compose environment variables provide a flexible mechanism for injecting runtime configuration into containers through Compose files, .env files, and host variables, enabling portable and reusable application deployments.
