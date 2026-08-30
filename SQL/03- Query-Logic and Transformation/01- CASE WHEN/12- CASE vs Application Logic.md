# 12- CASE vs Application Logic

## Overview

`CASE` allows conditional logic to execute inside the database query. Application code such as Python can perform the same logical transformation after rows have been retrieved.

The engineering decision is not simply "SQL or Python." It is about **where the logic belongs in the data flow**.

```text
Database
   │
   │ filtering / joining / aggregation
   ▼
SQL result
   │
   │ application-level behavior
   ▼
Django / FastAPI / service layer
   │
   ▼
API / gRPC response
```

A useful rule is:

> Put data-oriented logic close to the data, and application behavior close to the application.

For example, deriving a database classification:

```sql
CASE
    WHEN total_amount >= 10000 THEN 'enterprise'
    WHEN total_amount >= 1000 THEN 'business'
    ELSE 'standard'
END AS customer_tier
```

is usually a good SQL responsibility.

By contrast, deciding whether an HTTP response should trigger a particular workflow may belong in application code.

## Why the Boundary Matters

Conditional logic can appear at multiple layers:

```text
PostgreSQL
    ↓
Django / FastAPI
    ↓
Service layer
    ↓
Serializer / response model
    ↓
Client
```

If the same rule is implemented independently in multiple layers, the system can develop conflicting definitions.

For example:

```text
SQL:
balance > 1000 → "high_risk"

Python:
balance >= 1000 → "high_risk"
```

The boundary difference of one operator can produce inconsistent API responses, reports, background jobs, and dashboards.

The goal is therefore not to maximize SQL or minimize application logic. The goal is to establish **one authoritative implementation for each important rule**.

## When CASE Belongs in SQL

`CASE` is generally appropriate when the logic:

- Operates directly on database columns.
- Is needed for filtering, grouping, aggregation, or ordering.
- Reduces data before transferring it to the application.
- Represents a database-derived classification.
- Is useful to multiple consumers of the same query.
- Can be expressed naturally using relational data.

Example:

```sql
SELECT
    order_id,
    total_amount,
    CASE
        WHEN total_amount >= 10000 THEN 'large'
        WHEN total_amount >= 1000 THEN 'medium'
        ELSE 'small'
    END AS order_size
FROM orders;
```

The database already has `total_amount`, so calculating `order_size` while querying avoids transferring unnecessary raw data and duplicating the classification in application code.

## When Application Logic Belongs in Python

Application code is usually a better location when the logic:

- Depends on external services.
- Requires complex domain workflows.
- Uses user-specific runtime state.
- Depends on configuration outside the database.
- Performs side effects.
- Requires complex control flow.
- Is primarily presentation behavior.
- Is easier to unit-test as domain code.
- Combines data from several independent sources.

For example:

```python
def should_require_manual_review(order, fraud_score, feature_flags):
    if feature_flags.manual_review_disabled:
        return False

    if order.total_amount >= 10_000 and fraud_score >= 0.8:
        return True

    return order.customer_is_new and fraud_score >= 0.6
```

This is not naturally a database concern if `fraud_score` and feature-flag state come from other systems.

## Data Logic vs Domain Logic

A useful distinction is between **data transformation** and **domain behavior**.

| Type of logic | Typical location |
| --- | --- |
| Replace `NULL` with a fallback | SQL |
| Classify rows by database columns | SQL |
| Conditional aggregation | SQL |
| Sort by derived priority | SQL |
| Filter records according to query requirements | SQL |
| Validate an HTTP request | Application |
| Call an external API | Application |
| Coordinate a business workflow | Application |
| Publish Kafka events | Application |
| Send email | Application |
| Apply presentation-specific formatting | Application |
| Enforce cross-system business rules | Usually application/service layer |

The boundary is not absolute. The correct placement depends on ownership, reuse, performance, consistency, and operational requirements.

## Example: Customer Segmentation

Suppose the database contains:

```text
customers
├── id
├── annual_revenue
├── employee_count
└── country
```

A query needs to return a customer segment.

SQL is a natural location:

```sql
SELECT
    id,
    CASE
        WHEN annual_revenue >= 10000000
             AND employee_count >= 1000
            THEN 'enterprise'
        WHEN annual_revenue >= 1000000
            THEN 'business'
        ELSE 'standard'
    END AS segment
FROM customers;
```

The classification is based entirely on relational data.

If multiple backend services need the same segmentation, centralizing the transformation at the data layer can also reduce duplicated implementation.

## Example: Application-Specific Behavior

Now suppose the application must decide whether to show a promotional banner.

The decision depends on:

- Customer segment.
- Current feature flags.
- Experiment assignment.
- Marketing configuration.
- Recent interaction with another service.

This is better handled outside SQL:

```python
def should_show_banner(customer_segment, experiment, feature_flags):
    if not feature_flags.promotions_enabled:
        return False

    if experiment.variant != "treatment":
        return False

    return customer_segment in {"business", "enterprise"}
```

The SQL query can provide the segment:

```sql
SELECT
    id,
    CASE
        WHEN annual_revenue >= 10000000 THEN 'enterprise'
        WHEN annual_revenue >= 1000000 THEN 'business'
        ELSE 'standard'
    END AS segment
FROM customers;
```

The application then applies runtime behavior.

## CASE in WHERE vs Application Filtering

One of the most important production distinctions is whether the database should filter rows before transmission.

Avoid:

```python
orders = Order.objects.all()

large_orders = [
    order
    for order in orders
    if order.total_amount >= 1000
]
```

when the requirement is simply to retrieve qualifying rows.

Prefer database filtering:

```python
large_orders = Order.objects.filter(total_amount__gte=1000)
```

which produces a database predicate rather than retrieving unnecessary rows.

Similarly, do not fetch thousands of rows merely to classify them in Python if the classification can be performed efficiently in SQL.

## CASE in SELECT vs Python Transformation

Suppose an API needs an order priority:

```text
urgent
high
normal
```

The SQL can derive it:

```sql
SELECT
    order_id,
    CASE
        WHEN status = 'failed' THEN 'urgent'
        WHEN total_amount >= 10000 THEN 'high'
        ELSE 'normal'
    END AS priority
FROM orders;
```

The application receives the already-derived value.

This can be useful when:

- The query already scans the rows.
- The derived value is needed by the API.
- The same classification is needed by reports.
- Moving the computation avoids unnecessary application processing.

However, if the priority depends on application-only state, compute it in the application.

## CASE in GROUP BY

SQL is particularly valuable when the derived classification participates in aggregation.

```sql
SELECT
    CASE
        WHEN total_amount >= 10000 THEN 'large'
        WHEN total_amount >= 1000 THEN 'medium'
        ELSE 'small'
    END AS order_size,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY
    CASE
        WHEN total_amount >= 10000 THEN 'large'
        WHEN total_amount >= 1000 THEN 'medium'
        ELSE 'small'
    END;
```

Moving this grouping to Python would require transferring all relevant rows to the application before aggregation.

For large datasets, that is usually the wrong architecture.

The database is optimized for:

```text
scan → classify → aggregate → return small result
```

rather than:

```text
scan → transfer millions of rows → Python → classify → aggregate
```

## CASE with ORDER BY

A common use of `CASE` is expressing custom database-side priority.

```sql
SELECT
    id,
    status,
    created_at
FROM orders
ORDER BY
    CASE status
        WHEN 'failed' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'processing' THEN 3
        WHEN 'completed' THEN 4
        ELSE 5
    END,
    created_at ASC;
```

The database can perform the ordering before returning the result.

Implementing the same ordering after fetching rows is usually inferior when the database can perform it as part of the query.

## Network Cost Matters

Database/application boundaries are also performance boundaries.

Consider one million rows.

### Database-side transformation

```text
PostgreSQL
   │
   ├── read rows
   ├── evaluate CASE
   ├── aggregate/filter
   │
   ▼
10,000 relevant rows
   │
   ▼
Application
```

### Application-side transformation

```text
PostgreSQL
   │
   ▼
1,000,000 rows
   │
   │ network transfer
   ▼
Application
   │
   ├── classify
   ├── filter
   └── aggregate
```

The second approach can increase:

- Network bandwidth.
- Database connection time.
- Application memory usage.
- Python CPU consumption.
- Garbage collection pressure.
- API latency.

For data-intensive operations, pushing appropriate computation into SQL can significantly reduce total system work.

## Do Not Push Everything Into SQL

The opposite mistake is equally dangerous.

A query containing deeply nested business rules can become difficult to maintain:

```sql
SELECT
    CASE
        WHEN ...
            THEN CASE
                WHEN ...
                    THEN CASE
                        WHEN ...
                            THEN ...
                        ELSE ...
                    END
                ELSE ...
            END
        ELSE ...
    END
FROM orders;
```

If the logic is effectively a domain workflow, SQL may no longer be the best representation.

Signs that logic has become too application-heavy for SQL include:

- Multiple external dependencies.
- Complex state transitions.
- Side effects.
- Many unrelated business concepts.
- Difficult-to-test procedural behavior.
- Large numbers of configuration-dependent branches.

In those cases, keep SQL responsible for producing the required data and move domain orchestration into the service layer.

## Maintainability Trade-Off

| Approach | Strength | Risk |
| --- | --- | --- |
| SQL `CASE` | Efficient data-side transformation | Complex rules can become difficult to maintain |
| Python conditionals | Flexible and testable | Can require transferring too much data |
| Database function | Reusable database-side rule | Increases database coupling |
| Mapping table | Data-driven and maintainable | Requires additional schema/data management |
| Service/domain layer | Good for complex workflows | Can duplicate data logic if poorly designed |

The right choice depends on the rule's ownership and execution context.

## Reusing Business Rules

Suppose the business defines:

```text
Customer is high value when:
annual_revenue >= 10M
OR
lifetime_value >= 1M
```

If this rule appears in:

- REST API.
- Admin dashboard.
- Kafka consumer.
- Scheduled Celery task.
- Analytics query.

implementing it separately in every component creates drift.

Possible strategies include:

### Database-Derived Classification

```sql
CASE
    WHEN annual_revenue >= 10000000
         OR lifetime_value >= 1000000
        THEN 'high_value'
    ELSE 'standard'
END
```

Useful when the classification is fundamentally data-derived and widely consumed.

### Mapping or Rule Table

For frequently changing business thresholds, store rules as data rather than hard-coding them into dozens of queries.

```text
customer_segments
├── segment
├── minimum_revenue
├── minimum_lifetime_value
└── priority
```

This can make changes operationally safer when business users or configuration workflows control thresholds.

### Domain Service

Use a shared application-level service when the rule requires application context:

```python
class CustomerClassificationService:
    def classify(self, customer, account_data, risk_data):
        ...
```

The key is to establish a **single source of truth**, not merely choose SQL because it is shorter.

## Security Considerations

`CASE` itself is not a security boundary.

Do not assume that hiding a sensitive value through a `CASE` expression provides authorization.

For example:

```sql
CASE
    WHEN is_admin THEN salary
    ELSE NULL
END
```

may be useful for presentation, but authorization should be enforced using proper access-control mechanisms.

Similarly, application code should not retrieve data that the caller is not authorized to access merely because it plans to remove sensitive fields later.

Prefer:

```text
authorization/filtering
        ↓
database query
        ↓
authorized dataset
        ↓
conditional transformation
        ↓
API response
```

Data minimization should happen as early as practical.

## Testing Strategy

The location of conditional logic affects how it should be tested.

### SQL Logic

Test:

- Boundary values.
- `NULL` values.
- Every `WHEN` branch.
- `ELSE` behavior.
- Type behavior.
- Interaction with joins and aggregation.

For:

```sql
CASE
    WHEN amount >= 1000 THEN 'large'
    ELSE 'small'
END
```

test at least:

```text
999
1000
1001
NULL
```

### Application Logic

Test domain behavior independently:

```python
def classify_amount(amount):
    if amount >= 1000:
        return "large"
    return "small"
```

If the rule exists in both SQL and Python, contract or integration tests should verify that both implementations produce identical results.

The stronger architectural solution, however, is often to avoid maintaining two independent implementations.

## Observability

Conditional SQL logic can affect production behavior without appearing obvious from application code.

For important queries monitor:

- Query latency.
- Rows scanned.
- Rows returned.
- Execution-plan changes.
- Database CPU.
- Buffer/cache behavior.
- Query frequency.

Use tools such as:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    CASE
        WHEN total_amount >= 10000 THEN 'large'
        ELSE 'normal'
    END AS order_size
FROM orders;
```

For application-side transformations, monitor:

- CPU usage.
- Memory allocation.
- Request latency.
- Serialization time.
- Database-to-application payload size.

The correct location is partly an operational decision: measure where the work actually costs the system.

## Production Decision Framework

When deciding between SQL `CASE` and application logic, ask:

| Question | If yes |
| --- | --- |
| Does the logic operate only on database values? | Prefer SQL |
| Is the result needed for `WHERE`, `GROUP BY`, or `ORDER BY`? | Prefer SQL |
| Can SQL reduce the number of rows transferred? | Strong SQL candidate |
| Does the logic require another service? | Prefer application/service layer |
| Does it cause side effects? | Application |
| Is it presentation-only? | Usually application |
| Is it a complex domain workflow? | Application/service layer |
| Is the rule shared by many database consumers? | Consider database-side implementation |
| Does the rule change frequently as business configuration? | Consider data-driven rules |
| Would SQL make the query unmaintainable? | Move appropriate logic upward |

This avoids the simplistic rule of "business logic never belongs in SQL."

## Anti-Patterns

### Fetch Everything and Filter in Python

```python
orders = list(Order.objects.all())

orders = [
    order
    for order in orders
    if order.status == "pending"
]
```

This wastes database, network, and application resources.

Use:

```python
orders = Order.objects.filter(status="pending")
```

### Duplicating CASE Logic in Python

SQL:

```sql
CASE
    WHEN amount >= 1000 THEN 'large'
    ELSE 'small'
END
```

Python:

```python
if amount > 1000:
    size = "large"
else:
    size = "small"
```

The boundary mismatch produces inconsistent results for exactly `1000`.

Avoid duplicated rules unless there is a deliberate synchronization strategy.

### Putting External Service Calls Into Database Logic

Do not design SQL transformations around assumptions that the database can directly coordinate external application services.

Keep external integration logic in the service layer.

### Using Application Logic for Large Aggregations

Avoid:

```python
orders = list(Order.objects.all())

revenue = sum(
    order.amount
    for order in orders
    if order.status == "completed"
)
```

Prefer:

```sql
SELECT COALESCE(SUM(amount), 0)
FROM orders
WHERE status = 'completed';
```

Let the database process the data where the aggregation belongs.

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| Should all business logic be kept out of SQL? | No; data-derived rules can legitimately belong in SQL |
| When is `CASE` preferable to Python? | When the transformation is database-oriented or reduces data before transfer |
| Why filter in SQL instead of Python? | It reduces rows scanned by the application, network transfer, memory, and application CPU |
| Should complex workflows be implemented with `CASE`? | Usually no; workflow orchestration belongs in application/service logic |
| Is SQL always faster than Python? | No; performance depends on the operation, indexes, plans, data volume, and architecture |
| What is the biggest architectural risk of duplicated logic? | Different layers can implement subtly different versions of the same rule |
| When should application logic be preferred? | When logic depends on external systems, runtime configuration, side effects, or complex domain workflows |
| Can SQL implement business logic? | Yes, when the business rule is naturally data-oriented and database-side execution provides value |
| Why can application-side transformation be expensive? | It may require transferring and materializing many rows before computation |
| Is a `CASE` expression an authorization mechanism? | No; authorization must be enforced through proper access-control and data-access mechanisms |

## Key Takeaways

- Use SQL `CASE` for data-oriented conditional transformations, especially when filtering, grouping, ordering, or reducing data before it reaches the application.
- Use application logic for workflows, external dependencies, side effects, runtime configuration, and complex domain behavior.
- Avoid duplicating the same business rule independently in SQL and Python; establish a clear source of truth to prevent semantic drift.
- Do not move large database operations into Python merely because application code is easier to write; network transfer, memory, CPU, and latency can become the real bottleneck.
- Choose the boundary based on data ownership, performance, maintainability, reuse, and operational requirements rather than treating SQL or application logic as universally superior.