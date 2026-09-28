# 06- Secrets

## Overview

Secrets are sensitive values required by CI/CD workflows, applications, deployment systems, and external services. In GitHub Actions, secrets provide a controlled mechanism for supplying credentials and other sensitive configuration without committing them to source code.

Typical secrets include:

- Database passwords
- API tokens
- Private keys
- Third-party credentials
- Deployment credentials
- Signing keys
- Webhook secrets

For production CI/CD, secret management is not simply a matter of hiding values in YAML. The complete security model includes:

```text
Secret Storage
      ↓
Secret Access
      ↓
Workflow Permissions
      ↓
Runner Execution
      ↓
Command / Action
      ↓
External System
      ↓
Secret Rotation and Audit
```

The existing CI/CD notes explicitly recommend using GitHub Secrets instead of storing credentials in code and identify OIDC as the preferred modern approach for AWS authentication because it avoids long-lived credentials. :chatgpt-content-reference{index="0"}

A secure pipeline should follow these principles:

- Never commit secrets to source control.
- Give jobs only the secrets they require.
- Prefer short-lived credentials over long-lived credentials.
- Avoid exposing secrets to untrusted code.
- Do not print secrets in logs.
- Separate CI secrets from production deployment credentials.
- Use protected environments for sensitive deployments.
- Rotate credentials and remove obsolete secrets.
- Prefer workload identity mechanisms such as OIDC when supported.

## What GitHub Actions Secrets Provide

GitHub Actions exposes configured secrets through the `secrets` context.

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Run integration tests
        env:
          DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
        run: pytest
```

The workflow source contains only the secret name:

```text
DATABASE_PASSWORD
```

The actual value is stored outside the workflow source.

The basic model is:

```text
GitHub Secret Store
        |
        | secrets.<NAME>
        v
Workflow
        |
        v
Job / Step
        |
        v
Process Environment
```

Secrets are therefore an input to workflow execution, not application configuration that should be hardcoded into the repository.

## Why Secrets Exist

Without a secret-management mechanism, teams commonly make unsafe choices:

```yaml
env:
  API_TOKEN: "abc123"
```

or:

```python
API_TOKEN = "abc123"
```

or:

```dockerfile
ENV API_TOKEN=abc123
```

These approaches can expose credentials through:

- Git history
- Pull requests
- Code review
- Docker image layers
- Build logs
- Backups
- Artifact repositories
- Local clones
- Developer machines

The safer model is:

```text
Source Code
    |
    | no secret values
    v
GitHub Actions
    |
    | secret reference
    v
Secret Store
    |
    v
Trusted Job
    |
    v
Target System
```

## Types of GitHub Actions Secrets

GitHub Actions supports secrets at different administrative scopes.

| Scope | Typical use | Example |
|---|---|---|
| Repository | Application-specific credentials | `STRIPE_API_KEY` |
| Organization | Shared credentials across repositories | Common integration token |
| Environment | Deployment-specific credentials | Production database credential |

Environment secrets are particularly useful for staging and production because access can be tied to a protected deployment environment.

A practical design is:

```text
Organization
    |
    +-- Shared non-production integration
    |
Repository
    |
    +-- Application-specific secrets
    |
Environment
    |
    +-- staging secrets
    +-- production secrets
```

Avoid creating a single organization-wide credential when repositories can use narrower identities.

## Repository Secrets

Repository secrets belong to a specific repository.

Example:

```yaml
- name: Run integration tests
  env:
    TEST_API_TOKEN: ${{ secrets.TEST_API_TOKEN }}
  run: pytest
```

Repository secrets are appropriate when:

- only one repository needs the credential
- the credential is specific to the application
- the secret does not need environment-specific values

Examples:

```text
TEST_API_TOKEN
SENTRY_AUTH_TOKEN
PACKAGE_REGISTRY_TOKEN
```

A repository secret should not automatically be exposed to every job.

## Organization Secrets

Organization secrets allow centralized secret management across multiple repositories.

They are useful when multiple repositories genuinely share a credential or integration.

Examples:

```text
INTERNAL_PACKAGE_TOKEN
SHARED_SECURITY_SCAN_TOKEN
ORGANIZATION_INTEGRATION_TOKEN
```

However, broad availability increases blast radius.

Prefer repository or environment scope when a secret is not genuinely shared.

## Environment Secrets

Environment secrets are associated with GitHub Environments such as:

```text
development
staging
production
```

A deployment job references its target environment:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest

    environment:
      name: production

    steps:
      - name: Deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: ./scripts/deploy.sh
```

This provides a useful separation:

```text
Staging
  |
  +-- STAGING_DATABASE_URL
  +-- STAGING_API_TOKEN
  +-- STAGING_DEPLOY_TOKEN

Production
  |
  +-- PRODUCTION_DATABASE_URL
  +-- PRODUCTION_API_TOKEN
  +-- PRODUCTION_DEPLOY_TOKEN
```

The workflow can remain largely identical while the environment supplies different sensitive values.

## Secret Scope and Blast Radius

Secret scope directly affects the potential impact of compromise.

Consider:

```text
One organization-wide production credential
              |
              +-- Repository A
              +-- Repository B
              +-- Repository C
              +-- Repository D
```

A compromised workflow in one repository may expose a credential usable elsewhere.

A narrower model is:

```text
Repository A
    |
    +-- Repository-specific credential

Repository B
    |
    +-- Repository-specific credential

Production Environment
    |
    +-- Production deployment credential
```

Use the narrowest scope that satisfies the actual requirement.

## Referencing Secrets

Secrets are referenced using:

```yaml
${{ secrets.SECRET_NAME }}
```

Example:

```yaml
- name: Call internal API
  env:
    API_TOKEN: ${{ secrets.INTERNAL_API_TOKEN }}
  run: |
    python scripts/check_service.py
```

Prefer environment injection when a command or application naturally consumes environment variables.

For example:

```python
import os

token = os.environ["API_TOKEN"]
```

For larger Python applications, use a configuration layer that validates required settings.

## Passing Secrets to Commands

Avoid embedding secrets directly into shell command strings.

Less desirable:

```yaml
- name: Deploy
  run: ./deploy.sh --token "${{ secrets.DEPLOY_TOKEN }}"
```

Prefer:

```yaml
- name: Deploy
  env:
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
  run: ./deploy.sh
```

The script can consume:

```bash
#!/usr/bin/env bash

set -euo pipefail

./deployment-client --token "$DEPLOY_TOKEN"
```

This does not make the secret universally safe, but it reduces unnecessary exposure through command construction and makes the secret boundary clearer.

## Secret Masking

GitHub Actions attempts to mask configured secret values when they appear in workflow logs.

Do not rely on masking as the primary security control.

Bad:

```yaml
- name: Debug credentials
  run: echo "${{ secrets.API_TOKEN }}"
```

Even if the value is masked, intentionally writing secrets to logs is poor security practice.

Instead:

```yaml
- name: Verify configuration
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
  run: |
    if [[ -z "$API_TOKEN" ]]; then
      echo "::error::API_TOKEN is not configured"
      exit 1
    fi
```

This verifies availability without exposing the value.

## Masking Limitations

Secret masking is based on values GitHub knows should be masked. Do not assume that every transformation of a secret will also be recognized.

Potential transformations include:

```text
Secret
  |
  +-- Base64 encoding
  +-- Substring extraction
  +-- JSON serialization
  +-- URL encoding
  +-- Concatenation
  +-- Hashing
```

For example:

```bash
echo "$API_TOKEN" | base64
```

The encoded representation may not be treated identically to the original secret.

The safest approach is to avoid producing secret-derived output altogether.

## Secret Exposure Through Environment Variables

Environment variables are convenient but can still be exposed by poorly designed code.

For example:

```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}

steps:
  - run: env
```

The `env` command may expose sensitive values to the workflow log.

Avoid diagnostic commands such as:

```bash
env
printenv
set
```

when secrets are present in the environment.

Instead, inspect only safe metadata:

```bash
echo "Environment: $APP_ENV"
echo "Region: $AWS_REGION"
```

## Secret Exposure Through Artifacts

Never intentionally upload secrets as artifacts.

Bad:

```yaml
- name: Collect diagnostics
  run: env > diagnostics.txt

- uses: actions/upload-artifact@v4
  with:
    name: diagnostics
    path: diagnostics.txt
```

The file may contain credentials.

A safer diagnostic file contains explicitly selected values:

```bash
{
  echo "Environment: $APP_ENV"
  echo "Python: $(python --version)"
  echo "Git SHA: $GITHUB_SHA"
} > diagnostics.txt
```

Artifacts should contain build outputs, reports, logs, or diagnostics that are safe to retain.

## Secret Exposure Through Docker Images

Never bake runtime secrets into Docker images.

Bad:

```dockerfile
FROM python:3.12-slim

ENV DATABASE_PASSWORD=production-password

COPY . /app
```

The image can be pushed to a registry and retained indefinitely.

Prefer runtime injection:

```text
Docker Image
     |
     | runtime configuration
     v
Container
     |
     +-- DATABASE_URL
     +-- API_TOKEN
     +-- APP_ENV
```

For AWS workloads, sensitive runtime configuration can be supplied through managed services such as AWS Secrets Manager and injected into ECS tasks using IAM-controlled access. The existing ECS notes recommend Secrets Manager for database credentials, API tokens, and third-party secrets, with KMS used for encryption. :chatgpt-content-reference{index="1"}

## Secret Management vs Runtime Secret Storage

GitHub Actions Secrets and application runtime secret stores solve different problems.

| Mechanism | Primary purpose |
|---|---|
| GitHub Actions Secrets | Secrets required by GitHub workflows |
| AWS Secrets Manager | Runtime application secrets in AWS |
| AWS Systems Manager Parameter Store | Configuration and parameter storage |
| Kubernetes Secrets | Kubernetes workload configuration |
| External secret manager | Centralized application/runtime secret management |

For example:

```text
GitHub Actions
      |
      | deployment identity
      v
AWS
      |
      v
Secrets Manager
      |
      v
ECS Task
      |
      v
Application
```

A deployment pipeline does not necessarily need to retrieve every application secret itself.

Prefer letting the runtime platform retrieve runtime secrets when possible.

## GitHub Secrets vs AWS Secrets Manager

A common production architecture is:

```text
GitHub Actions
    |
    | CI/CD credentials
    v
GitHub Secrets / OIDC
    |
    v
AWS IAM
    |
    v
ECS
    |
    v
AWS Secrets Manager
    |
    v
Application Container
```

The deployment pipeline needs enough permission to deploy, while the application receives only the runtime secrets it requires.

This creates two separate security boundaries:

```text
CI/CD Identity
        |
        v
Deployment Permissions

Application Identity
        |
        v
Runtime Permissions
```

The ECS notes specifically distinguish task roles from infrastructure/execution roles and recommend using Secrets Manager rather than hardcoded application credentials. :chatgpt-content-reference{index="2"}

## GITHUB_TOKEN

GitHub Actions automatically provides a `GITHUB_TOKEN` for repository operations.

It should be treated as a credential.

Do not assume that because GitHub creates it automatically, it is unrestricted or harmless.

Explicitly define permissions:

```yaml
permissions:
  contents: read
```

For a deployment job that needs OIDC:

```yaml
permissions:
  contents: read
  id-token: write
```

A job should receive only the permissions it requires.

## Job-Level Permissions

Permissions can be reduced at the job level.

```yaml
jobs:
  test:
    permissions:
      contents: read
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - run: pytest

  deploy:
    permissions:
      contents: read
      id-token: write
    runs-on: ubuntu-latest

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE }}
          aws-region: ${{ vars.AWS_REGION }}
```

This creates a smaller security boundary:

```text
Test Job
  |
  +-- contents: read

Deploy Job
  |
  +-- contents: read
  +-- id-token: write
```

The test job does not need permission to obtain AWS credentials.

## Secret Access and Job Isolation

Do not expose production credentials to jobs that do not require them.

A strong pipeline might look like:

```text
Lint
  |
  +-- No secrets

Unit Tests
  |
  +-- Test configuration only

Integration Tests
  |
  +-- Test credentials

Build
  |
  +-- Registry access if required

Staging Deploy
  |
  +-- Staging deployment identity

Production Deploy
  |
  +-- Production deployment identity
```

This limits the impact of a compromised step or third-party action.

## Pull Requests From Forks

Forked pull requests require special consideration because code comes from a repository outside the normal trust boundary.

A malicious pull request could attempt to access:

```text
Environment variables
Secrets
GITHUB_TOKEN
Filesystem contents
Cloud credentials
Network resources
```

Never assume that pull request code is trusted merely because the pull request is opened against your repository.

A secure conceptual boundary is:

```text
Forked Pull Request
        |
        v
Untrusted Code
        |
        +-- No production secrets
        +-- Minimal permissions
        +-- Isolated validation
```

Privileged deployment should occur only from trusted workflow contexts.

## `pull_request` vs `pull_request_target`

The distinction is critical.

### `pull_request`

```yaml
on:
  pull_request:
```

This is generally appropriate for validating pull request code without granting that code privileged repository access.

Typical use:

```text
Checkout PR
   |
   v
Lint
   |
   v
Tests
   |
   v
Security Checks
```

### `pull_request_target`

```yaml
on:
  pull_request_target:
```

This runs in the context of the base repository and therefore requires additional caution.

A dangerous pattern is:

```text
pull_request_target
       |
       v
Checkout attacker-controlled code
       |
       v
Execute code
       |
       v
Access secrets
       |
       v
Exfiltrate credentials
```

The fundamental rule is:

> Never combine privileged secrets with execution of untrusted pull request code.

`pull_request_target` can be useful for trusted automation that needs access to base-repository configuration, but it should not be treated as a safer version of `pull_request` for arbitrary code execution.

## Script Injection

Untrusted GitHub event data can become shell injection when interpolated directly into commands.

Potentially untrusted data includes:

- Pull request titles
- Branch names
- Commit messages
- Issue titles
- Issue bodies
- Workflow inputs
- Repository dispatch payloads

Avoid:

```yaml
- name: Process PR title
  run: echo "${{ github.event.pull_request.title }}"
```

Prefer passing the value as an environment variable:

```yaml
- name: Process PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: |
    printf '%s\n' "$PR_TITLE"
```

The shell receives the value as data rather than having the workflow engine construct executable shell syntax from it.

For complex processing, use a trusted script and validate the input.

## Secret Inheritance

Reusable workflows can explicitly receive secrets.

Example:

```yaml
jobs:
  deploy:
    uses: ./.github/workflows/deploy.yml
    secrets:
      DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

Reusable workflows can also use:

```yaml
secrets: inherit
```

Example:

```yaml
jobs:
  deploy:
    uses: acme/platform-workflows/.github/workflows/deploy.yml@v1
    secrets: inherit
```

Inheritance is convenient for organization-wide workflows but increases the amount of secret state available to the called workflow.

For sensitive deployment pipelines, explicitly declaring required secrets provides a clearer security contract.

## Reusable Workflow Secret Contracts

A reusable workflow can define its expected secret interface:

```yaml
on:
  workflow_call:
    secrets:
      AWS_DEPLOY_ROLE:
        required: true
```

The caller provides:

```yaml
jobs:
  deploy:
    uses: acme/platform-workflows/.github/workflows/deploy.yml@v1
    secrets:
      AWS_DEPLOY_ROLE: ${{ secrets.AWS_DEPLOY_ROLE }}
```

This makes dependencies visible.

A reusable deployment workflow should avoid silently depending on repository-specific secrets that callers may not know about.

## Secret Rotation

Secrets should have a lifecycle.

```text
Create
  ↓
Use
  ↓
Monitor
  ↓
Rotate
  ↓
Validate
  ↓
Revoke Old Credential
```

Rotation should be designed before the first production deployment.

For example:

```text
Credential A active
      |
      v
Create Credential B
      |
      v
Deploy / Validate B
      |
      v
Switch consumers
      |
      v
Revoke Credential A
```

Avoid rotation procedures that require downtime.

## Secret Rotation Considerations

Before rotating a credential, identify:

- Consumers
- Workflow references
- Environment scopes
- Runtime services
- External integrations
- Rotation dependencies
- Rollback procedure
- Audit requirements

A secret used by GitHub Actions may have consumers in:

```text
Repository workflows
Reusable workflows
Deployment scripts
Terraform
External systems
```

Rotation must account for all of them.

## Long-Lived Credentials

Long-lived credentials increase operational risk.

For example:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

can remain valid until explicitly rotated or revoked.

The existing CI/CD notes recommend GitHub OIDC instead of long-term AWS credentials because OIDC provides short-lived credentials and reduces secret-management requirements. :chatgpt-content-reference{index="3"}

For AWS deployments, prefer:

```text
GitHub Actions
      |
      | OIDC token
      v
AWS STS
      |
      v
Temporary Credentials
      |
      v
IAM Role
      |
      v
AWS Service
```

## GitHub Actions OIDC With AWS

A deployment job can request an OIDC token:

```yaml
permissions:
  contents: read
  id-token: write
```

Then configure AWS credentials:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v5
  with:
    role-to-assume: ${{ vars.AWS_DEPLOY_ROLE }}
    aws-region: ${{ vars.AWS_REGION }}
```

The workflow can validate the resulting identity:

```yaml
- name: Verify AWS identity
  run: aws sts get-caller-identity
```

The key difference is:

```text
Long-lived model

GitHub
  |
  +-- permanent AWS access key
  |
  v
AWS


OIDC model

GitHub
  |
  +-- short-lived identity token
  |
  v
AWS STS
  |
  +-- temporary credentials
  |
  v
AWS
```

## IAM Trust Policy

OIDC security depends heavily on the IAM trust relationship.

Do not create a role that effectively allows every repository or branch to assume the role.

The trust policy should constrain the GitHub identity according to the deployment model, such as:

```text
Repository
Branch
Environment
Organization
Workflow identity
```

A production deployment role should have a significantly narrower trust boundary than a general CI role.

## AWS Permissions

The deployment role should follow least privilege.

For an ECR/ECS deployment, permissions might include only the operations actually required by the deployment mechanism.

For example:

```text
ECR
  |
  +-- authenticate
  +-- push image
  +-- inspect image

ECS
  |
  +-- describe service
  +-- update service
  +-- describe deployment
```

Avoid:

```text
AdministratorAccess
```

for CI/CD roles.

The existing ECS security notes emphasize least privilege and separation of task and execution roles. :chatgpt-content-reference{index="4"}

## Secrets and ECR

A typical secure image pipeline is:

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
      v
Amazon ECR
      |
      v
Immutable Image
```

The existing CI/CD notes recommend versioned images and warn against relying on `latest` because it makes rollbacks and auditing difficult. :chatgpt-content-reference{index="5"}

Secrets should not be embedded into the image during this process.

## Secrets and ECS

For ECS applications, distinguish deployment credentials from application runtime credentials.

```text
GitHub Actions
      |
      | OIDC
      v
AWS IAM
      |
      v
ECS Deployment
      |
      v
ECS Task
      |
      | Task Role
      v
AWS Secrets Manager
      |
      v
Application
```

This means GitHub Actions does not need to know every database password used by the application.

The ECS notes describe Secrets Manager as the storage mechanism for database credentials, API tokens, and third-party credentials, with runtime access controlled by IAM. :chatgpt-content-reference{index="6"}

## Secrets and Docker BuildKit

Some builds require sensitive material, such as private package registry credentials.

Do not use:

```dockerfile
ARG PRIVATE_TOKEN

RUN pip install private-package
```

because build arguments can become part of build metadata or otherwise increase exposure risk.

Use BuildKit secret mounts when a build genuinely requires a secret:

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN --mount=type=secret,id=pip_token \
    PIP_TOKEN="$(cat /run/secrets/pip_token)" && \
    pip install --no-cache-dir \
      --extra-index-url "https://token:${PIP_TOKEN}@packages.example.com/simple" \
      -r requirements.txt
```

Workflow configuration can provide the secret to BuildKit without baking it into the final image.

The exact mechanism should be reviewed carefully for the package manager and registry being used.

## Secrets in Python Applications

A Django application should not contain:

```python
DATABASE_PASSWORD = "production-password"
```

Prefer environment configuration:

```python
import os

DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"]
```

For production deployments, the application can receive the value from the runtime platform.

FastAPI follows the same principle:

```python
import os

API_TOKEN = os.environ["API_TOKEN"]
```

For larger applications, validate configuration centrally instead of reading environment variables throughout the codebase.

## Secrets and Kubernetes

Kubernetes Secrets provide a runtime mechanism for delivering sensitive configuration to workloads.

The conceptual flow is:

```text
Secret Management
      |
      v
Kubernetes Secret
      |
      v
Pod
      |
      v
Application
```

GitHub Actions should not unnecessarily retrieve production application secrets merely to deploy Kubernetes manifests.

Where possible:

```text
GitHub Actions
    |
    +-- Deployment identity
    |
    v
Kubernetes
    |
    v
Runtime Secret Management
```

This keeps CI/CD credentials separate from application credentials.

## Secret Handling in Composite and Third-Party Actions

Every action receiving a secret should be considered trusted code.

For example:

```yaml
- name: Publish package
  uses: vendor/publish-action@v1
  with:
    token: ${{ secrets.PUBLISH_TOKEN }}
```

The action can potentially access the input.

Before granting a third-party action a secret:

- Review its source.
- Understand its permissions.
- Check its maintenance status.
- Pin the action appropriately.
- Understand what code executes on the runner.
- Avoid granting unnecessary secrets.

A compromised action can potentially exfiltrate any secret available to its step or process.

## Action Pinning

A workflow using:

```yaml
uses: vendor/action@v1
```

trusts whatever code the referenced version resolves to under that action's versioning model.

For stronger supply-chain controls, organizations may pin actions to immutable commit SHAs:

```yaml
uses: actions/checkout@<commit-sha>
```

SHA pinning improves reproducibility and prevents a mutable reference from silently moving to different code.

The trade-off is maintenance: SHA pins must be deliberately updated when action versions change.

Organizations may combine:

```text
Trusted action sources
+
Version policy
+
SHA pinning
+
Dependabot
+
Code review
```

to manage action dependencies.

## Secret Scanning

Secret scanning should be part of the engineering lifecycle.

A production pipeline may contain:

```text
Pre-commit / Local
       |
       v
Pull Request
       |
       +-- Secret Detection
       |
       +-- Dependency Scan
       |
       +-- Static Analysis
       |
       v
Build
       |
       v
Deployment
```

Secret scanning is a detection mechanism, not permission to commit credentials.

If a real credential is accidentally committed:

1. Revoke or rotate it immediately.
2. Investigate where it was exposed.
3. Remove it from active source where appropriate.
4. Review repository history and artifacts.
5. Identify downstream consumers.
6. Audit usage.
7. Replace the credential.

Deleting the line from the latest commit is not sufficient if the credential remains valid.

## Secrets and Git History

A secret committed once may remain in:

```text
Git history
Forks
Clones
Caches
Artifacts
Pull request references
Backups
Developer machines
```

Therefore:

```text
Remove secret from file
```

is not equivalent to:

```text
Credential revoked
```

The correct incident response begins with revocation.

## Secrets and Pull Request Reviews

Never place secrets directly into pull request comments or review output.

Avoid:

```text
Deployment token: abc123
```

Even if a repository is private, review content can have broader visibility than expected.

Use secret references and automated validation instead.

## Secrets and Logs

Logs should contain safe operational metadata.

Good:

```text
Deploying commit 8f3c1d2
Environment: production
Region: ap-south-1
```

Bad:

```text
DATABASE_PASSWORD=...
AWS_SECRET_ACCESS_KEY=...
API_TOKEN=...
```

The objective is:

```text
High diagnostic value
        +
Zero unnecessary secret exposure
```

## Debugging Secret Problems

When a workflow reports an authentication failure, do not print the secret.

Instead, validate:

```text
Secret exists
      ↓
Correct secret name
      ↓
Correct scope
      ↓
Correct environment
      ↓
Job can access it
      ↓
Consumer receives it
      ↓
Credential is valid
```

A safe diagnostic pattern is:

```yaml
- name: Validate token configuration
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
  run: |
    if [[ -z "$API_TOKEN" ]]; then
      echo "::error::API_TOKEN is unavailable"
      exit 1
    fi

    echo "API_TOKEN is configured"
```

Never print the token itself.

## Secret Troubleshooting

Use the following failure-domain model.

| Symptom | Possible cause | Isolation strategy | Corrective action |
|---|---|---|---|
| Secret is empty | Wrong name or scope | Validate secret reference | Correct secret name/scope |
| Secret unavailable in production | Environment not assigned | Check `environment:` | Attach correct environment |
| Authentication fails | Expired/revoked credential | Validate externally | Rotate credential |
| AWS authentication fails | OIDC/IAM trust issue | Run `aws sts get-caller-identity` | Fix trust/permissions |
| Secret appears in logs | Explicit output | Inspect commands/actions | Remove secret logging |
| Fork workflow cannot access secret | Security boundary | Inspect trigger and repository context | Redesign workflow |
| Third-party action exposes secret | Action compromise or misuse | Review action source/logs | Remove secret access |
| Deployment works in staging but not production | Different secret/configuration | Compare configuration metadata | Correct production environment |

## AWS OIDC Troubleshooting

For OIDC failures, check:

```text
Workflow permissions
        ↓
id-token: write
        ↓
OIDC provider configuration
        ↓
IAM trust policy
        ↓
Repository / branch / environment claims
        ↓
IAM role permissions
```

Workflow:

```yaml
permissions:
  contents: read
  id-token: write
```

Then:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v5
  with:
    role-to-assume: ${{ vars.AWS_DEPLOY_ROLE }}
    aws-region: ${{ vars.AWS_REGION }}

- name: Verify identity
  run: aws sts get-caller-identity
```

If `configure-aws-credentials` fails, determine whether the failure is:

```text
GitHub OIDC token
       |
       +-- unavailable

AWS OIDC provider
       |
       +-- misconfigured

IAM trust policy
       |
       +-- claim mismatch

IAM role permissions
       |
       +-- insufficient
```

Do not replace OIDC with permanent access keys merely to make the workflow pass.

## Secrets and Environments

A strong deployment architecture is:

```mermaid
flowchart TD
    A[Pull Request] --> B[CI]
    B --> C[Build]
    C --> D[Immutable Artifact]

    D --> E[Staging Environment]
    E --> F[Validation]

    F --> G[Production Environment]
    G --> H[Approval]

    H --> I[Production Deployment]

    J[Staging Secrets] --> E
    K[Production Secrets] --> I

    L[OIDC Identity] --> I
    M[AWS IAM] --> L
```

The important boundary is that production secrets are not needed for ordinary CI.

## Multi-Environment Secret Design

A common design is:

```text
Development
  |
  +-- Development API credentials
  +-- Development database credentials

Staging
  |
  +-- Staging API credentials
  +-- Staging database credentials

Production
  |
  +-- Production API credentials
  +-- Production database credentials
```

Avoid a single secret such as:

```text
DATABASE_PASSWORD
```

being manually copied between environments if the underlying systems have independent credentials.

Use explicit environment-specific ownership.

## Secret Naming

Use predictable names.

Examples:

```text
DATABASE_URL
DATABASE_PASSWORD
REDIS_URL
INTERNAL_API_TOKEN
SENTRY_AUTH_TOKEN
AWS_DEPLOY_ROLE
```

Avoid ambiguous names:

```text
TOKEN
KEY
PASSWORD
SECRET
```

Good naming makes auditing and troubleshooting easier.

For environment-specific secrets, the environment itself can provide the scope, so the same logical name can be used:

```text
staging:
  DATABASE_URL

production:
  DATABASE_URL
```

The workflow remains environment-neutral while the environment determines the value.

## Secrets and Deployment Approval

Production secrets can be protected by environment controls.

```text
Deployment Job
      |
      v
Production Environment
      |
      v
Required Reviewer
      |
      v
Production Secret Access
      |
      v
Deployment
```

This creates an important security property:

```text
Approval
   +
Environment protection
   +
Secret availability
   =
Controlled production deployment
```

The exact protection rules should match the organization's risk and compliance requirements.

## Secrets and Rollback

Rollback should not require access to a completely different set of credentials unless necessary.

A robust model is:

```text
Immutable Artifact A
        |
        +-- production configuration
        |
        v
Production

Failure
   |
   v
Previous Immutable Artifact
        |
        +-- same production configuration
        |
        v
Rollback
```

This is one reason to separate artifact identity from environment secrets.

The existing ECS CI/CD notes recommend versioned images and rolling back to a previous task definition revision rather than relying on mutable `latest` tags. :chatgpt-content-reference{index="7"}

## Secret Management and Disaster Recovery

Secrets are part of the production recovery plan.

A disaster recovery architecture should account for:

```text
Application artifact
Infrastructure definition
Environment configuration
Secrets
IAM roles
DNS configuration
Database recovery
```

If infrastructure can be rebuilt but production credentials cannot be recovered, the system is not fully recoverable.

For AWS applications, use managed secret storage and documented recovery procedures.

## Secret Management and Auditing

Track:

- Who can modify secrets.
- Which environments contain secrets.
- Which workflows consume them.
- Which teams own them.
- Rotation requirements.
- Expiration dates where applicable.
- Emergency revocation procedures.

Do not rely on undocumented knowledge such as:

```text
"John knows which production token to use."
```

Production credentials should have organizational ownership rather than personal ownership.

## Operational Best Practices

### Prefer OIDC for Cloud Authentication

For AWS:

```text
GitHub Actions
    |
    v
OIDC
    |
    v
STS
    |
    v
IAM Role
```

This avoids unnecessary long-lived AWS access keys. :chatgpt-content-reference{index="8"}

### Use Environment-Scoped Production Credentials

Keep production credentials attached to the production environment rather than exposing them to all workflows.

### Minimize Permissions

Use:

```yaml
permissions:
  contents: read
```

as a starting point and grant additional permissions only when required.

### Minimize Secret Availability

A secret should exist in the smallest scope capable of satisfying the requirement.

### Do Not Log Secrets

Diagnostic information should describe the configuration state without revealing values.

### Rotate Credentials

Treat credentials as expiring operational assets, not permanent infrastructure.

### Prefer Managed Runtime Secret Stores

For AWS workloads, use Secrets Manager or an equivalent managed secret store for application runtime secrets. The ECS notes specifically recommend Secrets Manager for credentials and tokens and KMS-backed encryption. :chatgpt-content-reference{index="9"}

## Common Mistakes

### Hardcoding Credentials

Bad:

```python
API_KEY = "production-api-key"
```

Why it fails:

- Credential enters source control.
- Git history preserves the value.
- Developers and automation can access it.
- Rotation becomes difficult.

### Using Long-Lived AWS Keys

Bad:

```yaml
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

Preferred for supported AWS workflows:

```text
GitHub OIDC
   ↓
STS
   ↓
Temporary Credentials
```

### Giving Every Job Production Secrets

Bad:

```text
Lint
  |
  +-- production secrets

Tests
  |
  +-- production secrets

Build
  |
  +-- production secrets
```

Prefer:

```text
Lint
  |
  +-- no production secrets

Tests
  |
  +-- test credentials

Build
  |
  +-- no production secrets

Deploy
  |
  +-- production credentials
```

### Printing Secrets During Debugging

Bad:

```bash
echo "$DATABASE_PASSWORD"
```

Better:

```bash
test -n "$DATABASE_PASSWORD"
echo "Database password is configured"
```

### Baking Secrets Into Images

Bad:

```dockerfile
ENV API_TOKEN=...
```

Use runtime secret injection instead.

### Using `pull_request_target` With Untrusted Code

This can create a direct path from attacker-controlled code to privileged repository secrets.

Separate:

```text
Untrusted validation
```

from:

```text
Privileged deployment
```

### Blindly Using `secrets: inherit`

Inheritance can expose more secrets than a reusable workflow actually needs.

Prefer explicit secret contracts for sensitive reusable workflows.

## Production Security Architecture

A mature secret architecture can be represented as:

```mermaid
flowchart LR
    A[Developer] --> B[GitHub Repository]

    B --> C[GitHub Actions]

    C --> D[Minimal GITHUB_TOKEN]
    C --> E[Repository Secrets]
    C --> F[Environment Secrets]
    C --> G[OIDC Identity]

    G --> H[AWS STS]
    H --> I[IAM Role]

    I --> J[ECR]
    I --> K[ECS]

    K --> L[Task Role]
    L --> M[AWS Secrets Manager]

    M --> N[Application]

    E --> O[CI Tests]
    F --> P[Deployment]
```

This separates:

```text
CI credentials
Deployment identity
Runtime application identity
Runtime application secrets
```

Each should have its own scope and permissions.

## Senior-Level Design Principles

### Separate Identity From Secret Distribution

For cloud deployments, the preferred architecture is often:

```text
Identity
   |
   v
OIDC / IAM
   |
   v
AWS Resource

Runtime Secret
   |
   v
Secrets Manager
   |
   v
Application
```

Do not use one permanent credential for both deployment and application runtime access.

### Separate Build From Deployment

Build jobs should not automatically receive production credentials.

```text
Build
  |
  +-- source
  +-- dependencies
  +-- artifact
```

Then:

```text
Deploy
  |
  +-- artifact
  +-- deployment identity
  +-- environment configuration
```

### Treat Third-Party Actions as Code Dependencies

A third-party action can execute arbitrary code on the runner.

Therefore:

```text
Third-Party Action
       |
       +-- Can execute code
       +-- Can access available environment variables
       +-- Can access available credentials
       +-- Can potentially alter artifacts
```

Only provide a secret to an action when the action genuinely needs it.

### Design for Credential Compromise

Assume a credential can eventually be exposed.

Reduce impact with:

- Short-lived credentials
- Least privilege
- Narrow scopes
- Environment protection
- Network controls
- Rotation
- Audit logging
- Separate identities
- Minimal runner access

The objective is not only preventing exposure but limiting the blast radius when prevention fails.

## Interview Traps

### Why Are GitHub Secrets Better Than Hardcoded Credentials?

They separate sensitive values from workflow source and provide managed secret storage and controlled access. They do not eliminate the risk of malicious workflow code consuming an accessible secret.

### Are GitHub Secrets Automatically Safe?

No. A secret can still be exposed by workflow code, third-party actions, artifacts, logs, shell commands, or compromised runners.

### Why Is OIDC Better for AWS?

OIDC allows GitHub Actions to obtain temporary AWS credentials through STS rather than requiring permanent AWS access keys. :chatgpt-content-reference{index="10"}

### Why Should Production Secrets Be Environment-Scoped?

Environment scope allows production credentials to be separated from ordinary CI and can be combined with deployment protection and approvals.

### Why Should You Avoid Printing Secrets Even If GitHub Masks Them?

Masking is a defensive mechanism, not permission to expose credentials. Transformations or unexpected output paths can still create leakage risks.

### What Is the Difference Between Deployment Credentials and Application Credentials?

Deployment credentials authorize CI/CD to change infrastructure or release software. Application credentials authorize the running workload to access runtime resources.

They should normally be different identities.

### Why Should Application Secrets Be Stored in AWS Secrets Manager?

The application can retrieve or receive runtime secrets under an IAM-controlled identity without requiring GitHub Actions to possess those credentials.

### Why Is `pull_request_target` Dangerous?

It can provide the base repository security context to a workflow. Executing untrusted pull request code in that context can expose privileged credentials.

### What Happens If a Secret Is Committed to Git?

Removing the file does not make the credential safe. The credential should be revoked or rotated immediately, followed by investigation of the exposure.

### Should Secrets Be Passed Through Docker Build Arguments?

Avoid using build arguments for sensitive values because build metadata and layers can create unintended exposure. Use BuildKit secret mechanisms when a build genuinely requires a secret.

## Production Secret Checklist

Before approving a production workflow, verify:

- Secrets are never committed to source control.
- Production credentials are scoped to the production environment where appropriate.
- CI jobs do not receive unnecessary production secrets.
- `GITHUB_TOKEN` permissions are explicitly minimized.
- AWS authentication uses OIDC where supported.
- IAM trust policies restrict which GitHub identities can assume deployment roles.
- Deployment roles follow least privilege.
- Runtime application secrets are stored in an appropriate managed secret store.
- Secrets are never printed to logs.
- Secrets are not uploaded as artifacts.
- Secrets are not baked into Docker images.
- Third-party actions receive only the credentials they require.
- Untrusted pull request code cannot access privileged credentials.
- `pull_request_target` is used only with a deliberate security model.
- Secret rotation procedures are documented.
- Revocation procedures are tested.
- Secret ownership is documented.
- Production rollback does not depend on rebuilding artifacts with embedded credentials.
- Secret-related failures can be diagnosed without revealing secret values.

## Key Takeaways

- Treat GitHub Actions secrets as sensitive credentials with explicit scope, minimal access, controlled workflows, and documented rotation procedures.
- Separate CI credentials, deployment identities, and application runtime secrets; for AWS, prefer OIDC and temporary STS credentials over long-lived access keys.
- Never expose secrets through logs, artifacts, Docker images, shell interpolation, or untrusted pull request execution.
- Use protected environments and least-privilege permissions to keep production credentials away from ordinary CI jobs and untrusted code.
- Design for credential compromise with short-lived identities, narrow permissions, managed runtime secret storage, auditing, rotation, and small blast radius.