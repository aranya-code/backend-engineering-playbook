# 01- GitHub Hosted Runners

## Overview

GitHub-hosted runners are managed execution environments provided by GitHub for running GitHub Actions jobs.

They provide an ephemeral compute environment in which a workflow job can:

- Check out source code
- Install dependencies
- Run tests
- Build applications
- Build Docker images
- Execute security scans
- Publish artifacts
- Authenticate with AWS
- Deploy applications

The fundamental execution model is:

```text
Workflow
    ↓
Job
    ↓
Runner
    ↓
Steps
    ↓
Commands / Actions
```

For backend engineering, GitHub-hosted runners remove much of the operational burden associated with maintaining CI infrastructure while still providing configurable execution environments.

A typical Python CI pipeline might execute as:

```text
GitHub Event
    ↓
GitHub Actions Workflow
    ↓
Ubuntu Runner
    ↓
Python Setup
    ↓
Dependencies
    ↓
PostgreSQL / Redis
    ↓
pytest
    ↓
Docker Build
    ↓
Artifact / Registry
```

---

## What Is a GitHub-Hosted Runner?

A GitHub-hosted runner is a virtual machine managed by GitHub that executes a GitHub Actions job.

A workflow selects a runner using:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
```

GitHub provisions an appropriate runner, executes the job, and disposes of the environment after the job completes.

The runner provides:

- Operating system
- CPU
- Memory
- Shell
- Preinstalled tools
- Git
- Common development runtimes
- Docker support where applicable
- Network connectivity required by the workflow

The runner is not the workflow itself.

```text
Workflow
  └── defines what should happen

Job
  └── defines one execution unit

Runner
  └── provides compute where the job executes
```

---

## Why GitHub-Hosted Runners Exist

Maintaining CI infrastructure manually introduces operational work:

```text
Provision VM
    ↓
Install software
    ↓
Patch OS
    ↓
Maintain runners
    ↓
Scale capacity
    ↓
Clean workspaces
    ↓
Monitor availability
    ↓
Replace failed machines
```

GitHub-hosted runners move much of this infrastructure management to GitHub.

This is particularly useful for teams that want to focus on:

```text
Application
+
Pipeline
+
Testing
+
Deployment
```

rather than operating a dedicated CI fleet.

---

## When to Use GitHub-Hosted Runners

GitHub-hosted runners are generally suitable when jobs:

- Do not require private network access
- Can use standard operating systems
- Do not require specialized hardware
- Do not require persistent local state
- Can operate within GitHub-hosted execution constraints
- Do not require proprietary internal tooling unavailable on the hosted environment

Common workloads include:

- Python linting
- Django tests
- FastAPI tests
- PostgreSQL integration tests
- Redis integration tests
- Docker builds
- Security scanning
- Package builds
- Static analysis
- Release automation

---

## When GitHub-Hosted Runners May Not Be Enough

A self-hosted runner may be more appropriate when a job requires:

- Private VPC access
- Internal databases
- Internal APIs
- Custom enterprise software
- Specialized hardware
- Persistent local tooling
- Network-restricted infrastructure
- Specific operating system configuration

For example:

```text
GitHub-hosted runner
       X
       │
       │ Private VPC
       │
       ▼
Internal Database
```

If the CI job must directly access resources that are intentionally unreachable from the public internet, a self-hosted architecture may be required.

---

## GitHub Actions Execution Architecture

A simplified architecture is:

```mermaid
flowchart LR
    EVENT[GitHub Event] --> WORKFLOW[Workflow]
    WORKFLOW --> JOB[Job]
    JOB --> RUNNER[GitHub-Hosted Runner]
    RUNNER --> STEPS[Steps]
    STEPS --> ACTIONS[Actions / Shell Commands]
    ACTIONS --> ARTIFACT[Artifacts]
    ACTIONS --> REGISTRY[Container Registry]
    ACTIONS --> DEPLOY[Deployment]
```

The runner is the execution boundary for the job.

This distinction becomes important for:

- Security
- Credentials
- Filesystem state
- Network access
- Docker access
- Performance
- Cost
- Failure isolation

---

## Selecting a Runner

The simplest configuration is:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
```

Other operating-system families can be selected according to the runner labels available to the repository and account.

Typical categories include:

```text
Ubuntu
Windows
macOS
```

For production CI, Linux is common for backend workloads because most Python, Docker, Kubernetes, and AWS tooling is Linux-oriented.

---

## Linux Runners

Linux runners are a natural fit for backend systems.

Typical workloads include:

```text
Python
Django
FastAPI
PostgreSQL
Redis
Docker
Terraform
AWS CLI
Kubernetes CLI
```

Example:

```yaml
jobs:
  backend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

---

## Windows Runners

Windows runners are useful when the software requires:

- Windows-specific APIs
- Windows-native tooling
- .NET workflows
- PowerShell-specific behavior
- Windows application testing

For a Python backend that is deployed to Linux containers, Windows testing is usually required only when Windows compatibility itself is a requirement.

---

## macOS Runners

macOS runners are primarily relevant when the build or test process depends on Apple-specific tooling.

For typical server-side Python CI, they are usually unnecessary unless the project explicitly targets macOS.

---

## Runner Image

A hosted runner is created from a managed runner image.

The image typically includes common development tools and runtimes.

However, a pipeline should not blindly assume that a particular tool version will remain unchanged forever.

For deterministic builds, explicitly select important runtime versions.

For example:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"
```

Prefer:

```text
Explicit application runtime
```

over relying on:

```text
Whatever happens to be installed on the runner
```

---

## Runtime Version Management

A runner may contain multiple versions of a runtime.

For example:

```text
Python 3.11
Python 3.12
Python 3.13
```

Your workflow should explicitly select the version required by the project.

Example:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
```

For compatibility testing:

```yaml
strategy:
  matrix:
    python-version:
      - "3.11"
      - "3.12"
      - "3.13"
```

This separates:

```text
Runner operating system
```

from:

```text
Application runtime version
```

---

## Job Execution Lifecycle

A simplified lifecycle is:

```text
Workflow Trigger
      ↓
Job Queued
      ↓
Runner Allocated
      ↓
Runner Initialized
      ↓
Repository Checkout
      ↓
Environment Preparation
      ↓
Step 1
      ↓
Step 2
      ↓
Step N
      ↓
Artifacts / Results
      ↓
Job Completion
      ↓
Runner Environment Disposed
```

Understanding this lifecycle helps explain why files created in one job are not automatically available to another job.

---

## Jobs Have Separate Runners

Consider:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

  test:
    runs-on: ubuntu-latest
```

These jobs should be treated as independent execution environments.

A file created by:

```text
build
```

is not automatically available to:

```text
test
```

Use artifacts when data must cross job boundaries.

```text
Build Runner
    ↓
Upload Artifact
    ↓
GitHub Artifact Storage
    ↓
Download Artifact
    ↓
Test/Deploy Runner
```

---

## Filesystem Isolation

Within a job, steps generally share the same workspace.

```text
Job
 └── Runner
      └── Workspace
           ├── source
           ├── build output
           └── temporary files
```

Therefore:

```yaml
steps:
  - name: Build
    run: |
      mkdir -p dist
      echo "artifact" > dist/build.txt

  - name: Inspect
    run: |
      cat dist/build.txt
```

works because both steps execute within the same job environment.

Across jobs, use artifacts or another explicit storage mechanism.

---

## Workspace and Temporary Files

A job can create:

```text
Source files
Build files
Test reports
Logs
Temporary credentials
Caches
Generated configuration
```

Do not assume the workspace is a permanent storage location.

For sensitive temporary data:

- Minimize its lifetime
- Avoid unnecessary files
- Avoid printing credentials
- Clean up when appropriate
- Prefer short-lived authentication

---

## Ephemeral Nature

One of the most important characteristics of GitHub-hosted runners is that jobs should be treated as ephemeral.

Do not design CI around persistent local state such as:

```text
Previous build directory
Previous Docker image
Previous credentials
Previous database
Previous test result
```

Instead:

```text
Source
 ↓
Prepare
 ↓
Build
 ↓
Test
 ↓
Publish
```

Each job should be able to establish the state it requires.

---

## Why Ephemeral Execution Matters

Ephemeral execution reduces contamination between jobs.

Consider a persistent runner:

```text
Job A
 ↓
Leaves file
 ↓
Job B
 ↓
Accidentally consumes file
```

This can produce:

- Non-reproducible builds
- Security problems
- Hidden dependencies
- Incorrect test results

Hosted runners encourage a cleaner model:

```text
Job
 ↓
Fresh execution environment
 ↓
Known inputs
 ↓
Known outputs
```

---

## GitHub-Hosted vs Self-Hosted Runners

| Area | GitHub-Hosted | Self-Hosted |
|---|---|---|
| Infrastructure management | GitHub | Team |
| Scaling | Managed | Team-managed |
| Customization | More limited | Extensive |
| Private network access | Limited by architecture | Strong |
| Persistent tooling | Not the design goal | Possible |
| Maintenance | Lower | Higher |
| Isolation | Managed ephemeral model | Team responsibility |
| Specialized hardware | Depends on available offerings | Full control |
| Operational burden | Lower | Higher |

The decision should be based on workload requirements rather than preference.

---

## GitHub-Hosted Runner Advantages

### Reduced Infrastructure Management

You do not need to maintain the runner operating system fleet.

### Ephemeral Execution

Each job can start from a clean environment.

### Easy Scaling

Independent jobs can execute on separate runner instances subject to account and service limits.

### Standardized Environments

Teams can use common runner labels and consistent workflow definitions.

### Lower Operational Overhead

The team spends less time managing:

- OS patching
- Runner registration
- Runner health
- Capacity planning
- Machine replacement

---

## GitHub-Hosted Runner Limitations

Hosted runners are not a universal solution.

Potential limitations include:

- Limited control over the underlying machine
- Restrictions around private network access
- Dependency on GitHub service availability
- Service quotas and concurrency limits
- Execution time constraints
- Storage limitations
- Less control over hardware
- Less control over network topology

A production architecture should account for these constraints.

---

## GitHub-Hosted Runner and Private AWS Resources

A common misconception is:

```text
GitHub-hosted runner
       ↓
Automatically reaches
       ↓
Private AWS VPC
```

It does not.

If an integration test requires:

```text
GitHub-hosted runner
       ↓
Private RDS
```

the network path must explicitly exist.

Possible architectures include:

```text
GitHub-hosted runner
       ↓
Publicly accessible test endpoint
```

or:

```text
GitHub Actions
       ↓
Controlled private connectivity
       ↓
Self-hosted runner
       ↓
Private VPC
       ↓
RDS
```

Private infrastructure requirements should be evaluated before selecting the runner model.

---

## Backend Testing Architecture

A typical GitHub-hosted integration test job can use service containers.

```mermaid
flowchart TB
    RUNNER[GitHub-Hosted Runner]

    RUNNER --> APP[Python Test Process]
    RUNNER --> PG[PostgreSQL Service]
    RUNNER --> REDIS[Redis Service]

    APP --> PG
    APP --> REDIS
```

This is useful for:

- Django
- FastAPI
- pytest
- Database integration tests
- Cache integration tests

The services exist for the lifetime of the job.

---

## PostgreSQL Example

A backend integration test can use:

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres -d testdb"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
        run: pytest
```

The health configuration helps ensure PostgreSQL is ready before tests execute.

---

## Redis Example

Redis can similarly be provided as a service:

```yaml
services:
  redis:
    image: redis:7
    ports:
      - 6379:6379
```

The application can use:

```text
redis://localhost:6379/0
```

when the workflow architecture uses the runner host networking model.

---

## Service Readiness

Container startup is not equivalent to application readiness.

This sequence can fail:

```text
Container Started
      ↓
pytest immediately starts
      ↓
PostgreSQL still initializing
      ↓
Connection refused
```

Use health checks or explicit readiness logic.

Production-quality CI should distinguish:

```text
Process started
```

from:

```text
Service ready
```

---

## Docker on GitHub-Hosted Runners

Hosted Linux runners commonly support Docker-based workflows.

A typical flow is:

```text
Checkout
 ↓
Docker Buildx
 ↓
Build Image
 ↓
Scan
 ↓
Push Registry
```

Example:

```yaml
- name: Build image
  run: |
    docker build -t orders:${GITHUB_SHA} .
```

For advanced builds, use Buildx.

---

## Docker Buildx

Buildx provides modern BuildKit-based Docker build capabilities.

A typical pipeline can include:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
```

Then:

```yaml
- name: Build image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: false
    tags: orders:${{ github.sha }}
```

This supports more advanced caching and multi-platform build workflows.

---

## Docker Layer Caching

Docker builds can be expensive if dependencies are rebuilt repeatedly.

A pipeline can use BuildKit caching to reduce build time.

Conceptually:

```text
Dockerfile
    ↓
Layer Graph
    ↓
Unchanged Layers → Cache
Changed Layers   → Rebuild
```

Cache optimization should improve performance without becoming a correctness dependency.

---

## Cache vs Artifact on Hosted Runners

A Docker cache can be recreated.

A release artifact cannot necessarily be recreated safely during an incident.

Therefore:

```text
Cache
→ Performance optimization

Artifact
→ Release/deployment output
```

Do not treat a cache as the authoritative source for production deployment.

---

## Python Dependency Caching

Python dependencies can also be cached.

For example:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: "pip"
```

The cache can reduce installation time while keeping dependency installation reproducible from the project's dependency definitions.

---

## Matrix and Hosted Runners

A matrix can create multiple independent runner allocations.

Example:

```yaml
strategy:
  matrix:
    python:
      - "3.11"
      - "3.12"
      - "3.13"
```

This means:

```text
Python 3.11 → Runner
Python 3.12 → Runner
Python 3.13 → Runner
```

Matrix size directly affects:

- Runner consumption
- CI duration
- Cost
- Registry load
- External dependency load

---

## Matrix Design and External Dependencies

Suppose a matrix contains:

```text
3 Python versions
×
2 databases
×
2 operating systems
```

That creates:

```text
12 executions
```

If each test suite connects to PostgreSQL and Redis, the external dependency load can multiply as well.

Do not expand matrices without considering:

```text
Runner capacity
Database capacity
Registry traffic
API rate limits
CI cost
Execution duration
```

---

## Job-Level Isolation

A matrix job should be treated as an independent execution unit.

Avoid relying on:

```text
Runner-local state
```

to communicate between matrix variants.

Use:

```text
Artifacts
Outputs
External storage
```

when information needs to move between jobs.

---

## Artifacts from Hosted Runners

Artifacts are useful for:

- Test reports
- Coverage reports
- Build packages
- Debug logs
- Screenshots
- E2E traces
- Deployment metadata

Example:

```yaml
- name: Upload test reports
  uses: actions/upload-artifact@v4
  with:
    name: test-reports
    path: |
      reports/
      coverage.xml
```

Artifacts should have appropriate retention periods.

---

## Debugging Artifacts

When a job fails, useful artifacts may include:

```text
pytest output
Coverage XML
HTML reports
Screenshots
Browser traces
Application logs
Docker logs
Generated configuration
```

This is especially useful for:

- E2E tests
- Integration tests
- Intermittent failures
- Browser automation

Avoid uploading sensitive credentials or secret-bearing files.

---

## Environment Variables

Environment variables can exist at different scopes.

```yaml
env:
  APP_ENV: test
```

Job-level:

```yaml
jobs:
  test:
    env:
      APP_ENV: test
```

Step-level:

```yaml
- name: Test
  env:
    DATABASE_URL: ...
  run: pytest
```

Use the narrowest scope appropriate for the value.

---

## Secrets on Hosted Runners

Secrets are injected into the job only when the workflow is authorized to access them.

Production secrets should not be unnecessarily exposed to:

```text
Lint jobs
Unit test jobs
Untrusted pull requests
Build jobs
Static analysis jobs
```

For example, a build job may not need AWS production credentials.

Separate:

```text
Build permissions
```

from:

```text
Deployment permissions
```

---

## AWS OIDC from Hosted Runners

A common deployment pattern is:

```text
GitHub-Hosted Runner
        ↓
GitHub OIDC
        ↓
AWS STS
        ↓
IAM Role
        ↓
ECR / ECS / S3 / Lambda
```

Example workflow permissions:

```yaml
permissions:
  contents: read
  id-token: write
```

The IAM trust relationship should restrict which repository and workflow identity can assume the role.

---

## Build and Deploy Separation

A secure architecture should avoid giving every job production credentials.

Prefer:

```text
Lint
 ↓
Tests
 ↓
Security
 ↓
Build
 ↓
Artifact
 ↓
Deployment Job
 ↓
AWS Credentials
```

rather than:

```text
Every Job
 ↓
Production AWS Credentials
```

This reduces blast radius.

---

## Runner Security

Although GitHub manages hosted runners, the workflow still controls what code executes on them.

A malicious dependency or compromised action can execute commands with the permissions available to the job.

Therefore:

```text
Hosted Runner
≠
Automatically Safe Workflow
```

Security still depends on:

- Permissions
- Secrets
- Actions
- Dependencies
- Input handling
- Network access
- Workflow design

---

## Untrusted Pull Requests

A pull request can modify application code.

If that code executes in a privileged workflow:

```text
Untrusted Code
      ↓
Runner
      ↓
Credentials
      ↓
Production Resource
```

the trust boundary has failed.

For untrusted PR workflows:

- Minimize permissions
- Avoid production secrets
- Avoid privileged credentials
- Avoid unnecessary network access
- Carefully evaluate third-party actions
- Treat workflow-controlled execution as code execution

---

## Third-Party Actions on Hosted Runners

An action executes code on the runner.

For example:

```yaml
- uses: some-org/some-action@v1
```

should therefore be treated as a dependency.

Security controls include:

```text
Trusted Source
+
Version Pinning
+
SHA Pinning
+
Least Privilege
+
Minimal Secrets
```

This is particularly important in release and deployment workflows.

---

## GitHub-Hosted Runner Network Model

The runner needs network connectivity to whatever services the workflow uses.

Typical public-service access:

```text
Runner
 ├── GitHub
 ├── PyPI
 ├── Docker Registry
 ├── AWS APIs
 └── Public APIs
```

Private services require additional architecture.

For example:

```text
Runner
   X
   │
Private RDS
```

may not work without an appropriate connectivity model.

---

## Network Egress Considerations

CI jobs often install dependencies from external services:

```text
PyPI
npm Registry
Docker Hub
GitHub
AWS
```

Security-sensitive organizations may want to control outbound traffic.

With GitHub-hosted runners, network control is less customizable than with infrastructure that the organization owns.

This can influence the decision to use self-hosted runners.

---

## Private Package Registries

A Python application may depend on private packages.

The workflow can authenticate to an internal registry or GitHub Packages as required.

Example conceptual flow:

```text
Runner
  ↓
Authenticate
  ↓
Private Package Registry
  ↓
Install
```

Credentials should be scoped only to the installation job and should never be printed.

---

## Runner Labels

Runner labels allow workflows to target compatible execution environments.

For GitHub-hosted runners, the selected label describes the required environment.

For self-hosted runners, teams can create labels representing:

```text
linux
docker
private-network
gpu
deployment
```

The important distinction is that self-hosted labels also become part of the organization's scheduling and security model.

---

## Workflow Quotas and Limits

GitHub Actions operates within service limits.

Limits can affect:

- Concurrent jobs
- Workflow execution
- Storage
- Artifact retention
- Cache storage
- API usage
- Runner capacity

The exact limits can vary by plan and GitHub service configuration.

Do not design a system assuming unlimited parallel execution.

For large organizations, model expected workload:

```text
Repositories
×
Workflow Frequency
×
Matrix Size
×
Average Job Duration
```

---

## Scaling CI Workloads

Suppose:

```text
100 repositories
×
10 CI runs/day
×
10-minute average runtime
```

The organization may generate substantial CI workload.

If every repository additionally uses:

```text
10-job matrix
```

the execution demand grows significantly.

Scaling considerations include:

- Matrix size
- Job duration
- Trigger frequency
- Concurrency
- Caching
- Selective testing
- Reusable workflows
- Runner availability

---

## Selective Testing

Large monorepos can avoid unnecessary work.

For example:

```text
Changed paths
    ↓
Determine affected services
    ↓
Generate matrix
    ↓
Run only required tests
```

This can reduce:

- Runner consumption
- CI duration
- External dependency usage

while preserving useful test coverage.

---

## Hosted Runner Cost Considerations

Cost depends on the GitHub plan, runner type, usage, and workload.

Common cost drivers include:

- Long-running tests
- Large matrices
- Docker builds
- E2E tests
- Repeated workflows
- Excessive retries
- Large artifact storage

Optimize the pipeline based on engineering value rather than simply minimizing execution time.

---

## Performance Optimization

Useful optimizations include:

### Dependency Caching

```text
pip cache
npm cache
Docker cache
```

### Parallel Testing

Split independent test suites.

### Matrix Optimization

Test only meaningful combinations.

### Build Context Optimization

Use:

```text
.dockerignore
```

to reduce Docker build context.

### Test Selection

Run fast tests early and expensive tests only after required validation succeeds.

---

## Failure Isolation

A well-designed workflow should make it obvious where failure occurred.

```text
Lint
  ↓
Unit
  ↓
Integration
  ↓
Security
  ↓
Build
  ↓
Publish
  ↓
Deploy
```

If all operations are placed into one large job, failure isolation becomes harder.

Prefer logically separated jobs when boundaries provide meaningful benefits.

---

## Reliability and Retries

Retries can be useful for genuinely transient operations.

Examples:

- Network calls
- Registry operations
- Cloud API calls

Do not blindly retry deterministic failures such as:

```text
Syntax Error
Test Failure
Invalid Configuration
Authentication Failure
```

A retry policy should distinguish:

```text
Transient Failure
```

from:

```text
Deterministic Failure
```

---

## Idempotency

Deployment and infrastructure operations should ideally be idempotent.

A workflow rerun should not produce destructive duplicate state.

For example:

```text
Deploy version X
```

should converge to:

```text
Version X deployed
```

rather than:

```text
Duplicate resources
Duplicate deployments
Corrupted state
```

---

## Hosted Runner Failure Modes

Common failure domains include:

| Symptom | Possible Cause |
|---|---|
| Job never starts | Queue/concurrency/capacity |
| Tool not found | Runner image/tool assumption |
| Permission denied | File or execution permissions |
| Network failure | External service/connectivity |
| Docker failure | Daemon/build configuration |
| Test intermittently fails | Readiness/race/flaky dependency |
| Artifact missing | Upload path/job failure |
| Cache miss | Key mismatch |
| AWS authentication fails | OIDC/IAM configuration |
| Private service unavailable | Network architecture |

---

## Troubleshooting Workflow Startup

### Symptom

A workflow is queued or does not execute.

### Possible Causes

- Trigger did not match
- Workflow is disabled
- Branch/path filter excluded the change
- Concurrency is blocking execution
- Runner capacity is unavailable
- Required workflow configuration is invalid

### Isolation Strategy

Inspect:

```bash
gh workflow list
gh run list
```

Then inspect the workflow run:

```bash
gh run view RUN_ID
```

### Prevention

Keep trigger conditions explicit and avoid unnecessarily complex filters.

---

## Troubleshooting Tool Availability

### Symptom

```text
command not found
```

### Possible Causes

- Tool is not installed
- Runner image changed
- Wrong operating system
- PATH is incorrect
- Runtime setup step was skipped

### Checks

```bash
which python
python --version
which docker
docker --version
```

### Corrective Action

Explicitly install or configure required tools rather than relying on undocumented runner state.

---

## Troubleshooting Docker

### Symptom

Docker build fails unexpectedly.

### Possible Causes

- Invalid Dockerfile
- Build context too large
- Missing files
- Dependency failure
- Registry failure
- Cache issue
- Buildx configuration

### Checks

```bash
docker version
docker info
docker build .
```

For Buildx:

```bash
docker buildx ls
```

### Prevention

Use:

```text
.dockerignore
```

multi-stage builds, pinned dependencies, and explicit Buildx configuration.

---

## Troubleshooting PostgreSQL

### Symptom

Integration tests report:

```text
connection refused
```

### Possible Causes

- PostgreSQL is still starting
- Incorrect host/port
- Incorrect credentials
- Wrong database name
- Service container configuration

### Checks

```bash
pg_isready -h localhost -p 5432
```

Verify:

```text
DATABASE_URL
```

and the service health configuration.

---

## Troubleshooting AWS OIDC

### Symptom

The workflow cannot assume an AWS role.

### Possible Causes

- Missing `id-token: write`
- IAM trust policy mismatch
- Wrong repository condition
- Wrong branch/environment condition
- Incorrect audience
- Incorrect AWS role ARN

### Checks

```bash
aws sts get-caller-identity
```

If authentication succeeds, inspect the identity returned by STS.

The trust policy should be checked against the actual GitHub OIDC claims used by the workflow.

---

## Troubleshooting Artifacts

### Symptom

A later job cannot download an artifact.

### Possible Causes

- Upload step failed
- Incorrect artifact name
- Wrong path
- Job dependency missing
- Artifact was never produced

### Isolation Strategy

Check the producing job first.

```text
Producer Job
    ↓
Artifact Upload
    ↓
Artifact Exists
    ↓
Consumer Job
```

Do not troubleshoot the consumer before verifying the producer.

---

## Troubleshooting Caches

### Symptom

The workflow works but is unexpectedly slow.

### Possible Causes

- Cache miss
- Cache key changed
- Dependency lock file changed
- Cache scope mismatch
- Cache not populated

A cache miss should not break correctness.

If a pipeline fails because the cache is unavailable, the pipeline has incorrectly treated an optimization as a required dependency.

---

## Troubleshooting Runner Performance

### Symptom

A job becomes unexpectedly slow.

### Possible Causes

- Dependency installation
- Docker build
- Large checkout
- Large test matrix
- External API latency
- Cache miss
- Artifact upload
- Test suite growth

Break the job into measured stages.

```text
Checkout
Dependency Setup
Test Setup
Tests
Build
Artifact Upload
```

Measure before optimizing.

---

## Monitoring CI/CD Operations

A production engineering team should monitor:

```text
Workflow Success Rate
Workflow Duration
Queue Time
Failure Rate
Runner Utilization
Artifact Storage
Cache Usage
Deployment Duration
Rollback Frequency
```

For large organizations, trends are more useful than isolated failures.

---

## High Availability Considerations

GitHub-hosted runners reduce the need to maintain a runner fleet, but application delivery still depends on external systems.

Potential dependencies include:

```text
GitHub
Package Registry
Container Registry
AWS APIs
Application Infrastructure
DNS
Monitoring
```

High availability planning should identify which external dependencies are critical to deployment and which are recoverable later.

---

## Disaster Recovery

CI/CD disaster recovery should answer:

- Can the last known-good artifact be identified?
- Can the production version be redeployed?
- Can infrastructure be recreated?
- Are deployment configurations version-controlled?
- Are release records preserved?
- Are required credentials available through secure recovery procedures?
- Can the organization operate if a runner or workflow fails?

The most important recovery principle is:

```text
Do not depend on rebuilding an old release from uncertain state.
```

Retain immutable production artifacts.

---

## GitHub-Hosted Runner and Release Architecture

A production release can use:

```mermaid
sequenceDiagram
    participant Git as GitHub
    participant Runner as Hosted Runner
    participant Registry as ECR
    participant AWS as AWS Deployment

    Git->>Runner: Trigger release workflow
    Runner->>Runner: Checkout tagged commit
    Runner->>Runner: Build and test
    Runner->>Runner: Build Docker image
    Runner->>Registry: Push immutable image
    Runner->>AWS: Assume IAM role via OIDC
    Runner->>AWS: Deploy image digest
    AWS-->>Runner: Deployment status
    Runner-->>Git: Release/deployment result
```

The hosted runner acts as the orchestration environment.

It does not need to become a permanent deployment server.

---

## Security Boundary Model

```mermaid
flowchart TB
    EVENT[GitHub Event] --> WORKFLOW[Workflow Definition]
    WORKFLOW --> RUNNER[Hosted Runner]

    RUNNER --> CODE[Repository Code]
    RUNNER --> ACTIONS[Third-Party Actions]
    RUNNER --> SECRETS[Scoped Secrets]
    RUNNER --> OIDC[OIDC Token]

    OIDC --> STS[AWS STS]
    STS --> IAM[IAM Role]
    IAM --> AWS[AWS Resources]
```

Every boundary should be evaluated independently.

A GitHub-hosted runner provides managed compute, but workflow code still determines what permissions and credentials become available.

---

## Common Mistakes

### Assuming the Runner Is Persistent

A hosted runner should not be used as a permanent build server.

### Depending on Preinstalled Tool Versions

Runner images change. Important application runtimes should be explicitly selected.

### Sharing Files Between Jobs Without Artifacts

Jobs should be treated as separate execution environments.

### Treating Cache as Storage

Caches are optimization mechanisms, not authoritative release storage.

### Giving Build Jobs Production Credentials

Separate build and deployment permissions.

### Assuming Private VPC Access

Hosted runners do not automatically have connectivity to private AWS resources.

### Expanding Matrices Without Capacity Analysis

Matrix dimensions multiply runner and dependency consumption.

### Using Retries for Deterministic Failures

Retries do not fix broken code or invalid configuration.

### Running Untrusted Code With Privileged Access

A runner executes code. Treat every workflow execution path according to its trust level.

### Relying on `latest` for Production Identity

Use immutable artifact identifiers such as image digests.

---

## Interview Traps

### "Are GitHub-Hosted Runners Shared Between Jobs?"

Do not assume that a runner filesystem is a persistent shared workspace across jobs.

Use artifacts or explicit external storage for cross-job data.

### "Can a Hosted Runner Access a Private RDS Instance?"

Not automatically.

The network architecture must explicitly provide connectivity.

### "Does a Fresh Runner Make the Workflow Secure?"

No.

The workflow can still execute malicious dependencies, unsafe actions, or untrusted code with excessive permissions.

### "Why Use Self-Hosted Runners?"

Typical reasons include:

- Private network access
- Custom tooling
- Specialized hardware
- Internal systems

But self-hosted runners add operational and security responsibilities.

### "Should CI Depend on a Docker Cache?"

No.

Cache improves performance; correctness should not depend on it.

### "Why Use OIDC?"

OIDC allows short-lived AWS credentials through STS rather than storing long-lived AWS access keys.

---

## Production Runner Selection Checklist

Before choosing GitHub-hosted runners, verify:

- [ ] Required operating system is available.
- [ ] Required runtime versions can be configured.
- [ ] Required tools can be installed.
- [ ] Network requirements are compatible.
- [ ] Private resource access is not required or is explicitly supported.
- [ ] Docker requirements are supported.
- [ ] Matrix size is acceptable.
- [ ] Expected CI concurrency is understood.
- [ ] Artifact and cache requirements are understood.
- [ ] Security boundaries are documented.
- [ ] Deployment credentials are isolated.
- [ ] OIDC requirements are configured.
- [ ] Failure and recovery procedures are documented.

---

## Senior Design Principles

### Prefer Ephemeral Execution

Treat each job as disposable.

### Make Dependencies Explicit

Declare:

```text
Runtime
Dependencies
Services
Credentials
Artifacts
Outputs
```

rather than depending on hidden runner state.

### Separate Build and Deployment Privileges

A build job should not automatically have production access.

### Treat Runners as Execution Boundaries

Anything executed on a runner should be considered capable of accessing the permissions granted to that job.

### Use Hosted Runners When Infrastructure Requirements Are Simple

Do not introduce self-hosted infrastructure merely because it is possible.

### Use Self-Hosted Runners for Real Infrastructure Requirements

Private networks, specialized tooling, and hardware requirements can justify them.

### Design for Failure

CI should tolerate:

```text
Cache Miss
Transient Network Error
Artifact Failure
Runner Failure
External Service Failure
```

without corrupting release state.

### Preserve Artifact Identity

The production deployment should reference a deterministic artifact rather than an ephemeral runner workspace.

---

## Reference Production Architecture

```mermaid
flowchart LR
    DEV[Developer] --> PR[Pull Request]

    PR --> CI[GitHub Actions]
    CI --> HOSTED[Hosted Runner]

    HOSTED --> TEST[Unit / Integration Tests]
    HOSTED --> SECURITY[Security Scan]
    HOSTED --> BUILD[Docker Build]

    BUILD --> REGISTRY[ECR]

    REGISTRY --> STAGE[Staging]
    STAGE --> APPROVAL[Approval]
    APPROVAL --> PROD[Production]

    HOSTED --> OIDC[GitHub OIDC]
    OIDC --> STS[AWS STS]
    STS --> IAM[IAM Role]
    IAM --> REGISTRY
    IAM --> PROD

    PROD --> MONITOR[Monitoring]
    MONITOR --> ROLLBACK[Rollback]
```

The runner is deliberately positioned as an execution layer rather than as the permanent home of application state.

## Key Takeaways

- GitHub-hosted runners provide managed, ephemeral execution environments that are well suited to standard backend CI/CD workloads such as Python, Django, FastAPI, Docker, testing, and release automation.
- Treat runner state as disposable: cross-job data should move through explicit mechanisms such as artifacts, outputs, or external storage rather than filesystem assumptions.
- Hosted runners reduce infrastructure management, but they do not automatically solve private-network access, security, dependency isolation, quotas, cost, or workflow design.
- Production workflows should minimize runner privileges, isolate deployment credentials, use OIDC for AWS authentication where appropriate, and treat all executed code and third-party actions according to their trust level.
- Choose self-hosted runners only when requirements such as private network access, specialized tooling, or hardware justify the additional security and operational responsibility.