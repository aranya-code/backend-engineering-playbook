# README

## Overview

The **Interview** section is the final stage of the GitHub Actions CI/CD learning path. It is designed to move beyond feature-level knowledge and develop the ability to reason about GitHub Actions as a **production-grade CI/CD platform**.

The focus is not memorizing YAML syntax. Senior-level interviews typically test whether you can:

- Design maintainable CI/CD architectures.
- Choose appropriate GitHub Actions primitives.
- Secure workflows against untrusted code and compromised dependencies.
- Build and promote immutable artifacts.
- Authenticate securely with AWS using OIDC.
- Design scalable test matrices.
- Control deployment concurrency.
- Operate GitHub-hosted and self-hosted runners.
- Diagnose failures across multiple infrastructure boundaries.
- Design rollback and recovery strategies.
- Explain trade-offs under production constraints.

The interview material should be used after completing the foundational, security, deployment, operations, and troubleshooting sections of the GitHub Actions playbook.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Core GitHub Actions Questions](./01-%20Core%20GitHub%20Actions%20Questions.md) | This document provides interview questions and senior-level answers covering the core GitHub Actions concepts required for production CI/CD engineering. |
| 02 | [02- Workflow and Event Questions](./02-%20Workflow%20and%20Event%20Questions.md) | Workflow and event design is one of the most important GitHub Actions interview areas because the trigger determines when automation runs and what context is available. |
| 03 | [03- Jobs and Steps Questions](./03-%20Jobs%20and%20Steps%20Questions.md) | GitHub Actions workflows are executed through a hierarchy of workflows, jobs, and steps — each with its own execution scope and boundary. |
| 04 | [04- Expressions and Context Questions](./04-%20Expressions%20and%20Context%20Questions.md) | GitHub Actions expressions and contexts are the mechanism used to make workflows dynamic. |
| 05 | [05- Matrix Strategy Questions](./05-%20Matrix%20Strategy%20Questions.md) | GitHub Actions matrix strategies provide a declarative way to execute the same job across multiple combinations of inputs. |
| 06 | [06- Artifacts and Caching Questions](./06-%20Artifacts%20and%20Caching%20Questions.md) | GitHub Actions artifacts and caches solve different problems in CI/CD: artifacts are persistent workflow outputs; caches are disposable performance optimizations. |
| 07 | [07- Reusable Workflow Questions](./07-%20Reusable%20Workflow%20Questions.md) | Reusable workflows are one of the primary mechanisms for building maintainable GitHub Actions platforms across repositories. |
| 08 | [08- Custom Actions Questions](./08-%20Custom%20Actions%20Questions.md) | Custom GitHub Actions allow engineering teams to package repeatable CI/CD behavior behind a stable interface. |
| 09 | [09- Containers and Service Containers Questions](./09-%20Containers%20and%20Service%20Containers%20Questions.md) | GitHub Actions containers provide isolated execution environments for CI/CD jobs and the dependencies those jobs require. |
| 10 | [10- Environments and Deployment Questions](./10-%20Environments%20and%20Deployment%20Questions.md) | GitHub Actions environments provide a controlled boundary around deployments and environment-specific configuration. |
| 11 | [11- Concurrency Questions](./11-%20Concurrency%20Questions.md) | Concurrency in GitHub Actions controls how multiple workflow runs, jobs, and deployments interact when they target the same logical resource. |
| 12 | [12- Security Questions](./12-%20Security%20Questions.md) | GitHub Actions security is primarily a trust-boundary and privilege-management problem. |
| 13 | [13- GITHUB_TOKEN and Permissions Questions](./13-%20GITHUB_TOKEN%20and%20Permissions%20Questions.md) | `GITHUB_TOKEN` is the default GitHub-provided authentication token available to GitHub Actions workflows. |
| 14 | [14- OIDC and AWS Questions](./14-%20OIDC%20and%20AWS%20Questions.md) | GitHub Actions OpenID Connect (OIDC) provides a way for workflows to authenticate to AWS without storing long-lived AWS access keys in GitHub secrets. |
| 15 | [15- Docker CI CD Questions](./15-%20Docker%20CI%20CD%20Questions.md) | Docker is a core execution and packaging layer in modern CI/CD systems. In production pipelines, it is not enough to build a container image. |
| 16 | [16- Self Hosted Runner Questions](./16-%20Self%20Hosted%20Runner%20Questions.md) | Self-hosted runners allow GitHub Actions jobs to execute on infrastructure controlled by the organization instead of GitHub-managed machines. |
| 17 | [17- Supply Chain Security Questions](./17-%20Supply%20Chain%20Security%20Questions.md) | Software supply chain security protects the path from source code to a deployed production artifact. |
| 18 | [18- Release Automation Questions](./18-%20Release%20Automation%20Questions.md) | Release automation is the CI/CD layer responsible for turning validated source code into a controlled, traceable, repeatable software release. |
| 19 | [19- Troubleshooting Questions](./19-%20Troubleshooting%20Questions.md) | GitHub Actions troubleshooting is an engineering discipline rather than a process of repeatedly rerunning failed workflows and hoping for a different result. |
| 20 | [20- Architecture Questions](./20-%20Architecture%20Questions.md) | GitHub Actions architecture is the design of the complete automation system around workflows, runners, artifacts, environments, and deployment pipelines. |
| 21 | [21- Scenario Based Questions](./21-%20Scenario%20Based%20Questions.md) | GitHub Actions scenario-based interview questions test whether an engineer can design, secure, troubleshoot, and operate a CI/CD system under realistic production constraints. |
| 22 | [22- Production CI CD Scenarios](./22-%20Production%20CI%20CD%20Scenarios.md) | Production CI/CD scenarios evaluate whether an engineer can design and operate a delivery system under real operational constraints. |
| 23 | [23- Comparison Questions](./23-%20Comparison%20Questions.md) | Comparison questions in GitHub Actions interviews test whether an engineer understands why two mechanisms exist, when each is appropriate, and what trade-offs are involved. |
| 24 | [24- Common Interview Traps](./24-%20Common%20Interview%20Traps.md) | GitHub Actions interview traps usually appear when a candidate knows the YAML syntax but does not understand the execution model, trust boundaries, or production constraints. |
| 25 | [25- Senior Level Questions](./25-%20Senior%20Level%20Questions.md) | Senior GitHub Actions interviews are less about remembering YAML syntax and more about demonstrating that you can design, secure, operate, and evolve production CI/CD systems. |

---

## Interview Preparation Structure

The interview material progresses from conceptual questions toward architecture and production scenarios.

```text
Fundamentals
    ↓
Workflow Configuration
    ↓
Advanced Workflows
    ↓
Custom Actions
    ↓
Containers and Testing
    ↓
Security
    ↓
CI/CD and Deployment
    ↓
Runners and Operations
    ↓
Troubleshooting
    ↓
Architecture
    ↓
CLI
    ↓
Interview Preparation
```

The goal is to reach the point where a GitHub Actions question can be answered in terms of:

```text
Requirement
    ↓
Architecture
    ↓
Execution Model
    ↓
Trust Boundary
    ↓
Data / Artifact Flow
    ↓
Failure Modes
    ↓
Operational Controls
    ↓
Trade-offs
```

---

## Interview Documents

| File | Focus |
|---|---|
| [01- Fundamentals Questions.md](./01-%20Fundamentals%20Questions.md) | Core GitHub Actions concepts, execution model, workflows, jobs, steps, runners, actions, and terminology |
| [02- Workflow Design Questions.md](./02-%20Workflow%20Design%20Questions.md) | Workflow structure, triggers, expressions, contexts, dependencies, conditions, and execution design |
| [03- Matrix and Parallelism Questions.md](./03-%20Matrix%20and%20Parallelism%20Questions.md) | Matrix strategy, dynamic matrices, parallelism, `fail-fast`, `max-parallel`, and scaling test execution |
| [04- Reusable Workflow Questions.md](./04-%20Reusable%20Workflow%20Questions.md) | `workflow_call`, inputs, outputs, secrets, reusable CI/CD workflows, versioning, and governance |
| [05- Custom Action Questions.md](./05-%20Custom%20Action%20Questions.md) | Composite, JavaScript, and Docker actions, action contracts, versioning, testing, and security |
| [06- Containers and Testing Questions.md](./06-%20Containers%20and%20Testing%20Questions.md) | Job containers, service containers, PostgreSQL, MySQL, Redis, pytest, integration testing, coverage, and test artifacts |
| [07- Security Questions.md](./07-%20Security%20Questions.md) | `GITHUB_TOKEN`, permissions, secrets, untrusted input, PR security, third-party actions, runners, and supply-chain security |
| [08- AWS and OIDC Questions.md](./08-%20AWS%20and%20OIDC%20Questions.md) | OIDC, STS, IAM trust policies, AWS authentication, ECR, ECS, EC2, Lambda, and deployment security |
| [09- Docker and Artifact Questions.md](./09-%20Docker%20and%20Artifact%20Questions.md) | Buildx, image tagging, digests, ECR, caching, immutable artifacts, SBOM, provenance, and promotion |
| [10- Deployment Questions.md](./10-%20Deployment%20Questions.md) | Environment promotion, approvals, concurrency, rolling, blue/green, canary, zero downtime, and rollback |
| [11- Runner and Operations Questions.md](./11-%20Runner%20and%20Operations%20Questions.md) | Hosted/self-hosted runners, runner groups, labels, private networking, ephemeral runners, autoscaling, and operations |
| [12- Troubleshooting Questions.md](./12-%20Troubleshooting%20Questions.md) | Failure-domain troubleshooting, diagnostics, workflow failures, runners, AWS, Docker, artifacts, and deployments |
| [13- Architecture Questions.md](./13-%20Architecture%20Questions.md) | CI/CD architecture, production pipelines, microservices, monorepos, enterprise workflows, and platform design |
| [14- Scenario Based Questions.md](./14-%20Scenario%20Based%20Questions.md) | Production scenarios requiring architecture, security, reliability, deployment, and incident reasoning |
| [15- Comparison Questions.md](./15-%20Comparison%20Questions.md) | Trade-off questions such as reusable workflows vs actions, artifacts vs caches, rolling vs blue/green vs canary |
| [16- Common Interview Traps.md](./16-%20Common%20Interview%20Traps.md) | Frequently misunderstood GitHub Actions behavior, security mistakes, configuration traps, and senior-level pitfalls |
| [17- Supply Chain Security Questions.md](./17-%20Supply%20Chain%20Security%20Questions.md) | Dependency, action, runner, artifact, provenance, SBOM, signing, and supply-chain attack scenarios |
| [18- Release Automation Questions.md](./18-%20Release%20Automation%20Questions.md) | Git tags, semantic versioning, releases, immutable artifacts, release promotion, and rollback |
| [19- Senior Level Questions.md](./19-%20Senior%20Level%20Questions.md) | Senior-level engineering questions covering architecture, security, AWS, Docker, runners, reliability, deployment, and production reasoning |
| [20- Architecture Questions.md](./20-%20Architecture%20Questions.md) | Advanced architecture and system-design questions for production GitHub Actions platforms |
| [21- Scenario Based Questions.md](./21-%20Scenario%20Based%20Questions.md) | Senior production scenarios covering security, deployments, concurrency, AWS, runners, testing, and incident response |
| [23- Comparison Questions.md](./23-%20Comparison%20Questions.md) | Advanced GitHub Actions comparison and trade-off questions |
| [24- Common Interview Traps.md](./24-%20Common%20Interview%20Traps.md) | High-frequency interview traps involving execution, security, artifacts, permissions, deployment, and operations |
| [25- Senior Level Questions.md](./25-%20Senior%20Level%20Questions.md) | Comprehensive senior-level question bank covering architecture, security, AWS, Docker, deployment, runners, reliability, and production incidents |

> Keep the navigation table synchronized with the actual files in this folder. If files are renamed or reordered, update the corresponding links.

---

## Core Interview Domains

### GitHub Actions Fundamentals

You should be able to explain:

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

Important topics:

- Workflow files
- YAML structure
- Jobs
- Steps
- Actions
- Runners
- Execution lifecycle
- GitHub-hosted runners
- Workflow limitations
- Quotas and constraints

The important interview skill is explaining how these components interact rather than defining them independently.

---

### Workflow Configuration

Be comfortable with:

- `push`
- `pull_request`
- `pull_request_target`
- `workflow_dispatch`
- `schedule`
- `workflow_call`
- `workflow_run`
- `repository_dispatch`
- `release`
- Branch filters
- Path filters
- Tag filters
- Manual inputs

You should also understand expression evaluation:

```yaml
if: ${{ success() && github.ref == 'refs/heads/main' }}
```

and the difference between:

```text
GitHub expression evaluation
```

and:

```text
Shell execution
```

This distinction becomes particularly important when discussing security.

---

## Contexts and Data Flow

Senior candidates should understand how workflow data moves between execution boundaries.

```text
Step
 ↓
GITHUB_OUTPUT
 ↓
Step Output
 ↓
Job Output
 ↓
needs.<job>.outputs
 ↓
Dependent Job
```

Know the purpose and scope of:

- `github`
- `env`
- `vars`
- `secrets`
- `steps`
- `needs`
- `job`
- `runner`
- `matrix`
- `strategy`
- `inputs`

Also understand:

- `$GITHUB_ENV`
- `$GITHUB_OUTPUT`
- `$GITHUB_PATH`
- Step summaries
- Annotations
- Logging

---

## Advanced Workflow Design

Senior-level preparation should cover:

- Reusable workflows
- Composite actions
- Fan-out/fan-in
- Dependency graphs
- Dynamic matrices
- Structured JSON outputs
- Conditional execution
- Workflow outputs
- Multi-environment workflows
- Promotion workflows
- Deployment concurrency

A key distinction:

| Mechanism | Primary Role |
|---|---|
| Reusable workflow | Multi-job workflow orchestration |
| Composite action | Reusable steps within a job |
| JavaScript action | Programmatic action logic |
| Docker action | Containerized action execution |

---

## Matrix and Parallelism

Understand how matrix execution affects both CI speed and infrastructure capacity.

Example:

```text
Python Versions
      ×
Database Versions
      ×
Operating Systems
```

can quickly create hundreds of jobs.

Important controls include:

- `include`
- `exclude`
- `fail-fast`
- `max-parallel`
- Dynamic matrices
- JSON-generated matrices

Senior-level reasoning should consider:

- Runner capacity
- Queue time
- Database connection limits
- Cost
- Test duration
- Downstream service capacity
- Flaky tests
- PR vs nightly vs release coverage

---

## Containers and Testing

A production backend CI pipeline may look like:

```text
Python Application
       ↓
PostgreSQL
       +
Redis
       ↓
pytest
       ↓
Coverage
       ↓
Test Reports
       ↓
Artifacts
```

Be prepared to discuss:

- Job containers
- Service containers
- Container networking
- Readiness
- PostgreSQL
- MySQL
- Redis
- Django
- FastAPI
- pytest
- Unit testing
- Integration testing
- API testing
- End-to-end testing
- Coverage
- Test reports
- Test artifacts
- Parallel execution

A senior answer should address test isolation and service capacity, not only how to start a container.

---

## Security

Security should be treated as a system-wide concern.

Important areas include:

### Identity and Permissions

- `GITHUB_TOKEN`
- `permissions`
- Job-level permissions
- Least privilege
- `contents`
- `actions`
- `packages`
- `pull-requests`
- `id-token`

### Secrets

- Repository secrets
- Organization secrets
- Environment secrets
- Secret inheritance
- Masking
- Logging risks
- Command-argument exposure
- Artifact exposure
- Rotation

### Untrusted Input

Be prepared to reason about attacker-controlled:

- PR titles
- Branch names
- Commit messages
- Issue content
- Workflow inputs

For example, do not blindly interpolate untrusted values into shell commands.

### Pull Request Security

Understand:

```text
pull_request
vs
pull_request_target
```

and the security implications of:

- Forks
- Untrusted code
- Secrets
- Write permissions
- Privileged workflows

### Supply Chain

Understand:

- Third-party actions
- SHA pinning
- Dependency review
- Dependabot
- SBOM
- Provenance
- Attestations
- Signing
- Build integrity

### Runner Security

Understand:

- GitHub-hosted runners
- Persistent self-hosted runners
- Ephemeral runners
- Runner isolation
- Private network access
- Untrusted code execution

---

## AWS and OIDC

A senior backend engineer should be able to explain:

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
AWS Service
```

Important services include:

- IAM
- STS
- ECR
- S3
- ECS
- EC2
- Lambda
- CloudFormation
- Terraform

Understand the distinction between:

```text
IAM Trust Policy
```

and:

```text
IAM Permissions Policy
```

Also understand:

- `id-token: write`
- OIDC subject conditions
- Branch/environment restrictions
- Role separation
- Cross-account access
- `AccessDenied`
- `iam:PassRole`
- AWS CLI diagnostics
- CloudTrail investigation

---

## Docker and Artifact Promotion

The preferred production model is:

```text
Build
 ↓
Immutable Artifact
 ↓
Registry
 ↓
Staging
 ↓
Approval
 ↓
Production
```

rather than:

```text
Build Staging
 ↓
Deploy Staging

Build Production
 ↓
Deploy Production
```

Important topics:

- Docker
- Buildx
- Multi-stage builds
- Layer caching
- Image tags
- Commit SHA tags
- Image digests
- ECR
- Vulnerability scanning
- SBOM
- Provenance
- Attestations
- Signing

The deployment system should be able to identify exactly which artifact was deployed.

---

## Deployment Strategies

Know the trade-offs between:

| Strategy | Core Model | Key Concern |
|---|---|---|
| Rolling | Incremental replacement | Mixed versions |
| Blue/Green | Active and inactive environments | Additional capacity |
| Canary | Gradual traffic exposure | Requires strong observability |
| Zero Downtime | No intentional service interruption | Compatibility and graceful transitions |

Be prepared to discuss:

- Health checks
- Readiness
- Connection draining
- Deployment concurrency
- Rollback
- Database compatibility
- Long-lived connections
- Celery workers
- Kafka consumers
- Redis
- gRPC
- Feature flags

---

## Database and Migration Safety

A production deployment cannot treat application rollback and database rollback as the same operation.

Understand:

```text
Expand
 ↓
Deploy Compatible Application
 ↓
Migrate Usage
 ↓
Contract
```

For Django, consider:

- `manage.py migrate`
- Schema compatibility
- Application compatibility
- Static files
- Background workers
- Database connection behavior

Senior-level questions often test whether you understand that database changes can be difficult or impossible to reverse safely.

---

## Runners and Operations

Be comfortable with:

- GitHub-hosted runners
- Self-hosted runners
- Runner registration
- Runner labels
- Runner groups
- Linux runners
- Windows runners
- Custom software
- Private network access
- Persistent runners
- Ephemeral runners
- Runner autoscaling

Also understand operational concerns:

```text
Job Queue
 ↓
Runner Capacity
 ↓
Provisioning
 ↓
Execution
 ↓
Cleanup
 ↓
Replacement
```

Consider:

- CPU
- Memory
- Disk
- Network
- API rate limits
- Cloud quotas
- IP exhaustion
- Provisioning latency
- Cost
- Security
- Drift
- Monitoring

---

## Troubleshooting

Senior troubleshooting should follow a failure-domain model:

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

Relevant failure domains include:

- Workflow syntax
- Triggers
- Branch/path filters
- Jobs
- Steps
- Expressions
- Contexts
- Environment variables
- Secrets
- Permissions
- Matrices
- Reusable workflows
- Artifacts
- Caches
- Containers
- Service containers
- Custom actions
- Runners
- Self-hosted runners
- OIDC
- AWS authentication
- Docker builds
- Registries
- Deployments
- Concurrency
- Race conditions
- Security

Useful operational commands include:

```bash
gh workflow list
gh workflow run <workflow>
gh run list
gh run view <run-id>
gh run view <run-id> --log
gh run rerun <run-id>
gh run download <run-id>
```

AWS diagnostics may include:

```bash
aws sts get-caller-identity
aws ecr describe-repositories
aws ecr describe-images \
  --repository-name <repository>
```

The command should support a hypothesis. Do not execute commands randomly.

---

## GitHub CLI Interview Scope

The CLI material should remain focused on GitHub Actions operations.

### Workflow Inspection

```bash
gh workflow list
gh run list
gh run view <run-id>
```

### Logs

```bash
gh run view <run-id> --log
```

### Reruns

```bash
gh run rerun <run-id>
```

### Artifacts

```bash
gh run download <run-id>
```

### Workflow Execution

```bash
gh workflow run <workflow>
```

The goal is operational fluency rather than becoming a generic GitHub CLI reference.

---

## Architecture Preparation

Senior architecture preparation should cover:

```text
CI Architecture
        ↓
CD Architecture
        ↓
Artifact Architecture
        ↓
Environment Promotion
        ↓
Deployment Architecture
        ↓
Runner Architecture
        ↓
Security Architecture
        ↓
Observability
        ↓
Recovery / Rollback
```

Important architectures include:

- Production CI/CD
- Reusable workflows
- Enterprise workflow platforms
- Docker CI/CD
- AWS deployment
- Artifact promotion
- Environment promotion
- Rolling deployment
- Blue/green deployment
- Canary deployment
- High-availability CI/CD
- Scalable runner infrastructure
- Recovery architecture
- Rollback architecture

---

## Production Pipeline Reference

The target level of understanding is a complete pipeline such as:

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
Approval
    ↓
Production
    ↓
Monitoring
    ↓
Rollback
```

Each stage should have an explicit purpose.

| Stage | Primary Responsibility |
|---|---|
| Pull Request | Validate proposed change |
| Lint | Static quality checks |
| Unit Tests | Fast deterministic validation |
| Integration Tests | Validate service interactions |
| Security Scan | Identify security issues |
| Matrix Testing | Validate compatibility |
| Build | Produce deployable artifact |
| Docker Image | Package runtime |
| ECR | Store immutable artifact |
| Staging | Validate production-like deployment |
| Approval | Human deployment gate |
| Production | Release validated artifact |
| Monitoring | Validate runtime behavior |
| Rollback | Restore known-good state |

---

## Senior Interview Scenarios

The interview preparation should emphasize scenarios such as:

### Deployment Concurrency

> Production deployment must never run twice simultaneously.

Discuss:

- Concurrency groups
- Idempotency
- Artifact identity
- Environment protection
- Deployment state

### Manual Approval

> Production requires approval before deployment.

Discuss:

- GitHub Environments
- Required reviewers
- Protected branches
- Artifact identity
- Deployment history
- Concurrency

### Matrix Scaling

> Multiple Python versions and databases must be tested.

Discuss:

- Matrix dimensions
- `fail-fast`
- `max-parallel`
- Cost
- Database capacity
- PR vs nightly strategy

### Integration Testing

> Django integration tests require PostgreSQL and Redis.

Discuss:

- Service containers
- Networking
- Readiness
- Test isolation
- Connection limits

### AWS Authentication

> AWS credentials must not be stored as long-lived secrets.

Discuss:

- OIDC
- STS
- IAM trust policy
- IAM permissions
- Role separation

### Shared CI

> A reusable CI pipeline must support multiple repositories.

Discuss:

- `workflow_call`
- Inputs
- Outputs
- Secrets
- Versioning
- Consumer compatibility
- Blast radius

### Compromised Action

> A third-party action used by multiple repositories is compromised.

Discuss:

- Containment
- Consumer inventory
- SHA/version identification
- Credential rotation
- Log review
- Artifact review
- Replacement
- Rebuild
- Governance

### Artifact Promotion

> A Docker image must move from staging to production without rebuilding.

Discuss:

```text
Build
 ↓
Digest
 ↓
ECR
 ↓
Staging
 ↓
Approval
 ↓
Same Digest
 ↓
Production
```

### Private Network

> A self-hosted runner needs access to an internal database.

Discuss:

- VPC
- Security groups
- Routing
- DNS
- Runner groups
- Labels
- Ephemeral runners
- Repository restrictions

---

## Senior-Level Reasoning Model

When answering an interview scenario, avoid immediately writing YAML.

Start with the requirement:

```text
What problem are we solving?
```

Then establish:

```text
Who can trigger it?
        ↓
What code executes?
        ↓
Where does it execute?
        ↓
What permissions does it need?
        ↓
What artifact is produced?
        ↓
How is it promoted?
        ↓
What can fail?
        ↓
How do we recover?
```

This demonstrates system-level thinking.

---

## Common Senior Interview Traps

### Treating GitHub Actions as Only YAML

A workflow is part of a distributed execution system involving runners, GitHub APIs, registries, cloud platforms, and application infrastructure.

### Confusing `needs` and `concurrency`

`needs` establishes dependency relationships.

`concurrency` controls competing executions.

### Treating Cache as Artifact

A cache accelerates execution.

An artifact represents an output.

### Granting Broad Permissions

Avoid:

```yaml
permissions: write-all
```

when a workflow requires only:

```yaml
permissions:
  contents: read
```

### Storing AWS Access Keys

Prefer OIDC and temporary credentials when the environment supports it.

### Rebuilding for Production

Rebuilding can produce a different artifact.

Prefer:

```text
Build Once
→ Promote Same Artifact
```

### Ignoring Database Compatibility

Application rollback may not be safe after an incompatible schema change.

### Using Persistent Runners for Untrusted Code

Persistent runners can retain state and credentials.

### Blindly Using `always()`

Always-running steps can behave incorrectly during cancellation and failure scenarios.

### Overusing Matrix Dimensions

A large matrix can become an infrastructure and cost problem.

### Assuming Deployment Success Means Application Health

A deployment command succeeding does not prove the application is healthy.

---

## Interview Preparation Checklist

### Fundamentals

- [ ] Explain Workflow → Job → Step → Action → Runner.
- [ ] Explain workflow execution.
- [ ] Explain job dependencies.
- [ ] Explain GitHub-hosted runners.

### Workflow Design

- [ ] Explain major events.
- [ ] Explain filters.
- [ ] Explain expressions.
- [ ] Explain contexts.
- [ ] Explain status functions.
- [ ] Explain outputs and environment propagation.

### Advanced Workflows

- [ ] Design reusable workflows.
- [ ] Design composite actions.
- [ ] Design dynamic matrices.
- [ ] Design fan-out/fan-in workflows.
- [ ] Design concurrency controls.

### Testing

- [ ] Design Python test matrices.
- [ ] Run PostgreSQL service containers.
- [ ] Run Redis service containers.
- [ ] Handle readiness.
- [ ] Publish coverage and reports.
- [ ] Control test parallelism.

### Security

- [ ] Configure least-privilege `GITHUB_TOKEN`.
- [ ] Secure secrets.
- [ ] Handle untrusted input.
- [ ] Explain `pull_request` vs `pull_request_target`.
- [ ] Secure third-party actions.
- [ ] Explain SHA pinning.
- [ ] Explain supply-chain security.
- [ ] Secure self-hosted runners.

### AWS

- [ ] Explain OIDC.
- [ ] Explain STS.
- [ ] Explain IAM trust policies.
- [ ] Explain IAM permissions.
- [ ] Authenticate with ECR.
- [ ] Deploy to ECS/EC2/Lambda.
- [ ] Troubleshoot `AccessDenied`.

### Docker

- [ ] Explain Buildx.
- [ ] Explain multi-stage builds.
- [ ] Explain layer caching.
- [ ] Explain image tags vs digests.
- [ ] Explain ECR workflows.
- [ ] Explain SBOM/provenance.

### Deployment

- [ ] Explain environment promotion.
- [ ] Explain approvals.
- [ ] Explain concurrency.
- [ ] Explain rolling deployment.
- [ ] Explain blue/green deployment.
- [ ] Explain canary deployment.
- [ ] Explain zero downtime.
- [ ] Explain rollback.

### Operations

- [ ] Troubleshoot workflow failures.
- [ ] Troubleshoot runners.
- [ ] Troubleshoot containers.
- [ ] Troubleshoot artifacts and caches.
- [ ] Troubleshoot OIDC.
- [ ] Troubleshoot AWS deployments.
- [ ] Use GitHub CLI operationally.

### Architecture

- [ ] Design production CI/CD.
- [ ] Design microservice CI/CD.
- [ ] Design monorepo CI/CD.
- [ ] Design enterprise reusable workflows.
- [ ] Design scalable runners.
- [ ] Design secure artifact promotion.
- [ ] Design rollback and recovery.

---

## How to Use This Section

A useful progression is:

```text
Read
 ↓
Explain Without Notes
 ↓
Solve Scenario
 ↓
Design Architecture
 ↓
Identify Failure Modes
 ↓
Explain Security Boundary
 ↓
Explain Trade-offs
 ↓
Implement YAML
 ↓
Troubleshoot
```

For each major topic, practice answering three levels of questions:

### Level 1 — Concept

> What is a reusable workflow?

### Level 2 — Implementation

> How would you implement a reusable workflow with inputs, secrets, outputs, and matrices?

### Level 3 — Architecture

> How would you design a versioned reusable CI/CD platform for 50 repositories while controlling security and blast radius?

A senior interview usually spends more time at Levels 2 and 3.

---

## Senior-Level Completion Criteria

You should be able to independently design and explain a production pipeline that:

```text
Accepts a Pull Request
        ↓
Runs Secure Validation
        ↓
Executes Matrix Testing
        ↓
Runs Integration Tests
        ↓
Builds an Immutable Artifact
        ↓
Publishes to ECR
        ↓
Deploys to Staging
        ↓
Validates Health
        ↓
Requires Production Approval
        ↓
Uses OIDC for AWS
        ↓
Controls Deployment Concurrency
        ↓
Promotes the Same Artifact
        ↓
Monitors Production
        ↓
Rolls Back Safely When Required
```

You should also be able to explain:

- How workflow data moves between jobs.
- How artifacts are produced and promoted.
- How dependencies are cached.
- How secrets are protected.
- How permissions are minimized.
- How OIDC authenticates with AWS.
- How reusable workflows reduce duplication.
- How concurrency prevents deployment races.
- How containers support integration testing.
- How Docker images are built and promoted.
- How deployments are protected.
- How failures are diagnosed.
- How production rollback works.
- How GitHub Actions security boundaries operate.
- How the platform scales without becoming operationally fragile.

---

## Key Takeaways

- **Senior GitHub Actions preparation should focus on architecture, security, reliability, troubleshooting, and production trade-offs rather than YAML memorization.**
- **The core production model is secure validation → immutable artifact → controlled promotion → health validation → monitoring → rollback.**
- **OIDC, least-privilege permissions, protected environments, concurrency, secure runners, and artifact integrity form the foundation of secure production CI/CD.**
- **Scenario-based reasoning is the strongest preparation for senior interviews because it tests how you handle failure, scale, security, and operational constraints together.**
- **The final goal is to independently design, explain, troubleshoot, and operate a production GitHub Actions platform for Python, Docker, AWS, and distributed backend systems.**