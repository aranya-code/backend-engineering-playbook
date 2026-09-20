# 07- Backup and Recovery

## Overview

EC2 backup and recovery is the process of protecting instance configuration, operating-system state, application data, and persistent storage so that workloads can be restored after accidental deletion, corruption, hardware failure, security incidents, or regional disruption.

A production backup strategy should not be based on a single mechanism such as an AMI or an EBS snapshot. Different recovery mechanisms protect different parts of the system.

A typical EC2 recovery architecture is:

```text
                    Production Workload
                           |
              +------------+------------+
              |                         |
              v                         v
        EC2 Configuration          Persistent Data
              |                         |
              v                         v
        Golden AMI / IaC          EBS Snapshots
              |                         |
              +------------+------------+
                           |
                           v
                    Backup Repository
                           |
              +------------+------------+
              |                         |
              v                         v
        Recovery Testing         Cross-Region Copy
              |                         |
              +------------+------------+
                           |
                           v
                    Disaster Recovery
```

The important distinction is:

- **AMI** primarily captures an instance launchable image and its associated EBS-backed storage configuration.
- **EBS snapshot** protects the contents of an individual EBS volume.
- **Application/database backup** protects logical application state and may provide recovery guarantees that infrastructure-level snapshots cannot.
- **Infrastructure as Code** recreates infrastructure configuration.
- **Cross-Region copies** protect against Region-level failures and some regional disaster scenarios.

A mature strategy combines these mechanisms according to the workload's Recovery Point Objective (RPO) and Recovery Time Objective (RTO).

## RPO and RTO

Two requirements should drive backup design.

| Requirement | Meaning | Example |
|---|---|---|
| RPO | Maximum acceptable data loss measured in time | RPO = 15 minutes |
| RTO | Maximum acceptable recovery time | RTO = 1 hour |

Suppose a database snapshot is created once every 24 hours.

If the database fails immediately before the next backup, the potential data-loss window could approach 24 hours.

That may be acceptable for a development environment but not for a financial transaction system.

A production design should therefore start with:

```text
Business Requirement
        |
        v
       RPO
        |
        v
Backup Frequency / Replication
        |
        v
       RTO
        |
        v
Recovery Architecture
        |
        v
Recovery Testing
```

## Backup Layers

A reliable EC2 environment normally protects multiple layers.

| Layer | Protection mechanism |
|---|---|
| Infrastructure | Terraform / CloudFormation / CDK |
| EC2 image | AMI / golden image |
| EBS data | EBS snapshots |
| Database | Database-native backups |
| Application files | Application-aware backup or object storage |
| Configuration | Git / Parameter Store / Secrets Manager |
| Logs | CloudWatch Logs / S3 |
| Cross-Region resilience | Snapshot or backup replication |
| Recovery procedures | Version-controlled runbooks |

No single layer is sufficient for every failure scenario.

## AMI vs EBS Snapshot

AMI and EBS snapshots are related but serve different operational purposes.

| Capability | AMI | EBS Snapshot |
|---|---|---|
| Primary purpose | Launchable EC2 image | Volume backup |
| OS recovery | Yes | Indirectly |
| Instance configuration | Captured as image metadata | No |
| Individual volume restore | Not the primary purpose | Yes |
| Launch new EC2 instance | Yes | Requires volume creation/attachment |
| Good for golden images | Yes | No |
| Good for data-volume backup | Possible indirectly | Yes |
| Application-consistency guarantee | No | No |
| Cross-Region recovery | Copy AMI | Copy snapshot |

An AMI should generally be treated as a **machine recovery artifact**, not as a replacement for application-aware data backups.

## EBS Snapshots

EBS snapshots provide point-in-time protection for EBS volumes.

The basic workflow is:

```text
EBS Volume
    |
    v
Create Snapshot
    |
    v
Snapshot Storage
    |
    +----> Retention
    |
    +----> Cross-Region Copy
    |
    +----> Restore
             |
             v
         New EBS Volume
             |
             v
          EC2 Instance
```

Create a snapshot:

```bash
aws ec2 create-snapshot \
    --profile production \
    --region ap-south-1 \
    --volume-id vol-0123456789abcdef0 \
    --description "Production application data backup"
```

Describe snapshots:

```bash
aws ec2 describe-snapshots \
    --profile production \
    --region ap-south-1 \
    --owner-ids self
```

Filter by volume:

```bash
aws ec2 describe-snapshots \
    --profile production \
    --region ap-south-1 \
    --filters Name=volume-id,Values=vol-0123456789abcdef0 \
    --query 'Snapshots[].{
        Snapshot:SnapshotId,
        Volume:VolumeId,
        State:State,
        StartTime:StartTime,
        Size:VolumeSize
    }' \
    --output table
```

EBS snapshots are incremental after the initial snapshot, so subsequent snapshots generally store only changed blocks while preserving the ability to restore the volume to a point in time.

## Snapshot Consistency

A critical production concern is **what state the application was in when the snapshot was taken**.

For a simple filesystem containing independent files, a crash-consistent snapshot may be sufficient.

For databases and transactional applications, infrastructure-level snapshots do not automatically provide application-level consistency.

For example:

```text
PostgreSQL
   |
   +-- WAL
   |
   +-- Data files
   |
   +-- Transactions
```

Taking an EBS snapshot while writes are occurring does not mean the resulting snapshot is equivalent to a clean database backup.

For critical databases, prefer database-native mechanisms such as:

- PostgreSQL physical backups
- PostgreSQL WAL archiving
- Managed database backup mechanisms
- Application-aware backup workflows

EBS snapshots can provide an additional infrastructure recovery layer.

## Application-Consistent Backups

Application consistency is important when multiple volumes or application components must represent one logical state.

For example:

```text
EC2
 |
 +-- Root Volume
 |
 +-- Application Volume
 |
 +-- Database Volume
```

If these volumes are backed up independently at different times, restoring them may produce inconsistent application state.

For applications with strict consistency requirements:

1. Quiesce writes where practical.
2. Flush application buffers if required.
3. Coordinate database/application backup mechanisms.
4. Create the infrastructure snapshot.
5. Resume normal operation.
6. Validate the resulting backup.

The correct approach depends on the application architecture.

## Creating Snapshots with Tags

Tags make backup lifecycle management much easier.

Example:

```bash
aws ec2 create-snapshot \
    --profile production \
    --region ap-south-1 \
    --volume-id vol-0123456789abcdef0 \
    --description "Production PostgreSQL data backup" \
    --tag-specifications \
        'ResourceType=snapshot,Tags=[{Key=Environment,Value=production},{Key=Backup,Value=daily},{Key=Application,Value=postgresql}]'
```

Useful tags include:

| Tag | Example |
|---|---|
| `Environment` | `production` |
| `Application` | `payments` |
| `Backup` | `daily` |
| `Retention` | `30d` |
| `Owner` | `platform` |
| `CostCenter` | `backend` |

Tagging should be standardized rather than created ad hoc by individual engineers.

## Snapshot Retention

A backup strategy needs explicit retention rules.

Example:

| Backup | Retention |
|---|---:|
| Hourly | 24 hours |
| Daily | 30 days |
| Weekly | 12 weeks |
| Monthly | 12 months |

The exact values should come from business, compliance, and recovery requirements.

Avoid indefinite retention unless required.

Uncontrolled snapshot accumulation creates:

- Cost
- Operational complexity
- Longer inventory searches
- Increased risk of deleting the wrong artifact later

## Automated Backup Lifecycle

For production environments, use automated backup policies rather than relying on engineers to execute CLI commands manually.

AWS Backup can centrally manage backups for supported AWS resources and provides policy-based scheduling and retention capabilities.

A centralized model can look like:

```text
AWS Resources
     |
     v
Backup Plan
     |
     +-- Schedule
     |
     +-- Retention
     |
     +-- Vault
     |
     +-- Encryption
     |
     +-- Copy Rules
     |
     v
Recovery Points
```

Centralized backup management is particularly useful when multiple AWS services and environments need consistent governance.

## AMI Creation

An AMI can be created from an EC2 instance for machine-level recovery.

Example:

```bash
aws ec2 create-image \
    --profile production \
    --region ap-south-1 \
    --instance-id i-0123456789abcdef0 \
    --name "payments-api-2026-09-20" \
    --description "Production payments API recovery image"
```

Describe AMIs:

```bash
aws ec2 describe-images \
    --profile production \
    --region ap-south-1 \
    --owners self
```

A golden AMI typically contains:

- Operating system
- Security updates
- Runtime
- Nginx
- Python
- Application dependencies
- Monitoring agent
- Baseline configuration

Application-specific runtime configuration should generally remain externalized.

## Golden AMI Strategy

A production image pipeline can be:

```text
Git Commit
    |
    v
CI Pipeline
    |
    v
Build AMI
    |
    v
Security Validation
    |
    v
Application Tests
    |
    v
AMI Published
    |
    v
Launch Template
    |
    v
Auto Scaling Group
```

This is more reliable than manually configuring production instances and then creating an AMI from an unknown state.

A golden AMI should be:

- Reproducible
- Versioned
- Tested
- Patched
- Tagged
- Traceable to source code
- Free of secrets

## AMI Metadata and Secrets

Do not bake secrets into an AMI.

Avoid:

```text
AMI
 |
 +-- .env
 +-- database password
 +-- API token
 +-- private key
```

Prefer:

```text
AMI
 |
 +-- Application
 +-- Runtime
 +-- Monitoring
       |
       v
Instance Role
       |
       +-- Secrets Manager
       |
       +-- Parameter Store
```

This allows the same image to be used across environments without embedding environment-specific credentials.

## Restoring an EBS Snapshot

A snapshot restore creates a new EBS volume.

Describe the snapshot:

```bash
aws ec2 describe-snapshots \
    --profile production \
    --region ap-south-1 \
    --snapshot-ids snap-0123456789abcdef0
```

Create a volume from it:

```bash
aws ec2 create-volume \
    --profile production \
    --region ap-south-1 \
    --availability-zone ap-south-1a \
    --snapshot-id snap-0123456789abcdef0 \
    --volume-type gp3
```

The new EBS volume must be created in the same Availability Zone where the target EC2 instance is located if it is going to be attached to that instance.

Verify:

```bash
aws ec2 describe-volumes \
    --profile production \
    --region ap-south-1 \
    --volume-ids vol-0123456789abcdef0
```

Then attach it:

```bash
aws ec2 attach-volume \
    --profile production \
    --region ap-south-1 \
    --volume-id vol-0123456789abcdef0 \
    --instance-id i-0123456789abcdef0 \
    --device /dev/sdf
```

The Linux device name may appear differently because modern EC2 instances can expose EBS devices through NVMe mappings.

## Restoring a Root Volume

Root-volume recovery requires additional care.

A typical process is:

```text
Identify Failed Root Volume
          |
          v
Stop Instance
          |
          v
Detach Root Volume
          |
          v
Create Replacement Volume
          |
          v
Attach Replacement Root Volume
          |
          v
Start Instance
          |
          v
Run Health Checks
```

The exact procedure depends on the operating system, boot configuration, filesystem, and architecture.

For serious production incidents, restoring a known-good AMI and launching a replacement instance can be safer than manually repairing an individual instance.

## Instance Replacement vs Repair

Modern EC2 operations generally favor immutable replacement for stateless application instances.

### Repair

```text
Broken EC2
   |
   +-- SSH
   +-- Fix package
   +-- Fix config
   +-- Restart
```

### Replacement

```text
Known-good AMI
      |
      v
Launch New EC2
      |
      v
Health Check
      |
      v
ALB
      |
      v
Terminate Broken EC2
```

Replacement is generally easier to reproduce and audit.

Manual repair may still be appropriate when:

- Data must be recovered from the original filesystem
- Forensic investigation is required
- The instance contains unique state
- The failure is not yet understood
- Replacing the instance would destroy important evidence

## Cross-Region Backup

A snapshot or AMI stored only in the primary Region does not protect effectively against a Region-level disaster.

A stronger architecture is:

```text
Primary Region
ap-south-1
    |
    +-- EBS Snapshot
    |
    +-- AMI
    |
    v
Cross-Region Copy
    |
    v
Secondary Region
ap-southeast-1
```

Copy an EBS snapshot:

```bash
aws ec2 copy-snapshot \
    --profile production \
    --region ap-southeast-1 \
    --source-region ap-south-1 \
    --source-snapshot-id snap-0123456789abcdef0 \
    --description "DR copy of production backup"
```

Cross-Region copies can protect against regional failures, but they do not by themselves create a complete disaster recovery environment.

You also need to consider:

- VPC
- Subnets
- Security Groups
- IAM roles
- Load balancers
- Route 53
- AMIs
- Application configuration
- Database recovery
- Secrets
- External dependencies

## Cross-Account Backup

For stronger protection against account-level compromise or destructive administrative actions, consider maintaining backups in a separate AWS account.

Example:

```text
Production Account
       |
       | Backup Copy
       v
Backup Account
       |
       v
Backup Vault
       |
       v
Recovery
```

This creates a separate security boundary.

Cross-account backup architecture is especially valuable for ransomware and compromised-credential scenarios.

## Encryption

Backups should generally be encrypted.

For encrypted EBS snapshots:

```text
EBS Volume
    |
    | encrypted
    v
EBS Snapshot
    |
    | encrypted
    v
Recovery Volume
```

When using customer managed KMS keys, recovery workflows must account for:

- KMS key permissions
- Key policy
- IAM permissions
- Cross-account access
- Cross-Region key considerations
- Key availability

A backup that cannot be decrypted during an incident is operationally equivalent to an unavailable backup.

## Backup Security

Protect backups against unauthorized deletion and modification.

Important controls include:

- Least-privilege IAM
- Separate backup account
- KMS encryption
- Restricted snapshot permissions
- Backup vault access controls
- Backup deletion protection where supported
- CloudTrail auditing
- MFA for sensitive administrative operations
- Restricted root-account usage
- Immutable or logically isolated backup strategies

The backup system itself is part of the security boundary.

## Recovery Testing

A backup is not proven until it has been restored successfully.

A practical recovery test:

```text
Select Backup
      |
      v
Create Recovery Environment
      |
      v
Restore EBS / AMI
      |
      v
Start EC2
      |
      v
Validate Application
      |
      v
Validate Data
      |
      v
Validate Networking
      |
      v
Measure RTO
      |
      v
Document Result
```

Test at least:

- Bootability
- Filesystem integrity
- Application startup
- Configuration loading
- Database connectivity
- Redis connectivity
- Network connectivity
- IAM permissions
- TLS configuration
- Application health checks

## Recovery Validation

A successful AWS API operation does not prove that the application has been recovered.

For example:

```text
create-volume -> success
```

does not mean:

```text
Database -> healthy
```

After recovery, validate the complete application path:

```text
DNS
 |
 v
Load Balancer
 |
 v
EC2
 |
 v
Nginx
 |
 v
Django / FastAPI
 |
 +--> PostgreSQL
 |
 +--> Redis
```

For databases, perform application-level validation rather than checking only that the database process is running.

## Recovery Runbook

A production recovery runbook should contain:

### Identification

- Incident ID
- Affected Region
- Affected resources
- Failure type
- RPO requirement
- RTO requirement

### Recovery Inputs

- AMI ID
- Snapshot ID
- Volume ID
- KMS key
- VPC ID
- Subnet ID
- Security Group IDs
- IAM role
- Launch Template version

### Recovery Procedure

1. Confirm the failure domain.
2. Identify the latest valid recovery point.
3. Verify backup integrity and permissions.
4. Select the recovery Region if required.
5. Restore infrastructure.
6. Restore persistent data.
7. Launch replacement instances.
8. Validate application health.
9. Validate data integrity.
10. Restore traffic.
11. Monitor the recovered environment.
12. Document the incident.

## Infrastructure as Code During Recovery

Infrastructure should be reproducible from source control.

Example:

```text
Git Repository
     |
     v
Terraform / CloudFormation
     |
     +-- VPC
     +-- Security Groups
     +-- ALB
     +-- Target Groups
     +-- ASG
     +-- IAM
     |
     v
Recovery Region
```

This avoids depending on undocumented console changes.

A recovery plan should explicitly identify which components are:

- Recreated from IaC
- Restored from backup
- Copied cross-region
- Retrieved from external systems

## Database Recovery

For EC2-hosted PostgreSQL:

```text
PostgreSQL
    |
    +-- WAL Archive
    |
    +-- Base Backup
    |
    +-- EBS Snapshot
    |
    +-- Configuration Backup
```

A robust strategy can combine:

- PostgreSQL-native backups
- WAL archiving
- EBS snapshots
- Cross-Region copies
- Periodic recovery tests

Do not assume an EBS snapshot alone provides point-in-time database recovery.

For managed databases such as Amazon RDS, use the service's native backup and recovery capabilities rather than treating the database as just another EC2 filesystem.

## Application Data and Stateless EC2

For a Django or FastAPI service:

```text
EC2
 |
 +-- Application Code
 +-- Python Runtime
 +-- Nginx
 +-- Temporary Files
```

The instance should ideally be disposable.

Persistent data should live in dedicated systems such as:

- PostgreSQL
- Amazon S3
- Redis where appropriate
- EBS volumes where required
- Managed AWS services

This allows:

```text
Failed EC2
    |
    X
    |
    v
New EC2 from AMI
    |
    v
Reconnect to persistent services
```

The less unique state stored inside an EC2 instance, the easier recovery becomes.

## Backup and Auto Scaling

Backups should not be tightly coupled to individual ephemeral application instances.

For an ASG:

```text
Launch Template
      |
      v
ASG
 +----+----+
 |    |    |
EC2  EC2  EC2
 |    |    |
 +----+----+
      |
      v
Persistent Data
      |
      v
Backup Strategy
```

Backing up every disposable application instance independently may create unnecessary operational complexity.

Instead:

- Bake application software into versioned AMIs.
- Store persistent data separately.
- Back up stateful volumes and services.
- Recreate application instances from known-good images.

## Backup Monitoring

Backup jobs should themselves be monitored.

Track:

- Backup success
- Backup failure
- Backup age
- Number of recovery points
- Retention compliance
- Cross-Region copy status
- Cross-account copy status
- KMS errors
- Storage growth
- Recovery test results

A useful alert is:

```text
Latest successful backup
        |
        v
Older than allowed RPO
        |
        v
ALERT
```

Do not only monitor whether a backup job ran. Monitor whether a usable recovery point exists.

## Backup Cost Management

Backup storage is cheaper than many forms of downtime, but uncontrolled retention can still become expensive.

Review:

- Snapshot retention
- AMI retention
- Cross-Region copies
- Duplicate recovery points
- Unused snapshots
- Backup vault storage
- Recovery test environments

Use lifecycle policies where appropriate.

Avoid deleting backups solely based on age if they are required for:

- Compliance
- Security investigations
- Legal retention
- Disaster recovery
- Long-term operational recovery

## Disaster Recovery Strategies

Common EC2 disaster recovery models include:

| Strategy | Recovery speed | Cost | Complexity |
|---|---|---|---|
| Backup and restore | Lower | Lower | Lower |
| Pilot light | Moderate | Moderate | Moderate |
| Warm standby | Faster | Higher | Higher |
| Multi-Region active/active | Very fast potential recovery | High | High |

### Backup and Restore

```text
Primary Region
    |
    v
Backups
    |
    X Failure
    |
    v
Restore in Recovery Region
```

Lowest infrastructure cost, but recovery takes longer.

### Pilot Light

Core infrastructure or data services remain available in the recovery Region while application capacity is created when required.

### Warm Standby

A reduced-capacity production environment is continuously available in the recovery Region.

### Multi-Region Active/Active

Traffic is actively served from multiple Regions.

This provides strong availability characteristics but requires significantly more architectural complexity.

Do not select a DR model based solely on technology. Select it based on RTO, RPO, business impact, and operational capability.

## Recovery From Accidental Instance Termination

If an EC2 instance is terminated accidentally:

```text
Identify Instance
      |
      v
Identify AMI / Launch Template
      |
      v
Identify Persistent Volumes
      |
      v
Restore Required Data
      |
      v
Launch Replacement
      |
      v
Attach / Restore Storage
      |
      v
Register With ALB
      |
      v
Validate Application
```

This is much easier when the environment is designed around immutable infrastructure.

If the instance contained unique data that was not backed up, recovery may not be possible.

## Recovery From EBS Corruption

A practical workflow is:

```text
Affected Volume
      |
      v
Stop Writes
      |
      v
Identify Last Known-Good Snapshot
      |
      v
Restore Snapshot
      |
      v
Create Replacement Volume
      |
      v
Attach to Recovery Instance
      |
      v
Validate Filesystem
      |
      v
Validate Application Data
      |
      v
Promote / Replace
```

Do not overwrite the only potentially recoverable volume before establishing a safe recovery point.

## Recovery From Regional Failure

A Region-level recovery plan might be:

```text
Primary Region Failure
        |
        v
Select DR Region
        |
        v
Provision Infrastructure
        |
        v
Restore AMI / Launch Template
        |
        v
Restore EBS / Database Data
        |
        v
Configure Networking
        |
        v
Configure Secrets
        |
        v
Start Application Fleet
        |
        v
Validate Health
        |
        v
Shift DNS / Traffic
        |
        v
Monitor
```

This workflow must be tested before an actual regional incident.

## Common Mistakes

### Treating an AMI as a Complete Backup

An AMI is useful for machine recovery but does not replace application-aware backups.

**Avoid it:** maintain separate protection for persistent data and databases.

### Never Testing Restores

A successful snapshot operation proves only that AWS created the recovery point.

**Avoid it:** perform scheduled restore tests.

### Keeping All Backups in One Region

A regional outage can affect both the workload and its backups.

**Avoid it:** copy critical recovery points to another Region where justified by the DR requirements.

### Embedding Secrets in AMIs

Secrets become replicated wherever the AMI is copied.

**Avoid it:** retrieve secrets at runtime through IAM-authorized services.

### Backing Up Ephemeral Instances Instead of State

If EC2 instances are designed to be disposable, backing up every instance can hide architectural problems.

**Avoid it:** make application instances reproducible and back up the actual persistent state.

### Ignoring KMS Permissions

An encrypted backup may exist but still be unusable if the recovery identity cannot use the required KMS key.

**Avoid it:** include KMS permissions and key policies in recovery testing.

### Assuming Snapshots Are Database Backups

A filesystem snapshot is not automatically equivalent to a transactionally consistent database backup.

**Avoid it:** use database-native backup mechanisms for databases.

### No Retention Policy

Unlimited snapshots increase cost and operational complexity.

**Avoid it:** define retention based on RPO, compliance, and recovery requirements.

### Restoring Infrastructure Without Configuration

A recovered EC2 instance may still fail because required configuration, DNS, secrets, or IAM roles are missing.

**Avoid it:** include infrastructure and configuration recovery in the runbook.

## Production Best Practices

### Design for Replacement

Prefer:

```text
Known-good AMI
      |
      v
New EC2
      |
      v
Health Check
      |
      v
Traffic
```

over:

```text
Broken EC2
      |
      v
Manual repair
      |
      v
Unknown final state
```

### Separate Compute From State

Keep EC2 instances as stateless as practical.

Persistent state should have its own backup and recovery strategy.

### Automate Backups

Use policy-driven mechanisms such as AWS Backup, scheduled automation, or service-native backup capabilities instead of relying on manual commands.

### Version Recovery Artifacts

Track:

- AMI ID
- AMI creation date
- Application version
- Git commit
- Launch Template version
- Snapshot ID
- Backup policy version

### Encrypt Recovery Points

Use encryption consistently and test KMS access during restoration.

### Test Cross-Region Recovery

If the business requirement includes regional disaster recovery, actually restore in the target Region.

### Document Recovery Dependencies

A recovery runbook should identify every dependency required to make the application operational.

### Monitor Backup Freshness

Alert when the newest valid backup exceeds the required RPO.

### Keep Recovery Procedures Version-Controlled

Store runbooks and infrastructure definitions alongside engineering source code.

## Production Recovery Checklist

### Backup

- [ ] EC2 machine recovery strategy defined
- [ ] EBS volumes backed up
- [ ] Database-native backups configured
- [ ] Backup retention defined
- [ ] Backup encryption enabled
- [ ] Backup jobs monitored
- [ ] Backup freshness monitored

### Recovery

- [ ] RPO documented
- [ ] RTO documented
- [ ] Recovery runbook available
- [ ] AMI recovery tested
- [ ] EBS restore tested
- [ ] Database restore tested
- [ ] Application validation tested
- [ ] DNS recovery tested
- [ ] IAM and KMS recovery tested

### Disaster Recovery

- [ ] Critical backups copied to another Region
- [ ] Cross-account protection evaluated
- [ ] Recovery infrastructure defined as code
- [ ] DR dependencies documented
- [ ] DR environment tested
- [ ] Traffic failover procedure tested

### Security

- [ ] Backup access follows least privilege
- [ ] KMS permissions tested
- [ ] Secrets excluded from AMIs
- [ ] Backup deletion permissions restricted
- [ ] CloudTrail auditing enabled
- [ ] Sensitive recovery operations protected

## Interview Traps

### Is an EBS Snapshot a Full Backup of an EC2 Instance?

No.

An EBS snapshot protects an EBS volume. An EC2 instance may contain multiple volumes, instance configuration, IAM associations, networking configuration, and application dependencies.

### Is an AMI the Same as an EBS Snapshot?

No.

An AMI is a launchable machine image that references its backing storage snapshots and includes image metadata required for launching instances.

### Are EBS Snapshots Application-Consistent?

Not automatically.

They provide infrastructure-level point-in-time protection, but database recovery requirements may require application-aware or database-native backups.

### Does a Snapshot Automatically Protect Against Region Failure?

No.

A recovery point stored only in one Region does not provide protection against loss of that Region.

### Why Test Backups?

Because backup creation and successful recovery are different operations.

A recovery test verifies:

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
Application
  |
  v
Data
  |
  v
Traffic
```

### Why Use AMIs With Auto Scaling?

An AMI provides a repeatable machine image from which the ASG can launch replacement instances.

### Why Keep EC2 Stateless?

Stateless instances can be replaced rather than repaired, which improves scalability, deployment safety, and disaster recovery.

### What Determines Backup Frequency?

Primarily the required RPO, along with application consistency, cost, storage behavior, compliance, and operational requirements.

### What Determines the Recovery Architecture?

Primarily the required RTO and RPO, combined with business impact, application dependencies, budget, and operational capability.

## Key Takeaways

- **Use layered protection:** combine golden AMIs, EBS snapshots, database-native backups, Infrastructure as Code, and configuration management rather than treating one artifact as the complete backup strategy.
- **Design around RPO and RTO:** backup frequency, retention, replication, and recovery architecture should be derived from how much data loss and downtime the workload can tolerate.
- **Test restoration, not just backup creation:** a recovery point is only operationally useful when it can be restored, decrypted, booted, and validated as a working application.
- **Separate compute from persistent state:** make EC2 instances reproducible and disposable while protecting databases, EBS data, and other persistent state independently.
- **Plan for regional and account-level failures when required:** cross-Region and cross-account recovery points, IaC, KMS access, networking, secrets, and tested recovery runbooks are necessary for serious disaster recovery.