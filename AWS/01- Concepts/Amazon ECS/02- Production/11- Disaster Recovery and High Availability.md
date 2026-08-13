# ECS Disaster Recovery and High Availability

# Why Disaster Recovery Matters

Many systems are designed for:

```text
Normal Operation
```

Few are designed for:

```text
Failure
```

The real test of architecture is how it behaves when things break.

---

# High Availability vs Disaster Recovery

These concepts are related but different.

---

# High Availability (HA)

Goal:

```text
Prevent Downtime
```

Examples:

- Multi-AZ ECS
- Multiple ALB Targets
- Database Replicas

---

# Disaster Recovery (DR)

Goal:

```text
Recover From Failure
```

Examples:

- Region Failure
- Data Corruption
- Major Outage

---

# Business Perspective

The question is:

```text
How Much Downtime
Can The Business Tolerate?
```

---

# Recovery Time Objective (RTO)

RTO measures:

```text
Maximum Acceptable Downtime
```

---

Example

```text
RTO = 30 Minutes
```

Service must be restored within 30 minutes.

---

# Recovery Point Objective (RPO)

RPO measures:

```text
Maximum Acceptable Data Loss
```

---

Example

```text
RPO = 5 Minutes
```

Maximum acceptable data loss is 5 minutes.

---

# Understanding Tradeoffs

Lower RTO:

```text
Higher Cost
```

---

Lower RPO:

```text
Higher Complexity
```

---

# Failure Domains

A failure domain is a boundary where failures can occur.

Examples:

```text
Container
Host
Availability Zone
Region
```

---

# ECS Failure Domains

```text
Task Failure
Instance Failure
AZ Failure
Region Failure
```

Each requires different mitigation strategies.

---

# Single-AZ Architecture

```text
ALB
 ↓
ECS Tasks
 ↓
Database
```

All in one AZ.

---

Risk

```text
AZ Failure
 ↓
Outage
```

---

# Multi-AZ Architecture

Architecture

```text
AZ-A
 ↓
Tasks

AZ-B
 ↓
Tasks

AZ-C
 ↓
Tasks
```

---

Benefits

- Higher availability
- Better fault tolerance
- Automatic recovery

---

# Multi-AZ Database

Example:

```text
Primary Database
       ↓
Standby Database
```

Different AZs.

---

Benefits

Automatic failover.

---

# ECS Multi-AZ Design

Best Practice:

```text
Spread Tasks
Across AZs
```

---

Example

```text
6 Tasks

AZ-A = 2
AZ-B = 2
AZ-C = 2
```

---

# Region Failure Scenario

Although rare:

```text
Entire AWS Region
Unavailable
```

can happen.

---

# Multi-Region Architecture

```text
Region A
 ↓
ECS

Region B
 ↓
ECS
```

---

Benefits

- Disaster recovery
- Global resilience

---

# Active-Passive Design

Primary region handles traffic.

---

Backup region remains ready.

```text
Region A
 Active

Region B
 Standby
```

---

Advantages

- Lower cost
- Simpler operations

---

Disadvantages

- Recovery delay

---

# Active-Active Design

Both regions serve traffic.

```text
Region A
Region B
```

---

Advantages

- Fastest recovery
- Better global latency

---

Disadvantages

- Higher cost
- More complexity

---

# Route 53 Failover Routing

Route 53 can monitor health.

---

Workflow

```text
Region A Healthy
      ↓
Route Traffic
```

---

Failure

```text
Region A Down
      ↓
Route To Region B
```

---

# Database Disaster Recovery

Databases are often the hardest component to recover.

---

# Backup Strategy

Use:

```text
Automated Backups
Snapshots
Point-In-Time Recovery
```

---

# Snapshot Example

```text
Database
 ↓
Snapshot
```

Stored separately.

---

# Point-In-Time Recovery

Recover database to:

```text
Specific Time
```

before an incident.

---

# Data Corruption Scenario

Example:

```text
Accidental DELETE
```

---

Solution

```text
Restore Backup
```

or

```text
Point-In-Time Recovery
```

---

# ECS Backup Considerations

Containers are:

```text
Ephemeral
```

---

Back up:

```text
Databases
EFS
S3
Configuration
```

not containers themselves.

---

# Configuration Backup

Store:

```text
Terraform
CloudFormation
CDK
```

in source control.

---

Benefits

Infrastructure can be recreated.

---

# Disaster Recovery Runbook

Every production system should have:

```text
Documented Recovery Procedures
```

---

Runbook Includes

- Failure scenarios
- Recovery steps
- Escalation paths
- Validation procedures

---

# Example Runbook

Database Failure

```text
Identify Failure
 ↓
Failover
 ↓
Validate
 ↓
Restore Service
```

---

# Chaos Engineering

Practice failure intentionally.

---

Goal

```text
Test Recovery
Before Real Failure
```

---

Examples

```text
Kill Tasks
Disable Services
Simulate Failures
```

---

Benefits

Find weaknesses before customers do.

---

# Production Outage Example

Issue:

```text
AZ Failure
```

---

Impact

```text
50% Tasks Lost
```

---

Mitigation

```text
Multi-AZ Deployment
```

Remaining tasks continue serving traffic.

---

# Production Outage Example

Issue:

```text
Database Failure
```

---

Recovery

```text
Automatic Failover
```

via Multi-AZ database.

---

# Production Outage Example

Issue:

```text
Bad Deployment
```

---

Recovery

```text
Rollback
```

to previous task definition.

---

# Business Continuity

Goal:

```text
Continue Operating
During Disruption
```

---

Requires

- DR Planning
- Runbooks
- Backups
- Monitoring

---

# Disaster Recovery Levels

## Backup Only

Lowest cost.

Highest recovery time.

---

## Pilot Light

Minimal standby environment.

---

## Warm Standby

Reduced-capacity secondary environment.

---

## Active-Active

Highest resilience.

Highest cost.

---

# Cost vs Recovery Tradeoff

| Strategy | Cost | Recovery Speed |
|-----------|------|---------------|
| Backup Only | Low | Slow |
| Pilot Light | Medium | Faster |
| Warm Standby | Higher | Fast |
| Active-Active | Highest | Fastest |

---

# Common Mistakes

## No Backups

Risk:

Permanent data loss.

---

## Untested Recovery Plan

Risk:

Recovery fails during crisis.

---

## Single-AZ Architecture

Risk:

AZ outage causes downtime.

---

## No Runbooks

Risk:

Slow incident response.

---

## Ignoring RTO/RPO

Risk:

Business expectations not met.

---

# Troubleshooting DR Readiness

Verify:

```text
Backups Exist
Recovery Tested
Failover Works
Monitoring Enabled
Runbooks Updated
```

---

# Common Interview Questions

## Difference Between HA and DR?

HA prevents downtime.

DR recovers from downtime.

---

## What is RTO?

Maximum acceptable downtime.

---

## What is RPO?

Maximum acceptable data loss.

---

## Why Use Multi-AZ?

Improve availability.

---

## Why Use Multi-Region?

Improve disaster recovery.

---

## What Should Be Backed Up?

Databases, EFS, S3, configuration.

---

# Senior Engineer Perspective

Failures are inevitable.

The question is not:

```text
Will Something Fail?
```

The question is:

```text
How Prepared Are We?
```

Senior engineers design systems that:

- Survive failures
- Recover quickly
- Minimize business impact

The best disaster recovery plan is one that is regularly tested and continuously improved.

---

# Key Takeaways

- High Availability and Disaster Recovery are different disciplines.
- RTO and RPO drive recovery strategy decisions.
- Multi-AZ improves availability.
- Multi-Region improves disaster recovery.
- Databases require special recovery planning.
- Backups are mandatory.
- Runbooks accelerate recovery.
- Chaos Engineering validates resilience.
