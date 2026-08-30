# 17- Common Date and Time Mistakes

## Overview

Date and time bugs are rarely caused by syntax. They usually come from incorrect assumptions about **time zones, precision, calendar boundaries, data types, intervals, or query semantics**.

A production backend may process the same event across:

- PostgreSQL
- Python
- Django or FastAPI
- Redis
- Kafka
- Celery workers
- Docker and Kubernetes
- Multiple AWS regions
- Users in different time zones

A timestamp can therefore change representation several times while still referring to the same instant. The engineering goal is to preserve the intended temporal meaning throughout that lifecycle.

The most reliable approach is to define temporal semantics explicitly:

```text
Business requirement
       ↓
Calendar date or absolute instant?
       ↓
Choose appropriate SQL type
       ↓
Define timezone semantics
       ↓
Define range boundaries
       ↓
Query using native temporal values
       ↓
Format only at the presentation boundary
```

## The Core Mental Model

There are three concepts that must not be confused:

| Concept | Meaning | Example |
|---|---|---|
| Instant | A specific point on the global timeline | `2026-08-30T10:00:00Z` |
| Local date/time | A calendar representation in a timezone | `2026-08-30 15:30 Asia/Kolkata` |
| Duration | Amount of elapsed time | `90 minutes` |

A major source of bugs is treating one as another.

For example:

```text
"August 30"
```

is a calendar date, not an instant.

Whereas:

```text
2026-08-30T00:00:00Z
```

is a specific instant.

Likewise:

```text
"1 month"
```

is a calendar period and should not automatically be interpreted as a fixed number of seconds.

## Mistake: Choosing the Wrong Data Type

The database type should match the business meaning of the value.

In PostgreSQL:

| Type | Meaning | Typical use |
|---|---|---|
| `DATE` | Calendar date without time | Birthday, invoice date |
| `TIME` | Time of day without date | Store opening time |
| `TIMESTAMP` | Date and time without timezone semantics | Local/business wall-clock value |
| `TIMESTAMPTZ` | Timestamp interpreted as an absolute instant | Events, audit timestamps |
| `INTERVAL` | Temporal duration/period | Retention period, scheduling interval |

For an event such as:

```text
Order created at 2026-08-30 10:15 UTC
```

an absolute timestamp is normally required:

```sql
created_at TIMESTAMPTZ NOT NULL
```

For a customer's birthday:

```sql
birth_date DATE NOT NULL
```

Using a timestamp for a value that is fundamentally a calendar date introduces unnecessary timezone semantics.

### Production Rule

Ask:

> **Does this value represent an instant, a calendar value, or a duration?**

Choose the type accordingly.

## Mistake: Treating `TIMESTAMP` and `TIMESTAMPTZ` as Equivalent

PostgreSQL's names are easy to misunderstand.

`TIMESTAMP` means:

```text
timestamp without time zone
```

It represents a date/time value without an associated timezone interpretation.

`TIMESTAMPTZ` means:

```text
timestamp with time zone
```

It represents an instant. PostgreSQL stores the instant and displays it according to the session timezone.

For example:

```sql
CREATE TABLE events (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

For distributed backend systems, `TIMESTAMPTZ` is usually the safer choice for event timestamps because the value represents a global instant.

### Important Detail

`TIMESTAMPTZ` does **not** preserve the original timezone string.

If a client sends:

```text
2026-08-30T15:30:00+05:30
```

PostgreSQL stores the corresponding instant, not the fact that the user originally supplied `+05:30`.

If the original user timezone matters for future business logic, store it separately.

For example:

```sql
CREATE TABLE user_preferences (
    user_id BIGINT PRIMARY KEY,
    timezone TEXT NOT NULL
);
```

## Mistake: Mixing Naive and Timezone-Aware Datetimes

Python distinguishes between naive and timezone-aware `datetime` objects.

Naive:

```python
from datetime import datetime

value = datetime.now()
```

Timezone-aware:

```python
from datetime import datetime, UTC

value = datetime.now(UTC)
```

For distributed applications, prefer timezone-aware values for instants.

A dangerous pattern is mixing:

```text
naive datetime
+
UTC datetime
+
local server time
+
database timestamp
```

and assuming they represent the same thing.

In Django, use timezone-aware datetimes when timezone support is enabled.

```python
from django.utils import timezone

now = timezone.now()
```

Avoid manually attaching a timezone to a datetime merely by replacing its `tzinfo` unless you understand whether the existing value is a wall-clock representation or an actual instant.

## Mistake: Using Server Local Time

This is dangerous:

```python
from datetime import datetime

created_at = datetime.now()
```

because the result depends on the machine's timezone configuration.

The application may run on:

```text
Developer laptop → Asia/Kolkata
Docker → UTC
Kubernetes node → UTC
Production region → another configuration
```

The same code can therefore produce different results.

Prefer an explicit timezone-aware instant:

```python
from datetime import datetime, UTC

created_at = datetime.now(UTC)
```

or the framework's timezone abstraction.

## Mistake: Using `CURRENT_TIMESTAMP` Without Understanding Its Semantics

In PostgreSQL:

```sql
SELECT CURRENT_TIMESTAMP;
```

and:

```sql
SELECT now();
```

represent the current transaction timestamp.

They do not continuously advance during a long-running transaction.

If actual wall-clock time is required:

```sql
SELECT clock_timestamp();
```

The distinction matters for:

- Transaction diagnostics.
- Long-running jobs.
- Performance measurements.
- Operational instrumentation.

Do not substitute one for the other without understanding the requirement.

## Mistake: Filtering by Casting the Timestamp

A common query is:

```sql
SELECT *
FROM orders
WHERE created_at::date = DATE '2026-08-30';
```

Although logically understandable, this transforms the column.

For a large table with:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

prefer:

```sql
SELECT *
FROM orders
WHERE created_at >= TIMESTAMPTZ '2026-08-30 00:00:00+00'
  AND created_at <  TIMESTAMPTZ '2026-08-31 00:00:00+00';
```

This allows the database to use the timestamp index naturally.

### General Rule

Prefer:

```sql
column >= :start
AND column < :end
```

over:

```sql
FUNCTION(column) = :value
```

when both express the same business requirement.

## Mistake: Using `BETWEEN` for Timestamp Days

This pattern is problematic:

```sql
WHERE created_at BETWEEN
    '2026-08-30 00:00:00'
    AND
    '2026-08-30 23:59:59';
```

It assumes that `23:59:59` is the final possible timestamp.

That assumption fails when the database stores fractional seconds.

A record such as:

```text
2026-08-30 23:59:59.500000
```

would be excluded.

Prefer:

```sql
WHERE created_at >= TIMESTAMPTZ '2026-08-30 00:00:00+00'
  AND created_at <  TIMESTAMPTZ '2026-08-31 00:00:00+00';
```

This is a half-open interval:

```text
[start, end)
```

It includes the start and excludes the end.

## Mistake: Confusing Inclusive and Exclusive Boundaries

Suppose two jobs process consecutive periods:

```text
Job A: [10:00, 11:00)
Job B: [11:00, 12:00)
```

An event at exactly:

```text
11:00
```

belongs to Job B.

This makes ranges composable:

```text
[10:00, 11:00)
[11:00, 12:00)
[12:00, 13:00)
```

There is no overlap and no gap.

For data pipelines, reporting, event processing, and pagination, this is generally safer than independently defining inclusive end timestamps.

## Mistake: Ignoring Timezone When Defining a Day

The statement:

> "Orders created on August 30"

is incomplete for a global application.

It could mean:

```text
August 30 UTC
```

or:

```text
August 30 Asia/Kolkata
```

or:

```text
August 30 America/New_York
```

These represent different sets of instants.

For a user-local day:

```text
User's calendar date
        ↓
User timezone
        ↓
Local start of day
        ↓
Local start of next day
        ↓
Convert boundaries to absolute instants
        ↓
Query TIMESTAMPTZ
```

The timezone is therefore part of the query semantics, not merely a display preference.

## Mistake: Assuming Every Day Has 24 Hours

A calendar day and a 24-hour duration are not always equivalent.

Timezone transitions such as daylight saving time can produce local days with different elapsed durations.

Therefore:

```text
calendar day
```

and:

```text
24 elapsed hours
```

are different concepts.

If the requirement is:

> the next calendar day in the user's timezone

perform calendar-based timezone-aware calculation.

If the requirement is:

> exactly 24 hours from this instant

use an elapsed duration.

The business requirement determines which one is correct.

## Mistake: Confusing Days, Hours, and Months

These are not interchangeable:

```sql
INTERVAL '24 hours'
INTERVAL '1 day'
INTERVAL '30 days'
INTERVAL '1 month'
```

For example:

```sql
SELECT CURRENT_TIMESTAMP + INTERVAL '30 days';
```

means a duration of 30 days.

Whereas:

```sql
SELECT CURRENT_TIMESTAMP + INTERVAL '1 month';
```

means calendar-month arithmetic.

For billing systems, subscriptions, reminders, and recurring jobs, this distinction can materially change behavior.

## Mistake: Treating a Month as 30 Days

Avoid:

```text
monthly_subscription_expiry = start + 30 days
```

when the business rule is:

> one calendar month after the subscription date.

Use calendar-month semantics instead.

The difference is visible immediately around months with:

- 28 days.
- 29 days.
- 30 days.
- 31 days.

It also becomes important for recurring schedules.

## Mistake: Using `EXTRACT(MONTH ...)` to Filter a Specific Month

This query:

```sql
WHERE EXTRACT(MONTH FROM created_at) = 8
```

matches August across all years.

If the requirement is August 2026, use:

```sql
WHERE created_at >= TIMESTAMPTZ '2026-08-01 00:00:00+00'
  AND created_at <  TIMESTAMPTZ '2026-09-01 00:00:00+00';
```

The range expresses both the month and the year.

## Mistake: Using `DATE_TRUNC()` as a Default Filter

This is readable:

```sql
WHERE DATE_TRUNC('day', created_at) =
      TIMESTAMPTZ '2026-08-30 00:00:00+00'
```

but it transforms every candidate timestamp before comparison.

For indexed filtering, prefer:

```sql
WHERE created_at >= TIMESTAMPTZ '2026-08-30 00:00:00+00'
  AND created_at <  TIMESTAMPTZ '2026-08-31 00:00:00+00';
```

`DATE_TRUNC()` remains valuable for grouping:

```sql
SELECT
    DATE_TRUNC('month', created_at) AS month,
    COUNT(*)
FROM orders
GROUP BY DATE_TRUNC('month', created_at);
```

The distinction is:

> **Use transformation for bucketing; use boundaries for filtering.**

## Mistake: Formatting Before Filtering

Avoid:

```sql
WHERE TO_CHAR(created_at, 'YYYY-MM') = '2026-08'
```

`TO_CHAR()` produces text.

The database can no longer treat the expression as the original temporal value.

Prefer:

```sql
WHERE created_at >= TIMESTAMPTZ '2026-08-01 00:00:00+00'
  AND created_at <  TIMESTAMPTZ '2026-09-01 00:00:00+00';
```

Format the result after the database has performed the temporal filtering.

## Mistake: Formatting Dates in SQL When the API Owns Presentation

SQL can format timestamps:

```sql
SELECT TO_CHAR(created_at, 'YYYY-MM-DD');
```

but APIs often benefit from returning structured temporal values.

For example:

```json
{
  "created_at": "2026-08-30T10:15:00Z"
}
```

The frontend or API presentation layer can then format the value according to locale and user preferences.

Database formatting is appropriate for:

- Database-generated reports.
- Exports.
- SQL-specific reporting.
- Human-readable database output.

Avoid unnecessarily converting values to strings when they still need temporal processing.

## Mistake: Comparing Different Timezones as Strings

Never rely on lexical string comparison for arbitrary timestamp representations:

```text
"2026-08-30T10:00:00Z"
"2026-08-30T15:30:00+05:30"
```

These strings represent the same instant but are not necessarily equivalent as raw text.

Parse temporal values into proper temporal types before comparison.

## Mistake: Storing Timezone Names Inside Timestamp Strings

Avoid designs such as:

```text
2026-08-30 15:30:00 Asia/Kolkata
```

inside an unstructured text column.

Prefer separate concepts:

```text
event_time → TIMESTAMPTZ
user_timezone → IANA timezone name
```

For example:

```text
event_time:    2026-08-30T10:00:00Z
timezone:      Asia/Kolkata
```

This preserves the instant while retaining the business timezone when required.

Use IANA timezone names such as:

```text
Asia/Kolkata
America/New_York
Europe/London
```

rather than hard-coding offsets such as:

```text
+05:30
-05:00
```

when recurring local-time behavior matters.

## Mistake: Using Fixed Offsets Instead of Timezone Rules

A fixed offset:

```text
UTC-05:00
```

does not encode daylight-saving transitions.

A timezone identifier:

```text
America/New_York
```

contains timezone rules that can change the offset depending on the date.

For recurring schedules such as:

> Run at 09:00 local time every day.

store the timezone identity rather than only the current offset.

## Mistake: Assuming UTC Solves Every Date Problem

UTC is excellent for representing absolute instants, but UTC does not solve calendar semantics.

For example:

> "Send the customer a notification at 9 AM every day."

requires:

```text
customer timezone
+
local wall-clock time
+
recurrence rules
```

It cannot be represented correctly by storing only:

```text
09:00 UTC
```

because the customer's local offset may differ.

A strong architecture separates:

```text
Instant
Calendar date/time
Timezone
Recurrence
Duration
```

rather than forcing everything into UTC timestamps.

## Mistake: Losing Precision

Database and application layers can support fractional seconds.

For example:

```text
2026-08-30 12:00:00.123456
```

If an application truncates this to:

```text
2026-08-30 12:00:00
```

before comparison, ordering or deduplication can change.

Avoid unnecessarily reducing timestamp precision.

This matters for:

- Event ordering.
- Idempotency.
- CDC pipelines.
- Audit logs.
- Distributed tracing.
- Incremental processing.

When timestamps alone are insufficient for deterministic ordering, use a stable secondary key.

For example:

```sql
ORDER BY created_at, id
```

## Mistake: Using Timestamps as the Only Ordering Key

Two events can share the same timestamp.

This query:

```sql
ORDER BY created_at
```

does not guarantee deterministic ordering among rows with equal timestamps.

Prefer:

```sql
ORDER BY created_at, id
```

when `id` provides a stable unique ordering.

This is particularly important for keyset pagination:

```sql
SELECT id, created_at
FROM orders
WHERE (created_at, id) > (:last_created_at, :last_id)
ORDER BY created_at, id
LIMIT 100;
```

## Mistake: Using Offset Pagination for Large Time-Series Tables

This becomes expensive:

```sql
SELECT *
FROM events
ORDER BY created_at
OFFSET 1000000
LIMIT 100;
```

The database may need to walk through a large number of rows before returning the requested page.

For large append-heavy tables, keyset pagination is usually preferable:

```sql
SELECT *
FROM events
WHERE (created_at, id) > (:last_created_at, :last_id)
ORDER BY created_at, id
LIMIT 100;
```

with:

```sql
CREATE INDEX idx_events_created_id
ON events (created_at, id);
```

## Mistake: Performing Date Filtering in Python

Avoid:

```python
orders = list(Order.objects.all())

filtered = [
    order for order in orders
    if start <= order.created_at < end
]
```

This moves work from the database into application memory.

Prefer database filtering:

```python
orders = Order.objects.filter(
    created_at__gte=start,
    created_at__lt=end,
)
```

The database can then use:

- Indexes.
- Query planning.
- Predicate pushdown.
- Partition pruning.
- Efficient execution strategies.

## Mistake: Constructing SQL from Date Strings

Avoid:

```python
query = f"""
    SELECT *
    FROM orders
    WHERE created_at >= '{start}'
"""
```

Use parameterized queries instead.

Conceptually:

```sql
SELECT *
FROM orders
WHERE created_at >= :start
  AND created_at < :end;
```

The database driver should bind the temporal values using appropriate types.

This prevents SQL injection and avoids unnecessary parsing ambiguity.

## Mistake: Relying on Implicit Date Parsing

Avoid ambiguous literals such as:

```text
01/02/2026
```

Does this mean:

```text
January 2
```

or:

```text
February 1
```

Use ISO-oriented representations:

```text
2026-02-01
```

For timezone-aware instants, use an explicit offset or UTC:

```text
2026-02-01T10:30:00Z
```

or:

```text
2026-02-01T16:00:00+05:30
```

Do not depend on server locale settings for parsing application input.

## Mistake: Using Local Time in Distributed Systems

Consider:

```text
API server
   ↓
Kafka event
   ↓
Celery worker
   ↓
Database
```

If every component uses a different local timezone, an event timestamp can be interpreted inconsistently.

A safer design is:

```text
External request
      ↓
Parse explicit timezone
      ↓
Convert/normalize instant
      ↓
Persist absolute timestamp
      ↓
Publish event with explicit timestamp
      ↓
Consumers preserve instant
      ↓
Convert to local time only when required
```

This reduces ambiguity across services.

## Mistake: Assuming Container Timezone Configuration Is Business Logic

Docker and Kubernetes workloads frequently run with UTC-oriented system configuration.

That is desirable for infrastructure consistency, but it should not be used to define business-local time.

For example:

```text
Container timezone = UTC
```

does not mean:

```text
Customer timezone = UTC
```

Application configuration should explicitly carry business timezone information.

## Mistake: Incorrectly Handling "Today"

This is ambiguous:

```sql
WHERE created_at >= CURRENT_DATE
```

The meaning of `CURRENT_DATE` depends on the database/session timezone.

For a system-wide UTC business day, define that explicitly.

For a user-local day, derive the boundaries using the user's timezone.

The phrase:

```text
today
```

should always have an explicitly defined timezone context in production systems.

## Mistake: Confusing `DATE` With Midnight Timestamps

These are semantically different:

```text
2026-08-30
```

and:

```text
2026-08-30 00:00:00 UTC
```

The first means:

> the calendar date August 30.

The second means:

> a specific instant at midnight UTC.

Converting a `DATE` into midnight UTC can introduce unintended semantics.

Use `DATE` when time-of-day and timezone are irrelevant.

## Mistake: Calculating Age With Simple Year Subtraction

This is incorrect:

```sql
EXTRACT(YEAR FROM CURRENT_DATE) -
EXTRACT(YEAR FROM birth_date)
```

because the birthday may not have occurred yet this year.

For calendar age, PostgreSQL provides:

```sql
SELECT AGE(CURRENT_DATE, birth_date)
FROM users;
```

Application requirements should determine whether the result needs:

- Calendar age.
- Exact elapsed duration.
- Number of days.
- Business-specific age rules.

## Mistake: Ignoring Leap Years

A year is not always 365 days.

Leap years introduce February 29.

Therefore, avoid implementing calendar-year logic as:

```text
365 × number_of_years
```

when the business requirement is calendar-based.

Use database/application date arithmetic designed for calendar values.

## Mistake: Ignoring End-of-Month Behavior

Calendar arithmetic can produce non-obvious results around the end of a month.

For example, adding one month to a date near the end of a month requires a defined policy for months that do not contain the same day.

Billing and subscription systems should explicitly define behavior such as:

- Last day of month.
- Same ordinal day when possible.
- Clamped day.
- Fixed elapsed duration.

Do not assume that "one month later" has a universally obvious interpretation.

## Mistake: Using the Database Timestamp as the Only Source of Event Time

For event-driven systems, multiple timestamps can have different meanings:

```text
event_time
created_at
processed_at
published_at
received_at
updated_at
```

They are not interchangeable.

For example:

```text
event_time     = when the business event happened
published_at   = when Kafka received/published the event
processed_at   = when the consumer processed it
```

When designing event schemas, name timestamps according to their semantics.

## Mistake: Treating `updated_at` as an Event History

An `updated_at` column tells you when the current row was last changed.

It does not provide a complete history of changes.

If auditing requires:

```text
who changed what
when it changed
what the previous value was
```

use an audit/event history model rather than relying on one timestamp.

## Mistake: Ignoring Clock Skew

Distributed systems do not have a perfectly synchronized global wall clock.

Servers can experience small differences because of:

- NTP adjustments.
- VM scheduling.
- Clock drift.
- Network delays.
- Different timestamp sources.

Do not assume that:

```text
service A timestamp < service B timestamp
```

always proves that A happened before B.

For strict event ordering, use appropriate mechanisms such as:

- Database sequence/identity values.
- Kafka partition ordering.
- Explicit event offsets.
- Logical clocks where appropriate.
- Domain-specific ordering keys.

## Mistake: Using Wall-Clock Time for Measuring Duration

Avoid measuring latency using unrelated wall-clock timestamps across machines:

```text
worker_end_time - api_start_time
```

Clock differences can distort the result.

For local duration measurement in Python, use a monotonic clock:

```python
import time

start = time.monotonic()
# Work
elapsed = time.monotonic() - start
```

Wall-clock timestamps are for temporal identity; monotonic clocks are appropriate for measuring elapsed execution time.

## Mistake: Assuming Database and Application Clocks Are Identical

Consider:

```text
Python application → PostgreSQL
```

The application and database have separate clocks.

Therefore:

```python
datetime.now(UTC)
```

and:

```sql
CURRENT_TIMESTAMP
```

can differ slightly.

Choose a clear ownership model.

For database-generated audit timestamps:

```sql
created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```

For externally generated event timestamps, use the event's authoritative source.

Do not casually mix timestamps from different clocks when exact temporal ordering matters.

## Mistake: Ignoring Query Performance

A date function may be logically correct but operationally expensive.

Always inspect important production queries:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM orders
WHERE created_at >= :start
  AND created_at < :end;
```

Check for:

- Unexpected sequential scans.
- Poor row estimates.
- Excessive buffer reads.
- Large numbers of filtered rows.
- Missing indexes.
- Partition pruning failures.

Temporal predicates often sit on very large tables, so a small query-design mistake can become a significant production cost.

## Mistake: Creating Indexes Without Considering the Query Pattern

An index on:

```sql
(created_at)
```

is useful for:

```sql
WHERE created_at >= :start
  AND created_at < :end
```

but a different query pattern may require a different index.

For example:

```sql
WHERE user_id = :user_id
  AND created_at >= :start
  AND created_at < :end
```

may benefit from:

```sql
CREATE INDEX idx_orders_user_created
ON orders (user_id, created_at);
```

Index design should follow actual workload and query predicates rather than simply adding indexes to every date column.

## Mistake: Ignoring Partitioning Semantics

Large time-series tables may be partitioned by time.

For example:

```text
events
├── events_2026_07
├── events_2026_08
└── events_2026_09
```

Queries with explicit temporal boundaries can enable partition pruning.

Poorly expressed predicates can prevent the database from eliminating irrelevant partitions efficiently.

Time-based partitioning should therefore be designed together with:

- Retention policy.
- Query patterns.
- Index strategy.
- Partition boundaries.
- Operational maintenance.

## Mistake: Assuming `CURRENT_DATE` Is Always UTC

In PostgreSQL:

```sql
SELECT CURRENT_DATE;
```

uses the session's timezone context.

If the application expects UTC semantics but database connections use another timezone, "today" can differ between components.

Production systems should explicitly establish timezone conventions instead of relying on defaults.

## Mistake: Returning Inconsistent Timestamp Formats From APIs

An API should use a consistent temporal representation.

Prefer standardized representations such as ISO 8601/RFC 3339:

```json
{
  "created_at": "2026-08-30T10:15:00Z"
}
```

Avoid mixing:

```text
2026-08-30
08/30/2026
30-08-2026 10:15
2026-08-30T10:15:00Z
```

within the same API without explicit semantic reasons.

The representation should communicate whether the value is:

- A date.
- A local datetime.
- An absolute instant.

## Mistake: Treating User Input as UTC Without Evidence

Suppose a user enters:

```text
2026-08-30 09:00
```

This has no timezone.

It should not automatically become:

```text
2026-08-30 09:00 UTC
```

unless the product explicitly defines the input as UTC.

The application needs to know the intended timezone from:

- User profile.
- Request context.
- Explicit offset.
- Business configuration.

Otherwise the system is inventing temporal meaning.

## Mistake: Ignoring DST in Recurring Jobs

A Celery or Kubernetes scheduled task such as:

```text
Run every day at 09:00
```

can mean either:

```text
09:00 UTC every day
```

or:

```text
09:00 local business time every day
```

These are different schedules.

For local-time recurring work, the scheduling system must understand the target timezone and its daylight-saving rules.

For global infrastructure jobs, UTC schedules are often simpler and more predictable.

## Mistake: Assuming a Date Range Is Always UTC

An API may receive:

```text
from=2026-08-30
to=2026-08-31
```

Those are calendar dates, not necessarily UTC instants.

The backend must define whether the API means:

```text
UTC calendar dates
```

or:

```text
user-local calendar dates
```

or another business timezone.

Ambiguous temporal APIs eventually produce inconsistent reports.

## Mistake: Using One Temporal Model for Every Business Requirement

A mature system may legitimately contain several temporal types:

```text
birth_date             → DATE
store_opening_time     → TIME
created_at             → TIMESTAMPTZ
customer_timezone      → IANA timezone
subscription_period    → calendar interval/domain rules
processing_duration    → elapsed duration
```

Trying to represent all of them as:

```text
VARCHAR
```

or:

```text
TIMESTAMP
```

usually pushes complexity into application code and creates ambiguity.

The data model should preserve the semantics that downstream systems need.

## Production-Safe Date/Time Checklist

Before shipping a date/time feature, verify:

### Data Model

- Is this an instant, date, local time, or duration?
- Is the database type appropriate?
- Does the application need to retain the user's timezone separately?
- Is fractional-second precision important?

### Query

- Can the filter be expressed as a native range?
- Is the predicate index-friendly?
- Are the start/end boundaries explicit?
- Are ranges half-open?
- Is `EXPLAIN (ANALYZE, BUFFERS)` appropriate for validation?

### Timezone

- What timezone defines the business operation?
- Is the timezone explicit?
- Is UTC being used for absolute instants?
- Is a calendar operation being confused with elapsed time?

### Application

- Are Python datetimes timezone-aware where required?
- Are date strings parsed explicitly?
- Is server-local time being avoided?
- Are database and application clocks being treated appropriately?

### API

- Does the API clearly distinguish dates from instants?
- Are timestamps consistently serialized?
- Are offsets or `Z` included for absolute timestamps?
- Is user-local interpretation explicitly defined?

### Distributed Systems

- Are event timestamps named according to their meaning?
- Is clock skew relevant?
- Is timestamp ordering being confused with event ordering?
- Are recurring schedules timezone-aware when required?

## Practical Design Pattern

A robust production design for an order system might look like:

```sql
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    order_date DATE NOT NULL
);

CREATE INDEX idx_orders_created_at
ON orders (created_at);

CREATE INDEX idx_orders_user_created
ON orders (user_id, created_at);
```

The semantics are intentionally separated:

```text
created_at
    → absolute event instant

paid_at
    → absolute payment instant

cancelled_at
    → absolute cancellation instant

order_date
    → business calendar date
```

A daily query can then use:

```sql
SELECT id, user_id, created_at
FROM orders
WHERE created_at >= :start
  AND created_at < :end
ORDER BY created_at, id;
```

The database preserves temporal semantics while the application controls the business interpretation of `:start` and `:end`.

## Recommended Engineering Rules

| Rule | Recommendation |
|---|---|
| Event timestamps | Prefer `TIMESTAMPTZ` in PostgreSQL |
| Calendar-only values | Prefer `DATE` |
| Absolute instants | Normalize around UTC |
| User timezone | Store separately when needed |
| Filtering | Use `>= start AND < end` |
| Timestamp indexing | Keep predicates on the native column |
| Grouping | `DATE_TRUNC()` is often appropriate |
| Component extraction | Use `EXTRACT()` |
| Formatting | Use `TO_CHAR()` at presentation/reporting boundaries |
| Calendar arithmetic | Use calendar-aware operations |
| Elapsed duration | Use timestamp subtraction or monotonic clocks as appropriate |
| API timestamps | Use unambiguous ISO 8601/RFC 3339 representations |
| Dynamic SQL | Always parameterize temporal values |
| Pagination | Use deterministic ordering and keyset pagination for large datasets |
| Distributed ordering | Do not infer causality from wall-clock timestamps alone |

## Key Takeaways

- **Most date/time bugs come from incorrect temporal semantics: distinguish instants, calendar dates, local times, durations, and timezones before choosing a data type or function.**
- **Use timezone-aware absolute timestamps for distributed events, keep business/user timezones separately when required, and avoid relying on server-local time.**
- **Prefer half-open, index-friendly ranges such as `column >= start AND column < end` instead of transforming timestamp columns or inventing end-of-day timestamps.**
- **Do not confuse calendar operations with elapsed durations; days, months, years, daylight-saving transitions, and fixed-hour intervals have different semantics.**
- **Treat date/time behavior as a system-wide concern spanning SQL, application code, APIs, schedulers, distributed services, indexes, and query performance.**