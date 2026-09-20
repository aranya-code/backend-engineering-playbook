# 11- Production Best Practices

## Overview

Production EC2 environments should be designed around **replaceability, least privilege, observability, controlled change, predictable recovery, and failure isolation**.

An EC2 instance should generally be treated as a replaceable compute unit rather than a permanent server that engineers manually maintain for years.

A production architecture should look approximately like:

```text
                         Internet
                            |
                            v
                     Route 53 / DNS
                            |
                            v
                    Application Load Balancer
                            |
                +-----------+-----------+
                |                       |
                v                       v
             AZ-a                     AZ-b
          +---------+               +---------+
          |   EC2   |               |   EC2   |
          |  App    |               |  App    |
          +----+----+               +----+----+
               |                         |
               +------------+------------+
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
        PostgreSQL        Redis          Kafka
```

For production workloads, EC2 operations should be standardized around:

- Infrastructure as Code
- Launch Templates
- Auto Scaling Groups
- Multi-AZ deployment
- Load balancing
- IAM roles
- Systems Manager
- Automated patching
- Centralized monitoring
- Structured logging
- Backup and recovery
- Controlled deployments
- Resource tagging
- Cost management
- Quota management
- Incident response

The goal is not to eliminate failures. The goal is to ensure that failures are **detected quickly, contained, recoverable, and operationally predictable**.

## Production EC2 Principles

A useful production mindset is:

| Principle | Production Approach |
|---|---|
| Compute | Treat instances as replaceable |
| Availability | Use multiple AZs |
| Scaling | Use Auto Scaling |
| Traffic | Use load balancing |
| Access | Prefer IAM roles and Systems Manager |
| Configuration | Use IaC and immutable artifacts |
| Patching | Automate and standardize |
| Monitoring | Metrics, logs, alarms, traces |
| Storage | Separate ephemeral compute from persistent data |
| Recovery | Automate replacement and restoration |
| Security | Least privilege and private networking |
| Deployment | Controlled, reversible releases |
| Cost | Right-size and remove unused resources |

## Treat EC2 Instances as Replaceable

The most important operational principle is to avoid making individual instances special.

Bad architecture:

```text
Production Server
     |
     +-- Manual configuration
     +-- Manual package installation
     +-- Local application changes
     +-- Important files on root disk
     +-- Manually configured cron jobs
     +-- Engineers depend on its IP
```

Better architecture:

```text
Launch Template
      |
      v
Golden AMI / Bootstrap
      |
      v
Auto Scaling Group
      |
      +-- EC2
      +-- EC2
      +-- EC2
```

If an instance fails:

```text
Unhealthy Instance
       |
       v
ASG detects failure
       |
       v
Terminate / replace
       |
       v
New instance
       |
       v
Application becomes healthy
```

This reduces operational dependency on individual machines.

## Immutable Infrastructure

Immutable infrastructure means that production instances are replaced rather than extensively modified in place.

A typical deployment flow is:

```text
Code
 |
 v
CI/CD
 |
 v
Build AMI / Container Artifact
 |
 v
Launch Template
 |
 v
Instance Refresh
 |
 v
New EC2 Fleet
 |
 v
Health Validation
 |
 v
Old Fleet Removed
```

This provides:

- Reproducibility
- Consistent configuration
- Easier rollback
- Reduced configuration drift
- Predictable deployments

Manual SSH-based changes should be treated as exceptions, not the standard deployment mechanism.

## Infrastructure as Code

Production EC2 infrastructure should be managed through tools such as:

- Terraform
- AWS CloudFormation
- AWS CDK

The infrastructure definition should cover resources such as:

- VPC
- Subnets
- Security Groups
- IAM roles
- Launch Templates
- Auto Scaling Groups
- Load balancers
- Target groups
- EBS configuration
- CloudWatch alarms

Example Terraform structure:

```text
infrastructure/
├── modules/
│   ├── network/
│   ├── security/
│   ├── ec2/
│   └── load-balancer/
├── environments/
│   ├── production/
│   └── staging/
└── README.md
```

IaC provides a controlled source of truth for infrastructure.

It does not eliminate operational responsibility. Changes still require review, testing, rollout planning, and rollback procedures.

## Multi-AZ Deployment

Production applications should avoid depending on a single Availability Zone when availability requirements justify redundancy.

Example:

```text
                    ALB
                     |
          +----------+----------+
          |                     |
         AZ-a                  AZ-b
          |                     |
      +---+---+             +---+---+
      | EC2   |             | EC2   |
      | EC2   |             | EC2   |
      +-------+             +-------+
```

Benefits include:

- AZ failure isolation
- Better availability
- Safer maintenance
- More flexible scaling
- Reduced dependence on a single failure domain

A single-AZ deployment may still be appropriate for some development or low-criticality workloads, but production high-availability requirements should explicitly justify the chosen topology.

## Auto Scaling Groups

Use Auto Scaling Groups for workloads where instances can be replaced safely.

A production ASG should define:

- Minimum capacity
- Desired capacity
- Maximum capacity
- Launch Template
- Subnets/AZs
- Health checks
- Scaling policies
- Instance warmup
- Replacement behavior
- Instance refresh strategy

Example:

```text
Min:     2
Desired: 4
Max:    12
```

The values should be based on:

- Traffic
- CPU/memory requirements
- Application concurrency
- Downstream dependency capacity
- Failure scenarios
- Cost constraints

Do not choose `MaxSize` arbitrarily. It should be compatible with service quotas, subnet capacity, database capacity, and other dependencies.

## Load Balancing

Production EC2 application servers should generally not be directly exposed to the public internet when an application load balancer can provide the required entry point.

Recommended flow:

```text
Client
  |
  v
Route 53
  |
  v
ALB
  |
  +--> EC2
  +--> EC2
  +--> EC2
```

Benefits include:

- Health-based routing
- TLS termination
- Traffic distribution
- Connection draining
- Integration with Auto Scaling
- Reduced direct exposure of instances

The backend Security Group should normally allow application traffic from the load balancer Security Group rather than from arbitrary internet addresses.

## Security Group Design

Use layered Security Groups.

Example:

```text
Internet
   |
   v
ALB Security Group
   |
   v
Application Security Group
   |
   v
Database Security Group
```

Example policy:

| Component | Inbound Source | Port |
|---|---|---:|
| ALB | Internet or controlled clients | 443 |
| Application EC2 | ALB Security Group | 8000 |
| PostgreSQL | Application Security Group | 5432 |
| Redis | Application Security Group | 6379 |

This is preferable to exposing every service to the VPC CIDR or internet.

Security Groups are stateful and allow-only. Use them as resource-level access controls, not as a replacement for complete network architecture.

## Private Subnets

Application EC2 instances do not normally need public IPv4 addresses when traffic enters through a load balancer.

A common architecture is:

```text
Public Subnets
    |
    +-- ALB
    |
    v
Private Subnets
    |
    +-- EC2
    +-- EC2
    |
    v
Private Services
    |
    +-- PostgreSQL
    +-- Redis
```

Benefits include:

- Reduced direct internet exposure
- More controlled ingress
- Better network segmentation
- Easier enforcement of security policies

Private instances may still require outbound internet access for tasks such as package installation or external APIs. This can be provided through NAT or appropriate VPC endpoints depending on the workload.

## IAM Roles Instead of Static Credentials

EC2 applications should use IAM roles through instance profiles rather than storing long-lived AWS access keys on disk.

Bad:

```python
import boto3

client = boto3.client(
    "s3",
    aws_access_key_id="...",
    aws_secret_access_key="...",
)
```

Better:

```python
import boto3

s3 = boto3.client("s3")
```

The application can obtain credentials through the EC2 instance role.

For example:

```text
EC2
 |
 v
Instance Profile
 |
 v
IAM Role
 |
 v
AWS API
```

Grant only the permissions required by the application.

For example, an application that uploads objects to one S3 bucket should not receive broad administrative permissions.

## Instance Metadata Service

Use IMDSv2 where supported and configure the instance metadata service appropriately.

The goal is to reduce exposure to credential theft through unintended metadata access paths.

Operational controls should include:

- IMDSv2
- Least-privilege IAM roles
- Restricted application permissions
- Secure SSRF defenses
- No hard-coded credentials

Application security should still address SSRF independently. IMDS configuration is a defense layer, not a complete SSRF mitigation.

## Systems Manager

AWS Systems Manager Session Manager can reduce the need for direct SSH access.

Instead of:

```text
Internet
   |
   v
Port 22
   |
   v
EC2
```

prefer where practical:

```text
Engineer
   |
   v
AWS IAM
   |
   v
Systems Manager
   |
   v
EC2
```

Benefits include:

- Centralized IAM authorization
- Reduced SSH exposure
- Auditable sessions
- No need for inbound port 22 in many architectures
- Better operational control

Use SSH only when it is justified by the operational requirements.

## SSH Security

If SSH is required:

- Restrict source addresses.
- Avoid `0.0.0.0/0`.
- Use strong key management.
- Prefer bastion or controlled access paths where appropriate.
- Monitor access.
- Remove unused access paths.
- Avoid shared private keys.
- Rotate credentials according to organizational requirements.

Do not treat opening port 22 to the internet as a normal production default.

## Patch Management

Production EC2 instances need an explicit patching strategy.

Patching can cover:

- Operating system packages
- Kernel
- OpenSSL
- Python runtime
- Nginx
- Application dependencies
- Security agents
- Monitoring agents

A common approach is:

```text
Patch Baseline
      |
      v
Staging
      |
      v
Automated Validation
      |
      v
Production Instance Refresh
      |
      v
Health Checks
      |
      v
Complete Rollout
```

For immutable environments, patching the base AMI and replacing instances is often easier to reason about than manually patching every production host.

## Application Dependency Management

Python applications should use reproducible dependency management.

For example:

```text
requirements.txt
pyproject.toml
lock file where applicable
```

Build artifacts should be generated through CI/CD rather than manually installing packages on production instances.

For Django or FastAPI:

```text
Git Commit
    |
    v
CI
    |
    +-- Tests
    +-- Security checks
    +-- Build
    |
    v
Artifact
    |
    v
Deployment
```

This reduces configuration drift between environments.

## Application Process Management

Do not run production Django or FastAPI applications using development servers.

For Django:

```text
ALB
 |
 v
Nginx
 |
 v
Gunicorn
 |
 v
Django
```

For FastAPI:

```text
ALB
 |
 v
Nginx
 |
 v
Uvicorn / Gunicorn-managed workers
 |
 v
FastAPI
```

The exact process architecture depends on the deployment model, but production systems should provide:

- Process supervision
- Graceful shutdown
- Worker management
- Health checks
- Structured logs
- Timeouts

## Graceful Shutdown

Applications must handle instance termination safely.

This is particularly important for:

- Celery workers
- Long-running HTTP requests
- gRPC connections
- Kafka consumers
- Background jobs

Example:

```text
ASG Termination
      |
      v
Lifecycle Hook
      |
      v
Stop New Work
      |
      v
Drain Existing Work
      |
      v
Close Connections
      |
      v
Terminate Instance
```

Without graceful shutdown, deployments and scaling events can cause:

- Dropped requests
- Duplicate jobs
- Interrupted consumers
- Partial processing

## Celery on EC2

Celery workers should be designed for replacement.

```text
Django / FastAPI
      |
      v
Redis / RabbitMQ
      |
      v
Celery Workers
      |
      v
Database / External APIs
```

When an EC2 worker is terminated:

- Stop accepting new work where possible.
- Allow active tasks to complete.
- Configure appropriate visibility/acknowledgement semantics.
- Make tasks idempotent.
- Avoid relying on local instance state.

The queue should be the durable boundary, not the EC2 filesystem.

## Kafka Consumers on EC2

Kafka consumers should also tolerate instance replacement.

A robust design should consider:

- Consumer groups
- Partition assignment
- Rebalancing
- Graceful shutdown
- Offset management
- Idempotent processing
- Downstream transaction boundaries

A terminating EC2 instance should not cause permanent loss of work merely because the process exits.

## Persistent Data

Avoid storing critical application state only on an EC2 root volume.

Prefer managed or durable services where appropriate:

```text
EC2
 |
 +-- Stateless application
 |
 +-- Temporary files
 |
 v
Managed / Durable Storage
 |
 +-- PostgreSQL
 +-- S3
 +-- Redis
 +-- EBS where required
```

If EBS contains important state, define:

- Backup policy
- Snapshot policy
- Restore procedure
- Encryption
- Retention
- Monitoring
- Recovery testing

## EBS Best Practices

Production EBS usage should include:

- Encryption
- Appropriate volume type
- Capacity monitoring
- IOPS/throughput monitoring
- Snapshot strategy
- Correct `DeleteOnTermination` configuration
- Backup validation
- Filesystem monitoring

Do not assume that increasing EBS volume size automatically expands the filesystem.

The operational sequence is generally:

```text
Increase EBS Volume
       |
       v
Verify Block Device
       |
       v
Expand Partition if required
       |
       v
Expand Filesystem
       |
       v
Verify Capacity
```

## Storage Separation

Separate workloads according to their durability requirements.

Example:

```text
Root EBS
  |
  +-- OS
  +-- Application
  +-- Logs requiring local buffering

Data EBS
  |
  +-- Persistent workload data

S3
  |
  +-- Objects
  +-- Backups
  +-- Artifacts
```

Do not automatically place every file on a single root volume.

## Logging

Production applications should produce structured logs.

Example:

```json
{
  "timestamp": "2026-09-20T14:30:00Z",
  "level": "INFO",
  "service": "orders-api",
  "request_id": "req-123",
  "message": "Order created",
  "order_id": "ord-456"
}
```

Useful fields include:

- Timestamp
- Log level
- Service
- Environment
- Request ID
- Trace ID
- User or tenant identifier where appropriate
- Event name
- Error type

Avoid logging secrets, access tokens, passwords, or sensitive payloads.

## Centralized Logging

Do not rely exclusively on local EC2 log files.

A production architecture should forward logs to centralized storage or observability systems.

Example:

```text
EC2
 |
 +-- Django
 +-- Nginx
 +-- Celery
 |
 v
CloudWatch Agent / Logging Pipeline
 |
 v
CloudWatch Logs
 |
 v
Logs Insights / Alerting
```

Centralization makes logs available even after an instance is replaced.

## Monitoring

Monitor both infrastructure and application behavior.

### Infrastructure Metrics

Typical metrics include:

- CPU utilization
- CPU credit metrics where applicable
- Network traffic
- EBS performance
- EBS volume usage
- Status checks
- Instance count
- ASG desired vs healthy capacity

### Application Metrics

Monitor:

- Request rate
- Error rate
- Latency
- Throughput
- Queue depth
- Worker utilization
- Database connection usage
- Cache hit ratio
- Kafka consumer lag

The important distinction is:

```text
EC2 Healthy
    !=
Application Healthy
```

## Health Checks

Use multiple health layers.

```text
EC2
 |
 +-- System Status
 |
 +-- Instance Status
 |
 +-- Application Health
 |
 +-- ALB Target Health
 |
 +-- Dependency Health
```

A good application health endpoint should be lightweight.

Example:

```http
GET /health/live
```

For deeper checks:

```http
GET /health/ready
```

Readiness can validate required dependencies when appropriate.

Do not make liveness checks depend on every downstream system. A temporary database failure should not necessarily cause every application process to be restarted.

## Observability

Production observability should correlate:

```text
Metrics
  +
Logs
  +
Traces
  +
Events
```

For a request:

```text
Client
  |
  v
ALB
  |
  v
Django / FastAPI
  |
  +--> Redis
  |
  +--> PostgreSQL
  |
  +--> Kafka
```

Use correlation IDs or distributed trace IDs to connect activity across services.

This is especially important in microservice architectures.

## CloudWatch Alarms

Create alarms around conditions that require action.

Examples:

- High CPU
- High memory where agent metrics are available
- Status check failures
- Low healthy target count
- ASG capacity mismatch
- EBS burst/throughput pressure
- Application error rate
- Queue depth
- Disk utilization

An alarm should have an operational owner and an associated response.

Avoid creating alarms that nobody acts on.

## Alert Quality

Good alerts are:

- Actionable
- Specific
- Stable
- Contextual
- Routed to the correct team

Bad alert:

```text
CPU > 70%
```

without workload context.

Better:

```text
Production API fleet CPU > 85%
for 10 minutes
AND request latency is elevated
```

The exact thresholds should be derived from workload behavior rather than generic numbers.

## Backups

Production workloads should have defined recovery objectives.

Document:

- RPO
- RTO
- Backup frequency
- Retention
- Backup location
- Encryption
- Restore process
- Recovery ownership

EC2 backups may involve:

- EBS snapshots
- AMIs
- AWS Backup
- Application-level database backups
- S3 backups
- Cross-Region copies

A snapshot existing in AWS does not prove that recovery works.

## Test Recovery

Recovery procedures should be tested.

Example:

```text
Backup
  |
  v
Restore
  |
  v
Boot
  |
  v
Application Validation
  |
  v
Database Validation
  |
  v
Traffic Validation
```

Test:

- Snapshot restoration
- AMI launch
- Database recovery
- Application startup
- Network configuration
- IAM permissions
- DNS
- Load balancer registration

A backup strategy without restore testing is incomplete.

## Disaster Recovery

Select a DR strategy based on RTO and RPO.

| Strategy | Typical Complexity | Recovery Characteristics |
|---|---|---|
| Backup and restore | Lower | Slower recovery |
| Pilot light | Medium | Faster than backup-only |
| Warm standby | Higher | Faster recovery |
| Multi-Region active/active | Highest | Designed for very low recovery interruption |

DR capacity must include:

- EC2 quotas
- Subnet IP capacity
- EBS capacity
- IAM
- Networking
- DNS
- Load balancing
- Database recovery
- Secrets
- Application artifacts

## Configuration Management

Avoid configuration drift.

Production configuration should come from controlled sources such as:

- IaC
- Parameter Store
- Secrets Manager
- Environment variables
- Configuration management systems

Do not maintain undocumented values in:

```text
/etc/
~/.bashrc
local shell history
manual application edits
```

unless those changes are part of an explicitly managed configuration process.

## Secrets Management

Never store production secrets directly in:

- Git repositories
- AMIs
- User Data
- Docker images
- Shell scripts
- Source code
- Unencrypted local configuration

Prefer:

```text
Application
    |
    v
IAM Role
    |
    v
Secrets Manager / Parameter Store
```

Applications should retrieve only the secrets they require.

## User Data

User Data is useful for instance initialization but should not become a giant configuration management system.

Good uses:

- Bootstrap agents
- Register configuration
- Fetch deployment artifacts
- Perform initialization
- Configure basic runtime dependencies

Avoid putting sensitive secrets directly into User Data.

For complex provisioning, use:

- Golden AMIs
- Configuration management
- Systems Manager
- CI/CD
- IaC

## AMI Strategy

Production environments should use controlled AMI versions.

A typical pipeline:

```text
Base AMI
   |
   v
Security Updates
   |
   v
Runtime Installation
   |
   v
Application Dependencies
   |
   v
Validation
   |
   v
Golden AMI
   |
   v
Launch Template
```

Track:

- AMI ID
- Build date
- OS version
- Application version
- Security patch level
- Architecture
- Owner

Do not keep obsolete AMIs indefinitely. Retention should balance rollback capability against storage cost and security risk.

## Launch Templates

Use Launch Templates rather than embedding instance configuration in ad-hoc launch commands.

A Launch Template can define:

- AMI
- Instance type
- IAM instance profile
- Security Groups
- EBS mappings
- User Data
- Metadata options
- Network configuration

Version Launch Templates deliberately.

Example:

```text
Launch Template
      |
      +-- v1
      +-- v2
      +-- v3
              |
              v
          Production ASG
```

Do not change production configuration without knowing which version is currently deployed.

## Deployment Strategy

Production deployments should be controlled and observable.

Common approaches include:

- Rolling deployment
- Instance refresh
- Blue/green deployment
- Canary deployment

A basic rolling deployment:

```text
Old Fleet
   |
   v
Launch New Instance
   |
   v
Health Check
   |
   v
Register Target
   |
   v
Drain Old Instance
   |
   v
Terminate Old Instance
```

Never treat "instance started" as equivalent to "deployment succeeded."

The application must become healthy and serve real traffic successfully.

## Rollback

Every production deployment should have a rollback strategy.

A rollback can involve:

- Previous AMI
- Previous Launch Template version
- Previous application artifact
- Previous configuration
- Previous database-compatible application version

Rollback planning must consider database schema compatibility.

A deployment rollback is not always safe if the new version has already performed irreversible database migrations.

## Database Compatibility

EC2 application deployments frequently depend on PostgreSQL or another database.

Use an expand-and-contract migration strategy when schema changes must coexist across application versions.

Example:

```text
Version A
   |
   v
Add compatible column
   |
   v
Deploy Version B
   |
   v
Backfill / migrate
   |
   v
Remove old field later
```

Avoid deployments where the new application requires a schema that the old fleet cannot understand while both versions are running.

## Resource Tagging

Production resources should have consistent tags.

Example:

```text
Environment = production
Application  = orders-api
Team         = payments
Owner        = backend-platform
ManagedBy    = terraform
CostCenter   = engineering
```

Tags support:

- Cost allocation
- Resource discovery
- Automation
- Ownership
- Incident response
- Compliance
- Cleanup

Tagging standards should be enforced through IaC and organizational controls where possible.

## Resource Ownership

Every production resource should have a clear owner.

Useful ownership metadata includes:

- Team
- Application
- Environment
- Service
- Cost center
- Repository
- On-call team

An instance without ownership is difficult to operate safely during an incident.

## Cost Management

Production optimization should consider total workload cost.

Review:

- Instance utilization
- Instance family
- EBS capacity
- EBS performance
- Public IPv4 usage
- Load balancers
- NAT Gateway
- Data transfer
- CloudWatch usage
- Snapshots
- Unused resources

Do not optimize cost by simply reducing instance size until the application becomes unreliable.

A better model is:

```text
Cost per useful unit of work
```

For example:

```text
Cost per:
- API request
- Background job
- Processed event
- Transaction
```

## Capacity Planning

Plan capacity using more than CPU.

Consider:

- CPU
- Memory
- Network
- EBS
- Connection limits
- Application concurrency
- Database capacity
- Redis capacity
- Kafka throughput
- Service quotas
- Subnet IP capacity

Example:

```text
Traffic
  |
  v
EC2 Scaling
  |
  +--> CPU
  +--> Memory
  +--> Network
  +--> Connections
        |
        v
     PostgreSQL
```

Adding more EC2 instances can increase database connections and overload PostgreSQL even when EC2 itself has plenty of capacity.

## Database Connection Management

For Django/FastAPI applications, uncontrolled database connection growth can become a production failure.

Example:

```text
20 EC2
   |
   +-- 4 workers each
   |
   = potentially many DB connections
            |
            v
       PostgreSQL
```

Connection pooling and appropriate worker sizing should be considered.

Scaling compute without considering database connection capacity can turn successful EC2 scaling into a database outage.

## Redis Capacity

Redis can similarly become the bottleneck.

Consider:

- Connection count
- Memory
- Network throughput
- Command latency
- Eviction behavior
- Key cardinality

A larger EC2 fleet may generate substantially more Redis traffic.

## Kafka Capacity

Kafka consumers and producers should be monitored independently of EC2 health.

Track:

- Consumer lag
- Producer throughput
- Error rate
- Partition distribution
- Network throughput
- Rebalancing

An EC2 instance can be healthy while the Kafka consumer is effectively failing.

## Nginx Best Practices

When Nginx runs on EC2:

- Configure sensible timeouts.
- Restrict exposed ports.
- Forward appropriate headers.
- Use TLS appropriately.
- Configure connection limits where necessary.
- Monitor access and error logs.
- Avoid unlimited buffering or request sizes without reason.

Example flow:

```text
ALB
 |
 v
Nginx
 |
 v
Gunicorn / Uvicorn
 |
 v
Application
```

Keep infrastructure and application responsibilities clearly separated.

## Timeouts

Every network boundary should have deliberate timeout values.

Examples:

```text
ALB
 |
 v
Nginx
 |
 v
Application
 |
 v
PostgreSQL / Redis / External API
```

A missing timeout can create stuck connections and resource exhaustion.

Set and review:

- ALB timeout
- Nginx timeout
- Gunicorn/Uvicorn timeout
- HTTP client timeout
- Database timeout
- Redis timeout
- gRPC deadline

Timeouts should reflect actual workload behavior rather than arbitrary defaults.

## Security Hardening

Production EC2 security should include:

- Least-privilege IAM
- IMDSv2
- Encrypted EBS
- Restricted Security Groups
- Private subnets where appropriate
- Automated patching
- Centralized logging
- CloudTrail
- Systems Manager
- Vulnerability management
- Controlled AMIs
- Secret management

Security should be layered:

```text
Identity
  +
Network
  +
Host
  +
Application
  +
Data
  +
Monitoring
```

No single control should be expected to provide complete protection.

## Host Hardening

Depending on organizational requirements:

- Remove unnecessary packages.
- Disable unnecessary services.
- Restrict listening ports.
- Apply security patches.
- Use host-based monitoring where required.
- Configure filesystem permissions.
- Enforce secure SSH settings if SSH exists.
- Monitor privileged operations.

Avoid modifying hardened images manually without recording the changes.

## Network Security

Use network segmentation deliberately.

Example:

```text
Internet
   |
   v
Public ALB
   |
   v
Private App Subnets
   |
   +--> Private Database
   |
   +--> Private Cache
```

Use:

- Security Groups
- Network ACLs where appropriate
- Route tables
- VPC endpoints
- NAT where required
- Private DNS

Do not expose internal databases or caches directly to the internet.

## High Availability

High availability should exist at multiple layers.

```text
              ALB
               |
        +------+------+
        |             |
       AZ-a          AZ-b
        |             |
      EC2 EC2       EC2 EC2
        |             |
        +------+------+
               |
          Data Layer
```

Also consider:

- Database availability
- Cache failure
- Queue failure
- External dependency failure
- DNS failure
- AWS service failure

EC2 multi-AZ alone does not make the entire application highly available.

## Failure Isolation

Avoid large blast radius.

Examples:

- Separate production and staging accounts.
- Use multiple AZs.
- Separate critical workloads.
- Use independent deployment boundaries.
- Apply least-privilege IAM.
- Isolate network tiers.
- Use workload-specific scaling.

A single faulty automation script should not be able to terminate every production instance.

## Safe Change Management

Production changes should have:

- Change scope
- Owner
- Expected impact
- Validation method
- Rollback plan
- Monitoring plan

For infrastructure changes:

```text
Change
  |
  v
Review
  |
  v
Test
  |
  v
Deploy
  |
  v
Observe
  |
  +--> Healthy --> Complete
  |
  +--> Unhealthy --> Rollback
```

Avoid making emergency changes without recording them.

## Operational CLI Safety

When using AWS CLI against production:

Always verify:

```bash
aws sts get-caller-identity
aws configure get region
```

Then inspect resources before destructive operations.

For example:

```bash
aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[].Instances[].{
        InstanceId:InstanceId,
        State:State.Name,
        Name:Tags[?Key==`Name`].Value|[0],
        Environment:Tags[?Key==`Environment`].Value|[0]
    }' \
    --output table
```

Only then perform operations such as stop or terminate.

Production CLI workflows should use:

- Explicit profiles
- Explicit Regions
- Tags
- Resource IDs
- `--dry-run` where supported
- Confirmation for destructive actions

## Prevent Accidental Termination

Use safeguards where appropriate:

- EC2 termination protection
- ASG scale-in protection
- IAM restrictions
- Tag-based policies
- Change approval
- Separate production accounts
- Strong CLI profile discipline

Termination protection should not be treated as a substitute for backups or redundancy.

## Production Incident Response

A production EC2 incident should follow a structured workflow.

```text
Alert
  |
  v
Confirm Impact
  |
  v
Identify Scope
  |
  v
Check Recent Changes
  |
  v
Check Application
  |
  v
Check EC2 Health
  |
  v
Check Dependencies
  |
  v
Mitigate
  |
  v
Recover
  |
  v
Validate
  |
  v
Document
```

During an incident, prioritize restoring service over making broad architectural changes.

## Recent Change Analysis

Many incidents correlate with a recent deployment or configuration change.

Check:

- Application deployment
- AMI version
- Launch Template version
- Security Group changes
- IAM changes
- DNS changes
- Database migrations
- Auto Scaling configuration
- Load balancer configuration

Do not assume infrastructure failure simply because EC2 metrics look abnormal.

## Operational Runbooks

Critical operations should have documented runbooks.

Examples:

- EC2 instance replacement
- ASG replacement loop
- High CPU
- Disk full
- EBS failure
- ALB target unhealthy
- Deployment rollback
- Database connection exhaustion
- DR recovery
- Quota exhaustion

A runbook should contain:

```text
Detection
   |
Diagnosis
   |
Mitigation
   |
Recovery
   |
Validation
   |
Escalation
```

## Production Readiness Checklist

### Architecture

- [ ] Multi-AZ strategy defined
- [ ] ALB/NLB architecture defined
- [ ] ASG configured where appropriate
- [ ] Private subnets used where appropriate
- [ ] Failure domains identified
- [ ] Downstream dependencies reviewed

### Security

- [ ] IAM roles used instead of static credentials
- [ ] Least privilege implemented
- [ ] IMDSv2 configured
- [ ] Security Groups restricted
- [ ] EBS encryption enabled
- [ ] SSH restricted or replaced with Session Manager
- [ ] Secrets stored outside source code and AMIs
- [ ] CloudTrail enabled

### Compute

- [ ] Launch Templates managed
- [ ] AMIs versioned
- [ ] Instances treated as replaceable
- [ ] ASG health checks configured
- [ ] Instance refresh strategy defined
- [ ] Graceful shutdown implemented

### Application

- [ ] Production application server configured
- [ ] Timeouts configured
- [ ] Health endpoints implemented
- [ ] Structured logging enabled
- [ ] Correlation IDs available
- [ ] Database connections controlled
- [ ] Background workers gracefully terminate
- [ ] External API calls have timeouts

### Monitoring

- [ ] EC2 metrics monitored
- [ ] Application metrics monitored
- [ ] Logs centralized
- [ ] Status checks monitored
- [ ] ALB target health monitored
- [ ] ASG capacity monitored
- [ ] Database health monitored
- [ ] Alerts have operational owners

### Storage and Backup

- [ ] EBS encrypted
- [ ] Disk utilization monitored
- [ ] Snapshot strategy defined
- [ ] Database backup strategy defined
- [ ] Restore procedure documented
- [ ] Recovery testing performed
- [ ] Backup retention defined

### Operations

- [ ] AWS CLI production workflow documented
- [ ] IaC is source of truth
- [ ] Change management defined
- [ ] Runbooks available
- [ ] Incident response process defined
- [ ] Quotas monitored
- [ ] Resource ownership documented
- [ ] Tagging standards enforced

### Cost

- [ ] Instances right-sized
- [ ] Idle resources reviewed
- [ ] EBS usage reviewed
- [ ] Public IPv4 usage reviewed
- [ ] Data transfer reviewed
- [ ] NAT costs reviewed
- [ ] Snapshot retention reviewed
- [ ] Cost allocation tags configured

## Common Production Mistakes

### Treating EC2 as a Permanent Server

Manual configuration creates drift and makes recovery difficult.

**Better:** build reproducible instances and replace them through ASG or controlled automation.

### Using Public IPs as Application Dependencies

Public IPs can change after instance lifecycle events.

**Better:** use ALB, DNS, private discovery, or stable network abstractions.

### Scaling EC2 Without Scaling Dependencies

Adding instances can overload:

- PostgreSQL
- Redis
- Kafka
- External APIs

**Better:** model the entire dependency chain.

### Monitoring Only CPU

CPU can be normal while the application is failing.

**Better:** monitor latency, errors, queue depth, database connections, target health, and business-critical signals.

### Allowing SSH From Anywhere

This unnecessarily expands the attack surface.

**Better:** use Systems Manager or tightly restrict SSH access.

### Storing Secrets in User Data

User Data can expose sensitive information through infrastructure tooling and operational interfaces.

**Better:** use Secrets Manager or Parameter Store with IAM authorization.

### Ignoring Graceful Shutdown

Immediate termination can interrupt requests and background jobs.

**Better:** implement draining and graceful termination.

### Treating Snapshots as Complete Backups

A volume snapshot does not automatically provide application-consistent database recovery.

**Better:** combine infrastructure backups with application/database-native backup strategies.

### No Rollback Plan

A deployment without rollback increases recovery time during incidents.

**Better:** maintain previous artifacts and a tested rollback procedure.

### No Restore Testing

A backup that has never been restored is an assumption.

**Better:** periodically perform recovery exercises.

### Hard-Coding AWS Resource IDs

Resource IDs can change when infrastructure is replaced.

**Better:** use IaC, tags, discovery, and configuration management.

### Ignoring Service Quotas

An ASG can be correctly configured but still unable to scale because of quotas.

**Better:** monitor quota utilization and maintain operational headroom.

## Interview Traps

### Should Production EC2 Instances Be Manually Patched?

Manual patching may be necessary during emergencies, but it should not be the normal operating model for immutable infrastructure.

Use automated patching or controlled AMI replacement.

### Why Use an Auto Scaling Group Even With Stable Traffic?

ASGs provide automated replacement, health management, controlled scaling, and integration with deployment workflows.

### Why Use an ALB Instead of Public EC2 IPs?

The ALB provides a stable application entry point, health-aware routing, TLS termination, and integration with scalable backend fleets.

### Why Are IAM Roles Preferred Over Access Keys on EC2?

IAM roles provide temporary credentials through the instance profile and avoid distributing long-lived credentials onto hosts.

### Does Multi-AZ EC2 Guarantee High Availability?

No.

The database, cache, queue, DNS, load balancer, external dependencies, and application design can still introduce single points of failure.

### Why Is `running` Not Equivalent to Healthy?

An EC2 instance can be running while:

- The application process is dead.
- The target is unhealthy.
- The database is unavailable.
- The filesystem is full.
- Requests are timing out.

Health must be evaluated at multiple layers.

### Why Should Applications Be Stateless?

Stateless application instances are easier to replace and scale.

Session state, files, and durable application data should be stored in appropriate external systems when possible.

### What Makes an EC2 Deployment Production-Ready?

A production deployment should have:

- Reproducible infrastructure
- Secure access
- Health checks
- Monitoring
- Automated replacement
- Backup and recovery
- Controlled rollout
- Rollback capability
- Capacity planning
- Operational ownership

## Key Takeaways

- **Treat EC2 as replaceable compute:** use Launch Templates, Auto Scaling, immutable artifacts, and controlled instance replacement instead of relying on manually maintained servers.
- **Design the complete failure boundary:** Multi-AZ EC2, load balancing, dependency capacity, health checks, backups, and recovery procedures must work together; EC2 redundancy alone does not provide application availability.
- **Secure access by default:** use IAM roles, IMDSv2, private networking, restricted Security Groups, Systems Manager, encrypted storage, and centralized secret management.
- **Make operations observable and reversible:** centralize logs and metrics, monitor application and infrastructure health, use controlled deployments, maintain rollback paths, and test disaster recovery.
- **Manage EC2 as part of a larger system:** capacity, database connections, Redis, Kafka, EBS, networking, quotas, cost, and application behavior must all be considered when scaling or changing production infrastructure.