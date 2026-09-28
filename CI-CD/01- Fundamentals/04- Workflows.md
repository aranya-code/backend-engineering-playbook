# 04- Workflows

## Overview

A GitHub Actions workflow is a version-controlled automation definition that describes **when automation starts, what jobs execute, how those jobs depend on one another, where they run, and how data moves through the pipeline**.

Workflow files are stored under:

```text
.github/workflows/
```

Example:

```text
.github/
└── workflows/
    ├── ci.yml
    ├── deploy-staging.yml
    ├── deploy-production.yml
    └── release.yml
```

A useful mental model is:

```text
Event
  ↓
Workflow
  ↓
Jobs
  ↓
Steps
  ├── Actions
  └── Shell Commands
  ↓
Runner
```

A workflow is therefore more than YAML configuration. It is an executable dependency graph.

For a production backend system, a workflow may implement:

```text
Pull Request
      │
      ├── Lint
      ├── Unit Tests
      ├── Integration Tests
      ├── Security Scan
      └── Matrix Tests
              │
              ▼
            Build
              │
              ▼
        Docker Image
              │
              ▼
             ECR
              │
              ▼
           Staging
              │
              ▼
           Approval
              │
              ▼
         Production
              │
              ▼
      Health Validation
              │
              ▼
           Rollback
```

A production workflow should therefore be evaluated on:

- correctness
- security
- determinism
- maintainability
- execution time
- failure isolation
- observability
- recovery behavior
- cost
- scalability

---

## Workflow Components

The core relationship is:

```text
Workflow
   │
   ├── Job
   │    ├── Step
   │    │    ├── Action
   │    │    └── Shell Command
   │    │
   │    └── Runner
   │
   └── Job
        └── ...
```

| Component | Responsibility |
|---|---|
| Workflow | Defines the complete automation process |
| Trigger | Determines when the workflow starts |
| Job | Defines an execution unit |
| Step | Performs an individual operation |
| Action | Reusable functionality invoked by a step |
| Runner | Machine/environment that executes a job |
| Context | Runtime information exposed by GitHub Actions |
| Output | Data passed between steps or jobs |
| Artifact | Durable workflow output |
| Cache | Reusable data intended to accelerate execution |

Understanding these boundaries is essential when designing and troubleshooting workflows.

---

## Workflow File

A workflow is normally a YAML file such as:

```text
.github/workflows/ci.yml
```

A minimal workflow:

```yaml
name: Backend CI

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run tests
        run: pytest
```

The execution model is:

```text
Push
  ↓
Backend CI
  ↓
test job
  ↓
ubuntu-latest runner
  ↓
Checkout
  ↓
pytest
```

---

## Workflow Structure

A production workflow commonly contains:

```yaml
name: Backend CI

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

env:
  PYTHON_VERSION: "3.12"

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install linting tools
        run: python -m pip install ruff

      - name: Run lint
        run: ruff check .
```

The major workflow-level areas are:

```text
name
  ↓
on
  ↓
permissions
  ↓
env
  ↓
concurrency
  ↓
jobs
```

Not every workflow needs every section.

---

## Workflow Naming

Use the `name` field to identify the workflow clearly.

```yaml
name: Backend CI
```

Good names communicate responsibility:

```yaml
name: Backend CI
name: Production Deployment
name: Docker Build
name: Release
name: Scheduled Maintenance
```

Avoid ambiguous names:

```yaml
name: Workflow 1
name: Test
name: Pipeline
```

In repositories containing many workflows, clear names significantly improve operational debugging.

---

## The `on` Section

The `on` section defines workflow triggers.

Example:

```yaml
on:
  push:
    branches:
      - main

  pull_request:
    branches:
      - main

  workflow_dispatch:
```

Common triggers include:

| Trigger | Typical purpose |
|---|---|
| `push` | Run automation after commits |
| `pull_request` | Validate proposed changes |
| `pull_request_target` | Controlled automation using base-repository context |
| `workflow_dispatch` | Manual execution |
| `schedule` | Scheduled automation |
| `workflow_call` | Reusable workflows |
| `workflow_run` | React to another workflow |
| `repository_dispatch` | External event integration |
| `release` | Release automation |

Trigger selection is part of the workflow's security and operational design.

---

## `push`

`push` runs when commits are pushed.

```yaml
on:
  push:
    branches:
      - main
```

Typical uses:

- continuous integration
- artifact creation
- image builds
- staging deployment
- release automation

For example:

```text
Push to main
      ↓
CI
      ↓
Build
      ↓
Deploy Staging
```

A production deployment should not use unrestricted `push` triggering unless every push is intentionally production-authoritative.

---

## `pull_request`

`pull_request` is commonly used to validate proposed changes.

```yaml
on:
  pull_request:
    branches:
      - main
```

A backend PR workflow might run:

```text
Pull Request
     │
     ├── Ruff
     ├── Unit Tests
     ├── PostgreSQL Tests
     ├── Redis Tests
     ├── Security Scan
     └── Docker Build Validation
```

The objective is to detect problems before merge.

A useful security principle is:

> Pull request validation should not receive production privileges merely because it needs to execute untrusted code.

---

## `pull_request_target`

`pull_request_target` executes in the context of the base repository.

This can be useful for repository automation that needs access to trusted repository resources, but it introduces a different security boundary from `pull_request`.

A dangerous pattern is:

```text
Fork PR
   ↓
pull_request_target
   ↓
Checkout PR Code
   ↓
Execute PR Code
   ↓
Secrets
```

If untrusted pull request code executes with access to privileged credentials, those credentials may be exposed.

Therefore, do not treat:

```yaml
pull_request_target:
```

as a simple replacement for:

```yaml
pull_request:
```

Use it only when the trust model is explicitly understood.

---

## `workflow_dispatch`

`workflow_dispatch` enables manual execution.

```yaml
on:
  workflow_dispatch:
```

Typical uses:

- production deployment
- rollback
- maintenance
- operational recovery
- manual release promotion

Inputs can make manual workflows explicit:

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: Target environment
        required: true
        type: choice
        options:
          - staging
          - production

      version:
        description: Version to deploy
        required: true
        type: string
```

The values are available through:

```yaml
${{ inputs.environment }}
```

and:

```yaml
${{ inputs.version }}
```

Inputs should still be validated and treated as untrusted data where appropriate.

---

## `schedule`

Scheduled workflows use cron expressions.

```yaml
on:
  schedule:
    - cron: "0 2 * * *"
```

Typical uses include:

- scheduled tests
- maintenance
- cleanup
- security checks
- dependency verification
- operational reports

Scheduled workflows should be designed to tolerate repeated execution.

If a scheduled workflow creates or modifies resources, make the operation idempotent.

---

## `workflow_call`

`workflow_call` makes a workflow reusable.

```yaml
on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string
```

A caller can use:

```yaml
jobs:
  ci:
    uses: organization/platform-workflows/.github/workflows/python-ci.yml@v1
    with:
      python-version: "3.12"
```

This is useful when several repositories need the same CI or deployment orchestration.

---

## `workflow_run`

`workflow_run` allows a workflow to react to another workflow.

Conceptually:

```text
CI Workflow
    ↓
Completed
    ↓
Deployment Workflow
```

This can separate validation from deployment:

```text
CI
 ├── Lint
 ├── Tests
 ├── Security
 └── Build
       ↓
Deployment
 ├── Staging
 └── Production
```

When using this model, carefully define what artifacts and outputs are trusted across the workflow boundary.

---

## `repository_dispatch`

`repository_dispatch` allows external systems to trigger workflows through the GitHub API.

Architecture:

```text
External System
      ↓
GitHub API
      ↓
repository_dispatch
      ↓
GitHub Actions
```

Possible uses include:

- internal deployment platforms
- external release systems
- cross-system automation
- platform orchestration

Payload data should be validated before being used by privileged operations.

---

## `release`

The `release` event is useful for release-oriented automation.

```text
Release
   ↓
Build
   ↓
Test
   ↓
Package
   ↓
Publish
```

This separates release automation from ordinary development pushes.

---

## Branch Filters

Branch filters restrict when a workflow executes.

```yaml
on:
  push:
    branches:
      - main
      - develop
```

Branches can also be excluded:

```yaml
on:
  push:
    branches-ignore:
      - experimental/**
```

Deployment workflows should normally have explicit branch or release boundaries.

---

## Tag Filters

Tags are useful for versioned releases.

```yaml
on:
  push:
    tags:
      - "v*.*.*"
```

Examples:

```text
v1.0.0
v1.1.0
v2.0.0
```

This supports release pipelines such as:

```text
Git Tag
   ↓
Build
   ↓
Test
   ↓
Package
   ↓
Release
```

---

## Path Filters

Path filters avoid running workflows when unrelated files change.

```yaml
on:
  push:
    branches:
      - main
    paths:
      - "backend/**"
      - "pyproject.toml"
      - ".github/workflows/backend-ci.yml"
```

For a monorepo:

```text
repository/
├── services/
│   ├── users/
│   ├── payments/
│   └── notifications/
├── frontend/
└── infrastructure/
```

A users-service workflow can use:

```yaml
paths:
  - "services/users/**"
```

Path filtering can reduce:

- runner usage
- CI duration
- cost
- unnecessary notifications

However, shared files must be considered carefully.

If a common library changes, a service-specific workflow may need to run even if the service's own directory was not modified.

---

## Workflow Execution Lifecycle

A workflow execution can be viewed as:

```text
Event
  ↓
Trigger Matching
  ↓
Workflow Selected
  ↓
Jobs Evaluated
  ↓
Matrix Expansion
  ↓
Dependency Graph Resolved
  ↓
Jobs Queued
  ↓
Runner Assigned
  ↓
Job Environment Prepared
  ↓
Steps Execute
  ↓
Job Result
  ↓
Dependent Jobs Execute
  ↓
Workflow Result
```

This model is useful when diagnosing failures.

For example:

```text
Workflow does not start
```

is different from:

```text
Workflow starts but job is skipped
```

which is different from:

```text
Job starts but a step fails
```

These failures belong to different layers.

---

## Job Execution Lifecycle

A job roughly follows this lifecycle:

```text
Job Selected
     ↓
Runner Allocated
     ↓
Job Environment Prepared
     ↓
Container / Services Started
     ↓
Default Environment Prepared
     ↓
Steps Execute Sequentially
     ↓
Post-Step Processing
     ↓
Job Result
```

A job runs on one runner environment.

This is why files created in one job should not be assumed to exist in another job.

Use artifacts or other explicit transfer mechanisms when data must cross job boundaries.

---

## Step Execution Lifecycle

Steps within a job execute sequentially.

```yaml
steps:
  - name: Checkout
    uses: actions/checkout@v4

  - name: Install
    run: python -m pip install -r requirements.txt

  - name: Test
    run: pytest
```

Execution:

```text
Checkout
   ↓
Install
   ↓
Test
```

Later steps can access files and environment state produced by earlier steps within the same job.

---

## Jobs

Jobs are the major execution units inside a workflow.

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - run: ruff check .

  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - run: pytest
```

Independent jobs can execute in parallel.

```text
          ┌── Lint ──┐
Start ────┤          │
          └── Test ──┘
```

This is one of the most important mechanisms for reducing CI duration.

---

## Job Dependencies with `needs`

Use `needs` when execution ordering matters.

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
      - run: docker build .
```

The dependency graph is:

```text
Test
 ↓
Build
```

Multiple dependencies are possible:

```yaml
build:
  needs:
    - lint
    - test
    - security
```

Result:

```text
Lint ──────────┐
Test ──────────┼──► Build
Security ──────┘
```

---

## Fan-Out and Fan-In

A production CI pipeline commonly uses fan-out/fan-in.

```text
                  ┌── Lint ───────────┐
                  │                   │
Start ────────────┼── Unit Tests ─────┼──► Build
                  │                   │
                  ├── Security ───────┤
                  │                   │
                  └── Integration ────┘
```

Independent checks execute concurrently.

The build starts only after the required checks complete successfully.

This reduces the critical path without weakening dependencies.

---

## Steps

Steps represent individual operations within a job.

A step can execute a shell command:

```yaml
- name: Run tests
  run: pytest
```

or invoke an action:

```yaml
- name: Checkout
  uses: actions/checkout@v4
```

A production workflow usually combines both:

```text
Action
  ↓
Action
  ↓
Shell Command
  ↓
Shell Command
```

---

## `run` vs `uses`

The two mechanisms operate at different abstraction levels.

| Syntax | Purpose |
|---|---|
| `run` | Execute commands on the runner |
| `uses` | Invoke an action |
| `with` | Provide action inputs |
| `env` | Provide environment variables |

Example:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"

- name: Install dependencies
  run: python -m pip install -r requirements.txt
```

A useful design principle is:

> Use actions for standardized reusable functionality and shell commands for repository-specific operations.

---

## Actions

Actions package reusable functionality.

Examples:

```yaml
- uses: actions/checkout@v4
```

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
```

Actions can:

- download code
- configure runtimes
- authenticate with services
- build artifacts
- publish packages
- interact with APIs
- perform reusable operational tasks

Third-party actions should be treated as software dependencies.

---

## Runners

A runner is the execution environment for a job.

Example:

```yaml
runs-on: ubuntu-latest
```

Common runner operating systems include:

```text
Linux
Windows
macOS
```

For backend engineering, Linux runners are common because they align closely with:

- Docker
- Kubernetes
- AWS
- PostgreSQL
- Redis
- Linux production environments

Runner selection should be driven by job requirements.

---

## GitHub-Hosted Runners

GitHub-hosted runners provide managed execution environments.

Typical advantages:

- no runner maintenance
- clean execution environments
- straightforward scaling
- standardized operating systems
- reduced operational overhead

Typical limitations:

- finite execution resources
- startup overhead
- limited access to private infrastructure
- hosted environment constraints
- platform-specific quotas and usage limits

They are usually appropriate for public or standard CI workloads.

---

## Self-Hosted Runners

Self-hosted runners provide infrastructure managed by the organization.

Useful when workflows require:

- private network access
- specialized hardware
- custom software
- internal services
- controlled network routes
- specialized operating systems

Architecture:

```text
GitHub Actions
      ↓
Self-Hosted Runner
      ↓
Private Network
 ┌────┼─────────┐
 ▼    ▼         ▼
DB   Internal  AWS
     APIs
```

The trade-off is increased operational and security responsibility.

---

## Runner Isolation

A runner executing untrusted code is a security boundary.

This matters especially for:

- pull requests from forks
- public repositories
- untrusted dependencies
- arbitrary shell execution

Persistent self-hosted runners are particularly risky because malicious code may leave behind:

- credentials
- files
- processes
- modified tools
- persistence mechanisms

For untrusted workloads, ephemeral or strongly isolated runners are preferable where practical.

---

## Workflow Environments

Deployment environments commonly represent:

```text
development
staging
production
```

A job can target an environment:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production

    steps:
      - run: ./deploy.sh
```

Environments can provide:

- environment-specific secrets
- environment-specific variables
- deployment protection
- required reviewers
- deployment history
- branch restrictions

---

## Environment Promotion

A controlled deployment architecture is:

```text
Build
  ↓
Immutable Artifact
  ↓
Development
  ↓
Staging
  ↓
Approval
  ↓
Production
```

The same artifact should preferably move through environments.

Avoid:

```text
Build A
  ↓
Staging

Build B
  ↓
Production
```

because the production artifact is then not necessarily the artifact that was tested in staging.

---

## Environment Secrets

Environment secrets allow production credentials to remain scoped to production.

Conceptually:

```text
Repository
│
├── CI Secrets
│
├── Staging Environment
│    └── Staging Secrets
│
└── Production Environment
     └── Production Secrets
```

This is preferable to making every workflow capable of accessing production credentials.

---

## Required Reviewers

Production environments can require human approval before deployment proceeds.

```text
Deployment Job
      ↓
Production Environment
      ↓
Required Reviewer
      ↓
Approved
      ↓
Deployment
```

Approval is a control layer, not a substitute for automated validation.

A strong deployment pipeline is:

```text
Automated Tests
      ↓
Security Checks
      ↓
Immutable Artifact
      ↓
Approval
      ↓
Deployment
      ↓
Health Check
```

---

## Deployment History

Environment-based deployments provide a useful operational history.

A production operator should be able to answer:

```text
What was deployed?
When was it deployed?
Which commit produced it?
Who approved it?
Did the deployment succeed?
What environment received it?
```

Traceability should connect:

```text
Commit
  ↓
Workflow Run
  ↓
Build
  ↓
Artifact / Image Digest
  ↓
Deployment
  ↓
Environment
```

---

## Contexts

Contexts expose runtime information to expressions.

| Context | Typical information |
|---|---|
| `github` | Repository, event, branch, commit, actor |
| `env` | Environment variables |
| `vars` | Repository/organization/environment variables |
| `secrets` | Secrets |
| `steps` | Step outputs |
| `needs` | Dependent job outputs and results |
| `job` | Current job information |
| `runner` | Runner information |
| `matrix` | Current matrix values |
| `strategy` | Matrix strategy information |
| `inputs` | Workflow inputs |

Example:

```yaml
- name: Show execution information
  run: |
    echo "Repository: ${{ github.repository }}"
    echo "Commit: ${{ github.sha }}"
    echo "Event: ${{ github.event_name }}"
```

Never dump sensitive contexts indiscriminately.

---

## Expressions

Expressions use:

```text
${{ ... }}
```

Example:

```yaml
if: ${{ github.ref == 'refs/heads/main' }}
```

They are evaluated by GitHub Actions rather than by the shell.

Conceptually:

```text
Workflow YAML
      ↓
GitHub Expression Evaluation
      ↓
Rendered Step
      ↓
Shell Execution
```

This distinction is critical when debugging conditions and security issues.

---

## Expression Operators

Common operators include:

```text
==
!=
>
>=
<
<=
&&
||
!
```

Example:

```yaml
if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

Conditions should remain readable.

Complex expressions are often easier to maintain when the workflow is decomposed into meaningful jobs or steps.

---

## Expression Functions

Important functions include:

| Function | Purpose |
|---|---|
| `success()` | Checks normal successful execution state |
| `failure()` | Detects preceding failure |
| `always()` | Makes a condition true regardless of normal success/failure state |
| `cancelled()` | Detects cancellation |
| `contains()` | Checks whether a value contains another value |
| `startsWith()` | Checks a prefix |
| `endsWith()` | Checks a suffix |
| `format()` | Formats strings |
| `fromJSON()` | Converts JSON into workflow data |
| `toJSON()` | Converts values into JSON |
| `hashFiles()` | Produces a hash for matching files |

---

## Status Functions

Status functions are particularly important for failure handling.

### `success()`

```yaml
if: success()
```

Useful when an operation should execute only when the required preceding execution succeeded.

### `failure()`

```yaml
if: failure()
```

Useful for diagnostics:

```yaml
- name: Upload logs
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: failure-logs
    path: logs/
```

### `cancelled()`

```yaml
if: cancelled()
```

Useful when cancellation requires specific handling.

### `always()`

```yaml
if: always()
```

This evaluates true regardless of the normal success/failure status.

However, `always()` does not guarantee execution after cancellation. Workflow cancellation can terminate execution before the step is started.

Therefore:

```text
always()
```

does not mean:

```text
Guaranteed execution under every possible condition
```

This distinction matters for cleanup and incident recovery logic.

---

## `continue-on-error`

`continue-on-error` allows an operation to fail without making the surrounding execution fail in the normal way.

Example:

```yaml
- name: Optional compatibility check
  continue-on-error: true
  run: ./compatibility-check.sh
```

Use this only for genuinely non-blocking operations.

Avoid it for:

- security checks
- required tests
- migrations
- production deployments
- health checks

Otherwise, the workflow can report success while an important operation has failed.

---

## Environment Variables

Environment variables can exist at different scopes.

### Workflow Scope

```yaml
env:
  APP_ENV: ci
```

### Job Scope

```yaml
jobs:
  test:
    env:
      APP_ENV: test
```

### Step Scope

```yaml
- name: Run tests
  env:
    APP_ENV: integration
  run: pytest
```

A useful conceptual precedence model is:

```text
Workflow
   ↓
Job
   ↓
Step
```

The narrower scope can override the broader value.

---

## `env` Context vs Shell Environment

GitHub Actions expressions can access:

```yaml
${{ env.APP_ENV }}
```

The shell can access the corresponding environment variable:

```bash
echo "$APP_ENV"
```

These are related but operate at different layers.

Example:

```yaml
env:
  APP_ENV: test

steps:
  - run: echo "${{ env.APP_ENV }}"
  - run: echo "$APP_ENV"
```

Both can reference the same configured value, but one is resolved by GitHub Actions and the other by the shell.

---

## Repository, Organization, and Environment Variables

Non-secret configuration can be managed through variables.

The `vars` context provides configured variables:

```yaml
${{ vars.AWS_REGION }}
```

This is useful for values such as:

```text
AWS_REGION
ECR_REPOSITORY
DEPLOYMENT_ROLE
SERVICE_NAME
```

Secrets should not be stored as ordinary variables.

Environment-specific configuration should remain environment-specific.

---

## Secrets

Secrets are accessed through the `secrets` context.

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
```

Common scopes include:

- repository secrets
- organization secrets
- environment secrets

Prefer the narrowest scope that satisfies the workflow.

---

## Secret Handling

Avoid:

```yaml
- run: echo "${{ secrets.API_TOKEN }}"
```

Avoid placing secrets directly in command arguments when possible.

Prefer environment variables:

```yaml
- name: Call service
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
  run: |
    ./scripts/call-service.sh
```

The script can read:

```bash
"$API_TOKEN"
```

This does not make a secret automatically safe, but it reduces unnecessary exposure.

---

## Secret Masking Limitations

Secret masking is a safety mechanism, not a guarantee that arbitrary sensitive information cannot leak.

Potential leakage paths include:

- command output
- generated files
- artifacts
- process arguments
- debug logs
- transformed or encoded values
- third-party actions

Never intentionally print secrets.

---

## `secrets: inherit`

Reusable workflows can inherit secrets:

```yaml
jobs:
  deploy:
    uses: organization/platform/.github/workflows/deploy.yml@v1
    secrets: inherit
```

This is convenient for organization-wide workflows but expands the reusable workflow's access to caller secrets.

For highly sensitive systems, explicitly defining the required secret interface can provide better governance.

---

## Matrix Strategies

A matrix allows one job definition to run multiple configurations.

```yaml
strategy:
  matrix:
    python:
      - "3.11"
      - "3.12"
      - "3.13"
```

The logical job:

```text
test
```

becomes:

```text
test / Python 3.11
test / Python 3.12
test / Python 3.13
```

---

## Multiple Matrix Dimensions

Multiple dimensions produce combinations.

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

This produces:

```text
3.11 + PostgreSQL
3.11 + MySQL
3.12 + PostgreSQL
3.12 + MySQL
```

The number of executions grows multiplicatively.

```text
2 Python versions
×
2 databases
=
4 jobs
```

Large matrices should therefore be justified by compatibility requirements.

---

## `include`

`include` adds special matrix data or combinations.

```yaml
strategy:
  matrix:
    python:
      - "3.11"
      - "3.12"

    include:
      - python: "3.12"
        experimental: true
```

This is useful when one configuration requires additional metadata.

---

## `exclude`

`exclude` removes combinations.

```yaml
strategy:
  matrix:
    python:
      - "3.11"
      - "3.12"

    database:
      - postgres
      - mysql

    exclude:
      - python: "3.11"
        database: mysql
```

Use it to eliminate unsupported combinations rather than encoding complex conditions throughout the workflow.

---

## `fail-fast`

Matrix execution can stop other matrix work when a failure occurs.

To collect results from all configurations:

```yaml
strategy:
  fail-fast: false
  matrix:
    python:
      - "3.11"
      - "3.12"
      - "3.13"
```

This is useful for compatibility testing.

Example:

```text
Python 3.11 → PASS
Python 3.12 → FAIL
Python 3.13 → PASS
```

Complete results can be more valuable than immediate termination when diagnosing compatibility failures.

---

## `max-parallel`

`max-parallel` limits simultaneous matrix execution.

```yaml
strategy:
  max-parallel: 2
  matrix:
    python:
      - "3.11"
      - "3.12"
      - "3.13"
      - "3.14"
```

This can protect:

- runner capacity
- external APIs
- databases
- CI budgets
- rate-limited services

---

## Matrix and `needs`

A matrix job can depend on a preparation job.

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest

    steps:
      - run: echo "prepare"

  test:
    needs: prepare

    strategy:
      matrix:
        python:
          - "3.11"
          - "3.12"

    runs-on: ubuntu-latest

    steps:
      - run: python --version
```

Execution:

```text
        prepare
           │
     ┌─────┴─────┐
     ▼           ▼
  Python 3.11  Python 3.12
```

---

## Dynamic Matrices

A dynamic matrix can be generated at runtime.

```yaml
jobs:
  generate:
    runs-on: ubuntu-latest

    outputs:
      matrix: ${{ steps.generate.outputs.matrix }}

    steps:
      - id: generate
        run: |
          echo 'matrix={"python":["3.11","3.12","3.13"]}' >> "$GITHUB_OUTPUT"

  test:
    needs: generate

    runs-on: ubuntu-latest

    strategy:
      matrix: ${{ fromJSON(needs.generate.outputs.matrix) }}

    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}

      - run: pytest
```

The data flow is:

```text
Generate Configuration
        ↓
$GITHUB_OUTPUT
        ↓
Job Output
        ↓
needs.generate.outputs
        ↓
fromJSON()
        ↓
Matrix
```

This is useful for monorepos and dynamically discovered test targets.

---

## Step Outputs

Step outputs communicate values between steps.

```yaml
- name: Determine version
  id: version
  run: |
    VERSION="1.4.0"
    echo "version=$VERSION" >> "$GITHUB_OUTPUT"
```

Consume it:

```yaml
- name: Use version
  run: echo "${{ steps.version.outputs.version }}"
```

The important boundary is:

```text
Step
 ↓
$GITHUB_OUTPUT
 ↓
steps.<id>.outputs
```

---

## Job Outputs

A job can expose outputs to dependent jobs.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      image: ${{ steps.meta.outputs.image }}

    steps:
      - id: meta
        run: |
          echo "image=backend:${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

Consume it:

```yaml
jobs:
  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - run: echo "Deploying ${{ needs.build.outputs.image }}"
```

Data flow:

```text
Build Step
    ↓
Step Output
    ↓
Job Output
    ↓
needs.build.outputs
    ↓
Deploy Job
```

---

## `$GITHUB_ENV`

`GITHUB_ENV` transfers environment variables to later steps in the same job.

```yaml
- name: Set version
  run: echo "APP_VERSION=1.4.0" >> "$GITHUB_ENV"

- name: Use version
  run: echo "$APP_VERSION"
```

It does not provide a general cross-job communication mechanism.

For cross-job values use:

- job outputs
- artifacts
- external storage
- registries

depending on the type and lifetime of the data.

---

## `$GITHUB_OUTPUT`

`GITHUB_OUTPUT` is the supported mechanism for setting step outputs.

```yaml
- id: version
  run: echo "version=1.4.0" >> "$GITHUB_OUTPUT"
```

Consume:

```yaml
${{ steps.version.outputs.version }}
```

For structured values, JSON can be emitted and later parsed with `fromJSON()`.

---

## `$GITHUB_PATH`

`GITHUB_PATH` modifies the `PATH` for subsequent steps.

```yaml
- name: Add local tools
  run: echo "$HOME/.local/bin" >> "$GITHUB_PATH"
```

Later steps can resolve executables from the added directory.

---

## Step Summaries

A workflow can publish human-readable results using `GITHUB_STEP_SUMMARY`.

```yaml
- name: Publish test summary
  run: |
    {
      echo "## Test Results"
      echo ""
      echo "- Total: 248"
      echo "- Passed: 248"
      echo "- Failed: 0"
    } >> "$GITHUB_STEP_SUMMARY"
```

Useful summary information includes:

- test counts
- deployment version
- environment
- image digest
- security findings
- links to artifacts

---

## Annotations and Logging Commands

Workflow logging commands can create annotations:

```bash
echo "::warning file=app.py,line=42::Deprecated configuration"
```

Or notices:

```bash
echo "::notice::Deployment started"
```

These can surface important information directly in workflow results.

Use logging commands deliberately.

Avoid turning logs into an unstructured stream of redundant messages.

---

## Artifacts

Artifacts are workflow outputs that need to survive the individual job execution environment.

Examples:

- coverage reports
- test reports
- packaged applications
- logs
- debugging files
- release bundles

Upload:

```yaml
- name: Upload coverage
  uses: actions/upload-artifact@v4
  with:
    name: coverage
    path: coverage.xml
```

Download:

```yaml
- name: Download coverage
  uses: actions/download-artifact@v4
  with:
    name: coverage
```

Architecture:

```text
Job A
  ↓
Upload Artifact
  ↓
Artifact Storage
  ↓
Download Artifact
  ↓
Job B
```

---

## Artifact Paths

The path must match files actually produced by the workflow.

Example:

```yaml
- name: Inspect generated files
  run: |
    pwd
    find . -maxdepth 4 -type f | sort

- name: Upload reports
  uses: actions/upload-artifact@v4
  with:
    name: reports
    path: |
      reports/
      coverage.xml
```

A frequent failure is assuming that a file exists because a command was expected to generate it.

Verify the filesystem before uploading.

---

## Artifact Retention

Retention should reflect operational requirements.

```yaml
- name: Upload test report
  uses: actions/upload-artifact@v4
  with:
    name: test-report
    path: reports/
    retention-days: 14
```

Short-lived CI reports generally do not require the same retention policy as release artifacts.

Artifact storage also has repository and organization constraints, so retention should be part of cost management.

---

## Artifacts vs Caches

These concepts have different semantics.

| Artifact | Cache |
|---|---|
| Workflow output | Performance optimization |
| Intended for retrieval | Intended for reuse |
| Test report | Dependency cache |
| Build package | Package manager cache |
| Release data | Docker build cache |
| Can be part of delivery | Must not define correctness |
| Missing artifact can be a failure | Cache miss is normally acceptable |

A deployment should never depend on a cache being available.

---

## Dependency Caching

Python dependencies can be cached through `setup-python`.

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: pip
    cache-dependency-path: requirements.txt
```

The cache should reflect dependency state.

Conceptually:

```text
requirements.txt
      ↓
Dependency Hash
      ↓
Cache Key
      ↓
Cache Hit / Miss
```

---

## Cache Keys

A robust cache key commonly includes relevant dimensions such as:

```text
Operating System
Runtime Version
Dependency Definition
```

For example:

```yaml
key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

For Python projects using multiple versions, runtime version should be considered when the cached data is runtime-sensitive.

---

## `hashFiles()`

`hashFiles()` calculates a hash from matching files.

```yaml
${{ hashFiles('**/requirements.txt') }}
```

Common dependency files include:

```text
requirements.txt
poetry.lock
uv.lock
package-lock.json
pnpm-lock.yaml
yarn.lock
```

Changing the dependency definition can therefore invalidate the cache.

---

## Restore Keys

Restore keys provide fallback matching.

```yaml
key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

restore-keys: |
  ${{ runner.os }}-pip-
```

The exact dependency cache should be preferred.

A broader cache can be useful as a fallback, but correctness must not depend on it.

---

## Docker Build Cache

Docker Buildx can use GitHub Actions cache storage.

```yaml
- name: Build Docker image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: false
    tags: backend:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

Caching can significantly reduce repeated Docker build time.

The cache remains an optimization:

```text
Cache Hit  → Faster Build
Cache Miss → Correct Build Should Still Work
```

---

## Workflow Concurrency

Concurrency prevents conflicting executions from operating on the same logical resource simultaneously.

For production:

```yaml
concurrency:
  group: production-deployment
  cancel-in-progress: false
```

Architecture:

```text
Deployment A ───────────────► Production
                                  │
Deployment B ── waits ────────────┘
```

This prevents deployment races such as:

```text
Deployment A starts
Deployment B starts
A modifies production
B modifies production
A completes
B completes
```

The final state may then depend on timing rather than intended ordering.

---

## Pull Request Concurrency

For CI validation, older runs are often unnecessary after a new commit.

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Example:

```text
Commit A → CI running
Commit B → New CI starts
          ↓
       Commit A CI cancelled
```

This saves runner capacity and reduces stale feedback.

---

## Production Deployment Concurrency

Production deployments normally use:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Do not automatically cancel an active production deployment merely because another deployment was queued.

The appropriate policy depends on the deployment system and rollback model.

The important point is that concurrency should reflect the protected resource.

---

## Workflow-Level vs Job-Level Concurrency

Workflow-level:

```yaml
concurrency:
  group: production
```

Job-level:

```yaml
jobs:
  deploy:
    concurrency:
      group: production
```

Use the narrowest scope that protects the actual resource.

For example, there may be no reason to serialize:

```text
Lint
Unit Tests
Security Scan
```

when only:

```text
Production Deployment
```

requires serialization.

---

## Reusable Workflows

Reusable workflows use `workflow_call`.

Example:

```yaml
name: Python CI

on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}

      - run: python -m pip install -r requirements.txt
      - run: pytest
```

Caller:

```yaml
jobs:
  ci:
    uses: organization/platform-workflows/.github/workflows/python-ci.yml@v1
    with:
      python-version: "3.12"
```

---

## Reusable Workflow Inputs

Inputs define the workflow's contract.

```yaml
on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string

      run-integration-tests:
        required: false
        type: boolean
        default: true
```

Consume them:

```yaml
if: inputs.run-integration-tests
```

Explicit contracts make reusable workflows easier to govern.

---

## Reusable Workflow Outputs

Reusable workflows can expose outputs.

```yaml
on:
  workflow_call:
    outputs:
      image:
        description: Built image reference
        value: ${{ jobs.build.outputs.image }}
```

The caller can consume the output:

```yaml
jobs:
  build:
    uses: organization/platform/.github/workflows/build.yml@v1

  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - run: echo "${{ needs.build.outputs.image }}"
```

This enables reusable workflow composition.

---

## Reusable Workflows Across Repositories

An organization can centralize common workflows:

```text
platform-workflows
│
├── python-ci.yml
├── docker-build.yml
├── security-scan.yml
└── aws-deploy.yml
```

Application repositories then consume them:

```text
users-service ────────┐
payments-service ─────┼──► platform-workflows
orders-service ───────┘
```

Advantages:

- reduced duplication
- centralized standards
- consistent security controls
- easier platform governance

Trade-off:

> A shared workflow becomes a dependency for every repository that consumes it.

Therefore, version reusable workflows deliberately.

---

## Reusable Workflow Versioning

Example:

```yaml
uses: organization/platform-workflows/.github/workflows/python-ci.yml@v1
```

Versioned references can allow:

```text
v1 → Existing repositories
v2 → New architecture
```

Security-sensitive references may use immutable commit SHAs rather than mutable tags.

---

## Reusable Workflow vs Composite Action

These are different abstractions.

### Reusable Workflow

```text
Reusable Workflow
      │
      ├── Job
      │    ├── Step
      │    └── Step
      │
      └── Job
           └── Step
```

It can orchestrate multiple jobs.

### Composite Action

```text
Composite Action
      │
      ├── Step
      ├── Step
      └── Step
```

It packages reusable steps within a job.

Use:

| Requirement | Prefer |
|---|---|
| Multi-job CI pipeline | Reusable workflow |
| Multi-stage deployment | Reusable workflow |
| Standardized step sequence | Composite action |
| Reusable setup logic | Composite action |
| Organization-wide job graph | Reusable workflow |

---

## Workflow Limitations and Constraints

GitHub Actions workflows operate within platform constraints.

Important categories include:

- maximum execution time
- concurrent job limits
- repository and organization concurrency
- artifact storage
- cache storage and eviction
- log retention
- API rate limits
- runner resource limits
- matrix size
- workflow command/output size
- scheduled workflow availability
- hosted runner capacity

The exact limits depend on the GitHub plan, repository configuration, runner type, and feature.

The engineering implication is more important than memorizing individual numbers:

> A workflow must be designed within finite compute, storage, concurrency, and execution boundaries.

---

## Workflow Quotas and Capacity Planning

Large repositories can encounter resource pressure from:

```text
Large Matrix
    ×
Frequent Commits
    ×
Multiple Branches
    ×
Long-Running Tests
```

For example:

```text
20 matrix combinations
×
10 commits/day
=
200 job executions/day
```

If each job also starts multiple service containers, the infrastructure demand increases further.

Manage this through:

- matrix design
- path filters
- concurrency
- caching
- parallelism
- selective integration tests
- reusable workflows
- runner capacity planning

---

## Scheduled Workflow Constraints

Scheduled automation should not be treated as an exact distributed scheduler.

A scheduled workflow may be delayed under platform load or other operational conditions.

Therefore, avoid designs that require:

```text
Cron at exactly 02:00:00
```

for correctness-critical operations.

For strict timing requirements, use an appropriate scheduling platform and invoke GitHub Actions only when GitHub Actions is the right execution boundary.

---

## Matrix Scaling Constraints

A matrix can grow rapidly.

For example:

```text
4 Python versions
×
3 operating systems
×
2 databases
=
24 executions
```

Add another dimension:

```text
24
×
2 architectures
=
48 executions
```

Before adding a matrix dimension, ask:

- Is the combination supported?
- Does it represent a real compatibility requirement?
- Can the tests be reduced?
- Should some combinations be nightly rather than per PR?
- Should `max-parallel` be limited?

---

## Workflow Design for Python Backend Systems

A practical Python CI workflow can be structured as:

```yaml
name: Python CI

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

      - run: python -m pip install ruff
      - run: ruff check .

  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: python -m pip install -r requirements.txt
      - run: pytest

  build:
    needs:
      - lint
      - test

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t backend:${{ github.sha }} .
```

Dependency graph:

```text
       ┌── Lint ──┐
       │          │
PR ────┤          ├──► Build
       │          │
       └── Test ──┘
```

---

## Django with PostgreSQL

Django integration tests can use a PostgreSQL service container.

```yaml
jobs:
  test:
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
          --health-cmd="pg_isready -U django -d django_test"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: python -m pip install -r requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: postgresql://django:django@localhost:5432/django_test
        run: python manage.py migrate

      - name: Run tests
        env:
          DATABASE_URL: postgresql://django:django@localhost:5432/django_test
        run: pytest
```

The database's health check matters because:

```text
Container Started
```

does not necessarily mean:

```text
Database Ready
```

---

## FastAPI with PostgreSQL and Redis

A FastAPI integration-test job can use both services:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: app
          POSTGRES_DB: app_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U app -d app_test"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: python -m pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://app:app@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: pytest --cov=. --cov-report=xml
```

Architecture:

```text
                 GitHub Actions
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
           FastAPI PostgreSQL Redis
              │        │        │
              └────────┼────────┘
                       ▼
                     pytest
                       │
                       ▼
                  coverage.xml
                       │
                       ▼
                    Artifact
```

---

## Containerized Jobs

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
      - run: pip install -r requirements.txt
      - run: pytest
```

This provides a more controlled runtime environment.

It is useful when:

- the application requires a specific Linux environment
- local development already uses a container
- runtime consistency is important

---

## Container Networking

When jobs and service containers use containerized execution, networking behavior differs from simply running services on the host.

Design the connection model explicitly:

```text
Application Container
       │
       ├── PostgreSQL Service
       │
       └── Redis Service
```

Do not blindly copy local Docker Compose hostnames into every GitHub Actions configuration.

The correct hostname and port depend on whether the application itself is running:

- directly on the runner
- inside a job container
- inside another container

---

## Testing Pipeline

A production Python testing workflow can be:

```text
Python Application
       │
       ├── PostgreSQL
       │
       ├── Redis
       │
       ▼
     pytest
       │
       ├── Unit Tests
       ├── API Tests
       ├── Integration Tests
       └── Database Tests
       │
       ▼
   Coverage Report
       │
       ▼
     Artifact
```

This is substantially closer to production behavior than testing only isolated functions.

---

## Unit vs Integration vs End-to-End Tests

| Test type | Purpose | Typical workflow location |
|---|---|---|
| Unit | Validate isolated logic | Every PR |
| API | Validate HTTP behavior | Every PR |
| Integration | Validate service/database interactions | PR / main |
| End-to-end | Validate complete system paths | Main / scheduled |
| Smoke | Validate deployment health | After deployment |

Do not make every workflow run a complete production-scale end-to-end suite if that creates excessive latency and cost.

---

## Workflow Security

Workflow files should be treated as privileged infrastructure code.

A workflow may access:

```text
Repository
Secrets
Cloud Credentials
Package Registries
Deployment Systems
Private Networks
```

Therefore, every permission should have a reason.

---

## `GITHUB_TOKEN`

GitHub provides a workflow token for repository operations.

Permissions should be explicitly minimized.

Example:

```yaml
permissions:
  contents: read
```

For AWS OIDC:

```yaml
permissions:
  contents: read
  id-token: write
```

Do not grant broad write permissions when read access is sufficient.

---

## Job-Level Permissions

Permissions can be scoped to individual jobs.

```yaml
jobs:
  test:
    permissions:
      contents: read

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
```

A deployment job may require:

```yaml
permissions:
  contents: read
  id-token: write
```

This limits privilege to the job that actually requires it.

---

## Untrusted GitHub Data

Values such as:

- pull request titles
- branch names
- commit messages
- issue content
- workflow inputs

may contain attacker-controlled content.

Avoid directly embedding them into shell syntax.

Risky pattern:

```yaml
- run: echo "PR title: ${{ github.event.pull_request.title }}"
```

Prefer a data boundary:

```yaml
- name: Print PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: |
    printf '%s\n' "$PR_TITLE"
```

The shell receives the value as data rather than interpolated shell syntax.

---

## Third-Party Actions

An action executes code inside the workflow environment.

Therefore:

```yaml
uses: some-org/some-action@v1
```

is effectively a software dependency.

Risks include:

- compromised upstream repository
- malicious releases
- dependency compromise
- excessive token permissions
- access to secrets
- supply-chain attacks

Prefer trusted sources and controlled versioning.

For higher-assurance workflows, immutable commit SHA pinning can provide stronger protection against mutable tag changes.

---

## Workflow Governance

Organizations can govern Actions through:

- approved actions
- action allowlists
- reusable workflows
- permission standards
- runner policies
- environment protection
- repository policies
- enterprise policies

A platform team can provide:

```text
Approved Python CI
Approved Docker Build
Approved Security Scan
Approved AWS Deployment
```

This reduces inconsistent security practices across repositories.

---

## Workflow Architecture

A production architecture can separate concerns:

```text
                 GitHub Repository
                        │
                        ▼
                  CI Workflow
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
        Lint          Tests        Security
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                      Build
                        │
                        ▼
                Immutable Artifact
                        │
                        ▼
                     Staging
                        │
                        ▼
                    Approval
                        │
                        ▼
                   Production
                        │
                        ▼
                  Health Check
                        │
                  ┌─────┴─────┐
                  ▼           ▼
               Healthy      Failed
                  │           │
                  ▼           ▼
               Complete    Rollback
```

This architecture makes the delivery lifecycle explicit.

---

## Build Once, Promote Many

A mature deployment system should preferably use:

```text
Source
  ↓
Build
  ↓
Immutable Artifact
  ↓
Staging
  ↓
Production
```

For Docker:

```text
Source
  ↓
Docker Build
  ↓
Image Digest
  ↓
ECR
  ↓
Staging
  ↓
Production
```

The same image digest is promoted.

This improves:

- reproducibility
- traceability
- rollback
- auditability
- confidence that production received what was tested

---

## Docker Image References

Avoid relying exclusively on:

```text
latest
```

Prefer immutable references such as:

```text
backend:<commit-sha>
```

or:

```text
backend@sha256:<digest>
```

A semantic version can still be useful:

```text
backend:1.4.0
```

but the digest provides stronger immutability.

---

## AWS OIDC Workflow

A production AWS deployment should preferably avoid long-lived AWS credentials stored in GitHub.

Architecture:

```text
GitHub Actions
      │
      ▼
GitHub OIDC Token
      │
      ▼
AWS IAM Trust Policy
      │
      ▼
AWS STS
      │
      ▼
Temporary Credentials
      │
      ▼
AWS Service
```

A workflow can request the required permission:

```yaml
permissions:
  contents: read
  id-token: write
```

Then:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ vars.AWS_DEPLOY_ROLE }}
    aws-region: ${{ vars.AWS_REGION }}
```

The IAM trust policy should restrict which repository, branch, tag, or environment can assume the role.

---

## Docker and ECR Workflow

A production image workflow may look like:

```text
Pull Request
     ↓
Tests
     ↓
Docker Build
     ↓
Security Scan
     ↓
ECR
     ↓
Image Digest
     ↓
Staging
     ↓
Production
```

Relevant AWS services can include:

```text
IAM
STS
ECR
ECS
EC2
Lambda
S3
CloudFormation
```

The exact deployment architecture depends on the runtime platform.

---

## Deployment Strategies

GitHub Actions orchestrates deployments; the deployment platform determines how application instances receive the new version.

Common strategies include:

| Strategy | Characteristics |
|---|---|
| Rolling | Gradually replaces instances |
| Blue/Green | Maintains old and new environments |
| Canary | Sends limited traffic to new version |
| Recreate | Stops old version before starting new version |

For production systems, strategy selection should consider:

- traffic patterns
- rollback requirements
- database compatibility
- infrastructure cost
- deployment duration
- health-check quality

---

## Zero-Downtime Deployment

A zero-downtime deployment requires more than a GitHub Actions workflow.

The runtime architecture must support:

```text
Old Version
     │
     ├── Serving Traffic
     │
New Version
     │
     ├── Healthy
     │
     ▼
Traffic Shift
     │
     ▼
Old Version Removed
```

For example:

```text
Load Balancer
      │
 ┌────┴────┐
 ▼         ▼
v1        v2
 │         │
 │      Health Check
 │         │
 └────┬────┘
      ▼
Traffic Shift
```

Application startup, health checks, database compatibility, and graceful shutdown all matter.

---

## Rollback

A deployment workflow should define rollback before deployment starts.

For immutable Docker images:

```text
Production
    ↓
Current Digest
    ↓
Deployment Failure
    ↓
Previous Known-Good Digest
    ↓
Redeploy
```

Rollback should preferably reference a known artifact rather than rebuilding an old commit during an incident.

---

## Release Workflows

A release workflow can connect Git tags to deployment artifacts.

```text
Git Commit
    ↓
Tag v1.4.0
    ↓
Release Workflow
    ↓
Build
    ↓
Test
    ↓
Package
    ↓
Publish
```

Typical release components include:

- semantic version
- changelog
- release notes
- release artifacts
- container image
- GitHub Release
- pre-release classification

---

## Runner Operations

Runner operations include:

- runner registration
- runner labels
- runner groups
- operating system management
- software installation
- network access
- security patching
- capacity planning
- monitoring
- autoscaling

A self-hosted runner should be treated as production infrastructure.

---

## Runner Labels

Labels allow jobs to target specialized runners.

Conceptually:

```yaml
runs-on:
  - self-hosted
  - linux
  - private-network
```

A label should represent a meaningful execution requirement.

Examples:

```text
linux
windows
docker
gpu
private-network
```

Avoid arbitrary labels that make scheduling difficult to understand.

---

## Persistent vs Ephemeral Runners

Persistent runner:

```text
Runner
  ↓
Job A
  ↓
Job B
  ↓
Job C
```

Ephemeral runner:

```text
Runner
  ↓
One Job
  ↓
Destroyed
```

Persistent runners are simpler but create greater contamination and persistence risks.

Ephemeral runners improve isolation but require more infrastructure automation.

---

## Self-Hosted Runner Security

A self-hosted runner that executes untrusted code can become a path into the private network.

Potential impact:

```text
Malicious PR
    ↓
Self-Hosted Runner
    ↓
Private Network
    ├── Internal APIs
    ├── Databases
    └── Cloud Resources
```

Do not place untrusted public pull request workloads on privileged persistent runners.

---

## Workflow Cost Optimization

Cost is influenced by:

```text
Number of Jobs
×
Execution Duration
×
Runner Cost
```

Optimize using:

- path filters
- dependency caching
- Docker caching
- parallel execution
- matrix reduction
- scheduled heavy tests
- appropriate runner sizes
- concurrency cancellation
- avoiding redundant builds

Do not optimize away tests that provide important production confidence.

---

## Workflow Observability

A production workflow should make important state visible.

Useful information includes:

```text
Commit SHA
Version
Environment
Artifact
Image Digest
Deployment Time
Test Results
Security Results
Deployment Result
```

Step summaries can provide concise operational information without forcing engineers to inspect every log line.

---

## Workflow Debugging

A useful troubleshooting hierarchy is:

```text
Workflow
   ↓
Trigger
   ↓
Job
   ↓
Runner
   ↓
Step
   ↓
Action / Command
   ↓
External Dependency
```

Always identify the failed layer before changing configuration.

---

## Trigger Troubleshooting

### Symptom

Workflow did not run.

### Possible Causes

- wrong event
- wrong branch
- wrong path
- wrong tag
- workflow disabled
- workflow file not present on the relevant branch

### Isolation

Check:

```text
Event
 ↓
Branch
 ↓
Path
 ↓
Tag
 ↓
Workflow Configuration
```

### Prevention

Keep trigger configuration explicit and test important filters with representative changes.

---

## Job Troubleshooting

### Symptom

Workflow starts but job is skipped.

### Possible Causes

- `if`
- failed `needs`
- matrix configuration
- environment protection
- concurrency behavior

### Isolation

Inspect the dependency graph and job condition before inspecting application commands.

---

## Step Troubleshooting

### Symptom

Job starts but a step fails.

### Possible Causes

- command failure
- missing dependency
- wrong working directory
- missing environment variable
- permission problem
- action failure

### Isolation

Run the exact command locally where possible and inspect:

```text
Working Directory
Environment
Input Files
Tool Versions
Permissions
```

---

## Expression Troubleshooting

Common causes:

```text
Wrong context
Wrong property
Incorrect comparison
Unexpected type
JSON parsing failure
```

Safe debugging:

```yaml
- name: Debug execution context
  run: |
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
    echo "SHA: ${{ github.sha }}"
```

Never print secret values.

---

## Artifact Troubleshooting

Use:

```text
Was the file generated?
        ↓
Does the path exist?
        ↓
Did upload execute?
        ↓
Was the correct run inspected?
        ↓
Was retention sufficient?
```

Filesystem inspection:

```bash
find . -maxdepth 4 -type f | sort
```

---

## Cache Troubleshooting

First distinguish:

```text
Cache Miss
```

from:

```text
Cache Configuration Failure
```

A cache miss is normal.

Check:

- key
- dependency hash
- cache path
- OS
- runtime version
- dependency lockfile

The pipeline must remain correct without the cache.

---

## Service Container Troubleshooting

Typical symptoms:

```text
Connection refused
Authentication failed
Database unavailable
Redis unavailable
```

Check:

```text
Container started
      ↓
Container healthy
      ↓
Correct hostname
      ↓
Correct port
      ↓
Credentials
      ↓
Application configuration
```

A running container is not necessarily a ready service.

---

## AWS OIDC Troubleshooting

OIDC failures should be isolated through the complete authentication path:

```text
GitHub Permission
      ↓
OIDC Token
      ↓
IAM Trust Policy
      ↓
STS AssumeRole
      ↓
IAM Permission
      ↓
AWS API
```

If `AssumeRole` fails, changing ECR permissions may not solve the problem.

The failure may instead be in the IAM trust relationship.

---

## Docker Troubleshooting

Separate the Docker failure domains:

```text
Runner
  ↓
Docker / Buildx
  ↓
Dockerfile
  ↓
Base Image
  ↓
Dependencies
  ↓
Build Context
  ↓
Registry Authentication
  ↓
Registry Push
```

This prevents modifying application code when the actual failure is registry authentication.

---

## GitHub CLI for Workflow Operations

GitHub CLI is useful for operational Actions management.

List workflows:

```bash
gh workflow list
```

Run a workflow:

```bash
gh workflow run ci.yml
```

List workflow runs:

```bash
gh run list
```

Inspect a run:

```bash
gh run view <run-id>
```

Inspect logs:

```bash
gh run view <run-id> --log
```

Rerun a workflow:

```bash
gh run rerun <run-id>
```

List artifacts from a run:

```bash
gh run view <run-id> --json artifacts
```

Download artifacts:

```bash
gh run download <run-id>
```

List repository secrets:

```bash
gh secret list
```

List repository variables:

```bash
gh variable list
```

List environments:

```bash
gh api repos/{owner}/{repo}/environments
```

The CLI is particularly useful for incident response and operational automation.

---

## Production CI/CD Workflow

A mature backend pipeline can be represented as:

```mermaid
flowchart TD
    A[Pull Request] --> B[CI]

    B --> C[Lint]
    B --> D[Unit Tests]
    B --> E[Integration Tests]
    B --> F[Security Scan]
    B --> G[Matrix Tests]

    E --> H[(PostgreSQL)]
    E --> I[(Redis)]

    C --> J[Build]
    D --> J
    E --> J
    F --> J
    G --> J

    J --> K[Docker Build]
    K --> L[Image Scan]
    L --> M[ECR]

    M --> N[Immutable Image Digest]
    N --> O[Staging]

    O --> P[Health Validation]
    P --> Q[Production Approval]

    Q --> R[Production]
    R --> S[Health Validation]

    S --> T{Healthy?}
    T -->|Yes| U[Complete]
    T -->|No| V[Rollback]
    V --> N
```

The important boundaries are:

```text
Validation
   ↓
Build
   ↓
Artifact
   ↓
Promotion
   ↓
Deployment
   ↓
Validation
   ↓
Recovery
```

---

## Production Workflow Example

A controlled production workflow might look like:

```yaml
name: Production Deployment

on:
  workflow_dispatch:
    inputs:
      image:
        description: Immutable image reference
        required: true
        type: string

permissions:
  contents: read
  id-token: write

concurrency:
  group: production-deployment
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest

    environment:
      name: production

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Deploy
        env:
          IMAGE: ${{ inputs.image }}
        run: |
          ./scripts/deploy.sh "$IMAGE"

      - name: Validate deployment
        run: ./scripts/health-check.sh
```

Important controls include:

- manual invocation
- restricted permissions
- OIDC
- production environment
- deployment concurrency
- immutable image reference
- health validation

---

## Failure Domains

A mature workflow should isolate failure domains.

```text
Source
  ↓
Workflow Configuration
  ↓
Runner
  ↓
Dependencies
  ↓
Build
  ↓
Artifact
  ↓
Registry
  ↓
Deployment
  ↓
Runtime
```

A failure in one layer should be diagnosable without treating the entire pipeline as one opaque system.

---

## Common Workflow Mistakes

### Assuming Jobs Share Files

Incorrect:

```text
Job A creates build.zip
        ↓
Job B expects build.zip
```

Jobs run in separate execution environments.

Correct:

```text
Job A
  ↓
Artifact
  ↓
Job B
```

---

### Serializing Independent Jobs

Avoid:

```text
Lint
 ↓
Unit Tests
 ↓
Security
 ↓
Integration
 ↓
Build
```

when those checks do not depend on one another.

Prefer:

```text
        ┌── Lint ──────────┐
        ├── Unit Tests ────┤
Start ──┼── Security ──────┼──► Build
        └── Integration ───┘
```

---

### Using Cache as Artifact Storage

Caches are optimizations.

Release artifacts should use:

- artifacts
- container registries
- package registries
- release storage

depending on the delivery architecture.

---

### Using `latest` as the Deployment Identity

Avoid making:

```text
latest
```

the only reference to a production image.

Use:

```text
commit SHA
```

or preferably:

```text
image digest
```

for deployment identity.

---

### Overusing `always()`

This:

```yaml
if: always()
```

should not be added to every cleanup or diagnostic step without understanding cancellation semantics.

It can also make workflows harder to reason about.

---

### Overusing `continue-on-error`

If required tests use:

```yaml
continue-on-error: true
```

the workflow may become green while the application is broken.

Use it only when failure is genuinely non-blocking.

---

### Hardcoding Credentials

Never put credentials directly in workflow YAML.

Bad:

```yaml
env:
  AWS_SECRET_ACCESS_KEY: "secret"
```

Prefer:

```text
OIDC
```

for AWS where supported, or tightly scoped GitHub secrets when a secret is actually required.

---

### Rebuilding for Every Environment

Avoid:

```text
Build
 ↓
Staging

Build Again
 ↓
Production
```

Prefer:

```text
Build Once
 ↓
Immutable Artifact
 ↓
Staging
 ↓
Production
```

---

## Interview-Level Workflow Questions

### How would you design CI for a Python backend?

A strong answer should discuss:

```text
Pull Request
   ↓
Lint
   ↓
Unit Tests
   ↓
Integration Tests
   ↓
Security
   ↓
Matrix
   ↓
Build
```

and explain which stages can run in parallel.

---

### How would you prevent two production deployments from running simultaneously?

Use a deployment-specific concurrency group:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Then explain why production deployment is a shared mutable resource.

---

### How would you test multiple Python versions?

Use a matrix:

```yaml
strategy:
  matrix:
    python:
      - "3.11"
      - "3.12"
      - "3.13"
```

Then consider:

- supported versions
- `fail-fast`
- `max-parallel`
- dependency compatibility
- test duration

---

### How would you test Django against PostgreSQL and Redis?

Use service containers:

```text
Django
  │
  ├── PostgreSQL
  └── Redis
        ↓
      pytest
```

Include readiness checks and environment-specific connection configuration.

---

### How would you avoid long-lived AWS credentials?

Use:

```text
GitHub OIDC
   ↓
AWS IAM
   ↓
STS
   ↓
Temporary Credentials
```

Then restrict the IAM trust policy to the intended repository and deployment boundary.

---

### How would you share CI logic across repositories?

Use a reusable workflow:

```text
Repository A ──┐
Repository B ──┼──► Reusable CI Workflow
Repository C ──┘
```

Version the shared workflow so changes can be adopted deliberately.

---

### When would you use a composite action instead?

Use a composite action when the reusable unit is a collection of steps within a single job.

Example:

```text
Setup Python
 ↓
Install Dependencies
 ↓
Configure Tools
```

If multiple jobs need orchestration, prefer a reusable workflow.

---

### How would you prevent a compromised third-party action from gaining excessive access?

Discuss:

- least-privilege `GITHUB_TOKEN`
- job-level permissions
- trusted action sources
- version/SHA pinning
- dependency review
- action governance
- avoiding unnecessary secrets
- isolated runners
- protected environments

The important engineering principle is:

> A workflow action should receive only the privileges required for its task.

---

### How would you promote a Docker image from staging to production without rebuilding?

Build once:

```text
Source
 ↓
Docker Build
 ↓
ECR
 ↓
Image Digest
 ↓
Staging
 ↓
Approval
 ↓
Same Image Digest
 ↓
Production
```

This prevents staging and production from receiving different builds.

---

### How would you design rollback?

Use a known-good immutable artifact:

```text
Production
   ↓
Failure
   ↓
Previous Image Digest
   ↓
Redeploy
   ↓
Health Check
```

Do not depend on rebuilding the old commit during the incident.

---

### How would you handle a self-hosted runner requiring private network access?

Discuss:

```text
Private Network
      ↓
Self-Hosted Runner
      ↓
Runner Isolation
      ↓
GitHub Actions
```

Then address:

- runner groups
- labels
- network controls
- credential exposure
- ephemeral runners
- untrusted code
- patching
- monitoring
- autoscaling

The security boundary matters as much as connectivity.

---

## Workflow Design Checklist

### Triggering

- [ ] Correct event is configured.
- [ ] Branch filters are intentional.
- [ ] Path filters are intentional.
- [ ] Tag filters are appropriate.
- [ ] Manual inputs are explicit.
- [ ] Privileged workflows cannot unexpectedly execute untrusted code.

### Job Design

- [ ] Jobs represent meaningful execution boundaries.
- [ ] `needs` represents real dependencies.
- [ ] Independent work runs in parallel.
- [ ] Matrix size is controlled.
- [ ] `max-parallel` is considered.
- [ ] `continue-on-error` is used only for non-blocking work.

### Data Flow

- [ ] Step outputs use `$GITHUB_OUTPUT`.
- [ ] Environment variables use `$GITHUB_ENV` where appropriate.
- [ ] Cross-job data uses outputs or artifacts.
- [ ] Artifacts are not confused with caches.
- [ ] Dynamic matrices use structured outputs when required.

### Security

- [ ] `GITHUB_TOKEN` permissions are minimized.
- [ ] Secrets are not printed.
- [ ] Untrusted GitHub data is safely handled.
- [ ] `pull_request_target` is used only with an explicit trust model.
- [ ] Third-party actions are reviewed.
- [ ] Sensitive actions use appropriate version pinning.
- [ ] AWS authentication uses OIDC where appropriate.

### Deployment

- [ ] Environments are clearly separated.
- [ ] Production has appropriate protection.
- [ ] Deployment concurrency is configured.
- [ ] Immutable artifacts are promoted.
- [ ] Health validation runs after deployment.
- [ ] Rollback is defined.
- [ ] Deployment identity is traceable to a commit and artifact.

### Operations

- [ ] Workflow logs are useful.
- [ ] Failure artifacts are available.
- [ ] Step summaries provide important operational information.
- [ ] Artifact retention is intentional.
- [ ] Cache behavior is understood.
- [ ] Runner capacity is appropriate.
- [ ] Workflow limits are considered.
- [ ] Workflow ownership is clear.

## Key Takeaways

- **A GitHub Actions workflow is an executable dependency graph in which triggers start workflows, jobs define execution boundaries, steps perform operations, actions provide reusable functionality, and runners execute jobs.**
- **Production workflow design depends on explicit triggers, dependencies, conditions, contexts, outputs, artifacts, concurrency, environment protection, and least-privilege permissions.**
- **Artifacts carry authoritative workflow outputs, while caches accelerate repeated work; production deployments should promote the same immutable artifact rather than rebuild independently for each environment.**
- **Security boundaries must be designed into workflows through minimal `GITHUB_TOKEN` permissions, safe handling of untrusted GitHub data, careful `pull_request_target` usage, trusted action dependencies, protected environments, and OIDC-based AWS authentication.**
- **Senior-level workflow design focuses on critical-path optimization, deterministic execution, failure isolation, observability, resource constraints, deployment serialization, traceability, and reliable rollback.**