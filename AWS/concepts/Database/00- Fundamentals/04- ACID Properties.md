# ACID Properties

ACID is the contract a relational database makes with you: every transaction will be **Atomic**, **Consistent**, **Isolated**, and **Durable**. These four properties are what separate a real database from a file with aspirations. If your system handles money, inventory, medical records, or anything where a wrong answer has consequences, ACID is non-negotiable.

Understanding ACID is not optional. Misunderstanding isolation levels alone has caused more production outages and data corruption incidents than any other database concept.

---

## Atomicity

A transaction is all-or-nothing. Every operation in the transaction either completes successfully, or none of them do. There is no partial state.

### The Banking Example

```
  ┌────────────────────────────────────────────────┐
  │          TRANSFER $500: Account A → B          │
  │                                                │
  │   BEGIN TRANSACTION                            │
  │   ├── Step 1: Debit A by $500                  │
  │   │           A: $1000 → $500    ✓             │
  │   ├── Step 2: Credit B by $500                 │
  │   │           B: $2000 → $2500   ✓             │
  │   COMMIT ─────────────────── Both applied      │
  │                                                │
  │   ── FAILURE SCENARIO ──                       │
  │                                                │
  │   BEGIN TRANSACTION                            │
  │   ├── Step 1: Debit A by $500                  │
  │   │           A: $1000 → $500    ✓             │
  │   ├── Step 2: Credit B by $500                 │
  │   │           ❌ CRASH / ERROR                  │
  │   ROLLBACK ──────────────── Both reverted      │
  │           A: $500 → $1000   (restored)         │
  │                                                │
  │   Money is neither created nor destroyed.      │
  └────────────────────────────────────────────────┘
```

Without atomicity, a crash between Step 1 and Step 2 means $500 vanishes. The customer's account is debited, but the recipient never gets the funds. Atomicity guarantees that if any step fails, the entire transaction is rolled back to its pre-transaction state.

**How databases implement atomicity:**

- **Undo Logs (Rollback Segments):** Before modifying data, the database writes the original values to an undo log. If the transaction aborts, the undo log is replayed to restore the original state.
- **Write-Ahead Logging (WAL):** Changes are written to a sequential log before being applied to data pages. On crash recovery, incomplete transactions found in the log are rolled back.

---

## Consistency

A transaction brings the database from one valid state to another. All data integrity constraints — primary keys, foreign keys, unique constraints, check constraints, triggers — are enforced at the boundary of the transaction.

Consistency in ACID is **different** from consistency in CAP. ACID consistency means the database enforces its own rules. CAP consistency means all nodes see the same data at the same time.

### What Consistency Enforces

| Constraint Type | Example | Violation Behavior |
|---|---|---|
| Primary Key | `user_id` must be unique | INSERT rejected with duplicate key error |
| Foreign Key | `order.user_id` references `users.id` | INSERT rejected if referenced user does not exist |
| NOT NULL | `email` column cannot be NULL | INSERT/UPDATE rejected |
| CHECK | `balance >= 0` | UPDATE rejected if balance goes negative |
| Unique Index | `email` must be unique across table | INSERT rejected with duplicate error |
| Trigger | After INSERT, update audit log | Trigger runs within same transaction |

If any constraint is violated, the entire transaction is aborted. The database never enters an invalid state.

**Production note:** Many teams disable foreign keys in high-write systems for performance. This moves the consistency burden to your application code. If your application has bugs (it does), you now have orphaned records. Choose this tradeoff deliberately, not accidentally.

---

## Isolation

Isolation determines how concurrent transactions interact with each other. This is the most misunderstood ACID property and the source of the most production bugs.

The SQL standard defines four isolation levels, each permitting or preventing specific anomalies:

### The Three Anomalies

**Dirty Read:** Transaction A reads data written by Transaction B before B commits. If B rolls back, A has read data that never existed.

**Non-Repeatable Read:** Transaction A reads the same row twice and gets different values because Transaction B modified and committed the row between A's reads.

**Phantom Read:** Transaction A executes a query twice and gets different row sets because Transaction B inserted or deleted rows that match A's query between executions.

```
  ┌──────────────────────────────────────────────────┐
  │            ISOLATION ANOMALY EXAMPLES             │
  │                                                   │
  │   DIRTY READ:                                     │
  │   T1: BEGIN                                       │
  │   T2: BEGIN → UPDATE balance=500 (uncommitted)    │
  │   T1: SELECT balance → reads 500 (DIRTY!)        │
  │   T2: ROLLBACK → balance reverts to 1000          │
  │   T1: now has stale value 500                     │
  │                                                   │
  │   NON-REPEATABLE READ:                            │
  │   T1: SELECT balance → 1000                       │
  │   T2: UPDATE balance=500 → COMMIT                 │
  │   T1: SELECT balance → 500 (different!)           │
  │                                                   │
  │   PHANTOM READ:                                   │
  │   T1: SELECT COUNT(*) WHERE dept='eng' → 10       │
  │   T2: INSERT INTO employees(dept='eng') → COMMIT  │
  │   T1: SELECT COUNT(*) WHERE dept='eng' → 11       │
  └──────────────────────────────────────────────────┘
```

### Isolation Levels vs Anomalies

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Performance | Lock Behavior |
|---|---|---|---|---|---|
| **Read Uncommitted** | ❌ Possible | ❌ Possible | ❌ Possible | Fastest | No read locks |
| **Read Committed** | ✅ Prevented | ❌ Possible | ❌ Possible | Fast | Short read locks |
| **Repeatable Read** | ✅ Prevented | ✅ Prevented | ❌ Possible | Moderate | Held read locks |
| **Serializable** | ✅ Prevented | ✅ Prevented | ✅ Prevented | Slowest | Range locks / SSI |

### Level Details

**Read Uncommitted:** Almost never used in production. You can read data that another transaction has written but not committed. If that transaction rolls back, you have acted on phantom data. Only acceptable for rough analytics where precision does not matter.

**Read Committed:** The default for PostgreSQL and Oracle. Each query in a transaction sees only data committed before that query started. You will not read dirty data, but running the same query twice in a transaction may return different results if another transaction committed between your queries.

**Repeatable Read:** The default for MySQL/InnoDB. Once you read a row, re-reading it in the same transaction returns the same value, even if another transaction commits a change. InnoDB uses MVCC (Multi-Version Concurrency Control) to achieve this without heavy locking. Phantoms are still theoretically possible, though InnoDB's gap locks prevent most phantom cases in practice.

**Serializable:** The strongest level. Transactions behave as if they executed one at a time. PostgreSQL implements this via SSI (Serializable Snapshot Isolation), which detects conflicts and aborts one of the conflicting transactions. MySQL uses shared range locks. Performance impact is significant — expect higher abort rates and lower throughput.

---

## Durability

Once a transaction is committed, it stays committed — even if the server crashes, loses power, or catches fire. The data survives.

### Write-Ahead Logging (WAL)

WAL is the primary mechanism for durability. Before any data page is modified on disk, the change is first written to a sequential log file.

```
  ┌────────────────────────────────────────────────┐
  │              WAL CRASH RECOVERY                │
  │                                                │
  │   Normal Operation:                            │
  │   ┌──────┐    ┌──────────┐    ┌──────────┐    │
  │   │ App  │───▶│ WAL Log  │───▶│ Data     │    │
  │   │      │    │ (fsync)  │    │ Pages    │    │
  │   └──────┘    └──────────┘    └──────────┘    │
  │                    │                           │
  │                    ▼                           │
  │              ┌──────────┐                      │
  │              │ Durable  │                      │
  │              │ Storage  │                      │
  │              └──────────┘                      │
  │                                                │
  │   After Crash:                                 │
  │   1. Read WAL from last checkpoint             │
  │   2. REDO committed transactions               │
  │      (replay changes to data pages)            │
  │   3. UNDO uncommitted transactions             │
  │      (rollback incomplete changes)             │
  │   4. Database is consistent again              │
  └────────────────────────────────────────────────┘
```

**Checkpointing:** Periodically, the database flushes dirty pages from memory to disk and records a checkpoint in the WAL. During recovery, the database only needs to replay WAL entries after the last checkpoint, reducing recovery time.

**fsync and the Durability Lie:** When the database calls `fsync()`, the OS flushes the file's data from its buffer cache to the physical disk. If your storage controller has a volatile write cache and reports success before data reaches persistent media, your durability guarantee is broken. EBS volumes on AWS are replicated and designed to handle this correctly, but if you run databases on instance store (ephemeral) volumes, you are gambling.

---

## ACID on AWS: RDS and Aurora

### Amazon RDS (MySQL, PostgreSQL)

| ACID Property | Implementation |
|---|---|
| Atomicity | InnoDB undo logs (MySQL), PostgreSQL MVCC rollback |
| Consistency | Engine-level constraint enforcement. All standard SQL constraints supported. |
| Isolation | Configurable. MySQL default: Repeatable Read. PostgreSQL default: Read Committed. |
| Durability | WAL shipped to S3 every 5 minutes. Multi-AZ: synchronous replication to standby. Automated backups with point-in-time recovery. |

### Amazon Aurora

| ACID Property | Implementation |
|---|---|
| Atomicity | Log-structured distributed storage. Undo managed across 6 storage nodes. |
| Consistency | Full SQL constraint enforcement. Same as standard MySQL/PostgreSQL. |
| Isolation | MySQL-compatible: Repeatable Read default. PostgreSQL-compatible: Read Committed default. |
| Durability | 6-way replication across 3 AZs. 4/6 write quorum. Continuous backup to S3. Survives loss of an entire AZ + one additional node. |

**Aurora's key innovation:** The database only ships redo log records to storage nodes, not full data pages. This reduces network I/O by 7-8x compared to standard RDS. The storage nodes apply the redo log to reconstruct data pages independently.

---

## Common Mistakes

1. **Using the default isolation level without understanding it.** MySQL defaults to Repeatable Read. PostgreSQL defaults to Read Committed. If you migrated from one to the other without adjusting, your application's concurrency behavior changed, and you may not have noticed — yet.

2. **Long-running transactions under Serializable isolation.** Serializable tracks read/write dependencies. Long transactions accumulate more dependencies, increasing the probability of serialization failures. Your application must handle retries.

3. **Disabling fsync for performance.** Setting `fsync=off` in PostgreSQL makes writes faster by not flushing to disk. It also means a power failure can corrupt your database. Never do this in production.

4. **Assuming Repeatable Read prevents all anomalies.** It prevents dirty reads and non-repeatable reads but does not prevent phantom reads (per the SQL standard). MySQL's InnoDB gap locks mitigate this, but PostgreSQL's Repeatable Read does not use gap locks.

5. **Confusing ACID Consistency with CAP Consistency.** ACID consistency is about constraint enforcement within a single database. CAP consistency is about data agreement across distributed nodes. They are entirely different concepts that share a name.

---

## Real-World Production Scenario

**Multi-Step Order Processing on Aurora MySQL:**

```sql
BEGIN;
-- Atomicity: all-or-nothing
INSERT INTO orders (user_id, total) VALUES (42, 299.99);
SET @order_id = LAST_INSERT_ID();

-- Consistency: FK constraint ensures user exists
INSERT INTO order_items (order_id, product_id, qty, price)
VALUES (@order_id, 101, 1, 299.99);

-- Isolation: Repeatable Read ensures inventory check
-- is stable within this transaction
SELECT stock FROM products WHERE id = 101 FOR UPDATE;
-- FOR UPDATE acquires row-level lock, preventing concurrent
-- transactions from modifying this row

UPDATE products SET stock = stock - 1 WHERE id = 101;

-- Durability: once COMMIT returns, this is permanent
COMMIT;
```

The `FOR UPDATE` clause is critical. Without it, two concurrent transactions can both read `stock = 1`, both decrement it, and set `stock = 0` — selling two items when only one exists. `FOR UPDATE` acquires a row-level exclusive lock, forcing the second transaction to wait until the first commits or rolls back.

---

## Interview Questions

**Q1: A transaction transfers $100 from Account A to Account B. The debit succeeds but the credit fails. What happens, and which ACID property is responsible?**

Atomicity guarantees rollback. The debit to Account A is reverted using the undo log. The database returns to its pre-transaction state. No money is lost, no money is created. The application receives an error and can retry or report the failure.

**Q2: You are running PostgreSQL with the default isolation level (Read Committed). A report query counts active users, then counts their orders in a second query within the same transaction. Between the two queries, a user deletes their account. What happens?**

Under Read Committed, the second query sees the deletion because each statement sees a new snapshot. The report will show a user in the count but their orders may be missing (or the user may be missing from a join). This is a non-repeatable read. To prevent it, use Repeatable Read or Serializable isolation, which gives the entire transaction a consistent snapshot.

**Q3: Your team migrated from MySQL (InnoDB) to PostgreSQL. After migration, you observe phantom reads in a report that previously worked correctly. Why?**

MySQL InnoDB defaults to Repeatable Read and uses gap locks to prevent phantoms in most cases. PostgreSQL defaults to Read Committed, which allows both non-repeatable reads and phantoms. Even if you set PostgreSQL to Repeatable Read, PostgreSQL uses MVCC snapshots (not gap locks) and does not prevent phantoms in the same way InnoDB does. You need Serializable isolation in PostgreSQL to fully prevent phantoms, but must handle serialization failures in your application code.

**Q4: How does Aurora achieve durability across AZ failures?**

Aurora replicates every write to 6 storage nodes across 3 AZs (2 nodes per AZ). A write is acknowledged after 4 of 6 nodes confirm (write quorum). A read requires 3 of 6 nodes (read quorum). This means Aurora survives the loss of an entire AZ (2 nodes) plus one additional node failure — and still serves both reads and writes. Continuous backup to S3 enables point-in-time recovery to any second within the retention window.

---

## Key Takeaways

- **Atomicity is your safety net.** Without it, partial failures leave your database in states that no application logic can safely handle. Always use transactions for multi-step operations.
- **ACID Consistency ≠ CAP Consistency.** ACID consistency enforces schema constraints within one database. CAP consistency is about replication agreement across distributed nodes. Do not confuse them.
- **Isolation levels are a performance-correctness spectrum.** Read Uncommitted is fast but dangerous. Serializable is safe but slow. Know your default, know your anomalies, and choose deliberately.
- **Durability requires hardware cooperation.** WAL and fsync only work if the storage layer honors flush requests. Use EBS volumes with Multi-AZ replication on AWS — never instance store for databases.
- **`FOR UPDATE` is not optional for inventory-type problems.** Any read-then-write pattern on shared data requires explicit locking or optimistic concurrency control. Hoping for the best is not a concurrency strategy.
- **Aurora's 4/6 write quorum is the gold standard.** It provides durability across AZ failures without the latency penalty of synchronous cross-region replication.
