# 09- Containers and Service Containers Questions

## Overview

GitHub Actions containers provide isolated execution environments for CI/CD jobs and the dependencies those jobs require.

For backend engineering, the important distinction is between:

| Mechanism | Purpose | Typical example |
|---|---|---|
| Job container | Runs the job's steps inside a container | `python:3.12-slim` |
| Service container | Provides a dependency alongside the job | PostgreSQL, Redis, MySQL |
| Docker-in-Docker / Docker socket | Builds or runs Docker workloads | Docker image builds |
| Docker Compose | Coordinates multiple application dependencies | Django + PostgreSQL + Redis |
| GitHub-hosted runner | Provides the underlying execution host | `ubuntu-latest` |

A production integration-test pipeline often looks like:

```text
GitHub Actions Runner
        │
        ├── Job Container
        │     └── Python / Django / FastAPI / pytest
        │
        ├── PostgreSQL Service
        │
        └── Redis Service
```

The core engineering problem is not simply "how do I start a container?" It is understanding:

- Where the job actually runs.
- How containers communicate.
- How service readiness is established.
- How environment variables are propagated.
- How data is isolated.
- How matrices affect service instances.
- How failures are diagnosed.
- How containerized CI interacts with Docker, AWS, and production deployment architecture.

---

## GitHub Actions Container Execution Model

The execution hierarchy is:

```text
Workflow
   ↓
Job
   ↓
Runner
   ↓
Containerized Job
   ↓
Steps
```

A job can specify:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    steps:
      - uses: actions/checkout@v5

      - run: python --version
```

The runner remains responsible for orchestrating the job, while the commands execute inside the specified job container.

---

## Why Run a Job Inside a Container?

A job container provides a predictable runtime.

Without a container:

```text
GitHub-hosted runner
 ↓
Preinstalled software
 ↓
Your tests
```

With a container:

```text
GitHub-hosted runner
 ↓
Pinned container image
 ↓
Your tests
```

This can reduce differences between local and CI environments.

Typical use cases include:

- Python version standardization.
- System dependency control.
- Reproducible integration tests.
- Custom Linux distributions.
- Native library compatibility.
- Consistent CI tooling.

---

## Basic Job Container

Example:

```yaml
name: Python Tests

on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    steps:
      - uses: actions/checkout@v5

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

The `run` commands execute inside the container.

---

## Job Container vs Runner

A common misconception is that:

```yaml
container:
  image: python:3.12-slim
```

replaces the runner.

It does not.

Conceptually:

```text
GitHub Actions Runner
        │
        └── Job Container
              │
              ├── Step 1
              ├── Step 2
              └── Step 3
```

The runner still manages the job lifecycle.

---

## Container Image Selection

Prefer explicit, maintained image versions.

For example:

```yaml
container:
  image: python:3.12-slim
```

rather than relying on an uncontrolled custom image.

For higher reproducibility requirements, organizations may maintain their own CI images:

```text
company/ci-python:3.12-v4
```

A CI image should be treated as a production dependency.

---

## CI Image Design

A custom CI image might contain:

```text
Python
pip
pytest
Ruff
MyPy
PostgreSQL client
AWS CLI
jq
curl
```

Example:

```dockerfile
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       jq \
       postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pytest \
    ruff
```

Keep CI images focused.

Do not build a massive image containing every tool used by every repository unless there is a strong operational reason.

---

## Container Environment Variables

Environment variables can be configured at the job level:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim
      env:
        DJANGO_SETTINGS_MODULE: config.settings.test
        PYTHONUNBUFFERED: "1"

    steps:
      - uses: actions/checkout@v5
      - run: pytest
```

Sensitive values should generally come from secrets or protected environments rather than being hardcoded.

---

## Container Working Directory

A container job can use a working directory:

```yaml
container:
  image: python:3.12-slim
```

and configure command execution:

```yaml
defaults:
  run:
    working-directory: /workspace
```

The exact filesystem behavior should be verified when using custom container images because assumptions about pre-existing directories can cause failures.

---

## Container Shell

The shell used by commands should match the image.

For Linux-based images:

```yaml
- name: Run tests
  shell: bash
  run: pytest
```

However, minimal images may not include Bash.

For example, a very small image may only provide:

```text
/bin/sh
```

If the workflow explicitly requires Bash, ensure it exists in the image.

---

## Service Containers

A service container provides a dependency to the job.

Typical services include:

```text
PostgreSQL
MySQL
Redis
```

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
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app_test

      redis:
        image: redis:7

    steps:
      - uses: actions/checkout@v5
      - run: pytest
```

The service exists for the lifetime of the job.

---

## Job Container vs Service Container

The distinction is fundamental.

```text
Job Container
    ↓
Runs your CI commands

Service Container
    ↓
Runs a dependency required by those commands
```

For a Django application:

```text
Job Container
└── Python + Django + pytest

Service Containers
├── PostgreSQL
└── Redis
```

---

## Typical Backend Architecture

```mermaid
flowchart TD
    R[GitHub Actions Runner] --> J[Python Job Container]

    J --> D[Django / FastAPI]
    J --> T[pytest]

    J --> P[PostgreSQL Service]
    J --> REDIS[Redis Service]

    T --> P
    T --> REDIS
```

This mirrors the dependency structure of many backend applications.

---

## Service Container Networking

Networking depends on whether the job itself runs in a container.

There are two important configurations.

### Job Runs Directly on Runner

```text
Runner
 ├── Job
 └── PostgreSQL service
```

The job commonly accesses the service through the published port.

Example:

```yaml
services:
  postgres:
    image: postgres:16
    ports:
      - 5432:5432
```

Then:

```bash
psql -h localhost -U app -d app_test
```

### Job Runs Inside a Container

```text
Network
 ├── Job Container
 └── PostgreSQL Service
```

The service can be addressed through its service label.

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

as the hostname.

---

## The `localhost` Trap

One of the most common container CI mistakes is assuming:

```text
localhost
```

always means the service container.

It does not.

Inside the job container:

```text
localhost
```

means the job container itself.

It does not automatically mean:

```text
PostgreSQL service container
```

Use the service hostname when the job itself is containerized.

---

## PostgreSQL Service Container

Example:

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app_test
        options: >-
          --health-cmd="pg_isready -U app -d app_test"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

    steps:
      - uses: actions/checkout@v5

      - name: Install PostgreSQL client
        run: |
          apt-get update
          apt-get install -y --no-install-recommends postgresql-client

      - name: Run tests
        env:
          DATABASE_URL: postgresql://app:test@postgres:5432/app_test
        run: pytest
```

The important point is:

```text
postgres
```

is the service hostname from the job container.

---

## PostgreSQL Readiness

Starting a PostgreSQL container does not necessarily mean the database is immediately ready for application connections.

A production-oriented CI pipeline should account for readiness.

Health checks can help:

```yaml
options: >-
  --health-cmd="pg_isready -U app -d app_test"
  --health-interval=10s
  --health-timeout=5s
  --health-retries=5
```

An application-level retry can provide another layer of resilience.

---

## Django + PostgreSQL

A Django integration pipeline can use:

```yaml
env:
  DATABASE_URL: postgresql://app:test@postgres:5432/app_test
```

Then:

```yaml
- name: Validate migrations
  run: python manage.py migrate --noinput

- name: Run tests
  run: pytest
```

The sequence is:

```text
Start PostgreSQL
      ↓
Wait for readiness
      ↓
Install Python dependencies
      ↓
Apply migrations
      ↓
Run Django tests
```

---

## FastAPI + PostgreSQL

A FastAPI application can use the same service architecture:

```text
FastAPI
   ↓
SQLAlchemy / async database driver
   ↓
PostgreSQL service
```

Example environment:

```yaml
env:
  DATABASE_URL: postgresql+psycopg://app:test@postgres:5432/app_test
```

The important CI concern is not FastAPI itself but reliable dependency startup and isolation.

---

## MySQL Service Container

Example:

```yaml
services:
  mysql:
    image: mysql:8.4
    env:
      MYSQL_ROOT_PASSWORD: root-test
      MYSQL_DATABASE: app_test
      MYSQL_USER: app
      MYSQL_PASSWORD: test
    options: >-
      --health-cmd="mysqladmin ping -h 127.0.0.1 -uapp -ptest"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=10
```

The application should connect using the appropriate hostname based on whether the job runs on the runner or inside a container.

---

## Redis Service Container

Example:

```yaml
services:
  redis:
    image: redis:7
    options: >-
      --health-cmd="redis-cli ping"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=5
```

A containerized job can connect using:

```text
redis://redis:6379/0
```

For a job running directly on the runner, expose the port and use the appropriate host configuration.

---

## Redis and Celery

A realistic backend integration test may look like:

```text
Django / FastAPI
       ↓
     Celery
       ↓
     Redis
```

The CI environment may therefore contain:

```text
Job Container
├── Python
├── Application
├── pytest
└── Celery

Redis Service
└── Broker / result backend
```

The tests should explicitly control whether Celery workers are required.

Do not introduce a real asynchronous worker merely because the production system uses Celery if the test only needs to validate task creation.

---

## Kafka Service Containers

Kafka integration testing is more complex than PostgreSQL or Redis because of:

- Broker startup time.
- Listener configuration.
- Advertised listeners.
- Network addressing.
- Topic creation.
- Consumer readiness.

For Kafka-heavy systems, an external test environment or dedicated integration infrastructure may sometimes be more reliable than creating a complete Kafka stack for every PR.

Use service containers when the dependency is sufficiently lightweight and deterministic for the required test scope.

---

## Multiple Service Containers

A job can use several services.

Example:

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: test
      POSTGRES_DB: app_test

  redis:
    image: redis:7

  mysql:
    image: mysql:8.4
    env:
      MYSQL_ROOT_PASSWORD: root-test
      MYSQL_DATABASE: legacy_test
      MYSQL_USER: app
      MYSQL_PASSWORD: test
```

The architecture becomes:

```text
              ┌── PostgreSQL
              │
Job Container ├── Redis
              │
              └── MySQL
```

Only introduce services required by the test.

Every service adds:

- Startup time.
- Resource consumption.
- Failure modes.
- Maintenance.
- Network complexity.

---

## Service Ports

When the job runs directly on the runner, services commonly expose ports:

```yaml
services:
  postgres:
    image: postgres:16
    ports:
      - 5432:5432
```

The test can then connect through the runner's network interface.

When the job itself is containerized, service-container networking can instead use the service name.

This distinction should be explicit in the workflow design.

---

## Dynamic Service Ports

For parallel jobs, fixed host ports can create unnecessary conflicts.

A matrix job may have several independent service instances.

A useful design is to isolate each job rather than assuming all matrix jobs share one network.

GitHub Actions creates separate job environments, so each matrix job should be treated as its own CI execution boundary.

---

## Matrix Testing

A common backend requirement is:

```text
Python 3.11
Python 3.12
Python 3.13
```

Example:

```yaml
strategy:
  matrix:
    python:
      - "3.11"
      - "3.12"
      - "3.13"
```

The job can combine the matrix with a service:

```yaml
container:
  image: python:${{ matrix.python }}-slim
```

Each matrix job receives its own execution environment.

---

## Database Matrix

You can also test database compatibility:

```yaml
strategy:
  matrix:
    database:
      - postgres:15
      - postgres:16
```

Then:

```yaml
services:
  postgres:
    image: ${{ matrix.database }}
```

This is useful when an application officially supports multiple PostgreSQL versions.

However, matrix size grows multiplicatively.

---

## Matrix Explosion

Suppose:

```text
3 Python versions
×
2 PostgreSQL versions
×
2 operating systems
```

creates:

```text
3 × 2 × 2 = 12 jobs
```

Add Redis versions:

```text
12 × 2 = 24 jobs
```

The engineering cost includes:

- Runner minutes.
- Queue time.
- Service startup.
- Artifact storage.
- Failure investigation.

Use a compatibility matrix that reflects actual support requirements rather than testing every possible combination.

---

## `fail-fast`

Example:

```yaml
strategy:
  fail-fast: true
  matrix:
    python:
      - "3.11"
      - "3.12"
      - "3.13"
```

If an early failure makes remaining matrix execution unnecessary, cancellation can reduce CI consumption.

For compatibility testing where every result is important, consider:

```yaml
fail-fast: false
```

---

## `max-parallel`

Control concurrent matrix execution:

```yaml
strategy:
  max-parallel: 3
  matrix:
    python:
      - "3.11"
      - "3.12"
      - "3.13"
      - "3.14"
```

This can prevent excessive pressure on:

- Runner capacity.
- External APIs.
- Shared registries.
- Test infrastructure.

---

## Test Isolation

Every integration test should have isolated state.

For PostgreSQL:

```text
Database per job
```

is generally preferable to:

```text
Shared database for all jobs
```

Similarly, Redis keys should be isolated or the service should be created independently per job.

Isolation prevents:

```text
Test A modifies state
      ↓
Test B sees unexpected state
      ↓
Flaky failure
```

---

## Database Migrations in CI

For Django:

```yaml
- name: Apply migrations
  run: python manage.py migrate --noinput
```

Then:

```yaml
- name: Run tests
  run: pytest
```

This validates that the schema can be constructed from scratch.

For larger systems, migration validation can be a separate CI concern from full integration tests.

---

## Transaction Isolation

Tests should not depend accidentally on transaction behavior from previous tests.

Consider:

- Test database creation.
- Transaction rollback.
- Fixtures.
- Explicit cleanup.
- Parallel test workers.
- Database connection pooling.

For pytest-based systems, use appropriate fixtures and database isolation mechanisms rather than manually deleting records after every test.

---

## Parallel Test Execution

Tools such as pytest-xdist can parallelize tests:

```bash
pytest -n auto
```

This can significantly reduce test time, but only when tests are sufficiently isolated.

Potential problems include:

- Shared database state.
- Port conflicts.
- Shared filesystem state.
- Redis key collisions.
- Race conditions.

Parallelism should follow test isolation.

---

## Containerized Integration Testing Pipeline

A realistic backend pipeline:

```mermaid
flowchart LR
    PR[Pull Request] --> CI[GitHub Actions]

    CI --> J[Python Job Container]

    J --> P[PostgreSQL]
    J --> R[Redis]

    J --> T[pytest]
    T --> C[Coverage]
    C --> A[Test Artifacts]
```

This is a common pattern for Django and FastAPI applications.

---

## Test Layers

A production CI system should distinguish:

| Test type | Typical environment | Primary purpose |
|---|---|---|
| Unit | Job container | Isolated application logic |
| Integration | Job + services | Database/cache/infrastructure interaction |
| API | Job + application dependencies | HTTP/API contract behavior |
| E2E | Full application stack | User-level system behavior |
| Smoke | Staging/production-like environment | Deployment validation |

Do not make every pull request run the most expensive test layer.

---

## Artifacts From Container Tests

Test reports can be uploaded:

```yaml
- name: Upload test reports
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@v4
  with:
    name: test-results-${{ matrix.python }}
    path: |
      reports/
      coverage.xml
```

Artifacts are appropriate for:

- JUnit XML.
- Coverage reports.
- Screenshots.
- Logs.
- Debug output.
- Build packages.

They are not a substitute for caches.

---

## Containers vs Caches

| Feature | Container | Artifact | Cache |
|---|---|---|---|
| Runtime isolation | Yes | No | No |
| Persisted between jobs | No | Yes | Yes |
| Intended for test reports | No | Yes | No |
| Intended for dependencies | No | No | Yes |
| Immutable deployment artifact | No | Can be | No |
| Reusable execution environment | Yes | No | No |

A cache is an optimization.

An artifact is a workflow output.

A container is an execution environment.

---

## Dependency Caching

Python dependency installation can dominate CI time.

A typical approach is:

```yaml
- uses: actions/setup-python@v6
  with:
    python-version: "3.12"
    cache: pip
    cache-dependency-path: requirements.txt
```

For lockfile-based projects, use the appropriate lockfile as the cache dependency input.

The cache should never be treated as the source of truth for application dependencies.

---

## Docker Layer Caching

Docker builds can use BuildKit caching.

Example:

```yaml
- name: Build image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: false
    tags: orders-api:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

The cache improves build performance but should not replace immutable image storage.

---

## Custom CI Images vs Service Containers

These solve different problems.

```text
Custom CI Image
    ↓
Tools required by the job

Service Container
    ↓
Runtime dependency required by tests
```

Example:

```text
CI Image
└── Python + pytest + Ruff + clients

Services
├── PostgreSQL
└── Redis
```

Do not package PostgreSQL into the job image merely because the tests need PostgreSQL.

---

## Docker Compose Comparison

Docker Compose can be useful when the application requires a larger dependency graph.

For example:

```text
Django
PostgreSQL
Redis
Celery
Nginx
```

Compose provides explicit multi-container orchestration.

GitHub service containers are often simpler when only a small number of dependencies are needed.

| Requirement | Service Containers | Docker Compose |
|---|---|---|
| One or two dependencies | Excellent | Possible but heavier |
| Simple PostgreSQL/Redis | Excellent | Good |
| Full application topology | Limited | Excellent |
| Custom networking | Limited | Strong |
| Local parity | Moderate | Strong |
| Complex multi-service E2E | Less convenient | Strong |

Use the simplest mechanism that accurately represents the test environment.

---

## Container Volumes

Containers are ephemeral.

If a test requires persistent data during a single job, volume behavior must be explicitly considered.

Typical CI test databases do not need persistence beyond the job.

Avoid designing CI around persistent container state.

For debugging, logs and test artifacts are usually better than persistent service containers.

---

## Container Security

Containerized CI is not automatically secure.

Risks include:

- Malicious dependencies.
- Compromised base images.
- Docker socket access.
- Privileged containers.
- Untrusted code.
- Secrets exposed to processes.
- Vulnerable system packages.

Use:

```text
Trusted base images
+
Pinned versions
+
Minimal permissions
+
Non-privileged execution where practical
+
Ephemeral runners for sensitive workloads
```

---

## Untrusted Pull Requests

Be particularly careful when running containerized code from forks.

The container does not create a magical security boundary around GitHub secrets.

A malicious repository may execute arbitrary commands inside the job container.

Do not combine:

```text
Untrusted PR code
+
Production secrets
+
Privileged runner
+
Private network
```

unless the trust model explicitly supports it.

---

## `pull_request` and Service Containers

For ordinary PR validation, service containers are commonly appropriate:

```text
Fork PR
 ↓
pull_request
 ↓
Ephemeral test environment
 ↓
PostgreSQL
 ↓
pytest
```

The important security principle is that the PR should not receive credentials or permissions that allow it to affect protected production resources.

---

## `pull_request_target` Risk

`pull_request_target` executes with the base repository context and therefore requires special care.

A dangerous pattern is:

```text
pull_request_target
 ↓
Checkout PR code
 ↓
Run PR code
 ↓
Secrets
```

If untrusted code executes with privileged secrets, those secrets may be exposed.

Containerization does not eliminate this risk.

---

## AWS Integration

Containerized CI may interact with AWS for:

- ECR.
- S3.
- ECS.
- EC2.
- Lambda.
- CloudFormation.
- Terraform.

Use GitHub OIDC where appropriate:

```text
GitHub Actions
      ↓
OIDC
      ↓
AWS STS
      ↓
IAM Role
      ↓
AWS Resource
```

Do not store long-lived AWS access keys merely because the job runs in a container.

---

## OIDC From a Container Job

The containerized job can still participate in the workflow's GitHub authentication model.

The workflow needs the appropriate permission:

```yaml
permissions:
  contents: read
  id-token: write
```

The AWS IAM trust policy should restrict the GitHub identity appropriately.

Containerization does not remove the need for least privilege.

---

## Docker Build Inside GitHub Actions

A containerized test job and a Docker image build are separate concerns.

For example:

```text
Job Container
    ↓
Run Integration Tests

Separate Build Job
    ↓
Docker Buildx
    ↓
ECR
```

This separation is often preferable because the build job may require Docker-specific runner capabilities.

---

## Docker Socket

If a job needs to execute Docker commands:

```bash
docker build .
```

the runner needs access to a Docker daemon or another supported builder.

Giving a container direct access to the host Docker socket can create a significant privilege boundary.

Avoid:

```text
Untrusted code
 ↓
Job container
 ↓
Host Docker socket
 ↓
Host control
```

unless the security model explicitly permits it.

---

## Buildx

A production Docker build may use:

```yaml
- name: Set up Buildx
  uses: docker/setup-buildx-action@v3

- name: Build image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: ${{ env.IMAGE }}:${{ github.sha }}
```

Buildx supports:

- Advanced caching.
- Multi-platform builds.
- BuildKit.
- Registry-backed workflows.

---

## Image Tagging

Use immutable identifiers for deployment identity.

Example:

```text
orders-api:<git-sha>
```

or:

```text
orders-api@sha256:<digest>
```

A mutable tag such as:

```text
latest
```

should not be the primary production deployment identity.

---

## Build Once, Promote Many

A production pipeline should preferably follow:

```text
Source
 ↓
Build
 ↓
Immutable Docker Image
 ↓
ECR
 ↓
Staging
 ↓
Approval
 ↓
Production
```

Do not rebuild the image separately for production.

Rebuilding can introduce:

- Different dependency resolution.
- Different base image.
- Different build timestamp.
- Different compiler behavior.
- Different generated artifacts.

The promoted artifact should be the tested artifact.

---

## Health Validation

Deployment success should not mean merely:

```text
Deployment API returned success
```

Validate application health.

For example:

```text
Deploy
 ↓
Wait for service rollout
 ↓
Check task health
 ↓
HTTP smoke test
 ↓
Validate dependencies
```

For Django/FastAPI:

```text
GET /health
```

can provide a lightweight application-level signal.

---

## Service Readiness vs Application Readiness

These are different.

```text
PostgreSQL container ready
```

does not guarantee:

```text
Django application ready
```

Similarly:

```text
Redis available
```

does not guarantee:

```text
Celery worker healthy
```

Integration tests should validate the dependency behavior they actually require.

---

## Health Checks

Health checks should be:

- Fast.
- Deterministic.
- Relevant.
- Independent where possible.

For PostgreSQL:

```bash
pg_isready
```

For Redis:

```bash
redis-cli ping
```

For an HTTP application:

```bash
curl --fail http://localhost:8000/health
```

Avoid health checks that depend on the entire production dependency graph when the purpose is simply to verify one service.

---

## Container Resource Considerations

Every container consumes runner resources.

Monitor:

- CPU.
- Memory.
- Disk.
- Network.
- Process count.

A matrix with:

```text
10 jobs × PostgreSQL × Redis
```

can consume significantly more resources than a single integration job.

Resource constraints can appear as random test failures when the actual cause is runner exhaustion.

---

## CI Reliability

Containerized CI improves reproducibility but introduces additional failure domains:

```text
Image pull
 ↓
Container startup
 ↓
Network creation
 ↓
Service readiness
 ↓
Application startup
 ↓
Tests
```

A failure at any layer can look like an application test failure.

Troubleshooting must therefore start at the infrastructure layer.

---

## Troubleshooting Container Jobs

### Symptom: Job Cannot Start

**Possible causes**

- Invalid image.
- Registry failure.
- Image architecture mismatch.
- Image pull failure.
- Runner issue.

**Checks**

```bash
docker pull <image>
```

where Docker access is available in an equivalent environment.

Inspect the GitHub Actions job log for the image-pull stage.

**Prevention**

- Use maintained images.
- Pin versions.
- Test custom CI images.
- Monitor image availability.

---

## Troubleshooting Service Containers

### Symptom: Application Cannot Connect to PostgreSQL

**Possible causes**

- Wrong hostname.
- Wrong port.
- Database not ready.
- Incorrect credentials.
- Network configuration.
- Job/service networking mismatch.

**Isolation**

First determine:

```text
Is job running directly on runner?
```

or:

```text
Is job running inside container?
```

Then validate:

```text
hostname
port
credentials
readiness
```

For a containerized job, check the service hostname:

```text
postgres
```

rather than assuming:

```text
localhost
```

---

## PostgreSQL Diagnostic Flow

```text
Test fails to connect
        ↓
Check hostname
        ↓
Check port
        ↓
Check service startup
        ↓
Check health status
        ↓
Check credentials
        ↓
Check database name
        ↓
Check network
```

Then validate from the job environment using the PostgreSQL client where available.

---

## Troubleshooting Redis

### Symptom

```text
Connection refused
```

Check:

```text
redis service started?
correct hostname?
correct port?
health check passed?
application URL correct?
```

For a containerized job:

```text
redis://redis:6379/0
```

is a typical service URL.

---

## Troubleshooting MySQL

Check:

```text
MYSQL_DATABASE
MYSQL_USER
MYSQL_PASSWORD
```

and distinguish:

```text
root credentials
```

from:

```text
application credentials
```

Also check:

- Initialization completion.
- Character set.
- Port.
- Hostname.
- Health check.
- SQL mode where relevant.

---

## Troubleshooting `localhost`

If the job is containerized:

```text
localhost
```

means:

```text
Job container
```

not:

```text
PostgreSQL service
```

Use:

```text
postgres
redis
mysql
```

according to the service labels.

This is one of the most common GitHub Actions service-container interview traps.

---

## Troubleshooting Environment Variables

Verify the configuration without printing secrets.

For non-sensitive values:

```bash
echo "$DATABASE_HOST"
echo "$DATABASE_PORT"
```

For secrets, avoid:

```bash
echo "$DATABASE_PASSWORD"
```

Instead verify presence:

```bash
if [ -n "${DATABASE_PASSWORD:-}" ]; then
  echo "DATABASE_PASSWORD is configured"
else
  echo "DATABASE_PASSWORD is missing"
  exit 1
fi
```

---

## Troubleshooting Service Readiness

If tests intermittently fail immediately after startup:

```text
Container started
      ↓
Application connects too early
      ↓
Connection refused
```

Add or improve health checks and readiness handling.

Do not solve deterministic startup races by adding an arbitrary:

```bash
sleep 30
```

unless there is a specific reason and no better readiness signal exists.

---

## Troubleshooting Container Image Dependencies

### Symptom

```text
command not found
```

Possible causes:

- Tool not installed.
- PATH not configured.
- Minimal image.
- Wrong shell.
- Architecture mismatch.

Check:

```bash
which python
which bash
which psql
which redis-cli
```

Use an explicit CI image when the dependency set is stable and widely shared.

---

## Troubleshooting Permissions

Containerized jobs may fail because a process cannot:

```text
write a directory
create a file
execute a binary
access a mounted path
```

Check:

```bash
id
pwd
ls -la
```

Then inspect ownership and permissions.

Avoid solving every permissions problem with:

```bash
chmod -R 777
```

That hides the underlying ownership problem and weakens security.

---

## Troubleshooting Docker Builds

For Docker build failures:

```text
Check Dockerfile
 ↓
Check build context
 ↓
Check .dockerignore
 ↓
Check base image
 ↓
Check dependency installation
 ↓
Check Buildx
 ↓
Check cache
 ↓
Check registry
```

A failed cache lookup is not necessarily a build failure.

---

## Troubleshooting Cache Failures

A cache miss should normally be treated as:

```text
Performance degradation
```

rather than:

```text
Correctness failure
```

The pipeline should still be able to build from scratch.

If correctness depends on the cache, the architecture is fragile.

---

## Troubleshooting Artifact Failures

If test reports are missing:

Check:

```text
Did tests produce the files?
Did the path match?
Did the upload step execute?
Was the step skipped?
Did the container write to the expected workspace?
```

Example:

```yaml
- name: Inspect reports
  if: ${{ !cancelled() }}
  run: |
    find . -maxdepth 3 -type f | sort
```

Then upload the correct path.

---

## Troubleshooting Matrix Failures

A matrix failure should identify:

```text
Python version
Database version
OS
Service configuration
```

Use artifact names that include matrix dimensions:

```yaml
name: test-results-${{ matrix.python }}-${{ matrix.database }}
```

This prevents different matrix jobs from producing ambiguous artifacts.

---

## Troubleshooting Self-Hosted Runners

For self-hosted container workloads, check:

```text
Runner online
 ↓
Labels match
 ↓
Docker available
 ↓
Container runtime healthy
 ↓
Disk available
 ↓
Memory available
 ↓
Network available
 ↓
Private DNS working
```

Also inspect persistent runner state if the runner is not ephemeral.

---

## Security Troubleshooting

If a security-sensitive container job behaves unexpectedly, inspect:

```text
Trigger
 ↓
Code source
 ↓
Permissions
 ↓
Secrets
 ↓
Runner type
 ↓
Container privileges
 ↓
Network access
 ↓
Third-party dependencies
```

Do not assume the container itself is the security boundary.

---

## GitHub CLI Operations

Useful commands include:

```bash
gh workflow list
```

```bash
gh run list
```

```bash
gh run view <run-id>
```

```bash
gh run view <run-id> --log
```

```bash
gh run rerun <run-id>
```

For artifact investigation:

```bash
gh run download <run-id>
```

These commands are useful when investigating failed containerized CI runs.

---

## Production Container Testing Architecture

A mature backend CI/CD pipeline can use:

```mermaid
flowchart TD
    PR[Pull Request] --> LINT[Lint]
    LINT --> UNIT[Unit Tests]

    UNIT --> INT[Integration Test Job]

    INT --> APP[Python Job Container]

    APP --> PG[PostgreSQL Service]
    APP --> REDIS[Redis Service]

    APP --> TEST[pytest]
    TEST --> REPORT[Coverage / JUnit]

    REPORT --> ARTIFACT[Test Artifacts]

    INT --> SEC[Security Scan]
    SEC --> BUILD[Docker Build]

    BUILD --> IMAGE[Immutable Image]
    IMAGE --> ECR[ECR]

    ECR --> STAGE[Staging]
    STAGE --> APPROVAL[Approval]
    APPROVAL --> PROD[Production]
    PROD --> MONITOR[Monitoring]
```

This separates:

```text
Test runtime
```

from:

```text
Deployment runtime
```

while maintaining a single artifact identity.

---

## Production Backend Example

For a Django application:

```text
PR
 ↓
Lint
 ↓
Unit Tests
 ↓
Job Container: Python 3.12
 ↓
PostgreSQL Service
 ↓
Redis Service
 ↓
pytest
 ↓
Coverage
 ↓
Security Scan
 ↓
Docker Buildx
 ↓
ECR
 ↓
Staging
 ↓
Approval
 ↓
Production
```

The same pattern can be adapted to FastAPI applications.

---

## High Availability Considerations

CI service containers are normally ephemeral and should not be designed as highly available production infrastructure.

The objective is:

```text
Fast
Deterministic
Isolated
Disposable
```

Do not attempt to reproduce production HA topology inside every PR unless the test explicitly validates HA behavior.

Production systems may require:

```text
Multi-AZ PostgreSQL
Redis replication
Kafka clusters
Load balancers
Multiple application instances
```

CI integration tests usually require only the minimum dependency topology needed to validate application behavior.

---

## Disaster Recovery Considerations

CI service containers normally have no recovery requirement after a failed job.

A failed job should generally be:

```text
Discarded
 ↓
Diagnosed
 ↓
Rerun / fixed
```

Production deployment pipelines are different.

Production deployments require:

```text
Rollback
Artifact history
Health validation
Recovery procedures
```

Do not confuse CI test environment recovery with production disaster recovery.

---

## Cost Optimization

Containerized CI costs increase with:

```text
Matrix size
+
Service count
+
Job duration
+
Runner type
+
Docker build time
```

Optimize through:

- Dependency caching.
- Docker layer caching.
- Targeted integration tests.
- Appropriate matrix size.
- Parallel execution.
- Path-based workflow selection.
- Reusable CI images.
- Efficient test suites.

Do not reduce critical coverage merely to reduce CI minutes.

---

## Reliability Patterns

Reliable containerized CI should have:

```text
Pinned images
+
Health checks
+
Deterministic setup
+
Isolated test data
+
Explicit networking
+
Bounded retries
+
Useful diagnostics
+
Reproducible dependencies
```

Avoid:

```text
latest tags
+
arbitrary sleeps
+
shared mutable state
+
implicit localhost assumptions
+
persistent runner state
```

---

## Common Mistakes

### Using `localhost` for a Service Container

Incorrect when the job itself runs inside a container.

Use the service hostname.

### Assuming Container Startup Means Service Readiness

Startup and readiness are different states.

### Using `latest`

Mutable image tags can introduce unexpected CI behavior.

### Sharing Test Databases Across Matrix Jobs

This creates isolation and race problems.

### Creating Excessive Matrix Dimensions

A technically comprehensive matrix can become operationally impractical.

### Running Every Dependency for Every Test

Only start services required by the test layer.

### Using `sleep 30` Everywhere

Prefer readiness checks.

### Giving Untrusted Jobs Private Network Access

This can expose internal infrastructure.

### Mounting the Docker Socket Into Untrusted Containers

This can create a significant host privilege boundary.

### Treating Caches as Required State

A cache should optimize execution, not determine correctness.

---

## Interview Questions

### What Is a Service Container?

A service container is a containerized dependency that runs alongside a GitHub Actions job.

Typical examples:

```text
PostgreSQL
MySQL
Redis
```

The job uses the service to perform integration or end-to-end testing.

---

### What Is the Difference Between a Job Container and a Service Container?

A job container executes the job's commands.

A service container provides an external dependency to that job.

```text
Job Container
→ Application / pytest

Service Container
→ PostgreSQL / Redis
```

---

### How Does Networking Work Between a Job Container and PostgreSQL?

When the job itself runs in a container, the service can generally be addressed using its service label:

```text
postgres
```

Therefore:

```text
postgres:5432
```

is typically used rather than:

```text
localhost:5432
```

---

### Why Does `localhost` Often Fail?

Inside the job container:

```text
localhost
```

refers to the job container itself.

The PostgreSQL service is a different container.

Therefore the application should use the service hostname.

---

### How Would You Test Django With PostgreSQL and Redis?

A practical architecture is:

```text
Python Job Container
       │
       ├── Django
       ├── pytest
       │
       ├── PostgreSQL Service
       └── Redis Service
```

Then:

```text
Wait for readiness
 ↓
Run migrations
 ↓
Run pytest
 ↓
Generate coverage
 ↓
Upload reports
```

---

### How Would You Handle PostgreSQL Startup Races?

Use:

- Container health checks.
- Readiness checks.
- Application connection retries where appropriate.

Avoid arbitrary sleep-based synchronization.

---

### How Would You Test Multiple Python and PostgreSQL Versions?

Use a matrix:

```yaml
strategy:
  matrix:
    python:
      - "3.11"
      - "3.12"
    postgres:
      - "15"
      - "16"
```

Then select the appropriate job container and PostgreSQL service image.

Be careful about matrix multiplication and CI cost.

---

### How Would You Prevent Test Data From Colliding?

Use independent service containers per job and isolated databases.

For parallel test execution, ensure fixtures, database state, Redis keys, and filesystem resources do not overlap unexpectedly.

---

### When Would You Use Docker Compose Instead of Service Containers?

Use service containers for relatively simple dependency requirements.

Use Docker Compose when the test requires a more complete multi-container topology with custom networking, multiple application components, or stronger local-environment parity.

---

### How Would You Secure Containerized CI?

Use:

- Trusted and maintained images.
- Pinned versions.
- Least-privilege GitHub permissions.
- Minimal secrets.
- Safe handling of untrusted inputs.
- Ephemeral runners for sensitive workloads.
- Restricted private-network access.
- Avoidance of unnecessary privileged containers.
- Controlled Docker daemon access.

---

### Can a Containerized Job Safely Run Fork Pull Requests?

The container itself does not determine safety.

The workflow must ensure that untrusted code does not receive privileged secrets, permissions, or access to sensitive infrastructure.

The trigger and permission model are more important than simply using containers.

---

### How Would You Debug a PostgreSQL Connection Failure?

Use the failure-domain sequence:

```text
Job execution mode
 ↓
Hostname
 ↓
Port
 ↓
Credentials
 ↓
Database name
 ↓
Service startup
 ↓
Health status
 ↓
Network
```

If the job is containerized, verify that the application uses:

```text
postgres
```

rather than:

```text
localhost
```

---

### What Happens If Redis Is Running but Tests Still Fail?

Check:

```text
Redis readiness
 ↓
Hostname
 ↓
Port
 ↓
Database index
 ↓
Connection URL
 ↓
Authentication configuration
 ↓
Application startup
```

Service availability alone does not guarantee application configuration correctness.

---

### Should CI Reproduce the Entire Production Infrastructure?

Usually not.

CI should reproduce the dependencies necessary to validate the behavior being tested.

A full production topology may be appropriate for specific E2E or staging tests, but recreating it for every PR increases:

```text
Cost
Complexity
Startup time
Failure surface
Maintenance
```

---

## Senior Scenario: Production-Like Integration Tests

> A Django service requires PostgreSQL and Redis. The team wants every PR to validate both dependencies.

A practical design is:

```text
PR
 ↓
GitHub Actions
 ↓
Python Job Container
 ├── Django
 ├── pytest
 ├── PostgreSQL service
 └── Redis service
```

Use isolated services per job, health checks, migrations, and test reports.

Keep deployment credentials and production network access outside this PR test path.

---

## Senior Scenario: Matrix Explosion

> The team wants to test four Python versions, three PostgreSQL versions, two Redis versions, and two operating systems.

The theoretical matrix is:

```text
4 × 3 × 2 × 2 = 48 jobs
```

Before implementing it, determine:

- Actual supported combinations.
- Compatibility requirements.
- Cost.
- Runtime.
- Failure diagnosis complexity.

Use `include` and `exclude` to represent valid combinations instead of blindly testing the Cartesian product.

---

## Senior Scenario: Private Database Access

> Integration tests need access to a private PostgreSQL instance in AWS.

A service container may not be the appropriate solution.

If the test requires real private infrastructure:

```text
GitHub Actions
 ↓
Self-hosted / private runner
 ↓
VPC
 ↓
Private PostgreSQL
```

This introduces a much larger security boundary.

Prefer ephemeral isolated test infrastructure where practical rather than allowing broad CI access to production databases.

---

## Senior Scenario: Docker Socket

> A containerized job needs to build Docker images and therefore mounts `/var/run/docker.sock`.

The team should recognize that the Docker socket can provide significant control over the host Docker daemon.

Consider safer build architectures such as:

```text
Dedicated build job
+
Buildx
+
Ephemeral runner
```

rather than giving arbitrary application test containers unrestricted host Docker access.

---

## Senior Scenario: Flaky Integration Tests

> PostgreSQL integration tests randomly fail with connection-refused errors.

Do not immediately increase test retries.

Investigate:

```text
Container startup
 ↓
Health check
 ↓
Readiness
 ↓
Network
 ↓
Connection configuration
 ↓
Runner resource pressure
```

If the root cause is a startup race, fix readiness rather than masking it with retries.

---

## Senior Scenario: Production Artifact Promotion

> The integration-test job runs in a Python container and the build job creates a Docker image.

Keep the two responsibilities separate:

```text
Integration Job
 ↓
Validate source

Build Job
 ↓
Build immutable image
 ↓
Push to ECR
 ↓
Return digest

Deployment
 ↓
Promote digest
```

The tested source should produce the same immutable artifact that reaches production.

---

## Senior Scenario: Self-Hosted Runner

> Integration tests need private AWS services unavailable from GitHub-hosted runners.

Use a dedicated runner architecture:

```text
Private Runner Group
        ↓
Ephemeral Runner
        ↓
Private VPC
        ↓
Test Infrastructure
```

Restrict repository access to the runner group and avoid allowing untrusted workflows to use the same privileged runner pool.

---

## Production Checklist

### Job Containers

- [ ] Container image is explicitly selected.
- [ ] Image versions are controlled.
- [ ] Required tools are present.
- [ ] Shell assumptions are documented.
- [ ] Environment variables are explicit.
- [ ] Container resource requirements are understood.

### Service Containers

- [ ] Only required services are started.
- [ ] Service versions are controlled.
- [ ] Health/readiness checks exist where needed.
- [ ] Networking model is understood.
- [ ] Service hostnames are correct.
- [ ] Test state is isolated.

### Testing

- [ ] Unit and integration tests are separated.
- [ ] Database migrations are validated.
- [ ] PostgreSQL/MySQL/Redis dependencies are deterministic.
- [ ] Matrix dimensions reflect actual compatibility requirements.
- [ ] Coverage and test reports are preserved.
- [ ] Failed-test diagnostics are available.

### Security

- [ ] Secrets are minimized.
- [ ] Permissions use least privilege.
- [ ] Fork PRs cannot access production credentials.
- [ ] Untrusted input is handled safely.
- [ ] Self-hosted runners are isolated.
- [ ] Docker socket access is controlled.
- [ ] Private network access is restricted.

### Production Delivery

- [ ] Docker images are immutable.
- [ ] Buildx is used where appropriate.
- [ ] Images are pushed to a controlled registry.
- [ ] OIDC is used for AWS authentication where appropriate.
- [ ] The same artifact is promoted across environments.
- [ ] Deployment health is validated.
- [ ] Rollback is supported.

---

## Key Takeaways

- **Job containers execute CI steps, while service containers provide dependencies such as PostgreSQL, MySQL, and Redis; understanding this boundary is essential for reliable backend integration testing.**
- **Container networking depends on the execution model: a containerized job should normally address service containers by their service hostname rather than assuming `localhost` refers to the dependency.**
- **Production-grade integration tests require readiness checks, isolated state, controlled matrices, deterministic images, and diagnostics that distinguish infrastructure failures from application test failures.**
- **Containers do not automatically create a security boundary: untrusted PR code, privileged Docker access, secrets, private networks, self-hosted runners, and third-party dependencies must still be controlled.**
- **Use containers to make CI reproducible, but keep orchestration and deployment concerns separate: build immutable artifacts once, promote the same artifact, and use protected deployment workflows for staging and production.**