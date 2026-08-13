# Interview Questions: Production Troubleshooting Scenarios

This section presents realistic production incident scenarios that test a candidate's ability to diagnose, triage, and resolve database issues under pressure. Each scenario mirrors real-world outages encountered in production environments.

---

# Scenario 1: Database CPU at 100%

## The Situation

Your monitoring alert fires at 2 PM: RDS PostgreSQL `CPUUtilization` is at 100%. Application response times have spiked from 50ms to 15 seconds. The on-call team is paged.

## Expected Diagnostic Steps

**Step 1: Confirm the scope**
- Check CloudWatch: Is CPU the bottleneck, or are memory, I/O, or connections also saturated?
- Check `DatabaseConnections`: Are connections piling up because queries are taking longer?

**Step 2: Identify the offending query**
- Open **Performance Insights**. Look at the DB Load chart. The AAS (Average Active Sessions) will show which queries are consuming the most CPU.
- Filter by Top SQL. Identify the query with the highest load.

**Step 3: Analyze the query**
- Run `EXPLAIN ANALYZE` on the offending query.
- Look for **Sequential Scans** on large tables, **Nested Loop Joins** on unindexed columns, or **Sort operations** spilling to disk.

**Step 4: Apply the fix**
- If a missing index is the cause: Create the index using `CREATE INDEX CONCURRENTLY` (non-blocking in PostgreSQL).
- If the query is fundamentally inefficient: Rewrite the query or add a materialized view.
- If a sudden code deployment introduced the query: Roll back the deployment.

**Step 5: Verify**
- Confirm CPU drops back to baseline after the fix.
- Set up a CloudWatch alarm on `CPUUtilization > 80%` to catch this earlier next time.

---

# Scenario 2: "Too Many Connections" Errors

## The Situation

Your application logs are flooded with `FATAL: too many connections for role "app_user"`. No new application instances were deployed. The error started gradually 30 minutes ago.

## Expected Diagnostic Steps

**Step 1: Check the connection count**
- CloudWatch metric `DatabaseConnections` shows connections at the maximum (e.g., 200/200).
- This confirms the database has reached its `max_connections` limit.

**Step 2: Identify who is holding connections**
- Query the database directly:
```sql
SELECT client_addr, state, count(*)
FROM pg_stat_activity
GROUP BY client_addr, state
ORDER BY count DESC;
```
- Look for connections in `idle` state. A large number of idle connections indicates a **connection leak** in the application.

**Step 3: Identify the leak**
- Check if a specific application pod has disproportionately many connections.
- Review recent code changes for missing `finally` blocks or unclosed database sessions (common in Python/Django: forgetting `connection.close()` or not using `with` context managers).

**Step 4: Immediate mitigation**
- Terminate idle connections:
```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND query_start < NOW() - INTERVAL '10 minutes';
```
- If the application uses Lambda: Deploy **RDS Proxy** to pool connections.

**Step 5: Permanent fix**
- Fix the connection leak in application code.
- Configure the application connection pool with proper `max_pool_size`, `idle_timeout`, and `max_lifetime` settings.
- Set `idle_in_transaction_session_timeout` in the PostgreSQL parameter group to auto-kill sessions that have been idle inside a transaction for too long.

---

# Scenario 3: Replication Lag Causing Stale Reads

## The Situation

A customer complains: "I just updated my profile, but when I refresh the page, I still see the old data." The application uses a read replica for GET requests.

## Root Cause

The application performs the profile update (write) against the primary database. The page refresh (read) is routed to a read replica. Because replication is asynchronous, the replica hasn't received the update yet — this is **replication lag**.

```text
User writes profile ──► Primary DB (committed) ──► Replica (not yet replicated)
User reads profile  ──► Read Replica (returns stale data)
```

## Solution

**Option 1: Read-After-Write Consistency**
Route reads that immediately follow a user's own write to the **primary** database instead of the replica. Implement this using a session flag or a short-duration cookie that forces primary reads for 5-10 seconds after a write.

**Option 2: Use Aurora**
Aurora reader instances share the same distributed storage volume as the writer. Replication lag is typically under 10 milliseconds, making stale reads virtually imperceptible.

**Option 3: Cache the write**
After the write, update the cache (ElastiCache) immediately. Subsequent reads hit the cache first, bypassing the replica entirely during the consistency window.

---

# Scenario 4: Storage Full on RDS

## The Situation

At 3 AM, your RDS instance transitions to `storage-full` state. The database becomes read-only. All write operations fail. The application is down.

## Expected Diagnostic Steps

**Step 1: Check why storage filled up**
- Connect to the database (reads still work) and check table sizes:
```sql
SELECT relname, pg_size_pretty(pg_total_relation_size(oid))
FROM pg_class
WHERE relkind = 'r'
ORDER BY pg_total_relation_size(oid) DESC
LIMIT 10;
```
- Check for oversized temporary tables created by unindexed sort/join operations.
- Check for WAL files piling up (if replication slots are stuck).

**Step 2: Immediate fix**
- Manually increase the allocated storage size via the RDS console or CLI. This takes effect within minutes and does not require downtime.
- If storage auto scaling was enabled, check if it reached the Maximum Storage Threshold and increase the limit.

**Step 3: Permanent fix**
- Enable Storage Auto Scaling if not already enabled.
- Set a reasonable Maximum Storage Threshold.
- Add a CloudWatch alarm on `FreeStorageSpace` with a threshold of 20% of total storage.
- If bloat is the cause, run `VACUUM FULL` on the largest tables (requires maintenance window as it locks the table).

---

# Scenario 5: ElastiCache Redis High CPU with Low Host CPU

## The Situation

Your ElastiCache Redis cluster is responding slowly. Application timeouts are increasing. CloudWatch shows `CPUUtilization` at only 22%, so the on-call engineer dismisses it as a non-issue. But latency continues to increase.

## Root Cause

Redis command execution is **single-threaded**. On a 4-vCPU host, the Redis engine thread can only saturate 1 core (25% of total host CPU). The `CPUUtilization` metric averages across all cores, showing 22% — but the engine thread is at 100%.

```text
Core 1: Redis Engine Thread ──► 100% (Saturated)
Core 2: Network I/O ──────────► 10%
Core 3: Idle ──────────────────► 0%
Core 4: Idle ──────────────────► 0%

Host CPUUtilization = (100+10+0+0)/4 = 27.5%  ← Looks fine!
EngineCPUUtilization = 100%                     ← Actually saturated!
```

## Solution

**Step 1: Monitor the correct metric**
- Set CloudWatch alarms on **`EngineCPUUtilization`**, not `CPUUtilization`. Alert at 80%.

**Step 2: Find the expensive commands**
- Enable Redis Slow Log (`slowlog-log-slower-than = 10000` microseconds).
- Check for expensive O(N) commands: `KEYS *`, `SMEMBERS` on large sets, `HGETALL` on large hashes, or complex Lua scripts.
- Replace `KEYS *` with `SCAN` (cursor-based, non-blocking).

**Step 3: Scale**
- If the workload is legitimately high-throughput: Enable **Cluster Mode** and shard the dataset across multiple primary nodes, each with its own engine thread.

---

# Scenario 6: Accidental DELETE on Production Database

## The Situation

A developer runs `DELETE FROM orders WHERE status = 'pending'` on the production database, intending to clean up test data. The query deletes 50,000 real customer orders.

## Recovery Steps

**If Using Aurora MySQL (with Backtrack enabled):**
```text
1. Identify the exact timestamp of the DELETE (from CloudTrail or application logs)
2. Run: aws rds backtrack-db-cluster --db-cluster-id prod-cluster --backtrack-to "2025-07-08T14:30:00Z"
3. Database rewinds IN-PLACE to before the DELETE (takes seconds)
4. Verify data is restored
```
- **Advantage**: No new instance, no endpoint change, recovery in seconds.

**If Using RDS (no Backtrack):**
```text
1. Use Point-in-Time Recovery (PITR) to restore to a timestamp just before the DELETE
2. RDS creates a NEW database instance with the restored data
3. Extract the deleted rows from the restored instance
4. INSERT the recovered rows back into the production database
5. Delete the temporary restored instance
```
- **Disadvantage**: Creates a new instance (new endpoint), takes minutes to hours depending on database size.

## Prevention

- Enable **Deletion Protection** on production databases.
- Implement a **read-only database user** for developers. Require a separate approval workflow for write access.
- Use `BEGIN; DELETE ...; SELECT count(*) ... ; ROLLBACK;` to preview the impact before committing.
- Enable `log_statement = 'all'` in the parameter group to audit all SQL statements.

---

# Scenario 7: DynamoDB Throttling During a Traffic Spike

## The Situation

Your DynamoDB table starts returning `ProvisionedThroughputExceededException` errors during a marketing campaign. The table is in Provisioned capacity mode with 1,000 WCU.

## Diagnostic Steps

**Step 1: Check the partition key distribution**
- In CloudWatch, check the `ConsumedWriteCapacityUnits` metric per partition. If one partition is receiving disproportionate traffic, you have a **hot partition**.

**Step 2: Identify the cause**
- If the partition key is a date (`2025-07-08`), all campaign writes hit a single partition.
- If the partition key is a user ID but one celebrity user generates 90% of traffic, that partition is hot.

## Solution

**Immediate**:
- Switch to **On-Demand capacity mode** (absorbs spikes instantly, no pre-provisioning needed).

**Long-term**:
- Redesign the partition key to distribute writes evenly.
- Use **write sharding**: Append a random suffix to the partition key (e.g., `2025-07-08#7`) to distribute writes across multiple partitions.
- Pre-warm provisioned capacity before known traffic events.

---

# Key Takeaways

- Always monitor **`EngineCPUUtilization`** for Redis, not host-level `CPUUtilization`.
- Connection leaks are the #1 cause of "too many connections" errors. Fix the leak, then consider RDS Proxy.
- Stale reads from replicas are expected behavior (eventual consistency). Route consistency-critical reads to the primary.
- Aurora Backtrack recovers from accidental deletes in seconds. Standard RDS requires PITR (minutes-hours).
- DynamoDB throttling is almost always a hot partition problem. Use high-cardinality partition keys.
- Set CloudWatch alarms on `FreeStorageSpace`, `CPUUtilization`, `DatabaseConnections`, and `ReplicaLag` as a minimum baseline.

---
