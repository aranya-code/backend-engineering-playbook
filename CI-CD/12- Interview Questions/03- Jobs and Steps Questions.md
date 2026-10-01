# 03- Jobs and Steps Questions

## Overview

GitHub Actions workflows are executed through a hierarchy:

```text
Workflow
   ↓
Job
   ↓
Step
   ↓
Action / Shell Command
   ↓
Runner
```

Understanding jobs and steps is fundamental to designing reliable CI/CD pipelines. Interview questions in this area usually test more than YAML syntax. They test whether you understand:

- Execution order.
- Job isolation.
- Step dependencies.
- `needs`.
- Conditions.
- Status functions.
- Matrix execution.
- Outputs.
- Artifacts.
- Runners.
- Containers.
- Permissions.
- Failure handling.
- Concurrency.
- Production deployment architecture.

A senior engineer should be able to reason about a workflow as a dependency graph rather than as a sequential YAML file.

---

## Workflow → Job → Step → Action → Runner

### Workflow

A workflow is the top-level automation definition.

```yaml
name: Backend CI

on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - run: pytest
```

The workflow defines:

- When execution starts.
- Which jobs exist.
- Job dependencies.
- Permissions.
- Concurrency.
- Environment configuration.

---

### Job

A job is an independently scheduled execution unit.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - run: pytest
```

Each job executes on a runner and has its own execution environment.

Jobs are isolated by default.

```text
Job A
Runner A
Filesystem A
Environment A

Job B
Runner B
Filesystem B
Environment B
```

Files created in Job A are not automatically available in Job B.

This is one of the most important concepts in GitHub Actions.

---

### Step

A step is an individual operation within a job.

```yaml
steps:
  - name: Checkout
    uses: actions/checkout@v4

  - name: Install dependencies
    run: pip install -r requirements.txt

  - name: Run tests
    run: pytest
```

Steps within a job execute sequentially by default.

They share the same job environment and workspace.

```text
Job
 ├── Step 1
 ├── Step 2
 ├── Step 3
 └── Step 4
```

---

### Action

An action is reusable automation invoked by a step.

```yaml
- uses: actions/checkout@v4
```

Actions can be:

- JavaScript actions.
- Composite actions.
- Docker actions.

A shell command is not an action:

```yaml
- run: pytest
```

It is a step executing a shell command.

---

### Runner

A runner is the machine or execution environment where a job runs.

Examples:

- GitHub-hosted Linux runner.
- GitHub-hosted Windows runner.
- GitHub-hosted macOS runner.
- Self-hosted runner.
- Containerized job environment.

The runner provides:

- CPU.
- Memory.
- Filesystem.
- Operating system.
- Network access.
- Installed tooling.

---

## Job Execution Lifecycle

A simplified lifecycle is:

```mermaid
flowchart TD
    A[Workflow Triggered] --> B[Evaluate Jobs]
    B --> C[Resolve Job Dependencies]
    C --> D[Select Runner]
    D --> E[Initialize Job]
    E --> F[Execute Steps]
    F --> G{Step Failed?}
    G -->|No| H[Job Success]
    G -->|Yes| I[Job Failure]
    I --> J[Failure Handling]
    H --> K[Downstream Jobs]
```

At a high level:

1. GitHub determines which workflow is triggered.
2. Jobs are evaluated.
3. Job dependencies are resolved.
4. A runner is selected.
5. The job environment is initialized.
6. Steps execute.
7. Job status is determined.
8. Dependent jobs are evaluated.

---

## Job Isolation

### Why are jobs isolated?

Job isolation allows GitHub Actions to:

- Run jobs in parallel.
- Use different operating systems.
- Use different runners.
- Scale workloads independently.
- Limit failure propagation.
- Create security boundaries.

For example:

```text
           ┌── Lint
PR ────────┼── Unit Tests
           ├── Security Scan
           └── Integration Tests
```

These jobs can execute concurrently.

---

### What does not automatically persist between jobs?

Typically:

- Files.
- Installed Python packages.
- Environment changes.
- Shell state.
- Processes.
- Local services.

If Job A creates:

```text
build/app.tar.gz
```

Job B cannot assume that file exists.

Use artifacts when the data needs to cross job boundaries.

---

## Steps Share Job State

Within a job:

```yaml
steps:
  - name: Create file
    run: echo "hello" > output.txt

  - name: Read file
    run: cat output.txt
```

The second step can access the file because both steps execute in the same job workspace.

This differs from separate jobs.

```text
Job A
  Step 1 → output.txt
  Step 2 → reads output.txt

Job B
  Step 1 → output.txt does not automatically exist
```

---

## Job Dependencies With `needs`

### What is `needs`?

`needs` defines an explicit dependency between jobs.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: ./build.sh
```

The execution graph is:

```text
test
 ↓
build
```

Without `needs`, independent jobs can run concurrently.

---

### Why use `needs`?

Use `needs` when one job depends on another.

Examples:

```text
Tests
 ↓
Build
 ↓
Deploy
```

or:

```text
Lint ───────┐
Unit ───────┼──→ Build
Security ───┘
```

---

### Fan-Out

Fan-out means one job enables multiple parallel jobs.

```text
          ┌── Python 3.11
Plan ─────┼── Python 3.12
          └── Python 3.13
```

Example:

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version:
          - "3.11"
          - "3.12"
          - "3.13"
```

---

### Fan-In

Fan-in means multiple jobs converge into a downstream job.

```text
Lint ───────┐
Unit ───────┤
Integration ┼──→ Build
Security ───┘
```

Example:

```yaml
jobs:
  lint:
    ...

  unit:
    ...

  integration:
    ...

  build:
    needs:
      - lint
      - unit
      - integration
```

The build job waits for all required jobs.

---

## Sequential vs Parallel Execution

### Sequential

```yaml
jobs:
  test:
    ...

  build:
    needs: test

  deploy:
    needs: build
```

Execution:

```text
test
 ↓
build
 ↓
deploy
```

Useful for:

- Deployment pipelines.
- Promotion.
- Validation gates.

---

### Parallel

```yaml
jobs:
  lint:
    ...

  unit:
    ...

  security:
    ...
```

Execution:

```text
       ┌── lint
       │
start ─┼── unit
       │
       └── security
```

Useful for:

- Independent tests.
- Static analysis.
- Security scanning.

Parallelism reduces CI duration.

---

## Job Status Propagation

Suppose:

```text
test → build → deploy
```

If `test` fails:

```text
test: failure
build: skipped
deploy: skipped
```

This is the normal dependency behavior.

The key distinction is:

```text
failure
vs
skipped
```

A skipped downstream job did not necessarily fail. Its prerequisite did not successfully complete.

---

## Conditional Jobs

Jobs can use `if`.

```yaml
deploy:
  if: ${{ github.ref == 'refs/heads/main' }}
  needs: build
  runs-on: ubuntu-latest

  steps:
    - run: ./deploy.sh
```

This is useful for environment-specific behavior.

However, do not rely only on a branch condition for production authorization.

Use:

- Environments.
- Required reviewers.
- Least-privilege permissions.
- OIDC.
- IAM.
- Concurrency.

---

## Step Conditions

Steps can also use `if`.

```yaml
steps:
  - name: Run tests
    run: pytest

  - name: Upload diagnostics
    if: ${{ failure() }}
    run: ./collect-diagnostics.sh
```

This allows failure-specific handling.

---

## Job Conditions vs Step Conditions

| Characteristic | Job `if` | Step `if` |
|---|---|---|
| Controls | Entire job | Individual step |
| Runner allocated | Depends on job execution | Job already running |
| Use case | Deployment gating | Cleanup/diagnostics |
| Scope | Job | Step |
| Cost impact | Can prevent job execution | Runner already active |

Use job-level conditions when an entire workload should not execute.

Use step-level conditions when the job should run but specific operations should be conditional.

---

## Status Functions

### `success()`

Used when execution should continue only after successful preceding execution.

```yaml
- name: Publish
  if: ${{ success() }}
  run: ./publish.sh
```

---

### `failure()`

Useful for diagnostics and failure handling.

```yaml
- name: Upload test reports
  if: ${{ failure() }}
  uses: actions/upload-artifact@v4
  with:
    name: test-reports
    path: reports/
```

---

### `always()`

Allows a step to be considered regardless of preceding success/failure state.

```yaml
- name: Collect logs
  if: ${{ always() }}
  run: ./collect-logs.sh
```

Use carefully for critical operations.

A common mistake is assuming `always()` guarantees execution under every cancellation or infrastructure condition.

---

### `cancelled()`

Allows logic to respond specifically to cancellation.

```yaml
- name: Record cancellation
  if: ${{ cancelled() }}
  run: ./record-cancellation.sh
```

Cancellation is operationally different from ordinary failure.

---

## `continue-on-error`

### What is it?

It allows an intentionally non-blocking operation to fail without producing normal failure behavior for the enclosing execution path.

```yaml
- name: Experimental compatibility check
  continue-on-error: true
  run: ./compatibility-check.sh
```

Use cases:

- Experimental checks.
- Non-blocking compatibility tests.
- Transitional migration checks.

Do not use it to hide unreliable production tests.

Bad pattern:

```yaml
- name: Unit tests
  continue-on-error: true
  run: pytest
```

This removes an important CI quality gate.

---

## Matrix Jobs

### What is a matrix?

A matrix creates multiple job executions from combinations of variables.

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

This produces:

```text
Job 1 → Python 3.11
Job 2 → Python 3.12
Job 3 → Python 3.13
```

---

### Multiple Matrix Dimensions

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
    database:
      - postgres
      - mysql
```

This produces four combinations:

```text
3.11 + postgres
3.11 + mysql
3.12 + postgres
3.12 + mysql
```

Matrix cardinality grows multiplicatively.

For:

```text
3 Python versions
× 2 databases
× 2 operating systems
```

the theoretical matrix contains:

```text
3 × 2 × 2 = 12 jobs
```

This directly affects cost and execution time.

---

## `include`

`include` adds or modifies specific matrix combinations.

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"

    include:
      - python-version: "3.12"
        experimental: true
```

This is useful when some combinations require additional metadata.

---

## `exclude`

`exclude` removes combinations that should not execute.

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"

    database:
      - postgres
      - mysql

    exclude:
      - python-version: "3.11"
        database: mysql
```

Use this when a compatibility combination is unsupported or unnecessary.

---

## `fail-fast`

`fail-fast` controls matrix cancellation behavior.

```yaml
strategy:
  fail-fast: true
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

With `fail-fast: true`, a matrix failure can cause other in-progress matrix jobs to be cancelled.

For compatibility testing, this can reduce wasted CI time.

For complete compatibility reporting, you may prefer:

```yaml
fail-fast: false
```

---

## `max-parallel`

Controls how many matrix jobs can execute concurrently.

```yaml
strategy:
  max-parallel: 2
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
      - "3.14"
```

This can be useful when:

- Downstream services have limited capacity.
- Self-hosted runners are constrained.
- Database capacity is limited.
- Cost must be controlled.

---

## Matrix + `needs`

A downstream job can depend on a matrix job.

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version:
          - "3.11"
          - "3.12"
    ...

  build:
    needs: test
```

The build job waits for the required matrix execution to complete successfully.

---

## Dynamic Matrices

Dynamic matrices allow an earlier job to determine what should run.

Architecture:

```text
Planning Job
    ↓
JSON Output
    ↓
fromJSON()
    ↓
Dynamic Matrix
    ↓
Parallel Jobs
```

Example:

```yaml
jobs:
  plan:
    runs-on: ubuntu-latest
    outputs:
      services: ${{ steps.plan.outputs.services }}

    steps:
      - id: plan
        run: |
          echo 'services=["orders","payments"]' >> "$GITHUB_OUTPUT"

  test:
    needs: plan
    strategy:
      matrix:
        service: ${{ fromJSON(needs.plan.outputs.services) }}

    runs-on: ubuntu-latest

    steps:
      - run: echo "Testing ${{ matrix.service }}"
```

This pattern is useful for monorepos and affected-service testing.

---

## Step Outputs

Steps can expose outputs using `GITHUB_OUTPUT`.

```yaml
- id: version
  run: echo "value=1.2.3" >> "$GITHUB_OUTPUT"
```

Another step in the same job can use:

```yaml
- run: echo "${{ steps.version.outputs.value }}"
```

---

## Job Outputs

A job can expose outputs to downstream jobs.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      image: ${{ steps.metadata.outputs.image }}

    steps:
      - id: metadata
        run: |
          echo "image=my-app:${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

Another job can access:

```yaml
jobs:
  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - run: echo "${{ needs.build.outputs.image }}"
```

This is the preferred mechanism for passing small pieces of structured metadata between jobs.

---

## Outputs vs Artifacts vs Cache

| Mechanism | Purpose | Typical Data |
|---|---|---|
| Step output | Small value within job | Version |
| Job output | Small value across jobs | Image digest |
| Artifact | Persistent job output | Build package/test reports |
| Cache | Reusable dependency/build data | pip/npm/Docker cache |
| Environment variable | Runtime configuration | `APP_ENV` |

A common interview mistake is treating all five mechanisms as interchangeable.

---

## Artifacts Across Jobs

Suppose:

```text
Build Job
 ↓
application.tar.gz
 ↓
Deploy Job
```

Upload:

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: application
    path: dist/
```

Download:

```yaml
- uses: actions/download-artifact@v5
  with:
    name: application
    path: dist/
```

Artifacts are appropriate when the actual files need to cross job boundaries.

---

## Environment Variables

Environment variables can exist at different scopes.

### Workflow Level

```yaml
env:
  APP_ENV: test
```

### Job Level

```yaml
jobs:
  test:
    env:
      APP_ENV: test
```

### Step Level

```yaml
steps:
  - name: Test
    env:
      DATABASE_URL: postgres://...
    run: pytest
```

Prefer the narrowest scope that satisfies the requirement.

This improves clarity and reduces accidental exposure.

---

## `$GITHUB_ENV`

Use `$GITHUB_ENV` when a step needs to make an environment variable available to subsequent steps in the same job.

```yaml
- name: Set version
  run: echo "APP_VERSION=1.2.3" >> "$GITHUB_ENV"

- name: Show version
  run: echo "$APP_VERSION"
```

The variable does not automatically propagate to another job.

For cross-job data, use outputs.

---

## `$GITHUB_PATH`

`$GITHUB_PATH` allows a step to add a directory to `PATH` for subsequent steps.

```yaml
- name: Add tool directory
  run: echo "$HOME/.local/bin" >> "$GITHUB_PATH"
```

This modifies the environment for later steps in the same job.

---

## Job Containers

A job can execute inside a container.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    steps:
      - uses: actions/checkout@v4
      - run: python --version
      - run: pytest
```

This provides a more controlled runtime environment.

---

## Why Use Job Containers?

They can improve:

- Runtime consistency.
- Dependency isolation.
- Reproducibility.
- Native dependency management.

Useful for Python backend projects where the CI runtime should closely resemble the application's runtime.

---

## Service Containers

Service containers provide dependencies such as PostgreSQL or Redis.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: app_test
        options: >-
          --health-cmd="pg_isready -U postgres"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

    steps:
      - uses: actions/checkout@v4

      - run: pytest
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/app_test
```

For a backend integration pipeline:

```text
Python
 ↓
PostgreSQL
 ↓
Redis
 ↓
pytest
 ↓
Coverage
 ↓
Artifacts
```

---

## Runner Networking vs Container Networking

Networking differs depending on whether the job executes directly on the runner or inside a container.

A runner-based job may use mapped ports such as:

```text
localhost:5432
```

A containerized job can communicate with service containers through the service network.

This distinction is a frequent source of integration-test failures.

---

## Job Failure Domains

When a job fails, classify the failure before changing the YAML.

Common domains:

```text
Workflow
 ├── Trigger
 ├── Job
 │    ├── Runner
 │    ├── Environment
 │    ├── Permissions
 │    └── Steps
 │          ├── Shell
 │          ├── Action
 │          ├── Container
 │          └── Service
 ├── Dependencies
 ├── Artifacts
 └── External Systems
```

This prevents random configuration changes.

---

## Troubleshooting Job Failures

Use:

```text
Symptom
 ↓
Possible Causes
 ↓
Isolation Strategy
 ↓
Commands / Checks
 ↓
Root Cause
 ↓
Corrective Action
 ↓
Prevention
```

### Step 1: Identify the First Failure

Do not start with the final failed job.

If:

```text
lint       ✓
unit       ✗
build      skipped
deploy     skipped
```

The root cause is probably in `unit`, not `build`.

---

### Step 2: Inspect Dependencies

Check:

```yaml
needs:
```

and:

```yaml
if:
```

A skipped job may be behaving correctly because a dependency failed.

---

### Step 3: Inspect Runner State

For runner-related failures, check:

- Operating system.
- Architecture.
- Available tools.
- Disk.
- Memory.
- Network.
- Permissions.

---

## Common Step Failures

### Exit Codes

Shell commands generally communicate success or failure through exit status.

```bash
pytest
```

If pytest exits non-zero, the step normally fails.

This is why commands such as:

```bash
pytest || true
```

should be used carefully.

They can hide real failures.

---

## Working Directory Problems

A common failure:

```yaml
- run: pytest
```

when the application is actually located under:

```text
backend/
```

Use:

```yaml
defaults:
  run:
    working-directory: backend
```

or:

```yaml
- run: pytest
  working-directory: backend
```

---

## Missing Dependencies

A step may fail because the runner does not contain the required dependency.

Example:

```text
pytest: command not found
```

Correct approach:

```yaml
- name: Install dependencies
  run: pip install -r requirements.txt
```

Do not assume every runner contains your application's dependencies.

---

## Job Outputs and Failure Handling

Suppose:

```text
plan
 ↓
build
 ↓
deploy
```

If `plan` produces a malformed output, downstream jobs may fail even though their YAML is correct.

For structured outputs:

```yaml
- id: plan
  run: |
    services='["orders","payments"]'
    echo "services=$services" >> "$GITHUB_OUTPUT"
```

Validate the generated data before consuming it.

---

## Security and Jobs

### Least-Privilege Permissions

Set permissions explicitly where possible.

```yaml
permissions:
  contents: read
```

Deployment jobs may require additional permissions:

```yaml
permissions:
  contents: read
  id-token: write
```

Avoid giving every job broad permissions.

---

## Job-Level Permission Isolation

Consider:

```text
Lint Job
 → contents: read

Test Job
 → contents: read

Build Job
 → contents: read

Deploy Job
 → contents: read
 → id-token: write
```

This reduces blast radius.

A compromised test dependency should not automatically receive production deployment permissions.

---

## GITHUB_TOKEN and Jobs

`GITHUB_TOKEN` is available to workflows with permissions determined by the workflow/repository configuration.

The important senior-level principle is:

> Authentication does not imply authorization.

A job may have a token but still receive a `403` because the required permission is not granted.

---

## Job-Level Secrets

Sensitive values should be scoped narrowly.

Prefer:

```yaml
jobs:
  deploy:
    environment: production
```

rather than making production secrets available to every CI job.

A secure architecture is:

```text
PR Jobs
  ↓
No production secrets

Build Jobs
  ↓
No production secrets

Deployment Job
  ↓
Production environment
  ↓
Production secrets / OIDC
```

---

## Job Dependencies and Security Boundaries

`needs` defines execution dependency, not authorization.

For example:

```text
test
 ↓
deploy
```

does not mean:

> "Because tests succeeded, deployment is authorized."

Production authorization should still use:

- Protected environments.
- Required reviewers.
- IAM.
- OIDC.
- Branch policies.
- Artifact validation.

---

## Concurrency at Job Level

Concurrency can be defined for jobs.

```yaml
deploy:
  concurrency:
    group: production
    cancel-in-progress: false
```

This is useful when only the deployment job needs serialization.

For example:

```text
Lint ───────┐
Unit ───────┤
Security ───┼──→ Build → Deploy
Integration ┘           ↑
                        concurrency
```

CI can remain parallel while production deployment remains serialized.

---

## Job-Level Concurrency vs Workflow-Level Concurrency

| | Workflow-Level | Job-Level |
|---|---|---|
| Scope | Entire workflow run | Specific job |
| Useful for | PR cancellation | Deployment serialization |
| Parallel CI | Can restrict more broadly | Preserves other jobs |
| Production control | Possible | Often more precise |

Choose the smallest scope that solves the race condition.

---

## Build Once, Deploy Many

A production pipeline should preferably use:

```text
Test
 ↓
Build
 ↓
Immutable Artifact
 ↓
Staging
 ↓
Approval
 ↓
Production
```

Not:

```text
Build
 ↓
Staging

Build again
 ↓
Production
```

The second model can produce different artifacts.

For Docker:

```text
Source SHA
 ↓
Docker Buildx
 ↓
Image Digest
 ↓
ECR
 ↓
Staging
 ↓
Production
```

The production job should consume the same digest.

---

## Complete Backend CI Example

```yaml
name: Backend CI

on:
  pull_request:
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

      - run: pip install ruff
      - run: ruff check .

  unit:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: pip install -r requirements.txt
      - run: pytest tests/unit

  integration:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: app_test
        options: >-
          --health-cmd="pg_isready -U postgres"
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

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: pip install -r requirements.txt

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: pytest tests/integration

  build:
    needs:
      - lint
      - unit
      - integration

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Build application
        run: ./build.sh
```

The dependency graph is:

```text
          ┌── lint ──────────┐
          │                  │
PR ───────┼── unit ──────────┼──→ build
          │                  │
          └── integration ───┘
```

This is a classic fan-out/fan-in CI architecture.

---

## Production CI/CD Pipeline

A production pipeline can extend the previous design:

```mermaid
flowchart LR
    PR[Pull Request]
    LINT[Lint]
    UNIT[Unit Tests]
    INT[Integration Tests]
    SEC[Security Scan]
    MATRIX[Matrix Tests]
    BUILD[Build]
    IMAGE[Docker Image]
    ECR[ECR]
    STAGE[Staging]
    APPROVAL[Approval]
    PROD[Production]
    MONITOR[Monitoring]
    ROLLBACK[Rollback]

    PR --> LINT
    PR --> UNIT
    PR --> INT
    PR --> SEC
    PR --> MATRIX

    LINT --> BUILD
    UNIT --> BUILD
    INT --> BUILD
    SEC --> BUILD
    MATRIX --> BUILD

    BUILD --> IMAGE
    IMAGE --> ECR
    ECR --> STAGE
    STAGE --> APPROVAL
    APPROVAL --> PROD
    PROD --> MONITOR
    MONITOR --> ROLLBACK
```

The key engineering properties are:

- Parallel validation.
- Explicit dependency graph.
- Immutable artifacts.
- Environment promotion.
- Approval gates.
- Deployment concurrency.
- Monitoring.
- Rollback.

---

## Backend Integration Testing

For Django:

```text
Django
 ↓
PostgreSQL
 ↓
Redis
 ↓
pytest
```

For FastAPI:

```text
FastAPI
 ↓
PostgreSQL
 ↓
Redis
 ↓
pytest
```

The pipeline should validate:

- Database connectivity.
- Migrations.
- API behavior.
- Cache integration.
- Authentication.
- Transaction behavior.
- External dependency boundaries.

---

## Celery and Kafka Jobs

If integration tests require Celery:

```text
Application
 ↓
Redis / RabbitMQ
 ↓
Celery Worker
 ↓
Task
```

The worker should be treated as part of the integration-test environment.

For Kafka:

```text
Application
 ↓
Kafka
 ↓
Consumer
 ↓
Database
```

Do not assume that a service container being started means the service is ready to accept application traffic.

Readiness and health checks matter.

---

## Job Resource Considerations

A job can consume:

- CPU.
- Memory.
- Disk.
- Network.
- Runner capacity.

Large matrix jobs can multiply resource consumption.

For example:

```text
4 Python versions
× 2 databases
× 2 operating systems
= 16 jobs
```

If each job takes 8 minutes, total wall-clock time depends on available parallel capacity, while total compute consumption scales with the number of executions.

Senior CI design balances:

```text
Speed
+
Coverage
+
Reliability
+
Cost
```

---

## Job Caching

Caching is useful for dependencies.

Python example:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: pip
```

For custom caching:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.lock') }}
```

Do not use caches as the authoritative mechanism for release artifacts.

Use artifacts or registries for immutable outputs.

---

## Job Artifacts

Use artifacts for:

- Coverage reports.
- Test reports.
- Debug logs.
- Build packages.
- Diagnostic files.

Example:

```yaml
- name: Upload test report
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@v4
  with:
    name: test-report
    path: reports/
```

Artifacts are especially useful when a job fails and developers need evidence.

---

## Job Observability

Production CI should expose enough information to diagnose failures.

Useful information includes:

- Job duration.
- Step duration.
- Failure reason.
- Runner type.
- Matrix dimensions.
- Artifact identity.
- Commit SHA.
- Deployment environment.
- Docker digest.
- AWS account/region.
- Deployment result.

Step summaries can provide concise operational information.

```yaml
- name: Deployment summary
  run: |
    {
      echo "## Deployment"
      echo "- Environment: production"
      echo "- SHA: $GITHUB_SHA"
    } >> "$GITHUB_STEP_SUMMARY"
```

Avoid writing secrets or sensitive infrastructure information into summaries.

---

## Common Jobs and Steps Interview Questions

### What is the difference between a job and a step?

A job is an independently scheduled execution unit with its own runner environment.

A step is an operation executed within that job.

Steps share job state; separate jobs do not automatically share files or processes.

---

### Why would you split one large job into multiple jobs?

Benefits:

- Parallel execution.
- Failure isolation.
- Different permissions.
- Different runners.
- Different environments.
- Better visibility.
- Smaller security blast radius.

Trade-off:

- More workflow complexity.
- Artifact/output transfer.
- Additional runner startup overhead.

---

### Why not put the entire pipeline into one job?

A single job:

```text
Lint
 ↓
Unit
 ↓
Integration
 ↓
Security
 ↓
Build
 ↓
Deploy
```

has poor parallelism and a larger privilege boundary.

A multi-job pipeline can instead use:

```text
Lint ───────┐
Unit ───────┤
Security ───┼──→ Build → Deploy
Integration ┘
```

---

### How do you pass a value between steps?

Use `$GITHUB_OUTPUT`.

```yaml
- id: metadata
  run: echo "version=1.2.3" >> "$GITHUB_OUTPUT"
```

Consume:

```yaml
${{ steps.metadata.outputs.version }}
```

---

### How do you pass a value between jobs?

Expose a job output:

```yaml
outputs:
  version: ${{ steps.metadata.outputs.version }}
```

Then consume it through:

```yaml
${{ needs.build.outputs.version }}
```

---

### How do you pass a file between jobs?

Use an artifact.

```text
Job A
 ↓
Upload Artifact
 ↓
Job B
 ↓
Download Artifact
```

Do not rely on the filesystem surviving across jobs.

---

### How do you run jobs in parallel?

Do not define unnecessary `needs` dependencies.

```yaml
jobs:
  lint:
    ...

  unit:
    ...

  security:
    ...
```

These jobs can execute independently.

---

### How do you make jobs sequential?

Use `needs`.

```yaml
jobs:
  build:
    needs: test
```

---

### What happens when a job in `needs` fails?

Dependent jobs are normally skipped unless their conditions explicitly allow another execution path.

This is why status functions and `if` behavior are important when designing failure-handling jobs.

---

### How do you run cleanup after failure?

For example:

```yaml
- name: Upload diagnostics
  if: ${{ failure() }}
  uses: actions/upload-artifact@v4
```

For reporting that should occur after either success or failure:

```yaml
- name: Publish test report
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@v4
```

The condition should match the desired cancellation behavior.

---

### How do you prevent a failed experimental matrix entry from blocking the whole pipeline?

Use carefully scoped `continue-on-error`, often with matrix metadata.

```yaml
strategy:
  matrix:
    python:
      - "3.12"
      - "3.13"

    include:
      - python: "3.13"
        experimental: true

continue-on-error: ${{ matrix.experimental == true }}
```

This should only be used for intentionally non-blocking combinations.

---

### How would you design a matrix for Python and PostgreSQL compatibility?

```yaml
strategy:
  fail-fast: false
  matrix:
    python:
      - "3.11"
      - "3.12"

    postgres:
      - "15"
      - "16"
```

Then configure the test environment using the current matrix values.

The interview discussion should include matrix size, runtime, cost, compatibility coverage, and service readiness.

---

### How do you reduce matrix cost?

Options include:

- Remove redundant combinations.
- Use `include`/`exclude`.
- Use `max-parallel`.
- Run the full matrix only on selected events.
- Use a smaller PR matrix and broader scheduled/release matrix.
- Use dependency-aware testing.

---

## Advanced Interview Scenario: Production Deployment Race

### Question

Two developers merge commits close together. Both workflows attempt production deployment. How do you prevent simultaneous deployments?

### Engineering approach

Use deployment concurrency:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Then combine it with:

```text
Immutable artifact
+
Environment protection
+
Health checks
+
Idempotent deployment
+
Rollback
```

The key distinction is that concurrency controls workflow overlap; it does not make the deployment itself safe.

---

## Advanced Interview Scenario: Shared CI

### Question

Twenty repositories have identical Python CI workflows. How would you reduce duplication?

Use a reusable workflow:

```text
Repository
     ↓
workflow_call
     ↓
Central CI Workflow
```

Expose controlled:

- Inputs.
- Secrets.
- Outputs.

Version the reusable workflow and establish ownership/governance.

---

## Advanced Interview Scenario: Compromised Action

### Question

A third-party action used by the test job becomes compromised. How would you limit its impact?

Use:

- SHA pinning.
- Least-privilege permissions.
- Job-level permissions.
- No production secrets in test jobs.
- Separate deployment jobs.
- Protected environments.
- Trusted runner strategy.
- Action allowlists where appropriate.
- Dependency monitoring.
- Artifact provenance.
- Security review.

Architecture:

```text
Untrusted Action
      ↓
Restricted Test Job
      ↓
No Production Credentials
      ↓
Deployment Job
      ↓
Protected Environment
```

---

## Advanced Interview Scenario: Self-Hosted Runner

### Question

A deployment must reach a private AWS network. How would you design the runner architecture?

Consider:

```text
GitHub Actions
      ↓
Protected Runner Group
      ↓
Ephemeral Runner
      ↓
Private VPC
      ↓
ECS / EC2 / Kubernetes
```

Security considerations include:

- Runner isolation.
- Network segmentation.
- IAM/OIDC.
- Ephemeral lifecycle.
- No persistent secrets.
- Egress controls.
- Runner image hardening.
- Autoscaling.
- Monitoring.

---

## Advanced Interview Scenario: Build Once, Deploy Many

### Question

How would you ensure staging and production run exactly the same Docker artifact?

Use:

```text
Source SHA
 ↓
Docker Buildx
 ↓
Image Digest
 ↓
ECR
 ↓
Staging
 ↓
Approval
 ↓
Same Digest
 ↓
Production
```

Do not rebuild from source during production deployment.

The digest is the artifact identity.

---

## Advanced Interview Scenario: Job Failure Diagnosis

### Question

The deployment job is skipped, but tests passed. What do you inspect?

Use:

```text
Job dependency
 ↓
needs
 ↓
Job if condition
 ↓
Event context
 ↓
Environment protection
 ↓
Concurrency
 ↓
Previous job conclusion
```

A skipped job is not automatically a workflow bug.

---

## Advanced Interview Scenario: Integration Tests Fail

### Question

Django integration tests fail to connect to PostgreSQL.

Investigate:

```text
1. Is PostgreSQL running?
2. Is the service healthy?
3. Is the hostname correct?
4. Is the port correct?
5. Are credentials correct?
6. Is the job containerized?
7. Is localhost correct for this networking model?
8. Is the database initialized?
9. Are migrations required?
10. Is the test starting before PostgreSQL is ready?
```

The key is to diagnose the execution environment before changing application code.

---

## Production Checklist

### Job Design

- [ ] Jobs have clear responsibilities.
- [ ] Independent jobs run in parallel.
- [ ] `needs` represents real dependencies.
- [ ] Job boundaries reflect security boundaries.
- [ ] Job outputs are used for small metadata.
- [ ] Artifacts are used for files.

### Step Design

- [ ] Steps are focused.
- [ ] Exit codes are handled correctly.
- [ ] Working directories are explicit where necessary.
- [ ] Dependencies are installed deterministically.
- [ ] Failure handling is intentional.
- [ ] `continue-on-error` is not hiding real failures.

### Matrix Design

- [ ] Matrix dimensions are justified.
- [ ] Cardinality is understood.
- [ ] `fail-fast` behavior is intentional.
- [ ] `max-parallel` matches available capacity.
- [ ] Experimental combinations are explicitly marked.
- [ ] Dynamic matrices are validated.

### Security

- [ ] Permissions are least privilege.
- [ ] Production secrets are isolated.
- [ ] Deployment jobs are separated from untrusted CI.
- [ ] Third-party actions are trusted and pinned appropriately.
- [ ] Self-hosted runners are protected.
- [ ] AWS authentication uses OIDC where appropriate.

### Production Deployment

- [ ] Artifact is immutable.
- [ ] Build and deployment are separated.
- [ ] The same artifact is promoted.
- [ ] Production has environment protection.
- [ ] Deployment concurrency is configured.
- [ ] Health checks exist.
- [ ] Rollback is documented.

### Operations

- [ ] Logs are accessible.
- [ ] Failure diagnostics are collected.
- [ ] Test reports are retained.
- [ ] Step summaries provide useful context.
- [ ] Runner capacity is monitored.
- [ ] CI cost is reviewed.

---

## Key Takeaways

- **Jobs are independently scheduled execution units; steps execute within a job and share its workspace and runtime state.**
- **Use `needs` to model real dependencies, while leaving independent jobs unconstrained so GitHub Actions can execute them in parallel.**
- **Use outputs for small values, artifacts for files, caches for reusable dependencies, and environment mechanisms for runtime configuration; these mechanisms solve different problems.**
- **Production job design should separate security boundaries, minimize permissions, protect deployment jobs, use immutable artifacts, and control deployment concurrency.**
- **Senior-level GitHub Actions design treats the workflow as a dependency graph with explicit failure handling, resource constraints, observability, security boundaries, and rollback paths.**