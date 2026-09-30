# 06- Docker CI CD Architecture

## Overview

Docker CI/CD architecture defines how container images move from source code through validation, image construction, security controls, registry storage, environment promotion, deployment, monitoring, and rollback.

For backend systems, Docker provides a consistent packaging boundary:

```text
Application Source
        ↓
Docker Build
        ↓
Immutable Image
        ↓
Container Registry
        ↓
Deployment Platform
        ↓
Runtime
```

A production Docker pipeline should separate:

```text
Build
  ↓
Validate
  ↓
Publish
  ↓
Promote
  ↓
Deploy
  ↓
Observe
  ↓
Rollback
```

The central architectural principle is:

> **Build the image once, identify it immutably, and promote the same image through environments.**

This avoids environment-specific rebuilds and makes production deployments reproducible.

---

## Docker in a CI/CD System

Docker sits between application code and the deployment runtime.

```text
Git Repository
      ↓
GitHub Actions
      ↓
Docker Buildx
      ↓
Docker Image
      ↓
ECR / Registry
      ↓
ECS / Kubernetes / EC2
      ↓
Running Container
```

The CI system should be responsible for producing a trustworthy artifact.

The CD system should consume that artifact.

---

## Why Docker Is Important in CI/CD

Docker provides:

- Consistent runtime packaging.
- Dependency isolation.
- Reproducible build environments.
- Portable deployment artifacts.
- Explicit runtime dependencies.
- Easier local-to-production parity.
- Standardized deployment interfaces.

For a Python backend:

```text
Django / FastAPI
      ↓
Python Runtime
      ↓
Application Dependencies
      ↓
Docker Image
      ↓
ECS / Kubernetes / EC2
```

The image becomes the deployable unit.

---

## Docker CI/CD Architecture

A production architecture can be represented as:

```mermaid
flowchart LR
    SRC[Git Repository]
    PR[Pull Request]
    CI[GitHub Actions CI]
    TEST[Test and Security]
    BUILD[Docker Buildx]
    SCAN[Image Scan]
    SBOM[SBOM / Provenance]
    REG[ECR / Registry]
    STG[Staging]
    APPROVAL[Production Approval]
    PROD[Production]
    MON[Monitoring]
    RB[Rollback]

    SRC --> PR
    PR --> CI
    CI --> TEST
    TEST --> BUILD
    BUILD --> SCAN
    SCAN --> SBOM
    SBOM --> REG
    REG --> STG
    STG --> APPROVAL
    APPROVAL --> PROD
    PROD --> MON
    MON --> RB
    RB --> REG
```

The important boundary is between **image creation** and **image deployment**.

---

## Docker Image Lifecycle

A production Docker image normally follows:

```text
Source
 ↓
Dockerfile
 ↓
Build Context
 ↓
BuildKit / Buildx
 ↓
Image
 ↓
Security Validation
 ↓
Registry
 ↓
Promotion
 ↓
Deployment
```

Each stage should have an explicit responsibility.

| Stage | Responsibility |
|---|---|
| Source | Application code |
| Dockerfile | Image construction instructions |
| Buildx | Build execution |
| Scan | Vulnerability assessment |
| SBOM | Dependency inventory |
| Registry | Artifact storage |
| Deployment | Runtime rollout |
| Monitoring | Runtime validation |
| Rollback | Recovery |

---

## CI vs CD Responsibilities

A useful boundary is:

```text
CI
 ├── Lint
 ├── Unit Tests
 ├── Integration Tests
 ├── Security Tests
 ├── Docker Build
 ├── Image Scan
 ├── SBOM
 └── Publish Image

CD
 ├── Resolve Artifact
 ├── Deploy
 ├── Health Check
 ├── Promote
 ├── Monitor
 └── Rollback
```

CI answers:

> Is this source code suitable for producing a release artifact?

CD answers:

> Can this already-validated artifact be safely deployed?

---

## Build Once, Deploy Many

The preferred production model is:

```text
Commit
 ↓
Build Image
 ↓
Image Digest
 ↓
Staging
 ↓
Production
```

Not:

```text
Commit
 ↓
Build Staging Image
 ↓
Build Production Image
```

Every rebuild creates another artifact.

For example:

```text
orders-api:staging
orders-api:production
```

may represent two different binaries even if both were built from the same commit.

Instead, promote:

```text
orders-api@sha256:abc...
```

through every environment.

---

## Immutable Artifact Identity

Docker tags are useful for human-readable references:

```text
orders-api:1.8.0
orders-api:abc1234
```

but tags can be mutable.

A digest identifies the exact image:

```text
orders-api@sha256:abcdef...
```

Production deployments should preferably reference immutable image identity.

A useful metadata chain is:

```text
Commit SHA
    ↓
Build Run
    ↓
Image Tag
    ↓
Image Digest
    ↓
Deployment
```

This enables traceability from production back to source.

---

## Dockerfile Architecture

A production Dockerfile should separate build-time and runtime concerns.

Example for FastAPI:

```dockerfile
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY requirements.txt .

RUN pip install --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The builder contains dependency installation logic.

The runtime image contains only what is required to execute the application.

---

## Multi-Stage Builds

Multi-stage builds reduce runtime image size.

```text
Builder Image
 ├── Compiler
 ├── Build Tools
 ├── Development Dependencies
 └── Application Dependencies
          ↓
       Runtime
          ↓
 ├── Runtime
 ├── Application
 └── Runtime Dependencies
```

Benefits:

- Smaller images.
- Lower attack surface.
- Less unnecessary tooling.
- Faster image transfer.
- Lower registry and network costs.

---

## Docker Build Context

The build context determines what files Docker can access.

Example:

```bash
docker build -t orders-api .
```

The `.` sends the current directory as build context.

A `.dockerignore` should exclude unnecessary files:

```text
.git
.github
.venv
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.env
node_modules
dist
build
```

This improves:

- Build performance.
- Cache efficiency.
- Security.
- Image construction predictability.

---

## Never Copy Secrets Into Images

Avoid:

```dockerfile
COPY .env /app/.env
```

Secrets baked into an image become part of the image layers.

Even if the file is later deleted:

```dockerfile
COPY .env .
RUN rm .env
```

the secret may remain recoverable from image history or layers.

Use runtime configuration instead.

```text
GitHub Secrets / AWS Secrets Manager
        ↓
Deployment Platform
        ↓
Container Environment
```

---

## Docker Build Arguments

Build arguments can configure builds:

```dockerfile
ARG APP_VERSION
LABEL org.opencontainers.image.version=$APP_VERSION
```

Build:

```bash
docker build \
  --build-arg APP_VERSION=1.8.0 \
  -t orders-api:1.8.0 .
```

Do not use build arguments for sensitive credentials.

Build arguments can become visible through image metadata or build history depending on how they are used.

---

## Docker Build Secrets

When build-time access to a secret is genuinely required, use BuildKit secret mounts rather than embedding credentials.

Conceptually:

```text
CI Secret
    ↓
BuildKit Secret Mount
    ↓
Build Step
    ↓
Secret Not Persisted in Image
```

The secret should not become part of:

- Dockerfile commands.
- Image layers.
- Build arguments.
- Application files.

---

## Buildx

Docker Buildx provides advanced BuildKit-based building capabilities.

It is useful for:

- Multi-platform images.
- Parallel builds.
- Advanced caching.
- Build metadata.
- CI/CD builds.

Example:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t orders-api:1.8.0 \
  --push .
```

The exact platform set should match the production runtime.

---

## Multi-Platform Images

A single logical image can support multiple architectures:

```text
orders-api:1.8.0
        ↓
Manifest
 ├── linux/amd64
 └── linux/arm64
```

This is useful when:

- Development uses Apple Silicon.
- CI uses x86 runners.
- Production uses ARM instances.
- Different deployment platforms require different architectures.

Architecture compatibility should be tested before production rollout.

---

## Docker Layer Caching

Docker builds consist of layers.

A simplified Dockerfile:

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
```

When only application source changes, the dependency installation layer can remain cached.

Poor ordering:

```dockerfile
COPY . .
RUN pip install -r requirements.txt
```

Every source change can invalidate the dependency installation layer.

The better structure separates stable inputs from frequently changing inputs.

---

## GitHub Actions Docker Cache

A GitHub Actions workflow can use BuildKit caching:

```yaml
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

Cache improves build performance but is not the release artifact.

```text
Cache
    = Build acceleration

Image
    = Deployment artifact
```

---

## Registry-Based Docker Cache

A registry can also store build cache.

Conceptually:

```text
CI Runner
   ↓
Buildx
   ├── Pull Cache → Registry
   └── Push Cache → Registry
```

This is useful when:

- Runners are ephemeral.
- Multiple runners share builds.
- Builds are large.
- Local runner cache cannot be relied upon.

---

## Cache Security

Caches should not be treated as trusted release artifacts.

Potential risks include:

- Cache poisoning.
- Cross-branch contamination.
- Untrusted pull requests.
- Incorrect cache keys.
- Stale dependencies.

Cache keys should reflect meaningful dependency inputs.

For Python:

```yaml
key: ${{ runner.os }}-python-${{ hashFiles('**/requirements*.txt', '**/poetry.lock') }}
```

The exact cache strategy should match the dependency management system.

---

## Docker Metadata

A production image should carry useful metadata.

Typical metadata includes:

```text
Repository
Commit SHA
Version
Build Time
Source URL
Revision
```

OCI labels can provide traceability:

```dockerfile
LABEL org.opencontainers.image.source="https://github.com/example/orders"
LABEL org.opencontainers.image.revision="abc123"
LABEL org.opencontainers.image.version="1.8.0"
```

This metadata helps incident investigation and artifact auditing.

---

## Docker Image Tagging Strategy

A practical strategy can use multiple tags:

```text
orders-api:abc1234
orders-api:1.8.0
orders-api:latest
```

The roles differ:

| Tag | Purpose |
|---|---|
| Commit SHA | Traceability |
| Semantic version | Release identity |
| `latest` | Human convenience |
| Digest | Immutable identity |

Production deployment should use the digest or another immutable reference.

---

## Image Vulnerability Scanning

A production pipeline should scan images before publication or promotion.

```text
Build
 ↓
Scan
 ↓
Policy
 ↓
Publish
```

Scanning can identify:

- OS package vulnerabilities.
- Application dependency vulnerabilities.
- Known CVEs.
- Risky packages.

A scan should not automatically imply that every vulnerability is exploitable.

Risk evaluation may consider:

- Severity.
- Reachability.
- Runtime exposure.
- Exploit availability.
- Compensating controls.

---

## SBOM

An SBOM provides a machine-readable inventory of components.

For a Python image:

```text
Base Image
 ├── OS packages
 └── Python runtime

Application
 ├── Django
 ├── FastAPI
 ├── Requests
 └── Other dependencies
```

SBOMs improve:

- Vulnerability response.
- Compliance.
- Dependency visibility.
- Incident investigation.

---

## Provenance

Artifact provenance answers questions such as:

```text
Which repository produced this image?
Which commit?
Which workflow?
Which build environment?
Which builder?
```

A useful chain is:

```text
Source
 ↓
Workflow
 ↓
Builder
 ↓
Image
```

This helps establish trust in the build process.

---

## Artifact Attestations and Signing

An enterprise image may use:

```text
Image
 ↓
Signature
 ↓
Provenance Attestation
 ↓
SBOM
```

Deployment policy can then require that the artifact:

- Came from an approved repository.
- Was built by an approved workflow.
- Has expected provenance.
- Passed required security checks.

---

## GitHub Actions Docker Workflow

A practical workflow can look like:

```yaml
name: Docker Build

on:
  push:
    branches:
      - main

permissions:
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ghcr.io/example/orders:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

The same architecture can be adapted to Amazon ECR.

---

## AWS ECR Architecture

For AWS:

```text
GitHub Actions
      ↓
OIDC
      ↓
AWS STS
      ↓
IAM Role
      ↓
ECR
      ↓
ECS / EC2 / EKS
```

The workflow does not need long-lived AWS access keys when OIDC is appropriately configured.

---

## ECR Authentication

A typical workflow uses AWS credentials configured through OIDC and then logs into ECR.

Conceptually:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v5
  with:
    role-to-assume: ${{ vars.AWS_DEPLOY_ROLE }}
    aws-region: us-east-1
```

Then:

```yaml
- name: Login to Amazon ECR
  id: login-ecr
  uses: aws-actions/amazon-ecr-login@v2
```

The IAM role should have only the ECR permissions required by the workflow.

---

## ECR Push Permissions

A build workflow commonly requires permissions associated with:

```text
ecr:GetAuthorizationToken
ecr:BatchCheckLayerAvailability
ecr:InitiateLayerUpload
ecr:UploadLayerPart
ecr:CompleteLayerUpload
ecr:PutImage
```

The exact policy should be restricted to the required repository and operations.

---

## ECR Pull Permissions

The runtime identity is different from the build identity.

Conceptually:

```text
GitHub Actions Role
    ↓
Push Image

ECS Task Execution Role
    ↓
Pull Image
```

Do not automatically give runtime identities permission to push images.

Separating push and pull privileges reduces blast radius.

---

## AWS OIDC Trust Boundary

Production architecture should look like:

```text
GitHub Repository
       ↓
GitHub Environment
       ↓
OIDC Token
       ↓
IAM Trust Policy
       ↓
Deployment Role
       ↓
ECR / ECS / AWS
```

The IAM trust policy should restrict the repositories and environments that can assume the role.

---

## Docker and ECS

A common architecture is:

```text
GitHub Actions
      ↓
Buildx
      ↓
ECR
      ↓
ECS Task Definition
      ↓
ECS Service
      ↓
ALB
      ↓
Django / FastAPI
```

The ECS service references the image.

Production deployment should update the task definition to the intended immutable image.

---

## Docker and Kubernetes

The architecture becomes:

```text
GitHub Actions
      ↓
Buildx
      ↓
ECR
      ↓
Kubernetes Deployment
      ↓
Pods
      ↓
Service
      ↓
Ingress / Nginx
```

A deployment may reference:

```yaml
image: 123456789.dkr.ecr.us-east-1.amazonaws.com/orders@sha256:...
```

Using an immutable image reference reduces accidental version changes.

---

## Docker and EC2

For EC2:

```text
GitHub Actions
      ↓
ECR
      ↓
EC2
      ↓
Docker Pull
      ↓
Container
      ↓
Nginx
      ↓
Application
```

The EC2 instance can use an IAM instance profile to authenticate with AWS services.

Deployment should avoid embedding AWS credentials in the container image.

---

## Docker and Lambda

Container-based Lambda functions use images stored in ECR.

```text
GitHub Actions
      ↓
Build Lambda Image
      ↓
ECR
      ↓
Lambda
```

The image must conform to Lambda's container image requirements.

The deployment workflow should update Lambda to the intended image identity and validate the resulting function.

---

## Django Container Architecture

A production Django image generally contains:

```text
Python Runtime
    ↓
Django
    ↓
Application
```

It should not normally contain:

- PostgreSQL.
- Redis.
- Kafka.
- Nginx.

Those are separate runtime services.

A typical architecture is:

```text
ALB / Nginx
      ↓
Django Containers
      ├── PostgreSQL
      ├── Redis
      └── Celery Workers
```

The CI pipeline validates the integration between these components.

---

## FastAPI Container Architecture

```text
ALB / Nginx
      ↓
FastAPI Containers
      ├── PostgreSQL
      ├── Redis
      └── Celery / Workers
```

A typical runtime command is:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For production, the exact process model should match the runtime platform and application concurrency requirements.

---

## Containerized Integration Testing

CI can use service containers:

```text
GitHub Actions Job
      ↓
Python Application Container
      ├── PostgreSQL
      └── Redis
              ↓
            pytest
```

Example:

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app
        options: >-
          --health-cmd "pg_isready -U test -d app"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - run: |
          pip install -r requirements.txt
          pytest tests/integration
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app
          REDIS_URL: redis://localhost:6379/0
```

Readiness is important because container startup does not guarantee service availability.

---

## Docker Compose vs GitHub Service Containers

Docker Compose is useful when the integration environment is complex.

```text
Compose
 ├── API
 ├── PostgreSQL
 ├── Redis
 ├── Kafka
 └── Worker
```

GitHub service containers are often simpler for isolated CI dependencies.

| Requirement | Service Containers | Docker Compose |
|---|---|---|
| Simple database dependency | Good | Good |
| Multiple interconnected services | Moderate | Strong |
| Complex networking | Limited | Strong |
| Reproduce production topology | Limited | Strong |
| Simple CI configuration | Strong | Moderate |
| Full local stack | Limited | Strong |

Choose based on environment complexity rather than preference.

---

## Docker Networking in CI

A common mistake is assuming every container can access a service through `localhost`.

The correct address depends on the networking model.

For runner-based service containers:

```text
GitHub Runner
    ↓
localhost:<mapped-port>
    ↓
Service Container
```

For jobs running inside a container with service containers:

```text
Job Container
    ↓
Service Name
    ↓
PostgreSQL / Redis
```

The networking model must be understood before writing connection strings.

---

## Docker Health and Readiness

A running container does not necessarily mean the application is ready.

```text
Container Started
       ↓
Process Started
       ↓
Application Initialized
       ↓
Database Connection Ready
       ↓
Ready
```

Use:

- Health checks.
- Readiness probes.
- Explicit retry logic.
- Connection validation.

This is particularly important for PostgreSQL, Redis, Kafka, and application startup migrations.

---

## CI Test Pipeline

A realistic backend pipeline is:

```text
Pull Request
     ↓
Lint
     ↓
Unit Tests
     ↓
PostgreSQL + Redis
     ↓
Integration Tests
     ↓
Coverage
     ↓
Docker Build
     ↓
Image Scan
     ↓
Artifact
```

The Docker build should ideally happen after application correctness checks unless building earlier provides a specific validation benefit.

---

## Test the Docker Image

Building an image is not the same as validating it.

A stronger pipeline is:

```text
Build
 ↓
Run Container
 ↓
Health Check
 ↓
API Smoke Test
 ↓
Stop
```

Example:

```bash
docker run -d \
  --name orders-api \
  -p 8000:8000 \
  orders-api:${GITHUB_SHA}

curl --fail http://localhost:8000/health
```

This catches issues such as:

- Missing files.
- Incorrect startup command.
- Missing runtime dependencies.
- Incorrect ports.
- Invalid environment handling.

---

## Docker Image Health Endpoint

A backend application can expose:

```text
GET /health
```

or separate endpoints such as:

```text
/health/live
/health/ready
```

A readiness check may validate required dependencies.

For example:

```text
Application
    ↓
PostgreSQL
    ↓
Redis
```

The exact health-check depth should be chosen carefully to avoid turning health endpoints into expensive dependency probes.

---

## Deployment Strategy

Docker enables several deployment strategies.

### Rolling

```text
Old
Old
Old
Old

↓ gradually replace

New
New
New
New
```

### Blue-Green

```text
Blue  → Current
Green → New
```

Traffic switches after validation.

### Canary

```text
95% → Stable
5%  → New
```

The choice depends on:

- Risk.
- Infrastructure.
- Traffic.
- Rollback requirements.
- Cost.
- Application behavior.

---

## Zero-Downtime Docker Deployment

Zero downtime requires coordination between:

```text
Load Balancer
Container Lifecycle
Application Startup
Connection Draining
Database Schema
Deployment Strategy
```

The Docker image alone cannot guarantee zero downtime.

---

## Graceful Shutdown

Applications should handle termination signals appropriately.

This matters when:

- ECS replaces tasks.
- Kubernetes terminates pods.
- EC2 restarts containers.
- Rolling deployment removes instances.

The application should stop accepting new work and allow active requests to complete within the configured termination window.

---

## Docker and Celery

Celery workers often use the same application image:

```text
orders-api image
      ├── Web Process
      └── Celery Worker
```

The image can be reused while changing the startup command.

For example:

```bash
celery -A app worker --loglevel=INFO
```

This supports build-once/deploy-many while keeping worker and API code aligned.

---

## Docker and Kafka

Kafka consumers require additional deployment considerations:

- Consumer group state.
- Message compatibility.
- Consumer lag.
- Graceful shutdown.
- Schema evolution.
- Rolling deployment behavior.

A container deployment should not assume HTTP health checks alone prove the consumer is healthy.

---

## Database Compatibility

Container deployments must account for database schema compatibility.

Prefer:

```text
Expand Schema
 ↓
Deploy New Image
 ↓
Backfill
 ↓
Switch Behavior
 ↓
Contract Schema
```

This supports rollback better than destructive migrations tightly coupled to the new container version.

---

## Docker Image Promotion

Promotion should be based on artifact identity.

```text
ECR
 ├── Digest A
 ├── Digest B
 └── Digest C
```

Staging:

```text
Digest B
```

Production:

```text
Digest B
```

Do not rebuild:

```text
Source
 ↓
Production Build
```

after staging validation.

---

## Environment Configuration

The image should remain environment-neutral.

Avoid:

```text
orders-api-staging-image
orders-api-production-image
```

Prefer:

```text
orders-api@sha256:...
```

with environment-specific runtime configuration:

```text
Staging
 ├── DATABASE_URL
 ├── REDIS_URL
 └── API_CONFIG

Production
 ├── DATABASE_URL
 ├── REDIS_URL
 └── API_CONFIG
```

This preserves artifact immutability.

---

## Configuration vs Image

A useful separation is:

```text
Image
 ├── Application
 ├── Dependencies
 └── Runtime

Environment
 ├── Secrets
 ├── URLs
 ├── Feature Configuration
 └── Resource Configuration
```

Do not rebuild the image simply because a deployment environment has different configuration.

---

## Secret Management

Never bake secrets into:

- Dockerfiles.
- Docker image layers.
- Git repositories.
- Build arguments.
- Application source.

Prefer:

```text
AWS Secrets Manager
AWS Systems Manager Parameter Store
GitHub Environments
Runtime Secret Injection
```

The specific mechanism depends on the deployment platform.

---

## Docker Security

Production images should:

- Use trusted base images.
- Pin important dependencies.
- Minimize installed packages.
- Avoid unnecessary shells/tools.
- Run as non-root where practical.
- Scan images.
- Generate SBOMs.
- Track provenance.
- Avoid secrets in layers.
- Use minimal build contexts.

Example:

```dockerfile
RUN useradd --create-home appuser
USER appuser
```

Running as non-root reduces the impact of certain container compromises.

---

## Base Image Strategy

Possible base images include:

```text
python:3.12
python:3.12-slim
python:3.12-alpine
```

The choice should consider:

- Compatibility.
- Native dependencies.
- Image size.
- Security.
- Build complexity.
- Operational support.

A smaller image is not automatically a better production image if it introduces significant compatibility or maintenance problems.

---

## Image Update Strategy

Base images should be updated regularly.

A controlled lifecycle is:

```text
Base Image Update
 ↓
Build
 ↓
Test
 ↓
Scan
 ↓
Staging
 ↓
Production
```

Avoid automatically updating production images without validation.

---

## Supply Chain Architecture

Docker CI/CD has a supply chain:

```text
Base Image
 ↓
OS Packages
 ↓
Python Dependencies
 ↓
Application Source
 ↓
Dockerfile
 ↓
Buildx
 ↓
Image
 ↓
Registry
 ↓
Runtime
```

Each layer introduces potential supply-chain risk.

Controls should include:

- Trusted base images.
- Dependency scanning.
- Lock files.
- SBOM.
- Provenance.
- Image signing where appropriate.
- Registry controls.

---

## Python Dependency Reproducibility

A Python container should use a controlled dependency strategy.

For example:

```text
requirements.txt
requirements.lock
poetry.lock
uv.lock
```

The selected mechanism should produce deterministic dependency resolution where practical.

Avoid uncontrolled installation such as:

```dockerfile
RUN pip install django
```

because the resulting image can change without a source-code change.

---

## Docker and Lock Files

Dependency files should be copied before application source where possible:

```dockerfile
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
```

This improves cache reuse.

A dependency change invalidates the dependency layer.

A source-only change can reuse it.

---

## CI Pipeline with Docker Buildx

```yaml
name: Docker CI

on:
  pull_request:

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest

  docker:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build image
        uses: docker/build-push-action@v6
        with:
          context: .
          load: true
          tags: orders-api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Smoke test image
        run: |
          docker run -d \
            --name orders-api \
            -p 8000:8000 \
            orders-api:${{ github.sha }}

          sleep 5
          curl --fail http://localhost:8000/health
```

The exact readiness mechanism should be more robust than a fixed sleep for production-quality test infrastructure.

---

## Production Build and Publish Workflow

```yaml
name: Build and Publish

on:
  push:
    branches:
      - main

permissions:
  contents: read
  id-token: write

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: orders-api

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: ${{ vars.AWS_CI_ROLE }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to ECR
        id: ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Set up Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ${{ steps.ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

Production deployments should subsequently resolve the resulting immutable image identity.

---

## Build Output and Job Outputs

A Docker build workflow can expose image metadata.

Example:

```yaml
- name: Build image
  id: build
  run: |
    IMAGE="${REGISTRY}/${REPOSITORY}:${GITHUB_SHA}"
    echo "image=$IMAGE" >> "$GITHUB_OUTPUT"
```

Job output:

```yaml
jobs:
  build:
    outputs:
      image: ${{ steps.build.outputs.image }}
```

The caller can consume it:

```yaml
jobs:
  deploy:
    needs: build
    uses: organization/platform/.github/workflows/deploy.yml@v1
    with:
      image: ${{ needs.build.outputs.image }}
```

For production, passing the digest is stronger than passing only a tag.

---

## Reusable Docker Workflow

A platform team can centralize Docker construction:

```yaml
name: Reusable Docker Build

on:
  workflow_call:
    inputs:
      image-name:
        required: true
        type: string

      push:
        required: false
        type: boolean
        default: false

    outputs:
      image:
        description: "Built image"
        value: ${{ jobs.build.outputs.image }}
```

This enables:

```text
Service A
Service B
Service C
       ↓
Reusable Docker Workflow
```

without duplicating Buildx, cache, metadata, and registry logic.

---

## Docker Workflow and Composite Actions

Use a reusable workflow when Docker CI requires multiple jobs:

```text
Test
 ↓
Build
 ↓
Scan
 ↓
Publish
```

Use a composite action for a focused operation:

```text
Setup Docker Metadata
```

The distinction remains:

```text
Reusable Workflow
    = pipeline orchestration

Composite Action
    = reusable step group
```

---

## Monorepo Docker Architecture

For a monorepo:

```text
services/
 ├── orders/
 │    └── Dockerfile
 ├── payments/
 │    └── Dockerfile
 └── users/
      └── Dockerfile
```

A planning job can detect changed services:

```text
Commit
 ↓
Change Detection
 ↓
orders
payments
 ↓
Dynamic Matrix
 ↓
Parallel Docker Builds
```

This prevents rebuilding unrelated services.

---

## Docker Matrix Builds

A matrix can test multiple combinations:

```yaml
strategy:
  matrix:
    python:
      - "3.11"
      - "3.12"
```

For Docker:

```text
Python 3.11 → Image
Python 3.12 → Image
```

The matrix should have a clear compatibility objective.

Do not create large image matrices merely because the platform supports them.

---

## Multi-Architecture Build

Example:

```yaml
- name: Build multi-platform image
  uses: docker/build-push-action@v6
  with:
    context: .
    platforms: linux/amd64,linux/arm64
    push: true
    tags: ${{ steps.meta.outputs.tags }}
```

Consider:

- Native dependencies.
- CPU architecture.
- Build duration.
- Runner capabilities.
- Test coverage for each architecture.

---

## Docker Build Performance

Optimize builds using:

- Correct layer ordering.
- `.dockerignore`.
- BuildKit.
- Buildx.
- Dependency caching.
- Multi-stage builds.
- Efficient build contexts.
- Reusable base images.

A common optimization is:

```text
Stable Dependencies
        ↓
Cached Layer
        ↓
Frequently Changing Application Code
```

---

## Docker Build Cost

Build cost increases with:

- Large contexts.
- Large images.
- Poor cache utilization.
- Multi-platform builds.
- Excessive matrix combinations.
- Repeated dependency installation.

Monitor:

```text
Build Duration
Cache Hit Rate
Runner Minutes
Image Size
Registry Storage
```

---

## Registry Storage Management

Images accumulate over time:

```text
Commit A
Commit B
Commit C
...
Commit N
```

ECR lifecycle policies or equivalent registry controls should remove obsolete artifacts while retaining:

- Recent releases.
- Production rollback versions.
- Compliance-required artifacts.

Do not delete rollback artifacts immediately after deployment.

---

## Deployment Rollback

A Docker rollback should select a known-good artifact.

```text
Current
  ↓
Failure
  ↓
Known-Good Digest
  ↓
Redeploy
```

Example:

```text
Production
    ↓
orders-api@sha256:new
    ↓
Failure
    ↓
orders-api@sha256:known-good
```

The rollback should not rebuild the previous source version unless there is no viable immutable artifact.

---

## Automated Rollback

Automated rollback can be triggered by:

- Health-check failure.
- Deployment circuit breaker.
- Error-rate threshold.
- Availability failure.

However, automated rollback can create loops:

```text
Deploy
 ↓
Rollback
 ↓
Redeploy
 ↓
Rollback
```

Use bounded retries and clear rollback criteria.

---

## Monitoring After Deployment

A successful deployment command does not prove application health.

Monitor:

```text
HTTP Error Rate
Latency
CPU
Memory
Container Restarts
Database Connections
Queue Depth
Kafka Consumer Lag
```

For Django/FastAPI services, also consider:

- Request throughput.
- Dependency failures.
- Background task failures.
- Database errors.

---

## Deployment Health Validation

A deployment pipeline can validate:

```text
Container Running
        ↓
Readiness
        ↓
HTTP Health
        ↓
Application Smoke Test
        ↓
Metrics
        ↓
Deployment Complete
```

For Kubernetes, readiness and liveness semantics should be designed separately.

For ECS, task and target-group health should both be considered.

---

## Docker CI/CD Failure Domains

Common failure domains include:

```text
Source
Dockerfile
Build Context
Dependencies
Buildx
Cache
Registry
Authentication
Image
Deployment
Runtime
Networking
Database
Observability
```

Troubleshoot one domain at a time.

---

## Docker Build Failure

### Symptom

`docker build` fails.

### Possible Causes

- Invalid Dockerfile.
- Missing file.
- Dependency failure.
- Network failure.
- Native dependency compilation.
- Incorrect build context.

### Checks

```bash
docker build --progress=plain .
```

Inspect:

- Failing layer.
- Base image.
- Dependency resolution.
- Build context.

### Prevention

- Pin important dependencies.
- Keep Dockerfiles deterministic.
- Use appropriate base images.
- Maintain a small build context.

---

## Cache Failure

### Symptom

Builds are unexpectedly slow.

### Possible Causes

- Cache miss.
- Incorrect cache key.
- Dockerfile layer invalidation.
- Changed dependency file.
- Cache scope mismatch.

### Isolation

Build without cache:

```bash
docker build --no-cache .
```

Then compare build behavior.

### Prevention

Optimize Dockerfile layer ordering and use an appropriate BuildKit cache strategy.

---

## Registry Failure

### Symptom

Image cannot be pushed.

### Possible Causes

- Authentication.
- IAM permission.
- Wrong repository.
- Wrong region.
- Registry unavailable.
- Image size or configuration issue.

### AWS Checks

```bash
aws sts get-caller-identity
```

```bash
aws ecr describe-repositories \
  --repository-names orders-api \
  --region us-east-1
```

### Prevention

- Validate identity before push.
- Restrict IAM permissions.
- Use OIDC.
- Keep repository configuration consistent.

---

## ECR Authentication Failure

Trace:

```text
GitHub Job
 ↓
OIDC
 ↓
STS
 ↓
IAM Role
 ↓
ECR Authorization
 ↓
Docker Login
```

Check:

```yaml
permissions:
  id-token: write
  contents: read
```

Then validate:

```bash
aws sts get-caller-identity
```

The IAM trust policy must match the GitHub OIDC claims.

---

## Docker Runtime Failure

### Symptom

Image builds successfully but container exits immediately.

### Possible Causes

- Incorrect `CMD`.
- Missing dependency.
- Missing environment variable.
- Incorrect working directory.
- Application startup failure.
- Port mismatch.

### Checks

```bash
docker logs orders-api
```

```bash
docker inspect orders-api
```

Run interactively when appropriate:

```bash
docker run --rm -it orders-api:debug /bin/sh
```

---

## Container Networking Failure

### Symptom

Application cannot connect to PostgreSQL or Redis.

Check:

```text
Hostname
Port
Network
Credentials
DNS
Readiness
```

Do not assume:

```text
localhost
```

is correct for every container topology.

---

## Deployment Failure

### Symptom

New container image is published but deployment fails.

Possible causes:

- Invalid task definition.
- Image pull permission.
- Image architecture mismatch.
- Missing environment configuration.
- Health-check failure.
- Security group/network issue.
- Application startup failure.

The investigation should follow:

```text
Registry
 ↓
Runtime Identity
 ↓
Image Pull
 ↓
Container Start
 ↓
Health
 ↓
Application
 ↓
Dependencies
```

---

## Image Pull Failure

A runtime needs pull access.

For AWS:

```text
ECS Task Execution Role
       ↓
ECR
```

This should be distinct from:

```text
GitHub Actions Deployment Role
       ↓
ECR Push
```

Separating these identities reduces privilege.

---

## Security Failure Domains

Docker CI/CD security failures can occur through:

```text
Untrusted Source
 ↓
Workflow
 ↓
Build
 ↓
Dependency
 ↓
Image
 ↓
Registry
 ↓
Runtime
```

Controls should be applied at each boundary.

---

## Docker and Untrusted Pull Requests

Do not automatically execute untrusted pull request code with:

- Production credentials.
- AWS deployment roles.
- Persistent privileged runners.
- Docker socket access.
- Private network access.

A safer PR architecture is:

```text
Fork PR
 ↓
Read-only CI
 ↓
Isolated Runner
 ↓
No Production Credentials
```

Deployment should happen only from an appropriately trusted context.

---

## Docker Socket Security

Mounting:

```text
/var/run/docker.sock
```

into a container gives the container powerful access to the Docker daemon.

This can effectively become host-level control depending on the environment.

Avoid granting Docker socket access to untrusted workloads.

For CI workloads that need Docker, evaluate:

- Hosted runners.
- Ephemeral runners.
- BuildKit.
- Rootless approaches.
- Isolated builders.

---

## Self-Hosted Docker Runners

Self-hosted runners running Docker builds require careful isolation.

Consider:

- Ephemeral lifecycle.
- Docker daemon security.
- Workspace cleanup.
- Network access.
- Registry credentials.
- Runner permissions.
- Image cache contamination.

Persistent runners can accidentally retain artifacts from previous jobs.

---

## Docker and Secrets

A secure pipeline should have:

```text
CI Secret
 ↓
Authentication
 ↓
Build / Deployment
 ↓
Runtime Secret Store
```

not:

```text
Secret
 ↓
Dockerfile
 ↓
Image Layer
 ↓
Registry
```

If a secret enters the image, assume it may need rotation.

---

## Artifact Integrity

Before deployment, establish:

```text
Image Exists
+
Digest Matches
+
Expected Repository
+
Expected Build
+
Expected Provenance
+
Required Security Checks Passed
```

Only then should the deployment proceed.

---

## Enterprise Docker Architecture

```mermaid
flowchart TB
    DEV[Developer]
    GIT[Git Repository]

    subgraph CI["GitHub Actions"]
        TEST[Lint / Unit / Integration]
        BUILD[Buildx]
        SCAN[Security Scan]
        SBOM[SBOM / Provenance]
    end

    REG[ECR / Container Registry]

    subgraph ENV["Environments"]
        STG[Staging]
        PROD[Production]
    end

    subgraph RUNTIME["Runtime"]
        ECS[ECS / Kubernetes / EC2]
        APP[Django / FastAPI]
        DB[(PostgreSQL)]
        REDIS[(Redis)]
        KAFKA[Kafka]
    end

    DEV --> GIT
    GIT --> TEST
    TEST --> BUILD
    BUILD --> SCAN
    SCAN --> SBOM
    SBOM --> REG
    REG --> STG
    STG --> PROD
    PROD --> ECS
    ECS --> APP
    APP --> DB
    APP --> REDIS
    APP --> KAFKA
```

---

## Enterprise Reusable Docker Platform

For many repositories:

```text
                  Platform Repository
                         │
              Reusable Docker Workflow
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
    Orders API      Payments API      Users API
        │                │                │
        └────────────────┼────────────────┘
                         ↓
                    ECR Registry
```

The reusable workflow can standardize:

- Buildx.
- Caching.
- Metadata.
- Security scanning.
- SBOM.
- Provenance.
- Registry authentication.
- Image outputs.

---

## Docker CI/CD with Reusable Workflows

Caller:

```yaml
jobs:
  build:
    uses: organization/platform/.github/workflows/docker-build.yml@v1
    with:
      image-name: orders-api
      push: true

  deploy:
    needs: build
    uses: organization/platform/.github/workflows/aws-deploy.yml@v1
    with:
      environment: staging
      image-digest: ${{ needs.build.outputs.image-digest }}
```

This keeps application repositories focused on service intent.

---

## Docker CI/CD and Enterprise Governance

A platform team can define standards for:

```text
Base Images
Dockerfile Security
Image Scanning
SBOM
Provenance
Tagging
Registry
Retention
Deployment Identity
Rollback
```

Application teams remain responsible for their Dockerfiles and service behavior.

---

## High Availability

Docker itself does not provide application high availability.

HA requires:

```text
Multiple Containers
+
Load Balancing
+
Health Checks
+
Failure Detection
+
Replacement
+
Sufficient Capacity
```

For ECS:

```text
ALB
 ↓
Multiple Tasks
```

For Kubernetes:

```text
Service
 ↓
Multiple Pods
```

For EC2-based Docker:

```text
Load Balancer
 ↓
Multiple Instances
 ↓
Containers
```

---

## Disaster Recovery

A Docker-based recovery plan should preserve:

```text
Docker Image
Image Digest
Dockerfile
Source Commit
Deployment Configuration
Infrastructure Code
Runtime Configuration
Database Recovery Strategy
```

A rollback is not the same as disaster recovery.

Rollback handles application release failure.

DR handles loss or major unavailability of infrastructure or data.

---

## Cost Optimization

Docker CI/CD cost can be reduced through:

- Layer caching.
- Efficient Dockerfiles.
- Smaller build contexts.
- Selective builds.
- Dynamic matrices.
- Multi-stage builds.
- Image retention policies.
- Appropriate runner types.
- Build once/deploy many.

Do not optimize solely for image size if it significantly increases build complexity or operational risk.

---

## Common Docker CI/CD Mistakes

### Rebuilding for Every Environment

This weakens artifact immutability.

### Using `latest` for Production

The meaning can change without a workflow change.

### Baking Secrets Into Images

Secrets can persist in image layers.

### Copying the Entire Repository

This increases build context and may leak unnecessary files.

### Ignoring `.dockerignore`

Large or sensitive files can enter the build context.

### Running as Root Unnecessarily

This increases the impact of some container compromises.

### Treating Cache as an Artifact

Cache accelerates builds; it is not the release artifact.

### Ignoring Image Architecture

An ARM image may not run on an x86 runtime.

### Testing Only the Docker Build

A successful build does not prove the container starts correctly.

### Ignoring Graceful Shutdown

Rolling deployments can terminate active requests or background tasks.

### Giving Runtime Containers Push Permissions

Runtime identities should normally pull images rather than publish them.

---

## Production Docker CI/CD Checklist

### Build

- [ ] Dockerfile is deterministic.
- [ ] Multi-stage build is used where useful.
- [ ] `.dockerignore` is configured.
- [ ] Dependencies are controlled.
- [ ] Build context is minimal.
- [ ] Buildx is used where appropriate.

### Security

- [ ] No secrets are baked into images.
- [ ] Images use trusted base images.
- [ ] Containers run as non-root where practical.
- [ ] Images are scanned.
- [ ] SBOM/provenance requirements are defined.
- [ ] Untrusted PRs cannot access production credentials.

### Registry

- [ ] Images are stored in an approved registry.
- [ ] Image identity is traceable.
- [ ] Production uses immutable image references.
- [ ] Registry permissions are least-privilege.
- [ ] Retention policies preserve rollback artifacts.

### CI

- [ ] Unit tests run before release.
- [ ] Integration tests cover required dependencies.
- [ ] Docker image smoke tests exist.
- [ ] Build caching is configured appropriately.
- [ ] Build failures are observable.

### CD

- [ ] Build and deployment are separated.
- [ ] The same image is promoted between environments.
- [ ] Environment protection is configured.
- [ ] Deployment concurrency is controlled.
- [ ] Health validation exists.
- [ ] Rollback uses a known-good image.

### Operations

- [ ] Container startup is observable.
- [ ] Application health is monitored.
- [ ] Runtime dependencies are monitored.
- [ ] Image metadata supports traceability.
- [ ] Runner capacity is monitored.
- [ ] Disaster recovery procedures are documented.

---

## Senior Design Principles

### Treat the Image as the Release Artifact

The Docker image should represent the exact software being promoted.

### Separate Build From Deployment

Build systems create artifacts.

Deployment systems consume artifacts.

### Prefer Immutable Identity

Use image digests for deployment-critical references.

### Keep Configuration Outside the Image

Environment-specific values belong in the runtime environment.

### Design for Rollback

A deployment is incomplete until the organization knows how to restore a known-good image.

### Secure Every Boundary

The important boundaries are:

```text
Source
 ↓
Workflow
 ↓
Builder
 ↓
Image
 ↓
Registry
 ↓
Runtime
```

### Optimize for Reproducibility

The same source and controlled dependencies should produce predictable artifacts.

### Make Container Health Observable

A successful `docker push` does not mean the application is healthy.

### Separate Build and Runtime Permissions

The identity that pushes an image should not automatically become the identity that runs the application.

---

## Senior Interview Scenarios

### Design a Docker Pipeline for a FastAPI Service

Discuss:

```text
Pull Request
 ↓
Lint
 ↓
Unit Tests
 ↓
PostgreSQL / Redis Integration Tests
 ↓
Docker Build
 ↓
Image Scan
 ↓
ECR
 ↓
Staging
 ↓
Production
```

Explain how the same image reaches every environment.

### How Would You Prevent Environment-Specific Rebuilds?

Use:

```text
Build Once
 ↓
Image Digest
 ↓
Promote
```

Environment configuration remains outside the image.

### How Would You Secure Docker Builds?

Discuss:

- Trusted base images.
- Dependency locking.
- Build secrets.
- Least-privilege credentials.
- SBOM.
- Provenance.
- Image scanning.
- Runner isolation.

### Production Image Works in Staging but Fails in Production

Investigate:

```text
Same Digest?
Same Architecture?
Same Environment Configuration?
Same Runtime Permissions?
Same Network?
Same Secrets?
Same Dependencies?
```

If staging and production use different image digests, the first assumption of artifact parity is already broken.

### How Would You Deploy Without Downtime?

Discuss:

- Rolling.
- Blue-green.
- Canary.
- Health checks.
- Graceful shutdown.
- Connection draining.
- Database compatibility.
- Deployment concurrency.
- Rollback.

### How Would You Build for AMD64 and ARM64?

Use Buildx:

```text
Buildx
 ├── linux/amd64
 └── linux/arm64
```

Then publish a multi-platform image manifest.

Discuss native dependencies and test coverage.

### How Would You Handle a Compromised Base Image?

Discuss:

```text
Detect
 ↓
Identify Affected Images
 ↓
Block Promotion
 ↓
Replace Base Image
 ↓
Rebuild
 ↓
Scan
 ↓
Publish
 ↓
Redeploy
```

Then determine whether previously deployed artifacts require replacement.

### How Would You Troubleshoot a Container That Builds but Immediately Exits?

Start with:

```bash
docker logs <container>
```

Then inspect:

```bash
docker inspect <container>
```

Check:

```text
CMD
ENTRYPOINT
Environment
Working Directory
Dependencies
Ports
Filesystem
Architecture
```

---

## Production Reference Architecture

A mature Docker CI/CD platform can follow:

```text
Developer
    ↓
Pull Request
    ↓
GitHub Actions
    ├── Lint
    ├── Unit Tests
    ├── Integration Tests
    ├── Security
    └── Matrix
            ↓
        Docker Buildx
            ↓
      Image Scan / SBOM
            ↓
      Immutable Image
            ↓
           ECR
            ↓
         Staging
            ↓
      Health Validation
            ↓
      Production Approval
            ↓
        Production
            ↓
        Monitoring
            ↓
         Rollback
```

The resulting system has a clear separation of responsibilities:

```text
Source Repository
    = source of truth

GitHub Actions
    = orchestration

Buildx
    = image construction

ECR
    = artifact storage

ECS / Kubernetes / EC2
    = runtime

Monitoring
    = runtime validation

Rollback
    = recovery
```

## Key Takeaways

- A production Docker CI/CD system should **build the image once, assign immutable identity, publish it to a trusted registry, and promote that same artifact across environments**.
- Docker CI should combine **Buildx, efficient layer caching, deterministic dependencies, image scanning, SBOM/provenance, and secure registry authentication** rather than treating `docker build` as the entire pipeline.
- Environment-specific configuration belongs outside the image, while **secrets, runtime settings, database compatibility, health checks, and deployment strategy** must be handled at the deployment layer.
- Enterprise Docker pipelines require strong security boundaries across **source, workflows, builders, images, registries, runners, and runtime identities**, with special care around untrusted pull requests and Docker daemon access.
- A senior production architecture connects **CI validation → immutable Docker image → ECR/registry → staging → approval → production → monitoring → rollback**, with reproducibility and artifact traceability maintained throughout.