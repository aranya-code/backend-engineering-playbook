# 11- Concurrency Questions

## Overview

Concurrency in GitHub Actions controls how multiple workflow runs, jobs, and deployments interact when they target the same logical resource.

For production CI/CD, concurrency is not simply a YAML feature. It is a mechanism for controlling:

- Duplicate work.
- Deployment races.
- Conflicting infrastructure changes.
- Production releases.
- PR validation runs.
- Environment promotion.
- Matrix execution.
- Resource consumption.
- Rollback behavior.
- Operational consistency.

A typical production deployment might look like:

```text
Commit A
   ↓
Build A
   ↓
Staging A
   ↓
Approval
   ↓
Production A
```

while another commit arrives:

```text
Commit B
   ↓
Build B
   ↓
Staging B
   ↓
Production?
```

Without an explicit concurrency strategy, both deployments may interact with the same production environment.

The senior engineering question is therefore not:

> "How do I use `concurrency`?"

It is:

> "Which executions are allowed to coexist, which should be cancelled, which should wait, and what resource is actually being protected?"

---

## What Is Concurrency in GitHub Actions?

GitHub Actions provides a `concurrency` mechanism for limiting workflow or job executions that share a concurrency group.

Basic example:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

This establishes a logical group:

```text
production
```

Executions in the same group are coordinated according to the configured policy.

A concurrency group can be static:

```yaml
group: production
```

or dynamically derived:

```yaml
group: pr-${{ github.event.pull_request.number }}
```

---

## Why Concurrency Exists

Consider a repository where every push to `main` triggers deployment.

```text
Commit A → Deployment A
Commit B → Deployment B
Commit C → Deployment C
```

If commits arrive rapidly, deployments can overlap:

```text
Deployment A ────────────────>
Deployment B ────────>
Deployment C ───────>
```

This can create:

- Deployment races.
- Conflicting infrastructure changes.
- Incorrect final state.
- Database migration conflicts.
- Multiple production rollouts.
- Confusing monitoring signals.
- Wasted runner capacity.

Concurrency lets the system define a controlled execution policy.

---

## Concurrency Model

A useful mental model is:

```text
Workflow / Job
      │
      ▼
Concurrency Group
      │
      ├── Running execution
      │
      └── Pending execution
```

For a deployment group:

```text
production
    │
    ├── Deployment A → running
    │
    └── Deployment B → waiting
```

The exact behavior depends on the configured concurrency policy.

---

## Workflow-Level Concurrency

Concurrency can be configured at workflow level:

```yaml
name: Deploy

on:
  push:
    branches:
      - main

concurrency:
  group: production
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - run: ./deploy.sh
```

This applies concurrency control to workflow runs.

It is useful when the entire workflow represents one logical operation.

---

## Job-Level Concurrency

Concurrency can also be applied to an individual job:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest

    concurrency:
      group: production
      cancel-in-progress: false

    steps:
      - run: ./deploy.sh
```

This is useful when other jobs in the same workflow should remain independent.

For example:

```text
Lint
 ├── independent
Unit Tests
 ├── independent
Security
 ├── independent
Deploy
 └── protected by production concurrency
```

---

## Workflow-Level vs Job-Level Concurrency

| Characteristic | Workflow-level | Job-level |
|---|---|---|
| Scope | Entire workflow run | Specific job |
| Other jobs blocked | Yes | No |
| Useful for | Entire deployment workflow | Deployment stage |
| Resource isolation | Broad | Precise |
| Flexibility | Lower | Higher |

Choose the narrowest scope that protects the resource correctly.

---

## Concurrency Groups

A concurrency group identifies executions that should be coordinated.

Static:

```yaml
concurrency:
  group: production
```

Dynamic:

```yaml
concurrency:
  group: environment-${{ inputs.environment }}
```

PR-specific:

```yaml
concurrency:
  group: pr-${{ github.event.pull_request.number }}
```

Branch-specific:

```yaml
concurrency:
  group: branch-${{ github.ref }}
```

The group should represent the actual resource whose concurrent modification is unsafe.

---

## Choosing the Correct Concurrency Key

The key should answer:

> Which executions conflict with each other?

For a single production deployment target:

```yaml
group: production
```

For multiple environments:

```yaml
group: deploy-${{ inputs.environment }}
```

This allows:

```text
deploy-staging
deploy-production
```

to execute independently.

---

## Avoid Overly Broad Groups

This:

```yaml
group: deployments
```

could unnecessarily serialize:

```text
staging
production
development
```

even though these environments may be independent.

A more precise model is:

```yaml
group: deploy-${{ inputs.environment }}
```

Now:

```text
staging  → staging group
production → production group
```

are independently controlled.

---

## Avoid Overly Narrow Groups

The opposite mistake is equally dangerous.

For example:

```yaml
group: deploy-${{ github.sha }}
```

means every commit receives a different concurrency group.

That effectively prevents different commits from coordinating with each other.

You have concurrency syntax without meaningful resource protection.

---

## `cancel-in-progress`

The `cancel-in-progress` setting determines whether an in-progress execution should be cancelled when another execution enters the same concurrency group.

Example:

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

For rapidly changing PRs, this can reduce wasted work.

---

## When `cancel-in-progress: true` Makes Sense

PR validation is a common example.

Suppose a developer pushes:

```text
Commit A
Commit B
Commit C
```

and each triggers the same expensive test workflow.

If Commit C is now the relevant state, older validation runs may no longer provide useful feedback.

A policy such as:

```yaml
concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

can prioritize the latest PR state.

---

## When `cancel-in-progress: false` Makes Sense

Production deployments often need to avoid abruptly cancelling an active deployment.

Example:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Suppose:

```text
Deployment A
    ↓
Currently modifying production
```

and:

```text
Deployment B
    ↓
Triggered
```

Cancelling A halfway through can leave the environment in an intermediate state.

A safer policy may be:

```text
A finishes
 ↓
B proceeds
```

---

## CI and CD Need Different Concurrency Policies

A common mistake is applying the same policy everywhere.

A better model is:

```text
Pull Request CI
    ↓
cancel-in-progress: true

Production Deployment
    ↓
cancel-in-progress: false
```

CI optimizes for freshness and resource efficiency.

Production deployment optimizes for controlled state transitions.

---

## Production Deployment Concurrency

Example:

```yaml
name: Production Deployment

on:
  workflow_dispatch:

concurrency:
  group: production
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest

    environment:
      name: production

    steps:
      - name: Deploy
        run: ./scripts/deploy.sh
```

This establishes:

```text
Production
    │
    ├── Deployment A → running
    │
    └── Deployment B → waiting
```

---

## Environment-Specific Concurrency

For a reusable deployment workflow:

```yaml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string

concurrency:
  group: deploy-${{ inputs.environment }}
  cancel-in-progress: false
```

This allows:

```text
deploy-development
deploy-staging
deploy-production
```

to behave independently.

---

## Concurrency and GitHub Environments

Environments and concurrency solve different problems.

### Environment

Controls:

- Secrets.
- Variables.
- Reviewers.
- Deployment protection.
- Deployment history.

### Concurrency

Controls:

- Simultaneous executions.
- Deployment races.
- Cancellation/waiting behavior.

They complement each other.

```text
Deployment
    │
    ├── Environment protection
    │       └── "May this deployment proceed?"
    │
    └── Concurrency
            └── "May this deployment run concurrently?"
```

---

## Concurrency and Approval Gates

Consider:

```text
Deployment A
    ↓
Waiting for approval

Deployment B
    ↓
Triggered
```

A production architecture should prevent ambiguous promotion.

Use:

```text
Environment protection
+
Concurrency
+
Immutable artifact identity
```

The approval should correspond to the deployment that actually executes.

---

## Concurrency Does Not Replace Environment Protection

This:

```yaml
concurrency:
  group: production
```

does not answer:

> Who is allowed to deploy?

It only coordinates executions in the group.

Authorization should be handled through:

- Repository permissions.
- Environment protection.
- Branch restrictions.
- IAM.
- Workflow permissions.

---

## Concurrency Does Not Replace Idempotency

Concurrency reduces overlapping execution, but deployment operations should still be safe to retry.

For example:

```text
Deployment
 ↓
Network timeout
 ↓
Workflow retries
```

The deployment command should not corrupt state if the first operation actually succeeded but the workflow did not observe the response.

Use idempotent deployment operations wherever possible.

---

## Concurrency and Idempotency

These are complementary.

```text
Concurrency
    ↓
Prevents conflicting operations

Idempotency
    ↓
Makes repeated operations safe
```

A production deployment should ideally have both.

---

## Concurrency and Race Conditions

A race condition occurs when the outcome depends on the timing of concurrent operations.

Example:

```text
Deployment A
    ↓
Reads current version = v41

Deployment B
    ↓
Reads current version = v41

A → deploys v42
B → deploys v43
```

If both modify shared deployment state without coordination, the final state may be difficult to predict.

---

## Deployment Race Example

Consider:

```text
Production
    ↓
v41
```

Then:

```text
Deployment A → v42
Deployment B → v43
```

Possible sequence:

```text
A starts
B starts
A changes infrastructure
B changes infrastructure
A health checks
B health checks
A finishes
B finishes
```

The resulting state may not match either deployment's assumptions.

Concurrency provides a serialization boundary.

---

## Database Migration Race

Concurrency becomes especially important for schema changes.

Suppose two workflows both execute:

```bash
python manage.py migrate
```

against the same database.

Potential issues include:

- Lock contention.
- Duplicate migration execution attempts.
- Conflicting schema changes.
- Application/schema version mismatch.

A production database migration strategy should coordinate deployment execution separately from ordinary CI.

---

## Expand-Contract and Concurrency

Consider:

```text
Deployment A
    ↓
Adds column

Deployment B
    ↓
Removes old column
```

If deployments overlap unexpectedly, the schema transition may become unsafe.

Use:

```text
Backward-compatible schema
+
Controlled deployment order
+
Concurrency
```

to make the state transition deterministic.

---

## Concurrency With Rolling Deployments

Rolling deployments already coordinate instance replacement, but CI/CD concurrency is still relevant.

```text
GitHub Actions
    ↓
ECS/Kubernetes
    ↓
Rolling deployment
```

The deployment platform controls instance replacement.

GitHub Actions concurrency controls whether multiple deployment commands are launched against the same service.

These are different layers.

---

## Concurrency With Blue-Green Deployment

Blue-green deployments can still race.

Example:

```text
Blue → production
Green → candidate
```

Deployment A may prepare Green while Deployment B attempts to create another Green state.

Use a deployment concurrency group:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Traffic switching should also be treated as a serialized production operation.

---

## Concurrency With Canary Deployment

Canary releases introduce additional state:

```text
v1 → 95%
v2 → 5%
```

A second deployment should not blindly start another canary while the first is being evaluated.

Otherwise:

```text
Canary A
    ↓
5% v2

Canary B
    ↓
5% v3
```

can produce ambiguous routing and monitoring results.

---

## Concurrency and ECS

For Amazon ECS, GitHub Actions may initiate:

```text
Register task definition
        ↓
Update ECS service
        ↓
Wait for deployment
        ↓
Validate health
```

A second workflow should not independently update the same ECS service while the first deployment is still being evaluated.

Use a deployment concurrency group.

---

## Concurrency and Kubernetes

Kubernetes has its own reconciliation model, but GitHub Actions can still issue conflicting changes.

Example:

```text
Workflow A
    ↓
kubectl apply v42

Workflow B
    ↓
kubectl apply v43
```

The cluster may converge to the later desired state, but the workflows may report inconsistent deployment outcomes.

GitHub Actions concurrency prevents competing release workflows from operating simultaneously.

---

## Concurrency and Terraform

Terraform is particularly sensitive to concurrent state operations.

Consider:

```text
Terraform Run A
    ↓
terraform apply

Terraform Run B
    ↓
terraform apply
```

Both may attempt to modify overlapping infrastructure.

Terraform state locking provides one layer of protection, but CI/CD concurrency still provides useful workflow-level coordination.

A production pipeline should avoid allowing independent workflows to intentionally compete for the same infrastructure state.

---

## Concurrency and CloudFormation

CloudFormation stacks also represent shared mutable state.

Avoid:

```text
Workflow A → update-stack
Workflow B → update-stack
```

against the same stack at the same time.

Use:

```text
GitHub Actions concurrency
+
CloudFormation stack state
```

to make infrastructure changes predictable.

---

## Concurrency and Lambda

Lambda deployments can also race:

```text
Deployment A → publish version 42
Deployment B → publish version 43
```

If aliases, traffic weights, or provisioned concurrency are involved, overlapping release workflows can make the final state difficult to reason about.

Serialize production release operations for the same Lambda deployment target.

---

## Concurrency and ECR

ECR is an artifact registry rather than a deployment environment.

Multiple builds can often push different images concurrently.

For example:

```text
orders:v42
payments:v17
users:v31
```

do not necessarily conflict.

The important distinction is:

```text
Artifact creation
```

versus:

```text
Deployment promotion
```

Do not unnecessarily serialize all image builds merely because production deployment must be serialized.

---

## Build Concurrency vs Deployment Concurrency

These should usually be treated differently.

```text
Build A ─────────>
Build B ─────────>
Build C ─────────>
```

can often run concurrently.

But:

```text
Production A
Production B
Production C
```

may need serialization.

This distinction improves throughput without sacrificing deployment safety.

---

## Matrix Jobs and Concurrency

A matrix can generate many jobs:

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

These jobs may safely execute concurrently.

However, if each matrix job modifies the same shared resource, concurrency must be reconsidered.

For example, this is dangerous:

```text
Python 3.11 → modifies shared DB
Python 3.12 → modifies shared DB
Python 3.13 → modifies shared DB
```

Use isolated resources for parallel integration testing.

---

## Matrix Testing With Isolated Databases

A safer architecture is:

```text
Python 3.11 → PostgreSQL test DB A
Python 3.12 → PostgreSQL test DB B
Python 3.13 → PostgreSQL test DB C
```

This allows parallel execution without requiring global deployment-style serialization.

---

## Concurrency and Service Containers

Service containers are generally scoped to their workflow job.

For example:

```yaml
services:
  postgres:
    image: postgres:17
```

Each job can have its own service-container lifecycle.

This makes parallel matrix testing safer than pointing every matrix job at one shared external database.

---

## Concurrency and Redis

Integration tests using Redis should similarly avoid unintended shared mutable state.

For example:

```text
Test Job A → Redis service A
Test Job B → Redis service B
```

is easier to reason about than:

```text
All jobs → shared Redis
```

where test keys, locks, and cache state can interfere.

---

## Concurrency and Kafka

Kafka integration tests require particular care.

Parallel test jobs may interfere through:

- Shared topics.
- Consumer groups.
- Message retention.
- Offsets.

Use isolated topics or test environments where parallel jobs need independent state.

---

## Concurrency and Celery

Celery tests can conflict if parallel jobs share:

- Queues.
- Redis broker state.
- Task IDs.
- Result backends.

Prefer isolated service containers or unique namespaces/queues for independent test jobs.

---

## PR Concurrency

For pull requests, a common pattern is:

```yaml
concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

The logical resource is the PR validation stream.

Example:

```text
PR #123
 ├── Commit A → cancelled
 ├── Commit B → cancelled
 └── Commit C → current
```

This avoids spending resources validating obsolete commits.

---

## Branch Concurrency

For branch-based development:

```yaml
concurrency:
  group: branch-${{ github.ref }}
  cancel-in-progress: true
```

This groups workflow runs by branch.

It is useful when the latest branch state is the only state that matters for a particular validation workflow.

---

## Scheduled Workflow Concurrency

Scheduled workflows can overlap if execution takes longer than expected.

Example:

```yaml
on:
  schedule:
    - cron: "0 * * * *"
```

If one run takes longer than the interval, another run may start.

Use concurrency when overlapping scheduled executions would cause problems.

```yaml
concurrency:
  group: scheduled-maintenance
  cancel-in-progress: false
```

---

## Manual Workflow Concurrency

Manual workflows are especially easy to trigger accidentally multiple times.

Example:

```yaml
on:
  workflow_dispatch:
```

A production deployment should still have:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Manual execution does not eliminate race conditions.

---

## Concurrency With Reusable Workflows

A reusable workflow can centralize deployment concurrency.

Example:

```yaml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string

jobs:
  deploy:
    runs-on: ubuntu-latest

    concurrency:
      group: deploy-${{ inputs.environment }}
      cancel-in-progress: false

    steps:
      - run: ./deploy.sh
```

This allows multiple repositories to follow the same deployment policy.

---

## Reusable Workflow Concurrency Design

A reusable deployment workflow should define clearly:

```text
Input
 ↓
Environment
 ↓
Concurrency group
 ↓
Artifact
 ↓
Deployment
```

The workflow should not derive an unsafe group from arbitrary user-controlled input.

Validate environment values where possible.

For example:

```text
Allowed:
development
staging
production

Rejected:
arbitrary shell fragments
```

---

## Concurrency and Security

Concurrency is not a security authorization mechanism.

A malicious workflow should not gain production access merely because it can use:

```yaml
concurrency:
  group: production
```

Security must still rely on:

- `permissions`.
- Secrets.
- Environments.
- IAM.
- OIDC trust policies.
- Branch protection.
- Trusted workflow sources.

Concurrency controls execution ordering, not authorization.

---

## Untrusted Pull Requests

Do not assume a concurrency group makes a pull request safe.

A forked PR can still contain untrusted code.

The security boundary remains:

```text
Untrusted source
 ↓
Workflow trigger
 ↓
Permissions
 ↓
Secrets
 ↓
Runner
```

Concurrency does not remove any of these risks.

---

## `pull_request` and Concurrency

A common safe PR model is:

```yaml
on:
  pull_request:

concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

This controls duplicate validation without granting additional privileges to the PR.

---

## `pull_request_target` and Concurrency

`pull_request_target` runs with the context of the base repository and therefore requires particular security care.

Concurrency does not make unsafe checkout or execution patterns safe.

Avoid combining:

```text
pull_request_target
+
untrusted checkout
+
secrets
+
powerful permissions
```

merely because the workflow has a concurrency group.

---

## Concurrency and Third-Party Actions

Third-party actions execute inside the same workflow execution context.

If an action has excessive permissions, concurrency does not reduce that privilege.

Use:

```yaml
permissions:
  contents: read
```

and grant additional permissions only where required.

Concurrency should be one layer of defense, not the security boundary.

---

## Concurrency and Self-Hosted Runners

Persistent self-hosted runners introduce additional risks.

If multiple workflows access shared state on the runner:

```text
Runner
 ├── Workspace A
 ├── Workspace B
 └── Persistent cache
```

concurrency alone may not provide filesystem isolation.

Use:

- Ephemeral runners where appropriate.
- Separate runner groups.
- Proper workspace cleanup.
- Restricted permissions.
- Network isolation.

---

## Concurrency and Runner Capacity

Concurrency can reduce load, but overly broad serialization can create queues.

For example:

```text
100 PRs
 ↓
group: all-tests
 ↓
One execution at a time
```

This may produce poor developer feedback.

Prefer scoped groups:

```text
PR #1 → group 1
PR #2 → group 2
PR #3 → group 3
```

unless the resource is genuinely shared.

---

## Cost Implications

Concurrency affects CI cost.

Without PR cancellation:

```text
Commit A → 20 min
Commit B → 20 min
Commit C → 20 min
```

Three obsolete runs may consume approximately 60 runner-minutes.

With appropriate cancellation:

```text
A → cancelled
B → cancelled
C → completes
```

Resource consumption can be significantly reduced.

However, cancellation should not be used where partial execution can leave shared systems inconsistent.

---

## Reliability Considerations

Good concurrency design improves reliability by reducing:

- Conflicting deployments.
- Duplicate infrastructure mutations.
- Race conditions.
- Duplicate scheduled operations.
- Unnecessary CI work.

But concurrency itself can become a reliability problem if:

- Groups are too broad.
- Jobs remain queued indefinitely.
- Cancellation interrupts unsafe operations.
- Deployment ordering is unclear.

---

## High Availability Considerations

CI/CD concurrency should not become a single point of operational failure.

For example, serializing every repository's deployment through:

```yaml
group: production
```

would be inappropriate in a multi-service platform if services have independent production targets.

Prefer:

```text
production-orders
production-payments
production-users
```

when those services can safely deploy independently.

---

## Microservices Concurrency

For a microservice architecture:

```text
orders
payments
users
notifications
```

each service may have its own deployment resource.

Use:

```yaml
group: production-${{ inputs.service }}
```

rather than:

```yaml
group: production
```

if services do not share deployment state.

---

## Shared Infrastructure

Some resources genuinely require global coordination.

For example:

```text
Terraform state
Shared Kubernetes cluster configuration
Shared production database migration
Global API gateway
```

may require broader serialization.

The concurrency scope should follow the shared mutable resource.

---

## Monorepo Concurrency

In a monorepo:

```text
services/
  orders/
  payments/
  users/
```

selective deployment can use service-specific concurrency:

```yaml
group: deploy-${{ inputs.service }}-${{ inputs.environment }}
```

Then:

```text
orders/staging
payments/staging
```

can potentially deploy independently.

But:

```text
shared infrastructure
```

may use a separate global concurrency group.

---

## Dependency-Aware Concurrency

If:

```text
payments
    ↓
shared-contract
```

requires coordinated deployment, independent service concurrency may not be sufficient.

The deployment architecture should understand dependency relationships.

Concurrency should protect shared state without unnecessarily serializing independent work.

---

## Concurrency and Fan-Out/Fan-In

Consider:

```text
            ┌── Unit Tests
            │
Build ──────┼── Integration Tests
            │
            └── Security
                    ↓
                  Deploy
```

Parallel jobs can fan out.

Deployment then becomes the fan-in point.

A common pattern is:

```text
Parallel validation
        ↓
Build artifact
        ↓
Serialized deployment
```

This provides high CI throughput with controlled CD execution.

---

## Concurrency and Outputs

Outputs can identify the artifact entering a serialized deployment.

Example:

```yaml
jobs:
  build:
    outputs:
      image: ${{ steps.image.outputs.image }}

    steps:
      - id: image
        run: |
          echo "image=123456789.dkr.ecr.ap-south-1.amazonaws.com/api:${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

Deployment:

```yaml
jobs:
  deploy:
    needs: build

    concurrency:
      group: production
      cancel-in-progress: false

    steps:
      - run: echo "Deploying ${{ needs.build.outputs.image }}"
```

This makes the deployment target explicit.

---

## Concurrency and Artifacts

Artifacts should carry immutable identity.

For example:

```text
orders-api
commit: 8f3a2c1
image digest: sha256:...
```

A serialized deployment should consume that exact artifact.

Do not let the deployment job silently resolve:

```text
latest
```

at execution time.

---

## Concurrency and Caches

Caches are generally not deployment artifacts.

A cache may be shared across runs for performance.

For example:

```text
pip cache
Docker build cache
npm cache
```

The cache should not be treated as the authoritative source of a production release.

Concurrency therefore should protect the release artifact independently of cache behavior.

---

## Concurrency and Docker Tags

Mutable tags can create race conditions.

Consider:

```text
Build A → push latest
Build B → push latest
```

Now:

```text
latest
```

may refer to B even if a deployment expected A.

Prefer immutable identifiers:

```text
orders:8f3a2c1
```

or:

```text
orders@sha256:...
```

for deployment promotion.

---

## Concurrency and ECR Promotion

A good architecture is:

```text
Build
 ↓
Push immutable image to ECR
 ↓
Record digest
 ↓
Staging
 ↓
Approval
 ↓
Production
```

Multiple image builds can occur concurrently.

Production promotion should be serialized per target.

---

## Concurrency and Rollback

Rollback itself should use the same production deployment concurrency boundary.

For example:

```text
Production deployment
    ↓
group: production
```

and:

```text
Rollback
    ↓
group: production
```

This prevents:

```text
Deployment A
+
Rollback B
```

from modifying production simultaneously.

---

## Rollback Race Example

Suppose:

```text
Production = v43
```

and:

```text
Deployment v44
```

fails.

A rollback begins:

```text
Rollback → v43
```

At the same time, another release starts:

```text
Deployment v45
```

Without coordination:

```text
v44 → v43 → v45
```

may happen while health checks and operators are reacting to different states.

The deployment control plane should serialize these operations.

---

## Concurrency and Health Checks

A deployment should not be considered complete merely because the deployment API returned success.

Example:

```text
ECS update-service → success
```

does not necessarily mean:

```text
Application → healthy
```

A serialized deployment should usually include:

```text
Deploy
 ↓
Wait
 ↓
Health validation
 ↓
Complete
```

This reduces the chance of starting the next release before the previous one is operationally stable.

---

## Concurrency and Monitoring

Monitoring should identify:

- Deployment ID.
- Concurrency group.
- Commit SHA.
- Artifact digest.
- Environment.
- Start time.
- End time.
- Result.
- Rollback status.

This makes concurrent deployment incidents easier to reconstruct.

---

## Common Concurrency Mistakes

### Using One Global Group for Everything

```yaml
group: production
```

may serialize unrelated services.

### Using the Commit SHA as the Group

```yaml
group: ${{ github.sha }}
```

does not coordinate different commits.

### Cancelling Production Deployments

```yaml
cancel-in-progress: true
```

can interrupt state-changing operations.

### Assuming Concurrency Provides Security

It does not replace permissions, environments, IAM, or secrets protection.

### Ignoring Rollbacks

Rollback must participate in the same deployment coordination model.

### Ignoring Infrastructure Locking

GitHub concurrency and Terraform/CloudFormation/Kubernetes state mechanisms solve different problems.

### Sharing Mutable Deployment Tags

Using `latest` makes artifact identity ambiguous.

### Serializing Independent Builds

Builds that do not share mutable state usually do not need global serialization.

---

## Troubleshooting Concurrency Problems

Use the standard failure model:

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

---

## Workflow Appears Stuck

### Symptom

A workflow remains pending.

### Possible Causes

- Another execution occupies the concurrency group.
- A previous workflow is still running.
- A deployment is waiting for approval.
- A runner is unavailable.

### Isolation Strategy

Inspect workflow runs and identify the group owner.

### Commands / Checks

```bash
gh run list
```

Inspect a specific run:

```bash
gh run view RUN_ID
```

### Corrective Action

Determine whether the blocking execution should:

- Finish.
- Be cancelled.
- Be rerun.
- Be investigated.

### Prevention

Use appropriately scoped concurrency groups.

---

## Unexpected Cancellation

### Symptom

A workflow starts and an earlier workflow is cancelled.

### Possible Cause

Both executions use:

```yaml
cancel-in-progress: true
```

with the same concurrency group.

### Isolation

Inspect the workflow's concurrency configuration and run history.

### Corrective Action

Use a more specific group or disable cancellation if older executions must finish.

---

## Two Production Deployments Run

### Symptom

Two deployments appear to modify production simultaneously.

### Possible Causes

- No concurrency group.
- Different concurrency group names.
- Deployment occurs through different workflows.
- Reusable workflows use inconsistent groups.
- Manual operational changes bypass the CI/CD control plane.

### Isolation

Trace:

```text
Workflow
 ↓
Job
 ↓
Environment
 ↓
Concurrency group
 ↓
Deployment target
```

### Prevention

Centralize production deployment policy in a reusable workflow where practical.

---

## All Deployments Are Queued

### Symptom

Many unrelated services are waiting.

### Possible Cause

A broad group:

```yaml
group: production
```

is shared across independent services.

### Corrective Action

Scope the group:

```yaml
group: production-${{ inputs.service }}
```

### Prevention

Model concurrency around actual shared resources.

---

## Deployment Cancelled During Infrastructure Mutation

### Symptom

Infrastructure is left partially updated.

### Possible Cause

Production used:

```yaml
cancel-in-progress: true
```

### Corrective Action

Recover the infrastructure state first, then reassess deployment state.

### Prevention

Use:

```yaml
cancel-in-progress: false
```

for operations where cancellation is unsafe.

---

## Rollback and Deployment Conflict

### Symptom

A rollback and deployment execute around the same time.

### Possible Cause

Rollback uses a different concurrency group.

### Corrective Action

Use the same production deployment group for both operations.

Example:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

### Prevention

Treat rollback as a production deployment operation.

---

## Terraform Concurrency Failure

### Symptom

Terraform jobs conflict over infrastructure state.

### Possible Causes

- Multiple workflows apply the same state.
- GitHub Actions concurrency is absent.
- State locking is misconfigured.
- Separate workflows operate on the same infrastructure.

### Checks

```bash
terraform plan
terraform state list
```

Inspect the remote state backend and locking configuration.

### Prevention

Coordinate GitHub workflow concurrency with infrastructure-state locking.

---

## Database Migration Concurrency Failure

### Symptom

Deployment fails during migration.

### Possible Causes

- Multiple deployments run migrations.
- Incompatible schema changes.
- Long-running locks.
- Application and schema versions are incompatible.

### Checks

Inspect:

```text
Deployment history
Database migration state
Database locks
Application version
```

### Prevention

Use:

```text
Expand-contract
+
Controlled migration ownership
+
Deployment concurrency
```

---

## Concurrency Troubleshooting Matrix

| Symptom | Likely Cause | Primary Check | Prevention |
|---|---|---|---|
| Run queued | Existing group member | `gh run list` | Correct group scope |
| Older run cancelled | `cancel-in-progress: true` | Workflow YAML | Adjust cancellation |
| Two deployments overlap | Missing/inconsistent group | Workflow/job config | Shared deployment group |
| All services queue | Group too broad | Group naming | Service-specific groups |
| Rollback races release | Different groups | Deployment workflows | Same production group |
| CI is slow | Over-serialization | Group scope | Narrow groups |
| DB migration conflict | Concurrent deployments | Deployment + DB state | Migration coordination |
| Terraform conflict | Shared state | Backend locking | CI + state coordination |

---

## GitHub CLI for Concurrency Operations

GitHub CLI is useful for inspecting runs.

List recent runs:

```bash
gh run list
```

List runs for a workflow:

```bash
gh run list --workflow deploy.yml
```

Inspect a run:

```bash
gh run view RUN_ID
```

View logs:

```bash
gh run view RUN_ID --log
```

Watch a run:

```bash
gh run watch RUN_ID
```

Rerun a failed workflow:

```bash
gh run rerun RUN_ID
```

Cancel a workflow:

```bash
gh run cancel RUN_ID
```

The CLI helps inspect the symptoms; the workflow definition and deployment state determine the actual concurrency model.

---

## Production CI/CD Concurrency Architecture

A mature pipeline can use different policies for different stages:

```text
                         ┌── Unit Tests ───────┐
                         │                     │
Pull Request ────────────┼── Integration ──────┼── Validation
                         │                     │
                         └── Security ────────┘
                                      │
                                      ▼
                                    Build
                                      │
                                      ▼
                                  ECR Image
                                      │
                                      ▼
                                   Staging
                                      │
                                      ▼
                                  Approval
                                      │
                              production group
                                      │
                                      ▼
                                 Production
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                    Monitoring                 Rollback
```

The important distinction is:

```text
Parallelize independent work.
Serialize shared mutable state.
```

---

## Production Concurrency Reference Workflow

```yaml
name: Production Deployment

on:
  workflow_dispatch:
    inputs:
      image:
        description: "Immutable image reference"
        required: true
        type: string

permissions:
  contents: read
  id-token: write

concurrency:
  group: production
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest

    environment:
      name: production

    steps:
      - name: Validate image reference
        env:
          IMAGE: ${{ inputs.image }}
        run: |
          test -n "$IMAGE"
          echo "Deploying immutable artifact: $IMAGE"

      - name: Authenticate with AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Deploy
        env:
          IMAGE: ${{ inputs.image }}
        run: |
          ./scripts/deploy.sh "$IMAGE"

      - name: Validate deployment
        run: |
          ./scripts/healthcheck.sh
```

The important design elements are:

- Immutable artifact input.
- Production environment.
- OIDC-compatible permissions.
- Production concurrency.
- No production cancellation.
- Explicit health validation.

---

## CI Concurrency Reference Workflow

```yaml
name: Pull Request CI

on:
  pull_request:

concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

This is a reasonable model when older PR runs become obsolete after a new commit is pushed.

---

## Multi-Environment Deployment Workflow

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest

    environment:
      name: ${{ inputs.environment }}

    concurrency:
      group: deploy-${{ inputs.environment }}
      cancel-in-progress: false

    steps:
      - name: Deploy
        env:
          ENVIRONMENT: ${{ inputs.environment }}
          IMAGE: ${{ inputs.image }}
        run: |
          ./scripts/deploy.sh "$ENVIRONMENT" "$IMAGE"
```

This creates independent groups:

```text
deploy-development
deploy-staging
deploy-production
```

---

## Service-Specific Deployment Workflow

For a microservice platform:

```yaml
concurrency:
  group: deploy-${{ inputs.service }}-${{ inputs.environment }}
  cancel-in-progress: false
```

Possible groups:

```text
deploy-orders-production
deploy-payments-production
deploy-users-production
```

This allows independent services to deploy concurrently while protecting each service's production target.

---

## Shared Infrastructure Workflow

For shared infrastructure:

```yaml
concurrency:
  group: shared-production-infrastructure
  cancel-in-progress: false
```

This can protect resources such as:

```text
Shared Terraform state
Shared API Gateway
Shared production network
Shared infrastructure stack
```

The scope should be based on actual resource ownership.

---

## Architecture Decision: What Should Be Serialized?

Ask these questions:

1. Does the execution mutate shared state?
2. Can two executions safely overlap?
3. Can one execution invalidate the assumptions of another?
4. Is rollback affected by concurrent execution?
5. Does the underlying platform already provide locking?
6. Can the operation be made idempotent?
7. Is the resource environment-specific or globally shared?
8. Does serialization materially affect throughput?

The answers determine the appropriate concurrency boundary.

---

## Architecture Decision: What Should Be Cancelled?

Cancellation is appropriate when:

```text
Older work is obsolete
+
Cancellation is safe
+
No shared mutable state is left inconsistent
```

Examples:

```text
PR linting
PR unit tests
PR static analysis
```

Cancellation is riskier when:

```text
Operation mutates production
+
Partial execution has side effects
```

Examples:

```text
Production deployment
Database migration
Infrastructure apply
Traffic switching
```

---

## Architecture Decision: What Should Wait?

Waiting is useful when:

```text
The operation is valid
+
It must occur after another operation
+
Cancelling it would lose useful work
```

Examples:

```text
Production deployment B
waiting for
Production deployment A
```

However, long queues should trigger investigation rather than being accepted as normal.

---

## Concurrency and Failure Domains

A mature CI/CD system identifies shared failure domains.

Examples:

```text
Repository
Workflow
Runner
Artifact Registry
Environment
Database
Infrastructure State
Production Service
```

Concurrency should be applied where multiple executions can damage or invalidate the same failure domain.

---

## High-Scale GitHub Actions Architecture

At scale:

```text
Developer
    ↓
PR
    ↓
Parallel CI
    ├── Python matrix
    ├── PostgreSQL matrix
    ├── Redis integration
    ├── Security
    └── Build
            ↓
        Immutable Artifact
            ↓
       Environment Promotion
            ↓
       Serialized Deployment
```

This architecture keeps expensive validation parallel while protecting deployment targets.

---

## Enterprise Governance

Organizations should standardize concurrency policies for high-risk workflows.

Possible governance rules:

- Production deployments must define concurrency.
- Rollbacks must share the production deployment group.
- Infrastructure applies must coordinate shared state.
- Deployment workflows should use immutable artifacts.
- CI and CD should have different cancellation policies where appropriate.
- Reusable deployment workflows should standardize production behavior.
- Concurrency groups should reflect actual shared resources.
- Production workflows should be auditable.

---

## Common Interview Traps

### "Concurrency Prevents Two Workflows From Running"

Too broad.

Concurrency coordinates executions that share the same concurrency group. Independent groups can run simultaneously.

### "`cancel-in-progress: true` Is Always Better"

False.

It is useful for obsolete CI runs but may be unsafe for state-changing production operations.

### "Concurrency Provides Deployment Authorization"

False.

Authorization comes from permissions, environments, IAM, branch protections, and related controls.

### "Terraform State Locking Makes GitHub Concurrency Unnecessary"

Not necessarily.

Terraform locking protects state operations at the infrastructure layer. GitHub concurrency can coordinate the higher-level deployment workflow and prevent competing release operations.

### "All Production Deployments Should Use One Global Group"

Not necessarily.

Independent services may safely deploy concurrently.

### "A Unique SHA Is a Good Concurrency Group"

Usually not for deployment coordination.

Different SHAs produce different groups and therefore do not coordinate.

---

## Senior Interview Questions

### How Would You Design Concurrency for PR CI?

Use a PR-specific group:

```yaml
concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

The latest PR commit supersedes older validation runs.

---

### How Would You Design Production Deployment Concurrency?

Use a production-target-specific group:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Combine it with:

- Protected environment.
- Approval controls.
- Immutable artifacts.
- Least-privilege permissions.
- Health validation.
- Rollback.

---

### Should Build Jobs Be Serialized?

Usually not.

Independent builds can execute concurrently:

```text
Build A ──┐
Build B ──┼── parallel
Build C ──┘
```

Only shared mutable resources should generally require serialization.

---

### How Would You Handle Multiple Services in a Monorepo?

Use service- and environment-specific groups:

```yaml
group: deploy-${{ inputs.service }}-${{ inputs.environment }}
```

Then independently deployable services do not unnecessarily block one another.

---

### How Would You Handle a Shared Database?

The application deployment groups may be service-specific, but schema migrations against one shared database may require a broader migration coordination mechanism.

For example:

```text
Application deployments
    ↓
service-specific groups

Database migrations
    ↓
shared database migration group
```

This separates application concurrency from database-schema concurrency.

---

### How Would You Prevent a Rollback From Racing With a New Deployment?

Use the same production concurrency group for both:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Treat rollback as another production state transition.

---

### What Is the Relationship Between Concurrency and Idempotency?

Concurrency reduces simultaneous conflicting execution.

Idempotency makes repeated execution safe.

Production deployment systems should ideally provide both.

---

### How Would You Design Concurrency for Terraform?

Identify the actual Terraform state boundary.

If multiple workflows operate on the same state:

```text
shared state
    ↓
shared concurrency group
```

Combine GitHub Actions coordination with Terraform's backend locking rather than relying on either layer alone.

---

### How Does Concurrency Improve CI Cost?

For PR workflows, cancelling obsolete runs prevents expensive tests from continuing after newer commits supersede them.

For example:

```text
Commit A → cancelled
Commit B → cancelled
Commit C → completes
```

This can reduce runner consumption significantly.

---

### What Is the Biggest Concurrency Design Principle?

A strong answer is:

> Parallelize independent work and serialize operations that mutate shared state.

This principle applies beyond GitHub Actions to:

- Databases.
- Terraform.
- Kubernetes.
- ECS.
- CloudFormation.
- Deployment traffic.
- Message processing.
- Release management.

---

## Senior Production Scenarios

### Scenario: Production Must Never Have Two Active Deployments

Design:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Then combine with:

```text
Production Environment
 ↓
Approval
 ↓
Immutable artifact
 ↓
Deployment
 ↓
Health validation
```

---

### Scenario: Developers Push Five Commits to One PR

Use:

```yaml
concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

Older validation runs become obsolete as newer commits arrive.

---

### Scenario: Three Microservices Deploy Independently

Use:

```yaml
concurrency:
  group: deploy-${{ inputs.service }}-${{ inputs.environment }}
  cancel-in-progress: false
```

This produces:

```text
orders-production
payments-production
users-production
```

instead of serializing all production deployments.

---

### Scenario: A Shared Terraform State Is Used by Multiple Repositories

Use a shared coordination strategy around the state boundary.

```text
Repository A
    ↓
Terraform state X

Repository B
    ↓
Terraform state X
```

Both workflows need to respect the same resource ownership and locking model.

---

### Scenario: Deployment A Is Waiting for Approval and Deployment B Is Triggered

The system must define which release should be promoted.

A robust design uses:

```text
Immutable artifact
+
Environment protection
+
Deployment concurrency
+
Clear release ownership
```

Do not let approval become detached from artifact identity.

---

### Scenario: Deployment Succeeds but Health Checks Fail

The deployment should not simply release the concurrency boundary and allow another deployment to proceed blindly.

Instead:

```text
Deploy
 ↓
Health validation
 ↓
Failure
 ↓
Rollback / incident handling
 ↓
Stable production state
```

The exact behavior depends on the deployment strategy.

---

## Production Review Checklist

### Concurrency Design

- [ ] Every shared production deployment target has a concurrency policy.
- [ ] Concurrency groups reflect actual resource boundaries.
- [ ] CI and CD use appropriate cancellation policies.
- [ ] Independent services are not unnecessarily serialized.
- [ ] Shared infrastructure has explicit coordination.

### Deployment Safety

- [ ] Production deployments do not get cancelled unexpectedly.
- [ ] Rollbacks use the same production concurrency boundary.
- [ ] Deployment artifacts are immutable.
- [ ] Health validation is part of deployment completion.
- [ ] Database migration concurrency is explicitly considered.

### Security

- [ ] Concurrency is not treated as an authorization mechanism.
- [ ] Environment protection is configured appropriately.
- [ ] IAM permissions remain least privilege.
- [ ] OIDC trust is restricted.
- [ ] Untrusted PR workflows do not receive unnecessary secrets.

### Reliability

- [ ] Deployment operations are idempotent where possible.
- [ ] Race conditions have been considered.
- [ ] Rollback is coordinated.
- [ ] Monitoring identifies the active deployment.
- [ ] Failure recovery is documented.

### Performance and Cost

- [ ] Independent CI work runs in parallel.
- [ ] Obsolete PR runs can be cancelled safely.
- [ ] Concurrency groups are not unnecessarily broad.
- [ ] Runner capacity is sufficient for expected queues.
- [ ] Expensive deployment queues are monitored.

---

## Key Takeaways

- **Concurrency should be designed around shared mutable resources: parallelize independent CI work and serialize operations that can conflict, especially production deployments and shared infrastructure changes.**
- **Use `cancel-in-progress: true` when older work is safely obsolete, such as PR validation; use `false` for state-changing operations where cancellation can leave systems inconsistent.**
- **Concurrency is not authorization. Combine it with environments, least-privilege permissions, OIDC/IAM, approvals, immutable artifacts, and branch protections for production security.**
- **Deployment, rollback, database migration, Terraform, ECS, Kubernetes, and traffic-switching operations should be considered together when defining concurrency boundaries and race-condition prevention.**
- **Senior CI/CD design minimizes unnecessary serialization while guaranteeing deterministic behavior for shared resources, balancing throughput, reliability, cost, and operational safety.**