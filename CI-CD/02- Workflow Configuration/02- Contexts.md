# 02- Contexts

## Overview

GitHub Actions contexts provide structured information about the workflow execution environment. They expose repository metadata, event payloads, variables, secrets, step outputs, job results, runner information, matrix values, strategy configuration, and workflow inputs.

Contexts are the primary mechanism for making workflows dynamic without hard-coding repository-specific values.

A production CI/CD pipeline commonly uses contexts to answer questions such as:

- Which repository triggered this workflow?
- Which branch or tag caused the run?
- Which commit is being built?
- Is this a pull request or a push?
- Did a dependent job succeed?
- What matrix combination is currently running?
- Which environment is being deployed?
- What output did an earlier step produce?
- Which runner is executing the job?
- What deployment input was supplied?

The core model is:

```text
Workflow
    |
    +-- Event
    |     |
    |     +-- github context
    |
    +-- Configuration
    |     |
    |     +-- vars / env / secrets
    |
    +-- Job
    |     |
    |     +-- needs / job / matrix / strategy / runner
    |
    +-- Steps
          |
          +-- steps / outputs
```

Contexts should be understood separately from expressions. A context provides data; an expression accesses and evaluates that data.

For example:

```yaml
if: ${{ github.ref_name == 'main' }}
```

Here:

- `github` is a context.
- `ref_name` is a property in that context.
- `==` is an expression operator.
- `${{ }}` tells GitHub Actions to evaluate the expression.

---

## Why Contexts Matter

Without contexts, workflows would require large amounts of hard-coded configuration.

A workflow could theoretically contain:

```yaml
env:
  REPOSITORY: my-company/my-service
  BRANCH: main
  COMMIT: abc123
```

but these values become incorrect as soon as another commit, branch, repository, or workflow run is used.

Contexts provide runtime information automatically.

For example:

```yaml
env:
  COMMIT_SHA: ${{ github.sha }}
  BRANCH_NAME: ${{ github.ref_name }}
  RUN_ID: ${{ github.run_id }}
```

The same workflow can now run against different commits and branches without modifying the YAML.

This becomes particularly important for:

- Multi-branch CI
- Pull request validation
- Matrix testing
- Docker image tagging
- Artifact promotion
- Environment-specific deployment
- AWS authentication
- Reusable workflows
- Production rollback
- Debugging and observability

---

## Contexts vs Expressions vs Environment Variables

These concepts are related but not interchangeable.

| Concept | Purpose | Example |
|---|---|---|
| Context | Provides structured workflow data | `github.sha` |
| Expression | Evaluates or transforms values | `${{ github.ref_name == 'main' }}` |
| Environment variable | Makes a value available to a process | `$COMMIT_SHA` |
| Secret | Provides sensitive configuration | `${{ secrets.API_TOKEN }}` |
| Output | Transfers data between workflow components | `${{ steps.build.outputs.image }}` |

A common production pattern is:

```text
GitHub context
      |
      v
Expression
      |
      v
Environment variable
      |
      v
Shell / application
```

Example:

```yaml
- name: Build
  env:
    COMMIT_SHA: ${{ github.sha }}
  run: docker build -t "backend:${COMMIT_SHA}" .
```

GitHub evaluates the expression first. The runner then receives `COMMIT_SHA` as an environment variable.

---

## Context Availability

Contexts are not universally available in every location.

For example:

- `github` is broadly available.
- `steps` represents steps in the current job.
- `needs` depends on declared job dependencies.
- `matrix` exists when a matrix strategy is active.
- `inputs` depends on workflow inputs.
- Event-specific properties under `github.event` depend on the triggering event.
- `secrets` availability depends on workflow security boundaries and configuration.

This matters because event payloads differ.

A pull request event can contain:

```yaml
github.event.pull_request
```

while a normal push event does not provide the same pull-request object.

A robust workflow therefore considers both:

```text
What context exists?
        +
What event triggered the workflow?
```

---

## `github` Context

The `github` context contains information about the repository, workflow run, event, commit, actor, and Git reference.

Common properties include:

| Property | Typical use |
|---|---|
| `github.repository` | Repository identifier |
| `github.repository_owner` | Repository owner |
| `github.ref` | Full Git reference |
| `github.ref_name` | Short branch or tag name |
| `github.sha` | Commit SHA |
| `github.actor` | User or automation actor |
| `github.event_name` | Triggering event |
| `github.workflow` | Workflow name |
| `github.run_id` | Unique workflow run identifier |
| `github.run_number` | Workflow run number |
| `github.run_attempt` | Attempt number |
| `github.server_url` | GitHub server URL |
| `github.api_url` | GitHub API URL |

Example:

```yaml
- name: Build metadata
  env:
    REPOSITORY: ${{ github.repository }}
    COMMIT_SHA: ${{ github.sha }}
    BRANCH: ${{ github.ref_name }}
    EVENT: ${{ github.event_name }}
    RUN_ID: ${{ github.run_id }}
  run: |
    echo "Repository: $REPOSITORY"
    echo "Commit: $COMMIT_SHA"
    echo "Branch: $BRANCH"
    echo "Event: $EVENT"
    echo "Run: $RUN_ID"
```

---

## `github.ref` vs `github.ref_name`

These values are frequently confused.

For a branch:

```text
github.ref
    refs/heads/main

github.ref_name
    main
```

For a tag:

```text
github.ref
    refs/tags/v1.5.0

github.ref_name
    v1.5.0
```

Use `github.ref_name` when the short branch or tag name is sufficient.

Use `github.ref` when the full Git reference is relevant.

For example:

```yaml
if: ${{ github.ref == 'refs/heads/main' }}
```

or:

```yaml
if: ${{ github.ref_name == 'main' }}
```

Both can be valid; choose one representation consistently.

---

## `github.sha`

`github.sha` identifies the commit associated with the workflow event.

It is especially useful for immutable artifact naming.

```yaml
env:
  IMAGE_TAG: ${{ github.sha }}
```

Docker:

```yaml
- name: Build image
  env:
    IMAGE_TAG: ${{ github.sha }}
  run: docker build -t "backend:${IMAGE_TAG}" .
```

For a production pipeline:

```text
Git Commit
    |
    v
github.sha
    |
    v
Docker Image Tag
    |
    v
Container Registry
```

This provides a direct relationship between source code and deployed artifact.

For production deployment, an image digest is even stronger as an immutable artifact identifier, while the commit SHA remains useful as traceability metadata.

---

## `github.event_name`

`github.event_name` identifies the event that triggered the workflow.

Examples include:

```text
push
pull_request
workflow_dispatch
schedule
workflow_call
workflow_run
release
repository_dispatch
```

Example:

```yaml
if: ${{ github.event_name == 'pull_request' }}
```

Another:

```yaml
if: >-
  ${{
    github.event_name == 'push' &&
    github.ref_name == 'main'
  }}
```

This is useful when one workflow handles multiple event types.

---

## `github.event`

The `github.event` context contains the payload associated with the triggering event.

Its structure depends on the event.

For a pull request:

```yaml
${{ github.event.pull_request.number }}
```

For a push, the payload contains different information.

This means workflows should avoid assuming that event-specific properties always exist.

A safer pattern is:

```yaml
if: ${{ github.event_name == 'pull_request' }}
```

followed by use of pull-request-specific data.

---

## Event-Specific Context Data

Different events expose different payload structures.

| Event | Typical information |
|---|---|
| `push` | Branch/tag, commits, repository information |
| `pull_request` | PR number, title, source/base branch, labels |
| `workflow_dispatch` | Manual inputs |
| `release` | Release metadata |
| `schedule` | Scheduled workflow execution |
| `workflow_run` | Previous workflow execution |
| `repository_dispatch` | Custom event payload |

The event payload should be treated as external input, especially for events that can originate from untrusted contributors.

---

## `github.actor`

`github.actor` identifies the user or automation account associated with the workflow event.

Example:

```yaml
- name: Record actor
  run: echo "Triggered by ${{ github.actor }}"
```

This can be useful for audit information.

Do not use actor identity as the sole authorization mechanism for production deployments.

Production authorization should rely on stronger controls such as:

- Protected branches
- Protected environments
- Required reviewers
- Least-privilege permissions
- Trusted workflow sources
- Deployment policies

---

## `github.workflow`

The workflow name can be accessed through:

```yaml
${{ github.workflow }}
```

It can be useful for diagnostics and notifications.

Example:

```yaml
- name: Build metadata
  env:
    WORKFLOW_NAME: ${{ github.workflow }}
  run: echo "Workflow: $WORKFLOW_NAME"
```

---

## `github.run_id`, `github.run_number`, and `github.run_attempt`

These values identify workflow execution state.

```text
run_id
    unique workflow run identifier

run_number
    human-readable workflow sequence

run_attempt
    attempt number for a rerun
```

Example:

```yaml
env:
  RUN_ID: ${{ github.run_id }}
  RUN_NUMBER: ${{ github.run_number }}
  RUN_ATTEMPT: ${{ github.run_attempt }}
```

These values are useful for:

- Build metadata
- Debugging
- Artifact naming
- Deployment auditing
- Incident investigation

---

## `env` Context

The `env` context represents environment variables configured in the workflow.

Example:

```yaml
env:
  APP_NAME: backend-api

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Display configuration
        run: echo "$APP_NAME"
```

The same value can be accessed as an expression:

```yaml
${{ env.APP_NAME }}
```

or by the shell:

```bash
$APP_NAME
```

These are two different access mechanisms.

---

## Environment Variable Scope

Environment variables can be defined at three major workflow levels.

### Workflow Level

```yaml
env:
  LOG_LEVEL: INFO
```

Available to jobs unless overridden.

### Job Level

```yaml
jobs:
  test:
    env:
      APP_ENV: test
```

Available to steps in that job.

### Step Level

```yaml
steps:
  - name: Integration tests
    env:
      DATABASE_URL: postgresql://localhost/test
    run: pytest
```

Available only to that step.

The practical hierarchy is:

```text
Workflow env
      ↓
Job env
      ↓
Step env
```

More specific configuration can override a broader value with the same name.

---

## `env` Context vs Runner Environment

The `env` context belongs to GitHub Actions expression evaluation.

The runner environment contains actual environment variables available to the executed process.

For example:

```yaml
env:
  COMMIT_SHA: ${{ github.sha }}

steps:
  - run: echo "$COMMIT_SHA"
```

The flow is:

```text
github.sha
    |
    | expression evaluation
    v
env.COMMIT_SHA
    |
    | runner environment
    v
$COMMIT_SHA
```

This distinction is important when debugging why an expression works but a shell command does not.

---

## `vars` Context

The `vars` context provides GitHub Actions configuration variables.

Variables can be defined at supported scopes such as:

- Organization
- Repository
- Environment

Example:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
  ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
```

Variables are intended for non-sensitive configuration.

Good examples include:

```text
AWS_REGION
ECR_REPOSITORY
SERVICE_NAME
DEPLOYMENT_TIMEOUT
```

Do not use variables for passwords, private keys, tokens, or other sensitive credentials.

---

## `vars` vs `env`

These mechanisms solve different problems.

| Feature | `vars` | `env` |
|---|---|---|
| Primary purpose | GitHub configuration | Runtime environment |
| Scope | Organization/repository/environment | Workflow/job/step |
| Secret storage | No | No |
| Expression access | `vars.NAME` | `env.NAME` |
| Shell access | Through `env` | Direct |
| Good for | Shared configuration | Process environment |

A common pattern is:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
```

This converts centrally managed configuration into a runtime environment variable.

---

## Variable Precedence

When the same environment variable is defined at multiple workflow scopes, the more specific scope takes precedence.

Example:

```yaml
env:
  APP_ENV: development

jobs:
  test:
    env:
      APP_ENV: test

    steps:
      - name: Test
        env:
          APP_ENV: ci
        run: echo "$APP_ENV"
```

The effective value is:

```text
ci
```

For maintainability, avoid defining the same variable at multiple scopes unless overriding it is intentional.

---

## `secrets` Context

The `secrets` context provides access to configured sensitive values.

Example:

```yaml
- name: Authenticate
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
  run: ./scripts/authenticate.sh
```

Secrets can be configured at supported scopes including:

- Organization
- Repository
- Environment

Environment secrets are particularly important for production deployment workflows.

---

## Secret Scope and Deployment Environments

A typical backend platform might have:

```text
Development
    |
    +-- development configuration
    +-- development secrets

Staging
    |
    +-- staging configuration
    +-- staging secrets

Production
    |
    +-- production configuration
    +-- production secrets
```

A deployment job can target an environment:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Deploy
        run: ./deploy.sh
```

Protected environment configuration can then control access to production secrets and deployment approvals.

---

## Secret Masking

GitHub Actions attempts to mask configured secrets in workflow logs.

However:

```text
Secret masking
    ≠
Safe secret handling
```

Never intentionally print secrets.

Avoid:

```yaml
- name: Debug
  run: echo "${{ secrets.API_TOKEN }}"
```

Prefer:

```yaml
- name: Authenticate
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
  run: ./authenticate.sh
```

The application or CLI receives the credential without the workflow intentionally writing it to logs.

---

## Secrets in Command Arguments

Avoid putting sensitive values directly into command arguments.

Instead of:

```yaml
- run: ./deploy.sh --token "${{ secrets.DEPLOY_TOKEN }}"
```

prefer:

```yaml
- name: Deploy
  env:
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
  run: ./deploy.sh
```

The deployment script can read:

```python
import os

token = os.environ["DEPLOY_TOKEN"]
```

This reduces the chance of exposing secrets through command inspection, debugging, process listings, or accidental logging.

---

## `secrets: inherit`

Reusable workflows can receive secrets from the caller using:

```yaml
secrets: inherit
```

Example:

```yaml
jobs:
  deploy:
    uses: organization/platform-workflows/.github/workflows/deploy.yml@v1
    secrets: inherit
```

This is convenient, but it expands the set of secrets available to the called workflow.

For security-sensitive environments, prefer explicit secret interfaces when practical.

For example:

```yaml
jobs:
  deploy:
    uses: organization/platform-workflows/.github/workflows/deploy.yml@v1
    secrets:
      AWS_ROLE_ARN: ${{ secrets.AWS_ROLE_ARN }}
```

The principle is:

```text
Reusable workflow
        |
        +-- Only required secrets
```

rather than:

```text
Reusable workflow
        |
        +-- Every available repository secret
```

---

## `steps` Context

The `steps` context contains information about steps that have already executed in the current job.

It is primarily used for:

- Step outputs
- Step results
- Step-level data flow

Example:

```yaml
- name: Generate image tag
  id: metadata
  run: echo "tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

- name: Display image tag
  run: echo "${{ steps.metadata.outputs.tag }}"
```

The important structure is:

```text
step
  |
  +-- id: metadata
          |
          +-- outputs.tag
                  |
                  +-- steps.metadata.outputs.tag
```

---

## Step IDs

A step must have an `id` when another step needs to reference its outputs.

Correct:

```yaml
- name: Generate version
  id: version
  run: echo "value=1.5.0" >> "$GITHUB_OUTPUT"

- name: Publish version
  run: echo "${{ steps.version.outputs.value }}"
```

Without the ID:

```yaml
- name: Generate version
  run: echo "value=1.5.0" >> "$GITHUB_OUTPUT"
```

there is no named step reference such as:

```text
steps.version.outputs.value
```

---

## Step Results

The `steps` context can expose information about step execution.

A common pattern is:

```yaml
- name: Publish diagnostics
  if: ${{ failure() }}
  uses: actions/upload-artifact@v4
  with:
    name: diagnostics
    path: logs/
```

For detailed execution logic, status functions such as `success()` and `failure()` are generally clearer than building complex conditions around step state.

---

## `$GITHUB_OUTPUT` and `steps`

The modern mechanism for setting step outputs is `$GITHUB_OUTPUT`.

```yaml
- name: Generate metadata
  id: metadata
  shell: bash
  run: |
    echo "version=1.5.0" >> "$GITHUB_OUTPUT"
    echo "commit=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

Consume the outputs:

```yaml
- name: Display metadata
  env:
    VERSION: ${{ steps.metadata.outputs.version }}
    COMMIT: ${{ steps.metadata.outputs.commit }}
  run: |
    echo "Version: $VERSION"
    echo "Commit: $COMMIT"
```

This is preferable to older deprecated workflow command patterns.

---

## `needs` Context

The `needs` context provides information from jobs that the current job depends on.

Example:

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
  |
  v
Build
```

The `needs` context lets the downstream job consume outputs and inspect results.

---

## Job Outputs Through `needs`

A job can expose outputs generated by its steps.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      image-tag: ${{ steps.metadata.outputs.image-tag }}

    steps:
      - name: Generate image tag
        id: metadata
        run: echo "image-tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - name: Deploy image
        env:
          IMAGE_TAG: ${{ needs.build.outputs.image-tag }}
        run: ./deploy.sh "$IMAGE_TAG"
```

The complete data path is:

```text
Step
  |
  | $GITHUB_OUTPUT
  v
Step output
  |
  v
Job output
  |
  v
needs.build.outputs.image-tag
  |
  v
Deploy job
```

This is one of the most important context-based data flows in production GitHub Actions.

---

## `needs.<job>.result`

A dependent job can inspect the result of a required job.

Typical values include:

```text
success
failure
cancelled
skipped
```

Example:

```yaml
if: ${{ needs.tests.result == 'success' }}
```

A production deployment might use:

```yaml
deploy:
  needs:
    - lint
    - test
    - security

  if: >-
    ${{
      needs.lint.result == 'success' &&
      needs.test.result == 'success' &&
      needs.security.result == 'success'
    }}

  runs-on: ubuntu-latest

  steps:
    - run: ./deploy.sh
```

This makes the promotion rule visible in the workflow.

---

## Multiple `needs` Dependencies

A job can depend on multiple jobs.

```yaml
build:
  needs:
    - lint
    - unit-tests
    - integration-tests
    - security
```

The resulting graph is:

```mermaid
flowchart LR
    L[Lint] --> B[Build]
    U[Unit Tests] --> B
    I[Integration Tests] --> B
    S[Security Scan] --> B
    B --> D[Deploy]
```

This is a fan-in pattern.

The build job does not need to repeat the implementation of those checks. The dependency graph expresses the relationship.

---

## `job` Context

The `job` context provides information about the current job.

A useful property is:

```yaml
${{ job.status }}
```

Example:

```yaml
- name: Record job status
  env:
    STATUS: ${{ job.status }}
  run: echo "Job status: $STATUS"
```

The context can be useful for diagnostics and workflow logic, but most normal dependency decisions are better expressed using `needs` and status functions.

---

## `runner` Context

The `runner` context describes the runner executing the current job.

Common properties include:

| Property | Meaning |
|---|---|
| `runner.os` | Runner operating system |
| `runner.arch` | Runner architecture |
| `runner.name` | Runner name |
| `runner.temp` | Temporary directory |
| `runner.tool_cache` | Tool cache location |

Example:

```yaml
- name: Inspect runner
  env:
    OS: ${{ runner.os }}
    ARCH: ${{ runner.arch }}
    NAME: ${{ runner.name }}
  run: |
    echo "OS: $OS"
    echo "Architecture: $ARCH"
    echo "Runner: $NAME"
```

This is useful when workflows run across Linux and Windows or across different runner architectures.

---

## Runner-Specific Behavior

A workflow should avoid assuming that every runner behaves identically.

For example:

```yaml
strategy:
  matrix:
    os:
      - ubuntu-latest
      - windows-latest

runs-on: ${{ matrix.os }}
```

The workflow now has multiple execution environments.

Shell behavior, filesystem conventions, installed tooling, paths, and operating-system utilities can differ.

When portability matters, prefer:

- Explicit setup actions
- Cross-platform tooling
- Python or Node scripts for complex logic
- Minimal shell-specific assumptions

---

## `matrix` Context

The `matrix` context represents the current matrix combination.

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version:
          - "3.11"
          - "3.12"
          - "3.13"

    steps:
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}

      - name: Test
        run: python -m pytest
```

GitHub expands the matrix into independent job executions.

```text
Matrix
   |
   +-- Python 3.11
   +-- Python 3.12
   +-- Python 3.13
```

---

## Multiple Matrix Dimensions

Multiple dimensions produce combinations.

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

This creates four combinations:

```text
3.11 + postgres
3.11 + mysql
3.12 + postgres
3.12 + mysql
```

The dimensions can be consumed through the `matrix` context:

```yaml
env:
  DATABASE: ${{ matrix.database }}
  PYTHON_VERSION: ${{ matrix.python-version }}
```

---

## Matrix `include`

`include` adds metadata or additional combinations.

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

A job can consume:

```yaml
continue-on-error: ${{ matrix.experimental == true }}
```

This is useful for explicitly separating stable compatibility targets from experimental targets.

---

## Matrix `exclude`

`exclude` removes unsupported combinations.

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

This prevents invalid or unnecessary test combinations.

---

## Matrix Context in Artifact Names

Matrix values are useful for making test artifacts unique.

```yaml
- name: Upload coverage
  uses: actions/upload-artifact@v4
  with:
    name: coverage-python-${{ matrix.python-version }}
    path: coverage.xml
```

For multiple dimensions:

```yaml
name: coverage-${{ matrix.python-version }}-${{ matrix.database }}
```

This makes artifacts easier to identify during failure analysis.

---

## Matrix and `needs`

A matrix job can depend on another job.

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest

    steps:
      - run: echo "Preparing test configuration"

  test:
    needs: prepare

    strategy:
      matrix:
        python-version:
          - "3.11"
          - "3.12"

    runs-on: ubuntu-latest

    steps:
      - run: python -V
```

The dependency is:

```text
Prepare
   |
   v
Matrix expansion
   |
   +-- Python 3.11
   +-- Python 3.12
```

---

## Dynamic Matrices

Dynamic matrices are generated at runtime.

A preparation job can generate JSON:

```yaml
jobs:
  generate:
    runs-on: ubuntu-latest

    outputs:
      versions: ${{ steps.matrix.outputs.versions }}

    steps:
      - id: matrix
        run: |
          echo 'versions=["3.11","3.12","3.13"]' >> "$GITHUB_OUTPUT"
```

The matrix consumes it:

```yaml
  test:
    needs: generate

    strategy:
      matrix:
        python-version: ${{ fromJSON(needs.generate.outputs.versions) }}

    runs-on: ubuntu-latest

    steps:
      - name: Test
        run: python -m pytest
```

The data flow is:

```text
Generate
   |
   | JSON
   v
Job output
   |
   | needs
   v
fromJSON()
   |
   v
Matrix
```

Dynamic matrices are useful when test targets are determined by configuration or repository metadata.

They also introduce additional complexity, so static matrices should remain the default when the supported combinations are stable.

---

## `strategy` Context

The `strategy` context relates to the current job's matrix strategy.

Matrix execution controls include:

```yaml
strategy:
  fail-fast: false
  max-parallel: 3

  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

These settings have operational consequences.

### `fail-fast`

Controls whether in-progress matrix jobs can be cancelled when another matrix job fails.

### `max-parallel`

Controls the maximum number of matrix jobs that can execute concurrently.

A senior-level design considers:

```text
Matrix size
+
Runner capacity
+
Test duration
+
External service limits
+
Cost
```

before increasing parallelism.

---

## `inputs` Context

The `inputs` context provides values supplied to workflows.

It is particularly important for:

- `workflow_dispatch`
- `workflow_call`

Example:

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: Deployment environment
        required: true
        type: choice
        options:
          - staging
          - production
```

Use the input:

```yaml
- name: Display target
  run: echo "Deploying to ${{ inputs.environment }}"
```

For production workflows, use typed inputs and constrain valid values whenever possible.

---

## Manual Deployment Inputs

A controlled deployment workflow can expose:

```text
environment
version
rollback
```

For example:

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

      image-tag:
        description: Immutable image tag
        required: true
        type: string
```

The deployment job can then consume:

```yaml
env:
  IMAGE_TAG: ${{ inputs.image-tag }}
```

The important security principle is that workflow inputs should be treated as user-controlled data, not trusted shell source.

---

## `inputs` in Reusable Workflows

Reusable workflows define inputs through `workflow_call`.

```yaml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string

      image-tag:
        required: true
        type: string
```

The called workflow can consume:

```yaml
${{ inputs.environment }}
```

and:

```yaml
${{ inputs.image-tag }}
```

This creates a clear workflow interface.

```text
Calling Repository
       |
       | inputs
       v
Reusable Workflow
       |
       | outputs
       v
Calling Repository
```

---

## Contexts in Reusable Workflows

A reusable deployment workflow might receive:

```text
inputs:
    environment
    image-tag

secrets:
    deployment credentials
```

and produce:

```text
outputs:
    deployment-id
    deployment-status
```

This is preferable to embedding repository-specific deployment logic in every application repository.

A reusable workflow effectively becomes a CI/CD platform API.

---

## `secrets` and Reusable Workflows

Explicit secret mapping:

```yaml
jobs:
  deploy:
    uses: organization/platform-workflows/.github/workflows/deploy.yml@v1
    with:
      environment: production
      image-tag: ${{ needs.build.outputs.image-tag }}
    secrets:
      AWS_ROLE_ARN: ${{ secrets.AWS_ROLE_ARN }}
```

The called workflow defines:

```yaml
on:
  workflow_call:
    secrets:
      AWS_ROLE_ARN:
        required: true
```

This makes the security contract visible.

---

## Contexts and AWS OIDC

Contexts are useful when configuring GitHub Actions authentication with AWS.

A production deployment can use GitHub's OIDC identity instead of storing long-lived AWS credentials.

A typical flow is:

```text
GitHub Actions
      |
      | OIDC identity token
      v
AWS STS
      |
      | AssumeRoleWithWebIdentity
      v
Temporary AWS credentials
      |
      v
ECR / ECS / S3 / CloudFormation
```

The workflow can use repository and environment information to control which deployments are allowed to assume a particular AWS role.

For example, the workflow can distinguish:

```text
main branch
+
production environment
```

from:

```text
feature branch
+
pull request
```

The exact AWS trust policy is an infrastructure-level security control; GitHub contexts provide the identity information used by the workflow and OIDC claims.

---

## Contexts and Docker Image Metadata

Contexts are particularly useful for immutable container tags.

```yaml
env:
  IMAGE_TAG: ${{ github.sha }}
```

A Docker build can then use:

```yaml
- name: Build image
  env:
    IMAGE_TAG: ${{ github.sha }}
  run: |
    docker build \
      --tag "backend:${IMAGE_TAG}" \
      .
```

For ECR:

```yaml
- name: Build and push
  env:
    IMAGE_URI: ${{ vars.ECR_REGISTRY }}/${{ vars.ECR_REPOSITORY }}
    IMAGE_TAG: ${{ github.sha }}
  run: |
    docker build -t "${IMAGE_URI}:${IMAGE_TAG}" .
    docker push "${IMAGE_URI}:${IMAGE_TAG}"
```

The resulting relationship is:

```text
Git commit
    |
    v
github.sha
    |
    v
Docker tag
    |
    v
ECR
    |
    v
ECS
```

This is more auditable than relying only on a mutable tag such as `latest`.

---

## Contexts and Environment Promotion

A deployment workflow can use:

```yaml
environment:
  name: ${{ inputs.environment }}
```

and:

```yaml
env:
  IMAGE_TAG: ${{ needs.build.outputs.image-tag }}
```

The deployment then becomes:

```text
Build
  |
  +-- immutable image
  |
  v
Staging
  |
  +-- validation
  |
  v
Production
  |
  +-- protected environment
  +-- approval
  +-- concurrency control
```

Contexts connect the workflow stages without rebuilding the application.

---

## Contexts and Artifacts

Artifacts are files produced during workflow execution.

A matrix job can create unique artifacts:

```yaml
- name: Upload test report
  uses: actions/upload-artifact@v4
  with:
    name: pytest-${{ matrix.python-version }}
    path: reports/
```

The context determines artifact identity:

```text
matrix.python-version
        |
        v
artifact name
        |
        v
GitHub artifact storage
```

This is useful for:

- Coverage reports
- Test results
- Build packages
- Debug logs
- Diagnostic output

Artifacts should not be confused with caches.

```text
Artifact
    = output worth retaining or transferring

Cache
    = reusable dependency/build acceleration data
```

---

## Contexts and Caching

The `runner` and `github` contexts are commonly used in cache keys.

Example:

```yaml
key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
```

This creates a dependency-sensitive key.

The components represent:

```text
Operating system
+
Dependency definition
+
File hash
```

A cache key should reflect the inputs that determine cache validity.

---

## `runner` and Cache Portability

A cache created for one runner environment may not be appropriate for another.

For example:

```text
Linux cache
    ≠
Windows cache
```

Therefore:

```yaml
key: ${{ runner.os }}-...
```

can prevent inappropriate cross-platform reuse.

For compiled dependencies, architecture can also matter.

A senior-level cache design considers:

- Operating system
- Architecture
- Dependency lock files
- Runtime version
- Build configuration

---

## Contexts and Service Containers

Backend integration tests commonly use service containers.

For example:

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: test-password
          POSTGRES_DB: app_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U app -d app_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: python -m pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://app:test-password@localhost:5432/app_test
        run: python -m pytest
```

The environment variable provides the application with the connection information.

This pattern applies to Django and FastAPI integration testing.

---

## Contexts and Redis

A Python backend may require both PostgreSQL and Redis.

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: test-password
      POSTGRES_DB: app_test
    ports:
      - 5432:5432

  redis:
    image: redis:7
    ports:
      - 6379:6379
```

The test process can receive:

```yaml
env:
  DATABASE_URL: postgresql://app:test-password@localhost:5432/app_test
  REDIS_URL: redis://localhost:6379/0
```

The contexts themselves do not provide database connectivity. They provide the configuration values that the runner process consumes.

---

## Contexts and Environment-Specific Configuration

A production repository can centralize non-sensitive configuration using variables.

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
  ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
```

Then environment-specific values can be selected through the deployment environment.

For example:

```text
staging
    AWS_REGION = ap-south-1
    ECR_REPOSITORY = backend-staging

production
    AWS_REGION = ap-south-1
    ECR_REPOSITORY = backend-production
```

The workflow logic remains the same while configuration changes by environment.

---

## Contexts and Security Boundaries

Contexts are powerful because they expose information to workflow execution.

That also makes them a security concern.

Treat potentially attacker-controlled values as untrusted.

Examples include:

- Pull request titles
- Pull request branch names
- Commit messages
- Issue content
- Manual workflow inputs
- Repository content from untrusted contributors

Do not insert these directly into shell source.

Unsafe:

```yaml
- name: Process PR title
  run: echo "${{ github.event.pull_request.title }}"
```

Safer:

```yaml
- name: Process PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: |
    printf '%s\n' "$PR_TITLE"
```

The value becomes data passed to the process rather than source code inserted into the shell command.

---

## Contexts and `pull_request_target`

`pull_request_target` requires particular caution because it executes in the context of the base repository.

The dangerous combination is:

```text
pull_request_target
       +
untrusted checkout
       +
secrets
       +
write permissions
```

Avoid architectures where untrusted pull-request code is executed with access to production credentials.

A safer design separates:

```text
PR validation
    |
    +-- Untrusted code
    +-- Minimal permissions
    +-- No production secrets
```

from:

```text
Production deployment
    |
    +-- Trusted branch
    +-- Protected environment
    +-- Least privilege
    +-- Controlled credentials
```

---

## Contexts and Least-Privilege Permissions

Context availability does not automatically mean the workflow should have broad GitHub permissions.

For example:

```yaml
permissions:
  contents: read
```

A deployment job might require additional narrowly scoped permissions.

```yaml
permissions:
  contents: read
  id-token: write
```

The `id-token` permission is particularly relevant to GitHub OIDC authentication.

A strong design separates:

```text
Data available to workflow
        ≠
Authority granted to workflow
```

A context can tell the workflow what repository or branch it is operating on, but permissions determine what the workflow is allowed to do.

---

## Contexts and Untrusted Branch Names

Avoid:

```yaml
run: ./deploy.sh ${{ github.head_ref }}
```

Prefer:

```yaml
- name: Process source branch
  env:
    HEAD_REF: ${{ github.head_ref }}
  run: ./process-branch.sh "$HEAD_REF"
```

Even if the value appears to be a normal Git branch name, repository contributors control branch names.

The same principle applies to:

```text
commit messages
PR titles
issue titles
workflow inputs
release metadata
```

---

## Context Debugging

When a condition behaves unexpectedly, expose only the specific values needed.

```yaml
- name: Debug workflow metadata
  env:
    EVENT_NAME: ${{ github.event_name }}
    REF: ${{ github.ref }}
    REF_NAME: ${{ github.ref_name }}
    SHA: ${{ github.sha }}
    RUN_ID: ${{ github.run_id }}
  run: |
    echo "Event: $EVENT_NAME"
    echo "Ref: $REF"
    echo "Ref name: $REF_NAME"
    echo "SHA: $SHA"
    echo "Run ID: $RUN_ID"
```

For matrix debugging:

```yaml
- name: Debug matrix
  env:
    MATRIX: ${{ toJSON(matrix) }}
  run: echo "$MATRIX"
```

For step outputs:

```yaml
- name: Debug build metadata
  env:
    IMAGE_TAG: ${{ steps.metadata.outputs.image-tag }}
  run: echo "Image tag: $IMAGE_TAG"
```

Do not use broad context dumps in production debugging if they may expose sensitive information.

---

## Context Troubleshooting

Use a structured diagnostic model.

```text
Unexpected value
       |
       v
Identify triggering event
       |
       v
Verify context availability
       |
       v
Inspect exact property
       |
       v
Check expression evaluation
       |
       v
Check job dependency
       |
       v
Check output generation
       |
       v
Check environment scope
       |
       v
Correct configuration
```

### Job Is Skipped

Check:

- `if`
- `github.event_name`
- `github.ref`
- `github.ref_name`
- `needs.<job>.result`
- Environment protection
- Manual input values

### Output Is Empty

Check:

- Producer step has an `id`
- `$GITHUB_OUTPUT` is written correctly
- Output name matches exactly
- Consumer executes after producer
- Cross-job output is exposed through job `outputs`

### Matrix Value Is Missing

Check:

- Matrix definition
- `include`
- `exclude`
- Dynamic JSON
- `fromJSON()`
- Matrix property name

### Environment Variable Is Unexpected

Check:

- Workflow-level `env`
- Job-level `env`
- Step-level `env`
- `vars`
- `$GITHUB_ENV`
- Shell environment
- Variable naming consistency

### Event Property Is Missing

Check:

```yaml
- name: Show event
  env:
    EVENT_NAME: ${{ github.event_name }}
  run: echo "$EVENT_NAME"
```

Then verify that the referenced property actually belongs to that event payload.

---

## Context Data Flow

A production workflow often combines several contexts.

```mermaid
flowchart TD
    E[GitHub Event] --> G[github Context]
    I[Workflow Inputs] --> IN[inputs Context]
    C[Repository / Org / Environment Configuration] --> V[vars Context]
    S[Secrets Configuration] --> SC[secrets Context]

    G --> X[Expressions]
    IN --> X
    V --> X
    SC --> X

    X --> ENV[Environment Variables]
    X --> ST[Step Outputs]

    ST --> SO[Job Outputs]
    SO --> N[needs Context]

    M[Matrix Strategy] --> MX[matrix Context]
    R[Runner] --> RC[runner Context]

    N --> D[Downstream Job]
    MX --> D
    RC --> D
    ENV --> D
```

This model is useful when designing complex pipelines because it makes data ownership explicit.

---

## Contexts in a Production CI/CD Pipeline

Consider:

```text
Pull Request
    |
    v
Lint
    |
    v
Matrix Tests
    |
    v
Security Scan
    |
    v
Build
    |
    +-- image digest
    |
    v
ECR
    |
    v
Staging
    |
    v
Approval
    |
    v
Production
```

Contexts support this pipeline at different stages.

| Pipeline requirement | Useful context |
|---|---|
| Identify commit | `github.sha` |
| Identify branch | `github.ref_name` |
| Identify event | `github.event_name` |
| Select Python version | `matrix` |
| Select operating system | `matrix` / `runner` |
| Pass build metadata | `steps` / `needs` |
| Select environment | `inputs` |
| Read configuration | `vars` |
| Access deployment secret | `secrets` |
| Check dependency status | `needs` |
| Identify runner | `runner` |

---

## Contexts and Artifact Promotion

A strong production pipeline produces an immutable artifact once and promotes it.

Example:

```text
Build Job
   |
   +-- github.sha
   |
   +-- Docker image
   |
   +-- image digest
   |
   v
ECR
   |
   v
Staging
   |
   v
Production
```

The deployment job can consume:

```yaml
env:
  IMAGE_TAG: ${{ needs.build.outputs.image-tag }}
```

rather than rebuilding the image.

This provides:

- Reproducibility
- Traceability
- Faster promotion
- Easier rollback
- Reduced environment drift

---

## Contexts and Concurrency

Context values can be used to construct concurrency groups.

For pull requests:

```yaml
concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

For production:

```yaml
concurrency:
  group: production-deployment
  cancel-in-progress: false
```

This prevents multiple workflow executions from competing for the same deployment target.

The design principle is:

```text
Context
   |
   v
Concurrency identity
   |
   v
Controlled execution
```

---

## Contexts and Reusable Workflows

Reusable workflows commonly use:

```text
inputs
secrets
needs
github
vars
```

Example caller:

```yaml
jobs:
  deploy:
    uses: organization/platform-workflows/.github/workflows/deploy.yml@v1
    with:
      environment: staging
      image-tag: ${{ needs.build.outputs.image-tag }}
    secrets:
      AWS_ROLE_ARN: ${{ secrets.AWS_ROLE_ARN }}
```

The reusable workflow becomes independent of the caller's implementation details.

This supports centralized CI/CD governance across multiple backend services.

---

## Contexts and Composite Actions

Composite actions operate within a job and primarily package reusable steps.

They commonly consume:

```text
inputs
env
runner environment
step outputs
```

Example:

```yaml
runs:
  using: composite

  steps:
    - name: Install dependencies
      shell: bash
      run: python -m pip install -r requirements.txt

    - name: Run tests
      shell: bash
      run: python -m pytest
```

A composite action does not replace a reusable workflow.

The distinction is:

```text
Reusable Workflow
    → Can orchestrate multiple jobs

Composite Action
    → Packages steps inside a job
```

---

## Contexts and Custom Actions

Custom actions receive inputs and execute in the runner environment.

Example:

```yaml
- name: Build metadata
  uses: organization/build-metadata@v1
  with:
    commit-sha: ${{ github.sha }}
    environment: ${{ inputs.environment }}
```

The calling workflow resolves the expressions and provides the resulting values to the action.

This creates a clean boundary:

```text
Workflow context
      |
      v
Expression evaluation
      |
      v
Action input
      |
      v
Action implementation
```

---

## Contexts and GitHub Actions Security

A useful security model is:

```text
Context data
    |
    +-- Some trusted
    +-- Some configuration
    +-- Some sensitive
    +-- Some attacker-controlled
```

Examples:

| Data | Typical trust consideration |
|---|---|
| `github.sha` | Repository event metadata |
| `github.ref_name` | Can reflect contributor-controlled branch names |
| `github.event.pull_request.title` | User-controlled |
| `inputs.*` | User-supplied workflow input |
| `vars.*` | Configuration |
| `secrets.*` | Sensitive |
| `steps.*` | Workflow-generated |
| `needs.*` | Upstream workflow-generated |
| `matrix.*` | Workflow configuration/generated |
| `runner.*` | Execution environment |

The important engineering rule is not to treat every context as equally trusted.

---

## Contexts and Observability

Context values can improve CI/CD observability.

Useful metadata includes:

```text
repository
branch
commit
workflow
run ID
run attempt
environment
artifact
image tag
deployment ID
```

A deployment system can associate:

```text
github.sha
    ↓
Docker image
    ↓
ECR digest
    ↓
ECS task definition
    ↓
deployment
```

This makes incident investigation significantly easier.

For example, when an ECS service is running an unexpected image, the deployment record can be traced back to the GitHub workflow run and source commit.

---

## Common Mistakes

### Confusing Contexts with Environment Variables

Incorrect mental model:

```text
github.sha == shell variable
```

They are not the same.

Correct:

```text
github.sha
    ↓
expression
    ↓
env variable
    ↓
shell
```

---

### Assuming All Event Payloads Are Identical

This can break workflows that run on multiple triggers.

Avoid:

```yaml
${{ github.event.pull_request.number }}
```

without considering whether the event is actually a pull request.

---

### Using `secrets` for Non-Sensitive Configuration

Avoid storing:

```text
AWS_REGION
SERVICE_NAME
ECR_REPOSITORY
```

as secrets when they are not sensitive.

Use appropriate configuration variables.

---

### Treating `vars` as Secrets

Do not put credentials into:

```yaml
vars:
  DATABASE_PASSWORD: ...
```

Use secrets or a dedicated secret-management system.

---

### Dumping Contexts for Debugging

Avoid broad debugging such as:

```yaml
- run: echo '${{ toJSON(github) }}'
```

Event payloads can contain information that should not be unnecessarily logged.

---

### Overusing `$GITHUB_ENV`

Environment variables are convenient, but they can obscure data flow.

Prefer outputs when a value is logically workflow metadata:

```text
Build image
    ↓
image-tag output
    ↓
Deploy job
```

rather than:

```text
Build image
    ↓
GITHUB_ENV
    ↓
same job only
```

---

### Using Step Outputs Across Jobs Without Job Outputs

This does not work across job boundaries:

```text
steps.metadata.outputs.tag
```

from another job.

Expose it explicitly:

```yaml
outputs:
  image-tag: ${{ steps.metadata.outputs.tag }}
```

Then consume:

```yaml
${{ needs.build.outputs.image-tag }}
```

---

### Treating Matrix Jobs as One Execution

Each matrix combination is an independent execution.

For example:

```text
3 Python versions
×
2 databases
=
6 job executions
```

This affects:

- Cost
- Runtime
- Failure diagnosis
- Artifact naming
- External service load

---

## Production Best Practices

### Keep Context Usage Explicit

Prefer:

```yaml
env:
  IMAGE_TAG: ${{ github.sha }}
```

over repeating complex expressions throughout multiple steps.

### Use Outputs for Workflow Data

Use:

```text
$GITHUB_OUTPUT
```

for values that logically belong to workflow data flow.

### Use `needs` for Job Dependencies

Do not implement job dependency logic through external files or implicit assumptions.

### Use `vars` for Non-Sensitive Configuration

Centralize stable configuration where appropriate.

### Use Environment Secrets for Sensitive Deployments

Production credentials should not be available to unrelated CI jobs.

### Treat Event Data as Untrusted

Especially:

```text
pull request metadata
branch names
commit messages
manual inputs
issue content
```

### Keep Conditions Auditable

A reviewer should be able to understand why production deployment runs.

### Prefer Immutable Artifact References

Use:

```text
commit SHA
image digest
version
```

for artifact promotion.

### Minimize Permissions

Context availability does not imply authorization.

Use the smallest required `permissions` block.

### Separate Validation from Deployment

A pull request should normally validate code without receiving production deployment credentials.

---

## Interview Traps

### What is a GitHub Actions context?

A context is a structured collection of runtime information exposed to workflow expressions.

### What is the difference between `github` and `github.event`?

`github` contains general workflow and repository execution information.

`github.event` contains the payload for the specific triggering event.

### What is the difference between `env` and `vars`?

`env` represents environment variables configured for workflow execution.

`vars` represents GitHub configuration variables available through the relevant scopes.

### What is the difference between `steps` and `needs`?

`steps` provides information and outputs from steps in the current job.

`needs` provides results and outputs from dependent jobs.

### How do you pass data from one job to another?

Use:

```text
$GITHUB_OUTPUT
    ↓
step output
    ↓
job output
    ↓
needs.<job>.outputs.<name>
```

### What is the `matrix` context?

It contains the current combination of values for a matrix job.

### Why can `github.event.pull_request` be unavailable?

Because the workflow may have been triggered by an event that does not contain pull-request data, such as `push`.

### Why should branch names be treated as untrusted?

Repository contributors can control branch names, so directly embedding them into shell commands can create command-injection risk.

### Why use `runner` context?

It exposes execution-environment information such as operating system and architecture, which is useful for portable and multi-platform workflows.

### Why are contexts important in production CI/CD?

They connect workflow metadata, configuration, secrets, job dependencies, matrix execution, outputs, and deployment decisions without hard-coding environment-specific values.

---

## Production Design Example

A production backend pipeline can combine the major contexts as follows:

```yaml
name: Backend CI/CD

on:
  pull_request:
    branches:
      - main

  push:
    branches:
      - main

  workflow_dispatch:
    inputs:
      environment:
        description: Deployment environment
        required: true
        type: choice
        options:
          - staging
          - production

permissions:
  contents: read

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

    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install dependencies
        run: python -m pip install -r requirements.txt

      - name: Run tests
        env:
          APP_ENV: test
        run: python -m pytest

  build:
    needs: test
    if: ${{ needs.test.result == 'success' }}
    runs-on: ubuntu-latest

    outputs:
      image-tag: ${{ steps.metadata.outputs.image-tag }}

    steps:
      - uses: actions/checkout@v5

      - name: Generate image metadata
        id: metadata
        run: echo "image-tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

      - name: Build image
        env:
          IMAGE_TAG: ${{ steps.metadata.outputs.image-tag }}
        run: docker build -t "backend:${IMAGE_TAG}" .

  deploy:
    needs: build

    if: >-
      ${{
        github.event_name == 'workflow_dispatch' &&
        needs.build.result == 'success'
      }}

    runs-on: ubuntu-latest

    environment:
      name: ${{ inputs.environment }}

    concurrency:
      group: deployment-${{ inputs.environment }}
      cancel-in-progress: false

    permissions:
      contents: read
      id-token: write

    steps:
      - name: Deploy
        env:
          IMAGE_TAG: ${{ needs.build.outputs.image-tag }}
          AWS_REGION: ${{ vars.AWS_REGION }}
        run: |
          echo "Deploying ${IMAGE_TAG}"
          echo "AWS region: ${AWS_REGION}"
          ./scripts/deploy.sh "${inputs_environment}"
```

The deployment example demonstrates the major context categories:

```text
github
  |
  +-- event_name

inputs
  |
  +-- environment

needs
  |
  +-- build.outputs.image-tag

vars
  |
  +-- AWS_REGION

matrix
  |
  +-- python-version

runner
  |
  +-- execution environment

secrets
  |
  +-- protected credentials when required
```

In a real deployment workflow, the environment value should be consumed consistently through the `inputs` context or an explicitly defined environment variable rather than relying on an undefined shell variable.

---

## Context Architecture

A useful senior-level mental model is to treat contexts as different data domains.

```mermaid
flowchart TB
    subgraph Event
        E[GitHub Event]
        G[github Context]
    end

    subgraph Configuration
        V[vars Context]
        S[secrets Context]
        I[inputs Context]
        ENV[env Context]
    end

    subgraph Execution
        R[runner Context]
        M[matrix Context]
        ST[strategy Context]
        J[job Context]
    end

    subgraph WorkflowData
        STEP[steps Context]
        NEEDS[needs Context]
    end

    E --> G
    G --> X[Expression Evaluation]
    V --> X
    S --> X
    I --> X
    ENV --> X

    X --> STEP
    STEP --> NEEDS

    R --> X
    M --> X
    ST --> X
    J --> X

    NEEDS --> D[Deployment / Build / Test]
    X --> D
```

The important architectural distinction is:

```text
Contexts
    ↓
provide information

Expressions
    ↓
evaluate information

Outputs
    ↓
move workflow data

Environment variables
    ↓
provide process configuration

Permissions / environments
    ↓
control authority
```

These mechanisms complement each other but should not be treated as interchangeable.

---

## Key Takeaways

- GitHub Actions contexts provide structured runtime data such as repository metadata, event payloads, variables, secrets, job results, matrix values, runner information, and workflow inputs.
- `github`, `steps`, `needs`, `matrix`, `strategy`, `runner`, `inputs`, `env`, `vars`, and `secrets` serve different data-flow responsibilities and are not interchangeable.
- Use `$GITHUB_OUTPUT` and job outputs with `needs` for explicit cross-step and cross-job data flow; use environment variables for process-level configuration.
- Treat event payloads, branch names, pull-request metadata, and workflow inputs as potentially untrusted data, especially when constructing shell commands or using sensitive permissions.
- Production workflows should combine contexts with least-privilege permissions, protected environments, immutable artifacts, explicit dependencies, and controlled deployment boundaries.