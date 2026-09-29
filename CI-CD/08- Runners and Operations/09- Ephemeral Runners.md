# 09- Ephemeral Runners

## Overview

An ephemeral runner is a GitHub Actions runner that is provisioned for a limited execution lifecycle, runs a job or a controlled unit of work, and is then destroyed or permanently removed from service.

The core idea is:

```text
Provision
    ↓
Register
    ↓
Execute one workload
    ↓
Collect results
    ↓
Terminate / Deregister
```

This differs from a persistent self-hosted runner, which remains available after a job completes and is reused by subsequent workflows.

Ephemeral runners are particularly useful when CI/CD workloads execute untrusted code, require private-network access, need custom software, or demand stronger workload isolation than a long-lived runner can provide.

For production backend systems, ephemeral runners are commonly used for:

- Private-network integration testing
- Docker builds
- Deployment workflows
- Security-sensitive workloads
- Infrastructure automation
- Kubernetes administration
- AWS deployments
- Workloads requiring custom OS packages
- High-isolation CI environments
- Autoscaled CI infrastructure

The important architectural principle is:

> Treat an ephemeral runner as disposable compute, not as a permanent server.

A production pipeline should assume that everything written to the runner filesystem, process environment, temporary directories, credentials, caches, and Docker state can disappear when the job finishes.

---

## Ephemeral vs Persistent Runners

| Property | Ephemeral Runner | Persistent Runner |
|---|---|---|
| Lifecycle | Short-lived | Long-lived |
| Job reuse | Normally one workload | Multiple workloads |
| Isolation | Stronger | Weaker |
| State persistence | Minimal | Common |
| Cleanup requirement | Primarily infrastructure teardown | Extensive cleanup after every job |
| Configuration drift | Lower with immutable images | Higher |
| Startup latency | Higher | Lower |
| Autoscaling | Natural fit | More complicated |
| Untrusted workloads | Better isolation model | Higher risk |
| Private network access | Supported | Supported |
| Operational complexity | Higher provisioning complexity | Higher hygiene complexity |
| Cost model | Pay for active capacity | Pay for provisioned capacity |
| Failure recovery | Replace runner | Repair or recycle runner |
| Recommended for sensitive workloads | Often | Only with strong isolation |

A persistent runner may be simpler operationally for low-risk internal workloads, but it creates a larger blast radius if a job compromises the machine.

---

## Why Ephemeral Runners Exist

A runner executes workflow code. That code may:

- Install dependencies
- Execute shell commands
- Run Python programs
- Build Docker images
- Access databases
- Access private services
- Read environment variables
- Use GitHub tokens
- Assume AWS roles
- Access filesystem contents
- Start child processes
- Communicate with external services

A persistent runner therefore accumulates risk over time.

For example:

```text
Job A
  ↓
Installs dependency
  ↓
Leaves files/processes/cache
  ↓
Job completes

Job B
  ↓
Runs on same machine
  ↓
Can potentially encounter Job A's residual state
```

With an ephemeral runner:

```text
Job A
  ↓
Fresh runner
  ↓
Execution
  ↓
Runner destroyed

Job B
  ↓
Another fresh runner
  ↓
Execution
```

The second model reduces cross-job contamination and makes the runner lifecycle easier to reason about.

---

## Core Lifecycle

A production ephemeral runner generally follows this lifecycle:

```mermaid
flowchart TD
    A[Workflow queued] --> B[Provision runner]
    B --> C[Bootstrap runner]
    C --> D[Register runner]
    D --> E[Runner becomes ready]
    E --> F[GitHub assigns job]
    F --> G[Execute job]
    G --> H[Upload artifacts / results]
    H --> I[Cleanup]
    I --> J[Terminate infrastructure]
```

The provisioning mechanism can be:

- Cloud VM
- Container
- Kubernetes Pod
- Autoscaling infrastructure
- AWS EC2
- AWS Auto Scaling
- Kubernetes-based runner controller
- Internal compute platform

The implementation mechanism changes, but the lifecycle remains conceptually similar.

---

## Runner State Model

A useful operational model is:

```mermaid
stateDiagram-v2
    [*] --> Provisioning
    Provisioning --> Bootstrapping
    Bootstrapping --> Registering
    Registering --> Ready
    Ready --> Executing
    Executing --> Cleanup
    Cleanup --> Terminating
    Terminating --> [*]

    Bootstrapping --> Failed
    Registering --> Failed
    Executing --> Failed
    Cleanup --> Failed
    Failed --> Terminating
```

The infrastructure system should be able to determine which state a runner is in.

This is important because a runner can fail before GitHub ever assigns a job.

---

## Runner Registration

An ephemeral runner must still register with GitHub before it can receive work.

Registration normally involves:

1. Provision infrastructure.
2. Install the runner software.
3. Obtain a short-lived registration token through the appropriate GitHub API.
4. Configure the runner.
5. Apply labels and runner-group configuration.
6. Start the runner service/process.
7. Wait until GitHub sees the runner as online.
8. Allow the workflow scheduler to assign work.

The registration token should not be treated as a permanent credential.

### Conceptual Bootstrap

```bash
./config.sh \
  --url https://github.com/example-org/example-repo \
  --token "$RUNNER_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "linux,ephemeral,private-network"
```

The exact registration mechanism depends on the runner deployment architecture.

The bootstrap process should avoid writing sensitive registration information into:

- Git history
- Container images
- AMIs
- Terraform state
- Persistent logs
- Shell history

---

## Runner Identity

Runner names should be unique enough to support operational diagnosis.

A useful naming strategy is:

```text
<environment>-<purpose>-<instance-id>
```

For example:

```text
prod-deploy-8f2c1a
integration-test-4d92ab
docker-build-a72e19
```

Avoid embedding secrets or sensitive infrastructure information into runner names.

Runner identity should primarily help operators answer:

- Which workload used this runner?
- Which infrastructure instance created it?
- Which image version did it use?
- Which workflow run was assigned?
- When was it created?
- Why did it terminate?

---

## Runner Labels

Labels allow workflows to select appropriate runners.

Example:

```yaml
jobs:
  integration:
    runs-on:
      - self-hosted
      - linux
      - ephemeral
      - private-network
```

Labels can represent capabilities such as:

- Operating system
- CPU architecture
- GPU availability
- Docker support
- Private-network access
- Environment
- Specialized tooling

Avoid using labels as the only security boundary.

For example:

```text
self-hosted
private-network
production
```

does not automatically guarantee that an untrusted workflow is prevented from accessing production infrastructure.

Runner groups, workflow permissions, environment protection, repository access, and network controls must be considered together.

---

## Runner Groups

Runner groups provide an additional organizational boundary around self-hosted runners.

A production organization may separate:

```text
Runner Groups

├── CI
│   ├── Unit testing
│   └── Integration testing
│
├── Build
│   └── Docker builds
│
├── Staging Deployment
│   └── Private staging network
│
└── Production Deployment
    └── Restricted production network
```

This reduces accidental runner selection and helps enforce administrative boundaries.

A common production model is:

```text
Repository
    ↓
Runner Group
    ↓
Runner Labels
    ↓
Ephemeral Runner
    ↓
Job
```

---

## Immutable Runner Images

The most reliable ephemeral runner architecture starts from an immutable image.

Examples include:

- AWS AMI
- Container image
- Kubernetes Pod template
- Golden VM image

The image should contain stable prerequisites such as:

- Operating system
- Git
- Python
- Docker tooling
- AWS CLI
- Required compilers
- Security agents
- Organization-approved utilities

The runner-specific identity and registration credentials should be injected during startup rather than baked into the image.

### Image Lifecycle

```text
Base OS
   ↓
Security Updates
   ↓
Runner Dependencies
   ↓
CI Tooling
   ↓
Validation
   ↓
Golden Image
   ↓
Ephemeral Runner
```

Do not bake:

- GitHub registration tokens
- AWS access keys
- Repository secrets
- Production credentials
- Long-lived private keys

into the image.

---

## Configuration Drift

Persistent machines naturally accumulate configuration drift.

For example:

```text
Day 1:
Python 3.12
Docker 27
AWS CLI v2

Day 60:
Python upgraded manually
Docker partially upgraded
Extra OS packages installed
Unknown files remain
```

Ephemeral infrastructure reduces this problem because each runner starts from a known image.

A useful model is:

```text
Immutable Image
+
Versioned Bootstrap
+
Declarative Configuration
=
Predictable Runner
```

Runner images should themselves be versioned.

Example:

```text
runner-image:v2026.09.01
runner-image:v2026.09.15
runner-image:v2026.10.01
```

Avoid silently modifying a production image without changing its version.

---

## One Job Per Runner

The strongest isolation model is:

```text
Runner
  ↓
One assigned job
  ↓
Runner destroyed
```

The objective is to avoid:

```text
Runner
  ↓
Job A
  ↓
Job B
  ↓
Job C
```

This limits cross-job contamination.

It also simplifies incident investigation because a runner has a relatively narrow workload history.

---

## Ephemeral Runner and State

A runner should be treated as stateless.

Do not depend on local runner state for:

- Build outputs
- Deployment state
- Test results
- Database state
- Application configuration
- Release metadata

Instead use appropriate external systems:

| Data | Preferred Storage |
|---|---|
| Build artifact | Artifact storage / registry |
| Docker image | Container registry |
| Test report | GitHub artifact |
| Deployment metadata | GitHub / external deployment system |
| Terraform state | Remote state backend |
| Application secrets | Secret manager |
| Build cache | GitHub/cache infrastructure |
| Production data | Database / durable storage |

---

## Workspace Isolation

The workspace contains source code and generated files during a job.

A job might create:

```text
$GITHUB_WORKSPACE
├── source
├── .venv
├── node_modules
├── build
├── coverage
└── temporary files
```

With an ephemeral runner, these disappear with the infrastructure.

However, destruction must actually occur.

If the underlying VM or container is accidentally retained, the supposed isolation guarantee is weakened.

---

## Cleanup

Cleanup should cover:

- Runner deregistration
- Temporary credentials
- Processes
- Containers
- Mounted volumes
- Temporary files
- Cloud resources
- Network interfaces
- Metadata
- Logs containing sensitive information

The infrastructure controller should have a cleanup path even when the workflow fails.

Conceptually:

```text
Job succeeds
     ↓
Cleanup
     ↓
Destroy

Job fails
     ↓
Cleanup
     ↓
Destroy

Runner crashes
     ↓
Controller detects failure
     ↓
Destroy / replace
```

Never design cleanup only around the successful execution path.

---

## Security Model

An ephemeral runner improves isolation, but it does not automatically make a workflow secure.

The runner executes workflow instructions.

If an attacker can modify workflow-controlled commands, the runner may execute those commands with the permissions available to the job.

Security therefore requires defense in depth:

```text
Workflow Security
       ↓
Least-Privilege Permissions
       ↓
Secret Protection
       ↓
Trusted Actions
       ↓
Runner Isolation
       ↓
Network Segmentation
       ↓
Artifact Integrity
       ↓
AWS IAM / OIDC Controls
```

---

## Untrusted Pull Requests

Untrusted pull requests are one of the most important runner-security scenarios.

A pull request can contain changes to:

- Application code
- Test code
- Build scripts
- Dependency configuration
- Dockerfiles
- Workflow-related files in appropriate contexts

A test command such as:

```yaml
- run: pytest
```

executes repository-controlled code.

Therefore:

```text
Pull Request
    ↓
Workflow
    ↓
Runner
    ↓
Repository Code
```

must be treated as an execution boundary.

Do not assume that running tests means only trusted CI infrastructure is being used.

---

## `pull_request` vs `pull_request_target`

`pull_request` is generally the safer default for validating untrusted pull-request code because the workflow executes in the pull-request context.

`pull_request_target` executes with the base repository context and can have access to privileges and secrets that the normal pull-request event does not provide.

The dangerous pattern is effectively:

```text
pull_request_target
        ↓
Checkout untrusted PR code
        ↓
Execute PR-controlled script
        ↓
Access privileged credentials
```

This can turn the workflow into a credential-exposure mechanism.

Ephemeral runners reduce persistence risk, but they do not prevent a malicious job from using credentials available during its execution.

---

## Secrets on Ephemeral Runners

Ephemeral does not mean secret-safe by itself.

A job can potentially expose credentials through:

- Logs
- Process arguments
- Generated files
- Artifacts
- Docker build arguments
- Child processes
- Debug output
- Temporary files

Prefer short-lived credentials whenever possible.

For AWS:

```text
GitHub Actions
      ↓
OIDC identity token
      ↓
AWS STS
      ↓
Assume IAM Role
      ↓
Temporary credentials
      ↓
AWS API
```

This is preferable to storing long-lived AWS access keys as GitHub secrets.

---

## GitHub Token Permissions

Use least privilege.

Example:

```yaml
permissions:
  contents: read
```

For an AWS deployment using OIDC:

```yaml
permissions:
  contents: read
  id-token: write
```

Do not grant:

```yaml
permissions: write-all
```

unless there is a specific, justified requirement.

For sensitive jobs, permissions should be defined as close to the job as practical.

---

## AWS OIDC

A production ephemeral runner should generally avoid long-lived AWS credentials.

Example:

```yaml
permissions:
  contents: read
  id-token: write

steps:
  - name: Configure AWS credentials
    uses: aws-actions/configure-aws-credentials@v5
    with:
      role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
      aws-region: ap-south-1
```

The IAM trust policy should restrict the identities that may assume the role.

The runner itself does not need permanent AWS credentials.

---

## Private Network Access

Ephemeral runners are particularly useful when workloads need private network access.

For example:

```text
GitHub Actions
      ↓
Ephemeral Runner
      ↓
Private VPC
      ├── PostgreSQL
      ├── Redis
      ├── Internal API
      ├── Kafka
      └── Kubernetes API
```

Common implementations include:

- EC2-based runners
- Kubernetes-based runners
- Private subnets
- NAT gateways
- VPC endpoints
- VPN
- Transit Gateway
- VPC peering

Network access should be narrowly scoped.

A runner requiring access to PostgreSQL does not necessarily need unrestricted access to the entire VPC.

---

## Security Groups and Network Segmentation

A useful model is:

```text
Runner Security Group
        ↓
Allow HTTPS → Required AWS services
        ↓
Allow PostgreSQL → Test database
        ↓
Allow Redis → Test Redis
        ↓
Allow Kafka → Test Kafka
```

Avoid broad rules such as:

```text
0.0.0.0/0 → all ports
```

for private runner infrastructure.

Network controls should complement GitHub permissions rather than replace them.

---

## Private Package Registries

A private runner may need access to:

- Private PyPI
- GitHub Packages
- npm registry
- Internal artifact repository
- Docker registry

Credentials should be injected at runtime.

For Python:

```bash
python -m pip install --require-hashes -r requirements.txt
```

or use a lock-file-driven dependency workflow where appropriate.

Do not bake private registry credentials into the runner image.

---

## Python Backend Integration

A typical Django or FastAPI integration-test workflow can look like:

```text
Workflow
   ↓
Ephemeral Runner
   ↓
Checkout
   ↓
Python environment
   ↓
PostgreSQL
   ↓
Redis
   ↓
Migrations
   ↓
pytest
   ↓
Coverage
   ↓
Artifact upload
   ↓
Runner destruction
```

Example:

```yaml
jobs:
  integration:
    runs-on:
      - self-hosted
      - linux
      - ephemeral
      - private-network

    permissions:
      contents: read

    steps:
      - uses: actions/checkout@v5

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: postgresql://app:test@postgres:5432/testdb
        run: python manage.py migrate --noinput

      - name: Run tests
        run: pytest --cov=. --cov-report=xml

      - name: Upload coverage
        if: ${{ !cancelled() }}
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage.xml
```

The exact service networking depends on whether PostgreSQL runs as a service container, another container, or an external private service.

---

## Docker Builds on Ephemeral Runners

Ephemeral runners are well suited to Docker builds because Docker state does not need to remain on the host.

A typical pipeline is:

```text
Source
  ↓
Ephemeral Runner
  ↓
Docker Buildx
  ↓
Cache
  ↓
Image
  ↓
Registry
```

Use BuildKit/Buildx for modern builds.

Example:

```yaml
- name: Set up Buildx
  uses: docker/setup-buildx-action@v3

- name: Build image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: false
    tags: backend:${{ github.sha }}
```

The image should be identified by an immutable identifier such as a commit SHA and preferably a registry digest after publishing.

---

## Cache vs Artifact

A common design mistake is treating runner-local state as a durable build artifact.

These mechanisms serve different purposes:

| Mechanism | Purpose | Durability |
|---|---|---|
| Runner filesystem | Temporary execution state | Ephemeral |
| GitHub cache | Reusable acceleration data | Managed cache |
| Artifact | Job output/result | Durable for retention period |
| Container registry | Deployable image | Durable |
| S3/object storage | Durable deployment artifact | Durable |
| Terraform state | Infrastructure state | Durable |

A cache should never be the authoritative source for a production deployment artifact.

---

## Docker Layer Caching

Ephemeral runners start with an empty local Docker cache.

Without a remote cache:

```text
New Runner
   ↓
No Docker layers
   ↓
Full build
```

Use remote cache mechanisms when build performance matters.

Example:

```yaml
- name: Build image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: ghcr.io/example/backend:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

Cache configuration should be evaluated carefully for:

- Security
- Cache poisoning
- Branch isolation
- Storage cost
- Cache hit rate
- Reproducibility

---

## Build Once, Deploy Many

A strong production model is:

```text
Build
  ↓
Immutable Docker Image
  ↓
Registry
  ↓
Staging
  ↓
Approval
  ↓
Production
```

Avoid:

```text
Build for Staging
        ↓
Build again for Production
```

because the two builds can differ.

The production deployment should reference the same immutable artifact tested in staging.

For Docker:

```text
Image tag
    ↓
Registry
    ↓
Digest
    ↓
Staging
    ↓
Production
```

The digest provides stronger artifact identity than a mutable tag.

---

## Runner Autoscaling

Ephemeral runners naturally support autoscaling.

A simplified architecture is:

```text
Workflow Queue
      ↓
Runner Controller
      ↓
Provision Capacity
      ↓
Ephemeral Runners
      ↓
Execute Jobs
      ↓
Terminate
```

Scaling dimensions can include:

- Number of queued jobs
- Runner labels
- Runner groups
- Job type
- CPU requirements
- Memory requirements
- Network requirements

---

## Cold Start

The major trade-off with ephemeral runners is startup latency.

The lifecycle includes:

```text
Provision VM
    ↓
Boot OS
    ↓
Install/start dependencies
    ↓
Register runner
    ↓
Wait for assignment
    ↓
Execute job
```

If this takes 90 seconds and the job itself takes 30 seconds, startup dominates total runtime.

Reduce cold start through:

- Golden images
- Preinstalled dependencies
- Fast bootstrap
- Smaller images
- Pre-pulled container images where appropriate
- Efficient registration
- Warm capacity for latency-sensitive workloads

---

## Warm Pools

A warm pool can provide some of the latency benefits of persistent infrastructure while preserving disposable workload semantics.

Conceptually:

```text
                    ┌── Warm Runner A
Workflow Queue ────>├── Warm Runner B
                    └── Warm Runner C

Job completes
      ↓
Runner destroyed
      ↓
New runner replenishes warm pool
```

The runners should still be treated as disposable.

A warm pool is not the same as allowing completed jobs to reuse the same runner.

---

## Autoscaling Trade-offs

| Strategy | Startup | Isolation | Cost | Complexity |
|---|---:|---:|---:|---:|
| Persistent runners | Low | Lower | Potential idle cost | Medium |
| Fully ephemeral | Higher | High | Efficient at low utilization | High |
| Warm ephemeral pool | Low/medium | High | Medium | High |
| Large fixed pool | Low | Medium | Higher idle cost | Medium |

The correct strategy depends on workload characteristics rather than isolation alone.

---

## Failure Handling

Provisioning can fail before a workflow receives a runner.

Potential failure points include:

```text
Provisioning
    ↓
Image boot
    ↓
Network
    ↓
Registration
    ↓
Runner readiness
    ↓
Job execution
    ↓
Cleanup
    ↓
Termination
```

Each stage should be observable independently.

For example:

| Failure | Likely Area |
|---|---|
| Runner never appears | Registration |
| Runner appears offline | Connectivity |
| Job stays queued | Labels/groups/capacity |
| Job starts but fails immediately | Bootstrap/image |
| AWS authentication fails | OIDC/IAM |
| Private DB unreachable | Network |
| Cleanup fails | Controller/infrastructure |
| Runner remains online | Lifecycle management |

---

## Runner Readiness

Do not consider a runner ready merely because the operating system has booted.

A readiness check should validate required dependencies.

For example:

```bash
python --version
docker version
aws --version
git --version
```

For private networking:

```bash
getent hosts internal-api.example.internal
```

For AWS identity:

```bash
aws sts get-caller-identity
```

The identity check should only be performed where the runner is expected to have AWS access.

---

## Bootstrap Reliability

Bootstrap should be:

- Idempotent
- Observable
- Fast
- Versioned
- Failure-aware

Avoid large opaque startup scripts.

Prefer:

```text
Image
+
Small bootstrap script
+
Runtime configuration
```

over:

```text
Minimal image
+
Hundreds of package installations
+
Complex startup logic
```

The second model increases cold-start time and introduces more network dependencies.

---

## Runner Metadata

Useful metadata includes:

- Runner ID
- Runner name
- Image version
- Infrastructure instance ID
- Workflow run ID
- Repository
- Job name
- Creation timestamp
- Termination timestamp
- Runner group
- Labels
- Region
- Availability zone

This allows operators to correlate:

```text
GitHub Job
   ↕
Runner
   ↕
Cloud Instance
   ↕
Infrastructure Logs
```

---

## Observability

Monitor both GitHub and infrastructure layers.

### GitHub-side metrics

Track:

- Queue time
- Job duration
- Job failure rate
- Runner availability
- Runner assignment failures
- Workflow duration
- Retry frequency

### Infrastructure metrics

Track:

- Provisioning latency
- Boot latency
- CPU
- Memory
- Disk
- Network
- Instance failures
- Registration failures
- Cleanup failures
- Termination failures

A useful metric is:

```text
Runner Provisioning Time
=
Runner Ready Timestamp
-
Provision Request Timestamp
```

Another:

```text
Job Queue Time
=
Job Start Timestamp
-
Job Queued Timestamp
```

These distinguish GitHub scheduling delays from infrastructure delays.

---

## Logging

Runner infrastructure should provide logs for:

- Bootstrap
- Registration
- Readiness checks
- Infrastructure provisioning
- Cleanup
- Termination

Do not log:

- Tokens
- Secrets
- Private keys
- Full environment dumps
- Sensitive request headers

Avoid commands such as:

```bash
env
```

in production debugging unless the output has been carefully controlled.

---

## Debugging Ephemeral Runners

The runner may disappear before an engineer can connect to it.

Therefore debugging should rely primarily on external observability.

Useful sources include:

- GitHub workflow logs
- Step summaries
- Cloud-init logs
- System logs
- Infrastructure logs
- Runner-controller logs
- Cloud monitoring
- Artifact uploads

For difficult failures, preserve diagnostics before termination.

For example:

```text
Job failure
   ↓
Collect logs
   ↓
Upload diagnostic artifact
   ↓
Destroy runner
```

Do not keep failed runners alive indefinitely just because debugging is convenient.

---

## Failure Diagnostics

A useful diagnostic artifact can contain:

```text
runner-info.txt
system-info.txt
python-version.txt
docker-version.txt
network-checks.txt
disk-usage.txt
process-summary.txt
test-results.xml
```

Sensitive information must be excluded.

---

## Containerized Ephemeral Runners

Ephemeral runners can themselves execute inside containers or Kubernetes Pods.

Architecture:

```text
GitHub Actions
      ↓
Runner Controller
      ↓
Ephemeral Pod
      ↓
Runner Process
      ↓
Job
```

This can provide rapid provisioning and strong lifecycle control.

However, container isolation depends on the surrounding Kubernetes and container security model.

A containerized runner should not automatically be considered equivalent to a fully isolated VM.

---

## Docker Socket Risk

Mounting the host Docker socket:

```text
/var/run/docker.sock
```

into a runner container can provide powerful host-level control.

A workflow with access to that socket may effectively gain control over the Docker host.

Therefore:

```text
Runner Container
      ↓
Docker Socket
      ↓
Host Docker Daemon
      ↓
Potential Host Control
```

should be treated as a privileged security boundary.

Where possible, use isolated build environments and minimize privileged operations.

---

## Kubernetes-Based Runners

Kubernetes can provision runners dynamically.

Conceptually:

```text
GitHub
  ↓
Runner Controller
  ↓
Kubernetes API
  ↓
Runner Pod
  ↓
Job
  ↓
Pod termination
```

Advantages:

- Fast provisioning
- Native autoscaling
- Namespace isolation
- Resource limits
- Declarative infrastructure
- Easy replacement

Consider:

- Kubernetes API permissions
- Pod security
- Service accounts
- Network policies
- Secrets
- Container image trust
- Node isolation
- Privileged containers

---

## Resource Limits

Ephemeral runners should have predictable resource allocation.

For containers or Kubernetes:

```yaml
resources:
  requests:
    cpu: "2"
    memory: "4Gi"
  limits:
    cpu: "4"
    memory: "8Gi"
```

The appropriate values depend on workload characteristics.

Too little capacity causes:

- OOM failures
- Slow builds
- Timeouts
- Test instability

Too much capacity causes:

- Increased cost
- Lower infrastructure utilization

Measure actual workloads before choosing limits.

---

## CPU- and Memory-Heavy Builds

Docker builds, compilation, test matrices, and browser-based E2E tests can require substantially different resources.

Instead of one universal runner label:

```text
ephemeral
```

consider capability labels:

```text
ephemeral-small
ephemeral-medium
ephemeral-large
```

or:

```text
linux
docker
8cpu
16gb
```

Labels should describe capabilities rather than become an uncontrolled taxonomy.

---

## Disk Management

Ephemeral runners can still run out of disk during a single job.

Common causes:

- Docker layers
- Large dependencies
- Browser binaries
- Build artifacts
- Multiple test databases
- Large logs
- Container images

Diagnostics:

```bash
df -h
du -sh "$GITHUB_WORKSPACE" 2>/dev/null || true
docker system df 2>/dev/null || true
```

Avoid aggressive cleanup commands during a job unless their impact is understood.

---

## Network Reliability

Runner startup may depend on:

- GitHub endpoints
- Container registries
- Package registries
- AWS APIs
- Internal services
- DNS
- Proxy services

A private runner with restricted egress can fail before it ever receives a job.

Document required network destinations.

---

## DNS

Private environments often fail because DNS resolution is incomplete rather than because the service itself is unavailable.

Useful checks:

```bash
getent hosts internal-api.example.internal
```

```bash
nslookup internal-api.example.internal
```

where the relevant DNS tooling is installed.

Verify:

- DNS resolver
- Route
- Security group
- NACL
- Service listener
- TLS certificate
- Application health

---

## Runner Security Hardening

A self-hosted ephemeral runner should follow standard host hardening practices:

- Run with least privilege
- Keep OS packages patched
- Minimize installed software
- Disable unnecessary services
- Restrict inbound access
- Restrict outbound access where practical
- Protect metadata endpoints
- Use short-lived credentials
- Monitor infrastructure
- Rotate runner images
- Destroy failed runners
- Avoid persistent secrets

For AWS EC2 runners, consider IMDSv2 and tightly scoped instance roles.

---

## Runner Image Updates

Runner images should be updated through a controlled lifecycle:

```text
New Base Image
    ↓
Security Updates
    ↓
CI Tool Updates
    ↓
Automated Tests
    ↓
Canary Runner Pool
    ↓
Production Rollout
    ↓
Retire Previous Image
```

Do not manually patch individual ephemeral instances.

The instance should be disposable; the image pipeline should be the durable source of configuration.

---

## Supply Chain Security

Runner security also depends on what the runner executes.

Important controls include:

- Pin third-party actions
- Prefer trusted action sources
- Review action dependencies
- Use SHA pinning where required by policy
- Restrict GITHUB_TOKEN permissions
- Validate untrusted input
- Avoid shell interpolation of untrusted data
- Generate SBOMs
- Produce artifact provenance
- Sign important artifacts
- Scan dependencies and images

Ephemeral infrastructure does not compensate for a malicious workflow step.

---

## Third-Party Actions

A third-party action executes code with the permissions granted to its job.

Therefore:

```yaml
permissions:
  contents: read
```

is substantially safer than broad permissions.

Prefer:

```yaml
uses: owner/action@<trusted-commit-sha>
```

when organizational policy requires immutable action references.

Also review:

- Action source
- Maintainer
- Release history
- Dependencies
- Runtime
- Required permissions
- Network behavior
- Secret requirements

---

## Artifact Integrity

A secure pipeline should establish artifact identity before deployment.

Example:

```text
Git Commit
   ↓
Build
   ↓
Docker Image
   ↓
Digest
   ↓
SBOM
   ↓
Provenance
   ↓
Staging
   ↓
Approval
   ↓
Production
```

The runner should not be the system of record for the artifact.

The registry or artifact store should be the durable source.

---

## Production Deployment Runners

Deployment runners deserve stronger controls than ordinary CI runners.

A useful separation is:

```text
CI Runner Group
    ↓
Tests / Build

Deployment Runner Group
    ↓
Staging / Production deployment
```

Production runners may require:

- Restricted repositories
- Restricted workflows
- Restricted runner groups
- Dedicated AWS IAM roles
- Private network access
- Environment approvals
- Stronger audit logging

---

## Deployment Concurrency

Production deployment jobs should not race.

Example:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

This prevents multiple production deployments from executing concurrently.

For pull requests, cancellation can often be appropriate:

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

The policy should reflect the workload.

Do not blindly use `cancel-in-progress: true` for deployments where cancellation could leave infrastructure in an uncertain state.

---

## Environment Protection

GitHub Environments can provide:

- Required reviewers
- Environment secrets
- Deployment history
- Deployment protection

A production flow can be:

```text
Build
  ↓
Staging
  ↓
Health Validation
  ↓
Production Approval
  ↓
Production Deployment
  ↓
Health Validation
```

The approval should happen before privileged production credentials become available to the deployment job.

---

## Database Migrations

Ephemeral runners do not change database migration safety requirements.

A production deployment may need:

```text
Expand
  ↓
Deploy compatible application
  ↓
Backfill
  ↓
Switch application behavior
  ↓
Contract
```

Avoid assuming:

```text
Deploy
  ↓
Destructive migration
  ↓
Instant rollback
```

is safe.

Database changes often have a longer compatibility lifecycle than application binaries.

---

## Celery and Background Workers

A deployment involving Django/FastAPI plus Celery should account for:

```text
Web Application
      ↓
Redis / Broker
      ↓
Celery Workers
      ↓
Database
```

The deployment runner should not assume that replacing the web application alone completes the deployment.

Consider:

- Worker compatibility
- Queue draining
- Task serialization
- Database schema compatibility
- Long-running tasks
- Worker restart strategy

---

## Kafka

Kafka-backed systems introduce additional compatibility concerns.

A deployment may involve:

```text
Producer
   ↓
Kafka
   ↓
Consumer
```

The new application version must remain compatible with messages produced by currently running services where rolling deployment is used.

Ephemeral runners are only responsible for orchestration; application-level compatibility still determines deployment safety.

---

## Terraform Deployments

Terraform execution from ephemeral runners is useful because no persistent runner state is required.

Use remote state.

```text
Ephemeral Runner
      ↓
terraform plan
      ↓
Saved plan
      ↓
Review / Approval
      ↓
terraform apply
      ↓
Remote State
```

Do not rely on local Terraform state surviving runner destruction.

Protect:

- State storage
- State locking
- IAM permissions
- Plan artifacts
- Secrets
- Provider credentials

---

## CloudFormation Deployments

CloudFormation also fits ephemeral runners well because stack state lives in AWS rather than the runner.

The runner should invoke:

```bash
aws cloudformation deploy ...
```

while AWS maintains durable stack state.

Use:

- Change sets where appropriate
- IAM least privilege
- OIDC
- Stack policies
- Drift detection
- Rollback controls

---

## Rolling Deployments

Rolling deployments replace instances or tasks incrementally.

```text
Version A A A A
       ↓
Version B A A A
       ↓
Version B B A A
       ↓
Version B B B A
       ↓
Version B B B B
```

The CI/CD runner orchestrates the deployment, but service health determines whether the rollout should continue.

---

## Blue-Green Deployments

Blue-green maintains two environments:

```text
Blue  → Current
Green → New
```

Traffic switches only after validation.

```text
Build
  ↓
Deploy Green
  ↓
Validate
  ↓
Switch Traffic
  ↓
Green becomes Active
```

The previous environment can remain available for rollback.

The trade-off is additional infrastructure capacity.

---

## Canary Deployments

Canary deployment gradually exposes traffic to a new version.

```text
Version A → 95%
Version B → 5%
```

Then:

```text
A → 75%
B → 25%
```

and eventually:

```text
A → 0%
B → 100%
```

Promotion should be based on measurable health criteria such as:

- Error rate
- Latency
- Saturation
- Application metrics
- Business metrics

---

## Zero-Downtime Requirements

Zero downtime is not achieved simply by using ephemeral runners.

The deployed application must support:

- Health checks
- Readiness checks
- Graceful shutdown
- Connection draining
- Backward-compatible APIs
- Database compatibility
- Correct deployment ordering

For a Django/FastAPI application behind Nginx or a load balancer:

```text
Load Balancer
      ↓
Healthy Instances
      ↓
Application
      ↓
Database / Redis / Kafka
```

A runner only orchestrates the transition.

---

## Rollback

A rollback should identify the exact previous artifact.

Example:

```text
Production
    ↓
Current Digest
    ↓
Deployment Failure
    ↓
Previous Known-Good Digest
    ↓
Redeploy
```

Avoid rebuilding an old Git commit during an incident when the original artifact is available.

The original artifact is more reproducible.

---

## Rollback Limitations

Application rollback does not automatically mean database rollback.

For example:

```text
Application v2
    ↓
Migration adds nullable column
    ↓
Deploy fails
    ↓
Application v1
```

may be safe.

But:

```text
Application v2
    ↓
Migration drops column
    ↓
Application v1
```

may not be safe.

Database changes must therefore be designed for rollback compatibility.

---

## Disaster Recovery

The runner infrastructure itself should be replaceable.

Important dependencies should not depend on one runner instance.

For example:

```text
GitHub
   ↓
Runner Controller
   ↓
AWS / Kubernetes
   ↓
Ephemeral Runners
```

If a runner disappears, another runner should be able to execute the workload.

For critical CI/CD infrastructure, consider:

- Multiple availability zones
- Multiple runner pools
- Automated replacement
- Versioned images
- Infrastructure as code
- Remote state
- Backup of required durable configuration
- Recovery runbooks

---

## High Availability

High availability for runners is different from application HA.

The objective is generally:

```text
Runner Failure
    ↓
Detect
    ↓
Replace
    ↓
Continue / Retry
```

rather than keeping one specific runner alive.

A runner is disposable infrastructure.

The runner control plane and provisioning system are the more important availability dependencies.

---

## Cost Optimization

Ephemeral runners can reduce idle compute cost because capacity exists primarily when jobs are running.

However, excessive provisioning can become expensive.

Cost drivers include:

- VM runtime
- Kubernetes compute
- NAT gateways
- Storage
- Container registry
- Logs
- Data transfer
- EBS volumes
- Cloud load balancers
- Warm pools

Optimize by:

- Right-sizing runners
- Reducing cold-start time
- Using caching
- Parallelizing only where useful
- Avoiding oversized runners
- Reusing immutable base images
- Cleaning resources reliably
- Choosing appropriate autoscaling policies

---

## Performance Optimization

A useful pipeline metric is:

```text
Total CI Time
=
Queue Time
+
Runner Provisioning
+
Dependency Setup
+
Build/Test
+
Artifact Transfer
+
Cleanup
```

Optimization should target the dominant component.

For example, if:

```text
Provisioning = 20 sec
Dependency setup = 180 sec
Tests = 60 sec
```

optimizing runner boot time by 10 seconds has less impact than improving dependency caching.

---

## Cache Strategy

Use caches for data that is expensive to recreate but safe to reuse.

Good candidates:

- Python package downloads
- npm dependencies
- Docker layers
- Compiler caches

Avoid caching sensitive or environment-specific state.

A cache should never be trusted as an authoritative source of deployment state.

---

## Reliability Principles

A production ephemeral runner platform should follow these principles:

1. Runner creation must be repeatable.
2. Runner configuration must be versioned.
3. Runner identity must be observable.
4. Runner failures must be replaceable.
5. Runner state must not be required for correctness.
6. Credentials should be short-lived.
7. Cleanup must happen after success and failure.
8. Critical artifacts must be externalized.
9. Infrastructure should be declarative.
10. Failed runners should not remain indefinitely.

---

## Troubleshooting Methodology

Use the following model:

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

This prevents random configuration changes during incidents.

---

## Runner Never Appears

### Symptom

A workflow remains queued and no runner appears online.

### Possible Causes

- Provisioning failure
- Bootstrap failure
- Registration token failure
- Network failure
- Incorrect repository/org scope
- Runner controller failure

### Isolation

Check infrastructure provisioning first.

Then check:

```text
Instance exists?
    ↓
Bootstrap completed?
    ↓
Runner installed?
    ↓
Registration succeeded?
    ↓
Runner online?
```

### Prevention

Expose provisioning and registration metrics independently.

---

## Runner Appears Offline

### Possible Causes

- Process stopped
- Network connectivity
- DNS failure
- Proxy configuration
- Host failure
- Runner software failure

Check infrastructure and runner logs.

Do not immediately modify the runner manually if the architecture is designed around replacement.

Replacing a disposable runner is usually preferable to repairing it.

---

## Job Remains Queued

Possible causes:

- No runner with matching labels
- Runner group inaccessible to repository
- Runner pool exhausted
- Runner offline
- Incorrect `runs-on`
- Capacity controller failure

Example:

```yaml
runs-on:
  - self-hosted
  - linux
  - ephemeral
  - private-network
```

Every required label must match an available runner.

---

## Registration Failures

Check:

- Registration token validity
- Repository/organization URL
- Runner permissions
- Network connectivity
- System clock
- Runner version
- Bootstrap logs

Do not log registration tokens while debugging.

---

## AWS OIDC Failures

Check:

```bash
aws sts get-caller-identity
```

If authentication occurs through OIDC, validate:

- `id-token: write`
- IAM OIDC provider
- Trust policy
- Repository identity
- Branch/environment conditions
- AWS account
- Role ARN
- Region
- Token audience

The failure may occur before AWS authorization is attempted.

---

## Private Network Failures

Check in order:

```text
DNS
 ↓
Route
 ↓
Security Group
 ↓
NACL
 ↓
TLS
 ↓
Application Listener
 ↓
Application Health
```

For example:

```bash
getent hosts internal-db.example.internal
```

Then test connectivity using an appropriate client rather than relying solely on ping.

---

## Docker Build Failures

Check:

- Docker daemon
- Buildx
- Disk space
- Base image access
- Registry access
- Build context
- `.dockerignore`
- Build secrets
- Cache configuration

Useful commands:

```bash
docker version
docker buildx version
docker system df
```

---

## Cache Failures

A cache miss is not necessarily a pipeline failure.

Distinguish:

```text
Cache miss
    ↓
Build still succeeds
```

from:

```text
Cache corruption
    ↓
Build fails
```

If the cache is suspected, temporarily disable or bypass it to isolate the problem.

---

## Cleanup Failures

Cleanup failure is operationally significant.

A failed cleanup can result in:

- Orphaned VM
- Orphaned disk
- Orphaned network interface
- Registered offline runner
- Cost leakage
- Security exposure

The provisioning system should periodically reconcile:

```text
Infrastructure Inventory
        vs
GitHub Runner Inventory
```

and identify resources that no longer have a valid lifecycle owner.

---

## GitHub CLI

GitHub CLI is useful for operational workflows.

List workflows:

```bash
gh workflow list
```

Run a workflow:

```bash
gh workflow run ci.yml
```

List recent runs:

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

Rerun a failed run:

```bash
gh run rerun <run-id>
```

List artifacts:

```bash
gh run view <run-id> --json artifacts
```

The CLI should complement, not replace, structured monitoring and infrastructure observability.

---

## Production Architecture

A mature architecture can look like:

```mermaid
flowchart LR
    A[Developer / Pull Request] --> B[GitHub Actions]
    B --> C[CI Workflow]

    C --> D[Runner Controller]
    D --> E[Ephemeral CI Runner]

    E --> F[Lint]
    E --> G[Unit Tests]
    E --> H[Integration Tests]
    E --> I[Security Scan]
    E --> J[Docker Build]

    H --> K[(PostgreSQL)]
    H --> L[(Redis)]

    J --> M[Container Registry]

    M --> N[Staging]
    N --> O[Health Validation]
    O --> P[Approval]
    P --> Q[Production]

    Q --> R[Monitoring]
    Q --> S[Rollback]

    E --> T[OIDC]
    T --> U[AWS STS]
    U --> V[IAM Role]
    V --> M
    V --> Q
```

The important separation is:

```text
GitHub
   ↓
Workflow Orchestration
   ↓
Disposable Compute
   ↓
Durable External Systems
```

The runner should not become the durable system of record.

---

## Enterprise Runner Architecture

At organizational scale, runner infrastructure can be divided by trust and capability:

```text
Enterprise
│
├── Standard CI
│   └── Ephemeral Linux runners
│
├── Build
│   └── Ephemeral Docker-capable runners
│
├── Private Integration
│   └── Ephemeral VPC-connected runners
│
├── Staging Deployment
│   └── Restricted deployment runners
│
└── Production Deployment
    └── Highly restricted ephemeral runners
```

This provides workload isolation without requiring every repository to build its own runner infrastructure.

---

## Failure Domains

Treat these as separate failure domains:

```text
GitHub Control Plane
        ↓
Runner Controller
        ↓
Cloud Infrastructure
        ↓
Runner Image
        ↓
Runner Network
        ↓
Job Execution
        ↓
External Dependency
```

For example, if PostgreSQL is unavailable, replacing the runner does not solve the problem.

Likewise, if the runner image is broken, retrying the same image repeatedly does not solve the root cause.

---

## Governance

Enterprise runner governance should define:

- Approved runner images
- Approved runner groups
- Label conventions
- Supported operating systems
- Patch policy
- Image lifecycle
- Maximum runner lifetime
- Network boundaries
- AWS IAM policies
- Repository access
- Action allowlists
- Secret policies
- Logging requirements
- Incident response
- Cleanup requirements

A centralized platform team can provide the infrastructure while application teams consume standardized runner capabilities.

---

## Runner Image Governance

A runner image should have an owner and lifecycle.

Example:

```text
runner-linux-v12
    ↓
Security validation
    ↓
CI compatibility tests
    ↓
Canary
    ↓
Organization rollout
    ↓
runner-linux-v13
    ↓
v12 retirement
```

Do not allow old runner images to remain indefinitely.

Old images may contain:

- Vulnerable packages
- Outdated Docker
- Unsupported Python
- Vulnerable system libraries
- Outdated runner software

---

## Common Mistakes

### Treating Ephemeral as Automatically Secure

Ephemeral infrastructure reduces persistence risk but does not prevent malicious workflow execution.

### Storing Credentials in Images

Runner images must not contain long-lived secrets.

### Giving Production Runners Broad Network Access

Use network segmentation and narrowly scoped security groups.

### Giving Jobs Excessive Permissions

Use job-level least privilege.

### Using `pull_request_target` Carelessly

Never combine privileged execution with untrusted code without a deliberate security model.

### Relying on Runner Filesystem State

Anything required after the job must be stored externally.

### Rebuilding for Each Environment

Promote the same immutable artifact.

### Ignoring Cleanup Failures

Orphaned infrastructure creates both cost and security problems.

### Using Persistent Runners for Untrusted Code

A compromised job can leave behind state that affects future jobs.

### Debugging by Manually Modifying Runners

Changes disappear and create configuration drift. Fix the image or bootstrap process instead.

---

## Production Checklist

### Runner Lifecycle

- [ ] Runner provisioning is automated.
- [ ] Runner registration is automated.
- [ ] Runner identity is observable.
- [ ] Runner lifecycle is versioned.
- [ ] Successful runners are terminated.
- [ ] Failed runners are also terminated.
- [ ] Orphaned resources are periodically reconciled.

### Security

- [ ] GITHUB_TOKEN permissions are minimized.
- [ ] Production credentials are short-lived.
- [ ] AWS authentication uses OIDC where appropriate.
- [ ] IAM trust policies are restricted.
- [ ] Third-party actions are reviewed.
- [ ] Sensitive actions are pinned according to policy.
- [ ] Untrusted pull requests do not receive unnecessary privileges.
- [ ] Production runners have restricted network access.

### Infrastructure

- [ ] Runner images are immutable.
- [ ] Image versions are tracked.
- [ ] Images are regularly patched.
- [ ] Infrastructure is declarative.
- [ ] Resource limits are appropriate.
- [ ] Disk capacity is monitored.
- [ ] DNS and routing are validated.

### CI/CD

- [ ] Build artifacts are externalized.
- [ ] Docker images are immutable.
- [ ] Staging and production promote the same artifact.
- [ ] Deployment concurrency is controlled.
- [ ] Production deployments are protected.
- [ ] Health validation is automated.
- [ ] Rollback artifacts are retained.

### Operations

- [ ] Provisioning latency is measured.
- [ ] Queue time is measured.
- [ ] Registration failures are observable.
- [ ] Cleanup failures are observable.
- [ ] Diagnostic artifacts can be collected safely.
- [ ] Incident runbooks exist.
- [ ] Recovery does not depend on a specific runner instance.

---

## Senior-Level Design Principles

### Disposable Compute

A runner should be replaceable without affecting pipeline correctness.

### Immutable Infrastructure

Fix the image or bootstrap definition instead of manually repairing individual runners.

### Externalize State

Artifacts, Terraform state, deployment metadata, and application state must live outside the runner.

### Minimize Privilege

Runner isolation is only effective when the job itself has appropriately limited permissions.

### Separate Trust Zones

CI, integration testing, staging deployment, and production deployment do not necessarily belong on the same runner pool.

### Prefer Short-Lived Credentials

Use OIDC and temporary credentials where supported.

### Build Once, Promote Many

The artifact tested in staging should be the artifact deployed to production.

### Observe the Lifecycle

Provisioning, registration, execution, cleanup, and termination are all operational states that require visibility.

### Automate Recovery

A failed runner should generally trigger replacement rather than manual repair.

### Design for Failure

Assume that runners, images, networks, registries, and external services can fail independently.

---

## Interview Preparation

### Why use ephemeral runners?

They reduce cross-job persistence, limit contamination, simplify replacement, and work well with autoscaling.

### Are ephemeral runners automatically secure?

No. They reduce persistence risk but do not solve excessive permissions, secret exposure, malicious workflow code, or network overexposure.

### What happens when an ephemeral runner finishes?

The runner should be removed from service and its underlying compute should be terminated according to the provisioning architecture.

### Why not use persistent runners everywhere?

Persistent runners can retain state between jobs and create larger security and reliability blast radii.

### How would you allow private database access?

Provision runners inside an appropriate private network and allow only the required connectivity through routing, security groups, NACLs, DNS, and application-level authentication.

### How would you authenticate to AWS?

Prefer GitHub OIDC to AWS STS with a narrowly scoped IAM role rather than long-lived AWS access keys.

### How do you debug a runner that disappears after failure?

Collect diagnostics externally before termination and use infrastructure logs, GitHub logs, runner-controller logs, and metadata correlation.

### How would you scale runners?

Use an autoscaling controller driven by workflow demand, with immutable runner images and disposable lifecycle management.

### How do you prevent deployment races?

Use GitHub Actions concurrency controls and design deployment operations to be idempotent.

### How do you roll back?

Redeploy the previously validated immutable artifact rather than rebuilding an older source revision during an incident.

### What is the most important architectural principle?

The runner is disposable compute. Durable state belongs in durable external systems.

---

## Production Reference Flow

A production-grade workflow can be understood as:

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
Immutable Docker Image
      ↓
Registry
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
Rollback if required
```

The runners supporting these stages should be disposable:

```text
Job
 ↓
Fresh Runner
 ↓
Execute
 ↓
Persist Required Outputs
 ↓
Destroy
```

This separation allows the CI/CD platform to scale without making individual runner machines part of the system's correctness.

## Key Takeaways

- Ephemeral runners provide disposable execution environments that reduce cross-job contamination and work naturally with autoscaling.
- Runner security still depends on least-privilege permissions, protected secrets, trusted workflows, restricted network access, and safe handling of untrusted code.
- Treat runners as stateless compute: durable artifacts, deployment state, Terraform state, and application data must live outside the runner.
- Production runner platforms should use immutable images, automated provisioning, lifecycle observability, reliable cleanup, and automatic replacement rather than manual repair.
- A mature CI/CD architecture separates runner pools by trust and capability while promoting immutable artifacts from build through staging to production.