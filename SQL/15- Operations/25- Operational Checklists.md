# 25- Operational Checklists

## Overview

Operational checklists turn database reliability practices into repeatable procedures. They reduce dependency on individual engineers, make incidents easier to manage, and provide a consistent standard for deployments, maintenance, monitoring, recovery, and capacity management.

For a production PostgreSQL system, a checklist should cover the complete operational lifecycle:

```text
Design
  ↓
Deploy
  ↓
Monitor
  ↓
Maintain
  ↓
Scale
  ↓
Recover
  ↓
Review
  └──────────────→ Improve
```

A good checklist is not a collection of generic reminders. Each item should be actionable, verifiable, and tied to a known operational risk.

---

## Operational Principles

A production database should be operated according to a few core principles:

| Principle | Operational meaning |
|---|---|
| Automate | Automate repetitive and deterministic operations |
| Observe | Make failures and degradation measurable |
| Bound | Use timeouts, limits, quotas, and retry budgets |
| Verify | Validate backups, migrations, failovers, and changes |
| Recover | Maintain tested recovery procedures |
| Minimize blast radius | Isolate workloads, credentials, and failure domains |
| Prefer reversible changes | Use incremental and backward-compatible deployments |
| Document | Record procedures, ownership, and escalation paths |

The most important distinction is between **configuration** and **verified capability**.

For example:

```text
Backup job configured
        ≠
Backup successfully restored
```

Likewise:

```text
Replica configured
        ≠
Failover successfully tested
```

Operational maturity comes from verifying the complete behavior.

---

## Daily Database Health Checklist

A daily review should focus on signals that indicate emerging reliability problems.

### Availability

- [ ] Database is reachable.
- [ ] Primary is healthy.
- [ ] Expected replicas are connected.
- [ ] No unexpected failovers occurred.
- [ ] No database restart loops are present.

### Connections

- [ ] Connection count is within the expected range.
- [ ] No unexpected connection spikes occurred.
- [ ] Connection pools are not exhausting.
- [ ] No significant number of `idle in transaction` sessions exist.
- [ ] Connection acquisition latency is healthy.

### Queries

- [ ] No unexpected query latency regression occurred.
- [ ] Top expensive queries are understood.
- [ ] Query error rates are normal.
- [ ] No abnormal query-volume spike occurred.
- [ ] No unexpected sequential scans appeared on critical workloads.

### Locks and Transactions

- [ ] No prolonged lock waits exist.
- [ ] No unexpected blockers exist.
- [ ] No deadlock spike occurred.
- [ ] No unusually long-running transactions exist.
- [ ] Transaction throughput is within expected range.

### Storage and Maintenance

- [ ] Disk utilization has sufficient headroom.
- [ ] WAL growth is normal.
- [ ] Autovacuum is keeping up.
- [ ] Analyze activity is healthy.
- [ ] Table and index growth is within expected trends.
- [ ] No unusual bloat indicators are present.

### Replication

- [ ] Replica lag is within workload-specific limits.
- [ ] Replicas are replaying WAL normally.
- [ ] Replication slots are not retaining unexpected WAL.
- [ ] No replica has fallen permanently behind.

---

## Weekly Operational Checklist

Weekly reviews should focus on trends rather than individual incidents.

### Performance

- [ ] Review top queries by total execution time.
- [ ] Review top queries by mean latency.
- [ ] Review query frequency changes.
- [ ] Review CPU trends.
- [ ] Review memory trends.
- [ ] Review I/O latency and throughput.
- [ ] Review temporary file usage.
- [ ] Investigate new query-plan regressions.

Example:

```sql
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

The goal is to identify workload trends before they become incidents.

---

## Weekly Storage Review

Track:

- [ ] Database size.
- [ ] Largest tables.
- [ ] Largest indexes.
- [ ] Growth rate.
- [ ] WAL generation.
- [ ] Backup size.
- [ ] Available disk capacity.
- [ ] Partition growth.
- [ ] Retention effectiveness.

Example:

```sql
SELECT
    schemaname,
    relname,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;
```

Storage planning should use growth trends rather than only the current percentage consumed.

---

## Weekly Index Review

- [ ] Identify rapidly growing indexes.
- [ ] Identify unused or rarely used indexes.
- [ ] Review redundant indexes.
- [ ] Review indexes on high-write tables.
- [ ] Review new indexes added during deployments.
- [ ] Check whether critical queries still use expected access paths.
- [ ] Review index creation failures.
- [ ] Review index maintenance requirements.

Do not automatically remove an index solely because its current scan count is low. Consider observation period, workload seasonality, constraints, and recent statistics resets.

---

## Monthly Database Review

A monthly review should examine capacity, reliability, and architectural direction.

### Capacity

- [ ] CPU growth reviewed.
- [ ] Memory growth reviewed.
- [ ] Storage growth reviewed.
- [ ] Connection growth reviewed.
- [ ] Query volume growth reviewed.
- [ ] WAL growth reviewed.
- [ ] Replica capacity reviewed.
- [ ] Failover capacity reviewed.

### Reliability

- [ ] Backup success reviewed.
- [ ] Restore test completed according to policy.
- [ ] Replication health reviewed.
- [ ] Failover readiness reviewed.
- [ ] Recovery procedures reviewed.
- [ ] Incident history reviewed.
- [ ] Known reliability risks tracked.

### Security

- [ ] Database roles reviewed.
- [ ] Privileged access reviewed.
- [ ] Credential rotation status checked.
- [ ] Audit logs reviewed.
- [ ] TLS configuration verified.
- [ ] Backup access reviewed.
- [ ] Unnecessary privileges removed.

### Maintenance

- [ ] Autovacuum behavior reviewed.
- [ ] Long-running transactions reviewed.
- [ ] Table growth reviewed.
- [ ] Index growth reviewed.
- [ ] Partition lifecycle reviewed.
- [ ] Retention policies verified.

---

## Pre-Deployment Checklist

Database changes should be reviewed independently of application code.

### Schema Compatibility

- [ ] Migration is backward-compatible with currently running application versions.
- [ ] New columns have safe defaults or deployment sequencing.
- [ ] Removed columns are no longer referenced.
- [ ] Data types are compatible with existing data.
- [ ] Constraints will not unexpectedly reject existing records.
- [ ] Foreign-key changes have been evaluated for locking impact.

### Performance

- [ ] Query plans were evaluated against realistic data.
- [ ] New indexes were justified.
- [ ] Large updates are batched where appropriate.
- [ ] Migration duration has been estimated.
- [ ] Expected WAL generation has been considered.
- [ ] Replica impact has been considered.

### Locking

- [ ] Migration lock behavior is understood.
- [ ] `lock_timeout` is configured where appropriate.
- [ ] Long-running transactions are considered.
- [ ] Peak traffic timing has been evaluated.
- [ ] Large-table DDL has an operational plan.

### Rollout

- [ ] Deployment order is documented.
- [ ] Application compatibility is verified.
- [ ] Rollback or forward-recovery strategy exists.
- [ ] Monitoring is prepared before deployment.
- [ ] Success criteria are defined.
- [ ] Abort criteria are defined.

---

## Migration Checklist

For a production migration:

1. Verify current application and schema versions.
2. Confirm the migration is backward-compatible.
3. Check active long-running transactions.
4. Estimate table size and migration duration.
5. Check lock behavior.
6. Apply the migration using the approved deployment mechanism.
7. Monitor CPU, locks, latency, WAL, and replication.
8. Verify the resulting schema.
9. Verify application behavior.
10. Record the deployment outcome.

For large changes, prefer expand-and-contract:

```text
Expand
  ↓
Add compatible schema
  ↓
Deploy application
  ↓
Backfill gradually
  ↓
Validate
  ↓
Switch application behavior
  ↓
Contract
  ↓
Remove obsolete schema later
```

Avoid destructive schema changes during the same deployment that still has old application instances running.

---

## Pre-Index Creation Checklist

Before creating an index:

- [ ] Identify the exact query pattern.
- [ ] Confirm the query is important enough to optimize.
- [ ] Capture the current execution plan.
- [ ] Check existing indexes.
- [ ] Check column selectivity.
- [ ] Consider equality, range, and ordering requirements.
- [ ] Consider partial or expression indexes where appropriate.
- [ ] Estimate index size.
- [ ] Consider write amplification.
- [ ] Consider replication and backup impact.
- [ ] Determine whether concurrent creation is required.

For large production tables, consider:

```sql
CREATE INDEX CONCURRENTLY orders_customer_created_idx
ON orders (customer_id, created_at DESC);
```

`CREATE INDEX CONCURRENTLY` has additional operational constraints and cannot run inside a transaction block.

---

## Index Removal Checklist

Before removing an index:

- [ ] Confirm the index is not required by a constraint.
- [ ] Review historical usage.
- [ ] Review query plans.
- [ ] Check application releases that may depend on it.
- [ ] Consider seasonal workloads.
- [ ] Check whether replicas use the index differently.
- [ ] Check whether it supports a unique constraint.
- [ ] Check whether another index fully replaces it.
- [ ] Record the reason for removal.
- [ ] Monitor query performance after removal.

Prefer evidence over assumptions.

---

## VACUUM and ANALYZE Checklist

### Routine Maintenance

- [ ] Autovacuum is enabled.
- [ ] Autovacuum is keeping up with write volume.
- [ ] Analyze statistics are reasonably fresh.
- [ ] Large/high-churn tables receive appropriate maintenance.
- [ ] Long-running transactions are not preventing cleanup.
- [ ] Transaction ID age is monitored.
- [ ] Dead tuple growth is investigated.

Example:

```sql
SELECT
    schemaname,
    relname,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 20;
```

Do not treat a high dead-tuple count as an automatic reason to run manual vacuum immediately. Investigate workload, autovacuum behavior, transaction age, and table characteristics first.

---

## Backup Checklist

### Configuration

- [ ] Backup mechanism is configured.
- [ ] Backup retention matches business requirements.
- [ ] WAL archiving is healthy where PITR is required.
- [ ] Backup storage is independent from the primary database.
- [ ] Cross-region or cross-account copies exist where required.
- [ ] Encryption is enabled.
- [ ] Backup access is restricted.

### Verification

- [ ] Latest backup completed successfully.
- [ ] Backup integrity is checked.
- [ ] WAL archives are arriving normally.
- [ ] Backup age is within RPO.
- [ ] Restore tests are performed according to policy.

Remember:

```text
Backup exists
      ↓
Backup is accessible
      ↓
Backup can be restored
      ↓
Restored database is valid
      ↓
Application can operate
```

Each stage must be verified.

---

## Restore Checklist

Before restoration:

- [ ] Incident scope is understood.
- [ ] Recovery target is defined.
- [ ] Required backup/WAL range is available.
- [ ] RPO is understood.
- [ ] Recovery environment is secured.
- [ ] Application impact is understood.
- [ ] Dependent systems are identified.
- [ ] Stakeholders are informed.

During restoration:

- [ ] Restore to the intended recovery point.
- [ ] Monitor restore progress.
- [ ] Validate database startup.
- [ ] Validate schema.
- [ ] Validate critical tables.
- [ ] Validate critical queries.

After restoration:

- [ ] Application connectivity verified.
- [ ] Critical business workflows verified.
- [ ] Replication re-established if required.
- [ ] Kafka/Celery processing state reviewed.
- [ ] Redis cache behavior reviewed.
- [ ] Endpoint routing verified.
- [ ] Monitoring restored.
- [ ] Incident timeline documented.

---

## Point-in-Time Recovery Checklist

For PITR:

- [ ] Base backup exists.
- [ ] Required WAL segments are available.
- [ ] Target timestamp is clearly defined.
- [ ] Recovery environment is isolated.
- [ ] Restore procedure is documented.
- [ ] Recovery target is validated.
- [ ] Application state is reconciled.
- [ ] RTO is measured.

A PITR procedure should be periodically tested against realistic database sizes.

---

## Replication Checklist

### Primary

- [ ] WAL generation is healthy.
- [ ] Expected replicas are connected.
- [ ] Replication slots are healthy.
- [ ] WAL retention is controlled.
- [ ] Primary workload remains within capacity.

### Replicas

- [ ] Replica is in recovery mode as expected.
- [ ] Replay is progressing.
- [ ] Replica lag is within acceptable limits.
- [ ] Long-running replica queries are understood.
- [ ] Read routing excludes unhealthy replicas.

Example:

```sql
SELECT
    application_name,
    client_addr,
    state,
    sync_state,
    write_lag,
    flush_lag,
    replay_lag
FROM pg_stat_replication;
```

Replica lag thresholds should be workload-specific.

---

## Read Replica Checklist

Before routing traffic to replicas:

- [ ] Application understands asynchronous replication.
- [ ] Read-after-write requirements are documented.
- [ ] Critical consistency-sensitive reads use the primary.
- [ ] Replica lag is monitored.
- [ ] Replica failure has a fallback.
- [ ] Connection pools are separated where appropriate.
- [ ] Reporting queries do not overload transactional replicas.

Do not assume:

```text
Write primary
    ↓
Immediate read replica
    ↓
Guaranteed latest data
```

Asynchronous replication does not provide that guarantee.

---

## Failover Checklist

### Before Failover

- [ ] Confirm failure condition.
- [ ] Determine whether primary is actually unavailable.
- [ ] Prevent split-brain behavior.
- [ ] Identify the best promotion candidate.
- [ ] Confirm replication state.
- [ ] Communicate incident status.

### During Failover

- [ ] Promote the intended standby.
- [ ] Update stable writer endpoint.
- [ ] Prevent old primary from accepting writes.
- [ ] Reconnect application pools.
- [ ] Monitor transaction errors.
- [ ] Monitor connection storms.

### After Failover

- [ ] Verify the new primary.
- [ ] Verify application writes.
- [ ] Verify read routing.
- [ ] Verify replica topology.
- [ ] Check replication lag.
- [ ] Check error rates.
- [ ] Check connection counts.
- [ ] Investigate uncertain transactions.
- [ ] Rebuild the intended standby topology.

Failover is incomplete until the application has successfully resumed normal database behavior.

---

## Connection Pool Checklist

- [ ] Pool sizes are explicitly configured.
- [ ] Total fleet connection budget is known.
- [ ] PostgreSQL connection limits are understood.
- [ ] Pool acquisition timeout exists.
- [ ] Connection leaks are monitored.
- [ ] Idle-in-transaction sessions are monitored.
- [ ] Stale connections are handled.
- [ ] Failover reconnect behavior is tested.
- [ ] Worker connections are included in capacity calculations.
- [ ] Read and write pools are evaluated separately where needed.

A useful capacity calculation is:

```text
Total possible connections
=
web replicas × pool capacity
+
worker replicas × pool capacity
+
admin/reporting clients
+
deployment overlap
+
other database clients
```

---

## Lock Monitoring Checklist

When lock contention is suspected:

- [ ] Identify waiting sessions.
- [ ] Identify blocking sessions.
- [ ] Identify locked relations.
- [ ] Determine transaction age.
- [ ] Determine query duration.
- [ ] Identify application request/job.
- [ ] Determine whether the blocker is expected.
- [ ] Check for long-running transactions.
- [ ] Check for DDL.
- [ ] Check for hot-row workloads.

Useful diagnostics include:

```sql
SELECT
    pid,
    usename,
    application_name,
    state,
    wait_event_type,
    wait_event,
    xact_start,
    query_start,
    query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';
```

And:

```sql
SELECT
    pid,
    pg_blocking_pids(pid) AS blocking_pids,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

Diagnose the blocker, not merely the waiting request.

---

## Deadlock Checklist

When deadlocks occur:

- [ ] Capture the PostgreSQL deadlock error.
- [ ] Confirm SQLSTATE `40P01`.
- [ ] Identify participating transactions.
- [ ] Identify lock acquisition order.
- [ ] Check multi-row update ordering.
- [ ] Check foreign-key interactions.
- [ ] Check triggers.
- [ ] Check advisory locks.
- [ ] Check DDL.
- [ ] Verify transaction retry behavior.
- [ ] Add bounded backoff and jitter where appropriate.
- [ ] Fix inconsistent lock ordering.

The best long-term solution is usually to remove the circular dependency rather than merely increasing retries.

---

## Slow Query Incident Checklist

When query latency increases:

1. Confirm whether the latency increase is real.
2. Determine whether the issue affects one query or the workload broadly.
3. Check database CPU, memory, and I/O.
4. Check connection pool behavior.
5. Check lock waits.
6. Check replica lag if reads use replicas.
7. Inspect `pg_stat_statements`.
8. Capture the execution plan.
9. Compare estimated and actual rows.
10. Check recent deployments or data growth.
11. Check statistics and indexes.
12. Apply the smallest safe mitigation.
13. Verify recovery.
14. Record the root cause.

Do not immediately create an index because a query is slow.

---

## High CPU Checklist

- [ ] Identify top CPU-consuming queries.
- [ ] Check query frequency.
- [ ] Check N+1 behavior.
- [ ] Check retry amplification.
- [ ] Check sequential scans.
- [ ] Check joins and aggregations.
- [ ] Check sorting and temporary work.
- [ ] Check JSON/regex/function-heavy expressions.
- [ ] Check autovacuum activity.
- [ ] Check concurrent sessions.
- [ ] Check recent deployments.
- [ ] Check data growth.
- [ ] Reduce workload safely before scaling infrastructure.

---

## High Memory Checklist

- [ ] Check OS available memory.
- [ ] Check swap usage.
- [ ] Check container memory limits.
- [ ] Check PostgreSQL shared memory settings.
- [ ] Check active connection count.
- [ ] Check `work_mem` interactions with concurrency.
- [ ] Check large sorts and hashes.
- [ ] Check large result sets.
- [ ] Check maintenance operations.
- [ ] Check application memory separately.
- [ ] Check Redis and worker memory if colocated.

Do not increase `work_mem` globally without considering the number of concurrent memory-consuming operations.

---

## Storage Incident Checklist

When disk utilization increases rapidly:

- [ ] Confirm actual filesystem usage.
- [ ] Identify database growth.
- [ ] Check largest tables.
- [ ] Check largest indexes.
- [ ] Check WAL growth.
- [ ] Check replication slots.
- [ ] Check failed WAL archiving.
- [ ] Check temporary files.
- [ ] Check logs.
- [ ] Check backup staging.
- [ ] Check long-running transactions.
- [ ] Check unusual batch jobs.
- [ ] Protect remaining free space.

Emergency actions should avoid destructive cleanup that could compromise recovery.

---

## Table Growth Checklist

For rapidly growing tables:

- [ ] Determine row growth rate.
- [ ] Determine storage growth rate.
- [ ] Identify the owning service.
- [ ] Determine retention requirements.
- [ ] Determine whether old data can be archived.
- [ ] Evaluate partitioning.
- [ ] Review index growth.
- [ ] Review vacuum behavior.
- [ ] Review backup impact.
- [ ] Review query performance as data grows.
- [ ] Update capacity forecasts.

A table can become an operational problem long before the database reaches its absolute storage limit.

---

## Partition Maintenance Checklist

For partitioned tables:

- [ ] Future partitions exist before expected traffic arrives.
- [ ] Partition bounds are correct.
- [ ] Default partition is monitored.
- [ ] Indexes exist where required.
- [ ] Partition pruning is working.
- [ ] Old partitions are archived or removed according to policy.
- [ ] Partition count remains operationally manageable.
- [ ] Statistics are maintained.
- [ ] Retention automation is monitored.
- [ ] Partition creation failures trigger alerts.

Partitioning is not a replacement for query optimization or appropriate indexes.

---

## Production Query Change Checklist

Before modifying a high-traffic query:

- [ ] Identify all callers.
- [ ] Capture current SQL.
- [ ] Capture current execution plan.
- [ ] Understand result cardinality.
- [ ] Check production data distribution.
- [ ] Check index dependencies.
- [ ] Check transaction behavior.
- [ ] Check replica behavior.
- [ ] Check expected CPU/I/O impact.
- [ ] Test realistic parameters.
- [ ] Deploy gradually where possible.
- [ ] Monitor after release.

For Django and SQLAlchemy applications, inspect generated SQL rather than evaluating ORM code alone.

---

## Security Operations Checklist

### Access

- [ ] Runtime roles use least privilege.
- [ ] Migration access is separated.
- [ ] Administrative access is restricted.
- [ ] Break-glass access is controlled.
- [ ] Unused roles are removed.
- [ ] Membership changes are reviewed.

### Credentials

- [ ] Production credentials are stored securely.
- [ ] Credentials are rotated.
- [ ] Secrets are not committed to source control.
- [ ] Secrets are not written to logs.
- [ ] CI/CD uses appropriate workload identity where possible.

### Database

- [ ] TLS is enabled where required.
- [ ] Network access is restricted.
- [ ] RLS policies are tested where used.
- [ ] Sensitive data access is auditable.
- [ ] Backup access is restricted.

---

## Monitoring Configuration Checklist

Every production database should have dashboards for:

### Database Health

- CPU.
- Memory.
- Disk.
- I/O latency.
- Connections.
- Transactions.
- Errors.

### Query Health

- Query latency.
- Query volume.
- Total execution time.
- Slow queries.
- Query-plan changes.
- Temporary I/O.

### Concurrency

- Lock waits.
- Deadlocks.
- Long transactions.
- Idle-in-transaction sessions.

### Maintenance

- Autovacuum.
- Analyze.
- Dead tuples.
- Table growth.
- Index growth.
- Transaction ID age.

### Replication

- Replica lag.
- WAL generation.
- WAL retention.
- Replication connection state.
- Replay progress.

### Recovery

- Backup success.
- Backup age.
- WAL archive status.
- Restore-test status.

---

## Alerting Checklist

Alerts should be actionable.

### Critical

- [ ] Primary unavailable.
- [ ] Database unavailable.
- [ ] Storage exhaustion imminent.
- [ ] Recovery capability unavailable.
- [ ] Replication required for HA is broken.

### High

- [ ] Connection pool exhaustion.
- [ ] Severe replica lag.
- [ ] Long lock waits.
- [ ] Significant query latency regression.
- [ ] WAL retention growing unexpectedly.
- [ ] Backup failure.

### Medium

- [ ] Increasing deadlocks.
- [ ] Increasing serialization failures.
- [ ] Increasing storage growth.
- [ ] Autovacuum falling behind.
- [ ] Increasing connection usage.

Avoid alerting solely on high utilization without considering saturation, latency, and workload behavior.

---

## Deployment Verification Checklist

Immediately after a database-related deployment:

- [ ] Migration completed successfully.
- [ ] Application health checks are passing.
- [ ] Database connections are healthy.
- [ ] Query error rate is normal.
- [ ] Latency is within expected range.
- [ ] CPU is within expected range.
- [ ] Locks are normal.
- [ ] Replica lag is normal.
- [ ] WAL generation is normal.
- [ ] Critical business workflows succeed.

For Kubernetes rolling deployments, verify that old and new application versions can coexist with the deployed schema.

---

## Post-Incident Checklist

After a database incident:

### Incident Review

- [ ] Timeline reconstructed.
- [ ] Trigger identified.
- [ ] Detection time recorded.
- [ ] Mitigation time recorded.
- [ ] Recovery time recorded.
- [ ] Customer impact measured.
- [ ] Data integrity verified.
- [ ] RPO/RTO compared with actual results.

### Root Cause

- [ ] Technical root cause identified.
- [ ] Contributing factors identified.
- [ ] Detection gaps identified.
- [ ] Recovery gaps identified.
- [ ] Capacity assumptions reviewed.
- [ ] Operational process reviewed.

### Follow-Up

- [ ] Corrective actions created.
- [ ] Owners assigned.
- [ ] Priorities assigned.
- [ ] Monitoring improvements identified.
- [ ] Runbooks updated.
- [ ] Tests added where appropriate.

Avoid closing an incident with only:

> Restarted database and service recovered.

The goal is to understand why the system entered an unsafe state and how recurrence will be prevented.

---

## Disaster Recovery Checklist

At the architecture level:

- [ ] RPO is documented.
- [ ] RTO is documented.
- [ ] Backup strategy matches RPO.
- [ ] Recovery strategy matches RTO.
- [ ] Cross-region strategy exists where required.
- [ ] Recovery credentials are available.
- [ ] Recovery environment is documented.
- [ ] Database restoration is tested.
- [ ] Application restoration is tested.
- [ ] DNS/endpoint changes are documented.
- [ ] Kafka/Celery recovery behavior is documented.
- [ ] Redis recovery behavior is documented.
- [ ] Business validation steps are documented.

---

## Capacity Planning Checklist

Review capacity across:

| Resource | Questions |
|---|---|
| CPU | Is utilization growing faster than traffic? |
| Memory | Is available memory declining? |
| Storage | How many days/months of capacity remain? |
| I/O | Is latency increasing under peak load? |
| Connections | Is connection demand approaching safe limits? |
| WAL | Is generation increasing unexpectedly? |
| Replicas | Can replicas handle expected read traffic? |
| Failover | Can the standby handle production load? |
| Queries | Are query counts growing with traffic? |
| Background work | Are workers consuming increasing DB capacity? |

Plan capacity using peak and failure scenarios, not only average traffic.

---

## Production SQL Change Checklist

For changes involving SQL itself:

- [ ] SQL is parameterized.
- [ ] Dynamic identifiers are validated or safely constructed.
- [ ] Query result size is bounded.
- [ ] Pagination strategy is appropriate.
- [ ] Transaction boundary is intentional.
- [ ] Lock behavior is understood.
- [ ] Timeout behavior is appropriate.
- [ ] Query plan is evaluated.
- [ ] Index impact is evaluated.
- [ ] Error handling is defined.
- [ ] Retry semantics are safe.
- [ ] Observability exists.

---

## Backend Integration Checklist

For Django and FastAPI services:

### Django

- [ ] ORM-generated SQL is understood for critical queries.
- [ ] N+1 queries are prevented.
- [ ] `select_related()` and `prefetch_related()` are used appropriately.
- [ ] Transactions use explicit boundaries.
- [ ] `select_for_update()` is used only when required.
- [ ] Persistent connection behavior is understood.
- [ ] Database routers are correct when replicas are used.
- [ ] `transaction.on_commit()` is used for appropriate post-commit actions.

### FastAPI / SQLAlchemy

- [ ] Session lifecycle is explicit.
- [ ] Connections are returned to the pool.
- [ ] Transaction boundaries are clear.
- [ ] Pool limits are configured.
- [ ] Pool timeout is bounded.
- [ ] Long-running sessions are monitored.
- [ ] Async database access is not blocking the event loop.
- [ ] Retry behavior is transaction-aware.

---

## Background Worker Checklist

For Celery or Kafka consumers:

- [ ] Worker concurrency is included in database capacity planning.
- [ ] Tasks are idempotent.
- [ ] Database transactions are short.
- [ ] External calls are not unnecessarily held inside transactions.
- [ ] Retries are bounded.
- [ ] Backoff and jitter are configured where appropriate.
- [ ] Failed tasks do not create uncontrolled database load.
- [ ] Batch operations are controlled.
- [ ] Worker shutdown behavior is safe.
- [ ] Database connection cleanup is verified.

---

## Operational Ownership Checklist

Every production database should have clear ownership.

Document:

- [ ] Service owner.
- [ ] Database owner.
- [ ] Platform owner.
- [ ] Security owner.
- [ ] On-call team.
- [ ] Escalation path.
- [ ] Backup owner.
- [ ] Recovery owner.
- [ ] Migration owner.

A database without a clear operational owner becomes a reliability risk even when the technology itself is correctly configured.

---

## Change Management Checklist

For significant database changes:

- [ ] Change has an identified owner.
- [ ] Risk is documented.
- [ ] Dependencies are documented.
- [ ] Rollout strategy is documented.
- [ ] Rollback/forward-recovery strategy is documented.
- [ ] Monitoring is prepared.
- [ ] Expected impact is known.
- [ ] Maintenance window is defined if required.
- [ ] Stakeholders are informed.
- [ ] Post-change validation is defined.

---

## Interview-Oriented Operational Questions

A senior backend engineer should be able to answer:

- How do you detect database saturation?
- How do you distinguish CPU pressure from lock contention?
- How do you identify the session blocking other transactions?
- How do you investigate a sudden query latency increase?
- How do you detect a connection pool problem?
- How do you determine whether an index is actually useful?
- How do you monitor table growth?
- Why is autovacuum important?
- How do you verify that backups are usable?
- How do you design PITR?
- What happens to application connections during failover?
- How do you handle uncertain commits?
- How do you prevent retry storms?
- How do you safely deploy a schema change?
- How do you handle a large production backfill?
- How do you monitor replica lag?
- What happens if the primary fails while a request is committing?
- How do you plan database capacity?
- How do you protect the database from background workers?
- How do you test disaster recovery?

A strong answer should describe **signals, diagnosis, mitigation, verification, and prevention**, rather than only naming a PostgreSQL command.

---

## Common Operational Mistakes

### Monitoring Only CPU

A database can be unhealthy while CPU remains moderate because it is waiting on locks, I/O, connections, or external dependencies.

**Better:** correlate CPU, wait events, connections, locks, I/O, and latency.

### Alerting on Every Metric

Too many alerts create noise and eventually get ignored.

**Better:** alert on conditions that require action.

### No Baseline

A value such as 100 active connections has different meaning for different systems.

**Better:** establish workload-specific baselines and capacity limits.

### Manual Production Changes

Ad-hoc SQL changes create drift and reduce auditability.

**Better:** use version-controlled migrations or controlled operational procedures.

### No Verification After Changes

A successful migration command does not prove application correctness.

**Better:** perform post-change validation.

### Ignoring Background Work

Celery, Kafka consumers, ETL jobs, and reporting workloads can dominate database load.

**Better:** include every database client in operational monitoring.

### Treating Runbooks as Documentation Only

A runbook that has never been exercised may fail during an incident.

**Better:** rehearse important procedures.

### Removing Monitoring During Incidents

Disabling alerts can hide the evidence needed to understand recovery.

**Better:** suppress only noisy alerts and preserve diagnostic telemetry.

---

## Production Operational Review

A mature database operation should be able to answer these questions quickly:

```text
Is the database available?
        ↓
Is it saturated?
        ↓
What workload is consuming capacity?
        ↓
Are queries slow or waiting?
        ↓
Are connections exhausted?
        ↓
Are locks blocking progress?
        ↓
Is replication healthy?
        ↓
Is storage growing safely?
        ↓
Can we recover if this gets worse?
```

This provides a practical incident-diagnosis hierarchy:

| Layer | Primary question |
|---|---|
| Availability | Can clients connect? |
| Capacity | Is the database saturated? |
| Concurrency | Are sessions waiting? |
| Workload | Which queries consume resources? |
| Maintenance | Is PostgreSQL keeping up with cleanup/statistics? |
| Replication | Are replicas healthy? |
| Storage | Is capacity sufficient? |
| Recovery | Can the system be restored or failed over? |

---

## Operational Maturity Model

| Level | Characteristics |
|---|---|
| Reactive | Engineers discover failures manually |
| Basic | Metrics and basic alerts exist |
| Managed | Runbooks, backups, monitoring, and ownership are defined |
| Reliable | Recovery and failover are regularly tested |
| Mature | Capacity, failure modes, automation, and operational risk are continuously reviewed |

The goal is not maximum process. The goal is predictable operation with a controlled response to failure.

---

## Key Takeaways

- **Operational checklists make reliability repeatable:** every critical database operation should have explicit, verifiable steps and ownership.
- **Monitor the complete system:** queries, connections, locks, storage, maintenance, replication, backups, application behavior, and capacity must be evaluated together.
- **Verify recovery capabilities:** backups, PITR, replicas, failover, and restore procedures are only reliable when they are regularly tested.
- **Prefer controlled and reversible changes:** use backward-compatible migrations, bounded backfills, explicit rollout plans, and post-change validation.
- **Senior database operations are failure-oriented:** understand what can fail, how it will be detected, how the blast radius is limited, how recovery works, and how recurrence will be prevented.