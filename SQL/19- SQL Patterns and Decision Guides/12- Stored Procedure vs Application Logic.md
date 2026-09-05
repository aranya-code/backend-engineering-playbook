# 12- Stored Procedure vs Application Logic

## Overview

Stored procedures and application logic are two different places where business and data-processing behavior can live.

A **stored procedure** executes logic inside the database:

```text
Application
    ↓
CALL procedure(...)
    ↓
PostgreSQL
    ↓
SQL + procedural logic
    ↓
Database changes / result
```

**Application logic** executes in the backend service:

```text
Client
   ↓
Nginx
   ↓
Django / FastAPI
   ↓
Python business logic
   ↓
SQL
   ↓
PostgreSQL
```

The decision is architectural, not simply a matter of SQL preference.

Stored procedures can be valuable when logic must execute close to the data, coordinate multiple database operations, or enforce behavior independently of application clients.

Application logic is usually preferable for complex business workflows, domain rules, integrations, orchestration, and behavior that benefits from normal software-engineering tooling.

The central question is:

> Should this behavior be owned by the database, or by the application domain?

---

## Stored Procedure

A stored procedure is a database object containing procedural logic that can be invoked by an application or another database operation.

PostgreSQL supports procedures through `CREATE PROCEDURE`:

```sql
CREATE PROCEDURE create_order(
    p_customer_id bigint,
    p_total_amount numeric(12, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO orders (
        customer_id,
        total_amount
    )
    VALUES (
        p_customer_id,
        p_total_amount
    );
END;
$$;
```

It can be invoked with:

```sql
CALL create_order(42, 199.99);
```

PostgreSQL also has functions:

```sql
CREATE FUNCTION ...
```

Functions and procedures overlap in their ability to encapsulate database-side logic, but they have different invocation and transaction semantics.

Do not use "stored procedure" as a generic name for every database-side function.

---

## Application Logic

Application logic is behavior implemented in the backend service.

For example:

```python
def calculate_order_total(items, discount):
    subtotal = sum(item.price * item.quantity for item in items)

    if subtotal >= 1000:
        discount += 0.10

    return subtotal * (1 - discount)
```

The application can then persist the resulting state through SQL or an ORM.

In a Django application:

```python
from decimal import Decimal


def calculate_total(subtotal: Decimal, discount: Decimal) -> Decimal:
    if subtotal >= Decimal("1000.00"):
        discount += Decimal("0.10")

    return subtotal * (Decimal("1") - discount)
```

This code is easy to test, review, version, and deploy using standard application engineering practices.

---

## Core Difference

| Dimension | Stored Procedure | Application Logic |
|---|---|---|
| Execution location | Database | Application server |
| Primary language | PL/pgSQL / database language | Python or application language |
| Data locality | Excellent | Requires database interaction |
| Business-domain modeling | Limited compared with application code | Excellent |
| Database transaction control | Strong | Strong through transactions |
| Unit testing | More specialized | Mature application tooling |
| Version control | Migration/schema tooling | Standard source control |
| External API calls | Generally inappropriate | Excellent |
| Redis/Kafka integration | Generally inappropriate | Excellent |
| Database-only enforcement | Excellent | Depends on every application client |
| Horizontal application scaling | Not directly relevant | Straightforward |
| Database CPU consumption | Higher | Lower database-side procedural workload |
| Cross-service reuse | Possible but tightly DB-coupled | Requires service/API design |
| Deployment coupling | Database deployment | Application deployment |
| Domain complexity | Usually poor fit | Usually strong fit |

---

## Why Stored Procedures Exist

Stored procedures exist primarily to execute controlled database operations close to the data.

They can be useful when:

- Multiple database statements must be coordinated.
- The operation is highly data-intensive.
- The logic should be callable by multiple database clients.
- Database-side permissions should restrict what clients can do.
- Network round trips would otherwise be excessive.
- A critical invariant should be enforced independently of one application.

For example:

```text
Application
    ↓
CALL process_payment(...)
    ↓
PostgreSQL
    ├── Validate account
    ├── Update balance
    ├── Insert ledger entry
    └── Record audit event
```

The entire operation can be designed as one database transaction.

---

## Why Application Logic Exists

Application code is usually the better home for behavior involving:

- Domain rules.
- Complex workflows.
- External services.
- APIs.
- Authentication flows.
- Authorization orchestration.
- Kafka publishing.
- Redis coordination.
- Email or notification delivery.
- Business policies.
- Domain objects.
- Complex validation.
- Long-running workflows.

For example:

```text
Order Service
    ↓
Validate order
    ↓
Reserve inventory
    ↓
Call payment service
    ↓
Persist order state
    ↓
Publish event
    ↓
Send notification
```

This workflow crosses system boundaries and is therefore generally inappropriate for a PostgreSQL stored procedure.

---

## Data-Local vs Domain-Local Logic

A useful architectural distinction is:

```text
Data-local logic
        ↓
Database

Domain-local logic
        ↓
Application
```

Examples of data-local operations:

- Bulk transformations.
- Set-based updates.
- Data validation closely tied to schema.
- Complex SQL calculations.
- Database-side batch processing.

Examples of domain-local operations:

- Pricing policy.
- Subscription lifecycle.
- Payment-provider orchestration.
- User-facing business workflows.
- External API interactions.

This distinction is more useful than the simplistic rule:

> SQL belongs in the database; business logic belongs in Python.

Real production systems contain legitimate overlap.

---

## Transactional Stored Procedure Example

Suppose an internal operation needs to transfer funds between two accounts.

A database-side procedure can coordinate the writes:

```sql
CREATE PROCEDURE transfer_funds(
    p_from_account bigint,
    p_to_account bigint,
    p_amount numeric(12, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Transfer amount must be positive';
    END IF;

    UPDATE accounts
    SET balance = balance - p_amount
    WHERE id = p_from_account
      AND balance >= p_amount;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Insufficient funds or source account not found';
    END IF;

    UPDATE accounts
    SET balance = balance + p_amount
    WHERE id = p_to_account;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Destination account not found';
    END IF;

    INSERT INTO account_transfers (
        from_account_id,
        to_account_id,
        amount
    )
    VALUES (
        p_from_account,
        p_to_account,
        p_amount
    );
END;
$$;
```

The procedure can be called using:

```sql
CALL transfer_funds($1, $2, $3);
```

The exact transaction boundary should be designed carefully. PostgreSQL procedure transaction behavior differs from ordinary function execution, and applications should not assume that `CALL` automatically creates the complete business transaction they need.

---

## Application Equivalent

The same operation could be implemented in Django:

```python
from django.db import transaction
from django.db.models import F


@transaction.atomic
def transfer_funds(from_account_id, to_account_id, amount):
    if amount <= 0:
        raise ValueError("Transfer amount must be positive")

    updated = (
        Account.objects
        .filter(
            id=from_account_id,
            balance__gte=amount,
        )
        .update(balance=F("balance") - amount)
    )

    if updated != 1:
        raise ValueError("Insufficient funds or source account not found")

    updated = (
        Account.objects
        .filter(id=to_account_id)
        .update(balance=F("balance") + amount)
    )

    if updated != 1:
        raise ValueError("Destination account not found")

    AccountTransfer.objects.create(
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        amount=amount,
    )
```

The application transaction can coordinate the database operations.

However, if other clients can modify the same data directly, application logic alone may not be sufficient to enforce the invariant.

That is where database constraints and database-side protections become important.

---

## Stored Procedure Does Not Replace Constraints

A common mistake is using procedural code to enforce something that should be a database constraint.

For example, if an email must be unique:

```sql
CREATE UNIQUE INDEX uq_customers_email
    ON customers (email);
```

This is stronger than:

```text
SELECT whether email exists
        ↓
IF not exists
        ↓
INSERT
```

because concurrent transactions can both observe that the value does not exist.

The database constraint provides the actual invariant.

A useful hierarchy is:

```text
Schema constraint
    ↓
Database transaction / locking
    ↓
Database-side procedural logic
    ↓
Application logic
```

The exact ordering depends on the problem, but invariants that can be expressed declaratively should generally be enforced declaratively.

---

## Stored Procedures and Concurrency

Stored procedures can help coordinate database operations, but they do not magically eliminate concurrency problems.

Consider:

```text
Request A → procedure
Request B → procedure
```

Both may execute concurrently.

Correctness still depends on:

- Isolation level.
- Row locking.
- Constraints.
- Atomic updates.
- Lock ordering.
- Transaction boundaries.

For example:

```sql
UPDATE inventory
SET available = available - $1
WHERE product_id = $2
  AND available >= $1;
```

This atomic conditional update may be more important than whether the operation is wrapped inside a procedure.

The database mechanism enforcing the invariant matters more than the presence of procedural code.

---

## Application Transactions

Application logic can still provide strong transactional guarantees.

Django:

```python
from django.db import transaction

with transaction.atomic():
    ...
```

SQLAlchemy:

```python
with session.begin():
    ...
```

The application defines the workflow while PostgreSQL provides transactional guarantees.

This is often the preferred architecture when the workflow is primarily application-owned.

---

## Stored Procedure and Network Round Trips

One potential advantage of database-side logic is reducing application/database round trips.

Without a procedure:

```text
Application → SELECT
Database    → result

Application → UPDATE
Database    → result

Application → INSERT
Database    → result
```

With database-side logic:

```text
Application → CALL procedure
Database    → execute multiple operations
Database    → result
```

This can reduce network overhead.

However, the performance benefit depends on the actual workload.

For a small number of simple operations, the difference may be negligible.

For high-volume, data-intensive operations, reducing round trips can be meaningful.

---

## Set-Based SQL vs Procedural Loops

Before writing a stored procedure containing a loop:

```sql
FOR item IN
    SELECT ...
LOOP
    ...
END LOOP;
```

ask whether the operation can be expressed as set-based SQL.

For example, prefer:

```sql
UPDATE orders
SET status = 'expired'
WHERE status = 'pending'
  AND expires_at < now();
```

over iterating through every row and issuing individual updates.

Set-based SQL often allows PostgreSQL to optimize the operation more effectively.

This principle applies whether the query is executed directly by the application or inside a stored procedure.

---

## Stored Procedure Performance

Stored procedures can improve performance when they:

- Reduce round trips.
- Keep data processing close to the database.
- Reuse efficient set-based SQL.
- Avoid transferring large intermediate datasets to Python.

They can hurt performance when they:

- Perform procedural row-by-row loops.
- Hold transactions open for too long.
- Consume excessive database CPU.
- Create lock contention.
- Perform expensive computation on the primary database.
- Are called at extremely high concurrency.

A stored procedure moves computation to the database; it does not make computation free.

---

## Database CPU as a Shared Resource

In a typical backend architecture:

```text
Kubernetes
 ├── API Pod 1
 ├── API Pod 2
 ├── API Pod 3
 └── API Pod N
          ↓
      PostgreSQL
```

Application CPU scales horizontally by adding pods.

The primary database often remains a shared bottleneck.

Moving complex computation from Python into PostgreSQL can therefore increase pressure on:

- Database CPU.
- Memory.
- I/O.
- Connection capacity.
- Lock management.

Before moving logic into a stored procedure, ask:

> Can the database handle this workload at peak concurrency?

---

## Application Scaling vs Database Scaling

Suppose a service has:

```text
20 application pods
```

and a stored procedure performs expensive CPU-intensive work.

Every pod can call the procedure concurrently:

```text
20 pods
  ↓
20 concurrent procedure executions
  ↓
PostgreSQL
  ↓
High CPU
```

Adding more Kubernetes pods may make the database problem worse.

Application-side computation can sometimes scale more naturally because application workers can be horizontally distributed.

This is an important senior-level trade-off.

---

## External Services

Stored procedures are generally a poor fit for workflows involving external services.

For example:

```text
Order
 ↓
Payment provider
 ↓
Shipping provider
 ↓
Email provider
 ↓
Kafka
```

This belongs in application/service orchestration.

A database transaction cannot safely provide atomicity across PostgreSQL and an external HTTP API.

The appropriate architecture may use:

- Transactional outbox.
- Idempotency keys.
- Retry policies.
- Saga/workflow orchestration.
- Kafka.
- Celery.
- Durable state transitions.

---

## Transactional Outbox

A common architecture is:

```text
Application
    ↓
Database transaction
    ├── Business state
    └── Outbox event
              ↓
          CDC / Worker
              ↓
            Kafka
              ↓
        Other services
```

Application code owns the workflow while PostgreSQL guarantees atomic persistence of the business state and outbox record.

Example:

```sql
BEGIN;

UPDATE orders
SET status = 'confirmed'
WHERE id = $1;

INSERT INTO outbox_events (
    aggregate_id,
    event_type,
    payload
)
VALUES (
    $1,
    'order.confirmed',
    $2
);

COMMIT;
```

A background process then publishes the event.

This is usually preferable to trying to make a stored procedure communicate directly with Kafka or external services.

---

## Business Logic in Stored Procedures

Stored procedures can contain business rules:

```sql
IF p_amount > 10000 THEN
    ...
END IF;
```

The problem is not that this is inherently wrong.

The problem is ownership and maintainability.

If the rule changes frequently and is part of a large domain model, putting it in the database can make:

- Testing harder.
- Code review harder.
- Local development harder.
- Debugging harder.
- Deployment more complex.
- Cross-service behavior harder to coordinate.

If the rule is fundamentally a database invariant or data-local operation, database-side enforcement may be appropriate.

---

## Business Logic That Belongs in the Application

Application logic is usually preferable for:

### Domain Workflows

```text
Order
→ Payment
→ Inventory
→ Shipment
```

### External Integrations

```text
Payment API
Email API
Shipping API
```

### Complex Policies

```text
Subscription entitlement
Pricing rules
Feature eligibility
```

### User Interaction

```text
HTTP request
→ validation
→ authorization
→ domain logic
→ response
```

### Cross-Service Orchestration

```text
Service A
   ↓
Kafka
   ↓
Service B
   ↓
Service C
```

These concerns naturally belong in application/service architecture.

---

## Logic That Can Belong in the Database

Database-side logic is often appropriate for:

- Bulk data transformations.
- Complex set-based operations.
- Data cleanup.
- Database-local workflows.
- Specialized reporting operations.
- Controlled administrative operations.
- Operations requiring fewer network round trips.
- Shared database operations used by multiple clients.

For example:

```sql
CREATE PROCEDURE archive_old_orders(
    p_before timestamptz
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO archived_orders
    SELECT *
    FROM orders
    WHERE created_at < p_before;

    DELETE FROM orders
    WHERE created_at < p_before;
END;
$$;
```

For production use, this kind of operation would require additional consideration around foreign keys, locking, transaction size, WAL generation, bloat, failure recovery, and batch sizing.

---

## Stored Procedures and Large Data Operations

For large tables, a procedure can encapsulate batch processing.

However, avoid one enormous transaction:

```text
10 million rows
    ↓
One transaction
    ↓
Large locks
Large WAL
Long rollback
Replication lag
```

A production design may process smaller batches.

For example:

```sql
WITH batch AS (
    SELECT id
    FROM orders
    WHERE status = 'pending'
      AND expires_at < now()
    ORDER BY id
    LIMIT 5000
)
UPDATE orders AS o
SET status = 'expired'
FROM batch
WHERE o.id = batch.id;
```

This can be executed repeatedly by an application worker or batch process.

A stored procedure is not automatically the best orchestration mechanism for a long-running migration.

---

## Stored Procedures and Migrations

Stored procedures become schema objects and therefore should be version-controlled.

For Django:

```python
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0015_previous"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE PROCEDURE archive_old_orders(
                    p_before timestamptz
                )
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    DELETE FROM orders
                    WHERE created_at < p_before;
                END;
                $$;
            """,
            reverse_sql="""
                DROP PROCEDURE IF EXISTS archive_old_orders(timestamptz);
            """,
        ),
    ]
```

The procedure should be deployed through the same controlled CI/CD process as the schema.

Do not manually patch production procedures without recording the change.

---

## Deployment Coupling

A stored procedure introduces database/application version coupling.

Consider:

```text
Application v2
     ↓
Procedure v1
```

If the application expects a procedure signature or behavior that is not available, deployment can fail.

Use backward-compatible deployment strategies:

```text
Expand
  ↓
Deploy compatible application
  ↓
Switch behavior
  ↓
Contract
```

This is especially important in zero-downtime deployments.

---

## Procedure Signature Changes

Suppose the application currently calls:

```sql
CALL process_order($1, $2);
```

Changing the procedure to:

```sql
CALL process_order($1, $2, $3);
```

can break old application instances during rolling deployment.

Safer approaches may include:

- Creating a new procedure version.
- Supporting both signatures temporarily.
- Deploying the database change first.
- Migrating application callers.
- Removing the old interface later.

Database procedures can therefore behave like APIs.

---

## Stored Procedures as Internal APIs

A mature system can intentionally expose a controlled procedure interface:

```text
Application
    ↓
CALL create_order(...)
    ↓
Database procedure
    ↓
Multiple tables
```

This can be valuable when:

- Multiple clients need the same atomic operation.
- Database access should be constrained.
- The database is the authoritative owner of the operation.
- Direct table manipulation should be discouraged.

But it also creates database coupling.

Treat procedure signatures and semantics as contracts.

---

## Versioning Database APIs

If a procedure is consumed by multiple applications:

```text
Service A ─┐
Service B ─┼── PostgreSQL procedure
Admin Tool ─┘
```

changing the procedure can become equivalent to changing a shared API.

Consider:

```text
process_order_v1(...)
process_order_v2(...)
```

during migration if compatibility is required.

Avoid unnecessary version proliferation, but do not break consumers casually.

---

## Testing Stored Procedures

Stored procedures require database-aware tests.

Test:

- Valid inputs.
- Invalid inputs.
- Boundary conditions.
- NULL behavior.
- Concurrent execution.
- Transaction rollback.
- Constraint violations.
- Lock behavior.
- Permission behavior.
- Performance with realistic data volumes.

A unit test of Python code cannot fully validate PostgreSQL procedural behavior.

Integration tests should execute against PostgreSQL itself.

Docker-based CI environments are often useful for this:

```text
CI
 ↓
Docker PostgreSQL
 ↓
Apply migrations
 ↓
Create procedures
 ↓
Run integration tests
```

---

## Testing Application Logic

Application logic benefits from mature testing layers:

```text
Unit tests
    ↓
Service/domain tests
    ↓
Integration tests
    ↓
API tests
```

For example:

```python
def test_large_order_gets_discount():
    total = calculate_total(
        subtotal=Decimal("1500.00"),
        discount=Decimal("0.00"),
    )

    assert total == Decimal("1350.00")
```

This is typically simpler to test than embedding the same rule in PL/pgSQL.

---

## Observability

Stored procedures can make database-level observability more important.

Monitor:

- Procedure execution frequency.
- Query duration.
- Database CPU.
- Lock waits.
- Deadlocks.
- I/O.
- Temporary files.
- Replication lag.
- Connection utilization.

Use PostgreSQL query statistics and execution plans to investigate expensive statements generated or invoked by procedures.

For example:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...
```

A procedure call itself may not reveal the expensive internal SQL unless the underlying statements are investigated.

---

## Application Observability

Application logic provides richer application-level telemetry:

```text
HTTP request
    ↓
Trace
    ↓
Service method
    ↓
Database query
    ↓
External API
```

With OpenTelemetry-style tracing, it is easier to associate:

- Request ID.
- User/request context.
- Application operation.
- Database query.
- External dependency.

Stored procedures can still be traced at the database/query level, but the application generally has more context about the complete business workflow.

---

## Security

Stored procedures can support least privilege.

An application role may be given permission to execute a specific procedure rather than direct access to underlying tables.

Conceptually:

```text
Application role
       |
       +── EXECUTE procedure
                 ↓
          Controlled operation
                 ↓
             Base tables
```

This can reduce direct table manipulation.

However, stored procedures must be designed securely.

Consider:

- `SECURITY DEFINER`.
- Procedure/function ownership.
- `search_path`.
- Dynamic SQL.
- SQL injection.
- Input validation.
- Privilege escalation.
- RLS interaction.

If dynamic SQL is required, identifiers and values must be handled using the database's safe mechanisms rather than string concatenation.

---

## SECURITY DEFINER Considerations

PostgreSQL routines using `SECURITY DEFINER` execute with the privileges of the owner.

This can be powerful and dangerous.

A security-definer routine should:

- Have a minimally privileged owner.
- Avoid unsafe `search_path` behavior.
- Qualify object references where appropriate.
- Restrict who can execute it.
- Avoid unsafe dynamic SQL.
- Be tested using the actual caller role.

Do not grant broad execution rights on privileged routines without understanding the security boundary.

---

## Application Logic Security

Application logic is also responsible for:

- Authentication.
- Authorization.
- Input validation.
- Rate limiting.
- CSRF protection where applicable.
- API security.
- Secret management.
- External-service credentials.

A stored procedure should not become a substitute for application authorization.

Similarly, application authorization should not be the only protection for database invariants that can be enforced safely at the database layer.

---

## Stored Procedure vs Trigger

A stored procedure normally executes when explicitly invoked:

```sql
CALL process_order(...);
```

A trigger executes automatically in response to a database event.

```text
INSERT
  ↓
Trigger
  ↓
Database-side logic
```

Triggers are useful for specific database-level behavior but can make data flow less visible.

Do not introduce triggers merely because a procedure exists.

The important question remains:

> Should this behavior happen automatically whenever this database event occurs?

---

## Stored Procedure vs Function

PostgreSQL distinguishes procedures and functions.

A simplified comparison:

| Property | Function | Procedure |
|---|---|---|
| Invocation | `SELECT`, expression, etc. | `CALL` |
| Returns a value | Yes, normally | Not as a function result |
| Transaction control | More restricted | Procedures can have transaction-control capabilities when invoked in permitted contexts |
| Common use | Queryable computation | Explicit database operation |
| Can be used in SQL expressions | Yes | No |

For ordinary data-returning database logic, PostgreSQL functions are often the relevant construct.

For explicit database operations with procedure semantics, use procedures where their capabilities are appropriate.

---

## When Stored Procedures Are a Strong Fit

Stored procedures are a strong candidate when most of these are true:

- The operation is database-centric.
- The workload is set-oriented or data-intensive.
- Multiple database statements must be coordinated.
- Network round trips matter.
- The database should own the operation.
- The logic changes relatively infrequently.
- Multiple database clients need the same behavior.
- Database-level permissions are useful.
- External services are not part of the operation.

Examples:

- Bulk archival.
- Database maintenance workflows.
- Specialized batch transformations.
- Controlled financial ledger operations.
- Complex database-local state transitions.

---

## When Application Logic Is a Strong Fit

Application logic is usually preferable when:

- The behavior is domain-heavy.
- The workflow spans multiple services.
- External APIs are involved.
- Kafka events are involved.
- Redis is involved.
- The rule changes frequently.
- Rich testing is important.
- Domain abstractions are important.
- The application owns the workflow.

Examples:

- Subscription lifecycle.
- Checkout orchestration.
- Payment-provider integration.
- Notification workflows.
- Authorization policies.
- Cross-service business processes.

---

## Decision Matrix

| Requirement | Stored Procedure | Application Logic |
|---|---:|---:|
| Complex domain workflow | Poor fit | Excellent |
| Database-local transformation | Excellent | Good |
| Bulk data processing | Excellent | Good |
| External API integration | Poor fit | Excellent |
| Kafka orchestration | Poor fit | Excellent |
| Redis interaction | Poor fit | Excellent |
| Reduce DB round trips | Excellent | Limited |
| Database-level operation ownership | Excellent | Good |
| Easy unit testing | Moderate | Excellent |
| Rich domain modeling | Poor | Excellent |
| Multiple DB clients sharing operation | Excellent | Requires API |
| Database CPU efficiency | Depends | Depends |
| Enforce declarative invariant | Use constraint instead | Not sufficient alone |
| Long-running workflow | Usually poor | Excellent with workers |
| Stable DB-centric operation | Excellent | Good |

---

## Production Decision Framework

Use this decision process:

```text
Is the operation primarily data-local?
        |
       Yes
        |
        +── Is it set-based / database-intensive?
        |         |
        |        Yes
        |         ↓
        |   Consider database-side logic
        |
        No
        ↓
   Application logic


Does the workflow cross services or external systems?
        |
       Yes
        ↓
Application / workflow orchestration


Can the invariant be expressed as a constraint?
        |
       Yes
        ↓
Use a database constraint


Does the operation need durable asynchronous processing?
        |
       Yes
        ↓
Application worker / Celery / Kafka-based workflow
```

The decision should account for:

- Ownership.
- Performance.
- Failure handling.
- Deployment.
- Testing.
- Security.
- Operational complexity.
- Database capacity.
- Team expertise.

---

## Common Mistakes

### Putting All Business Logic in Stored Procedures

This can turn the database into an application runtime and make domain behavior difficult to test and evolve.

### Avoiding Stored Procedures on Principle

The opposite extreme is also problematic.

Database-centric, data-heavy operations can be excellent candidates for database-side execution.

### Using Application Checks Instead of Constraints

This creates race conditions when multiple clients operate concurrently.

Use:

```sql
UNIQUE
CHECK
FOREIGN KEY
EXCLUDE
```

where appropriate.

### Writing Row-by-Row PL/pgSQL

Prefer set-based SQL when possible.

### Calling External APIs From Database Logic

This creates problematic coupling and failure semantics.

Keep external orchestration in the application.

### Moving CPU-Heavy Work Into PostgreSQL

The database is a shared resource.

Database-side computation can become a production bottleneck.

### Creating Huge Stored-Procedure Transactions

Large transactions can cause:

- Lock contention.
- WAL growth.
- Replica lag.
- Long rollback times.
- Bloat.

Batch large operations when appropriate.

### Ignoring Connection Pooling

Stored procedures execute on a database connection and inherit the transaction/session context of that connection.

Understand pooling behavior before relying on session state.

### Treating Procedures as Unversioned Scripts

Procedure definitions are production code.

Version them through migrations and CI/CD.

### Changing Procedure Signatures During Rolling Deployments

Old application instances may still call the previous signature.

Use backward-compatible migration strategies.

### Using SECURITY DEFINER Without Security Review

Privileged routines can become privilege-escalation paths if ownership, `search_path`, dynamic SQL, or execution privileges are misconfigured.

---

## Interview Traps

### "Stored procedures are always faster."

False.

They can reduce round trips and data transfer, but they can also increase database CPU, locking, and contention.

### "Application logic is always better because Python is easier to maintain."

Not universally.

Database-centric, set-oriented operations can be more efficient and safer when executed close to the data.

### "A stored procedure guarantees atomicity."

Not automatically.

Correct transaction boundaries and database semantics still matter.

### "Application transactions cannot provide strong consistency."

They can.

Application transaction APIs such as Django `atomic()` or SQLAlchemy transaction contexts can use PostgreSQL transactional guarantees.

### "Stored procedures eliminate race conditions."

No.

Constraints, locks, isolation, and atomic operations determine concurrency correctness.

### "A UNIQUE check in application code is equivalent to a UNIQUE constraint."

No.

Concurrent transactions can both pass an application-side existence check.

### "Stored procedures are good for calling Kafka."

Generally no.

Use application workers, transactional outbox patterns, CDC, or messaging infrastructure.

### "Views, functions, procedures, and triggers are interchangeable."

They have different lifecycles, invocation models, permissions, and transaction semantics.

### "Putting business logic in the database means the application becomes stateless."

No.

Application workflows, caches, external services, and distributed state can still exist.

### "A procedure is just SQL saved under a name."

Not necessarily.

Procedures can contain procedural control flow, exception handling, transaction-related behavior, and database-side state manipulation.

---

## Production Checklist

Before introducing a stored procedure:

- Define database ownership of the operation.
- Confirm that the logic is genuinely data-local.
- Prefer set-based SQL over procedural row-by-row processing.
- Review transaction boundaries.
- Review locking and concurrency behavior.
- Check database CPU and memory capacity.
- Benchmark realistic workloads.
- Test failure and rollback behavior.
- Test concurrent execution.
- Review privileges.
- Review `SECURITY DEFINER` usage if applicable.
- Secure dynamic SQL.
- Version the procedure through migrations.
- Consider rolling-deployment compatibility.
- Monitor execution latency and database resource consumption.

Before keeping logic in the application:

- Confirm that the workflow is domain-oriented.
- Identify external-service dependencies.
- Use database transactions where required.
- Enforce invariants with database constraints where possible.
- Avoid unnecessary database round trips.
- Use bulk/set-based SQL for data-intensive operations.
- Instrument the workflow with application tracing.
- Design retries and idempotency for asynchronous operations.
- Test concurrency-sensitive behavior.
- Avoid pulling large datasets into Python unnecessarily.

---

## Key Takeaways

- **Stored procedures are strongest for controlled, database-centric operations:** especially set-based processing, complex data-local workflows, and operations where reducing database round trips matters.
- **Application logic is usually the better home for domain workflows and distributed orchestration:** particularly when Redis, Kafka, Celery, external APIs, or multiple services are involved.
- **Use database constraints for database invariants whenever possible:** a stored procedure or application-side existence check is not a substitute for `UNIQUE`, `CHECK`, `FOREIGN KEY`, or other declarative guarantees.
- **Moving logic into PostgreSQL moves computation onto a shared database resource:** evaluate CPU, memory, locking, transaction duration, replication lag, and concurrency before adopting database-side processing.
- **Treat stored procedures as production code and database APIs:** version them through migrations, test against PostgreSQL, secure privileged routines, and preserve compatibility during rolling deployments.