# 13- Secrets and Variables Operations

## Overview

Secrets and variables are operational configuration mechanisms used by GitHub Actions to provide workflows with sensitive credentials and non-sensitive configuration.

The distinction is fundamental:

```text
Secrets
→ Sensitive values
→ Credentials, tokens, passwords, keys

Variables
→ Non-sensitive configuration
→ Regions, repository names, feature settings, identifiers
```

In production CI/CD, secrets and variables must be managed as part of the workflow platform rather than treated as arbitrary YAML configuration.

A mature operational model considers:

- Scope
- Ownership
- Environment
- Permissions
- Rotation
- Auditability
- Exposure risk
- Availability
- Disaster recovery
- Lifecycle
- Governance

A typical deployment flow is:

```mermaid
flowchart LR
    A[Workflow] --> B[Variables]
    A --> C[Secrets]
    B --> D[Job]
    C --> D
    D --> E[OIDC / AWS]
    D --> F[Docker / ECR]
    D --> G[Deployment]
```

---

## Secrets vs Variables

| Property | Secrets | Variables |
|---|---|---|
| Sensitive data | Yes | No |
| Masking | Supported | No |
| Typical values | Passwords, tokens, credentials | Region, repository name |
| Logging risk | Lower but not zero | High if sensitive data is incorrectly stored |
| Environment scope | Yes | Yes |
| Organization scope | Yes | Yes |
| Repository scope | Yes | Yes |
| Recommended for AWS static credentials | Avoid where possible | No |
| Recommended for AWS region | No | Yes |

Never store a secret in a variable simply because the variable is easier to reference.

---

## Secret Scopes

Secrets can exist at different administrative scopes.

```text
Organization
    ↓
Repository
    ↓
Environment
    ↓
Workflow Job
```

Typical scopes include:

- Organization secrets
- Repository secrets
- Environment secrets

The broader the scope, the larger the potential blast radius.

---

## Organization Secrets

Organization secrets are useful when multiple repositories require the same credential or configuration.

Examples:

```text
INTERNAL_PACKAGE_TOKEN
SHARED_SECURITY_SERVICE_TOKEN
```

However, organization-wide secrets should not automatically be exposed to every repository.

Restrict access to the repositories that genuinely require them.

---

## Repository Secrets

Repository secrets are appropriate for credentials specific to one repository.

Example:

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
```

Repository secrets reduce cross-repository exposure compared with organization-wide secrets.

---

## Environment Secrets

Environment secrets are particularly useful for deployment credentials.

Example:

```yaml
jobs:
  deploy:
    environment:
      name: production

    steps:
      - name: Deploy
        run: ./deploy.sh
```

The production environment can contain production-specific secrets and protection rules.

A common architecture is:

```text
Staging Environment
    ├── STAGING_API_KEY
    └── STAGING_DATABASE_URL

Production Environment
    ├── PRODUCTION_API_KEY
    └── PRODUCTION_DATABASE_URL
```

This prevents workflows from using the same credentials across environments.

---

## Environment Protection

Production environments can be protected using:

- Required reviewers
- Deployment protection rules
- Branch restrictions
- Environment-specific secrets
- Deployment history

A deployment workflow can therefore enforce:

```text
Build
 ↓
Test
 ↓
Staging
 ↓
Validation
 ↓
Production Approval
 ↓
Production Secrets Available
 ↓
Deployment
```

This creates a security boundary around production credentials.

---

## Variable Scopes

Variables can exist at:

- Organization level
- Repository level
- Environment level

Example:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
```

Variables are appropriate for non-sensitive configuration such as:

```text
AWS_REGION
ECR_REPOSITORY
DEPLOYMENT_TIMEOUT
SERVICE_NAME
```

---

## Environment Variables

Workflow environment variables can be defined at different scopes.

Workflow-level:

```yaml
env:
  PYTHON_VERSION: "3.12"
```

Job-level:

```yaml
jobs:
  test:
    env:
      DJANGO_SETTINGS_MODULE: config.settings.test
```

Step-level:

```yaml
- name: Run tests
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: pytest
```

Prefer the narrowest scope that satisfies the requirement.

---

## Variable Precedence

Configuration can come from several sources.

Operationally, distinguish:

```text
Workflow configuration
Repository variables
Environment variables
Step/job environment variables
Shell environment
```

Do not create multiple values with the same logical name unless overriding behavior is intentional.

Ambiguous configuration creates difficult production failures.

---

## `vars` vs `env`

`vars` references GitHub configuration variables:

```yaml
${{ vars.AWS_REGION }}
```

`env` represents environment variables available to workflow steps:

```yaml
${{ env.AWS_REGION }}
```

For example:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
```

This explicitly copies configuration from the GitHub variable context into the process environment.

---

## Secret Access

Secrets are referenced through the `secrets` context:

```yaml
${{ secrets.API_TOKEN }}
```

Example:

```yaml
- name: Call deployment API
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
  run: |
    ./deploy.sh
```

Passing secrets through environment variables is often preferable to placing them directly into command arguments.

---

## Avoid Secrets in Command Arguments

Avoid:

```yaml
run: curl -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" https://example.internal
```

Prefer:

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
run: |
  curl \
    -H "Authorization: Bearer ${API_TOKEN}" \
    https://example.internal
```

This makes the secret boundary clearer and reduces accidental exposure through command construction.

---

## Secret Masking

GitHub Actions attempts to mask secret values in logs.

However, masking is not a replacement for safe handling.

Do not assume this is safe:

```bash
echo "$SECRET"
```

Never intentionally print credentials, even if GitHub is expected to mask them.

Secrets can also be exposed through:

- Generated files
- Artifacts
- Debug output
- Process arguments
- Docker build layers
- Application logs
- Test reports

---

## Secret Handling Limitations

Secret masking has important limitations.

If a secret is transformed before logging, masking may not always protect the transformed value.

Examples include:

```text
Encoding
Hashing
Substring extraction
JSON transformation
Concatenation
Compression
```

Treat secrets as data that must never enter logs rather than relying on masking to make accidental exposure safe.

---

## `secrets: inherit`

Reusable workflows can inherit secrets:

```yaml
jobs:
  deploy:
    uses: organization/platform/.github/workflows/deploy.yml@v1
    secrets: inherit
```

This reduces configuration duplication but can broaden the secret boundary.

Prefer explicit secret passing for workflows with narrow requirements.

```yaml
jobs:
  deploy:
    uses: organization/platform/.github/workflows/deploy.yml@v1
    secrets:
      deployment-token: ${{ secrets.DEPLOYMENT_TOKEN }}
```

---

## Secret Passing Through Reusable Workflows

Caller:

```yaml
jobs:
  deploy:
    uses: organization/platform/.github/workflows/deploy.yml@v1
    secrets:
      aws-role-arn: ${{ secrets.AWS_ROLE_ARN }}
```

Reusable workflow:

```yaml
on:
  workflow_call:
    secrets:
      aws-role-arn:
        required: true
```

This creates an explicit interface between the caller and reusable workflow.

---

## Secret Lifecycle

Secrets should have a lifecycle:

```text
Create
  ↓
Validate
  ↓
Use
  ↓
Monitor
  ↓
Rotate
  ↓
Revoke
  ↓
Replace
```

Do not treat a secret as permanent infrastructure.

---

## Secret Rotation

Rotation should be designed before the credential is deployed.

A safe rotation sequence is:

```text
Create New Credential
        ↓
Validate New Credential
        ↓
Deploy New Credential
        ↓
Verify Consumers
        ↓
Revoke Old Credential
```

For credentials supporting overlapping validity, use a dual-secret transition.

```text
Old Credential ────────┐
                       ├── Transition
New Credential ────────┘
```

This avoids outages caused by changing the credential and consumer simultaneously.

---

## Rotation Frequency

Rotation frequency should depend on:

- Credential type
- Exposure risk
- Provider capability
- Compliance requirements
- Operational cost
- Blast radius

Short-lived credentials should generally be preferred over long-lived credentials when the platform supports them.

---

## AWS Credentials

Avoid storing long-lived AWS access keys in GitHub secrets when OIDC is available.

Preferred model:

```text
GitHub Actions
      ↓
OIDC Token
      ↓
AWS STS
      ↓
IAM Role
      ↓
Temporary Credentials
      ↓
ECR / S3 / ECS / EC2 / Lambda
```

Workflow permission:

```yaml
permissions:
  contents: read
  id-token: write
```

This reduces long-lived credential management.

---

## AWS OIDC and Variables

Non-sensitive AWS configuration can remain in variables:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
  ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
```

The workflow can obtain temporary AWS credentials through OIDC.

This separates:

```text
Configuration
→ GitHub Variables

Authentication
→ OIDC + IAM

Authorization
→ IAM Policy
```

---

## OIDC Trust Boundaries

The AWS IAM trust policy should restrict which GitHub workflows can assume the role.

Conceptually:

```text
GitHub Repository
       ↓
Workflow Identity
       ↓
OIDC Token
       ↓
IAM Trust Policy
       ↓
STS
       ↓
Temporary Credentials
```

Avoid creating one highly privileged role usable by every repository.

---

## Python Backend Example

A Django or FastAPI deployment might require:

```text
AWS_REGION
ECR_REPOSITORY
DATABASE_URL
REDIS_URL
```

A reasonable separation is:

| Value | Storage |
|---|---|
| `AWS_REGION` | Variable |
| `ECR_REPOSITORY` | Variable |
| `DATABASE_URL` | Secret |
| `REDIS_URL` | Secret |
| AWS credentials | OIDC |
| Deployment environment | Environment |

---

## Django Example

A production workflow can inject a database secret only into the migration step:

```yaml
- name: Run migrations
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    python manage.py migrate
```

Avoid making the database credential available to unrelated steps such as linting or static analysis.

---

## FastAPI Example

A FastAPI deployment may require:

```yaml
- name: Deploy API
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    REDIS_URL: ${{ secrets.REDIS_URL }}
  run: |
    ./deploy.sh
```

The deployment script should avoid logging these values.

---

## PostgreSQL Credentials

Do not store database passwords in:

```text
Repository variables
Workflow YAML
Dockerfile
Source code
Build arguments
```

Use secrets or an external secret manager.

For production workloads, the application may retrieve secrets from:

- AWS Secrets Manager
- Kubernetes Secrets
- External secret-management systems

GitHub secrets should not automatically become the runtime application's permanent secret store.

---

## Redis Credentials

If Redis authentication is required:

```yaml
env:
  REDIS_URL: ${{ secrets.REDIS_URL }}
```

Avoid placing credentials directly into cache keys or artifact metadata.

---

## Kafka Credentials

Kafka credentials can include:

```text
SASL username
SASL password
Client certificates
Private keys
```

These must be treated as secrets.

Do not publish them in:

- Workflow summaries
- Debug logs
- Test reports
- Artifacts
- Docker image layers

---

## Docker and Secrets

Do not pass secrets as Docker build arguments unless the mechanism is specifically designed to avoid persisting them.

Risky:

```dockerfile
ARG API_TOKEN
RUN curl -H "Authorization: Bearer ${API_TOKEN}" ...
```

Build history or intermediate layers can create unintended exposure.

Use BuildKit secret mounts where a build-time secret is genuinely required.

---

## Docker Runtime Secrets

Runtime secrets should generally be supplied by the deployment platform rather than baked into the image.

Prefer:

```text
Docker Image
    ↓
Immutable
    ↓
Runtime Secret Injection
    ↓
Application
```

Avoid:

```text
Secret
 ↓
Dockerfile
 ↓
Image
 ↓
Registry
```

---

## Kubernetes Secrets

For Kubernetes deployments, GitHub Actions should generally deploy references to runtime secrets rather than embedding sensitive values into workflow logs or manifests unnecessarily.

A common architecture is:

```text
GitHub Actions
      ↓
Deployment Manifest
      ↓
Kubernetes
      ↓
External Secret / Secret Store
      ↓
Pod
```

---

## Secrets and Untrusted Pull Requests

Do not expose privileged secrets to untrusted pull request code.

Particularly dangerous combinations include:

```text
Untrusted PR
+
Self-hosted runner
+
Production secrets
```

or:

```text
Untrusted PR
+
Private network access
+
Cloud credentials
```

Fork workflows should operate within an appropriately restricted trust boundary.

---

## `pull_request` vs `pull_request_target`

`pull_request` is designed for validating pull request changes.

`pull_request_target` executes in the context of the base repository and therefore requires particular caution.

Never use `pull_request_target` as a shortcut for making secrets available to arbitrary pull request code.

A dangerous pattern is:

```text
pull_request_target
      ↓
Checkout attacker-controlled code
      ↓
Execute code
      ↓
Expose repository secrets
```

---

## Secret Exposure Through Artifacts

Artifacts may contain sensitive information unintentionally.

Examples:

```text
pytest report
Django traceback
Debug logs
Environment dumps
Configuration files
Core dumps
Browser traces
```

Before uploading artifacts, inspect their contents.

Never use:

```bash
env > debug.txt
```

in a production workflow that has secrets in its environment.

---

## Secret Exposure Through Logs

Avoid commands such as:

```bash
set -x
```

when secrets are present.

Also avoid:

```bash
printenv
```

or:

```bash
env
```

in deployment jobs.

Use targeted diagnostics instead.

---

## Secret Exposure Through Error Messages

Applications may accidentally include credentials in exceptions.

For example:

```text
Connection failed:
postgres://user:password@host/db
```

Logs and test reports containing such values can become workflow artifacts.

Sanitize connection strings before logging.

---

## Variables and Configuration Drift

Variables can change without changing the workflow code.

This is useful for environment-specific configuration but can also create drift.

For example:

```text
Staging:
ECR_REPOSITORY=orders-staging

Production:
ECR_REPOSITORY=orders-prod
```

Configuration should be documented and governed.

---

## Configuration as Data

Separate:

```text
Workflow Logic
```

from:

```text
Environment Configuration
```

Example:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}
  ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
```

The workflow remains reusable while configuration changes per environment.

---

## Secret Naming

Use predictable names.

Examples:

```text
DATABASE_URL
REDIS_URL
KAFKA_USERNAME
KAFKA_PASSWORD
DEPLOYMENT_TOKEN
```

For environment-specific secrets, the environment itself should normally provide the scope rather than encoding environment names into every key.

Prefer:

```text
production environment → DATABASE_URL
staging environment → DATABASE_URL
```

over:

```text
PRODUCTION_DATABASE_URL
STAGING_DATABASE_URL
```

when the workflow already uses GitHub Environments.

---

## Secret Ownership

Every important secret should have:

- Business owner
- Technical owner
- Consumer list
- Rotation process
- Expiration strategy
- Incident response process

A secret without ownership becomes difficult to rotate safely.

---

## Secret Inventory

Maintain an inventory containing:

| Field | Example |
|---|---|
| Name | `DATABASE_URL` |
| Scope | Production |
| Owner | Platform Team |
| Consumer | Orders API |
| Source | AWS Secrets Manager |
| Rotation | 90 days |
| Impact | Production outage |
| Recovery | Restore previous credential |

Do not store the secret value itself in the inventory.

---

## Secret Rotation Runbook

A production runbook should define:

1. Identify the credential.
2. Identify all consumers.
3. Generate the replacement.
4. Validate the replacement.
5. Update the secret.
6. Deploy or restart affected workloads.
7. Verify application health.
8. Revoke the old credential.
9. Monitor for failures.
10. Record the rotation.

---

## Emergency Secret Revocation

If a secret is exposed:

```text
Detect
 ↓
Revoke
 ↓
Rotate
 ↓
Identify Access
 ↓
Inspect Logs
 ↓
Assess Impact
 ↓
Restore Secure Configuration
 ↓
Monitor
```

Do not wait for the normal rotation schedule.

---

## Git History and Leaked Secrets

Removing a secret from the latest commit does not mean it is no longer exposed.

If a credential entered Git history:

1. Revoke the credential.
2. Rotate it.
3. Investigate access.
4. Remove the sensitive data from history if appropriate.
5. Audit downstream systems.

The most important action is revocation, not merely rewriting Git history.

---

## Secret Scanning

Use secret scanning and repository security controls where available.

The objective is:

```text
Prevent
 ↓
Detect
 ↓
Revoke
 ↓
Rotate
 ↓
Investigate
```

Secret scanning is a detection mechanism, not permission to store secrets in source code.

---

## Operational Access

Access to production secrets should follow least privilege.

Avoid giving every engineer:

```text
Production secret read access
```

when the normal operational workflow can perform the required action without exposing the secret.

---

## External Secret Managers

For runtime applications, external secret stores are often more appropriate than GitHub secrets.

Examples include:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Kubernetes-integrated secret systems

Architecture:

```text
GitHub Actions
      ↓
Deploy Application
      ↓
Runtime Environment
      ↓
Secret Manager
      ↓
Application
```

This separates CI/CD credentials from application runtime credentials.

---

## Secret Availability and Reliability

Secrets are part of the deployment dependency graph.

If a production deployment requires:

```text
Secret Store
 ↓
Credential
 ↓
Deployment
```

the secret-management system becomes a production dependency.

Plan for:

- Provider outages
- Permission failures
- Rotation failures
- Expired credentials
- Incorrect values
- Replication issues

---

## Disaster Recovery

Secret recovery should be designed without creating additional exposure.

Maintain:

- Secret ownership
- Secret source
- Recovery procedure
- Rotation procedure
- Environment mapping
- External dependency documentation

Avoid storing plaintext backup copies of production credentials merely for disaster recovery.

---

## Secrets and High Availability

Applications should not rely on a single manually managed credential.

For critical services, design rotation and failover mechanisms that support credential overlap when possible.

For example:

```text
Credential A
    ↓
Active

Credential B
    ↓
Prepared

Rotate
    ↓
B becomes active
    ↓
A revoked
```

---

## Monitoring

Monitor operational events such as:

- Authentication failures
- Deployment failures
- Credential rotation failures
- OIDC assumption failures
- IAM access denials
- Secret-manager access errors

Do not monitor by logging secret values.

---

## Auditing

Audit:

- Secret creation
- Secret updates
- Secret deletion
- Environment changes
- Workflow changes
- IAM role changes
- OIDC trust-policy changes

Audit records should identify:

```text
Who
What
When
Where
Why
```

without exposing secret values.

---

## Cost Considerations

GitHub secrets themselves are not generally the main cost driver.

Operational costs often come from:

- External secret managers
- CI runtime
- Secret rotation infrastructure
- Incident response
- Excessive deployment retries
- Manual operational processes

Automating rotation and deployment can reduce operational effort and failure risk.

---

## Workflow Permissions

Use explicit permissions.

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

Do not grant unrelated write permissions merely because a workflow contains secrets.

A secret does not grant authorization by itself; the workflow's permissions and external systems determine what it can do.

---

## Secrets and GITHUB_TOKEN

`GITHUB_TOKEN` is automatically provided by GitHub Actions and should be treated as a credential.

Its access should be minimized.

Example:

```yaml
permissions:
  contents: read
```

If a workflow needs to create releases or modify pull requests, grant only the required permissions.

---

## Secrets in Reusable Workflows

Reusable workflows should define narrow interfaces.

Avoid exposing every available secret to every reusable workflow.

Prefer:

```text
Caller
 ↓
Specific Secret
 ↓
Reusable Workflow
 ↓
Specific Deployment Step
```

rather than:

```text
Caller
 ↓
All Secrets
 ↓
Reusable Workflow
 ↓
Many Jobs
```

---

## Secret Access at Job Scope

A useful pattern is to expose a credential only to the job that needs it.

```yaml
jobs:
  test:
    permissions:
      contents: read
    steps:
      - run: pytest

  deploy:
    permissions:
      contents: read
      id-token: write
    environment: production
    steps:
      - run: ./deploy.sh
```

The testing job never receives production deployment credentials.

---

## Separation of CI and Deployment Secrets

CI usually requires:

```text
Package registry access
Test database credentials
Test service credentials
```

Deployment requires:

```text
AWS identity
Production environment access
Deployment API credentials
```

These should not be shared unnecessarily.

---

## Secret Rotation Without Downtime

A backend deployment can support overlapping credentials.

```text
Existing Credential
       ↓
Application accepts A
       ↓
Add B
       ↓
Application accepts A + B
       ↓
Switch consumers to B
       ↓
Remove A
```

This is safer than:

```text
Delete A
 ↓
Deploy B
```

which can create a temporary outage.

---

## Production Example

Consider a Django application deployed to ECS.

Configuration:

```text
GitHub Variables
├── AWS_REGION
└── ECR_REPOSITORY

GitHub Environment: production
└── DEPLOYMENT_CONFIG

AWS OIDC
└── Temporary AWS credentials

AWS Secrets Manager
├── DATABASE_URL
├── REDIS_URL
└── DJANGO_SECRET_KEY
```

The deployment pipeline can therefore separate:

```text
CI configuration
AWS authentication
Application runtime secrets
Production deployment protection
```

---

## Example Production Workflow

```yaml
name: Production Deployment

on:
  workflow_dispatch:
    inputs:
      image-tag:
        description: Immutable image tag
        required: true
        type: string

permissions:
  contents: read
  id-token: write

jobs:
  deploy:
    environment:
      name: production

    runs-on: ubuntu-latest

    env:
      AWS_REGION: ${{ vars.AWS_REGION }}
      ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v6
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Verify AWS identity
        run: aws sts get-caller-identity

      - name: Deploy
        env:
          IMAGE_TAG: ${{ inputs.image-tag }}
        run: |
          ./deploy.sh "$IMAGE_TAG"
```

The workflow contains:

- Non-sensitive configuration in variables
- AWS role configuration in a protected secret/environment
- Temporary AWS credentials through OIDC
- Immutable image identity through an input
- Production environment protection

---

## Secrets and Variables in Step Summaries

Never include:

```text
Secret values
Authorization headers
Database URLs
Private keys
Access tokens
```

in `$GITHUB_STEP_SUMMARY`.

Safe:

```bash
{
  echo "## Deployment"
  echo "- Environment: production"
  echo "- Image: ${IMAGE_TAG}"
  echo "- Region: ${AWS_REGION}"
} >> "$GITHUB_STEP_SUMMARY"
```

---

## Troubleshooting Secret Problems

### Symptom

A secret appears empty.

### Possible Causes

- Incorrect secret name
- Wrong environment
- Secret unavailable to the event
- Missing reusable-workflow declaration
- Missing `secrets: inherit`
- Fork workflow restrictions
- Incorrect repository or organization scope

### Isolation Strategy

Check:

```text
Secret Name
 ↓
Scope
 ↓
Environment
 ↓
Workflow Event
 ↓
Reusable Workflow Interface
 ↓
Job
```

Never print the secret value.

### Corrective Action

Fix the scope or workflow interface rather than weakening security controls.

---

## Troubleshooting Variable Problems

### Symptom

A variable contains an unexpected value.

### Possible Causes

- Multiple configuration scopes
- Environment override
- Job-level override
- Step-level override
- Incorrect `vars` vs `env` reference

### Isolation Strategy

Temporarily print the non-sensitive value and identify its source.

For example:

```yaml
- name: Inspect configuration
  run: |
    echo "AWS_REGION=${AWS_REGION}"
    echo "ECR_REPOSITORY=${ECR_REPOSITORY}"
```

Do this only for non-sensitive configuration.

---

## Troubleshooting OIDC

### Symptom

AWS authentication fails.

### Checks

```yaml
permissions:
  id-token: write
```

Then verify:

```text
OIDC Provider
 ↓
IAM Trust Policy
 ↓
Repository
 ↓
Branch / Environment
 ↓
Role ARN
 ↓
AWS Account
```

Diagnostic command after successful authentication:

```bash
aws sts get-caller-identity
```

Do not replace OIDC with long-lived credentials merely to bypass an IAM trust-policy problem.

---

## Troubleshooting Secret Rotation

### Symptom

Deployment fails immediately after rotation.

### Possible Causes

- New credential invalid
- Consumer not updated
- Incorrect secret scope
- Application still expects old credential
- External provider has propagation delay

### Isolation

```text
New Credential
 ↓
Provider Validation
 ↓
GitHub Secret
 ↓
Deployment
 ↓
Application
 ↓
External Service
```

If possible, retain overlapping credentials during transition.

---

## Troubleshooting Production Deployment Failures

Separate:

```text
Secret Retrieval Failure
```

from:

```text
Authentication Failure
```

and:

```text
Authorization Failure
```

and:

```text
Application Configuration Failure
```

For example:

```text
Secret exists
 ↓
AWS authentication succeeds
 ↓
IAM authorization fails
```

is not a secret-storage problem.

---

## GitHub CLI Operations

List repository secrets:

```bash
gh secret list
```

Set a repository secret:

```bash
gh secret set DEPLOYMENT_TOKEN
```

List environment secrets:

```bash
gh secret list --env production
```

List repository variables:

```bash
gh variable list
```

Set a repository variable:

```bash
gh variable set AWS_REGION --body ap-south-1
```

List environment variables:

```bash
gh variable list --env production
```

Use the CLI for operational management, but maintain appropriate governance around who can change production configuration.

---

## Operational Change Management

Secret and variable changes should be treated as production changes.

For critical environments:

```text
Change Request
 ↓
Review
 ↓
Change
 ↓
Validation
 ↓
Deployment
 ↓
Monitoring
```

Avoid ad-hoc changes without ownership or auditability.

---

## Secret and Variable Governance

Organizations should establish:

- Approved secret scopes
- Naming conventions
- Rotation requirements
- Ownership
- Environment boundaries
- Access policies
- External secret-manager usage
- OIDC standards
- Audit requirements
- Incident response procedures

---

## Common Mistakes

### Storing Secrets in Variables

Variables are not a substitute for secrets.

### Using Repository Secrets for Every Environment

This can mix staging and production credentials.

Use environment-specific secrets where appropriate.

### Sharing All Secrets With Reusable Workflows

`secrets: inherit` can broaden the trust boundary.

### Printing Environment Variables

Commands such as:

```bash
printenv
```

can expose credentials.

### Putting Secrets in Docker Images

Secrets baked into images can persist in layers and registries.

### Using Long-Lived AWS Keys

Prefer OIDC and temporary STS credentials.

### Rotating Without Consumer Analysis

Changing a credential without understanding all consumers can cause outages.

### Keeping Secrets Forever

Credentials should have a lifecycle and ownership.

### Storing Runtime Secrets in GitHub

GitHub Actions secrets are primarily CI/CD configuration. Runtime applications may be better served by dedicated secret-management systems.

### Ignoring Fork Security

Untrusted code must not receive privileged credentials or access to trusted private infrastructure.

---

## Production Architecture

A mature architecture separates configuration, authentication, and runtime secrets.

```mermaid
flowchart TD
    A[GitHub Workflow] --> B[GitHub Variables]
    A --> C[GitHub Environment Secrets]

    B --> D[Non-sensitive Configuration]
    C --> E[Deployment Configuration]

    A --> F[OIDC]
    F --> G[AWS STS]
    G --> H[Temporary Credentials]

    H --> I[ECR]
    H --> J[ECS / EC2 / Lambda]

    J --> K[AWS Secrets Manager]
    K --> L[Runtime Application]

    D --> I
    E --> J
```

The important boundary is:

```text
CI/CD Authentication
        ≠
Application Runtime Secrets
```

Keeping these responsibilities separate reduces blast radius and simplifies rotation.

---

## Failure Domains

Secrets and variables introduce several independent failure domains:

```text
GitHub Configuration
        ↓
Environment Configuration
        ↓
OIDC / IAM
        ↓
External Secret Store
        ↓
Deployment
        ↓
Runtime Application
```

Troubleshooting should identify the first failed boundary rather than treating every authentication error as a generic secret problem.

---

## Senior Engineering Considerations

A senior engineer should ask:

- Who owns this secret?
- Why does this workflow need it?
- Can OIDC eliminate the credential?
- Can the secret be scoped to an environment?
- Can the job avoid receiving the secret entirely?
- What happens if the credential expires?
- How is rotation performed?
- Can rotation happen without downtime?
- Where does the runtime application obtain its secrets?
- What is the blast radius if this credential is compromised?
- How is access audited?
- How does disaster recovery restore the configuration without exposing credentials?

---

## Production Review Checklist

### Secrets

- [ ] Sensitive values use secrets rather than variables.
- [ ] Production secrets are environment-scoped.
- [ ] Secret ownership is defined.
- [ ] Rotation procedures exist.
- [ ] Emergency revocation is documented.
- [ ] Secrets are never intentionally logged.
- [ ] Secrets are not embedded in Docker images.
- [ ] Secrets are not stored in artifacts.
- [ ] Fork workflows cannot access privileged credentials.

### Variables

- [ ] Variables contain only non-sensitive configuration.
- [ ] Scope is intentional.
- [ ] Naming is consistent.
- [ ] Environment overrides are documented.
- [ ] Duplicate configuration is minimized.

### AWS

- [ ] OIDC is used where practical.
- [ ] IAM trust policies are restricted.
- [ ] AWS permissions follow least privilege.
- [ ] Long-lived AWS keys are avoided.
- [ ] `id-token: write` is scoped appropriately.

### Operations

- [ ] Secret inventory exists.
- [ ] Rotation is tested.
- [ ] Changes are auditable.
- [ ] External secret-manager dependencies are documented.
- [ ] Recovery procedures exist.
- [ ] Monitoring covers authentication and deployment failures.

## Interview Scenarios

### Production Deployment Requires AWS Access

Design the authentication flow without storing long-lived AWS access keys.

Expected reasoning:

```text
GitHub OIDC
 → STS
 → IAM Role
 → Temporary Credentials
```

Then explain trust-policy restrictions and least privilege.

### Staging and Production Need Different Credentials

Use GitHub Environments with environment-specific secrets.

Explain:

```text
staging → staging secrets
production → production secrets
```

and environment protection.

### A Secret Was Accidentally Logged

The immediate response should be:

```text
Stop further exposure
 ↓
Revoke / rotate credential
 ↓
Determine access
 ↓
Inspect logs/artifacts
 ↓
Assess impact
 ↓
Fix workflow
 ↓
Monitor
```

Do not rely solely on log masking.

### A Reusable Workflow Needs One Credential

Prefer an explicit secret interface instead of inheriting every secret available to the caller.

### A Developer Requests Production Secret Access

Ask whether the operational task can be performed without exposing the secret.

Prefer workflow-based operations and least privilege over broad human access.

### Production Secret Rotation Must Not Cause Downtime

Use overlapping credentials when the external system supports them:

```text
Old + New
    ↓
Switch consumers
    ↓
Validate
    ↓
Revoke old
```

### A Pull Request Needs a Private API

Do not automatically expose production credentials or private-network access to untrusted pull request code.

Separate trusted deployment workflows from untrusted validation workflows.

---

## Senior Design Principles

### Secrets Are Credentials, Not Configuration

Treat them as security-sensitive assets with lifecycle management.

### Variables Are Configuration, Not Secret Storage

Use them for non-sensitive values that need operational configurability.

### Scope Is a Security Control

Repository, organization, environment, and job boundaries determine blast radius.

### Prefer Short-Lived Credentials

OIDC and STS reduce the operational risk associated with long-lived credentials.

### Separate CI From Runtime Secret Management

GitHub Actions should not become the permanent secret store for every backend application.

### Rotation Must Be Designed

A secret that cannot be rotated safely is an operational liability.

### Do Not Trust Masking

Prevent exposure rather than depending on log redaction.

### Treat Configuration Changes as Production Changes

Secrets and variables can change runtime behavior even when application code is unchanged.

## Key Takeaways

- Use **secrets for sensitive values** and **variables for non-sensitive configuration**, with the narrowest practical scope.
- Production secrets should be environment-protected, owned, auditable, rotatable, and isolated from untrusted pull request workflows.
- Prefer **GitHub OIDC → AWS STS → IAM roles** over long-lived AWS credentials stored in GitHub secrets.
- Separate CI/CD authentication from application runtime secret management, using systems such as AWS Secrets Manager when appropriate.
- Treat secret and variable changes as production configuration changes requiring least privilege, controlled rotation, monitoring, and recovery procedures.