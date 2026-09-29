# 12- Container and Service Container Issues

## Overview

GitHub Actions supports containerized jobs and service containers to provide reproducible CI environments and dependencies such as PostgreSQL, MySQL, and Redis.

The important distinction is:

- **Job container** — the workflow job itself executes inside a container.
- **Service container** — a supporting container runs alongside the job.
- **Runner** — the host environment that manages the job and containers.

A typical backend integration-test pipeline looks like:

```text
GitHub-hosted runner
        │
        ├── Job container
        │      └── Python + Django/FastAPI + pytest
        │
        ├── PostgreSQL service
        │
        └── Redis service
```

Container failures are often caused by confusing the networking model, service readiness, image compatibility, environment variables, ports, permissions, or the distinction between the runner and the container.

A reliable troubleshooting model is:

```text
Symptom
   ↓
Identify execution environment
   ↓
Identify networking model
   ↓
Verify container lifecycle
   ↓
Verify service readiness
   ↓
Verify credentials/configuration
   ↓
Inspect logs and connectivity
   ↓
Isolate root cause
   ↓
Correct configuration
   ↓
Prevent recurrence
```

---

## Container Execution Model

The basic GitHub Actions execution hierarchy is:

```text
Workflow
  ↓
Job
  ↓
Runner
  ├── Job container
  │     ├── Step 1
  │     ├── Step 2
  │     └── Step 3
  │
  └── Service containers
        ├── PostgreSQL
        ├── Redis
        └── MySQL
```

A job can execute directly on the runner:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest
```

Or inside a container:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest
```

The runner still orchestrates the job even when the commands execute inside the container.

---

## Job Containers vs Service Containers

| Feature | Job Container | Service Container |
|---|---|---|
| Purpose | Run workflow steps | Provide supporting services |
| Example | Python runtime | PostgreSQL |
| Steps execute inside it | Yes | No |
| Application code | Usually | No |
| Database | Usually not | Common |
| Redis | Usually not | Common |
| Lifecycle | Job-scoped | Job-scoped |
| Networking | Depends on job model | Connected to job networking |

A common production testing architecture is:

```text
Python job container
       │
       ├── Django/FastAPI
       ├── pytest
       └── application dependencies
              │
              ├── PostgreSQL service
              └── Redis service
```

---

## When to Use a Job Container

Use a job container when you need a consistent execution environment.

Typical reasons include:

- Exact Linux distribution
- Exact Python runtime
- Native libraries
- System packages
- Reproducible test environments
- CI parity with production images

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-bookworm

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

---

## When to Use Service Containers

Use service containers when the application under test requires external infrastructure.

Common examples:

```text
PostgreSQL
MySQL
Redis
```

A Django application might use:

```text
Django
   ↓
PostgreSQL
   +
Redis
```

A FastAPI application might use:

```text
FastAPI
   ↓
PostgreSQL
   +
Redis
```

Service containers are particularly useful for integration testing because they avoid depending on shared development or external infrastructure.

---

## Basic Service Container Configuration

Example PostgreSQL service:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U testuser -d testdb"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://testuser:testpassword@localhost:5432/testdb
        run: pytest
```

This model uses the runner as the application execution environment.

---

## Networking Model

Networking is one of the most common sources of container failures.

The correct hostname depends on whether the job itself runs inside a container.

### Runner-Based Job

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        ports:
          - 5432:5432
```

The test process runs on the runner, so:

```text
localhost:5432
```

can be used when the service port is published to the runner.

### Containerized Job

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

The job container and service container share the job's container network.

Use the service label:

```text
postgres:5432
```

rather than assuming `localhost`.

---

## The `localhost` Trap

This is a common mistake:

```text
Application container
      ↓
localhost:5432
```

`localhost` refers to the current container, not necessarily the PostgreSQL service.

For a containerized job:

```text
test container
      │
      └── postgres:5432
```

For a runner-based job with published ports:

```text
runner
      │
      └── localhost:5432
              ↓
          PostgreSQL
```

Always identify where the application process actually runs before choosing the database hostname.

---

## Networking Decision Table

| Job Model | Service Host | Typical Port |
|---|---|---:|
| Runner-based | `localhost` | Published port |
| Containerized job | Service label | Service port |
| External database | DNS hostname | Database port |
| Kubernetes integration | Service DNS | Service port |
| Docker Compose | Compose service name | Container port |

The same application configuration should not blindly be reused across all environments.

---

## Service Labels Become DNS Names

Consider:

```yaml
services:
  postgres:
    image: postgres:16
```

When the job itself runs in a container, the service can typically be addressed as:

```text
postgres
```

Therefore:

```text
postgres:5432
```

is usually preferable to:

```text
localhost:5432
```

for container-to-container communication.

---

## Multiple Services

A realistic backend test can use:

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: test-password
      POSTGRES_DB: app_test

  redis:
    image: redis:7
```

The application configuration becomes:

```text
DATABASE_HOST=postgres
DATABASE_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
```

Architecture:

```mermaid
flowchart LR
    A[GitHub Actions Job] --> B[Django/FastAPI]
    B --> C[PostgreSQL]
    B --> D[Redis]
```

---

## Failure Domain: Service Not Reachable

### Symptom

Typical errors include:

```text
connection refused
could not connect to server
Name or service not known
Temporary failure in name resolution
```

### Possible Causes

- Wrong hostname
- Wrong port
- Service not ready
- Port not published
- Job/container networking misunderstanding
- Service container failed to start
- Incorrect environment variables
- Authentication failure presented as connectivity failure

### Isolation Strategy

First determine:

```text
Where does the application process run?
```

Then:

```text
Where does the service run?
```

Finally:

```text
How should the two communicate?
```

---

## Connectivity Checks

From a runner-based job:

```bash
nc -zv localhost 5432
```

For Redis:

```bash
nc -zv localhost 6379
```

From a containerized job, test the service hostname:

```bash
getent hosts postgres
```

and:

```bash
nc -zv postgres 5432
```

If `nc` is unavailable, use application-specific clients or install appropriate diagnostic tools in the test image.

---

## Failure Domain: Service Container Fails to Start

### Possible Causes

- Invalid image
- Unsupported image architecture
- Invalid environment variables
- Container initialization failure
- Resource exhaustion
- Invalid health check
- Broken image tag
- Image pull failure

Inspect the workflow logs and verify the image independently.

For PostgreSQL:

```text
postgres:16
```

is preferable to an uncontrolled floating image when reproducibility matters.

---

## Pinning Service Images

Avoid unnecessarily vague service definitions:

```yaml
image: postgres:latest
```

Prefer an explicit major or organization-approved version:

```yaml
image: postgres:16
```

For highly controlled environments, an organization may use a more specific immutable image reference.

The goal is to avoid unexpected CI changes caused by mutable image updates.

---

## Failure Domain: Database Starts but Tests Fail

A running container does not necessarily mean the service is ready.

There are several states:

```text
Container created
      ↓
Process started
      ↓
Database initializing
      ↓
Database accepting connections
```

Tests should begin only after the service reaches the required readiness state.

---

## Health Checks

PostgreSQL:

```yaml
options: >-
  --health-cmd="pg_isready -U testuser -d testdb"
  --health-interval=10s
  --health-timeout=5s
  --health-retries=5
```

Redis:

```yaml
options: >-
  --health-cmd="redis-cli ping"
  --health-interval=10s
  --health-timeout=5s
  --health-retries=5
```

Health checks should test the service's actual readiness condition rather than merely checking whether the process exists.

---

## Readiness vs Liveness

For CI integration tests, readiness matters more than simple process liveness.

```text
Liveness:
"Is the process running?"

Readiness:
"Can the application successfully use the service?"
```

For PostgreSQL:

```text
postgres process exists
        ≠
database accepts connections
```

---

## Failure Domain: PostgreSQL Readiness

### Symptom

Tests fail intermittently with:

```text
connection refused
database system is starting up
```

### Root Cause

The test begins before PostgreSQL is ready.

### Corrective Action

Use the service health check and ensure the test begins only after the service is ready.

### Prevention

Use deterministic readiness checks rather than arbitrary sleeps.

Avoid:

```bash
sleep 30
```

when a meaningful health check can be used.

---

## PostgreSQL Integration Testing

A Django pipeline may use:

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: django
      POSTGRES_PASSWORD: django-password
      POSTGRES_DB: django_test
    ports:
      - 5432:5432
    options: >-
      --health-cmd="pg_isready -U django -d django_test"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=5
```

Then:

```yaml
- name: Run migrations and tests
  env:
    DATABASE_URL: postgresql://django:django-password@localhost:5432/django_test
  run: |
    python manage.py migrate
    pytest
```

This is appropriate when the job runs directly on the runner.

---

## Containerized Django Testing

When Django runs inside a job container:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: django
          POSTGRES_PASSWORD: django-password
          POSTGRES_DB: django_test

    steps:
      - uses: actions/checkout@v4

      - run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://django:django-password@postgres:5432/django_test
        run: |
          python manage.py migrate
          pytest
```

The important difference is:

```text
postgres
```

rather than:

```text
localhost
```

---

## FastAPI Integration Testing

FastAPI tests can use the same service model:

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: test-password
      POSTGRES_DB: app_test

  redis:
    image: redis:7
```

Application configuration:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
```

Workflow:

```yaml
env:
  DATABASE_URL: postgresql://app:test-password@postgres:5432/app_test
  REDIS_URL: redis://redis:6379/0
```

This keeps infrastructure configuration outside application source code.

---

## MySQL Service Containers

Example:

```yaml
services:
  mysql:
    image: mysql:8.4
    env:
      MYSQL_ROOT_PASSWORD: root-password
      MYSQL_DATABASE: app_test
      MYSQL_USER: app
      MYSQL_PASSWORD: app-password
    ports:
      - 3306:3306
    options: >-
      --health-cmd="mysqladmin ping -h 127.0.0.1 -uapp -papp-password"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=10
```

Be careful with:

- Authentication configuration
- Character sets
- Collations
- SQL modes
- Initialization timing
- Root vs application credentials

---

## Redis Service Containers

Basic configuration:

```yaml
services:
  redis:
    image: redis:7
    ports:
      - 6379:6379
    options: >-
      --health-cmd="redis-cli ping"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=5
```

For a containerized job:

```text
redis:6379
```

For a runner-based job with published ports:

```text
localhost:6379
```

---

## Celery Integration Testing

A Django or FastAPI application using Celery may have:

```text
Application
   ↓
Redis
   ↓
Celery worker
```

Service containers can provide Redis, but the Celery worker itself may need to run as a separate process in the job.

For example:

```bash
celery -A app worker --loglevel=INFO &
pytest
```

Be careful with background processes:

- Capture logs.
- Ensure process termination.
- Verify broker readiness.
- Avoid tests that depend on race-prone startup timing.

For more complex integration environments, Docker Compose or a dedicated ephemeral environment may be more appropriate.

---

## Kafka Integration Testing

Kafka is significantly heavier than PostgreSQL or Redis.

Consider:

```text
Application
    ↓
Kafka
    ↓
Consumer
```

Before using Kafka as a standard service container, consider:

- Startup time
- Memory requirements
- Broker configuration
- Listener configuration
- Readiness
- Test isolation
- Parallel matrix capacity

For complex Kafka integration testing, a dedicated container image or Compose-based environment may provide better control.

---

## Service Containers and Environment Variables

Keep configuration explicit:

```yaml
env:
  DB_HOST: postgres
  DB_PORT: "5432"
  DB_NAME: app_test
  DB_USER: app
  DB_PASSWORD: test-password
```

Avoid embedding test configuration throughout scripts.

For production workflows, never reuse test credentials as production credentials.

---

## Service Container Credentials

Service container credentials are normally test-only.

Example:

```yaml
env:
  POSTGRES_PASSWORD: test-password
```

Do not place production secrets in service container configuration.

Integration tests should use isolated credentials and disposable databases.

---

## Failure Domain: Authentication Failure

### Symptom

```text
password authentication failed
access denied
authentication plugin error
```

### Possible Causes

- Wrong username
- Wrong password
- Wrong database
- Wrong authentication configuration
- Environment variable mismatch
- Application reading different variables than expected

### Isolation

Print safe configuration metadata:

```bash
echo "DB_HOST=$DB_HOST"
echo "DB_PORT=$DB_PORT"
echo "DB_NAME=$DB_NAME"
echo "DB_USER=$DB_USER"
```

Never print:

```bash
echo "$DB_PASSWORD"
```

---

## Failure Domain: Wrong Database

A service may be healthy while the application connects to the wrong database.

Verify:

```text
Host
Port
Database
Username
Authentication
```

For PostgreSQL:

```bash
psql "$DATABASE_URL" -c "SELECT current_database(), current_user;"
```

Use test credentials only.

---

## Container Environment vs Runner Environment

A common debugging mistake is checking environment variables on the runner when the failing process executes inside a container.

Example:

```text
Runner:
DB_HOST=postgres

Container:
DB_HOST missing
```

The application sees the container's environment, not an arbitrary shell state on the host.

Debug from the same execution environment as the failing process.

---

## Container Working Directory

A job container may have a different filesystem layout than the runner.

A failing command such as:

```bash
pytest tests/
```

may be caused by the working directory.

Inspect:

```bash
pwd
ls -la
find . -maxdepth 2 -type f | head -50
```

Configure explicitly when necessary:

```yaml
container:
  image: python:3.12
  options: --workdir /workspace
```

or use the repository workspace conventions provided by GitHub Actions.

---

## Missing Executables

A minimal image such as:

```text
python:3.12-slim
```

may not contain common diagnostic tools.

Possible symptoms:

```text
bash: command not found
nc: command not found
curl: command not found
git: command not found
```

Do not assume a production-minimal image is also a complete CI image.

Use a CI-specific image when appropriate.

---

## Job Container Shell Differences

Container images may use different shells.

A workflow step that assumes Bash may fail when the image defaults to another shell.

Explicitly select the shell when needed:

```yaml
- name: Run checks
  shell: bash
  run: |
    set -euo pipefail
    pytest
```

Ensure the selected shell exists in the image.

---

## Package Installation Failures

Minimal containers frequently lack native build dependencies.

For Python packages such as:

```text
psycopg
mysqlclient
cryptography
```

installation may require appropriate system libraries depending on the package and installation mode.

If the job uses a custom CI image, install required build tooling there rather than repeatedly installing it in every workflow run.

---

## Custom CI Images

For larger organizations, a controlled CI image can contain:

```text
Python
pip
pytest
gcc
database clients
Docker tooling
AWS CLI
diagnostic tools
```

Example architecture:

```text
Approved CI Image
      ↓
GitHub Actions Job
      ↓
Service Containers
      ↓
Tests
```

Benefits:

- Faster startup
- Consistent tooling
- Fewer repeated package installations

Trade-offs:

- Image maintenance
- Security patching
- Image versioning
- Larger blast radius when the image is broken

---

## Failure Domain: Image Pull Failure

### Symptom

```text
pull access denied
manifest unknown
image not found
unauthorized
```

### Possible Causes

- Incorrect image name
- Incorrect tag
- Private registry authentication
- Registry outage
- Architecture mismatch
- Image removed

### Isolation

Verify:

```text
Registry
Repository
Tag/digest
Authentication
Architecture
```

For production workflows, prefer controlled image versions and trusted registries.

---

## Multi-Architecture Issues

A service image may not support the architecture of the runner.

Potential problem:

```text
Runner architecture
        ≠
Image architecture
```

Check the image manifest with Docker when available:

```bash
docker manifest inspect postgres:16
```

For custom images, publish the architectures required by the CI fleet.

---

## Docker-in-Docker Considerations

Running Docker inside a job container introduces another boundary.

```text
Runner
  ↓
Job container
  ↓
Docker daemon / BuildKit
  ↓
Build containers
```

Potential problems include:

- Docker socket access
- Permissions
- Network isolation
- Cache configuration
- Security boundaries
- Privileged containers

Do not mount the host Docker socket into untrusted jobs without understanding the security implications.

---

## Service Containers and Docker Socket Security

Access to the host Docker daemon can effectively provide powerful control over the runner.

This is particularly dangerous for:

- Fork pull requests
- Untrusted source code
- Self-hosted runners
- Privileged deployment jobs

Separate trusted build/deployment workflows from untrusted validation workflows.

---

## Service Container Logs

When a service fails, the application log alone may not explain the problem.

Investigate:

```text
Application logs
Service logs
Health status
Runner logs
Network diagnostics
```

For complex local reproduction, use Docker:

```bash
docker ps
docker logs <container>
docker inspect <container>
```

GitHub Actions service-container logs are also available through the workflow execution context.

---

## Failure Domain: Health Check Never Becomes Healthy

### Possible Causes

- Incorrect health command
- Service startup takes longer than expected
- Wrong credentials
- Database initialization failure
- Wrong database name
- Required extension/configuration missing

The health command should be tested against the same assumptions used by the application.

---

## Avoid Arbitrary Sleeps

This is fragile:

```bash
sleep 30
pytest
```

Why?

```text
Fast environment
    → wastes 30 seconds

Slow environment
    → 30 seconds may not be enough
```

Prefer readiness checks.

---

## Failure Domain: Port Confusion

Typical database ports:

| Service | Default Port |
|---|---:|
| PostgreSQL | 5432 |
| MySQL | 3306 |
| Redis | 6379 |
| Kafka | 9092 |

But the important question is not only the port number.

It is:

```text
Which network namespace is the client using?
```

---

## Published Ports vs Container Ports

Runner-based job:

```yaml
ports:
  - 5432:5432
```

means:

```text
Runner port 5432
       ↓
Container port 5432
```

Containerized job using service networking generally does not need the service published to the runner for job-to-service communication.

This is why copying port mappings between the two models can create unnecessary complexity.

---

## Failure Domain: Service Name Resolution

### Symptom

```text
could not translate host name "postgres"
```

### Possible Causes

- Application is running directly on runner
- Service label is wrong
- Job is not configured as expected
- Network configuration differs from assumption

If the application runs on the runner:

```text
localhost
```

may be appropriate.

If it runs in the job container:

```text
postgres
```

may be appropriate.

---

## Containers and Matrix Testing

A test matrix might contain:

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

Each matrix job receives its own job and service-container lifecycle.

This provides isolation but multiplies resource consumption.

For example:

```text
3 Python versions
×
PostgreSQL
×
Redis
=
3 independent environments
```

Scale downstream capacity accordingly.

---

## Matrix + Database Versions

A compatibility matrix could be:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
    postgres-version: ["15", "16"]
```

This creates:

```text
2 × 2 = 4 jobs
```

Each job may start its own PostgreSQL service.

Large matrices can therefore create substantial CI resource demand.

---

## Fail-Fast and Service Containers

For compatibility testing:

```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.11", "3.12"]
```

`fail-fast: false` allows all matrix cells to finish.

This can be useful when compatibility information across all versions matters.

For expensive environments, however, evaluate the cost of allowing every matrix cell to continue.

---

## Containerized Integration Test Pipeline

A production-oriented backend pipeline may look like:

```mermaid
flowchart TD
    A[Pull Request] --> B[Lint]
    B --> C[Unit Tests]
    C --> D[Integration Test Job]
    D --> E[Python Job Container]
    E --> F[PostgreSQL Service]
    E --> G[Redis Service]
    E --> H[pytest]
    H --> I[Coverage]
    I --> J[Test Artifacts]
    J --> K[Build]
```

This separates fast unit validation from infrastructure-dependent integration tests.

---

## Container vs Service Container vs Docker Compose

| Approach | Best Fit | Complexity |
|---|---|---|
| Job container | Consistent CI runtime | Low |
| Service containers | Small set of dependencies | Low |
| Docker Compose | Complex multi-service topology | Medium |
| Ephemeral environment | Production-like integration | High |

Use the simplest architecture that provides the required fidelity.

---

## When Service Containers Are Not Enough

Service containers become less convenient when you need:

- Many dependent services
- Complex startup ordering
- Custom network topology
- Multiple replicas
- Kafka clusters
- Nginx/API gateway configuration
- Service-specific volumes
- Complex initialization scripts

At that point, Docker Compose or an ephemeral environment may be more appropriate.

---

## Docker Compose in CI

A Compose-based integration environment might look like:

```text
docker compose
   ├── api
   ├── postgres
   ├── redis
   ├── worker
   └── nginx
```

This provides more explicit topology control.

However, it also introduces:

- More configuration
- More startup orchestration
- More logs
- More resource consumption
- More troubleshooting surface

---

## Security Considerations

Containerized CI executes code.

Therefore, treat containers as execution boundaries, not automatic security boundaries.

Important controls include:

- Least-privilege `GITHUB_TOKEN`
- No unnecessary secrets in test jobs
- Trusted container images
- Image version control
- SHA pinning for third-party actions
- Ephemeral runners for untrusted or sensitive workloads
- No unnecessary Docker socket access
- Network segmentation
- Minimal service credentials

---

## Secrets in Containers

Avoid:

```yaml
run: echo "${{ secrets.DATABASE_PASSWORD }}"
```

Secrets can leak through logs, command arguments, process inspection, artifacts, or debugging output.

Prefer environment injection:

```yaml
env:
  DATABASE_PASSWORD: ${{ secrets.TEST_DATABASE_PASSWORD }}
```

and consume it from the application.

For ordinary integration tests, prefer non-sensitive disposable credentials rather than repository secrets whenever possible.

---

## Untrusted Pull Requests

A secure architecture is:

```text
Fork PR
   ↓
Untrusted validation
   ↓
No production secrets
   ↓
No privileged runner
   ↓
No production deployment
```

Do not combine:

```text
untrusted checkout
+
privileged job container
+
self-hosted runner
+
production credentials
```

---

## Self-Hosted Runner Considerations

Containerization does not eliminate self-hosted runner risk.

A malicious job can potentially attack:

- Host filesystem
- Docker daemon
- Network
- Credentials
- Other workloads

For sensitive environments:

```text
Untrusted PR
   ↓
GitHub-hosted or isolated ephemeral runner

Trusted deployment
   ↓
Dedicated deployment runner/group
```

Separate trust zones.

---

## Performance Considerations

Container startup and service initialization contribute to CI duration.

Measure:

```text
Runner provisioning
+
Image pull
+
Container startup
+
Service initialization
+
Dependency installation
+
Test execution
```

Optimize through:

- Appropriate images
- Dependency caching
- Docker layer caching
- Prebuilt CI images
- Smaller test environments
- Parallel execution
- Targeted integration tests

Do not optimize by weakening isolation.

---

## Resource Constraints

Service containers consume runner resources.

A matrix such as:

```text
Python 3.11 × PostgreSQL
Python 3.12 × PostgreSQL
Python 3.13 × PostgreSQL
```

creates multiple database instances.

Add Redis and the resource footprint increases further.

Monitor:

- CPU
- Memory
- Disk
- Container startup time
- Test duration

---

## High Availability and CI

CI service containers are normally disposable rather than highly available.

Do not build HA infrastructure merely to support ordinary CI integration tests.

Instead:

```text
Disposable test infrastructure
+
Deterministic setup
+
Fast recovery
```

For production deployment testing, use an environment whose availability characteristics match the actual system being validated.

---

## Reliability Principles

A reliable container test environment should be:

- Disposable
- Deterministic
- Versioned
- Isolated
- Readiness-aware
- Reproducible
- Observable

Avoid relying on:

```text
Timing assumptions
Shared databases
Persistent runner state
Floating image versions
Undocumented host configuration
```

---

## Disaster Recovery Considerations

CI service containers normally do not require traditional database backup and recovery.

The desired recovery mechanism is:

```text
Destroy environment
      ↓
Recreate environment
      ↓
Run migrations
      ↓
Run tests
```

The ability to recreate the environment is more valuable than preserving the test database.

---

## Observability

Capture enough evidence to diagnose failures:

```text
Workflow logs
Job logs
Application logs
Service logs
Test reports
Coverage reports
Container health
Build metadata
```

For failed integration tests, upload useful reports as artifacts.

Avoid uploading secrets or sensitive database dumps.

---

## Failure-Domain Troubleshooting Matrix

| Symptom | Likely Domain | First Check |
|---|---|---|
| Service unavailable | Networking/readiness | Host + port |
| DNS failure | Container networking | Service label |
| Connection refused | Readiness/port | Health status |
| Authentication failure | Configuration | User/password/database |
| Image not found | Registry/image | Image/tag |
| Package installation failure | Container image | System dependencies |
| Command not found | Runtime image | Installed tools |
| Tests flaky | Readiness/race | Service startup |
| Only matrix jobs fail | Resource isolation | Matrix dimensions |
| Docker build fails | Docker runtime | Socket/Buildx |
| Job container exits | Image/entrypoint | Container logs |
| Redis unavailable | Service/network | `redis:6379` |
| PostgreSQL unavailable | Service/readiness | `pg_isready` |

---

## Practical Diagnostic Sequence

When an integration test fails:

### Identify the execution model

```text
Runner job?
Job container?
Service container?
Docker Compose?
```

### Verify services

```text
Correct image
Correct environment
Correct health check
Correct lifecycle
```

### Verify networking

```text
Hostname
Port
Network namespace
Published ports
```

### Verify readiness

```text
Healthy
Accepting connections
Database initialized
```

### Verify application configuration

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
Redis URL
Kafka configuration
```

### Verify dependencies

```text
Python packages
Native libraries
System binaries
```

### Reproduce

Run the smallest failing connectivity test before running the entire suite.

---

## Useful Diagnostic Commands

### Docker

```bash
docker ps
docker ps -a
docker images
docker logs <container>
docker inspect <container>
docker stats
```

### PostgreSQL

```bash
pg_isready -h postgres -p 5432
```

### MySQL

```bash
mysqladmin ping -h mysql -P 3306
```

### Redis

```bash
redis-cli -h redis ping
```

### DNS

```bash
getent hosts postgres
getent hosts redis
```

### TCP Connectivity

```bash
nc -zv postgres 5432
nc -zv redis 6379
```

Use only the tools available in the execution image or install them as part of a controlled CI image.

---

## GitHub CLI for Container Failures

Inspect workflow runs:

```bash
gh run list
```

Inspect a run:

```bash
gh run view <run-id>
```

Inspect failed logs:

```bash
gh run view <run-id> --log-failed
```

Rerun after changing the workflow:

```bash
gh run rerun <run-id>
```

The CLI is useful for retrieving workflow evidence, while container-specific diagnostics still need to run inside the relevant workflow environment.

---

## Common Misconfigurations

### Using `localhost` From a Job Container

Incorrect:

```text
DATABASE_HOST=localhost
```

when PostgreSQL is a service container.

Prefer:

```text
DATABASE_HOST=postgres
```

### Publishing Ports Unnecessarily

A containerized job communicating with its service through the internal network generally does not need host port publishing.

### No Readiness Check

Starting tests immediately after service creation creates intermittent failures.

### Using `latest`

Floating images make CI behavior less deterministic.

### Installing Everything at Runtime

Large dependency and tool installation steps increase startup time and failure surface.

### Using Production Secrets

Integration tests should not require production credentials.

---

## Production Pipeline Example

A mature Python CI pipeline can be structured as:

```yaml
name: Backend CI

on:
  pull_request:
  push:
    branches:
      - main

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
          POSTGRES_PASSWORD: test-password
          POSTGRES_DB: app_test
        options: >-
          --health-cmd="pg_isready -U app -d app_test"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

      redis:
        image: redis:7
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: postgresql://app:test-password@postgres:5432/app_test
        run: python manage.py migrate

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://app:test-password@postgres:5432/app_test
          REDIS_URL: redis://redis:6379/0
        run: pytest -m integration
```

The architecture is:

```text
Pull Request
    ↓
GitHub-hosted runner
    ↓
Python job container
    ├── PostgreSQL service
    └── Redis service
            ↓
        Integration Tests
            ↓
        Coverage / Reports
            ↓
        Build
            ↓
        Immutable Artifact
```

---

## Container and Service Container Failure Model

The most useful mental model is to separate failure domains:

```mermaid
flowchart TD
    A[Integration Test Failure] --> B{Execution Environment}
    B --> C[Runner]
    B --> D[Job Container]
    B --> E[Service Container]

    D --> F{Application Failure}
    D --> G{Dependency Failure}

    E --> H{Startup Failure}
    E --> I{Readiness Failure}
    E --> J{Network Failure}

    G --> K[Python/System Dependencies]
    J --> L[Hostname/Port]
    I --> M[Health Check]
    H --> N[Image/Configuration]

    C --> O[Resource/Runner Failure]
```

Do not debug all layers simultaneously.

Isolate the smallest failing boundary.

---

## Architecture Trade-offs

| Architecture | Reproducibility | Complexity | Isolation | Startup Cost |
|---|---|---|---|---|
| Runner + services | High | Low | Good | Low |
| Job container + services | Higher | Low | Strong | Medium |
| Docker Compose | High | Medium | Strong | Medium |
| Ephemeral environment | Very high | High | Strongest | High |

For most backend integration tests:

```text
Job container + service containers
```

is a strong balance between reproducibility and operational simplicity.

For complex distributed-system tests:

```text
Docker Compose
or
Ephemeral environment
```

may be more appropriate.

---

## Senior Engineering Considerations

A senior engineer should ask:

### Is containerization solving a real problem?

Do not add containers merely because production uses Docker.

### Is the network model explicit?

Every test environment should clearly define:

```text
Client
Service
Hostname
Port
Network
Readiness
```

### Is the environment disposable?

A test should not depend on state left by a previous job.

### Is the environment reproducible?

Versions, images, configuration, and initialization should be deterministic.

### Is the trust boundary clear?

Untrusted PR code should not gain access to privileged infrastructure merely because it executes inside a container.

### Is the failure observable?

A failed test should provide enough logs and metadata to distinguish application, container, network, and service failures.

---

## Interview Scenarios

### PostgreSQL works locally but fails in GitHub Actions. What do you check?

Check:

```text
Execution model
Host name
Port
Service readiness
Credentials
Database name
Environment variables
Container networking
```

Do not assume the local Docker networking model matches GitHub Actions.

---

### Why does `localhost` sometimes work and sometimes fail?

Because the meaning of `localhost` depends on where the application process runs.

```text
Runner process
    → localhost = runner

Job container
    → localhost = job container
```

A service container is a different network endpoint.

---

### How would you prevent flaky PostgreSQL tests?

Use:

- Explicit image versions
- Health checks
- Deterministic initialization
- Test database isolation
- Correct service hostname
- Explicit migrations
- Appropriate connection retry behavior

Avoid arbitrary sleeps.

---

### Would you use service containers for Kafka?

It depends on the test scope.

For a lightweight integration test, possibly.

For complex Kafka behavior involving multiple brokers, custom listeners, partitions, replication, or realistic topology, Docker Compose or an ephemeral environment may provide better control.

---

### How would you secure service containers for fork pull requests?

Keep them disposable and isolated, use no production secrets, minimize `GITHUB_TOKEN` permissions, avoid privileged Docker access, and use GitHub-hosted or appropriately isolated ephemeral runners.

---

### What is the difference between a job container and a service container?

A job container is where workflow steps execute.

A service container provides infrastructure that the job consumes.

```text
Job container
    ↓
Application/Test Process
    ↓
Service container
```

---

### How would you diagnose a connection-refused error?

Follow:

```text
Is service running?
    ↓
Is service healthy?
    ↓
Is hostname correct?
    ↓
Is port correct?
    ↓
Is client in the expected network?
    ↓
Are credentials correct?
    ↓
Can a minimal client connect?
```

This is more reliable than changing configuration randomly.

---

## Production Checklist

### Job Containers

- [ ] Image version is controlled.
- [ ] Required tools are installed.
- [ ] Shell assumptions are explicit.
- [ ] Working directory is understood.
- [ ] Native dependencies are available.
- [ ] Image architecture is compatible.

### Service Containers

- [ ] Images are version-controlled.
- [ ] Environment variables are correct.
- [ ] Health checks are configured.
- [ ] Readiness is validated.
- [ ] Credentials are disposable.
- [ ] Services are isolated per job.

### Networking

- [ ] Job execution model is known.
- [ ] Service hostname is correct.
- [ ] Port is correct.
- [ ] Published ports are used only when needed.
- [ ] DNS resolution can be diagnosed.
- [ ] Connectivity can be tested independently.

### Security

- [ ] No production secrets are used.
- [ ] Permissions follow least privilege.
- [ ] Untrusted PRs cannot access privileged infrastructure.
- [ ] Docker socket access is avoided unless required.
- [ ] Third-party actions are controlled.
- [ ] Runner isolation matches the trust boundary.

### Reliability

- [ ] No arbitrary startup sleeps.
- [ ] Service readiness is deterministic.
- [ ] Tests do not depend on persistent state.
- [ ] Matrix capacity is understood.
- [ ] Failures provide useful diagnostics.
- [ ] Integration environments are reproducible.

## Key Takeaways

- Distinguish **job containers**, **service containers**, and the **runner**; most container CI failures become easier to diagnose once the execution boundary is identified.
- Networking depends on where the application runs: runner-based jobs commonly use published `localhost` ports, while containerized jobs generally communicate with services using service-container names such as `postgres:5432`.
- Service startup is not the same as service readiness; use meaningful health checks instead of arbitrary `sleep` commands.
- Keep integration environments disposable, versioned, isolated, and security-conscious, especially for fork pull requests and self-hosted runners.
- Troubleshoot systematically across image, process, readiness, networking, configuration, dependencies, and resources rather than changing multiple layers at once.