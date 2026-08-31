# 05- Conditional Logic

## Overview

Conditional logic allows a stored procedure to make decisions based on input values, database state, or the result of previous operations. In PostgreSQL, PL/pgSQL provides `IF`, `ELSIF`, `ELSE`, and `CASE` for implementing procedural branching.

Conditional logic is useful when a database-side operation must enforce a state transition, validate an invariant, choose between different database operations, or handle exceptional business conditions.

The production goal is not to maximize procedural logic. Prefer declarative SQL when a condition can be expressed directly in `WHERE`, `CASE`, constraints, or an atomic DML statement. Use procedural branching when the decision itself is part of a multi-step database workflow.

## `IF` Statement

The basic form is:

```sql
IF condition THEN
    statements;
END IF;
```

Example:

```sql
IF p_quantity <= 0 THEN
    RAISE EXCEPTION 'Quantity must be greater than zero';
END IF;
```

The condition must evaluate to `TRUE` for the statements to execute. SQL's three-valued logic means `NULL` conditions are not treated as true.

For example:

```sql
IF v_status = 'completed' THEN
    ...
END IF;
```

does not execute when `v_status` is `NULL`.

When `NULL` has business significance, handle it explicitly:

```sql
IF v_status IS NULL THEN
    RAISE EXCEPTION 'Order status is missing';
END IF;
```

## `IF ... ELSE`

Use `ELSE` when exactly one of two branches should execute.

```sql
IF v_balance >= p_amount THEN
    v_result := 'approved';
ELSE
    v_result := 'rejected';
END IF;
```

This is useful for binary decisions, but avoid putting large amounts of business logic into either branch. If both branches contain substantial database operations, consider whether the operation can be expressed more directly with SQL predicates.

## `IF ... ELSIF ... ELSE`

Multiple mutually exclusive conditions can be expressed with `ELSIF`.

```sql
IF v_total >= 10000 THEN
    v_priority := 'high';
ELSIF v_total >= 1000 THEN
    v_priority := 'medium';
ELSE
    v_priority := 'normal';
END IF;
```

The branches are evaluated from top to bottom. Once a condition evaluates to true, its branch executes and subsequent conditions are skipped.

The ordering therefore matters.

For example:

```sql
IF v_total >= 1000 THEN
    v_priority := 'medium';
ELSIF v_total >= 10000 THEN
    v_priority := 'high';
END IF;
```

The `high` branch can never execute because every value greater than or equal to `10000` also satisfies the first condition.

## `CASE`

`CASE` is often preferable when the purpose is to derive a value rather than execute substantially different procedural workflows.

### Searched `CASE`

```sql
v_priority :=
    CASE
        WHEN v_total >= 10000 THEN 'high'
        WHEN v_total >= 1000 THEN 'medium'
        ELSE 'normal'
    END;
```

This is especially useful for classifications and derived values.

The same expression can be used directly in SQL:

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

When a conditional transformation can be performed in one SQL statement, this set-based approach is generally preferable to retrieving a value into a variable and branching procedurally.

### Simple `CASE`

A simple `CASE` compares one expression against multiple values:

```sql
CASE v_status
    WHEN 'pending' THEN 'processing'
    WHEN 'processing' THEN 'completed'
    WHEN 'cancelled' THEN 'cancelled'
    ELSE 'unknown'
END
```

It is useful when the decision depends directly on one value.

## `IF` Versus `CASE`

| Requirement | Preferred construct |
|---|---|
| Execute different procedural statements | `IF` |
| Binary procedural decision | `IF ... ELSE` |
| Multiple procedural branches | `IF ... ELSIF ... ELSE` |
| Derive a value | `CASE` |
| Conditional value in `SELECT` | `CASE` |
| Conditional value in `UPDATE` | `CASE` |
| State transition requiring different operations | `IF` |
| Set-based transformation | `CASE` |

The distinction is important: `IF` controls procedural execution, while `CASE` is primarily an expression that produces a value.

## Conditions and Boolean Logic

PL/pgSQL supports normal SQL boolean operators:

```sql
IF p_quantity > 0
   AND v_available_quantity >= p_quantity THEN
    ...
END IF;
```

Use parentheses when the intended precedence is not immediately obvious:

```sql
IF (v_status = 'pending' OR v_status = 'processing')
   AND v_is_active THEN
    ...
END IF;
```

Complex boolean expressions should be kept readable. If a condition is difficult to understand during code review, calculate meaningful intermediate values or restructure the procedure.

For example:

```sql
v_can_process :=
    v_is_active
    AND v_status = 'pending'
    AND v_available_quantity >= p_quantity;

IF v_can_process THEN
    ...
END IF;
```

## `NULL` and Three-Valued Logic

A major source of conditional bugs is treating SQL boolean logic like two-valued application-language logic.

SQL expressions can produce:

- `TRUE`
- `FALSE`
- `NULL` / `UNKNOWN`

Consider:

```sql
v_status := NULL;

IF v_status = 'pending' THEN
    RAISE NOTICE 'Pending';
ELSE
    RAISE NOTICE 'Not pending';
END IF;
```

The equality comparison produces `NULL`, so the `IF` condition is not true and the `ELSE` branch executes.

Use explicit predicates when `NULL` matters:

```sql
IF v_status IS NULL THEN
    ...
ELSIF v_status = 'pending' THEN
    ...
END IF;
```

Do not use:

```sql
v_status = NULL
```

Use:

```sql
v_status IS NULL
```

instead.

## Conditional Logic With Parameters

Stored procedure parameters are often validated before database work begins.

```sql
CREATE OR REPLACE PROCEDURE reserve_inventory(
    p_product_id bigint,
    p_quantity integer
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_product_id IS NULL THEN
        RAISE EXCEPTION 'Product ID cannot be NULL';
    END IF;

    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Quantity must be greater than zero';
    END IF;

    -- Inventory operation.
END;
$$;
```

Input validation provides a clear procedure contract and prevents unnecessary database work.

However, validation in procedural code does not replace database constraints.

For example, if quantity must always be positive, enforce that invariant at the schema level where possible:

```sql
ALTER TABLE order_items
ADD CONSTRAINT order_items_quantity_positive
CHECK (quantity > 0);
```

Application and procedure validation improves error quality; constraints provide durable database-level enforcement.

## Conditional Logic With Query Results

A procedure often retrieves state and then branches.

```sql
DECLARE
    v_status orders.status%TYPE;
BEGIN
    SELECT status
    INTO STRICT v_status
    FROM orders
    WHERE order_id = p_order_id;

    IF v_status = 'pending' THEN
        ...
    ELSIF v_status = 'processing' THEN
        ...
    ELSE
        RAISE EXCEPTION
            'Order % cannot be processed from status %',
            p_order_id,
            v_status;
    END IF;
END;
```

This pattern is useful when different states genuinely require different workflows.

The cardinality of the query must be understood. `INTO STRICT` is appropriate when exactly one order must exist.

## Conditional DML

A common mistake is retrieving a row only to determine whether an update can happen.

Instead of:

```sql
SELECT status
INTO v_status
FROM orders
WHERE order_id = p_order_id;

IF v_status = 'pending' THEN
    UPDATE orders
    SET status = 'processing'
    WHERE order_id = p_order_id;
END IF;
```

consider an atomic predicate:

```sql
UPDATE orders
SET status = 'processing'
WHERE order_id = p_order_id
  AND status = 'pending';

IF NOT FOUND THEN
    RAISE EXCEPTION
        'Order % is missing or cannot transition from its current state',
        p_order_id;
END IF;
```

This approach is often better because the condition and modification are evaluated as one database operation.

It also reduces the race window between reading state and changing it.

## State Transitions

Conditional logic is particularly useful for database-backed state machines.

Suppose an order follows:

```text
pending -> processing -> completed
    |          |
    v          v
 cancelled  cancelled
```

A procedure can enforce valid transitions:

```sql
CREATE OR REPLACE PROCEDURE advance_order(
    p_order_id bigint,
    p_target_status text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_status orders.status%TYPE;
BEGIN
    SELECT status
    INTO STRICT v_current_status
    FROM orders
    WHERE order_id = p_order_id
    FOR UPDATE;

    IF v_current_status = 'pending'
       AND p_target_status = 'processing' THEN

        UPDATE orders
        SET status = 'processing'
        WHERE order_id = p_order_id;

    ELSIF v_current_status = 'processing'
          AND p_target_status = 'completed' THEN

        UPDATE orders
        SET status = 'completed'
        WHERE order_id = p_order_id;

    ELSIF p_target_status = 'cancelled'
          AND v_current_status IN ('pending', 'processing') THEN

        UPDATE orders
        SET status = 'cancelled'
        WHERE order_id = p_order_id;

    ELSE
        RAISE EXCEPTION
            'Invalid order transition: % -> %',
            v_current_status,
            p_target_status;
    END IF;
END;
$$;
```

The `FOR UPDATE` lock is important. Without appropriate locking or an atomic update predicate, concurrent transactions can make decisions using stale state.

## Conditional Logic and Concurrency

Consider this unsafe pattern:

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

Two concurrent transactions can both read the same available quantity and both decide that the reservation is valid.

A safer set-based approach is:

```sql
UPDATE inventory
SET available_quantity = available_quantity - p_quantity
WHERE product_id = p_product_id
  AND available_quantity >= p_quantity;

IF NOT FOUND THEN
    RAISE EXCEPTION 'Insufficient inventory';
END IF;
```

If the workflow requires reading multiple pieces of state before deciding, lock the relevant rows:

```sql
SELECT available_quantity
INTO v_available
FROM inventory
WHERE product_id = p_product_id
FOR UPDATE;
```

The correct solution depends on the invariant, isolation level, transaction boundary, and contention pattern.

## `FOUND` With Conditional Logic

`FOUND` is useful after SQL statements that affect or retrieve rows.

```sql
UPDATE orders
SET status = 'completed'
WHERE order_id = p_order_id
  AND status = 'processing';

IF NOT FOUND THEN
    RAISE EXCEPTION
        'Order % does not exist or is not processing',
        p_order_id;
END IF;
```

This is often cleaner than performing a separate existence check.

It also avoids an unnecessary query and makes the condition part of the actual modification.

Remember that `FOUND` is affected by subsequent PL/pgSQL statements, so inspect it immediately when its value matters.

## Conditional Logic and Constraints

Do not use procedural conditionals for invariants that belong in database constraints.

For example, this is usually better enforced with a constraint:

```sql
ALTER TABLE payments
ADD CONSTRAINT payments_amount_positive
CHECK (amount > 0);
```

rather than relying exclusively on:

```sql
IF p_amount <= 0 THEN
    RAISE EXCEPTION 'Amount must be positive';
END IF;
```

Use procedural conditions when the rule requires workflow or contextual decisions.

Use constraints for structural invariants such as:

- `NOT NULL`
- `CHECK`
- `UNIQUE`
- `PRIMARY KEY`
- `FOREIGN KEY`
- exclusion constraints where appropriate

The strongest design often uses both: constraints for permanent invariants and procedural logic for workflow behavior.

## Conditional Logic and Set-Based SQL

Procedural branching should not replace SQL's declarative capabilities.

For example, avoid:

```sql
FOR v_order IN
    SELECT order_id, total_amount
    FROM orders
    WHERE status = 'pending'
LOOP
    IF v_order.total_amount >= 10000 THEN
        UPDATE orders
        SET priority = 'high'
        WHERE order_id = v_order.order_id;
    ELSE
        UPDATE orders
        SET priority = 'normal'
        WHERE order_id = v_order.order_id;
    END IF;
END LOOP;
```

Use one set-based statement:

```sql
UPDATE orders
SET priority =
    CASE
        WHEN total_amount >= 10000 THEN 'high'
        ELSE 'normal'
    END
WHERE status = 'pending';
```

The set-based version generally reduces procedural overhead and gives the database optimizer more freedom.

## Nested Conditional Logic

Nested `IF` statements are valid:

```sql
IF v_is_active THEN
    IF v_status = 'pending' THEN
        ...
    ELSE
        ...
    END IF;
ELSE
    ...
END IF;
```

However, deep nesting quickly becomes difficult to maintain.

Prefer guard clauses where appropriate:

```sql
IF NOT v_is_active THEN
    RAISE EXCEPTION 'Account is inactive';
END IF;

IF v_status <> 'pending' THEN
    RAISE EXCEPTION 'Order is not pending';
END IF;

-- Main processing path.
```

This keeps the normal execution path easier to follow.

## Conditional Logic With Transactions

Conditional branches frequently participate in transactions.

A typical backend flow is:

```text
HTTP request
     |
     v
Django / FastAPI
     |
     v
BEGIN
     |
     v
CALL stored procedure
     |
     +--> Validate input
     |
     +--> Read/lock state
     |
     +--> Conditional decision
     |
     +--> UPDATE / INSERT
     |
     v
COMMIT
```

If any branch raises an exception, the surrounding transaction may be rolled back according to the caller's transaction handling.

Therefore, production procedures should define behavior for:

- Missing rows.
- Invalid states.
- Duplicate operations.
- Concurrent requests.
- Constraint violations.
- Deadlocks.
- Transaction retries.

Do not assume that conditional logic alone guarantees atomicity.

## Exception Versus Conditional Logic

Expected business conditions should generally be handled with conditions.

For example:

```sql
UPDATE inventory
SET available_quantity = available_quantity - p_quantity
WHERE product_id = p_product_id
  AND available_quantity >= p_quantity;

IF NOT FOUND THEN
    RAISE EXCEPTION 'Insufficient inventory';
END IF;
```

Using exceptions as ordinary branching logic can make control flow harder to understand.

Exception handling is more appropriate for unexpected or database-level failures:

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
        RAISE EXCEPTION
            'Payment already exists for order %',
            p_order_id;
END;
```

Handle specific exceptions where possible. Avoid swallowing failures with:

```sql
EXCEPTION
    WHEN OTHERS THEN
        NULL;
```

## Dynamic SQL and Conditional Logic

Conditional logic sometimes determines which table, column, or query must be executed.

Dynamic SQL should never concatenate untrusted values directly into SQL.

Unsafe:

```sql
EXECUTE 'SELECT * FROM orders WHERE customer_id = ' || p_customer_id;
```

Use parameters for values:

```sql
EXECUTE
    'SELECT count(*) FROM orders WHERE customer_id = $1'
USING p_customer_id;
```

For identifiers, use `format()` with `%I`:

```sql
EXECUTE format(
    'SELECT count(*) FROM %I',
    p_table_name
);
```

Conditional logic does not make dynamic SQL safe. Input validation and correct parameterization remain necessary.

## Performance Considerations

Conditional logic itself is usually inexpensive. The expensive part is often the database work performed inside each branch.

For example:

```sql
IF condition THEN
    SELECT ...;
    UPDATE ...;
    INSERT ...;
ELSE
    SELECT ...;
    UPDATE ...;
END IF;
```

Each branch may have different query plans and indexing requirements.

For production procedures:

- Keep predicates sargable where possible.
- Index columns used by frequently executed branch queries.
- Avoid repeated queries that could be combined.
- Prefer set-based operations.
- Keep transactions short.
- Avoid unnecessary locks.
- Benchmark branches independently.
- Use `EXPLAIN` for expensive SQL statements.

A procedure can be logically correct while still causing production latency because one rarely tested branch performs an expensive query.

## Security Considerations

Conditional logic can enforce authorization-related rules, but database-side authorization should be designed explicitly.

For example:

```sql
IF NOT v_user_can_modify THEN
    RAISE EXCEPTION 'Operation is not permitted';
END IF;
```

This can be useful, but do not treat an application-side boolean as inherently trustworthy if the database is responsible for enforcing access control.

When procedures are exposed directly to application roles:

- Grant only required `EXECUTE` privileges.
- Restrict direct table access when appropriate.
- Carefully review `SECURITY DEFINER` procedures.
- Avoid unsafe dynamic SQL.
- Validate security-sensitive parameters.
- Keep privileged operations narrowly scoped.

For `SECURITY DEFINER` routines, use a controlled `search_path` and schema-qualified object references where appropriate.

## Production Best Practices

### Keep Conditions Close to the Data Operation

Prefer:

```sql
UPDATE orders
SET status = 'processing'
WHERE order_id = p_order_id
  AND status = 'pending';
```

over a separate read followed by a conditional update when the state transition can be expressed atomically.

### Make Invalid States Explicit

Prefer:

```sql
ELSE
    RAISE EXCEPTION
        'Unsupported order state: %',
        v_status;
```

over silently doing nothing.

### Use Constraints for Invariants

Do not rely exclusively on procedure branches to enforce rules that should remain true regardless of how data is modified.

### Keep Branches Small

A conditional branch should represent a clear decision. Large branches with duplicated SQL are difficult to test and maintain.

### Avoid Duplicate Queries

If multiple branches independently query the same data, consider retrieving the required state once or restructuring the operation into a single set-based statement.

### Test Every Branch

At minimum, test:

- Each valid branch.
- Each invalid branch.
- `NULL` inputs.
- Missing rows.
- Concurrent execution.
- Constraint violations.
- Rollback behavior.
- Boundary values.

## Common Mistakes

| Mistake | Why it is problematic | Better approach |
|---|---|---|
| Comparing a value with `= NULL` | SQL uses three-valued logic | Use `IS NULL` |
| Incorrect `ELSIF` ordering | Earlier conditions may make later branches unreachable | Order conditions from most specific to appropriate general cases |
| Reading before updating | Creates race windows | Prefer atomic DML predicates or locking |
| Looping when `CASE` works | Adds procedural overhead | Use set-based SQL |
| Using exceptions for normal branching | Makes control flow harder to reason about | Use explicit conditions |
| Ignoring `FOUND` | Can hide zero-row operations | Check it immediately when required |
| Relying only on procedural validation | Other clients can bypass the procedure | Use database constraints |
| Deeply nested `IF` statements | Reduces maintainability | Use guard clauses and simpler branches |
| Broad exception swallowing | Hides real failures | Handle specific exceptions and re-raise unexpected errors |
| Unsafe dynamic SQL | Can introduce SQL injection | Use `USING` and safe identifier formatting |

## Interview Traps

### Is `CASE` the Same as `IF`?

No. `CASE` is an expression that produces a value, while `IF` is procedural control flow that determines which statements execute.

### What Happens When an `IF` Condition Is `NULL`?

It is not treated as true. The `THEN` branch is skipped, so an `ELSE` branch executes if present.

### Why Is This Unsafe?

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

Because concurrent transactions can read the same inventory value before either transaction performs its update. An atomic conditional update or appropriate row locking is required.

### Should Business Rules Always Be Implemented With `IF`?

No. Rules that are structural invariants should usually be enforced with database constraints. Set-based transformations should generally use SQL expressions such as `CASE`.

### Why Is This Often Better?

```sql
UPDATE orders
SET status = 'processing'
WHERE order_id = p_order_id
  AND status = 'pending';
```

It combines the state predicate and modification into one database operation, reducing round trips and avoiding an unnecessary read-before-write race.

### Can `IF` Replace Database Constraints?

No. Procedural checks only execute when the procedure executes. Constraints protect the data regardless of which application, script, migration, or database client modifies it.

### Is `IF` Always Faster Than `CASE`?

No. They solve different problems. Performance depends primarily on the SQL operations executed and the resulting query plans, not simply on whether the syntax uses `IF` or `CASE`.

## Key Takeaways

- **Use `IF` for procedural decisions and `CASE` for conditional expressions; prefer set-based SQL when the database can perform the operation directly.**
- **Treat `NULL` explicitly because SQL conditions use three-valued logic rather than ordinary two-valued boolean logic.**
- **Make state transitions concurrency-safe with atomic predicates or appropriate row locks instead of relying on an unsafe read-then-update sequence.**
- **Use database constraints for durable invariants and procedural conditions for workflow-specific decisions.**
- **Keep branches small, test every execution path, and make transaction, exception, security, and performance behavior explicit.**