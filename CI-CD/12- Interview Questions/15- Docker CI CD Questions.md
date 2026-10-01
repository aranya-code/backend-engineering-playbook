# 15- Docker CI CD Questions

## Overview

Docker is a core execution and packaging layer in modern CI/CD systems. In production pipelines, it is not enough to know how to write a `Dockerfile` or run `docker build`.

A senior backend engineer should understand the complete lifecycle:

```text
Source Code
    ↓
CI Validation
    ↓
Docker Build
    ↓
BuildKit / Buildx
    ↓
Image
    ↓
Security Scan
    ↓
SBOM / Provenance
    ↓
Container Registry
    ↓
Staging
    ↓
Approval
    ↓
Production
    ↓
Health Validation
    ↓
Rollback
```

The important engineering properties are:

- Reproducible builds
- Immutable artifacts
- Fast and reliable builds
- Secure build environments
- Efficient layer caching
- Traceable image provenance
- Least-privilege registry access
- Build-once, promote-many deployment
- Safe rollback
- Environment isolation

This document focuses on Docker CI/CD interview questions from fundamentals through senior production architecture.

---

## Docker in CI/CD

Docker provides a standardized artifact and runtime boundary between development, CI, staging, and production.

A typical backend pipeline looks like:

```text
Developer
   ↓
Git Push / Pull Request
   ↓
GitHub Actions
   ├── Lint
   ├── Unit Tests
   ├── Integration Tests
   ├── Security Scan
   └── Docker Build
           ↓
       Image
           ↓
        ECR
           ↓
       Staging
           ↓
       Production
```

Docker solves packaging and runtime consistency, but it does not solve:

- CI orchestration
- Authentication
- Deployment strategy
- Secrets management
- Application observability
- Database migrations
- Rollback policy
- Infrastructure management

Those concerns must be designed around the container lifecycle.

---

## Docker Image vs Container

| Concept | Meaning |
|---|---|
| Dockerfile | Instructions for creating an image |
| Image | Immutable package containing application/runtime dependencies |
| Container | Runtime instance created from an image |
| Registry | Stores and distributes images |
| Tag | Human-readable image reference |
| Digest | Content-addressed immutable image identifier |
| Build context | Files available to the Docker build |
| Layer | Filesystem change represented by an image layer |

A CI pipeline normally creates an **image**.

A deployment platform creates **containers** from that image.

---

## Dockerfile and CI

A production Dockerfile should be designed for:

- Reproducibility
- Small image size
- Fast rebuilds
- Security
- Layer caching
- Minimal runtime dependencies
- Clear runtime behavior

Example:

```dockerfile
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

For more complex applications, multi-stage builds can separate build dependencies from runtime dependencies.

---

## Why Multi-Stage Builds Matter

A build environment may require:

```text
gcc
build-essential
headers
compilers
development libraries
```

The runtime container often does not.

A multi-stage build can separate them:

```text
Builder Image
    ↓
Compile / Install
    ↓
Runtime Artifacts
    ↓
Minimal Runtime Image
```

Example:

```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip wheel \
    --no-cache-dir \
    --wheel-dir /wheels \
    -r requirements.txt


FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /wheels /wheels

RUN pip install \
    --no-cache-dir \
    /wheels/* \
    && rm -rf /wheels

COPY . .

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

This can reduce the runtime image's attack surface and size.

---

## Build Context

The Docker build context determines which files are available to the build.

Avoid sending unnecessary content:

```text
.git/
.venv/
__pycache__/
node_modules/
coverage/
local secrets
large datasets
```

Use `.dockerignore`.

Example:

```dockerignore
.git
.github
.venv
__pycache__
*.pyc
.pytest_cache
.coverage
htmlcov
.env
.env.*
node_modules
dist
build
```

A smaller context can improve build performance and reduce accidental secret inclusion.

---

## Docker Build Context Security

A common mistake is assuming:

```text
.env
```

is safe because it is not explicitly copied.

If the file exists inside the build context, it can potentially become accessible to build steps.

Do not place secrets in the build context.

Prefer:

```text
OIDC
+
Secret Manager
+
BuildKit secret mechanisms
```

depending on the requirement.

---

## Docker Build in GitHub Actions

A typical production workflow uses Docker Buildx.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    permissions:
      contents: read

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          push: false
          tags: example-api:${{ github.sha }}
```

The image can later be pushed to a registry.

---

## Why Buildx?

Buildx provides a modern interface to BuildKit and supports features such as:

- Efficient builds
- Advanced caching
- Multi-platform builds
- Build secrets
- Build outputs
- Build provenance
- Parallel build execution

A senior engineer should understand Buildx as a build orchestration interface rather than merely another Docker command.

---

## BuildKit

BuildKit is Docker's modern build engine.

Conceptually:

```text
Dockerfile
    ↓
BuildKit
    ├── Dependency graph
    ├── Parallel execution
    ├── Cache reuse
    ├── Secret handling
    └── Build outputs
```

This improves build performance and enables more advanced build features.

---

## Docker Layer Caching

Docker builds are composed of layers.

For example:

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
```

If application source changes but `requirements.txt` does not, the dependency installation layer may remain reusable.

This is why stable, expensive operations should generally appear before frequently changing source files.

---

## Bad Layer Ordering

```dockerfile
COPY . .

RUN pip install -r requirements.txt
```

Every source change can invalidate the dependency installation layer.

A better structure is:

```dockerfile
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
```

This can significantly improve CI build times.

---

## GitHub Actions Docker Cache

A BuildKit cache can be persisted using GitHub Actions cache storage.

Example:

```yaml
- name: Build image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: false
    tags: example-api:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

Caching should be treated as an optimization, not as an artifact source of truth.

---

## Cache vs Artifact

| Property | Docker Build Cache | Artifact |
|---|---|---|
| Purpose | Speed up builds | Preserve/promote output |
| Source of truth | No | Yes |
| Reproducibility dependency | Cache-independent build required | Artifact itself |
| Safe to delete | Usually yes | Depends |
| Deployment object | No | Yes |
| Example | BuildKit layers | Docker image |

Never design production deployment around the assumption that a build cache will always exist.

---

## Registry Cache

For larger organizations, registry-based BuildKit caching may be useful.

Conceptually:

```text
GitHub Runner
    ↓
BuildKit
    ↓
ECR cache
```

This can be useful when:

- Multiple runners build the same project.
- Build frequency is high.
- CI runs are distributed.
- Local runner cache is unavailable.

Cache permissions and isolation must still be considered.

---

## Docker Image Tags

Common tagging strategies include:

```text
latest
1.4.0
1.4
main
staging
<commit-sha>
```

Each has different operational properties.

For CI/CD, a commit-based tag is highly useful:

```text
orders-api:8f32b6c
```

because it maps an image to a source revision.

---

## Mutable vs Immutable Tags

A mutable tag:

```text
orders-api:latest
```

can point to different image contents over time.

An immutable reference should identify one artifact.

For stronger deployment guarantees, use:

```text
orders-api@sha256:<digest>
```

for promotion.

---

## Image Digest

A Docker image digest identifies image content.

Example:

```text
123456789012.dkr.ecr.ap-south-1.amazonaws.com/orders-api@sha256:abc123...
```

This is stronger for deployment identity than relying only on:

```text
latest
```

or another mutable tag.

---

## Build Once, Promote Many

A production deployment should preferably follow:

```text
Build
 ↓
Image
 ↓
Security Scan
 ↓
ECR
 ↓
Staging
 ↓
Approval
 ↓
Production
```

The same image should be promoted.

Avoid:

```text
Build staging image
 ↓
Deploy staging

Build production image
 ↓
Deploy production
```

because the two builds can differ.

---

## Why Rebuilding Is Dangerous

Between two builds, the following may change:

- Base image
- OS packages
- Python dependencies
- npm packages
- External package repositories
- Build tools
- Build environment
- Source state

Therefore:

```text
Same source commit
```

does not necessarily guarantee:

```text
Same binary/image
```

unless reproducibility is deliberately designed.

---

## Build Once, Promote Many Architecture

```mermaid
flowchart LR
    SOURCE[Git Commit] --> CI[CI Validation]
    CI --> BUILD[Docker Build]
    BUILD --> SCAN[Security Scan]
    SCAN --> IMAGE[Immutable Image]
    IMAGE --> ECR[ECR]
    ECR --> STAGE[Staging]
    STAGE --> APPROVAL[Production Approval]
    APPROVAL --> PROD[Production]
    PROD --> HEALTH[Health Validation]
    HEALTH --> MONITOR[Monitoring]
```

The image identity remains constant throughout promotion.

---

## ECR Integration

A typical AWS pipeline is:

```text
GitHub Actions
    ↓
GitHub OIDC
    ↓
AWS STS
    ↓
IAM Role
    ↓
ECR
```

Example:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ vars.AWS_ROLE_ARN }}
    aws-region: ${{ vars.AWS_REGION }}

- name: Login to Amazon ECR
  id: login-ecr
  uses: aws-actions/amazon-ecr-login@v2

- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: |
      ${{ steps.login-ecr.outputs.registry }}/orders-api:${{ github.sha }}
```

---

## Why OIDC Is Preferred

Avoid:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

as long-lived GitHub secrets when OIDC can provide the required authentication model.

Use:

```text
GitHub OIDC
    ↓
STS
    ↓
Temporary credentials
```

The deployment role should still follow least privilege.

---

## Docker Registry Authentication

A registry authentication flow is:

```text
CI Runner
   ↓
Authentication
   ↓
Registry
   ↓
Push Image
```

Authentication should not be embedded into the Docker image.

For AWS:

```text
GitHub
 ↓
OIDC
 ↓
STS
 ↓
ECR
```

For other registries, use the registry's supported credential or federation model.

---

## Image Vulnerability Scanning

A production pipeline should include vulnerability scanning.

Conceptually:

```text
Docker Build
    ↓
Image
    ↓
Vulnerability Scanner
    ↓
Policy
    ├── Pass
    └── Fail
```

Scanning can identify:

- OS package vulnerabilities
- Language dependency vulnerabilities
- Known CVEs
- Vulnerable base images

Scanning does not guarantee that an image is secure.

---

## Vulnerability Policy

A production organization should define:

```text
Severity threshold
+
Exception process
+
Ownership
+
Remediation SLA
+
Re-scan policy
```

Do not blindly fail every build for every vulnerability without understanding exploitability and operational impact.

Likewise, do not ignore critical vulnerabilities indefinitely.

---

## Base Image Strategy

Example:

```dockerfile
FROM python:3.12-slim
```

Base image decisions affect:

- Security
- Image size
- Compatibility
- Patch availability
- Build speed
- Operational support

Pinning only a broad image family may still allow different underlying image contents over time.

Production teams should define a base-image update strategy.

---

## Dependency Pinning

For Python:

```text
requirements.txt
poetry.lock
uv.lock
```

or another appropriate lock mechanism can make dependency resolution more reproducible.

Docker CI should not rely on unrestricted floating dependencies for production builds.

---

## Docker and Python CI

A production Python pipeline can separate application testing from image construction:

```text
Checkout
 ↓
Python Setup
 ↓
Lint
 ↓
Unit Tests
 ↓
Integration Tests
 ↓
Security Scan
 ↓
Docker Build
 ↓
Image Scan
 ↓
Push
```

This avoids discovering basic Python failures only after an expensive image build.

---

## Django Docker CI

For Django:

```text
Lint
 ↓
pytest
 ↓
PostgreSQL service
 ↓
Redis service
 ↓
Migration validation
 ↓
Docker build
 ↓
Image scan
```

The Docker image should contain the production application runtime, not the CI test environment unnecessarily.

---

## FastAPI Docker CI

For FastAPI:

```text
Lint
 ↓
Unit Tests
 ↓
API Tests
 ↓
PostgreSQL
 ↓
Redis
 ↓
Docker Build
 ↓
Image Scan
 ↓
ECR
```

The same immutable image can then be promoted across environments.

---

## Docker Compose in CI

Docker Compose can be useful for integration testing multiple dependent services.

Example architecture:

```text
FastAPI
 ├── PostgreSQL
 ├── Redis
 └── Kafka
```

Compose is particularly useful when local development and CI need similar multi-container integration environments.

However, GitHub Actions service containers can be simpler for straightforward CI dependencies.

---

## Job Container vs Service Container

| Concept | Purpose |
|---|---|
| Job container | Runs CI steps inside a container |
| Service container | Provides a dependency to the job |
| Docker build container | Creates an image |
| Production container | Runs the deployed application |

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12

    services:
      postgres:
        image: postgres:16
```

This gives:

```text
Job Container
    ↓
pytest
    ↓
PostgreSQL Service
```

---

## Container Networking in GitHub Actions

Networking depends on whether the job itself runs inside a container.

A common mistake is blindly using:

```text
localhost
```

for every service.

When the job and service containers share the appropriate Docker network, the service is commonly accessed using its service label.

Example:

```yaml
services:
  postgres:
    image: postgres:16
```

Application configuration can use:

```text
postgres
```

as the hostname rather than assuming `localhost`.

---

## PostgreSQL Integration Testing

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: test-password
          POSTGRES_DB: app_test
        options: >-
          --health-cmd "pg_isready -U app -d app_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://app:test-password@postgres:5432/app_test
        run: pytest
```

The health check reduces failures caused by trying to connect before PostgreSQL is ready.

---

## Redis Integration Testing

A Redis service can be added:

```yaml
services:
  postgres:
    image: postgres:16

  redis:
    image: redis:7
```

The application can use:

```text
redis://redis:6379/0
```

when the networking model makes the service hostname available.

---

## Kafka Integration Testing

Kafka introduces additional operational complexity:

- Broker startup time
- Listener configuration
- Network addresses
- Metadata discovery
- Client compatibility
- Resource requirements

Kafka should not be added to every CI job by default.

Use it for tests that actually require Kafka behavior.

---

## Health Checks

A container being started does not necessarily mean the application is ready.

Distinguish:

```text
Process started
```

from:

```text
Application ready
```

and:

```text
Dependency ready
```

Production pipelines should use health validation before promotion.

---

## Docker Health Validation

For an HTTP application:

```bash
curl --fail --silent --show-error \
  http://127.0.0.1:8000/health
```

A stronger health strategy can validate:

```text
Application
+
Database connectivity
+
Critical dependencies
```

while avoiding an overly expensive readiness endpoint.

---

## Container Exit Codes

CI should respect container exit codes.

Example:

```bash
docker run --rm example-api:test pytest
```

If pytest fails:

```text
pytest exit code != 0
    ↓
docker run exits non-zero
    ↓
GitHub Actions step fails
```

Do not hide failures with:

```bash
docker run ... || true
```

unless the failure is intentionally non-blocking.

---

## Docker Build Failures

Common causes include:

- Incorrect Dockerfile syntax
- Missing build context files
- Incorrect paths
- Dependency installation failures
- Network failures
- Base image problems
- Architecture mismatch
- Permission problems
- Cache corruption
- Registry authentication

Troubleshoot the build separately from deployment.

---

## Docker Build Debugging

Run locally:

```bash
docker build \
  --progress=plain \
  -t example-api:test .
```

Inspect:

```bash
docker images
docker history example-api:test
docker inspect example-api:test
```

The plain progress output is particularly useful for CI failures.

---

## Docker Context Debugging

Check:

```bash
docker build --no-cache -t example-api:test .
```

If a build succeeds with cache disabled, investigate cache validity and layer reuse.

If it fails both ways, investigate the Dockerfile, context, dependencies, or build environment.

---

## Registry Push Failures

### Symptom

Docker build succeeds but push fails.

### Possible Causes

- Authentication failure
- Incorrect repository
- Wrong AWS account
- Wrong region
- Missing ECR permissions
- Registry outage
- Image architecture mismatch

### Isolation

Verify:

```bash
aws sts get-caller-identity
```

Then verify repository existence:

```bash
aws ecr describe-repositories \
  --repository-names orders-api
```

---

## Docker Pull Failures

A deployment may fail because the runtime cannot pull the image.

Possible causes:

```text
Wrong image tag
Wrong digest
Registry permissions
Network connectivity
ECR repository policy
Expired credentials
Image does not exist
```

For ECS, distinguish:

```text
Task execution role
```

from:

```text
Task role
```

The execution role is relevant to operations such as pulling images and retrieving certain runtime configuration.

---

## Docker Image Size

Large images increase:

- Registry storage
- Network transfer
- Pull latency
- Deployment time
- Cold-start time

Reduce image size through:

- Slim runtime images
- Multi-stage builds
- `.dockerignore`
- Removing build tools
- Removing package caches
- Avoiding unnecessary files

Do not optimize image size at the expense of operational correctness or security.

---

## Docker Image Size vs Build Speed

These goals can conflict.

For example:

```text
Aggressive dependency minimization
```

may complicate builds.

A practical production target is:

```text
Small enough
+
Fast enough
+
Secure
+
Maintainable
```

rather than minimizing every byte.

---

## Multi-Platform Images

Buildx can build multiple architectures:

```text
linux/amd64
linux/arm64
```

Example:

```yaml
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    platforms: linux/amd64,linux/arm64
    tags: ${{ env.IMAGE }}
```

This is useful when workloads run on different CPU architectures.

---

## Multi-Architecture Risks

Native dependencies can behave differently across architectures.

Examples include:

- Python C extensions
- Database drivers
- System libraries
- Native binaries

Test the architectures you actually deploy.

Do not assume that a successful `amd64` build guarantees `arm64` compatibility.

---

## Docker Build Arguments

Build arguments can configure builds:

```dockerfile
ARG PYTHON_VERSION=3.12
```

But build arguments should not be treated as secure secret storage.

Do not pass secrets through:

```text
ARG
ENV
```

when they would become visible through image metadata or layers.

---

## BuildKit Secrets

When a build genuinely requires a secret, use supported BuildKit secret mechanisms rather than baking the secret into the image.

Conceptually:

```text
CI secret
    ↓
BuildKit secret mount
    ↓
Build step
    ↓
Secret unavailable in final image
```

The exact implementation should follow the supported Docker BuildKit interface.

---

## Dockerfile Secret Anti-Pattern

Avoid:

```dockerfile
ARG TOKEN

RUN curl \
  -H "Authorization: Bearer ${TOKEN}" \
  https://private.example.com/package
```

The secret may become exposed through build metadata, logs, cache behavior, or other build artifacts.

Use BuildKit's secret handling where necessary.

---

## Docker Socket Security

Mounting:

```text
/var/run/docker.sock
```

into a container effectively gives that container powerful access to the Docker daemon.

This can create a major security boundary violation.

Avoid exposing the host Docker socket to untrusted workloads.

---

## Docker-in-Docker

Docker-in-Docker can be useful for certain CI scenarios but introduces complexity around:

- Privileged containers
- Storage
- Networking
- Daemon lifecycle
- Security
- Performance

Prefer the simplest build architecture that meets the requirement.

Buildx with an appropriately isolated builder is often easier to reason about than unnecessarily nested Docker daemons.

---

## Self-Hosted Runner Security

Docker builds on self-hosted runners require additional scrutiny.

Consider:

```text
Persistent runner
+
Docker socket
+
Untrusted PR
```

This can create a path from repository code to the host.

For untrusted workloads, consider:

- GitHub-hosted runners
- Ephemeral runners
- Isolated runner groups
- Restricted network access
- Minimal permissions

---

## Docker on Ephemeral Runners

A strong architecture is:

```text
Provision runner
    ↓
Run job
    ↓
Build image
    ↓
Push artifact
    ↓
Destroy runner
```

This reduces persistence between jobs.

It does not remove the need for least privilege or secure build configuration.

---

## Docker and Untrusted Pull Requests

Avoid allowing arbitrary pull request code to:

```text
Access production AWS credentials
+
Access Docker socket
+
Access private network
+
Push trusted release artifacts
```

Separate:

```text
Untrusted validation
```

from:

```text
Trusted build and deployment
```

when the security model requires it.

---

## Docker Image Poisoning

An attacker may attempt to introduce malicious code into an image.

Controls include:

```text
Protected source
+
Trusted build workflow
+
Dependency controls
+
Image scanning
+
SBOM
+
Provenance
+
Attestation
+
Signing
+
Immutable promotion
```

The goal is to establish confidence in both:

```text
What was built
```

and:

```text
How it was built
```

---

## SBOM

A Software Bill of Materials describes components contained in an artifact.

For a Docker image, it can include:

```text
OS packages
Python packages
Native dependencies
Application dependencies
```

SBOMs support:

- Vulnerability analysis
- Incident response
- Compliance
- Dependency inventory

---

## Artifact Provenance

Provenance answers questions such as:

```text
Which source produced this image?
Which workflow built it?
Which repository?
Which revision?
Which build environment?
```

This complements image scanning.

---

## Image Signing

Image signing can establish that an artifact was produced or approved by a trusted workflow or organization.

A production promotion model can become:

```text
Image
 ↓
Verify provenance
 ↓
Verify signature
 ↓
Deploy
```

This provides stronger supply-chain controls than relying solely on image tags.

---

## Docker CI/CD Security Model

```mermaid
flowchart TD
    SOURCE[Protected Source] --> WORKFLOW[Trusted Workflow]
    WORKFLOW --> BUILD[Isolated Docker Build]
    BUILD --> SCAN[Vulnerability Scan]
    SCAN --> SBOM[SBOM]
    SBOM --> PROV[Provenance / Attestation]
    PROV --> SIGN[Artifact Verification]
    SIGN --> ECR[Immutable Registry]
    ECR --> STAGE[Staging]
    STAGE --> APPROVAL[Approval]
    APPROVAL --> PROD[Production]
```

Each stage creates a separate security boundary.

---

## Docker and Kubernetes

A Kubernetes deployment should preferably reference an immutable image.

Example:

```yaml
containers:
  - name: api
    image: 123456789012.dkr.ecr.ap-south-1.amazonaws.com/orders-api@sha256:abc123...
```

This avoids ambiguity about what image Kubernetes should execute.

A CI pipeline should not require a new image build merely because the target environment changed.

---

## Docker and ECS

ECS task definitions can reference:

```text
ECR image tag
```

or preferably a specific immutable image identity.

The deployment pipeline should capture the exact artifact deployed so rollback can restore the known-good version.

---

## Docker and EC2

For EC2-based Docker deployments:

```text
GitHub Actions
    ↓
ECR
    ↓
EC2
    ↓
docker pull
    ↓
docker run / compose / systemd
```

The EC2 runtime should authenticate to ECR using an appropriate instance identity rather than embedding long-lived registry credentials.

---

## Docker and Lambda

Lambda can use container images as deployment artifacts.

The pipeline becomes:

```text
Docker Build
 ↓
ECR
 ↓
Lambda
```

The image should still follow:

```text
immutable identity
+
security scanning
+
provenance
+
controlled promotion
```

---

## Docker Deployment Strategies

Docker images can support:

- Rolling deployment
- Blue/green deployment
- Canary deployment
- Zero-downtime deployment

The image lifecycle remains:

```text
Build once
 ↓
Promote artifact
 ↓
Deploy progressively
 ↓
Validate
 ↓
Rollback if necessary
```

---

## Rolling Deployment

A rolling deployment gradually replaces old containers.

```text
Old version: 5
New version: 0

      ↓

Old version: 3
New version: 2

      ↓

Old version: 0
New version: 5
```

The platform must maintain sufficient capacity and validate health during rollout.

---

## Blue/Green Deployment

Two environments exist:

```text
Blue → Current
Green → New
```

The new image is deployed to the inactive environment.

After validation:

```text
Traffic
  ↓
Green
```

Rollback can switch traffic back to Blue.

The major trade-off is increased infrastructure cost.

---

## Canary Deployment

Canary gradually shifts traffic:

```text
v1 → 95%
v2 → 5%
```

Then:

```text
v1 → 75%
v2 → 25%
```

Eventually:

```text
v1 → 0%
v2 → 100%
```

Promotion should be based on defined health criteria rather than arbitrary timing.

---

## Zero-Downtime Docker Deployment

Zero downtime requires more than Docker.

It typically requires:

```text
Multiple instances
+
Readiness checks
+
Graceful shutdown
+
Connection draining
+
Compatible database changes
+
Load balancing
+
Safe deployment strategy
```

A new container starting successfully does not prove that zero downtime exists.

---

## Database Migrations

Docker deployments must account for schema compatibility.

Dangerous sequence:

```text
Deploy application requiring new schema
        ↓
Old containers still running
        ↓
Old application breaks
```

Prefer expand-contract migration strategies.

Example:

```text
Add compatible column
 ↓
Deploy new application
 ↓
Backfill
 ↓
Switch reads/writes
 ↓
Remove old schema later
```

---

## Docker and Redis

If a deployment changes Redis key formats or serialization:

```text
Old application
+
New application
+
Shared Redis
```

can produce compatibility failures.

Version changes should consider:

- Key format
- Serialization
- TTL
- Cache invalidation
- Session compatibility

---

## Docker and Celery

Celery workers are independently deployed containers.

A production pipeline may include:

```text
Django API
Celery Worker
Celery Beat
Redis
```

Deploying the API without considering worker compatibility can create failures.

Maintain backward-compatible task payloads during rolling deployments.

---

## Docker and Kafka

Kafka consumers require special care during deployment.

Consider:

- Consumer group behavior
- Message schema compatibility
- Graceful shutdown
- Offset handling
- Rolling restarts
- Duplicate processing
- Idempotency

The Docker image itself is only one part of safe Kafka deployment.

---

## Docker and Nginx

A common production architecture is:

```text
Internet
   ↓
Load Balancer
   ↓
Nginx
   ↓
Django / FastAPI containers
   ↓
PostgreSQL
```

CI should build and promote application images independently from infrastructure configuration where practical.

---

## Docker and gRPC

gRPC deployments require attention to:

- Port configuration
- HTTP/2
- TLS
- Service discovery
- Health checks
- Backward-compatible protobuf contracts

During rolling deployments, old and new services may coexist.

API compatibility therefore matters as much as image correctness.

---

## Docker Image Rollback

A rollback should reference a known-good image.

Example:

```text
Current:
orders-api@sha256:new

Rollback:
orders-api@sha256:known-good
```

Avoid rebuilding the previous source revision just to perform a rollback.

The previously validated artifact should already exist.

---

## Docker Rollback Architecture

```mermaid
flowchart LR
    GOOD[Known Good Image] --> REG[ECR]
    REG --> STAGE[Staging]
    STAGE --> PROD[Production]
    PROD --> FAIL[Failure]
    FAIL --> ROLLBACK[Rollback]
    ROLLBACK --> GOOD
```

The registry becomes part of the release history.

---

## Docker CI/CD Failure Domains

A useful troubleshooting model is:

```text
Source
 ↓
Workflow
 ↓
Runner
 ↓
Docker Build
 ↓
Cache
 ↓
Registry
 ↓
Deployment
 ↓
Runtime
```

Do not troubleshoot all failures as "Docker problems."

---

## Docker Build Failure Troubleshooting

### Symptom

`docker build` fails.

### Possible Causes

- Dockerfile syntax
- Missing files
- Dependency failure
- Network failure
- Base image issue
- Build context problem
- Architecture mismatch

### Isolation

Run:

```bash
docker build --progress=plain --no-cache -t test-image .
```

### Root Cause

Identify the exact failing Dockerfile instruction.

### Prevention

- Pin dependencies.
- Keep build context small.
- Maintain Dockerfile tests.
- Monitor base images.

---

## Cache Failure Troubleshooting

### Symptom

Build is unexpectedly slow or behaves inconsistently.

### Possible Causes

- Cache miss
- Incorrect cache key
- Dockerfile layer invalidation
- Corrupted cache
- Different runner architecture

### Isolation

Run:

```bash
docker build --no-cache -t test-image .
```

If the clean build works, investigate cache configuration.

### Prevention

Treat cache as an optimization, never as the source of truth.

---

## Registry Failure Troubleshooting

### Symptom

Build succeeds but image push fails.

### Checks

```bash
aws sts get-caller-identity
aws ecr describe-repositories --repository-names orders-api
```

Then verify:

```text
Repository
Region
Role
Permissions
Image tag
Registry availability
```

---

## Deployment Failure Troubleshooting

### Symptom

Image exists but production deployment fails.

### Possible Causes

- Wrong image digest
- Pull permission
- Health check failure
- Port mismatch
- Environment variable
- Secret configuration
- Security group
- Load balancer
- Application startup failure

### Isolation

Separate:

```text
Image correctness
```

from:

```text
Runtime configuration
```

and:

```text
Infrastructure
```

---

## Container Startup Failure

Inspect:

```bash
docker logs <container>
```

and:

```bash
docker inspect <container>
```

Check:

- Entrypoint
- CMD
- Environment
- Ports
- Volumes
- Health status
- Exit code

For Kubernetes:

```bash
kubectl logs <pod>
kubectl describe pod <pod>
```

For ECS, inspect task and service events.

---

## Exit Code Troubleshooting

A container may exit immediately because:

```text
Application crashed
+
Wrong command
+
Missing environment variable
+
Missing dependency
+
Migration failure
+
Permission problem
```

Do not solve startup failures by adding arbitrary delays.

Find the dependency or initialization failure.

---

## Docker Networking Troubleshooting

Check:

```bash
docker network ls
docker network inspect <network>
```

Verify:

```text
Hostname
Port
Listener
Container network
DNS
Security group
```

For CI service containers, verify the networking model before assuming `localhost`.

---

## Docker DNS

Containers commonly communicate using service/container names within an appropriate Docker network.

Example:

```text
api
 ↓
postgres:5432
```

rather than:

```text
localhost:5432
```

when PostgreSQL is a separate container.

`localhost` refers to the current network namespace, not automatically to another container.

---

## Port Mapping

Understand the difference between:

```text
Container port
```

and:

```text
Host port
```

Example:

```text
Host:      5432
Container: 5432
```

A container-to-container connection may not need host port publishing if both services share a Docker network.

Publishing ports unnecessarily can increase complexity and exposure.

---

## Docker Healthcheck vs Application Readiness

A Docker `HEALTHCHECK` can verify container health, but application readiness may depend on:

```text
Database
+
Redis
+
External dependencies
```

A production readiness strategy should match the actual service dependency model.

---

## Docker CI/CD Performance

Build performance is affected by:

```text
Build context
+
Dockerfile layer ordering
+
Dependency downloads
+
Cache hit rate
+
Base image
+
Parallelism
+
Network
+
Runner resources
```

Useful optimizations include:

- `.dockerignore`
- Stable layer ordering
- BuildKit
- Buildx
- Cache reuse
- Multi-stage builds
- Dependency caching
- Appropriate runner sizing

---

## Docker CI/CD Scalability

At scale, consider:

```text
Many repositories
+
Many runners
+
Many builds
+
Large images
+
Multiple architectures
+
Multiple environments
```

A centralized platform may provide:

- Standard Docker workflows
- Reusable workflows
- Approved base images
- Registry standards
- Security scanning
- Build cache infrastructure
- Artifact retention policies

---

## Runner Capacity

Docker builds can consume significant:

- CPU
- Memory
- Disk
- Network bandwidth

A CI platform should monitor runner saturation.

Large parallel matrices can create:

```text
10 builds
×
Large Docker builds
×
Large image transfers
```

and overload runners or registries.

Use:

```yaml
strategy:
  max-parallel: 4
```

when downstream capacity requires control.

---

## Docker CI/CD Cost Optimization

Common cost drivers include:

- Runner execution time
- Docker build time
- Registry storage
- Image transfer
- Large matrices
- Redundant builds
- Inefficient cache strategy
- Long artifact retention

High-value optimizations include:

```text
Build once
+
Cache effectively
+
Avoid unnecessary matrices
+
Keep images reasonably small
+
Reuse immutable artifacts
```

Do not optimize by skipping required security or integration validation.

---

## Docker Image Retention

Registries accumulate:

```text
Commit images
+
Release images
+
Temporary images
+
Old deployment versions
```

Use lifecycle policies to control storage.

Keep enough historical artifacts to support:

```text
Rollback
+
Incident investigation
+
Compliance requirements
```

while removing artifacts that are no longer operationally useful.

---

## Image Retention Strategy

A production policy might distinguish:

```text
Production release images
    ↓
Longer retention

Staging images
    ↓
Moderate retention

PR images
    ↓
Short retention
```

The exact policy should reflect rollback and compliance requirements.

---

## Docker CI/CD Observability

Monitor:

### Build

- Build duration
- Cache hit rate
- Failure rate
- Runner utilization

### Registry

- Push failures
- Pull failures
- Storage
- Vulnerabilities

### Deployment

- Deployment duration
- Failure rate
- Rollback rate
- Health-check failures

### Runtime

- Startup time
- Crash loops
- CPU
- Memory
- Request latency
- Error rate

---

## Deployment Metadata

Every production deployment should ideally be traceable to:

```text
Repository
Commit
Workflow run
Image tag
Image digest
Build timestamp
Environment
Deployment actor
Approval
```

This makes incident investigation significantly easier.

---

## Docker CI/CD Architecture for a Python Backend

```mermaid
flowchart TD
    DEV[Developer] --> PR[Pull Request]

    PR --> LINT[Lint]
    PR --> UNIT[Unit Tests]
    PR --> INT[Integration Tests]
    PR --> SEC[Security Scan]

    LINT --> BUILD[Docker Build]
    UNIT --> BUILD
    INT --> BUILD
    SEC --> BUILD

    BUILD --> IMAGE[Immutable Image]
    IMAGE --> SCAN[Image Scan]
    SCAN --> SBOM[SBOM / Provenance]
    SBOM --> ECR[ECR]

    ECR --> STAGE[Staging]
    STAGE --> HEALTH[Health Checks]
    HEALTH --> APPROVAL[Production Approval]
    APPROVAL --> PROD[Production]

    PROD --> MONITOR[Monitoring]
    MONITOR --> ROLLBACK[Rollback]
```

---

## Production GitHub Actions Pipeline

```yaml
name: CI/CD

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -r requirements-dev.txt
      - run: ruff check .

  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: test-password
          POSTGRES_DB: app_test
        options: >-
          --health-cmd "pg_isready -U app -d app_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -r requirements-dev.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://app:test-password@postgres:5432/app_test
          REDIS_URL: redis://redis:6379/0
        run: pytest --cov=. --cov-report=xml

      - name: Upload coverage
        if: ${{ !cancelled() }}
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage.xml

  build:
    needs:
      - lint
      - test

    runs-on: ubuntu-latest

    permissions:
      contents: read

    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - name: Build image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: false
          tags: orders-api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

This establishes the general separation:

```text
CI validation
    ↓
Docker build
```

A production deployment workflow can then promote the immutable image.

---

## Separate Build and Deployment

A mature system commonly separates:

```text
CI
```

from:

```text
CD
```

Example:

```text
CI Workflow
    ↓
Build
    ↓
Image
    ↓
ECR

CD Workflow
    ↓
Select image digest
    ↓
Staging
    ↓
Approval
    ↓
Production
```

This makes artifact promotion explicit.

---

## Docker Artifact Metadata

A useful release record contains:

```text
IMAGE_TAG=8f32b6c
IMAGE_DIGEST=sha256:...
GIT_SHA=8f32b6c...
WORKFLOW_RUN=123456
ENVIRONMENT=production
```

This allows operators to answer:

> What exactly is running?

---

## Docker and Concurrency

Production deployments should normally prevent overlapping changes.

Example:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

This protects against:

```text
Deployment A starts
Deployment B starts
Deployment A finishes after B
```

which can result in an older image becoming active.

---

## Docker and Immutable Promotion

A deployment workflow should ideally receive:

```text
Image digest
```

rather than:

```text
latest
```

Example:

```yaml
with:
  image: >-
    123456789012.dkr.ecr.ap-south-1.amazonaws.com/orders-api@sha256:abc123...
```

The deployment system then knows exactly which artifact is being promoted.

---

## Docker Release Workflow

A release pipeline can follow:

```text
Git Tag
 ↓
CI
 ↓
Tests
 ↓
Docker Build
 ↓
Image Scan
 ↓
SBOM
 ↓
Push ECR
 ↓
Create Release Metadata
 ↓
Staging
 ↓
Approval
 ↓
Production
```

Semantic versioning can provide a human-readable release identifier, while the digest provides immutable artifact identity.

---

## Semantic Versioning and Docker

Example:

```text
orders-api:2.4.0
```

can identify a release.

Also retain:

```text
orders-api:<git-sha>
```

and the immutable digest.

This provides:

```text
Human-readable release
+
Source traceability
+
Immutable artifact identity
```

---

## Docker CI/CD Common Mistakes

### Using `latest` for Production

It makes deployment identity ambiguous.

### Rebuilding for Production

The production artifact may differ from the staged artifact.

### Storing Secrets in Dockerfile

Secrets can leak into image layers or metadata.

### Ignoring `.dockerignore`

This increases build context and may expose sensitive files.

### Installing Build Tools in Runtime Images

This increases image size and attack surface.

### Treating Cache as Artifact

Caches can disappear or become invalid.

### Running All Tests Inside the Docker Build

This can make the image build slower and less predictable.

### Ignoring Health Checks

A running process is not necessarily a ready application.

### Using a Persistent Privileged Runner for Untrusted Code

A compromised job may affect the runner and future jobs.

### Giving Deployment Jobs Excessive AWS Permissions

OIDC does not make broad IAM permissions safe.

---

## Interview Traps

### Is Docker CI/CD?

No.

Docker is primarily a container packaging/runtime technology. CI/CD platforms orchestrate validation, artifact creation, promotion, and deployment.

---

### Does a Docker Image Guarantee Reproducibility?

No.

Reproducibility requires controlling dependencies, base images, build inputs, build tooling, and other sources of nondeterminism.

---

### Is `latest` Immutable?

No.

A tag can be moved to another image.

---

### Is a Docker Digest the Same as a Tag?

No.

A tag is a human-readable reference.

A digest is content-addressed and identifies specific image content.

---

### Does Docker Layer Caching Guarantee Correctness?

No.

Cache improves performance. The build must remain correct without relying on stale or unavailable cache data.

---

### Should Secrets Be Passed Through `ARG`?

Not for sensitive values that must remain confidential.

Use supported BuildKit secret mechanisms where a build genuinely requires a secret.

---

### Does a Running Container Mean the Application Is Healthy?

No.

The process may be running while dependencies are unavailable or the application is unable to serve traffic.

---

### Why Use Multi-Stage Builds?

To separate build dependencies from runtime dependencies and produce a cleaner runtime image.

---

### Why Use `.dockerignore`?

To reduce build context size, improve performance, and prevent unnecessary or sensitive files from being included in the build context.

---

### Why Use Image Digests?

To identify an exact artifact and avoid ambiguity caused by mutable tags.

---

### Why Build Once and Promote Many?

Because the same validated artifact should be tested and promoted across environments rather than rebuilt differently for each environment.

---

### What Is the Difference Between Build and Deployment?

Build:

```text
Source → Artifact
```

Deployment:

```text
Artifact → Runtime Environment
```

Keeping the two concerns separate improves traceability and rollback.

---

## Senior Interview Scenario: Design Docker CI/CD for Django

### Requirement

A Django application requires:

- PostgreSQL
- Redis
- pytest
- Docker
- AWS ECR
- ECS
- Production approval

### Architecture

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
Security Scan
    ↓
Docker Build
    ↓
Image Scan
    ↓
SBOM / Provenance
    ↓
ECR
    ↓
Staging
    ↓
Health Validation
    ↓
Production Approval
    ↓
ECS
    ↓
Monitoring
    ↓
Rollback
```

---

## Senior Interview Scenario: Production Must Never Rebuild

Use:

```text
Build
 ↓
Push immutable image
 ↓
Capture digest
 ↓
Staging
 ↓
Approval
 ↓
Production
```

Do not run:

```text
docker build
```

again during production deployment.

The production deployment should reference the previously validated image.

---

## Senior Interview Scenario: Build Is Too Slow

Investigate:

```text
Build context
Dockerfile layer ordering
Cache hit rate
Dependency installation
Base image
Runner resources
Network
```

Then optimize:

```text
.dockerignore
+
Stable dependency layers
+
BuildKit
+
Buildx
+
Cache
+
Multi-stage builds
```

Do not immediately increase runner size without measuring the bottleneck.

---

## Senior Interview Scenario: Image Is 2 GB

Investigate:

```text
Base image
Build dependencies
Package caches
Copied source
Build artifacts
Unnecessary files
```

Potential improvements:

```text
Slim runtime image
+
Multi-stage build
+
.dockerignore
+
No package cache
+
Minimal runtime dependencies
```

Validate that functionality and operational support remain intact.

---

## Senior Interview Scenario: Docker Build Works Locally but Fails in GitHub Actions

Investigate environmental differences:

```text
Docker version
BuildKit
Architecture
Environment variables
Build context
Network
Authentication
File permissions
Dependency availability
```

Then reproduce with a local environment that matches CI.

Avoid adding arbitrary CI-only workarounds before understanding the difference.

---

## Senior Interview Scenario: Image Push Works but ECS Cannot Start

Separate the problem:

```text
GitHub → ECR
```

from:

```text
ECS → ECR
```

The image may exist while ECS lacks permission or network access to pull it.

Investigate:

```text
Task execution role
ECR repository
Image digest/tag
Network path
Security groups
ECR permissions
Task startup logs
```

---

## Senior Interview Scenario: Rollback Required

The rollback should use the previous known-good image:

```text
Current:
sha256:new

Rollback:
sha256:known-good
```

Do not rebuild the old commit unless there is a specific operational reason.

---

## Senior Interview Scenario: Multiple Python Versions

A test matrix might use:

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

This validates compatibility.

But Docker production image selection should remain explicit.

Do not confuse:

```text
Test compatibility matrix
```

with:

```text
Production image build matrix
```

unless multiple production architectures or runtimes are genuinely required.

---

## Senior Interview Scenario: Multi-Architecture Deployment

Requirement:

```text
amd64
+
arm64
```

Use Buildx:

```yaml
platforms: linux/amd64,linux/arm64
```

Then verify:

```text
Native dependencies
Base image support
Runtime compatibility
Performance
```

A multi-platform manifest can provide a common image reference while selecting the appropriate architecture at runtime.

---

## Senior Interview Scenario: Compromised Docker Action

If a third-party action is compromised inside a privileged deployment job:

```text
Action
 ↓
Job permissions
 ↓
OIDC
 ↓
AWS role
 ↓
Production
```

The response should include:

```text
Stop affected deployments
+
Restrict trust/permissions
+
Inspect workflow/action
+
Review CloudTrail
+
Validate deployed artifacts
+
Pin/replace compromised action
+
Rotate affected credentials where applicable
+
Restore trusted pipeline
```

---

## Production Docker CI/CD Review Checklist

### Source

- [ ] Protected branches are configured.
- [ ] Dependencies are controlled.
- [ ] Dockerfile changes are reviewed.
- [ ] `.dockerignore` is maintained.

### Build

- [ ] BuildKit/Buildx is used where appropriate.
- [ ] Multi-stage builds are used where useful.
- [ ] Layer ordering is optimized.
- [ ] Build context is minimal.
- [ ] Build dependencies are separated from runtime dependencies.

### Security

- [ ] Secrets are not baked into images.
- [ ] Build secrets use appropriate secret mechanisms.
- [ ] Third-party actions are reviewed.
- [ ] Privileged jobs have minimal permissions.
- [ ] Self-hosted runners are appropriately isolated.
- [ ] Images are scanned.

### Artifact

- [ ] Images are tagged with source identity.
- [ ] Image digests are recorded.
- [ ] SBOM is generated where required.
- [ ] Provenance is available where required.
- [ ] Artifact retention supports rollback.
- [ ] Immutable artifacts are promoted.

### Registry

- [ ] ECR/registry authentication uses an appropriate identity mechanism.
- [ ] Registry permissions are least privilege.
- [ ] Lifecycle policies are configured.
- [ ] Vulnerability scanning is enabled where appropriate.

### Deployment

- [ ] Staging validation occurs before production.
- [ ] Production approval is protected.
- [ ] Deployment concurrency is configured.
- [ ] Health checks are meaningful.
- [ ] Rollback uses a known-good artifact.
- [ ] Database compatibility is considered.

### Operations

- [ ] Build duration is monitored.
- [ ] Cache performance is monitored.
- [ ] Runner capacity is monitored.
- [ ] Registry storage is controlled.
- [ ] Deployment failures are observable.
- [ ] Deployment metadata is traceable.

---

## Senior Design Principles

A production Docker CI/CD system should follow these principles:

```text
Build once
    ↓
Create immutable artifact
    ↓
Scan artifact
    ↓
Record provenance
    ↓
Store artifact
    ↓
Promote artifact
    ↓
Validate deployment
    ↓
Monitor
    ↓
Rollback using known-good artifact
```

The strongest design separates:

```text
Source validation
+
Artifact creation
+
Artifact security
+
Artifact promotion
+
Runtime deployment
+
Runtime monitoring
```

This separation reduces coupling and makes failures easier to isolate.

---

## Key Takeaways

- **Docker in CI/CD is an artifact and runtime boundary, not the CI/CD platform itself; production pipelines must separately address validation, security, promotion, deployment, monitoring, and rollback.**
- **Build once and promote the same immutable image across environments; use commit identity and preferably image digests instead of relying on mutable tags such as `latest`.**
- **BuildKit, Buildx, multi-stage builds, `.dockerignore`, correct Dockerfile layer ordering, and effective caching improve build performance without making cache the source of truth.**
- **Docker security extends beyond image scanning: protect build secrets, isolate privileged runners, control third-party actions, minimize AWS/OIDC permissions, generate provenance/SBOMs where required, and protect artifact integrity.**
- **A senior engineer should troubleshoot Docker CI/CD by failure domain—build, cache, registry, deployment, networking, runtime, or infrastructure—and design the pipeline so every production artifact is traceable, reproducible, deployable, observable, and rollbackable.**