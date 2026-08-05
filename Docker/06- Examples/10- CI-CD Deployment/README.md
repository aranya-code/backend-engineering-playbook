# CI/CD Deployment

## Overview

This project demonstrates how to automate the build, testing, and deployment of a Dockerized FastAPI application using **GitHub Actions**.

Unlike the previous example, which focused on preparing an application for production, this project focuses on **automation**. Every code change follows a repeatable pipeline that validates the application, builds a Docker image, and deploys it automatically.

The goal is to understand Continuous Integration (CI), Continuous Deployment (CD), GitHub Actions workflows, deployment automation, and rollback strategies.

---

# CI/CD Architecture

```text
               Developer

                   │

             git push origin main

                   │

                   ▼

               GitHub Repository

                   │

                   ▼

            GitHub Actions Runner

         ┌─────────┴──────────┐

         ▼                    ▼

    Continuous          Continuous
    Integration         Deployment

         │                    │

         ▼                    ▼

     Run Tests          Build Docker Image

                              │

                              ▼

                     Deploy Application

                              │

                              ▼

                     Verify Health Check

                              │

                              ▼

                        Production
```

---

# Concepts Covered

- Continuous Integration
- Continuous Deployment
- GitHub Actions
- Docker Build Automation
- Docker Compose
- Automated Testing
- Health Checks
- Deployment Verification
- GitHub Secrets
- Rollback Strategy
- Production Automation

---

# Project Structure

```text
10- CI-CD Deployment/
│
├── README.md
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── .dockerignore
├── .gitignore
├── .env.example
│
├── app/
│   ├── main.py
│   ├── settings.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   └── home.py
│   │
│   └── static/
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
│
├── scripts/
│   ├── start.sh
│   └── deploy.sh
│
├── deployment/
│   ├── production.md
│   └── rollback.md
│
└── screenshots/
```

---

# Prerequisites

Install:

- Git
- Docker Desktop (Windows/macOS)
- Docker Engine + Docker Compose (Linux)
- GitHub Account

Basic understanding of:

- Docker
- Git
- FastAPI

---

# CI vs CD

| Continuous Integration | Continuous Deployment |
|-------------------------|-----------------------|
| Validate code | Release application |
| Run tests | Deploy application |
| Build application | Verify deployment |
| Detect problems early | Deliver changes automatically |

---

# CI Pipeline

```text
Developer

↓

Git Push

↓

GitHub

↓

Checkout Code

↓

Install Dependencies

↓

Run Tests

↓

Pipeline Passed
```

---

# CD Pipeline

```text
CI Successful

↓

Build Docker Image

↓

Deploy

↓

Health Check

↓

Production Ready
```

---

# GitHub Actions Workflows

## ci.yml

Responsibilities

- Checkout repository
- Install Python
- Install dependencies
- Run tests

---

## cd.yml

Responsibilities

- Build Docker image
- Deploy application
- Verify deployment

---

# Running Locally

## Copy Environment Variables

```bash
cp .env.example .env
```

---

## Build

```bash
docker compose build
```

---

## Run

```bash
docker compose up
```

Application

```text
http://localhost:8000
```

---

# Deployment Flow

```text
Developer

↓

Push

↓

GitHub

↓

CI

↓

Tests

↓

Docker Build

↓

CD

↓

Deploy

↓

Health Check

↓

Production
```

---

# Health Verification

After deployment, GitHub Actions checks:

```text
GET /health
```

Healthy

```json
{
    "status": "healthy"
}
```

If the endpoint fails, the deployment should be considered unsuccessful.

---

# GitHub Secrets

Never store secrets inside:

```text
Dockerfile

Repository

Workflow Files
```

Instead, use GitHub Secrets.

Typical secrets include:

| Secret | Purpose |
|----------|----------|
| DOCKER_USERNAME | Docker Hub username |
| DOCKER_PASSWORD | Docker Hub token/password |
| SSH_HOST | Remote server |
| SSH_USERNAME | SSH user |
| SSH_PRIVATE_KEY | Deployment key |

---

# Deployment Script

The deployment script performs:

```text
Stop Containers

↓

Pull Latest Image

↓

Start Containers

↓

Deployment Complete
```

---

# Rollback Strategy

If deployment fails:

```text
Deploy

↓

Health Check

↓

Failed

↓

Rollback

↓

Previous Version Restored
```

Common rollback methods:

- Previous Docker image
- Previous Git tag
- Previous Docker Compose release

---

# Useful Commands

Build image

```bash
docker build -t cicd-demo .
```

Run locally

```bash
docker compose up
```

Run tests

```bash
pytest
```

View logs

```bash
docker compose logs
```

Stop containers

```bash
docker compose down
```

Run GitHub Actions locally (optional)

```bash
act
```

Validate Docker image

```bash
docker images
```

List running containers

```bash
docker ps
```

---

# Workflow Lifecycle

```text
Code Change

↓

Commit

↓

Push

↓

CI

↓

Tests

↓

Docker Build

↓

CD

↓

Deploy

↓

Health Check

↓

Users
```

---

# Production Deployment Lifecycle

```text
Developer

↓

GitHub Repository

↓

GitHub Actions

↓

Docker Image

↓

Deployment

↓

Running Container

↓

Production
```

---

# What You Learn

| Concept | Where It Appears |
|----------|------------------|
| CI | ci.yml |
| CD | cd.yml |
| Docker Build | Dockerfile |
| Docker Compose | compose.yaml |
| GitHub Actions | `.github/workflows` |
| Deployment Script | deploy.sh |
| Health Checks | `/health` |
| GitHub Secrets | Workflow configuration |
| Rollback | rollback.md |

---

# Common Mistakes

## Skipping Tests

Never deploy code that hasn't passed automated tests.

---

## Committing Secrets

Never commit:

```text
Passwords

API Keys

SSH Keys

Tokens
```

Use GitHub Secrets instead.

---

## Ignoring Health Checks

Deployment should finish only after the application responds successfully.

---

## Deploying Without Rollback

Always have a rollback strategy before deploying a new version.

---

# Best Practices

- Keep CI and CD automated.
- Run tests before building Docker images.
- Store secrets in GitHub Secrets.
- Verify deployments with health checks.
- Keep deployment scripts idempotent.
- Use pinned dependency versions.
- Keep workflows small and focused.
- Document deployment and rollback procedures.

---

# CI/CD Pipeline Summary

```text
Write Code

↓

Commit

↓

Push

↓

GitHub Actions

↓

Test

↓

Build

↓

Deploy

↓

Verify

↓

Production
```

---

# Relationship to Previous Example

```text
Example 09

↓

Production-Ready Docker Application

↓

Example 10

↓

Automatically Build

↓

Automatically Test

↓

Automatically Deploy
```

This project completes the Docker learning journey by showing how a production-ready application can be released automatically through a modern CI/CD pipeline.

---

# Key Takeaways

- Continuous Integration validates every code change before deployment.
- Continuous Deployment automates the release process after successful validation.
- GitHub Actions provides a powerful platform for building, testing, and deploying applications.
- Docker ensures consistent builds across development, testing, and production.
- Health checks help confirm successful deployments before users are affected.
- Secrets should always be managed securely through GitHub Actions rather than committed to source control.
- A reliable rollback strategy is an essential part of any deployment process.

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*