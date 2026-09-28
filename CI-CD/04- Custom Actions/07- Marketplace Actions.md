# 07- Marketplace Actions

## Overview

GitHub Marketplace actions provide reusable CI/CD capabilities that can be consumed directly from workflows. They can simplify common tasks such as source checkout, language setup, Docker builds, security scanning, artifact handling, cloud authentication, and deployment.

A Marketplace action is still executable code running inside a GitHub Actions job. Therefore, adopting an action is a software supply-chain decision, not merely a convenience feature.

The production model is:

```text
Marketplace Action
        ↓
Source / Maintainer
        ↓
Action Implementation
        ↓
Runner
        ↓
Workflow Permissions
        ↓
Secrets / Tokens
        ↓
External Systems
```

The important questions are not only:

> Does this action solve the problem?

but also:

- What code will execute?
- Which permissions does it receive?
- Which secrets can it access?
- Which dependencies does it use?
- Which runtime does it require?
- How is the action versioned?
- Can its behavior change unexpectedly?
- Can it access production infrastructure?
- How can the organization audit and govern it?

## What Marketplace Actions Are

A Marketplace action is a reusable GitHub Action published for consumption by workflows.

A workflow might contain:

```yaml
steps:
  - name: Checkout source
    uses: actions/checkout@v4

  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: "3.12"

  - name: Run tests
    run: pytest
```

The `uses:` syntax identifies an action:

```text
owner/repository@version
```

For example:

```yaml
uses: actions/checkout@v4
```

The action executes as part of the workflow's job.

## Marketplace Actions vs Custom Actions

Marketplace actions and custom actions use the same underlying GitHub Actions model.

| Aspect | Marketplace Action | Internal Custom Action |
|---|---|---|
| Source | External/public or published action | Organization-controlled |
| Ownership | Third party or public maintainer | Internal team |
| Trust model | External dependency | Internal dependency |
| Updates | Maintainer controlled | Organization controlled |
| Review | Organization must perform | Internal review |
| Versioning | Maintainer-defined | Organization-defined |
| Governance | Allowlist/restrictions | Platform governance |
| Typical use | Common CI/CD capability | Organization-specific behavior |

Marketplace does not mean automatically trusted.

An action should be evaluated according to the access it receives and the impact of its behavior.

## Why Use Marketplace Actions

Marketplace actions can reduce duplicated CI/CD implementation.

Instead of implementing Docker authentication, artifact upload, or language setup from scratch, a workflow can use an established action.

For example:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"
```

Benefits include:

- Reuse.
- Faster workflow development.
- Standardized integrations.
- Maintained implementations.
- Reduced duplicated code.
- Easier workflow composition.

The trade-off is that the organization becomes dependent on external executable code.

## When to Use Marketplace Actions

Marketplace actions are useful when:

- The task is common.
- The action is actively maintained.
- Its implementation is understandable.
- Its permissions are appropriate.
- Its security posture is acceptable.
- Its versioning is predictable.
- The organization can govern the dependency.

Examples include:

```text
Checkout
Python setup
Node setup
Docker build
Artifact upload
Artifact download
Cloud authentication
Security scanning
```

## When to Build an Internal Action

Consider an internal action when the behavior is:

- Organization-specific.
- Security-sensitive.
- Repeated across many repositories.
- Closely coupled to internal infrastructure.
- Required to follow internal deployment policy.
- Difficult to safely standardize through an external action.

Example:

```text
Internal Deployment Platform
        ↓
Internal Deploy Action
        ↓
AWS ECS
```

This allows the platform team to control:

- Inputs.
- Outputs.
- Authentication.
- Permissions.
- Deployment policy.
- Observability.
- Versioning.
- Rollback behavior.

## Marketplace Action Execution Model

The execution model remains:

```text
Workflow
   ↓
Job
   ↓
Runner
   ↓
Marketplace Action
   ↓
Action Runtime
   ↓
External System
```

Depending on the action type, the runtime may be:

```text
JavaScript
Docker
Composite
```

Therefore, before adopting an action, determine its implementation type.

## Action Types

Marketplace actions commonly use one of the three major custom action models.

| Type | Runtime | Typical use |
|---|---|---|
| JavaScript | Node.js | API integrations and programmatic logic |
| Docker | Container | Specialized Linux runtime |
| Composite | Runner shell / actions | Reusable step sequences |

The implementation type affects:

- Startup behavior.
- Dependencies.
- Platform compatibility.
- Debugging.
- Security considerations.
- Runtime maintenance.

## Marketplace Action Discovery

Finding an action is only the first step.

Evaluate the action using:

```text
Discovery
   ↓
Source Review
   ↓
Permission Review
   ↓
Dependency Review
   ↓
Version Review
   ↓
Security Review
   ↓
Test
   ↓
Controlled Adoption
```

Do not select an action based only on:

- Marketplace ranking.
- Number of users.
- README quality.
- Number of stars.
- Convenience.

Those signals may be useful context but do not replace technical review.

## Source Repository Review

Before using a security-sensitive action, inspect its source repository.

Review:

- `action.yml`.
- Dockerfile if applicable.
- JavaScript source.
- Composite steps.
- Dependencies.
- Build process.
- Release process.
- Workflow permissions.
- Tests.
- Documentation.
- Security history.

The goal is to understand what code will execute inside your CI/CD environment.

## `action.yml` Review

Start with `action.yml`.

Look for:

```yaml
name:
description:
inputs:
outputs:
runs:
```

For example:

```yaml
runs:
  using: node20
  main: dist/index.js
```

or:

```yaml
runs:
  using: docker
  image: Dockerfile
```

or:

```yaml
runs:
  using: composite
```

The action definition reveals the execution model and interface.

## Permission Review

A Marketplace action inherits the permissions available to its job.

For example:

```yaml
permissions:
  contents: read
```

provides substantially less access than:

```yaml
permissions:
  contents: write
  pull-requests: write
  packages: write
```

Before adopting an action, determine what permissions it actually needs.

Prefer:

```yaml
permissions:
  contents: read
```

when read access is sufficient.

## GITHUB_TOKEN

GitHub Actions commonly provides the `GITHUB_TOKEN` to workflows.

Its capabilities are controlled through the workflow's `permissions` configuration.

Example:

```yaml
permissions:
  contents: read
```

A Marketplace action executing within that job can potentially use the permissions granted to the workflow.

Therefore:

```text
Third-Party Action
        +
Broad GITHUB_TOKEN
        =
Larger Blast Radius
```

Minimize permissions before introducing third-party actions.

## Job-Level Permissions

Permissions can be scoped to a job.

Example:

```yaml
jobs:
  test:
    permissions:
      contents: read

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - run: pytest
```

A deployment job may require additional permissions:

```yaml
jobs:
  deploy:
    permissions:
      contents: read
      id-token: write
```

This keeps elevated access away from unrelated jobs.

## Marketplace Actions and Secrets

A third-party action may receive secrets through:

```yaml
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
```

or another supported configuration mechanism.

Before providing a secret, ask:

- Why does the action need it?
- Is the secret necessary?
- Can OIDC replace a long-lived credential?
- Can the action operate with a narrower credential?
- Does the action log input values?
- Does the action send data externally?

Never provide production secrets merely because an action's documentation requests them.

## Secret Exposure

Avoid:

```yaml
- uses: third-party/action@v1
  env:
    TOKEN: ${{ secrets.PRODUCTION_TOKEN }}
```

unless the action genuinely requires the token and has been reviewed.

A better architecture may be:

```text
GitHub OIDC
    ↓
AWS STS
    ↓
Temporary Credentials
    ↓
Marketplace Action
```

instead of:

```text
Long-Lived AWS Access Key
    ↓
Marketplace Action
```

## Marketplace Actions and OIDC

For AWS deployments, OIDC can remove the need for long-lived AWS credentials.

Example:

```yaml
permissions:
  contents: read
  id-token: write
```

The workflow can authenticate through:

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
```

The IAM trust policy should restrict which GitHub repositories, branches, tags, or environments can assume the role.

## Untrusted Pull Requests

Third-party actions become particularly sensitive when processing untrusted pull requests.

Consider:

```text
Fork Pull Request
       ↓
Untrusted Repository Code
       ↓
Workflow
       ↓
Marketplace Action
       ↓
Credentials
```

If untrusted code can influence a privileged job, the action may become part of an attack path.

For pull request workflows:

```yaml
on:
  pull_request:
```

the security model differs from:

```yaml
on:
  pull_request_target:
```

`pull_request_target` requires particular caution because it runs in the context of the base repository.

Never assume that putting a third-party action inside a container automatically makes execution safe.

## `pull_request` vs `pull_request_target`

A simplified model is:

| Trigger | Primary context | Security concern |
|---|---|---|
| `pull_request` | Pull request merge context | Secrets are restricted; untrusted code may execute |
| `pull_request_target` | Base repository context | Privileged permissions/secrets require careful handling |

A dangerous pattern is combining `pull_request_target` with execution of attacker-controlled workflow code.

For example:

```text
pull_request_target
       ↓
Checkout PR branch
       ↓
Execute PR code
       ↓
Privileged token
```

This can create a serious security boundary violation.

## Third-Party Action Trust Boundary

A Marketplace action should be treated as code execution.

The trust boundary is:

```text
Repository
    ↓
Workflow
    ↓
Third-Party Action
    ↓
Runner
    ↓
Credentials / Tokens
    ↓
External Infrastructure
```

The action may potentially:

- Read files.
- Access environment variables.
- Use tokens.
- Call external APIs.
- Modify files.
- Execute commands.
- Access cloud resources permitted to the job.

Therefore, action selection belongs in the CI/CD security review process.

## Action Version References

Common references include:

```yaml
uses: third-party/action@main
```

```yaml
uses: third-party/action@v2
```

```yaml
uses: third-party/action@v2.4.1
```

```yaml
uses: third-party/action@<commit-sha>
```

They provide different reproducibility characteristics.

| Reference | Reproducibility | Maintenance |
|---|---|---|
| Branch | Low | Low |
| Major tag | Medium | Low |
| Exact release | High | Medium |
| SHA | Very high | Higher |

Avoid branch references for security-sensitive production workflows.

## SHA Pinning

SHA pinning references an immutable commit:

```yaml
- name: Checkout
  uses: actions/checkout@<commit-sha>
```

Advantages:

- Predictable execution.
- Stronger supply-chain control.
- Protection from mutable tag changes.
- Easier auditing.

The trade-off is maintenance.

Security fixes and action upgrades require explicit updates to the pinned SHA.

## Pinning Policy

An organization can define:

```text
Development
→ Approved major versions

Production
→ Approved immutable references
```

The important requirement is consistency.

A security-sensitive organization should not allow every repository to invent its own dependency trust model.

## Action Allowlisting

An enterprise can maintain an approved list:

```text
Approved
├── actions/checkout
├── actions/setup-python
├── actions/upload-artifact
├── docker/build-push-action
└── company/deploy-action
```

Unapproved actions may require review.

Allowlisting reduces the probability that an arbitrary Marketplace action gains access to sensitive workflows.

## Marketplace Restrictions

Organizations may restrict:

- Which actions repositories can use.
- Whether Marketplace actions are permitted.
- Whether actions must be pinned.
- Which repositories can access specific actions.
- Whether third-party actions require approval.

These controls are particularly important for:

- Production deployment repositories.
- Infrastructure repositories.
- Security-sensitive repositories.
- Organizations with private network access.

## Dependency Review

The action itself may have dependencies.

For a JavaScript action:

```text
Action
 ↓
package.json
 ↓
npm dependencies
 ↓
Transitive dependencies
```

For a Docker action:

```text
Action
 ↓
Dockerfile
 ↓
OS packages
 ↓
Language dependencies
```

Review dependency changes as part of action adoption and upgrades.

## Dependabot and Action Dependencies

Dependency update tooling can help identify outdated action dependencies and vulnerable packages.

For example:

```text
Third-Party Action
       ↓
Dependency Update
       ↓
Pull Request
       ↓
Tests
       ↓
Security Review
       ↓
Upgrade
```

Automated updates should still pass the organization's validation pipeline.

Do not blindly merge dependency updates into privileged deployment workflows.

## SBOM

A software bill of materials can provide visibility into dependencies used by an action or its image.

Conceptually:

```text
Marketplace Action
       ↓
Runtime Dependencies
       ↓
SBOM
       ↓
Security Analysis
```

For Docker actions, the SBOM can include:

- Base image packages.
- OS libraries.
- Python packages.
- Node packages.
- Other runtime dependencies.

This improves vulnerability response and supply-chain visibility.

## Provenance and Attestations

For internally built or repackaged CI/CD artifacts, provenance can establish how an artifact was produced.

A production supply-chain flow can be:

```text
Source
  ↓
Trusted Build
  ↓
Artifact
  ↓
SBOM
  ↓
Provenance
  ↓
Attestation
  ↓
Release
```

This becomes increasingly important when actions participate in production deployment pipelines.

## Marketplace Action Lifecycle

Treat adoption as a lifecycle:

```mermaid
flowchart LR
    A[Discover] --> B[Inspect Source]
    B --> C[Review Permissions]
    C --> D[Review Dependencies]
    D --> E[Choose Version]
    E --> F[Security Test]
    F --> G[Pilot]
    G --> H[Production]
    H --> I[Monitor]
    I --> J[Upgrade / Remove]
```

This is more reliable than adding an action directly to a production workflow after reading its README.

## Pilot Adoption

For a widely used action, test it in a limited environment first.

Example:

```text
Development
    ↓
Staging
    ↓
Pilot Repository
    ↓
Selected Production Repositories
    ↓
Organization-Wide Adoption
```

Monitor:

- Workflow failures.
- Runtime duration.
- Permission changes.
- Authentication behavior.
- Output changes.
- Artifact changes.
- Deployment behavior.

## Marketplace Actions in Python CI

A production Python workflow might use:

```yaml
name: Python CI

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

The workflow uses Marketplace actions for standardized infrastructure while keeping application-specific behavior in repository code.

## Django Example

A Django application may require PostgreSQL and Redis during integration testing.

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
          POSTGRES_DB: app_test
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: python manage.py migrate

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: pytest tests/integration
```

Marketplace actions handle standardized setup while service containers provide backend dependencies.

## FastAPI Example

A FastAPI pipeline can use Marketplace actions for environment setup and container operations:

```text
Pull Request
    ↓
Checkout
    ↓
Python Setup
    ↓
Dependency Installation
    ↓
pytest
    ↓
Coverage
    ↓
Docker Build
```

The application code remains independent from the Marketplace action implementation.

## Docker Marketplace Actions

A Docker-related workflow might use:

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: |
      ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ github.sha }}
```

Before using a Docker Marketplace action in production, evaluate:

- Docker privileges.
- Build context.
- Registry credentials.
- Build arguments.
- Cache configuration.
- Action version.
- Source code.
- Supply-chain implications.

## Docker Build Security

Be careful when a Marketplace action handles Docker builds.

A build can process:

- Dockerfiles.
- Build arguments.
- Repository files.
- Secrets.
- Base images.
- Registry credentials.

Do not pass secrets as ordinary Docker build arguments unless the design explicitly requires it and the mechanism is safe.

Prefer BuildKit-supported secret mechanisms when secrets are genuinely needed during a build.

## AWS Marketplace Actions

Marketplace actions may integrate with AWS services such as:

```text
IAM
STS
ECR
S3
ECS
EC2
Lambda
CloudFormation
```

The preferred authentication architecture is:

```mermaid
sequenceDiagram
    participant G as GitHub Actions
    participant O as GitHub OIDC
    participant S as AWS STS
    participant I as IAM Role
    participant A as AWS Service

    G->>O: Request OIDC identity token
    G->>S: AssumeRoleWithWebIdentity
    S->>I: Validate trust policy
    I-->>S: Temporary credentials
    S-->>G: Temporary credentials
    G->>A: API request
    A-->>G: Response
```

The action should receive only the permissions necessary for its operation.

## Marketplace Action and ECR

A container publishing workflow might be:

```text
GitHub Actions
      ↓
OIDC
      ↓
AWS STS
      ↓
IAM Role
      ↓
ECR Login
      ↓
Docker Build
      ↓
Image Push
```

The image should preferably use an immutable identifier:

```yaml
tags: |
  ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ github.sha }}
```

The deployment stage can then promote the same artifact.

## Marketplace Action and ECS

A deployment workflow may look like:

```text
Build
 ↓
ECR
 ↓
Staging ECS
 ↓
Health Validation
 ↓
Approval
 ↓
Production ECS
```

A Marketplace action can encapsulate one deployment operation, but the workflow should retain control over:

- Environment.
- Approval.
- Concurrency.
- IAM.
- Artifact identity.
- Health checks.
- Rollback.

## Production Pipeline

A mature pipeline may combine Marketplace actions with internal actions:

```mermaid
flowchart LR
    A[Pull Request] --> B[Checkout]
    B --> C[Python Setup]
    C --> D[Lint]
    D --> E[Matrix Tests]
    E --> F[Security Scan]
    F --> G[Docker Build]
    G --> H[ECR]
    H --> I[Staging]
    I --> J[Approval]
    J --> K[Production]
    K --> L[Health Validation]
    L --> M[Rollback]
```

Marketplace actions may provide standardized building blocks, while internal actions provide organization-specific controls.

## Build Once, Promote the Same Artifact

Do not rebuild an application for every environment.

Prefer:

```text
Source
  ↓
Build
  ↓
Immutable Image
  ↓
ECR
  ↓
Staging
  ↓
Approval
  ↓
Production
```

rather than:

```text
Source
 ├── Build Staging
 └── Build Production
```

The second approach can produce different artifacts from the same source.

Marketplace actions should participate in an immutable artifact strategy rather than encouraging environment-specific rebuilds.

## Marketplace Actions and Concurrency

A Marketplace deployment action does not automatically prevent two deployments from running simultaneously.

Use workflow concurrency:

```yaml
concurrency:
  group: production-backend
  cancel-in-progress: false
```

This separates:

```text
Action
→ Performs deployment

Concurrency
→ Coordinates deployments
```

Both are required for safe production orchestration.

## Environment Protection

Production deployment should use GitHub environments where appropriate:

```yaml
jobs:
  deploy:
    environment: production
```

The environment can provide:

- Required reviewers.
- Environment secrets.
- Deployment restrictions.
- Deployment history.

A Marketplace action should not be allowed to bypass these controls through workflow design.

## Monitoring Marketplace Actions

Monitor action behavior just like any other CI/CD dependency.

Useful metrics include:

- Workflow failure rate.
- Execution duration.
- Retry frequency.
- Authentication failures.
- Deployment failures.
- Rate-limit errors.
- Artifact failures.
- Runner failures.

For internal platform actions, track adoption by version:

```text
deploy-action
├── v1 → 72 repositories
├── v2 → 24 repositories
└── migration pending → 4 repositories
```

This makes upgrades manageable.

## Cost Considerations

Marketplace actions can affect CI cost indirectly through execution time.

Potential contributors include:

- Large Docker images.
- Repeated dependency installation.
- Inefficient API polling.
- Duplicate scans.
- Excessive artifact transfers.
- Poor caching.
- Long-running security analysis.

Measure workflow duration before and after introducing an action.

A convenient action is not automatically a cost-efficient action.

## Reliability

A Marketplace action may depend on external systems.

Possible failure domains include:

```text
Workflow
 ↓
Runner
 ↓
Action
 ↓
External API
 ↓
Cloud Service
```

Examples:

- GitHub API rate limits.
- AWS API failures.
- Registry outages.
- External security scanner failures.
- Network failures.

Design workflows with:

- Explicit timeouts.
- Safe retries.
- Idempotent operations.
- Clear failure handling.
- Rollback procedures.

Do not retry non-idempotent deployment operations blindly.

## High Availability

For critical CI/CD systems, avoid making a single third-party action the only mechanism capable of deploying production.

Maintain operational recovery options such as:

```text
Primary Deployment Action
        ↓
Known-good version
        ↓
Alternative controlled deployment path
```

The fallback should be tested rather than documented only as an emergency procedure.

## Disaster Recovery

For critical actions, maintain enough information to reproduce or replace the dependency.

Record:

- Action name.
- Version.
- Commit SHA.
- Repository.
- Required permissions.
- Required secrets.
- Runtime.
- Configuration.
- Consumer workflows.

For high-value deployment actions, document the rollback version.

## Action Removal

An action should be removed when:

- It is abandoned.
- It has an unacceptable security issue.
- It requires excessive permissions.
- A trusted internal alternative exists.
- Its behavior is no longer compatible.
- Its dependencies are no longer supportable.

Migration should follow:

```text
Current Action
      ↓
Replacement Validation
      ↓
Pilot
      ↓
Consumer Migration
      ↓
Monitoring
      ↓
Old Action Removal
```

Do not remove a shared action without identifying its consumers.

## Troubleshooting

Use the general model:

```text
Symptom
→ Possible Causes
→ Isolation Strategy
→ Commands / Checks
→ Root Cause
→ Corrective Action
→ Prevention
```

### Marketplace Action Cannot Be Resolved

Check:

- Repository name.
- Action path.
- Version reference.
- Repository visibility.
- Tag existence.
- Access permissions.

Example:

```yaml
uses: owner/repository@v1
```

Verify that `v1` actually exists.

### Action Suddenly Behaves Differently

Check:

```text
Action reference
      ↓
Resolved version
      ↓
Recent release
      ↓
Dependency changes
      ↓
Runtime changes
```

A mutable major tag may have advanced to a new compatible release.

### Action Fails After SHA Pinning

Possible causes:

- SHA is incorrect.
- Commit does not contain the expected action.
- Action release was not built correctly.
- The pinned commit contains a bug.
- Required runtime changed.

Compare the pinned SHA against the known-good release.

### Permission Denied

Check:

```yaml
permissions:
  contents: read
```

and any other permissions required by the action.

Do not immediately change to:

```yaml
permissions: write-all
```

Instead identify the exact missing permission.

### Secret Is Missing

Check:

- Repository secret.
- Organization secret.
- Environment secret.
- Workflow environment.
- Secret access policy.
- Fork PR restrictions.

Do not solve a secret-scope problem by copying production credentials into repository-level secrets.

### AWS Authentication Fails

Check:

```text
id-token: write
      ↓
OIDC token
      ↓
IAM trust policy
      ↓
Role ARN
      ↓
Temporary credentials
```

Validate repository, branch, tag, or environment conditions in the IAM trust policy.

### Third-Party Action Has Excessive Permissions

Reduce:

```yaml
permissions:
```

to the minimum required.

If the action genuinely requires broad access, reassess whether:

- It should be used.
- An internal alternative should be created.
- The workflow should isolate it into a separate job.
- The operation can be redesigned.

### Action Fails Only on Fork PRs

Check:

- Event type.
- Secret availability.
- `GITHUB_TOKEN` permissions.
- Repository write permissions.
- `pull_request_target`.
- Untrusted code execution.

Do not expose privileged credentials merely to make fork PR CI pass.

### Docker Action Cannot Access Repository Files

Check:

- `$GITHUB_WORKSPACE`.
- Container working directory.
- Action runtime.
- Volume/workspace behavior.
- Relative paths.

The container's `/app` directory is not automatically the repository root.

### Action Becomes Slow

Measure:

```text
Startup
 ↓
Dependency installation
 ↓
API requests
 ↓
Polling
 ↓
External service
```

Determine the actual bottleneck before replacing or redesigning the action.

## GitHub CLI Operations

List workflow runs:

```bash
gh run list
```

Inspect a run:

```bash
gh run view <run-id>
```

View logs:

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

List releases:

```bash
gh release list
```

Inspect a release:

```bash
gh release view v1.2.3
```

Create a release:

```bash
gh release create v1.2.3 --generate-notes
```

These commands are useful for diagnosing action behavior and managing releases around CI/CD operations.

## Governance

Marketplace actions should be governed at the organization or enterprise level.

Useful controls include:

- Approved action sources.
- Action allowlists.
- SHA-pinning policy.
- Permission standards.
- Secret-handling standards.
- Dependency review.
- Security review.
- Release monitoring.
- Runner restrictions.
- Production workflow restrictions.

A practical governance model is:

```text
Developer
   ↓
Approved Action
   ↓
Version Policy
   ↓
Permission Review
   ↓
Security Controls
   ↓
Production Workflow
```

## Enterprise Marketplace Strategy

For a large organization:

```text
Marketplace
    ↓
Security Review
    ↓
Approved Catalog
    ↓
Reusable Workflow / Internal Wrapper
    ↓
Repository Consumers
```

An internal wrapper can provide an abstraction around a third-party action.

For example:

```text
Repositories
      ↓
Company Docker Build Action
      ↓
Approved Marketplace Action
      ↓
Docker Registry
```

This lets the platform team control the consumer-facing interface even if the underlying implementation is third-party.

## Internal Wrapper Actions

An internal wrapper can standardize:

- Permissions.
- Inputs.
- Outputs.
- Logging.
- Security checks.
- Versioning.
- Configuration.

Example:

```yaml
- name: Build application image
  uses: company/docker-build@v2
  with:
    image-name: backend-api
    image-tag: ${{ github.sha }}
```

The internal action may internally use a trusted Marketplace action.

This reduces direct dependency sprawl across repositories.

## Dependency Sprawl

A repository containing:

```yaml
- uses: action-a@v1
- uses: action-b@v2
- uses: action-c@main
- uses: action-d@v3
- uses: action-e@v1
```

has several external trust relationships.

Centralizing common capabilities through reusable workflows or internal actions can reduce this surface:

```text
Repository
    ↓
Reusable Workflow
    ↓
Approved Actions
```

This improves:

- Governance.
- Security.
- Maintainability.
- Upgrade management.
- Auditability.

## Marketplace Actions and Reusable Workflows

Reusable workflows can provide a higher-level abstraction:

```text
Repository
   ↓
Reusable CI Workflow
   ├── Checkout Action
   ├── Python Setup Action
   ├── Test
   └── Security Action
```

The repository consumer does not need to manage every Marketplace dependency directly.

This allows the platform team to upgrade underlying actions centrally while preserving the workflow interface.

## Marketplace Actions and Custom Actions

Use a Marketplace action when the capability is sufficiently generic and trusted.

Use an internal action when the capability represents organizational policy or infrastructure.

Use a reusable workflow when the requirement involves multiple jobs and orchestration.

```text
Marketplace Action
→ Reusable capability

Internal Action
→ Organization-specific capability

Reusable Workflow
→ Multi-job pipeline orchestration
```

These mechanisms complement each other.

## Production Architecture

A scalable enterprise CI/CD architecture may look like:

```mermaid
flowchart TD
    A[Application Repository] --> B[Reusable CI Workflow]

    B --> C[Approved Marketplace Actions]
    B --> D[Internal Custom Actions]

    C --> E[Checkout]
    C --> F[Python / Node Setup]
    C --> G[Docker Build]

    D --> H[Security Policy]
    D --> I[Deployment]

    G --> J[ECR]
    I --> K[AWS]

    B --> L[Environment Protection]
    B --> M[Concurrency]

    K --> N[Staging]
    N --> O[Approval]
    O --> P[Production]

    P --> Q[Health Validation]
    Q --> R[Rollback]
```

The architecture separates:

```text
Application Logic
        ↓
Pipeline Orchestration
        ↓
Approved Actions
        ↓
Infrastructure
```

## Security Review Checklist

Before approving a Marketplace action:

- [ ] Source repository has been reviewed.
- [ ] Action type is understood.
- [ ] `action.yml` has been inspected.
- [ ] Required permissions are understood.
- [ ] Secrets are identified.
- [ ] External network access is understood.
- [ ] Dependencies are reviewed.
- [ ] Dockerfile has been reviewed if applicable.
- [ ] Runtime dependencies are known.
- [ ] Release/versioning strategy is understood.
- [ ] Mutable branch references are avoided.
- [ ] SHA pinning policy is followed where required.
- [ ] Fork PR behavior is understood.
- [ ] `pull_request_target` implications are reviewed.
- [ ] Self-hosted runner exposure is considered.
- [ ] AWS OIDC trust is restricted if applicable.
- [ ] Security scanning has been performed where appropriate.
- [ ] Action is included in the approved-action policy.
- [ ] Rollback or replacement strategy exists.

## Production Checklist

Before using a Marketplace action in a production pipeline:

- [ ] Action purpose is clearly defined.
- [ ] Source is trusted.
- [ ] Version is explicitly selected.
- [ ] Required permissions are minimized.
- [ ] Secrets are minimized.
- [ ] OIDC is preferred over long-lived cloud credentials where supported.
- [ ] Inputs are validated.
- [ ] Outputs are understood.
- [ ] Dependencies are reviewed.
- [ ] Action is tested in a non-production environment.
- [ ] Failure behavior is understood.
- [ ] Timeouts and retries are appropriate.
- [ ] Deployment concurrency is configured where necessary.
- [ ] Environment protection is configured.
- [ ] Immutable application artifacts are used.
- [ ] Monitoring exists for important production workflows.
- [ ] Rollback is tested.
- [ ] Action upgrades have a defined process.
- [ ] Organization governance requirements are satisfied.

## Interview Scenarios

### Evaluate a Marketplace Action

A developer wants to add:

```yaml
uses: third-party/deploy-action@v1
```

to a production workflow.

Explain how you would evaluate:

- Source trust.
- Versioning.
- Permissions.
- Secrets.
- Dependencies.
- Runtime.
- Security history.
- SHA pinning.
- Runner type.
- Rollback.

### Third-Party Action Requires `contents: write`

The action only appears to publish a deployment status.

Discuss:

```text
Does it really need write access?
        ↓
Inspect implementation
        ↓
Identify API calls
        ↓
Reduce permissions
        ↓
Test
```

Do not grant broad permissions without establishing the requirement.

### Marketplace Action Uses AWS Credentials

A deployment action requests:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

Design a safer architecture using:

```text
GitHub OIDC
    ↓
AWS STS
    ↓
IAM Role
    ↓
Temporary Credentials
```

Discuss:

- IAM trust policy.
- Repository conditions.
- Environment conditions.
- Least privilege.
- Credential lifetime.

### Fork PR Security

A repository uses:

```yaml
pull_request_target:
```

and executes a Marketplace action against the pull request source.

Identify the security boundary and explain how untrusted code could interact with privileged workflow context.

### Action Version Upgrade

A Marketplace action moves from:

```yaml
uses: third-party/action@v1
```

to:

```yaml
uses: third-party/action@v2
```

Explain how you would validate:

- Breaking changes.
- Permission changes.
- Runtime changes.
- Output changes.
- Dependency changes.
- Security changes.
- Production compatibility.

### Design an Enterprise Action Policy

An organization has 300 repositories and wants centralized control over Marketplace actions.

Design:

```text
Approved Catalog
      ↓
Reusable Workflows
      ↓
Internal Actions
      ↓
Repository Consumers
```

Discuss:

- Allowlists.
- SHA pinning.
- Security review.
- Dependency updates.
- Version governance.
- Exception handling.
- Monitoring.
- Rollback.

### Marketplace Action Compromise

A widely used third-party action is discovered to have a compromised release.

Design the response:

```text
Detection
   ↓
Block / Stop Adoption
   ↓
Identify Consumers
   ↓
Pin / Roll Back
   ↓
Rotate Exposed Credentials
   ↓
Investigate Logs
   ↓
Replace Action
   ↓
Prevent Recurrence
```

Consider the additional risk if the action had access to:

- Production secrets.
- `id-token: write`.
- Repository write permissions.
- Self-hosted runners.
- Private networks.

## Key Takeaways

- A Marketplace action is executable third-party code inside the CI/CD trust boundary, so evaluate its source, runtime, dependencies, permissions, secrets, and versioning before production use.
- Minimize `GITHUB_TOKEN` permissions and secrets, prefer OIDC for AWS authentication where appropriate, and treat `pull_request_target` plus untrusted code as a particularly sensitive security boundary.
- Use controlled version references and SHA pinning where required; avoid mutable branch references for security-sensitive production workflows.
- Enterprise environments should govern Marketplace actions through approved catalogs, allowlists, reusable workflows, internal wrappers, dependency review, and consistent security standards.
- Marketplace actions should remain replaceable CI/CD dependencies: test upgrades, monitor behavior, use immutable application artifacts, and maintain rollback or migration paths for critical production workflows.