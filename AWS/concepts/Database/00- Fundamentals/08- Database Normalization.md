# Database Normalization

Normalization is the process of structuring a relational database to eliminate redundancy and prevent update anomalies. Every production schema starts messy. Normalization gives you a systematic method to decompose it into well-structured tables where each fact is stored exactly once. This guide walks through each normal form with concrete before/after examples, then shows when to stop.

---

## Why Normalize?

Unnormalized data causes three categories of anomalies:

| Anomaly Type   | What Happens                                                        | Example                                              |
|----------------|---------------------------------------------------------------------|------------------------------------------------------|
| **Insert**     | Cannot add data without unrelated data existing                     | Cannot add a new product category without an order    |
| **Update**     | Changing one fact requires updating multiple rows                   | Updating a customer address in 500 order rows         |
| **Delete**     | Removing a row accidentally destroys unrelated data                 | Deleting the last order for a customer loses their address |

Normalization eliminates these anomalies by decomposing tables so that each non-key attribute depends on **the key, the whole key, and nothing but the key**.

---

## First Normal Form (1NF)

**Rule:** Every column contains atomic (indivisible) values. No repeating groups or arrays.

### Before (Violates 1NF)

```
┌──────────┬────────────┬──────────────────────────┐
│ order_id │ customer   │ products                 │
├──────────┼────────────┼──────────────────────────┤
│ 101      │ Alice      │ Widget, Gadget, Sprocket │
│ 102      │ Bob        │ Gadget                   │
│ 103      │ Alice      │ Widget, Bolt             │
└──────────┴────────────┴──────────────────────────┘
```

The `products` column contains comma-separated values — not atomic. You cannot query "find all orders containing Gadget" without string parsing.

### After (1NF)

```
┌──────────┬────────────┬──────────┐
│ order_id │ customer   │ product  │
├──────────┼────────────┼──────────┤
│ 101      │ Alice      │ Widget   │
│ 101      │ Alice      │ Gadget   │
│ 101      │ Alice      │ Sprocket │
│ 102      │ Bob        │ Gadget   │
│ 103      │ Alice      │ Widget   │
│ 103      │ Alice      │ Bolt     │
└──────────┴────────────┴──────────┘

Primary Key: (order_id, product)
```

Each row now holds one product per order. Queries become straightforward `WHERE product = 'Gadget'`.

---

## Second Normal Form (2NF)

**Rule:** Must be in 1NF, and every non-key attribute must depend on the **entire** composite primary key — no partial dependencies.

2NF only applies when the primary key is composite. If your PK is a single column, you are already in 2NF once you achieve 1NF.

### Before (Violates 2NF)

```
┌──────────┬────────────┬──────────┬─────────────┬───────┐
│ order_id │ product_id │ product  │ unit_price  │ qty   │
├──────────┼────────────┼──────────┼─────────────┼───────┤
│ 101      │ P1         │ Widget   │ 25.00       │ 3     │
│ 101      │ P2         │ Gadget   │ 40.00       │ 1     │
│ 102      │ P2         │ Gadget   │ 40.00       │ 5     │
└──────────┴────────────┴──────────┴─────────────┴───────┘

PK: (order_id, product_id)
```

`product_name` and `unit_price` depend only on `product_id`, not on the full key `(order_id, product_id)`. This is a **partial dependency**.

**Problem:** If Gadget's price changes, you must update every row containing `P2`.

### After (2NF)

```
orders_items                        products
┌──────────┬────────────┬───────┐  ┌────────────┬──────────┬─────────────┐
│ order_id │ product_id │ qty   │  │ product_id │ product  │ unit_price  │
├──────────┼────────────┼───────┤  ├────────────┼──────────┼─────────────┤
│ 101      │ P1         │ 3     │  │ P1         │ Widget   │ 25.00       │
│ 101      │ P2         │ 1     │  │ P2         │ Gadget   │ 40.00       │
│ 102      │ P2         │ 5     │  └────────────┴──────────┴─────────────┘
└──────────┴────────────┴───────┘
```

Now `product_name` and `unit_price` live in the `products` table and depend on the full key of that table (`product_id`). Updating a price is a single-row update.

---

## Third Normal Form (3NF)

**Rule:** Must be in 2NF, and no non-key attribute depends on another non-key attribute — no transitive dependencies.

### Before (Violates 3NF)

```
┌──────────┬────────────┬───────────────┬─────────────────┐
│ order_id │ customer_id│ customer_name │ customer_city   │
├──────────┼────────────┼───────────────┼─────────────────┤
│ 101      │ C1         │ Alice         │ Seattle         │
│ 102      │ C2         │ Bob           │ Portland        │
│ 103      │ C1         │ Alice         │ Seattle         │
└──────────┴────────────┴───────────────┴─────────────────┘

PK: order_id
```

`customer_name` and `customer_city` depend on `customer_id`, which is not the primary key. This creates a **transitive dependency**: `order_id → customer_id → customer_name`.

**Problem:** Alice moves from Seattle to Denver. You must update every order row for customer C1.

### After (3NF)

```
orders                              customers
┌──────────┬────────────┐          ┌─────────────┬───────────────┬─────────────────┐
│ order_id │ customer_id│          │ customer_id │ customer_name │ customer_city   │
├──────────┼────────────┤          ├─────────────┼───────────────┼─────────────────┤
│ 101      │ C1         │          │ C1          │ Alice         │ Seattle         │
│ 102      │ C2         │          │ C2          │ Bob           │ Portland        │
│ 103      │ C1         │          └─────────────┴───────────────┴─────────────────┘
└──────────┴────────────┘
```

Customer data is stored once. Address updates are single-row operations.

---

## Boyce-Codd Normal Form (BCNF)

**Rule:** Must be in 3NF, and every determinant must be a candidate key.

BCNF handles a rare edge case where a non-candidate-key attribute determines part of a candidate key. In practice, most 3NF schemas are already in BCNF.

### Example (Violates BCNF)

```
┌────────────┬────────────┬─────────────┐
│ student    │ subject    │ professor   │
├────────────┼────────────┼─────────────┤
│ Alice      │ Math       │ Dr. Smith   │
│ Bob        │ Math       │ Dr. Smith   │
│ Alice      │ Physics    │ Dr. Jones   │
│ Carol      │ Math       │ Dr. Lee     │
└────────────┴────────────┴─────────────┘

Candidate Key: (student, subject)
Dependency: professor → subject (each professor teaches exactly one subject)
```

`professor → subject` means professor determines subject, but professor is not a candidate key. This violates BCNF.

### After (BCNF)

```
enrollments                      professor_subjects
┌────────────┬─────────────┐    ┌─────────────┬────────────┐
│ student    │ professor   │    │ professor   │ subject    │
├────────────┼─────────────┤    ├─────────────┼────────────┤
│ Alice      │ Dr. Smith   │    │ Dr. Smith   │ Math       │
│ Bob        │ Dr. Smith   │    │ Dr. Jones   │ Physics    │
│ Alice      │ Dr. Jones   │    │ Dr. Lee     │ Math       │
│ Carol      │ Dr. Lee     │    └─────────────┴────────────┘
└────────────┴─────────────┘
```

---

## Dependency Elimination — Visual Summary

```
  Unnormalized Data
  ┌─────────────────────────────────────────────────────┐
  │ order_id, products[], customer, city, product_price │
  └──────────────────────┬──────────────────────────────┘
                         │
                    ┌────┴────┐
                    │  1NF    │  Eliminate repeating groups
                    └────┬────┘  (one fact per cell)
                         │
              ┌──────────┴──────────┐
              │                     │
        ┌─────┴─────┐        ┌─────┴─────┐
        │ orders    │        │ order_    │
        │           │        │ items     │
        └─────┬─────┘        └─────┬─────┘
              │                    │
         ┌────┴────┐          ┌────┴────┐
         │  2NF    │          │  2NF    │  Remove partial deps
         └────┬────┘          └────┬────┘  (split by full key)
              │                    │
              │              ┌─────┴─────┐
              │              │ products  │
              │              └───────────┘
         ┌────┴────┐
         │  3NF    │  Remove transitive deps
         └────┬────┘  (extract non-key dependencies)
              │
        ┌─────┴─────┐
        │ customers │
        └───────────┘
```

---

## Real-World Example: E-Commerce Schema Normalization

### Starting Point — Flat Table

```
┌──────────┬──────────┬──────────┬───────────┬──────────┬───────┬───────────┬──────────────┬───────────┐
│ order_id │ date     │ cust_id  │ cust_name │ cust_email│ sku   │ prod_name │ unit_price   │ qty       │
├──────────┼──────────┼──────────┼───────────┼──────────┼───────┼───────────┼──────────────┼───────────┤
│ 5001     │ 2025-01-15│ 42      │ Alice     │ a@x.com  │ SKU-A │ Keyboard  │ 79.99        │ 2         │
│ 5001     │ 2025-01-15│ 42      │ Alice     │ a@x.com  │ SKU-B │ Mouse     │ 29.99        │ 1         │
│ 5002     │ 2025-01-16│ 87      │ Bob       │ b@y.com  │ SKU-A │ Keyboard  │ 79.99        │ 1         │
└──────────┴──────────┴──────────┴───────────┴──────────┴───────┴───────────┴──────────────┴───────────┘
```

### Normalized Schema (3NF)

```sql
-- Customers table (eliminates transitive dependency)
CREATE TABLE customers (
    customer_id   INT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE
);

-- Products table (eliminates partial dependency)
CREATE TABLE products (
    sku         VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    unit_price   DECIMAL(10,2) NOT NULL
);

-- Orders table (master record)
CREATE TABLE orders (
    order_id    INT PRIMARY KEY,
    order_date  DATE NOT NULL,
    customer_id INT NOT NULL REFERENCES customers(customer_id)
);

-- Order items (junction table, full composite key dependency)
CREATE TABLE order_items (
    order_id   INT NOT NULL REFERENCES orders(order_id),
    sku        VARCHAR(20) NOT NULL REFERENCES products(sku),
    quantity   INT NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (order_id, sku)
);
```

**Result:** Customer data stored once. Product data stored once. Price changes are single-row updates. Deleting an order does not lose customer information.

---

## When to Stop Normalizing

Normalization beyond 3NF rarely provides practical benefits in production systems. Here is the decision framework:

| Normal Form | When to Apply                                                  | Practical Benefit           |
|-------------|----------------------------------------------------------------|-----------------------------|
| 1NF         | Always                                                         | Queryable, indexable data   |
| 2NF         | Always (automatic with surrogate PKs)                          | No partial redundancy       |
| 3NF         | Almost always                                                  | Single source of truth      |
| BCNF        | Only when 3NF leaves specific anomalies                        | Marginal                    |
| 4NF/5NF     | Academic interest only for most applications                   | Negligible in practice      |

**Stop at 3NF** for OLTP workloads. If your read patterns require frequent multi-table joins, consider strategic denormalization (covered in the next guide) — but start normalized and denormalize with intention, not by default.

**Production guidance:**

- Use surrogate primary keys (`SERIAL`, `BIGSERIAL`, `UUID`) — they naturally prevent 2NF violations since the PK is a single column.
- Snapshot data at transaction time when business logic requires it. For example, store the price at the time of purchase in `order_items.line_price` even though `products.unit_price` exists. This is not denormalization — it is recording a historical fact.
- Foreign keys enforce referential integrity but add overhead on write-heavy tables. In high-throughput systems (>10K writes/sec), consider enforcing integrity at the application layer and auditing periodically.

---

## Common Mistakes

1. **Storing computed values without a source of truth** — keeping a `total_amount` column that is never recalculated from line items. When items change, the total becomes stale. If you store aggregates, use triggers or materialized views to keep them consistent.
2. **Using comma-separated values instead of junction tables** — this violates 1NF and makes queries impossible to index. Always use a proper many-to-many join table.
3. **Over-normalizing reference data** — splitting a `status` enum into a separate lookup table with 5 rows adds a JOIN to every query for no meaningful benefit. Use `CHECK` constraints or PostgreSQL enum types for small, stable value sets.
4. **Confusing historical snapshots with redundancy** — storing the shipping address on an order is not denormalization. The customer may move, but the order was shipped to that specific address. This is a business fact, not a copy of mutable data.

---

## Interview Questions

**Q1: Explain the difference between 2NF and 3NF with an example.**

2NF eliminates partial dependencies — where a non-key attribute depends on only part of a composite primary key. 3NF eliminates transitive dependencies — where a non-key attribute depends on another non-key attribute. Example: In a table with PK `(order_id, product_id)`, if `product_name` depends only on `product_id`, that is a 2NF violation (partial dependency). If `customer_city` depends on `customer_id` which depends on `order_id`, that is a 3NF violation (transitive dependency).

**Q2: Your e-commerce orders table has 200 million rows and requires a 6-table JOIN to render an order summary. How do you handle this?**

Start by verifying that all JOIN columns are indexed and statistics are current (`ANALYZE`). If the JOIN is inherently expensive due to data volume, create a materialized view that precomputes the order summary and refresh it on a schedule (or use triggers for near-real-time). For the API layer, consider a denormalized read model (CQRS pattern) stored in a separate table or cache. The normalized source tables remain the source of truth for writes.

**Q3: Is storing a product price in the order_items table a normalization violation?**

No. The price at the time of purchase is a distinct business fact from the current product price. Products may change prices after the order is placed. The `order_items.line_price` captures the agreed-upon price at transaction time. This is a historical snapshot, not data redundancy.

---

## Key Takeaways

- **Normalization eliminates redundancy** by ensuring each fact is stored exactly once, preventing insert, update, and delete anomalies.
- **1NF = atomic values**, 2NF = no partial key dependencies, 3NF = no transitive dependencies. Memorize this progression.
- **Stop at 3NF for OLTP** — going beyond 3NF rarely provides meaningful production benefits and increases query complexity.
- **Surrogate keys simplify normalization** — single-column primary keys automatically satisfy 2NF, eliminating partial dependency concerns.
- **Historical snapshots are not denormalization** — storing the price at order time, the shipping address at delivery time, or the username at audit time records business facts.
- **Start normalized, denormalize intentionally** — it is far easier to combine normalized tables into read-optimized views than to decompose a denormalized mess into a correct schema.
