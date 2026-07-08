# Database Denormalization

Normalization gives you correctness. Denormalization gives you speed. Every production system eventually hits a point where normalized queries — joining 5 or 6 tables to render a single API response — become the bottleneck. Denormalization is the deliberate introduction of redundancy to optimize read performance. This guide covers the techniques, the trade-offs, and the decision framework for when to break the rules.

---

## Why Denormalize?

Normalized schemas store each fact once, which is optimal for write correctness but expensive for reads. Consider rendering a product page on an e-commerce site:

```sql
-- Normalized: 5 JOINs to render one product page
SELECT p.name, p.description, c.category_name, b.brand_name,
       AVG(r.rating), COUNT(r.id), i.quantity
FROM products p
JOIN categories c ON p.category_id = c.id
JOIN brands b ON p.brand_id = b.id
JOIN reviews r ON r.product_id = p.id
JOIN inventory i ON i.product_id = p.id
WHERE p.id = 12345
GROUP BY p.name, p.description, c.category_name, b.brand_name, i.quantity;
```

At 50K requests/second, those JOINs become a real problem. Denormalization collapses this into a single-table read.

**Core motivations:**

- **Eliminate JOINs** — reduce query complexity and latency
- **Pre-compute aggregates** — avoid real-time GROUP BY on millions of rows
- **Co-locate related data** — keep everything needed for a read path in one place
- **Support caching layers** — flat structures serialize and cache efficiently

---

## Denormalization Techniques

### 1. Duplicating Columns Across Tables

Store frequently-accessed foreign data directly in the referencing table.

```
  Normalized                          Denormalized
  ┌─────────────────┐                ┌──────────────────────────────┐
  │ orders          │                │ orders                       │
  │ ─────────────── │                │ ──────────────────────────── │
  │ order_id     PK │                │ order_id          PK         │
  │ customer_id  FK │──┐             │ customer_id       FK         │
  │ order_date      │  │             │ customer_name     (copied)   │
  └─────────────────┘  │             │ customer_email    (copied)   │
                       │             │ order_date                   │
  ┌─────────────────┐  │             └──────────────────────────────┘
  │ customers       │◄─┘
  │ ─────────────── │                Eliminates JOIN for order
  │ customer_id  PK │                listing queries
  │ customer_name   │
  │ customer_email  │
  └─────────────────┘
```

**Trade-off:** When a customer updates their name, you must update it in both `customers` and every row in `orders`. This is acceptable when customer name changes are rare but order listing queries happen millions of times per day.

### 2. Materialized Views

A materialized view is a query result stored as a physical table. PostgreSQL supports this natively.

```sql
CREATE MATERIALIZED VIEW mv_product_summary AS
SELECT
    p.id AS product_id,
    p.name,
    p.description,
    c.category_name,
    b.brand_name,
    COALESCE(AVG(r.rating), 0) AS avg_rating,
    COUNT(r.id) AS review_count,
    i.quantity AS stock_quantity
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN brands b ON p.brand_id = b.id
LEFT JOIN reviews r ON r.product_id = p.id
LEFT JOIN inventory i ON i.product_id = p.id
GROUP BY p.id, p.name, p.description, c.category_name, b.brand_name, i.quantity;

-- Refresh periodically (takes a lock on the view)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_product_summary;
```

**Production pattern:** Refresh materialized views on a schedule (every 5-15 minutes) or trigger a refresh after bulk data changes. Use `CONCURRENTLY` to avoid locking reads during refresh (requires a unique index on the view).

### 3. Precomputed Aggregates

Store computed values (counts, sums, averages) directly in the source table instead of calculating them on every read.

```sql
-- Add aggregate columns to products table
ALTER TABLE products ADD COLUMN review_count INT DEFAULT 0;
ALTER TABLE products ADD COLUMN avg_rating DECIMAL(3,2) DEFAULT 0;

-- Update via trigger on review insert/update/delete
CREATE OR REPLACE FUNCTION update_product_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products SET
        review_count = (SELECT COUNT(*) FROM reviews WHERE product_id = NEW.product_id),
        avg_rating = (SELECT COALESCE(AVG(rating), 0) FROM reviews WHERE product_id = NEW.product_id)
    WHERE id = NEW.product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Trade-off:** Triggers add latency to writes and can cause deadlocks under high concurrency. For non-critical aggregates, use a background job instead of triggers.

### 4. Embedding Related Data (Document Style)

Store related data as JSON within a relational column. This brings NoSQL patterns into PostgreSQL.

```sql
-- Instead of a separate reviews table for the read path
ALTER TABLE products ADD COLUMN recent_reviews JSONB DEFAULT '[]';

-- Periodically update with latest 5 reviews
UPDATE products SET recent_reviews = (
    SELECT jsonb_agg(row_to_json(r))
    FROM (
        SELECT author, rating, comment, created_at
        FROM reviews
        WHERE product_id = products.id
        ORDER BY created_at DESC
        LIMIT 5
    ) r
)
WHERE id IN (SELECT DISTINCT product_id FROM reviews WHERE created_at > NOW() - INTERVAL '1 day');
```

---

## Trade-Offs

| Factor              | Normalized                              | Denormalized                            |
|----------------------|-----------------------------------------|-----------------------------------------|
| Read performance     | Slower (multiple JOINs)                 | Faster (single table/document read)     |
| Write performance    | Faster (update one place)               | Slower (update multiple copies)         |
| Data consistency     | Guaranteed by structure                 | Must be enforced by application/triggers|
| Storage              | Minimal (no duplication)                | Higher (redundant copies)               |
| Schema flexibility   | Easy to evolve                          | Harder (changes propagate to copies)    |
| Query complexity     | Complex (many JOINs)                    | Simple (flat reads)                     |
| Update anomalies     | None                                    | Possible if sync logic fails            |

### Update Anomaly Example

```
  Denormalized orders table:
  ┌──────────┬─────────────┬────────────────┐
  │ order_id │ customer_id │ customer_name  │
  ├──────────┼─────────────┼────────────────┤
  │ 1001     │ 42          │ Alice Smith    │  ← Updated ✓
  │ 1002     │ 42          │ Alice Smith    │  ← Missed ✗ (still old name)
  │ 1003     │ 42          │ Alice Johnson  │  ← Source of truth
  └──────────┴─────────────┴────────────────┘

  Result: Inconsistent data. Order 1001 and 1002 show different names
  for the same customer. This is an update anomaly.
```

**Mitigation strategies:**

1. **Eventual consistency via background jobs** — a worker periodically syncs denormalized columns from the source table.
2. **Triggers** — database triggers propagate changes automatically but add write latency.
3. **Application-level dual writes** — the application updates both tables in the same transaction. Fragile but low-latency.
4. **Change Data Capture (CDC)** — tools like Debezium stream changes from the normalized source to denormalized targets asynchronously.

---

## When to Denormalize

Denormalize when you have evidence — not assumptions — that JOINs are the bottleneck.

```
  Decision Flow:
  ┌─────────────────────────┐
  │ Is the query slow?      │
  └────────┬────────────────┘
           │ Yes
  ┌────────▼────────────────┐
  │ Have you added proper   │
  │ indexes?                │──── No ──→ Add indexes first
  └────────┬────────────────┘
           │ Yes
  ┌────────▼────────────────┐
  │ Is the bottleneck       │
  │ JOINs / aggregation?    │──── No ──→ Optimize query / config
  └────────┬────────────────┘
           │ Yes
  ┌────────▼────────────────┐
  │ Can a materialized view │
  │ solve it?               │──── Yes ──→ Use materialized view
  └────────┬────────────────┘
           │ No (staleness unacceptable)
  ┌────────▼────────────────┐
  │ Denormalize with        │
  │ triggers / CDC / app    │
  │ logic                   │
  └─────────────────────────┘
```

### Scenarios Where Denormalization Wins

| Scenario                      | Technique                        | Example                                    |
|-------------------------------|----------------------------------|--------------------------------------------|
| **OLAP / Analytics**          | Star/snowflake schema            | Data warehouse fact tables with dimensions  |
| **Read-heavy APIs**           | Precomputed read models          | Product catalog API serving 50K RPS         |
| **Dashboard aggregates**      | Materialized views               | Real-time sales dashboard with SUM/AVG      |
| **Search / feed rendering**   | Embedded documents               | Social media feed with user + post data     |
| **Caching layers**            | Flat JSON documents              | Redis cache populated from denormalized view|

---

## NoSQL Databases Are Inherently Denormalized

NoSQL databases (DynamoDB, MongoDB, Cassandra) are designed around denormalized data models. There are no JOINs — you model your data around your access patterns.

```
  Relational (Normalized)              DynamoDB (Denormalized)
  ┌──────────────┐                    ┌──────────────────────────────────┐
  │ users        │                    │ PK: USER#42                      │
  │ orders    ───┤──JOIN──┐           │ SK: ORDER#5001                   │
  │ order_items──┤──JOIN──┤           │ {                                │
  │ products  ───┤──JOIN──┘           │   customer_name: "Alice",        │
  └──────────────┘                    │   order_date: "2025-01-15",      │
  4 tables, 3 JOINs                   │   items: [                       │
                                      │     {sku: "SKU-A", name: "KB"},  │
                                      │     {sku: "SKU-B", name: "Mouse"}│
                                      │   ],                             │
                                      │   total: 189.97                  │
                                      │ }                                │
                                      └──────────────────────────────────┘
                                      1 item, 0 JOINs
```

**DynamoDB design principle:** Design your table around your queries, not your entities. Each item should contain everything needed to answer a specific query. This often means storing the same data (e.g., customer name) in multiple items across different access patterns.

---

## Real-World Example: Product Catalog with Embedded Reviews

### Problem

An e-commerce product API serves 50K RPS. Each product page shows product details, category, brand, average rating, review count, and the 3 most recent reviews. The normalized query joins 4 tables and takes 12ms average — too slow at scale.

### Solution: Denormalized Read Table

```sql
CREATE TABLE product_catalog_read (
    product_id      INT PRIMARY KEY,
    product_name    VARCHAR(200),
    description     TEXT,
    category_name   VARCHAR(100),
    brand_name      VARCHAR(100),
    unit_price      DECIMAL(10,2),
    avg_rating      DECIMAL(3,2),
    review_count    INT,
    recent_reviews  JSONB,       -- Latest 3 reviews embedded
    stock_quantity  INT,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index for common access patterns
CREATE INDEX idx_catalog_category ON product_catalog_read (category_name);
CREATE INDEX idx_catalog_brand ON product_catalog_read (brand_name);
```

### Sync Strategy

```
  Source of Truth (Normalized)           Read Model (Denormalized)
  ┌──────────┐ ┌──────────┐            ┌──────────────────────┐
  │ products │ │ reviews  │            │ product_catalog_read │
  │          │ │          │──── CDC ──→│                      │
  │          │ │          │  (Debezium) │ Single table with    │
  └──────────┘ └──────────┘            │ all data embedded    │
  ┌──────────┐ ┌──────────┐            └──────────────────────┘
  │categories│ │ brands   │
  │          │ │          │──── CDC ──→  Refresh on change
  └──────────┘ └──────────┘
```

**Result:** Product page query drops from 12ms (4-table JOIN) to 0.8ms (single primary key lookup). Consistency lag is <2 seconds via CDC.

---

## Normalization vs Denormalization — Comparison Table

| Criteria                  | Normalization                              | Denormalization                            |
|---------------------------|--------------------------------------------|--------------------------------------------|
| **Goal**                  | Eliminate redundancy                       | Optimize read performance                  |
| **Data integrity**        | Structurally enforced                      | Application/trigger enforced               |
| **Write performance**     | Fast (single update point)                 | Slow (multiple copies to update)           |
| **Read performance**      | Slow for complex queries                   | Fast (pre-joined, pre-aggregated)          |
| **Storage efficiency**    | Minimal                                    | Higher due to duplication                  |
| **Schema evolution**      | Easier (change in one place)               | Harder (changes cascade to copies)         |
| **Best for**              | OLTP, financial systems, source of truth   | OLAP, APIs, dashboards, search             |
| **Consistency model**     | Strong consistency                         | Eventual consistency (usually acceptable)  |
| **Maintenance overhead**  | Low                                        | Higher (sync jobs, triggers, monitoring)   |
| **Database type**         | Relational (PostgreSQL, MySQL)             | NoSQL (DynamoDB, MongoDB) or read replicas |

---

## Common Mistakes

1. **Denormalizing before measuring** — many teams denormalize preemptively based on assumptions. Always profile with `EXPLAIN ANALYZE` first. A missing index is cheaper than a denormalization layer.
2. **No sync mechanism** — duplicating data without a reliable propagation strategy (triggers, CDC, background jobs) guarantees stale and inconsistent data.
3. **Denormalizing the write path** — denormalization optimizes reads. If you denormalize tables that are primarily written to, you get the worst of both worlds: slow writes AND consistency risks.
4. **Treating denormalized tables as source of truth** — the normalized schema must remain the authoritative source. Denormalized tables are derivative and rebuildable. If you lose the denormalized table, you can reconstruct it from the normalized source.
5. **Ignoring staleness requirements** — a 15-minute refresh interval for a materialized view is fine for a dashboard but unacceptable for an account balance display. Match your refresh strategy to your consistency requirements.

---

## Interview Questions

**Q1: Your API response time increased from 5ms to 200ms after the user base grew 10x. The bottleneck is a 6-table JOIN. How do you approach this?**

First, verify indexes are optimal on all JOIN columns and run `EXPLAIN ANALYZE`. If JOINs are genuinely the bottleneck (not missing indexes or stale statistics), create a denormalized read model — either a materialized view refreshed periodically, or a dedicated read table populated via CDC. Keep the normalized schema for writes. This is the CQRS pattern: separate read and write models. For the API, read from the denormalized table; for admin operations, write to the normalized tables.

**Q2: How would you keep a denormalized table in sync with its source tables?**

Three approaches in increasing reliability: (1) Application-level dual writes — update both tables in the same database transaction. Simple but tightly couples code and breaks if any write path is missed. (2) Database triggers — automatically propagate changes. Reliable within the database but adds write latency and can cause deadlocks. (3) Change Data Capture (CDC) using tools like Debezium — streams WAL changes to consumers that update the denormalized table. Decoupled, scalable, and handles all write paths, but introduces a consistency lag of seconds.

**Q3: When would you choose a materialized view over a denormalized table?**

A materialized view when: the query logic is complex and changes frequently (easier to modify a view definition than a sync pipeline), staleness of 5-15 minutes is acceptable, and the dataset fits comfortably in a single refresh cycle. A denormalized table when: you need near-real-time consistency (seconds), you need to add custom indexes not available on a materialized view, or you need the data in a different database or service entirely (cross-service denormalization).

---

## Key Takeaways

- **Denormalization is a read optimization** — never denormalize your write path. Keep normalized tables as the source of truth and derive denormalized read models from them.
- **Always have a sync strategy** — CDC (Debezium), triggers, or scheduled batch jobs. Without one, denormalized data becomes stale and untrustworthy.
- **Materialized views are your first tool** — they are the least invasive form of denormalization in PostgreSQL. Start there before building custom sync pipelines.
- **NoSQL databases require you to think denormalized from day one** — model your data around access patterns, not entity relationships. DynamoDB single-table design is denormalization taken to its logical conclusion.
- **Measure before you denormalize** — use `EXPLAIN ANALYZE`, `pg_stat_statements`, and RDS Performance Insights to confirm that JOINs are the actual bottleneck, not missing indexes or misconfigured memory.
- **Match staleness tolerance to business requirements** — a product catalog can tolerate 5 minutes of lag. An account balance cannot. Your denormalization strategy must reflect this.
