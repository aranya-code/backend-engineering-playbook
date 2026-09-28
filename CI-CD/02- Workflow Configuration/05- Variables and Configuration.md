# 05- Variables and Configuration

## Overview

GitHub Actions variables and configuration mechanisms control how workflows receive environment-specific settings, runtime values, secrets, generated outputs, and deployment configuration.

For production CI/CD, configuration should be separated from workflow logic wherever practical. A Python, Django, or FastAPI pipeline should not need to duplicate configuration for development, staging, and production. Instead, workflows should consume repository or organization variables for non-sensitive configuration, secrets for sensitive values, environments for deployment-specific controls, and environment/output mechanisms for values generated during execution.

The main configuration mechanisms are:

| Mechanism | Primary purpose | Sensitive data | Typical scope |
|---|---|---:|---|
| `env` | Runtime environment variables | No | Workflow, job, step |
| `vars` | Non-secret configuration variables | No | Organization, repository, environment |
| `secrets` | Sensitive configuration | Yes | Organization, repository, environment |
| `$GITHUB_ENV` | Pass environment variables to later steps | No | Current job |
| `$GITHUB_OUTPUT` | Pass generated values between steps/jobs | No | Step/job |
| `$GITHUB_PATH` | Extend executable search path | No | Current job |
| Environments | Deployment-specific configuration and protection | Can contain secrets | Environment |
| Artifacts | Persist files between jobs/runs | Not inherently secure | Workflow/run |
| Cache | Reuse dependencies/build data | Not a secret store | Repository/workflow |

A useful production model is:

```text
                    GitHub Repository
                           |
          +----------------+----------------+
          |                |                |
       Workflow          vars            secrets
          |                |                |
          +----------------+----------------+
                           |
                    Job / Environment
                           |
          +----------------+----------------+
          |                |                |
       env vars       $GITHUB_ENV     $GITHUB_OUTPUT
          |                |                |
          +----------------+----------------+
                           |
                    Application / Deploy
```

The important distinction is that **configuration values, secrets, generated runtime values, and persisted files solve different problems**. Treating them as interchangeable creates security, reliability, and maintainability problems.

## Configuration Model

A production workflow typically has several configuration layers.

```text
Organization Configuration
        |
        v
Repository Configuration
        |
        v
Environment Configuration
        |
        v
Workflow / Job / Step Configuration
        |
        v
Runtime-generated Configuration
        |
        v
Application / Deployment
```

For example, an organization may define common settings such as AWS regions, while a repository defines application-specific settings and the production environment contains production deployment configuration and secrets.

### Static vs Runtime Configuration

Static configuration is known before the workflow starts.

Examples:

```yaml
env:
  PYTHON_VERSION: "3.12"
  AWS_REGION: "ap-south-1"
```

Runtime configuration is generated during execution.

Examples:

- Docker image digest
- generated version
- artifact name
- database connection information
- dynamically generated matrix
- deployment revision

Runtime values should generally be passed through supported GitHub Actions mechanisms such as `$GITHUB_OUTPUT` rather than being encoded into workflow source.

## Environment Variables

The `env` keyword defines environment variables available to workflow processes.

GitHub Actions supports three primary `env` scopes:

- Workflow
- Job
- Step

### Workflow-Level Environment Variables

Workflow-level variables apply to jobs and steps unless overridden by a more specific `env` declaration.

```yaml
name: Backend CI

on:
  push:
    branches:
      - main

env:
  PYTHON_VERSION: "3.12"
  PYTHONUNBUFFERED: "1"

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Run tests
        run: pytest
```

Workflow-level configuration is useful for values shared by most or all jobs.

Avoid placing large amounts of configuration at this level when only one job needs it. Excessive global state makes workflows harder to reason about.

### Job-Level Environment Variables

A job can define variables specific to that job.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    env:
      DJANGO_SETTINGS_MODULE: config.settings.test
      PYTHONUNBUFFERED: "1"

    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        run: pytest
```

This is useful when configuration belongs to a specific lifecycle stage.

For example:

```text
lint job       -> lint-specific configuration
test job       -> test configuration
build job      -> build configuration
deploy job     -> deployment configuration
```

### Step-Level Environment Variables

A step can define highly localized configuration.

```yaml
- name: Run migration check
  env:
    DJANGO_SETTINGS_MODULE: config.settings.ci
  run: python manage.py check --deploy
```

Step-level configuration is preferable when the variable should not be available to unrelated commands in the job.

### Environment Variable Scope

For `env` declarations, the effective value is determined by the most specific applicable scope:

```text
Step
  |
Job
  |
Workflow
```

For example:

```yaml
env:
  APP_MODE: production

jobs:
  deploy:
    env:
      APP_MODE: staging

    steps:
      - name: Show mode
        env:
          APP_MODE: canary
        run: echo "$APP_MODE"
```

The step prints:

```text
canary
```

Keep this hierarchy predictable. Excessive overriding creates configuration drift and makes debugging difficult.

## `vars` Context

GitHub Actions configuration variables are exposed through the `vars` context.

They are designed for **non-sensitive configuration** that should not be embedded directly in workflow YAML.

Example:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Deploy
        run: ./scripts/deploy.sh
        env:
          AWS_REGION: ${{ vars.AWS_REGION }}
          ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
```

Typical configuration variables include:

- AWS region
- ECR repository name
- deployment role name
- application identifier
- environment name
- feature flags
- non-sensitive endpoints
- infrastructure identifiers

Do not use `vars` for passwords, tokens, private keys, database credentials, or other sensitive information.

### Organization, Repository, and Environment Variables

Configuration variables can exist at different administrative scopes.

| Scope | Typical use |
|---|---|
| Organization | Shared configuration across repositories |
| Repository | Application-specific configuration |
| Environment | Deployment-specific configuration |

A production environment can therefore provide configuration different from staging without changing workflow source.

```text
Organization
    |
    +-- shared configuration
            |
Repository
    |
    +-- application configuration
            |
Environment
    |
    +-- staging / production configuration
```

Environment-level configuration is particularly useful when the same deployment workflow promotes an artifact through multiple environments.

## `vars` vs `env`

These mechanisms solve different problems.

| Feature | `env` | `vars` |
|---|---|---|
| Defined in workflow YAML | Yes | Usually configured in GitHub |
| Sensitive values | No | No |
| Runtime environment variable | Yes | Only after being referenced/exported |
| Centralized configuration | Limited | Strong |
| Environment-specific values | Possible through environment/job configuration | Native environment scope |
| Good for reusable workflow configuration | Sometimes | Yes |
| Good for generated runtime values | No | No |

For example:

```yaml
env:
  PYTHON_VERSION: "3.12"
```

defines a workflow environment variable directly.

Whereas:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
```

takes a centrally managed configuration variable and exposes it to the process as an environment variable.

Do not treat `vars` as a replacement for `$GITHUB_ENV`. `vars` is configuration; `$GITHUB_ENV` is a runtime mechanism for passing environment variables between steps.

## Secrets

Secrets are intended for sensitive values.

Typical examples include:

- database passwords
- API tokens
- private keys
- third-party credentials
- deployment credentials
- webhook secrets
- cloud credentials where OIDC is not available

Secrets are referenced through the `secrets` context.

```yaml
- name: Run application tests
  env:
    DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
  run: pytest
```

Avoid embedding secrets directly into commands.

Prefer:

```yaml
- name: Deploy
  env:
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
  run: ./scripts/deploy.sh
```

over:

```yaml
- name: Deploy
  run: ./scripts/deploy.sh --token "${{ secrets.DEPLOY_TOKEN }}"
```

Passing sensitive values through environment variables reduces accidental exposure through command-line inspection and process diagnostics, although it does not eliminate all exposure risks.

## Secret Scopes

Secrets can be managed at different levels.

| Scope | Purpose |
|---|---|
| Organization | Shared credentials where centralized governance is appropriate |
| Repository | Repository-specific credentials |
| Environment | Deployment-specific credentials |

Environment secrets are especially useful for production deployments.

```text
CI
 |
 +-- test
 |
 +-- build
 |
 +-- staging deployment
 |
 +-- production deployment
          |
          +-- production secrets
```

A test job should not receive production secrets simply because a production deployment exists elsewhere in the workflow.

Apply the principle:

> Give each job only the secrets it actually needs.

## Secret Masking

GitHub Actions attempts to mask registered secret values in logs.

However, masking should not be treated as a complete data-loss-prevention mechanism.

Avoid:

```yaml
- name: Debug
  run: echo "${{ secrets.API_TOKEN }}"
```

Even when masking occurs, exposing secrets to command output is poor operational practice.

Also avoid transforming secrets and assuming the transformed representation will necessarily be masked.

For example:

```text
secret
  |
  +-- base64 encoding
  |
  +-- substring extraction
  |
  +-- hashing
  |
  +-- serialization
```

The transformed value may not match the original secret value known to the masking system.

### Secret Exposure Rules

Avoid:

- printing secrets
- storing secrets in artifacts
- writing secrets into build logs
- committing secrets to repositories
- embedding secrets into Docker images
- passing secrets unnecessarily to third-party actions
- exposing secrets to untrusted pull request code

Treat every command that receives a secret as trusted code.

## `secrets: inherit`

Reusable workflows can receive secrets explicitly or inherit secrets.

Example:

```yaml
jobs:
  deploy:
    uses: acme/platform-workflows/.github/workflows/deploy.yml@v1
    secrets: inherit
```

`secrets: inherit` can simplify organization-wide reusable workflows, but it should not be used indiscriminately.

A reusable deployment workflow should request only the secrets it actually requires whenever practical.

Explicit secret passing provides a clearer security contract:

```yaml
jobs:
  deploy:
    uses: acme/platform-workflows/.github/workflows/deploy.yml@v1
    secrets:
      AWS_DEPLOY_ROLE: ${{ secrets.AWS_DEPLOY_ROLE }}
```

For sensitive production workflows, explicit contracts are generally easier to audit.

## GitHub Environments

GitHub Environments represent deployment targets such as:

- development
- staging
- production

An environment can provide:

- environment variables
- environment secrets
- required reviewers
- deployment protection rules
- deployment history
- branch/tag restrictions

A deployment job references an environment:

```yaml
jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment:
      name: production

    steps:
      - name: Deploy
        run: ./scripts/deploy.sh
```

This creates a useful security boundary around production deployment configuration.

## Environment Protection

Production environments can require human approval before deployment proceeds.

A typical flow is:

```text
Build
  |
  v
Artifact
  |
  v
Staging
  |
  v
Validation
  |
  v
Production Environment
  |
  v
Required Approval
  |
  v
Production Deployment
```

Environment protection is useful when:

- production deployments require approval
- infrastructure changes need review
- regulated workloads require controlled promotion
- deployment separation is required

Approval should be treated as a deployment control, not as a substitute for automated validation.

## Deployment History

Environment deployment history provides operational context for answering questions such as:

- What was deployed?
- When was it deployed?
- Which workflow performed the deployment?
- Which commit or artifact was promoted?
- Which environment was affected?

A reliable deployment pipeline should make the deployed version traceable to source control and build artifacts.

## Environment Restrictions

Production environments can restrict which branches or tags can deploy.

For example:

```text
Pull request
    |
    X
production

main
    |
    v
production
```

This prevents arbitrary branches from directly deploying production workloads.

For release-oriented systems, a production environment may instead accept signed or protected release tags.

## Configuration Precedence

Configuration should be designed so that the source of a value is obvious.

A practical model is:

```text
Central configuration
        |
        v
Environment-specific configuration
        |
        v
Workflow/job/step configuration
        |
        v
Runtime-generated values
```

Do not create multiple sources for the same logical configuration unless there is a clear precedence rule.

For example, avoid having all of these independently define an AWS region:

```text
workflow YAML
repository variable
environment variable
shell script
Python settings module
Docker ENV
```

This creates configuration drift.

Prefer one authoritative source and explicitly pass the value into downstream systems.

## Runtime Configuration with `$GITHUB_ENV`

`$GITHUB_ENV` allows one step to create an environment variable for subsequent steps in the same job.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Generate version
        run: echo "APP_VERSION=${GITHUB_SHA::12}" >> "$GITHUB_ENV"

      - name: Use version
        run: echo "Building version $APP_VERSION"
```

The variable becomes available to later steps in the same job.

It is **not available to the step that writes it**.

For example:

```yaml
- name: Set variable
  run: |
    echo "APP_VERSION=1.2.3" >> "$GITHUB_ENV"
    echo "$APP_VERSION"
```

The current step does not receive the newly written value.

The correct pattern is:

```yaml
- name: Set variable
  run: echo "APP_VERSION=1.2.3" >> "$GITHUB_ENV"

- name: Use variable
  run: echo "$APP_VERSION"
```

### When to Use `$GITHUB_ENV`

Use `$GITHUB_ENV` when:

- multiple later steps in the same job need a value
- the value is runtime-generated
- the value naturally belongs in the process environment

Do not use it to transfer values between jobs. Use `$GITHUB_OUTPUT` and job outputs for that.

## Runtime Outputs with `$GITHUB_OUTPUT`

`$GITHUB_OUTPUT` communicates generated values from one step to later workflow logic.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      image_tag: ${{ steps.metadata.outputs.image_tag }}

    steps:
      - name: Generate image tag
        id: metadata
        run: echo "image_tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

      - name: Display tag
        run: echo "Image tag is ${{ steps.metadata.outputs.image_tag }}"
```

The job output can then be consumed by another job:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      image_tag: ${{ steps.metadata.outputs.image_tag }}

    steps:
      - id: metadata
        run: echo "image_tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - name: Deploy image
        run: echo "Deploying ${{ needs.build.outputs.image_tag }}"
```

The data flow is:

```text
Step
  |
  | $GITHUB_OUTPUT
  v
Step Output
  |
  v
Job Output
  |
  | needs.<job>.outputs
  v
Dependent Job
```

## Structured Outputs

Complex configuration can be serialized as JSON.

```yaml
jobs:
  metadata:
    runs-on: ubuntu-latest

    outputs:
      config: ${{ steps.generate.outputs.config }}

    steps:
      - id: generate
        run: |
          CONFIG='{"python":["3.11","3.12"],"database":["postgres","mysql"]}'
          echo "config=$CONFIG" >> "$GITHUB_OUTPUT"
```

The downstream job can deserialize it with `fromJSON()`.

```yaml
strategy:
  matrix: ${{ fromJSON(needs.metadata.outputs.config) }}
```

This is useful for dynamically generating matrix configurations without duplicating workflow configuration.

## `$GITHUB_PATH`

`$GITHUB_PATH` adds directories to the executable search path for subsequent steps.

```yaml
- name: Add tools to PATH
  run: echo "$HOME/.local/bin" >> "$GITHUB_PATH"

- name: Verify tool
  run: my-tool --version
```

Use this when a tool is installed into a directory that is not already in `PATH`.

Avoid modifying `PATH` globally unless there is a clear reason. Unexpected path changes can cause a workflow to execute a different binary than intended.

## Step Summaries

GitHub Actions supports step summaries through `$GITHUB_STEP_SUMMARY`.

```yaml
- name: Publish test summary
  run: |
    {
      echo "## Test Results"
      echo ""
      echo "- Tests: 842"
      echo "- Failed: 0"
      echo "- Coverage: 94.2%"
    } >> "$GITHUB_STEP_SUMMARY"
```

Step summaries are useful for:

- test summaries
- deployment information
- image identifiers
- coverage
- generated reports
- operational metadata

They are preferable to flooding raw logs with large amounts of repetitive information.

## Annotations and Logging Commands

GitHub Actions provides workflow commands for communicating structured information to the Actions runtime.

For example:

```bash
echo "::warning file=app.py,line=42::Deprecated API usage"
```

Errors can be reported similarly:

```bash
echo "::error file=app.py,line=42::Validation failed"
```

Use annotations for actionable diagnostics rather than generating large amounts of unstructured output.

Modern workflows should use supported environment files such as:

```text
$GITHUB_ENV
$GITHUB_OUTPUT
$GITHUB_PATH
$GITHUB_STEP_SUMMARY
```

Avoid deprecated workflow command mechanisms for passing values.

## Configuration for Python Applications

A Python backend should generally distinguish:

```text
GitHub Actions configuration
        |
        v
Process environment
        |
        v
Python application configuration
        |
        v
Django / FastAPI
```

For example:

```yaml
- name: Run Django tests
  env:
    DJANGO_SETTINGS_MODULE: config.settings.ci
    DATABASE_URL: ${{ secrets.CI_DATABASE_URL }}
    REDIS_URL: redis://redis:6379/0
  run: pytest
```

The Python application can then read these values from its runtime environment.

For FastAPI:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
```

For larger applications, a typed configuration layer such as Pydantic Settings can provide stronger validation and clearer configuration contracts.

The workflow should supply configuration; application code should validate and interpret it.

## Django Environment Configuration

A common Django structure is:

```text
config/
    settings/
        base.py
        ci.py
        staging.py
        production.py
```

GitHub Actions can select the appropriate configuration:

```yaml
env:
  DJANGO_SETTINGS_MODULE: config.settings.ci
```

Sensitive configuration should remain outside the repository:

```yaml
env:
  SECRET_KEY: ${{ secrets.DJANGO_SECRET_KEY }}
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

Do not commit production `SECRET_KEY`, database credentials, or third-party API tokens.

## FastAPI Environment Configuration

FastAPI applications commonly separate deployment configuration from application code.

```yaml
- name: Run API tests
  env:
    APP_ENV: ci
    DATABASE_URL: postgresql://postgres:postgres@postgres:5432/app
    REDIS_URL: redis://redis:6379/0
  run: pytest
```

For production, the same application image can receive different runtime configuration:

```text
Same image
   |
   +-- staging environment
   |
   +-- production environment
```

This supports immutable deployment practices.

## Docker and Configuration

A critical production principle is to avoid baking environment-specific secrets into Docker images.

Avoid:

```dockerfile
ENV DATABASE_PASSWORD=production-password
```

Instead:

```text
Docker image
    |
    | runtime configuration
    v
Container
    |
    +-- DATABASE_URL
    +-- REDIS_URL
    +-- APP_ENV
```

For example, an ECS task definition, Kubernetes Deployment, or another runtime platform can inject configuration when the container starts.

This allows the same immutable image to be promoted between environments.

## Configuration and Immutable Deployments

A production deployment should ideally separate:

```text
Artifact
+
Configuration
+
Environment
```

rather than building a different artifact for every environment.

Preferred:

```text
Git commit
    |
    v
Build
    |
    v
Immutable Docker image
    |
    +----------+
    |          |
    v          v
 Staging   Production
    |          |
 staging     production
 config       config
```

Avoid:

```text
Build staging image
        |
        v
Build production image
```

because rebuilding can introduce differences unrelated to configuration.

The goal is:

> Build once, configure per environment, promote the same artifact.

## AWS Configuration

GitHub Actions often needs AWS configuration for deployment.

A secure modern pattern is OIDC-based authentication.

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Verify identity
        run: aws sts get-caller-identity
```

The workflow does not need a long-lived AWS access key when OIDC is configured correctly.

A useful configuration split is:

```text
vars
 |
 +-- AWS_REGION
 +-- ECR_REPOSITORY
 +-- AWS_DEPLOY_ROLE

secrets
 |
 +-- third-party credentials
 +-- application secrets

OIDC
 |
 +-- temporary AWS credentials
```

The AWS IAM role should trust only the intended GitHub repository, branch, environment, or other appropriate workflow identity constraints.

## Configuration and ECR/ECS

A production deployment may use:

```text
GitHub Actions
      |
      | OIDC
      v
AWS STS
      |
      v
IAM Role
      |
      +------------------+
      |                  |
      v                  v
     ECR                ECS
      |                  |
 Docker image       Task definition
                         |
                         v
                    Runtime config
```

The image should remain environment-independent.

For example:

```text
Image:
  123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend@sha256:...

Configuration:
  DATABASE_URL
  REDIS_URL
  APP_ENV=production
```

This makes rollback safer because configuration and artifact identity can be reasoned about separately.

## Containers and Service Configuration

Integration tests often require PostgreSQL and Redis.

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: app
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U postgres -d app"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip

      - run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/app
          REDIS_URL: redis://localhost:6379/0
        run: pytest
```

Configuration here has two roles:

1. Configure the service containers.
2. Configure the application under test.

Keep those responsibilities explicit.

## Matrix Configuration

Configuration variables can be combined with matrix strategies.

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

The resulting test combinations are:

```text
Python 3.11 + PostgreSQL
Python 3.11 + MySQL
Python 3.12 + PostgreSQL
Python 3.12 + MySQL
```

Matrix configuration should remain manageable. Large Cartesian products can multiply runner consumption and CI cost rapidly.

## Dynamic Matrix Configuration

A configuration-producing job can generate JSON:

```yaml
jobs:
  generate-matrix:
    runs-on: ubuntu-latest

    outputs:
      matrix: ${{ steps.matrix.outputs.matrix }}

    steps:
      - id: matrix
        run: |
          MATRIX='{"python-version":["3.11","3.12"],"database":["postgres","mysql"]}'
          echo "matrix=$MATRIX" >> "$GITHUB_OUTPUT"

  test:
    needs: generate-matrix
    runs-on: ubuntu-latest

    strategy:
      matrix: ${{ fromJSON(needs.generate-matrix.outputs.matrix) }}

    steps:
      - name: Show configuration
        run: |
          echo "Python: ${{ matrix.python-version }}"
          echo "Database: ${{ matrix.database }}"
```

This pattern is useful when supported configuration is generated from another source.

Do not introduce dynamic matrices merely to avoid writing a small static matrix. Static configuration is easier to review and troubleshoot.

## Configuration and Reusable Workflows

Reusable workflows should expose configuration through explicit inputs.

```yaml
on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string
      environment:
        required: true
        type: string
    secrets:
      DEPLOY_TOKEN:
        required: true
```

A caller can provide:

```yaml
jobs:
  deploy:
    uses: ./.github/workflows/deploy.yml
    with:
      python-version: "3.12"
      environment: production
    secrets:
      DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

This creates a clear contract:

```text
Caller
  |
  +-- inputs
  +-- secrets
  |
  v
Reusable Workflow
  |
  +-- jobs
  +-- steps
  +-- outputs
```

Avoid hidden dependencies on repository-specific environment variables inside reusable workflows. Reusable components are easier to maintain when their required configuration is explicit.

## Configuration and Composite Actions

Composite actions package reusable steps within a job.

A composite action may accept inputs:

```yaml
name: Setup Python Backend

inputs:
  python-version:
    required: true
    description: Python version

runs:
  using: composite
  steps:
    - uses: actions/setup-python@v6
      with:
        python-version: ${{ inputs.python-version }}

    - shell: bash
      run: pip install -r requirements.txt
```

The distinction is important:

| Mechanism | Configuration interface | Scope |
|---|---|---|
| `env` | Environment variables | Workflow/job/step |
| `vars` | Centralized non-secret values | Org/repository/environment |
| `secrets` | Sensitive values | Org/repository/environment |
| Reusable workflow | Inputs/secrets/outputs | Multiple jobs |
| Composite action | Inputs/environment | Steps within a job |

## Configuration and Concurrency

Deployment configuration often needs concurrency controls.

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

This prevents two production deployments from executing simultaneously.

A more granular approach can include the environment:

```yaml
concurrency:
  group: deploy-${{ github.repository }}-${{ inputs.environment }}
  cancel-in-progress: false
```

This prevents deployments from racing against each other while allowing independent environments to proceed concurrently.

Configuration should therefore include not only application values but also operational controls such as deployment concurrency.

## Security Boundaries

Configuration becomes dangerous when untrusted input crosses into trusted execution.

Potentially attacker-controlled values include:

- pull request titles
- branch names
- commit messages
- issue content
- workflow inputs
- repository dispatch payloads

Avoid:

```yaml
- name: Process PR title
  run: echo "${{ github.event.pull_request.title }}"
```

If the value contains shell metacharacters, direct interpolation can alter the command being executed.

Prefer passing the value through an environment variable:

```yaml
- name: Process PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: |
    printf '%s\n' "$PR_TITLE"
```

For more complex processing, pass structured data to a trusted application or script and validate it there.

## `pull_request` and `pull_request_target`

Configuration becomes especially sensitive for pull requests from forks.

A workflow triggered by:

```yaml
on:
  pull_request:
```

has a different security model from:

```yaml
on:
  pull_request_target:
```

`pull_request_target` executes in the context of the base repository and can have access to repository-level configuration and secrets subject to permissions.

Therefore, do not execute untrusted pull request code with privileged credentials.

A dangerous pattern is:

```text
pull_request_target
       |
       v
checkout attacker-controlled code
       |
       v
execute code
       |
       v
production credentials
```

A safer conceptual separation is:

```text
Untrusted PR
    |
    v
No production secrets
    |
    v
Validation

Trusted base branch
    |
    v
Privileged deployment
    |
    v
Production
```

This is one of the most important configuration security boundaries in GitHub Actions.

## Configuration for Build and Deployment

A production pipeline can separate configuration into stages.

```text
Pull Request
    |
    +-- test configuration
    |
    v
Build
    |
    +-- registry configuration
    |
    v
Staging
    |
    +-- staging configuration
    |
    v
Production
    |
    +-- production configuration
```

The workflow source remains largely identical while environment-specific values change through GitHub Environments and configuration variables.

## Artifact vs Configuration

Artifacts and configuration should not be confused.

An artifact is a build output:

```text
wheel
tarball
coverage report
test report
Docker metadata
deployment manifest
```

Configuration is runtime or workflow input:

```text
AWS_REGION
DATABASE_URL
APP_ENV
deployment role
feature flags
```

A production artifact should not contain environment-specific credentials.

## Artifact Promotion

A robust deployment model is:

```text
Source
  |
  v
Build
  |
  v
Immutable Artifact
  |
  +----------+
  |          |
  v          v
Staging   Production
  |          |
config A   config B
```

The artifact can be identified by:

```text
Git commit SHA
Docker digest
release version
artifact ID
```

This makes rollback deterministic.

For Docker:

```text
backend:git-8f3c1d2
```

or, preferably for immutable deployment:

```text
backend@sha256:<digest>
```

Configuration should identify the environment, not mutate the artifact.

## Configuration and Caching

Caches should never be treated as authoritative configuration.

For example:

```yaml
- uses: actions/setup-python@v6
  with:
    python-version: "3.12"
    cache: pip
```

Caching improves performance but must not change correctness.

A cache miss should produce the same correct build as a cache hit.

This principle is important for:

- pip dependencies
- npm dependencies
- Docker layers
- build tools
- compiled dependencies

Do not store secrets or deployment credentials in caches.

## Configuration and Reliability

Configuration failures often cause production incidents because the application itself may be healthy while its runtime configuration is incorrect.

Examples:

```text
Correct application
+
Wrong database URL
=
Failed deployment
```

```text
Correct image
+
Wrong AWS region
=
Deployment to wrong resource
```

```text
Correct deployment
+
Wrong Redis URL
=
Runtime failure
```

Validate critical configuration before deployment.

For example:

```yaml
- name: Validate deployment configuration
  env:
    AWS_REGION: ${{ vars.AWS_REGION }}
    ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
  run: |
    test -n "$AWS_REGION"
    test -n "$ECR_REPOSITORY"
```

For stronger validation, use a dedicated configuration validation script.

## Configuration Drift

Configuration drift occurs when environments gradually stop matching the intended configuration model.

Common causes include:

- manually changed environment variables
- duplicated configuration
- undocumented repository variables
- different secret names
- inconsistent environment setup
- hardcoded values in scripts
- environment-specific workflow branches
- stale deployment settings

A production configuration inventory should identify:

```text
Variable
Source
Scope
Sensitive?
Consumer
Owner
Rotation requirement
```

Example:

| Variable | Source | Scope | Sensitive | Consumer |
|---|---|---|---:|---|
| `AWS_REGION` | `vars` | Environment | No | Deployment |
| `ECR_REPOSITORY` | `vars` | Repository | No | Docker |
| `AWS_DEPLOY_ROLE` | `vars` | Environment | No | OIDC |
| `DATABASE_URL` | `secrets` | Environment | Yes | Application |
| `DJANGO_SECRET_KEY` | `secrets` | Environment | Yes | Django |

## Monitoring Configuration Failures

CI/CD observability should make configuration failures diagnosable without exposing sensitive values.

Useful information includes:

```text
Environment name
Commit SHA
Artifact digest
Workflow run ID
Job name
Deployment ID
AWS account identifier where appropriate
AWS region
Configuration source
```

Do not log:

```text
Database passwords
API tokens
Private keys
Session credentials
Secret values
```

A useful deployment summary might contain:

```text
Environment: production
Version: 8f3c1d2
Image: backend@sha256:...
AWS Region: ap-south-1
Deployment: ECS service update
```

This gives operators enough context to investigate without exposing credentials.

## Configuration and Disaster Recovery

Disaster recovery requires configuration to be reproducible.

A recovery process should be able to reconstruct:

```text
Source revision
      +
Artifact
      +
Infrastructure definition
      +
Environment configuration
      +
Secrets
      =
Recoverable deployment
```

Secrets should be stored in managed systems with appropriate backup and recovery procedures rather than only existing in an engineer's local environment.

For infrastructure managed by Terraform or CloudFormation, keep configuration and infrastructure definitions version-controlled.

## Production Configuration Checklist

Before production deployment, verify:

- Non-sensitive configuration is stored in appropriate variables.
- Sensitive values are stored as secrets.
- Production secrets are scoped to the production environment.
- Deployment jobs reference the correct environment.
- Required reviewers are configured where appropriate.
- AWS authentication uses OIDC where supported.
- IAM permissions follow least privilege.
- Critical configuration values are validated.
- Secrets are not printed in logs.
- Secrets are not baked into Docker images.
- Runtime configuration is separated from immutable artifacts.
- Deployment configuration is traceable.
- Configuration changes are auditable.
- Rollback does not require rebuilding the application.
- Configuration required for recovery is documented.

## Common Mistakes and Pitfalls

### Hardcoding Secrets

Bad:

```yaml
env:
  DATABASE_PASSWORD: "production-password"
```

Why it is dangerous:

- credentials enter source control
- repository history retains the value
- code review exposes the value
- rotation becomes difficult

Use GitHub Secrets or an external secret-management system instead.

### Using `env` as a Secret Store

Bad:

```yaml
env:
  AWS_ACCESS_KEY_ID: ...
  AWS_SECRET_ACCESS_KEY: ...
```

Environment variables are a transport mechanism, not a secure secret-management system.

Use the `secrets` context or OIDC.

### Sharing Production Secrets with Test Jobs

Avoid giving every job all secrets.

Bad architecture:

```text
Every job
   |
   +-- production secrets
   +-- staging secrets
   +-- deployment credentials
```

Prefer:

```text
Test
  |
  +-- test configuration

Build
  |
  +-- registry permissions if required

Production Deploy
  |
  +-- production configuration
  +-- production credentials
```

### Rebuilding for Every Environment

Bad:

```text
Build staging image
Build production image
```

This can produce different artifacts.

Prefer:

```text
Build once
    |
    v
Immutable artifact
    |
    +-- staging
    +-- production
```

### Overusing `$GITHUB_ENV`

Do not use `$GITHUB_ENV` for every value.

Use:

- `env` for declarative configuration
- `vars` for centralized non-secret configuration
- `secrets` for sensitive configuration
- `$GITHUB_ENV` for runtime environment values
- `$GITHUB_OUTPUT` for step/job data flow

### Using `$GITHUB_ENV` Across Jobs

`$GITHUB_ENV` does not provide cross-job communication.

Incorrect assumption:

```text
Job A
  |
  +-- $GITHUB_ENV
       |
       v
Job B
```

Use:

```text
Job A
  |
  +-- $GITHUB_OUTPUT
       |
       v
Job Output
       |
       v
Job B via needs
```

### Logging Configuration

Avoid debugging configuration with:

```bash
env
```

or:

```bash
printenv
```

because secrets may be present in the process environment.

Instead, print only safe metadata:

```bash
echo "Environment: $APP_ENV"
echo "Region: $AWS_REGION"
```

### Configuration Duplication

If the same value appears in:

```text
workflow YAML
Dockerfile
shell script
Python settings
Terraform
GitHub variable
```

determine which system owns the value and pass it explicitly.

## Troubleshooting Configuration

Use a failure-domain model rather than changing configuration randomly.

| Symptom | Possible causes | Isolation strategy |
|---|---|---|
| Variable is empty | Wrong scope or name | Inspect context and scope |
| Secret unavailable | Environment not referenced | Verify `environment:` |
| Wrong value | Override or duplicate source | Trace configuration precedence |
| Value missing in next step | Step-local variable | Use `$GITHUB_ENV` |
| Value missing in next job | Used `$GITHUB_ENV` | Use job outputs |
| AWS deployment fails | Wrong region/role | Verify `vars`, OIDC, STS |
| Docker image has wrong config | Build-time configuration | Inspect image build process |
| Production uses staging settings | Environment mismatch | Verify environment assignment |
| Secret appears in logs | Explicit output/transformation | Remove logging and review command |

### Safe Diagnostic Commands

Check safe variables:

```bash
echo "APP_ENV=$APP_ENV"
echo "AWS_REGION=$AWS_REGION"
```

Verify AWS identity:

```bash
aws sts get-caller-identity
```

Verify AWS configuration:

```bash
aws configure list
```

Do not dump credential values.

For workflow diagnostics, inspect:

- workflow run logs
- job logs
- step summaries
- environment configuration
- repository variables
- environment variables
- secret availability
- job permissions
- reusable workflow inputs
- job outputs
- deployment history

## Senior-Level Configuration Architecture

A mature GitHub Actions configuration architecture can be modeled as:

```mermaid
flowchart TD
    A[Git Repository] --> B[Workflow]
    B --> C[Configuration Layer]

    C --> D[Organization Variables]
    C --> E[Repository Variables]
    C --> F[Environment Variables]
    C --> G[Secrets]

    B --> H[Runtime Layer]
    H --> I[env]
    H --> J[GITHUB_ENV]
    H --> K[GITHUB_OUTPUT]

    C --> H

    H --> L[Build]
    H --> M[Test]
    H --> N[Deploy]

    G --> N
    F --> N

    N --> O[Staging]
    N --> P[Production]
```

The architecture should preserve clear boundaries:

```text
Non-sensitive static configuration
        -> vars

Sensitive configuration
        -> secrets

Deployment-specific configuration
        -> environment

Runtime-generated environment values
        -> GITHUB_ENV

Cross-step/job data
        -> GITHUB_OUTPUT

Persistent files
        -> artifacts

Performance optimization
        -> caches
```

## Production Pipeline Example

The following illustrates how these mechanisms fit into a Python backend pipeline.

```yaml
name: Backend CI/CD

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

env:
  PYTHON_VERSION: "3.12"

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: app
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U postgres -d app"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v6
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/app
          REDIS_URL: redis://localhost:6379/0
        run: pytest --cov=. --cov-report=xml

      - name: Publish coverage summary
        run: |
          echo "## Test Results" >> "$GITHUB_STEP_SUMMARY"
          echo "Coverage report generated." >> "$GITHUB_STEP_SUMMARY"

  build:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: test
    runs-on: ubuntu-latest

    outputs:
      image_tag: ${{ steps.metadata.outputs.image_tag }}

    steps:
      - uses: actions/checkout@v4

      - id: metadata
        name: Generate image tag
        run: echo "image_tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

      - name: Build image
        env:
          IMAGE_TAG: ${{ steps.metadata.outputs.image_tag }}
        run: docker build -t "backend:${IMAGE_TAG}" .

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest

    environment:
      name: production

    concurrency:
      group: production-deployment
      cancel-in-progress: false

    permissions:
      contents: read
      id-token: write

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Show deployment metadata
        run: |
          echo "Image tag: ${{ needs.build.outputs.image_tag }}"
          echo "AWS region: ${{ vars.AWS_REGION }}"

      - name: Verify AWS identity
        run: aws sts get-caller-identity

      - name: Deploy
        env:
          IMAGE_TAG: ${{ needs.build.outputs.image_tag }}
          ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
        run: |
          echo "Deploying ${ECR_REPOSITORY}:${IMAGE_TAG}"
```

The example demonstrates the separation between:

```text
Workflow configuration
    |
    +-- env
    +-- vars
    +-- secrets
    +-- environment
    +-- outputs
    +-- concurrency

Runtime infrastructure
    |
    +-- PostgreSQL
    +-- Redis
    +-- AWS
    +-- ECR/ECS
```

A production implementation would additionally include image publishing, vulnerability scanning, immutable artifact promotion, deployment health checks, and rollback handling.

## Configuration Design Principles

### Single Source of Truth

Every important configuration value should have an identifiable owner.

```text
AWS region       -> GitHub variable
Database secret  -> environment secret
Image digest     -> build output
Runtime config   -> deployment environment
Application code -> repository
```

### Least Privilege

Configuration access should follow job responsibility.

```text
Lint
  -> no secrets

Unit Tests
  -> test configuration only

Build
  -> registry permissions if required

Production Deploy
  -> production configuration
  -> production deployment identity
```

### Immutable Artifacts

Do not modify an artifact because it is being promoted to another environment.

```text
Artifact
  |
  +-- staging configuration
  |
  +-- production configuration
```

### Explicit Interfaces

Reusable workflows should expose:

```text
Inputs
Secrets
Outputs
```

rather than relying on undocumented repository state.

### Safe Runtime Configuration

Sensitive values should be injected as late as practical:

```text
Workflow
    |
    v
Deployment
    |
    v
Runtime
```

rather than being embedded during source checkout or image construction.

## Interview Traps

### `env` vs `vars`

`env` defines environment variables in workflow configuration. `vars` provides centrally managed non-secret configuration that can be referenced through the `vars` context.

### `$GITHUB_ENV` vs `$GITHUB_OUTPUT`

`$GITHUB_ENV` passes environment variables to later steps in the same job.

`$GITHUB_OUTPUT` produces step outputs that can be exposed as job outputs and consumed by dependent jobs.

### Secrets vs Variables

Variables are intended for non-sensitive configuration. Secrets are intended for sensitive values.

### Artifacts vs Caches

Artifacts preserve workflow outputs for later retrieval or consumption. Caches accelerate repeated work and are not authoritative build outputs or secret storage.

### Why Not Store AWS Keys as Secrets?

Long-lived AWS keys increase credential lifetime and rotation burden. OIDC can exchange a GitHub Actions identity for temporary AWS credentials through STS.

### Why Is `pull_request_target` Dangerous?

It operates with the base repository's security context. Executing untrusted pull request code while exposing privileged secrets or permissions can turn the workflow into a credential-exfiltration path.

### Why Use Environment Protection?

It separates automated CI from controlled deployment promotion and can require approval before production access is granted.

### Why Build Once?

Rebuilding for each environment can produce different artifacts. Promoting the same immutable artifact provides stronger reproducibility and rollback guarantees.

## Senior-Level Production Scenarios

### Scenario: Production Deployments Are Racing

Requirements:

```text
Only one production deployment at a time.
```

Use a production-specific concurrency group:

```yaml
concurrency:
  group: production-deployment
  cancel-in-progress: false
```

Then ensure deployment jobs target the production environment.

### Scenario: Multiple Python Versions

Use a matrix:

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
```

Avoid putting environment-specific secrets into the matrix.

### Scenario: Staging and Production Use the Same Image

Build once:

```text
Git commit
   |
   v
Docker build
   |
   v
Immutable image digest
   |
   +-- staging
   |
   +-- production
```

Only deployment configuration changes.

### Scenario: AWS Credentials Must Not Be Long-Lived

Use:

```text
GitHub Actions
    |
    | OIDC token
    v
AWS STS
    |
    v
Temporary credentials
```

Restrict the IAM trust policy to the intended GitHub identity.

### Scenario: A Reusable CI Pipeline Is Needed

Create a reusable workflow with explicit:

```text
workflow_call
    |
    +-- inputs
    +-- secrets
    +-- outputs
```

Keep repository-specific configuration outside the reusable workflow where practical.

### Scenario: Production Requires Approval

Use a protected GitHub Environment:

```yaml
environment:
  name: production
```

Configure required reviewers and other deployment protection rules at the environment level.

## Key Takeaways

- Use `env` for workflow/job/step runtime variables, `vars` for centralized non-sensitive configuration, and `secrets` for sensitive values.
- Use `$GITHUB_ENV` for environment values within a job and `$GITHUB_OUTPUT` plus job outputs for explicit data flow between jobs.
- Keep production secrets scoped to protected environments, minimize job permissions, and prefer OIDC with AWS STS over long-lived cloud credentials.
- Separate immutable build artifacts from environment-specific configuration so the same artifact can be promoted, audited, and rolled back reliably.
- Treat configuration as a security and reliability boundary: avoid duplication, validate critical values, prevent untrusted input from reaching privileged commands, and keep deployment configuration observable without exposing secrets.