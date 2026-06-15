# Docker Compose Commands Cheat Sheet

## Overview

This cheat sheet contains the most commonly used Docker Compose commands for:

- Creating Applications
- Starting Services
- Stopping Services
- Viewing Logs
- Managing Networks
- Managing Volumes
- Debugging
- Troubleshooting

Use this file as a quick revision guide before interviews, certifications, or production work.

---

# Basic Commands

## Check Compose Version

```bash
docker compose version
```

---

## Validate Compose File

```bash
docker compose config
```

Checks:

- YAML Syntax
- Variable Expansion
- Service Definitions

---

# Starting Applications

## Start Application

```bash
docker compose up
```

---

## Start in Detached Mode

```bash
docker compose up -d
```

Containers run in background.

---

## Build and Start

```bash
docker compose up --build
```

---

## Force Recreate Containers

```bash
docker compose up --force-recreate
```

---

## Start Specific Service

```bash
docker compose up web
```

---

# Stopping Applications

## Stop Application

```bash
docker compose down
```

---

## Stop and Remove Volumes

```bash
docker compose down -v
```

Warning:

```text
Deletes Persistent Data
```

---

## Stop Without Removing

```bash
docker compose stop
```

---

## Start Stopped Containers

```bash
docker compose start
```

---

## Restart Services

```bash
docker compose restart
```

---

# Service Management

## List Running Services

```bash
docker compose ps
```

---

## View Service Status

```bash
docker compose ps
```

Shows:

```text
Running

Exited

Healthy

Unhealthy
```

---

## Scale Services

```bash
docker compose up --scale web=3
```

---

## Scale Multiple Services

```bash
docker compose up --scale web=3 --scale api=2
```

---

# Logs

## View Logs

```bash
docker compose logs
```

---

## Follow Logs

```bash
docker compose logs -f
```

---

## View Logs for Service

```bash
docker compose logs web
```

---

## Last 100 Lines

```bash
docker compose logs --tail=100
```

---

# Executing Commands

## Open Shell

```bash
docker compose exec web sh
```

---

## Open Bash

```bash
docker compose exec web bash
```

---

## Run Command

```bash
docker compose exec web ls
```

---

# Container Information

## List Containers

```bash
docker compose ps
```

---

## View Container IDs

```bash
docker compose ps -q
```

---

## Top Processes

```bash
docker compose top
```

---

# Build Commands

## Build Images

```bash
docker compose build
```

---

## Build Without Cache

```bash
docker compose build --no-cache
```

---

## Pull Images

```bash
docker compose pull
```

---

## Push Images

```bash
docker compose push
```

---

# Volume Commands

## View Volumes

```bash
docker volume ls
```

---

## Remove Volumes During Cleanup

```bash
docker compose down -v
```

---

## Inspect Volume

```bash
docker volume inspect <volume-name>
```

---

# Network Commands

## View Networks

```bash
docker network ls
```

---

## Inspect Network

```bash
docker network inspect <network-name>
```

---

# Environment Variables

## Render Final Configuration

```bash
docker compose config
```

---

## Use Custom Environment File

```bash
docker compose --env-file prod.env up
```

---

# Profiles

## Start Profile

```bash
docker compose --profile dev up
```

---

## Start Multiple Profiles

```bash
docker compose --profile dev --profile monitoring up
```

---

# Debugging Commands

## View Service Logs

```bash
docker compose logs
```

---

## Check Running Services

```bash
docker compose ps
```

---

## Open Container Shell

```bash
docker compose exec web sh
```

---

## View Configuration

```bash
docker compose config
```

---

# Cleanup Commands

## Stop and Remove Containers

```bash
docker compose down
```

---

## Remove Orphan Containers

```bash
docker compose down --remove-orphans
```

---

## Remove Unused Images

```bash
docker image prune
```

---

## Remove Unused Volumes

```bash
docker volume prune
```

---

## Remove Everything

```bash
docker system prune -a
```

---

# Common Workflows

## Development Workflow

Start:

```bash
docker compose up -d
```

View Logs:

```bash
docker compose logs -f
```

Open Shell:

```bash
docker compose exec app sh
```

Stop:

```bash
docker compose down
```

---

## Rebuild Workflow

Build:

```bash
docker compose build
```

Start:

```bash
docker compose up -d
```

---

## Troubleshooting Workflow

View Services:

```bash
docker compose ps
```

View Logs:

```bash
docker compose logs
```

Open Shell:

```bash
docker compose exec app sh
```

---

# Most Important Commands

## Start Application

```bash
docker compose up -d
```

---

## Stop Application

```bash
docker compose down
```

---

## View Status

```bash
docker compose ps
```

---

## View Logs

```bash
docker compose logs -f
```

---

## Execute Shell

```bash
docker compose exec app sh
```

---

## Validate Configuration

```bash
docker compose config
```

---

# One-Page Revision Commands

```bash
docker compose up

docker compose up -d

docker compose down

docker compose ps

docker compose logs

docker compose logs -f

docker compose exec app sh

docker compose build

docker compose pull

docker compose config

docker compose restart

docker compose stop

docker compose start

docker compose top

docker compose --profile dev up
```

---

# Common Interview Questions

## Which Command Starts a Compose Application?

```bash
docker compose up
```

---

## Which Command Stops a Compose Application?

```bash
docker compose down
```

---

## Which Command Shows Logs?

```bash
docker compose logs
```

---

## Which Command Opens a Shell?

```bash
docker compose exec <service> sh
```

---

## Which Command Validates the Compose File?

```bash
docker compose config
```

---

## Which Command Scales Services?

```bash
docker compose up --scale
```

---

# Interview One-Liner

Mastering Docker Compose commands enables efficient deployment, management, scaling, troubleshooting, and maintenance of multi-container applications using a simple declarative workflow.
