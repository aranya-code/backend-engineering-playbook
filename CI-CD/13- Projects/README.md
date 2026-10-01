# README

## Overview

This directory contains hands-on, runnable GitHub Actions projects for the Backend Engineering Playbook.

These are not project descriptions. Each project contains real source code, tests, workflow YAML, Docker configuration, and deployment configuration where applicable. The projects are designed to be cloned, configured, and run against a real GitHub repository.

The progression moves from a minimal Python CI pipeline through increasingly complex production patterns — service containers, reusable workflows, custom actions, security controls, Docker builds, Amazon ECR publishing, AWS OIDC authentication, multi-environment promotion, and a full production CI/CD capstone.

```text
Basic CI
    ↓
Framework Testing (Django / FastAPI)
    ↓
Service Containers (PostgreSQL / Redis)
    ↓
Matrix Testing
    ↓
Reusable Workflows
    ↓
Custom Actions
    ↓
Security
    ↓
Docker CI
    ↓
ECR Deployment
    ↓
AWS OIDC
    ↓
Multi-Environment Promotion
    ↓
Production CI/CD
    ↓
Capstone
```

Each project's README explains what GitHub Actions concepts it demonstrates and how to run it.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Python CI Starter](./01-%20Python%20CI%20Starter/) | A minimal runnable Python project that demonstrates checkout, Python setup, dependency installation, linting, and pytest. |
| 02 | [02- Django CI Pipeline](./02-%20Django%20CI%20Pipeline/) | Runnable Django health endpoint with automated Django checks and pytest in a GitHub Actions CI pipeline. |
| 03 | [03- FastAPI CI Pipeline](./03-%20FastAPI%20CI%20Pipeline/) | Small FastAPI service with API tests demonstrating a complete GitHub Actions CI pipeline for a FastAPI application. |
| 04 | [04- Django PostgreSQL Redis CI](./04-%20Django%20PostgreSQL%20Redis%20CI/) | Integration-test lab using GitHub Actions service containers for PostgreSQL and Redis alongside a Django application. |
| 05 | [05- Python Matrix Testing](./05-%20Python%20Matrix%20Testing/) | Demonstrates testing one codebase against multiple Python versions using a GitHub Actions matrix strategy. |
| 06 | [06- Reusable Workflow Lab](./06-%20Reusable%20Workflow%20Lab/) | Shows a caller workflow invoking a local reusable workflow with typed inputs and outputs using `workflow_call`. |
| 07 | [07- Custom Actions Lab](./07-%20Custom%20Actions%20Lab/) | Contains a local composite action and a Python test suite demonstrating how to build and consume custom GitHub Actions. |
| 08 | [08- Secure CI Pipeline](./08-%20Secure%20CI%20Pipeline/) | Security-focused CI example demonstrating least-privilege permissions, secret handling, and secure workflow design. |
| 09 | [09- Docker CI Pipeline](./09-%20Docker%20CI%20Pipeline/) | Builds a real Docker image after Python tests pass, demonstrating a Docker-based CI pipeline with GitHub Actions. |
| 10 | [10- Docker ECR Deployment](./10-%20Docker%20ECR%20Deployment/) | Publishes a Docker image to Amazon ECR using GitHub OIDC for keyless AWS authentication. |
| 11 | [11- AWS OIDC Deployment](./11-%20AWS%20OIDC%20Deployment/) | Focused OIDC lab for AWS authentication without storing long-lived AWS access keys in GitHub secrets. |
| 12 | [12- Multi Environment Deployment](./12-%20Multi%20Environment%20Deployment/) | Demonstrates promotion from staging to production using GitHub Environments, protection rules, and deployment approval. |
| 13 | [13- Production CI CD Pipeline](./13-%20Production%20CI%20CD%20Pipeline/) | A production-oriented CI/CD skeleton combining testing, container image publishing, and controlled multi-environment deployment. |
| 14 | [14- GitHub Actions Capstone](./14-%20GitHub%20Actions%20Capstone/) | A complete reference project combining the major GitHub Actions concepts from the full learning path into one integrated implementation. |

---

## Project Progression

| # | Project | Primary Focus | Key Concepts |
|---|---|---|---|
| 01 | Python CI Starter | Basic CI | Checkout, setup-python, pip, pytest, lint |
| 02 | Django CI Pipeline | Django testing | Django checks, pytest-django, CI triggers |
| 03 | FastAPI CI Pipeline | API testing | FastAPI, httpx, pytest, API CI pipeline |
| 04 | Django PostgreSQL Redis CI | Service containers | PostgreSQL, Redis, service container networking |
| 05 | Python Matrix Testing | Matrix strategy | `matrix`, `max-parallel`, multi-version testing |
| 06 | Reusable Workflow Lab | `workflow_call` | Reusable workflows, inputs, outputs, secrets |
| 07 | Custom Actions Lab | Composite actions | `action.yml`, composite steps, action inputs/outputs |
| 08 | Secure CI Pipeline | Security | Least privilege, `GITHUB_TOKEN`, secret handling |
| 09 | Docker CI Pipeline | Container builds | Docker build, layer caching, image tagging |
| 10 | Docker ECR Deployment | ECR + OIDC | Amazon ECR, OIDC, image push, IAM trust policy |
| 11 | AWS OIDC Deployment | AWS federation | OIDC token, `aws-actions/configure-aws-credentials` |
| 12 | Multi Environment Deployment | Promotion | GitHub Environments, protection rules, approvals, rollback |
| 13 | Production CI CD Pipeline | Production CI/CD | Build once, artifact promotion, staging, production |
| 14 | GitHub Actions Capstone | Integrated implementation | All major concepts combined |

---

## How to Use These Projects

Each project is a standalone, runnable GitHub Actions implementation.

To use a project:

1. Create a new GitHub repository or use an existing one.
2. Copy the project's source code and `.github/workflows/` directory into the repository.
3. Push to GitHub to trigger the workflow.
4. Configure any required secrets or environments as described in the project README.
5. Observe the workflow execution and iterate.

Each project README explains:

- What the project demonstrates.
- How to run it.
- What GitHub Actions concepts it exercises.
- What secrets or environment configuration is required.

---

## Prerequisites

| Project | Prerequisites |
|---|---|
| 01–07 | GitHub repository, no external services required |
| 08 | GitHub repository, understanding of `GITHUB_TOKEN` permissions |
| 09 | GitHub repository, Docker Hub account or equivalent (optional) |
| 10–11 | AWS account, IAM role with OIDC trust policy, Amazon ECR repository |
| 12–13 | AWS account, GitHub Environments configured, production approval reviewers |
| 14 | All of the above |

---

## Key Takeaways

- Each project is a working implementation, not a YAML template. Run it against a real repository.
- The progression from project 01 to project 14 mirrors the full GitHub Actions learning path from fundamentals to production-grade CI/CD.
- Projects 10–14 require AWS infrastructure. The project READMEs include the required IAM trust policy and environment configuration.
- The capstone project (14) combines all major concepts — testing, Docker, ECR, OIDC, environments, reusable workflows, custom actions, and multi-environment deployment — into a single reference implementation.
