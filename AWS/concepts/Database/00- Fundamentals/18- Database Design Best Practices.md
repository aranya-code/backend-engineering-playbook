# Database Design Best Practices

Good database design is invisible. Bad database design surfaces as mysterious bugs, performance cliffs, migration nightmares, and 3 AM pages. The decisions you make in the first week of a project — data types, constraints, naming conventions, migration strategy — determine whether the system is maintainable at scale or a liability that slows every feature.

---

## Schema Design Principles

### Use Appropriate Data Types

Every column should use the smallest data type that correctly represents the domain.

| Use This | Not This | Why |
|----------|----------|-----|
| `BOOLEAN` | `VARCHAR(5)` storing `"true"/"false"` | 1 byte vs 5+ bytes, enforced at the type level |
| `TIMESTAMPTZ` | `TIMESTAMP` | Always store timezone-aware timestamps — ambiguous timestamps cause cross-timezone bugs |
| `NUMERIC(10,2)` | `FLOAT` | Floating-point arithmetic produces rounding errors on financial data |
| `INET` | `VARCHAR(45)` | Validates IP format, supports range queries, uses less storage |
| `UUID` | `VARCHAR(36)` | 16 bytes vs 37 bytes, native comparison operators |
| `SMALLINT` | `INTEGER` | If the domain is 0-65K (e.g., age, port number), 2 bytes vs 4 bytes |

### Avoid Implicit Type Casting

```sql
-- Bad: implicit cast from VARCHAR to INTEGER on every row
SELECT * FROM orders WHERE order_id = '12345';

-- Good: match the column type
SELECT * FROM orders WHERE order_id = 12345;
```

Implicit casts can silently prevent index usage. The planner may not be able to use an integer index when the filter value is a string.

### UUID vs Auto-Increment for Primary Keys

| Aspect | Auto-Increment (SERIAL/BIGSERIAL) | UUID (uuid_generate_v4 / gen_random_uuid) |
|--------|-----------------------------------|------------------------------------------|
| Size | 4-8 bytes | 16 bytes |
| Ordering | Sequential (insertion order) | Random |
| Index performance | Excellent (B-tree appends) | Good (random inserts cause page splits) |
| Distributed safety | Conflicts across shards/replicas | Globally unique without coordination |
| Information leakage | Exposes record count and creation order | Opaque — no inference possible |

**Use auto-increment** for internal-only tables where sequential ordering helps performance and the ID is never exposed externally. **Use UUIDs** for distributed systems, public-facing APIs, and multi-region architectures where ID coordination is impractical.

For PostgreSQL, use `UUIDv7` (time-sorted UUID) when available — it provides UUID uniqueness with B-tree-friendly sequential ordering.

---

## Naming Conventions

Inconsistent naming creates cognitive load on every query and every code review. Pick a convention and enforce it.

**Recommended conventions:**

| Element | Convention | Example |
|---------|------------|---------|
| Tables | `snake_case`, singular | `user_account`, `order_item` |
| Columns | `snake_case`, descriptive | `created_at`, `email_address`, `is_active` |
| Primary keys | `id` or `<table>_id` | `user_account.id` |
| Foreign keys | `<referenced_table>_id` | `order_item.order_id` |
| Indexes | `idx_<table>_<columns>` | `idx_order_item_order_id` |
| Constraints | `chk_<table>_<description>` | `chk_order_item_quantity_positive` |
| Boolean columns | `is_`, `has_`, `can_` prefix | `is_verified`, `has_subscription` |
| Timestamp columns | `_at` suffix | `created_at`, `updated_at`, `deleted_at` |

**Avoid:**

- Abbreviations (`usr`, `qty`, `amt`) — they save typing but cost readability
- Reserved words as column names (`user`, `order`, `group`) — they require quoting everywhere
- Prefixing every column with the table name (`order_order_id`, `order_order_status`)

---

## Constraint Design

Constraints are the last line of defense for data integrity. Application-layer validation has bugs — database constraints do not.

### NOT NULL by Default

Make columns `NOT NULL` unless you have an explicit reason to allow nulls. NULL introduces three-valued logic, complicates queries (`IS NULL` vs `= NULL`), and creates subtle bugs in aggregations.

```sql
-- Explicit: every column has a defined NOT NULL or nullable intent
CREATE TABLE user_account (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    display_name    VARCHAR(100) NOT NULL,
    bio             TEXT,                          -- Nullable: genuinely optional
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### CHECK Constraints

Enforce domain rules at the database level.

```sql
ALTER TABLE order_item ADD CONSTRAINT chk_order_item_quantity_positive
    CHECK (quantity > 0);

ALTER TABLE order_item ADD CONSTRAINT chk_order_item_price_non_negative
    CHECK (unit_price >= 0);

ALTER TABLE user_account ADD CONSTRAINT chk_user_account_email_format
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
```

### Foreign Keys

Always define foreign keys. They prevent orphaned records and document relationships. Specify `ON DELETE` behavior explicitly:

- `CASCADE` — delete child when parent is deleted (e.g., order items when order is deleted)
- `RESTRICT` — prevent parent deletion if children exist (e.g., prevent user deletion if they have orders)
- `SET NULL` — set FK to null when parent is deleted (e.g., set `assigned_to` to null when employee is removed)

---

## Migration Strategies

### Forward-Only Migrations

Never write `DOWN` migrations for production databases. Rollback migrations are untested, dangerous under data changes, and create false confidence. Instead, write a new forward migration to undo changes.

### Zero-Downtime Migrations with Expand-Contract

The expand-contract pattern allows schema changes without application downtime. Every breaking change is split into backward-compatible steps.

```
  Expand-Contract Migration Pattern

  Phase 1: EXPAND (backward-compatible addition)
  ┌─────────────────────────────────────────────────┐
  │  App v1 (reads old column)                      │
  │  App v2 (reads old column, writes both columns) │
  │                                                 │
  │  Database: ADD new column (nullable)            │
  │  Database: Backfill new column from old column  │
  │  Database: ADD trigger to sync old → new        │
  └─────────────────────────────────────────────────┘
                        │
                        ▼
  Phase 2: MIGRATE (switch readers)
  ┌─────────────────────────────────────────────────┐
  │  App v3 (reads new column, writes both columns) │
  │                                                 │
  │  Verify: all reads use new column               │
  │  Verify: data consistency between columns       │
  └─────────────────────────────────────────────────┘
                        │
                        ▼
  Phase 3: CONTRACT (remove old column)
  ┌─────────────────────────────────────────────────┐
  │  App v4 (reads and writes only new column)      │
  │                                                 │
  │  Database: DROP old column                      │
  │  Database: DROP sync trigger                    │
  │  Database: ADD NOT NULL to new column            │
  └─────────────────────────────────────────────────┘
```

**Example: Renaming `email` to `email_address`**

```sql
-- Phase 1: Expand
ALTER TABLE user_account ADD COLUMN email_address VARCHAR(255);
UPDATE user_account SET email_address = email WHERE email_address IS NULL;
-- Deploy app v2 that writes to both columns

-- Phase 2: Migrate
-- Deploy app v3 that reads from email_address
-- Verify no queries reference the old 'email' column

-- Phase 3: Contract
ALTER TABLE user_account DROP COLUMN email;
ALTER TABLE user_account ALTER COLUMN email_address SET NOT NULL;
ALTER TABLE user_account ADD CONSTRAINT uq_user_account_email_address UNIQUE (email_address);
```

### Blue-Green Schema Changes

For large tables where `ALTER TABLE` locks are unacceptable:

1. Create a new table with the desired schema
2. Set up a trigger to replicate writes from old table to new table
3. Backfill historical data
4. Switch application reads to new table
5. Switch application writes to new table
6. Drop old table and trigger

Use `pg_repack` or `pg_squeeze` for online table rewrites without locks on PostgreSQL.

---

## Connection Management

### Pool Sizing

The optimal connection pool size is **not** "as many as possible." More connections means more context switching, more lock contention, and more memory pressure.

**Formula (per application instance):**

```
pool_size = (core_count * 2) + effective_spindle_count
```

For cloud databases on SSD: `pool_size = (vCPU * 2) + 1`

For a 4-vCPU RDS instance: `pool_size = (4 * 2) + 1 = 9` connections per application instance.

**Total connections budget:**

```
max_connections = pool_size_per_instance × number_of_instances + reserved_connections

Example:
  pool_size = 9
  app_instances = 10
  reserved (monitoring, admin, migrations) = 10
  max_connections = 9 × 10 + 10 = 100
```

If your calculation exceeds the RDS instance's `max_connections`, either scale up the instance or add a connection pooler (PgBouncer/RDS Proxy).

### Idle Timeout

Set `idle_in_transaction_session_timeout` to prevent abandoned transactions from holding locks:

```sql
-- Kill transactions idle for more than 30 seconds
ALTER DATABASE myapp SET idle_in_transaction_session_timeout = '30s';
```

Set application-side pool idle timeout to 5-10 minutes. Connections sitting idle consume server memory and count against `max_connections`.

---

## Monitoring from Day One

Do not add monitoring after the first outage. These five metrics must be dashboarded and alerted before your first production deployment.

### Essential Metrics and Alert Thresholds

| Metric | Source | Warning | Critical |
|--------|--------|---------|----------|
| **Slow queries** (> 1s) | `pg_stat_statements` / slow query log | > 10/min | > 50/min |
| **Active connections** | `pg_stat_activity` | > 70% of `max_connections` | > 85% |
| **Deadlocks** | `pg_stat_database.deadlocks` | Any occurrence | > 5/min |
| **Replication lag** | CloudWatch `ReplicaLag` | > 5s | > 30s |
| **Dead tuples ratio** | `pg_stat_user_tables` | > 20% of live tuples | > 40% |
| **Disk usage** | CloudWatch `FreeStorageSpace` | < 25% free | < 10% free |
| **CPU utilization** | CloudWatch | > 70% sustained | > 90% sustained |

### Deadlock Detection

Enable deadlock logging:

```
log_lock_waits = on
deadlock_timeout = 1s     -- default is 1s, adjust if needed
```

Monitor `pg_stat_database.deadlocks` — any non-zero value warrants investigation. Deadlocks indicate conflicting transaction ordering in application code.

### Connection Count Alerts

```sql
-- Current connection breakdown
SELECT state, count(*)
FROM pg_stat_activity
GROUP BY state;

-- Long-running queries (potential lock holders)
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
  AND state != 'idle';
```

---

## Common Mistakes

1. **Not using constraints.** Relying on application code for data integrity means every bug in every service that touches the database is a potential data corruption incident. The database is the last line of defense — use it.
2. **Running migrations during peak traffic.** `ALTER TABLE ... ADD COLUMN` with a `DEFAULT` value on PostgreSQL < 11 rewrites the entire table with an exclusive lock. Schedule schema changes during low-traffic windows or use expand-contract.
3. **Using `TEXT` for everything.** `TEXT` is convenient but prevents the database from enforcing length limits, allows garbage data, and makes storage estimation impossible.
4. **Ignoring connection pool sizing.** Setting `max_pool_size = 100` on every application instance connected to an RDS instance with `max_connections = 150` guarantees connection exhaustion.
5. **No monitoring until the first outage.** Slow query logs, connection counts, and disk usage alerts must exist before production launch — not after the postmortem.

---

## Interview Questions

**Q1: Your team is migrating from auto-increment integer IDs to UUIDs for a table with 500 million rows in production, with zero downtime. Describe your approach.**

Use the expand-contract pattern. Phase 1 (Expand): Add a `uuid` column with a default of `gen_random_uuid()`, backfill existing rows in batches (50K-100K per batch with `pg_sleep` between batches to avoid locking). Phase 2 (Migrate): Deploy application code that reads by UUID, update all foreign key references in dependent tables. Phase 3 (Contract): Drop the old integer ID column. This takes weeks for 500M rows — plan accordingly and run during low-traffic hours.

**Q2: A junior developer adds a migration that runs `ALTER TABLE orders ADD COLUMN discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0;` on a table with 200 million rows. What happens in PostgreSQL 10 vs PostgreSQL 14?**

In PostgreSQL 10, this acquires an `ACCESS EXCLUSIVE` lock and rewrites all 200M rows to set the default value — the table is completely locked for minutes to hours. In PostgreSQL 14 (and 11+), adding a column with a non-volatile `DEFAULT` is a metadata-only operation — it completes in milliseconds regardless of table size. The default value is stored in `pg_attribute` and applied on read.

**Q3: Your RDS PostgreSQL instance shows `max_connections = 200`, and your application has 30 instances each with a connection pool of 10. During a deployment, you see connection errors. What is happening?**

During rolling deployments, old and new application instances run simultaneously — briefly doubling the instance count to 60. Total connections: `60 × 10 = 600`, which exceeds `max_connections = 200`. Fix: reduce pool size per instance to `3` (giving `60 × 3 = 180`), or add RDS Proxy to multiplex connections, or increase `max_connections` (requires larger instance class).

---

## Key Takeaways

- **Use the strictest data types and constraints possible.** `VARCHAR(255)` is not a default — it is a decision. `NOT NULL` is not optional — it is the default. Constraints catch bugs that tests miss.
- **The expand-contract pattern is the only safe way to make breaking schema changes in production.** Never rename or remove a column in a single deployment.
- **Connection pool sizing is math, not guesswork.** Use the formula `(vCPU × 2) + 1` per instance and account for deployment surges.
- **Monitor slow queries, connection counts, deadlocks, and dead tuples from day one.** These four metrics predict every common database outage.
- **Forward-only migrations are a production best practice.** Down migrations are untested recovery code — write a new forward migration to undo changes instead.
- **Name things consistently and descriptively.** A well-named schema is self-documenting. `user_account.is_active` tells you everything; `ua.flag1` tells you nothing.
