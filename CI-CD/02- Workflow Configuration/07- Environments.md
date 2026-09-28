# 07- Environments

## Overview

GitHub Actions environments provide a controlled boundary around deployment targets such as development, staging, and production. An environment can associate environment-specific variables and secrets with protection rules, while GitHub records deployments against that environment.

For a production backend system, environments are more than configuration labels. They establish a deployment control point between CI and CD:

```text
Pull Request
    ↓
Lint / Tests / Security Scan
    ↓
Build Immutable Artifact
    ↓
Deploy to Development
    ↓
Validate
    ↓
Deploy to Staging
    ↓
Validate
    ↓
Production Approval
    ↓
Deploy Same Artifact to Production
    ↓
Monitor / Roll Back if Required
```

A well-designed environment strategy separates configuration and deployment authorization without rebuilding the application for every environment.

Typical environments include:

| Environment | Primary purpose | Typical deployment |
|---|---|---|
| Development | Developer integration and early validation | Automatic |
| QA | Functional and integration validation | Automatic or controlled |
| Staging | Production-like validation | Controlled |
| Production | Customer-facing workloads | Approval/protection required |

The exact number of environments should reflect operational requirements. Creating many environments without meaningful isolation usually increases configuration drift and maintenance overhead.

---

## Why Environments Matter

Without environment boundaries, deployment workflows commonly become a collection of hardcoded conditionals:

```yaml
if: github.ref == 'refs/heads/main'
```

combined with environment-specific credentials, URLs, database configuration, and deployment commands.

This makes it difficult to answer basic operational questions:

- Which credentials were used?
- Which configuration was deployed?
- Who approved the production deployment?
- Which artifact was promoted?
- Which deployment is currently running?
- Can the previous release be restored?
- Can a staging deployment accidentally access production resources?

Environments provide a structured boundary for these concerns.

A production deployment should ideally be represented as:

```text
Artifact
   +
Production Environment
   +
Production Configuration
   +
Production Authorization
   +
Deployment
```

rather than:

```text
Source Code
   +
Production Branch
   +
Production Credentials
   +
Build
   +
Deployment
```

The first model separates artifact creation from environment-specific promotion.

---

## Environment Components

A GitHub Actions environment can provide:

- Environment name
- Environment secrets
- Environment variables
- Deployment protection rules
- Required reviewers
- Deployment history
- Branch/tag restrictions where configured
- A deployment target associated with workflow execution

Conceptually:

```text
GitHub Repository
        │
        ├── Workflow
        │
        ├── Repository Variables
        ├── Repository Secrets
        │
        └── Environments
                │
                ├── development
                │      ├── Variables
                │      └── Secrets
                │
                ├── staging
                │      ├── Variables
                │      └── Secrets
                │
                └── production
                       ├── Variables
                       ├── Secrets
                       └── Protection Rules
```

The environment becomes active when a job references it:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Deploy
        run: ./scripts/deploy.sh
```

The `environment` declaration is therefore part of the deployment job's authorization and configuration boundary.

---

## Environment Configuration

A deployment should identify its target environment explicitly.

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v5

      - name: Deploy
        run: ./scripts/deploy.sh
```

For production:

```yaml
jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v5

      - name: Deploy
        run: ./scripts/deploy.sh
```

The environment itself should determine which environment-specific values become available.

Avoid embedding environment-specific credentials directly into workflow YAML.

Bad:

```yaml
env:
  AWS_ACCESS_KEY_ID: production-access-key
  AWS_SECRET_ACCESS_KEY: production-secret
```

Prefer environment-scoped secrets or, for AWS deployments, short-lived OIDC-based authentication.

---

## Environment Variables

Environment variables can represent configuration that differs between environments.

Example:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - name: Deploy
        env:
          API_URL: ${{ vars.API_URL }}
        run: |
          ./scripts/deploy.sh "$API_URL"
```

A possible configuration model is:

| Environment | `API_URL` |
|---|---|
| Development | `https://api-dev.example.com` |
| Staging | `https://api-staging.example.com` |
| Production | `https://api.example.com` |

Environment configuration should contain deployment-specific values rather than business logic.

For example:

```text
Environment configuration:
    API endpoint
    AWS region
    ECS cluster
    ECS service
    deployment parameters
```

Application behavior that should remain identical across environments should generally remain in application code or shared configuration.

---

## Environment Secrets

Sensitive environment-specific values should not be stored in workflow YAML.

Examples include:

- Third-party API credentials
- Deployment credentials
- Database credentials
- Signing keys
- Private tokens

Example:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Deploy application
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: ./scripts/deploy.sh
```

Environment secrets provide an important separation:

```text
staging
    ↓
staging credentials

production
    ↓
production credentials
```

A staging deployment should not automatically receive production credentials.

For AWS deployments, long-lived AWS credentials should generally be avoided in favor of GitHub OIDC with AWS STS.

---

## Environment Protection Rules

Production deployments frequently require stronger controls than development deployments.

Typical controls include:

- Required reviewers
- Deployment branch restrictions
- Environment-specific secrets
- Environment-specific variables
- Deployment history
- Approval before protected deployment

A production environment can therefore act as an authorization boundary:

```text
Build
  ↓
Staging
  ↓
Validation
  ↓
Production Environment
  ↓
Required Approval
  ↓
Production Deployment
```

This is preferable to implementing approval logic entirely inside shell scripts.

---

## Required Reviewers

A production environment can require approval before a deployment proceeds.

A workflow can reference the protected environment:

```yaml
jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment:
      name: production

    steps:
      - name: Deploy
        run: ./scripts/deploy-production.sh
```

The workflow may pause until the configured protection requirement is satisfied.

The important distinction is:

```text
Workflow authorization
        ≠
Application authorization
```

Environment protection controls whether the deployment job is allowed to proceed. It does not replace application-level authentication or AWS IAM authorization.

---

## Environment Deployment Flow

A production-oriented deployment can use the following model:

```mermaid
flowchart LR
    PR[Pull Request] --> CI[Lint and Tests]
    CI --> BUILD[Build Artifact]
    BUILD --> DEV[Development]
    DEV --> DEVTEST[Development Validation]
    DEVTEST --> STAGE[Staging]
    STAGE --> SMOKE[Smoke Tests]
    SMOKE --> APPROVAL[Production Approval]
    APPROVAL --> PROD[Production]
    PROD --> MONITOR[Monitoring]
    MONITOR --> ROLLBACK[Rollback if Required]
```

The critical architectural property is that the same validated artifact moves through the environments.

---

## Build Once, Promote Many

A common CI/CD mistake is rebuilding the application separately for each environment:

```text
Source
 ├── Build → Development
 ├── Build → Staging
 └── Build → Production
```

This introduces the possibility that the artifacts are not identical.

A stronger model is:

```text
Source
   ↓
Build
   ↓
Immutable Artifact
   ↓
Development
   ↓
Staging
   ↓
Production
```

For Docker-based applications:

```text
Git Commit
    ↓
Docker Build
    ↓
Image: sha-abc123
    ↓
ECR
    ↓
Development
    ↓
Staging
    ↓
Production
```

This allows the production environment to receive the exact image that passed previous validation.

Versioned images are preferable to relying on mutable `latest` tags because a deployment can be associated with a specific artifact and rollback target. :chatgpt-content-reference{index="0"}

---

## Environment Promotion with Docker

A production pipeline should avoid rebuilding the Docker image during production deployment.

Example build:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      image: ${{ steps.meta.outputs.image }}

    steps:
      - uses: actions/checkout@v5

      - name: Build image
        id: build
        run: |
          IMAGE="123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend:${GITHUB_SHA}"
          docker build -t "$IMAGE" .
          docker push "$IMAGE"

      - name: Set image output
        id: meta
        run: echo "image=123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend:${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

Later jobs should deploy that exact image:

```yaml
jobs:
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - name: Deploy image
        env:
          IMAGE: ${{ needs.build.outputs.image }}
        run: ./scripts/deploy.sh "$IMAGE"
```

The production job can consume the same output:

```yaml
jobs:
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Deploy approved image
        env:
          IMAGE: ${{ needs.build.outputs.image }}
        run: ./scripts/deploy.sh "$IMAGE"
```

This creates an artifact promotion model rather than an environment-specific rebuild model.

---

## Environment Separation with AWS

A common AWS deployment model is:

```text
GitHub Actions
       │
       │ OIDC
       ▼
AWS STS
       │
       ▼
IAM Role
       │
       ├── Development Account / Resources
       ├── Staging Account / Resources
       └── Production Account / Resources
```

Where practical, separate AWS accounts provide stronger isolation than merely using different resource names within one account.

For ECS, for example:

```text
development
    └── ECS Cluster
          └── Backend Service

staging
    └── ECS Cluster
          └── Backend Service

production
    └── ECS Cluster
          └── Backend Service
```

The GitHub environment can determine which IAM role and AWS resources are targeted.

---

## GitHub OIDC and Environment-Based AWS Access

GitHub Actions can authenticate to AWS using OIDC rather than storing long-lived AWS access keys.

Example:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v5

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ap-south-1

      - name: Verify identity
        run: aws sts get-caller-identity
```

The environment can restrict access to the production role while staging uses a different role.

```text
GitHub production environment
        ↓
Production IAM role
        ↓
Production AWS resources
```

OIDC reduces the need to store permanent AWS credentials in GitHub. Existing deployment notes also emphasize OIDC and versioned images for production deployments. :chatgpt-content-reference{index="1"}

---

## Environment-Specific Backend Architecture

A Python backend might use the same application artifact across environments while changing infrastructure configuration.

```text
                    Same Application Image
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
        Development     Staging      Production
             │             │             │
             ▼             ▼             ▼
          PostgreSQL     PostgreSQL    PostgreSQL
          Redis          Redis         Redis
          Celery         Celery        Celery
          Nginx          Nginx         Nginx
```

For Django or FastAPI, environment-specific configuration may include:

```text
DATABASE_URL
REDIS_URL
CELERY_BROKER_URL
ALLOWED_HOSTS
CORS_ALLOWED_ORIGINS
AWS_REGION
AWS_RESOURCE_NAMES
LOG_LEVEL
```

The application package itself should remain the same whenever possible.

---

## Environment Parity

Environment parity means that environments behave sufficiently similarly that successful staging validation provides meaningful evidence about production.

Perfect parity is usually expensive and unnecessary.

A practical approach is:

| Concern | Development | Staging | Production |
|---|---|---|---|
| Application image | Same build | Same build | Same build |
| Database engine | Same | Same | Same |
| Redis | Same | Same | Same |
| AWS service types | Similar | Same | Same |
| Scale | Low | Production-like | Production |
| Secrets | Separate | Separate | Separate |
| Data | Synthetic/test | Sanitized/test | Production |
| Approval | Usually none | Optional | Required |

The application artifact should ideally remain identical even when infrastructure capacity differs.

---

## Database Isolation

Database separation is critical.

A production deployment should never accidentally execute against a staging database.

Use separate connection configuration:

```text
Development
    DATABASE_URL → development database

Staging
    DATABASE_URL → staging database

Production
    DATABASE_URL → production database
```

For Django:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
```

The environment supplies the correct value.

Avoid environment detection based on ambiguous conditions such as:

```python
if DEBUG:
    ...
```

Production configuration should be explicit.

---

## Redis and Background Workers

Environment isolation must include asynchronous infrastructure.

For a Django/FastAPI system using Celery:

```text
Production API
      │
      ├── PostgreSQL
      ├── Redis
      └── Celery Workers
```

The staging environment should use separate queues and Redis resources.

Otherwise, a staging worker could consume production jobs.

A safe model is:

```text
staging:
    REDIS_URL → staging Redis
    CELERY_QUEUE → staging

production:
    REDIS_URL → production Redis
    CELERY_QUEUE → production
```

The same principle applies to Kafka topics, message queues, object storage, and other shared infrastructure.

---

## Environment Concurrency

Production deployments should not race with one another.

A common failure scenario is:

```text
Deployment A → production
Deployment B → production
                   ↓
            overlapping rollout
```

Use GitHub Actions concurrency:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    concurrency:
      group: production-deployment
      cancel-in-progress: false

    steps:
      - name: Deploy
        run: ./scripts/deploy.sh
```

This establishes a deployment serialization boundary.

For pull requests, cancellation may be desirable:

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

For production deployment, cancelling an already-running deployment may be dangerous. The correct setting depends on whether interruption is safe for the deployment mechanism.

---

## Environment Approval and Concurrency

Approval and concurrency solve different problems.

| Mechanism | Problem addressed |
|---|---|
| Environment protection | Who/what can deploy |
| Required reviewer | Human authorization |
| Concurrency | Prevent overlapping executions |
| Deployment validation | Whether deployment succeeded |
| Rollback | Recovery from failed deployment |

A production pipeline may therefore use all of them:

```text
Artifact
   ↓
Staging
   ↓
Smoke Tests
   ↓
Production Environment
   ↓
Approval
   ↓
Concurrency Lock
   ↓
Deployment
   ↓
Health Validation
   ↓
Success / Rollback
```

Production approval and smoke testing are also part of the deployment patterns represented in the existing notes. :chatgpt-content-reference{index="2"}

---

## Environment Health Validation

Deployment success should not be defined only as "the deployment command exited with code 0."

After deployment, validate application health.

For a FastAPI service:

```bash
curl --fail --silent --show-error \
  https://api.example.com/health
```

For a Django service behind Nginx:

```bash
curl --fail --silent --show-error \
  https://api.example.com/health/
```

Useful validation layers include:

```text
Deployment command
       ↓
Infrastructure health
       ↓
Application health
       ↓
Dependency health
       ↓
Smoke tests
       ↓
Monitoring
```

A deployment can succeed at the infrastructure layer while the application remains unusable.

---

## Smoke Tests

A staging environment is particularly useful for production-like smoke testing.

Example:

```yaml
jobs:
  smoke-test:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - name: Check API health
        run: |
          curl --fail --silent --show-error \
            https://api-staging.example.com/health

      - name: Check API endpoint
        run: |
          curl --fail --silent --show-error \
            https://api-staging.example.com/api/v1/health
```

Smoke tests should validate the smallest set of critical paths needed to establish deployment confidence.

Do not turn smoke tests into a complete end-to-end test suite.

---

## Rollback Strategy

A production environment is incomplete without a recovery strategy.

For containerized deployments:

```text
Current:
backend:sha-new

Rollback:
backend:sha-previous
```

The previous immutable artifact should remain available in the registry according to the organization's retention policy.

For ECS, rollback can involve deploying a previous task definition revision or previous container image. Existing deployment notes explicitly describe rollback to a previous ECS task definition revision. :chatgpt-content-reference{index="3"}

A rollback flow:

```text
Production failure
       ↓
Stop promotion
       ↓
Identify previous known-good artifact
       ↓
Deploy previous artifact
       ↓
Run health checks
       ↓
Monitor
       ↓
Investigate failed release
```

Rollback should be a deterministic operational procedure, not an emergency improvisation.

---

## Environment History and Auditability

Production deployments should answer:

- What was deployed?
- When was it deployed?
- Which commit produced it?
- Which artifact was used?
- Who approved it?
- Which workflow executed it?
- What environment received it?
- Was it rolled back?

A useful artifact naming strategy is:

```text
backend:<git-sha>
backend:v2.8.1
```

For immutable deployment references, a commit SHA is especially useful:

```text
123456789012.dkr.ecr.ap-south-1.amazonaws.com/backend:8c7d91e
```

Avoid making `latest` the only deployment identifier.

The existing CI/CD notes similarly recommend versioned images rather than relying on `latest` because immutable version references improve rollback and auditability. :chatgpt-content-reference{index="4"}

---

## Multi-Environment Workflow

A simple promotion workflow can be expressed as:

```yaml
name: Backend Deployment

on:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest

    outputs:
      image: ${{ steps.image.outputs.image }}

    steps:
      - uses: actions/checkout@v5

      - name: Build image
        run: |
          IMAGE="registry.example.com/backend:${GITHUB_SHA}"
          docker build -t "$IMAGE" .
          docker push "$IMAGE"

      - name: Export image
        id: image
        run: |
          echo "image=registry.example.com/backend:${GITHUB_SHA}" >> "$GITHUB_OUTPUT"

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - name: Deploy
        env:
          IMAGE: ${{ needs.build.outputs.image }}
        run: ./scripts/deploy.sh staging "$IMAGE"

      - name: Smoke test
        run: ./scripts/smoke-test.sh staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production

    concurrency:
      group: production-deployment
      cancel-in-progress: false

    permissions:
      contents: read
      id-token: write

    steps:
      - name: Deploy
        env:
          IMAGE: ${{ needs.build.outputs.image }}
        run: ./scripts/deploy.sh production "$IMAGE"

      - name: Health validation
        run: ./scripts/smoke-test.sh production
```

The production environment can independently enforce approval requirements.

This separates:

```text
Build
  ↓
Artifact
  ↓
Staging deployment
  ↓
Staging validation
  ↓
Production authorization
  ↓
Production deployment
```

---

## Environment Variables vs Secrets vs Repository Variables

These mechanisms have different responsibilities.

| Mechanism | Typical purpose | Sensitive? | Scope |
|---|---|---:|---|
| `env` | Workflow/job/step runtime values | Not inherently | Workflow/job/step |
| `vars` | Non-secret configuration | No | Repository/org/environment |
| `secrets` | Sensitive values | Yes | Repository/org/environment |
| Environment | Deployment boundary | N/A | Named environment |

A useful design is:

```text
Environment
    ├── vars
    │     ├── AWS_REGION
    │     ├── ECS_CLUSTER
    │     └── SERVICE_NAME
    │
    └── secrets
          └── sensitive values
```

Do not use secrets simply because a value is environment-specific. Non-sensitive configuration should normally use variables.

---

## Environment-Specific AWS Resources

For larger systems, environment isolation should extend across AWS resources.

Example:

```text
Development Account
    ├── ECR
    ├── ECS
    ├── RDS
    └── Redis

Staging Account
    ├── ECR
    ├── ECS
    ├── RDS
    └── Redis

Production Account
    ├── ECR
    ├── ECS
    ├── RDS
    └── Redis
```

Where separate AWS accounts are not practical, resource-level isolation still needs to be explicit.

Terraform commonly models this using separate environment configurations or state boundaries:

```text
infrastructure/
    environments/
        dev/
        staging/
        prod/
```

Environment separation in infrastructure-as-code reduces accidental cross-environment changes. :chatgpt-content-reference{index="5"}

---

## Configuration Drift

Environment drift occurs when environments stop representing the same application architecture.

Examples:

```text
Development:
    Python 3.12
    PostgreSQL 16

Production:
    Python 3.11
    PostgreSQL 14
```

or:

```text
Staging:
    Redis enabled

Production:
    Redis unavailable
```

This weakens staging validation.

Reduce drift by:

- Building one application artifact.
- Using the same base Docker image.
- Managing infrastructure with IaC.
- Versioning deployment configuration.
- Avoiding manual production changes.
- Running automated environment validation.
- Keeping service versions intentionally aligned.

---

## Environment Isolation and Security

Environment separation is also a security boundary.

A production environment should not expose its credentials to every workflow.

Prefer:

```text
Pull Request
    ↓
Read-only CI
    ↓
No production secrets
```

and:

```text
Main branch
    ↓
Staging
    ↓
Production approval
    ↓
Production secrets
```

Do not allow arbitrary pull request code to access production credentials.

This is especially important when pull requests originate from forks or contain untrusted code.

---

## Production Secrets and Runtime Secrets

GitHub environment secrets should not automatically become application runtime secrets.

A better separation is:

```text
GitHub Actions
    ↓
Deployment authorization
    ↓
AWS IAM / OIDC
    ↓
AWS deployment
    ↓
Runtime workload
    ↓
AWS Secrets Manager
```

The running application can retrieve runtime secrets from AWS Secrets Manager or another dedicated secret-management system rather than receiving all sensitive values through the CI pipeline.

Existing deployment material uses Secrets Manager for runtime secrets and separate ECS roles for workload permissions. :chatgpt-content-reference{index="6"} :chatgpt-content-reference{index="7"}

---

## High Availability Considerations

Environments should not introduce unnecessary single points of failure.

For production:

```text
GitHub Actions
      │
      ▼
Production Environment
      │
      ▼
Load Balancer
      │
 ┌────┴────┐
 ▼         ▼
AZ-A      AZ-B
 │         │
ECS       ECS
 │         │
 └────┬────┘
      ▼
Database / Cache
```

Deployment strategy should preserve application availability during rollout.

Depending on the platform, this can involve:

- Rolling deployments
- Blue/green deployments
- Canary releases
- Health checks
- Minimum healthy capacity
- Automatic rollback

The environment controls authorization; the deployment platform controls rollout behavior.

---

## Cost Considerations

More environments generally mean more infrastructure.

For example:

```text
Development → small capacity
Staging     → production-like but controlled capacity
Production  → full capacity
```

Cost optimization can include:

- Smaller development instances
- Scheduled shutdown of non-production resources
- Shared CI infrastructure where safe
- Ephemeral test environments
- Automated cleanup
- Shorter non-production artifact retention

Do not optimize cost by sharing production databases, Redis instances, or credentials across environments. The operational and security risk usually outweighs the infrastructure savings.

---

## Monitoring Deployments

Deployment monitoring should correlate application health with deployment events.

Useful signals include:

- Deployment duration
- Deployment success/failure rate
- Rollback count
- Application error rate
- HTTP 5xx rate
- Latency
- CPU and memory
- Container restart count
- Database health
- Queue depth
- Celery task failures

A useful operational relationship is:

```text
Deployment Event
      ↓
Application Metrics
      ↓
Error / Latency Change
      ↓
Deployment Correlation
      ↓
Rollback Decision
```

Monitoring should remain available after the workflow completes.

---

## Disaster Recovery

Environment strategy should account for infrastructure recovery as well as application rollback.

Rollback handles:

```text
Bad application version
```

Disaster recovery handles broader failures:

```text
AWS resource failure
Database failure
Region failure
Infrastructure corruption
Credential compromise
Configuration corruption
```

Production recovery should therefore include:

- Versioned application artifacts
- Infrastructure-as-code
- Database backups
- Tested restore procedures
- Secrets recovery
- Environment recreation
- Documented deployment procedures
- Recovery objectives

An environment that cannot be recreated reliably is difficult to operate safely at scale.

---

## Common Environment Mistakes

| Mistake | Why it is dangerous | Better approach |
|---|---|---|
| Rebuilding for every environment | Artifacts can differ | Build once and promote |
| Using `latest` only | Weak rollback/auditability | Immutable tags |
| Sharing production secrets | Expands blast radius | Environment-scoped access |
| Sharing production DB with staging | Data corruption risk | Separate databases |
| No approval for production | Accidental releases | Environment protection |
| No deployment concurrency | Race conditions | Production concurrency group |
| Manual production configuration | Configuration drift | IaC and version control |
| Staging unlike production | Weak validation | Maintain meaningful parity |
| Storing runtime secrets in CI | Larger secret exposure surface | Runtime secret manager |
| Treating successful deployment as health | Application can still be broken | Post-deployment validation |

---

## Troubleshooting Environment Deployments

Use a consistent failure-isolation model:

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

### Environment Not Found

**Symptom**

A workflow references an environment but the deployment does not behave as expected.

**Possible causes**

- Environment name mismatch.
- Environment does not exist.
- Wrong repository.
- Environment protection configuration is incorrect.

**Checks**

```text
Repository
→ Settings
→ Environments
→ Verify exact environment name
```

Check the workflow:

```yaml
environment: production
```

The name must correspond to the intended GitHub environment.

---

### Environment Secrets Are Empty

**Symptom**

A secret resolves unexpectedly or the deployment fails authentication.

**Possible causes**

- Secret exists in another environment.
- Job does not reference the expected environment.
- Secret name is incorrect.
- Workflow is running from a different repository.
- Secret is unavailable to the execution context.

**Isolation**

Confirm:

```yaml
jobs:
  deploy:
    environment: production
```

Then verify that the secret exists in the `production` environment.

Never print the secret to diagnose the problem.

---

### Production Deployment Runs Without Expected Approval

**Possible causes**

- Job references the wrong environment.
- Workflow deploys directly without the protected environment.
- Protection rules are configured on another environment.
- Deployment path bypasses the intended production job.

**Check**

```yaml
environment: production
```

Review the environment's protection configuration and deployment history.

---

### Staging Works but Production Fails

Possible failure domains include:

```text
Configuration
Secrets
IAM permissions
AWS resources
Network access
Database
Redis
Application scale
Environment variables
Production-only feature flags
```

Compare environment configuration rather than immediately rebuilding the application.

A useful diagnostic approach is:

```text
Same artifact?
    ↓
Yes
    ↓
Compare environment configuration
    ↓
Compare infrastructure
    ↓
Compare permissions
    ↓
Compare runtime dependencies
```

If the artifact is identical, the investigation can focus on environment-specific differences.

---

### Deployment Race

**Symptom**

Two production deployments overlap.

**Possible causes**

- No concurrency group.
- Different workflow names create different groups.
- Manual and automated deployment workflows use separate groups.

**Correction**

Use a shared production concurrency group:

```yaml
concurrency:
  group: production-deployment
  cancel-in-progress: false
```

Ensure all workflows capable of deploying production use the same logical group.

---

### Rollback Failure

A rollback can fail if:

- The previous image was deleted.
- The previous task definition is unavailable.
- Infrastructure changed incompatibly.
- Database migrations are not backward-compatible.
- Configuration changed with the application.

Application rollback therefore needs compatibility planning.

For database migrations, prefer backward-compatible migration sequences:

```text
Expand
  ↓
Deploy compatible application
  ↓
Migrate data
  ↓
Contract
```

This reduces the risk that an application rollback becomes impossible because of a schema change.

---

## Production Deployment Checklist

Before enabling production deployment:

- [ ] Production environment exists.
- [ ] Required reviewers are configured where required.
- [ ] Production secrets are isolated.
- [ ] Non-sensitive configuration uses variables.
- [ ] AWS authentication uses OIDC where applicable.
- [ ] IAM permissions follow least privilege.
- [ ] Production deployment has concurrency control.
- [ ] Artifact is immutable.
- [ ] Production does not rebuild the application unnecessarily.
- [ ] Health checks exist.
- [ ] Smoke tests exist.
- [ ] Rollback procedure is documented.
- [ ] Previous artifacts remain available.
- [ ] Database migrations are rollback-aware.
- [ ] Monitoring covers deployment health.
- [ ] Deployment history is auditable.
- [ ] Infrastructure is managed consistently.
- [ ] Production and staging have meaningful parity.

---

## Senior-Level Design Considerations

At senior level, environment design is primarily about controlling change.

The important questions are not:

> "How do I create a staging environment?"

They are:

- What is the promotion boundary?
- Which artifact is trusted?
- Who can promote it?
- What prevents unauthorized promotion?
- What prevents concurrent production deployments?
- What happens when deployment partially succeeds?
- How is rollback performed?
- How are runtime secrets separated from CI credentials?
- How is configuration drift detected?
- Can the environment be recreated?
- What evidence proves that the deployed artifact was tested?
- Which failures belong to CI and which belong to the environment?

A mature design therefore looks like:

```text
                    Source
                      │
                      ▼
              CI Validation
                      │
                      ▼
             Immutable Artifact
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
   Development                Security Checks
          │                       │
          └───────────┬───────────┘
                      ▼
                   Staging
                      │
                 Smoke Tests
                      │
                      ▼
              Production Approval
                      │
                Concurrency Lock
                      │
                      ▼
                 Production
                      │
             Health Validation
                      │
              ┌───────┴───────┐
              ▼               ▼
           Healthy         Unhealthy
              │               │
              ▼               ▼
          Continue         Rollback
```

This separates validation, authorization, deployment, and recovery into explicit engineering responsibilities.

---

## Interview Traps

### Environment vs Branch

A branch is a source-control concept.

An environment is a deployment and operational boundary.

They can be related, but they are not interchangeable.

For example:

```text
main branch
    ↓
build artifact
    ↓
staging
    ↓
production
```

A production environment can receive an artifact produced from `main` without requiring a separate permanent production branch.

### Environment vs Secret

An environment is not simply a collection of secrets.

It can provide:

- Configuration
- Secrets
- Protection rules
- Deployment history
- Authorization boundaries

### Approval vs Deployment Success

Approval means:

```text
Authorized to deploy
```

It does not mean:

```text
Deployment is guaranteed to succeed
```

Health validation is still required after approval.

### Rollback vs Redeployment

Redeploying the same failed artifact is not rollback.

Rollback means restoring a previously known-good version.

```text
Current:
sha-new

Rollback:
sha-previous
```

### Staging vs Production

Staging is useful only when it provides meaningful evidence about production behavior.

Simply naming an environment `staging` does not make it production-like.

---

## Key Takeaways

- GitHub Actions environments provide deployment boundaries for environment-specific configuration, secrets, protection rules, and deployment history.
- Production pipelines should preferably build an immutable artifact once and promote that same artifact through development, staging, and production.
- Production environments should combine least-privilege authentication, protected secrets, approval controls, deployment concurrency, health validation, and deterministic rollback.
- Environment isolation must include databases, Redis, queues, AWS resources, credentials, and runtime configuration—not only application URLs.
- Senior-level environment design focuses on controlled promotion, auditability, failure isolation, configuration parity, recovery, and minimizing deployment risk.