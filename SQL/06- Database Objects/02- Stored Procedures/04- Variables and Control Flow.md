# 04- Variables and Control Flow

## Overview

Stored procedures need local state and conditional execution when a database operation involves more than a single SQL statement. In PostgreSQL, PL/pgSQL provides variables, assignments, conditional statements, loops, and exception handling so a procedure can implement database-side business logic.

These constructs are useful when multiple database operations must execute as one unit, particularly when the database must make decisions based on current transactional state.

The important production principle is to keep procedural logic focused on **data-local operations and transactional invariants**. Do not move an entire application workflow into PL/pgSQL simply because the language can express it.

## Variables

A PL/pgSQL variable is local state maintained during execution of a procedure or block.

Variables are normally declared in a `DECLARE` section:

```sql
CREATE OR REPLACE PROCEDURE process_order(
    p_order_id bigint
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status text;
    v_total_amount numeric(12, 2);
BEGIN
    SELECT status, total_amount
    INTO v_status, v_total_amount
    FROM orders
    WHERE order_id = p_order_id;

    RAISE NOTICE 'Order %, status %, amount %',
        p_order_id,
        v_status,
        v_total_amount;
END;
$$;
```

The lifecycle is:

```text
CALL
  |
  v
Procedure starts
  |
  v
DECLARE variables initialized
  |
  v
SQL statements modify/read state
  |
  v
Procedure completes
  |
  v
Local variables disappear
```

Variables exist only for the duration of the relevant procedure invocation or block.

## Variable Declaration

The general form is:

```sql
DECLARE
    variable_name data_type;
```

Example:

```sql
DECLARE
    v_order_id bigint;
    v_status text;
    v_total numeric(12, 2);
    v_is_valid boolean;
```

Variables can also have defaults:

```sql
DECLARE
    v_retry_count integer DEFAULT 0;
    v_processed_at timestamptz DEFAULT CURRENT_TIMESTAMP;
```

The default expression is evaluated when the variable is initialized.

## Naming Conventions

Use a consistent naming convention to distinguish parameters, local variables, and columns.

A practical convention is:

| Object | Convention | Example |
|---|---|---|
| Procedure parameter | `p_` | `p_order_id` |
| Local variable | `v_` | `v_status` |
| Table column | No prefix | `status` |
| Constant-like value | `c_` where useful | `c_max_retries` |

Example:

```sql
DECLARE
    v_status text;
BEGIN
    SELECT status
    INTO v_status
    FROM orders
    WHERE order_id = p_order_id;
END;
```

This reduces ambiguity and makes procedural code easier to review.

## Assigning Values

Use `:=` for procedural assignment:

```sql
v_total := 100.00;
```

Expressions can also be assigned:

```sql
v_total := v_subtotal + v_tax;
```

A variable can receive a query result using `SELECT ... INTO`:

```sql
SELECT total_amount
INTO v_total
FROM orders
WHERE order_id = p_order_id;
```

Do not confuse PL/pgSQL assignment with SQL `SELECT`.

This:

```sql
v_total := 100.00;
```

is procedural assignment.

This:

```sql
SELECT total_amount
INTO v_total
FROM orders
WHERE order_id = p_order_id;
```

executes SQL and stores its result in a PL/pgSQL variable.

## `SELECT ... INTO`

`SELECT ... INTO` is one of the most important mechanisms for transferring query results into procedural variables.

```sql
DECLARE
    v_customer_id bigint;
    v_status text;
BEGIN
    SELECT customer_id, status
    INTO v_customer_id, v_status
    FROM orders
    WHERE order_id = p_order_id;
END;
```

The selected columns should match the target variables in number and compatible type.

### Handling Missing Rows

A query returning no row requires deliberate handling.

For example:

```sql
SELECT customer_id
INTO v_customer_id
FROM orders
WHERE order_id = p_order_id;

IF NOT FOUND THEN
    RAISE EXCEPTION 'Order % does not exist', p_order_id;
END IF;
```

`FOUND` is a PL/pgSQL status variable affected by statements such as `SELECT INTO`, `UPDATE`, `DELETE`, and other SQL operations.

### Handling Multiple Rows

If a query can return multiple rows, do not accidentally assume it returns one.

For example:

```sql
SELECT customer_id
INTO v_customer_id
FROM orders
WHERE status = 'pending';
```

This query may match many orders.

If the procedure expects exactly one row, enforce that expectation explicitly:

```sql
SELECT customer_id
INTO STRICT v_customer_id
FROM orders
WHERE order_id = p_order_id;
```

`INTO STRICT` raises an exception if the query returns zero rows or more than one row.

This is useful when cardinality is part of the procedure's contract.

## `%TYPE`

PL/pgSQL can derive a variable's type from an existing table column:

```sql
DECLARE
    v_status orders.status%TYPE;
    v_total orders.total_amount%TYPE;
```

This reduces the risk of duplicating a type definition.

If the column changes from:

```sql
numeric(12, 2)
```

to another compatible definition, the variable declaration follows the column's type.

This is useful for procedures tightly coupled to a database schema.

## `%ROWTYPE`

A variable can represent an entire table row:

```sql
DECLARE
    v_order orders%ROWTYPE;
BEGIN
    SELECT *
    INTO v_order
    FROM orders
    WHERE order_id = p_order_id;
END;
```

Fields can then be accessed individually:

```sql
v_order.status
v_order.customer_id
v_order.total_amount
```

`%ROWTYPE` is convenient when several columns from the same row are required.

However, selecting an entire row when only two fields are needed can obscure the procedure's actual data dependency.

Prefer explicit columns when clarity and minimal data access matter.

## Record Variables

`record` provides a flexible row-shaped variable:

```sql
DECLARE
    v_order record;
BEGIN
    SELECT order_id, status, total_amount
    INTO v_order
    FROM orders
    WHERE order_id = p_order_id;
END;
```

A `record` variable takes its structure from the query that populates it.

Use `record` when the row structure is dynamic or varies between queries. For stable schemas, `%ROWTYPE` or explicit variables are usually clearer.

## Constants

A variable can be declared as a constant:

```sql
DECLARE
    c_max_retry_count CONSTANT integer := 3;
```

Constants are useful for values that should not change during procedure execution.

They can make business rules more explicit:

```sql
IF v_retry_count >= c_max_retry_count THEN
    RAISE EXCEPTION 'Maximum retry count exceeded';
END IF;
```

Avoid scattering magic numbers throughout procedural code:

```sql
IF v_retry_count >= 3 THEN
```

when the number represents a meaningful business or operational rule.

## Conditional Control Flow

PL/pgSQL supports `IF`, `ELSIF`, and `ELSE`.

```sql
IF v_status = 'pending' THEN
    -- Process pending order.
ELSIF v_status = 'processing' THEN
    -- Process active order.
ELSE
    -- Handle other states.
END IF;
```

A production procedure should make state transitions explicit.

```sql
IF v_status = 'pending' THEN
    UPDATE orders
    SET status = 'processing'
    WHERE order_id = p_order_id;
ELSIF v_status = 'processing' THEN
    RAISE EXCEPTION 'Order % is already processing', p_order_id;
ELSE
    RAISE EXCEPTION 'Order % cannot be processed from status %',
        p_order_id,
        v_status;
END IF;
```

This is more reliable than silently ignoring unsupported states.

## Boolean Conditions

Conditions should express business rules directly.

```sql
IF p_quantity <= 0 THEN
    RAISE EXCEPTION 'Quantity must be positive';
END IF;
```

Multiple conditions can be combined:

```sql
IF p_quantity > 0
   AND v_available_quantity >= p_quantity THEN
    ...
END IF;
```

Be careful with `NULL`, because SQL uses three-valued logic.

For example:

```sql
IF v_status = 'completed' THEN
```

does not execute when `v_status` is `NULL`.

If `NULL` has a specific business meaning, handle it explicitly:

```sql
IF v_status IS NULL THEN
    RAISE EXCEPTION 'Order status is missing';
END IF;
```

## `CASE`

`CASE` is useful when assigning or selecting among several values.

```sql
v_priority :=
    CASE
        WHEN v_total_amount >= 10000 THEN 'high'
        WHEN v_total_amount >= 1000 THEN 'medium'
        ELSE 'normal'
    END;
```

It can also be used directly in SQL:

```sql
UPDATE orders
SET priority =
    CASE
        WHEN total_amount >= 10000 THEN 'high'
        WHEN total_amount >= 1000 THEN 'medium'
        ELSE 'normal'
    END
WHERE order_id = p_order_id;
```

Prefer SQL expressions such as `CASE` when the operation can be expressed declaratively. Do not introduce procedural branching when a single set-based SQL statement is clearer and more efficient.

## Loops

PL/pgSQL supports several loop patterns.

A basic loop:

```sql
LOOP
    -- statements

    EXIT WHEN v_processed >= p_batch_size;
END LOOP;
```

A `WHILE` loop:

```sql
WHILE v_processed < p_batch_size LOOP
    -- statements

    v_processed := v_processed + 1;
END LOOP;
```

A numeric `FOR` loop:

```sql
FOR v_index IN 1..10 LOOP
    RAISE NOTICE 'Processing %', v_index;
END LOOP;
```

These constructs are useful for genuinely procedural work, but row-by-row loops should be treated carefully.

## Iterating Over Query Results

A common pattern is:

```sql
FOR v_order IN
    SELECT order_id, customer_id
    FROM orders
    WHERE status = 'pending'
LOOP
    -- Process v_order.
END LOOP;
```

This is easy to read, but it may perform poorly when thousands or millions of rows are processed individually.

Prefer set-based SQL where possible.

Instead of:

```sql
FOR v_order IN
    SELECT order_id
    FROM orders
    WHERE status = 'pending'
LOOP
    UPDATE orders
    SET status = 'processing'
    WHERE order_id = v_order.order_id;
END LOOP;
```

prefer:

```sql
UPDATE orders
SET status = 'processing'
WHERE status = 'pending';
```

The set-based version generally gives the optimizer more freedom and avoids unnecessary procedural overhead.

## Batch Processing

Loops can still be appropriate for controlled batch processing.

For example, a maintenance procedure may process a bounded number of rows per iteration to limit transaction impact.

```sql
LOOP
    DELETE FROM audit_events
    WHERE event_id IN (
        SELECT event_id
        FROM audit_events
        WHERE created_at < p_cutoff
        ORDER BY event_id
        LIMIT p_batch_size
    );

    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    EXIT WHEN v_deleted = 0;
END LOOP;
```

The exact batching strategy should account for indexes, lock duration, transaction boundaries, replication, and workload characteristics.

A procedure loop does **not** automatically create a new transaction per iteration. Transaction boundaries are determined by the surrounding transaction semantics.

## `EXIT` and `CONTINUE`

`EXIT` terminates a loop:

```sql
LOOP
    EXIT WHEN v_processed >= p_limit;

    v_processed := v_processed + 1;
END LOOP;
```

`CONTINUE` skips to the next iteration:

```sql
FOR v_order IN
    SELECT order_id, status
    FROM orders
LOOP
    CONTINUE WHEN v_order.status = 'cancelled';

    -- Process active order.
END LOOP;
```

Use these constructs sparingly. Excessive branching inside loops can make database-side workflows difficult to test and reason about.

## Nested Blocks

PL/pgSQL supports nested blocks:

```sql
BEGIN
    -- Outer block.

    BEGIN
        -- Inner block.
    END;
END;
```

Nested blocks are particularly useful for scoped exception handling.

Variables declared inside an inner block are local to that block:

```sql
DECLARE
    v_outer text;
BEGIN
    v_outer := 'outer';

    DECLARE
        v_inner text := 'inner';
    BEGIN
        RAISE NOTICE '% %', v_outer, v_inner;
    END;
END;
```

Keep nesting shallow. Deep procedural nesting usually indicates that logic should be simplified or moved to separate routines.

## Exception Handling

PL/pgSQL supports exception blocks:

```sql
BEGIN
    INSERT INTO payments (
        order_id,
        amount
    )
    VALUES (
        p_order_id,
        p_amount
    );

EXCEPTION
    WHEN unique_violation THEN
        RAISE EXCEPTION 'Payment already exists for order %',
            p_order_id;
END;
```

Exception handling is useful when the procedure must translate or handle specific database errors.

However, exceptions are not a substitute for normal control flow.

Prefer:

```sql
IF NOT EXISTS (
    SELECT 1
    FROM orders
    WHERE order_id = p_order_id
) THEN
    RAISE EXCEPTION 'Order not found';
END IF;
```

when the condition is expected and inexpensive to check.

Use exception handling when dealing with genuinely exceptional outcomes or when an operation's atomic behavior depends on catching a database error.

## Transaction Semantics

A procedure may execute multiple statements:

```sql
UPDATE orders ...;
INSERT INTO audit_events ...;
UPDATE inventory ...;
```

These operations execute within the caller's transaction context.

This matters because application code might invoke the procedure through:

```text
HTTP request
    |
    v
Django / FastAPI
    |
    v
Database transaction
    |
    v
CALL procedure
    |
    +--> UPDATE
    +--> INSERT
    +--> UPDATE
    |
    v
COMMIT / ROLLBACK
```

The procedure's procedural control flow does not mean every statement is independently committed.

For critical workflows, reason about:

- Transaction boundaries.
- Isolation level.
- Row and table locks.
- Deadlocks.
- Retry behavior.
- Statement duration.
- Failure and rollback behavior.

## Row Count Diagnostics

After DML, you can inspect the number of affected rows:

```sql
DECLARE
    v_updated integer;
BEGIN
    UPDATE orders
    SET status = 'completed'
    WHERE order_id = p_order_id;

    GET DIAGNOSTICS v_updated = ROW_COUNT;

    IF v_updated = 0 THEN
        RAISE EXCEPTION 'Order % was not updated', p_order_id;
    END IF;
END;
```

This is valuable when the difference between:

```text
row existed and changed
```

and:

```text
nothing matched
```

is important to the procedure's contract.

## Combining Variables and Control Flow

A realistic procedure may combine:

1. Input validation.
2. Row lookup.
3. State validation.
4. Conditional logic.
5. Atomic updates.
6. Audit logging.

Example:

```sql
CREATE OR REPLACE PROCEDURE complete_order(
    p_order_id bigint
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status orders.status%TYPE;
BEGIN
    IF p_order_id IS NULL THEN
        RAISE EXCEPTION 'Order ID cannot be NULL';
    END IF;

    SELECT status
    INTO STRICT v_status
    FROM orders
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF v_status = 'completed' THEN
        RAISE EXCEPTION 'Order % is already completed', p_order_id;
    END IF;

    IF v_status <> 'processing' THEN
        RAISE EXCEPTION
            'Order % cannot be completed from status %',
            p_order_id,
            v_status;
    END IF;

    UPDATE orders
    SET status = 'completed',
        completed_at = CURRENT_TIMESTAMP
    WHERE order_id = p_order_id;

    INSERT INTO order_events (
        order_id,
        event_type,
        created_at
    )
    VALUES (
        p_order_id,
        'completed',
        CURRENT_TIMESTAMP
    );
END;
$$;
```

The `FOR UPDATE` lock is significant: it prevents concurrent transactions from changing the selected order between the state check and the update.

## Set-Based SQL Versus Procedural Logic

One of the most important senior-level decisions is knowing when **not** to use control flow.

| Requirement | Preferred Approach |
|---|---|
| Transform many rows | Set-based SQL |
| Filter rows | `WHERE` |
| Conditional column value | `CASE` |
| Aggregate data | `GROUP BY` / aggregate functions |
| Single state transition | SQL `UPDATE` with predicates |
| Complex per-row external workflow | Application/worker layer |
| Small procedural state machine | PL/pgSQL |
| Batch maintenance | Carefully designed loop/batching |
| Error translation | Exception handling |

A common anti-pattern is converting a SQL problem into an imperative loop:

```text
SELECT rows
    |
    v
Loop over rows
    |
    +--> SELECT
    +--> UPDATE
    +--> INSERT
    |
    v
Next row
```

This can create unnecessary database work.

Prefer:

```text
One optimized SQL statement
        |
        v
Database optimizer
        |
        v
Set-based execution
```

## Performance Considerations

Procedural logic can introduce overhead when it executes SQL repeatedly.

For example:

```sql
FOR v_row IN SELECT ...
LOOP
    UPDATE ...
END LOOP;
```

may execute one `UPDATE` per row.

For a large dataset, a set-based statement:

```sql
UPDATE orders
SET status = 'expired'
WHERE status = 'pending'
  AND expires_at < CURRENT_TIMESTAMP;
```

is usually preferable.

When procedural code is required:

- Keep loops bounded.
- Avoid unnecessary queries inside loops.
- Fetch only required columns.
- Use appropriate indexes.
- Avoid repeated lookups of the same data.
- Batch large maintenance operations.
- Measure with `EXPLAIN` and production-like data volumes.

## Concurrency Considerations

Control flow that reads state and then modifies it can introduce race conditions.

Unsafe pattern:

```sql
SELECT available_quantity
INTO v_available
FROM inventory
WHERE product_id = p_product_id;

IF v_available >= p_quantity THEN
    UPDATE inventory
    SET available_quantity = available_quantity - p_quantity
    WHERE product_id = p_product_id;
END IF;
```

Two concurrent transactions may both observe sufficient inventory.

Prefer an atomic predicate:

```sql
UPDATE inventory
SET available_quantity = available_quantity - p_quantity
WHERE product_id = p_product_id
  AND available_quantity >= p_quantity;

IF NOT FOUND THEN
    RAISE EXCEPTION 'Insufficient inventory';
END IF;
```

Use row locking when the workflow genuinely requires read-then-decide semantics:

```sql
SELECT available_quantity
INTO v_available
FROM inventory
WHERE product_id = p_product_id
FOR UPDATE;
```

The choice depends on the invariant, transaction isolation, and workload.

## Security Considerations

Variables and control flow do not inherently make a procedure secure.

Avoid constructing SQL from untrusted input:

```sql
-- Unsafe
EXECUTE 'DELETE FROM orders WHERE customer_id = ' || p_customer_id;
```

Use parameterized dynamic SQL:

```sql
EXECUTE
    'DELETE FROM orders WHERE customer_id = $1'
USING p_customer_id;
```

For dynamically selected identifiers, use safe identifier formatting:

```sql
EXECUTE format(
    'SELECT count(*) FROM %I',
    p_table_name
);
```

Security also requires appropriate procedure privileges and careful handling of `SECURITY DEFINER` procedures.

If a procedure executes with elevated privileges, validate all user-controlled inputs and ensure its `search_path` and referenced objects cannot be hijacked.

## Operational Considerations

Procedures containing significant control flow should be observable and testable.

Consider:

- Logging important state transitions.
- Returning meaningful errors.
- Measuring execution duration.
- Monitoring lock waits.
- Monitoring deadlocks.
- Testing high-contention scenarios.
- Testing zero-row and multi-row cases.
- Testing `NULL` inputs.
- Testing rollback behavior.
- Testing retry behavior.

Avoid excessive `RAISE NOTICE` statements in high-throughput production procedures because they can generate unnecessary client/server traffic and logs.

For persistent operational events, an audit table is usually more appropriate.

## Common Mistakes

### Using Variables When SQL Can Do the Work

Avoid procedural code for simple transformations:

```sql
SELECT ...
INTO v_value;

v_value := v_value * 1.1;

UPDATE ...
```

when the calculation can be performed directly in SQL.

### Row-by-Row Processing

A loop that executes SQL for every row can become a major performance bottleneck.

Prefer set-based operations unless per-row procedural behavior is actually required.

### Ignoring `NULL`

Conditions involving `NULL` may evaluate to unknown rather than true or false.

Use `IS NULL` and `IS NOT NULL` explicitly.

### Assuming `SELECT INTO` Always Finds One Row

Use `INTO STRICT` when exactly one row is required.

Otherwise, check `FOUND` and define the expected cardinality.

### Reading Without Considering Concurrency

A procedure can be logically correct in a single-user test and incorrect under concurrent requests.

State checks and updates must be designed as one concurrency-safe operation.

### Catching Every Exception

Avoid broad exception handling that hides failures:

```sql
EXCEPTION
    WHEN OTHERS THEN
        NULL;
```

This can silently corrupt application behavior and make production incidents difficult to diagnose.

Handle specific exceptions and re-raise unexpected failures.

### Excessive Procedural Complexity

If a procedure contains deeply nested loops, conditionals, dynamic SQL, and multiple exception layers, it may have become an application rather than a database routine.

Reconsider the responsibility boundary.

## Production Checklist

Before deploying a procedure with variables and control flow:

- [ ] Variables use clear and consistent names.
- [ ] Parameter and variable types match the domain.
- [ ] `SELECT INTO` cardinality is explicitly handled.
- [ ] `NULL` semantics are deliberate.
- [ ] Set-based SQL is preferred over unnecessary loops.
- [ ] Loops are bounded and operationally safe.
- [ ] State checks are concurrency-safe.
- [ ] Required rows use appropriate locking.
- [ ] Exceptions are specific and observable.
- [ ] Dynamic SQL uses safe parameter binding.
- [ ] Transaction behavior is understood and tested.
- [ ] Appropriate indexes support queries executed by the procedure.
- [ ] High-contention scenarios have been tested.
- [ ] Long-running operations have measurable performance characteristics.
- [ ] Production logging is useful without being excessively verbose.

## Interview Traps

### Does a PL/pgSQL Loop Create a New Transaction for Every Iteration?

No. A loop is procedural control flow; it does not inherently create transaction boundaries.

### Is Procedural SQL Faster Than Application Code?

Not automatically. Keeping data-local logic in the database can reduce network round trips, but inefficient procedural SQL can be much slower than an optimized set-based query.

### Should Every `SELECT INTO` Use `STRICT`?

No. `STRICT` is appropriate when exactly one row is part of the expected contract. Other cases may intentionally allow no row or use different cardinality handling.

### Why Is a Row-by-Row Loop Often Slower?

It can repeatedly invoke SQL operations and create procedural overhead instead of allowing the optimizer to execute one set-based operation efficiently.

### Does `FOR UPDATE` Prevent All Concurrency Problems?

No. It locks selected rows, but correctness still depends on transaction boundaries, isolation level, lock ordering, and the complete workflow.

### Should Exceptions Be Used for Normal Branching?

Generally no. Expected business conditions should usually be handled with explicit predicates or checks. Exceptions should represent exceptional database outcomes.

### Can Variables Protect Database Integrity?

No. Variables are temporary execution state. Database constraints, transactions, locks, and atomic SQL operations provide the durable integrity guarantees.

## Key Takeaways

- **Use PL/pgSQL variables and control flow for data-local procedural logic, not as a replacement for set-based SQL or application workflows.**
- **Treat `SELECT INTO`, `FOUND`, `INTO STRICT`, `NULL` handling, and variable naming as core correctness concerns.**
- **Prefer atomic SQL and appropriate row locking when control flow reads state before modifying it under concurrency.**
- **Keep loops bounded and avoid row-by-row database operations when a set-based statement can express the same operation.**
- **Design exception handling, transaction behavior, dynamic SQL, and observability as production concerns rather than implementation details.**