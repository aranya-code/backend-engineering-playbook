# 06- Date Addition and Subtraction

## Overview

Date and time arithmetic is a core SQL operation for backend systems that manage expiration windows, scheduling, billing periods, retention policies, SLAs, and event timelines.

In PostgreSQL, date/time arithmetic is primarily performed using:

- `+` and `-` operators.
- `INTERVAL` values.
- `AGE()` for calendar-oriented differences.
- Timestamp/date subtraction.
- `MAKE_INTERVAL()` when interval components need to be constructed dynamically.

The critical engineering distinction is between **elapsed time** and **calendar arithmetic**. Adding `24 hours` is not always equivalent to adding `1 day`, particularly when timezone-aware timestamps cross daylight-saving transitions.

## Date Arithmetic Operators

PostgreSQL supports direct arithmetic between date/time values and intervals.

```sql
SELECT DATE '2026-08-30' + INTERVAL '7 days';
```

Result:

```text
2026-09-06 00:00:00
```

Subtracting an interval:

```sql
SELECT TIMESTAMP '2026-08-30 14:30:00' - INTERVAL '2 hours';
```

Result:

```text
2026-08-30 12:30:00
```

The general model is:

```text
date/time value
      +
   interval
      =
new date/time value
```

and:

```text
date/time value
      -
   interval
      =
new date/time value
```

## `INTERVAL`

`INTERVAL` represents a duration or calendar-relative amount of time.

Common forms include:

```sql
INTERVAL '5 minutes'
INTERVAL '2 hours'
INTERVAL '7 days'
INTERVAL '3 weeks'
INTERVAL '2 months'
INTERVAL '1 year'
```

Multiple units can be combined:

```sql
INTERVAL '1 year 2 months 10 days'
```

For example:

```sql
SELECT
    TIMESTAMP '2026-08-30 10:00:00'
    + INTERVAL '1 day 3 hours';
```

Result:

```text
2026-08-31 13:00:00
```

### Common Interval Units

| Unit | Example | Typical use |
|---|---|---|
| Microsecond | `INTERVAL '500 microseconds'` | Fine-grained timing |
| Millisecond | `INTERVAL '250 milliseconds'` | Short operational windows |
| Second | `INTERVAL '30 seconds'` | Timeouts and SLAs |
| Minute | `INTERVAL '15 minutes'` | Scheduling |
| Hour | `INTERVAL '2 hours'` | Operational windows |
| Day | `INTERVAL '7 days'` | Retention and deadlines |
| Week | `INTERVAL '2 weeks'` | Business periods |
| Month | `INTERVAL '1 month'` | Billing/calendar periods |
| Year | `INTERVAL '1 year'` | Annual periods |

## Adding Days

Adding days is straightforward:

```sql
SELECT
    created_at,
    created_at + INTERVAL '30 days' AS expires_at
FROM subscriptions;
```

This is useful for:

- Trial expiration.
- Temporary access.
- Retention windows.
- Verification-token expiration.
- Scheduled processing.

A typical backend query might be:

```sql
SELECT id, email
FROM verification_tokens
WHERE expires_at <= CURRENT_TIMESTAMP
  AND used_at IS NULL;
```

For a system where expiration is derived from creation time:

```sql
SELECT
    id,
    created_at + INTERVAL '24 hours' AS expires_at
FROM verification_tokens;
```

For frequently evaluated expiration logic, storing the actual `expires_at` value is often preferable because it makes indexing and operational queries simpler.

## Adding Hours, Minutes, and Seconds

Use an explicit interval:

```sql
SELECT
    created_at + INTERVAL '2 hours' AS deadline
FROM jobs;
```

Multiple components can be combined:

```sql
SELECT
    created_at + INTERVAL '1 day 4 hours 30 minutes' AS deadline
FROM jobs;
```

This is useful for SLA calculations and scheduled processing.

For example:

```sql
SELECT id
FROM support_tickets
WHERE created_at + INTERVAL '4 hours' <= CURRENT_TIMESTAMP;
```

For a large production table, an indexed `due_at` column is generally preferable to calculating the deadline for every row.

## Adding Months and Years

Calendar arithmetic becomes more subtle with months and years.

```sql
SELECT DATE '2026-01-15' + INTERVAL '1 month';
```

Result:

```text
2026-02-15 00:00:00
```

A month is not a fixed number of seconds. Months have different lengths, so:

```sql
INTERVAL '1 month'
```

should not be treated as:

```text
30 days
```

Similarly:

```sql
INTERVAL '1 year'
```

should not be treated as:

```text
365 days
```

when calendar semantics matter.

## End-of-Month Behavior

Month arithmetic requires particular attention around dates near the end of a month.

For example:

```sql
SELECT DATE '2026-01-31' + INTERVAL '1 month';
```

PostgreSQL normalizes the resulting date according to its timestamp/date arithmetic rules rather than treating a month as a fixed 30-day duration.

This matters for:

- Monthly subscriptions.
- Billing cycles.
- Recurring invoices.
- Contract periods.
- Calendar-based notifications.

Do not assume that adding one month means "add exactly 30 days."

## Subtracting Dates

Subtracting one `DATE` from another produces an integer number of days.

```sql
SELECT DATE '2026-08-30' - DATE '2026-08-25';
```

Result:

```text
5
```

This is useful when only whole calendar days matter.

For example:

```sql
SELECT
    delivered_on - shipped_on AS delivery_days
FROM shipments;
```

## Subtracting Timestamps

Subtracting timestamps produces an `INTERVAL`.

```sql
SELECT
    TIMESTAMP '2026-08-30 15:00:00'
    - TIMESTAMP '2026-08-30 12:30:00';
```

Result:

```text
02:30:00
```

This is useful for elapsed-time analysis:

```sql
SELECT
    id,
    completed_at - started_at AS processing_duration
FROM jobs
WHERE completed_at IS NOT NULL;
```

## `AGE()`

`AGE()` calculates a symbolic difference between timestamps or dates.

```sql
SELECT AGE(
    TIMESTAMP '2026-08-30',
    TIMESTAMP '2025-06-15'
);
```

The result represents the difference using calendar-oriented units such as years, months, and days.

This differs from simple timestamp subtraction.

| Operation | Result style | Best suited for |
|---|---|---|
| `date - date` | Integer days | Calendar-day difference |
| `timestamp - timestamp` | Interval | Exact elapsed duration |
| `AGE()` | Years/months/days | Human/calendar-oriented difference |

Use `AGE()` when the distinction between months and days matters semantically.

## Elapsed Time vs Calendar Difference

This distinction is important in senior-level SQL work.

Suppose:

```text
start = 2025-01-31
end   = 2026-01-31
```

A human might describe this as:

```text
1 year
```

while an elapsed-duration calculation can represent the actual time interval between the timestamps.

Similarly, a billing system may care about:

```text
one calendar month
```

rather than:

```text
30 × 24 hours
```

Choose the arithmetic operation based on the business definition rather than convenience.

## `DATE` vs `TIMESTAMP` Arithmetic

The type of the input affects the result.

```sql
SELECT DATE '2026-08-30' + 7;
```

returns a `DATE`.

By contrast:

```sql
SELECT DATE '2026-08-30' + INTERVAL '7 days';
```

produces a timestamp-like result.

When the application requires a `DATE`, make the conversion explicit if necessary:

```sql
SELECT (
    DATE '2026-08-30' + INTERVAL '7 days'
)::date;
```

Avoid relying on implicit conversions in complex queries because they can obscure the intended data type.

## `TIMESTAMPTZ` and Time Zones

Timezone-aware arithmetic requires careful reasoning.

Consider:

```sql
SELECT
    TIMESTAMPTZ '2026-03-08 01:30:00-05'
    + INTERVAL '1 day';
```

With `TIMESTAMPTZ`, PostgreSQL represents an absolute instant and interprets it according to timezone rules when displaying or performing calendar-sensitive operations.

The important distinction is:

```text
INTERVAL '24 hours'
```

versus:

```text
INTERVAL '1 day'
```

Across daylight-saving transitions, these can have different wall-clock results.

### Practical Rule

If the requirement means:

> "Exactly 24 elapsed hours later"

use:

```sql
INTERVAL '24 hours'
```

If the requirement means:

> "The same local time on the next calendar day"

use:

```sql
INTERVAL '1 day'
```

This distinction matters for scheduling, notifications, reports, and recurring jobs.

## Business Calendar Arithmetic

Backend systems frequently need calendar-based calculations.

Examples:

```text
subscription renewal
invoice due date
trial expiration
password reset expiration
SLA deadline
reporting period
retention period
```

Consider a subscription:

```sql
SELECT
    subscription_id,
    started_at,
    started_at + INTERVAL '1 month' AS renewal_at
FROM subscriptions;
```

The business requirement determines whether the correct implementation is:

```text
one calendar month
```

or:

```text
30 days
```

Those are not equivalent.

## Parameterized Date Arithmetic

Application code should pass dynamic values as parameters rather than constructing SQL strings.

For example:

```sql
SELECT id, created_at
FROM orders
WHERE created_at >= $1
  AND created_at < $1 + INTERVAL '7 days';
```

The application supplies `$1` as a timestamp parameter.

This approach:

- Prevents SQL injection.
- Preserves query-plan reuse.
- Keeps business logic separate from SQL construction.
- Avoids formatting errors.

In Django or FastAPI applications using PostgreSQL drivers/ORMs, use the driver's parameterization facilities rather than interpolating dates into SQL strings.

## Dynamic Intervals

When the interval amount comes from a parameter, avoid unsafe SQL string construction.

Instead of generating SQL such as:

```text
INTERVAL '30 days'
```

through string interpolation, use PostgreSQL functions or arithmetic appropriate to the parameter type.

For example, if a number of days is supplied:

```sql
SELECT
    created_at + ($1 * INTERVAL '1 day') AS expires_at
FROM orders;
```

The application can pass:

```text
30
```

as `$1`.

This is safer and clearer than dynamically constructing SQL syntax.

## Date Arithmetic in Filtering

A common pattern is finding records older than a fixed period:

```sql
SELECT id
FROM events
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
```

This is useful for retention jobs and cleanup operations.

However, for production systems, an explicit indexed column comparison is generally preferable to wrapping the indexed column in a function.

Good:

```sql
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
```

Potentially problematic:

```sql
WHERE created_at + INTERVAL '30 days' < CURRENT_TIMESTAMP
```

The first form leaves the indexed column directly on one side of the comparison.

For large tables, verify with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM events
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
```

## Calculating Expiration Times

For security-sensitive tokens, a production design commonly stores an explicit expiration timestamp:

```sql
CREATE TABLE password_reset_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    token_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ
);
```

The application can calculate:

```text
expires_at = created_at + configured lifetime
```

and persist it.

Then expiration checks become simple:

```sql
SELECT id
FROM password_reset_tokens
WHERE expires_at <= CURRENT_TIMESTAMP
  AND used_at IS NULL;
```

This is operationally preferable to recalculating expiration from `created_at` for every request.

## Recurring Schedules

Calendar arithmetic also appears in recurring jobs.

For example:

```sql
SELECT
    last_run_at + INTERVAL '1 day' AS next_run_at
FROM scheduled_jobs;
```

However, recurring scheduling is more complex than simply adding a fixed interval when requirements include:

- Time zones.
- Daylight-saving changes.
- Business days.
- Holidays.
- Month-end rules.
- Missed executions.
- Retry semantics.

For these cases, application-level scheduling systems such as Celery or dedicated schedulers may be more appropriate, with SQL storing the authoritative schedule state.

## Date Arithmetic and Indexes

Suppose a table contains millions of events:

```sql
CREATE INDEX idx_events_created_at
ON events (created_at);
```

Prefer:

```sql
SELECT COUNT(*)
FROM events
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours';
```

over:

```sql
SELECT COUNT(*)
FROM events
WHERE created_at + INTERVAL '24 hours' >= CURRENT_TIMESTAMP;
```

The first formulation naturally expresses the indexed column as the value being compared against a calculated boundary.

This pattern is especially important for:

- Retention queries.
- Time-window analytics.
- Monitoring queries.
- Queue processing.
- Operational dashboards.

## Date Arithmetic and Partitioning

Time-partitioned tables benefit from predicates that expose explicit timestamp boundaries.

For example:

```sql
SELECT COUNT(*)
FROM events
WHERE created_at >= TIMESTAMPTZ '2026-08-01 00:00:00+00'
  AND created_at <  TIMESTAMPTZ '2026-09-01 00:00:00+00';
```

This makes the intended range explicit and can help PostgreSQL eliminate irrelevant partitions.

For large event systems, partitioning should be designed together with:

- Query patterns.
- Retention requirements.
- Index strategy.
- Vacuum behavior.
- Archival strategy.
- Backup and recovery requirements.

## `MAKE_INTERVAL()`

When interval components are dynamic, PostgreSQL provides `MAKE_INTERVAL()`.

For example:

```sql
SELECT MAKE_INTERVAL(
    days => 30,
    hours => 4
);
```

This is useful when values are supplied independently:

```sql
SELECT
    created_at + MAKE_INTERVAL(
        days => $1,
        hours => $2
    ) AS deadline
FROM jobs;
```

It is preferable to constructing SQL interval literals through string concatenation.

## Negative Intervals

Intervals can be negative:

```sql
SELECT INTERVAL '-3 days';
```

or:

```sql
SELECT
    created_at - INTERVAL '3 days'
FROM orders;
```

Equivalent arithmetic can sometimes be expressed either way:

```sql
created_at - INTERVAL '3 days'
```

or:

```sql
created_at + INTERVAL '-3 days'
```

Prefer the form that most clearly communicates the business operation.

## NULL Behavior

Date arithmetic propagates `NULL`.

```sql
SELECT
    NULL::timestamp + INTERVAL '7 days';
```

Result:

```text
NULL
```

Likewise:

```sql
SELECT
    shipped_at - delivered_at
FROM shipments;
```

returns `NULL` when either timestamp is `NULL`.

This is generally desirable because a missing date represents missing information rather than zero duration.

If a default is genuinely required:

```sql
SELECT COALESCE(delivered_at - shipped_at, INTERVAL '0 seconds')
FROM shipments;
```

Use this carefully. Converting an unknown duration into zero can hide data-quality problems.

## Transaction Time and Current Time

PostgreSQL provides several current-time concepts.

For most SQL operations:

```sql
CURRENT_TIMESTAMP
```

represents the current transaction timestamp.

For example:

```sql
SELECT CURRENT_TIMESTAMP + INTERVAL '30 minutes';
```

Within a transaction, the transaction timestamp remains stable.

This is usually desirable for consistency.

If an operation specifically requires the actual wall-clock time at execution, PostgreSQL also provides:

```sql
clock_timestamp()
```

These should not be treated as interchangeable.

| Function | Behavior |
|---|---|
| `CURRENT_TIMESTAMP` | Transaction start time |
| `statement_timestamp()` | Start time of the current statement |
| `clock_timestamp()` | Actual wall-clock time when evaluated |

For deterministic database operations, `CURRENT_TIMESTAMP` is generally the safer default.

## Production Example: Event Retention

Suppose an event-processing service retains raw events for 30 days.

A cleanup operation can use:

```sql
DELETE FROM events
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
```

For a high-volume system, do not blindly execute one massive `DELETE`.

Consider:

- Batch deletion.
- Time-based partitioning.
- Partition dropping for retention.
- Lock duration.
- WAL generation.
- Replica lag.
- Autovacuum impact.
- Monitoring deletion throughput.

For very large append-only event tables, partition-based retention can be significantly more operationally efficient than repeatedly deleting individual rows.

## Production Example: SLA Monitoring

Suppose API requests have a four-hour processing SLA.

A query can identify overdue requests:

```sql
SELECT id, created_at
FROM requests
WHERE completed_at IS NULL
  AND created_at < CURRENT_TIMESTAMP - INTERVAL '4 hours';
```

An operational system can then:

```mermaid
flowchart LR
    Events["Requests"]
    DB["PostgreSQL"]
    Query["SLA Query"]
    Worker["Worker / Celery"]
    Alert["Alerting"]

    Events --> DB
    DB --> Query
    Query --> Worker
    Worker --> Alert
```

For high-scale systems, index the columns supporting the actual access pattern and measure the query with `EXPLAIN (ANALYZE, BUFFERS)`.

## Common Mistakes

### Treating a Month as 30 Days

Incorrect assumption:

```text
1 month = 30 days
```

Calendar months have different lengths.

Use:

```sql
INTERVAL '1 month'
```

when the business requirement is calendar-based.

Use:

```sql
INTERVAL '30 days'
```

when the requirement is explicitly a 30-day duration.

### Treating a Day as Always 24 Hours

For timezone-aware scheduling, these concepts can differ around daylight-saving transitions:

```sql
INTERVAL '1 day'
```

and:

```sql
INTERVAL '24 hours'
```

Choose based on whether the requirement is calendar-relative or elapsed-time-based.

### Wrapping Indexed Columns in Arithmetic

Avoid:

```sql
WHERE created_at + INTERVAL '30 days' < CURRENT_TIMESTAMP
```

when the equivalent boundary can be calculated once:

```sql
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
```

The latter is generally friendlier to index and partition pruning strategies.

### Building Dynamic SQL Intervals with String Concatenation

Avoid:

```text
'INTERVAL ''' || user_input || ' days'''
```

Dynamic SQL construction can introduce correctness and security problems.

Use parameters with interval arithmetic or `MAKE_INTERVAL()`.

### Using SQL String Formatting for Dates

Avoid converting dates into strings before performing arithmetic.

Prefer native date/time types:

```sql
created_at + INTERVAL '7 days'
```

rather than formatting and reparsing timestamps.

### Ignoring NULL

Do not assume:

```sql
NULL + INTERVAL '1 day'
```

becomes the original value or zero.

It becomes `NULL`.

### Mixing Business and Database Timezones

A service may run in UTC while users operate in local time zones.

Do not assume that:

```sql
CURRENT_TIMESTAMP + INTERVAL '1 day'
```

automatically means "tomorrow at the user's local time."

Timezone-aware business rules must explicitly define the relevant timezone.

## Interview Traps

| Question | Strong answer |
|---|---|
| How do you add seven days? | `timestamp + INTERVAL '7 days'` |
| What does `date - date` return? | An integer number of days |
| What does `timestamp - timestamp` return? | An `INTERVAL` |
| When should `AGE()` be used? | For calendar-oriented differences expressed in years/months/days |
| Is one month equal to 30 days? | No; month length varies |
| Is one day always exactly 24 hours? | Not necessarily when timezone/DST semantics are involved |
| How should a large retention query be written? | Prefer an indexed timestamp boundary such as `created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'` |
| How should dynamic interval values be supplied? | Use parameters with interval arithmetic or `MAKE_INTERVAL()` rather than constructing SQL strings |
| What happens when date arithmetic involves `NULL`? | The result is generally `NULL` |
| Why store `expires_at` instead of recalculating it? | It simplifies indexing, querying, auditing, and operational processing |
| What is the difference between `CURRENT_TIMESTAMP` and `clock_timestamp()`? | `CURRENT_TIMESTAMP` is transaction-stable; `clock_timestamp()` reflects the actual wall clock |

## Key Takeaways

- **Use `INTERVAL` with native date/time types for date arithmetic; do not convert dates to strings before performing calculations.**
- **Distinguish calendar arithmetic (`1 month`, `1 day`) from fixed elapsed durations (`30 days`, `24 hours`) because they can have different business and timezone semantics.**
- **For high-volume filtering, calculate the time boundary separately and compare the indexed timestamp column directly.**
- **Use `AGE()` for human/calendar-oriented differences and timestamp subtraction for elapsed durations.**
- **Make timezone and NULL behavior explicit in production systems, especially for scheduling, billing, expiration, and SLA logic.**