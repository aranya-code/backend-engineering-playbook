# Production Checklist

## Overview

Deploying Apache Kafka to production involves much more than simply starting a few brokers. A production Kafka cluster must be secure, fault tolerant, scalable, observable, and capable of handling failures without data loss.

A well-designed production deployment ensures:

- High Availability
- Fault Tolerance
- Scalability
- Security
- Performance
- Disaster Recovery
- Easy Operations

This chapter provides a comprehensive checklist that backend engineers, DevOps engineers, and platform teams can use before promoting a Kafka cluster to production.

---

# Production Readiness

A production Kafka deployment should satisfy the following goals.

```text
Reliable

↓

Secure

↓

Observable

↓

Scalable

↓

Recoverable
```

If any of these areas are missing, the cluster is not production ready.

---

# Production Architecture

A typical production deployment looks like:

```text
                Producers

                    │

                    ▼

          Load Balancer (Optional)

                    │

                    ▼

        ┌─────────────────────────┐
        │     Kafka Cluster       │
        │                         │
        │ Broker 1               │
        │ Broker 2               │
        │ Broker 3               │
        └─────────────────────────┘

                    │

                    ▼

               Consumers

                    │

                    ▼

             Monitoring Stack
```

Production clusters usually consist of multiple brokers.

---

# Cluster Size

Never deploy a production Kafka cluster with a single broker.

Recommended minimum:

```text
3 Brokers
```

Larger deployments may use:

- 5 Brokers
- 7 Brokers
- 9 Brokers

depending on throughput and availability requirements.

---

# Replication Factor

Every important topic should use replication.

Recommended:

```text
Replication Factor = 3
```

Benefits:

- Fault tolerance
- High availability
- Broker failure recovery

Avoid:

```text
Replication Factor = 1
```

in production.

---

# Minimum In-Sync Replicas

Configure:

```properties
min.insync.replicas=2
```

When combined with:

```properties
acks=all
```

Kafka prevents writes if insufficient replicas are available.

---

# Producer Acknowledgements

Recommended:

```properties
acks=all
```

This provides the highest durability.

Avoid:

```properties
acks=0
```

for business-critical applications.

---

# Idempotent Producer

Enable:

```properties
enable.idempotence=true
```

Benefits:

- Prevent duplicate messages
- Safer retries
- Improved reliability

Recommended for nearly every production producer.

---

# Compression

Enable message compression.

Recommended algorithms:

- zstd
- lz4
- snappy

Compression reduces:

- Network traffic
- Disk usage
- Storage cost

---

# Partition Planning

Ensure partitions are sized appropriately.

Consider:

- Consumer parallelism
- Expected throughput
- Future scaling
- Ordering requirements

Avoid creating partitions without a capacity plan.

---

# Topic Naming

Use consistent topic names.

Example:

```text
orders.created

orders.updated

payments.completed

inventory.reserved
```

Avoid:

```text
topic1

test

demo

abc
```

---

# Topic Retention

Configure retention according to business requirements.

Examples:

```text
7 Days

30 Days

90 Days
```

Review:

- retention.ms
- retention.bytes
- cleanup.policy

---

# Cleanup Policy

Choose the correct policy.

Delete:

```text
cleanup.policy=delete
```

Compaction:

```text
cleanup.policy=compact
```

Do not use the default without understanding the workload.

---

# Security

Production clusters should enable:

- SSL/TLS
- SASL
- ACLs

Never expose Kafka without authentication.

---

# Encryption

Enable SSL for:

```text
Producer

↓

Broker

↓

Consumer
```

Also encrypt:

```text
Broker

↓

Broker
```

Replication traffic should also be protected.

---

# Authentication

Use:

```text
SASL_SSL
```

Preferred authentication:

- SCRAM
- OAuth
- Kerberos

Avoid:

```text
PLAINTEXT
```

---

# Authorization

Implement ACLs.

Every application should have:

- Dedicated service account
- Least privilege permissions

Avoid wildcard permissions whenever possible.

---

# Monitoring

Monitor continuously.

Essential metrics:

- Consumer Lag
- Broker Health
- ISR
- Disk Usage
- CPU
- Memory
- Network Throughput
- Request Latency

---

# Logging

Centralize Kafka logs.

Monitor:

- Broker failures
- Authentication failures
- Replication issues
- Controller changes
- Consumer errors

---

# Alerting

Configure alerts for:

- Broker offline
- Consumer lag
- Disk usage
- Under replicated partitions
- High request latency
- Failed authentication
- JVM memory

Alerts should notify operators before users notice problems.

---

# Capacity Planning

Estimate:

- Daily messages
- Storage growth
- Peak throughput
- Network bandwidth
- Retention storage
- Future expansion

Always leave headroom for growth.

---

# Disk Selection

Kafka performs best on fast storage.

Preferred:

- NVMe SSD
- Enterprise SSD

Avoid:

- Slow HDDs
- Network drives with high latency

Disk performance directly affects throughput.

---

# Operating System

Tune the operating system.

Examples:

- File descriptors
- Socket buffers
- Virtual memory
- Disk scheduler
- TCP settings

Kafka performance depends on OS tuning.

---

# JVM Configuration

Monitor JVM:

- Heap usage
- Garbage Collection
- Thread count

Avoid excessive heap sizes.

Kafka benefits from operating system page cache.

---

# Broker Placement

Distribute brokers across:

- Availability Zones
- Racks
- Physical hosts

Avoid placing every broker on the same machine.

---

# Rack Awareness

Configure rack awareness.

```text
Rack A

↓

Broker 1

----------------

Rack B

↓

Broker 2

----------------

Rack C

↓

Broker 3
```

This improves resilience during infrastructure failures.

---

# Consumer Design

Consumers should:

- Handle retries
- Commit offsets correctly
- Be idempotent
- Handle duplicate events
- Recover gracefully

Avoid committing offsets before processing completes.

---

# Producer Design

Producers should:

- Retry transient failures
- Enable idempotence
- Use batching
- Enable compression
- Handle delivery failures

---

# Schema Management

Use a schema management strategy.

Recommended:

```text
Schema Registry
```

Benefits:

- Compatibility checks
- Versioning
- Safe schema evolution

---

# Backup Strategy

Plan for recovery.

Include:

- Topic backup
- Metadata backup
- Configuration backup
- Cross-region replication

Recovery procedures should be documented and tested.

---

# Disaster Recovery

Prepare for:

- Broker failures
- Disk failures
- Region failures
- Cluster corruption

Recovery plans should be validated periodically.

---

# Upgrade Planning

Before upgrading:

- Test in staging
- Verify client compatibility
- Plan rollback
- Perform rolling upgrades
- Monitor after upgrade

Never upgrade production blindly.

---

# Infrastructure as Code

Manage Kafka infrastructure using automation.

Examples:

- Terraform
- Ansible
- Helm
- Kubernetes Operators

Avoid manual configuration drift.

---

# Documentation

Maintain documentation for:

- Topics
- Brokers
- Security
- ACLs
- Monitoring
- Recovery procedures
- Upgrade procedures

Good documentation reduces operational risk.

---

# Production Checklist

Before deployment, verify:

| Item | Status |
|------|--------|
| Minimum 3 Brokers | ✅ |
| Replication Factor ≥ 3 | ✅ |
| `acks=all` | ✅ |
| `min.insync.replicas` configured | ✅ |
| Idempotent Producer enabled | ✅ |
| SSL/TLS enabled | ✅ |
| SASL enabled | ✅ |
| ACLs configured | ✅ |
| Monitoring configured | ✅ |
| Alerts configured | ✅ |
| Backups configured | ✅ |
| Disaster Recovery plan | ✅ |
| Capacity planning completed | ✅ |
| Topic retention reviewed | ✅ |
| Compression enabled | ✅ |
| Documentation complete | ✅ |

---

# Common Production Mistakes

- Deploying a single broker.
- Using Replication Factor = 1.
- Running Kafka without SSL.
- Using PLAINTEXT authentication.
- Granting excessive ACL permissions.
- Ignoring consumer lag.
- Filling disks to 100%.
- Creating too many partitions.
- Forgetting backups.
- Upgrading without testing.
- Ignoring monitoring and alerting.

---

# Best Practices

- Always deploy at least three brokers.
- Use Replication Factor = 3 for critical topics.
- Enable `acks=all` and idempotent producers.
- Encrypt all network traffic.
- Authenticate every client.
- Apply the Principle of Least Privilege.
- Monitor Kafka continuously.
- Plan capacity well in advance.
- Test disaster recovery procedures regularly.
- Automate infrastructure provisioning and configuration.

---

# Summary

Running Kafka in production requires careful planning across architecture, security, scalability, monitoring, and operations. A production-ready Kafka cluster should be highly available, fault tolerant, secure, observable, and recoverable. By following a structured production checklist—including replication, acknowledgements, security, monitoring, backups, capacity planning, and disaster recovery—organizations can build reliable event streaming platforms capable of supporting mission-critical workloads.

---

# Key Takeaways

- Production Kafka requires more than simply running brokers.
- Use at least three brokers with a Replication Factor of three.
- Configure `acks=all`, `min.insync.replicas`, and idempotent producers for durability.
- Secure the cluster using SSL/TLS, SASL, and ACLs.
- Monitor broker health, consumer lag, and infrastructure continuously.
- Plan storage, throughput, and future growth before deployment.
- Test backup and disaster recovery procedures regularly.
- A comprehensive production checklist significantly reduces operational risk and improves cluster reliability.