# 07- Runners

## Overview

A GitHub Actions runner is the execution environment that runs the steps defined by a workflow job.

The runner is where commands such as:

```bash
pytest
docker build
terraform plan
aws ecs update-service
```

actually execute.

The fundamental execution model is:

```text
Workflow
   ↓
Job
   ↓
Runner
   ↓
Steps
   ├── Shell commands
   └── Actions
```

Runner architecture becomes increasingly important as CI/CD systems grow. A small project can rely almost entirely on GitHub-hosted runners, while a production organization may require:

- Specialized operating systems
- Private-network access
- Custom build tools
- GPU or high-memory workloads
- Internal package repositories
- Network-isolated deployment environments
- Ephemeral self-hosted runners
- Runner groups and governance
- Autoscaling
- Cost controls

For a senior backend engineer, runner selection is not merely a configuration choice. It is a decision involving **security boundaries, network topology, reproducibility, performance, availability, scalability, and cost**.

## What Is a Runner?

A runner is a machine or execution environment that receives a GitHub Actions job and executes its steps.

For example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - run: pytest
```

The important configuration is:

```yaml
runs-on: ubuntu-latest
```

This tells GitHub Actions which runner environment should execute the job.

The runner then:

1. Receives the job.
2. Prepares the execution environment.
3. Checks out or accesses repository content through workflow steps.
4. Executes actions and shell commands.
5. Produces logs and outputs.
6. Uploads artifacts or other results when requested.
7. Reports the final job status.

---

## Runner Responsibilities

A runner provides the execution substrate for the job.

Depending on the runner type, it may provide:

- Operating system
- CPU
- Memory
- Filesystem
- Network connectivity
- Preinstalled software
- Container runtime
- Git
- Shell
- Language runtimes
- Build tools
- Access to private infrastructure

The workflow controls what happens on the runner, while the runner determines the environment in which that work occurs.

This distinction matters:

```text
Workflow configuration
        ↓
Defines work

Runner
        ↓
Provides environment to execute work
```

---

## Runner Architecture

A simplified GitHub Actions architecture is:

```mermaid
flowchart TD
    A[GitHub Repository] --> B[Workflow]
    B --> C[Job]
    C --> D[Runner Selection]
    D --> E[GitHub-hosted Runner]
    D --> F[Self-hosted Runner]

    E --> G[Execute Steps]
    F --> H[Execute Steps]

    G --> I[Logs / Artifacts / Status]
    H --> I
```

For GitHub-hosted execution:

```text
GitHub
  ↓
Runner allocation
  ↓
Temporary execution environment
  ↓
Job
  ↓
Runner cleanup
```

For self-hosted execution:

```text
GitHub
  ↓
Runner service
  ↓
Organization-controlled machine
  ↓
Job
```

The operational and security implications are substantially different.

---

## Runner Selection with `runs-on`

The simplest configuration is:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
```

Other common operating system families include:

```yaml
runs-on: ubuntu-latest
```

```yaml
runs-on: windows-latest
```

```yaml
runs-on: macos-latest
```

The appropriate choice depends on the application and tooling.

For most Python backend CI workloads, Linux is generally the natural environment because production systems commonly use Linux containers and Linux-based infrastructure.

---

## GitHub-Hosted Runners

GitHub-hosted runners are managed by GitHub.

They provide an ephemeral execution environment for a workflow job without requiring the organization to maintain the underlying machine.

Typical flow:

```text
Job queued
   ↓
GitHub allocates hosted runner
   ↓
Runner executes job
   ↓
Job completes
   ↓
Runner environment is discarded
```

This model is particularly useful for standard CI workloads.

### Advantages

- Minimal infrastructure management
- No runner patching responsibility
- Easy scaling across concurrent jobs
- Standardized environments
- Ephemeral execution
- Simple integration with GitHub Actions
- Good fit for public and standard backend CI workloads

### Limitations

- Limited control over infrastructure
- Cannot directly provide arbitrary private-network access
- Hardware options are constrained by the available runner types
- Jobs are subject to GitHub Actions capacity, quotas, and platform limits
- Large or specialized workloads may require different infrastructure

---

## Why Ephemeral Execution Matters

An ephemeral runner starts with a relatively clean environment for a job and is discarded afterward.

This provides an important isolation property:

```text
Job A
  ↓
Runner A
  ↓
Discard

Job B
  ↓
Runner B
```

Job B does not normally inherit arbitrary files or processes left behind by Job A.

This reduces contamination between jobs.

For CI security, this is particularly useful when workflows execute dependencies or repository-controlled code.

---

## Runner Isolation

Runner isolation should be considered at multiple levels:

```text
Workflow
   ↓
Job
   ↓
Runner
   ↓
Process
   ↓
Container
```

Each layer provides different isolation characteristics.

A container can isolate an application process, but it does not automatically make a self-hosted runner safe for untrusted workloads.

A senior engineer should distinguish:

```text
Container isolation
≠
Runner isolation
≠
Network isolation
≠
Credential isolation
```

Production security requires considering all of them together.

---

## GitHub-Hosted Runner Environment

A GitHub-hosted runner generally provides a preconfigured operating system environment with common development tools.

However, workflows should avoid assuming that arbitrary software will always exist unless it is part of the documented runner environment.

For reproducibility, explicitly install or configure important dependencies.

For example:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
```

rather than relying on whichever Python version happens to be available on the runner.

The same principle applies to:

- Node.js
- Java
- Terraform
- Docker tooling
- AWS CLI
- Other build dependencies

---

## Runner Labels

Self-hosted runners can have labels.

For example:

```text
self-hosted
linux
x64
private-network
```

A workflow can target matching labels:

```yaml
jobs:
  deploy:
    runs-on:
      - self-hosted
      - linux
      - private-network
```

The runner must have all required labels.

Conceptually:

```text
Job requirements
      ↓
Label matching
      ↓
Eligible runners
      ↓
Runner selected
```

Labels are useful for expressing infrastructure capabilities.

---

## Runner Labels as Capability Contracts

Instead of using labels only as names, treat them as capability declarations.

For example:

```text
self-hosted
linux
x64
docker
private-network
```

can communicate:

```text
Linux
+
x64
+
Docker available
+
Private network access
```

A deployment job can then explicitly require the capabilities it needs.

Avoid labels such as:

```text
runner1
runner2
machine3
```

when they provide no meaningful architectural information.

Prefer capability-oriented labels.

---

## Runner Groups

Runner groups allow organizations to control which repositories or workflows can use specific self-hosted runners.

A conceptual organization might have:

```text
Runner Group: Public CI
    ↓
Standard CI repositories

Runner Group: Internal Build
    ↓
Trusted internal repositories

Runner Group: Production Deploy
    ↓
Restricted deployment repositories
```

Runner groups are especially important when runners have access to sensitive infrastructure.

A production deployment runner should not automatically be available to every repository in an organization.

---

## Self-Hosted Runners

A self-hosted runner is infrastructure operated by the organization rather than GitHub.

It can run on:

- Physical servers
- Virtual machines
- Cloud instances
- Private data centers
- Kubernetes infrastructure
- Specialized compute infrastructure

The architecture becomes:

```text
GitHub Actions
      ↓
Self-hosted runner
      ↓
Organization infrastructure
      ↓
Private services
```

This is useful when workflows require capabilities that GitHub-hosted runners cannot provide.

---

## When to Use Self-Hosted Runners

Self-hosted runners are appropriate when there is a concrete infrastructure requirement.

Examples include:

- Access to private databases
- Internal package registries
- Private APIs
- VPC-only infrastructure
- Custom operating systems
- Specialized hardware
- Large compute workloads
- Internal security tooling
- Network-restricted deployment systems
- Persistent build infrastructure where justified

Do not adopt self-hosted runners merely because they appear more customizable.

They introduce infrastructure and security responsibilities.

---

## Self-Hosted Runner Advantages

| Advantage | Engineering Benefit |
|---|---|
| Private networking | Access internal infrastructure |
| Custom software | Install organization-specific tools |
| Hardware control | Optimize CPU, memory, disk, GPU |
| Network control | Use private routing and firewalls |
| Persistent resources | Useful for specialized workloads |
| Custom security controls | Integrate with internal infrastructure |

---

## Self-Hosted Runner Limitations

| Limitation | Operational Impact |
|---|---|
| Patch management | Organization owns OS maintenance |
| Security | Runner can become a privileged attack surface |
| Availability | Runner infrastructure can fail |
| Scaling | Organization must provide capacity |
| Monitoring | Runner health must be monitored |
| Cost | VM, storage, networking, and operations cost |
| Isolation | Persistent runners require careful cleanup |
| Maintenance | Software drift must be controlled |

The main trade-off is:

```text
More infrastructure control
        ↓
More operational responsibility
```

---

## Persistent vs Ephemeral Self-Hosted Runners

### Persistent Runner

A persistent runner remains available for multiple jobs.

```text
Runner
  ↓
Job A
  ↓
Job B
  ↓
Job C
  ↓
Job D
```

Advantages:

- Lower startup overhead
- Can retain locally installed tools
- Can be useful for specialized workloads

Risks:

- Workspace contamination
- Credential remnants
- Process leakage
- Docker state leakage
- Dependency drift
- Cross-job data exposure

### Ephemeral Runner

An ephemeral runner is created for a job or limited execution lifecycle and then destroyed.

```text
Runner
  ↓
Job
  ↓
Destroy
```

Advantages:

- Better isolation
- Cleaner state
- Reduced cross-job contamination
- Easier security reasoning

For sensitive workloads, ephemeral infrastructure is generally easier to secure.

---

## Persistent Runner Contamination

Consider a persistent runner:

```text
Job A
  ↓
pip install package-x
  ↓
Environment modified

Job B
  ↓
Unexpected package-x available
```

Or:

```text
Job A
  ↓
Docker image/cache/temp files
  ↓
Runner retains state

Job B
  ↓
Unexpected state
```

This creates reproducibility problems.

A persistent runner should therefore have explicit cleanup and hardening procedures.

---

## Runner Workspace

A runner provides a workspace where repository files and build output can be created.

A job may produce:

```text
workspace/
├── source/
├── .venv/
├── build/
├── coverage.xml
└── logs/
```

Do not assume that files in a workspace are available to a different job.

Cross-job file transfer should use:

```text
Artifacts
```

or another explicit data-transfer mechanism.

---

## Runner Context

GitHub Actions exposes runner information through the `runner` context.

Examples include:

```yaml
- name: Display runner information
  run: |
    echo "OS: ${{ runner.os }}"
    echo "Architecture: ${{ runner.arch }}"
    echo "Runner name: ${{ runner.name }}"
```

The `runner` context is useful for diagnostics and conditional behavior.

For example:

```yaml
if: runner.os == 'Windows'
```

should be used only when platform-specific behavior is genuinely required.

Avoid making workflows unnecessarily platform-dependent.

---

## Operating System Differences

A workflow that works on Linux may behave differently on Windows.

Differences include:

- Shell syntax
- Path separators
- Environment variables
- File permissions
- Executable formats
- Installed tooling
- Case sensitivity
- Docker behavior

For example:

```yaml
- name: Run script
  shell: bash
  run: ./scripts/ci.sh
```

is naturally suited to Linux environments.

Cross-platform workflows should explicitly account for these differences rather than assuming shell behavior is universal.

---

## Runner Architecture for Python Backends

A standard Python backend pipeline can use GitHub-hosted Linux runners:

```mermaid
flowchart LR
    A[GitHub Repository] --> B[CI Workflow]
    B --> C[Lint Job]
    B --> D[Unit Test Job]
    B --> E[Integration Test Job]

    C --> F[Ubuntu Runner]
    D --> G[Ubuntu Runner]
    E --> H[Ubuntu Runner]

    H --> I[PostgreSQL]
    H --> J[Redis]
```

This provides separate execution environments for:

- Ruff or other linting
- pytest unit tests
- Integration tests
- PostgreSQL
- Redis

The jobs can execute concurrently when dependencies permit.

---

## Containers on Runners

A runner can execute Docker workloads.

For example:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - name: Build image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: false
          tags: backend:${{ github.sha }}
```

The runner provides the environment in which Docker tooling executes.

The architecture is:

```text
GitHub-hosted runner
        ↓
Docker / Buildx
        ↓
Backend image
        ↓
Registry or artifact
```

---

## Runner and Docker Security

A Docker build is not automatically isolated from the runner.

A malicious or compromised build process can potentially interact with the runner environment according to the permissions available to it.

Therefore:

```text
Docker container
≠
Complete security boundary
```

Be particularly careful when:

- Building untrusted pull requests
- Running privileged Docker operations
- Using self-hosted runners
- Mounting host directories
- Exposing Docker sockets
- Providing cloud credentials

Never assume that placing an untrusted command inside a container makes a privileged runner safe.

---

## Service Containers and Runners

Integration tests often require:

```text
Application
PostgreSQL
Redis
```

A GitHub-hosted runner can host service containers for the job.

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
          POSTGRES_DB: app_test
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - run: pip install -r requirements.txt

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379/0
        run: pytest tests/integration
```

Runner networking and service-container networking must be understood together.

---

## Private Network Access

One of the most common reasons to introduce self-hosted runners is private network access.

For example:

```mermaid
flowchart LR
    A[GitHub Actions] --> B[Self-hosted Runner]
    B --> C[Private VPC]
    C --> D[Internal API]
    C --> E[Private Database]
    C --> F[Internal Registry]
```

This can be useful for:

- Internal deployment APIs
- Private databases
- Internal package registries
- Private Kubernetes clusters
- Internal services

However, it also creates a major security boundary.

If untrusted workflow code can execute on the runner, that code may gain access to resources reachable from the runner.

---

## Self-Hosted Runner Security Boundary

Consider:

```text
Pull Request
    ↓
Workflow
    ↓
Self-hosted runner
    ↓
Private VPC
    ↓
Production resources
```

If the pull request contains malicious code and the workflow executes it on a privileged self-hosted runner, the runner becomes an entry point into the private network.

This is why sensitive self-hosted runners should not generally execute arbitrary untrusted pull request code.

Use separate runner groups and workflow policies for trusted workloads.

---

## `pull_request` and Self-Hosted Runners

A pull request can contain code controlled by contributors.

Therefore, a dangerous architecture is:

```text
Untrusted PR
    ↓
Privileged self-hosted runner
    ↓
Production network
```

Safer architecture:

```text
Untrusted PR
    ↓
GitHub-hosted isolated runner
    ↓
Tests
```

Then:

```text
Trusted main branch
    ↓
Restricted deployment workflow
    ↓
Privileged self-hosted runner
```

This separates untrusted validation from privileged deployment.

---

## Runner Labels for Security

A useful design can define:

```text
ci-linux
ci-windows
private-deploy
production-deploy
```

Then restrict sensitive workflows to:

```yaml
runs-on:
  - self-hosted
  - linux
  - production-deploy
```

This makes the intended execution boundary visible.

Labels alone are not a complete security mechanism, but they are useful when combined with runner groups, repository access controls, workflow permissions, and network controls.

---

## Runner Groups for Production

A production runner group should have restricted access.

Conceptually:

```text
Organization
│
├── Standard CI Runners
│   └── Many repositories
│
├── Internal Build Runners
│   └── Selected repositories
│
└── Production Deployment Runners
    └── Restricted repositories/workflows
```

This reduces the blast radius of a compromised repository.

---

## Runner Registration

A self-hosted runner must be registered with GitHub.

The registration process establishes the relationship between:

```text
GitHub repository / organization
        ↕
Self-hosted runner
```

The runner software then communicates with GitHub to receive eligible jobs.

The registration credential should be treated as sensitive infrastructure configuration.

Do not commit runner registration tokens or credentials into source control.

---

## Runner Labels During Registration

A runner can be associated with labels representing capabilities.

For example:

```text
self-hosted
linux
x64
docker
private-network
```

A workflow requiring Docker and private-network access can target:

```yaml
runs-on:
  - self-hosted
  - linux
  - docker
  - private-network
```

This avoids relying on a specific machine name.

---

## Linux vs Windows Runners

| Consideration | Linux | Windows |
|---|---|---|
| Python backend CI | Strong fit | Useful when required |
| Docker workflows | Common | Possible with different behavior |
| Shell | Bash commonly used | PowerShell commonly used |
| Production Linux parity | High | Lower |
| Windows-specific software | Limited | Strong |
| Typical backend CI cost | Often lower | Workload-dependent |

Choose the runner operating system based on application requirements rather than personal preference.

---

## Custom Software

Self-hosted runners are useful when workflows require software that is difficult to provide through standard hosted environments.

Examples:

```text
Internal CLI
Private SDK
Enterprise security scanner
Special compiler
Custom database client
Proprietary deployment tool
```

The trade-off is maintenance.

Every custom dependency creates:

```text
Installation
+
Version management
+
Security patching
+
Compatibility testing
+
Monitoring
```

Therefore, custom software should be treated as part of the runner's infrastructure lifecycle.

---

## Runner Image Management

For self-hosted infrastructure, define how runner software is provisioned.

Common approaches include:

```text
Golden VM image
Infrastructure as Code
Configuration management
Containerized runner infrastructure
Ephemeral cloud instances
Kubernetes-based runners
```

The objective is reproducibility.

Avoid manually configuring a runner and then allowing it to drift indefinitely.

---

## Runner Drift

Runner drift occurs when machines that are intended to be equivalent gradually become different.

For example:

```text
Runner A
Python 3.12
Docker 27
Tool X 4.1

Runner B
Python 3.12
Docker 26
Tool X 3.9
```

The same workflow may behave differently depending on which runner receives it.

Mitigate drift through:

- Immutable runner images
- Infrastructure as Code
- Automated provisioning
- Version pinning
- Regular replacement
- Health checks

---

## Ephemeral Runner Architecture

A scalable production design can use ephemeral runners:

```mermaid
flowchart TD
    A[Workflow Job] --> B[Runner Provisioning]
    B --> C[Ephemeral Runner]
    C --> D[Execute Job]
    D --> E[Publish Results]
    E --> F[Destroy Runner]
```

The runner is treated as disposable infrastructure.

This improves:

- Isolation
- Reproducibility
- Security
- Operational recovery

It also increases infrastructure complexity because runner provisioning must be reliable and fast.

---

## Autoscaling Runners

Large organizations may need dynamic runner capacity.

Conceptually:

```text
Jobs queued
    ↓
Runner demand detected
    ↓
Provision runners
    ↓
Jobs execute
    ↓
Demand decreases
    ↓
Runners removed
```

This avoids maintaining a large pool of idle infrastructure.

Autoscaling must account for:

- Startup time
- Maximum concurrency
- Cloud quotas
- Runner registration
- Runner cleanup
- Failed provisioning
- Cost
- Capacity spikes

---

## Runner Capacity Planning

Suppose:

```text
Average jobs per hour = 500
Average job duration = 6 minutes
```

The average concurrency requirement is approximately:

```text
500 × 6 / 60 = 50 concurrent jobs
```

Peak concurrency will generally be higher than the average.

Capacity planning should therefore consider:

```text
Average load
+
Peak load
+
Deployment bursts
+
Retry storms
+
Release events
```

Do not size runner infrastructure only against average traffic.

---

## Runner Queuing

If no eligible runner is available:

```text
Job
 ↓
Queued
 ↓
Runner becomes available
 ↓
Job starts
```

Long queue times can indicate:

- Insufficient runner capacity
- Incorrect labels
- Runner failures
- Runner group restrictions
- Excessive matrix concurrency
- Organization concurrency limits

Runner queue time should be monitored separately from job execution time.

---

## Runner Performance

CI performance is affected by:

```text
CPU
Memory
Disk I/O
Network bandwidth
Dependency download time
Docker build time
Test execution time
Runner startup time
```

For Python applications, common bottlenecks include:

- Dependency installation
- Large Docker builds
- Integration tests
- Database initialization
- Browser-based E2E tests

Use caching and parallelism where appropriate, but measure before optimizing.

---

## Cost Optimization

Runner cost should be considered across the pipeline.

Potential optimizations include:

- Cache dependencies
- Avoid unnecessary matrix combinations
- Use `max-parallel`
- Cancel obsolete PR workflows
- Separate expensive integration tests from lightweight checks
- Use appropriate runner sizes
- Autoscale self-hosted infrastructure
- Avoid permanently running oversized self-hosted machines
- Reuse artifacts instead of rebuilding unnecessarily

For pull requests, concurrency can prevent obsolete jobs from consuming resources:

```yaml
concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

For production deployments, cancellation should usually be treated much more carefully.

---

## Runner Reliability

A runner should be treated as infrastructure.

Monitor:

- Runner availability
- Job queue time
- Job startup time
- CPU
- Memory
- Disk usage
- Network errors
- Docker daemon health
- Runner service health
- Failed registrations
- Unexpected disconnections

For self-hosted runners, also monitor:

- OS health
- Security updates
- Disk cleanup
- Process leaks
- Workspace contamination
- Certificate expiration
- Cloud instance health

---

## Runner Health Checks

A production self-hosted runner should have health checks covering:

```text
Runner process
    ↓
Network connectivity
    ↓
Disk availability
    ↓
Required tools
    ↓
Docker/container runtime
    ↓
Cloud credentials mechanism
```

A runner that appears registered but cannot execute jobs reliably should be removed from the available pool until repaired.

---

## Runner Cleanup

Persistent runners require explicit cleanup.

Potential cleanup targets include:

```text
Temporary files
Docker images
Docker containers
Package caches
Build directories
Test databases
Credentials
Logs
Core dumps
```

Be particularly careful with secrets.

A job that writes:

```text
~/.aws/credentials
```

or another credential file onto a persistent runner creates a potential cross-job exposure.

Prefer temporary credentials and ensure sensitive files are not retained.

---

## Secrets and Runners

A secret passed to a job becomes available to code executed by that job.

Therefore:

```text
Secret
  ↓
Job
  ↓
All code executed by job
```

If a job runs untrusted code, giving that job secrets is dangerous.

This principle is especially important for self-hosted runners.

A secure design separates:

```text
Untrusted CI
    ↓
No privileged secrets

Trusted deployment
    ↓
Restricted secrets / OIDC
```

---

## OIDC and Runner Design

AWS OIDC removes the need for long-lived AWS credentials, but it does not eliminate runner security concerns.

The flow is:

```text
GitHub Job
    ↓
OIDC Token
    ↓
AWS IAM Trust Policy
    ↓
STS AssumeRole
    ↓
Temporary Credentials
    ↓
AWS APIs
```

The job still needs:

```yaml
permissions:
  id-token: write
```

Only the required deployment job should normally receive that permission.

On a self-hosted runner, also consider the possibility of other processes or jobs interacting with the runner environment.

Ephemeral runners reduce this risk.

---

## Runner Security Model

A production runner security model should consider:

| Layer | Question |
|---|---|
| Repository | Which repositories can use this runner? |
| Workflow | Which workflows can target it? |
| Job | What permissions does the job receive? |
| Runner | Who controls the machine? |
| Network | What can the runner reach? |
| Credentials | What credentials can code obtain? |
| Filesystem | Can previous job data persist? |
| Containers | Can jobs access the host? |
| Monitoring | Can suspicious behavior be detected? |

A runner should have the minimum network and credential access required by its workloads.

---

## Untrusted Code on Self-Hosted Runners

This is one of the most important GitHub Actions security considerations.

Avoid architectures such as:

```text
Fork PR
   ↓
Untrusted code
   ↓
Persistent self-hosted runner
   ↓
Private network
   ↓
Production systems
```

A safer architecture is:

```text
Fork PR
   ↓
GitHub-hosted runner
   ↓
Tests without privileged credentials

Trusted main branch
   ↓
Restricted workflow
   ↓
Ephemeral deployment runner
   ↓
Private infrastructure
```

The key principle is:

```text
Untrusted code should not inherit trusted infrastructure access.
```

---

## Runner Governance

At organizational scale, establish policies for:

- Allowed runner groups
- Repository access
- Runner labels
- Runner registration
- Runner lifecycle
- OS patching
- Software versions
- Network access
- Secret access
- Monitoring
- Retirement
- Incident response

A runner should have an explicit owner.

Unowned infrastructure becomes a long-term security and reliability liability.

---

## Runner Lifecycle

A controlled lifecycle is:

```mermaid
stateDiagram-v2
    [*] --> Provisioned
    Provisioned --> Registered
    Registered --> Healthy
    Healthy --> Executing
    Executing --> Healthy
    Healthy --> Draining
    Draining --> Retired
    Retired --> [*]
    Registered --> Failed
    Failed --> Draining
```

For ephemeral runners, the lifecycle is shorter:

```text
Provision
 ↓
Register
 ↓
Execute
 ↓
Deregister
 ↓
Destroy
```

Automating this lifecycle reduces operational drift.

---

## Runner Troubleshooting

Runner failures should be isolated from workflow failures.

### Job Is Queued

**Symptom**

A job remains queued and never starts.

**Possible causes**

- No eligible runner
- Incorrect labels
- Runner offline
- Runner group restrictions
- Runner capacity exhausted
- Concurrency or organization limits

**Isolation strategy**

Check:

```text
runs-on
↓
Labels
↓
Runner group
↓
Runner availability
↓
Queue status
```

For self-hosted runners, verify the runner is online and eligible.

**Prevention**

- Use meaningful labels
- Monitor runner availability
- Maintain capacity headroom
- Test runner registration automatically

---

### Self-Hosted Runner Is Offline

**Symptom**

The runner appears unavailable.

**Possible causes**

- Runner process stopped
- Host unavailable
- Network failure
- DNS failure
- Firewall restrictions
- Host maintenance
- Registration failure

**Isolation strategy**

Check:

```text
Host
→ Runner service
→ Network
→ GitHub connectivity
```

Useful host checks include:

```bash
systemctl status actions.runner.*
```

and:

```bash
journalctl -u actions.runner.* --since "30 minutes ago"
```

The exact service name depends on how the runner was installed.

---

### Job Starts on the Wrong Runner

**Possible causes**

- Incorrect labels
- Overly broad `runs-on`
- Runner group configuration
- Capability labels missing

**Isolation strategy**

Inspect:

```yaml
runs-on:
  - self-hosted
  - linux
  - production-deploy
```

and verify that only intended runners carry those labels.

---

### Docker Builds Fail Only on One Runner

**Possible causes**

- Docker version drift
- Buildx differences
- Disk exhaustion
- Corrupted Docker state
- Resource exhaustion
- Different runner image

**Checks**

```bash
docker version
docker info
df -h
free -h
```

Compare the failing runner with a healthy runner.

**Prevention**

Use reproducible runner images and replace rather than manually repairing heavily drifted infrastructure.

---

### Integration Tests Cannot Reach Services

Check:

```text
Runner network
Service container
Port mapping
DNS
Health status
Container networking
```

For a normal runner:

```text
localhost:<mapped-port>
```

may be correct.

For a containerized job:

```text
<service-name>:<port>
```

may be required.

---

### Runner Disk Is Full

**Symptom**

Builds or Docker operations fail with storage errors.

**Checks**

```bash
df -h
docker system df
```

Potential causes include:

- Docker images
- Build cache
- Large workspaces
- Test artifacts
- Persistent logs

Use cleanup policies or ephemeral runners rather than allowing persistent machines to accumulate unlimited state.

---

### Runner Has Unexpected State

**Symptom**

A workflow behaves differently on repeated executions.

**Possible causes**

- Persistent workspace
- Cached dependencies
- Docker state
- Environment variables
- Modified system packages
- Processes left running

**Corrective action**

Prefer runner replacement for heavily contaminated infrastructure.

For persistent runners, establish deterministic cleanup.

---

## Runner Monitoring Metrics

Useful operational metrics include:

| Metric | Why It Matters |
|---|---|
| Queue duration | Detects capacity shortages |
| Job duration | Detects performance regressions |
| Runner availability | Detects infrastructure failures |
| Runner utilization | Supports capacity planning |
| Failure rate | Detects unreliable infrastructure |
| Disk usage | Prevents build failures |
| Memory usage | Detects resource pressure |
| Startup latency | Important for autoscaling |
| Provisioning failure rate | Detects scaling problems |

Runner metrics should be considered alongside workflow metrics.

---

## High Availability

A production CI/CD system should avoid depending on one physical runner.

Bad architecture:

```text
All production deployments
        ↓
One VM
        ↓
One self-hosted runner
```

If that VM fails:

```text
Production deployments unavailable
```

Prefer:

```text
Deployment jobs
      ↓
Runner pool
 ┌────┼────┐
 ↓    ↓    ↓
R1   R2   R3
```

For sensitive deployment infrastructure, runners can be distributed across failure domains where the underlying infrastructure supports it.

---

## Disaster Recovery

Runner infrastructure should be replaceable.

For self-hosted runners, keep infrastructure configuration in:

- Infrastructure as Code
- Image definitions
- Configuration management
- Runner bootstrap scripts
- Documentation

Do not rely on manually configured servers as the only copy of runner configuration.

The desired recovery model is:

```text
Runner failure
    ↓
Provision replacement
    ↓
Register
    ↓
Health validation
    ↓
Resume jobs
```

This is significantly safer than repairing an unknown machine manually during an incident.

---

## Runner Architecture for AWS

A common AWS architecture is:

```mermaid
flowchart TD
    A[GitHub Actions] --> B[Runner Group]
    B --> C[Ephemeral EC2 Runners]

    C --> D[Private Subnet]
    D --> E[ECR]
    D --> F[ECS]
    D --> G[Internal Services]

    C --> H[AWS STS]
    H --> I[IAM Role]
```

The runner can access private AWS infrastructure while GitHub remains the workflow control plane.

Security controls should include:

- IAM least privilege
- Security groups
- Private subnet design
- Restricted outbound access where appropriate
- Ephemeral runner lifecycle
- Short-lived credentials
- Runner group restrictions
- Centralized logging

---

## Runner Architecture for Kubernetes

Organizations may also run ephemeral CI infrastructure on Kubernetes.

Conceptually:

```text
GitHub Actions
      ↓
Runner Controller / Provisioner
      ↓
Kubernetes
      ↓
Ephemeral Runner Pod
      ↓
Job
      ↓
Pod Removed
```

This can provide:

- Elastic capacity
- Ephemeral execution
- Infrastructure standardization
- Integration with existing Kubernetes operations

However, it adds another control plane and should be justified by scale or infrastructure requirements.

---

## Runner Strategy by Workload

| Workload | Typical Runner Strategy |
|---|---|
| Python linting | GitHub-hosted Linux |
| Python unit tests | GitHub-hosted Linux |
| PostgreSQL integration tests | GitHub-hosted Linux + services |
| Docker build | GitHub-hosted Linux |
| Public repository CI | GitHub-hosted runner |
| Private network deployment | Restricted self-hosted runner |
| Specialized hardware | Self-hosted |
| Sensitive production deployment | Restricted ephemeral self-hosted |
| Windows-specific build | Windows runner |
| Large-scale CI | Hosted + autoscaled self-hosted mix |

The correct architecture depends on security, network, performance, and operational requirements.

---

## Common Runner Mistakes

### Treating a Runner as Permanent Infrastructure

A runner is execution infrastructure, not necessarily an application server.

For ephemeral workloads, replace runners instead of allowing long-term drift.

### Giving Runners Excessive Network Access

If a runner only needs:

```text
ECR
ECS
```

it should not automatically have access to:

```text
Production database
Internal admin systems
Unrelated VPCs
```

Network reachability should follow least privilege.

### Running Untrusted PRs on Privileged Runners

This can expose:

- Internal networks
- Credentials
- Docker
- Filesystem state
- Deployment infrastructure

Use isolated hosted runners for untrusted workloads.

### Using Persistent Runners Without Cleanup

Persistent state creates:

```text
Security risk
+
Reproducibility problems
+
Disk growth
+
Dependency drift
```

### Installing Tools Manually

Manual installation causes configuration drift.

Prefer reproducible runner provisioning.

### Using One Runner for Everything

A single runner may combine:

```text
PR CI
Production deployment
Private network access
Long-lived credentials
```

This creates a large blast radius.

Separate workloads using runner groups and labels.

---

## Production Runner Checklist

### Runner Selection

- Is a GitHub-hosted runner sufficient?
- Does the job require private network access?
- Does it require specialized hardware?
- Does it require a specific operating system?

### Security

- Can untrusted code execute?
- Does the runner have access to private infrastructure?
- Are credentials short-lived?
- Is the runner ephemeral where appropriate?
- Are runner groups restricted?
- Are network permissions minimal?

### Reliability

- Is there runner redundancy?
- Can the runner be recreated automatically?
- Is queue time monitored?
- Are health checks implemented?

### Reproducibility

- Is the runner image versioned?
- Are important tools pinned?
- Is configuration automated?
- Is runner drift detected?

### Cost

- Is runner capacity proportional to demand?
- Can obsolete PR jobs be cancelled?
- Are expensive matrix combinations necessary?
- Can autoscaling reduce idle capacity?

### Operations

- Are logs available?
- Is disk usage monitored?
- Is Docker state controlled?
- Is the runner lifecycle automated?
- Is there a documented replacement procedure?

---

## Interview-Level Runner Scenarios

### Why Would You Choose a Self-Hosted Runner?

A strong answer should start with a concrete requirement:

```text
Private network access
Specialized hardware
Custom infrastructure
Specific compliance requirement
```

rather than simply saying:

```text
Self-hosted runners are faster.
```

The answer should also discuss the additional maintenance and security responsibilities.

---

### How Would You Secure a Production Deployment Runner?

Consider:

```text
Restricted runner group
+
Dedicated labels
+
Ephemeral lifecycle
+
Least-privilege IAM
+
OIDC
+
Private networking
+
No untrusted PR execution
+
Monitoring
```

---

### How Would You Handle Runner Scaling?

For predictable low-volume workloads:

```text
Small static pool
```

For variable workloads:

```text
Autoscaled ephemeral runners
```

For large organizations:

```text
Runner pools
+
Runner groups
+
Autoscaling
+
Capacity monitoring
```

---

### Why Are Ephemeral Runners Safer?

Because they reduce:

```text
Cross-job state
Credential remnants
Dependency drift
Workspace contamination
Long-lived compromise
```

They are not a complete security solution, but they reduce the persistence of compromised state.

---

### How Would You Give a Runner Private VPC Access Without Exposing Production?

Use:

```text
Dedicated runner
      ↓
Restricted subnet
      ↓
Security groups
      ↓
Only required internal endpoints
```

Combine network controls with:

```text
OIDC
IAM least privilege
Runner groups
Ephemeral lifecycle
```

Network access and credential access should be independently restricted.

---

## Key Takeaways

- A GitHub Actions runner is the execution environment for a job; runner selection directly affects reproducibility, performance, security, networking, and cost.
- GitHub-hosted runners are a strong default for standard CI, while self-hosted runners should be introduced for concrete requirements such as private networking, specialized hardware, or controlled infrastructure.
- Privileged self-hosted runners should be isolated from untrusted pull-request workloads, with restricted runner groups, minimal network access, least-privilege credentials, and preferably ephemeral execution.
- Production runner infrastructure should be reproducible, observable, replaceable, and scalable rather than dependent on manually maintained machines.
- Senior-level runner design balances execution speed and capacity against security boundaries, failure isolation, infrastructure cost, operational complexity, and disaster recovery.