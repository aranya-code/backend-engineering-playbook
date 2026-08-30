# 01- Arithmetic Operators

## Overview

Arithmetic operators perform numeric calculations directly inside SQL expressions. They are useful for computing derived values, applying quantities and rates, calculating totals, and expressing business logic close to the data.

Common arithmetic operators are:

| Operator | Operation | Example |
|---|---|---|
| `+` | Addition | `price + tax` |
| `-` | Subtraction | `stock - reserved` |
| `*` | Multiplication | `quantity * unit_price` |
| `/` | Division | `total / quantity` |
| `%` | Modulo / remainder | `quantity % 10` |

Arithmetic expressions can appear in `SELECT`, `WHERE`, `ORDER BY`, `HAVING`, `UPDATE`, and other SQL clauses where expressions are permitted.

```sql
SELECT
    product_id,
    quantity,
    unit_price,
    quantity * unit_price AS line_total
FROM order_items;
```

The database evaluates the expression for each qualifying row and returns the calculated value without requiring the application to perform the calculation.

## Why Arithmetic Operators Matter in Backend Systems

Arithmetic in SQL is particularly useful when the calculation is naturally data-oriented.

For example, an order service may store:

```text
quantity
unit_price
discount
tax
```

and calculate the final amount as part of the query:

```sql
SELECT
    id,
    quantity,
    unit_price,
    quantity * unit_price AS subtotal
FROM order_items;
```

This can reduce application-side processing and allows filtering or sorting based on derived values.

```sql
SELECT
    id,
    quantity,
    unit_price,
    quantity * unit_price AS subtotal
FROM order_items
WHERE quantity * unit_price >= 100
ORDER BY subtotal DESC;
```

For large datasets, however, whether an expression can use an index efficiently depends on the database, expression, schema, and query plan.

## Basic Arithmetic

### Addition

Addition uses `+`.

```sql
SELECT
    price,
    tax,
    price + tax AS total_price
FROM products;
```

Typical backend uses include:

- Adding monetary components.
- Combining counters.
- Calculating projected quantities.
- Adding intervals or numeric values where supported by the database.

### Subtraction

Subtraction uses `-`.

```sql
SELECT
    stock_quantity,
    reserved_quantity,
    stock_quantity - reserved_quantity AS available_quantity
FROM inventory;
```

This is common for derived inventory, balances, quotas, and remaining capacity.

### Multiplication

Multiplication uses `*`.

```sql
SELECT
    quantity,
    unit_price,
    quantity * unit_price AS line_total
FROM order_items;
```

Typical uses include:

- Quantity × price.
- Rate × duration.
- Capacity × allocation.
- Unit conversion.

### Division

Division uses `/`.

```sql
SELECT
    total_amount,
    item_count,
    total_amount / item_count AS average_item_value
FROM orders;
```

Division requires additional attention because behavior varies by data type and database engine.

For example, integer division may discard the fractional component in some database systems:

```sql
SELECT 5 / 2;
```

Do not assume the result will be `2.5` across all SQL databases and numeric types. Use an appropriate decimal or numeric type when fractional precision matters.

### Modulo

The `%` operator commonly returns the remainder after division.

```sql
SELECT
    order_id,
    quantity % 10 AS remainder
FROM order_items;
```

Modulo is useful for:

- Detecting even/odd values.
- Bucketing records.
- Periodic calculations.
- Sharding or partitioning logic in some applications.

For example:

```sql
SELECT id
FROM users
WHERE id % 2 = 0;
```

Database syntax can differ for modulo, so verify the target database's supported syntax.

## Operator Precedence

SQL evaluates arithmetic expressions according to operator precedence.

Multiplication and division generally have higher precedence than addition and subtraction.

```sql
SELECT 10 + 5 * 2;
```

Conceptually:

```text
10 + (5 * 2)
= 20
```

Parentheses should be used when the intended calculation is important or when they make business logic clearer.

```sql
SELECT
    price * (1 - discount_rate) AS discounted_price
FROM products;
```

Prefer explicit parentheses over relying on readers remembering precedence rules.

| Priority | Operators |
|---|---|
| Higher | `*`, `/`, `%` |
| Lower | `+`, `-` |
| Explicit | `( ... )` |

## Arithmetic with Columns

Arithmetic becomes most useful when applied to columns.

Consider:

```text
orders
---------------------------------
id
subtotal
shipping_fee
discount
tax
```

A final amount can be calculated as:

```sql
SELECT
    id,
    subtotal,
    shipping_fee,
    discount,
    tax,
    subtotal + shipping_fee - discount + tax AS total_amount
FROM orders;
```

This keeps the calculation close to the persisted source values.

For business-critical financial calculations, however, do not rely on an arbitrary expression scattered across multiple application queries. Define the calculation consistently and use appropriate numeric types and rounding rules.

## NULL and Arithmetic

Arithmetic involving `NULL` generally produces `NULL`.

```sql
SELECT
    price,
    discount,
    price - discount AS final_price
FROM products;
```

If `discount` is `NULL`, the result is typically `NULL`.

When `NULL` means "no discount", explicitly define that behavior:

```sql
SELECT
    price - COALESCE(discount, 0) AS final_price
FROM products;
```

This distinction is important:

```text
NULL
↓
unknown / missing value

0
↓
known numeric value
```

Do not automatically replace every `NULL` with zero. `NULL` may represent missing or unknown data rather than zero.

## Division by Zero

Division by zero can produce an error or database-specific behavior.

Avoid:

```sql
SELECT
    revenue / order_count AS revenue_per_order
FROM daily_metrics;
```

if `order_count` can be zero.

A safer pattern is:

```sql
SELECT
    revenue / NULLIF(order_count, 0) AS revenue_per_order
FROM daily_metrics;
```

`NULLIF(order_count, 0)` converts zero to `NULL`, avoiding division by zero in databases that error on the operation.

You can then decide how the application should represent the resulting `NULL`.

For example:

```sql
SELECT
    COALESCE(
        revenue / NULLIF(order_count, 0),
        0
    ) AS revenue_per_order
FROM daily_metrics;
```

Whether returning zero is semantically correct depends on the business meaning.

## Numeric Types and Precision

Arithmetic correctness depends heavily on data types.

Common numeric types include:

| Type | Typical Use |
|---|---|
| Integer | Counts, IDs, quantities |
| `DECIMAL` / `NUMERIC` | Exact decimal values |
| Floating point | Approximate scientific/measurement values |
| Database-specific numeric types | Specialized calculations |

For monetary values, prefer exact decimal types such as `NUMERIC` or `DECIMAL` rather than floating-point types.

Example:

```sql
CREATE TABLE order_items (
    id BIGINT PRIMARY KEY,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL
);
```

Then:

```sql
SELECT
    quantity * unit_price AS line_total
FROM order_items;
```

The database can preserve decimal semantics appropriate for financial calculations.

## Rounding and Precision

Arithmetic may produce more precision than the business domain requires.

For example:

```sql
SELECT
    total_amount / quantity AS average_price
FROM order_items;
```

If the result is displayed as currency, explicit rounding may be required.

```sql
SELECT
    ROUND(total_amount / NULLIF(quantity, 0), 2) AS average_price
FROM order_items;
```

The exact behavior and function signature of `ROUND()` can vary by database and numeric type.

Production systems should define:

- Scale and precision.
- Rounding mode.
- Currency rules.
- Tax calculation rules.
- Whether rounding happens per line item or after aggregation.

These decisions can materially affect financial results.

## Arithmetic in WHERE

Arithmetic expressions can be used to filter rows.

```sql
SELECT
    id,
    quantity,
    unit_price
FROM order_items
WHERE quantity * unit_price >= 100;
```

This is valid SQL, but the expression may make index usage less straightforward.

If the derived value is frequently queried, consider whether the schema should expose a suitable persisted/generated value or whether another query formulation allows better index utilization.

Always validate with `EXPLAIN` for performance-sensitive queries.

## Arithmetic in ORDER BY

Derived values can also control ordering.

```sql
SELECT
    id,
    quantity,
    unit_price,
    quantity * unit_price AS line_total
FROM order_items
ORDER BY line_total DESC;
```

This is useful for ranking records based on calculated business values.

For example:

```sql
SELECT
    product_id,
    available_stock,
    unit_price,
    available_stock * unit_price AS inventory_value
FROM inventory
ORDER BY inventory_value DESC;
```

For large datasets, expression-based sorting can require additional computation or sorting work unless the database can exploit an appropriate index or generated expression.

## Arithmetic in UPDATE

Arithmetic operators are commonly used for atomic database-side updates.

```sql
UPDATE inventory
SET stock_quantity = stock_quantity - 1
WHERE product_id = 42
  AND stock_quantity > 0;
```

This is generally preferable to:

```text
SELECT stock_quantity
        ↓
application calculates stock - 1
        ↓
UPDATE stock_quantity
```

because the latter introduces a race window between reading and writing.

A conditional atomic update allows the database to evaluate the current value and modify it as one statement.

```sql
UPDATE inventory
SET stock_quantity = stock_quantity - :quantity
WHERE product_id = :product_id
  AND stock_quantity >= :quantity;
```

The application should verify the affected-row count before assuming the operation succeeded.

## Arithmetic and Transactions

Arithmetic updates often participate in transactions.

For example, transferring an amount between accounts conceptually involves:

```sql
UPDATE accounts
SET balance = balance - :amount
WHERE id = :source_id
  AND balance >= :amount;

UPDATE accounts
SET balance = balance + :amount
WHERE id = :destination_id;
```

The two operations should normally be part of the same transaction when they represent one business operation.

```text
BEGIN
  debit source
       ↓
  credit destination
       ↓
COMMIT
```

If the second operation fails, the transaction should roll back the first operation according to the application's transaction policy.

Arithmetic itself does not provide transactional safety. The surrounding transaction and concurrency controls do.

## Arithmetic and Aggregation

Arithmetic operators can be combined with aggregate functions.

```sql
SELECT
    customer_id,
    SUM(quantity * unit_price) AS customer_total
FROM order_items
GROUP BY customer_id;
```

This is a common pattern in reporting and backend data access.

The distinction is important:

```sql
SUM(quantity * unit_price)
```

means:

```text
calculate each line total
        ↓
sum all line totals
```

whereas:

```sql
SUM(quantity) * unit_price
```

has different semantics and is only valid if `unit_price` is appropriately defined at the aggregation level.

Aggregation changes the level at which arithmetic is performed, so verify the business meaning carefully.

## Arithmetic and NULL-Safe Aggregation

Consider:

```sql
SELECT
    customer_id,
    SUM(quantity * unit_price) AS total
FROM order_items
GROUP BY customer_id;
```

If one operand is `NULL`, the row-level expression may become `NULL`, and aggregate behavior then depends on the database's handling of null values.

If missing numeric values semantically mean zero, normalize them explicitly:

```sql
SELECT
    customer_id,
    SUM(
        COALESCE(quantity, 0) * COALESCE(unit_price, 0)
    ) AS total
FROM order_items
GROUP BY customer_id;
```

Only do this when `NULL = 0` is actually the intended business rule.

## Backend Application Example

A FastAPI service may expose an order summary endpoint backed by SQL:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/orders/{order_id}/summary")
def get_order_summary(order_id: int):
    # The data-access layer should use a parameterized SQL query.
    ...
```

The corresponding query could calculate the line total in the database:

```sql
SELECT
    oi.order_id,
    SUM(oi.quantity * oi.unit_price) AS subtotal
FROM order_items AS oi
WHERE oi.order_id = :order_id
GROUP BY oi.order_id;
```

The application receives the derived value rather than loading every line item merely to perform a calculation in Python.

The same principle applies to Django ORM expressions, where database-side expressions can be represented without constructing raw SQL manually.

## Performance Considerations

Arithmetic operations are usually inexpensive at row level, but their placement in a query can affect execution plans.

Compare:

```sql
WHERE quantity * unit_price >= 100
```

with a query that can use a directly indexed column.

For high-volume workloads, consider:

- Whether the expression prevents efficient index access.
- Whether the calculation occurs for millions of rows.
- Whether sorting requires a large in-memory or disk-based operation.
- Whether a generated/computed column is appropriate.
- Whether a functional/expression index is supported and useful.
- Whether the value should be materialized.

Use the database execution plan:

```sql
EXPLAIN
SELECT
    id,
    quantity * unit_price AS line_total
FROM order_items
WHERE quantity * unit_price >= 100;
```

For PostgreSQL production investigation:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    quantity * unit_price AS line_total
FROM order_items
WHERE quantity * unit_price >= 100;
```

Do not optimize arithmetic prematurely. First identify whether the calculation is actually part of the query's performance bottleneck.

## Generated and Functional Values

If an arithmetic expression is frequently queried, a database-supported generated/computed column can sometimes improve query design.

Conceptually:

```text
base columns
    ↓
generated value
    ↓
index
    ↓
efficient filtering/sorting
```

The exact syntax is database-specific.

This approach can be appropriate when:

- The derived value is deterministic.
- The expression is frequently queried.
- The calculation is expensive or repeatedly executed.
- Indexing the derived value provides measurable benefit.

It introduces additional schema complexity, so it should be justified by the workload.

## Security Considerations

Arithmetic operators themselves are not a major SQL injection risk. The danger comes from dynamically constructing SQL expressions from untrusted input.

Avoid:

```python
query = f"""
SELECT *
FROM products
ORDER BY price * {user_expression}
"""
```

Instead, validate allowed operations and columns explicitly.

Values should be passed through parameterized queries:

```sql
SELECT
    quantity * unit_price AS line_total
FROM order_items
WHERE order_id = :order_id;
```

The database driver should bind `:order_id` rather than interpolating it into the SQL string.

For dynamic SQL identifiers or expressions, use an allowlist rather than treating them like ordinary parameter values.

## Common Mistakes

### Ignoring Integer Division

Assuming:

```sql
5 / 2
```

always produces `2.5` can cause incorrect calculations.

Use suitable numeric types and verify behavior for the target database.

### Treating NULL as Zero Automatically

This:

```sql
price + COALESCE(tax, 0)
```

is correct only if missing tax means zero.

Otherwise, it hides missing data.

### Dividing Without Protecting Against Zero

Avoid calculations where the denominator can legitimately be zero without handling that case.

```sql
revenue / NULLIF(order_count, 0)
```

is a common defensive pattern.

### Performing Read-Modify-Write in Application Code

Avoid:

```text
SELECT balance
→ Python subtracts amount
→ UPDATE balance
```

when the operation can be expressed as an atomic SQL update.

Prefer:

```sql
UPDATE accounts
SET balance = balance - :amount
WHERE id = :account_id
  AND balance >= :amount;
```

with appropriate transaction and concurrency controls.

### Using Floating Point for Money

Floating-point arithmetic can introduce representation and rounding issues.

Use exact decimal database types for monetary values and define explicit rounding rules.

### Assuming Expressions Are Automatically Indexed

A query using:

```sql
WHERE quantity * unit_price > 100
```

does not mean an index on `quantity` or `unit_price` will necessarily make the expression efficient.

Inspect the execution plan and design indexes around actual access patterns.

### Relying on Implicit Type Conversion

Mixing integers, decimals, strings, and other numeric types can produce database-specific conversion or precision behavior.

Use explicit and appropriate schema types.

## Interview Traps

| Question | Key Point |
|---|---|
| Why use arithmetic in SQL? | To calculate derived values close to the data and potentially reduce application work |
| What happens when arithmetic uses `NULL`? | The expression generally becomes `NULL` |
| How can division by zero be prevented? | Use logic such as `NULLIF()` where appropriate |
| Why avoid floating point for money? | Exact decimal arithmetic is generally required for financial correctness |
| Can arithmetic expressions use indexes? | Sometimes, but it depends on the expression, index type, and database |
| Why use `SET balance = balance - :amount`? | It avoids a separate application-side read-modify-write window |
| Why are parentheses useful? | They make precedence and business intent explicit |

## Production Checklist

Before deploying arithmetic-heavy SQL, verify:

- Numeric columns use appropriate database types.
- Monetary calculations use exact decimal types.
- Division-by-zero cases are handled.
- `NULL` semantics are intentional.
- Rounding rules are explicitly defined.
- Atomic updates are used for counters and balances where appropriate.
- Related arithmetic updates use transactions when required.
- Dynamic SQL expressions are validated with allowlists.
- Parameterized queries are used for values.
- Performance-sensitive expressions are checked with `EXPLAIN`.
- Generated or functional indexes are introduced only when workload measurements justify them.

## Key Takeaways

- SQL arithmetic operators enable database-side calculations for quantities, prices, balances, rates, and other derived values.
- `NULL`, numeric types, division behavior, and rounding rules can materially affect correctness and must be handled explicitly.
- Database-side arithmetic updates can provide safer atomic operations than application-side read-modify-write logic.
- Arithmetic expressions can affect index usage and query performance, so production workloads should be validated with execution plans.
- Treat financial precision, transaction boundaries, concurrency, and dynamic SQL validation as engineering concerns rather than merely SQL syntax details.