# README

## Overview

The MongoDB Operations section covers the operational practices required to run MongoDB reliably in development, staging, and production environments.

The focus is on operating MongoDB as a production backend dependency rather than simply executing database commands.

Key operational areas include:

- Index management
- Query performance analysis
- Monitoring and observability
- Logging
- Replica-set operations
- Backup and restore
- Data lifecycle management
- Capacity planning
- Service limits and quotas
- Production best practices

The operational workflow should connect database behavior to application behavior:

```text
Application Workload
        ↓
MongoDB Queries / Writes
        ↓
Indexes / Query Planner
        ↓
CPU / Memory / Storage / Network
        ↓
Replication / High Availability
        ↓
Monitoring / Alerting
        ↓
Capacity / Reliability / Recovery
```

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Database Inspection and Statistics](./01-%20Database%20Inspection%20and%20Statistics.md) | Database inspection, collection statistics, server status, index usage, and operational metrics |
| 02 | [02- Index Management](./02-%20Index%20Management.md) | Creating, reviewing, modifying, monitoring, and safely operating MongoDB indexes |
| 03 | [03- Query Performance Analysis](./03-%20Query%20Performance%20Analysis.md) | Diagnosing slow queries, analyzing execution plans, and identifying query bottlenecks |
| 04 | [04- Monitoring and Observability](./04-%20Monitoring%20and%20Observability.md) | MongoDB metrics, health monitoring, replication, storage, query performance, and observability |
| 05 | [05- Logging](./05-%20Logging.md) | MongoDB server logs, application logging, structured logging, retention, and operational troubleshooting |
| 06 | [06- Replica Set Operations](./06-%20Replica%20Set%20Operations.md) | Replica-set health, elections, failover, replication lag, member management, and recovery operations |
| 07 | [07- Backup and Restore Operations](./07-%20Backup%20and%20Restore%20Operations.md) | Backup strategies, mongodump, mongorestore, restore validation, RPO, RTO, and disaster recovery |
| 08 | [08- Data Lifecycle Management](./08-%20Data%20Lifecycle%20Management.md) | TTL, archival, retention, deletion, lifecycle workers, and long-term data management |
| 09 | [09- Capacity Planning](./09-%20Capacity%20Planning.md) | CPU, memory, storage, working set, connections, replication, growth forecasting, and scaling decisions |
| 10 | [10- Service Limits and Quotas](./10-%20Service%20Limits%20and%20Quotas.md) | MongoDB limits, connection constraints, BSON limits, provider quotas, and operational headroom |
| 11 | [11- Production Best Practices](./11-%20Production%20Best%20Practices.md) | Production architecture, security, reliability, deployment, monitoring, backups, and operational discipline |

## Operations Learning Path

A practical progression through the operations section is:

```text
Index Management
      ↓
Query Performance Analysis
      ↓
Monitoring and Observability
      ↓
Logging
      ↓
Replica Set Operations
      ↓
Backup and Restore
      ↓
Data Lifecycle Management
      ↓
Capacity Planning
      ↓
Service Limits and Quotas
      ↓
Production Best Practices
```

The sequence moves from database-level operational mechanics toward production architecture and reliability.

## Operational Areas

### Performance

Performance operations focus on understanding why MongoDB queries and writes consume resources.

Core areas include:

- Index design and lifecycle
- Query execution plans
- `COLLSCAN`
- `IXSCAN`
- `FETCH`
- Query selectivity
- Compound indexes
- ESR guideline
- Aggregation performance
- Working-set behavior
- Connection pool pressure
- Read and write performance

A typical performance workflow is:

```text
Slow request
    ↓
Measure API latency
    ↓
Measure MongoDB latency
    ↓
Identify query shape
    ↓
Run explain()
    ↓
Inspect indexes
    ↓
Check CPU / memory / I/O
    ↓
Optimize
    ↓
Validate with representative workload
```

### Reliability

MongoDB reliability depends on:

- Replica sets
- Majority behavior
- Elections
- Failover
- Replication health
- Oplog capacity
- Backup and restore
- Disaster recovery
- Capacity headroom

Production reliability should be validated through failure testing rather than assumed from topology alone.

### Observability

Monitoring should connect MongoDB behavior with application behavior.

Important signals include:

| Category | Examples |
|---|---|
| Application | Request rate, latency, errors |
| Query | Execution time, query shape, scanned documents |
| Database | Operations/sec, connections, cursors |
| Compute | CPU, memory |
| Storage | Disk usage, IOPS, latency |
| Replication | Lag, elections, oplog window |
| Indexes | Size, usage, growth |
| Capacity | Growth rate, remaining headroom |

## Backup and Recovery

Replication is not a replacement for backups.

A production recovery strategy should define:

```text
Backup
  ↓
Retention
  ↓
Restore
  ↓
Validation
  ↓
RPO / RTO measurement
  ↓
Disaster recovery testing
```

Restore testing should be treated as an operational requirement.

## Capacity and Limits

Capacity planning should consider:

- Data growth
- Index growth
- Working set
- CPU
- Memory
- Storage
- Storage latency
- Network
- Connections
- Replication
- Application concurrency
- Background workloads
- Failure-state capacity

Service limits and quotas should be tracked separately from practical performance capacity.

```text
Hard technical limit
        +
Provider quota
        +
Infrastructure limit
        +
Performance capacity
        ↓
Production operating boundary
```

## Production Operating Principles

### Design for Failure

Assume that:

- A primary can fail.
- A secondary can fall behind.
- Storage can become constrained.
- Queries can regress.
- Deployments can introduce unexpected load.
- Applications can generate duplicate operations.
- Backups can fail.
- Network connectivity can degrade.

Production architecture should define detection, recovery, and prevention for these scenarios.

### Automate Repeatable Operations

Prefer:

```text
Version control
+
Infrastructure as Code
+
CI/CD
+
Automated migrations
+
Automated backups
+
Automated monitoring
```

over undocumented manual database changes.

Manual `mongosh` or Compass operations can be appropriate for controlled incident response, but persistent configuration should have a reproducible source of truth.

### Measure Before Scaling

When MongoDB becomes slow:

```text
Measure
↓
Identify bottleneck
↓
Optimize workload
↓
Validate
↓
Scale if necessary
```

Do not automatically add CPU, RAM, indexes, or connections without identifying the limiting resource.

## Security Operations

Production MongoDB environments should enforce:

- Authentication
- Least-privilege authorization
- TLS
- Network isolation
- Secret management
- Credential rotation
- Encryption at rest where required
- Security monitoring
- Auditing where required

Application services should use dedicated database identities rather than administrative accounts.

## Data Lifecycle Operations

Long-lived MongoDB deployments require explicit lifecycle policies.

Typical flow:

```text
Active Data
    ↓
Retention Policy
    ↓
TTL / Archive
    ↓
Cold Storage or Deletion
```

Lifecycle design should consider:

- Data retention
- TTL indexes
- Archival
- Legal or compliance holds
- Large collection growth
- Storage cost
- Query performance
- Backup impact

## Production Change Workflow

Database changes should follow a controlled process:

```text
Design
  ↓
Review
  ↓
Test
  ↓
Assess capacity / failure impact
  ↓
Deploy
  ↓
Monitor
  ↓
Validate
  ↓
Document
```

High-risk changes include:

- Large index builds
- Schema migrations
- Bulk updates
- Large deletions
- Replica-set topology changes
- Sharding changes
- Retention-policy changes
- Major version upgrades

## Troubleshooting Methodology

Use a consistent diagnostic workflow:

```text
Symptom
↓
Possible causes
↓
Isolation strategy
↓
Diagnostic commands / metrics
↓
Root cause
↓
Corrective action
↓
Prevention
```

Avoid making multiple changes simultaneously during an incident unless required for immediate safety. Isolating one variable at a time makes root-cause analysis more reliable.

## Production Checklist

### Performance

- [ ] Important queries have appropriate indexes.
- [ ] Query plans are periodically reviewed.
- [ ] Slow queries are observable.
- [ ] Pagination is bounded.
- [ ] Large aggregations are controlled.
- [ ] Connection pools are appropriately sized.

### Reliability

- [ ] Replica-set health is monitored.
- [ ] Replication lag is monitored.
- [ ] Oplog window is monitored.
- [ ] Failover has been tested.
- [ ] N-1 capacity is understood.
- [ ] Recovery procedures are documented.

### Security

- [ ] Authentication is enabled.
- [ ] Application users follow least privilege.
- [ ] TLS is configured appropriately.
- [ ] Database access is network-restricted.
- [ ] Secrets are not stored in source control.
- [ ] Sensitive information is excluded from logs.

### Backup

- [ ] Backups are automated.
- [ ] Retention is documented.
- [ ] Restore procedures are documented.
- [ ] Restore tests are performed.
- [ ] RPO is defined and measured.
- [ ] RTO is defined and measured.

### Capacity

- [ ] Data growth is tracked.
- [ ] Index growth is tracked.
- [ ] Storage capacity is forecast.
- [ ] Connection capacity is understood.
- [ ] Application scaling impact is understood.
- [ ] Failure-state capacity has been evaluated.

### Operations

- [ ] Monitoring dashboards exist.
- [ ] Alerts are actionable.
- [ ] Logs are centralized.
- [ ] Runbooks exist for major failure scenarios.
- [ ] Production changes are controlled.
- [ ] Operational knowledge is documented.

## Senior-Level Focus

The most important shift from intermediate to senior MongoDB operations is moving from command execution to system reasoning.

An intermediate engineer may ask:

```text
"What MongoDB command fixes this?"
```

A senior engineer should ask:

```text
"What system condition caused this?"

"Which resource is constrained?"

"Is the problem application, query, database, infrastructure, or architecture?"

"What is the failure mode if we apply this fix?"

"How will we validate the fix?"

"How do we prevent recurrence?"
```

The operational goal is not merely to keep MongoDB running. It is to build a database platform that behaves predictably under normal load, peak load, failures, deployments, growth, and recovery scenarios.

## Key Takeaways

- **MongoDB operations should connect database behavior to application performance, infrastructure capacity, reliability, and recovery requirements.**
- **Performance work should follow a measure → diagnose → optimize → validate workflow rather than relying on indiscriminate scaling.**
- **Production reliability depends on replica-set health, tested backups, recovery procedures, monitoring, capacity headroom, and controlled changes.**
- **Security, lifecycle management, service limits, and operational runbooks are part of database engineering, not separate concerns.**
- **Senior MongoDB operations focus on understanding system behavior and failure modes rather than memorizing administrative commands.**