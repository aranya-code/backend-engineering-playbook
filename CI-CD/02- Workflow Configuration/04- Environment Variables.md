# 04- Environment Variables

## Overview

Environment variables are one of the primary mechanisms for passing configuration and runtime values into GitHub Actions jobs and steps.

In a production CI/CD system, environment variables commonly carry non-sensitive configuration such as:

- Application environment names
- Python versions
- AWS regions
- Docker image names
- Feature flags
- Service URLs
- Build metadata
- Deployment configuration

GitHub Actions provides several related mechanisms for configuration:

- `env` context
- Repository variables
- Organization variables
- Environment variables
- Environment secrets
- Workflow inputs
- Step outputs
- `$GITHUB_ENV`

These mechanisms solve different problems and should not be treated as interchangeable.

A mature pipeline separates:

```text
Configuration
    ↓
Variables

Sensitive configuration
    ↓
Secrets

Computed runtime values
    ↓
Step / Job outputs

Execution-specific values
    ↓
GitHub contexts
```

The goal is not simply to avoid hardcoding values. The goal is to establish clear configuration boundaries, predictable precedence, secure secret handling, and reproducible deployments.

---

## Why Environment Variables Matter in CI/CD

A backend application normally behaves differently across environments.

For example:

```text
Development
    API_URL=http://localhost:8000
    LOG_LEVEL=DEBUG

Staging
    API_URL=https://staging-api.example.com
    LOG_LEVEL=INFO

Production
    API_URL=https://api.example.com
    LOG_LEVEL=WARNING
```

Hardcoding these values directly into workflow steps creates maintenance and deployment risks.

Instead:

```yaml
env:
  APP_ENV: staging
  AWS_REGION: ap-south-1
```

The workflow can then reuse the same deployment logic across environments.

Environment variables are especially valuable when the same workflow is responsible for:

```text
Build
  ↓
Test
  ↓
Staging
  ↓
Production
```

while configuration changes between stages.

---

## Configuration Categories

A production workflow should distinguish different classes of values.

| Category | Example | Recommended Mechanism |
|---|---|---|
| Static workflow configuration | `AWS_REGION` | `vars` / `env` |
| Non-sensitive environment configuration | `APP_ENV` | Environment variables / `vars` |
| Sensitive credentials | AWS credentials | OIDC / `secrets` where required |
| Deployment input | `production` | `inputs` |
| Git metadata | Commit SHA | `github` context |
| Matrix value | Python version | `matrix` context |
| Computed value | Docker image digest | Step/job output |
| Temporary step value | Generated path | `$GITHUB_ENV` |
| Cross-job value | Build metadata | Job output / artifact |

The important principle is:

> Use the narrowest mechanism that correctly represents the value's purpose.

---

## The `env` Context

The `env` context represents environment variables defined in the workflow configuration.

Example:

```yaml
name: Backend CI

on:
  push:
    branches:
      - main

env:
  APP_NAME: backend-api
  AWS_REGION: ap-south-1

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Show configuration
        run: |
          echo "Application: $APP_NAME"
          echo "Region: $AWS_REGION"
```

The same variables are accessible through the expression context:

```yaml
- name: Show application name
  run: echo "${{ env.APP_NAME }}"
```

There is an important distinction:

```text
env context
    ↓
GitHub Actions expression evaluation

Environment variable
    ↓
Shell / process execution
```

For example:

```yaml
env:
  APP_ENV: production

steps:
  - name: Example
    run: |
      echo "$APP_ENV"
      echo "${{ env.APP_ENV }}"
```

Both can produce the same value, but they operate at different layers.

---

## Workflow-Level Environment Variables

A workflow-level `env` declaration applies broadly to jobs and steps unless overridden at a narrower scope.

```yaml
name: Backend CI/CD

on:
  push:
    branches:
      - main

env:
  APP_NAME: backend-api
  AWS_REGION: ap-south-1

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Run tests
        run: pytest

  build:
    runs-on: ubuntu-latest

    steps:
      - name: Build image
        run: docker build -t "$APP_NAME:${GITHUB_SHA}" .
```

Use workflow-level variables for values that genuinely apply to most or all jobs.

Avoid placing job-specific configuration at workflow scope merely for convenience.

---

## Job-Level Environment Variables

A job can define its own environment variables.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    env:
      APP_ENV: test
      DATABASE_HOST: localhost

    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        run: pytest
```

The variables apply to steps within that job.

This is useful when different jobs have different configuration.

```text
test job
    APP_ENV=test

build job
    APP_ENV=build

deploy job
    APP_ENV=staging
```

Job-level scope reduces accidental configuration leakage between unrelated jobs.

---

## Step-Level Environment Variables

A step can define the narrowest `env` scope.

```yaml
steps:
  - name: Run tests
    env:
      DJANGO_SETTINGS_MODULE: config.settings.test
      DATABASE_URL: postgresql://localhost/app
    run: pytest

  - name: Build image
    env:
      IMAGE_TAG: ${{ github.sha }}
    run: docker build -t "backend:$IMAGE_TAG" .
```

This is useful for temporary or step-specific configuration.

Prefer step-level scope when a value is only required by one command.

---

## Environment Variable Scope

GitHub Actions provides three common `env` scopes.

| Scope | Availability | Typical Use |
|---|---|---|
| Workflow | All applicable jobs/steps | Global workflow configuration |
| Job | All steps in a job | Job-specific configuration |
| Step | One step | Temporary/specific configuration |

Conceptually:

```text
Workflow
│
├── env
│
├── Job A
│   ├── env
│   └── Steps
│       ├── Step 1
│       └── Step 2
│
└── Job B
    ├── env
    └── Steps
        ├── Step 1
        └── Step 2
```

Use the smallest practical scope.

This improves maintainability and reduces accidental coupling.

---

## Environment Variable Precedence

When the same variable is defined at multiple `env` scopes, the narrower scope takes precedence.

For example:

```yaml
env:
  APP_ENV: production

jobs:
  deploy:
    env:
      APP_ENV: staging

    runs-on: ubuntu-latest

    steps:
      - name: Show environment
        env:
          APP_ENV: development
        run: echo "$APP_ENV"
```

The step sees:

```text
APP_ENV=development
```

because the step-level value is more specific than the job-level and workflow-level values.

The conceptual precedence is:

```text
Step
  ↓
Job
  ↓
Workflow
```

A senior engineer should avoid relying on complex overrides unless there is a clear reason.

Duplicate variable names across scopes can make production failures difficult to diagnose.

---

## `env` vs `vars`

GitHub Actions provides both `env` and `vars`.

### `env`

`env` is workflow-defined environment configuration.

```yaml
env:
  APP_ENV: staging
```

### `vars`

`vars` exposes configuration variables configured at the repository, organization, or environment level.

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Deploy
        env:
          AWS_REGION: ${{ vars.AWS_REGION }}
        run: ./scripts/deploy.sh
```

This allows configuration to be managed outside the workflow YAML.

---

## When to Use `env`

Use `env` when the value belongs directly to the workflow.

```yaml
env:
  PYTHONUNBUFFERED: '1'
  PIP_DISABLE_PIP_VERSION_CHECK: '1'
```

These are workflow execution settings.

Use `env` when:

- The value is tightly coupled to the workflow.
- It is safe to store in source control.
- It is unlikely to vary independently from the workflow.
- Keeping it near the workflow improves readability.

---

## When to Use `vars`

Use `vars` when configuration should be managed independently from workflow implementation.

For example:

```text
Repository
    AWS_REGION=ap-south-1

Environment: staging
    DEPLOY_ROLE=arn:aws:iam::123456789012:role/staging-deploy

Environment: production
    DEPLOY_ROLE=arn:aws:iam::123456789012:role/production-deploy
```

A workflow can reference:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
```

This separates deployment logic from environment-specific configuration.

---

## Repository Variables

Repository variables are useful for non-sensitive configuration shared by workflows in a repository.

Examples:

- AWS region
- Docker registry
- Application name
- Default deployment configuration
- Non-secret service identifiers

Example:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
  ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
```

Do not store passwords, private keys, tokens, or credentials in repository variables.

Use secrets or identity-based authentication for sensitive values.

---

## Organization Variables

Organization variables allow configuration to be shared across repositories.

A common enterprise pattern is:

```text
Organization
│
├── AWS_REGION
├── ECR_REGISTRY
└── STANDARD_PYTHON_VERSION
       │
       ├── backend-service-a
       ├── backend-service-b
       └── backend-service-c
```

This can reduce duplication across repositories.

However, organization-level configuration should be governed carefully because changing one variable can affect many pipelines.

Use organization variables for genuinely shared configuration rather than repository-specific behavior.

---

## Environment Variables

GitHub Actions environments such as:

- `development`
- `staging`
- `production`

can have their own variables and secrets.

Example:

```yaml
jobs:
  deploy:
    environment: staging
    runs-on: ubuntu-latest

    steps:
      - name: Deploy
        env:
          API_URL: ${{ vars.API_URL }}
        run: ./scripts/deploy.sh
```

The same workflow can target production:

```yaml
jobs:
  deploy:
    environment: production
    runs-on: ubuntu-latest

    steps:
      - name: Deploy
        env:
          API_URL: ${{ vars.API_URL }}
        run: ./scripts/deploy.sh
```

The deployment logic remains the same while the environment supplies different configuration.

---

## Environment Protection

An environment is more than a variable namespace.

Production environments can provide controls such as:

- Required reviewers
- Deployment branch restrictions
- Environment secrets
- Environment variables
- Deployment history

A mature deployment architecture can therefore separate:

```text
Workflow logic
      │
      ▼
Environment selection
      │
      ├── staging
      │     ├── configuration
      │     └── secrets
      │
      └── production
            ├── configuration
            ├── secrets
            └── approval/protection
```

This is preferable to embedding production credentials and configuration directly into workflow files.

---

## Development, Staging, and Production

A common backend deployment model is:

```text
Development
    ↓
CI validation
    ↓
Staging
    ↓
Integration / smoke tests
    ↓
Production
```

Environment-specific values should be externalized.

For example:

| Configuration | Development | Staging | Production |
|---|---|---|---|
| `APP_ENV` | `development` | `staging` | `production` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `WARNING` |
| `API_URL` | Local | Staging API | Production API |
| `DATABASE_HOST` | Local | Private DB | Private DB |
| AWS role | Dev role | Staging role | Production role |

Sensitive values should not be committed to the repository.

---

## Environment Variables vs Secrets

The distinction is fundamental.

| Property | Variables | Secrets |
|---|---|---|
| Sensitive data | No | Yes |
| Visible configuration | Appropriate | No |
| Example | `AWS_REGION` | API token |
| Storage | `vars` / `env` | `secrets` |
| Masking | Not intended | Secret masking |
| Typical use | Configuration | Credentials |

Example:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}

steps:
  - name: Deploy
    env:
      DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
    run: ./scripts/deploy.sh
```

Do not use variables simply because they are easier to manage when the value is sensitive.

---

## Secrets Context

Secrets are accessed through the `secrets` context.

```yaml
steps:
  - name: Deploy
    env:
      DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
    run: ./scripts/deploy.sh
```

Typical secret sources include:

- Repository secrets
- Organization secrets
- Environment secrets

Use environment secrets for production-specific deployment credentials when appropriate.

---

## Secret Masking

GitHub Actions attempts to mask recognized secret values in logs.

For example:

```yaml
steps:
  - name: Authenticate
    env:
      API_TOKEN: ${{ secrets.API_TOKEN }}
    run: ./scripts/authenticate.sh
```

Avoid deliberately printing secrets.

Bad:

```yaml
- name: Debug token
  run: echo "$API_TOKEN"
```

Even though masking may replace recognized values, logging secrets is still poor operational practice.

A secret can also be transformed, encoded, concatenated, or exposed indirectly in ways that make relying solely on masking unsafe.

The correct rule is:

> Never use logs as a mechanism for inspecting secret values.

---

## Avoid Secrets in Command Arguments

Avoid:

```yaml
- name: Deploy
  run: ./deploy.sh --token "${{ secrets.DEPLOY_TOKEN }}"
```

Passing secrets as command-line arguments can expose them through process inspection or tooling.

Prefer environment variables when the application or CLI supports them:

```yaml
- name: Deploy
  env:
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
  run: ./deploy.sh
```

The deployment script can then read:

```bash
"$DEPLOY_TOKEN"
```

Use the authentication mechanism recommended by the underlying platform whenever possible.

---

## Prefer OIDC for AWS

For GitHub Actions deploying to AWS, long-lived AWS access keys should generally not be stored as GitHub secrets when OIDC can be used.

A typical flow is:

```text
GitHub Actions
      │
      │ OIDC token
      ▼
AWS STS
      │
      │ AssumeRoleWithWebIdentity
      ▼
Temporary AWS credentials
      │
      ▼
ECR / ECS / S3 / Lambda / CloudFormation
```

The workflow typically requests the `id-token` permission:

```yaml
permissions:
  contents: read
  id-token: write
```

Then an AWS authentication action can establish temporary credentials.

This reduces the lifetime and exposure of AWS credentials.

---

## `$GITHUB_ENV`

`$GITHUB_ENV` allows a step to persist an environment variable for subsequent steps in the same job.

```yaml
steps:
  - name: Determine image tag
    run: |
      echo "IMAGE_TAG=${GITHUB_SHA}" >> "$GITHUB_ENV"

  - name: Build image
    run: |
      docker build -t "backend:$IMAGE_TAG" .
```

The value written by the first step becomes available to subsequent steps.

The flow is:

```text
Step A
  │
  │ writes to $GITHUB_ENV
  ▼
Runner environment
  │
  ▼
Step B
```

The variable is not automatically propagated to another job.

---

## `$GITHUB_ENV` Scope

Consider:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Set variable
        run: echo "IMAGE_TAG=${GITHUB_SHA}" >> "$GITHUB_ENV"

      - name: Use variable
        run: echo "$IMAGE_TAG"

  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Try to use variable
        run: echo "$IMAGE_TAG"
```

`deploy` does not automatically receive `IMAGE_TAG`.

For cross-job communication, use job outputs or artifacts.

---

## `$GITHUB_OUTPUT`

Use `$GITHUB_OUTPUT` when a step needs to expose a value as an output.

```yaml
steps:
  - name: Generate image tag
    id: metadata
    run: |
      echo "image_tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

  - name: Use image tag
    run: echo "${{ steps.metadata.outputs.image_tag }}"
```

This is the preferred mechanism for step outputs.

The output can then become a job output:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      image_tag: ${{ steps.metadata.outputs.image_tag }}

    steps:
      - id: metadata
        run: echo "image_tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

A downstream job can consume it through `needs`.

```yaml
jobs:
  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - run: echo "Deploying ${{ needs.build.outputs.image_tag }}"
```

---

## `$GITHUB_PATH`

`$GITHUB_PATH` adds directories to the runner's `PATH` for subsequent steps.

```yaml
steps:
  - name: Install internal CLI
    run: |
      mkdir -p "$HOME/bin"
      cp ./tools/deploy-cli "$HOME/bin/deploy-cli"
      echo "$HOME/bin" >> "$GITHUB_PATH"

  - name: Run internal CLI
    run: deploy-cli --version
```

This is useful when a tool is installed dynamically during a workflow.

Use it carefully because modifying `PATH` can change which executable is invoked by later steps.

---

## Step Summaries

GitHub Actions provides `$GITHUB_STEP_SUMMARY` for human-readable workflow summaries.

```yaml
- name: Publish test summary
  run: |
    {
      echo "## Test Results"
      echo ""
      echo "- Status: Passed"
      echo "- Python: 3.12"
      echo "- Coverage: 94%"
    } >> "$GITHUB_STEP_SUMMARY"
```

This is preferable to generating large amounts of unstructured log output when the information is intended for human review.

A useful production pipeline can expose:

```text
Test Summary
Build Metadata
Docker Image
Deployment Environment
Deployment Result
Health Check Result
```

without requiring engineers to inspect every log line.

---

## Annotations

GitHub Actions supports workflow commands that can create annotations.

For example:

```bash
echo "::warning file=app.py,line=42::Potential configuration issue"
```

and:

```bash
echo "::error file=app.py,line=18::Validation failed"
```

Annotations are useful for making important failures visible in the GitHub UI.

Do not generate excessive annotations. Use them for actionable diagnostics.

---

## Logging Commands

GitHub Actions supports workflow commands for communicating structured information to the runner and GitHub Actions.

Modern workflows commonly use environment files such as:

```text
$GITHUB_ENV
$GITHUB_OUTPUT
$GITHUB_PATH
$GITHUB_STEP_SUMMARY
```

Avoid relying on deprecated workflow-command mechanisms for setting outputs or environment variables.

For example, prefer:

```bash
echo "key=value" >> "$GITHUB_OUTPUT"
```

rather than older output-setting syntax.

---

## Environment Variables in Python Applications

A Python backend can consume environment variables normally.

```python
import os

APP_ENV = os.environ["APP_ENV"]
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

For Django:

```python
import os

DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
```

For FastAPI:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

For production applications, configuration should generally be centralized rather than scattering `os.getenv()` calls throughout business logic.

Libraries such as Pydantic Settings can provide structured configuration for FastAPI and Python services.

---

## Environment Variables and Docker

Docker containers receive environment variables at runtime.

A GitHub Actions workflow can build an image without embedding environment-specific secrets into the image:

```yaml
- name: Build image
  run: |
    docker build \
      --tag "backend:${GITHUB_SHA}" \
      .
```

Runtime configuration should be supplied when the container runs.

For example:

```bash
docker run \
  -e APP_ENV=staging \
  -e DATABASE_URL="$DATABASE_URL" \
  backend:"$IMAGE_TAG"
```

Do not bake environment-specific secrets into Docker image layers.

The preferred model is:

```text
Docker image
    ↓
Immutable application artifact

Runtime environment
    ↓
Configuration + secrets
```

This allows the same image to move through staging and production.

---

## Environment Variables and Kubernetes

The same principle applies to Kubernetes.

A deployment can reference configuration from a ConfigMap:

```yaml
env:
  - name: APP_ENV
    valueFrom:
      configMapKeyRef:
        name: backend-config
        key: APP_ENV
```

Secrets should come from Kubernetes Secrets or an external secret-management system rather than ordinary ConfigMaps.

GitHub Actions should generally deploy the workload rather than becoming the long-term storage location for application configuration.

---

## Environment Variables and AWS

A typical AWS deployment might use:

```text
GitHub Actions
    │
    ├── vars.AWS_REGION
    ├── vars.ECR_REPOSITORY
    └── OIDC authentication
             │
             ▼
          AWS STS
             │
             ▼
            ECR
             │
             ▼
            ECS
```

The workflow might define:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
  ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
```

Then use them:

```yaml
- name: Build image
  env:
    IMAGE_TAG: ${{ github.sha }}
  run: |
    docker build -t "$ECR_REPOSITORY:$IMAGE_TAG" .
```

Sensitive AWS credentials should not be placed into `env` as static values.

---

## Environment Variables and Matrix Builds

Matrix values can be exposed through environment variables.

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version:
          - '3.11'
          - '3.12'
          - '3.13'

    runs-on: ubuntu-latest

    env:
      PYTHON_VERSION: ${{ matrix.python-version }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v6
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Run tests
        run: pytest
```

This can improve readability when a matrix value is used repeatedly.

However, using `matrix.python-version` directly is often clearer when the value is only needed once.

---

## Environment Variables and Service Containers

Integration tests frequently require PostgreSQL or Redis.

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:17
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

    env:
      DATABASE_URL: postgresql://app:test-password@localhost:5432/app_test
      REDIS_URL: redis://localhost:6379/0

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'

      - run: pip install -r requirements.txt
      - run: pytest -m integration
```

Environment variables provide a stable interface between the application and the test infrastructure.

For production-quality integration testing, also account for service readiness rather than assuming the container is immediately ready after startup.

---

## Environment Variables and Caching

Environment variables can influence cache configuration, but dependency correctness should primarily be determined by dependency files.

For example:

```yaml
- name: Set up Python
  uses: actions/setup-python@v6
  with:
    python-version: '3.12'
    cache: pip
    cache-dependency-path: requirements.txt
```

Avoid using environment variables as a substitute for proper cache keys.

A cache must never cause the workflow to use stale dependencies simply because a variable remained unchanged.

---

## Build Metadata

Environment variables are useful for build metadata.

```yaml
env:
  APP_NAME: backend-api
  IMAGE_TAG: ${{ github.sha }}
```

A build can then use:

```yaml
- name: Build Docker image
  run: |
    docker build \
      --label "org.opencontainers.image.revision=${GITHUB_SHA}" \
      --tag "${APP_NAME}:${IMAGE_TAG}" \
      .
```

Commit SHA-based image tags provide traceability:

```text
Git commit
    ↓
GitHub Actions run
    ↓
Docker image
    ↓
ECR
    ↓
ECS deployment
```

This is preferable to relying exclusively on mutable tags such as `latest`.

---

## Environment Variables and Reproducibility

A production pipeline should be reproducible.

Given:

```text
Source revision
+
Dependency versions
+
Build configuration
+
Environment configuration
```

the resulting artifact should be predictable.

Avoid hidden configuration such as:

```bash
export SOME_SETTING=...
```

performed manually on a runner.

Prefer explicit workflow configuration:

```yaml
env:
  BUILD_MODE: production
```

or repository/environment variables:

```yaml
env:
  BUILD_MODE: ${{ vars.BUILD_MODE }}
```

This makes configuration reviewable and auditable.

---

## Environment Variables and Immutable Deployments

Environment-specific configuration should not require rebuilding the application artifact.

Prefer:

```text
Build once
    ↓
backend:abc123
    ↓
Staging
    ↓
Production
```

with:

```text
Staging configuration
    ↓
Staging runtime

Production configuration
    ↓
Production runtime
```

Avoid:

```text
Build staging image
    ↓
Build production image
```

when the only difference is runtime configuration.

This is a key CI/CD principle:

> Configuration belongs to the runtime environment; the application artifact should remain immutable whenever practical.

---

## Environment Variables and Secret Rotation

Environment-specific secrets may need rotation.

For example:

```text
Production
    DATABASE_PASSWORD
    API_TOKEN
    THIRD_PARTY_SECRET
```

A good design avoids hardcoding these values into the workflow or Docker image.

When secrets are rotated:

```text
Secret store updated
       ↓
Next deployment/runtime
       ↓
Application receives new value
```

The deployment pipeline should not require source-code changes simply because a credential changed.

For AWS workloads, prefer managed identity mechanisms and AWS Secrets Manager or Parameter Store where appropriate rather than routing every application secret through GitHub Actions.

---

## Configuration Architecture

A production architecture can separate configuration layers:

```mermaid
flowchart TD
    A[Workflow YAML] --> B[Workflow env]
    C[Organization Variables] --> D[vars Context]
    E[Repository Variables] --> D
    F[Environment Variables] --> D
    G[Secrets] --> H[secrets Context]
    I[GitHub Contexts] --> J[Workflow Runtime]
    B --> J
    D --> J
    H --> J
    J --> K[Runner Process]
    K --> L[Python / Django / FastAPI]
    K --> M[Docker / CLI / Deployment Tool]
```

Each layer has a distinct responsibility.

The objective is to prevent one configuration mechanism from becoming a universal storage location.

---

## Configuration Precedence Model

A useful production mental model is:

```text
GitHub event / inputs / contexts
             │
             ▼
      Workflow expressions
             │
             ▼
      env / vars / secrets
             │
             ▼
       Runner environment
             │
             ▼
       Process environment
             │
             ▼
 Application configuration layer
```

For application configuration, another layer may exist:

```text
GitHub Actions
      ↓
Container runtime
      ↓
Kubernetes / ECS / EC2
      ↓
Application process
```

Configuration should be intentionally passed between these layers rather than assumed to propagate automatically.

---

## What Does Not Automatically Propagate

A common mistake is assuming that every configuration mechanism is globally available.

For example:

```text
$GITHUB_ENV
    ↓
Same job only
```

while:

```text
Job output
    ↓
Downstream jobs through needs
```

and:

```text
Artifact
    ↓
Explicit upload/download
```

Similarly, a local shell variable:

```bash
IMAGE_TAG=abc123
```

does not automatically become a GitHub Actions environment variable for later steps.

To persist it:

```bash
echo "IMAGE_TAG=abc123" >> "$GITHUB_ENV"
```

To expose it as structured workflow data:

```bash
echo "image_tag=abc123" >> "$GITHUB_OUTPUT"
```

---

## Passing Values Between Steps and Jobs

### Same Step

```bash
IMAGE_TAG="$GITHUB_SHA"
```

### Later Steps in Same Job

```bash
echo "IMAGE_TAG=$GITHUB_SHA" >> "$GITHUB_ENV"
```

### Later Steps Through Step Output

```yaml
echo "image_tag=$GITHUB_SHA" >> "$GITHUB_OUTPUT"
```

### Another Job

```yaml
outputs:
  image_tag: ${{ steps.metadata.outputs.image_tag }}
```

and:

```yaml
needs.build.outputs.image_tag
```

### Large Build Data

Use an artifact rather than trying to place large data into environment variables or outputs.

---

## Do Not Put Large Data in Environment Variables

Environment variables are appropriate for configuration and small runtime values.

Avoid using them for:

- Build archives
- Large JSON documents
- Test reports
- Binary data
- Docker image data
- Large configuration files

Instead use:

```text
Small scalar value
    → env/output

Structured build metadata
    → output

Large file
    → artifact

Container image
    → registry
```

This makes the workflow more scalable and easier to operate.

---

## Security Considerations

### Never Store Secrets in Plain `env`

Bad:

```yaml
env:
  DATABASE_PASSWORD: "super-secret-password"
```

The value is now present in source-controlled workflow configuration.

Use:

```yaml
env:
  DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
```

when a GitHub secret is actually required.

For production AWS workloads, prefer OIDC or workload identity instead of static credentials.

---

### Avoid Secret Exposure Through Debugging

Be careful with:

```yaml
run: env
```

or:

```bash
printenv
```

These commands can expose sensitive environment variables.

Avoid dumping the complete process environment in production workflows.

Inspect only the specific non-sensitive values required for debugging.

---

### Treat Environment Variables as Potentially Sensitive

Even variables that are not classified as secrets may contain sensitive infrastructure information.

Examples:

```text
INTERNAL_API_URL
PRIVATE_HOSTNAME
DATABASE_HOST
INTERNAL_SERVICE_NAME
```

Do not assume that "not a secret" means "safe to publish everywhere."

Apply the principle of least exposure.

---

## Fork Pull Requests

Fork-based pull requests require special care.

Secrets are generally not made available to untrusted fork workflows in the same way as trusted repository workflows.

Do not design a pull request workflow that assumes production secrets will always be present.

A safer architecture is:

```text
Fork PR
   ↓
Untrusted validation
   ↓
No production secrets
   ↓
No privileged deployment

Trusted main branch
   ↓
Protected deployment workflow
   ↓
Environment secrets / OIDC
```

Do not use environment variables to bypass GitHub's security boundaries.

---

## `pull_request_target` Considerations

`pull_request_target` executes in the context of the base repository and therefore requires particular care around secrets and permissions.

Avoid this pattern:

```yaml
on:
  pull_request_target:

jobs:
  test:
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}

      - run: ./untrusted-script.sh
```

The problem is not the environment variable itself.

The problem is that privileged workflow context can become exposed to untrusted pull request code.

Conditions and environment variables cannot make untrusted source code safe.

---

## Organization and Environment Governance

At enterprise scale, configuration should have ownership.

A useful governance model is:

| Configuration | Owner |
|---|---|
| Workflow implementation | Repository team |
| Repository variables | Repository maintainers |
| Organization variables | Platform/DevOps team |
| Environment variables | Environment/platform owners |
| Production secrets | Security/platform owners |
| AWS IAM role configuration | Cloud/platform team |
| Deployment policies | Platform/security teams |

This avoids a situation where every application team independently creates incompatible deployment configuration.

---

## Environment Variables and Reliability

Configuration errors can be more damaging than application bugs.

For example:

```text
Correct application
       +
Wrong DATABASE_URL
       ↓
Production outage
```

or:

```text
Correct Docker image
       +
Wrong API endpoint
       ↓
Requests routed to wrong environment
```

Use validation before deployment.

For example:

```yaml
- name: Validate deployment configuration
  env:
    APP_ENV: ${{ vars.APP_ENV }}
    AWS_REGION: ${{ vars.AWS_REGION }}
  run: |
    set -euo pipefail

    test -n "$APP_ENV"
    test -n "$AWS_REGION"

    case "$APP_ENV" in
      staging|production)
        ;;
      *)
        echo "Invalid APP_ENV: $APP_ENV" >&2
        exit 1
        ;;
    esac
```

Configuration validation is especially valuable before destructive operations.

---

## Configuration Validation

For complex deployments, validate configuration before executing the deployment.

```text
Load configuration
      ↓
Validate required values
      ↓
Validate allowed values
      ↓
Validate environment
      ↓
Authenticate
      ↓
Deploy
```

For example:

```bash
set -euo pipefail

: "${APP_ENV:?APP_ENV is required}"
: "${AWS_REGION:?AWS_REGION is required}"

if [[ "$APP_ENV" != "staging" && "$APP_ENV" != "production" ]]; then
  echo "Unsupported environment: $APP_ENV" >&2
  exit 1
fi
```

This converts silent configuration mistakes into explicit failures.

---

## Configuration Drift

Environment variables managed outside the workflow can drift.

For example:

```text
Repository configuration
       │
       ├── staging = correct
       │
       └── production = outdated
```

A mature CI/CD system should make important configuration:

- Auditable
- Versioned where appropriate
- Owned
- Validated
- Observable
- Protected

For critical infrastructure, configuration-as-code can provide stronger review and reproducibility.

---

## Environment Variables and Deployment Rollbacks

Rollback should normally restore the previous application artifact while retaining the correct runtime configuration.

For example:

```text
Current:
backend:abc123
production config v5

Rollback:
backend:def456
production config v5
```

Do not accidentally rollback configuration together with application code unless configuration is versioned and intentionally coupled to the artifact.

This distinction matters for:

- Database compatibility
- API endpoints
- Feature flags
- External service credentials
- Infrastructure endpoints

---

## Common Mistakes

### Hardcoding Secrets

```yaml
env:
  API_KEY: "abc123"
```

**Problem:** Credentials become source-controlled configuration.

**Better:**

```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}
```

---

### Using Secrets for Non-Sensitive Configuration

Using secrets for values such as:

```text
AWS_REGION
LOG_LEVEL
ECR_REPOSITORY
```

adds unnecessary security and operational complexity.

Use variables where the value is genuinely non-sensitive.

---

### Using `env` for Cross-Job Communication

This does not work:

```yaml
jobs:
  build:
    steps:
      - run: echo "IMAGE_TAG=abc123" >> "$GITHUB_ENV"

  deploy:
    steps:
      - run: echo "$IMAGE_TAG"
```

`$GITHUB_ENV` is scoped to the job.

Use job outputs:

```yaml
outputs:
  image_tag: ${{ steps.metadata.outputs.image_tag }}
```

---

### Overusing Workflow-Level Variables

A large workflow-level `env` section creates hidden coupling.

Prefer:

```yaml
jobs:
  deploy:
    env:
      DEPLOY_ENV: production
```

when only deployment needs the value.

---

### Overriding Variables Across Scopes

This is difficult to reason about:

```yaml
env:
  API_URL: global

jobs:
  deploy:
    env:
      API_URL: staging

    steps:
      - env:
          API_URL: production
        run: ./deploy.sh
```

Prefer one clear source for each important configuration value.

---

### Printing the Entire Environment

Avoid:

```bash
printenv
```

in production debugging.

It can expose credentials or infrastructure information.

Print only the required values.

---

### Baking Configuration into Docker Images

Avoid:

```dockerfile
ENV APP_ENV=production
ENV DATABASE_URL=...
```

for environment-specific runtime configuration.

Build the image once and inject runtime configuration during deployment.

---

### Assuming Variables Are Immutable

Variables managed at repository or environment level can change independently from the workflow source.

For critical deployments, validate important values and understand who controls them.

---

## Troubleshooting Environment Variables

Use the following failure-domain model.

### Symptom

A command receives an empty or unexpected variable.

### Possible Causes

- Variable defined at the wrong scope.
- Incorrect `vars` or `secrets` name.
- Environment not selected.
- Step overrides job value.
- `$GITHUB_ENV` was written after the consuming step.
- Cross-job propagation was incorrectly assumed.
- Expression evaluated to an empty value.
- Variable is unavailable for the triggering event.

### Isolation Strategy

Inspect only non-sensitive configuration:

```yaml
- name: Inspect configuration
  run: |
    printf 'APP_ENV=%s\n' "$APP_ENV"
    printf 'AWS_REGION=%s\n' "$AWS_REGION"
```

For expressions:

```yaml
- name: Inspect context values
  run: |
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
```

Never print secrets to diagnose a configuration issue.

### Corrective Action

Check:

- Scope
- Name
- Environment
- Context
- Job dependency
- Output mapping
- Workflow event

### Prevention

Use:

- Clear variable naming
- Narrow scope
- Configuration validation
- Environment protection
- Documented ownership
- Explicit job outputs
- Avoidance of duplicate variable definitions

---

## Debugging `$GITHUB_ENV`

If a value is unexpectedly unavailable:

```yaml
steps:
  - name: Set value
    run: echo "IMAGE_TAG=${GITHUB_SHA}" >> "$GITHUB_ENV"

  - name: Inspect value
    run: |
      printf 'IMAGE_TAG=%s\n' "$IMAGE_TAG"
```

Remember that the step writing to `$GITHUB_ENV` does not receive the newly written value automatically.

The value becomes available to subsequent steps.

---

## Debugging `$GITHUB_OUTPUT`

Use an explicit step ID:

```yaml
- name: Generate metadata
  id: metadata
  run: |
    echo "image_tag=${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

Then consume it using:

```yaml
${{ steps.metadata.outputs.image_tag }}
```

Common mistakes include:

- Missing `id`
- Incorrect output name
- Incorrect expression
- Writing to the wrong file
- Expecting the output to become an environment variable automatically

---

## Production Environment Example

A reusable deployment workflow can keep application configuration separate from deployment implementation.

```yaml
name: Deploy Backend

on:
  workflow_dispatch:
    inputs:
      environment:
        required: true
        type: choice
        options:
          - staging
          - production

permissions:
  contents: read
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest

    environment: ${{ inputs.environment }}

    env:
      APP_ENV: ${{ inputs.environment }}
      AWS_REGION: ${{ vars.AWS_REGION }}
      ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}

    steps:
      - uses: actions/checkout@v4

      - name: Validate configuration
        run: |
          set -euo pipefail

          test -n "$APP_ENV"
          test -n "$AWS_REGION"
          test -n "$ECR_REPOSITORY"

      - name: Authenticate to AWS
        uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Deploy
        env:
          IMAGE_TAG: ${{ github.sha }}
        run: |
          ./scripts/deploy.sh \
            "$APP_ENV" \
            "$ECR_REPOSITORY" \
            "$IMAGE_TAG"
```

The architecture is:

```text
Manual Input
    │
    ▼
Environment Selection
    │
    ├── staging
    │
    └── production
           │
           ▼
Environment Variables
           │
           ▼
AWS OIDC
           │
           ▼
Immutable Image
           │
           ▼
Deployment
```

The same workflow can deploy different environments without embedding separate deployment implementations.

---

## Production Checklist

Before using environment variables in a production workflow, verify:

### Configuration

- [ ] Non-sensitive values use `vars` or `env` appropriately.
- [ ] Environment-specific values are scoped to the correct environment.
- [ ] Variable names are consistent.
- [ ] Duplicate values across scopes are avoided.
- [ ] Required configuration is validated.

### Secrets

- [ ] Credentials are not committed to workflow YAML.
- [ ] Secrets are not printed.
- [ ] Secrets are not passed unnecessarily as command arguments.
- [ ] Production secrets are environment-scoped where appropriate.
- [ ] AWS authentication uses OIDC when practical.

### Data Flow

- [ ] `$GITHUB_ENV` is used only for same-job propagation.
- [ ] `$GITHUB_OUTPUT` is used for step outputs.
- [ ] Job outputs are used for cross-job scalar data.
- [ ] Artifacts are used for large build outputs.
- [ ] Container images are stored in a registry.

### Deployment

- [ ] The same immutable artifact can be promoted across environments.
- [ ] Runtime configuration is injected at deployment time.
- [ ] Production environment protection is configured.
- [ ] Deployment concurrency is controlled.
- [ ] Configuration changes are auditable.

### Security

- [ ] Sensitive values are treated as secrets.
- [ ] Untrusted pull request code cannot access production configuration.
- [ ] `pull_request_target` is used only with a deliberate security model.
- [ ] Workflow permissions follow least privilege.
- [ ] Debugging does not dump sensitive environment state.

---

## Interview Traps

### What Is the Difference Between `env` and `vars`?

`env` is workflow-defined environment configuration, while `vars` exposes configuration variables managed at repository, organization, or environment scope.

### Can `$GITHUB_ENV` Pass Data Between Jobs?

No.

It persists environment variables for subsequent steps in the same job. Use job outputs or artifacts for cross-job communication.

### What Should Be Stored in `vars`?

Non-sensitive configuration such as:

```text
AWS_REGION
ECR_REPOSITORY
APP_NAME
```

Sensitive credentials belong in secrets or, preferably for AWS authentication, an identity-based mechanism such as OIDC.

### Should Database Passwords Be Stored in `env`?

Not as plaintext.

If GitHub Actions must supply the value, reference a secret:

```yaml
env:
  DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
```

For production applications, a dedicated secret-management service may be more appropriate.

### Why Should Docker Images Not Contain Environment-Specific Secrets?

Images are immutable artifacts that may be copied to multiple environments and registries.

Runtime configuration should be injected when the container starts.

### What Is the Difference Between `$GITHUB_ENV` and `$GITHUB_OUTPUT`?

`$GITHUB_ENV` persists an environment variable for subsequent steps in the same job.

`$GITHUB_OUTPUT` creates a step output that can be consumed through the `steps` context and promoted to a job output.

### Why Is OIDC Better for AWS Than Long-Lived Access Keys?

OIDC allows GitHub Actions to exchange a trusted identity token for temporary AWS credentials through STS, reducing the need to store long-lived AWS credentials in GitHub.

---

## Key Takeaways

- Use `env`, `vars`, `secrets`, contexts, and outputs for distinct purposes; do not treat them as interchangeable configuration stores.
- Keep environment-specific configuration externalized and inject it at runtime so the same immutable artifact can move from staging to production.
- Use `$GITHUB_ENV` for same-job environment propagation, `$GITHUB_OUTPUT` and job outputs for workflow data flow, and artifacts or registries for larger build outputs.
- Protect sensitive configuration with appropriate secret boundaries, least-privilege permissions, environment protection, and identity-based authentication such as AWS OIDC.
- Production configuration should be explicitly scoped, validated, auditable, and designed to avoid accidental exposure or configuration drift.