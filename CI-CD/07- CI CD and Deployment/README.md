# README

## Overview

This directory contains the **CI/CD and Deployment** section of the Backend Engineering Playbook.

The material is designed to take a backend engineer from GitHub Actions fundamentals through production-grade CI/CD architecture, release management, Docker-based delivery, AWS deployment, environment promotion, deployment strategies, rollback, and operational recovery.

The focus is not on YAML syntax alone. The objective is to understand how a CI/CD system behaves as a production engineering platform:

```text
Source Code
    ↓
Pull Request
    ↓
Validation
    ↓
Test
    ↓
Security
    ↓
Build
    ↓
Immutable Artifact
    ↓
Release
    ↓
Environment Promotion
    ↓
Deployment
    ↓
Monitoring
    ↓
Rollback / Recovery
```

The examples and architecture patterns are primarily relevant to:

- Python
- Django
- FastAPI
- REST APIs
- gRPC services
- Microservices
- Docker
- Kubernetes
- PostgreSQL
- MySQL
- Redis
- Kafka
- Celery
- Nginx
- AWS
- GitHub Actions

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- CI Pipeline Architecture](./01-%20CI%20Pipeline%20Architecture.md) | GitHub Actions is a CI/CD execution platform built around declarative workflows. |
| 02 | [02- CD Pipeline Architecture](./02-%20CD%20Pipeline%20Architecture.md) | Continuous Delivery and Continuous Deployment extend CI beyond validation into the controlled delivery of software to runtime environments. |
| 03 | [03- Build Once Deploy Many](./03-%20Build%20Once%20Deploy%20Many.md) | Build Once Deploy Many is a CI/CD architecture in which a deployable artifact is built exactly once and then promoted unchanged across environments. |
| 04 | [04- Artifact Promotion](./04-%20Artifact%20Promotion.md) | Artifact promotion is the process of moving a previously built and validated artifact through deployment environments without rebuilding it. |
| 05 | [05- Environment Promotion](./05-%20Environment%20Promotion.md) | Environment promotion is the controlled movement of a validated application release from one deployment environment to another. |
| 06 | [06- Deployment Approvals](./06-%20Deployment%20Approvals.md) | Deployment approval is a controlled decision point between a validated release and deployment into a protected environment. |
| 07 | [07- Deployment Protection Rules](./07-%20Deployment%20Protection%20Rules.md) | Deployment protection rules define the conditions that must be satisfied before a deployment can proceed into a protected environment. |
| 08 | [08- Deployment Concurrency](./08-%20Deployment%20Concurrency.md) | Deployment concurrency controls how multiple CI/CD workflow runs interact when they attempt to deploy the same environment or modify the sam... |
| 09 | [09- Docker Image Build and Publishing](./09-%20Docker%20Image%20Build%20and%20Publishing.md) | Docker image build and publishing is the CI/CD stage where application source code is transformed into an immutable container image and publ... |
| 10 | [10- Docker Buildx](./10-%20Docker%20Buildx.md) | Docker Buildx is the modern Docker build interface built on BuildKit. |
| 11 | [11- Docker Layer Caching](./11-%20Docker%20Layer%20Caching.md) | Docker layer caching is one of the most important techniques for reducing container build time and CI/CD cost. |
| 12 | [12- Amazon ECR Deployment](./12-%20Amazon%20ECR%20Deployment.md) | Amazon Elastic Container Registry (ECR) is AWS's managed container image registry. |
| 13 | [13- Amazon S3 Deployment](./13-%20Amazon%20S3%20Deployment.md) | Amazon S3 is an object storage service commonly used in CI/CD pipelines for storing and distributing deployment artifacts, static assets, fr... |
| 14 | [14- Amazon ECS Deployment](./14-%20Amazon%20ECS%20Deployment.md) | Amazon Elastic Container Service (ECS) is an AWS container orchestration service used to run Docker containers without requiring Kubernetes... |
| 15 | [15- Amazon EC2 Deployment](./15-%20Amazon%20EC2%20Deployment.md) | Amazon Elastic Compute Cloud (EC2) provides virtual machines that can run application workloads with direct control over the operating syste... |
| 16 | [16- AWS Lambda Deployment](./16-%20AWS%20Lambda%20Deployment.md) | AWS Lambda is a serverless compute service that executes application code in response to events without requiring the engineering team to ma... |
| 17 | [17- CloudFormation Deployment](./17-%20CloudFormation%20Deployment.md) | AWS CloudFormation is an infrastructure-as-code service for defining and managing AWS resources through declarative templates. |
| 18 | [18- Terraform Deployment](./18-%20Terraform%20Deployment.md) | Terraform is an infrastructure-as-code tool that allows infrastructure to be defined, reviewed, provisioned, and changed through version-con... |
| 19 | [19- OIDC Based AWS Deployment](./19-%20OIDC%20Based%20AWS%20Deployment.md) | OpenID Connect (OIDC) allows GitHub Actions to authenticate to AWS without storing long-lived AWS access keys in GitHub secrets. |
| 20 | [20- Blue Green Deployment](./20-%20Blue%20Green%20Deployment.md) | Blue-green deployment is a release strategy that maintains two production-capable environments: |
| 21 | [21- Canary Deployment](./21-%20Canary%20Deployment.md) | Canary deployment is a release strategy that introduces a new application version to a small, controlled portion of production traffic befor... |
| 22 | [22- Rolling Deployment](./22-%20Rolling%20Deployment.md) | A rolling deployment replaces instances of an existing application version with a new version incrementally instead of replacing the entire... |
| 23 | [23- Zero Downtime Deployment](./23-%20Zero%20Downtime%20Deployment.md) | Zero downtime deployment is a deployment approach designed to keep an application available to users while a new version is released. |
| 24 | [24- Rollback Strategies](./24-%20Rollback%20Strategies.md) | Rollback is the controlled process of returning a production system to a previously known-good application version or operational state afte... |
| 25 | [25- Release Automation](./25-%20Release%20Automation.md) | Release automation is the process of turning a validated code change into a controlled, traceable, and repeatable software release. |
| 26 | [26- Semantic Versioning and Releases](./26-%20Semantic%20Versioning%20and%20Releases.md) | Semantic Versioning (SemVer) provides a predictable versioning convention for software releases: |

---

## What This Section Covers

This section treats CI/CD as a complete engineering system rather than a collection of GitHub Actions workflows.

The material covers:

| Area | Focus |
|---|---|
| Workflow Design | Jobs, steps, dependencies, triggers, expressions |
| Reusable Automation | Reusable workflows and custom actions |
| Testing | Unit, integration, E2E, matrices, reports |
| Security | Permissions, secrets, OIDC, supply chain |
| Containers | Docker builds, caching, registries |
| Releases | Versioning, tags, release automation |
| Deployment | AWS, ECS, EC2, infrastructure |
| Promotion | Staging and production environments |
| Deployment Strategies | Rolling, blue/green, canary |
| Reliability | Zero downtime, concurrency, rollback |
| Operations | Runners, monitoring, troubleshooting |
| Architecture | Production and enterprise CI/CD design |
| CLI | GitHub Actions operational workflows |
| Interview Preparation | Senior-level design and troubleshooting |

---

## Learning Flow

The recommended progression is:

```text
GitHub Actions Fundamentals
        ↓
Workflow Configuration
        ↓
Advanced Workflow Design
        ↓
Custom Actions
        ↓
Containers and Testing
        ↓
Security
        ↓
CI/CD Architecture
        ↓
Docker and Artifact Delivery
        ↓
AWS Deployment
        ↓
Release Management
        ↓
Deployment Strategies
        ↓
Rollback and Recovery
        ↓
Runners and Operations
        ↓
Troubleshooting
        ↓
Architecture
        ↓
CLI
        ↓
Senior-Level Interview Preparation
```

This progression is intentional.

Understanding deployment strategies without understanding artifact identity, concurrency, environments, security, and rollback leads to incomplete production designs.

---

## Core CI/CD Architecture

A production pipeline should generally separate validation, artifact creation, promotion, and deployment.

```mermaid
flowchart LR
    PR[Pull Request] --> LINT[Lint]
    LINT --> UNIT[Unit Tests]
    UNIT --> INT[Integration Tests]
    INT --> SEC[Security Scan]
    SEC --> MATRIX[Matrix Validation]

    MATRIX --> BUILD[Build]
    BUILD --> IMAGE[Docker Image]
    IMAGE --> ECR[ECR / Registry]

    ECR --> STAGE[Staging]
    STAGE --> SMOKE[Smoke Tests]
    SMOKE --> APPROVAL[Production Approval]
    APPROVAL --> PROD[Production]

    PROD --> MONITOR[Monitoring]
    MONITOR --> ROLLBACK[Rollback]
```

The critical production principle is:

```text
Build Once
    ↓
Produce Immutable Artifact
    ↓
Promote Same Artifact
```

Avoid:

```text
Build Staging
    ↓
Build Production
```

because rebuilding can produce a different artifact from the same source revision.

---

## Repository Navigation

### GitHub Actions Foundations

These documents establish the execution model and fundamental workflow concepts.

| Document | Focus |
|---|---|
| `01- CI Pipeline Architecture.md` | CI architecture, workflow execution, dependency graphs, testing and build flow |
| `02- CD Pipeline Architecture.md` | CD architecture, promotion, deployment, approvals and production flow |
| `03- Build Once Deploy Many.md` | Immutable artifacts and promotion across environments |

---

### Environment and Deployment Control

These documents cover how validated artifacts move through deployment environments.

| Document | Focus |
|---|---|
| `05- Environment Promotion.md` | Environment boundaries, promotion and artifact identity |
| `06- Deployment Approvals.md` | Production approvals and deployment protection |
| `08- Deployment Concurrency.md` | Preventing deployment races and concurrent production changes |

---

### Docker and Artifact Delivery

These documents cover container-based build and delivery pipelines.

| Document | Focus |
|---|---|
| `09- Docker Image Build and Publishing.md` | Docker image construction and registry publishing |
| `11- Docker Layer Caching.md` | BuildKit and Docker layer caching |
| `12- Amazon ECR Deployment.md` | ECR authentication, publishing and artifact promotion |

---

### AWS Deployment

The AWS deployment material connects GitHub Actions to production AWS infrastructure.

| Document | Focus |
|---|---|
| `14- Amazon ECS Deployment.md` | ECS and Fargate/EC2-based container deployment |
| `15- Amazon EC2 Deployment.md` | EC2-based application deployment |
| `17- CloudFormation Deployment.md` | CloudFormation-based infrastructure deployment |
| `18- Terraform Deployment.md` | Terraform-based infrastructure deployment |

The AWS authentication model should generally follow:

```text
GitHub Actions
      ↓
GitHub OIDC
      ↓
AWS STS
      ↓
IAM Role
      ↓
AWS Service
```

Long-lived AWS access keys should not be the default authentication mechanism for GitHub Actions.

---

### Deployment Strategies

These documents cover production traffic and availability strategies.

| Document | Focus |
|---|---|
| `20- Blue Green Deployment.md` | Blue/green deployment architecture |
| `21- Canary Deployment.md` | Progressive traffic rollout |
| `23- Zero Downtime Deployment.md` | Availability-preserving deployment |
| `24- Rollback Strategies.md` | Recovery and rollback strategies |

Deployment strategy should be selected based on:

- Application architecture
- Traffic characteristics
- Stateful dependencies
- Database compatibility
- Rollback requirements
- Infrastructure capabilities
- Operational maturity
- Cost

---

### Release Management

These documents cover how software becomes a versioned release.

| Document | Focus |
|---|---|
| `25- Release Automation.md` | Automated release creation and artifact publication |
| `26- Semantic Versioning and Releases.md` | Semantic versioning and release lifecycle |

A release should establish traceability:

```text
Version
  ↓
Git Tag
  ↓
Commit SHA
  ↓
Workflow Run
  ↓
Artifact
  ↓
Artifact Digest
  ↓
Deployment
```

---

## CI/CD Building Blocks

A production GitHub Actions pipeline is composed of several independent building blocks.

### Workflow

Defines when and how automation executes.

```yaml
name: CI

on:
  pull_request:
  push:
    branches:
      - main
```

### Job

Defines an execution unit on a runner.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
```

### Step

Defines an individual operation inside a job.

```yaml
steps:
  - name: Run tests
    run: pytest
```

### Action

Packages reusable functionality.

```yaml
- uses: actions/checkout@v4
```

### Runner

Provides the execution environment.

```text
Workflow
   ↓
Job
   ↓
Runner
   ↓
Steps
   ↓
Actions / Commands
```

Understanding this hierarchy is essential before designing advanced workflows.

---

## Workflow Configuration

Important GitHub Actions triggers include:

```text
push
pull_request
pull_request_target
workflow_dispatch
schedule
workflow_call
workflow_run
repository_dispatch
release
```

Use triggers according to trust boundaries and operational requirements.

For example:

```yaml
on:
  pull_request:
    branches:
      - main
```

for pull request validation.

Manual operations can use:

```yaml
on:
  workflow_dispatch:
```

Release automation can use:

```yaml
on:
  push:
    tags:
      - "v*.*.*"
```

---

## Expressions and Contexts

GitHub Actions expressions allow workflow decisions to depend on runtime information.

Common contexts include:

```text
github
env
vars
secrets
steps
needs
job
runner
matrix
strategy
inputs
```

Common functions include:

```text
success()
failure()
always()
cancelled()
contains()
startsWith()
endsWith()
format()
fromJSON()
toJSON()
hashFiles()
```

Expressions and shell commands are different execution layers.

For example:

```yaml
if: ${{ github.ref == 'refs/heads/main' }}
```

is evaluated by GitHub Actions.

Whereas:

```yaml
run: echo "$GITHUB_REF"
```

is executed by the runner shell.

This distinction becomes particularly important when handling untrusted input.

---

## Data Flow Between Jobs

A production workflow frequently needs to pass:

```text
Version
Commit SHA
Artifact Name
Image Tag
Image Digest
Changed Services
Deployment Target
```

Use outputs for structured workflow data.

```yaml
jobs:
  build:
    outputs:
      image_digest: ${{ steps.image.outputs.digest }}
```

Then consume it with:

```yaml
needs.build.outputs.image_digest
```

For structured data:

```text
JSON
  ↓
GITHUB_OUTPUT
  ↓
needs
  ↓
fromJSON()
  ↓
Dynamic Matrix
```

---

## Artifacts vs Caches

These are intentionally different mechanisms.

| Artifact | Cache |
|---|---|
| Workflow output | Performance optimization |
| Used for transfer/release/debugging | Used to accelerate repeated work |
| Explicitly retained | Can be recreated |
| Release-oriented | Build-oriented |
| Example: test report | Example: pip cache |
| Example: build package | Example: Docker layer cache |

A production deployment should not depend on a disposable dependency cache.

---

## Matrix Testing

Matrix strategies allow one job definition to execute across multiple configurations.

Example:

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

Backend applications can combine dimensions:

```text
Python
+
Database
+
Operating System
```

But matrix size grows multiplicatively.

If:

```text
3 Python versions
×
2 databases
×
2 operating systems
```

then:

```text
3 × 2 × 2 = 12 jobs
```

Matrix design therefore has direct cost and execution-time implications.

---

## Dynamic Matrices

A planning job can generate JSON:

```json
["orders", "payments", "users"]
```

A downstream job can consume it:

```yaml
strategy:
  matrix:
    service: ${{ fromJSON(needs.plan.outputs.services) }}
```

This is useful for:

- Monorepos
- Selective testing
- Service-specific builds
- Multi-service deployments

---

## Reusable Workflows

Reusable workflows allow organizations to standardize CI/CD logic.

Example:

```yaml
jobs:
  ci:
    uses: company/platform/.github/workflows/python-ci.yml@v2
```

A reusable workflow can orchestrate:

- Multiple jobs
- Testing
- Security
- Building
- Deployment
- Environment promotion

It is different from a composite action.

```text
Reusable Workflow
    ↓
Can orchestrate multiple jobs

Composite Action
    ↓
Packages reusable steps inside one job
```

---

## Custom Actions

GitHub Actions supports three major custom action models:

| Type | Primary Use |
|---|---|
| Composite | Reusable shell/tool steps |
| JavaScript | API and GitHub automation |
| Docker | Containerized action execution |

Use custom actions when repeated step-level behavior needs a stable interface.

Use reusable workflows when the reusable component needs to coordinate multiple jobs.

---

## Containers and Testing

A backend CI pipeline frequently requires infrastructure dependencies.

Example:

```text
Python Application
      ↓
PostgreSQL
      ↓
Redis
      ↓
pytest
      ↓
Coverage
      ↓
Artifacts
```

GitHub Actions service containers can provide isolated dependencies.

Typical services include:

```text
PostgreSQL
MySQL
Redis
```

Readiness is important.

Starting a container does not necessarily mean the service is ready to accept connections.

---

## Django CI Pipeline

A Django pipeline can follow:

```text
Checkout
 ↓
Python Setup
 ↓
Dependency Installation
 ↓
Lint
 ↓
Unit Tests
 ↓
PostgreSQL
 ↓
Redis
 ↓
Migrations
 ↓
Integration Tests
 ↓
Coverage
 ↓
Reports
```

Example:

```yaml
- name: Run tests
  env:
    DJANGO_SETTINGS_MODULE: config.settings.test
    DATABASE_URL: postgres://postgres:postgres@localhost:5432/testdb
    REDIS_URL: redis://localhost:6379/0
  run: |
    python manage.py migrate
    pytest --cov=.
```

---

## FastAPI CI Pipeline

A FastAPI service can follow:

```text
Checkout
 ↓
Dependency Installation
 ↓
Lint
 ↓
pytest
 ↓
Integration Tests
 ↓
Docker Build
 ↓
Security Scan
 ↓
Artifact
```

For services using PostgreSQL, Redis, Kafka, or external APIs, integration testing should provide controlled dependencies rather than relying on production systems.

---

## Security Model

CI/CD is a privileged execution environment.

A workflow may have access to:

```text
Source Code
Secrets
Cloud Credentials
Container Registry
Production Infrastructure
```

The security model should therefore follow:

```text
Least Privilege
+
Strong Trust Boundaries
+
Immutable Artifacts
+
Short-Lived Credentials
+
Controlled Runners
```

---

## GITHUB_TOKEN

The workflow token should receive only the permissions it needs.

Example:

```yaml
permissions:
  contents: read
```

A release workflow may require:

```yaml
permissions:
  contents: write
```

AWS OIDC authentication may require:

```yaml
permissions:
  id-token: write
```

Avoid broad permissions such as:

```yaml
permissions: write-all
```

unless there is a documented requirement.

---

## Secrets

Secrets can exist at different scopes:

```text
Organization
Repository
Environment
```

Production secrets should generally be associated with the production environment rather than made available to every workflow.

Avoid placing secrets directly into command arguments:

```yaml
run: some-command --password "${{ secrets.PASSWORD }}"
```

because command lines may be exposed through diagnostics or process inspection.

Prefer environment variables or purpose-built authentication mechanisms when appropriate.

---

## Untrusted Input

Never assume GitHub metadata is safe to interpolate into shell commands.

Potentially untrusted values include:

- Pull request titles
- Branch names
- Commit messages
- Issue content
- Manual workflow inputs
- External API data

Avoid:

```yaml
run: echo "${{ github.event.pull_request.title }}"
```

when the value is directly inserted into shell source.

Prefer passing the value through an environment variable:

```yaml
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: |
  printf '%s\n' "$PR_TITLE"
```

The same principle applies to Python subprocess calls, Docker arguments, AWS CLI commands, and generated configuration.

---

## `pull_request` vs `pull_request_target`

This distinction is important for security.

```text
pull_request
    ↓
Runs in the context of the pull request

pull_request_target
    ↓
Runs workflow logic from the base repository context
```

`pull_request_target` requires particular caution because combining privileged repository context with untrusted pull request content or code can create a dangerous trust boundary.

Do not use it simply as a way to make secrets available to forked pull requests.

---

## Third-Party Actions

Third-party actions are executable dependencies.

Risk controls include:

- Trusted sources
- Version pinning
- SHA pinning
- Minimal permissions
- Limited secrets
- Dependency review
- Action allowlists
- Internal reusable workflows

A release workflow containing an untrusted action can become a supply-chain entry point.

---

## OIDC and AWS

The preferred architecture for AWS authentication from GitHub Actions is generally:

```text
GitHub Actions
       │
       │ OIDC token
       ▼
AWS STS
       │
       │ AssumeRole
       ▼
IAM Role
       │
       ├── ECR
       ├── ECS
       ├── EC2
       ├── S3
       └── Lambda
```

This avoids storing long-lived AWS access keys in GitHub secrets.

The IAM trust policy should restrict the workflow identity as tightly as practical.

---

## Docker CI/CD

A containerized delivery pipeline commonly follows:

```text
Source
 ↓
Dockerfile
 ↓
Buildx
 ↓
Image
 ↓
Security Scan
 ↓
SBOM
 ↓
Registry
 ↓
Digest
 ↓
Environment Promotion
```

Build once:

```text
Image A
```

Promote the same image:

```text
Staging
 ↓
Production
```

Do not rebuild the application merely because the target environment changed.

---

## Release Architecture

A release establishes a stable versioned identity.

```text
Commit
 ↓
Semantic Version
 ↓
Git Tag
 ↓
Build
 ↓
Immutable Artifact
 ↓
GitHub Release
 ↓
Staging
 ↓
Approval
 ↓
Production
```

Release metadata should include enough information to identify the exact artifact deployed.

---

## Deployment Strategies

The major deployment strategies covered in this section are:

| Strategy | Primary Idea |
|---|---|
| Rolling | Replace instances gradually |
| Blue/Green | Maintain two environments and switch traffic |
| Canary | Gradually increase traffic to the new version |
| Zero Downtime | Maintain service availability throughout deployment |

The appropriate strategy depends on:

- Traffic routing
- Capacity
- Application state
- Database compatibility
- Rollback requirements
- Infrastructure platform

---

## Rolling Deployment

Typical flow:

```text
v1
 ↓
Replace a subset
 ↓
Health Check
 ↓
Replace more
 ↓
Health Check
 ↓
Complete
```

Rolling deployment is efficient but requires strong compatibility between old and new instances during the transition.

---

## Blue/Green Deployment

```text
             ┌── Blue v1
Traffic ─────┤
             └── Green v2

Initial:
Traffic → Blue

After validation:
Traffic → Green
```

The old environment can remain available as a rollback target.

The primary cost is running additional capacity.

---

## Canary Deployment

Canary deployment gradually exposes traffic:

```text
v1 → 95%
v2 → 5%

v1 → 75%
v2 → 25%

v1 → 50%
v2 → 50%

v2 → 100%
```

Promotion should be based on defined health signals rather than simply elapsed time.

---

## Zero Downtime

Zero-downtime deployment requires more than choosing a deployment strategy.

Consider:

- Readiness
- Liveness
- Graceful shutdown
- Connection draining
- Database compatibility
- Long-lived connections
- Background workers
- Queue consumers
- Load balancer behavior

For Django and FastAPI services, application shutdown behavior and database compatibility are part of deployment correctness.

---

## Deployment Concurrency

Production deployments should generally be serialized when they modify the same environment.

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

The policy for pull requests may differ:

```yaml
concurrency:
  group: pr-${{ github.head_ref }}
  cancel-in-progress: true
```

Production deployments and development validation have different concurrency requirements.

---

## Rollback

Rollback should use an existing known-good artifact.

```text
Current:
v2.5.0
 ↓
Failure

Rollback:
v2.4.3
```

Avoid rebuilding the old version during an incident.

The old artifact should already exist and be identifiable.

---

## Database Rollback

Application rollback does not necessarily mean database rollback.

Prefer backward-compatible migrations:

```text
Expand
 ↓
Deploy
 ↓
Migrate
 ↓
Contract
```

This allows application rollback without immediately requiring destructive schema reversal.

---

## Runners

GitHub Actions execution can use:

```text
GitHub-hosted runners
Self-hosted runners
Ephemeral runners
```

Self-hosted runners are useful when workflows require:

- Private network access
- Custom software
- Internal infrastructure
- Specialized hardware

But they introduce additional security and lifecycle responsibilities.

---

## Persistent vs Ephemeral Runners

Persistent runners can retain:

- Files
- Credentials
- Docker layers
- Tool installations
- Workspace state

This can create cross-job contamination and credential leakage.

Ephemeral runners provide stronger isolation by creating a clean execution environment for each workload.

---

## Runner Governance

Organizations should control:

- Runner registration
- Labels
- Runner groups
- Network access
- Software images
- Updates
- Access to secrets
- Lifecycle
- Autoscaling

A self-hosted runner with production network access should not be treated like a normal developer workstation.

---

## Operations

Operational CI/CD management includes:

```text
Workflow Management
Runner Management
Environment Management
Secret Management
Variable Management
Artifact Retention
Cache Management
Monitoring
Logging
Debugging
Cost Management
```

The goal is to keep the delivery platform reliable as repository and deployment counts increase.

---

## Monitoring CI/CD

Useful CI/CD metrics include:

- Workflow success rate
- Workflow duration
- Queue time
- Deployment duration
- Release frequency
- Deployment failure rate
- Rollback frequency
- Runner utilization
- Cache hit rate
- Artifact storage
- Approval wait time

Monitoring should cover the delivery platform itself, not just the applications it deploys.

---

## Reliability

A production CI/CD platform should be designed around failure domains.

```text
Source
 ↓
GitHub
 ↓
Runner
 ↓
Build
 ↓
Artifact Registry
 ↓
Cloud
 ↓
Deployment
```

Failures can occur independently at every layer.

A reliable system provides:

- Retry where safe
- Idempotent operations
- Clear state
- Immutable artifacts
- Reproducible builds
- Rollback
- Auditability
- Failure isolation

---

## Cost Optimization

CI/CD costs can grow through:

- Large test matrices
- Long-running jobs
- Docker builds
- Multi-platform builds
- Excessive artifact retention
- Excessive cache storage
- Unnecessary workflows
- Over-sized self-hosted infrastructure

Useful optimizations include:

- Dependency caching
- Docker layer caching
- Selective testing
- Dynamic matrices
- Reusable workflows
- Appropriate artifact retention
- Right-sized runners

Do not trade away security or release integrity simply to reduce CI minutes.

---

## Troubleshooting Model

Troubleshooting should follow:

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

Typical failure domains include:

```text
Workflow Syntax
Triggers
Expressions
Contexts
Secrets
Permissions
Matrices
Artifacts
Caches
Containers
Service Containers
Actions
Runners
OIDC
AWS
Docker
Registry
Deployment
Concurrency
Security
Production
```

---

## GitHub CLI for Operations

The GitHub CLI is useful for operational CI/CD tasks.

List workflows:

```bash
gh workflow list
```

Run a workflow:

```bash
gh workflow run release.yml
```

List workflow runs:

```bash
gh run list
```

Inspect a run:

```bash
gh run view RUN_ID
```

View logs:

```bash
gh run view RUN_ID --log
```

List releases:

```bash
gh release list
```

View a release:

```bash
gh release view v2.5.0
```

The CLI should complement automation rather than become a replacement for reproducible workflows.

---

## Production Pipeline Reference

A senior backend engineer should be able to design a pipeline such as:

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
Matrix Testing
    ↓
Build
    ↓
Docker Image
    ↓
ECR
    ↓
Staging
    ↓
Health Validation
    ↓
Production Approval
    ↓
Production
    ↓
Monitoring
    ↓
Rollback
```

Each transition should have a clear contract.

---

## Production Pipeline Contracts

| Boundary | Contract |
|---|---|
| PR → CI | Source is validated |
| CI → Build | Required tests passed |
| Build → Registry | Immutable artifact produced |
| Registry → Staging | Artifact identity preserved |
| Staging → Production | Validation and approval completed |
| Production → Monitoring | Deployment health observable |
| Monitoring → Rollback | Recovery artifact identifiable |

This approach prevents CI/CD from becoming a collection of loosely connected scripts.

---

## Recommended Architecture

```mermaid
flowchart TB
    subgraph Source
        PR[Pull Request]
        MAIN[Main Branch]
        TAG[Release Tag]
    end

    subgraph CI
        LINT[Lint]
        UNIT[Unit Tests]
        INT[Integration Tests]
        MATRIX[Test Matrix]
        SEC[Security]
    end

    subgraph Build
        BUILD[Docker Buildx]
        IMAGE[Immutable Image]
        SBOM[SBOM / Provenance]
    end

    subgraph Registry
        ECR[ECR]
    end

    subgraph Environments
        STAGE[Staging]
        PROD[Production]
    end

    subgraph Operations
        OBS[Monitoring]
        RB[Rollback]
    end

    PR --> LINT
    LINT --> UNIT
    UNIT --> INT
    INT --> MATRIX
    MATRIX --> SEC
    SEC --> MAIN

    MAIN --> BUILD
    BUILD --> IMAGE
    IMAGE --> SBOM
    SBOM --> ECR

    ECR --> STAGE
    STAGE --> PROD

    PROD --> OBS
    OBS --> RB
    RB --> ECR

    MAIN --> TAG
```

---

## Senior Engineering Focus

The most important concepts in this directory are not individual YAML properties.

They are architectural principles.

### Immutable Artifacts

Build once and promote the same artifact.

### Explicit Dependencies

Use `needs`, outputs, artifacts, and reusable workflows to make data flow explicit.

### Least Privilege

Treat workflows, runners, secrets, and cloud credentials as security boundaries.

### Environment Protection

Production should have explicit controls around deployment.

### Concurrency

Prevent multiple workflows from mutating the same production state simultaneously.

### Reproducibility

A release should be traceable to an exact commit, build, and artifact.

### Observability

CI/CD failures should be diagnosable without manually reconstructing what happened.

### Recovery

Rollback and recovery should be designed before production incidents occur.

---

## Common CI/CD Mistakes

### Treating GitHub Actions as Only YAML

A workflow is an execution system involving source, runners, credentials, dependencies, artifacts, and external infrastructure.

### Rebuilding for Every Environment

This violates the build-once/deploy-many model.

### Using Mutable Artifacts

Tags such as `latest` do not provide deterministic release identity.

### Sharing Production Credentials With CI

Build and test jobs should not receive production access unnecessarily.

### No Deployment Concurrency

Concurrent deployments can create race conditions.

### Overusing Self-Hosted Runners

Self-hosted infrastructure adds operational and security responsibilities.

### Using Caches as Artifacts

Caches are disposable optimizations.

### No Rollback Plan

A deployment pipeline without a recovery path is incomplete.

### Excessive Matrix Dimensions

Large matrices can multiply CI cost and execution time without providing proportional coverage.

### Mixing Trust Boundaries

Untrusted pull request code should not automatically receive privileged credentials or access to production infrastructure.

---

## Senior-Level Design Questions

Use these questions to validate understanding of this section:

- How does GitHub Actions execute a workflow from trigger to runner?
- How would you design a CI pipeline for a Django application using PostgreSQL and Redis?
- When should a reusable workflow be used instead of a composite action?
- How would you generate a dynamic matrix from changed services in a monorepo?
- How do artifacts differ from caches?
- How would you prevent two production deployments from running simultaneously?
- How would you protect a release workflow from a compromised third-party action?
- How does GitHub OIDC authenticate to AWS without long-lived credentials?
- How would you promote the same Docker image from staging to production?
- How would you design a zero-downtime deployment for a FastAPI service?
- How would you roll back an ECS deployment?
- How would you handle a database migration during a rolling deployment?
- How would you release multiple microservices independently?
- How would you design CI/CD for a private AWS network?
- When would you use a self-hosted runner?
- How would you diagnose an intermittent CI failure?
- How would you design release automation for semantic versions?
- How would you recover from a partially completed release?
- How would you protect production deployment from concurrency races?
- How would you design CI/CD for high availability and disaster recovery?

---

## Production Readiness Checklist

Before considering a CI/CD implementation production-ready, verify:

### Workflow

- [ ] Workflow triggers are intentional.
- [ ] Jobs have explicit dependencies.
- [ ] Expressions and shell execution are clearly separated.
- [ ] Outputs are used for cross-job data flow.
- [ ] Matrix dimensions are controlled.

### Testing

- [ ] Unit tests execute automatically.
- [ ] Integration tests use isolated dependencies.
- [ ] PostgreSQL/Redis services are ready before tests.
- [ ] Test reports are retained appropriately.
- [ ] Coverage is visible where required.

### Security

- [ ] `GITHUB_TOKEN` uses least privilege.
- [ ] Secrets are scoped appropriately.
- [ ] Untrusted input is handled safely.
- [ ] Third-party actions are controlled.
- [ ] AWS uses OIDC where appropriate.
- [ ] Production credentials are isolated.

### Artifacts

- [ ] Builds are reproducible.
- [ ] Artifacts are immutable.
- [ ] Docker images have deterministic identity.
- [ ] SBOM/provenance requirements are satisfied.
- [ ] Artifact retention supports rollback.

### Deployment

- [ ] Environments are explicitly defined.
- [ ] Production approval is configured where required.
- [ ] Deployment concurrency is controlled.
- [ ] Health checks validate deployments.
- [ ] Rollback is documented and tested.

### Operations

- [ ] Workflow logs are sufficient for diagnosis.
- [ ] Runner capacity is monitored.
- [ ] Artifact and cache retention is controlled.
- [ ] CI/CD costs are monitored.
- [ ] Failure domains are understood.
- [ ] Recovery procedures are documented.

---

## How to Use This Folder

For practical learning, work through the material in this order:

```text
Understand the Pipeline
        ↓
Understand Workflow Execution
        ↓
Understand Testing
        ↓
Understand Security
        ↓
Understand Artifact Creation
        ↓
Understand Docker
        ↓
Understand AWS Deployment
        ↓
Understand Releases
        ↓
Understand Deployment Strategies
        ↓
Understand Rollback
        ↓
Design the Complete Architecture
```

Do not memorize individual YAML properties in isolation.

For each feature, understand:

```text
Why does it exist?
       ↓
What problem does it solve?
       ↓
Where does it execute?
       ↓
What data does it consume?
       ↓
What state does it modify?
       ↓
What permissions does it require?
       ↓
What happens when it fails?
       ↓
How is it recovered?
```

That reasoning model is more valuable for senior backend engineering than memorizing workflow syntax.

## Key Takeaways

- This section should be treated as a complete CI/CD engineering system covering workflow design, testing, security, artifacts, releases, deployment, operations, and recovery.
- The central production pattern is **validate → build once → produce an immutable artifact → promote → deploy → observe → recover**.
- GitHub Actions security, AWS OIDC, least-privilege permissions, controlled runners, immutable artifacts, and environment protection are fundamental production concerns rather than optional enhancements.
- Senior-level CI/CD design requires understanding failure domains, concurrency, compatibility, observability, rollback, scalability, cost, and maintainability together.
- The ultimate goal is to independently design and operate a production pipeline for Python/Django/FastAPI systems using Docker, AWS, PostgreSQL, Redis, Kafka, Celery, and GitHub Actions.