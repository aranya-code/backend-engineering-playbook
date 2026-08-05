# Python Flask

## Overview
A simple Flask web API demonstrating how to dockerize a Python application. This project highlights core Docker concepts like port mapping, environment variable injection, and exposing health check endpoints commonly used in containerized environments.

## Docker Concepts Demonstrated
- **Port Mapping (`-p`)**: Forwarding traffic from the host machine to the container.
- **Detached Mode (`-d`)**: Running the container in the background.
- **Environment Variables**: Passing configuration to the container at runtime.
- **Health Endpoints**: Providing a route to verify the application's status.

## Project Structure
```
.
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── app
│   └── app.py
└── requirements.txt
```

## Prerequisites
- Docker installed on your system.

## Quick Start

1. **Build the image**
```bash
docker build -t python-flask-app .
```

2. **Run the container**
```bash
docker run -d -p 5000:5000 --env-file .env.example --name flask-container python-flask-app
```

| Flag | Description |
|------|-------------|
| `-d` | Runs the container in detached mode (in the background). |
| `-p 5000:5000` | Maps port 5000 on the host to port 5000 in the container. |
| `--env-file` | Loads environment variables from a file. |
| `--name` | Assigns a custom name to the container. |

## Expected Output
```bash
curl localhost:5000
```
```json
{
  "app": "Python Flask Docker App",
  "hostname": "9d90fb8c9f5f",
  "message": "Hello from Flask inside Docker!",
  "python_version": "3.12.2",
  "time": "2024-05-18T10:15:30.123456"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | The name of the application displayed in the API response. | `Python Flask Docker App` |
| `FLASK_PORT` | The port the application uses. | `5000` |

## Useful Commands

```bash
# View container logs
docker logs flask-container

# Access the container shell
docker exec -it flask-container /bin/sh

# Stop the container
docker stop flask-container

# Remove the container
docker rm flask-container
```

## What You Learn

| Concept | File | Description |
|---------|------|-------------|
| **Base Images & Layering** | `Dockerfile` | Using lightweight images (`slim`) and structuring instructions for caching. |
| **App Configuration** | `app.py` | Reading environment variables and binding to `0.0.0.0`. |
| **Context Optimization** | `.dockerignore` | Excluding unnecessary files to speed up builds. |

## Key Takeaways
- Always bind web servers to `0.0.0.0` inside containers so they can accept external connections.
- Ordering commands correctly in a Dockerfile (like copying `requirements.txt` before the app code) optimizes build times by leveraging Docker's cache.
- Implementing a `/health` endpoint is crucial for container orchestrators (like Kubernetes) to monitor app availability.

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*
