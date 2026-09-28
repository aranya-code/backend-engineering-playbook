# 10- Workflow Limits and Constraints

## Overview

GitHub Actions provides a flexible execution model for CI/CD, but workflows operate within platform limits and resource constraints. These constraints affect execution time, matrix size, concurrency, workflow file size, reusable workflow depth, artifacts, caches, storage, runner availability, API usage, and billing.

Understanding these limits is important when moving from small repository workflows to production pipelines. A workflow that works well with a few tests and one runner can become slow, expensive, unreliable, or impossible to execute when it expands into large matrix builds, multiple environments, integration testing, container builds, and parallel deployments.

The important engineering principle is:

> Design workflows around bounded execution, controlled parallelism, immutable artifacts, predictable resource consumption, and explicit failure handling.

Limits should not be treated merely as numbers to memorize. They are architectural constraints that influence how CI/CD pipelines should be decomposed.

---

## Why Workflow Limits Matter

A production pipeline may contain:

```text
Pull Request
    ↓
Lint
    ↓
Unit Tests
    ↓
Integration Tests
    ├── PostgreSQL
    └── Redis
    ↓
Security Scan
    ↓
Matrix Tests
    ├── Python 3.11
    ├── Python 3.12
    └── Python 3.13
    ↓
Build
    ↓
Docker Image
    ↓
ECR
    ↓
Staging
    ↓
Approval
    ↓
Production
```

Each stage consumes resources.

Typical constraints include:

- Workflow execution duration
- Job execution duration
- Matrix expansion
- Runner concurrency
- Workflow queueing
- Workflow file size
- Reusable workflow nesting
- Number of reusable workflow calls
- Artifact storage
- Cache storage
- Log volume
- Repository and organization quotas
- API rate limits
- Runner availability
- Billing allowances
- Environment approval waiting time
- Deployment concurrency
- Third-party service limits

A senior engineer therefore needs to answer questions such as:

- How many jobs can this matrix generate?
- How much parallelism does this pipeline require?
- What happens when all runners are busy?
- How much artifact storage does the repository consume?
- Is the cache actually reducing execution time?
- Can a workflow wait indefinitely for approval?
- Can a workflow exceed the platform's maximum execution window?
- What happens if a reusable workflow becomes deeply nested?
- Can repeated PR pushes create unnecessary concurrent runs?
- Is a deployment pipeline consuming excessive runner minutes?
- Should a large matrix be split into multiple workflows?

---

## Limits vs Quotas vs Operational Constraints

These terms describe different kinds of restrictions.

| Concept | Meaning | Example |
|---|---|---|
| Hard limit | Platform boundary that cannot normally be exceeded | Maximum matrix expansion |
| Quota | Allocated amount of usage | Included Actions minutes |
| Concurrency limit | Number of jobs that can execute simultaneously | Available hosted runners |
| Storage limit | Maximum or allocated storage | Artifact or cache storage |
| Rate limit | Maximum operations over a period | API requests |
| Retention limit | Maximum lifetime of stored data | Artifact retention |
| Configuration constraint | Restriction imposed by workflow syntax or architecture | Reusable workflow nesting |
| Resource constraint | Practical limitation caused by CPU, memory, network, or runner capacity | Docker build exhausting runner resources |
| Billing constraint | Cost boundary rather than technical execution boundary | Excess private-repository Actions usage |

GitHub can change platform limits over time. Production documentation should therefore distinguish architectural principles from exact platform-specific values.

---

## Workflow Execution Limits

### Workflow Run Duration

A workflow run cannot be allowed to execute indefinitely.

Long-running workflows can consume runners, delay subsequent workflows, increase cost, and make failure recovery difficult.

A workflow can spend time in several states:

```text
Queued
   ↓
Waiting for runner
   ↓
Running jobs
   ↓
Waiting for dependencies
   ↓
Waiting for approval
   ↓
Running deployment
   ↓
Completed
```

The overall workflow lifetime can therefore be significantly longer than the CPU execution time of an individual step.

### Production Implications

Avoid designing CI workflows that remain active for hours unless the workload genuinely requires it.

For example, this is usually a poor design:

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - name: Run extremely long test suite
        run: pytest tests/
```

if `tests/` contains a large number of independent tests that could be parallelized.

A better design is to partition the workload:

```yaml
jobs:
  test:
    strategy:
      matrix:
        shard: [1, 2, 3, 4]

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Run test shard
        run: pytest --splits 4 --group ${{ matrix.shard }}
```

The exact sharding mechanism depends on the testing framework and plugins being used.

---

## Environment Approval Waiting

Deployment environments can introduce waiting periods.

For example:

```text
Build
  ↓
Staging
  ↓
Production Environment
  ↓
Required Reviewer
  ↓
Approval
  ↓
Production Deployment
```

A deployment workflow should not assume that approval is immediate.

This affects:

- Overall workflow lifetime
- Runner utilization
- Deployment scheduling
- Rollout timing
- Incident response

A good architecture keeps expensive compute jobs separate from approval-dependent deployment jobs.

For example:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./build.sh

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: ./deploy.sh
```

The build should produce an immutable artifact before entering the approval stage.

---

## Matrix Expansion Limits

Matrices are powerful because they convert one job definition into many jobs.

Example:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
    database: ["postgresql", "mysql"]
```

This creates:

```text
3 Python versions × 2 databases
= 6 jobs
```

Adding another dimension can increase the number rapidly:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
    database: ["postgresql", "mysql"]
    os: [ubuntu-latest, windows-latest]
```

Now:

```text
3 × 2 × 2 = 12 jobs
```

The general formula is:

```text
Matrix jobs = product of all matrix dimension sizes
```

### Matrix Explosion

Consider:

```text
5 Python versions
× 4 operating systems
× 3 databases
× 2 dependency configurations
× 2 test modes
```

That becomes:

```text
5 × 4 × 3 × 2 × 2 = 240 jobs
```

The pipeline may technically fit within a platform matrix limit while still being operationally impractical.

### Senior Engineering Principle

Do not maximize matrix size merely because the platform permits it.

Use a matrix only where each dimension provides meaningful compatibility coverage.

For example:

```yaml
strategy:
  fail-fast: false
  max-parallel: 6

  matrix:
    python-version: ["3.11", "3.12", "3.13"]
    database: [postgresql, mysql]
```

`max-parallel` limits how many matrix jobs from that strategy are allowed to run simultaneously.

This provides a control between:

```text
Maximum parallelism
        ↓
Fast feedback
        ↓
Higher resource consumption
```

and:

```text
Lower parallelism
        ↓
Lower resource pressure
        ↓
Longer pipeline duration
```

---

## `fail-fast` and Matrix Cost

By default, matrix strategies can cancel in-progress matrix jobs when a failure occurs.

For production test pipelines, consider:

```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
```

This is useful when you want visibility into all compatibility failures.

However, disabling `fail-fast` increases resource consumption because other matrix jobs continue even after one fails.

Use:

```text
fail-fast: true
```

when early failure should stop redundant work.

Use:

```text
fail-fast: false
```

when complete compatibility information is more valuable than saving runner time.

---

## `include` and `exclude` as Limit Controls

A matrix does not have to represent every possible combination.

Example:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
    database: [postgresql, mysql]

    exclude:
      - python-version: "3.11"
        database: mysql

    include:
      - python-version: "3.13"
        database: postgresql
        experimental: true
```

Use `exclude` to remove combinations that do not provide useful coverage.

Use `include` to add specific combinations or metadata without creating a completely independent job definition.

This is often better than duplicating jobs manually.

---

## Dynamic Matrices

Large pipelines sometimes generate matrix configuration dynamically.

Example:

```yaml
jobs:
  generate-matrix:
    runs-on: ubuntu-latest

    outputs:
      matrix: ${{ steps.matrix.outputs.matrix }}

    steps:
      - id: matrix
        run: |
          matrix='{"python-version":["3.11","3.12","3.13"]}'
          echo "matrix=$matrix" >> "$GITHUB_OUTPUT"

  test:
    needs: generate-matrix
    strategy:
      matrix: ${{ fromJSON(needs.generate-matrix.outputs.matrix) }}

    runs-on: ubuntu-latest

    steps:
      - run: python --version
```

Dynamic matrices are useful when the supported configuration comes from:

- Repository configuration
- Generated metadata
- Service definitions
- Build configuration
- Environment-specific configuration

However, dynamically generating hundreds of jobs is usually a design smell.

---

## Runner Concurrency

A workflow can request many jobs, but requested parallelism does not guarantee simultaneous execution.

Consider:

```text
Workflow
├── lint
├── unit-tests
├── integration-tests
├── security-scan
├── build
└── matrix-tests
    ├── Python 3.11
    ├── Python 3.12
    ├── Python 3.13
    └── Python 3.14
```

If only a limited number of runners are available:

```text
Requested jobs
      ↓
Runner queue
      ↓
Available runners
      ↓
Job execution
```

Some jobs remain queued.

### Important Distinction

These are different constraints:

```text
Matrix capacity
    ≠
Runner concurrency
    ≠
Workflow concurrency
    ≠
Job scheduling capacity
```

A matrix can create many jobs, while runner capacity determines how many can actually execute.

---

## `max-parallel`

Use `max-parallel` when a matrix can otherwise create excessive resource pressure.

```yaml
jobs:
  test:
    strategy:
      max-parallel: 4
      matrix:
        python-version: ["3.11", "3.12", "3.13", "3.14"]

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
```

This is particularly useful for:

- Large matrices
- Expensive integration tests
- Database-heavy tests
- Docker builds
- Large organizations
- Self-hosted runner pools
- GPU workloads

---

## Workflow Concurrency

GitHub Actions allows multiple workflow runs to execute concurrently unless concurrency is explicitly controlled.

For a pull request, this can produce:

```text
Commit A → Workflow A
Commit B → Workflow B
Commit C → Workflow C
Commit D → Workflow D
```

If the developer pushes quickly, several runs may become obsolete.

Use workflow concurrency to cancel outdated work:

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This is especially appropriate for PR validation.

### Production Deployment Concurrency

Production deployments usually require different behavior.

```yaml
concurrency:
  group: production-deployment
  cancel-in-progress: false
```

This prevents two production deployments from executing simultaneously.

The distinction is important:

| Workload | Typical strategy |
|---|---|
| PR linting | Cancel obsolete runs |
| PR unit tests | Cancel obsolete runs |
| Feature branch builds | Usually cancel obsolete runs |
| Staging deployment | Often serialize |
| Production deployment | Serialize |
| Database migration | Strong serialization |
| Release publishing | Serialize |

---

## Concurrency Group Design

Avoid overly broad concurrency groups.

Bad:

```yaml
concurrency:
  group: production
```

if multiple independent deployment targets exist.

A better design may be:

```yaml
concurrency:
  group: production-${{ github.repository }}
  cancel-in-progress: false
```

or:

```yaml
concurrency:
  group: deploy-${{ inputs.environment }}
  cancel-in-progress: false
```

The concurrency key should represent the resource that must not be modified concurrently.

---

## Workflow Trigger Rate

A repository can generate excessive workflow events.

For example:

```yaml
on:
  push:
```

runs on every pushed branch and commit.

A large monorepo can therefore create substantial workflow volume.

Use filters where appropriate:

```yaml
on:
  push:
    branches:
      - main
    paths:
      - "backend/**"
      - ".github/workflows/**"
```

This reduces unnecessary execution.

### Common Sources of Excessive Workflow Runs

- Every branch triggering expensive workflows
- Multiple workflows responding to the same event
- Duplicate `push` and `pull_request` workflows
- Automated commits triggering CI again
- Generated files triggering unrelated pipelines
- Multiple services sharing one repository
- Release workflows triggered by every tag
- Excessive scheduled workflows

---

## Branch and Path Filters

Path filters are useful for monorepos.

Example:

```yaml
on:
  pull_request:
    paths:
      - "services/api/**"
      - "shared/**"
      - "pyproject.toml"
```

This can prevent unrelated changes from triggering expensive pipelines.

However, path filtering should not accidentally skip workflows required for:

- Security checks
- Required repository checks
- Release validation
- Infrastructure changes
- Shared library changes

A senior engineer should evaluate the dependency graph before adding aggressive path filters.

---

## Workflow File Size

Workflow files have platform-level size constraints.

Large workflow files are difficult to maintain even before reaching the platform limit.

A workflow should not become a giant YAML program containing:

- Repeated deployment logic
- Repeated setup steps
- Hundreds of matrix combinations
- Large shell scripts
- Embedded configuration
- Multiple unrelated pipelines

Prefer:

```text
Caller Workflow
      ↓
Reusable Workflow
      ↓
Composite Action
      ↓
Individual Steps
```

For example:

```yaml
jobs:
  ci:
    uses: organization/platform-workflows/.github/workflows/python-ci.yml@v1
    with:
      python-version: "3.12"
    secrets: inherit
```

Large workflows should be decomposed based on responsibility, not simply shortened.

---

## Reusable Workflow Constraints

Reusable workflows reduce duplication but introduce their own constraints.

A reusable workflow can call another reusable workflow:

```text
Application Workflow
        ↓
Reusable CI Workflow
        ↓
Reusable Security Workflow
```

Deep nesting should be avoided.

Excessive nesting makes debugging difficult:

```text
A
 ↓
B
 ↓
C
 ↓
D
 ↓
E
 ↓
F
```

A failure in `F` may require tracing multiple workflow boundaries.

Prefer a shallow architecture:

```text
Repository Workflow
       ↓
Platform CI Workflow
       ↓
Jobs
```

### Reusable Workflow vs Composite Action

| Requirement | Reusable Workflow | Composite Action |
|---|---|---|
| Multiple jobs | Yes | No |
| Job orchestration | Yes | No |
| Matrix at workflow job level | Yes | No |
| Environment deployment | Yes | Can be used within a job |
| Package reusable steps | Limited | Yes |
| Runs inside caller job | No | Yes |
| Best for organization-wide CI | Yes | Sometimes |
| Best for repeated setup steps | Sometimes | Yes |

A composite action is not a replacement for a reusable workflow.

---

## Reusable Workflow Call Limits

A workflow can call reusable workflows, but excessive composition can become constrained by platform limits and difficult to reason about.

Avoid architecture such as:

```text
Application
    ↓
Organization Workflow
    ↓
Security Workflow
    ↓
Docker Workflow
    ↓
AWS Workflow
    ↓
Deployment Workflow
```

when these layers are merely wrappers around a few steps.

Prefer meaningful boundaries:

```text
Application Workflow
    ├── Reusable CI Workflow
    └── Reusable Deployment Workflow
```

This reduces:

- Debugging complexity
- Dependency depth
- Permission ambiguity
- Versioning complexity
- Operational coupling

---

## Artifacts

Artifacts are used to persist files produced by a workflow run.

Typical artifacts include:

- Test reports
- Coverage reports
- Compiled packages
- Docker build metadata
- Logs
- Deployment manifests
- Security scan results
- Release packages

Example:

```yaml
- name: Upload coverage
  uses: actions/upload-artifact@v4
  with:
    name: coverage
    path: coverage.xml
```

Artifacts consume storage and may have retention policies.

### Artifact Lifecycle

```text
Job
 ↓
Generate artifact
 ↓
Upload
 ↓
Store
 ↓
Download from another job
 ↓
Deploy / inspect
 ↓
Retention expires
```

Do not upload unnecessary data.

Avoid:

```yaml
path: .
```

because it can accidentally upload:

- Virtual environments
- `.git`
- Dependency caches
- Build directories
- Temporary files
- Secrets
- Large generated datasets

Prefer explicit paths:

```yaml
path: |
  dist/
  reports/
  coverage.xml
```

---

## Artifact Storage Considerations

Artifact consumption depends on:

```text
Artifact size
×
Number of workflow runs
×
Retention period
```

For example:

```text
500 MB artifact
×
20 runs/day
×
30-day retention
```

can produce significant storage consumption.

Production recommendations:

- Upload only useful outputs.
- Keep retention appropriate for the artifact's purpose.
- Separate release artifacts from debugging artifacts.
- Avoid storing reproducible dependencies as artifacts.
- Avoid uploading Docker images as tar files unless required.
- Use registries such as ECR for container images.
- Use artifacts for workflow-to-workflow or job-to-job files where appropriate.

---

## Artifacts vs Caches

Artifacts and caches solve different problems.

| Feature | Artifact | Cache |
|---|---|---|
| Purpose | Preserve workflow output | Speed up future runs |
| Lifecycle | Explicitly associated with run | Reusable across runs |
| Typical content | Reports, packages, build output | Dependencies |
| Reproducibility | Yes | Not authoritative |
| Deployment input | Often | No |
| Safe to delete | Depends | Usually yes |
| Primary goal | Data transfer/persistence | Performance |

Never use caches as the source of truth for production deployment.

For example:

```text
Correct:

Build
 ↓
Artifact / Registry
 ↓
Promotion
 ↓
Production
```

Not:

```text
Build
 ↓
Cache
 ↓
Production
```

---

## Cache Storage and Eviction

Caches are intentionally disposable.

A cache miss must not break a workflow.

Example:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: pip
```

If the cache is unavailable, dependencies should still be installed from the package repository.

Good CI design:

```text
Cache hit
   ↓
Fast execution

Cache miss
   ↓
Normal dependency installation
   ↓
Workflow still succeeds
```

Bad CI design:

```text
Cache miss
   ↓
Build fails
```

### Cache Key Design

A useful key includes the dependency state:

```yaml
key: ${{ runner.os }}-python-${{ hashFiles('**/requirements*.txt', '**/poetry.lock') }}
```

The goal is:

```text
Same dependency definition
        ↓
Potential cache hit

Changed dependency definition
        ↓
New cache key
```

Avoid keys that never change:

```yaml
key: python-cache
```

because stale dependencies can persist unnecessarily.

---

## Cache Size and Retention

Cache storage is bounded.

Large caches can:

- Increase storage consumption
- Slow uploads/downloads
- Reduce cache usefulness
- Increase cache churn

Avoid caching:

- Docker images unnecessarily
- Large generated datasets
- Build outputs that should be artifacts
- Secrets
- Temporary files
- Entire application directories

Cache dependencies and deterministic build inputs rather than arbitrary workspace content.

---

## Logs and Diagnostic Output

Workflow logs are another operational resource.

Excessive logging can make failures difficult to diagnose.

Bad:

```bash
set -x
env
cat "$HOME/.config/application/config"
```

This can expose sensitive information.

Better:

```bash
echo "Running database integration tests"
pytest tests/integration/ -v
```

Use debug logging only when diagnosing a problem.

Production pipelines should distinguish:

```text
Normal logs
Debug logs
Error logs
Security-sensitive values
```

Never deliberately print:

```bash
echo "${{ secrets.AWS_ACCESS_KEY_ID }}"
```

or other credentials.

---

## Environment and Variable Constraints

GitHub Actions supports variables at different scopes:

```text
Organization
    ↓
Repository
    ↓
Environment
    ↓
Workflow / Job / Step
```

Variables are subject to size and count constraints.

Do not use configuration variables as a substitute for a configuration service or database.

Good use cases:

```text
AWS_REGION
DEPLOYMENT_TIMEOUT
SERVICE_NAME
FEATURE_FLAG
```

Poor use cases:

```text
Entire application configuration
Large JSON documents
Database contents
Large certificate bundles
Secrets
```

Secrets should remain in the appropriate secret store.

---

## Environment Constraints

Production environments often introduce:

- Required reviewers
- Branch restrictions
- Environment secrets
- Deployment protection rules
- Deployment history
- Concurrency controls

A common production pattern is:

```yaml
jobs:
  deploy-production:
    needs: deploy-staging
    environment:
      name: production

    runs-on: ubuntu-latest

    steps:
      - name: Deploy
        run: ./deploy.sh
```

Environment protection can create a deliberate pause between CI completion and production execution.

This is a reliability control, not merely a UI feature.

---

## Secrets and Constraint Boundaries

Secrets are intentionally restricted in several workflow scenarios.

Particular care is required with:

- Fork pull requests
- `pull_request`
- `pull_request_target`
- Reusable workflows
- Environment secrets
- `secrets: inherit`

Do not assume that every workflow execution has access to every secret.

For example:

```yaml
jobs:
  deploy:
    environment: production
    permissions:
      contents: read
      id-token: write
```

The production environment should control access to production-specific credentials and configuration.

---

## `GITHUB_TOKEN` Permissions

The default `GITHUB_TOKEN` permissions should not be treated as unlimited.

Prefer explicit permissions:

```yaml
permissions:
  contents: read
```

Then grant additional access only where required:

```yaml
permissions:
  contents: read
  pull-requests: write
```

For AWS OIDC:

```yaml
permissions:
  contents: read
  id-token: write
```

This reduces the blast radius if a workflow step or third-party action is compromised.

---

## API Rate Limits

GitHub Actions workflows may interact with GitHub APIs directly or through actions.

For example:

```bash
gh api repos/"$GITHUB_REPOSITORY"/actions/runs
```

A workflow that repeatedly performs API calls can encounter API rate limits.

Avoid:

```text
Loop
 ↓
API request
 ↓
API request
 ↓
API request
 ↓
...
```

when a single API response or GitHub Actions context can provide the required information.

Prefer:

- Existing contexts
- Step outputs
- Job outputs
- GitHub CLI with bounded requests
- REST API pagination where required
- GraphQL where it materially reduces requests
- Cached metadata where appropriate

---

## GitHub CLI and Operational Limits

GitHub CLI is useful for CI/CD operations:

```bash
gh run list
gh run view
gh run rerun
gh run cancel
gh run download
gh workflow list
gh workflow run
```

Do not build operational automation that repeatedly polls GitHub unnecessarily.

Bad:

```bash
while true; do
  gh run view "$RUN_ID"
  sleep 1
done
```

Prefer bounded polling:

```bash
for attempt in {1..30}; do
  status="$(gh run view "$RUN_ID" --json status --jq '.status')"

  if [ "$status" = "completed" ]; then
    break
  fi

  sleep 10
done
```

Operational automation should always have:

- Timeout
- Retry limit
- Backoff
- Failure handling
- Clear exit status

---

## Docker Build Constraints

Docker builds can consume significant:

- CPU
- Memory
- Disk
- Network bandwidth
- Runner time

A poorly designed Dockerfile can turn a fast CI pipeline into a slow one.

Prefer multi-stage builds:

```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /build/.venv /app/.venv
COPY . .

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "app"]
```

The exact build strategy should match the project's dependency tooling.

---

## Docker Layer Caching

Docker builds should use cache mechanisms intentionally.

Typical flow:

```text
Source
 ↓
Dockerfile
 ↓
Buildx
 ↓
Layer cache
 ↓
Image
 ↓
Registry
```

Avoid invalidating expensive layers unnecessarily.

Bad ordering:

```dockerfile
COPY . .
RUN pip install -r requirements.txt
```

A change to any source file invalidates the dependency installation layer.

Prefer:

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
```

when using a requirements-based build.

---

## Containerized Integration Testing

Service containers add resource consumption.

Typical backend pipeline:

```text
GitHub Actions Job
        │
        ├── Python
        ├── PostgreSQL
        └── Redis
```

Example:

```yaml
jobs:
  integration-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: app
        options: >-
          --health-cmd "pg_isready -U postgres -d app"
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

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/app
          REDIS_URL: redis://localhost:6379/0
        run: pytest tests/integration/ -v
```

The important constraint is that integration testing consumes runner resources in addition to the test process itself.

---

## Service Readiness vs Service Startup

Starting a container does not necessarily mean the service is ready.

For PostgreSQL:

```text
Container started
      ↓
PostgreSQL process started
      ↓
Database initialized
      ↓
Database accepting connections
      ↓
Tests
```

Tests should not immediately assume readiness.

Health checks reduce race conditions.

Without readiness handling:

```text
Test starts
    ↓
Connection refused
```

With readiness handling:

```text
PostgreSQL healthy
    ↓
Test starts
```

---

## Artifact Promotion Constraints

A production pipeline should avoid rebuilding the same application separately for staging and production.

Bad:

```text
Source
 ├── Build → Staging Image
 └── Build → Production Image
```

The two builds may differ because of:

- Dependency changes
- Mutable tags
- External package changes
- Build timestamps
- Build arguments
- Different environment variables
- Different base image resolution

Prefer:

```text
Source
   ↓
Build Once
   ↓
Immutable Artifact
   ↓
Staging
   ↓
Approval
   ↓
Production
```

For Docker:

```text
Git Commit
    ↓
Docker Build
    ↓
Image tagged with commit SHA
    ↓
ECR
    ↓
Staging
    ↓
Production
```

This reduces the dependency on repeated computation.

---

## Immutable Image Tags

Avoid using only:

```text
latest
```

for production deployments.

Prefer:

```text
my-service:8f4c2d1
```

or:

```text
my-service:v2.4.1
```

An immutable identifier makes rollback easier:

```text
Production
    ↓
Current: 8f4c2d1
    ↓
Failure
    ↓
Rollback: 7a19e44
```

The deployment system should know exactly which artifact was deployed.

---

## AWS Integration Constraints

GitHub Actions frequently interacts with:

- AWS IAM
- AWS STS
- Amazon ECR
- Amazon ECS
- Amazon EC2
- AWS Lambda
- Amazon S3
- CloudFormation
- Terraform

Authentication should preferably use OIDC rather than long-lived AWS access keys.

Typical flow:

```text
GitHub Actions
      ↓
OIDC Token
      ↓
AWS STS
      ↓
Assume IAM Role
      ↓
Temporary Credentials
      ↓
ECR / ECS / S3 / CloudFormation
```

Example:

```yaml
permissions:
  contents: read
  id-token: write

steps:
  - name: Configure AWS credentials
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
      aws-region: us-east-1
```

The IAM role should contain only the permissions required by the deployment.

---

## AWS Deployment Constraints

AWS introduces its own service limits independently of GitHub Actions.

For example:

```text
GitHub Actions
    ↓
ECR
    ↓
ECS
    ↓
Load Balancer
    ↓
Application
```

A GitHub workflow may succeed in building an image but fail during deployment because of:

- ECR authorization
- ECS service limits
- Task placement constraints
- Subnet capacity
- Security groups
- Load balancer health checks
- IAM permissions
- API throttling
- Account quotas

Therefore:

> A successful GitHub Actions job does not imply a healthy production deployment.

Deployment validation must check the target system.

---

## Runner Disk Constraints

Hosted runners provide finite local storage.

Large workloads can consume disk through:

- Docker images
- Docker build layers
- Python environments
- Node modules
- Test databases
- Build outputs
- Browser binaries
- Large artifacts

A diagnostic sequence can include:

```bash
df -h
docker system df
du -sh "$RUNNER_TEMP"/* 2>/dev/null || true
du -sh ./* 2>/dev/null | sort -h
```

Do not blindly delete system directories.

Clean only resources created by the workflow.

---

## Runner Memory Constraints

A job may fail even when GitHub Actions itself is functioning correctly.

Example:

```text
Runner
 ├── PostgreSQL
 ├── Redis
 ├── Docker daemon
 ├── pytest
 └── application build
```

All of these consume memory.

Symptoms may include:

- Process killed
- Docker build failure
- Database termination
- Browser crashes
- OOM errors
- Random test failures

Possible solutions:

- Reduce parallelism
- Split jobs
- Use a larger runner
- Reduce service memory
- Run tests in smaller groups
- Avoid unnecessary containers
- Optimize the build

---

## Network Constraints

CI workloads frequently depend on external systems:

```text
Runner
 ├── PyPI
 ├── npm registry
 ├── Docker registry
 ├── GitHub API
 ├── AWS APIs
 └── External services
```

Network failures can therefore appear as application failures.

Common symptoms:

```text
Timeout
Connection reset
DNS failure
HTTP 429
HTTP 5xx
TLS failure
```

Use retries only for transient failures.

Do not blindly retry:

```text
Authentication failures
Authorization failures
Invalid configuration
Syntax errors
Deterministic test failures
```

---

## Retry Constraints

Retries can improve resilience but can also multiply resource consumption.

Bad:

```text
Job
 ↓
Retry
 ↓
Retry
 ↓
Retry
 ↓
Retry
```

This can turn one failure into a large number of runner minutes.

Use bounded retries with backoff:

```text
Attempt 1
   ↓
Failure
   ↓
Wait
   ↓
Attempt 2
   ↓
Failure
   ↓
Longer wait
   ↓
Attempt 3
   ↓
Fail permanently
```

Retries should be applied only to operations where failure is plausibly transient.

---

## Scheduled Workflow Constraints

Scheduled workflows are useful for:

- Dependency checks
- Nightly integration tests
- Security scans
- Cleanup jobs
- Scheduled releases

Example:

```yaml
on:
  schedule:
    - cron: "0 2 * * *"
```

Do not assume scheduled workflows execute at an exact wall-clock second.

Schedules can be affected by platform load and repository activity.

Avoid scheduling large numbers of expensive jobs at the same time across an organization.

Instead of:

```text
02:00
 ├── Repository A
 ├── Repository B
 ├── Repository C
 ├── Repository D
 └── Repository E
```

consider distributing workloads where exact timing is not important.

---

## Workflow Queueing

A workflow can be syntactically valid and still remain queued.

Typical flow:

```text
Workflow triggered
       ↓
Workflow accepted
       ↓
Job queued
       ↓
Runner unavailable
       ↓
Job waits
       ↓
Runner becomes available
       ↓
Job starts
```

Queue time should be treated as an operational metric.

Track:

```text
Queue duration
Execution duration
Total workflow duration
```

If queue time becomes large, investigate:

- Runner concurrency
- Matrix size
- Self-hosted runner health
- Large scheduled workloads
- Organization-level capacity
- Excessive workflow triggers

---

## Self-Hosted Runner Constraints

Self-hosted runners provide more control but shift operational responsibility to the organization.

The organization must manage:

- CPU
- Memory
- Disk
- Networking
- Operating system
- Security patches
- Runner software
- Docker
- Credentials
- Isolation
- Autoscaling
- Availability

Persistent self-hosted runners are especially risky for untrusted code.

Example:

```text
Pull Request
    ↓
Untrusted Code
    ↓
Persistent Runner
    ↓
Previous Workspace
    ↓
Potential Credential / Data Exposure
```

Ephemeral runners provide stronger isolation:

```text
Job
 ↓
New Runner
 ↓
Execute
 ↓
Destroy Runner
```

Use self-hosted runners only when their additional capabilities justify the operational and security cost.

---

## Runner Labels and Scheduling

Labels allow jobs to target specific runner capabilities.

Example:

```yaml
runs-on:
  - self-hosted
  - linux
  - docker
```

A job requiring a matching label can remain queued indefinitely if no runner satisfies the requirement.

Common causes:

- Runner offline
- Incorrect label
- Runner group restriction
- Runner capacity exhausted
- Architecture mismatch
- Private network runner unavailable

When diagnosing a queued job, inspect runner availability before changing workflow logic.

---

## Storage Management

CI/CD storage can accumulate from:

```text
Artifacts
Caches
Packages
Logs
Build outputs
Docker layers
Release assets
```

A production repository should periodically review storage consumption.

Questions to ask:

- Which artifacts are retained?
- Are old artifacts still useful?
- Are caches large?
- Are build outputs duplicated?
- Are release assets duplicated?
- Are Docker images stored in the appropriate registry?
- Are logs being retained unnecessarily?

---

## Cost Constraints

For private repositories, GitHub Actions consumption can have billing implications depending on the GitHub plan and runner type.

The main cost drivers are:

```text
Runner minutes
×
Parallel jobs
×
Workflow frequency
```

Additional storage and related services can contribute to total cost.

A simple optimization model is:

```text
Total CI Cost
≈
Execution Cost
+
Storage Cost
+
External Service Cost
```

### Example

Suppose a workflow performs:

```text
10 matrix jobs
×
10 minutes
×
20 runs/day
```

That produces:

```text
2,000 job-minutes/day
```

Before optimizing, examine whether all ten jobs provide meaningful coverage.

Potential improvements:

- Reduce unnecessary matrix dimensions
- Cache dependencies
- Cancel obsolete PR runs
- Parallelize independent tests
- Split expensive integration tests
- Run full compatibility tests on main instead of every PR
- Use appropriate runner sizes
- Avoid rebuilding unchanged components

---

## Monorepo Constraints

Monorepos can generate excessive CI activity.

Example:

```text
repository/
├── services/
│   ├── users/
│   ├── payments/
│   └── orders/
├── frontend/
├── infrastructure/
└── shared/
```

A change to `frontend/` should not necessarily rebuild every backend service.

Path filters can help:

```yaml
on:
  pull_request:
    paths:
      - "services/payments/**"
      - "shared/**"
```

However, dependency relationships must be understood.

If:

```text
payments → shared
```

then a change in `shared/` may need to trigger payments CI.

The difficult part is not writing the filter; it is modeling the dependency graph correctly.

---

## Production Pipeline Constraints

A mature pipeline should explicitly bound every expensive stage.

Example:

```text
PR
 ↓
Fast Validation
 ↓
Matrix Testing
 ↓
Security
 ↓
Build Once
 ↓
Artifact
 ↓
Staging
 ↓
Approval
 ↓
Production
```

Recommended controls:

| Stage | Useful constraint |
|---|---|
| PR | Concurrency cancellation |
| Lint | Short timeout |
| Unit tests | Parallelization |
| Integration tests | Bounded services |
| Matrix | `max-parallel` |
| Security scan | Explicit scope |
| Build | Dependency cache |
| Docker | Layer caching |
| Artifact | Explicit paths and retention |
| Staging | Deployment concurrency |
| Production | Serialized deployment |
| Rollback | Immutable artifact |

---

## Failure Modes Caused by Limits

### Symptom: Workflow Is Cancelled

Possible causes:

- Maximum execution duration exceeded
- Explicit cancellation
- Concurrency cancellation
- Dependency failure
- Platform failure

Isolation:

```bash
gh run view RUN_ID
```

Check:

- Run status
- Job status
- Cancellation reason
- Logs
- Concurrency configuration

Corrective actions:

- Split long jobs
- Reduce matrix size
- Optimize setup
- Use caching
- Adjust concurrency policy
- Remove unnecessary waiting

---

### Symptom: Matrix Workflow Cannot Start

Possible causes:

- Matrix expansion exceeds platform limits
- Invalid matrix configuration
- Dynamic JSON is malformed
- Excessive dimensions

Isolation:

```text
Calculate:

dimension_1
× dimension_2
× dimension_3
× ...
```

Then inspect:

```yaml
strategy:
  matrix:
```

Corrective actions:

- Remove redundant combinations
- Use `exclude`
- Split the matrix across workflows
- Generate only supported combinations

---

### Symptom: Jobs Remain Queued

Possible causes:

- Runner concurrency exhausted
- Self-hosted runner offline
- Runner labels do not match
- Runner group restrictions
- Organization capacity constraints

Isolation:

```bash
gh run view RUN_ID
```

Then inspect repository and organization runner configuration.

Corrective actions:

- Reduce parallelism
- Fix runner labels
- Add runner capacity
- Improve autoscaling
- Split expensive workloads

---

### Symptom: Cache Misses on Every Run

Possible causes:

- Incorrect key
- Dependency files not included in hash
- OS/runtime changes
- Cache eviction
- Cache scope differences

Example:

```yaml
key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
```

Check whether the dependency definition actually changes between runs.

---

### Symptom: Artifact Storage Grows Rapidly

Possible causes:

- Excessive artifact size
- Long retention
- Duplicate artifacts
- Uploading entire workspaces
- Frequent workflow runs

Corrective actions:

```text
Reduce artifact size
        ↓
Reduce retention
        ↓
Upload only required paths
        ↓
Separate release artifacts
        ↓
Use ECR for container images
```

---

### Symptom: Docker Build Randomly Fails

Possible causes:

- Runner memory exhaustion
- Disk exhaustion
- Network failures
- Registry throttling
- Large build context
- Inefficient Dockerfile

Diagnostics:

```bash
df -h
docker system df
docker info
```

Also inspect the Docker build logs for:

```text
OOM
no space left on device
timeout
429
connection reset
```

---

## Troubleshooting Methodology

Use the following model for limit-related incidents:

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

### Example

```text
Symptom:
Matrix workflow takes 45 minutes.

Possible Causes:
- Too many matrix combinations
- Runner queueing
- Slow dependency installation
- Slow integration tests

Isolation:
Measure queue time and job execution time.

Commands / Checks:
- Review workflow run timing
- Inspect matrix dimensions
- Inspect runner availability
- Review dependency installation time

Root Cause:
Large matrix plus sequential dependency setup.

Corrective Action:
Enable dependency caching and cap matrix parallelism.

Prevention:
Track CI duration and matrix growth during pipeline changes.
```

---

## Designing Around Limits

The goal is not to avoid limits by reducing functionality.

The goal is to design the pipeline so that expensive resources are used deliberately.

### Principle: Bound Fan-Out

Instead of:

```text
1 job
 ↓
200 jobs
```

consider:

```text
1 job
 ↓
Relevant matrix
 ↓
Controlled parallelism
```

### Principle: Build Once

```text
Source
 ↓
Build
 ↓
Immutable Artifact
 ↓
Promotion
```

### Principle: Cancel Obsolete Work

For PR validation:

```yaml
concurrency:
  group: pr-${{ github.workflow }}-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

### Principle: Serialize Critical Resources

For production:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

### Principle: Cache Only Reproducible Dependencies

```text
Cache
 ↓
Performance optimization
```

not:

```text
Cache
 ↓
Source of truth
```

### Principle: Separate CI and CD

```text
CI
├── Lint
├── Test
├── Scan
└── Build

CD
├── Staging
├── Approval
├── Production
└── Rollback
```

This makes approval and deployment constraints easier to reason about.

---

## Architecture Pattern for Large Pipelines

A scalable architecture can look like:

```mermaid
flowchart TD
    PR[Pull Request] --> FAST[Fast Validation]
    FAST --> MATRIX[Matrix Testing]
    MATRIX --> SECURITY[Security Scans]
    SECURITY --> BUILD[Build Once]
    BUILD --> ARTIFACT[Immutable Artifact]
    ARTIFACT --> STAGING[Staging Deployment]
    STAGING --> VALIDATE[Deployment Validation]
    VALIDATE --> APPROVAL[Production Approval]
    APPROVAL --> PROD[Production Deployment]
    PROD --> MONITOR[Monitoring]
    MONITOR --> ROLLBACK[Rollback if Required]

    MATRIX --> CACHE[Dependency Cache]
    BUILD --> REGISTRY[Container Registry]
    REGISTRY --> STAGING
    REGISTRY --> PROD
```

This architecture reduces unnecessary rebuilding and creates explicit boundaries between compute-intensive CI and deployment-sensitive CD.

---

## Senior-Level Optimization Strategy

When a pipeline becomes slow or expensive, do not immediately add more runners.

Measure first.

A useful breakdown is:

```text
Total Pipeline Time
=
Queue Time
+
Setup Time
+
Dependency Installation
+
Test Time
+
Build Time
+
Artifact Transfer
+
Deployment Time
+
Approval Time
```

Each component requires a different optimization.

| Bottleneck | Likely solution |
|---|---|
| Queue time | Runner capacity / lower concurrency |
| Dependency installation | Dependency caching |
| Test execution | Parallelization / sharding |
| Matrix size | Reduce redundant dimensions |
| Docker build | Layer caching / smaller context |
| Artifact transfer | Smaller artifacts |
| Deployment | Better rollout strategy |
| Approval | Improve environment process |
| Repeated builds | Build once and promote |
| Duplicate PR runs | Concurrency cancellation |

---

## Reliability Considerations

A CI/CD pipeline is itself a production system.

It should have:

- Predictable execution
- Bounded retries
- Explicit timeouts
- Controlled concurrency
- Immutable artifacts
- Minimal permissions
- Reproducible builds
- Observable failures
- Rollback capability
- Runner isolation
- Dependency caching
- Storage management

The pipeline should fail clearly rather than remain indefinitely queued or partially executed.

---

## Security Considerations

Limits and resource constraints can become security boundaries.

Examples:

### Matrix Abuse

An untrusted input should not be allowed to generate an uncontrolled matrix.

### Cache Poisoning

Do not allow untrusted workflows to populate caches that trusted deployment workflows consume.

### Runner Exhaustion

Untrusted workflows should not be able to consume all production deployment capacity.

### Artifact Abuse

Do not upload sensitive or unnecessarily large data.

### Log Exposure

Large diagnostic dumps can accidentally expose credentials or configuration.

### Self-Hosted Runner Isolation

Never assume that a self-hosted runner is safe simply because the repository is internal.

Treat workflow execution as code execution.

---

## Cost Optimization Checklist

Before increasing runner capacity, check:

- Are obsolete PR workflows being cancelled?
- Are matrix dimensions necessary?
- Are dependency caches effective?
- Are artifacts unnecessarily large?
- Are artifacts retained too long?
- Are scheduled workflows duplicated?
- Are integration tests running unnecessarily on every commit?
- Are Docker layers being reused?
- Are unrelated monorepo services triggering each other?
- Are self-hosted runners being utilized efficiently?
- Are jobs waiting for dependencies unnecessarily?
- Are workflows rebuilding identical artifacts?

A small reduction in execution time becomes significant at organizational scale.

---

## Common Mistakes

### Treating Platform Limits as Application Limits

GitHub Actions limits are platform constraints, not application architecture.

Designing a pipeline around maximum theoretical capacity often creates operational problems.

### Creating Huge Matrices

A matrix should represent meaningful compatibility coverage, not every imaginable combination.

### Using Unlimited Parallelism

More parallel jobs do not always mean faster completion.

Runner contention, Docker builds, databases, and network bandwidth can become bottlenecks.

### Using Artifacts as Caches

Artifacts and caches have different semantics.

Artifacts represent workflow outputs; caches accelerate future execution.

### Using Caches as Deployment Inputs

Caches are disposable and should never be the authoritative source for production deployment.

### Retaining Everything Forever

Long artifact retention increases storage without necessarily increasing operational value.

### Rebuilding for Every Environment

Separate builds can produce different artifacts.

Prefer:

```text
Build → Artifact → Promote
```

over:

```text
Build → Staging
Build → Production
```

### Ignoring Queue Time

A workflow that executes in five minutes but waits twenty minutes for a runner still has poor developer feedback time.

### Overusing Retries

Retries can hide real failures and multiply CI costs.

### Excessive Workflow Composition

Too many reusable workflows and nested abstractions make failures harder to trace.

### Ignoring External Service Limits

GitHub Actions may be healthy while AWS, Docker registries, package registries, or GitHub APIs are throttling requests.

---

## Interview Traps

### Is a Large Matrix Always Better?

No.

A larger matrix increases compatibility coverage but also increases:

- Job count
- Runner demand
- Execution time
- Storage
- Logs
- Cost
- Failure surface

The correct matrix represents meaningful supported configurations.

### Does `max-parallel` Increase Runner Capacity?

No.

It limits how many matrix jobs can run concurrently. It does not create additional runners.

### Are Artifacts and Caches the Same?

No.

Artifacts preserve workflow outputs. Caches optimize future executions.

### Can Concurrency Replace Deployment Locking Everywhere?

No.

GitHub Actions concurrency can prevent overlapping workflow jobs, but deployment systems and infrastructure may require additional locking or transactional mechanisms.

### Does a Successful Build Mean Production Is Healthy?

No.

Build success proves that the build stage succeeded. Deployment and runtime health require separate validation.

### Should Production Use `latest`?

Using only `latest` weakens traceability and rollback.

Immutable image identifiers such as commit SHA or immutable release tags provide stronger deployment traceability.

### Should More Runners Always Be Added When CI Is Slow?

No.

First determine whether the bottleneck is:

```text
Queue
Execution
Dependency installation
Test design
Matrix explosion
Docker builds
Network
Artifact transfer
Deployment
```

Adding runners does not fix an inefficient job.

---

## Production Limits Checklist

Before releasing a production GitHub Actions pipeline, verify:

### Workflow

- Workflow files are reasonably sized.
- Expensive workflows have appropriate triggers.
- Branch and path filters are intentional.
- Long-running work is partitioned where useful.

### Matrix

- Matrix combinations are justified.
- Matrix expansion is bounded.
- `max-parallel` is used where appropriate.
- `fail-fast` behavior is intentional.
- Dynamic matrices cannot grow without control.

### Concurrency

- PR workflows cancel obsolete runs where appropriate.
- Staging deployments are controlled.
- Production deployments are serialized.
- Database migrations cannot race.
- Concurrency groups represent the actual protected resource.

### Artifacts

- Only required files are uploaded.
- Artifact retention is appropriate.
- Release artifacts are immutable.
- Artifacts are not being used as dependency caches.

### Caches

- Cache keys reflect dependency state.
- Cache misses do not break builds.
- Cache contents are safe to reuse.
- Large or unnecessary caches are avoided.

### Runners

- Runner capacity is understood.
- Self-hosted runners are isolated appropriately.
- Runner labels are correct.
- Resource-intensive jobs are controlled.
- Queue time is monitored.

### Security

- `GITHUB_TOKEN` permissions are minimized.
- Secrets are not printed.
- Untrusted input is not directly executed.
- Third-party actions are trusted and pinned appropriately.
- Self-hosted runners are protected from untrusted workloads.
- AWS access uses OIDC where appropriate.

### Deployment

- Builds produce immutable artifacts.
- The same artifact is promoted across environments.
- Production deployments use environment protection.
- Deployment concurrency is controlled.
- Rollback uses a known previous artifact.

### Operations

- Workflow logs are observable.
- Failure diagnostics are documented.
- CI duration is monitored.
- Storage usage is reviewed.
- Actions usage and cost are monitored.
- External service throttling is considered.

---

## Key Takeaways

- GitHub Actions limits are architectural constraints: matrix size, runner concurrency, execution duration, storage, caching, reusable workflows, and API usage all affect production pipeline design.
- Matrix expansion should be deliberate and bounded; use `include`, `exclude`, `fail-fast`, and `max-parallel` to control resource consumption.
- Artifacts are durable workflow outputs, while caches are disposable performance optimizations; production deployments should rely on immutable artifacts rather than caches.
- Concurrency, runner capacity, queue time, and workflow frequency must be designed together to prevent duplicate work, deployment races, excessive cost, and slow feedback.
- A production pipeline should build once, produce an immutable artifact, promote it through environments, validate deployment health, and retain a deterministic rollback path.