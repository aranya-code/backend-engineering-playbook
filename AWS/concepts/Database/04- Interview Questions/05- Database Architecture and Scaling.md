# Interview Questions: Database Architecture and Scaling

This section provides detailed, senior-level interview questions and model answers focusing on database architecture patterns, replication, sharding, partitioning, and scaling strategies.

---

# Replication and High Availability

## Q1: Explain the split-brain problem in database replication. How do AWS services prevent it?

Split-brain occurs when two database nodes in a replicated cluster both believe they are the primary (writer). Both accept writes independently, causing data divergence that is extremely difficult to reconcile.

```text
Normal Operation:
  Primary (AZ-1) ──sync──► Standby (AZ-2)
  
Split-Brain (Network Partition):
  Primary (AZ-1) ◄── writes ── App Server 1
  Standby (AZ-2) ◄── writes ── App Server 2
  Both think they are primary. Data diverges.
```

**How AWS Prevents Split-Brain:**

- **RDS Multi-AZ**: AWS controls the failover process centrally. The standby cannot self-promote. Only the RDS control plane can trigger a promotion after confirming the primary is truly unreachable. Fencing mechanisms ensure the old primary is forcefully shut down before the standby is promoted.
- **Aurora**: The shared distributed storage layer acts as the single source of truth. Even if a writer node fails, the storage quorum (4-of-6 writes) prevents conflicting writes. Only one writer endpoint exists at any time.
- **DynamoDB Global Tables**: Uses a last-writer-wins conflict resolution strategy. If two regions write to the same item simultaneously, the write with the latest timestamp wins. This is an AP (availability-first) design that accepts eventual consistency.

---

## Q2: What is the difference between synchronous and asynchronous replication? When would you choose each?

| Aspect | Synchronous | Asynchronous |
|--------|-------------|--------------|
| **Write Path** | Primary waits for standby to confirm write before acknowledging client | Primary acknowledges client immediately, ships write to standby in background |
| **Data Loss Risk** | Zero (RPO = 0) | Possible (RPO = replication lag) |
| **Write Latency** | Higher (depends on network RTT to standby) | Lower (no waiting) |
| **Throughput** | Lower (constrained by slowest replica) | Higher |
| **AWS Example** | RDS Multi-AZ | RDS Read Replicas |

**Choose Synchronous When**: Zero data loss is mandatory (financial transactions, healthcare records, regulatory compliance).

**Choose Asynchronous When**: Write performance and throughput are prioritized over strict consistency (analytics pipelines, read scaling, cross-region replication).

---

## Q3: Your RDS Read Replica has a replication lag of 30 seconds and growing. What is the root cause and how do you fix it?

**Common Root Causes:**

1. **Long-running transactions on primary**: A single transaction running for 5 minutes generates a large WAL entry. The replica must replay this sequentially, blocking replication of subsequent writes.
   - **Fix**: Break long transactions into smaller batches.

2. **Write-heavy workload exceeding replica capacity**: If the primary generates WAL records faster than the replica can apply them.
   - **Fix**: Ensure the replica instance class is at least as large as the primary. Upgrade both if needed.

3. **Replica running heavy queries**: If you're running analytics queries on the replica, they can compete for CPU/memory with the replication process.
   - **Fix**: Use a dedicated replica for reporting, separate from the replication target.

4. **Cross-region network latency**: Cross-region replicas add physical transit delay.
   - **Fix**: Accept higher lag for cross-region DR replicas, or use Aurora Global Database (<1s lag).

**Monitoring**: Set a CloudWatch alarm on `ReplicaLag`. Alert at >5 seconds for application-critical replicas, >60 seconds for reporting replicas.

---

# Sharding and Partitioning

## Q4: When should you shard a database, and what are the biggest challenges?

**When to Shard**: Only when vertical scaling is exhausted AND the write workload exceeds what a single primary node can handle. Sharding is a last resort due to its operational complexity.

```text
Scaling Ladder:
1. Optimize queries and indexes          ← Start here
2. Scale vertically (bigger instance)
3. Add read replicas (read scaling)
4. Implement caching (ElastiCache)
5. Partition tables within one instance
6. Shard across multiple instances       ← Last resort
```

**Biggest Challenges:**

1. **Cross-shard queries**: Queries that span multiple shards (e.g., `SELECT * FROM orders WHERE total > 100`) require scatter-gather across all shards, which is slow and complex.
2. **Shard key selection**: A poor shard key creates hot shards (uneven distribution). Changing the shard key later requires a full data migration.
3. **Transactions across shards**: ACID transactions cannot span multiple independent database instances without implementing distributed transaction protocols (2PC), which are fragile and slow.
4. **Resharding**: Adding or removing shards requires redistributing data, which causes downtime or requires complex online migration tooling.

---

## Q5: How does DynamoDB handle partitioning internally, and what is a hot partition?

DynamoDB automatically partitions data across storage nodes using a hash of the partition key.

```text
Table: Orders
Partition Key: customer_id

Hash(customer_id = "C001") → Partition A
Hash(customer_id = "C002") → Partition B
Hash(customer_id = "C003") → Partition A
Hash(customer_id = "C004") → Partition C
```

Each partition supports up to **3,000 RCU** and **1,000 WCU**. If a single partition key receives disproportionate traffic, that partition becomes a bottleneck — a **hot partition**.

**Hot Partition Example**: Using `date` as the partition key for an events table. All writes on the current day hit a single partition while historical partitions sit idle.

**Mitigations:**
- Use high-cardinality partition keys (e.g., `user_id`, `order_id`).
- Use write sharding (append a random suffix to the partition key: `2025-07-08#3`).
- DynamoDB adaptive capacity can partially redistribute burst capacity across partitions, but it cannot fix fundamentally skewed access patterns.

---

## Q6: Explain the CQRS pattern and when you would use it with AWS databases.

CQRS (Command Query Responsibility Segregation) separates the write model (commands) from the read model (queries) into distinct database systems optimized for each workload.

```text
                    Application Layer
                    ├── Write Commands ──► Amazon Aurora (Normalized, ACID)
                    │                          │
                    │                    DynamoDB Streams / EventBridge
                    │                          │
                    │                          ▼
                    │                    Denormalized Read Store
                    │                    (DynamoDB / ElastiCache)
                    │                          │
                    └── Read Queries ──────────┘
```

**When to Use CQRS:**
- Read and write patterns have dramatically different scaling requirements (e.g., 100:1 read-to-write ratio).
- Reads require denormalized views that are expensive to compute on the fly from a normalized relational schema.
- Event sourcing is used and the read model needs to be materialized differently from the event log.

**When NOT to Use**: Simple CRUD applications where reads and writes access the same tables with similar patterns. CQRS adds significant architectural complexity.

---

# Connection Management and Pooling

## Q7: Your Lambda function is creating 500 new database connections per second. How do you solve this?

Lambda functions scale by creating new execution environments, each establishing a new database connection. At scale, this exhausts the database's `max_connections` limit and causes connection failures.

```text
Problem:
Lambda (1) ──► New Connection ┐
Lambda (2) ──► New Connection ┤
Lambda (3) ──► New Connection ├──► RDS (max_connections = 200) → EXHAUSTED!
...                           │
Lambda (500) ──► New Connection┘

Solution:
Lambda (1) ──┐
Lambda (2) ──┤
Lambda (3) ──┼──► RDS Proxy (Connection Pool) ──► 20 Shared Connections ──► RDS
...          │    (Multiplexes 500 clients        (Steady state, healthy)
Lambda (500)─┘     over 20 backend connections)
```

**Solution: Deploy RDS Proxy**
- RDS Proxy maintains a pool of database connections and multiplexes Lambda requests over them.
- Proxy also reduces failover time from 60-120 seconds to ~30 seconds.
- Integrate with Secrets Manager for credential management and IAM authentication.

**Alternative**: If RDS Proxy is not suitable, implement connection reuse within Lambda by declaring the connection outside the handler function (reused across warm invocations within the same execution environment).

---

## Q8: How do you calculate the optimal connection pool size for a database?

The PostgreSQL wiki recommends this formula:

```text
Optimal Pool Size = (Core Count × 2) + Effective Spindle Count

Example:
  4 vCPU instance with SSD storage (1 spindle equivalent):
  Pool Size = (4 × 2) + 1 = 9 connections
```

**Key Principle**: More connections does NOT mean better performance. Each connection consumes memory (~10 MB per connection in PostgreSQL). Excessive connections cause context switching overhead, actually degrading throughput.

**Production Configuration:**
- Application pool (e.g., HikariCP): Set `maximumPoolSize` to the formula above per application pod.
- Total connections: Ensure `(pods × pool_size_per_pod) < max_connections` on the database.
- Set `idle_timeout` to 10 minutes to release unused connections.
- Monitor `DatabaseConnections` in CloudWatch; alert at 80% of `max_connections`.

---

# Consistency and Transactions

## Q9: How do you implement distributed transactions across microservices that each have their own database?

Traditional ACID transactions cannot span multiple independent databases. In a microservices architecture, you have several options:

**Option 1: Saga Pattern (Recommended)**

A Saga is a sequence of local transactions where each step triggers the next via events. If a step fails, compensating transactions undo the previous steps.

```text
Order Service              Payment Service           Inventory Service
     │                          │                         │
     ├── Create Order (local) ──►                         │
     │                          ├── Charge Card (local) ──►
     │                          │                         ├── Reserve Stock (local)
     │                          │                         │
     │              If Payment Fails:                     │
     │                          ├── Refund Card ──────────►
     │   ◄── Cancel Order ──────┤                         ├── Release Stock
```

**Option 2: Outbox Pattern**

Write the event and the database change in a single local transaction. A separate process reads the outbox table and publishes events to SQS/SNS/EventBridge.

**Option 3: Two-Phase Commit (2PC)** — Generally avoided in microservices due to blocking behavior and tight coupling.

---

## Q10: Explain the difference between optimistic and pessimistic locking. When do you use each?

**Pessimistic Locking**: Lock the row/resource before reading it. Other transactions are blocked until the lock is released.

```sql
-- Pessimistic: Acquire lock immediately
SELECT * FROM inventory WHERE product_id = 101 FOR UPDATE;
-- Row is locked. Other transactions wait.
UPDATE inventory SET quantity = quantity - 1 WHERE product_id = 101;
COMMIT;
-- Lock released.
```

**Optimistic Locking**: Don't lock anything. Read the data with a version number. On write, check if the version has changed. If it has, another transaction modified the data — retry.

```sql
-- Optimistic: Read with version
SELECT quantity, version FROM inventory WHERE product_id = 101;
-- Returns: quantity=50, version=3

-- Update only if version hasn't changed
UPDATE inventory SET quantity = 49, version = 4
WHERE product_id = 101 AND version = 3;
-- If 0 rows affected → conflict detected → retry
```

| Aspect | Pessimistic | Optimistic |
|--------|-------------|------------|
| **Locking** | Immediate, blocks others | No lock, version check on write |
| **Contention** | Good for high contention (many writers) | Good for low contention (rare conflicts) |
| **Deadlock Risk** | Higher | None |
| **Performance** | Lower throughput (blocking) | Higher throughput (no blocking) |
| **DynamoDB** | Not supported (no row locks) | Native support (conditional writes) |

---

# Key Takeaways

- Split-brain is prevented by centralized failover control (RDS) or storage quorum (Aurora).
- Shard only after exhausting vertical scaling, read replicas, and caching. Shard key selection is irreversible.
- DynamoDB hot partitions are caused by low-cardinality partition keys. Use high-cardinality keys or write sharding.
- Use RDS Proxy to solve Lambda connection exhaustion. More connections ≠ better performance.
- Use the Saga pattern for distributed transactions across microservices. Avoid 2PC.
- Choose optimistic locking for low-contention workloads, pessimistic for high-contention.

---
