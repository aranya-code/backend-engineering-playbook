# 03- Production CI CD Architecture

## Overview

A production CI/CD architecture is the system that moves a code change from source control to a validated, observable, recoverable production state.

GitHub Actions provides the execution platform, but production architecture is broader than workflow YAML. It includes:

- Source and trigger design.
- CI validation.
- Test infrastructure.
- Build systems.
- Artifact management.
- Environment promotion.
- Deployment orchestration.
- Cloud authentication.
- Runner infrastructure.
- Security boundaries.
- Observability.
- Rollback and disaster recovery.
- Governance and operational controls.

A mature architecture should make the following lifecycle explicit:

```text
Pull Request
    ↓
Lint
    ↓
Unit Tests
    ↓
Integration Tests
    ↓
Security Scan
    ↓
Matrix Validation
    ↓
Build
    ↓
Immutable Artifact
    ↓
Container Image
    ↓
Registry
    ↓
Staging
    ↓
Health Validation
    ↓
Approval
    ↓
Production
    ↓
Monitoring
    ↓
Rollback if required
```

The central architectural principle is:

> Build once, produce an immutable artifact, promote that artifact through environments, and keep enough metadata to reproduce, observe, and roll back the deployment.

---

## Production CI/CD Architecture

A production pipeline should separate validation, artifact creation, promotion, and deployment.

```mermaid
flowchart LR
    DEV[Developer] --> PR[Pull Request]

    PR --> PLAN[Planning]
    PLAN --> LINT[Lint]
    PLAN --> UNIT[Unit Tests]
    PLAN --> INT[Integration Tests]
    PLAN --> SEC[Security]
    PLAN --> MATRIX[Matrix Tests]

    INT --> SERVICES[(PostgreSQL / Redis)]

    LINT --> GATE[Quality Gate]
    UNIT --> GATE
    INT --> GATE
    SEC --> GATE
    MATRIX --> GATE

    GATE --> BUILD[Docker Buildx]
    BUILD --> SCAN[Scan / SBOM / Provenance]
    SCAN --> REG[ECR / Artifact Registry]

    REG --> STG[Staging]
    STG --> VALIDATE[Health Validation]

    VALIDATE --> APPROVAL[Production Approval]
    APPROVAL --> PROD[Production]

    PROD --> MON[Monitoring]
    MON --> DECISION{Healthy?}

    DECISION -->|Yes| ACTIVE[Continue]
    DECISION -->|No| ROLLBACK[Rollback]

    ROLLBACK --> REG
```

Each stage has a different responsibility.

| Stage | Primary responsibility |
|---|---|
| Pull Request | Change validation |
| Planning | Determine affected work |
| CI | Prove correctness |
| Build | Produce deployable artifact |
| Registry | Store immutable artifact |
| Staging | Validate deployment behavior |
| Approval | Apply production policy |
| Production | Run the artifact |
| Monitoring | Detect runtime problems |
| Rollback | Restore a known-good state |

---

## GitHub Actions Execution Model

GitHub Actions has several architectural layers:

```text
Workflow
   ↓
Job
   ↓
Step
   ↓
Action / Shell Command
   ↓
Runner
```

### Workflow

A workflow defines the automation boundary.

```yaml
name: CI

on:
  pull_request:
  push:
    branches:
      - main
```

### Job

A job defines an execution unit.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
```

Jobs can execute independently or depend on other jobs.

### Step

A step performs an operation inside a job.

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Run tests
    run: pytest
```

### Action

An action packages reusable functionality.

Examples include:

- Checkout.
- Python setup.
- Docker Buildx.
- Artifact upload.
- AWS authentication.

### Runner

The runner executes the job.

It may be:

- GitHub-hosted.
- Self-hosted.
- Persistent.
- Ephemeral.
- Linux.
- Windows.
- Specialized for private-network access.

---

## Workflow Architecture

A production repository should avoid turning one workflow into an unmaintainable collection of unrelated responsibilities.

A reasonable separation is:

```text
.github/workflows/
    ci.yml
    security.yml
    deployment.yml
    release.yml
    infrastructure.yml
```

The exact number depends on repository complexity.

The architectural goal is clear ownership rather than maximum workflow count.

---

## CI Architecture

Continuous Integration should answer:

> Is this change safe to merge?

A typical CI architecture is:

```text
Pull Request
    ↓
Planning
    ↓
┌────────────┬────────────┬────────────┐
│ Lint       │ Unit       │ Security   │
│            │ Tests      │            │
└────────────┴────────────┴────────────┘
              ↓
       Integration Tests
              ↓
       Compatibility Matrix
              ↓
         Quality Gate
```

Independent validation should run in parallel.

---

## Parallel CI

Example:

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ruff check .

  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/unit

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip-audit

  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/integration

  quality-gate:
    needs:
      - lint
      - unit
      - security
      - integration
    runs-on: ubuntu-latest
    steps:
      - run: echo "CI passed"
```

This reduces wall-clock time compared with executing every stage sequentially.

---

## Fan-Out and Fan-In

Fan-out creates parallel work:

```text
             ┌── Lint
             │
Planning ────┼── Unit Tests
             │
             ├── Security
             │
             └── Integration Tests
```

Fan-in waits for multiple branches:

```text
Lint ─────────┐
Unit ─────────┤
Security ─────┼──→ Quality Gate
Integration ──┘
```

This pattern is fundamental to scalable CI.

---

## Dependency Graph Design

Use `needs` to express actual dependencies.

```yaml
jobs:
  build:
    needs:
      - lint
      - unit
      - integration
```

Avoid artificial dependencies such as:

```text
lint → unit → security → integration
```

when these jobs are logically independent.

A dependency should exist because the downstream job requires the upstream result or output.

---

## Planning Jobs

Large repositories benefit from a planning phase.

```text
Changed Files
     ↓
Planning Job
     ↓
Affected Services
     ↓
Dynamic Matrix
     ↓
Targeted CI
```

For a monorepo:

```text
services/
    orders/
    payments/
    users/
```

A change under:

```text
services/orders/
```

does not necessarily require rebuilding every service.

---

## Dynamic Matrix Architecture

A planning job can produce structured JSON.

```yaml
jobs:
  plan:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.plan.outputs.matrix }}

    steps:
      - uses: actions/checkout@v4

      - id: plan
        run: |
          echo 'matrix={"service":["orders","payments"]}' >> "$GITHUB_OUTPUT"

  test:
    needs: plan
    strategy:
      matrix: ${{ fromJSON(needs.plan.outputs.matrix) }}

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/test-service.sh "${{ matrix.service }}"
```

Dynamic matrix values should be generated from trusted, validated inputs.

Do not treat arbitrary user-controlled strings as safe executable commands.

---

## Test Matrix Architecture

Matrix testing is useful for compatibility validation.

```yaml
strategy:
  fail-fast: false
  max-parallel: 4
  matrix:
    python:
      - "3.11"
      - "3.12"
    database:
      - postgres
      - mysql
```

This creates:

```text
Python 3.11 + PostgreSQL
Python 3.11 + MySQL
Python 3.12 + PostgreSQL
Python 3.12 + MySQL
```

Matrix cardinality grows multiplicatively:

```text
Python versions
× databases
× operating systems
× other dimensions
```

Large matrices can become expensive and can overload downstream systems.

---

## PR Matrix vs Nightly Matrix

A practical architecture is:

```text
Pull Request
    ↓
Small, high-value matrix

Nightly
    ↓
Full compatibility matrix

Release
    ↓
Production-supported matrix
```

This provides fast developer feedback without eliminating broad compatibility testing.

---

## Integration Testing Architecture

Backend applications commonly depend on external services.

Example:

```text
Python Application
       ↓
   ┌───┴────┐
   ↓        ↓
PostgreSQL Redis
   │        │
   └───┬────┘
       ↓
     pytest
       ↓
   Test Reports
```

For Django:

```text
Django
  ↓
PostgreSQL
  ↓
Redis
  ↓
Celery
```

For FastAPI:

```text
FastAPI
  ↓
PostgreSQL
  ↓
Redis
  ↓
pytest / HTTP Tests
```

---

## Service Containers

Service containers are useful for isolated CI dependencies.

Example:

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app
        options: >-
          --health-cmd "pg_isready -U test -d app"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - run: pytest tests/integration
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app
```

The architecture must account for the runner's networking model.

---

## Containerized Job Architecture

A job itself can execute inside a container.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    container:
      image: python:3.12-slim

    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest
```

This can improve runtime consistency, but containerized jobs introduce their own networking, filesystem, and tooling considerations.

---

## Docker Build Architecture

A production Docker build should generally use Buildx and multi-stage builds.

```text
Source
 ↓
Dockerfile
 ↓
Build Context
 ↓
BuildKit / Buildx
 ↓
Layer Cache
 ↓
Multi-stage Build
 ↓
Security Scan
 ↓
SBOM / Provenance
 ↓
Registry
```

Example:

```yaml
- name: Set up Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

---

## Docker Image Identity

Avoid using only:

```text
latest
```

for production deployment identity.

Prefer:

```text
orders-api:<commit-sha>
```

and retain the digest:

```text
orders-api@sha256:<digest>
```

A digest identifies the exact image content.

---

## Build Once, Deploy Many

The production architecture should preferably be:

```text
Source
  ↓
Build
  ↓
Artifact
  ↓
Registry
  ↓
Staging
  ↓
Production
```

Not:

```text
Source
 ├── Build → Staging
 └── Build → Production
```

Rebuilding can introduce differences caused by:

- Dependency resolution.
- Base image changes.
- Build tooling.
- Network dependencies.
- Environment differences.

---

## Artifact Promotion

The artifact should remain unchanged while its environment changes.

```text
Image Digest
    │
    ├── Staging
    │
    └── Production
```

Environment configuration belongs outside the artifact whenever practical.

```text
Same Artifact
    +
Staging Configuration
    =
Staging Runtime
```

```text
Same Artifact
    +
Production Configuration
    =
Production Runtime
```

---

## Artifact Metadata

A production deployment should retain:

| Metadata | Purpose |
|---|---|
| Commit SHA | Source identity |
| Workflow Run ID | CI execution identity |
| Image digest | Exact artifact |
| Version | Human-readable release |
| Build timestamp | Auditability |
| SBOM | Dependency inventory |
| Provenance | Build origin |
| Security results | Release evidence |
| Environment | Deployment target |
| Previous artifact | Rollback |

This metadata becomes valuable during incidents.

---

## Artifact Registry Architecture

For AWS:

```text
GitHub Actions
      ↓
OIDC
      ↓
AWS STS
      ↓
IAM Role
      ↓
ECR
      ↓
ECS / EC2 / EKS / Lambda
```

The registry becomes the controlled handoff point between CI and CD.

---

## AWS OIDC Architecture

GitHub Actions should use short-lived credentials rather than long-lived AWS access keys where appropriate.

```mermaid
sequenceDiagram
    participant G as GitHub Actions
    participant O as GitHub OIDC
    participant S as AWS STS
    participant I as IAM
    participant E as ECR

    G->>O: Request OIDC token
    O-->>G: Identity token
    G->>S: AssumeRoleWithWebIdentity
    S->>I: Evaluate trust policy
    I-->>S: Allow / Deny
    S-->>G: Temporary credentials
    G->>E: Push image
```

A deployment job typically requires:

```yaml
permissions:
  contents: read
  id-token: write
```

The IAM trust policy should restrict the permitted GitHub identity.

---

## AWS Account Separation

Production environments can use separate accounts:

```text
GitHub
  ├── Dev Role → Dev Account
  ├── Staging Role → Staging Account
  └── Production Role → Production Account
```

This reduces the blast radius of compromised credentials.

A production role should not automatically have access to unrelated development resources.

---

## Production Environment Architecture

A common promotion model is:

```text
CI
 ↓
Staging
 ↓
Automated Validation
 ↓
Production Approval
 ↓
Production
```

GitHub Environments can provide:

- Environment-specific secrets.
- Environment-specific variables.
- Required reviewers.
- Branch restrictions.
- Deployment history.
- Deployment protection.

---

## Deployment Approval Architecture

Approval should occur after useful evidence is available.

```text
Build
 ↓
Security
 ↓
Staging
 ↓
Health Checks
 ↓
Approval
 ↓
Production
```

Approving a deployment before staging validation reduces the evidence available to reviewers.

---

## Deployment Concurrency

Production deployments should normally be serialized.

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Without concurrency:

```text
Deployment A ───────────→ Production
Deployment B ───────→ Production
```

Deployment ordering becomes timing-dependent.

With concurrency:

```text
Deployment A ───────────→ Production
                              ↓
                         Deployment B
```

---

## CI Concurrency

Pull requests often benefit from cancellation:

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

If a developer pushes three commits quickly, obsolete CI runs can be cancelled.

This is usually different from production deployment concurrency.

---

## Environment Promotion Architecture

```mermaid
flowchart LR
    ART[Immutable Artifact] --> DEV[Development]
    DEV --> TEST[Test]
    TEST --> STG[Staging]
    STG --> CHECK[Validation]
    CHECK --> APPROVAL[Approval]
    APPROVAL --> PROD[Production]
```

Not every organization requires every environment.

The important property is that each promotion boundary has explicit ownership and validation.

---

## Deployment Strategies

Production deployment strategy should match system requirements.

| Strategy | Main property | Main concern |
|---|---|---|
| Rolling | Incremental replacement | Multiple versions coexist |
| Blue/Green | Separate environments | Higher infrastructure cost |
| Canary | Gradual traffic | Requires strong observability |
| Zero Downtime | No planned service interruption | Requires application/runtime coordination |

---

## Rolling Deployment

```text
v1 v1 v1 v1
 ↓
v2 v1 v1 v1
 ↓
v2 v2 v1 v1
 ↓
v2 v2 v2 v1
 ↓
v2 v2 v2 v2
```

Requirements include:

- Readiness checks.
- Graceful shutdown.
- Connection draining.
- Backward-compatible APIs.
- Database compatibility.

---

## Blue/Green Deployment

```text
                ┌── Blue v1
Traffic ────────┤
                └── Green v2
```

Deployment:

```text
Deploy Green
    ↓
Validate Green
    ↓
Switch Traffic
    ↓
Blue Becomes Standby
```

Rollback can switch traffic back to Blue.

Advantages:

- Fast traffic switching.
- Clear version separation.
- Simple application rollback.

Limitations:

- Higher infrastructure cost.
- Database compatibility is still required.
- External side effects may already have occurred.

---

## Canary Deployment

```text
                ┌── 95% Stable
Traffic ────────┤
                └── 5% Canary
```

Promotion can progress:

```text
95/5
 ↓
75/25
 ↓
50/50
 ↓
0/100
```

Promotion criteria should be explicit.

Examples:

- Error rate.
- Latency.
- Saturation.
- Health checks.
- Business metrics.

---

## Zero-Downtime Architecture

Zero downtime requires more than CI/CD orchestration.

The application, load balancer, database, and connection management must cooperate.

```text
Load Balancer
     ↓
Healthy Instance
     ↓
Graceful Shutdown
     ↓
New Instance
     ↓
Readiness Check
     ↓
Traffic
```

For Django or FastAPI, readiness should represent actual ability to serve traffic rather than merely process existence.

---

## Database Migration Architecture

Rolling deployments can temporarily run two application versions.

Therefore migrations should normally follow expand/contract patterns.

```text
Old Schema
    ↓
Expand Schema
    ↓
Deploy Compatible Code
    ↓
Backfill
    ↓
Switch Application
    ↓
Contract Old Schema
```

This is particularly important for PostgreSQL-backed Django and FastAPI systems.

---

## Django Deployment Architecture

A production Django pipeline may be:

```text
Pull Request
 ↓
Ruff
 ↓
pytest
 ↓
PostgreSQL
 ↓
Redis
 ↓
Celery Tests
 ↓
Docker Build
 ↓
ECR
 ↓
Staging
 ↓
Migration Validation
 ↓
Production
```

Production considerations include:

- Migration compatibility.
- Static assets.
- Gunicorn workers.
- Database connections.
- Redis connectivity.
- Celery worker compatibility.
- Health checks.

---

## FastAPI Deployment Architecture

A FastAPI pipeline may be:

```text
Pull Request
 ↓
Lint
 ↓
Type Checks
 ↓
pytest
 ↓
PostgreSQL / Redis
 ↓
Docker Build
 ↓
ECR
 ↓
ECS / Kubernetes / EC2
```

For gRPC systems, include contract validation and integration tests.

---

## Celery Deployment Architecture

Celery introduces asynchronous compatibility.

```text
Application
    ↓
Broker
    ↓
Celery Workers
    ↓
Database / External APIs
```

During deployment:

- Old workers may process messages produced by new code.
- New workers may process messages produced by old code.
- Long-running tasks may outlive the deployment.
- Retries can execute after the original deployment has changed.

Task payloads and task behavior should therefore remain compatible during the transition period.

---

## Kafka Deployment Architecture

Kafka introduces another compatibility boundary.

```text
Producer
    ↓
Kafka
    ↓
Consumer
```

Deployment architecture should consider:

- Event schema compatibility.
- Consumer compatibility.
- Producer compatibility.
- Consumer lag.
- Replay behavior.
- Rollback semantics.

Rolling back application code does not undo already-published events.

---

## API Compatibility

Production CI/CD should validate service contracts where required.

REST systems:

```text
Client
  ↓
REST API
```

gRPC systems:

```text
Client
  ↓
Protocol Buffer Contract
  ↓
gRPC Service
```

Microservices should avoid deploying incompatible producer and consumer contracts simultaneously.

---

## Infrastructure as Code Architecture

Application deployment and infrastructure management should remain logically separate.

```text
Terraform / CloudFormation
        ↓
Infrastructure

GitHub Actions
        ↓
Application Artifact
```

They can be orchestrated by the same release process, but their state and responsibilities should remain clear.

---

## Terraform Deployment Architecture

A typical production flow is:

```text
Pull Request
 ↓
terraform fmt
 ↓
terraform validate
 ↓
terraform plan
 ↓
Review
 ↓
Apply
```

Production Terraform should use controlled state storage and locking.

The deployment identity should use short-lived credentials where practical.

---

## CloudFormation Deployment Architecture

A production flow can be:

```text
Template
 ↓
Validation
 ↓
Change Set
 ↓
Review
 ↓
Execute
 ↓
Monitor
```

Change sets make infrastructure changes visible before execution.

---

## Lambda Deployment Architecture

Lambda deployments can use the same artifact-promotion principles:

```text
Source
 ↓
Build
 ↓
Artifact
 ↓
Validation
 ↓
Lambda Version
 ↓
Alias
 ↓
Production
```

Aliases can help separate deployment identity from the underlying version.

---

## EC2 Deployment Architecture

A controlled EC2 deployment may use:

```text
GitHub Actions
      ↓
Build Artifact
      ↓
S3 / Registry
      ↓
SSM / Deployment Mechanism
      ↓
EC2
      ↓
Health Check
```

Avoid making SSH access the only recovery mechanism for production deployments.

---

## ECS Deployment Architecture

A typical ECS architecture is:

```text
GitHub Actions
      ↓
ECR
      ↓
Task Definition
      ↓
ECS Service
      ↓
ALB
      ↓
Django / FastAPI
      ↓
PostgreSQL / Redis
```

Separate:

- ECS task execution role.
- Application task role.
- Deployment role.

They have different trust and permission requirements.

---

## Kubernetes Deployment Architecture

A Kubernetes-oriented architecture may be:

```text
GitHub Actions
      ↓
Registry
      ↓
Immutable Image
      ↓
Deployment Manifest / Helm
      ↓
Kubernetes
      ↓
Service
      ↓
Ingress
```

The deployment system should use immutable image references rather than mutable tags where practical.

---

## Reusable Workflow Architecture

A platform team can provide standardized CI:

```text
Application Repository
       │
       ├── Orders
       ├── Payments
       └── Users
              │
              ↓
     Reusable Python CI
              │
       ┌──────┼──────┐
       ↓      ↓      ↓
      Lint   Test   Security
```

Deployment workflows can be separated:

```text
Application Repository
       ↓
Reusable Deployment Workflow
       ↓
Environment
```

A reusable workflow can orchestrate multiple jobs.

A composite action packages reusable steps within a job.

---

## Custom Action Architecture

Use composite actions when the abstraction is step-level.

```text
Job
 ├── Setup
 ├── Composite Action
 │    ├── Step A
 │    ├── Step B
 │    └── Step C
 └── Test
```

Use reusable workflows when the abstraction is pipeline-level:

```text
Workflow
 ├── Job A
 ├── Job B
 ├── Job C
 └── Deployment
```

Choosing the wrong abstraction increases maintenance complexity.

---

## Security Architecture

Security should be applied across the entire pipeline.

```text
Source
 ↓
Workflow
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
Production
```

Every boundary can introduce risk.

---

## GITHUB_TOKEN Permissions

Use least privilege.

Example CI job:

```yaml
permissions:
  contents: read
```

Deployment job:

```yaml
permissions:
  contents: read
  id-token: write
```

Do not grant write permissions globally when only one job needs them.

---

## Job-Level Security Boundaries

A strong architecture separates:

```text
Test Jobs
    ↓
Read-only permissions

Deployment Job
    ↓
OIDC + Deployment permissions
```

A compromised test step should not automatically obtain production deployment privileges.

---

## Pull Request Security

For untrusted pull requests:

```text
Fork PR
  ↓
Read-only validation
  ↓
No production secrets
  ↓
No deployment credentials
```

Be especially careful with `pull_request_target`.

It runs with the context and permissions of the target repository, which creates a dangerous boundary if untrusted code is executed with elevated privileges.

---

## Shell Injection Boundary

Avoid directly embedding untrusted GitHub data into shell commands.

Risky pattern:

```yaml
run: echo "PR title: ${{ github.event.pull_request.title }}"
```

Prefer passing data through an environment variable:

```yaml
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: |
  printf '%s\n' "$PR_TITLE"
```

The same principle applies to:

- Branch names.
- Commit messages.
- Issue content.
- Workflow inputs.
- External API responses.

---

## Third-Party Action Security

Treat actions as dependencies.

Production controls should include:

- Trusted action sources.
- SHA pinning where required.
- Least-privilege permissions.
- Dependency review.
- Action inventory.
- Version governance.
- Regular updates.
- Incident response procedures.

A third-party action executes with the permissions available to its job.

---

## Runner Security

GitHub-hosted runners provide strong isolation characteristics for many CI workloads.

Self-hosted runners require additional controls.

Risk factors include:

- Persistent filesystem state.
- Docker socket access.
- Private network access.
- Long-lived credentials.
- Cached credentials.
- Installed software.
- Cross-job contamination.

Ephemeral runners can reduce persistent-state risk.

---

## Private Network Architecture

A self-hosted runner can provide access to private resources:

```text
GitHub Actions
      ↓
Private Runner
      ↓
VPC
 ├── PostgreSQL
 ├── Redis
 ├── Internal REST APIs
 └── gRPC Services
```

Controls should include:

- Runner groups.
- Network segmentation.
- Security groups.
- IAM.
- Egress controls.
- Ephemeral lifecycle.
- Restricted workflow access.

---

## Supply-Chain Architecture

A mature pipeline can provide:

```text
Source
 ↓
Dependency Validation
 ↓
Trusted Workflow
 ↓
Trusted Runner
 ↓
Build
 ↓
SBOM
 ↓
Provenance
 ↓
Attestation / Signing
 ↓
Registry
 ↓
Deployment
```

This provides evidence about how an artifact was created and what it contains.

---

## SBOM and Provenance

An SBOM describes dependencies.

Provenance describes build origin and process.

They answer different questions:

```text
SBOM:
"What is inside this artifact?"

Provenance:
"How and where was this artifact produced?"
```

Both can support production incident response and vulnerability management.

---

## Artifact Signing

A production deployment can require:

```text
Artifact
   ↓
Signature / Attestation
   ↓
Verification
   ↓
Deployment
```

This creates a stronger trust boundary between build and deployment.

---

## Monitoring Architecture

Deployment success should not be defined only by an exit code.

Use:

```text
Deployment
    ↓
Process Health
    ↓
Readiness
    ↓
HTTP / gRPC Health
    ↓
Error Rate
    ↓
Latency
    ↓
Resource Utilization
    ↓
Business Metrics
```

For production systems, CI/CD and runtime observability must work together.

---

## Deployment Metadata

A deployment should record:

```text
Application
Version
Commit SHA
Artifact Digest
Environment
Workflow
Run ID
Deployment Time
Operator / Actor
Previous Version
Deployment Strategy
Result
```

This allows operators to correlate deployment events with application incidents.

---

## Health Validation

A deployment should have explicit validation criteria.

Example:

```text
Deploy
 ↓
Wait for readiness
 ↓
HTTP health check
 ↓
Error rate check
 ↓
Latency check
 ↓
Dependency check
 ↓
Promotion
```

Health checks should be meaningful.

A process that is running but cannot connect to PostgreSQL may not be ready to receive production traffic.

---

## Automated Rollback

A controlled deployment can implement:

```text
Deploy
 ↓
Health Validation
 ↓
Healthy?
 ├── Yes → Continue
 └── No  → Rollback
```

Rollback criteria should be bounded and measurable.

Do not create automatic rollback loops where:

```text
Deploy → Fail → Rollback → Retry → Fail → Rollback
```

continues indefinitely.

---

## Artifact-Based Rollback

The safest rollback target is usually a previously validated artifact.

```text
Production
    ↓
Bad Artifact
    ↓
Select Previous Artifact
    ↓
Deploy
    ↓
Validate
```

Avoid rebuilding old source during an incident when the original production artifact is available.

---

## Database Rollback

Application rollback does not necessarily mean database rollback.

A deployment can be:

```text
Application rollback
+
Forward-compatible database schema
```

This is often safer than attempting destructive database rollback during an incident.

Use expand/contract migrations for compatibility.

---

## Feature Flag Rollback

Feature flags can provide a fast behavioral rollback:

```text
Production Artifact
       ↓
Feature Flag
   ┌───┴───┐
  OFF      ON
   ↓        ↓
Old       New
Behavior  Behavior
```

Feature flags complement artifact rollback; they do not replace it.

---

## Disaster Recovery

CI/CD recovery should preserve the ability to reconstruct deployment state.

Important dependencies include:

```text
Source Repository
Workflows
Reusable Workflows
Infrastructure as Code
Artifact Registry
Deployment Metadata
Secrets / Identity Configuration
Rollback Artifacts
```

A recovery plan should not depend on an engineer remembering undocumented manual steps.

---

## High Availability

CI/CD availability depends on multiple layers.

```text
GitHub
 ↓
Runner Capacity
 ↓
Artifact Registry
 ↓
Cloud APIs
 ↓
Deployment Platform
 ↓
Production Infrastructure
```

For self-hosted infrastructure:

- Avoid a single runner.
- Use multiple capacity units.
- Monitor runner health.
- Replace unhealthy runners.
- Use autoscaling where appropriate.
- Maintain recovery procedures.

---

## Runner Autoscaling

A scalable runner architecture is:

```text
Workflow Queue
      ↓
Autoscaler
      ↓
Runner Provisioning
      ↓
Ephemeral Runner
      ↓
Job
      ↓
Runner Destruction
```

Scaling should consider:

- Queue depth.
- Job duration.
- Provisioning time.
- CPU/memory requirements.
- Network capacity.
- Cloud quotas.
- Burst behavior.

---

## Cost Architecture

CI/CD cost is influenced by:

```text
Workflow Frequency
×
Execution Duration
×
Runner Cost
×
Matrix Cardinality
```

Optimize with:

- Parallel execution.
- Dependency caching.
- Docker layer caching.
- Targeted testing.
- PR concurrency cancellation.
- Dynamic matrices.
- Appropriate runner sizing.
- Reusable workflows.

Do not remove important validation solely to reduce CI minutes.

---

## Reliability Architecture

A reliable pipeline should be:

- Deterministic.
- Observable.
- Idempotent.
- Retry-aware.
- Timeout-aware.
- Recoverable.
- Secure.
- Versioned.

Transient failures may justify retries.

Deterministic failures should fail quickly.

---

## Failure Domains

Organize troubleshooting around boundaries.

```text
Workflow
  ↓
Trigger
  ↓
Job
  ↓
Step
  ↓
Runner
  ↓
Dependency
  ↓
Artifact
  ↓
Registry
  ↓
Deployment
  ↓
Runtime
```

This prevents debugging from becoming random experimentation.

---

## Production Troubleshooting Model

Use:

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

Example: AWS authentication failure.

```text
Symptom
→ AccessDenied

Possible Causes
→ Wrong IAM role
→ OIDC permission missing
→ Trust policy mismatch
→ Incorrect repository/environment claim

Isolation
→ Inspect workflow permissions
→ Inspect AWS identity
→ Inspect IAM trust policy

Command
→ aws sts get-caller-identity

Corrective Action
→ Fix identity/trust/permissions

Prevention
→ Least privilege + automated validation
```

---

## GitHub Actions Diagnostics

List workflows:

```bash
gh workflow list
```

Run a workflow:

```bash
gh workflow run ci.yml
```

List runs:

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

Rerun:

```bash
gh run rerun <run-id>
```

Download artifacts:

```bash
gh run download <run-id>
```

These commands are useful during CI/CD operations and incident response.

---

## AWS Diagnostics

Verify identity:

```bash
aws sts get-caller-identity
```

Inspect ECR images:

```bash
aws ecr describe-images \
  --repository-name orders-api
```

Inspect ECS service:

```bash
aws ecs describe-services \
  --cluster production \
  --services orders-api
```

The first question for an AWS authentication problem should often be:

```text
Which identity is actually executing this command?
```

---

## Docker Diagnostics

Inspect an image:

```bash
docker image inspect orders-api:local
```

Inspect Buildx:

```bash
docker buildx ls
```

Build locally:

```bash
docker buildx build \
  --tag orders-api:local \
  .
```

Investigate Docker failures in this order:

```text
Build Context
 ↓
Dockerfile
 ↓
Base Image
 ↓
Dependencies
 ↓
Build Cache
 ↓
Image Creation
 ↓
Registry Push
```

---

## Common Production Architecture Failures

### Rebuilding for Every Environment

Problem:

```text
Build → Staging
Build → Production
```

Risk:

The two artifacts may differ.

Use:

```text
Build once → Promote
```

### Mutable Production Tags

Problem:

```text
production:latest
```

Risk:

The same name can point to different content.

Use commit identity and retain the digest.

### Shared Deployment Credentials

Problem:

```text
All Jobs → Production Role
```

Risk:

A compromised test job can potentially deploy.

Use job-level permissions and isolated deployment credentials.

### Persistent Privileged Runner

Problem:

```text
Untrusted Job
 ↓
Persistent Runner
 ↓
Production Network
```

Risk:

Persistent state can survive between jobs.

Prefer ephemeral runners for sensitive workloads where practical.

### Serializing Everything

Problem:

```text
Lint
 ↓
Unit
 ↓
Security
 ↓
Integration
```

Risk:

Unnecessary latency.

Parallelize independent jobs.

### Excessive Matrix Dimensions

Problem:

```text
Python × DB × OS × Browser × Service
```

Risk:

Cost and execution time grow rapidly.

Use different matrix sizes for PR, nightly, and release validation.

---

## Enterprise Governance Architecture

A large organization may introduce a platform layer:

```mermaid
flowchart TB
    ENT[Enterprise Policies]
    ORG[Organization Governance]
    PLATFORM[CI/CD Platform Team]

    ENT --> ORG
    ORG --> PLATFORM

    PLATFORM --> RW[Reusable Workflows]
    PLATFORM --> ACTIONS[Approved Actions]
    PLATFORM --> RUNNERS[Runner Groups]
    PLATFORM --> SECURITY[Security Standards]
    PLATFORM --> OBS[Observability]

    RW --> APP1[Application A]
    RW --> APP2[Application B]
    RW --> APP3[Application C]
```

Governance should standardize high-risk areas without forcing every application into an identical deployment model.

---

## Action Governance

Enterprise environments may define:

- Approved action sources.
- SHA pinning requirements.
- Marketplace restrictions.
- Internal action registries.
- Review requirements.
- Deprecation policies.
- Dependency update procedures.

An action allowlist reduces supply-chain exposure.

---

## Runner Governance

Runner governance should define:

- Ownership.
- Registration scope.
- Runner groups.
- Labels.
- Network access.
- Patch policy.
- Image lifecycle.
- Ephemeral/persistent policy.
- Capacity.
- Monitoring.
- Retirement.

A runner should not exist indefinitely without an owner.

---

## Secret Governance

Secrets should be:

- Scoped.
- Rotated.
- Audited.
- Avoided when OIDC can replace static credentials.
- Restricted to jobs that require them.

Use environment protection for production secrets.

---

## Workflow Governance

Governance should cover:

```text
Workflow Standards
    ↓
Permissions
    ↓
Actions
    ↓
Secrets
    ↓
Runners
    ↓
Environments
    ↓
Deployments
```

Required workflows can standardize organization-wide security or compliance checks.

---

## Production Pipeline Example

A realistic backend pipeline can be structured as:

```text
Pull Request
     ↓
Change Detection
     ↓
┌────────────┬─────────────┬──────────────┐
│ Ruff       │ Unit Tests  │ Security     │
└────────────┴─────────────┴──────────────┘
                  ↓
        Integration Tests
                  ↓
      PostgreSQL + Redis
                  ↓
        Compatibility Matrix
                  ↓
             Buildx
                  ↓
       Docker Image + SBOM
                  ↓
              ECR
                  ↓
             Staging
                  ↓
         Health Validation
                  ↓
             Approval
                  ↓
            Production
                  ↓
            Monitoring
                  ↓
        Rollback if needed
```

---

## Production Workflow Example

```yaml
name: Production Deployment

on:
  workflow_dispatch:
    inputs:
      image_digest:
        description: "Immutable image digest"
        required: true
        type: string

concurrency:
  group: production
  cancel-in-progress: false

permissions:
  contents: read
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.PRODUCTION_DEPLOY_ROLE }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Deploy immutable artifact
        env:
          IMAGE_DIGEST: ${{ inputs.image_digest }}
        run: |
          ./scripts/deploy.sh "$IMAGE_DIGEST"

      - name: Validate deployment
        run: |
          ./scripts/health-check.sh
```

The important properties are:

- Explicit production environment.
- Deployment concurrency.
- OIDC instead of long-lived AWS credentials.
- Immutable artifact input.
- Health validation.

---

## Deployment State Model

A deployment can be represented as:

```text
Candidate
   ↓
Built
   ↓
Scanned
   ↓
Registered
   ↓
Staging
   ↓
Validated
   ↓
Approved
   ↓
Deploying
   ↓
Healthy
```

Failure transitions should be explicit:

```text
Deploying
   ↓
Unhealthy
   ↓
Rollback
   ↓
Known-Good
```

This state-oriented approach makes deployment behavior easier to reason about.

---

## Production Incident Architecture

During an incident:

```text
Alert
 ↓
Identify Deployment
 ↓
Identify Artifact
 ↓
Inspect Runtime Metrics
 ↓
Compare Previous Version
 ↓
Determine Failure Domain
 ↓
Rollback or Mitigate
 ↓
Validate
 ↓
Monitor
 ↓
Post-Incident Analysis
```

The deployment system should provide enough metadata to make these steps possible without reconstructing history manually.

---

## Recovery Architecture

A recovery plan should identify:

```text
Source
Artifact
Infrastructure
Configuration
Credentials / Identity
Database
External Dependencies
Monitoring
Rollback Target
```

For a severe production failure:

```text
Known-Good Artifact
        +
Known-Good Infrastructure
        +
Known-Compatible Database
        ↓
Recovery
```

CI/CD is part of the application's recovery architecture.

---

## Production Readiness Checklist

### Workflow

- [ ] Triggers are intentional.
- [ ] Jobs have clear responsibilities.
- [ ] Independent jobs run in parallel.
- [ ] Dependencies use `needs`.
- [ ] Workflow reuse is appropriate.

### Testing

- [ ] Unit tests are deterministic.
- [ ] Integration services have readiness checks.
- [ ] Matrix dimensions are justified.
- [ ] Test reports are retained.
- [ ] Full compatibility testing exists where required.

### Build

- [ ] Build is reproducible.
- [ ] Docker Buildx is used where appropriate.
- [ ] Layer caching is configured.
- [ ] Images have immutable identity.
- [ ] Security scanning is integrated.

### Artifacts

- [ ] Artifacts are immutable.
- [ ] Digests are recorded.
- [ ] SBOM/provenance is available where required.
- [ ] Previous artifacts are retained for rollback.
- [ ] Production does not rebuild the artifact.

### Security

- [ ] `GITHUB_TOKEN` permissions are minimal.
- [ ] Secrets are scoped.
- [ ] OIDC is used for AWS where appropriate.
- [ ] Third-party actions are governed.
- [ ] Untrusted code cannot access production credentials.
- [ ] Sensitive workloads use appropriate runner isolation.

### Deployment

- [ ] Staging validation exists.
- [ ] Production approval is protected.
- [ ] Deployment concurrency is controlled.
- [ ] Health checks are meaningful.
- [ ] Rollback is documented and tested.
- [ ] Database migrations support the deployment strategy.

### Operations

- [ ] Runner health is monitored.
- [ ] Workflow logs are available.
- [ ] Deployment metadata is retained.
- [ ] Artifact retention supports rollback.
- [ ] Failure domains are documented.
- [ ] Disaster recovery procedures exist.

---

## Senior Architecture Questions

### How would you design CI/CD for 50 Python microservices?

Consider:

- Reusable workflows.
- Internal actions.
- Monorepo vs multirepo implications.
- Dynamic change detection.
- Matrix testing.
- Shared security controls.
- Independent artifact identities.
- Environment ownership.
- Runner capacity.
- Governance.

### How would you prevent two production deployments from running simultaneously?

Consider:

```text
GitHub concurrency
+
Environment protection
+
Idempotent deployment
+
Artifact identity
```

### How would you avoid rebuilding an image for production?

Use:

```text
Build
→ Push
→ Digest
→ Staging
→ Approval
→ Production
```

### How would you authenticate GitHub Actions to AWS securely?

Use:

```text
OIDC
→ STS
→ IAM Role
→ Temporary Credentials
```

with a restrictive trust policy and minimal permissions.

### How would you support PostgreSQL and Redis integration tests?

Use:

```text
CI Runner
 ├── Application
 ├── PostgreSQL
 └── Redis
        ↓
      pytest
```

and ensure readiness before tests begin.

### How would you roll back a failed deployment?

Use the previous known-good artifact rather than rebuilding source during the incident.

### How would you protect a self-hosted runner?

Consider:

- Ephemeral lifecycle.
- Runner groups.
- Network segmentation.
- Least privilege.
- Image hardening.
- Cleanup.
- Monitoring.
- Restricted workflow access.

### How would you design canary deployment?

Define:

```text
Traffic Allocation
+
Health Criteria
+
Promotion Gates
+
Observability
+
Rollback
```

before automating traffic progression.

---

## Senior Design Principles

### Separate Build From Promotion

CI should prove that an artifact is valid.

CD should determine where and when that artifact runs.

### Treat Artifacts as Immutable

A deployment should reference an exact artifact, preferably by digest.

### Minimize Privilege at Every Boundary

Permissions should follow the job's responsibility.

### Design for Failure

Assume:

- Tests fail.
- Runners disappear.
- Registries become unavailable.
- AWS authentication fails.
- Deployments partially succeed.
- Health checks fail.
- Database migrations cause problems.

### Make Recovery a First-Class Workflow

Rollback should not be an undocumented collection of emergency commands.

### Keep Production Observable

Every deployment should produce enough metadata to correlate:

```text
Code
→ Artifact
→ Deployment
→ Runtime
→ Incident
```

### Keep Platform and Application Responsibilities Separate

Platform engineering should provide secure reusable primitives.

Application teams should retain ownership of application-specific behavior and validation.

---

## Key Takeaways

- A production CI/CD architecture separates **validation, build, artifact storage, environment promotion, deployment, monitoring, and recovery** into explicit boundaries.
- The most important deployment invariant is **build once, create an immutable artifact, and promote the same artifact** through staging and production.
- Production safety depends on least-privilege permissions, OIDC-based AWS authentication, protected environments, controlled concurrency, secure runners, and supply-chain controls.
- Deployment strategies such as rolling, blue/green, canary, and zero-downtime deployments must be designed together with health checks, database compatibility, observability, and rollback.
- Senior CI/CD architecture is primarily about **failure isolation, reproducibility, operational visibility, scalability, security, and recovery**, not simply writing workflow YAML.