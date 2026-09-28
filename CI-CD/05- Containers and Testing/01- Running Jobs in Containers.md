# 01- Running Jobs in Containers

## Overview

GitHub Actions can execute an entire job inside a container, allowing the workflow to use a controlled Linux environment instead of relying entirely on the software preinstalled on the GitHub-hosted runner.

This is useful for backend CI pipelines where reproducibility matters:

```text
GitHub Actions Runner
        │
        ▼
Containerized Job
        │
        ├── Python
        ├── Django / FastAPI
        ├── pytest
        ├── CLI tools
        └── Application dependencies
```

Running jobs in containers is different from using service containers.

- **Job container** — the steps of the job execute inside the specified container.
- **Service container** — an auxiliary container provides a dependency such as PostgreSQL, MySQL, or Redis.
- **Runner** — the GitHub-hosted or self-hosted machine that ultimately executes the workflow.

A common production-style testing architecture is:

```text
GitHub-hosted Runner
        │
        ├── Job Container
        │     ├── Python
        │     ├── pytest
        │     └── Application
        │
        ├── PostgreSQL Service
        │
        └── Redis Service
```

## Job Containers vs Service Containers

These concepts solve different problems.

| Component | Purpose | Example |
|---|---|---|
| Runner | Executes the GitHub Actions job | Ubuntu runner |
| Job container | Provides the execution environment | `python:3.12-slim` |
| Service container | Provides an external dependency | PostgreSQL |
| Docker action | Executes a custom action inside a container | Security scanner |
| Docker build | Builds an application image | Backend image |

A job container is primarily about **where workflow steps execute**.

A service container is primarily about **what external services those steps communicate with**.

## Why Run a Job in a Container?

A containerized job provides a more predictable execution environment.

Without a job container:

```text
GitHub-hosted Runner
 ├── Preinstalled Python
 ├── Preinstalled CLI tools
 ├── OS packages
 └── Workflow steps
```

With a job container:

```text
GitHub-hosted Runner
 └── Container
      ├── Defined base image
      ├── Defined runtime
      ├── Defined system packages
      └── Workflow steps
```

This can reduce differences between developers, CI environments, and other containerized execution environments.

Typical use cases include:

- Python version standardization.
- Linux distribution consistency.
- Integration testing.
- Specialized build environments.
- Reproducible CLI tooling.
- Legacy dependency isolation.
- Backend applications with known system requirements.

## Basic Job Container

A job can specify a container with the `container` property.

```yaml
name: Python CI

on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

The runner starts the container and executes the job steps inside it.

The high-level lifecycle is:

```text
Workflow Trigger
      ↓
Runner Allocated
      ↓
Container Started
      ↓
Repository Checked Out
      ↓
Steps Execute in Container
      ↓
Container Exits
      ↓
Job Completes
```

## Container Image Selection

The image defines the baseline environment.

For Python:

```yaml
container:
  image: python:3.12-slim
```

For a private registry:

```yaml
container:
  image: ghcr.io/company/backend-ci:1.4.0
```

For authenticated registries:

```yaml
container:
  image: ghcr.io/company/backend-ci:1.4.0
  credentials:
    username: ${{ secrets.REGISTRY_USERNAME }}
    password: ${{ secrets.REGISTRY_PASSWORD }}
```

Use intentionally versioned images rather than mutable tags when reproducibility is important.

Prefer:

```text
backend-ci:1.4.0
```

over:

```text
backend-ci:latest
```

For stronger immutability, pin the image by digest where practical:

```text
backend-ci@sha256:<digest>
```

## Job Container Configuration

GitHub Actions supports additional container configuration.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim
      env:
        PYTHONUNBUFFERED: "1"
        DJANGO_SETTINGS_MODULE: config.settings.test
      ports:
        - 8000
      volumes:
        - test-data:/workspace/data
      options: --cpus 2 --memory 4g

    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        run: pytest
```

The exact options should be chosen according to the runner environment and workload.

Avoid adding configuration merely because Docker supports it. Every additional container option introduces operational complexity.

## Environment Variables

Environment variables can be configured at different levels.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim
      env:
        PYTHONUNBUFFERED: "1"

    env:
      DJANGO_SETTINGS_MODULE: config.settings.test

    steps:
      - uses: actions/checkout@v4

      - name: Test
        env:
          TEST_MODE: "true"
        run: pytest
```

Keep environment configuration close to the scope where it is required.

Avoid placing secrets into images or Dockerfiles.

Prefer workflow-provided secrets and environment variables.

## Working Directory

The job's working directory determines where commands execute.

For example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    defaults:
      run:
        working-directory: backend

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Test
        run: pytest
```

The repository is available to the job container through the Actions workspace.

Be careful when changing working directories because relative paths used by:

- pytest
- coverage
- Docker
- scripts
- configuration files
- artifact uploads

may depend on the workspace location.

## Shell Behavior

Commands execute in the job container.

```yaml
- name: Python version
  run: python --version

- name: Operating system
  run: cat /etc/os-release
```

This means the command availability depends on the container image.

For example, a minimal image may not contain:

```text
curl
git
bash
gcc
make
```

Do not assume that tools available on `ubuntu-latest` are automatically available inside the container.

## Shell Selection

If a command requires Bash, specify it explicitly where appropriate.

```yaml
- name: Run deployment script
  shell: bash
  run: ./scripts/deploy.sh
```

However, the selected shell must exist in the container.

A minimal image may provide `/bin/sh` without Bash.

For Python-focused containers, verify the base image before relying on OS-level tooling.

## GitHub Actions and Container Requirements

Some GitHub Actions are implemented using JavaScript or Docker and may have runtime requirements that differ from ordinary shell steps.

Before using an action inside a containerized job, verify that the action supports the execution environment.

For example:

```yaml
container:
  image: python:3.12-slim

steps:
  - uses: actions/checkout@v4

  - run: pytest
```

A common mistake is assuming that every action behaves exactly like a shell command.

Actions have their own runtime model.

## Networking Model

Networking becomes particularly important when combining job and service containers.

Consider:

```text
Runner
 │
 ├── Job Container
 │       │
 │       └── Application Tests
 │
 ├── PostgreSQL Service
 │
 └── Redis Service
```

The job container and service containers participate in the job's container network.

This allows backend integration tests to communicate with services without exposing service ports to the public network.

## Service Containers

Service containers are appropriate for dependencies such as:

- PostgreSQL.
- MySQL.
- Redis.

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app_test

      redis:
        image: redis:7

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_HOST: postgres
          DATABASE_PORT: "5432"
          REDIS_HOST: redis
          REDIS_PORT: "6379"
        run: pytest
```

The service names can be used as network hostnames in the containerized job.

For example:

```text
postgres
redis
```

rather than assuming:

```text
localhost
```

## PostgreSQL Integration

A Django or FastAPI integration-test job can use PostgreSQL as a service.

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app_test
```

Application configuration:

```yaml
env:
  DATABASE_HOST: postgres
  DATABASE_PORT: "5432"
  DATABASE_NAME: app_test
  DATABASE_USER: app
  DATABASE_PASSWORD: app
```

The application should connect using the service hostname.

```text
Test Container
      │
      │ TCP
      ▼
postgres:5432
```

Do not assume that a service is immediately ready simply because its container has started.

## Redis Integration

Redis can be provided as a service container.

```yaml
services:
  redis:
    image: redis:7
```

Application configuration:

```yaml
env:
  REDIS_HOST: redis
  REDIS_PORT: "6379"
```

For Django:

```text
Django
  ↓
Redis
```

For FastAPI:

```text
FastAPI
  ↓
Redis
```

For Celery:

```text
FastAPI / Django
      ↓
    Celery
      ↓
    Redis
```

The test environment should validate the same connectivity assumptions used by the application.

## MySQL Integration

MySQL can be configured similarly.

```yaml
services:
  mysql:
    image: mysql:8.4
    env:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: app_test
      MYSQL_USER: app
      MYSQL_PASSWORD: app
```

The application should use the service hostname:

```text
mysql
```

rather than:

```text
localhost
```

when both the application and database run as containers.

## Service Readiness

Container startup and service readiness are not necessarily the same event.

```text
Container Started
       ≠
Application Ready
```

For example:

```text
PostgreSQL process starts
       ↓
Database initialization
       ↓
Database accepts connections
```

Tests should not blindly assume that the first connection attempt will succeed.

Where necessary, use readiness checks or retry logic.

Example:

```bash
for attempt in {1..30}; do
  if pg_isready -h postgres -U app; then
    exit 0
  fi

  sleep 2
done

echo "PostgreSQL did not become ready" >&2
exit 1
```

The readiness strategy should be bounded.

Avoid infinite retry loops.

## Python Backend Example

A realistic Django pipeline can use a Python job container with PostgreSQL and Redis.

```yaml
name: Django CI

on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: django
          POSTGRES_PASSWORD: django
          POSTGRES_DB: django_test

      redis:
        image: redis:7

    env:
      DJANGO_SETTINGS_MODULE: config.settings.test
      DATABASE_HOST: postgres
      DATABASE_PORT: "5432"
      DATABASE_NAME: django_test
      DATABASE_USER: django
      DATABASE_PASSWORD: django
      REDIS_HOST: redis
      REDIS_PORT: "6379"

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run migrations
        run: python manage.py migrate --noinput

      - name: Run tests
        run: pytest

      - name: Generate coverage
        run: |
          coverage run -m pytest
          coverage xml
```

This creates a reproducible test environment around the backend runtime and its dependencies.

## FastAPI Example

A FastAPI service can use the same model.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: fastapi
          POSTGRES_PASSWORD: fastapi
          POSTGRES_DB: fastapi_test

      redis:
        image: redis:7

    env:
      DATABASE_URL: postgresql://fastapi:fastapi@postgres:5432/fastapi_test
      REDIS_URL: redis://redis:6379/0

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

For production repositories, database credentials should normally come from controlled test configuration rather than copying production credentials into the workflow.

## Integration Testing Architecture

A complete backend integration-test environment can look like:

```mermaid
flowchart TD
    A[GitHub Actions Runner] --> B[Job Container]

    B --> C[Python Application]
    B --> D[pytest]

    B --> E[PostgreSQL Service]
    B --> F[Redis Service]

    C --> E
    C --> F
    D --> C

    D --> G[Coverage Report]
    G --> H[Test Artifact]
```

The job container provides the application execution environment while services provide external dependencies.

## Matrix Testing with Containers

Containers combine well with matrix testing.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      matrix:
        python-version:
          - "3.11"
          - "3.12"
          - "3.13"

    container:
      image: python:${{ matrix.python-version }}-slim

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

This produces independent test environments:

```text
                 ┌── Python 3.11
Pull Request ────┼── Python 3.12
                 └── Python 3.13
```

For database compatibility testing, the matrix can also vary the service image.

Use matrix testing when the compatibility coverage provides meaningful value.

Do not create unnecessarily large matrices because each combination consumes runner resources.

## Artifacts from Containerized Jobs

Test outputs can be uploaded after the containerized test execution.

```yaml
- name: Upload coverage
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@v4
  with:
    name: coverage
    path: coverage.xml
```

Artifacts are appropriate for:

- Coverage reports.
- Test reports.
- Debug logs.
- Build outputs.
- Diagnostic files.

Do not confuse artifacts with caches.

| Mechanism | Purpose |
|---|---|
| Artifact | Preserve or transfer output |
| Cache | Reuse expensive-to-generate state |

## Dependency Caching

Containerized jobs can still use dependency caching.

For Python, cache keys should incorporate dependency definitions.

```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

Caching should improve performance without becoming a correctness dependency.

A cache miss should still result in a successful build.

## Custom CI Images

Organizations with large numbers of workflows may create a standard CI image.

Example:

```dockerfile
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       git \
       build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pytest \
    coverage
```

Published internally:

```text
ghcr.io/company/python-ci:3.12-1.2.0
```

Consumed by:

```yaml
container:
  image: ghcr.io/company/python-ci:3.12-1.2.0
```

This can standardize tooling across many repositories.

However, the image becomes another dependency that requires:

- Versioning.
- Security scanning.
- Patch management.
- Ownership.
- Release controls.

## Container Image Maintenance

A CI image should have a defined lifecycle.

```text
Base Image Update
      ↓
Dependency Update
      ↓
Security Scan
      ↓
CI Validation
      ↓
Versioned Release
      ↓
Consumer Adoption
```

Do not let a shared CI image remain unchanged indefinitely.

Outdated base images can introduce known vulnerabilities and unsupported runtimes.

## Security Considerations

Containerized jobs do not automatically make CI secure.

The runner still represents an important trust boundary.

Potential risks include:

- Malicious dependencies.
- Untrusted pull request code.
- Container escape vulnerabilities.
- Secrets exposure.
- Privileged containers.
- Compromised base images.
- Malicious CI images.
- Persistent self-hosted runner state.

Avoid unnecessary privileges.

Do not use privileged containers unless there is a specific requirement and the security implications are understood.

## Secrets in Containers

Secrets should be passed at runtime rather than baked into images.

Bad:

```dockerfile
ENV AWS_ACCESS_KEY_ID=...
ENV AWS_SECRET_ACCESS_KEY=...
```

Prefer workflow-provided credentials.

For AWS deployments, prefer OIDC where applicable:

```text
GitHub Actions
      ↓
OIDC Token
      ↓
AWS STS
      ↓
Temporary Credentials
```

Secrets should never be written into Dockerfiles, source code, or generated artifacts.

## Pull Request Security

A containerized job may execute repository-controlled code.

For example:

```text
Pull Request
     ↓
Workflow
     ↓
Container
     ↓
Untrusted Code
```

The container boundary should not be treated as permission to expose sensitive credentials.

Be particularly careful with:

- Fork pull requests.
- `pull_request_target`.
- Self-hosted runners.
- Private network access.
- Repository secrets.

The primary security question is:

> What can code executing inside this container access?

## Self-Hosted Runners

Containers can reduce environmental differences on self-hosted runners, but they do not remove runner security risks.

A self-hosted runner may have access to:

- Internal networks.
- Cloud credentials.
- Source repositories.
- Cached files.
- Internal services.

For untrusted workloads, consider ephemeral isolated runners.

```text
GitHub
  ↓
Ephemeral Runner
  ↓
Job Container
  ↓
Test Environment
  ↓
Runner Destroyed
```

Persistent runners require stronger cleanup and isolation controls.

## Container Networking Pitfalls

Common mistakes include assuming:

```text
localhost
```

always refers to the desired service.

Inside a container:

```text
localhost
```

normally refers to that container itself.

For service containers, use the service hostname:

```text
postgres
redis
mysql
```

For example:

```text
DATABASE_HOST=postgres
REDIS_HOST=redis
```

The exact networking behavior depends on whether the workflow uses a job container, service containers, or host-based execution.

## Container Volumes

Volumes can be useful when data must persist during execution.

Example:

```yaml
container:
  image: python:3.12-slim
  volumes:
    - test-data:/workspace/data
```

However, CI jobs should generally minimize stateful dependencies.

Prefer:

```text
Fresh Environment
    ↓
Build/Test
    ↓
Artifacts
    ↓
Environment Destroyed
```

over persistent mutable state.

This improves reproducibility and reduces cross-run contamination.

## Performance Considerations

Containers introduce some overhead:

- Image download.
- Image extraction.
- Container startup.
- Dependency installation.
- Service startup.

Reduce unnecessary overhead through:

- Smaller images.
- Dependency caching.
- Reusable CI images.
- Docker layer caching where appropriate.
- Parallel matrix execution.
- Avoiding repeated setup.

A smaller image is not automatically better if it creates excessive setup work.

The goal is efficient total job execution.

## Scalability

For many repositories, a shared containerized CI model can standardize execution.

```text
                 ┌── Service A
                 │
Shared CI Image ─┼── Service B
                 │
                 └── Service C
```

However, a single shared image can become a platform bottleneck.

Use versioned images so teams can migrate independently:

```text
python-ci:3.11-1.x
python-ci:3.12-1.x
python-ci:3.13-1.x
```

Avoid forcing every repository to upgrade simultaneously unless the organization explicitly requires synchronized releases.

## Reliability

A containerized test environment should be disposable.

Good CI architecture:

```text
Create
  ↓
Initialize
  ↓
Test
  ↓
Collect Results
  ↓
Destroy
```

Avoid relying on state left by previous jobs.

This is especially important for:

- Database schemas.
- Redis data.
- Temporary files.
- Generated credentials.
- Application caches.

## High Availability and Disaster Recovery

CI containers are generally ephemeral, so application-style HA is usually unnecessary for the individual container.

The important reliability concern is the CI platform around them:

```text
Workflow
  ↓
Runner Availability
  ↓
Container Availability
  ↓
Dependency Availability
  ↓
Artifact Availability
```

For critical pipelines, ensure that:

- Workflows can be rerun safely.
- Artifacts have appropriate retention.
- CI images are versioned.
- Container registries are reliable.
- Critical action dependencies are controlled.
- Deployment actions are idempotent.

## Cost Considerations

Containerized jobs can increase runtime if images are large or dependencies are repeatedly installed.

For high-volume CI:

```text
Large Image
+ Slow Dependency Installation
+ Frequent Runs
=
Significant Runner Cost
```

Optimize high-frequency paths first.

Useful techniques include:

- Smaller base images.
- Dependency caching.
- Parallel tests.
- Appropriate matrix size.
- Reusable CI images.
- Avoiding unnecessary integration environments.

Do not optimize away tests merely to reduce CI cost.

## Common Mistakes

### Assuming the Runner Environment Still Applies

Inside a job container:

```yaml
container:
  image: python:3.12-slim
```

commands execute inside the container, not directly on the runner host.

Verify:

```bash
python --version
cat /etc/os-release
command -v bash
```

### Using `localhost` for Service Containers

Incorrect:

```text
DATABASE_HOST=localhost
```

Often correct:

```text
DATABASE_HOST=postgres
```

when PostgreSQL is defined as a service container.

### Using `latest`

Avoid:

```yaml
container:
  image: company/python-ci:latest
```

for production-critical pipelines.

Use controlled versions.

### Assuming Container Startup Means Service Readiness

A running PostgreSQL container does not necessarily mean PostgreSQL is ready for connections.

Use bounded readiness checks.

### Installing Too Much at Runtime

Repeatedly installing the same system packages increases execution time.

For stable toolchains, consider a versioned CI image.

### Baking Secrets into Images

Never place credentials in:

- Dockerfiles.
- Image layers.
- Source code.
- Build arguments when they can become persisted in image history.
- Generated artifacts.

### Making the Image Too Minimal

A tiny image may lack required tools such as:

```text
bash
git
curl
gcc
make
```

Balance image size with operational requirements.

### Overusing Privileged Containers

Privileged execution significantly increases the security boundary.

Use it only when there is a documented requirement.

## Troubleshooting

Use the standard troubleshooting model:

```text
Symptom
→ Possible Causes
→ Isolation Strategy
→ Commands / Checks
→ Root Cause
→ Corrective Action
→ Prevention
```

### Job Container Does Not Start

Check:

- Image name.
- Image tag.
- Registry authentication.
- Image architecture.
- Registry availability.
- Container configuration.

Useful checks:

```bash
docker pull <image>
docker inspect <image>
```

### Command Is Not Found

Check whether the tool exists inside the container:

```bash
command -v git
command -v bash
command -v curl
python --version
```

If missing, either:

- Install it.
- Use a better base image.
- Build a standard CI image.

### PostgreSQL Connection Fails

Check:

```text
DATABASE_HOST
DATABASE_PORT
PostgreSQL credentials
Service name
Service readiness
```

Confirm the application uses:

```text
postgres
```

rather than an incorrect hostname.

### Redis Connection Fails

Check:

```text
REDIS_HOST=redis
REDIS_PORT=6379
```

Then verify Redis readiness and application configuration.

### Tests Pass Locally but Fail in CI

Compare:

```text
Python Version
OS
System Packages
Environment Variables
Dependency Versions
Database
Redis
Timezone
Locale
Filesystem
```

Containerized jobs can make these differences easier to identify because the environment is explicitly defined.

### Container Image Pull Is Slow

Investigate:

- Image size.
- Registry latency.
- Number of workflow runs.
- Matrix size.
- Repeated image downloads.

Consider a smaller or better-optimized CI image.

### Service Is Not Ready

Add bounded readiness checks rather than arbitrary long sleeps.

Prefer:

```text
Probe
 ↓
Ready?
 ├── Yes → Continue
 └── No → Retry with bounded timeout
```

over:

```bash
sleep 60
```

without checking actual service state.

## Production Architecture

A production backend CI architecture can combine containerized jobs with service containers, reusable workflows, and immutable deployment artifacts.

```mermaid
flowchart TD
    A[Pull Request] --> B[Reusable CI Workflow]

    B --> C[Containerized Lint Job]
    B --> D[Containerized Unit Test Job]
    B --> E[Containerized Integration Test Job]

    E --> F[PostgreSQL Service]
    E --> G[Redis Service]

    C --> H[Build]
    D --> H
    E --> H

    H --> I[Docker Image]
    I --> J[ECR]

    J --> K[Staging]
    K --> L[Approval]
    L --> M[Production]

    M --> N[Health Validation]
    N --> O[Monitoring]
```

The important boundaries are:

```text
Workflow
→ Orchestration

Job Container
→ Execution Environment

Service Container
→ Test Dependency

Docker Image
→ Deployable Application Artifact
```

## Containerized CI Design Checklist

Before adopting job containers, verify:

### Execution

- The required runtime exists in the image.
- Required shell tools exist.
- The workspace is accessible.
- Working directories are correct.
- Actions used by the job support the execution model.

### Networking

- Service hostnames are correct.
- Ports are correct.
- Services become ready before tests execute.
- Private network requirements are understood.

### Security

- No secrets are baked into images.
- Permissions are minimal.
- Images are trusted and scanned.
- Untrusted code cannot access unnecessary credentials.
- Self-hosted runners are appropriately isolated.

### Reliability

- Jobs are reproducible.
- Services start deterministically.
- Readiness checks are bounded.
- Tests do not depend on persistent state.
- Artifacts are collected on failure where useful.

### Performance

- Images are appropriately sized.
- Dependencies are cached.
- Matrix size is justified.
- High-frequency setup work is optimized.

### Operations

- CI images are versioned.
- Base images are patched.
- Ownership is defined.
- Failures are diagnosable.
- Rollbacks or image-version reversion are possible.

## Interview Scenarios

### Design a Django Integration-Test Pipeline

Requirements:

- Python 3.12.
- PostgreSQL.
- Redis.
- pytest.
- Coverage report.

A reasonable design is:

```text
GitHub Runner
    ↓
Python Job Container
    ├── Django
    ├── pytest
    └── Coverage
    │
    ├── PostgreSQL Service
    └── Redis Service
```

### Why Use a Job Container?

Discuss:

- Environment reproducibility.
- Runtime isolation.
- Dependency consistency.
- Image maintenance.
- Startup overhead.
- Security boundaries.

### Job Container vs Service Container

Explain:

```text
Job Container
→ Executes workflow commands.

Service Container
→ Provides a dependency consumed by those commands.
```

### Why Not Use `localhost`?

Explain the container networking model and service hostnames.

### How Would You Reduce CI Time?

Consider:

```text
Smaller Images
+
Dependency Cache
+
CI Image
+
Parallel Jobs
+
Appropriate Matrix Size
```

Do not remove meaningful test coverage merely to reduce runtime.

### How Would You Secure a Self-Hosted Runner?

Discuss:

- Ephemeral runners.
- Runner groups.
- Network segmentation.
- Least privilege.
- Cleanup.
- Restricted repository access.
- Container isolation.
- Untrusted-code boundaries.

### How Would You Diagnose a CI-Only Failure?

Compare:

```text
Runtime
OS
Packages
Environment
Dependencies
Database
Redis
Networking
Filesystem
```

Then isolate the smallest difference between local and CI execution environments.

## Key Takeaways

- A job container defines where workflow steps execute, while service containers provide dependencies such as PostgreSQL, MySQL, and Redis.
- Containerized jobs improve execution consistency, but the container image, networking, readiness, dependencies, and security boundaries must be explicitly managed.
- Backend integration testing commonly combines a Python job container with PostgreSQL and Redis service containers, followed by pytest, coverage generation, and artifact collection.
- Production containerized CI should use versioned images, bounded readiness checks, least-privilege credentials, reproducible environments, dependency caching, and controlled image maintenance.
- Containers improve isolation and reproducibility but do not eliminate CI security risks, runner risks, networking problems, image supply-chain concerns, or the need for systematic troubleshooting.