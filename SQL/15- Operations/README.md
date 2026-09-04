# README

## Overview

The **Operations** section covers the practices required to run SQL databases reliably in production.

SQL knowledge alone is not sufficient for production backend engineering. A database must also be maintained, monitored, backed up, recovered, scaled, secured, and operated safely under normal and failure conditions.

This section focuses primarily on **PostgreSQL-oriented production operations**, while the principles apply broadly to relational databases.

The operational lifecycle can be viewed as:

```text
                    ┌──────────────────────┐
                    │      Application     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Production SQL DB  │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
     Maintenance          Observability        Backups
          │                    │                    │
          ▼                    ▼                    ▼
     VACUUM/ANALYZE       Metrics/Logs         WAL/PITR
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                               ▼
                       Recovery / Failover
                               │
                               ▼
                         Capacity Planning
```

The goal is not to memorize operational commands. The goal is to understand **what can fail, how to detect it, how to mitigate it, and how to prevent recurrence**.

## Navigation

- [01- SQL Production Operations](./01-%20SQL%20Production%20Operations.md) — Overview of production SQL operational practice and responsibilities
- [02- Database Monitoring](./02-%20Database%20Monitoring.md) — Database health, query, and resource monitoring
- [03- Query Performance Monitoring](./03-%20Query%20Performance%20Monitoring.md) — Identifying and tracking slow or expensive queries
- [04- Slow Query Monitoring](./04-%20Slow%20Query%20Monitoring.md) — Detecting and alerting on slow query patterns
- [05- Database CPU Monitoring](./05-%20Database%20CPU%20Monitoring.md) — CPU saturation detection and analysis
- [06- Database Memory Monitoring](./06-%20Database%20Memory%20Monitoring.md) — Memory pressure detection and analysis
- [07- Connection Monitoring](./07-%20Connection%20Monitoring.md) — Connection pool and database connection monitoring
- [08- Lock and Deadlock Monitoring](./08-%20Lock%20and%20Deadlock%20Monitoring.md) — Detecting lock contention and deadlocks in production
- [09- Index Monitoring](./09-%20Index%20Monitoring.md) — Index usage, bloat, and effectiveness monitoring
- [10- Table Growth Monitoring](./10-%20Table%20Growth%20Monitoring.md) — Tracking table size, growth rate, and storage trends
- [11- Storage Monitoring](./11-%20Storage%20Monitoring.md) — Disk space, WAL, and storage capacity monitoring
- [12- Database Statistics](./12-%20Database%20Statistics.md) — PostgreSQL statistics views and planner accuracy
- [13- Index Maintenance](./13-%20Index%20Maintenance.md) — Index lifecycle, usage, bloat, and production maintenance
- [14- Table Maintenance](./14-%20Table%20Maintenance.md) — Table health, dead tuples, bloat, and maintenance operations
- [15- VACUUM and ANALYZE](./15-%20VACUUM%20and%20ANALYZE.md) — MVCC cleanup, statistics maintenance, and autovacuum
- [16- Database Backups](./16-%20Database%20Backups.md) — Backup strategies, retention, encryption, and verification
- [17- Restore and Recovery](./17-%20Restore%20and%20Recovery.md) — Database restoration procedures and recovery validation
- [18- Point in Time Recovery](./18-%20Point%20in%20Time%20Recovery.md) — WAL archiving, recovery targets, and PITR
- [19- Database Capacity Planning](./19-%20Database%20Capacity%20Planning.md) — Resource forecasting, workload growth, and scaling decisions
- [20- Connection Pooling](./20-%20Connection%20Pooling.md) — Pool architecture, connection budgets, exhaustion, and application integration
- [21- Read Replicas](./21-%20Read%20Replicas.md) — Replica architecture, lag, read routing, consistency, and failure handling
- [22- Database Failover](./22-%20Database%20Failover.md) — Promotion, fencing, connection recovery, and HA operations
- [23- Production SQL Best Practices](./23-%20Production%20SQL%20Best%20Practices.md) — Production SQL design, performance, safety, and operational practices
- [24- Database Reliability Practices](./24-%20Database%20Reliability%20Practices.md) — Reliability engineering principles for SQL systems
- [25- Operational Checklists](./25-%20Operational%20Checklists.md) — Repeatable operational procedures and verification checklists

---

## Operations at a Glance

| Area | Primary concern | Typical signals |
|---|---|---|
| Index maintenance | Index performance and cost | Index size, usage, bloat, query plans |
| Table maintenance | Dead tuples and physical health | Dead tuples, table growth, vacuum activity |
| VACUUM / ANALYZE | MVCC cleanup and statistics | Autovacuum activity, transaction age |
| Backups | Data protection | Backup age, success/failure |
| Restore | Recoverability | Restore duration, validation |
| PITR | Recovery to a precise point | WAL availability, recovery target |
| Capacity planning | Future resource requirements | CPU, memory, storage, connections |
| Connection pooling | Connection concurrency | Pool utilization, acquisition latency |
| Read replicas | Read scalability and HA | Replica lag, replay state |
| Failover | Service continuity | Primary health, promotion state |
| Reliability | Predictable operation | SLOs, incidents, recovery time |
| Checklists | Repeatable operations | Verification and ownership |

---

## Recommended Learning Path

The operations material is most effective when studied after understanding database internals, transactions, indexing, replication, and scaling.

```text
Database Architecture
        │
        ▼
Query Processing
        │
        ▼
Transactions & Concurrency
        │
        ▼
Indexes & Partitioning
        │
        ▼
Replication & Scaling
        │
        ▼
Operations
        │
        ├── Maintenance
        ├── Backups
        ├── Recovery
        ├── Capacity
        ├── Failover
        └── Reliability
```

Recommended sequence:

1. Index Maintenance
2. Table Maintenance
3. VACUUM and ANALYZE
4. Database Backups
5. Restore and Recovery
6. Point in Time Recovery
7. Database Capacity Planning
8. Connection Pooling
9. Read Replicas
10. Database Failover
11. Production SQL Best Practices
12. Database Reliability Practices
13. Operational Checklists

---

## Document Index

| File | Focus |
|---|---|
| `01- Index Maintenance.md` | Index lifecycle, usage, bloat, creation, removal, and production maintenance |
| `02- Table Maintenance.md` | Table health, dead tuples, bloat, maintenance operations, and lifecycle |
| `03- VACUUM and ANALYZE.md` | MVCC cleanup, statistics maintenance, autovacuum, and transaction ID management |
| `04- Database Backups.md` | Backup strategies, retention, encryption, verification, and operational design |
| `05- Restore and Recovery.md` | Database restoration procedures and recovery validation |
| `06- Point in Time Recovery.md` | WAL archiving, recovery targets, PITR, and recovery testing |
| `07- Database Capacity Planning.md` | Resource forecasting, workload growth, headroom, and scaling decisions |
| `08- Connection Pooling.md` | Pool architecture, connection budgets, exhaustion, and application integration |
| `09- Read Replicas.md` | Replica architecture, lag, read routing, consistency, and failure handling |
| `10- Database Failover.md` | Promotion, fencing, connection recovery, failover validation, and HA operations |
| `11- Production SQL Best Practices.md` | Production SQL design, performance, safety, and operational practices |
| `12- Database Reliability Practices.md` | Reliability engineering principles for SQL systems |
| `13- Operational Checklists.md` | Repeatable operational procedures and verification checklists |
| `14- Production Monitoring.md` | Database health, query, resource, and reliability monitoring |
| `15- Incident Response.md` | Database incident diagnosis, mitigation, and recovery |
| `16- Database Performance Operations.md` | Production performance management and optimization |
| `17- Database Maintenance Windows.md` | Planning and executing maintenance safely |
| `18- Database Health Checks.md` | Routine database health validation |
| `19- Database Change Management.md` | Controlled database schema and configuration changes |
| `20- Database Upgrade Operations.md` | PostgreSQL/database version upgrade planning and execution |
| `21- Database Migration Operations.md` | Safe production migrations and large data changes |
| `22- Database Disaster Recovery.md` | Disaster recovery architecture and operational readiness |
| `23- Database Security Operations.md` | Operational database security and access management |
| `24- Database Operational Runbooks.md` | Production runbook design and execution |
| `25- Operational Checklists.md` | Consolidated operational checklists |

> The exact document set should remain synchronized with the actual files in this folder. The index should be updated whenever files are added, renamed, or removed.

---

## Maintenance Operations

Database maintenance exists because a transactional database continuously changes its physical and logical state.

For PostgreSQL, important maintenance activities include:

- VACUUM
- ANALYZE
- Autovacuum
- Index maintenance
- Table maintenance
- Partition lifecycle management
- Statistics maintenance
- Transaction ID monitoring
- Storage cleanup

Maintenance should normally be **continuous and automated**, rather than treated as an emergency activity.

### Maintenance relationship

```text
Application writes
       │
       ▼
MVCC creates new row versions
       │
       ├──────────────► Statistics become stale
       │
       └──────────────► Dead tuples accumulate
                              │
                              ▼
                    VACUUM / ANALYZE
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              Space cleanup       Better estimates
                    │                   │
                    ▼                   ▼
              Table health        Better plans
```

---

## Index Operations

Indexes improve query access paths but introduce storage, write, maintenance, and replication costs.

Production index management should therefore answer:

- Is the index required?
- Which query pattern does it support?
- Is it actually being used?
- Is it redundant?
- How large is it?
- How much write amplification does it introduce?
- Can it be created or removed safely?
- Does it support a constraint?
- Does it remain appropriate as data distribution changes?

### Index lifecycle

```text
Query requirement
       ↓
Existing index review
       ↓
Execution plan analysis
       ↓
Index design
       ↓
Production creation
       ↓
Usage monitoring
       ↓
Periodic review
       ↓
Retain / modify / remove
```

Never equate a sequential scan with a missing index. A sequential scan can be the optimal plan for a sufficiently large result set.

---

## Table Operations

Tables require maintenance because physical storage and logical workload change over time.

Important operational concerns include:

- Table size
- Dead tuples
- Table bloat
- Autovacuum behavior
- Long-running transactions
- Transaction ID age
- Index growth
- Partition growth
- Retention
- Archival
- Large deletes
- Large updates

Large tables should be treated as operational assets with explicit ownership and lifecycle policies.

---

## VACUUM and ANALYZE

`VACUUM` and `ANALYZE` solve different problems.

| Operation | Primary purpose |
|---|---|
| `VACUUM` | Reclaim/reuse space from dead tuples and support MVCC cleanup |
| `ANALYZE` | Update planner statistics |
| `AUTOVACUUM` | Automatically perform vacuum/analyze based on workload |
| `VACUUM FULL` | Rewrite a table to compact it aggressively |
| `VACUUM (ANALYZE)` | Perform vacuum and update statistics |

`VACUUM FULL` is significantly more disruptive than normal vacuum because it rewrites the table and requires stronger locking.

Production systems should generally rely on well-configured autovacuum and use manual maintenance deliberately.

---

## Backup Operations

Backups provide a recovery mechanism independent of the primary database.

A production backup strategy should define:

- Recovery Point Objective (RPO)
- Recovery Time Objective (RTO)
- Backup frequency
- Retention
- Storage location
- Encryption
- Access control
- Cross-region strategy
- Backup verification
- Restore testing

A replica is not a replacement for a backup.

```text
Primary
  │
  ├──► Read Replica ──► Read scaling / HA
  │
  └──► Backup / WAL ──► Recovery
```

A replica can replicate corruption or accidental deletion. Independent backups provide a separate recovery boundary.

---

## Restore and Recovery

Recovery is the process of turning stored recovery artifacts into a usable database.

A reliable recovery process includes:

```text
Backup / WAL
     ↓
Recovery environment
     ↓
Restore
     ↓
Recovery target
     ↓
Database validation
     ↓
Application validation
     ↓
Traffic restoration
```

Recovery should be tested against realistic database sizes.

The important metric is not:

```text
"Backup completed successfully"
```

but:

```text
"Database can be restored within the required RTO
and to the required recovery point."
```

---

## Point-in-Time Recovery

PITR uses a base backup plus WAL to reconstruct database state at a selected point in time.

Conceptually:

```text
Base Backup
    │
    ├── WAL 001
    ├── WAL 002
    ├── WAL 003
    ├── WAL 004
    ├── WAL 005
    │
    ▼
Recovery Target
    │
    ▼
Restored Database
```

PITR is particularly useful for:

- Accidental deletion
- Incorrect migrations
- Application bugs
- Corrupt logical changes
- Recovery to a point immediately before an incident

PITR depends on reliable WAL archiving. A base backup without the required WAL history cannot provide arbitrary point-in-time recovery.

---

## Capacity Planning

Database capacity planning should consider more than CPU.

```text
                 Database Capacity
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
      CPU            Memory          Storage
       │               │                │
       └───────────────┼────────────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
         Connections         I/O
              │                 │
              └────────┬────────┘
                       ▼
                   Workload
```

Important dimensions include:

| Dimension | Questions |
|---|---|
| CPU | Are queries consuming increasing CPU? |
| Memory | Is available memory declining? |
| Storage | How quickly is data growing? |
| I/O | Is storage latency increasing? |
| Connections | Is concurrency approaching safe limits? |
| WAL | Is write volume increasing? |
| Replicas | Can replicas handle read traffic? |
| Maintenance | Can autovacuum keep up? |
| Queries | Is query volume growing? |

Capacity planning should include failure scenarios.

For example:

```text
Normal:
Primary + 2 replicas

Failure:
Primary fails
      ↓
One replica promoted
      ↓
Remaining replica + new workloads
must still fit safely
```

Designing only for normal operation creates fragile HA systems.

---

## Connection Pooling

Connection pooling controls application-to-database concurrency.

A useful mental model is:

```text
Kubernetes Pods
      │
      ├── Pod A ──► Pool ──┐
      ├── Pod B ──► Pool ──┤
      ├── Pod C ──► Pool ──┼──► PostgreSQL
      └── Workers ─► Pool ─┘
```

The database sees the **aggregate** number of possible connections.

For example:

```text
10 pods × 10 connections = 100 possible connections

+
5 worker processes × 5 connections = 25

Total = 125 possible connections
```

This calculation must also consider deployment overlap, administrative connections, replicas, and other clients.

Connection pools are concurrency controls. They do not create additional database capacity.

---

## Read Replica Operations

Read replicas can increase read capacity and improve availability, but asynchronous replication introduces lag.

```text
                ┌───────────────┐
                │    Primary    │
                └───────┬───────┘
                        │ WAL
              ┌─────────┴─────────┐
              ▼                   ▼
       ┌──────────────┐    ┌──────────────┐
       │   Replica 1  │    │   Replica 2  │
       └──────────────┘    └──────────────┘
```

Applications should distinguish between:

- Reads that tolerate stale data
- Reads that require current state
- Reads immediately following a write
- Reporting workloads
- Critical transactional reads

A common production strategy is:

```text
Write
  ↓
Primary

Read
  ↓
Consistency-sensitive? ── Yes ──► Primary
  │
  No
  ↓
Healthy replica
```

Replica lag must be monitored rather than assumed to be negligible.

---

## Database Failover

Failover changes which database instance serves as the authoritative writer.

A safe failover sequence is approximately:

```text
Primary failure
      ↓
Detect failure
      ↓
Prevent split brain
      ↓
Select candidate
      ↓
Promote standby
      ↓
Update writer endpoint
      ↓
Reconnect clients
      ↓
Validate writes
      ↓
Rebuild replica topology
```

Failover introduces important application concerns:

- Existing connections may fail.
- Transactions may be interrupted.
- A commit may become uncertain to the client.
- Connection pools may reconnect simultaneously.
- Retries can create load spikes.
- Read routing may temporarily point to stale replicas.

Applications should therefore use:

- Stable database endpoints
- Bounded connection timeouts
- Bounded retries
- Exponential backoff
- Jitter
- Idempotent operations
- Explicit transaction boundaries

---

## Production SQL Practices

Production SQL should be designed with operational behavior in mind.

Important practices include:

### Parameterization

Use bound parameters rather than string interpolation.

```python
cursor.execute(
    """
    SELECT id, email
    FROM customers
    WHERE id = %s
    """,
    (customer_id,),
)
```

This protects against SQL injection and allows the driver/database to treat values as data rather than SQL syntax.

### Explicit Transactions

Keep transaction boundaries intentional and short.

Avoid holding a database transaction while performing slow external calls unless there is a specific correctness requirement.

### Atomic Operations

Prefer database-side atomic updates for shared state:

```sql
UPDATE inventory
SET available = available - 1
WHERE product_id = $1
  AND available > 0;
```

The application can inspect the affected row count rather than implementing an unsafe read-modify-write sequence.

### Bounded Results

Avoid unnecessarily returning large datasets.

Use:

- Appropriate projections
- Pagination
- Keyset pagination for large ordered datasets
- Batch processing
- Asynchronous exports

---

## Reliability Practices

Database reliability is a system property rather than a single PostgreSQL feature.

A reliable system combines:

```text
Correct SQL
    +
Safe transactions
    +
Controlled concurrency
    +
Maintenance
    +
Monitoring
    +
Backups
    +
Replication
    +
Failover
    +
Capacity planning
    +
Tested recovery
```

### Reliability dimensions

| Dimension | Example |
|---|---|
| Prevention | Constraints, safe migrations, least privilege |
| Detection | Metrics, logs, alerts |
| Mitigation | Rate limiting, failover, throttling |
| Recovery | Restore, PITR, promotion |
| Learning | Incident reviews and runbook updates |

---

## Monitoring Model

Production database monitoring should be layered.

```text
                    Database Monitoring
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
     Resources          Workload          Reliability
        │                  │                  │
   CPU / Memory       Query latency       Replication
   Disk / I/O         Query volume        Backups
   Connections        Query errors        Failover
   WAL                Locks               Recovery
```

### Resource metrics

Monitor:

- CPU
- Memory
- Disk utilization
- I/O latency
- I/O throughput
- Connections
- WAL generation
- Temporary files

### Query metrics

Monitor:

- Query latency
- Query volume
- Total execution time
- Error rate
- Slow queries
- Plan changes
- Rows processed

### Concurrency metrics

Monitor:

- Lock waits
- Deadlocks
- Long transactions
- Idle-in-transaction sessions
- Connection pool exhaustion

### Maintenance metrics

Monitor:

- Autovacuum activity
- Dead tuples
- Analyze freshness
- Transaction ID age
- Table growth
- Index growth

---

## Incident Diagnosis

When a database incident occurs, avoid immediately changing configuration.

Use a structured investigation:

```text
Is the database available?
        ↓
Is it saturated?
        ↓
Is the workload abnormal?
        ↓
Are queries slow?
        ↓
Are queries waiting?
        ↓
Are connections exhausted?
        ↓
Is replication affected?
        ↓
Is storage affected?
        ↓
Is maintenance falling behind?
```

Useful PostgreSQL sources include:

- `pg_stat_activity`
- `pg_stat_statements`
- `pg_locks`
- `pg_blocking_pids()`
- `pg_stat_replication`
- `pg_stat_user_tables`
- `pg_stat_user_indexes`

The application should also provide request IDs or job IDs that allow database activity to be correlated with API requests and background jobs.

---

## Maintenance Windows

Not every database operation requires a maintenance window, but operational risk should be evaluated.

Examples:

| Operation | Typical concern |
|---|---|
| Normal `VACUUM` | Resource consumption |
| `ANALYZE` | Resource consumption |
| `CREATE INDEX CONCURRENTLY` | Runtime and resource consumption |
| `VACUUM FULL` | Strong locking and table rewrite |
| Large backfill | CPU, I/O, WAL, locks |
| Major upgrade | Downtime or cutover complexity |
| Large schema change | Lock duration |
| Restore | Application unavailability |

The preferred approach is to make operations as incremental and online as practical.

---

## Database Change Management

Production database changes should be treated as software changes.

Every significant change should define:

- Owner
- Scope
- Risk
- Dependencies
- Rollout strategy
- Validation strategy
- Rollback or forward-recovery strategy
- Monitoring
- Abort conditions

For schema evolution, expand-and-contract is a strong default:

```text
Add compatible schema
        ↓
Deploy compatible application
        ↓
Backfill gradually
        ↓
Validate
        ↓
Switch application behavior
        ↓
Remove obsolete schema later
```

This allows old and new application versions to coexist during rolling deployments.

---

## Large Data Operations

Large updates and deletes can become operational incidents.

Potential effects include:

- Long transactions
- Lock contention
- High WAL generation
- Replica lag
- Table bloat
- Autovacuum pressure
- Increased I/O
- Connection pool delays

Prefer controlled batching.

Conceptually:

```text
10 million rows
      │
      ├── Batch 1
      ├── Batch 2
      ├── Batch 3
      ├── ...
      └── Batch N
```

Batch size should be selected based on workload behavior rather than a universal number.

---

## Background Workers

Celery, Kafka consumers, scheduled jobs, ETL processes, and administrative scripts are database clients too.

Operational capacity must include them:

```text
Web traffic
     │
     ├───────────────┐
     ▼               ▼
 Django/FastAPI   Workers
     │               │
     └───────┬───────┘
             ▼
        Connection Pool
             │
             ▼
         PostgreSQL
```

A background job that runs correctly in isolation can still damage production by:

- Consuming all connections
- Generating excessive writes
- Holding long transactions
- Creating lock contention
- Causing replica lag
- Amplifying retries

Background workloads should have explicit concurrency and retry limits.

---

## AWS Operational Mapping

In AWS environments, SQL operations commonly interact with:

- Amazon RDS
- Amazon Aurora
- Amazon CloudWatch
- AWS Backup
- Amazon S3
- AWS KMS
- IAM
- VPC networking
- Multi-AZ deployment
- Read replicas

The exact service architecture varies, but the operational principles remain:

```text
Application
    │
    ▼
Private Network
    │
    ▼
Managed Database
    │
    ├──► Monitoring
    ├──► Backups
    ├──► Replicas
    └──► Recovery
```

Managed database services remove infrastructure administration but do not eliminate the need for query optimization, capacity planning, transaction design, security, or recovery testing.

---

## Kubernetes Considerations

Kubernetes introduces additional operational variables:

- Pod scaling
- Rolling deployments
- Connection pool multiplication
- Worker scaling
- Readiness and liveness behavior
- Secret distribution
- Network policies
- Deployment overlap

A deployment that increases application replicas from 10 to 30 can also increase possible database connections by 3×.

Therefore:

```text
Application autoscaling
        ↓
Database connection demand
        ↓
Database concurrency
        ↓
CPU / memory / lock pressure
```

Autoscaling the application without considering database capacity can make an incident worse.

---

## Security Operations

Operational security should cover:

### Database access

- Least-privilege roles
- Separate runtime and migration roles
- Restricted administrative access
- Controlled break-glass access
- Regular role review

### Credentials

- Secure secret storage
- Credential rotation
- No credentials in source control
- No secrets in logs
- Restricted production access

### Data protection

- Encryption at rest
- TLS in transit
- Restricted backups
- Controlled restore environments
- Sensitive-data handling

### Auditing

Track important events such as:

- Privilege changes
- DDL changes
- Administrative actions
- Sensitive data access
- Authentication events
- Backup/recovery operations

---

## High Availability and Disaster Recovery

HA and DR solve different problems.

| Concern | HA | DR |
|---|---|---|
| Primary failure | Yes | Yes |
| Fast failover | Yes | Sometimes |
| Regional disaster | Usually limited | Yes |
| Accidental deletion | Not sufficient | Yes |
| Corrupted logical change | Not sufficient | Yes |
| PITR | Not inherently | Yes |
| Recovery environment | Usually unnecessary | Required |

A mature production architecture normally combines:

```text
                 Production
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
       Primary              Replicas
          │
          ▼
      WAL / Backup
          │
          ▼
   Recovery Environment
```

---

## Recovery Testing

Recovery procedures should be tested, not merely documented.

A recovery exercise should measure:

- Time to obtain recovery artifacts
- Restore duration
- WAL replay duration
- Validation duration
- Application startup time
- DNS/endpoint cutover time
- Data validation time
- Total RTO

Compare measured recovery against the required RTO.

```text
Required RTO: 60 minutes
Actual recovery: 95 minutes

Result:
Recovery architecture does not currently meet the requirement.
```

This is a capacity and architecture problem, not merely a documentation problem.

---

## Cost Considerations

Operational decisions have direct cost implications.

Examples:

| Decision | Potential benefit | Potential cost |
|---|---|---|
| Larger instance | More CPU/memory | Higher infrastructure cost |
| More replicas | Read capacity/HA | Compute and storage cost |
| Larger indexes | Faster reads | Storage/write cost |
| Longer backups | More recovery options | Storage cost |
| Cross-region recovery | Better DR | Replication/storage cost |
| More connection capacity | More concurrency | Memory/resource cost |
| Higher monitoring detail | Better diagnosis | Telemetry/storage cost |

Optimize for **required reliability and workload characteristics**, not maximum infrastructure size.

---

## Operational Best Practices

### Prefer automation

Automate:

- Backups
- Backup verification
- Maintenance
- Monitoring
- Alerting
- Replica health checks
- Capacity reporting
- Recovery tests where possible

### Prefer bounded operations

Use:

- Query timeouts
- Lock timeouts
- Connection acquisition timeouts
- Retry limits
- Batch sizes
- Worker concurrency limits
- Rate limits

### Prefer reversible changes

Use:

- Expand-and-contract migrations
- Gradual rollouts
- Feature flags where appropriate
- Controlled backfills
- Versioned schema changes

### Prefer evidence

Use:

- Execution plans
- Query statistics
- Resource metrics
- Lock diagnostics
- Replication metrics
- Historical trends

Avoid operational decisions based solely on intuition.

---

## Common Operational Mistakes

### Treating Backups as Verified Recovery

A successful backup job does not prove restoration works.

**Better:** perform regular restore tests.

### Using Replicas as Backups

Replicas can replicate unwanted changes.

**Better:** maintain independent backup and WAL recovery paths.

### Increasing Connection Pools During Saturation

More connections can increase CPU, memory, lock contention, and queueing.

**Better:** identify the downstream bottleneck first.

### Running `VACUUM FULL` as Routine Maintenance

`VACUUM FULL` rewrites the table and has significant locking/resource implications.

**Better:** understand why normal vacuum is insufficient before using it.

### Adding Indexes Without Measuring

Indexes improve some queries while increasing write and storage cost.

**Better:** validate with execution plans and workload data.

### Scaling Application Pods Without Database Planning

More application replicas can create more database connections and concurrent queries.

**Better:** include the database in autoscaling capacity calculations.

### Retrying Database Errors Indiscriminately

Retries can amplify an outage.

**Better:** retry only errors that are safe and appropriate to retry, with bounded backoff and jitter.

### Ignoring Long Transactions

Long transactions can affect vacuum cleanup, locks, storage, and recovery behavior.

**Better:** monitor transaction age and investigate unexpected long-lived transactions.

---

## Senior-Level Operational Questions

A senior backend engineer should be able to reason through questions such as:

- How do you know whether a database is actually saturated?
- How do you distinguish CPU pressure from lock contention?
- What happens when a connection pool is exhausted?
- How do application replicas affect database capacity?
- How do you verify that backups are recoverable?
- How do you design PITR?
- What happens to a request during database failover?
- How do you handle an uncertain commit?
- How do you safely execute a large backfill?
- Why might autovacuum fall behind?
- When would you use `CREATE INDEX CONCURRENTLY`?
- Why is `VACUUM FULL` operationally different from normal `VACUUM`?
- How do you diagnose replica lag?
- How do you determine whether an index should be removed?
- How do you design a database for an AZ or regional failure?
- How do you prevent background workers from overwhelming PostgreSQL?
- How do you determine whether the current RTO is achievable?
- How do you prevent retry storms during a database outage?

A strong senior-level answer should connect:

```text
Symptom
  ↓
Evidence
  ↓
Root cause
  ↓
Mitigation
  ↓
Verification
  ↓
Prevention
```

---

## Production Readiness Checklist

Before considering a SQL-backed production system operationally mature:

### Availability

- [ ] Database availability is monitored.
- [ ] HA architecture is defined.
- [ ] Failover behavior is tested.
- [ ] Application reconnect behavior is tested.

### Performance

- [ ] Critical queries have known execution plans.
- [ ] Query latency is monitored.
- [ ] Connection pools are bounded.
- [ ] Indexes are periodically reviewed.
- [ ] Capacity trends are tracked.

### Maintenance

- [ ] Autovacuum is healthy.
- [ ] Analyze statistics are maintained.
- [ ] Dead tuples are monitored.
- [ ] Table growth is tracked.
- [ ] Index growth is tracked.

### Backup and Recovery

- [ ] Backups are automated.
- [ ] Backup retention is defined.
- [ ] WAL archiving is monitored where required.
- [ ] Restore tests are performed.
- [ ] PITR is tested where required.
- [ ] RPO and RTO are documented.

### Security

- [ ] Runtime roles use least privilege.
- [ ] Administrative access is restricted.
- [ ] Credentials are managed securely.
- [ ] TLS is configured appropriately.
- [ ] Sensitive operations are audited.

### Operations

- [ ] Runbooks exist.
- [ ] Operational ownership is clear.
- [ ] Incident response procedures exist.
- [ ] Change management is defined.
- [ ] Recovery procedures are rehearsed.
- [ ] Capacity plans include failure scenarios.

---

## Operational Decision Framework

When facing a production database problem, use this sequence:

```text
1. Is it available?
        │
        ▼
2. Is it saturated?
        │
        ▼
3. What resource is constrained?
        │
        ├── CPU
        ├── Memory
        ├── I/O
        ├── Connections
        └── Locks
        │
        ▼
4. What workload caused the pressure?
        │
        ▼
5. Can workload be reduced safely?
        │
        ▼
6. Can the underlying issue be fixed safely?
        │
        ▼
7. Does the system recover?
        │
        ▼
8. What prevents recurrence?
```

This prevents premature actions such as blindly increasing resources, killing sessions, creating indexes, or restarting services.

---

## Relationship With Other Playbook Sections

Operations depends heavily on concepts covered elsewhere in the engineering playbook.

| Operations topic | Related concept |
|---|---|
| Index maintenance | Index architecture |
| Table maintenance | Storage engine / MVCC |
| VACUUM | Transaction architecture |
| Connection pooling | Backend-to-database architecture |
| Read replicas | Replication architecture |
| Failover | High availability architecture |
| Capacity planning | Database scaling architecture |
| PITR | Backup and recovery |
| Incident response | Observability and reliability |
| SQL best practices | Query optimization and security |
| Multi-region recovery | DR architecture |
| Database security operations | SQL security |

Operations should therefore be treated as the point where database architecture becomes **production behavior**.

---

## Key Takeaways

- **Database operations are a continuous lifecycle:** maintenance, monitoring, backups, recovery, scaling, and failover must work together rather than as isolated activities.
- **Measure before changing production:** use query statistics, execution plans, resource metrics, locks, replication state, and historical trends to identify the actual bottleneck.
- **Recovery must be verified:** backups, PITR, replicas, and failover mechanisms are only reliable when restoration and recovery procedures are regularly tested.
- **Control concurrency and change:** connection pools, worker concurrency, transaction duration, bounded retries, and safe migrations are critical to preventing operational failures.
- **Senior database engineering is failure-oriented:** design for saturation, node failure, data loss, bad deployments, replication problems, and recovery while continuously reducing the system's blast radius.