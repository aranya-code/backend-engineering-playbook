# Backup & Recovery

## Overview

Even the most reliable Kafka cluster can experience failures caused by hardware issues, accidental deletion, software bugs, data corruption, or regional outages. A production-ready Kafka deployment must therefore include a well-defined backup and recovery strategy.

Backup and Recovery is not just about copying Kafka log files—it also includes protecting topic configurations, cluster metadata, schemas, Access Control Lists (ACLs), and disaster recovery procedures.

An effective recovery strategy minimizes:

- Data loss
- Downtime
- Business impact
- Recovery time

This chapter explains how to prepare Kafka for failure and recover safely when failures occur.

---

# Why Backup Matters

Suppose a broker fails permanently.

```text
Broker Failure

↓

Disk Lost

↓

Messages Lost?
```

If replication exists:

```text
Follower Replica

↓

Leader Election

↓

Continue Processing
```

Replication protects against individual broker failures.

However, replication is **not** a backup.

---

# Replication vs Backup

Replication:

```text
Protects Against

↓

Broker Failure
```

Backup:

```text
Protects Against

↓

Data Loss

↓

Human Error

↓

Disaster
```

Both are required in production.

---

# Common Failure Scenarios

Production failures include:

- Broker failure
- Disk corruption
- Accidental topic deletion
- Configuration mistakes
- Data center outage
- Cloud region outage
- Software bugs
- Ransomware attacks

A backup strategy should address each scenario.

---

# What Should Be Backed Up?

A Kafka deployment includes more than message data.

Backup:

- Topic data
- Topic configuration
- Broker configuration
- ACLs
- Security certificates
- Schema Registry
- Client configuration
- Infrastructure configuration

Everything required to rebuild the cluster should be recoverable.

---

# Backup Architecture

```text
Kafka Cluster

↓

Topic Data

↓

Metadata

↓

Configuration

↓

Backup Storage

↓

Recovery
```

Backups should be stored separately from the Kafka cluster.

---

# Topic Data

Messages stored inside partitions are often the largest component.

Example:

```text
Orders

Payments

Inventory

Audit Logs
```

Critical topics may require long-term archival.

---

# Topic Configuration

Backup:

- Partition count
- Replication factor
- Retention settings
- Cleanup policy
- Compression

These settings are required when recreating topics.

---

# Broker Configuration

Protect broker configuration files.

Example:

```text
server.properties
```

Include:

- Listeners
- Security
- Replication
- Storage paths
- JVM settings

---

# Security Configuration

Backup:

- SSL certificates
- Keystores
- Truststores
- SASL configuration
- JAAS files

Without these files, clients may be unable to reconnect after recovery.

---

# ACL Backup

ACLs should also be preserved.

Example:

```text
READ

WRITE

ALTER

DELETE
```

Losing ACLs can prevent applications from accessing Kafka.

---

# Schema Registry Backup

If using Schema Registry:

Backup:

- Avro schemas
- Protobuf schemas
- JSON Schemas
- Compatibility settings

Schema loss can prevent applications from deserializing messages correctly.

---

# Infrastructure as Code

Store infrastructure definitions in version control.

Examples:

- Terraform
- Helm
- Kubernetes manifests
- Ansible

Infrastructure becomes reproducible.

---

# Backup Storage

Store backups in a different location.

Example:

```text
Kafka Cluster

↓

Cloud Storage

↓

Backup Region
```

Never store backups only on the same brokers.

---

# Cross-Region Backup

Example:

```text
Primary Region

↓

Backup Region
```

Regional failures should not destroy both production and backup data.

---

# MirrorMaker 2

Kafka provides **MirrorMaker 2 (MM2)** for cluster replication.

Example:

```text
Primary Cluster

↓

MirrorMaker 2

↓

Secondary Cluster
```

Common use cases:

- Disaster Recovery
- Multi-region replication
- Cluster migration

---

# Cluster Migration

Migration workflow:

```text
Old Cluster

↓

MirrorMaker

↓

New Cluster

↓

Switch Clients
```

Applications experience minimal downtime.

---

# Broker Recovery

Suppose one broker fails.

```text
Broker 2

↓

Hardware Failure
```

Recovery:

```text
Replace Server

↓

Install Kafka

↓

Restore Configuration

↓

Join Cluster

↓

Replica Synchronization
```

Kafka automatically rebuilds replicas.

---

# Topic Recovery

Suppose a topic is accidentally deleted.

Recovery:

```text
Restore Backup

↓

Recreate Topic

↓

Restore Data
```

Without backups, deleted topics cannot be recovered.

---

# Disaster Recovery

Example:

```text
Entire Data Center

↓

Unavailable
```

Recovery:

```text
Secondary Region

↓

Promote Cluster

↓

Reconnect Clients
```

Business operations continue from the recovery site.

---

# Recovery Objectives

Two important metrics:

### Recovery Time Objective (RTO)

How quickly the service must recover.

Example:

```text
15 Minutes
```

---

### Recovery Point Objective (RPO)

Maximum acceptable data loss.

Example:

```text
5 Minutes
```

Lower RPO values generally require more sophisticated replication strategies.

---

# Backup Frequency

Choose frequency according to business requirements.

Examples:

- Hourly
- Daily
- Weekly

Critical environments may require continuous replication.

---

# Backup Verification

Backups should be tested regularly.

Workflow:

```text
Create Backup

↓

Restore Test Environment

↓

Validate Data

↓

Document Results
```

Untested backups should not be assumed to be recoverable.

---

# Recovery Workflow

```text
Failure

↓

Assess Damage

↓

Restore Configuration

↓

Restore Data

↓

Validate Cluster

↓

Reconnect Clients

↓

Resume Operations
```

A documented runbook reduces recovery time.

---

# Monitoring Recovery

After restoration, verify:

- Broker health
- Topic availability
- Consumer lag
- Replication
- Producer connectivity
- Consumer connectivity

Monitoring confirms successful recovery.

---

# Backup Checklist

| Item | Status |
|------|--------|
| Topic data backed up | ✅ |
| Topic configurations backed up | ✅ |
| Broker configuration backed up | ✅ |
| ACLs backed up | ✅ |
| SSL certificates backed up | ✅ |
| Schema Registry backed up | ✅ |
| Infrastructure as Code stored | ✅ |
| Off-site backup configured | ✅ |
| Disaster recovery plan documented | ✅ |
| Recovery procedures tested | ✅ |

---

# Best Practices

- Treat replication and backup as separate concerns.
- Store backups outside the Kafka cluster.
- Use MirrorMaker 2 for cross-cluster replication.
- Protect configuration, schemas, and security artifacts.
- Test recovery procedures regularly.
- Define RTO and RPO targets.
- Automate backup processes where possible.
- Document every recovery procedure.
- Monitor backup success and failures.
- Perform disaster recovery drills periodically.

---

# Common Mistakes

- Assuming replication is a backup.
- Storing backups on the same infrastructure.
- Ignoring configuration backups.
- Forgetting Schema Registry data.
- Never testing recovery procedures.
- Missing disaster recovery documentation.
- Backing up data without validating restore capability.
- Ignoring cross-region disaster scenarios.

---

# Summary

Backup and recovery are essential components of operating Kafka in production. While replication protects against broker failures, it does not protect against accidental deletion, corruption, or large-scale disasters. A complete backup strategy includes message data, configurations, security settings, schemas, and infrastructure definitions. Combined with regular recovery testing and clearly defined RTO and RPO objectives, a well-designed backup and recovery plan ensures that Kafka deployments remain resilient even during major failures.

---

# Key Takeaways

- Replication improves availability but is not a replacement for backups.
- Back up topic data, configurations, security artifacts, and schemas.
- Store backups separately from the production Kafka cluster.
- MirrorMaker 2 is commonly used for cross-cluster replication and disaster recovery.
- Define Recovery Time Objective (RTO) and Recovery Point Objective (RPO).
- Test backup restoration procedures regularly.
- Automate backups and document recovery workflows.
- A validated backup and recovery strategy is essential for production-grade Kafka deployments.