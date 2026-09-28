# 06- Jobs and Steps

## Overview

Jobs and steps are the primary execution units inside a GitHub Actions workflow.

A workflow defines **when automation can start**, while jobs and steps define **what the automation actually does**.

The core execution hierarchy is:

```text
Workflow
   │
   ├── Job
   │    ├── Step
   │    │    ├── run
   │    │    └── uses
   │    └── Step
   │
   └── Job
```

A job runs on a runner and is isolated from other jobs unless data is deliberately transferred through outputs, artifacts, caches, or external systems.

For a production Python backend, a workflow might contain:

```text
Workflow
│
├── lint
│
├── unit-tests
│
├── integration-tests
│
├── security-scan
│
├── build
│
├── deploy-staging
│
└── deploy-production
```

Each job can then contain multiple steps:

```text
integration-tests
│
├── Checkout source
├── Set up Python
├── Start PostgreSQL
├── Start Redis
├── Install dependencies
├── Run migrations
├── Run pytest
└── Upload coverage
```

Understanding the boundary between workflows, jobs, steps, actions, and runners is essential for designing reliable and maintainable CI/CD systems.

## Workflow → Job → Step → Action → Runner

The relationship can be visualized as:

```mermaid
flowchart TD
    A[Workflow] --> B[Job]
    A --> C[Job]
    B --> D[Step]
    B --> E[Step]
    D --> F[Action]
    E --> G[Shell Command]
    B --> H[Runner]
    C --> I[Runner]
```

Each layer has a different responsibility.

| Component | Responsibility |
|---|---|
| Workflow | Defines triggers and overall automation |
| Job | Defines an execution unit and dependency boundary |
| Step | Defines an individual operation within a job |
| Action | Reusable implementation invoked by a step |
| Runner | Machine/environment that executes the job |

A useful mental model is:

```text
Workflow = orchestration
Job      = execution boundary
Step     = operation
Action   = reusable implementation
Runner   = execution environment
```

---

## What Is a Job?

A job is a collection of steps that execute together on the same runner.

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout source
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

The `test` job is one execution unit.

All steps in this job execute on the same runner environment and can normally access files created by earlier steps.

---

## Why Jobs Exist

Jobs provide isolation and orchestration.

Consider a backend pipeline:

```text
Lint
Tests
Security Scan
Build
Deploy
```

These operations have different requirements.

```text
Lint
→ CPU-light

Tests
→ PostgreSQL + Redis

Build
→ Docker + Buildx

Deploy
→ AWS credentials
```

Separating them into jobs allows each job to have its own:

- Runner
- Permissions
- Environment
- Dependencies
- Conditions
- Timeout
- Matrix configuration
- Services
- Concurrency
- Failure behavior

This is one of the most important design benefits of GitHub Actions jobs.

---

## Job Isolation

Jobs do not share a filesystem.

For example:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - run: echo "artifact" > build.txt

  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - run: cat build.txt
```

The deployment job cannot directly access `build.txt`.

The jobs use different runner environments.

To transfer the file, use an artifact:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - run: echo "artifact" > build.txt

      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: build.txt

  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-output

      - run: cat build.txt
```

The distinction is critical:

```text
Same job
→ Files persist between steps

Different jobs
→ Explicit data transfer required
```

---

## Job Execution Lifecycle

A simplified job lifecycle is:

```mermaid
sequenceDiagram
    participant G as GitHub Actions
    participant R as Runner
    participant S as Steps

    G->>R: Allocate runner
    R->>R: Prepare workspace
    R->>S: Execute step 1
    S-->>R: Result
    R->>S: Execute step 2
    S-->>R: Result
    R->>S: Execute remaining steps
    S-->>R: Final result
    R->>G: Publish logs/status
    G->>G: Evaluate dependent jobs
```

Conceptually:

```text
Job queued
   ↓
Runner selected
   ↓
Workspace prepared
   ↓
Steps execute sequentially
   ↓
Job result calculated
   ↓
Outputs/artifacts published
   ↓
Dependent jobs become eligible
```

If a job fails, dependent jobs using `needs` normally do not run unless their conditions explicitly allow execution.

---

## Job Dependencies with `needs`

Jobs without dependencies can execute in parallel.

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: ruff check .

  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest

  build:
    needs:
      - lint
      - test
    runs-on: ubuntu-latest

    steps:
      - run: docker build -t backend .
```

The execution graph becomes:

```text
        ┌──> lint ──┐
        │           │
Start ──┤           ├──> build
        │           │
        └──> test ──┘
```

This is called **fan-out/fan-in**.

```text
Fan-out
   ↓
Multiple independent jobs

Fan-in
   ↓
One job waits for all required jobs
```

---

## Parallel Jobs

Independent jobs can execute concurrently.

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: ruff check .

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/unit

  security:
    runs-on: ubuntu-latest
    steps:
      - run: pip-audit
```

Conceptually:

```text
              ┌── lint
              │
Workflow ─────┼── unit tests
              │
              └── security
```

Parallelism can reduce pipeline duration, but it consumes runner capacity.

The senior engineering trade-off is:

```text
More parallelism
    ↓
Lower latency
    ↓
Higher runner consumption
```

For large repositories, use matrix and concurrency controls deliberately rather than maximizing parallel execution blindly.

---

## Sequential Jobs

Use `needs` when a job requires a previous job to succeed.

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
      - run: docker build -t backend .
```

Execution:

```text
test
 ↓
build
```

This is appropriate when:

- Build should occur only after tests pass
- Deployment requires a successful build
- Security validation must complete before promotion
- Production deployment requires staging validation

---

## Multiple Job Dependencies

A job can depend on multiple jobs:

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: ruff check .

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/unit

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/integration

  build:
    needs:
      - lint
      - unit-tests
      - integration-tests
    runs-on: ubuntu-latest

    steps:
      - run: docker build -t backend .
```

The build job waits until all dependencies complete successfully.

---

## Job-Level Conditions

Jobs can be conditionally executed.

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - run: ./deploy.sh
```

This is useful when the workflow supports multiple execution paths.

For example:

```text
Pull Request
    ↓
Tests

Push to main
    ↓
Tests
    ↓
Build
    ↓
Deploy
```

The deployment job can explicitly require the main branch.

---

## Job Conditions and `needs`

Consider:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - run: ./deploy.sh
```

The deployment job requires:

```text
test succeeds
AND
branch is main
```

This creates a clear dependency graph.

For more complex logic:

```yaml
if: >
  github.event_name == 'push' &&
  github.ref == 'refs/heads/main'
```

Keep conditions explicit enough that an engineer can understand the deployment path from the YAML.

---

## `continue-on-error`

`continue-on-error` allows a job or step failure without making the enclosing execution fail in the normal way.

At the step level:

```yaml
- name: Optional analysis
  continue-on-error: true
  run: ./scripts/experimental-analysis.sh
```

This can be useful for:

- Non-blocking diagnostics
- Experimental checks
- Informational analysis
- Gradual rollout of new validation

It should not normally be used to hide failures in:

- Unit tests
- Security checks
- Database migrations
- Production deployments
- Artifact creation

A dangerous pipeline is:

```yaml
- name: Run tests
  continue-on-error: true
  run: pytest
```

If the pipeline continues toward production, a failing test has effectively become informational.

---

## Job Results and Status Functions

GitHub Actions provides status functions such as:

```text
success()
failure()
cancelled()
always()
```

Example:

```yaml
- name: Upload diagnostics
  if: ${{ failure() }}
  uses: actions/upload-artifact@v4
  with:
    name: diagnostics
    path: logs/
```

A cleanup step can use:

```yaml
- name: Cleanup
  if: ${{ always() }}
  run: ./scripts/cleanup.sh
```

`always()` does not guarantee execution after every possible cancellation or runner termination scenario.

For critical production workflows, cancellation behavior should be designed explicitly.

---

## Job-Level `always()`

A downstream job can use:

```yaml
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest

  diagnostics:
    needs: tests
    if: ${{ always() }}
    runs-on: ubuntu-latest

    steps:
      - run: ./scripts/collect-diagnostics.sh
```

This can be useful for collecting diagnostic information after a dependency completes.

However, do not interpret `always()` as bypassing all workflow state and infrastructure termination behavior.

---

## Steps

A step is an individual operation inside a job.

A step can:

- Execute a shell command
- Invoke an action
- Set environment variables
- Produce outputs
- Upload artifacts
- Modify the workspace
- Run tests
- Build software

Example:

```yaml
steps:
  - name: Checkout source
    uses: actions/checkout@v4

  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: '3.12'

  - name: Install dependencies
    run: pip install -r requirements.txt

  - name: Run tests
    run: pytest
```

Steps execute sequentially by default.

---

## `run` vs `uses`

The two primary step forms are:

```yaml
- name: Run command
  run: pytest
```

and:

```yaml
- name: Checkout repository
  uses: actions/checkout@v4
```

### `run`

`run` executes a command through the configured shell.

```yaml
- name: Run migrations
  run: python manage.py migrate
```

### `uses`

`uses` invokes an action.

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
```

The distinction is:

```text
run
→ Execute commands

uses
→ Execute reusable action logic
```

---

## Shell Execution

GitHub Actions chooses a shell appropriate to the runner unless explicitly configured.

For Linux:

```yaml
- name: Run tests
  shell: bash
  run: |
    set -euo pipefail
    pytest
```

For PowerShell:

```yaml
- name: Run tests
  shell: pwsh
  run: |
    pytest
```

Explicit shell selection can make cross-platform behavior clearer.

For production Linux CI, `bash` with strict error handling is often useful when executing multi-command scripts.

---

## Multi-Line Steps

A step can execute multiple commands:

```yaml
- name: Validate backend
  run: |
    python -m compileall app
    ruff check .
    pytest
```

If command sequencing becomes complex, move the logic into version-controlled scripts:

```yaml
- name: Run CI checks
  run: ./scripts/ci.sh
```

This improves:

- Local reproducibility
- Testing
- Maintainability
- Debugging
- IDE support

The workflow should orchestrate the process rather than becoming a large shell-script repository embedded inside YAML.

---

## Step Working Directory

Steps can specify a working directory:

```yaml
- name: Run backend tests
  working-directory: backend
  run: pytest
```

This is useful in monorepos:

```text
repository/
├── backend/
├── frontend/
├── infrastructure/
└── .github/
```

A backend job can therefore execute:

```yaml
- name: Install backend dependencies
  working-directory: backend
  run: pip install -r requirements.txt
```

Avoid excessive directory switching within a job. Job-level defaults can simplify repeated configuration.

---

## Job Defaults

For example:

```yaml
jobs:
  backend:
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: backend

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

This reduces repetition.

For shell configuration:

```yaml
defaults:
  run:
    shell: bash
    working-directory: backend
```

Defaults improve consistency across steps.

---

## Environment Variables

Environment variables can be defined at workflow, job, or step scope.

### Workflow Scope

```yaml
env:
  PYTHONUNBUFFERED: '1'

jobs:
  test:
    runs-on: ubuntu-latest
```

### Job Scope

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DJANGO_SETTINGS_MODULE: config.settings.test
```

### Step Scope

```yaml
- name: Run tests
  env:
    DATABASE_URL: postgresql://test:test@localhost:5432/app
  run: pytest
```

The narrower scope is useful for limiting exposure.

For sensitive values, prefer secrets rather than ordinary environment variables.

---

## Environment Variable Precedence

When the same variable is defined at multiple levels, the more specific scope takes precedence.

Conceptually:

```text
Workflow env
    ↓
Job env
    ↓
Step env
```

Example:

```yaml
env:
  APP_ENV: global

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      APP_ENV: test

    steps:
      - name: Show environment
        env:
          APP_ENV: step
        run: echo "$APP_ENV"
```

The step sees:

```text
step
```

Use narrow scopes where possible to reduce accidental configuration leakage.

---

## Secrets in Steps

Secrets can be injected into step environments:

```yaml
- name: Authenticate
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
  run: ./scripts/authenticate.sh
```

Prefer environment variables over embedding secrets directly into command strings.

Avoid:

```yaml
run: curl -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" https://api.example.com
```

Prefer:

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
run: |
  curl \
    --header "Authorization: Bearer $API_TOKEN" \
    https://api.example.com
```

Even with masking, secrets should be exposed to as few steps as possible.

---

## `$GITHUB_ENV`

`$GITHUB_ENV` allows one step to make an environment variable available to subsequent steps in the same job.

```yaml
- name: Set version
  run: echo "APP_VERSION=1.4.0" >> "$GITHUB_ENV"

- name: Use version
  run: echo "Version: $APP_VERSION"
```

The variable is available to later steps, not retroactively to the step that writes it.

The data flow is:

```text
Step A
  │
  └── $GITHUB_ENV
          ↓
      Step B
```

This is preferable to deprecated workflow command mechanisms.

---

## `$GITHUB_OUTPUT`

Step outputs allow structured values to move from one step to another.

```yaml
- name: Calculate version
  id: version
  run: echo "value=1.4.0" >> "$GITHUB_OUTPUT"

- name: Use version
  run: echo "Version: ${{ steps.version.outputs.value }}"
```

The important pieces are:

```yaml
id: version
```

and:

```text
$GITHUB_OUTPUT
```

The output is then accessed through:

```text
steps.version.outputs.value
```

---

## Job Outputs

Job outputs allow data to cross job boundaries.

```yaml
jobs:
  metadata:
    runs-on: ubuntu-latest

    outputs:
      version: ${{ steps.version.outputs.value }}

    steps:
      - id: version
        run: echo "value=1.4.0" >> "$GITHUB_OUTPUT"

  build:
    needs: metadata
    runs-on: ubuntu-latest

    steps:
      - name: Display version
        run: echo "Building version ${{ needs.metadata.outputs.version }}"
```

The data flow is:

```text
Step Output
    ↓
Job Output
    ↓
needs.<job>.outputs
```

This is useful for:

- Image tags
- Release versions
- Artifact names
- Deployment targets
- Generated configuration

---

## Passing Structured JSON Between Jobs

For dynamic pipeline configuration, JSON can be used.

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest

    outputs:
      matrix: ${{ steps.generate.outputs.matrix }}

    steps:
      - id: generate
        run: |
          echo 'matrix={"python":["3.11","3.12","3.13"],"database":["postgres","mysql"]}' >> "$GITHUB_OUTPUT"

  test:
    needs: prepare
    runs-on: ubuntu-latest

    strategy:
      matrix: ${{ fromJSON(needs.prepare.outputs.matrix) }}

    steps:
      - name: Test
        run: |
          echo "Python: ${{ matrix.python }}"
          echo "Database: ${{ matrix.database }}"
```

This creates a dynamic execution graph.

```text
prepare
   ↓
JSON configuration
   ↓
fromJSON()
   ↓
Matrix
   ↓
Multiple test jobs
```

Use this pattern when the matrix genuinely needs to be generated dynamically. Static matrices are easier to understand when the configuration is known in advance.

---

## Actions as Steps

An action packages reusable automation.

Example:

```yaml
- name: Checkout repository
  uses: actions/checkout@v4
```

Another:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
```

Actions can accept:

- Inputs
- Environment variables
- Permissions
- Secrets
- Configuration

The action itself runs as part of the step.

---

## Action Inputs

Example:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: pip
```

Inputs are action-specific.

Do not assume that arbitrary `with` keys are supported by every action.

Always use the action's documented interface.

---

## Step IDs

Assign an `id` when later steps need the step's outputs.

```yaml
- name: Generate metadata
  id: metadata
  run: |
    echo "image=backend:${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

- name: Build image
  run: docker build -t "${{ steps.metadata.outputs.image }}" .
```

Without the `id`, the output cannot be addressed through:

```text
steps.<id>.outputs.<name>
```

Use descriptive IDs:

```text
metadata
version
changes
matrix
artifact
```

Avoid generic IDs such as:

```text
step1
step2
step3
```

---

## Step Execution Order

Steps inside a job execute sequentially.

```yaml
steps:
  - name: Install
    run: pip install -r requirements.txt

  - name: Test
    run: pytest

  - name: Build
    run: docker build -t backend .
```

The execution order is:

```text
Install
  ↓
Test
  ↓
Build
```

A later step normally does not execute if a previous step fails.

Conditions can alter this behavior.

---

## Conditional Steps

A step can use `if`.

```yaml
- name: Upload coverage
  if: success()
  uses: actions/upload-artifact@v4
  with:
    name: coverage
    path: coverage.xml
```

A failure-specific diagnostic step:

```yaml
- name: Upload logs
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: logs
    path: logs/
```

A cleanup step:

```yaml
- name: Cleanup
  if: always()
  run: ./scripts/cleanup.sh
```

Conditions should express operational intent rather than hide failures.

---

## Step Timeout

A step can have a timeout:

```yaml
- name: Integration tests
  timeout-minutes: 15
  run: pytest tests/integration
```

Timeouts protect pipelines from:

- Deadlocked tests
- Network hangs
- Unavailable services
- Infinite retry loops
- Misconfigured integration tests

For critical production workflows, timeouts should be explicit around operations that can block.

---

## Job Timeout

Jobs can also have a timeout:

```yaml
jobs:
  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Run integration tests
        run: pytest tests/integration
```

Use job-level timeouts as a safety boundary and step-level timeouts where a particular operation has a known maximum duration.

---

## Jobs with Service Containers

Backend integration tests frequently require databases or caches.

Example:

```yaml
jobs:
  integration-tests:
    runs-on: ubuntu-latest

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

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: pytest tests/integration -v
```

This is a realistic backend testing pattern.

---

## Container Networking

When services are configured for a job running directly on the GitHub-hosted runner, mapped ports can be accessed through the runner:

```text
localhost:5432
localhost:6379
```

When the job itself runs inside a container, service networking behaves differently and services should be referenced using the appropriate service hostname.

For example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    services:
      postgres:
        image: postgres:16
```

The application container can use the service name:

```text
postgres
```

rather than assuming:

```text
localhost
```

This distinction is a common source of integration-test failures.

---

## Jobs Running in Containers

A job can execute inside a container:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

This provides a more controlled runtime than relying entirely on the runner's installed software.

Useful for:

- Reproducible test environments
- Consistent Python versions
- Linux dependency isolation
- Backend integration testing

However, containerized jobs introduce networking and filesystem considerations that must be understood before adding service containers.

---

## Python Backend Job Design

A production-oriented Python test job might look like:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    defaults:
      run:
        shell: bash

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest \
            --cov=app \
            --cov-report=term-missing \
            --cov-report=xml

      - name: Upload coverage
        if: ${{ always() }}
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage.xml
```

This pattern is suitable for Django or FastAPI applications.

---

## Django Job Example

A Django CI job can execute migrations and tests:

```yaml
jobs:
  django-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: django
          POSTGRES_PASSWORD: django
          POSTGRES_DB: django_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U django -d django_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Apply migrations
        env:
          DATABASE_URL: postgresql://django:django@localhost:5432/django_test
          DJANGO_SETTINGS_MODULE: config.settings.test
        run: python manage.py migrate --noinput

      - name: Run tests
        env:
          DATABASE_URL: postgresql://django:django@localhost:5432/django_test
          DJANGO_SETTINGS_MODULE: config.settings.test
        run: pytest
```

The important engineering principle is that CI should test against infrastructure behavior that resembles production where it materially affects correctness.

---

## FastAPI Job Example

FastAPI tests often use `pytest` with an application test client and may require PostgreSQL or Redis for integration coverage.

```yaml
jobs:
  fastapi-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx

      - name: Run API tests
        run: pytest tests/api -v
```

Separate unit and integration tests when their infrastructure requirements differ.

---

## Matrix Jobs

A matrix allows a job to execute across multiple configurations.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version:
          - '3.11'
          - '3.12'
          - '3.13'

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - run: pytest
```

This produces:

```text
test / Python 3.11
test / Python 3.12
test / Python 3.13
```

Matrix testing is valuable when compatibility across supported runtime versions is part of the application's contract.

---

## Multiple Matrix Dimensions

A matrix can contain multiple dimensions:

```yaml
strategy:
  matrix:
    python-version:
      - '3.11'
      - '3.12'
    database:
      - postgres
      - mysql
```

This creates four combinations:

```text
3.11 + postgres
3.11 + mysql
3.12 + postgres
3.12 + mysql
```

This is powerful but can grow quickly.

If there are:

```text
4 Python versions
× 3 databases
× 2 operating systems
```

the matrix creates:

```text
24 combinations
```

Matrix size should therefore be treated as a capacity and cost decision.

---

## Matrix `include`

`include` adds or extends matrix combinations.

```yaml
strategy:
  matrix:
    python-version:
      - '3.11'
      - '3.12'
    include:
      - python-version: '3.13'
        experimental: true
```

The additional combination can expose custom metadata.

```yaml
- name: Experimental test
  if: matrix.experimental == true
  run: pytest
```

Use `include` when a specific combination requires additional configuration.

---

## Matrix `exclude`

`exclude` removes combinations that should not run.

```yaml
strategy:
  matrix:
    python-version:
      - '3.11'
      - '3.12'
    database:
      - postgres
      - mysql

    exclude:
      - python-version: '3.11'
        database: mysql
```

This is useful when a particular compatibility combination is unsupported or unnecessary.

---

## `fail-fast`

Matrix strategies can stop in-progress or queued matrix jobs when one combination fails.

```yaml
strategy:
  fail-fast: true
  matrix:
    python-version:
      - '3.11'
      - '3.12'
      - '3.13'
```

With:

```yaml
fail-fast: false
```

other matrix combinations can continue even if one fails.

Use `fail-fast: false` when you need complete compatibility information from the entire matrix.

---

## `max-parallel`

Limit matrix concurrency:

```yaml
strategy:
  max-parallel: 2
  matrix:
    python-version:
      - '3.11'
      - '3.12'
      - '3.13'
      - '3.14'
```

This can control:

- Runner consumption
- External service load
- Database contention
- API rate limits
- CI cost

The trade-off is:

```text
Higher max-parallel
→ Faster completion
→ More resource consumption

Lower max-parallel
→ Slower completion
→ Lower concurrency
```

---

## Matrix and `needs`

A matrix job can depend on another job:

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    steps:
      - run: ./scripts/prepare.sh

  test:
    needs: prepare
    strategy:
      matrix:
        python-version:
          - '3.11'
          - '3.12'
    runs-on: ubuntu-latest

    steps:
      - run: pytest
```

All matrix combinations wait for the prerequisite job.

This is useful when a common preparation step produces configuration consumed by all matrix combinations.

---

## Matrix Outputs

Matrix output design requires care because multiple matrix executions represent multiple job instances.

If each matrix instance produces an output, define a clear aggregation strategy rather than assuming one output value will represent the entire matrix.

For example, use artifacts for per-matrix reports:

```yaml
- name: Upload test report
  uses: actions/upload-artifact@v4
  with:
    name: report-${{ matrix.python-version }}
    path: reports/
```

Then aggregate reports in a separate job.

This is usually clearer than trying to force many matrix values into a single job output.

---

## Artifacts Between Jobs

Artifacts are appropriate when jobs need to transfer files.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - run: pytest --junitxml=test-results.xml

      - uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results.xml

  report:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/download-artifact@v4
        with:
          name: test-results

      - run: cat test-results.xml
```

Artifacts can contain:

- Test reports
- Coverage reports
- Build packages
- Logs
- Debugging files
- Generated documentation
- Deployment manifests

---

## Artifacts vs Caches

Artifacts and caches have different purposes.

| Feature | Artifacts | Cache |
|---|---|---|
| Primary purpose | Transfer/preserve outputs | Speed up repeated work |
| Authoritative output | Yes | No |
| Intended for deployment | Yes | No |
| Retention | Configurable | Cache lifecycle |
| Reproducibility role | Strong | Optimization |
| Example | Docker metadata, test report | pip cache |
| Missing value | Pipeline may fail | Pipeline should rebuild |

Do not use a cache as the source of truth for a production deployment.

---

## Dependency Caching

Python dependencies can be cached through `setup-python`:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: pip
```

A more explicit cache can use `hashFiles()`:

```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

The dependency file participates in cache identity.

When dependencies change:

```text
requirements.txt
    ↓
hashFiles()
    ↓
New cache key
    ↓
Cache miss
    ↓
Dependencies downloaded
```

This prevents stale dependency caches from becoming the normal installation path.

---

## Cache Keys

A robust cache key commonly includes:

```text
Operating system
Runtime version
Dependency definition
```

For example:

```yaml
key: >-
  ${{ runner.os }}-
  python-${{ matrix.python-version }}-
  ${{ hashFiles('requirements.txt') }}
```

Different Python versions should generally not share a cache indiscriminately.

---

## Cache Restore Keys

Restore keys can provide fallback matches:

```yaml
restore-keys: |
  ${{ runner.os }}-python-${{ matrix.python-version }}-
  ${{ runner.os }}-python-
```

A restore key can improve cache hit rates while still allowing the workflow to rebuild missing dependencies.

---

## `$GITHUB_PATH`

A step can add a directory to the `PATH` for subsequent steps:

```yaml
- name: Add tools to PATH
  run: echo "$HOME/.local/bin" >> "$GITHUB_PATH"
```

Later steps can then invoke executables from that directory.

The mechanism is:

```text
Step A
  ↓
$GITHUB_PATH
  ↓
PATH updated
  ↓
Step B
```

Use it when an installed tool is intentionally exposed to later steps.

---

## Step Summaries

GitHub Actions supports step summaries through `$GITHUB_STEP_SUMMARY`.

```yaml
- name: Publish test summary
  run: |
    {
      echo "## Test Results"
      echo ""
      echo "- Unit tests: passed"
      echo "- Integration tests: passed"
    } >> "$GITHUB_STEP_SUMMARY"
```

Step summaries are useful for operational visibility without requiring engineers to inspect raw logs.

A production pipeline can summarize:

```text
Test count
Coverage
Artifact version
Deployment environment
Deployment duration
Health-check result
```

---

## Annotations

Workflow commands can create annotations for warnings and errors.

For example:

```yaml
- name: Report warning
  run: echo "::warning file=app.py,line=10::Potential configuration issue"
```

Annotations can make failures easier to locate in the GitHub interface.

Use them selectively. Excessive annotations create noise rather than useful diagnostics.

---

## Logging and Debugging

GitHub Actions exposes logs per step.

Useful debugging techniques include:

```yaml
- name: Print environment
  env:
    APP_ENV: ${{ vars.APP_ENV }}
  run: |
    printf 'APP_ENV=%s\n' "$APP_ENV"
```

Avoid printing:

```text
Secrets
Tokens
Passwords
Private keys
Credentials
```

For deeper debugging, GitHub Actions supports debug logging controls. Enable additional diagnostics only when required because verbose logs can increase noise and potentially expose operational details.

---

## Job Permissions

Permissions should be scoped to the job's actual needs.

For a read-only test job:

```yaml
jobs:
  test:
    permissions:
      contents: read

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - run: pytest
```

For AWS OIDC:

```yaml
jobs:
  deploy:
    permissions:
      contents: read
      id-token: write

    runs-on: ubuntu-latest
```

A deployment job should not inherit unnecessary write permissions.

Job boundaries therefore provide a useful security boundary.

---

## Jobs as Security Boundaries

Consider:

```text
lint
  ↓
test
  ↓
build
  ↓
deploy
```

The deployment job may require:

```text
AWS OIDC
ECR access
Environment secrets
Production permissions
```

The lint job does not.

Therefore:

```yaml
jobs:
  lint:
    permissions:
      contents: read

  deploy:
    permissions:
      contents: read
      id-token: write
```

This limits credential and permission exposure.

A compromised dependency or command in a low-privilege job has less access than the same compromise inside the deployment job.

---

## Environment Protection at Job Level

Production environments are attached to jobs:

```yaml
jobs:
  deploy:
    environment:
      name: production

    runs-on: ubuntu-latest

    steps:
      - run: ./deploy.sh
```

The environment can provide:

- Required reviewers
- Environment-specific secrets
- Deployment restrictions
- Deployment history

A useful pipeline is:

```text
Build
  ↓
Staging
  ↓
Validation
  ↓
Production Environment
  ↓
Approval
  ↓
Deploy
```

The deployment job is the natural location for production protection.

---

## Concurrency at Job Level

Concurrency can protect a deployment job:

```yaml
jobs:
  deploy:
    concurrency:
      group: production
      cancel-in-progress: false

    runs-on: ubuntu-latest

    steps:
      - run: ./deploy.sh
```

This prevents multiple deployments from entering the same production execution path simultaneously.

For pull-request validation:

```yaml
jobs:
  test:
    concurrency:
      group: pr-${{ github.event.pull_request.number }}
      cancel-in-progress: true
```

The appropriate policy depends on the job's semantics.

---

## Job Design for a Production Pipeline

A production pipeline might be structured as:

```yaml
jobs:
  lint:
    permissions:
      contents: read
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ruff check .

  unit-tests:
    permissions:
      contents: read
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/unit

  integration-tests:
    permissions:
      contents: read
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/integration

  build:
    needs:
      - lint
      - unit-tests
      - integration-tests
    permissions:
      contents: read
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t backend:${GITHUB_SHA} .

  deploy:
    needs: build
    permissions:
      contents: read
      id-token: write
    environment:
      name: production
    concurrency:
      group: production
      cancel-in-progress: false
    runs-on: ubuntu-latest
    steps:
      - run: ./scripts/deploy.sh
```

The dependency graph is:

```text
              ┌── lint ────────────┐
              │                    │
              ├── unit-tests ──────┤
Workflow ─────┤                    ├── build ── deploy
              └── integration ─────┘
```

This is substantially easier to reason about than placing the entire pipeline into one large job.

---

## One Large Job vs Multiple Jobs

| Design | Advantages | Limitations |
|---|---|---|
| One large job | Simple file sharing, fewer boundaries | Poor isolation, long execution, broad permissions |
| Multiple jobs | Parallelism, isolation, clearer dependencies | Requires explicit artifact/output transfer |
| Hybrid | Balances speed and isolation | Requires deliberate architecture |

A good production pipeline often uses:

```text
Separate jobs for security boundaries and major lifecycle stages
```

while keeping tightly coupled operations inside the same job.

For example:

```text
Good same-job grouping:
Install dependencies
→ Run migrations
→ Run integration tests

Good separate jobs:
Tests
→ Build
→ Deploy
```

---

## When to Split a Job

Split jobs when you need:

- Different permissions
- Different runners
- Different environments
- Parallel execution
- Separate failure domains
- Separate scaling characteristics
- Different secrets
- Different service containers
- Clear deployment gates

Keep operations together when:

- They share substantial filesystem state
- They are tightly coupled
- Splitting would require unnecessary artifact transfer
- Parallel execution provides little value

The goal is not maximum job count.

The goal is useful execution boundaries.

---

## Failure Domains

Jobs naturally create failure domains.

For example:

```text
Lint
 ↓
Failure isolated to code-quality stage

Integration Test
 ↓
Failure isolated to test infrastructure

Build
 ↓
Failure isolated to packaging

Deploy
 ↓
Failure isolated to release infrastructure
```

This improves troubleshooting.

A failure in:

```text
integration-tests
```

should not require investigating:

```text
ECR
ECS
AWS OIDC
```

if those systems are not involved yet.

Clear job boundaries reduce diagnostic complexity.

---

## Data Flow Between Jobs

Use the correct mechanism for each type of data.

| Requirement | Mechanism |
|---|---|
| Value between steps | Step output / `$GITHUB_ENV` |
| Value between jobs | Job outputs |
| File between jobs | Artifact |
| Reusable expensive dependency | Cache |
| External state | Database/API/object storage |
| Deployment artifact | Immutable artifact or registry image |

Avoid using artifacts for small scalar values when job outputs are sufficient.

Avoid using caches as authoritative build outputs.

---

## Build Once, Promote the Same Artifact

A production pipeline should avoid:

```text
Build staging image
      ↓
Rebuild production image
```

Prefer:

```text
Build
  ↓
Immutable image
  ↓
Registry
  ↓
Staging
  ↓
Production
```

The build job creates:

```text
backend:git-8f31c2a
```

The deployment jobs promote the same image.

This prevents environment-specific rebuild drift.

---

## Docker Build Job

A modern Docker build job can use Buildx:

```yaml
jobs:
  build:
    permissions:
      contents: read

    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: false
          tags: backend:${{ github.sha }}
```

A later deployment job can consume the immutable artifact rather than rebuilding it.

---

## Job-Level AWS OIDC Authentication

AWS credentials should not normally be stored as long-lived GitHub secrets for deployment.

A deployment job can use OIDC:

```yaml
jobs:
  deploy:
    permissions:
      contents: read
      id-token: write

    runs-on: ubuntu-latest

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
          aws-region: ap-south-1

      - name: Verify identity
        run: aws sts get-caller-identity
```

The flow is:

```text
GitHub Actions Job
      ↓
GitHub OIDC Token
      ↓
AWS IAM Trust Policy
      ↓
AWS STS
      ↓
Temporary Credentials
      ↓
AWS API
```

Only the deployment job needs the `id-token: write` permission.

---

## Reusable Workflow Jobs

A reusable workflow is invoked at the job level:

```yaml
jobs:
  ci:
    uses: organization/platform/.github/workflows/python-ci.yml@v1
    with:
      python-version: '3.12'
```

The caller treats the reusable workflow as a job-level unit.

This differs from a composite action:

```yaml
steps:
  - uses: organization/platform/.github/actions/python-setup@v1
```

The distinction matters when designing organization-wide CI architecture.

---

## Job Outputs for Deployment Metadata

A build job can expose deployment metadata:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      image: ${{ steps.meta.outputs.image }}

    steps:
      - id: meta
        run: |
          echo "image=123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend:${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

A deployment job can consume it:

```yaml
jobs:
  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - name: Deploy image
        env:
          IMAGE: ${{ needs.build.outputs.image }}
        run: ./scripts/deploy.sh "$IMAGE"
```

This creates explicit data flow rather than relying on hidden state.

---

## Common Job and Step Mistakes

### Mistake: Expecting Files to Survive Between Jobs

Incorrect assumption:

```text
Job A creates file
      ↓
Job B reads file
```

Actual behavior:

```text
Job A runner
      ↓
Runner lifecycle ends

Job B
      ↓
Different runner
```

Use artifacts or an external store.

---

### Mistake: Making Everything One Job

A giant job may look simple:

```text
Lint
Test
Build
Scan
Deploy
```

But it can create:

- Broad permissions
- Long-running jobs
- Poor failure isolation
- Difficult retries
- No useful parallelism
- Larger blast radius

Split meaningful lifecycle and security boundaries.

---

### Mistake: Splitting Every Step Into a Job

The opposite extreme creates:

```text
Checkout job
Install job
Lint job
Test job
Coverage job
```

This causes unnecessary artifact transfers and runner startup overhead.

Use steps when operations are tightly coupled and should share the same workspace.

---

### Mistake: Using `continue-on-error` for Critical Tests

Avoid:

```yaml
- run: pytest
  continue-on-error: true
```

when deployment depends on test success.

Use explicit non-blocking behavior only for checks that are intentionally informational.

---

### Mistake: Giving Every Job Broad Permissions

Avoid repository-wide or workflow-wide write access when only deployment needs privileged access.

Prefer:

```yaml
permissions:
  contents: read
```

and elevate only the specific deployment job:

```yaml
permissions:
  contents: read
  id-token: write
```

---

### Mistake: Passing Secrets Through Outputs

Do not use job outputs as a general secret transport mechanism.

Prefer:

```text
Secret
 ↓
Required job/step
 ↓
Environment variable
```

Keep secret scope as narrow as practical.

---

### Mistake: Hardcoding Versions in Many Steps

Avoid repeated values such as:

```yaml
python-version: '3.12'
```

across many unrelated steps when the version is intended to be a shared configuration value.

Use a consistent configuration strategy through reusable workflows, variables, or matrix definitions.

---

### Mistake: Overusing Dynamic Matrices

Dynamic matrices are powerful, but they make pipeline behavior harder to inspect.

Use a static matrix when:

```text
Supported versions are known
```

Use a dynamic matrix when:

```text
The configuration genuinely changes at runtime
```

Prefer the simplest representation that accurately models the test space.

---

## Job and Step Troubleshooting

### Job Is Skipped

**Symptom**

The workflow succeeds or partially executes, but a job shows as skipped.

**Possible causes**

- `needs` dependency failed
- Job-level `if` evaluated to false
- Branch/event condition did not match
- Matrix configuration produced no applicable combination
- Upstream job was skipped

**Isolation strategy**

Inspect:

```text
Event
→ Job condition
→ needs dependencies
→ Upstream result
→ Matrix configuration
```

Simplify the condition temporarily if necessary.

---

### Step Is Skipped

**Possible causes**

- Previous step failed
- `if` evaluated to false
- Job was cancelled
- Conditional status function prevented execution

Check:

```yaml
if: ${{ failure() }}
```

or:

```yaml
if: ${{ always() }}
```

depending on the intended behavior.

---

### Step Cannot Find a File

If the file was created by an earlier step in the same job, inspect:

```text
Working directory
File path
Shell behavior
Permissions
```

If it was created by another job, download the artifact first.

---

### Job Cannot Access Another Job's Output

Verify:

```yaml
needs: metadata
```

and:

```yaml
outputs:
  version: ${{ steps.version.outputs.value }}
```

Then access:

```yaml
${{ needs.metadata.outputs.version }}
```

The dependency must be explicitly declared.

---

### Matrix Job Consumes Too Many Runners

Inspect:

```text
Matrix dimensions
fail-fast
max-parallel
Runner capacity
Workflow concurrency
```

Reduce unnecessary combinations or set:

```yaml
strategy:
  max-parallel: 2
```

when external infrastructure cannot tolerate high concurrency.

---

### Integration Test Cannot Connect to PostgreSQL

Check:

```text
Service container started
Health check
Port mapping
Host name
Database credentials
Database readiness
```

For a normal runner job:

```text
localhost:5432
```

may be appropriate.

For a containerized job:

```text
postgres:5432
```

may be the correct network address.

---

## Operational Job Design Checklist

For each production job, ask:

### Execution

- Which runner executes it?
- Does it require a container?
- What software must exist on the runner?
- What is the timeout?

### Dependencies

- Which jobs must complete first?
- Can the job run in parallel?
- Does it require service containers?

### Security

- What permissions are required?
- Which secrets are required?
- Can untrusted code execute?
- Does the job need AWS OIDC?

### Data

- What inputs does the job consume?
- What outputs does it produce?
- Are artifacts required?
- Are caches merely optimization?

### Reliability

- What happens when the job fails?
- Can it be safely retried?
- Is deployment idempotent?
- Can concurrent executions race?

### Operations

- Are logs sufficient?
- Are failure artifacts available?
- Is the result visible in a step summary?
- Can an engineer diagnose the failure without rerunning blindly?

---

## Senior-Level Job Architecture

A mature CI/CD pipeline commonly resembles:

```mermaid
flowchart TD
    A[Pull Request] --> B[Lint]
    A --> C[Unit Tests]
    A --> D[Integration Tests]

    B --> E[Quality Gate]
    C --> E
    D --> E

    E --> F[Build]
    F --> G[Security Scan]
    G --> H[Immutable Artifact]

    H --> I[Staging Deployment]
    I --> J[Smoke Tests]

    J --> K[Production Approval]
    K --> L[Production Deployment]
    L --> M[Health Validation]
    M --> N[Monitoring]
```

The job graph should make the release policy visible.

A senior engineer should be able to answer:

```text
Which jobs are independent?
Which jobs are security boundaries?
Which jobs require privileged credentials?
Which jobs can be retried?
Which jobs produce artifacts?
Which jobs consume artifacts?
Where can the pipeline race?
Where can the pipeline fail?
What happens after cancellation?
```

If these answers are unclear, the workflow architecture is probably too implicit.

---

## Job and Step Design Principles

### Keep Jobs Focused

A job should represent a meaningful execution unit.

Good:

```text
lint
unit-tests
integration-tests
build
security-scan
deploy
```

Less useful:

```text
run-command-1
run-command-2
run-command-3
```

### Keep Steps Operationally Cohesive

Good:

```text
Install dependencies
→ Run migrations
→ Run integration tests
```

when they require the same environment.

### Minimize Privileges

Give deployment permissions only to deployment jobs.

### Make Data Flow Explicit

Use:

```text
outputs
artifacts
caches
external systems
```

rather than relying on undocumented state.

### Optimize for Failure Diagnosis

A failed job should identify the failed lifecycle stage.

```text
Integration Tests Failed
```

is more useful than:

```text
CI Pipeline Failed
```

---

## Production Pipeline Example

A realistic backend delivery pipeline can combine the concepts:

```yaml
name: Backend CI/CD

on:
  pull_request:
    branches:
      - main

  push:
    branches:
      - main

jobs:
  lint:
    permissions:
      contents: read
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - run: |
          pip install -r requirements.txt
          ruff check .

  unit-tests:
    permissions:
      contents: read
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - run: |
          pip install -r requirements.txt
          pytest tests/unit

  integration-tests:
    permissions:
      contents: read
    runs-on: ubuntu-latest

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

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - run: pip install -r requirements.txt

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: pytest tests/integration

  build:
    needs:
      - lint
      - unit-tests
      - integration-tests

    permissions:
      contents: read

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - name: Build image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: false
          tags: backend:${{ github.sha }}

  deploy:
    needs: build

    if: >
      github.event_name == 'push' &&
      github.ref == 'refs/heads/main'

    permissions:
      contents: read
      id-token: write

    environment:
      name: production

    concurrency:
      group: production
      cancel-in-progress: false

    runs-on: ubuntu-latest

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
          aws-region: ap-south-1

      - name: Deploy
        run: ./scripts/deploy.sh
```

The architecture is:

```text
                    ┌── Lint ────────────────┐
                    │                        │
Pull Request ───────┼── Unit Tests ──────────┤
                    │                        ├── Build
                    └── Integration Tests ───┘
                                             │
                                             │
                                      Push to main?
                                             │
                                             ▼
                                      Production Deploy
                                             │
                                             ▼
                                        AWS OIDC
```

This structure provides:

- Parallel validation
- Explicit dependencies
- Separate failure domains
- Least-privilege permissions
- Database integration testing
- Docker build isolation
- Production-only deployment conditions
- Environment protection
- Deployment concurrency
- AWS OIDC authentication

## Interview-Level Scenarios

### Production Deployment Must Not Run Twice

A strong design should include:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

and should explain why cancelling an active production deployment can be more dangerous than queueing the next one.

---

### Multiple Python Versions Must Be Tested

Use a matrix:

```yaml
strategy:
  matrix:
    python-version:
      - '3.11'
      - '3.12'
      - '3.13'
```

Explain the trade-off between compatibility coverage and runner consumption.

---

### PostgreSQL and Redis Are Required

Use service containers:

```text
Job
 ├── PostgreSQL service
 ├── Redis service
 └── pytest
```

Include health/readiness checks for services that require startup time.

---

### AWS Credentials Must Not Be Long-Lived Secrets

Use:

```text
GitHub OIDC
    ↓
AWS IAM
    ↓
STS temporary credentials
```

Grant:

```yaml
id-token: write
```

only to the job that needs AWS authentication.

---

### Shared CI Pipeline Across Repositories

Use a reusable workflow:

```yaml
jobs:
  ci:
    uses: organization/platform/.github/workflows/python-ci.yml@v1
```

Explain versioning and governance of the shared workflow.

---

### Compromised Third-Party Action

A strong answer should discuss:

- Action source trust
- SHA pinning
- Least-privilege permissions
- Secret scope
- Job isolation
- Runner isolation
- Organization action policies
- Avoiding unnecessary privileged jobs

The key architectural principle is:

```text
Untrusted dependency
      ↓
Minimal permissions
      ↓
Minimal secrets
      ↓
Limited blast radius
```

---

### Production Rollback

The deployment job should consume an immutable artifact:

```text
backend:git-8f31c2a
```

rather than:

```text
backend:latest
```

Rollback becomes:

```text
Current
  ↓
Known-good previous artifact
  ↓
Redeploy
  ↓
Health validation
```

---

### Self-Hosted Runner Requires Private Network Access

A senior design should consider:

```text
Private VPC
   │
   ├── Self-hosted runner
   │
   ├── Internal services
   │
   └── Databases
```

But self-hosted runners introduce additional risks because untrusted workflow code may gain access to the private network.

Mitigations include:

- Ephemeral runners
- Runner groups
- Restricted labels
- Network segmentation
- Minimal credentials
- Restricted workflow access
- Avoiding untrusted PR execution on privileged runners

---

## Job and Step Interview Traps

### Is a Job the Same as a Step?

No.

```text
Job
→ Collection of steps

Step
→ Individual operation
```

### Do Jobs Share Filesystems?

No.

Artifacts or other explicit mechanisms are required for cross-job files.

### Do Steps Run in Parallel?

No. Steps within a job execute sequentially unless the step itself starts parallel work.

### Can Jobs Run in Parallel?

Yes, when dependencies do not force serialization.

### Why Use `needs`?

To create explicit job dependencies and control execution order.

### When Should You Use an Artifact?

When a file needs to be transferred or retained.

### When Should You Use a Cache?

When data can be regenerated and caching only improves performance.

### Why Separate Deployment Into Its Own Job?

To provide:

- Security isolation
- Environment protection
- Concurrency control
- Clear failure boundaries
- Restricted credentials

### Why Not Put AWS Credentials in Every Job?

Because only the deployment job should need privileged AWS access.

---

## Production Job Design Checklist

Before considering a workflow production-ready, verify:

- Jobs represent meaningful lifecycle or security boundaries.
- Independent jobs run in parallel where useful.
- `needs` expresses actual dependencies.
- Critical tests block downstream deployment.
- `continue-on-error` is not hiding production-critical failures.
- Jobs have appropriate timeouts.
- Step conditions are explicit.
- Files are transferred between jobs using artifacts rather than filesystem assumptions.
- Small cross-job values use job outputs.
- Caches are treated as optimization rather than authoritative state.
- Service containers have appropriate readiness checks.
- Matrix size is intentional.
- `max-parallel` is used when external capacity requires throttling.
- Privileged permissions are limited to the jobs that require them.
- AWS OIDC is isolated to deployment jobs.
- Production deployment uses environment protection.
- Production deployments use concurrency controls.
- Build artifacts are immutable and traceable.
- Logs and diagnostic artifacts support failure analysis.
- The workflow remains understandable without tracing dozens of implicit dependencies.

## Key Takeaways

- A **job** is an isolated execution boundary, while **steps** are sequential operations executed within that job; jobs require explicit mechanisms such as outputs or artifacts to exchange data.
- Use `needs` to build explicit dependency graphs and exploit parallelism where possible, while separating meaningful lifecycle, security, and failure boundaries.
- Use `$GITHUB_ENV` for environment values within a job, `$GITHUB_OUTPUT` and job outputs for structured cross-step or cross-job data, artifacts for files, and caches only for regenerable performance optimizations.
- Production jobs should use least-privilege permissions, explicit conditions, appropriate timeouts, environment protection, and concurrency controls, especially for AWS deployments.
- Good job architecture makes the CI/CD pipeline easier to scale, troubleshoot, secure, retry, and reason about because execution boundaries and data flow are explicit.