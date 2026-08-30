# README

## Overview

This section covers SQL date and time operations required for building reliable backend systems. The focus is not only on syntax, but on choosing the correct temporal representation, writing predictable queries, and avoiding timezone and boundary errors.

Date and time handling becomes significantly more important as systems become distributed. A backend may receive timestamps from clients, persist them in PostgreSQL, publish them through Kafka, process them in Celery workers, and expose them through REST or gRPC APIs. Every layer must preserve the intended temporal semantics.

The material progresses from basic date/time operations to production concerns such as timezone-safe filtering, range boundaries, index usage, and common failure modes.

## Navigation

- [01- Date and Time Fundamentals](./01-%20Date%20and%20Time%20Fundamentals.md) — Choosing SQL temporal types and when to use each
- [02- DATE TIME and TIMESTAMP](./02-%20DATE%20TIME%20and%20TIMESTAMP.md) — Differences between date, time, and timestamp types
- [03- Time Zones](./03-%20Time%20Zones.md) — Time zone semantics and time zone-aware storage
- [04- Current Date and Time](./04-%20Current%20Date%20and%20Time.md) — Obtaining the current date/time in SQL
- [05- Date Extraction](./05-%20Date%20Extraction.md) — Extracting year, month, day, and other components
- [06- Date Addition and Subtraction](./06-%20Date%20Addition%20and%20Subtraction.md) — Temporal arithmetic with intervals
- [07- Date Difference](./07-%20Date%20Difference.md) — Calculating elapsed and calendar differences
- [08- Date Truncation](./08-%20Date%20Truncation.md) — Truncating timestamps for grouping and bucketing
- [09- Date Formatting](./09-%20Date%20Formatting.md) — Converting temporal values into display formats
- [10- Date Filtering](./10-%20Date%20Filtering.md) — Filtering rows using temporal predicates
- [11- Date Ranges](./11-%20Date%20Ranges.md) — Working with temporal intervals and boundaries
- [12- Inclusive vs Exclusive Time Ranges](./12-%20Inclusive%20vs%20Exclusive%20Time%20Ranges.md) — Designing correct range boundaries
- [13- Time Zone Safe Queries](./13-%20Time%20Zone%20Safe%20Queries.md) — Querying timestamps correctly across time zones
- [14- Date Functions and Indexes](./14-%20Date%20Functions%20and%20Indexes.md) — Preserving index efficiency with date functions
- [15- Choosing the Right Date Type](./15-%20Choosing%20the%20Right%20Date%20Type.md) — Matching data types to business semantics
- [16- Choosing the Right Date Function](./16-%20Choosing%20the%20Right%20Date%20Function.md) — Selecting the appropriate SQL temporal operation
- [17- Common Date and Time Mistakes](./17-%20Common%20Date%20and%20Time%20Mistakes.md) — Production pitfalls and failure modes

## Temporal Concepts

Before choosing a SQL function, determine what the value represents.

| Concept | Meaning | Example |
|---|---|---|
| Instant | A precise point on the global timeline | `2026-08-30T10:00:00Z` |
| Calendar date | A date without a time of day | `2026-08-30` |
| Local time | A wall-clock time in a particular context | `09:30 Asia/Kolkata` |
| Duration | An amount of elapsed time | `90 minutes` |
| Calendar period | A calendar-based amount | `1 month` |

These concepts should not be collapsed into a single representation.

For example, a customer's birthday is normally a calendar date:

```sql
birth_date DATE
```

An order creation event is normally an instant:

```sql
created_at TIMESTAMPTZ
```

A recurring store opening schedule may require:

```text
local time + timezone
```

rather than a UTC timestamp.

## Recommended PostgreSQL Types

For PostgreSQL-backed applications, choose the type according to the business meaning.

| PostgreSQL Type | Use When | Example |
|---|---|---|
| `DATE` | Only the calendar date matters | Birthday, invoice date |
| `TIME` | Only time of day matters | Store opening time |
| `TIMESTAMP` | A timezone-independent local datetime is intentional | Business-local wall-clock value |
| `TIMESTAMPTZ` | The value represents an absolute instant | Event creation time |
| `INTERVAL` | Temporal arithmetic or a duration is required | Retention period |

For most event timestamps in distributed backend systems:

```sql
created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```

is a strong default.

The timezone itself may still need to be stored separately:

```sql
timezone TEXT NOT NULL
```

when user-local or business-local calendar behavior matters.

## Date Extraction

Date extraction obtains a component from a temporal value.

Typical PostgreSQL usage:

```sql
SELECT
    EXTRACT(YEAR FROM created_at) AS year,
    EXTRACT(MONTH FROM created_at) AS month,
    EXTRACT(DAY FROM created_at) AS day
FROM orders;
```

Common components include:

| Component | Example |
|---|---|
| `YEAR` | `2026` |
| `MONTH` | `8` |
| `DAY` | `30` |
| `HOUR` | `15` |
| `MINUTE` | `45` |
| `SECOND` | `12` |
| `DOW` | Day of week |
| `DOY` | Day of year |
| `QUARTER` | Quarter |

Extraction is useful for analytics and derived values, but it should not automatically be used as a filtering strategy.

For example:

```sql
WHERE EXTRACT(MONTH FROM created_at) = 8
```

matches August across all years.

For a specific month, prefer a range:

```sql
WHERE created_at >= :start
  AND created_at < :end
```

## Date Addition and Subtraction

Temporal arithmetic allows dates and timestamps to be moved forward or backward.

PostgreSQL:

```sql
SELECT CURRENT_DATE + INTERVAL '7 days';
```

or:

```sql
SELECT CURRENT_TIMESTAMP - INTERVAL '30 minutes';
```

Calendar periods and elapsed durations should not be treated as interchangeable.

```sql
INTERVAL '30 days'
```

is different from:

```sql
INTERVAL '1 month'
```

A production billing system should define whether a subscription is extended by:

- A fixed number of elapsed days.
- A calendar month.
- A calendar year.
- A domain-specific billing period.

Avoid implementing calendar concepts as fixed seconds unless that is explicitly the business rule.

## Date Difference

Date difference depends on what "difference" means.

Possible interpretations include:

- Number of elapsed seconds.
- Number of elapsed hours.
- Number of calendar days.
- Number of calendar months.
- Calendar age.
- Business days.

For timestamps:

```sql
SELECT ended_at - started_at
FROM jobs;
```

returns an interval.

For calendar calculations:

```sql
SELECT AGE(CURRENT_DATE, birth_date)
FROM users;
```

may be more appropriate than manually subtracting years.

The correct operation depends on whether the requirement is based on elapsed time or calendar semantics.

## Date Truncation

`DATE_TRUNC()` reduces a timestamp to a specified precision.

For example:

```sql
SELECT DATE_TRUNC('month', created_at) AS month
FROM orders;
```

This produces a consistent bucket for monthly aggregation.

Typical use cases include:

- Monthly reports.
- Daily metrics.
- Hourly aggregation.
- Time-series analytics.

Example:

```sql
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*) AS order_count
FROM orders
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY day;
```

A key distinction is:

> Use truncation for bucketing and grouping; use explicit boundaries for filtering.

## Date Formatting

Formatting converts a temporal value into a string representation.

PostgreSQL provides `TO_CHAR()`:

```sql
SELECT TO_CHAR(
    created_at,
    'YYYY-MM-DD HH24:MI:SS'
)
FROM orders;
```

Formatting is appropriate for:

- Reports.
- SQL-generated exports.
- Human-readable database output.

For APIs, avoid converting timestamps to arbitrary display strings prematurely.

Prefer a standardized representation such as:

```json
{
  "created_at": "2026-08-30T10:15:00Z"
}
```

Presentation formatting should generally happen at the API/client boundary.

## Date Filtering

Temporal filtering should normally use explicit boundaries.

Preferred pattern:

```sql
SELECT id, created_at
FROM orders
WHERE created_at >= :start
  AND created_at < :end;
```

This has several advantages:

- Clear boundary semantics.
- Good compatibility with timestamp indexes.
- No artificial end-of-day value.
- No fractional-second edge cases.
- Easy composition of adjacent ranges.

For a UTC day:

```sql
WHERE created_at >= TIMESTAMPTZ '2026-08-30 00:00:00+00'
  AND created_at <  TIMESTAMPTZ '2026-08-31 00:00:00+00'
```

## Date Ranges

A date range represents a continuous temporal interval.

The preferred mental model for most backend queries is:

```text
[start, end)
```

meaning:

```text
start ≤ value < end
```

For example:

```text
[2026-08-30 00:00, 2026-08-31 00:00)
```

contains every timestamp on August 30 without needing to define the last representable timestamp of the day.

Adjacent ranges therefore compose naturally:

```text
[10:00, 11:00)
[11:00, 12:00)
[12:00, 13:00)
```

There is neither overlap nor a gap.

## Inclusive vs Exclusive Time Ranges

Inclusive end boundaries often introduce subtle bugs.

Avoid:

```sql
WHERE created_at BETWEEN :start AND :end
```

when the intended semantics are adjacent time windows.

Prefer:

```sql
WHERE created_at >= :start
  AND created_at < :end
```

This is especially important for:

- Reporting.
- Batch processing.
- ETL jobs.
- Event consumers.
- Time-series queries.
- Pagination.
- Data exports.

Half-open ranges provide a stable contract between producers and consumers.

## Time Zone Safe Queries

Timezones become critical when users and services operate in different regions.

A robust architecture distinguishes:

```text
Absolute instant
       ↓
TIMESTAMPTZ
       ↓
UTC-oriented storage/processing
       ↓
User/business timezone
       ↓
Local calendar interpretation
       ↓
Presentation
```

For example, the statement:

> "Orders created on August 30"

requires a timezone.

August 30 in:

```text
UTC
```

is not the same set of instants as August 30 in:

```text
Asia/Kolkata
```

For user-local reporting:

1. Determine the user's timezone.
2. Construct the local start of the requested date.
3. Construct the start of the next local date.
4. Convert those boundaries into absolute instants.
5. Query the timestamp column using `[start, end)`.

This avoids incorrectly treating local calendar dates as UTC dates.

## Date Functions and Indexes

Temporal functions can affect query performance.

An index such as:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

can efficiently support:

```sql
WHERE created_at >= :start
  AND created_at < :end
```

A function applied to the indexed column may prevent the normal index strategy from being effective:

```sql
WHERE created_at::date = :date
```

or:

```sql
WHERE DATE_TRUNC('day', created_at) = :day
```

For high-volume tables, prefer range predicates.

Always validate important production queries with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM orders
WHERE created_at >= :start
  AND created_at < :end;
```

## Choosing the Right Date Type

The data type should preserve business semantics.

### Use `DATE`

When only the calendar date matters:

```text
birthday
invoice_date
holiday_date
```

### Use `TIMESTAMPTZ`

When an exact instant matters:

```text
order_created_at
payment_received_at
event_published_at
```

### Use `TIME`

When only a wall-clock time matters:

```text
store_opening_time
daily_cutoff_time
```

### Store Timezone Separately

When local-time behavior must be preserved:

```text
timezone = "Asia/Kolkata"
local_time = "09:00"
```

Do not replace a timezone identifier with a fixed offset when future timezone rules matter.

## Choosing the Right Date Function

Different functions solve different problems.

| Requirement | Prefer |
|---|---|
| Get current timestamp | `CURRENT_TIMESTAMP` / `now()` |
| Get current date | `CURRENT_DATE` |
| Extract component | `EXTRACT()` |
| Group into temporal buckets | `DATE_TRUNC()` |
| Format for display | `TO_CHAR()` |
| Add/subtract temporal values | `+`, `-`, `INTERVAL` |
| Calculate calendar age | `AGE()` |
| Filter a time period | `>= start AND < end` |
| Filter by date on indexed timestamp | Timestamp range |
| Compare absolute instants | `TIMESTAMPTZ` |
| Represent calendar-only values | `DATE` |

The most important distinction is between **transforming a value** and **filtering by boundaries**.

For example:

```sql
-- Good for grouping
DATE_TRUNC('month', created_at)

-- Good for filtering
created_at >= :start
AND created_at < :end
```

## Common Date and Time Mistakes

Common production failures include:

| Mistake | Why It Fails | Better Approach |
|---|---|---|
| Using server local time | Behavior varies by environment | Use explicit timezone-aware values |
| Treating `DATE` as midnight UTC | Adds unintended instant semantics | Keep it as `DATE` |
| Using `TIMESTAMP` for global events | Timezone meaning becomes ambiguous | Prefer `TIMESTAMPTZ` |
| Using `BETWEEN` for whole-day timestamps | Fractional seconds can be excluded | Use `[start, end)` |
| Casting timestamps in filters | Can interfere with indexes | Use timestamp ranges |
| Formatting before filtering | Converts temporal values to text | Filter first, format later |
| Using fixed offsets for recurring local time | DST rules are lost | Store IANA timezone identifiers |
| Treating month as 30 days | Calendar and duration semantics differ | Use calendar-aware arithmetic |
| Filtering by extracted month only | Can match every year | Filter using complete boundaries |
| Using timestamp as the only ordering key | Equal timestamps are possible | Add a deterministic secondary key |
| Comparing timestamp strings | String representation may differ | Compare native temporal types |
| Assuming UTC solves local scheduling | Local calendar rules still matter | Store timezone and local schedule |
| Measuring latency with wall-clock time | Clock adjustments can distort duration | Use monotonic clocks |
| Constructing SQL with date strings | Creates injection and parsing risks | Parameterize values |

## Backend Integration

### Django

Use timezone-aware framework utilities:

```python
from django.utils import timezone

now = timezone.now()

orders = Order.objects.filter(
    created_at__gte=start,
    created_at__lt=end,
)
```

Avoid loading large datasets into Python merely to perform temporal filtering.

The database should perform filtering whenever possible.

### FastAPI

For API boundaries, parse temporal input into appropriate Python types and validate the intended semantics.

An instant should contain timezone information rather than silently assuming local server time.

Conceptually:

```text
HTTP request
    ↓
Parse datetime
    ↓
Validate timezone semantics
    ↓
Normalize instant
    ↓
Parameterized SQL query
    ↓
PostgreSQL
```

### Celery

For scheduled jobs, distinguish between:

```text
09:00 UTC every day
```

and:

```text
09:00 every day in the customer's timezone
```

The latter requires timezone-aware scheduling semantics.

### Kafka

Event schemas should distinguish timestamps according to their meaning:

```text
event_time
published_at
processed_at
```

These values should not be treated as interchangeable.

Timestamp ordering also does not necessarily establish causality across distributed services because clocks can differ.

## Production Query Pattern

A typical order query should look like:

```sql
SELECT
    id,
    user_id,
    created_at
FROM orders
WHERE user_id = :user_id
  AND created_at >= :start
  AND created_at < :end
ORDER BY created_at, id
LIMIT :limit;
```

A corresponding index may be:

```sql
CREATE INDEX idx_orders_user_created
ON orders (user_id, created_at);
```

This design provides:

- Explicit temporal boundaries.
- Efficient filtering.
- Deterministic ordering.
- Compatibility with keyset pagination.
- A clear contract between the application and database.

For large datasets, keyset pagination can continue from the previous row:

```sql
SELECT
    id,
    user_id,
    created_at
FROM orders
WHERE user_id = :user_id
  AND created_at >= :start
  AND created_at < :end
  AND (created_at, id) > (:last_created_at, :last_id)
ORDER BY created_at, id
LIMIT :limit;
```

## Production Checklist

Before shipping date/time functionality, verify:

### Data Model

- Does the value represent an instant, date, local time, or duration?
- Is the SQL type aligned with that meaning?
- Does the application need a separate timezone identifier?
- Is timestamp precision sufficient?

### Query

- Are temporal filters expressed using explicit boundaries?
- Are range endpoints defined consistently?
- Are predicates index-friendly?
- Are functions being unnecessarily applied to indexed columns?
- Has the query plan been inspected?

### Timezone

- Which timezone defines the business operation?
- Is the timezone explicit?
- Are absolute instants represented consistently?
- Are calendar operations distinguished from elapsed durations?

### API

- Are date and datetime values clearly distinguished?
- Are absolute timestamps serialized consistently?
- Are timezone offsets included where required?
- Is local-time interpretation explicitly defined?

### Distributed Systems

- Are timestamps named according to their semantics?
- Are database and application clocks being treated as separate sources?
- Is timestamp ordering being confused with event ordering?
- Are recurring jobs timezone-aware where necessary?

## Engineering Heuristics

Use these rules when designing date/time behavior:

```text
Calendar date?
    → DATE

Absolute instant?
    → TIMESTAMPTZ

Local wall-clock schedule?
    → Local time + timezone

Elapsed duration?
    → Duration/INTERVAL

Filtering?
    → [start, end)

Grouping?
    → DATE_TRUNC()

Component extraction?
    → EXTRACT()

Formatting?
    → Presentation/reporting layer

Large timestamp table?
    → Native timestamp predicates + appropriate index
```

The most important principle is to preserve temporal meaning throughout the system. SQL syntax is only one part of the problem; the database schema, application runtime, API contract, scheduling system, and distributed architecture must all agree on what a temporal value represents.


## Key Takeaways

- **Choose temporal types based on semantics: `DATE` for calendar dates, `TIMESTAMPTZ` for absolute instants, and explicit timezone information for local-time behavior.**
- **Use half-open ranges such as `[start, end)` for reliable date/time filtering and adjacent processing windows.**
- **Prefer native timestamp range predicates over applying functions or casts to indexed timestamp columns.**
- **Separate calendar operations from elapsed-duration calculations, especially for months, years, daylight-saving transitions, and recurring schedules.**
- **Treat date/time handling as a cross-layer concern spanning PostgreSQL, Python, APIs, schedulers, event streams, and distributed services.**