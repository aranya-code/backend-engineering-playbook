# FastAPI with PostgreSQL

## Overview
This project demonstrates how to dockerize a full-stack backend application using FastAPI and PostgreSQL. It sets up an API connected to a relational database, handles database migrations, and exposes automatic Swagger documentation. This example is excellent for learning how to orchestrate multiple containers that need to communicate with each other.

## Project Structure
```text
.
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── app/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── routers/
│   └── static/
├── compose.yaml
├── requirements.txt
└── scripts/
    └── wait_for_db.sh
```

## Prerequisites
- Docker installed and running
- Docker Compose installed

## Quick Start
1. Clone the repository and navigate to the project directory.
2. Create an environment file:
   ```bash
   cp .env.example .env
   ```
3. Build and start the containers:
   ```bash
   docker compose up --build
   ```
   | Flag | Description |
   |------|-------------|
   | `--build` | Forces a rebuild of the Docker image before starting the containers. Useful if you've changed the Dockerfile or requirements. |
   | `-d` | (Optional) Run containers in the background (detached mode). |

## Expected Output
Once the containers are running, you can access the interactive API documentation (Swagger UI) at:
http://localhost:8000/docs

The API provides endpoints like `/` and `/health`. 
Sample JSON response from the health check:
```json
{
  "status": "ok",
  "database": "connected"
}
```

## Environment Variables
| Variable | Description | Default Value |
|----------|-------------|---------------|
| `APP_NAME` | The name of the application | FastAPI Docker Example |
| `POSTGRES_DB` | Name of the PostgreSQL database | docker_demo |
| `POSTGRES_USER` | PostgreSQL user | postgres |
| `POSTGRES_PASSWORD` | PostgreSQL password | postgres |
| `POSTGRES_HOST` | Hostname of the database service | postgres |
| `POSTGRES_PORT` | Port number of the database | 5432 |

## Useful Commands
| Command | Action |
|---------|--------|
| `docker compose up -d` | Start services in background |
| `docker compose down` | Stop and remove containers, networks |
| `docker compose down -v` | Stop and remove containers, networks, and volumes (wipes database) |
| `docker compose logs -f api` | View live logs for the API service |

## What You Learn
| Concept | Relevant Files | Description |
|---------|----------------|-------------|
| Multi-container setup | `compose.yaml` | How to define and link multiple services (API and Database). |
| Docker Networking | `compose.yaml`, `.env` | How containers communicate using service names as hostnames (`POSTGRES_HOST=postgres`). |
| Data Persistence | `compose.yaml` | Using Docker Volumes (`postgres_data`) to ensure database data survives container restarts. |
| Container Initialization | `scripts/wait_for_db.sh` | How to wait for a database to be ready before starting the web application. |

## Key Takeaways
- Use `depends_on` in `compose.yaml` to control startup order.
- Service names in `compose.yaml` (e.g., `postgres`) resolve to IP addresses on the Docker network, allowing containers to talk to each other.
- Volumes are crucial for databases; without them, data is lost when the container stops.
- Passing `.env` files to containers simplifies configuration management.

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*