# 02- Service Containers

## Overview

Service containers provide temporary supporting services to a GitHub Actions job.

They are primarily used when application tests require external dependencies such as:

- PostgreSQL
- MySQL
- Redis
- Other containerized infrastructure dependencies

A typical backend integration-test environment looks like:

```text
GitHub Actions Runner
        │
        ├── Job
        │    └── Python / Django / FastAPI / pytest
        │
        ├── PostgreSQL Service
        │
        └── Redis Service
```

The job executes application and test code, while service containers provide the infrastructure that the code depends on.

This is especially useful for integration testing because the workflow can create a clean, isolated dependency environment for every run.

## Service Containers vs Job Containers

These concepts should not be confused.

| Component | Responsibility | Example |
|---|---|---|
| Runner | Hosts the GitHub Actions execution | `ubuntu-latest` |
| Job container | Provides the environment where job steps execute | `python:3.12-slim` |
| Service container | Provides an external dependency | `postgres:16` |
| Docker action | Runs a custom action in a container | Security scanner |
| Application container | Represents the deployable application | Django API image |

The distinction is:

```text
Job Container
→ Where the workflow commands execute

Service Container
→ What the workflow commands connect to
```

A workflow can use service containers without using a job container.

## Why Service Containers Exist

Backend applications rarely operate in isolation.

A Django application may depend on:

```text
Django
 ├── PostgreSQL
 ├── Redis
 └── Celery
```

A FastAPI application may depend on:

```text
FastAPI
 ├── PostgreSQL
 ├── Redis
 └── Kafka
```

Running integration tests against only mocks can miss problems involving:

- Database connectivity.
- SQL behavior.
- Transactions.
- Migrations.
- Connection pooling.
- Redis serialization.
- Cache behavior.
- Service networking.
- Authentication.
- Infrastructure configuration.

Service containers allow CI to exercise these real dependencies in a disposable environment.

## Basic Service Container

A simple PostgreSQL service:

```yaml
name: Integration Tests

on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app_test

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_HOST: localhost
          DATABASE_PORT: "5432"
          DATABASE_NAME: app_test
          DATABASE_USER: test
          DATABASE_PASSWORD: test
        run: pytest
```

When the job itself runs directly on the runner, service ports can be exposed to the runner and accessed through `localhost`.

The networking model changes when a job container is also used.

## Service Networking

There are two common execution models.

### Job Runs Directly on Runner

```text
Runner
 ├── Job Steps
 │
 └── PostgreSQL Container
        ↑
        │ localhost:5432
```

Example:

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

The test process can normally use:

```text
localhost:5432
```

### Job Runs Inside a Container

```text
Runner
 │
 ├── Job Container
 │      │
 │      └── pytest
 │
 └── PostgreSQL Service
```

The job container and service container share the job's container network.

The service hostname can be used:

```text
postgres:5432
```

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

    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        env:
          DATABASE_HOST: postgres
          DATABASE_PORT: "5432"
        run: pytest
```

The key rule is:

```text
Host-based job
→ localhost + exposed service port

Containerized job
→ service hostname + service port
```

## Service Container Configuration

A service can define:

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: app_test
    ports:
      - 5432:5432
    options: >-
      --health-cmd "pg_isready -U test -d app_test"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

Important configuration areas include:

| Configuration | Purpose |
|---|---|
| `image` | Service container image |
| `env` | Service configuration |
| `ports` | Expose service ports to the runner |
| `options` | Additional container runtime options |
| `credentials` | Authenticate to private container registries |

Use only the configuration required by the test environment.

## Environment Variables

Application configuration should explicitly point to the service.

For a host-based job:

```yaml
env:
  DATABASE_HOST: localhost
  DATABASE_PORT: "5432"
```

For a containerized job:

```yaml
env:
  DATABASE_HOST: postgres
  DATABASE_PORT: "5432"
```

For Redis:

```yaml
env:
  REDIS_HOST: redis
  REDIS_PORT: "6379"
```

Do not hard-code production endpoints into CI configuration.

A test environment should be isolated from production infrastructure.

## PostgreSQL Service

PostgreSQL is one of the most common service containers for backend integration tests.

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app_test
```

A Django application can then use:

```text
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=app_test
DATABASE_USER=app
DATABASE_PASSWORD=app
```

A typical flow is:

```text
Workflow
   ↓
PostgreSQL Starts
   ↓
Database Becomes Ready
   ↓
Django Migrations
   ↓
pytest
   ↓
Database Integration Tests
```

## PostgreSQL Health Checks

Container startup does not necessarily mean that PostgreSQL is ready to accept connections.

Use a health check where appropriate:

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: app_test
    options: >-
      --health-cmd "pg_isready -U test -d app_test"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

The distinction is important:

```text
Container Started
        ↓
PostgreSQL Process Started
        ↓
Initialization
        ↓
Database Ready
```

Tests should depend on readiness rather than merely container creation.

## MySQL Service

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
    ports:
      - 3306:3306
```

Application configuration:

```yaml
env:
  DATABASE_HOST: 127.0.0.1
  DATABASE_PORT: "3306"
  DATABASE_NAME: app_test
  DATABASE_USER: app
  DATABASE_PASSWORD: app
```

When the job uses a container, use the service hostname instead:

```yaml
env:
  DATABASE_HOST: mysql
  DATABASE_PORT: "3306"
```

## Redis Service

Redis is commonly used for:

- Caching.
- Celery brokers.
- Celery result backends.
- Distributed locks.
- Temporary application state.

Example:

```yaml
services:
  redis:
    image: redis:7
    ports:
      - 6379:6379
```

Application configuration:

```yaml
env:
  REDIS_HOST: localhost
  REDIS_PORT: "6379"
```

With a containerized job:

```yaml
env:
  REDIS_HOST: redis
  REDIS_PORT: "6379"
```

## Django Integration Testing

A Django project commonly requires both PostgreSQL and Redis.

```yaml
name: Django Integration Tests

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
```

This validates the application against real PostgreSQL and Redis instances instead of replacing them with mocks.

## FastAPI Integration Testing

FastAPI applications can use the same service-container architecture.

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

The application test suite can then exercise:

```text
HTTP API
  ↓
FastAPI
  ↓
Service Layer
  ↓
PostgreSQL
  ↓
Redis
```

## Celery and Redis

A backend using Celery may require Redis during integration testing.

```text
API
 ↓
Celery Task
 ↓
Redis Broker
 ↓
Worker
 ↓
PostgreSQL
```

A simple Redis service:

```yaml
services:
  redis:
    image: redis:7
```

For more complete integration testing, the worker itself may need to run as a separate process or job.

Service containers provide infrastructure dependencies; they do not automatically create additional application workers.

## Multiple Service Containers

Multiple services can coexist.

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app_test

  redis:
    image: redis:7

  mysql:
    image: mysql:8.4
    env:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: legacy_test
```

This is useful for integration testing systems that genuinely require multiple infrastructure dependencies.

However, every additional service increases:

- Startup time.
- Resource usage.
- Failure surface.
- CI complexity.

Only include dependencies required by the tests.

## Service Containers and Ports

Ports matter primarily when the job communicates with services through the runner network.

Example:

```yaml
services:
  postgres:
    image: postgres:16
    ports:
      - 5432:5432
```

For a containerized job, explicit host port publishing is often unnecessary because the job and service containers can communicate through the container network.

For example:

```yaml
container:
  image: python:3.12-slim

services:
  postgres:
    image: postgres:16
```

The application can connect to:

```text
postgres:5432
```

Avoid publishing ports unnecessarily.

Reducing exposed interfaces reduces complexity and the potential attack surface.

## Service Health and Readiness

Service health should be treated as part of test-environment initialization.

```mermaid
sequenceDiagram
    participant G as GitHub Runner
    participant S as PostgreSQL Service
    participant T as Test Job

    G->>S: Start container
    S->>S: Initialize database
    T->>S: Check readiness
    S-->>T: Ready
    T->>S: Connect
    S-->>T: Accept connection
    T->>S: Execute integration tests
```

A robust pipeline should distinguish:

```text
Infrastructure Failure
```

from:

```text
Application Test Failure
```

For example, if PostgreSQL never becomes ready, failing the test suite as though an application assertion failed makes diagnosis harder.

## Readiness Checks

A bounded readiness check can be implemented in a workflow step when necessary.

Example:

```bash
for attempt in {1..30}; do
  if pg_isready -h postgres -U test -d app_test; then
    echo "PostgreSQL is ready"
    exit 0
  fi

  sleep 2
done

echo "PostgreSQL did not become ready" >&2
exit 1
```

Avoid indefinite polling.

Avoid arbitrary large sleeps such as:

```bash
sleep 120
```

when a real readiness probe is available.

A good readiness mechanism should:

- Probe actual service state.
- Retry a bounded number of times.
- Fail with a clear message.
- Avoid unnecessary waiting.

## Integration Test Lifecycle

A clean service-container test lifecycle is:

```text
Workflow Trigger
      ↓
Runner Allocated
      ↓
Services Started
      ↓
Services Become Ready
      ↓
Application Dependencies Installed
      ↓
Migrations / Initialization
      ↓
Tests Execute
      ↓
Reports Generated
      ↓
Artifacts Uploaded
      ↓
Environment Destroyed
```

The environment should be disposable.

Do not rely on state surviving between workflow runs.

## Database Initialization

Database initialization may include:

```text
Create Database
      ↓
Run Migrations
      ↓
Load Required Fixtures
      ↓
Execute Tests
```

For Django:

```yaml
- name: Run migrations
  run: python manage.py migrate --noinput
```

For SQLAlchemy/Alembic:

```yaml
- name: Run migrations
  run: alembic upgrade head
```

Initialization should be deterministic.

## Test Isolation

Each workflow run should ideally receive a fresh database.

This prevents one test run from affecting another.

Good:

```text
Run A → PostgreSQL A
Run B → PostgreSQL B
Run C → PostgreSQL C
```

Avoid shared external test databases unless there is a specific architectural requirement.

Shared databases can create:

- Data collisions.
- Race conditions.
- Flaky tests.
- Cleanup problems.
- Cross-branch interference.

## Test Types

Service containers are most valuable for tests that require real infrastructure.

| Test Type | Service Containers |
|---|---|
| Pure unit test | Usually unnecessary |
| Mock-based service test | Usually unnecessary |
| Database integration test | Useful |
| Redis integration test | Useful |
| API integration test | Often useful |
| Repository test | Useful |
| End-to-end test | Potentially useful |
| Performance test | Depends on environment requirements |

Do not run every unit test against a full infrastructure stack.

A practical pipeline can separate:

```text
Unit Tests
    ↓
Fast Feedback

Integration Tests
    ↓
Real Dependencies

End-to-End Tests
    ↓
Full System Validation
```

## Matrix Testing

Service containers can be combined with matrix strategies.

For example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      matrix:
        postgres:
          - "15"
          - "16"

    services:
      postgres:
        image: postgres:${{ matrix.postgres }}
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app_test

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_HOST: localhost
          DATABASE_PORT: "5432"
        run: pytest
```

This is useful when database-version compatibility is an explicit requirement.

Avoid unnecessarily large matrices.

For example:

```text
3 Python versions
×
3 PostgreSQL versions
×
2 Redis versions
=
18 environments
```

Matrix growth can rapidly increase CI cost and execution time.

## Service Containers and Caching

Service containers themselves should generally not be treated as cacheable application state.

The database should be recreated.

Dependencies can be cached separately:

```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
```

The distinction is:

```text
Cache
→ Reuse expensive-to-generate dependencies

Service Container
→ Provide fresh infrastructure for the current test
```

## Service Containers and Artifacts

When tests fail, collect useful diagnostics.

```yaml
- name: Upload test reports
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@v4
  with:
    name: test-reports
    path: |
      reports/
      coverage.xml
```

Artifacts can include:

- Test reports.
- Coverage.
- Application logs.
- Debug output.
- Generated diagnostics.

Do not upload secrets or sensitive database contents.

## Security Considerations

Service containers run as part of the CI execution environment and should be treated as infrastructure components.

Security considerations include:

- Trusted container images.
- Versioned image references.
- Image vulnerability scanning.
- Minimal exposed ports.
- Non-production credentials.
- No production data.
- No unnecessary privileges.
- Restricted self-hosted runners.

Never connect service containers to production systems during ordinary CI tests.

## Secrets and Test Credentials

Test environments should use dedicated credentials.

Example:

```yaml
env:
  POSTGRES_USER: test
  POSTGRES_PASSWORD: test
  POSTGRES_DB: app_test
```

For more sensitive integration environments, use GitHub secrets or environment-specific credentials.

Never reuse production database credentials.

Avoid putting secrets directly into command-line arguments because command-line values can become visible through process inspection or logs depending on the execution environment.

## Third-Party Images

A service container depends on an external image.

Example:

```yaml
services:
  postgres:
    image: postgres:16
```

Treat this as a supply-chain dependency.

Controls can include:

- Trusted registries.
- Versioned image tags.
- Digest pinning where appropriate.
- Vulnerability scanning.
- Controlled image updates.
- Organizational policies.

Avoid silently pulling arbitrary images into security-sensitive workflows.

## Self-Hosted Runner Considerations

Service containers on self-hosted runners require additional attention.

A self-hosted runner may have access to:

- Private networks.
- Internal services.
- Cloud credentials.
- Cached data.
- Internal repositories.

If untrusted code can execute alongside those capabilities, the service-container architecture does not eliminate the underlying risk.

For untrusted workloads, consider:

```text
Ephemeral Runner
      ↓
Isolated Job
      ↓
Service Containers
      ↓
Runner Destroyed
```

## Resource Management

Service containers consume runner resources.

A workflow using:

```text
Job
+
PostgreSQL
+
Redis
+
MySQL
```

requires more CPU and memory than a job running only application tests.

Resource pressure can cause:

- Slow tests.
- Container startup failures.
- Out-of-memory conditions.
- Increased CI duration.

Keep the dependency environment as small as practical.

## Performance Optimization

Common optimization opportunities include:

### Reduce Image Size

Use appropriate service images and avoid unnecessary custom layers.

### Run Independent Tests in Parallel

Separate independent test groups into jobs where the additional runner cost is justified.

### Cache Dependencies

Cache Python or other dependency downloads.

### Avoid Unnecessary Services

If a unit-test job does not use Redis, do not start Redis.

### Use Appropriate Matrix Coverage

Test supported versions rather than every possible version combination.

## Reliability

Service-container reliability depends on deterministic initialization.

A reliable integration-test environment should have:

```text
Known Image
    ↓
Known Configuration
    ↓
Readiness Check
    ↓
Deterministic Initialization
    ↓
Tests
    ↓
Cleanup
```

Avoid hidden external dependencies.

For example, an integration test that requires an undocumented external Redis instance is less reproducible than one using a workflow service container.

## Common Mistakes

### Using `localhost` Incorrectly

For a job container:

```text
DATABASE_HOST=localhost
```

may point to the job container itself.

Use the service hostname:

```text
DATABASE_HOST=postgres
```

when using container networking.

### Publishing Ports Unnecessarily

If the job container can communicate directly with the service container, host port publishing may not be required.

### Assuming Readiness

Container creation does not guarantee service readiness.

Use health checks or bounded readiness probes.

### Using Production Data

Never copy production data into ordinary CI service containers.

Use synthetic or sanitized test data.

### Sharing a Test Database

Shared external databases can create race conditions between workflow runs.

Prefer isolated service containers.

### Overbuilding the Test Environment

Do not start PostgreSQL, MySQL, Redis, Kafka, Elasticsearch, and other services for a unit-test job that only tests pure Python logic.

### Unbounded Retries

Avoid:

```bash
while ! database_is_ready; do
  sleep 1
done
```

without a maximum retry duration.

### Using Mutable Images

Avoid depending indefinitely on:

```text
postgres:latest
```

when deterministic test environments matter.

## Troubleshooting

Use the standard model:

```text
Symptom
→ Possible Causes
→ Isolation Strategy
→ Commands / Checks
→ Root Cause
→ Corrective Action
→ Prevention
```

### Service Container Fails to Start

Check:

- Image name.
- Image tag.
- Registry availability.
- Image architecture.
- Environment variables.
- Container options.

### Connection Refused

Check:

```text
Service Running?
        ↓
Service Ready?
        ↓
Correct Host?
        ↓
Correct Port?
        ↓
Correct Credentials?
```

For a containerized job, verify the hostname:

```text
postgres
redis
mysql
```

### Database Initialization Fails

Check:

- Database credentials.
- Initialization environment variables.
- Migration scripts.
- Database version.
- Application compatibility.

### Redis Connection Fails

Check:

```text
REDIS_HOST
REDIS_PORT
Service Name
Service Readiness
```

### Tests Are Flaky

Investigate:

- Database state.
- Shared resources.
- Service readiness.
- Test ordering.
- Timeouts.
- Race conditions.
- Parallel execution.
- External dependencies.

### Tests Are Slow

Measure:

```text
Image Pull
+
Service Startup
+
Dependency Installation
+
Migration Time
+
Test Execution
+
Artifact Upload
```

Do not increase runner size or remove tests without identifying the dominant bottleneck.

## Production CI Architecture

A mature backend CI pipeline can separate fast unit testing from infrastructure-dependent integration testing.

```mermaid
flowchart TD
    A[Pull Request] --> B[Lint]

    B --> C[Unit Tests]
    B --> D[Integration Tests]

    D --> E[Job Container]

    E --> F[PostgreSQL]
    E --> G[Redis]

    C --> H[Security Scan]
    D --> H

    H --> I[Build]
    I --> J[Docker Image]
    J --> K[ECR]
    K --> L[Staging]
    L --> M[Approval]
    M --> N[Production]
```

This architecture provides:

- Fast feedback from unit tests.
- Real dependency validation from integration tests.
- Controlled artifact creation.
- Environment promotion.
- Clear failure domains.

## Recommended Test Architecture

For a Python backend:

```text
                 Pull Request
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
     Unit Tests             Integration Tests
          │                       │
          │                ┌──────┴──────┐
          │                │             │
          │                ▼             ▼
          │           PostgreSQL      Redis
          │                │             │
          └───────────────┬┴─────────────┘
                          ▼
                    Security Scan
                          ↓
                        Build
```

Keep infrastructure-dependent tests separate enough that failures can be diagnosed quickly.

## Operational Best Practices

Use the following practices for production-grade service-container pipelines:

- Pin or tightly control service image versions.
- Use dedicated test credentials.
- Never connect ordinary CI tests to production systems.
- Use service hostnames correctly.
- Add readiness checks where required.
- Keep service environments disposable.
- Avoid unnecessary services.
- Separate unit and integration tests.
- Cache dependencies rather than infrastructure state.
- Collect useful test artifacts.
- Keep matrix dimensions intentional.
- Scan and govern trusted container images.
- Isolate self-hosted runners appropriately.
- Make failures distinguishable between infrastructure and application problems.

## Interview Preparation

### What Is a Service Container?

Explain that it is a containerized dependency attached to a GitHub Actions job, commonly used for integration tests.

### Job Container vs Service Container?

Explain:

```text
Job Container
→ Executes workflow steps.

Service Container
→ Provides a dependency to those steps.
```

### Why Does `localhost` Sometimes Work and Sometimes Not?

Explain the networking distinction:

```text
Job on Runner
→ localhost can reach published service ports

Job in Container
→ service hostname is normally used
```

### How Would You Test Django with PostgreSQL and Redis?

Describe:

```text
Python Job Container
      ↓
Django
      ↓
pytest
      ↓
PostgreSQL + Redis Services
```

### How Would You Handle Database Readiness?

Use:

- Container health checks.
- Readiness probes.
- Bounded retries.
- Clear failure messages.

Avoid arbitrary long sleeps.

### How Would You Prevent Test Interference?

Use isolated service containers and fresh databases per workflow run.

### How Would You Test Multiple PostgreSQL Versions?

Use a matrix:

```yaml
strategy:
  matrix:
    postgres:
      - "15"
      - "16"
```

and dynamically select:

```yaml
services:
  postgres:
    image: postgres:${{ matrix.postgres }}
```

### What Security Risks Exist?

Discuss:

- Untrusted code.
- Service-image supply chain.
- Self-hosted runners.
- Production credential exposure.
- Network access.
- Excessive privileges.
- Mutable image references.

### How Would You Optimize CI Cost?

Consider:

```text
Avoid Unnecessary Services
+
Cache Dependencies
+
Parallelize Independent Tests
+
Control Matrix Size
+
Optimize Image Startup
```

## Key Takeaways

- Service containers provide disposable infrastructure dependencies such as PostgreSQL, MySQL, and Redis for GitHub Actions jobs, making them particularly useful for integration testing.
- Networking depends on the execution model: runner-based jobs commonly use published ports and `localhost`, while containerized jobs normally communicate with services through service hostnames.
- Production integration tests should use deterministic service versions, readiness checks, isolated test data, dedicated credentials, and disposable environments rather than shared or production infrastructure.
- Service containers should complement a layered test strategy: fast unit tests first, infrastructure-dependent integration tests separately, followed by security, build, and deployment stages.
- Treat service images, self-hosted runners, networking, credentials, resource usage, and matrix size as production CI concerns rather than merely test configuration details.