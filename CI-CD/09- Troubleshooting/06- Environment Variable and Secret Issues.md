# 06- Environment Variable and Secret Issues

## Overview

Environment variables and secrets are fundamental to GitHub Actions workflows because they connect workflow configuration with application execution, deployment systems, cloud credentials, databases, registries, and external services.

They are also one of the most common sources of CI/CD failures.

Typical symptoms include:

- A variable is unexpectedly empty.
- A secret is unavailable.
- A job receives the wrong environment value.
- A step sees a different value than the previous step.
- A secret works locally but not in GitHub Actions.
- Environment-level secrets are not available.
- A reusable workflow cannot access an expected secret.
- A fork pull request cannot access credentials.
- A deployment receives the wrong AWS region or account.
- A Docker build receives incorrect configuration.
- A secret appears masked in one place but leaks through another.
- A variable works at workflow scope but is overridden at job or step scope.
- `$GITHUB_ENV` or `$GITHUB_OUTPUT` is used incorrectly.
- A value is available in one step but not another.
- An environment variable is confused with the `vars` or `secrets` context.

The most reliable troubleshooting model is:

```text
Symptom
  ↓
Identify Variable / Secret Source
  ↓
Identify Scope
  ↓
Identify Event and Security Boundary
  ↓
Inspect Resolution and Data Flow
  ↓
Validate Availability Safely
  ↓
Identify Override / Propagation Issue
  ↓
Root Cause
  ↓
Corrective Action
  ↓
Prevention
```

The key distinction is:

```text
env
vars
secrets
inputs
outputs
```

are different mechanisms with different purposes, scopes, security properties, and lifecycles.

---

## GitHub Actions Configuration Model

A production workflow commonly combines several configuration mechanisms:

```text
Repository / Organization / Environment
                ↓
       Variables / Secrets
                ↓
Workflow Configuration
                ↓
Job Configuration
                ↓
Step Environment
                ↓
Application / Action / Shell
```

At the same time, data can move dynamically between steps and jobs:

```text
Step
 ↓
GITHUB_ENV
 ↓
Later Step

Step
 ↓
GITHUB_OUTPUT
 ↓
Job Output
 ↓
needs
 ↓
Another Job
```

Understanding which path a value follows is essential for troubleshooting.

---

## Environment Variables vs Variables vs Secrets

| Mechanism | Primary Purpose | Sensitive? | Typical Scope |
|---|---|---:|---|
| `env` | Runtime environment variables | Possibly | Workflow/job/step |
| `vars` | Non-sensitive configuration | No | Organization/repository/environment |
| `secrets` | Sensitive credentials/configuration | Yes | Organization/repository/environment |
| `inputs` | Workflow parameters | Not necessarily | Manual/reusable workflow |
| Step outputs | Dynamic step data | Depends | Current job |
| Job outputs | Dynamic job data | Depends | Downstream jobs |
| Artifacts | Files/data between jobs | Depends | Workflow/run |

A common design mistake is using one mechanism for everything.

For example:

```text
Database password → secret
AWS region        → variable
Build metadata    → output
Runtime setting   → env
Deployment target → validated input
```

---

## Workflow-Level Environment Variables

Example:

```yaml
env:
  APP_NAME: backend-api
  PYTHON_VERSION: "3.12"
```

All jobs and steps inherit the workflow-level environment unless overridden.

Example:

```yaml
name: CI

on:
  push:

env:
  APP_NAME: backend-api

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Show application
        run: echo "$APP_NAME"
```

Use workflow-level `env` for values that genuinely apply to the entire workflow.

Avoid putting environment-specific configuration at workflow scope if it makes the workflow harder to reason about.

---

## Job-Level Environment Variables

A job can define its own environment:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      APP_ENV: test

    steps:
      - run: echo "$APP_ENV"
```

This keeps job-specific configuration local.

For example:

```text
test job       → APP_ENV=test
staging deploy → APP_ENV=staging
production     → APP_ENV=production
```

---

## Step-Level Environment Variables

Step-level configuration is the narrowest scope:

```yaml
steps:
  - name: Run tests
    env:
      DATABASE_URL: postgresql://localhost/test
    run: pytest
```

This is useful for limiting sensitive or temporary configuration to the exact process that needs it.

For secrets, prefer narrow scope when practical.

---

## Environment Variable Precedence

When the same variable is defined at multiple levels, the more specific scope can override the broader scope.

Conceptually:

```text
Workflow
   ↓
Job
   ↓
Step
```

Example:

```yaml
env:
  APP_ENV: development

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      APP_ENV: staging

    steps:
      - name: Run
        env:
          APP_ENV: test
        run: echo "$APP_ENV"
```

The step receives:

```text
test
```

---

## Troubleshooting Variable Overrides

### Symptom

A variable has the correct value in one place but the wrong value in another.

### Possible Causes

- Workflow-level value
- Job-level override
- Step-level override
- Environment-level configuration
- Shell variable override
- Action-specific environment handling

### Isolation Strategy

Search the workflow for all definitions:

```text
APP_ENV
```

Then map:

```text
Workflow
  ↓
Job
  ↓
Step
  ↓
Shell
```

### Prevention

Use clear naming and avoid redefining the same variable unnecessarily.

---

## The `env` Context

GitHub Actions provides an `env` context for environment variables defined in workflow configuration.

Example:

```yaml
env:
  APP_ENV: staging

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Show configuration
        env:
          VALUE: ${{ env.APP_ENV }}
        run: |
          echo "$VALUE"
```

The `env` context should not be confused with the shell's environment.

There are two related layers:

```text
GitHub workflow expression
${{ env.APP_ENV }}

        ↓

Runner environment
$APP_ENV
```

---

## GitHub Expression vs Shell Environment

These are different evaluation systems.

GitHub expression:

```yaml
env:
  APP_ENV: ${{ vars.APP_ENV }}
```

Shell:

```bash
echo "$APP_ENV"
```

The first is resolved by GitHub Actions workflow processing.

The second is resolved by the shell at runtime.

This distinction becomes especially important when debugging missing or unexpected values.

---

## Repository Variables

Repository variables are accessed through:

```yaml
vars.NAME
```

Example:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
```

Variables are appropriate for non-sensitive configuration such as:

```text
AWS_REGION
ECR_REPOSITORY
DEPLOYMENT_MODE
SERVICE_NAME
LOG_LEVEL
```

Do not store credentials in repository variables.

---

## Organization Variables

Organization-level variables can provide shared configuration across repositories.

Example:

```text
AWS_REGION
PLATFORM_TEAM
DEFAULT_PYTHON_VERSION
ECR_REGISTRY
```

Advantages:

- Centralized configuration
- Less duplication
- Consistent platform defaults

Limitations:

- Changes can affect many repositories
- Repository owners may not immediately see where a value originated
- Incorrect organization-wide changes can create a broad blast radius

For critical configuration, document ownership and change procedures.

---

## Environment Variables

GitHub environments can provide environment-specific variables.

A common model is:

```text
development
staging
production
```

Each environment can have its own:

- Variables
- Secrets
- Protection rules
- Required reviewers
- Deployment history
- Branch/tag restrictions

This allows:

```text
staging:
  API_BASE_URL=staging.example.internal

production:
  API_BASE_URL=api.example.com
```

without hard-coding values into workflow YAML.

---

## Environment Selection

A deployment job can associate itself with an environment:

```yaml
jobs:
  deploy:
    environment: production
    runs-on: ubuntu-latest
```

This matters because environment-scoped configuration and protection rules are tied to that environment.

A common failure is expecting a production secret to be available before the job actually targets the production environment.

---

## Environment Protection

Production environments can require approval before deployment continues.

Conceptually:

```text
Build
 ↓
Artifact
 ↓
Staging
 ↓
Production Environment
 ↓
Required Review
 ↓
Production Deployment
```

Environment protection is a deployment security boundary, not merely configuration storage.

---

## Environment-Specific Secret Failure

### Symptom

A repository secret works, but a production secret appears unavailable.

### Possible Causes

- Secret exists only at environment scope.
- Job does not specify the environment.
- Wrong environment name.
- Environment protection has not completed.
- Workflow is running under an event where the secret is unavailable.

### Isolation

Check:

```yaml
environment: production
```

Then validate only whether the secret is present:

```yaml
- name: Validate deployment credential
  env:
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
  run: |
    if [[ -z "$DEPLOY_TOKEN" ]]; then
      echo "Deployment credential is unavailable"
      exit 1
    fi
```

Never print the value.

---

## Repository Secrets

Repository secrets are accessed through:

```yaml
secrets.NAME
```

Example:

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
```

Use repository secrets for credentials required by a repository but not specific to a deployment environment.

Examples:

```text
Third-party API credentials
Signing credentials
Test credentials
Repository-specific service credentials
```

---

## Organization Secrets

Organization secrets are useful when multiple repositories require the same credential.

Typical examples include:

```text
Shared package registry
Central security scanning service
Organization-level integration
```

Use repository/environment scoping where possible to reduce blast radius.

---

## Environment Secrets

Environment secrets are appropriate for environment-specific credentials:

```text
staging:
  DATABASE_PASSWORD
  AWS_ROLE_ARN

production:
  DATABASE_PASSWORD
  AWS_ROLE_ARN
```

This supports a clean separation:

```text
Same workflow
    ↓
Different environment
    ↓
Different credentials
```

---

## Secret Inheritance

Reusable workflows can receive secrets explicitly or use inheritance.

Explicit:

```yaml
jobs:
  deploy:
    uses: org/platform/.github/workflows/deploy.yml@v1
    secrets:
      AWS_ROLE_ARN: ${{ secrets.AWS_ROLE_ARN }}
```

Inheritance:

```yaml
jobs:
  deploy:
    uses: org/platform/.github/workflows/deploy.yml@v1
    secrets: inherit
```

`secrets: inherit` is convenient but broadens the secret interface.

For sensitive deployment workflows, explicit secret contracts are often easier to audit.

---

## Reusable Workflow Secret Failures

### Symptom

A secret exists in the caller repository but is unavailable inside the reusable workflow.

### Possible Causes

- Secret was not passed.
- `secrets: inherit` was not used where appropriate.
- Reusable workflow did not declare the required secret.
- Environment secret is being confused with repository secret.
- Caller and reusable workflow have different security boundaries.

### Isolation

Trace:

```text
Caller
 ↓
Workflow Call
 ↓
Secret Contract
 ↓
Reusable Workflow
 ↓
Job
 ↓
Step
```

Do not assume that repository secrets automatically become available inside every reusable workflow invocation.

---

## Secret Masking

GitHub attempts to mask secrets in logs.

Example:

```yaml
- name: Use credential
  env:
    TOKEN: ${{ secrets.API_TOKEN }}
  run: ./deploy.sh
```

However, masking should not be treated as a complete security control.

Avoid:

```bash
echo "$TOKEN"
```

and especially:

```bash
set -x
```

around commands that may expose credentials.

---

## Why Masking Is Not Enough

Secret values can potentially leak through:

- Command arguments
- Process output
- Debug logs
- Generated files
- Artifacts
- Test reports
- Exceptions
- Docker build output
- Third-party actions
- Application logs
- Shell tracing

The correct principle is:

```text
Do not expose
```

rather than:

```text
Expose safely because GitHub will mask it
```

---

## Secrets in Command Arguments

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
    -H "Authorization: Bearer $API_TOKEN" \
    https://api.example.com
```

Better still, use the authentication mechanism supported by the client without exposing credentials unnecessarily.

---

## Secrets in URLs

Avoid:

```text
https://user:password@example.com
```

Secrets embedded in URLs can appear in:

- Logs
- Error messages
- Proxy logs
- Application diagnostics
- Process listings

Use environment variables or supported credential mechanisms instead.

---

## Secrets and Docker Builds

Do not pass secrets as ordinary Docker build arguments:

```bash
docker build --build-arg API_TOKEN="$API_TOKEN" .
```

Build arguments can become part of build metadata or image history depending on usage.

For BuildKit-based builds, use secret mounts where supported:

```dockerfile
RUN --mount=type=secret,id=pypi_token \
    TOKEN="$(cat /run/secrets/pypi_token)" && \
    pip install --index-url "https://__token__:${TOKEN}@pypi.example.com/simple" \
    private-package
```

The CI system should also ensure the secret does not become part of the final image.

---

## Secrets and Artifacts

Never upload files containing credentials as debugging artifacts.

Dangerous example:

```yaml
- run: env > environment.txt

- uses: actions/upload-artifact@v4
  with:
    name: environment
    path: environment.txt
```

This can expose credentials.

Instead, selectively collect safe diagnostics:

```bash
printf 'runner_os=%s\n' "$RUNNER_OS"
printf 'python_version=%s\n' "$(python --version)"
```

---

## `$GITHUB_ENV`

`GITHUB_ENV` allows a step to create environment variables for subsequent steps in the same job.

Example:

```yaml
- name: Calculate version
  run: |
    VERSION="$(git rev-parse --short HEAD)"
    echo "APP_VERSION=$VERSION" >> "$GITHUB_ENV"

- name: Use version
  run: |
    echo "$APP_VERSION"
```

The important behavior is:

```text
Step A
  ↓
writes GITHUB_ENV
  ↓
Step B sees variable
```

The current step should not be treated as receiving the newly written value automatically.

---

## `$GITHUB_ENV` Failure

### Symptom

A variable written to `$GITHUB_ENV` appears unavailable immediately.

### Cause

The environment file communicates variables to subsequent steps.

Incorrect mental model:

```text
Current step writes env
 ↓
Current process automatically receives it
```

Correct model:

```text
Current step
 ↓
GITHUB_ENV
 ↓
Next step
```

---

## `$GITHUB_ENV` Security

Do not write untrusted content directly into the environment file without validation.

Avoid:

```bash
echo "CONFIG=$UNTRUSTED_INPUT" >> "$GITHUB_ENV"
```

if the input can contain workflow-command-sensitive or multiline content.

Normalize and validate values before exporting them.

---

## `$GITHUB_OUTPUT`

Outputs are preferable when data is logically an output rather than global job environment configuration.

Example:

```yaml
- id: metadata
  run: |
    VERSION="$(git rev-parse --short HEAD)"
    echo "version=$VERSION" >> "$GITHUB_OUTPUT"
```

Then:

```yaml
- name: Use metadata
  env:
    VERSION: ${{ steps.metadata.outputs.version }}
  run: |
    echo "$VERSION"
```

This creates a more explicit data dependency.

---

## `$GITHUB_PATH`

`GITHUB_PATH` can add directories to the runner's `PATH` for subsequent steps.

Example:

```yaml
- name: Add tool directory
  run: |
    echo "$HOME/.local/bin" >> "$GITHUB_PATH"
```

Later:

```yaml
- name: Run tool
  run: |
    my-tool --version
```

If a command works in one step but not another, inspect whether `GITHUB_PATH` was configured correctly.

---

## Variable Propagation Model

```mermaid
flowchart LR
    A[Workflow env] --> B[Job env]
    B --> C[Step env]
    C --> D[Shell Process]

    E[vars] --> C
    F[secrets] --> C
    G[inputs] --> C

    H[GITHUB_ENV] --> I[Later Steps]
    J[GITHUB_OUTPUT] --> K[Step Output]
    K --> L[Job Output]
    L --> M[needs]
    M --> N[Downstream Job]
```

This model is useful when deciding which mechanism to use.

---

## Choosing the Correct Mechanism

| Requirement | Recommended Mechanism |
|---|---|
| Static non-sensitive configuration | `vars` |
| Workflow-wide runtime value | `env` |
| Step-specific runtime value | Step `env` |
| Sensitive credential | `secrets` |
| Manual parameter | `inputs` |
| Data generated by a step | Step output |
| Data generated by a job | Job output |
| Large files | Artifact |
| Dependency reuse | Cache |
| AWS temporary identity | OIDC |

---

## Secrets vs AWS OIDC

For AWS deployments, avoid:

```text
AWS_ACCESS_KEY_ID secret
AWS_SECRET_ACCESS_KEY secret
```

as the default architecture for GitHub Actions.

Prefer:

```text
GitHub Actions
      ↓
OIDC token
      ↓
AWS STS
      ↓
IAM role
      ↓
Temporary credentials
      ↓
ECR / S3 / ECS / EC2 / Lambda
```

The workflow generally needs:

```yaml
permissions:
  id-token: write
  contents: read
```

The AWS IAM trust policy should restrict which GitHub identity can assume the role.

---

## AWS OIDC Troubleshooting

### Symptom

AWS authentication fails even though the workflow has an IAM role ARN.

### Possible Causes

- `id-token: write` missing.
- IAM trust policy mismatch.
- Wrong repository condition.
- Wrong branch/environment condition.
- Incorrect AWS account.
- Incorrect audience.
- Role ARN points to another account.
- Environment restrictions are inconsistent.

### Isolation

Check GitHub permissions:

```yaml
permissions:
  contents: read
  id-token: write
```

Then inspect the AWS identity after authentication:

```bash
aws sts get-caller-identity
```

This should be part of diagnostics, not credential logging.

---

## Secrets and Pull Requests

Fork pull requests require particular care.

A workflow triggered by an external fork should not automatically receive privileged secrets simply because the workflow file references:

```yaml
secrets.SOME_SECRET
```

The security model must assume:

```text
Pull Request
    ↓
Potentially untrusted code
```

This is especially important for:

- `pull_request`
- `pull_request_target`
- Self-hosted runners
- AWS OIDC
- Deployment credentials
- Third-party actions

---

## `pull_request` vs `pull_request_target`

The distinction is security-critical.

### `pull_request`

Generally intended for testing the pull request in a more isolated trust model.

### `pull_request_target`

Runs in the context of the base repository and therefore requires careful treatment of untrusted inputs and checked-out code.

Dangerous combination:

```text
pull_request_target
+
checkout PR code
+
secrets
+
self-hosted runner
```

Treat this as a privileged execution boundary.

---

## Environment Variables and Untrusted Input

Unsafe:

```yaml
run: |
  ./deploy.sh "${{ github.event.pull_request.title }}"
```

Safer:

```yaml
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: |
  printf 'PR title: %s\n' "$PR_TITLE"
```

For values that control behavior, validate them:

```bash
case "$TARGET_ENV" in
  staging|production)
    ;;
  *)
    echo "Invalid environment"
    exit 1
    ;;
esac
```

---

## Secret Availability by Event

A useful troubleshooting table:

| Situation | Secret Availability Considerations |
|---|---|
| Push to repository | Repository/environment rules apply |
| Same-repository PR | Depends on repository security model |
| Fork PR | Privileged secrets require particular caution and may be unavailable |
| `pull_request_target` | Base repository trust context; high caution |
| Manual dispatch | User input and environment rules apply |
| Reusable workflow | Secrets must be passed or inherited appropriately |
| Environment deployment | Environment-scoped secrets require correct environment association |

The exact availability depends on repository, organization, environment, and workflow configuration.

---

## Secret Rotation

Secrets should be treated as replaceable credentials.

Production lifecycle:

```text
Create
 ↓
Store
 ↓
Use
 ↓
Rotate
 ↓
Validate
 ↓
Revoke Old Credential
 ↓
Audit
```

Avoid workflows that require permanently embedded credentials.

For AWS, OIDC reduces the need for long-lived cloud credentials entirely.

---

## Secret Rotation Failure

### Symptom

A deployment suddenly fails after credential rotation.

### Possible Causes

- Workflow still references old secret.
- Environment secret was rotated but repository secret was not.
- External service has not accepted the new credential.
- Old credential was revoked before consumers were migrated.
- Reusable workflow receives a different secret scope.

### Prevention

Use staged credential rotation:

```text
Create new credential
 ↓
Update secret
 ↓
Validate consumers
 ↓
Monitor
 ↓
Revoke old credential
```

---

## Python Backend Example

A Django or FastAPI deployment commonly needs:

```text
DATABASE_URL
REDIS_URL
DJANGO_SECRET_KEY
API_TOKEN
AWS_REGION
```

Separate them appropriately:

```text
DATABASE_URL      → environment secret
REDIS_URL         → environment secret/config
DJANGO_SECRET_KEY → environment secret
API_TOKEN         → environment secret
AWS_REGION        → variable
```

Workflow:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: postgresql://localhost/test
      REDIS_URL: redis://localhost:6379/0

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

Use dedicated test credentials and services rather than production secrets.

---

## Django Example

```yaml
- name: Django checks
  env:
    DJANGO_SETTINGS_MODULE: config.settings.ci
    DATABASE_URL: postgresql://app:test-password@localhost/app_test
    REDIS_URL: redis://localhost:6379/0
  run: |
    python manage.py check
    python manage.py migrate --noinput
    python manage.py test
```

The workflow environment should not contain production credentials merely because the application is production-capable.

---

## FastAPI Example

```yaml
- name: API tests
  env:
    DATABASE_URL: postgresql://app:test-password@localhost/app_test
    REDIS_URL: redis://localhost:6379/0
  run: |
    pytest -q
```

For tests, prefer isolated service containers and test-specific credentials.

---

## Celery Configuration

A CI pipeline may need:

```text
REDIS_URL
CELERY_BROKER_URL
CELERY_RESULT_BACKEND
```

Do not automatically reuse production Redis credentials.

A safer integration test model is:

```text
GitHub Runner
    ↓
Redis Service Container
    ↓
Celery Worker
    ↓
pytest
```

This reduces dependency on external infrastructure and production secrets.

---

## Kafka Configuration

Integration tests involving Kafka may use:

```text
KAFKA_BOOTSTRAP_SERVERS
KAFKA_TOPIC
```

These are configuration values, not necessarily secrets.

Authentication credentials, certificates, or SASL passwords should be handled as secrets when required.

---

## PostgreSQL Configuration

A test job might define:

```yaml
env:
  PGHOST: localhost
  PGPORT: "5432"
  PGDATABASE: app_test
  PGUSER: app
  PGPASSWORD: test-password
```

Use disposable test credentials and isolate test databases.

Do not reuse production database credentials in CI.

---

## Environment Configuration Architecture

A production application often follows:

```text
Code
  +
Configuration
  +
Secrets
  +
Runtime Identity
```

The workflow should not bake environment-specific secrets into application artifacts.

Prefer:

```text
Same Docker image
      ↓
Staging configuration
      ↓
Production configuration
```

This supports build-once/deploy-many.

---

## Build Once, Configure Per Environment

A production pipeline should preferably:

```text
Source
 ↓
Build
 ↓
Immutable Docker Image
 ↓
Staging
 ↓
Approval
 ↓
Production
```

Configuration is injected at runtime:

```text
Image
+
Environment Variables
+
Environment Secrets
+
Cloud Identity
```

This avoids rebuilding the application solely because the environment changed.

---

## Docker and Runtime Secrets

Avoid baking secrets into:

```dockerfile
ENV DATABASE_PASSWORD=...
```

or:

```dockerfile
ARG API_TOKEN=...
```

The image should remain environment-independent.

Inject runtime configuration through:

- ECS task configuration
- Kubernetes Secrets
- Environment-specific deployment configuration
- External secret managers
- GitHub environment secrets for deployment operations

---

## Kubernetes Example

A CI workflow should generally build and publish the image rather than embedding production credentials into the image.

Conceptually:

```text
GitHub Actions
 ↓
Docker Build
 ↓
Registry
 ↓
Kubernetes Deployment
 ↓
Secret / ConfigMap
 ↓
Pod
```

Secrets should be provided through the runtime platform's secret mechanism.

---

## Environment Drift

A common production issue is:

```text
Staging works
Production fails
```

because configuration differs unexpectedly.

Track configuration differences explicitly:

```text
Environment
 ↓
Variables
 ↓
Secrets
 ↓
IAM role
 ↓
Network access
 ↓
Service dependencies
```

Do not solve every difference by copying production secrets into staging.

---

## Environment Parity

Useful parity dimensions include:

| Area | Staging | Production |
|---|---|---|
| Docker image | Same digest | Same digest |
| Runtime | Same major version | Same major version |
| Database engine | Compatible | Production |
| Redis | Compatible | Production |
| IAM model | Similar | Production |
| Network model | Similar | Production |
| Environment variables | Different values | Different values |
| Secrets | Separate | Separate |
| Artifact | Same | Same |

The goal is similar execution behavior without sharing production credentials.

---

## Troubleshooting Environment Variables

### Symptom

`APP_ENV` has the wrong value.

### Possible Causes

- Workflow-level `env`
- Job-level `env`
- Step-level `env`
- `vars.APP_ENV`
- Shell assignment
- Action-specific environment

### Isolation

Search for all definitions:

```bash
grep -R "APP_ENV" .github/workflows
```

Then inspect the final environment safely:

```yaml
- name: Check environment
  env:
    VALUE: ${{ env.APP_ENV }}
  run: |
    printf 'APP_ENV=%s\n' "$VALUE"
```

Do not dump the complete environment in production workflows.

---

## Troubleshooting Secrets

### Symptom

Secret is empty.

### Possible Causes

```text
Wrong name
Wrong scope
Wrong environment
Wrong reusable workflow contract
Fork restrictions
Event restrictions
Secret was not inherited
```

### Isolation

Check only presence:

```yaml
- name: Check credential availability
  env:
    TOKEN: ${{ secrets.API_TOKEN }}
  run: |
    if [[ -n "$TOKEN" ]]; then
      echo "Credential is available"
    else
      echo "Credential is unavailable"
      exit 1
    fi
```

Never output the value.

---

## Troubleshooting `$GITHUB_ENV`

### Symptom

Variable is missing in the next command.

### Checks

```text
Was the variable written to GITHUB_ENV?
Was the syntax correct?
Is the next command in a later step?
Was the variable overridden?
```

Correct:

```yaml
- name: Set value
  run: echo "VERSION=1.2.3" >> "$GITHUB_ENV"

- name: Use value
  run: echo "$VERSION"
```

---

## Troubleshooting `$GITHUB_OUTPUT`

### Symptom

Downstream step cannot read output.

Check:

```text
Producer step has id
 ↓
Writes to GITHUB_OUTPUT
 ↓
Output name matches
 ↓
Consumer references correct step
```

Example:

```yaml
- id: version
  run: echo "value=1.2.3" >> "$GITHUB_OUTPUT"

- run: echo "${{ steps.version.outputs.value }}"
```

---

## Troubleshooting Environment Protection

### Symptom

Production secret is unavailable or deployment does not proceed.

Check:

```text
environment name
required reviewers
deployment protection
branch restrictions
environment secret
environment variable
job environment association
```

Example:

```yaml
deploy:
  environment:
    name: production
```

The environment configuration must correspond to the intended deployment target.

---

## Troubleshooting Reusable Workflows

Trace the complete contract:

```text
Caller
 ↓
workflow_call
 ↓
inputs
 ↓
secrets
 ↓
Reusable Workflow
 ↓
Job
 ↓
Step
```

Example:

```yaml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
    secrets:
      AWS_ROLE_ARN:
        required: true
```

Caller:

```yaml
jobs:
  deploy:
    uses: org/platform/.github/workflows/deploy.yml@v1
    with:
      environment: staging
    secrets:
      AWS_ROLE_ARN: ${{ secrets.AWS_ROLE_ARN }}
```

Keep the interface explicit.

---

## Troubleshooting Fork Pull Requests

### Symptom

Tests pass on internal branches but fail for fork pull requests.

### Possible Causes

- Secret unavailable.
- Different token permissions.
- Different event payload.
- Different checkout behavior.
- Security restrictions.

### Correct Approach

Separate:

```text
Untrusted validation
```

from:

```text
Privileged deployment
```

A fork PR should not require production credentials merely to run tests.

---

## Secret Exposure Through Debugging

Avoid:

```yaml
- run: env
```

Avoid:

```bash
printenv
```

Avoid:

```bash
set -x
```

Avoid:

```yaml
- run: echo "${{ toJSON(github) }}"
```

Instead collect targeted safe diagnostics.

---

## Safe Diagnostic Pattern

```yaml
- name: Diagnostics
  env:
    EVENT: ${{ github.event_name }}
    REF: ${{ github.ref }}
    RUNNER_OS: ${{ runner.os }}
    APP_ENV: ${{ vars.APP_ENV }}
  run: |
    set -euo pipefail

    printf 'event=%s\n' "$EVENT"
    printf 'ref=%s\n' "$REF"
    printf 'runner_os=%s\n' "$RUNNER_OS"
    printf 'app_env=%s\n' "$APP_ENV"
```

For secrets:

```bash
if [[ -n "$TOKEN" ]]; then
  echo "TOKEN is configured"
else
  echo "TOKEN is missing"
fi
```

---

## Production Secret Architecture

A mature architecture separates configuration responsibilities:

```mermaid
flowchart TD
    A[Git Repository] --> B[GitHub Actions]

    B --> C[Non-sensitive Variables]
    B --> D[Environment Secrets]
    B --> E[OIDC Identity]

    C --> F[Workflow Configuration]
    D --> G[Deployment]
    E --> H[AWS STS]

    H --> I[IAM Role]
    I --> J[ECR / ECS / S3 / EC2 / Lambda]

    G --> K[Runtime Platform]
    K --> L[Application]
```

The CI system orchestrates access rather than becoming the permanent storage location for every application credential.

---

## Security Boundaries

A production workflow should distinguish:

```text
Untrusted code
     ↓
Read-only validation
     ↓
Trusted build
     ↓
Artifact
     ↓
Protected deployment
     ↓
Runtime identity
```

Do not allow untrusted code to inherit the credentials of the deployment stage.

---

## Least Privilege

Use narrow permissions:

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

Avoid broad permissions such as:

```yaml
permissions: write-all
```

unless there is a documented requirement.

Job-level permissions can further isolate privileged operations.

---

## Separate CI and CD Credentials

A strong production design is:

```text
PR / CI
 ↓
No production credentials

Build
 ↓
Registry permissions

Staging
 ↓
Staging deployment role

Production
 ↓
Production deployment role
```

This limits blast radius.

---

## Monitoring Secret and Variable Failures

Monitor:

- Failed deployments
- Missing environment configuration
- Authentication failures
- AWS STS failures
- Registry authentication failures
- Secret rotation failures
- Environment approval failures

Useful metadata:

```text
workflow
run_id
repository
environment
commit SHA
deployment
failure domain
```

Do not include secret values.

---

## Reliability Considerations

Avoid hidden configuration dependencies.

A workflow should fail early if required configuration is missing:

```yaml
- name: Validate required configuration
  env:
    AWS_REGION: ${{ vars.AWS_REGION }}
    ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
  run: |
    set -euo pipefail

    [[ -n "$AWS_REGION" ]] || {
      echo "AWS_REGION is missing"
      exit 1
    }

    [[ -n "$ECR_REPOSITORY" ]] || {
      echo "ECR_REPOSITORY is missing"
      exit 1
    }
```

This is preferable to failing halfway through deployment.

---

## Fail Fast on Configuration

Production deployment should validate:

```text
Environment
Region
Artifact identity
AWS role
Registry
Required configuration
```

before performing destructive or irreversible operations.

---

## Configuration Validation Job

A dedicated validation job can simplify deployment workflows:

```text
Build
 ↓
Configuration Validation
 ↓
Security Validation
 ↓
Approval
 ↓
Deployment
```

Example:

```yaml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Validate environment
        env:
          AWS_REGION: ${{ vars.AWS_REGION }}
          ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
        run: |
          set -euo pipefail
          [[ -n "$AWS_REGION" ]]
          [[ -n "$ECR_REPOSITORY" ]]
```

---

## Cost Considerations

Centralized variables and reusable workflows reduce duplication.

However:

- Large organization-level changes have a broad blast radius.
- Excessive configuration validation jobs increase runner usage.
- External secret managers can introduce operational and service costs.
- Repeated environment configuration can increase maintenance overhead.

Prefer simple, explicit configuration boundaries.

---

## High Availability Considerations

CI/CD configuration should not become a single point of deployment failure.

For critical systems:

```text
Immutable artifact
+
Reproducible workflow
+
Protected environments
+
Independent deployment identity
+
Rollback path
```

The application should not depend on a mutable CI workspace after deployment.

---

## Disaster Recovery

Secrets and variables are part of recovery planning.

Document:

```text
Who owns each credential?
Where is it configured?
How is it rotated?
How is it restored?
Which environment uses it?
Which AWS account does it access?
```

For AWS deployments, IAM roles and OIDC trust policies should be managed as code where practical.

---

## GitHub CLI Operations

List workflows:

```bash
gh workflow list
```

View a workflow:

```bash
gh workflow view deploy.yml
```

List runs:

```bash
gh run list
```

Inspect a run:

```bash
gh run view <run-id>
```

View failed logs:

```bash
gh run view <run-id> --log-failed
```

Rerun failed jobs:

```bash
gh run rerun <run-id> --failed
```

List repository variables:

```bash
gh variable list
```

List repository secrets without revealing values:

```bash
gh secret list
```

The CLI should be used to inspect configuration metadata, not to expose credential contents.

---

## Production CI/CD Configuration Flow

A mature pipeline can be modeled as:

```mermaid
flowchart LR
    A[Pull Request] --> B[Lint]
    B --> C[Unit Tests]
    C --> D[Integration Tests]
    D --> E[Security Scan]
    E --> F[Matrix]
    F --> G[Build]
    G --> H[Immutable Docker Image]
    H --> I[ECR]
    I --> J[Staging]
    J --> K[Approval]
    K --> L[Production]
    L --> M[Monitoring]
    M --> N[Rollback]
```

Configuration and credentials should follow controlled boundaries throughout the pipeline:

```text
PR
 ↓
No production secrets
 ↓
Build
 ↓
Registry identity
 ↓
Staging identity
 ↓
Production approval
 ↓
Production identity
```

---

## Configuration Data Flow

```text
Repository Variables
        ↓
Workflow
        ↓
Job Environment
        ↓
Step Environment
        ↓
Process

Environment Secrets
        ↓
Protected Job
        ↓
Deployment

OIDC
        ↓
AWS STS
        ↓
Temporary Credentials
        ↓
AWS API
```

The deployment artifact itself should remain independent from environment-specific credentials.

---

## Common Mistakes

### Storing Secrets in Repository Variables

Variables are not a substitute for secrets.

### Hard-Coding Credentials

Credentials should not be embedded in workflow YAML, Dockerfiles, scripts, or source code.

### Printing `env`

This can expose sensitive values.

### Using `set -x`

Shell tracing can reveal credentials.

### Reusing Production Secrets in CI Tests

Tests should use disposable credentials and isolated services.

### Forgetting Environment Association

Environment secrets are not automatically available to arbitrary jobs.

### Using `secrets: inherit` Everywhere

Inheritance can create unnecessarily broad secret access.

### Rebuilding for Every Environment

Prefer build once and promote the same immutable artifact.

### Putting Secrets in Docker Build Arguments

Use supported BuildKit secret mechanisms instead.

### Assuming Masking Solves Exposure

Masking is defense in depth, not permission to log sensitive values.

---

## Interview Traps

### Is `env` the Same as `vars`?

No.

`env` is runtime environment configuration defined in workflow YAML, while `vars` provides configuration variables at supported repository, organization, and environment scopes.

---

### Are GitHub Secrets Environment Variables?

A secret can be injected into an environment variable, but the `secrets` context and shell environment are different concepts.

Example:

```yaml
env:
  TOKEN: ${{ secrets.API_TOKEN }}
```

---

### Can a Step Modify an Environment Variable for a Previous Step?

No.

Environment changes are designed to affect subsequent steps through mechanisms such as `GITHUB_ENV`.

---

### Can a Secret Be Passed Through `$GITHUB_OUTPUT`?

Technically workflow mechanisms can transport values, but secrets should not be casually propagated through outputs because outputs may become visible to downstream workflow logic and logs.

Prefer direct secret injection where the credential is needed.

---

### Should AWS Access Keys Be Stored as GitHub Secrets?

For AWS deployments, prefer GitHub OIDC and short-lived STS credentials instead of long-lived access keys.

---

### Why Does a Secret Work in One Environment but Not Another?

Check:

```text
Secret scope
Environment association
Environment name
Protection rules
Workflow event
Reusable workflow contract
```

---

### Why Does a Variable Have a Different Value in a Step?

Check:

```text
Workflow env
Job env
Step env
vars
Shell assignments
```

The value may be overridden at a more specific scope.

---

### Why Does a Fork PR Not Have the Same Secrets?

Because untrusted fork code must not automatically receive privileged repository credentials.

This is a security boundary, not merely a configuration inconvenience.

---

## Senior-Level Design Principles

### Treat Configuration as an API

A reusable workflow should define:

```text
Inputs
Secrets
Outputs
Environment requirements
Permissions
```

rather than depending on hidden repository configuration.

---

### Separate Configuration From Artifact

Build:

```text
Immutable artifact
```

Deploy with:

```text
Environment configuration
+
Runtime secrets
+
Cloud identity
```

This supports reproducible promotion.

---

### Prefer Short-Lived Credentials

For AWS:

```text
GitHub
 ↓
OIDC
 ↓
STS
 ↓
Temporary credentials
```

This reduces long-lived credential exposure.

---

### Fail Closed

If:

```text
Environment unknown
Credential missing
AWS role unavailable
Artifact missing
Configuration invalid
```

the deployment should stop.

Do not silently select defaults for privileged operations.

---

### Keep Privileged Jobs Small

A production deployment job should receive only what it needs:

```text
contents: read
id-token: write
deployment-specific secrets
deployment-specific environment
```

Avoid giving broad credentials to test and lint jobs.

---

## Production Configuration Checklist

### Variables

```text
[ ] Non-sensitive values use vars where appropriate
[ ] Workflow env is not unnecessarily global
[ ] Job-specific values are scoped to jobs
[ ] Step-specific values are scoped to steps
[ ] Overrides are documented
```

### Secrets

```text
[ ] Secrets are stored in appropriate scopes
[ ] Production credentials are environment-scoped where appropriate
[ ] Secrets are never printed
[ ] Secrets are not placed in artifacts
[ ] Secrets are not embedded in Docker images
[ ] Rotation procedures exist
```

### Reusable Workflows

```text
[ ] Secret contract is explicit
[ ] Inputs are typed
[ ] Required secrets are declared
[ ] secrets: inherit is used deliberately
```

### Security

```text
[ ] Fork workflows do not receive unnecessary credentials
[ ] pull_request_target is treated as privileged
[ ] Untrusted input is not interpolated into shell commands
[ ] GITHUB_TOKEN permissions are minimized
[ ] AWS uses OIDC where appropriate
```

### Deployment

```text
[ ] Environment is explicitly selected
[ ] Environment protection is enabled where required
[ ] Same immutable artifact is promoted
[ ] Deployment identity is environment-specific
[ ] Rollback does not depend on rebuilding
```

---

## Key Takeaways

- Treat `env`, `vars`, `secrets`, `inputs`, outputs, artifacts, and caches as **different data-flow mechanisms**, each with a specific purpose and security boundary.
- Troubleshoot configuration systematically by tracing **scope → event → environment → workflow/job/step → runtime process**, rather than immediately changing YAML.
- Keep secrets out of logs, artifacts, Docker images, command arguments, and untrusted workflows; masking is not a substitute for preventing exposure.
- For production AWS deployments, prefer **OIDC → STS → temporary credentials** and keep privileged deployment identity separate from ordinary CI jobs.
- Build immutable artifacts once, inject environment-specific configuration at deployment/runtime, validate required configuration early, and fail closed when credentials or deployment configuration are missing.