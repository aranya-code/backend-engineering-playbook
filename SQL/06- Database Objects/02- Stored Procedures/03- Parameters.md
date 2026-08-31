# 03- Parameters

## Overview

Parameters define the interface between a stored procedure and its caller. They determine what data the procedure accepts, how that data is represented, whether values are optional, and how the procedure communicates information back to the caller.

In production systems, procedure parameters should be treated like an API contract. Poorly designed parameters create ambiguity, unnecessary coupling, implicit type conversions, unsafe dynamic SQL, and difficult-to-evolve database interfaces.

This document uses **PostgreSQL and PL/pgSQL** examples. Parameter syntax and capabilities differ across database engines.

## Parameter Categories

PostgreSQL procedures support three primary parameter modes:

| Mode | Purpose | Caller provides value? | Procedure can modify value? |
|---|---|---:|---:|
| `IN` | Input | Yes | Not returned as output |
| `OUT` | Output | No | Yes |
| `INOUT` | Input and output | Yes | Yes |

`IN` is the default mode.

For most application-facing procedures, `IN` parameters are the normal starting point.

```sql
CREATE OR REPLACE PROCEDURE update_order_status(
    p_order_id bigint,
    p_status text
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE orders
    SET status = p_status
    WHERE order_id = p_order_id;
END;
$$;
```

The application supplies both values:

```sql
CALL update_order_status(1001, 'completed');
```

## `IN` Parameters

An `IN` parameter represents data supplied to the procedure.

```sql
CREATE OR REPLACE PROCEDURE create_order(
    p_customer_id bigint,
    p_total_amount numeric(12, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO orders (
        customer_id,
        total_amount,
        status,
        created_at
    )
    VALUES (
        p_customer_id,
        p_total_amount,
        'pending',
        CURRENT_TIMESTAMP
    );
END;
$$;
```

`IN` parameters are appropriate when the procedure performs an operation based on caller-provided input.

Common examples include:

```text
p_order_id
p_customer_id
p_quantity
p_amount
p_status
p_effective_at
```

### Why `IN` Is Usually Preferred

For application-facing procedures, keeping the input contract explicit provides:

- Clear call semantics.
- Stronger validation.
- Easier testing.
- Better readability.
- Reduced coupling between database and application code.

Prefer:

```sql
CALL reserve_inventory(1001, 25);
```

over interfaces that require callers to understand internal database state.

## Parameter Data Types

Parameters should use types that accurately represent the domain.

```sql
CREATE OR REPLACE PROCEDURE adjust_account_balance(
    p_account_id bigint,
    p_delta numeric(18, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE accounts
    SET balance = balance + p_delta
    WHERE account_id = p_account_id;
END;
$$;
```

Avoid accepting everything as `text`:

```sql
-- Poor interface
CREATE PROCEDURE adjust_account_balance(
    p_account_id text,
    p_delta text
)
```

Strong typing moves validation closer to the database boundary and reduces implicit conversions.

### Common Type Choices

| Domain | Typical PostgreSQL Type |
|---|---|
| Database identifier | `bigint` or domain-specific type |
| Small count | `integer` |
| Money-like exact value | `numeric(p, s)` |
| Timestamp with timezone | `timestamptz` |
| Date only | `date` |
| Boolean state | `boolean` |
| Short categorical value | `text` or an appropriate enum/domain |
| UUID identifier | `uuid` |
| JSON payload | `jsonb` |

Use the same semantic type used by the underlying schema where possible.

## Parameter Naming

A common PostgreSQL convention is to prefix input parameters with `p_`.

```sql
p_order_id
p_customer_id
p_quantity
p_status
p_created_before
```

Local variables can use `v_`:

```sql
DECLARE
    v_current_status text;
    v_available_quantity integer;
```

This convention prevents accidental ambiguity:

```sql
UPDATE orders
SET status = p_status
WHERE order_id = p_order_id;
```

Compare that with:

```sql
WHERE order_id = order_id;
```

The latter is difficult to reason about and can produce logic errors.

## Parameter Defaults

Parameters can have default values.

```sql
CREATE OR REPLACE PROCEDURE archive_orders(
    p_before timestamptz,
    p_batch_size integer DEFAULT 1000
)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM orders
    WHERE created_at < p_before
      AND status = 'archived';
END;
$$;
```

The caller can omit the defaulted parameter where supported:

```sql
CALL archive_orders(CURRENT_TIMESTAMP - INTERVAL '90 days');
```

Or provide it explicitly:

```sql
CALL archive_orders(
    CURRENT_TIMESTAMP - INTERVAL '90 days',
    500
);
```

Defaults are useful when there is a safe, predictable behavior.

They should be used carefully for:

- Destructive operations.
- Large batch operations.
- Security-sensitive behavior.
- Expensive operations.

For example, silently defaulting a cleanup procedure to process millions of rows may be operationally dangerous.

## Parameter Ordering

Keep parameters ordered according to their conceptual importance.

For example:

```sql
CREATE OR REPLACE PROCEDURE reserve_inventory(
    p_product_id bigint,
    p_order_id bigint,
    p_quantity integer
)
```

A useful convention is:

```text
Required identifiers
        |
        v
Business values
        |
        v
Optional configuration
```

For example:

```sql
CREATE OR REPLACE PROCEDURE process_payment(
    p_payment_id bigint,
    p_account_id bigint,
    p_amount numeric(18, 2),
    p_idempotency_key text,
    p_retry_limit integer DEFAULT 3
)
```

The interface becomes easier to understand when related parameters have a predictable order.

## Named Parameter Invocation

PostgreSQL supports named notation when invoking routines.

For example:

```sql
CALL process_payment(
    p_payment_id => 1001,
    p_account_id => 2001,
    p_amount => 125.50,
    p_idempotency_key => 'payment-1001'
);
```

Named invocation can improve readability for procedures with several parameters of similar types.

It can also reduce mistakes caused by positional arguments.

However, application code should still follow a consistent calling convention rather than mixing positional and named arguments arbitrarily.

## `OUT` Parameters

`OUT` parameters represent values produced by the procedure.

Conceptually:

```text
Caller
  |
  | input
  v
Procedure
  |
  | output
  v
Caller
```

Example:

```sql
CREATE OR REPLACE PROCEDURE get_order_status(
    IN p_order_id bigint,
    OUT p_status text
)
LANGUAGE plpgsql
AS $$
BEGIN
    SELECT status
    INTO p_status
    FROM orders
    WHERE order_id = p_order_id;
END;
$$;
```

The procedure assigns the output value:

```sql
CALL get_order_status(1001, NULL);
```

The exact client-side handling of returned procedure output depends on the PostgreSQL driver.

For read-oriented operations, a PostgreSQL function returning a value or result set is often a more natural interface than a procedure.

## `INOUT` Parameters

`INOUT` parameters are supplied by the caller and can also be modified by the procedure.

```sql
CREATE OR REPLACE PROCEDURE apply_discount(
    INOUT p_amount numeric(12, 2),
    IN p_discount_percent numeric(5, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    p_amount := p_amount -
        (p_amount * p_discount_percent / 100);
END;
$$;
```

The input value is supplied:

```text
p_amount = 100.00
p_discount_percent = 10
```

The procedure changes the output value:

```text
p_amount = 90.00
```

`INOUT` can be useful when the output is conceptually a transformed version of the input, but overuse can make a procedure interface harder to understand.

## Choosing Between `IN`, `OUT`, and `INOUT`

| Requirement | Preferred Mode |
|---|---|
| Caller provides input | `IN` |
| Procedure returns a value | `OUT` |
| Procedure transforms caller-provided value | `INOUT` |
| Database mutation with no returned value | `IN` |
| Complex query/result set | Often better modeled as a function |
| Multiple output values | `OUT` parameters or a structured return mechanism |

Prefer the simplest interface that accurately represents the operation.

## Parameter Validation

Parameters should be validated according to domain rules before performing state-changing operations.

```sql
CREATE OR REPLACE PROCEDURE reserve_inventory(
    p_product_id bigint,
    p_quantity integer
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_product_id <= 0 THEN
        RAISE EXCEPTION 'Invalid product ID: %', p_product_id;
    END IF;

    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Quantity must be positive';
    END IF;

    UPDATE inventory
    SET available_quantity = available_quantity - p_quantity
    WHERE product_id = p_product_id;
END;
$$;
```

Validation belongs in the procedure when the rule is important to database integrity.

However, application-level validation should not be treated as a replacement for database enforcement.

A request can originate from:

- REST API.
- gRPC service.
- Celery worker.
- Administrative script.
- Another database routine.
- Direct database client.

The database is the final enforcement boundary for database invariants.

## NULL Parameters

`NULL` requires deliberate handling because it represents an unknown or absent value rather than an ordinary value.

Avoid assuming:

```sql
IF p_status = NULL THEN
```

This does not evaluate to true.

Use:

```sql
IF p_status IS NULL THEN
    ...
END IF;
```

Similarly:

```sql
WHERE status = p_status
```

does not match rows where `p_status` is `NULL`.

If `NULL` is not valid for a parameter, validate it explicitly:

```sql
IF p_customer_id IS NULL THEN
    RAISE EXCEPTION 'Customer ID cannot be NULL';
END IF;
```

## Nullable Versus Optional

These are different concepts.

### Nullable

A parameter can explicitly receive `NULL`.

```sql
CALL update_customer(1001, NULL);
```

### Optional

A parameter can be omitted because it has a default.

```sql
p_timeout_seconds integer DEFAULT 30
```

An optional parameter may still be non-null when supplied.

Do not confuse:

```text
optional
```

with:

```text
nullable
```

They solve different interface-design problems.

## Parameters and Constraints

Parameter validation should complement database constraints rather than duplicate every constraint manually.

For example:

```sql
CREATE TABLE inventory (
    product_id bigint PRIMARY KEY,
    available_quantity integer NOT NULL CHECK (available_quantity >= 0)
);
```

The procedure can validate business-level input:

```sql
IF p_quantity <= 0 THEN
    RAISE EXCEPTION 'Quantity must be positive';
END IF;
```

The table constraint still protects the invariant:

```text
Procedure validation
        |
        v
Business rule
        |
        v
Table constraint
        |
        v
Database integrity
```

This layered approach protects against other write paths that bypass the procedure.

## Parameter Validation and Concurrency

Validation alone does not guarantee correctness under concurrency.

Consider:

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

Two concurrent transactions can read the same quantity before either performs the update.

For state-sensitive operations, use appropriate locking or an atomic update.

A safer pattern can be:

```sql
UPDATE inventory
SET available_quantity = available_quantity - p_quantity
WHERE product_id = p_product_id
  AND available_quantity >= p_quantity;
```

Then check whether a row was affected:

```sql
IF NOT FOUND THEN
    RAISE EXCEPTION 'Insufficient inventory';
END IF;
```

The parameter design and concurrency design must therefore be considered together.

## Parameters and Dynamic SQL

Parameters are especially important when constructing dynamic SQL.

Use `USING` for data values:

```sql
EXECUTE
    'UPDATE orders SET status = $1 WHERE order_id = $2'
USING p_status, p_order_id;
```

For identifiers, use `format()` with `%I`:

```sql
EXECUTE format(
    'SELECT count(*) FROM %I',
    p_table_name
);
```

Do not concatenate untrusted values directly into SQL:

```sql
-- Unsafe
EXECUTE 'UPDATE orders SET status = ''' || p_status || '''';
```

Parameterization protects values from SQL injection and usually produces clearer code.

## Parameters and Security

A parameter is not automatically trustworthy because it came from a database procedure call.

The caller could be:

- A compromised application.
- A privileged developer.
- An administrative script.
- Another compromised database routine.

Treat external input as untrusted until validated.

For security-sensitive procedures:

- Validate identifiers.
- Validate allowed status values.
- Validate ranges.
- Validate ownership where required.
- Avoid dynamic SQL unless necessary.
- Use parameterized SQL.
- Apply least-privilege execution permissions.

For example:

```sql
IF p_status NOT IN ('pending', 'processing', 'completed') THEN
    RAISE EXCEPTION 'Unsupported order status';
END IF;
```

## Procedure Parameters as API Contracts

A production procedure should be treated similarly to a service API.

```text
Application
    |
    | Procedure name
    | Parameter types
    | Parameter semantics
    v
Database Procedure
    |
    | Business/data operation
    v
Database State
```

Changing a parameter can therefore be a breaking change.

For example, changing:

```sql
p_customer_id bigint
```

to:

```sql
p_customer_id text
```

may affect:

- Application code.
- ORM/database drivers.
- Other procedures.
- Permissions.
- Tests.
- Migration scripts.
- Operational tooling.

Avoid casually changing procedure signatures in production.

## Procedure Overloading

PostgreSQL supports routines with different signatures in appropriate circumstances.

For example:

```sql
CREATE OR REPLACE PROCEDURE notify_customer(
    p_customer_id bigint
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Default notification behavior
END;
$$;
```

A separate signature could provide additional input:

```sql
CREATE OR REPLACE PROCEDURE notify_customer(
    p_customer_id bigint,
    p_channel text
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Channel-specific behavior
END;
$$;
```

Overloading can be useful, but excessive variants increase interface complexity.

Prefer a small number of well-defined interfaces rather than many subtly different signatures.

## Parameter Count

A procedure with too many parameters is often a design smell.

For example:

```sql
CREATE PROCEDURE process_order(
    p_order_id bigint,
    p_customer_id bigint,
    p_currency text,
    p_amount numeric,
    p_tax numeric,
    p_discount numeric,
    p_shipping_amount numeric,
    p_status text,
    p_channel text,
    p_source text,
    p_retry_count integer,
    p_metadata jsonb
);
```

This interface may indicate that the procedure is taking responsibility for too much.

Consider whether:

- Some values can be derived from database state.
- Some parameters belong to a separate operation.
- A structured database type is appropriate.
- The application should own part of the workflow.
- The procedure should be decomposed.

Do not introduce complex parameter structures merely to avoid thinking about interface boundaries.

## Parameter Design for Idempotency

Distributed backend systems frequently retry operations.

A mutation procedure may therefore accept an idempotency key:

```sql
CREATE OR REPLACE PROCEDURE create_payment(
    p_order_id bigint,
    p_amount numeric(18, 2),
    p_idempotency_key text
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO payments (
        order_id,
        amount,
        idempotency_key,
        created_at
    )
    VALUES (
        p_order_id,
        p_amount,
        p_idempotency_key,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (idempotency_key) DO NOTHING;
END;
$$;
```

The parameter itself does not provide idempotency. The database constraint must enforce uniqueness:

```sql
CREATE UNIQUE INDEX payments_idempotency_key_idx
ON payments (idempotency_key);
```

This is an important production principle:

> Parameters carry the operation's intent; constraints enforce critical invariants.

## Application Integration

Use database-driver parameterization when invoking procedures.

With Django:

```python
from django.db import connection


def cancel_order(order_id: int, reason: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "CALL cancel_order(%s, %s)",
            [order_id, reason],
        )
```

With a PostgreSQL client, use its native parameter binding mechanism rather than interpolating values into SQL.

Avoid:

```python
cursor.execute(
    f"CALL cancel_order({order_id}, '{reason}')"
)
```

Parameterization protects against SQL injection and handles database-specific escaping and type conversion.

## Evolving Procedure Parameters

Changing a procedure interface requires migration planning.

A safer deployment strategy is often:

```text
Current procedure
      |
      v
Introduce compatible interface
      |
      v
Deploy application support
      |
      v
Migrate callers
      |
      v
Remove obsolete interface
```

For example, rather than abruptly removing a parameter used by multiple services, introduce a compatible procedure version or overloaded signature where appropriate.

Be especially careful when procedures are consumed by multiple microservices owned by different teams.

## Common Parameter Mistakes

### Using Generic `text` Parameters

```sql
p_quantity text
```

This moves validation and conversion complexity into procedural code.

Prefer:

```sql
p_quantity integer
```

when the domain requires an integer.

### Ambiguous Names

Avoid:

```sql
p_id
```

when the procedure operates on several entities.

Prefer:

```sql
p_order_id
p_customer_id
p_payment_id
```

### Ignoring NULL Semantics

Avoid:

```sql
IF p_value = NULL THEN
```

Use:

```sql
IF p_value IS NULL THEN
```

### Excessive Defaults

Defaults can hide important decisions.

A destructive operation should not silently choose a potentially dangerous scope merely because the caller omitted a parameter.

### Too Many Parameters

A large parameter list often signals an unclear responsibility boundary.

Refactor the procedure rather than continuously adding arguments.

### Trusting Application Validation

Do not assume API validation is sufficient.

Database procedures can be called through paths that bypass the API entirely.

### Concatenating Parameter Values Into SQL

Avoid:

```sql
EXECUTE 'SELECT ... WHERE id = ' || p_id;
```

Prefer parameter binding:

```sql
EXECUTE 'SELECT ... WHERE id = $1'
USING p_id;
```

### Changing Signatures Without Migration Planning

A procedure signature is part of the database contract. Treat changes as schema/API changes rather than local implementation edits.

## Production Checklist

Before deploying a procedure parameter interface:

- [ ] Every parameter has a clear business meaning.
- [ ] Parameter names are unambiguous.
- [ ] Data types match the underlying domain.
- [ ] `NULL` behavior is explicitly defined.
- [ ] Defaults are safe and intentional.
- [ ] Parameter validation is implemented where required.
- [ ] Database constraints protect critical invariants.
- [ ] Dynamic SQL uses parameter binding and safe identifier quoting.
- [ ] Security-sensitive parameters are validated.
- [ ] Parameter count is reasonable.
- [ ] Idempotency requirements are represented where necessary.
- [ ] Concurrent execution has been tested.
- [ ] Application callers use parameterized procedure calls.
- [ ] Signature changes are managed through migrations.
- [ ] Procedure behavior is covered by integration tests.

## Interview Traps

### Are Procedure Parameters Just Like Python Function Arguments?

Conceptually they form an interface, but database parameters also participate in database type systems, privileges, SQL execution semantics, transaction behavior, and routine resolution.

### Is `IN` Required for Every Input Parameter?

No. `IN` is the default parameter mode in PostgreSQL and does not always need to be written explicitly.

### Is `NULL` the Same as Omitting a Parameter?

No. Omitting a parameter may use its default value; explicitly passing `NULL` supplies a null value.

### Does Parameter Validation Replace Database Constraints?

No. Validation improves procedure behavior, while constraints protect database invariants across all write paths.

### Does Passing a Parameter Prevent SQL Injection?

Not automatically. Safe parameter binding prevents injection for values, but dynamically constructed identifiers and SQL fragments require additional safeguards.

### Are More Parameters Better Because They Make a Procedure Flexible?

No. Excessive parameters often indicate an unclear abstraction boundary and increase coupling.

### Does an Idempotency Parameter Guarantee Idempotency?

No. Idempotency requires enforcement, typically through a unique constraint or equivalent database mechanism.

## Key Takeaways

- **Procedure parameters are database API contracts; use explicit names, strong types, and simple interfaces.**
- **Distinguish `IN`, `OUT`, and `INOUT`, and treat `NULL` semantics separately from optional parameters with defaults.**
- **Validate business inputs in procedures while using database constraints to enforce invariants across every write path.**
- **Use parameter binding for dynamic SQL values and safe identifier handling for dynamically constructed SQL structure.**
- **Design parameters with concurrency, idempotency, security, and future schema/API evolution in mind.**