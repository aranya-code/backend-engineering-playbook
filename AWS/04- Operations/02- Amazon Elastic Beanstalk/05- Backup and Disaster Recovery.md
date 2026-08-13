# 05- Backup and Disaster Recovery

## Overview

Backup and disaster recovery (DR) for Amazon Elastic Beanstalk must be designed around the entire application stack, not the Elastic Beanstalk environment alone.

An Elastic Beanstalk environment can be recreated, but application availability also depends on persistent data, configuration, secrets, infrastructure, deployment artifacts, DNS, and external dependencies.

A production recovery strategy should therefore distinguish between:

- **Backup** — preserving data and configuration so they can be restored.
- **Recovery** — restoring service after a failure.
- **High availability** — continuing to serve traffic during expected component failures.
- **Disaster recovery** — restoring service after a larger regional, infrastructure, or operational failure.

A typical production architecture is:

```text
                         Route 53
                            │
                            ▼
                    Application Load
                       Balancer
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
          Beanstalk EC2            Beanstalk EC2
                │                       │
                └───────────┬───────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
              RDS                    Redis
           PostgreSQL              ElastiCache
                │
                ▼
             Backups
                │
                ▼
        Recovery / Restore
```

The key principle is:

> Rebuilding the Elastic Beanstalk environment is not the same as recovering the application.

## Recovery Objectives

Before selecting a backup strategy, define recovery objectives.

### Recovery Point Objective

**RPO** defines how much data loss is acceptable.

For example:

```text
Last successful backup
        │
        ▼
14:00 ──────────────── 15:00
                         ▲
                         │
                      Failure
```

If the RPO is one hour, losing up to approximately one hour of data may be acceptable.

Typical requirements might be:

| Workload | Example RPO |
|---|---:|
| Development | 24 hours |
| Internal application | 4–24 hours |
| Production API | 1 hour |
| Financial/critical workload | Minutes or near-zero |

The correct value depends on business requirements.

### Recovery Time Objective

**RTO** defines how long the service can remain unavailable.

For example:

```text
Failure
  │
  ▼
Detection
  │
  ▼
Recovery starts
  │
  ▼
Application restored
  │
  ▼
Traffic restored
```

If the RTO is 30 minutes, the recovery process must be capable of restoring service within that window.

### RPO vs RTO

| Objective | Question |
|---|---|
| RPO | How much data can we afford to lose? |
| RTO | How long can the system remain unavailable? |

A system requiring very low RPO and RTO generally needs a more sophisticated architecture and higher operational cost.

## What Must Be Backed Up

Do not treat the Elastic Beanstalk environment as the only recoverable asset.

A production application may depend on:

| Asset | Recovery requirement |
|---|---|
| Application source | Git repository |
| Deployment artifact | Artifact repository / CI system |
| Elastic Beanstalk configuration | Version-controlled configuration / IaC |
| Environment variables | Configuration management / secrets store |
| Secrets | Secrets Manager / Parameter Store |
| PostgreSQL data | RDS backups |
| User files | S3 |
| Redis data | Usually reconstructable, depending on workload |
| DNS | Route 53 configuration / IaC |
| IAM | Version-controlled policies / IaC |
| Security groups | IaC / configuration |
| VPC | IaC |
| Certificates | ACM configuration / IaC |
| Monitoring | CloudWatch configuration / IaC |

A useful recovery model is:

```text
Application
    │
    ├── Code ───────────────► Git
    ├── Artifacts ──────────► CI/CD artifact storage
    ├── Database ───────────► RDS backups
    ├── Files ──────────────► S3
    ├── Secrets ────────────► Secrets Manager
    ├── Infrastructure ────► IaC
    └── DNS ────────────────► Route 53 / IaC
```

## Elastic Beanstalk Environment Recovery

Elastic Beanstalk environments should be treated as reproducible infrastructure.

The recovery objective should not be:

```text
"Keep this exact EC2 instance alive forever."
```

It should be:

```text
Known configuration
       │
       ▼
Recreate environment
       │
       ▼
Deploy known-good artifact
       │
       ▼
Restore persistent data
       │
       ▼
Validate application
       │
       ▼
Restore traffic
```

This approach reduces dependence on individual instances.

## Application Code Backup

Application source code should be maintained in version control.

For example:

```text
Git repository
│
├── application/
├── requirements.txt
├── .platform/
├── .ebextensions/
├── infrastructure/
└── deployment configuration
```

Do not use an EC2 instance as the authoritative copy of application source code.

A production server should be replaceable.

## Deployment Artifact Recovery

Source code alone may not always reproduce the exact deployed application.

Production deployments should ideally produce immutable or identifiable artifacts.

Example:

```text
Git commit
    │
    ▼
CI build
    │
    ▼
Artifact
orders-api:8f31c2a
    │
    ▼
Staging
    │
    ▼
Production
```

Store enough metadata to identify:

- Git commit
- Build version
- Dependency versions
- Build timestamp
- Deployment environment

This makes rollback and incident recovery substantially easier.

## Database Backups

The database is usually the most important persistent component of a backend application.

For PostgreSQL hosted on Amazon RDS, use the database service's backup and recovery capabilities rather than attempting to make the Elastic Beanstalk EC2 filesystem the database backup mechanism.

A typical architecture is:

```text
Elastic Beanstalk
       │
       ▼
     RDS
       │
       ├── Automated backups
       ├── Snapshots
       └── Recovery procedures
```

The correct backup configuration depends on the required RPO, retention period, workload, and compliance requirements.

## Database Backup Types

Common recovery mechanisms include:

| Mechanism | Purpose |
|---|---|
| Automated backups | Routine operational recovery |
| Manual snapshots | Long-lived recovery point |
| Point-in-time recovery | Recover to a specific supported time |
| Logical backups | Portable logical representation |
| Cross-region copies | Regional disaster recovery |

Each mechanism has different recovery characteristics.

Do not assume that one backup mechanism satisfies every recovery requirement.

## Point-in-Time Recovery

Point-in-time recovery is useful when the desired recovery point is between regular snapshots.

For example:

```text
12:00        13:00        14:00
 │            │            │
 └────────────┴────────────┘
       Database changes

                    ▲
                    │
              Accidental DELETE
                    │
                    ▼
             Recover before
             destructive event
```

This is particularly valuable when an operator accidentally modifies or deletes production data.

The actual recovery capability and retention depend on the database configuration and service capabilities.

## Database Snapshot Strategy

Manual snapshots can be useful before high-risk operations.

Examples:

- Major schema migration
- Data transformation
- Large-scale cleanup
- Production database modification
- Application migration

Example workflow:

```text
Validate change
     │
     ▼
Create recovery point
     │
     ▼
Execute change
     │
     ▼
Monitor
     │
     ├── Success ──► Continue
     │
     └── Failure ──► Restore / recover
```

A snapshot is not a substitute for a tested recovery process.

## Database Migration Recovery

Database migrations require special consideration because application and schema versions must remain compatible.

Prefer backward-compatible migration patterns.

Example:

```text
Old application
      │
      ▼
Add nullable column
      │
      ▼
Deploy compatible application
      │
      ▼
Backfill data
      │
      ▼
Start using new column
      │
      ▼
Remove old structure later
```

Avoid deployments where the new application immediately requires a schema that the old application cannot understand if old instances may remain active during deployment.

## S3 Data Recovery

If the application stores user-uploaded files or other durable objects in Amazon S3, configure an appropriate data-protection strategy.

Typical options include:

- Versioning
- Lifecycle policies
- Replication where required
- Access controls
- Backup or archival strategies appropriate to the workload

Architecture:

```text
Django / FastAPI
      │
      ▼
     S3
      │
      ├── Versioning
      ├── Lifecycle
      └── Replication / recovery strategy
```

Do not rely on files stored under an Elastic Beanstalk instance's local filesystem as the authoritative copy of user data.

## Redis Recovery

Redis requires a different recovery strategy from PostgreSQL.

First determine whether Redis contains:

```text
Cache only
```

or:

```text
Business-critical persistent state
```

If Redis is only a cache:

```text
Redis failure
    │
    ▼
Cache becomes empty
    │
    ▼
Application reads database
    │
    ▼
Cache repopulates
```

Recovery is usually much simpler.

If Redis contains authoritative application state, the backup and recovery requirements become significantly more demanding.

The safest architecture is generally to keep the source of truth in durable storage and use Redis for derived or temporary state when possible.

## Configuration Recovery

Environment configuration is part of the recovery process.

Important configuration includes:

- Environment variables
- Instance configuration
- Scaling settings
- Load balancer configuration
- Health checks
- Deployment settings
- Worker configuration
- Network settings
- Security groups

Avoid relying on undocumented console configuration.

Prefer:

```text
Configuration
     │
     ▼
Version Control / IaC
     │
     ▼
Reproducible Environment
```

## Secrets Recovery

Secrets must remain recoverable without exposing them unnecessarily.

Examples:

- Database credentials
- API credentials
- Django `SECRET_KEY`
- JWT signing secrets
- Third-party service credentials

Prefer managed secret stores.

Do not create backups containing plaintext production secrets simply because they are convenient to restore.

A recovery process should define:

```text
Secret exists
     │
     ▼
Application IAM permission
     │
     ▼
Secret retrieval
     │
     ▼
Application starts
```

## Infrastructure as Code

Infrastructure as Code is one of the most important components of disaster recovery.

Infrastructure may include:

```text
VPC
├── Subnets
├── Route tables
├── NAT gateways
└── Security groups

Elastic Beanstalk
├── Application
├── Environment
└── Configuration

RDS
├── Database
└── Backup configuration

Route 53
└── DNS records
```

Using CloudFormation, AWS CDK, Terraform, or another suitable IaC approach makes infrastructure recreation significantly more predictable.

## Recovery Architecture

A stronger recovery design separates normal high availability from disaster recovery.

```text
                    Primary Region
                         │
              ┌──────────┴──────────┐
              │                     │
        Elastic Beanstalk          RDS
              │                     │
              │                     ├── Backups
              │                     │
              ▼                     ▼
            S3                 Recovery copies
              │
              ▼
         Replication
              │
              ▼
       Secondary Region
              │
              ▼
      Recovery Environment
```

The secondary-region architecture should be selected according to RTO, RPO, cost, and operational requirements.

## Disaster Recovery Strategies

Common strategies include:

| Strategy | Recovery speed | Cost | Complexity |
|---|---|---|---|
| Backup and restore | Slowest | Low | Low |
| Pilot light | Faster | Medium | Medium |
| Warm standby | Fast | Higher | Higher |
| Multi-region active/active | Fastest potential recovery | Highest | Highest |

### Backup and Restore

Infrastructure is recreated only after a disaster.

```text
Failure
  ↓
Provision infrastructure
  ↓
Restore data
  ↓
Deploy application
  ↓
Validate
  ↓
Restore traffic
```

This is usually the simplest strategy but can have a relatively high RTO.

### Pilot Light

Core data and selected infrastructure remain available while the full application environment is scaled up during recovery.

This reduces recovery time compared with rebuilding everything from scratch.

### Warm Standby

A reduced-capacity environment remains running and can be scaled up during a disaster.

This provides faster recovery at a higher ongoing cost.

### Multi-Region Active/Active

Multiple regions actively serve traffic.

This can provide strong availability characteristics but introduces significant complexity around:

- Data replication
- Consistency
- DNS
- Deployment
- Failover
- Observability
- Cost

Do not introduce multi-region architecture solely because it appears more resilient. The operational complexity must be justified by the business requirement.

## Route 53 Failover

DNS can participate in disaster recovery.

Conceptually:

```text
                    Route 53
                       │
              ┌────────┴────────┐
              ▼                 ▼
        Primary Region     Secondary Region
              │                 │
              ▼                 ▼
        Elastic Beanstalk   Recovery Stack
```

DNS failover must account for DNS caching and TTL behavior, so it should not be treated as an instantaneous traffic switch.

## Recovery Validation

Recovery procedures must be tested.

A backup that has never been restored should not be considered fully validated.

Test:

- Database restoration
- Application deployment
- Environment recreation
- Secret retrieval
- DNS configuration
- S3 object recovery
- Dependency connectivity
- Health checks
- Monitoring
- Rollback
- Traffic restoration

A useful workflow is:

```text
Backup
  ↓
Restore
  ↓
Start application
  ↓
Run health checks
  ↓
Run integration tests
  ↓
Validate data
  ↓
Measure recovery time
```

## Disaster Recovery Drill

A practical recovery drill can simulate:

```text
Primary environment unavailable
          │
          ▼
Provision recovery environment
          │
          ▼
Restore database
          │
          ▼
Deploy application
          │
          ▼
Restore configuration
          │
          ▼
Validate dependencies
          │
          ▼
Switch traffic
```

Measure the actual RTO rather than assuming it.

If the target RTO is 30 minutes but the tested recovery requires 90 minutes, the architecture does not currently satisfy the requirement.

## Backup Retention

Retention should be based on:

- Business requirements
- Compliance
- Recovery objectives
- Storage cost
- Operational requirements

A simple model might be:

```text
Recent backups
    │
    ├── Short retention
    │
    ├── Daily recovery points
    │
    └── Longer-term recovery points
```

Long-term retention should not be implemented blindly. Retaining large datasets indefinitely can significantly increase storage cost and operational complexity.

## Backup Security

Backups can contain sensitive production data and must be protected accordingly.

Consider:

- Encryption at rest
- Encryption in transit
- IAM permissions
- Backup access controls
- Cross-account protection where appropriate
- Cross-region protection where appropriate
- Audit logging
- Retention controls

A backup is not secure merely because the production database is secure.

If an attacker can access unrestricted database backups, they may bypass many production application controls.

## Backup Immutability and Deletion Protection

For critical workloads, consider controls that reduce the risk of backups being intentionally or accidentally deleted.

This is particularly important for destructive incidents such as:

```text
Compromised credentials
        │
        ▼
Attacker deletes production data
        │
        ▼
Attacker attempts to delete backups
```

Recovery architecture should account for the possibility that the same credentials used to operate production could also be used to destroy recovery assets.

Separate access and apply strong administrative controls where appropriate.

## Cross-Region Recovery

Regional disasters require a recovery strategy that does not depend exclusively on the affected region.

Potential recovery assets include:

- Database backup copies
- S3 replication
- Infrastructure definitions
- Application artifacts
- Configuration
- Secrets
- DNS configuration

A recovery region should be periodically validated rather than existing only as theoretical infrastructure.

## Cross-Account Recovery

For high-value environments, storing recovery assets in a separate AWS account can reduce blast radius.

Conceptually:

```text
Production Account
       │
       │ protected backup
       ▼
Backup / Recovery Account
       │
       ▼
Independent recovery assets
```

This can help protect recovery data from compromised production credentials.

The exact design should follow the organization's security and governance model.

## Backup Monitoring

Backup systems themselves require monitoring.

Monitor:

- Backup success
- Backup failure
- Backup age
- Retention
- Storage consumption
- Replication status
- Restore failures
- Recovery test results

A useful operational signal is:

```text
Last successful backup
        │
        ▼
Current time - backup time
        │
        ▼
Compare with RPO
```

If the last successful backup is older than the permitted RPO, the system should generate an operational alert.

## Recovery Monitoring

Recovery environments should also have observability.

Validate:

- Application health
- Database connectivity
- HTTP response codes
- Latency
- Background workers
- Queue processing
- S3 access
- External dependencies
- DNS resolution

Do not declare recovery complete merely because EC2 instances are running.

## Recovery Dependencies

Map dependencies before designing recovery.

Example:

```text
API
 │
 ├── RDS
 ├── Redis
 ├── S3
 ├── Secrets Manager
 ├── External payment API
 ├── Email provider
 └── DNS
```

If any dependency cannot be recovered within the target RTO, the overall application cannot meet that RTO.

## Recovery Order

Recovery should follow dependency order.

A typical sequence is:

```text
Infrastructure
      ↓
Networking
      ↓
Security / IAM
      ↓
Database / persistent data
      ↓
Secrets / configuration
      ↓
Application
      ↓
Background workers
      ↓
Load balancer
      ↓
DNS / traffic
      ↓
Validation
```

The exact order varies by architecture.

## Recovery Testing for Django

For a Django application, recovery validation should include more than checking whether the process starts.

Validate:

```text
Django starts
   │
   ├── Database connection
   ├── Migrations
   ├── Static files
   ├── S3 access
   ├── Redis connectivity
   ├── Celery workers
   └── External integrations
```

A practical smoke test might validate:

```text
GET /health
GET /api/
POST /api/authentication/
GET /api/resource/
```

Use representative endpoints rather than only checking the process status.

## Recovery Testing for FastAPI

For FastAPI applications, validate:

```text
Application startup
      │
      ├── Database connectivity
      ├── Redis connectivity
      ├── Configuration
      ├── External dependencies
      └── Background processing
```

Then validate critical API paths through automated smoke tests.

## Celery and Background Jobs

Background processing is part of disaster recovery.

Consider:

- Broker recovery
- Worker deployment
- Task durability
- Retry behavior
- Duplicate execution
- Idempotency
- Scheduled jobs

A recovery event can cause a task to execute more than once.

Applications should therefore make critical background operations idempotent where practical.

Example:

```text
Task received
    │
    ▼
Check idempotency key
    │
    ├── Already processed ──► Return safely
    │
    └── Not processed
             │
             ▼
        Perform operation
             │
             ▼
        Record completion
```

## Kafka Recovery Considerations

If the backend depends on Kafka, recovery planning must include:

- Topic configuration
- Consumer offsets
- Retention
- Producer configuration
- Consumer group state
- Cross-region strategy where required

Do not assume that recovering the Elastic Beanstalk application automatically recovers the messaging layer.

The application may restart successfully while processing is still inconsistent or delayed.

## Recovery Validation Checklist

```text
[ ] RPO is documented
[ ] RTO is documented
[ ] Application source is recoverable
[ ] Deployment artifacts are recoverable
[ ] Elastic Beanstalk configuration is reproducible
[ ] Infrastructure is defined through IaC where practical
[ ] Database backups are enabled
[ ] Database restore procedure is documented
[ ] Database restore has been tested
[ ] S3 data recovery is understood
[ ] Redis recovery behavior is documented
[ ] Secrets can be recovered securely
[ ] IAM permissions support recovery
[ ] Security groups can be recreated
[ ] DNS configuration is recoverable
[ ] TLS certificates are accounted for
[ ] Background workers can be recreated
[ ] Queues and messaging dependencies are covered
[ ] External dependencies are documented
[ ] Backup failures are monitored
[ ] Backup retention is defined
[ ] Backup access is restricted
[ ] Recovery assets are protected from production compromise
[ ] Cross-region recovery requirements are documented
[ ] Recovery environment can be provisioned
[ ] Recovery procedure has been tested
[ ] Actual RTO has been measured
[ ] Actual RPO has been validated
[ ] Runbooks are current
```

## Common Mistakes

### Backing Up Only the Database

Database backups do not recover:

- Application code
- Environment configuration
- Secrets
- Infrastructure
- DNS
- Deployment artifacts

**Avoid it:** define recovery for the complete application stack.

### Assuming Elastic Beanstalk Is the Backup

Elastic Beanstalk manages application environments; it is not a complete backup system for all application state.

**Avoid it:** explicitly protect every persistent dependency.

### Never Testing Restores

A backup can fail silently, be incomplete, be inaccessible, or take too long to restore.

**Avoid it:** perform regular restoration tests.

### Keeping the Only Backup in the Production Environment

If the production account or credentials are compromised, recovery assets may also be compromised.

**Avoid it:** consider separate access boundaries, accounts, or regions for critical recovery assets.

### Treating RTO as a Guess

Saying "we can restore it in 30 minutes" without testing is not a meaningful RTO.

**Avoid it:** measure recovery time during drills.

### Ignoring Application Configuration

A restored database with incorrect application configuration does not produce a functioning service.

**Avoid it:** make environment configuration reproducible.

### Forgetting Background Processing

The API may recover while Celery workers or messaging consumers remain unavailable.

**Avoid it:** include asynchronous workloads in recovery tests.

### Assuming DNS Failover Is Instantaneous

DNS resolution is affected by caching and TTL behavior.

**Avoid it:** design traffic failover with realistic DNS behavior.

### Treating Cache Data as the Source of Truth

If Redis is treated as authoritative when it was designed as a cache, recovery can become unexpectedly complex.

**Avoid it:** keep durable business state in an appropriate persistent datastore.

### Restoring Data Without Application Compatibility

A database can be restored successfully while the deployed application expects a different schema.

**Avoid it:** test application and database compatibility together.

## Production Best Practices

- Define RPO and RTO before selecting a disaster recovery architecture.
- Treat application recovery as a complete-stack problem.
- Keep application source and deployment artifacts independently recoverable.
- Store persistent application data outside Elastic Beanstalk instances.
- Use managed database backup and recovery capabilities for production databases.
- Protect S3 data with an appropriate versioning, retention, and replication strategy.
- Keep Redis reconstructable where possible by treating it as a cache rather than the system of record.
- Store infrastructure configuration in version control through IaC where practical.
- Keep production secrets in managed secret stores.
- Protect backups with independent access controls.
- Consider cross-region and cross-account recovery for critical workloads.
- Monitor backup freshness against the defined RPO.
- Regularly test database restoration and complete environment recovery.
- Measure actual recovery time instead of estimating it.
- Include workers, queues, caches, DNS, certificates, and external dependencies in recovery planning.
- Prefer immutable, identifiable application artifacts for predictable redeployment.
- Design database migrations to remain compatible during recovery and rolling deployments.
- Document recovery procedures as operational runbooks.
- Perform disaster recovery exercises periodically and update the runbooks based on findings.
- Ensure the people responsible for production operations know how to execute the recovery procedure.

## Interview Traps

### Is an Elastic Beanstalk Environment Backup Enough for Disaster Recovery?

No.

Disaster recovery must cover application code, configuration, infrastructure, persistent data, secrets, DNS, and dependencies.

### What Is the Difference Between RPO and RTO?

RPO measures acceptable data loss. RTO measures acceptable service downtime.

### Why Should Recovery Be Tested?

Because backup existence does not prove that data can be restored successfully within the required RTO.

### Should Redis Always Be Backed Up?

It depends on its role.

If Redis is only a cache, it may be rebuilt from the source of truth. If it contains authoritative state, recovery requirements are much more significant.

### Why Is Infrastructure as Code Important for Disaster Recovery?

It allows infrastructure to be recreated consistently instead of depending on undocumented manual configuration.

### Does Multi-AZ Equal Disaster Recovery?

No.

Multi-AZ primarily improves availability against failures within a region. Disaster recovery may require additional mechanisms for regional or large-scale failures.

### Is a Database Snapshot the Same as a Complete Backup Strategy?

No.

Snapshots are one recovery mechanism. A complete strategy also considers retention, point-in-time recovery, security, cross-region protection, restore testing, and RPO/RTO.

### Why Is Cross-Account Backup Useful?

It can reduce the risk that compromised production credentials can also delete or modify recovery assets.

## Key Takeaways

- Define **RPO** and **RTO** before designing backup and disaster recovery.
- Elastic Beanstalk environment recovery alone is not application disaster recovery.
- Treat the entire application stack as recoverable infrastructure.
- Keep application code, deployment artifacts, configuration, secrets, databases, object storage, DNS, and infrastructure independently recoverable.
- Use managed database backup and recovery capabilities for production PostgreSQL and other databases.
- Use point-in-time recovery where the required RPO and database capabilities justify it.
- Protect S3 data separately from Elastic Beanstalk instance storage.
- Keep application instances stateless wherever practical.
- Treat Redis differently depending on whether it is a cache or authoritative data store.
- Use Infrastructure as Code to make environments reproducible.
- Protect recovery assets from the same credentials and failure domains as production where appropriate.
- Consider cross-region and cross-account recovery for critical systems.
- Monitor backup freshness and backup failures.
- Test restores regularly; an untested backup is not a proven recovery mechanism.
- Include Celery, Kafka, queues, scheduled jobs, and other asynchronous workloads in disaster recovery planning.
- Design database migrations and application versions for compatibility during recovery.
- Do not assume DNS failover is instantaneous.
- Measure actual recovery time during disaster recovery exercises.
- Keep recovery procedures documented as executable runbooks.
- A production disaster recovery strategy is successful only when the system can recover **the required data, infrastructure, application, dependencies, and traffic within the defined RPO and RTO**.