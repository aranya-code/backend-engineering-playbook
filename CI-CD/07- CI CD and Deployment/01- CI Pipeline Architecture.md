# 01- CI Pipeline Architecture

## Overview

GitHub Actions is a CI/CD execution platform built around declarative workflows. A production CI pipeline should be designed as an execution architecture rather than as a collection of YAML steps.

A useful mental model is:

```text
Workflow
   │
   ├── Trigger
   │
   ├── Jobs
   │    ├── Lint
   │    ├── Unit Tests
   │    ├── Integration Tests
   │    ├── Security
   │    └── Build
   │
   ├── Artifacts
   │
   ├── Promotion
   │
   └── Deployment
```

For a backend system, a mature pipeline typically looks like:

```text
Pull Request
    │
    ├── Change Detection
    │
    ├── Lint
    │
    ├── Unit Tests ───────────────┐
    │                             │
    ├── Integration Tests         │
    │   ├── PostgreSQL            │
    │   └── Redis                 │
    │                             │
    ├── Security Scan             │
    │                             │
    └── Matrix Tests              │
                                  ▼
                              Build
                                │
                                ▼
                         Immutable Artifact
                                │
                                ▼
                               ECR
                                │
                                ▼
                             Staging
                                │
                             Approval
                                │
                                ▼
                           Production
                                │
                         Health Validation
                                │
                         Monitoring/Rollback
```

The architecture should optimize for:

- Fast feedback for developers
- Deterministic builds
- Parallel execution where possible
- Strong security boundaries
- Immutable artifacts
- Controlled production deployments
- Observable failures
- Reproducibility
- Low operational cost
- Safe recovery

---

## CI/CD Fundamentals

### Continuous Integration

Continuous Integration validates changes continuously as developers merge code into a shared repository.

A CI pipeline normally performs:

```text
Source Change
    ↓
Dependency Installation
    ↓
Lint
    ↓
Unit Tests
    ↓
Integration Tests
    ↓
Security Checks
    ↓
Build Validation
```

The purpose is not merely to prove that the application starts. CI should establish that the change:

- Compiles or packages correctly
- Meets code-quality requirements
- Passes automated tests
- Works against required dependencies
- Does not introduce known security problems
- Produces a deployable artifact

### Continuous Delivery

Continuous Delivery extends CI by producing a deployable artifact and making it available for controlled promotion.

```text
Code
 ↓
Validate
 ↓
Build
 ↓
Artifact
 ↓
Staging
 ↓
Approval
 ↓
Production
```

### Continuous Deployment

Continuous Deployment automatically promotes validated changes to production without a manual approval gate.

The technical pipeline can be identical to Continuous Delivery. The primary difference is the production promotion policy.

### CI vs CD

| Concern | CI | CD |
|---|---|---|
| Linting | Yes | Usually already completed |
| Unit tests | Yes | Usually already completed |
| Integration tests | Yes | Usually already completed |
| Security scanning | Yes | Often both |
| Build artifact | Yes | Consumes artifact |
| Staging deployment | Optional | Common |
| Production approval | No | Optional/required |
| Rollback | Limited | Critical |
| Environment protection | Usually no | Yes |
| Deployment concurrency | Less critical | Critical |

---

## GitHub Actions Architecture

GitHub Actions uses several related execution concepts.

```text
Workflow
   │
   ├── Event / Trigger
   │
   └── Job
        │
        ├── Runner
        │
        └── Steps
             │
             ├── Action
             └── Shell Command
```

### Workflow

A workflow is a YAML definition stored under:

```text
.github/workflows/
```

Example:

```yaml
name: Backend CI

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -r requirements.txt
      - run: pytest
```

A workflow defines:

- Triggers
- Permissions
- Environment configuration
- Jobs
- Job dependencies
- Execution strategy
- Artifacts
- Deployment behavior

### Job

A job is an independently scheduled execution unit.

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest

  test:
    runs-on: ubuntu-latest
```

Unless dependencies are defined, these jobs can execute in parallel.

### Step

A step is an individual operation inside a job.

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Install dependencies
    run: pip install -r requirements.txt

  - name: Run tests
    run: pytest
```

Steps within the same job execute sequentially by default.

### Action

An action packages reusable functionality.

```yaml
- uses: actions/checkout@v4
```

Actions can be:

- JavaScript actions
- Composite actions
- Docker actions
- Marketplace actions
- Internal actions
- Private actions

### Runner

A runner is the execution environment for a job.

```yaml
runs-on: ubuntu-latest
```

Common options include:

- GitHub-hosted Linux runners
- GitHub-hosted Windows runners
- GitHub-hosted macOS runners
- Self-hosted runners

### Workflow → Job → Step → Action → Runner

| Component | Responsibility |
|---|---|
| Workflow | Defines automation |
| Job | Defines an execution unit |
| Step | Performs individual operations |
| Action | Packages reusable behavior |
| Runner | Executes the job |

---

## Workflow Execution Model

A workflow execution can be viewed as a state transition:

```text
Event
  ↓
Workflow Matching
  ↓
Workflow Run Created
  ↓
Jobs Evaluated
  ↓
Dependency Graph Resolved
  ↓
Runner Assigned
  ↓
Steps Executed
  ↓
Artifacts / Outputs
  ↓
Job Completion
  ↓
Workflow Completion
```

For a job with:

```yaml
needs: lint
```

GitHub Actions will not start that job until `lint` has reached a state that allows the dependency graph to continue.

### Job Lifecycle

A simplified lifecycle is:

```text
Queued
  ↓
Runner Selected
  ↓
Runner Prepared
  ↓
Steps Started
  ↓
Step Execution
  ↓
Job Success / Failure / Cancellation
```

### Step Lifecycle

A step typically goes through:

```text
Condition Evaluation
       ↓
Environment Construction
       ↓
Action or Shell Invocation
       ↓
Exit Code
       ↓
Outputs / Environment Changes
       ↓
Next Step
```

A failed step normally causes the job to fail and prevents subsequent steps from running unless their conditions permit execution.

---

## Runners

### GitHub-Hosted Runners

GitHub-hosted runners are managed execution environments.

Advantages:

- Minimal infrastructure management
- Disposable execution environments
- Easy scaling
- Standard operating-system images
- Good isolation for normal CI workloads

Limitations:

- Limited control over installed software
- Network access restrictions
- Runtime and resource constraints
- Hosted-runner availability and quota considerations

### Self-Hosted Runners

Self-hosted runners provide control over:

- Network placement
- Installed software
- Hardware
- Private resources
- Custom runtime dependencies

They also increase the security and operational responsibility of the organization.

A self-hosted runner that executes untrusted code can become a path into the internal network.

### Persistent vs Ephemeral Runners

Persistent:

```text
Runner
  ↓
Job A
  ↓
Job B
  ↓
Job C
```

Ephemeral:

```text
Runner
  ↓
Job
  ↓
Runner Destroyed
```

Ephemeral execution reduces persistent state and cross-job contamination.

---

## Workflow Limitations and Constraints

Production architecture must account for platform limits such as:

- Job execution limits
- Workflow execution limits
- Concurrent execution limits
- Artifact storage
- Artifact retention
- Cache storage
- Runner availability
- Repository and organization policy restrictions
- API rate limits
- Environment protection behavior

Do not design a pipeline assuming unlimited parallelism.

A matrix containing:

```text
4 Python versions
× 3 databases
× 2 operating systems
```

creates:

```text
4 × 3 × 2 = 24
```

potential executions.

The actual cost and duration depend on runner availability, `max-parallel`, job duration, and resource usage.

---

## Workflow Triggers

Triggers determine when a workflow starts.

### `push`

Useful for branch-based CI:

```yaml
on:
  push:
    branches:
      - main
```

### `pull_request`

Useful for validating proposed changes:

```yaml
on:
  pull_request:
    branches:
      - main
```

This is the normal choice when untrusted fork code needs to be tested without granting it the same trust boundary as the target repository.

### `pull_request_target`

Runs in the context of the target repository.

Because this changes the security boundary, it requires particular caution when combined with:

- Checkout of PR code
- Secrets
- Write permissions
- Shell execution
- Third-party actions

Do not treat it as a drop-in replacement for `pull_request`.

### `workflow_dispatch`

Allows manual execution.

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        required: true
        type: choice
        options:
          - staging
          - production
```

Useful for:

- Controlled deployment
- Operational recovery
- Re-running specific workflows
- Manual maintenance

### `schedule`

Useful for recurring jobs:

```yaml
on:
  schedule:
    - cron: "0 2 * * *"
```

Typical use cases:

- Nightly integration tests
- Dependency checks
- Scheduled maintenance
- Periodic security scans

### `workflow_call`

Used to create reusable workflows.

```yaml
on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string
```

### `workflow_run`

Allows one workflow to react to another workflow completing.

Use it carefully because the trust and execution context can differ from the original workflow.

### `repository_dispatch`

Useful when an external system needs to trigger a workflow through GitHub APIs.

### `release`

Useful for release automation:

```yaml
on:
  release:
    types:
      - published
```

---

## Branch, Path, and Tag Filters

Filters prevent unnecessary workflow executions.

```yaml
on:
  pull_request:
    branches:
      - main
    paths:
      - "src/**"
      - "tests/**"
      - "pyproject.toml"
```

Tag filters:

```yaml
on:
  push:
    tags:
      - "v*"
```

Use path filtering carefully in monorepos. A workflow that ignores a required dependency change can produce a false green result.

---

## Expressions and Contexts

GitHub Actions expressions use:

```text
${{ expression }}
```

Example:

```yaml
if: ${{ github.ref == 'refs/heads/main' }}
```

Expressions are evaluated by GitHub Actions. Shell commands are executed later by the runner.

Do not confuse:

```yaml
run: echo "${{ github.ref }}"
```

with:

```bash
echo "$GITHUB_REF"
```

They use different evaluation mechanisms.

### Common Operators

Expressions support:

- `==`
- `!=`
- `&&`
- `||`
- `!`
- Comparisons
- Property access
- Functions

Example:

```yaml
if: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
```

### Important Functions

| Function | Purpose |
|---|---|
| `success()` | Previous required steps/jobs succeeded |
| `failure()` | A previous relevant execution failed |
| `always()` | Allows execution regardless of prior status |
| `cancelled()` | Checks cancellation state |
| `contains()` | Checks whether a value contains another value |
| `startsWith()` | Prefix check |
| `endsWith()` | Suffix check |
| `format()` | String formatting |
| `fromJSON()` | Parses JSON |
| `toJSON()` | Serializes values to JSON |
| `hashFiles()` | Produces a hash from matching files |

### Status Functions

Status functions should be used deliberately.

For example:

```yaml
- name: Upload diagnostics
  if: ${{ failure() }}
  uses: actions/upload-artifact@v4
```

For reporting that should happen after success, failure, or cancellation, `always()` can be useful:

```yaml
if: ${{ always() }}
```

However, `always()` should not be used indiscriminately for critical execution steps. A step that must not run after cancellation can accidentally become difficult to terminate if conditions are designed poorly.

A useful failure-aware condition is:

```yaml
if: ${{ !cancelled() }}
```

---

## GitHub Actions Contexts

Contexts expose workflow execution information.

| Context | Typical Information |
|---|---|
| `github` | Repository, event, ref, SHA, actor |
| `env` | Environment variables |
| `vars` | Repository/org/environment variables |
| `secrets` | Secrets available to the workflow |
| `steps` | Outputs from previous steps |
| `needs` | Outputs and results of dependent jobs |
| `job` | Current job information |
| `runner` | Runner information |
| `matrix` | Current matrix combination |
| `strategy` | Matrix strategy information |
| `inputs` | Workflow or manual inputs |

Example:

```yaml
- name: Display commit
  run: echo "${{ github.sha }}"
```

### Context Availability Matters

Not every context is available in every workflow location.

A senior engineer should verify where a value can be evaluated rather than assuming every context is globally available.

---

## Environment Variables

Environment variables can exist at multiple scopes.

```yaml
env:
  APP_NAME: backend

jobs:
  test:
    env:
      ENVIRONMENT: test

    steps:
      - name: Run tests
        env:
          DATABASE_URL: postgresql://...
        run: pytest
```

Typical precedence is:

```text
Step Environment
      ↓
Job Environment
      ↓
Workflow Environment
```

More specific scopes override broader scopes.

Do not use environment variables as a substitute for structured job outputs when values must cross job boundaries.

---

## Repository and Organization Variables

Non-secret configuration can be stored as variables.

```yaml
env:
  DEPLOY_REGION: ${{ vars.AWS_REGION }}
```

Variables are appropriate for configuration that does not require confidentiality.

Examples:

- AWS region
- Service name
- Deployment configuration
- Non-sensitive feature flags

Secrets should be used for confidential material.

---

## Secrets

Secrets can exist at:

- Repository level
- Organization level
- Environment level

Access:

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
```

### Secret Inheritance

Reusable workflows can receive secrets explicitly or through:

```yaml
secrets: inherit
```

Use inheritance carefully. It can make the secret boundary much broader than necessary.

Prefer explicit secret contracts for security-sensitive reusable workflows.

### Secret Limitations

Secrets should not be assumed to be safe from:

- Malicious scripts
- Command-line exposure
- Debug output
- Artifacts
- Generated files
- Dependency code
- Compromised actions

Secret masking is helpful but is not a replacement for preventing secret exposure.

---

## Environments

Typical deployment environments:

```text
development
    ↓
staging
    ↓
production
```

GitHub environments can provide:

- Environment secrets
- Environment variables
- Required reviewers
- Deployment protection
- Deployment history
- Branch restrictions

A production job can reference:

```yaml
jobs:
  deploy:
    environment:
      name: production
```

This creates a useful security boundary between build and deployment.

---

## Matrix Strategy

Matrices allow the same job definition to run against multiple configurations.

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

Use matrices when compatibility coverage is required.

### Multiple Dimensions

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

This creates:

```text
Python 3.11 + PostgreSQL
Python 3.11 + MySQL
Python 3.12 + PostgreSQL
Python 3.12 + MySQL
```

### `include`

Use `include` to add or modify specific combinations.

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
    include:
      - python-version: "3.13"
        experimental: true
```

### `exclude`

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
        database: "mysql"
```

### `fail-fast`

```yaml
strategy:
  fail-fast: false
```

Use `false` when the full matrix result is valuable even after one combination fails.

### `max-parallel`

```yaml
strategy:
  max-parallel: 3
```

This controls concurrency and helps manage:

- Runner consumption
- Database connections
- External service rate limits
- Cost

---

## Dynamic Matrices

A planning job can generate a JSON matrix.

```yaml
jobs:
  plan:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.generate.outputs.matrix }}

    steps:
      - id: generate
        run: |
          echo 'matrix={"service":["api","worker"]}' >> "$GITHUB_OUTPUT"

  test:
    needs: plan
    strategy:
      matrix: ${{ fromJSON(needs.plan.outputs.matrix) }}

    runs-on: ubuntu-latest

    steps:
      - run: echo "Testing ${{ matrix.service }}"
```

This pattern is useful for:

- Monorepos
- Changed-service detection
- Environment-specific testing
- Configuration-driven pipelines

The planning job becomes part of the pipeline's control plane.

---

## Outputs and Data Flow

Values can move through several scopes.

```text
Step Output
    ↓
Job Output
    ↓
needs.<job>.outputs
    ↓
Another Job
```

### Step Output

```yaml
- id: version
  run: echo "version=1.2.3" >> "$GITHUB_OUTPUT"
```

Consume it:

```yaml
- run: echo "${{ steps.version.outputs.version }}"
```

### Job Output

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      version: ${{ steps.version.outputs.version }}

    steps:
      - id: version
        run: echo "version=1.2.3" >> "$GITHUB_OUTPUT"
```

Consume it:

```yaml
jobs:
  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - run: echo "${{ needs.build.outputs.version }}"
```

### Structured JSON

JSON is useful when passing multiple related values.

```bash
echo 'metadata={"service":"api","environment":"staging"}' >> "$GITHUB_OUTPUT"
```

Then:

```yaml
${{ fromJSON(needs.build.outputs.metadata).service }}
```

Do not use outputs for large files. Use artifacts for file-based data.

---

## Artifacts

Artifacts persist files produced by a workflow run.

```yaml
- name: Upload test reports
  uses: actions/upload-artifact@v4
  with:
    name: test-reports
    path: |
      reports/
      coverage.xml
```

Artifacts are useful for:

- Test reports
- Coverage reports
- Logs
- Debugging files
- Build packages
- Deployment bundles
- Generated documentation

### Artifact Retention

Retention should match the operational need.

Long retention increases storage usage and may expose sensitive historical data for longer.

---

## Artifacts vs Caches

| Feature | Artifact | Cache |
|---|---|---|
| Purpose | Preserve/share outputs | Speed up repeated work |
| Deterministic output | Yes | No |
| Deployment input | Yes | Generally no |
| Test reports | Yes | No |
| Dependencies | Usually no | Yes |
| Persistence guarantee for workflow design | Intended output storage | Optimization |
| Safe to rebuild if missing | Depends | Yes |

A deployment should never depend on a cache being present.

---

## Dependency Caching

Caching reduces dependency installation time.

For Python:

```yaml
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: pip
    cache-dependency-path: pyproject.toml
```

Manual caching can use `hashFiles()`:

```yaml
key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
```

Cache keys should represent the inputs that affect the cached result.

A stale dependency cache can produce confusing failures if cache invalidation is poorly designed.

---

## GitHub Actions Workflow Commands

Modern workflows communicate using supported environment files and summaries.

### `GITHUB_ENV`

Pass environment values to later steps:

```bash
echo "APP_ENV=test" >> "$GITHUB_ENV"
```

### `GITHUB_OUTPUT`

Pass step outputs:

```bash
echo "image_tag=$GITHUB_SHA" >> "$GITHUB_OUTPUT"
```

### `GITHUB_PATH`

Add an executable directory:

```bash
echo "$HOME/.local/bin" >> "$GITHUB_PATH"
```

### Step Summary

```bash
{
  echo "## Test Results"
  echo ""
  echo "- Unit tests: passed"
  echo "- Integration tests: passed"
} >> "$GITHUB_STEP_SUMMARY"
```

Use summaries for human-readable operational information.

---

## Dependency Graphs

A pipeline should reflect logical dependencies rather than simply executing everything sequentially.

```mermaid
flowchart TD
    A[Pull Request] --> B[Lint]
    A --> C[Unit Tests]
    A --> D[Integration Tests]
    A --> E[Security Scan]

    B --> F[Build]
    C --> F
    D --> F
    E --> F

    F --> G[Publish Artifact]
    G --> H[Deploy Staging]
    H --> I[Approval]
    I --> J[Deploy Production]
```

This is preferable to:

```text
Lint → Unit → Integration → Security → Build
```

when those stages do not actually depend on each other.

### Fan-Out

```text
Build
 ├── Python 3.11
 ├── Python 3.12
 ├── PostgreSQL
 └── MySQL
```

### Fan-In

```text
Python 3.11 ─┐
Python 3.12 ─┤
PostgreSQL ──┤──→ Build
MySQL ───────┘
```

The pipeline should fan out where work is independent and fan in only where a downstream operation requires the combined result.

---

## Conditional Execution

Conditions can operate at step or job level.

```yaml
if: ${{ github.ref == 'refs/heads/main' }}
```

Example:

```yaml
deploy:
  if: ${{ github.ref == 'refs/heads/main' }}
  needs:
    - test
    - build
```

Use conditions to model policy rather than hiding important pipeline behavior inside shell scripts.

---

## Reusable Workflows

Reusable workflows package multi-job orchestration.

```yaml
on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string
```

A caller can invoke:

```yaml
jobs:
  ci:
    uses: organization/platform-workflows/.github/workflows/python-ci.yml@v1
    with:
      python-version: "3.12"
    secrets: inherit
```

Reusable workflows are appropriate for organizational standards such as:

- Python CI
- Docker build
- Security scanning
- Staging deployment
- Production deployment

### Reusable Workflow vs Composite Action

| Concern | Reusable Workflow | Composite Action |
|---|---|---|
| Scope | Multiple jobs | Steps within a job |
| `jobs` | Yes | No |
| Job dependencies | Yes | No |
| Matrix orchestration | Yes | Limited to caller |
| Environments | Yes | No independent job environment |
| Runner selection | Job-level | Caller job |
| Best use | Pipeline orchestration | Reusable step sequence |

A composite action should not be used to simulate an entire multi-job pipeline.

---

## Workflow Versioning

Reusable workflows are dependencies.

Avoid unbounded references where reproducibility matters.

Possible strategies:

```text
@v1
@v1.4.2
@<commit SHA>
```

Trade-offs:

- Major version: convenient, controlled compatibility boundary
- Exact version: reproducible
- SHA: strongest immutability, weaker readability

For high-assurance production workflows, pinning to a reviewed immutable reference is preferable.

---

## Concurrency

Concurrency prevents overlapping executions that should not coexist.

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

For pull requests:

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

This allows newer commits to replace obsolete PR runs.

### Production Deployment

Production deployments often should not cancel an active deployment blindly.

```yaml
concurrency:
  group: production-deployment
  cancel-in-progress: false
```

This prevents two deployments from racing against the same environment.

---

## Promotion Architecture

A production pipeline should preferably build once and promote the same artifact.

```text
Source
  ↓
CI
  ↓
Build
  ↓
Immutable Artifact
  ↓
Registry
  ↓
Staging
  ↓
Validation
  ↓
Production
```

Avoid:

```text
Build for Staging
      ↓
Build again for Production
```

The second approach can produce different artifacts due to:

- Dependency changes
- Base image changes
- Build-time timestamps
- Toolchain changes
- External downloads

### Immutable Docker Tags

Useful identifiers include:

```text
my-api:git-7f3a8e2
```

A Git SHA gives a strong relationship between source and artifact.

Semantic tags can additionally be used for human-facing releases:

```text
my-api:1.8.0
```

For deployment integrity, registry digests are stronger than mutable tags.

---

## Containerized CI

A job can execute inside a container:

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

This helps standardize the execution environment.

Consider:

- Image versioning
- Working directory
- Environment variables
- Network behavior
- Volume behavior
- Tool availability
- File permissions

---

## Service Containers

Backend integration tests often require services.

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
          POSTGRES_DB: app_test
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379
```

A typical test stack is:

```text
GitHub Runner
    │
    ├── Python Application
    │
    ├── PostgreSQL
    │
    └── Redis
```

Service containers should be treated as disposable test infrastructure.

---

## Service Readiness

A container being started does not necessarily mean the service is ready.

PostgreSQL may still be:

- Initializing the database
- Creating users
- Applying startup configuration

Use health checks or application-level readiness checks.

Example:

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: app_test
    options: >-
      --health-cmd="pg_isready -U test -d app_test"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=5
```

Do not rely on arbitrary sleeps such as:

```bash
sleep 30
```

unless there is no better readiness mechanism.

---

## Python, Django, and FastAPI CI

A realistic Python pipeline might be:

```text
Checkout
   ↓
Setup Python
   ↓
Restore pip cache
   ↓
Install dependencies
   ↓
Lint
   ↓
Unit tests
   ↓
Integration tests
   ↓
Coverage
   ↓
Security scan
   ↓
Build
```

### Django

Typical CI steps include:

```bash
python manage.py check
python manage.py migrate --noinput
pytest
```

For CI databases, use isolated test databases and never connect to production resources.

### FastAPI

Typical validation:

```bash
pytest
```

with integration tests exercising:

```text
HTTP Client
    ↓
FastAPI
    ↓
Service Layer
    ↓
PostgreSQL / Redis
```

### Celery

If asynchronous jobs are part of the system, integration testing may require:

```text
Application
   ↓
Redis / Broker
   ↓
Celery Worker
   ↓
Task Result
```

Do not make every CI pipeline execute the full distributed system if a smaller test boundary provides sufficient confidence.

---

## Testing Architecture

A production backend pipeline commonly separates:

```text
Unit Tests
    ↓
Integration Tests
    ↓
API Tests
    ↓
End-to-End Tests
```

### Unit Tests

Fast and isolated.

```text
Function
  ↓
Mocked Dependencies
  ↓
Assertion
```

### Integration Tests

Validate real interactions such as:

- PostgreSQL
- MySQL
- Redis
- Message brokers
- HTTP services

### End-to-End Tests

Validate a user-visible or system-level flow across multiple components.

They are slower and generally more expensive.

### Testing Principle

Do not put every test into the most expensive layer.

A healthy distribution generally has:

```text
Many fast unit tests
        ↓
Fewer integration tests
        ↓
Small number of critical E2E tests
```

---

## Matrix Testing for Backend Systems

Matrix testing can validate compatibility:

```yaml
strategy:
  matrix:
    python:
      - "3.11"
      - "3.12"
    database:
      - postgres
      - mysql
```

Do not blindly multiply every dimension.

For example:

```text
4 Python versions
× 3 databases
× 3 operating systems
× 2 application modes
```

creates:

```text
72 combinations
```

That may provide little additional confidence compared with a carefully selected compatibility matrix.

---

## Security Architecture

CI has access to source code, dependencies, credentials, deployment systems, and sometimes production environments. Treat it as a privileged production system.

### GITHUB_TOKEN

Every workflow execution can receive a GitHub token.

Permissions should be minimized.

```yaml
permissions:
  contents: read
```

For an AWS deployment requiring OIDC:

```yaml
permissions:
  contents: read
  id-token: write
```

Do not grant:

```yaml
permissions: write-all
```

without a concrete requirement.

### Job-Level Permissions

Permissions can be narrowed further:

```yaml
jobs:
  test:
    permissions:
      contents: read

  deploy:
    permissions:
      contents: read
      id-token: write
```

This creates privilege separation.

---

## Untrusted Input

GitHub metadata can be attacker-controlled.

Examples include:

- Pull request titles
- Branch names
- Commit messages
- Issue content
- Workflow inputs
- External payloads

Unsafe:

```yaml
- run: echo "${{ github.event.pull_request.title }}"
```

If untrusted data reaches a shell expression, shell syntax may be interpreted.

Prefer passing values through environment variables:

```yaml
- name: Print PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: printf '%s\n' "$PR_TITLE"
```

For Python subprocesses, prefer argument arrays:

```python
import subprocess

subprocess.run(
    ["python", "scripts/check.py", user_value],
    check=True,
)
```

Avoid:

```python
subprocess.run(f"python scripts/check.py {user_value}", shell=True)
```

---

## `pull_request` vs `pull_request_target`

The key security distinction is the trust boundary.

```text
pull_request
    ↓
PR code context
    ↓
Limited trust

pull_request_target
    ↓
Target repository context
    ↓
Potentially higher privilege
```

A dangerous pattern is:

```text
pull_request_target
    ↓
Checkout attacker-controlled code
    ↓
Execute it with secrets/write permissions
```

This can convert an untrusted contribution into privileged code execution.

Use `pull_request_target` only when its security model is intentionally required and the workflow does not accidentally execute untrusted code with privileged access.

---

## Third-Party Actions

An action is executable code.

Therefore:

```yaml
- uses: some-org/some-action@v1
```

is a dependency.

Security considerations include:

- Action ownership
- Maintenance status
- Dependencies
- Release process
- Runtime
- Required permissions
- Secret access
- Network access
- Transitive actions
- Mutable references

For high-assurance pipelines, immutable SHA pinning provides stronger reproducibility:

```yaml
- uses: actions/checkout@<reviewed-commit-sha>
```

Organizations can also use action allowlists and approved internal actions.

---

## Supply Chain Security

A production pipeline should protect:

```text
Source
 ↓
Workflow
 ↓
Dependencies
 ↓
Actions
 ↓
Runner
 ↓
Build
 ↓
Artifact
 ↓
Registry
 ↓
Deployment
```

Important controls include:

- Dependency review
- Dependabot
- Lock files
- Action pinning
- SHA pinning
- SBOM
- Provenance
- Artifact attestations
- Signing
- Vulnerability scanning
- Immutable artifacts
- Protected environments

A secure build is not enough if the resulting artifact cannot be traced to its source.

---

## Runner Security

### GitHub-Hosted Runners

These are generally preferable for normal untrusted CI because the execution environment is managed and disposable.

### Self-Hosted Runner Risks

A persistent self-hosted runner can retain:

- Source code
- Credentials
- Build artifacts
- Tool caches
- Temporary files
- Docker state

A compromised workflow may exploit that residual state.

### Ephemeral Runners

A stronger architecture is:

```text
Provision Runner
      ↓
Execute One Job
      ↓
Collect Required Outputs
      ↓
Destroy Runner
```

This reduces cross-job contamination.

For private infrastructure, use dedicated runner groups and labels.

---

## Docker Build Architecture

A production Docker pipeline can use Buildx:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: false
    tags: my-api:${{ github.sha }}
```

Multi-stage builds reduce runtime image size:

```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir build
RUN python -m build

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /app/dist ./dist
```

Use appropriate production practices for dependency installation, non-root execution, image scanning, and build-context minimization.

---

## Docker Layer Caching

Buildx caching can accelerate repeated builds.

```yaml
with:
  cache-from: type=gha
  cache-to: type=gha,mode=max
```

Caching should remain an optimization.

The build must remain correct if the cache is unavailable.

---

## AWS Authentication with OIDC

Long-lived AWS access keys should not be required for normal GitHub Actions deployments.

The architecture is:

```text
GitHub Actions
      │
      │ OIDC Token
      ▼
AWS STS
      │
      │ AssumeRoleWithWebIdentity
      ▼
IAM Role
      │
      ├── ECR
      ├── ECS
      ├── S3
      ├── Lambda
      └── Other Allowed Services
```

Typical permissions:

```yaml
permissions:
  contents: read
  id-token: write
```

The AWS IAM trust policy should restrict the GitHub identity using conditions such as repository, branch, or environment claims.

The deployment role should contain only the permissions required by the deployment.

---

## AWS Deployment Flow

A typical container deployment:

```text
GitHub Actions
      ↓
Build Docker Image
      ↓
Scan Image
      ↓
Generate SBOM
      ↓
Authenticate via OIDC
      ↓
Push Image to ECR
      ↓
Deploy ECS
      ↓
Health Validation
      ↓
Promote / Rollback
```

The same model can be adapted for:

- ECS
- EC2
- Lambda
- S3
- CloudFormation
- Terraform

---

## Deployment Strategies

### Rolling Deployment

Replace instances progressively.

Advantages:

- Simple operational model
- Incremental replacement

Limitations:

- Old and new versions coexist
- Rollback may require additional deployment work

### Blue/Green

```text
                ┌── Blue
Load Balancer ──┤
                └── Green
```

Traffic is switched between environments.

Advantages:

- Fast traffic switch
- Easier rollback

Limitations:

- Higher infrastructure cost
- Database compatibility still matters

### Canary

A small percentage of traffic is sent to the new version.

```text
95% → Stable
 5% → Canary
```

After health and business metrics are validated, traffic can increase.

### Zero-Downtime Deployment

Zero downtime requires more than the deployment command.

Consider:

- Health checks
- Connection draining
- Backward-compatible APIs
- Database migrations
- Readiness
- Graceful shutdown
- Load balancer behavior

---

## Database Migration Safety

Application deployment and database migrations are often coupled incorrectly.

A safer migration strategy is:

```text
Expand
  ↓
Deploy Compatible Application
  ↓
Backfill
  ↓
Switch Application Behavior
  ↓
Contract
```

Avoid migrations that make the currently running application immediately incompatible when old and new versions may coexist during rolling deployment.

---

## Rollback Architecture

Rollback should be planned before deployment.

For immutable Docker artifacts:

```text
Production
    ↓
Version N
    ↓
Problem Detected
    ↓
Redeploy Version N-1
```

Artifact immutability makes rollback substantially easier.

Rollback should consider:

- Application version
- Database compatibility
- Configuration
- Feature flags
- External API changes
- Background jobs
- Message schemas

A database migration that destroys information may not be safely reversible merely by redeploying the previous application version.

---

## Release Workflows

Release automation can use Git tags:

```text
v1.8.0
```

Typical release flow:

```text
Merge
 ↓
Tag
 ↓
Build
 ↓
Test
 ↓
Generate Release Artifact
 ↓
Publish Release
```

Semantic versioning provides a human-readable compatibility convention.

GitHub Releases can hold:

- Release notes
- Source references
- Build artifacts
- Pre-release versions

---

## Runners and Operations

Runner architecture should match workload requirements.

| Requirement | Typical Runner |
|---|---|
| Standard Python CI | GitHub-hosted |
| Docker build | GitHub-hosted or controlled self-hosted |
| Private database access | Self-hosted/private runner |
| Private network deployment | Self-hosted |
| Highly sensitive deployment | Dedicated/ephemeral |
| Specialized hardware | Self-hosted |

### Runner Labels

Labels allow jobs to select appropriate runners.

```yaml
runs-on:
  - self-hosted
  - linux
  - private-network
```

### Runner Groups

Runner groups provide an organizational access boundary for repositories and workflows.

Do not expose privileged runners broadly.

---

## Monitoring and Observability

A CI/CD platform should be observable as an operational system.

Track:

- Workflow duration
- Queue time
- Job failure rate
- Flaky test rate
- Cache hit rate
- Artifact storage
- Deployment frequency
- Deployment duration
- Rollback frequency
- Runner utilization
- Production deployment failures

A useful CI metric is:

```text
Feedback Time =
Commit/PR creation → Actionable CI Result
```

Reducing feedback time often provides more value than optimizing an individual shell command.

---

## Pipeline Performance

The critical path determines the minimum possible workflow duration.

If:

```text
Lint = 2 min
Unit = 5 min
Integration = 8 min
Security = 4 min
```

and all are independent, the critical path can approach:

```text
max(2, 5, 8, 4) = 8 min
```

before later stages.

If instead they are serialized:

```text
2 + 5 + 8 + 4 = 19 min
```

Parallelism is therefore an architectural decision.

### Performance Optimization Techniques

- Parallelize independent jobs
- Cache dependencies
- Reduce unnecessary matrix combinations
- Use path-based change detection
- Avoid repeated builds
- Build once and promote
- Use appropriate runner sizes
- Keep Docker contexts small
- Avoid unnecessary E2E execution on every change

---

## Cost Optimization

CI cost is influenced by:

```text
Runner Duration
×
Parallelism
×
Execution Frequency
```

Common cost drivers:

- Large matrices
- Slow integration tests
- Rebuilding Docker images
- Re-running unchanged services
- Excessive scheduled workflows
- Large artifact retention
- Persistent self-hosted infrastructure

Cost optimization should not compromise critical security or compatibility coverage.

---

## Reliability

A reliable pipeline should be:

- Deterministic
- Idempotent
- Observable
- Retry-aware
- Failure-isolated
- Reproducible

### Flaky Tests

Retries can hide defects.

Use retries carefully and distinguish:

```text
Transient Infrastructure Failure
```

from:

```text
Deterministic Test Failure
```

A flaky test should be tracked and fixed rather than permanently masked by retries.

### Idempotent Deployment

A deployment should safely tolerate retries.

For example:

```text
Deploy version X
Deploy version X again
```

should not corrupt the deployment state.

---

## High Availability and Disaster Recovery

CI/CD itself is part of the delivery infrastructure.

Consider:

- Backup of critical configuration
- Version-controlled workflows
- Recovery of self-hosted runner infrastructure
- Registry availability
- Artifact retention
- Infrastructure-as-code
- Alternate deployment procedures
- Break-glass operational access

A production system should not become undeployable because a runner image or manually configured server was lost.

---

## Failure Domains

Separate pipeline failures into domains:

```text
Workflow Configuration
        ↓
GitHub Event
        ↓
Runner
        ↓
Dependencies
        ↓
Tests
        ↓
Artifact
        ↓
Registry
        ↓
Cloud Authentication
        ↓
Deployment
        ↓
Application
```

This prevents debugging from becoming guesswork.

---

## Troubleshooting Method

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

### Workflow Syntax Failure

Check:

- YAML indentation
- Unsupported keys
- Expression syntax
- Event configuration

Validate the workflow before investigating application code.

### Trigger Not Running

Check:

- Event type
- Branch filter
- Path filter
- Tag filter
- Workflow file location
- Repository policy

### Job Not Running

Check:

- `needs`
- `if`
- Matrix expansion
- Previous job result
- Concurrency cancellation
- Environment protection

### Output Missing

Check:

```yaml
- id: generate
  run: echo "value=test" >> "$GITHUB_OUTPUT"
```

Then:

```yaml
${{ steps.generate.outputs.value }}
```

For cross-job output:

```yaml
${{ needs.build.outputs.value }}
```

Verify that the producing job declares the output.

### Secret Missing

Check:

- Secret scope
- Environment
- Fork behavior
- Reusable workflow secret contract
- Job permissions
- Whether the secret is actually required

Never print the secret for debugging.

### Permission Failure

Inspect:

```yaml
permissions:
  contents: read
```

Then add only the permission that the failing operation requires.

### Matrix Failure

Check:

- Matrix expansion
- `include`
- `exclude`
- JSON validity
- `fromJSON()`
- `max-parallel`
- Job-specific assumptions

### Artifact Failure

Check:

- Artifact path
- Working directory
- Whether the producing step created the files
- Artifact name
- Retention policy
- Download job dependency

Useful diagnostic command:

```bash
find . -maxdepth 4 -type f | sort
```

### Cache Failure

Treat cache failure as a performance problem first, not a correctness failure.

Check:

- Key
- `hashFiles()`
- Dependency files
- Restore keys
- Cache scope

The pipeline should still work without a cache hit.

### Container Failure

Check:

```bash
docker version
docker info
```

Then inspect:

- Image availability
- Architecture
- Environment variables
- Working directory
- Permissions
- Network
- Volumes

### Service Container Failure

Check readiness rather than only container creation.

For PostgreSQL:

```bash
pg_isready -h localhost -p 5432
```

For Redis:

```bash
redis-cli -h localhost ping
```

### OIDC Failure

Check:

- `id-token: write`
- AWS IAM OIDC provider
- Trust policy
- Repository condition
- Branch/environment condition
- Audience
- Subject claim
- Role ARN

### AWS Deployment Failure

Separate:

```text
GitHub authentication
        ↓
STS role assumption
        ↓
AWS API permissions
        ↓
Registry access
        ↓
Deployment API
        ↓
Application health
```

Do not assume every AWS failure is an IAM problem.

### Docker Registry Failure

Check:

- Authentication
- Registry URL
- Repository existence
- Permissions
- Image tag
- Network
- Registry limits

### Deployment Failure

Check:

- Artifact identity
- Target environment
- Deployment permissions
- Health checks
- Service logs
- Load balancer status
- Database compatibility
- Configuration

### Concurrency Problems

Check:

- Concurrency group
- `cancel-in-progress`
- Workflow-level vs job-level scope
- Environment
- Deployment timing

A deployment race can produce failures even when each individual deployment is correct.

---

## GitHub CLI for CI/CD Operations

GitHub CLI is useful for operational workflows.

### List Workflows

```bash
gh workflow list
```

### Run Workflow

```bash
gh workflow run deploy.yml
```

### List Runs

```bash
gh run list
```

### Inspect a Run

```bash
gh run view <run-id>
```

### View Logs

```bash
gh run view <run-id> --log
```

### Rerun

```bash
gh run rerun <run-id>
```

### List Artifacts

```bash
gh run download <run-id>
```

### Repository Information

```bash
gh repo view
```

### Secrets

```bash
gh secret list
```

### Variables

```bash
gh variable list
```

### Releases

```bash
gh release list
```

Use the CLI for operational visibility and controlled automation rather than treating it as a replacement for proper workflow architecture.

---

## Governance

Enterprise GitHub Actions environments should establish standards for:

- Workflow permissions
- Approved actions
- SHA pinning
- Reusable workflows
- Runner groups
- Environment protection
- Secrets
- Artifact retention
- Security scanning
- Deployment approval
- Auditability

### Action Allowlisting

Organizations may restrict which actions repositories can use.

This reduces supply-chain exposure but increases governance overhead.

### Reusable Workflow Governance

Central workflows should provide:

- Stable interfaces
- Versioning
- Documentation
- Compatibility guarantees
- Security controls
- Consumer migration paths

A reusable workflow becomes platform infrastructure once many repositories depend on it.

---

## Production CI/CD Architecture

A production backend pipeline can be structured as:

```mermaid
flowchart LR
    A[Pull Request] --> B[Lint]
    A --> C[Unit Tests]
    A --> D[Integration Tests]
    A --> E[Security Scan]
    A --> F[Matrix Tests]

    B --> G[Build]
    C --> G
    D --> G
    E --> G
    F --> G

    G --> H[Docker Image]
    H --> I[SBOM / Provenance]
    I --> J[ECR]

    J --> K[Staging]
    K --> L[Health Validation]
    L --> M[Approval]
    M --> N[Production]

    N --> O[Monitoring]
    O --> P{Healthy?}
    P -->|Yes| Q[Complete]
    P -->|No| R[Rollback]
```

The architecture separates:

```text
Validation
    ↓
Artifact Creation
    ↓
Artifact Storage
    ↓
Environment Promotion
    ↓
Production Deployment
```

This separation is one of the most important properties of a mature CI/CD system.

---

## Monorepo CI Architecture

For a monorepo:

```text
repository/
├── services/
│   ├── api/
│   ├── worker/
│   └── billing/
├── shared/
└── infrastructure/
```

A planning job can determine which components changed.

```text
Change Detection
      │
      ├── api changed
      │      ↓
      │    API CI
      │
      ├── worker changed
      │      ↓
      │    Worker CI
      │
      └── infrastructure changed
             ↓
          Infrastructure CI
```

This can significantly reduce unnecessary execution, but dependency relationships must be modeled correctly.

---

## Microservice CI/CD

For multiple services:

```text
                    ┌── Service A CI
                    │
Pull Request ───────┼── Service B CI
                    │
                    └── Service C CI
                           │
                           ▼
                    Shared Build Standards
```

Each service should ideally own its deployment artifact while sharing standardized CI infrastructure through reusable workflows.

Avoid creating a single giant workflow that becomes tightly coupled to every service.

---

## Artifact Promotion Architecture

A robust promotion model is:

```text
Commit SHA
    ↓
Build
    ↓
Artifact Digest
    ↓
Registry
    ↓
Staging
    ↓
Verification
    ↓
Production
```

The production deployment should reference the same artifact that passed staging.

This gives:

- Reproducibility
- Traceability
- Easier rollback
- Lower build variance
- Better auditability

---

## Failure Recovery Architecture

When production deployment fails:

```text
Deployment
   ↓
Health Check
   ↓
Failure
   ↓
Stop Further Promotion
   ↓
Preserve Diagnostics
   ↓
Rollback Known Artifact
   ↓
Validate Health
   ↓
Incident Investigation
```

Do not automatically rebuild an artifact during rollback unless rebuilding is intentionally part of the recovery architecture.

---

## Common Beginner Mistakes

### Serializing Independent Jobs

Bad:

```text
Lint
 ↓
Unit
 ↓
Integration
 ↓
Security
```

when all are independent.

Prefer parallel jobs with a later build dependency.

### Using `sleep` for Readiness

Bad:

```bash
sleep 30
```

Prefer service health checks or application-level readiness checks.

### Using Caches as Artifacts

Caches are optimizations, not deployment artifacts.

### Storing AWS Access Keys

Prefer OIDC and short-lived AWS role credentials.

### Broad Permissions

Avoid:

```yaml
permissions: write-all
```

unless absolutely necessary.

### Executing Untrusted Data

Avoid directly interpolating user-controlled GitHub values into shell commands.

### Rebuilding for Every Environment

Prefer:

```text
Build once → Promote
```

instead of:

```text
Build staging → Build production
```

### Overusing Matrices

A matrix should increase meaningful confidence, not merely multiply executions.

### Overusing `always()`

`always()` can make cleanup and diagnostics reliable, but indiscriminate use can interfere with expected cancellation behavior.

---

## Production Pitfalls

### Mutable Deployment Tags

Deploying:

```text
latest
```

makes artifact identity ambiguous.

Prefer immutable references such as:

```text
service:<commit-sha>
```

or an immutable registry digest.

### Persistent Privileged Runners

A runner with production network access should not casually execute arbitrary pull request code.

### Secrets in Command Arguments

Arguments can appear in process listings or logs.

Prefer environment-based or native credential mechanisms where supported.

### Uncontrolled Reusable Workflows

A shared workflow can become a large blast-radius dependency.

Version it and define a clear contract.

### Unbounded Concurrency

Multiple production deployments can race.

Use environment-specific concurrency controls.

### Ignoring Database Compatibility

Rolling deployments can temporarily run multiple application versions.

Database changes must support the overlap period.

---

## Senior-Level Design Principles

A senior CI/CD design should answer:

### What is the unit of deployment?

Prefer an immutable artifact with a traceable identity.

### What is the trust boundary?

Identify:

- Developer code
- Fork code
- GitHub metadata
- Actions
- Runners
- Secrets
- Cloud accounts
- Production environments

### Where is privilege granted?

Use job-specific permissions and isolated deployment jobs.

### What happens when a dependency fails?

The pipeline should fail predictably and expose enough diagnostic information.

### What happens when deployment runs twice?

Concurrency should prevent unsafe races.

### What happens when production fails?

Rollback should be based on a known-good artifact.

### What happens when a runner is compromised?

Use isolation, ephemeral runners where appropriate, minimal permissions, and restricted network access.

### What happens when a workflow changes?

Treat workflow definitions as production infrastructure and review them accordingly.

---

## CI/CD Architecture Trade-offs

| Decision | Option A | Option B | Trade-off |
|---|---|---|---|
| Runner | GitHub-hosted | Self-hosted | Simplicity vs control |
| Runner lifecycle | Persistent | Ephemeral | Efficiency vs isolation |
| Deployment | Rolling | Blue/green | Cost vs rollback simplicity |
| Promotion | Rebuild | Promote artifact | Flexibility vs reproducibility |
| Workflow reuse | Copy YAML | Reusable workflow | Local simplicity vs governance |
| Action reference | Version tag | SHA | Readability vs immutability |
| Matrix | Broad | Targeted | Coverage vs cost |
| Tests | Serial | Parallel | Simplicity vs speed |
| Credentials | Long-lived keys | OIDC | Simplicity vs security |
| Cache | None | Aggressive | Reliability vs speed |

There is no universally optimal configuration. The correct architecture depends on the trust model, workload, compliance requirements, deployment topology, and operational constraints.

---

## Interview Preparation

### Explain the Architecture

**Question:** How would you design CI for a Django application?

A strong answer should cover:

```text
PR
 ↓
Lint
 ↓
Unit Tests
 ↓
Integration Tests
 ↓
Security
 ↓
Build
 ↓
Immutable Artifact
```

Then discuss:

- PostgreSQL service container
- Redis service container
- Matrix testing
- Coverage
- Artifacts
- Dependency caching
- Permissions
- Reusable workflows
- Concurrency

### Production Deployment Must Not Run Twice

Use:

```yaml
concurrency:
  group: production-deployment
  cancel-in-progress: false
```

Then explain why canceling an active production deployment can itself be unsafe.

### Multiple Python Versions

Use:

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

Then discuss matrix cost and compatibility coverage.

### PostgreSQL and Redis Required

Use service containers with explicit versions and readiness checks.

Explain the networking difference between:

- Runner jobs
- Container jobs
- Service containers

### AWS Credentials Must Not Be Long-Lived

Use:

```text
GitHub OIDC
    ↓
AWS STS
    ↓
IAM Role
```

and restrict the trust policy.

### Reusable CI Across Repositories

Use:

```text
Central Reusable Workflow
          ↓
Repository A
Repository B
Repository C
```

Version the reusable workflow and maintain a stable interface.

### Compromised Third-Party Action

Use:

- SHA pinning
- Least-privilege permissions
- Minimal secrets
- Isolated jobs
- Trusted action sources
- Dependency review
- Runner isolation
- Artifact verification

### Production Rollback

Use immutable artifact references.

```text
Current: v2
Failure
 ↓
Known-good: v1
 ↓
Redeploy v1
```

Discuss database compatibility and external dependencies.

### Promote Docker Image Without Rebuilding

Build:

```text
image@sha256:<digest>
```

Promote that same artifact from staging to production.

### Self-Hosted Runner with Private Network Access

Discuss:

- Runner groups
- Labels
- Network segmentation
- Egress controls
- Ephemeral runners
- Minimal permissions
- Untrusted PR restrictions
- Credential isolation

---

## Production Pipeline Example

```yaml
name: Backend CI/CD

on:
  pull_request:
    branches:
      - main

  push:
    branches:
      - main

permissions:
  contents: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: pip install -r requirements.txt
      - run: ruff check .

  unit:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version:
          - "3.11"
          - "3.12"

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - run: pip install -r requirements.txt
      - run: pytest tests/unit

  integration:
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
          --health-cmd="pg_isready -U test -d app_test"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/app_test
      REDIS_URL: redis://localhost:6379/0

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: pip install -r requirements.txt
      - run: python manage.py migrate --noinput
      - run: pytest tests/integration

  security:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - run: pip install pip-audit
      - run: pip-audit

  build:
    needs:
      - lint
      - unit
      - integration
      - security

    runs-on: ubuntu-latest

    permissions:
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: |
          docker build \
            --tag backend:${GITHUB_SHA} \
            .

      - name: Save image
        run: |
          docker save backend:${GITHUB_SHA} \
            | gzip > backend-${GITHUB_SHA}.tar.gz

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: backend-image-${{ github.sha }}
          path: backend-${{ github.sha }}.tar.gz
```

This example demonstrates the core architectural pattern:

```text
Independent Validation
        ↓
Dependency Gate
        ↓
Build
        ↓
Immutable Artifact
```

A production deployment workflow can consume the resulting artifact and promote it through staging and production.

---

## Production Review Checklist

Before considering a CI/CD architecture production-ready, verify:

### Workflow

- [ ] Workflows are stored under `.github/workflows`
- [ ] Triggers are intentional
- [ ] Branch and path filters are correct
- [ ] Conditions are understandable
- [ ] Independent jobs run in parallel
- [ ] Dependencies use `needs`

### Testing

- [ ] Unit tests execute on every relevant change
- [ ] Integration tests use isolated services
- [ ] Service readiness is validated
- [ ] Matrix coverage is intentional
- [ ] Coverage and reports are retained appropriately

### Artifacts

- [ ] Build outputs are immutable
- [ ] Artifact identity maps to source
- [ ] Artifacts are separated from caches
- [ ] Retention is appropriate
- [ ] Production consumes known artifacts

### Security

- [ ] `GITHUB_TOKEN` permissions are minimized
- [ ] Secrets are scoped appropriately
- [ ] Untrusted input is handled safely
- [ ] Third-party actions are reviewed
- [ ] Critical actions are pinned appropriately
- [ ] Self-hosted runners are isolated
- [ ] OIDC is used for AWS where appropriate

### Deployment

- [ ] Environments are protected
- [ ] Production deployments have concurrency control
- [ ] Health validation exists
- [ ] Rollback is defined
- [ ] Database compatibility is considered
- [ ] Staging and production use the same artifact

### Operations

- [ ] Workflow failures are diagnosable
- [ ] Logs and artifacts are available
- [ ] Runner capacity is monitored
- [ ] Artifact and cache storage are controlled
- [ ] CI cost is monitored
- [ ] Recovery procedures are documented

---

## Key Takeaways

- A production GitHub Actions pipeline is an execution architecture built from workflows, jobs, steps, actions, runners, dependency graphs, artifacts, and controlled environments.
- Independent validation should execute in parallel, while deployment should consume an immutable artifact produced after the required quality and security gates pass.
- Security depends on explicit trust boundaries, least-privilege permissions, safe handling of untrusted input, protected environments, secure actions, isolated runners, and short-lived cloud credentials through OIDC.
- Reliable deployment requires concurrency control, health validation, artifact promotion, backward-compatible changes, and a tested rollback strategy.
- Senior-level CI/CD design optimizes the complete system for feedback time, reproducibility, security, scalability, operational visibility, cost, and failure recovery.