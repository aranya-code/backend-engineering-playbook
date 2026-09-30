# 04- Reusable Workflow Architecture

## Overview

Reusable workflows are a GitHub Actions mechanism for packaging an entire workflow interface so that multiple repositories or workflows can invoke the same CI/CD process.

They are most valuable when an organization has repeated pipeline architecture such as:

```text
Repository A ─┐
Repository B ─┼──→ Shared CI Workflow
Repository C ─┘
```

Instead of copying the same workflow logic into every repository, the common pipeline becomes a reusable workflow.

A production reusable workflow should be treated as a versioned platform API rather than a YAML snippet.

A useful architectural model is:

```text
Application Repository
        ↓
Workflow Caller
        ↓
Reusable Workflow
        ↓
┌────────┬────────┬──────────┐
│ Lint   │ Tests  │ Security │
└────────┴────────┴──────────┘
        ↓
     Build
        ↓
   Artifact
```

Reusable workflows are especially useful for:

- Standardized Python CI.
- Docker image builds.
- Security validation.
- AWS deployments.
- Environment promotion.
- Organization-wide compliance.
- Common release workflows.
- Multi-repository platform engineering.

The key design objective is **centralized implementation with explicit contracts**.

---

## Reusable Workflow vs Normal Workflow

A normal workflow is generally invoked by an event:

```yaml
on:
  pull_request:
```

A reusable workflow is invoked by another workflow:

```yaml
on:
  workflow_call:
```

Example:

```yaml
name: Reusable Python CI

on:
  workflow_call:
```

Caller:

```yaml
jobs:
  ci:
    uses: organization/platform/.github/workflows/python-ci.yml@v1
```

The caller provides the invocation context.

The reusable workflow owns the implementation.

---

## Why Reusable Workflows Exist

Without reuse, multiple repositories may contain nearly identical pipelines:

```text
orders/.github/workflows/ci.yml
payments/.github/workflows/ci.yml
users/.github/workflows/ci.yml
```

Over time they can drift:

```text
Orders     → Python 3.12
Payments   → Python 3.11
Users      → Different security scan
Inventory  → Different cache strategy
```

This creates:

- Maintenance duplication.
- Security inconsistency.
- Different CI behavior.
- Difficult platform-wide changes.
- Higher operational overhead.

Reusable workflows centralize common pipeline behavior.

---

## When to Use Reusable Workflows

Use a reusable workflow when multiple repositories share a **pipeline-level pattern**.

Good examples:

```text
Python CI
Docker Build and Publish
Terraform Validation
AWS Deployment
Production Deployment
Security Validation
Release Workflow
```

Avoid creating a reusable workflow merely because two workflows share two or three steps.

For step-level reuse, a composite action may be a better abstraction.

---

## Reusable Workflow vs Composite Action

This distinction is fundamental.

| Capability | Reusable Workflow | Composite Action |
|---|---|---|
| Reuse unit | Workflow | Steps |
| Multiple jobs | Yes | No |
| `workflow_call` | Yes | No |
| Job orchestration | Yes | No |
| Matrix orchestration | Yes | No |
| Environments | Yes | Not as a workflow boundary |
| Job-level permissions | Yes | Caller controls job |
| Deployment pipeline | Good fit | Usually not |
| Common setup sequence | Possible | Good fit |
| Cross-repository reuse | Yes | Yes |
| Pipeline API | Yes | Action API |

Think of the distinction as:

```text
Composite Action
    = reusable implementation inside a job

Reusable Workflow
    = reusable pipeline containing jobs
```

A reusable workflow can call actions, including composite actions.

---

## Reusable Workflow Architecture

A reusable workflow has three primary layers:

```text
Caller
  ↓
Workflow Contract
  ↓
Workflow Implementation
```

The contract consists primarily of:

- Inputs.
- Secrets.
- Permissions.
- Outputs.
- Environment behavior.
- Version.

Example:

```yaml
name: Reusable Python CI

on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string

      run-integration-tests:
        required: false
        type: boolean
        default: true

    secrets:
      private-pypi-token:
        required: false

    outputs:
      test-result:
        description: "CI result"
        value: ${{ jobs.test.outputs.result }}
```

The implementation follows below the contract.

---

## `workflow_call`

`workflow_call` makes a workflow callable by another workflow.

Example:

```yaml
on:
  workflow_call:
```

A reusable workflow can define:

- Inputs.
- Secrets.
- Outputs.

Example:

```yaml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string

      deploy:
        required: false
        type: boolean
        default: false

    secrets:
      deployment-token:
        required: true
```

This creates an explicit interface.

---

## Input Types

Reusable workflow inputs should use appropriate types.

Supported input types include:

- `string`
- `boolean`
- `number`

Example:

```yaml
on:
  workflow_call:
    inputs:
      python-version:
        type: string
        required: true

      run-integration-tests:
        type: boolean
        required: false
        default: true

      worker-count:
        type: number
        required: false
        default: 2
```

Typed inputs are preferable to encoding everything as strings.

---

## Required and Optional Inputs

Use required inputs for values necessary to execute the workflow.

```yaml
inputs:
  service-name:
    required: true
    type: string
```

Use optional inputs when there is a safe and sensible default.

```yaml
inputs:
  coverage:
    required: false
    type: boolean
    default: true
```

Avoid excessive configurability.

A reusable workflow with dozens of switches becomes difficult to understand and maintain.

---

## Input Validation

GitHub Actions provides input typing, but complex business validation may still be necessary.

Example:

```yaml
- name: Validate environment
  env:
    ENVIRONMENT: ${{ inputs.environment }}
  run: |
    case "$ENVIRONMENT" in
      staging|production)
        ;;
      *)
        echo "Unsupported environment: $ENVIRONMENT"
        exit 1
        ;;
    esac
```

Allowlist values when the input affects deployment behavior.

---

## Inputs as API Design

Treat workflow inputs like a function signature.

Good:

```text
environment
service
python-version
run-integration-tests
```

Risky:

```text
run-step-1
run-step-2
skip-step-3
enable-special-mode
legacy-mode
debug-mode
```

The latter exposes implementation details rather than a stable abstraction.

A reusable workflow should expose **intent**, not internal mechanics.

---

## Secrets

Reusable workflows can declare secrets explicitly.

```yaml
on:
  workflow_call:
    secrets:
      private-pypi-token:
        required: false
```

Caller:

```yaml
jobs:
  ci:
    uses: organization/platform/.github/workflows/python-ci.yml@v1
    secrets:
      private-pypi-token: ${{ secrets.PRIVATE_PYPI_TOKEN }}
```

The reusable workflow should consume only the secrets it actually needs.

---

## `secrets: inherit`

For workflows within appropriate repository/organization boundaries, callers may use:

```yaml
jobs:
  ci:
    uses: organization/platform/.github/workflows/python-ci.yml@v1
    secrets: inherit
```

This is convenient but broad.

Prefer explicit secret contracts when practical:

```yaml
secrets:
  private-pypi-token: ${{ secrets.PRIVATE_PYPI_TOKEN }}
```

Explicit contracts make dependencies easier to audit.

---

## Secret Design

A reusable workflow should not silently depend on repository secrets that are undocumented.

Bad abstraction:

```text
Reusable Workflow
     ↓
Assumes SECRET_A exists
     ↓
Fails in consumer repository
```

Better:

```text
Reusable Workflow
     ↓
Declares secret contract
     ↓
Caller supplies secret
```

This makes the workflow portable and predictable.

---

## Workflow Outputs

Reusable workflows can expose outputs to callers.

Example:

```yaml
on:
  workflow_call:
    outputs:
      image:
        description: "Built image"
        value: ${{ jobs.build.outputs.image }}
```

The job must define its output:

```yaml
jobs:
  build:
    outputs:
      image: ${{ steps.build.outputs.image }}

    steps:
      - id: build
        run: |
          echo "image=123456789.dkr.ecr.us-east-1.amazonaws.com/orders:${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
```

Caller:

```yaml
jobs:
  build:
    uses: organization/platform/.github/workflows/build.yml@v1

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ needs.build.outputs.image }}"
```

The data flow is:

```text
Step Output
    ↓
Job Output
    ↓
Reusable Workflow Output
    ↓
Caller Job
```

---

## Structured Workflow Outputs

JSON is useful when a reusable workflow needs to return structured data.

Example:

```yaml
- id: metadata
  run: |
    echo 'result={"image":"orders-api","environment":"staging"}' >> "$GITHUB_OUTPUT"
```

The caller can consume the output using:

```yaml
${{ fromJSON(needs.build.outputs.result).image }}
```

Structured outputs can support dynamic deployment decisions and matrices.

---

## Dynamic Matrix Through Reusable Workflows

A reusable workflow can generate information consumed by the caller.

```text
Reusable Workflow
       ↓
JSON Output
       ↓
Caller
       ↓
Dynamic Matrix
```

Example:

```yaml
jobs:
  plan:
    uses: organization/platform/.github/workflows/plan.yml@v1

  test:
    needs: plan
    strategy:
      matrix:
        service: ${{ fromJSON(needs.plan.outputs.services) }}
```

This pattern is useful for monorepos and service-oriented repositories.

---

## Reusable CI Workflow

A standardized Python CI workflow can provide:

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
Integration Tests
 ↓
Coverage
 ↓
Security
```

Caller:

```yaml
name: CI

on:
  pull_request:

jobs:
  ci:
    uses: organization/platform/.github/workflows/python-ci.yml@v1
    with:
      python-version: "3.12"
      run-integration-tests: true
```

The application repository remains small while the platform team maintains the implementation.

---

## Python CI Example

Reusable workflow:

```yaml
name: Reusable Python CI

on:
  workflow_call:
    inputs:
      python-version:
        required: false
        type: string
        default: "3.12"

      run-integration-tests:
        required: false
        type: boolean
        default: true

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v6
        with:
          python-version: ${{ inputs.python-version }}
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Lint
        run: ruff check .

      - name: Unit tests
        run: pytest tests/unit

      - name: Integration tests
        if: inputs.run-integration-tests
        run: pytest tests/integration
```

Caller:

```yaml
name: CI

on:
  pull_request:

jobs:
  ci:
    uses: organization/platform/.github/workflows/python-ci.yml@v1
    with:
      python-version: "3.12"
      run-integration-tests: true
```

---

## Django Reusable CI Architecture

For Django services, the reusable workflow can standardize:

```text
Python
 ↓
Dependencies
 ↓
Django Checks
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

The reusable workflow can own the infrastructure setup while the caller provides application-specific configuration.

---

## FastAPI Reusable CI Architecture

A FastAPI reusable workflow can standardize:

```text
Python
 ↓
Dependencies
 ↓
Lint / Type Checks
 ↓
PostgreSQL
 ↓
Redis
 ↓
pytest
 ↓
API Tests
 ↓
Coverage
```

The same workflow can support multiple FastAPI repositories through inputs.

---

## Reusable Integration Testing

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

The reusable workflow should document whether:

- Service containers are always enabled.
- They are controlled by inputs.
- Applications must provide their own setup.
- Additional services are supported.

---

## Reusable Docker Build Workflow

A common reusable Docker workflow can own:

```text
Buildx
 ↓
Cache
 ↓
Build
 ↓
Scan
 ↓
SBOM
 ↓
Push
 ↓
Output Digest
```

Example caller:

```yaml
jobs:
  build:
    uses: organization/platform/.github/workflows/docker-build.yml@v1
    with:
      image-name: orders-api
      push: true
```

The reusable workflow can expose:

```text
image
digest
registry
```

as outputs.

---

## Build Once, Deploy Many With Reusable Workflows

A reusable architecture can separate build and deployment:

```text
Reusable Build Workflow
        ↓
Immutable Image
        ↓
Reusable Staging Workflow
        ↓
Reusable Production Workflow
```

Caller:

```yaml
jobs:
  build:
    uses: organization/platform/.github/workflows/docker-build.yml@v1

  staging:
    needs: build
    uses: organization/platform/.github/workflows/deploy.yml@v1
    with:
      environment: staging
      image: ${{ needs.build.outputs.image }}

  production:
    needs: staging
    uses: organization/platform/.github/workflows/deploy.yml@v1
    with:
      environment: production
      image: ${{ needs.build.outputs.image }}
```

The production job should use the same artifact identity.

---

## Reusable AWS Deployment Workflow

A reusable AWS deployment workflow can standardize:

```text
GitHub OIDC
    ↓
AWS STS
    ↓
IAM Role
    ↓
ECR / ECS / EC2 / Lambda
```

Caller:

```yaml
jobs:
  deploy:
    uses: organization/platform/.github/workflows/aws-deploy.yml@v1
    with:
      environment: staging
      image: ${{ needs.build.outputs.image }}
    secrets: inherit
```

The deployment workflow should not require long-lived AWS access keys as a default design.

---

## AWS OIDC Permissions

A deployment job commonly requires:

```yaml
permissions:
  contents: read
  id-token: write
```

The reusable workflow should declare the permissions required by its jobs.

Avoid giving every reusable workflow broad permissions simply because one deployment workflow needs OIDC.

---

## Reusable Workflow and Permissions

Permissions are part of the workflow security contract.

Example:

```yaml
jobs:
  test:
    permissions:
      contents: read

  deploy:
    permissions:
      contents: read
      id-token: write
```

A reusable workflow should minimize privileges independently for each job.

This is especially important when the workflow is shared by many repositories.

---

## Reusable Workflow and Environments

Deployment workflows may use GitHub Environments:

```yaml
jobs:
  deploy:
    environment:
      name: production
```

This allows production policy to remain at the environment boundary.

For example:

```text
Reusable Deployment Workflow
          ↓
Production Environment
          ↓
Required Reviewer
          ↓
Production Secrets
```

The reusable workflow owns deployment mechanics.

The environment owns production protection.

---

## Environment Inputs

A reusable deployment workflow may accept:

```yaml
inputs:
  environment:
    required: true
    type: string
```

Validate environment values before using them.

```yaml
- name: Validate environment
  env:
    ENVIRONMENT: ${{ inputs.environment }}
  run: |
    case "$ENVIRONMENT" in
      staging|production)
        ;;
      *)
        echo "Invalid environment"
        exit 1
        ;;
    esac
```

Do not allow arbitrary input values to silently select sensitive infrastructure.

---

## Reusable Workflow and Concurrency

Deployment concurrency should normally belong to the deployment workflow.

```yaml
concurrency:
  group: deployment-${{ inputs.environment }}
  cancel-in-progress: false
```

This prevents:

```text
Production Deployment A
        +
Production Deployment B
        ↓
Race Condition
```

For pull request CI, a different policy may be appropriate:

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

---

## Fan-Out Architecture With Reusable Workflows

A caller can invoke multiple reusable workflows:

```text
                 ┌── Python CI
                 │
Pull Request ────┼── Security
                 │
                 └── Documentation Checks
```

Or a reusable workflow can internally fan out:

```text
Reusable CI
    ↓
┌───┼────┬──────┐
Lint Unit Security Integration
└───┼────┴──────┘
        ↓
    Quality Gate
```

The choice depends on where orchestration responsibility belongs.

---

## Fan-In Architecture

A caller can aggregate reusable workflow results:

```yaml
jobs:
  ci:
    uses: organization/platform/.github/workflows/ci.yml@v1

  security:
    uses: organization/platform/.github/workflows/security.yml@v1

  release:
    needs:
      - ci
      - security
    uses: organization/platform/.github/workflows/release.yml@v1
```

This creates a clear dependency graph.

---

## Cross-Repository Reusable Workflows

A centralized platform repository can provide workflows:

```text
organization/
    platform/
        .github/
            workflows/
                python-ci.yml
                docker-build.yml
                aws-deploy.yml
```

Consumer repositories call them:

```yaml
jobs:
  ci:
    uses: organization/platform/.github/workflows/python-ci.yml@v1
```

This is useful for enterprise standardization.

---

## Versioning Reusable Workflows

A reusable workflow is a dependency.

Avoid consumers depending on an uncontrolled moving reference when stability matters.

Possible strategies include:

```text
@v1
@v1.2.0
@<commit-sha>
```

A practical model is:

```text
v1
 ↓
Backward-compatible changes

v2
 ↓
Breaking contract changes
```

The exact versioning policy should be defined by the organization.

---

## Versioning Trade-Offs

| Reference | Convenience | Stability | Update control |
|---|---:|---:|---:|
| Branch | High | Low | Low |
| Major tag | High | Medium | Medium |
| Exact version tag | Medium | High | High |
| Commit SHA | Lower | Highest | Highest |

For sensitive enterprise workflows, stronger version pinning can reduce unexpected behavior.

---

## Breaking Changes

A reusable workflow can break many repositories at once.

Example:

```text
Platform Workflow v1
        ↓
50 Repositories
```

Changing:

```yaml
inputs:
  python-version:
```

to:

```yaml
inputs:
  runtime-version:
```

without compatibility planning can break all consumers.

Therefore reusable workflow APIs require backward compatibility discipline.

---

## Contract Stability

Treat these as public API elements:

- Workflow path.
- Input names.
- Input types.
- Defaults.
- Secret names.
- Output names.
- Output meanings.
- Expected permissions.
- Artifact formats.
- Deployment behavior.

Implementation details should remain private.

---

## Reusable Workflow Documentation

A reusable workflow should document:

```text
Purpose
Inputs
Defaults
Secrets
Outputs
Permissions
Environments
Supported repositories
Versioning
Failure behavior
Examples
```

Example:

```markdown
## Inputs

| Input | Type | Required | Default |
|---|---|---:|---|
| python-version | string | No | 3.12 |
| integration-tests | boolean | No | true |
| environment | string | Yes | - |
```

This makes the workflow discoverable as an internal platform API.

---

## Reusable Workflow Repository Structure

A platform repository may use:

```text
.github/
    workflows/
        python-ci.yml
        docker-build.yml
        security.yml
        aws-deploy.yml
        release.yml

actions/
    setup-python/
    docker-metadata/

docs/
    workflows/
```

Keep reusable workflows focused.

Do not turn one workflow into an entire internal platform implementation.

---

## Workflow Responsibilities

A good boundary might be:

```text
python-ci.yml
    → Python validation

docker-build.yml
    → Container build

security.yml
    → Security validation

aws-deploy.yml
    → Deployment

release.yml
    → Release management
```

Avoid:

```text
everything.yml
```

containing every CI/CD concern.

---

## Reusable Workflow and Composite Action Composition

Reusable workflows and composite actions can be layered.

```text
Reusable Workflow
      ↓
Composite Action
      ↓
Reusable Steps
```

Example:

```text
python-ci.yml
    ↓
setup-python-environment
    ↓
Install
Cache
Configure
```

This allows pipeline-level and step-level reuse simultaneously.

---

## Reusable Workflow Security Boundary

A shared workflow can become a high-value target.

If compromised:

```text
Reusable Workflow
       ↓
Many Repositories
       ↓
Many Credentials
```

Therefore:

- Protect the repository.
- Require code review.
- Restrict who can modify workflows.
- Use CODEOWNERS where appropriate.
- Pin dependencies.
- Minimize permissions.
- Review workflow changes as production code.
- Version releases carefully.

---

## Third-Party Actions Inside Reusable Workflows

A reusable workflow can centralize third-party actions.

This creates a dependency chain:

```text
Consumer Repository
        ↓
Reusable Workflow
        ↓
Third-Party Action
        ↓
Action Dependencies
```

The platform team therefore becomes responsible for validating those dependencies.

Use trusted sources and appropriate pinning.

---

## Untrusted Pull Requests

A reusable workflow should not automatically turn an untrusted pull request into a privileged execution context.

Risky architecture:

```text
Fork PR
 ↓
Reusable Workflow
 ↓
Production Secrets
 ↓
Self-Hosted Runner
```

Safer architecture:

```text
Fork PR
 ↓
Read-only validation
 ↓
GitHub-hosted / isolated runner
```

Deployment should occur only after an appropriate trust boundary has been crossed.

---

## Reusable Workflow and `pull_request_target`

Particular caution is required when a reusable workflow is invoked from a `pull_request_target` workflow.

Do not combine:

```text
Untrusted PR Code
+
Privileged Workflow
+
Secrets
+
Production Network
```

without a deliberate security architecture.

The workflow should never assume that because the workflow file is trusted, every piece of code it executes is trusted.

---

## Reusable Workflow and Outputs

Outputs are useful for:

```text
Build Metadata
Image Digest
Artifact Name
Version
Changed Services
Deployment Result
```

Example:

```yaml
outputs:
  image-digest:
    description: "Immutable Docker image digest"
    value: ${{ jobs.build.outputs.digest }}
```

The caller can then pass that exact digest to deployment.

---

## Artifact Promotion With Outputs

```text
Reusable Build
      ↓
Image Digest
      ↓
Caller
      ↓
Reusable Staging Deploy
      ↓
Reusable Production Deploy
```

Example:

```yaml
jobs:
  build:
    uses: organization/platform/.github/workflows/docker-build.yml@v1

  staging:
    needs: build
    uses: organization/platform/.github/workflows/deploy.yml@v1
    with:
      image-digest: ${{ needs.build.outputs.image-digest }}
      environment: staging

  production:
    needs: staging
    uses: organization/platform/.github/workflows/deploy.yml@v1
    with:
      image-digest: ${{ needs.build.outputs.image-digest }}
      environment: production
```

This is stronger than passing only a mutable tag.

---

## Reusable Workflow and Artifacts

Artifacts are appropriate for:

- Test reports.
- Coverage.
- Build packages.
- Debugging bundles.
- Deployment manifests.
- Logs.

Do not confuse workflow outputs with artifacts.

| Mechanism | Purpose |
|---|---|
| Step output | Small value between steps |
| Job output | Small value between jobs |
| Workflow output | Value exposed to caller |
| Artifact | Files transferred/stored |
| Cache | Reusable dependency/build data |

A Docker image should normally be stored in a registry rather than transferred as a generic workflow output.

---

## Reusable Workflow and Caching

Caching can be implemented centrally.

Example:

```yaml
- uses: actions/setup-python@v6
  with:
    python-version: ${{ inputs.python-version }}
    cache: pip
```

A shared workflow can standardize cache behavior.

However, cache correctness remains dependent on:

- Dependency lock files.
- Cache keys.
- Dependency scope.
- Runtime version.
- Architecture.

Caching must not be treated as an artifact or release mechanism.

---

## Reusable Workflow and Docker Cache

A reusable Docker workflow may standardize:

```yaml
with:
  cache-from: type=gha
  cache-to: type=gha,mode=max
```

The cache improves performance.

The image pushed to ECR remains the release artifact.

---

## Conditional Jobs

Reusable workflows can conditionally execute jobs based on inputs.

Example:

```yaml
jobs:
  integration:
    if: inputs.run-integration-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/integration
```

Be careful with conditionally skipped jobs and downstream `needs` dependencies.

A caller should understand whether a skipped job is considered acceptable for subsequent stages.

---

## Status Functions

Reusable workflows often need failure-aware reporting.

Examples:

```yaml
if: ${{ failure() }}
```

```yaml
if: ${{ cancelled() }}
```

```yaml
if: ${{ !cancelled() }}
```

Use status functions intentionally.

For example, uploading test reports after a test failure may require:

```yaml
- name: Upload test reports
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@v4
```

This differs from using `always()` indiscriminately.

---

## Cancellation Behavior

Cancellation should be part of workflow design.

For PR CI:

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

For production:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

A reusable deployment workflow should not assume that cancellation is harmless.

Deployment steps may have already changed infrastructure.

---

## Reusable Workflow Failure Isolation

A shared workflow should make failures easy to identify.

Good structure:

```text
Reusable CI
 ├── Lint
 ├── Unit Tests
 ├── Integration
 ├── Security
 └── Reports
```

Avoid hiding everything inside one opaque shell script.

The caller should still be able to understand:

```text
Which stage failed?
Why?
What evidence exists?
```

---

## Logging and Step Summaries

Reusable workflows should produce useful diagnostics.

Example:

```yaml
- name: Build summary
  run: |
    {
      echo "## Build"
      echo ""
      echo "- Image: $IMAGE"
      echo "- Commit: $GITHUB_SHA"
    } >> "$GITHUB_STEP_SUMMARY"
```

Do not print secrets.

Use step summaries for important human-readable execution information.

---

## Reusable Workflow Error Handling

A reusable workflow should fail clearly.

Avoid:

```bash
some-command || true
```

when the failure means the pipeline is invalid.

Use explicit validation:

```bash
set -euo pipefail
```

where appropriate in shell scripts.

A shared workflow should not hide application failures simply to make consumers appear successful.

---

## Reusable Workflow and Retries

Retries are appropriate for transient failures such as:

- Temporary network errors.
- Registry throttling.
- Cloud API throttling.

Do not retry deterministic failures such as:

- Invalid credentials.
- Broken tests.
- Invalid configuration.
- Compilation failures.
- Invalid Dockerfiles.

A shared workflow should use bounded retries with clear logging.

---

## Reusable Workflow and Idempotency

Deployment workflows should be safe to retry where practical.

```text
Desired State
    ↓
Apply
    ↓
Validated State
```

Avoid scripts that assume the previous deployment completed successfully.

Idempotency is especially important for:

- ECS deployments.
- Terraform.
- CloudFormation.
- Kubernetes.
- EC2 release directories.
- Database migration orchestration.

---

## Reusable Deployment Workflow

A production deployment workflow can have this structure:

```text
Reusable Deployment Workflow
        ↓
Validate Inputs
        ↓
Authenticate
        ↓
Resolve Immutable Artifact
        ↓
Deploy
        ↓
Wait for Readiness
        ↓
Health Check
        ↓
Report Result
```

The workflow should not rebuild application code.

---

## Production Deployment Contract

A deployment workflow might accept:

```yaml
inputs:
  environment:
    type: string
    required: true

  image-digest:
    type: string
    required: true

  service:
    type: string
    required: true
```

The contract expresses:

```text
Where?
What?
Which service?
```

rather than exposing internal deployment commands.

---

## Reusable Workflow Architecture for Microservices

For many services:

```text
             Platform Repository
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
     CI Workflow  Build      Deploy
        │         Workflow    Workflow
        │           │           │
        └───────────┼───────────┘
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
     Orders      Payments     Users
```

Each service keeps ownership of application-specific behavior while sharing platform mechanics.

---

## Reusable Workflow Architecture for a Monorepo

```text
Monorepo
 ├── orders/
 ├── payments/
 └── users/
       ↓
Planning Workflow
       ↓
Affected Services
       ↓
Reusable CI
       ↓
Reusable Build
       ↓
Reusable Deploy
```

This can reduce unnecessary CI execution while maintaining centralized platform behavior.

---

## Governance Model

An enterprise reusable workflow platform may define:

```text
Platform Team
    ↓
Workflow Contracts
    ↓
Versioned Releases
    ↓
Application Consumers
```

Governance should define:

- Ownership.
- Versioning.
- Review.
- Security.
- Deprecation.
- Consumer migration.
- Compatibility guarantees.
- Incident response.

---

## Ownership

Each reusable workflow should have an explicit owner.

Example:

| Workflow | Owner |
|---|---|
| Python CI | Backend Platform |
| Docker Build | Developer Platform |
| Security | Security Engineering |
| AWS Deploy | Cloud Platform |
| Release | Developer Platform |

Ownership prevents abandoned internal infrastructure.

---

## Change Management

A change to a reusable workflow can affect many repositories.

Before changing a production workflow:

```text
Change
 ↓
Identify Consumers
 ↓
Assess Compatibility
 ↓
Test
 ↓
Release New Version
 ↓
Migrate Consumers
 ↓
Deprecate Old Version
```

Avoid making breaking changes directly to a widely consumed stable version.

---

## Consumer Migration

A major version can be introduced:

```text
v1
 ↓
Existing consumers

v2
 ↓
New contract
```

Migration:

```text
Repository A → v2
Repository B → v1
Repository C → v1
```

This allows controlled adoption rather than organization-wide synchronized migration.

---

## Testing Reusable Workflows

Reusable workflows should be tested like platform code.

Test:

- Default inputs.
- Required inputs.
- Invalid inputs.
- Secrets.
- Permissions.
- Outputs.
- Matrix behavior.
- Failure paths.
- Cancellation.
- Deployment behavior.
- Version compatibility.

A reusable workflow should have representative consumer repositories or test fixtures.

---

## Contract Testing

Consumer compatibility should be tested explicitly.

For example:

```text
Reusable Workflow v1
       ↓
Consumer Fixture
       ↓
Expected Outputs
       ↓
Expected Artifacts
       ↓
Expected Deployment Behavior
```

This catches breaking changes before release.

---

## Integration Testing

A reusable AWS deployment workflow should be tested against an appropriate non-production environment.

Example:

```text
Reusable Workflow
       ↓
Test AWS Account
       ↓
ECR / ECS
       ↓
Health Validation
```

Avoid relying only on YAML syntax validation for deployment workflows.

---

## Security Testing

A shared workflow should be reviewed for:

- Excessive permissions.
- Secret exposure.
- Shell injection.
- Untrusted input.
- Third-party action risks.
- OIDC trust policy assumptions.
- Artifact integrity.
- Runner access.
- Container security.

A reusable workflow is part of the organization's CI/CD supply chain.

---

## Production Failure Scenario: Workflow Breaks Many Repositories

Suppose:

```text
python-ci.yml@v1
```

is used by 100 repositories.

A breaking change is introduced.

Potential impact:

```text
Workflow Change
      ↓
100 Consumers
      ↓
100 CI Failures
```

Prevention:

- Version workflows.
- Maintain backward compatibility.
- Test representative consumers.
- Use controlled releases.
- Monitor workflow failures after updates.

---

## Production Failure Scenario: Compromised Workflow

If a reusable workflow repository is compromised:

```text
Attacker
   ↓
Reusable Workflow
   ↓
Many Consumer Repositories
   ↓
Tokens / Secrets / AWS Roles
```

Mitigations include:

- Strong repository protection.
- CODEOWNERS.
- Required reviews.
- Least-privilege permissions.
- SHA pinning where appropriate.
- OIDC trust restrictions.
- Environment protection.
- Runner isolation.
- Audit logging.

---

## Production Failure Scenario: Deployment Race

Two repositories or workflows attempt production deployment:

```text
Deployment A ────────┐
                     ├── Production
Deployment B ────────┘
```

Without coordination, the final state may depend on timing.

Use:

```yaml
concurrency:
  group: production-${{ inputs.service }}
  cancel-in-progress: false
```

The concurrency key should match the actual resource being protected.

---

## Production Failure Scenario: Wrong Artifact

A deployment workflow receives:

```text
orders-api:latest
```

The tag may have changed since the build.

Prefer:

```text
orders-api@sha256:<digest>
```

The reusable workflow should validate that the artifact exists before deployment.

---

## Production Failure Scenario: Secret Missing

A consumer invokes:

```yaml
uses: organization/platform/.github/workflows/deploy.yml@v1
```

but does not provide a required secret.

The workflow should expose a clear contract:

```yaml
secrets:
  deployment-secret:
    required: true
```

Do not let the failure appear later as an unrelated authentication error.

---

## Production Failure Scenario: AWS Role Assumption Fails

Debug:

```bash
aws sts get-caller-identity
```

Check:

```text
id-token: write
        ↓
OIDC token
        ↓
IAM trust policy
        ↓
Repository / branch / environment claims
        ↓
STS
```

The reusable workflow should document the required AWS trust relationship.

---

## Reusable Workflow and Private Networks

A deployment workflow may require private infrastructure.

Architecture:

```text
GitHub
  ↓
Self-Hosted Runner
  ↓
Private VPC
  ↓
ECS / EC2 / Internal APIs
```

The reusable workflow should clearly document:

- Required runner labels.
- Runner groups.
- Network requirements.
- Required permissions.
- Expected AWS account.
- Environment restrictions.

Do not silently assume every consumer has private network access.

---

## Runner Selection

A reusable workflow can select a runner class:

```yaml
runs-on:
  - self-hosted
  - linux
  - production-deploy
```

The label should represent a capability rather than a machine identity.

Prefer:

```text
production-deploy
```

over:

```text
runner-17
```

This allows infrastructure to change without modifying workflow consumers.

---

## Ephemeral Runner Architecture

Sensitive reusable deployment workflows can use ephemeral runners:

```text
Workflow
   ↓
Provision Runner
   ↓
Run Deployment
   ↓
Destroy Runner
```

Benefits include:

- Reduced persistent state.
- Lower cross-job contamination risk.
- Easier lifecycle management.
- Better isolation.

The trade-offs include:

- Startup latency.
- Infrastructure complexity.
- Autoscaling requirements.
- Cost.

---

## Performance Considerations

Reusable workflows improve maintainability but can introduce operational overhead.

Consider:

- Workflow startup time.
- Repeated dependency installation.
- Matrix size.
- Cache efficiency.
- Artifact transfers.
- Runner provisioning.
- Cross-repository dependencies.

A shared workflow should optimize common paths rather than expose every possible feature.

---

## Scalability Considerations

At organization scale:

```text
10 repositories
    ↓
100 repositories
    ↓
1000 repositories
```

A centralized workflow can reduce duplication but increases platform blast radius.

Therefore:

```text
Centralization
+
Versioning
+
Testing
+
Governance
+
Observability
```

must evolve together.

---

## High Availability Considerations

Reusable workflows are dependent on:

- GitHub Actions availability.
- Workflow repository availability.
- Runner availability.
- Artifact registry availability.
- Cloud API availability.

For critical deployment systems:

- Keep rollback artifacts available.
- Maintain runner capacity.
- Avoid unnecessary external dependencies.
- Document manual recovery procedures.
- Maintain infrastructure-as-code.

---

## Disaster Recovery

The reusable workflow platform itself should be recoverable.

Preserve:

```text
Workflow Source
Version Tags
Deployment Definitions
Infrastructure Code
Consumer Inventory
Documentation
Rollback Procedures
```

A production organization should not depend on a single undocumented workflow branch.

---

## Cost Considerations

Reusable workflows can reduce cost by centralizing:

- Dependency caching.
- Docker caching.
- Matrix strategy.
- Test selection.
- Runner configuration.

But a poorly designed shared workflow can increase cost for every consumer.

Avoid defaulting every repository to:

```text
Full Matrix
+
Full E2E
+
Full Security Suite
```

when those checks are not required for every change.

---

## Common Mistakes

### Treating Reusable Workflows as Copy-Paste Templates

A reusable workflow should have a stable API.

### Exposing Too Many Inputs

Excessive configurability creates an internal programming language that is difficult to maintain.

### Hiding Required Secrets

Secrets should be explicit in the contract.

### Granting Excessive Permissions

A shared workflow should not automatically receive broad write access.

### Using Mutable Workflow References Carelessly

Uncontrolled moving references can introduce unexpected changes.

### Rebuilding During Deployment

Deployment workflows should consume the validated artifact.

### Sharing One Production Role Everywhere

Different environments and services should have appropriately scoped identities.

### Putting Everything in One Workflow

Separate CI, build, deployment, and release responsibilities when their lifecycle differs.

### Ignoring Cancellation

A deployment workflow must account for cancellation and partial execution.

### Not Testing Consumer Compatibility

A reusable workflow can break many repositories simultaneously.

---

## Troubleshooting Reusable Workflows

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

### Workflow Is Not Callable

Check:

- `workflow_call`.
- Workflow location.
- Repository path.
- Reference.
- Access permissions.

### Input Is Missing

Check:

```yaml
on:
  workflow_call:
    inputs:
```

and the caller:

```yaml
with:
```

### Secret Is Missing

Check:

```yaml
secrets:
```

and the caller's secret mapping.

### Output Is Empty

Trace:

```text
Step Output
 ↓
Job Output
 ↓
Workflow Output
 ↓
Caller needs.<job>.outputs
```

### Deployment Has Wrong Artifact

Check:

- Output propagation.
- Image tag.
- Image digest.
- Registry.
- Environment.
- Workflow version.

### AWS Authentication Fails

Check:

```bash
aws sts get-caller-identity
```

Then inspect:

- `id-token: write`.
- IAM trust policy.
- Repository claim.
- Environment claim.
- AWS account.
- Role ARN.

### Workflow Change Breaks Many Consumers

Check:

- Version reference.
- Recent reusable workflow changes.
- Consumer input contracts.
- Removed outputs.
- Changed defaults.
- Permission changes.

---

## GitHub CLI Operations

List workflows:

```bash
gh workflow list
```

Inspect workflow:

```bash
gh workflow view python-ci.yml
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

Repository secrets:

```bash
gh secret list
```

Repository variables:

```bash
gh variable list
```

Environment information can be managed through the appropriate GitHub CLI API commands when operational automation requires it.

The CLI should be used for CI/CD operations rather than treated as a generic GitHub course.

---

## Reference Architecture

```mermaid
flowchart TB
    subgraph Consumers
        A[Orders Repository]
        B[Payments Repository]
        C[Users Repository]
    end

    subgraph Platform["Platform Repository"]
        CI[Reusable Python CI]
        BUILD[Reusable Docker Build]
        SEC[Reusable Security]
        DEPLOY[Reusable AWS Deployment]
        RELEASE[Reusable Release]
    end

    subgraph AWS
        OIDC[OIDC / STS]
        ECR[ECR]
        STG[Staging]
        PROD[Production]
    end

    A --> CI
    B --> CI
    C --> CI

    A --> BUILD
    B --> BUILD
    C --> BUILD

    A --> SEC
    B --> SEC
    C --> SEC

    BUILD --> ECR
    ECR --> DEPLOY

    DEPLOY --> OIDC
    OIDC --> STG
    STG --> PROD

    RELEASE --> DEPLOY
```

This architecture provides:

- Centralized pipeline implementation.
- Explicit workflow contracts.
- Shared security controls.
- Versioned deployment logic.
- Build-once/deploy-many behavior.
- Environment separation.
- Reusable platform primitives.

---

## Production Reusable CI/CD Architecture

A complete service lifecycle can look like:

```text
Application Repository
        ↓
Pull Request
        ↓
Reusable CI
        ├── Lint
        ├── Unit Tests
        ├── Integration Tests
        ├── Security
        └── Matrix
        ↓
Reusable Docker Build
        ↓
Immutable Image
        ↓
ECR
        ↓
Reusable Staging Deployment
        ↓
Health Validation
        ↓
Production Approval
        ↓
Reusable Production Deployment
        ↓
Monitoring
        ↓
Rollback
```

The application repository primarily declares intent:

```yaml
jobs:
  ci:
    uses: organization/platform/.github/workflows/python-ci.yml@v1

  build:
    needs: ci
    uses: organization/platform/.github/workflows/docker-build.yml@v1
    with:
      image-name: orders-api

  staging:
    needs: build
    uses: organization/platform/.github/workflows/aws-deploy.yml@v1
    with:
      environment: staging
      image-digest: ${{ needs.build.outputs.image-digest }}

  production:
    needs: staging
    uses: organization/platform/.github/workflows/aws-deploy.yml@v1
    with:
      environment: production
      image-digest: ${{ needs.build.outputs.image-digest }}
```

The platform repository owns the implementation.

The application repository owns the service-specific intent.

---

## Senior Design Principles

### Treat Reusable Workflows as APIs

Inputs, outputs, secrets, permissions, and versioning form the workflow contract.

### Expose Intent, Not Implementation

Prefer:

```text
environment: production
```

over:

```text
run-production-deploy-step-17: true
```

### Keep Privilege Local

A reusable workflow should grant permissions only to the jobs that need them.

### Version Shared Workflows

A shared workflow is a dependency and should have a controlled release lifecycle.

### Build Once, Promote Many

Reusable build and deployment workflows should pass immutable artifact identity rather than rebuild source for each environment.

### Design for Blast Radius

A shared workflow can affect hundreds of repositories.

Therefore workflow changes require stronger testing and governance than repository-local scripts.

### Keep Failure Domains Visible

Consumers should be able to identify whether a failure originated in:

```text
Caller
Workflow Contract
Reusable Workflow
Action
Runner
Artifact
Cloud Authentication
Deployment
Runtime
```

### Make Recovery Explicit

Reusable deployment workflows should support deterministic rollback to a known-good artifact.

---

## Senior Interview Scenarios

### Multiple Repositories Need the Same Python CI

Design:

```text
Platform Repository
        ↓
Reusable Python CI
        ↓
Multiple Application Repositories
```

Discuss:

- Inputs.
- Outputs.
- Secrets.
- Versioning.
- Compatibility.
- Governance.

### A Shared Workflow Needs AWS Access

Discuss:

```text
GitHub OIDC
→ STS
→ IAM Role
→ AWS Service
```

Also discuss:

- Trust policy.
- `id-token: write`.
- Environment restrictions.
- Least privilege.

### A Reusable Workflow Needs to Return a Docker Image

Design:

```text
Build Step
 ↓
Job Output
 ↓
Workflow Output
 ↓
Caller
```

Prefer an immutable digest over a mutable tag.

### A Shared Workflow Breaks 100 Repositories

Discuss:

- Versioning.
- Consumer inventory.
- Backward compatibility.
- Contract tests.
- Rollback.
- Controlled rollout.

### A Deployment Must Not Run Twice

Use:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

Then discuss idempotency and deployment state.

### A Self-Hosted Runner Is Required

Discuss:

- Runner groups.
- Labels.
- Private network.
- Ephemeral runners.
- Security.
- Capacity.
- Monitoring.

### A Compromised Third-Party Action Is Used by the Shared Workflow

Discuss:

- SHA pinning.
- Dependency trust.
- Job-level permissions.
- Secret isolation.
- Runner isolation.
- OIDC restrictions.
- Incident response.

### How Would You Design a Platform Workflow for 500 Repositories?

Consider:

```text
Reusable Workflows
+
Versioning
+
Consumer Compatibility
+
Action Governance
+
Runner Governance
+
Observability
+
Security
+
Controlled Rollouts
```

The primary challenge is not YAML reuse; it is managing platform blast radius.

---

## Production Checklist

### Workflow Contract

- [ ] Inputs are minimal and meaningful.
- [ ] Input types are explicit.
- [ ] Defaults are safe.
- [ ] Required secrets are documented.
- [ ] Outputs are documented.
- [ ] Permissions are documented.

### Architecture

- [ ] Workflow responsibility is clear.
- [ ] Reusable workflow vs composite action is intentional.
- [ ] Jobs have appropriate boundaries.
- [ ] Fan-out/fan-in is used where useful.
- [ ] CI and CD responsibilities are separated.

### Security

- [ ] Permissions use least privilege.
- [ ] Secrets are scoped.
- [ ] OIDC is used instead of long-lived AWS credentials where appropriate.
- [ ] Untrusted PRs cannot access production credentials.
- [ ] Third-party actions are governed.
- [ ] Shared workflow repository is protected.

### Versioning

- [ ] Workflow versions are defined.
- [ ] Breaking changes use a new major version where appropriate.
- [ ] Consumer compatibility is tested.
- [ ] Deprecation policy exists.
- [ ] Rollback is possible.

### Deployment

- [ ] Artifact identity is immutable.
- [ ] Build and deployment are separated.
- [ ] Environment protection is configured.
- [ ] Production concurrency is controlled.
- [ ] Health validation exists.
- [ ] Rollback uses a known-good artifact.

### Operations

- [ ] Workflow logs are useful.
- [ ] Step summaries provide relevant metadata.
- [ ] Consumer failures can be traced.
- [ ] Runner requirements are documented.
- [ ] Platform workflow ownership is explicit.
- [ ] Failure and recovery procedures are documented.

## Key Takeaways

- A reusable workflow is a **versioned CI/CD API** that should expose stable inputs, secrets, outputs, permissions, and behavior rather than implementation details.
- Use reusable workflows for **pipeline-level reuse** and composite actions for **step-level reuse**; confusing these abstractions creates unnecessary coupling.
- Production reusable workflows should enforce **least privilege, immutable artifact promotion, controlled environments, concurrency, OIDC-based AWS authentication, and secure runner boundaries**.
- Because one workflow can affect many repositories, reusable workflow changes require **versioning, contract testing, backward compatibility, governance, and controlled rollout**.
- The strongest architecture separates **application intent from platform implementation**, allowing application teams to declare what they need while the platform provides secure, scalable, observable CI/CD capabilities.