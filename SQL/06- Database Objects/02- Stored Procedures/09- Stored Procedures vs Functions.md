# 09- Stored Procedures vs Functions

## Overview

Stored procedures and functions are server-side database routines that encapsulate reusable logic. They look similar syntactically, but they serve different purposes and have different execution semantics.

In PostgreSQL, the most important distinction is:

- **Function:** computes and returns a value or result set and is invoked with `SELECT` or as part of another SQL expression.
- **Procedure:** performs an operation and is invoked with `CALL`; it does not return a function value and can, under specific invocation conditions, control transactions with `COMMIT` and `ROLLBACK`.

The distinction matters when designing database APIs, transactional workflows, security boundaries, and application/database responsibilities.

## Functions

A function encapsulates computation that can be invoked from SQL expressions.

A simple PostgreSQL function:

```sql
CREATE OR REPLACE FUNCTION calculate_order_total(
    p_subtotal numeric,
    p_tax_rate numeric
)
RETURNS numeric
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT p_subtotal + (p_subtotal * p_tax_rate);
$$;
```

It can be called inside SQL:

```sql
SELECT calculate_order_total(100.00, 0.18);
```

It can also participate in larger expressions:

```sql
SELECT
    order_id,
    calculate_order_total(subtotal, tax_rate) AS total
FROM orders;
```

This composability is one of the defining characteristics of functions.

### Why Functions Exist

Functions are useful when a database operation represents a computation that can be treated as part of a SQL expression.

Typical examples include:

- Calculating derived values.
- Formatting or transforming values.
- Encapsulating reusable queries.
- Returning rows or result sets.
- Encapsulating reusable database operations.
- Implementing database-specific calculations.
- Providing controlled read access.

## Procedure

A procedure represents an operation that is invoked independently using `CALL`.

For example:

```sql
CREATE OR REPLACE PROCEDURE archive_old_orders(
    p_cutoff timestamptz
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE orders
    SET archived_at = CURRENT_TIMESTAMP
    WHERE created_at < p_cutoff
      AND archived_at IS NULL;
END;
$$;
```

It is invoked with:

```sql
CALL archive_old_orders(
    CURRENT_TIMESTAMP - INTERVAL '2 years'
);
```

The caller is asking the database to **perform an operation**, rather than requesting a value to be used in another SQL expression.

## Core Difference

| Characteristic | Function | Procedure |
|---|---|---|
| Invocation | `SELECT`, expression, etc. | `CALL` |
| Primary purpose | Compute/return a result | Perform an operation |
| Return value | Yes; scalar, row, or set | No function return value |
| Can be used in `SELECT` | Yes | No |
| Can be used inside expressions | Yes | No |
| Transaction control | Cannot independently `COMMIT`/`ROLLBACK` | Can in PostgreSQL under specific conditions |
| Trigger usage | Functions are used | Procedures are not directly used |
| Composability | High | Lower |
| Typical use | Queries and computations | Operational workflows |
| SQL integration | Strong | Explicit invocation |
| Result-set use | Natural | Usually through other mechanisms |
| Security boundary | Supported | Supported |

The exact behavior varies between database engines. This document uses PostgreSQL semantics for implementation examples.

## Invocation Model

The invocation syntax communicates intent.

### Function

```sql
SELECT calculate_order_total(100.00, 0.18);
```

The function produces a value that SQL can consume.

For example:

```sql
SELECT
    order_id,
    calculate_order_total(subtotal, tax_rate)
FROM orders;
```

Conceptually:

```text
SQL expression
      |
      v
   Function
      |
      v
   Result value
      |
      v
Continue SQL evaluation
```

### Procedure

```sql
CALL archive_old_orders(CURRENT_TIMESTAMP - INTERVAL '2 years');
```

Conceptually:

```text
CALL
  |
  v
Procedure
  |
  +--> database operations
  |
  +--> side effects
  |
  v
Operation completed
```

A procedure therefore fits operations more naturally than computations.

## Return Values

Functions have explicit return semantics.

### Scalar Function

```sql
CREATE OR REPLACE FUNCTION get_order_total(
    p_order_id bigint
)
RETURNS numeric
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(SUM(quantity * unit_price), 0)
    FROM order_items
    WHERE order_id = p_order_id;
$$;
```

Usage:

```sql
SELECT get_order_total(1001);
```

### Table-Returning Function

Functions can also return rows:

```sql
CREATE OR REPLACE FUNCTION get_customer_orders(
    p_customer_id bigint
)
RETURNS TABLE (
    order_id bigint,
    status text,
    created_at timestamptz
)
LANGUAGE sql
STABLE
AS $$
    SELECT id, status, created_at
    FROM orders
    WHERE customer_id = p_customer_id
    ORDER BY created_at DESC;
$$;
```

Usage:

```sql
SELECT *
FROM get_customer_orders(42);
```

This makes functions particularly useful for reusable query interfaces.

## Procedures and Side Effects

Procedures are a natural fit for operations whose primary purpose is changing database state.

For example:

```sql
CREATE OR REPLACE PROCEDURE mark_order_paid(
    p_order_id bigint
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE orders
    SET
        status = 'paid',
        paid_at = CURRENT_TIMESTAMP
    WHERE id = p_order_id
      AND status = 'pending';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Order % is not pending or does not exist',
            p_order_id;
    END IF;
END;
$$;
```

Invocation:

```sql
CALL mark_order_paid(1001);
```

The procedure communicates that the caller is requesting a database operation.

## Transaction Semantics

Transaction behavior is one of the most important PostgreSQL differences.

A normal function executes within the transaction context of its caller. It cannot independently commit or roll back the surrounding transaction.

For example:

```sql
BEGIN;

SELECT calculate_order_total(100.00, 0.18);

COMMIT;
```

The function does not own the transaction.

### Procedure Transaction Control

PostgreSQL procedures can use transaction control statements such as `COMMIT` and `ROLLBACK` when called in contexts where PostgreSQL permits transaction control.

For example:

```sql
CREATE OR REPLACE PROCEDURE process_batch()
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO audit_log(message)
    VALUES ('Batch started');

    COMMIT;

    INSERT INTO audit_log(message)
    VALUES ('Next transaction started');

    COMMIT;
END;
$$;
```

This must be called under PostgreSQL's rules for procedure transaction control. In particular, a procedure invoked inside an explicit transaction block cannot arbitrarily end that caller-owned transaction.

```sql
CALL process_batch();
```

is materially different from:

```sql
BEGIN;
CALL process_batch();
COMMIT;
```

The latter does not provide the same freedom for transaction control inside the procedure.

### Why This Matters

Transaction control makes procedures useful for certain database-native batch operations, but it also introduces complexity.

Long-running procedures that commit internally can produce:

- Partial completion.
- More complicated failure recovery.
- More difficult application-level transaction reasoning.
- Different locking behavior between batches.
- More complex retry semantics.

Do not use transaction control inside procedures simply because it is available.

## Functions vs Procedures in Application Code

A Python backend may invoke either type of routine through a database connection.

### Function

```python
from django.db import connection


def get_order_total(order_id: int) -> float:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT get_order_total(%s)",
            [order_id],
        )
        return cursor.fetchone()[0]
```

### Procedure

```python
from django.db import connection


def mark_order_paid(order_id: int) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "CALL mark_order_paid(%s)",
            [order_id],
        )
```

The database routine should not replace the application's domain/service layer automatically.

A common architecture is:

```text
HTTP / gRPC
     |
     v
Application Service
     |
     +----------------------+
     |                      |
     v                      v
 PostgreSQL              Kafka/Redis
     |
     +--> Functions
     |
     +--> Procedures
     |
     +--> Constraints
```

The application coordinates the broader workflow while the database owns data-centric responsibilities.

## Choosing Between a Function and Procedure

A useful decision rule is:

> If the caller needs a value or relation that can participate in SQL, prefer a function. If the caller is asking the database to perform an independent operation, consider a procedure.

| Requirement | Preferred |
|---|---|
| Calculate a value | Function |
| Return rows | Function |
| Use inside `SELECT` | Function |
| Use inside another SQL expression | Function |
| Reusable query abstraction | Function |
| Database transformation | Function |
| Perform a database operation | Procedure |
| Explicit operational command | Procedure |
| Database-side batch workflow | Procedure |
| Need PostgreSQL transaction control | Procedure, where appropriate |
| Trigger implementation | Function |
| Complex external workflow | Application logic |
| Kafka publication | Application logic |
| REST/gRPC orchestration | Application logic |

## Function Example: Reusable Query Logic

Suppose several backend components need a consistent definition of an active subscription.

A function can encapsulate that query:

```sql
CREATE OR REPLACE FUNCTION is_subscription_active(
    p_subscription_id bigint
)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM subscriptions
        WHERE id = p_subscription_id
          AND status = 'active'
          AND starts_at <= CURRENT_TIMESTAMP
          AND (ends_at IS NULL OR ends_at > CURRENT_TIMESTAMP)
    );
$$;
```

It can then be used naturally:

```sql
SELECT
    id,
    is_subscription_active(id) AS active
FROM subscriptions;
```

This is a strong function use case because the routine represents a queryable computation.

## Procedure Example: Database Operation

Suppose an operational job needs to archive historical data:

```sql
CREATE OR REPLACE PROCEDURE archive_orders_before(
    p_cutoff timestamptz
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE orders
    SET archived_at = CURRENT_TIMESTAMP
    WHERE created_at < p_cutoff
      AND archived_at IS NULL;

    INSERT INTO maintenance_log(operation, executed_at)
    VALUES ('archive_orders_before', CURRENT_TIMESTAMP);
END;
$$;
```

Invocation:

```sql
CALL archive_orders_before(
    CURRENT_TIMESTAMP - INTERVAL '2 years'
);
```

This is operational rather than computational, making a procedure a reasonable fit.

## Function Volatility

PostgreSQL functions have volatility classifications that communicate how their results behave.

| Classification | Meaning |
|---|---|
| `IMMUTABLE` | Same inputs always produce the same result |
| `STABLE` | Same result within a single statement, but may depend on database state |
| `VOLATILE` | Can change results or have side effects |

Example:

```sql
CREATE OR REPLACE FUNCTION calculate_tax(
    p_amount numeric,
    p_rate numeric
)
RETURNS numeric
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT p_amount * p_rate;
$$;
```

The classification is not merely documentation. PostgreSQL can use volatility information when optimizing expressions.

Do not mark a function `IMMUTABLE` unless it truly satisfies the required semantics.

Incorrect volatility declarations can produce incorrect query results or unsafe optimization.

## Function Side Effects

Functions can technically perform side effects when written in languages such as PL/pgSQL, but using functions as hidden commands can make SQL behavior difficult to reason about.

For example, a function named:

```text
get_customer()
```

should not unexpectedly:

- Insert audit records.
- Modify orders.
- Send notifications.
- Change unrelated tables.

Names and semantics should communicate whether the routine is computational or operational.

If an operation is fundamentally command-oriented, a procedure may communicate intent more clearly.

## Triggers and Functions

PostgreSQL triggers execute functions, not procedures.

For example:

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER orders_set_updated_at
BEFORE UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
```

This is an important interview distinction:

> PostgreSQL triggers execute trigger functions; procedures are invoked with `CALL`.

## Security

Both functions and procedures can participate in database security design.

Privileges can be controlled so that an application role has permission to execute a routine without unrestricted direct access to underlying tables.

A simplified model is:

```text
Application Role
      |
      v
EXECUTE privilege
      |
      v
Database Routine
      |
      v
Protected Tables
```

This can be valuable for sensitive operations, but security depends on the routine definition and ownership model.

For `SECURITY DEFINER` routines, carefully control:

- Routine ownership.
- `search_path`.
- Dynamic SQL.
- Object permissions.
- Input handling.
- Schema qualification.

For example, security-sensitive routines should avoid unsafe dynamic SQL:

```sql
EXECUTE 'SELECT * FROM ' || p_table_name;
```

Untrusted identifiers should never be concatenated into SQL without appropriate validation and identifier handling.

## Performance Considerations

Functions and procedures do not automatically improve performance.

### Functions

Functions can improve reuse and reduce application-side computation, but a poorly designed function can become expensive when called once per row.

For example:

```sql
SELECT expensive_function(id)
FROM millions_of_rows;
```

If the function performs additional queries for every row, this can create an N+1-style database workload:

```text
1 outer query
     |
     +--> function -> query
     +--> function -> query
     +--> function -> query
     ...
```

Prefer set-based SQL when possible.

### Procedures

Procedures can reduce application/database round trips for multi-step database operations:

```text
Application
     |
     | CALL
     v
Procedure
 ├── UPDATE
 ├── INSERT
 ├── UPDATE
 └── INSERT
```

However, a procedure containing inefficient queries remains inefficient.

Always evaluate:

- `EXPLAIN (ANALYZE, BUFFERS)`.
- Index usage.
- Lock waits.
- Transaction duration.
- Rows processed.
- CPU and I/O.
- Query frequency.
- Connection utilization.

## Maintainability

Database routines should be treated as production source code.

A recommended repository structure is:

```text
database/
├── migrations/
│   ├── 001_create_tables.sql
│   ├── 002_create_functions.sql
│   ├── 003_create_procedures.sql
│   └── 004_update_order_routines.sql
└── tests/
    ├── functions/
    └── procedures/
```

Avoid manually editing routines in production.

Use:

- Migration tooling.
- Code review.
- Automated tests.
- Version control.
- CI validation.
- Backward-compatible deployment strategies.

## Deployment and Versioning

Database routines can become contracts between the database and application.

Suppose version `N` of the application calls:

```sql
CALL process_order(order_id);
```

and version `N+1` requires:

```sql
CALL process_order(order_id, request_id);
```

During a rolling deployment, both application versions may temporarily exist.

A safer migration strategy is:

```text
Add compatible database interface
          |
          v
Deploy application using new interface
          |
          v
Verify all clients migrated
          |
          v
Remove obsolete interface
```

For significant contract changes, versioning routines can be appropriate:

```text
process_order_v1(...)
process_order_v2(...)
```

The exact strategy depends on the number of consumers and the deployment model.

## Transactions in Application-Owned Workflows

A common mistake is allowing the database routine and application to have conflicting transaction boundaries.

For example:

```text
Application transaction
    |
    +--> CALL procedure
    |
    +--> publish event
    |
    +--> commit
```

If the procedure commits independently, the application may no longer have the atomicity it expects.

For request/response operations, it is usually simpler to let the application own the transaction boundary and use functions/procedures as participants in that transaction.

For asynchronous database-native batch processing, procedure-controlled transaction boundaries can sometimes be appropriate.

The transaction owner should be explicit.

## Functions vs Procedures vs Application Logic

The practical choice is usually broader than just function versus procedure.

| Requirement | Function | Procedure | Application |
|---|---:|---:|---:|
| SQL calculation | Excellent | Poor fit | Possible |
| Reusable query | Excellent | Poor fit | Possible |
| Return rows | Excellent | Poor fit | Excellent |
| Trigger logic | Excellent | No | No |
| Database mutation | Possible | Excellent | Possible |
| Database transaction control | Limited | Stronger | Strong |
| Complex domain rules | Limited | Limited | Excellent |
| External API calls | Poor | Poor | Excellent |
| Kafka integration | Poor | Poor | Excellent |
| Redis integration | Poor | Poor | Excellent |
| Long-running workflow | Poor | Limited | Excellent |
| Database-specific optimization | Excellent | Excellent | Limited |
| Database security boundary | Excellent | Excellent | Possible |
| Portability | Database-specific | Database-specific | Usually better |

## Common Mistakes

### Using a Procedure Where a Function Is Expected

This fails when the caller needs to compose the result with SQL.

Incorrect conceptual model:

```sql
SELECT archive_old_orders(...);
```

If the operation is a procedure, use:

```sql
CALL archive_old_orders(...);
```

### Assuming Functions Cannot Modify Data

PostgreSQL functions can have side effects depending on their implementation and volatility. The distinction is not simply:

```text
function = read
procedure = write
```

The more accurate distinction is based on invocation and execution semantics.

### Assuming Procedures Are Always Better for Writes

A simple `UPDATE` often does not need a stored procedure.

Do not introduce a procedure merely to wrap one straightforward SQL statement unless it provides a meaningful abstraction, security boundary, or operational benefit.

### Calling Expensive Functions Per Row

A function that performs additional SQL per row can create severe performance problems.

Prefer set-based queries and inspect execution plans.

### Misusing Transaction Control

A procedure that commits internally can break assumptions made by the application transaction.

Define transaction ownership explicitly.

### Putting External Work in Database Routines

Database routines should generally not become substitutes for:

- HTTP clients.
- Kafka producers.
- Celery workers.
- Workflow engines.
- Application service layers.

Database transactions cannot automatically roll back external side effects.

### Incorrect Function Volatility

Declaring a state-dependent function as `IMMUTABLE` can allow PostgreSQL to make assumptions that are not valid.

Only declare `IMMUTABLE`, `STABLE`, or `VOLATILE` according to the function's actual behavior.

## Production Recommendations

### Prefer Functions When

Use a function when:

- A caller needs a result.
- The routine should participate in SQL expressions.
- A reusable query abstraction is valuable.
- The operation is naturally computational.
- A trigger requires database-side logic.
- A table-valued result is useful.

### Prefer Procedures When

Use a procedure when:

- The operation is command-oriented.
- The database operation is cohesive and reusable.
- A database-native maintenance workflow is appropriate.
- Transaction control inside the procedure is genuinely required and compatible with the calling model.
- A controlled database operation is useful as a security boundary.

### Prefer Application Logic When

Keep logic in Django, FastAPI, or another application service when it:

- Coordinates multiple systems.
- Calls external APIs.
- Publishes application events.
- Implements complex domain workflows.
- Requires asynchronous execution.
- Requires application-level retry or orchestration.
- Changes independently from database internals.

## Interview Traps

### What Is the Main Difference Between a Function and Procedure?

A function is invoked as part of SQL and returns a value or set of rows. A procedure is invoked with `CALL` to perform an operation and, in PostgreSQL, has capabilities around transaction control that functions do not.

### Can a PostgreSQL Function Modify Data?

Yes. PostgreSQL functions can perform data modifications depending on their implementation. Do not equate "function" with "read-only."

### Can a Procedure Be Used in a `SELECT`?

No. PostgreSQL procedures are invoked with `CALL`.

### Can a Function Control Transactions?

A PostgreSQL function cannot independently issue transaction-ending commands such as `COMMIT` or `ROLLBACK`.

### Can a Procedure Return Data?

A PostgreSQL procedure does not have a function-style `RETURNS` clause. It can communicate information through mechanisms such as output parameters or data stored elsewhere, but if the primary requirement is to return a queryable result, a function is generally the more natural abstraction.

### Which One Does a Trigger Use?

PostgreSQL triggers execute trigger functions.

### Are Procedures Faster Than Functions?

Not inherently. Performance depends on the SQL executed, execution plans, locking, data volume, transaction behavior, and invocation frequency.

### Should Every Database Operation Be a Stored Procedure?

No. Simple SQL, ORM operations, constraints, functions, procedures, and application logic all have appropriate use cases.

## Key Takeaways

- **Functions are composable SQL routines that return values or rows; procedures are command-oriented routines invoked with `CALL`.**
- **PostgreSQL functions cannot independently control transactions, while procedures can use transaction control only under the database's permitted invocation conditions.**
- **Choose functions for reusable computations and query interfaces, procedures for cohesive database operations, and application code for domain orchestration and external systems.**
- **Neither functions nor procedures are automatically faster; set-based SQL, query plans, indexes, locking, and transaction design determine real performance.**
- **Treat database routines as versioned production code with explicit transaction boundaries, security controls, tests, observability, and deployment compatibility.**