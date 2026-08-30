# 08- Date and Time Conversion

## Overview

Date and time conversion is the process of changing temporal values between SQL data types or between textual representations and temporal types.

In production backend systems, conversion is commonly required when:

- Importing timestamps from external systems.
- Converting `datetime` values to `date`.
- Converting timestamps to strings for exports.
- Parsing API or legacy text input.
- Normalizing data before comparison.
- Producing reporting-oriented date values.
- Interoperating with systems that use different temporal representations.

The critical engineering distinction is between **conversion**, **normalization**, and **presentation**:

| Operation | Purpose | Example |
| --- | --- | --- |
| Conversion | Change the data type | `DATETIME2` → `DATE` |
| Parsing | Interpret text as a temporal value | `'2026-08-30'` → `DATE` |
| Normalization | Establish a consistent temporal representation | Local timestamp → UTC |
| Formatting | Produce human-readable text | `2026-08-30` → `30 Aug 2026` |

SQL should primarily handle conversion, parsing, and data normalization. Human-oriented formatting is usually better handled by the application or presentation layer.

## Why Date and Time Conversion Matters

Temporal data crosses multiple system boundaries in backend architectures:

```mermaid
flowchart LR
    A[Client / External System] --> B[API]
    B --> C[Application]
    C --> D[Database]
    D --> E[Temporal Query]
    E --> F[Application Serialization]
    F --> G[Client]
```

A production system must preserve:

- The actual point in time.
- The intended time zone.
- Precision.
- Ordering semantics.
- Date-only vs timestamp semantics.
- A stable representation across services.

A conversion that appears harmless can change the meaning of the data.

For example:

```text
2026-08-30 23:30 UTC
```

may correspond to:

```text
2026-08-31 05:00 IST
```

If a timestamp is converted to a `DATE` before the correct time zone is applied, the resulting calendar date can be wrong.

## SQL Server Temporal Types

SQL Server provides several temporal types with different semantics.

| Type | Precision / behavior | Time zone offset | Typical use |
| --- | --- | --- | --- |
| `DATE` | Calendar date only | No | Birth dates, business dates |
| `TIME` | Time of day | No | Opening hours, schedules |
| `DATETIME` | Legacy date/time type | No | Legacy schemas |
| `SMALLDATETIME` | Lower precision | No | Legacy coarse timestamps |
| `DATETIME2` | Higher precision | No | General timestamp storage |
| `DATETIMEOFFSET` | Date/time + UTC offset | Yes | Values where offset information must be retained |

For new SQL Server schemas, `DATETIME2` is generally preferable to legacy `DATETIME` when a time-zone-independent timestamp is appropriate.

Use `DATETIMEOFFSET` when the offset is part of the required stored semantics.

## Converting DATETIME2 to DATE

Converting a timestamp to `DATE` removes the time component.

```sql
SELECT CAST(created_at AS DATE) AS created_date
FROM orders;
```

For:

```text
2026-08-30 14:35:42.1234567
```

the result is:

```text
2026-08-30
```

This is appropriate when the business meaning is explicitly date-only.

Typical examples:

- Customer birth date.
- Invoice date.
- Business calendar date.
- Daily reporting bucket.

It is not appropriate when the time component is required for ordering or event processing.

## Converting DATE to DATETIME2

A `DATE` can be converted into a timestamp:

```sql
SELECT CAST(order_date AS DATETIME2)
FROM orders;
```

The missing time component is filled using the type conversion rules, typically resulting in midnight:

```text
2026-08-30
        ↓
2026-08-30 00:00:00
```

Do not interpret this as the actual event time. It represents an artificial time created from a date-only value.

This distinction matters when migrating data from a date-only legacy column into a timestamp-based schema.

## Converting TIME

A `TIME` value can be converted into other compatible temporal types:

```sql
SELECT CAST(start_time AS DATETIME2)
FROM schedules;
```

The resulting value receives a date component according to SQL Server's conversion rules.

For business scheduling, avoid assuming that a `TIME` value represents a unique point in time. `09:00` without a date and time-zone context is only a time of day.

## Converting Between DATETIME2 and DATETIME

```sql
SELECT CAST(created_at AS DATETIME)
FROM orders;
```

The conversion may reduce precision because `DATETIME` has lower temporal precision than `DATETIME2`.

For example:

```text
DATETIME2:
2026-08-30 14:35:42.1234567

DATETIME:
2026-08-30 14:35:42.123
```

Do not use this conversion merely for convenience when the application depends on high-resolution timestamps.

For new schemas, prefer keeping `DATETIME2` unless compatibility with an existing system requires `DATETIME`.

## Date/Time to String

A temporal value can be converted to a string using `CONVERT`.

```sql
SELECT
    CONVERT(VARCHAR(10), created_at, 23) AS created_date
FROM orders;
```

Style `23` produces:

```text
2026-08-30
```

A timestamp can be converted similarly:

```sql
SELECT
    CONVERT(VARCHAR(19), created_at, 120) AS created_at_text
FROM orders;
```

Result:

```text
2026-08-30 14:35:42
```

This is useful for exports and integrations that explicitly require textual values.

However, do not convert timestamps to strings merely to make an API response look convenient. Preserve temporal types through the application boundary when possible.

## Common SQL Server Date Conversion Styles

Some useful `CONVERT` styles include:

| Style | Representation | Typical use |
| --- | --- | --- |
| `23` | `yyyy-mm-dd` | Date-only output |
| `120` | `yyyy-mm-dd hh:mi:ss` | Standard timestamp without offset |
| `121` | `yyyy-mm-dd hh:mi:ss.mmm` | Timestamp with milliseconds |
| `126` | ISO-style `yyyy-mm-ddThh:mi:ss...` | Machine-oriented interchange |

Example:

```sql
SELECT
    CONVERT(VARCHAR(33), created_at, 126)
FROM orders;
```

Style codes are SQL Server-specific and should not be treated as portable SQL.

## String to DATE

When external data contains a date as text, convert it explicitly.

For an ISO-style value:

```sql
SELECT TRY_CONVERT(
    DATE,
    '2026-08-30',
    23
) AS parsed_date;
```

The result is:

```text
2026-08-30
```

Using an explicit input format reduces ambiguity.

For ingestion pipelines, prefer `TRY_CONVERT()` when malformed records are possible.

```sql
SELECT
    payment_id,
    TRY_CONVERT(DATE, raw_payment_date, 23) AS payment_date
FROM payment_import;
```

Invalid values become `NULL` instead of aborting the conversion expression.

## String to DATETIME2

Use an explicit, deterministic representation for machine-generated timestamps.

```sql
SELECT TRY_CONVERT(
    DATETIME2,
    '2026-08-30T14:35:42.1234567',
    126
) AS parsed_timestamp;
```

For external systems, define the timestamp contract explicitly.

For example:

```text
ISO 8601
UTC
Explicit offset when applicable
```

is significantly safer than relying on ambiguous localized strings.

## Why Ambiguous Dates Are Dangerous

Avoid input such as:

```text
08/30/2026
```

or:

```text
30/08/2026
```

when the input contract is not explicit.

Different systems may interpret the same string differently.

Prefer:

```text
2026-08-30
```

and:

```text
2026-08-30T14:35:42.1234567Z
```

for machine-to-machine communication.

The application, database, and integration contract should agree on the representation.

## TRY_CAST vs TRY_CONVERT

For SQL Server:

```sql
SELECT TRY_CAST('2026-08-30' AS DATE);
```

and:

```sql
SELECT TRY_CONVERT(DATE, '2026-08-30', 23);
```

serve similar purposes, but `TRY_CONVERT()` provides SQL Server-specific style support.

| Function | Invalid input | Style support | Portability |
| --- | --- | --- | --- |
| `CAST` | Error | No | High |
| `CONVERT` | Error | Yes | SQL Server-specific |
| `TRY_CAST` | `NULL` | No | SQL Server-specific syntax |
| `TRY_CONVERT` | `NULL` | Yes | SQL Server-specific |

Use `TRY_*` functions when malformed input is expected and should be handled as data-quality failures rather than query failures.

Do not blindly replace every `CAST` with `TRY_CAST`. If invalid data indicates a programming or integrity bug, silently producing `NULL` can hide the problem.

## Date vs Timestamp Semantics

A senior engineer should distinguish:

```text
DATE
```

from:

```text
TIMESTAMP
```

A date answers:

> Which calendar day?

A timestamp answers:

> At what point in time?

For example:

```text
customer_birth_date = 1995-07-14
```

should usually be a `DATE`.

An event such as:

```text
payment_processed_at = 2026-08-30T14:35:42Z
```

requires timestamp semantics.

Do not convert one into the other simply because a downstream system accepts both.

## Time Zone Conversion

Time zones are one of the most error-prone areas of temporal data processing.

A timestamp without time-zone information:

```text
2026-08-30 14:35:42
```

does not identify a globally unique instant.

A timestamp with an offset:

```text
2026-08-30 14:35:42 +05:30
```

contains more information.

SQL Server's `DATETIMEOFFSET` can represent the offset:

```sql
SELECT CAST(
    '2026-08-30 14:35:42 +05:30'
    AS DATETIMEOFFSET
) AS event_time;
```

For systems operating across regions, explicitly define whether timestamps are:

- UTC instants.
- Local times.
- Offset-aware timestamps.
- Date-only business values.

## AT TIME ZONE

SQL Server provides `AT TIME ZONE` for time-zone conversion and interpretation.

For example:

```sql
SELECT
    created_at AT TIME ZONE 'India Standard Time' AS created_at_ist
FROM orders;
```

If `created_at` is a `DATETIME2`, SQL Server interprets it as being in the specified zone and returns a `DATETIMEOFFSET`.

This distinction is important:

```text
DATETIME2
    ↓ AT TIME ZONE
DATETIMEOFFSET
```

The operation is not merely formatting. It assigns or converts time-zone semantics.

## Converting UTC to Local Time

Suppose the database stores UTC using `DATETIME2`:

```text
2026-08-30 09:00:00
```

You can convert it to India Standard Time:

```sql
SELECT
    created_at AT TIME ZONE 'UTC'
        AT TIME ZONE 'India Standard Time' AS created_at_ist
FROM orders;
```

Conceptually:

```mermaid
flowchart LR
    A[UTC DATETIME2] --> B[Interpret as UTC]
    B --> C[DATETIMEOFFSET]
    C --> D[Convert to Target Time Zone]
    D --> E[Local DATETIMEOFFSET]
```

This should be used only when the source value is genuinely UTC.

Applying a UTC interpretation to local data produces an incorrect instant.

## Daylight Saving Time

Time zones are not simply fixed numeric offsets.

For example:

```text
UTC+05:30
```

is a fixed offset commonly used by India, while many other regions change their offsets depending on daylight-saving rules.

Prefer named time zones when rules matter:

```sql
AT TIME ZONE 'Eastern Standard Time'
```

rather than manually adding or subtracting hours.

Manual arithmetic such as:

```sql
DATEADD(HOUR, -5, created_at)
```

can become incorrect when daylight-saving rules change.

## Converting to UTC

For distributed systems, UTC is generally the preferred canonical representation for event timestamps.

If an offset-aware value is available:

```sql
SELECT
    event_time AT TIME ZONE 'UTC'
FROM events;
```

The resulting value represents the same instant in UTC.

The application can then convert the timestamp to the user's display time zone at the presentation boundary.

A common architecture is:

```text
User / Service
     ↓
Explicit timezone-aware timestamp
     ↓
Application
     ↓
UTC canonical representation
     ↓
Database
     ↓
UTC event timestamp
     ↓
Application
     ↓
User's timezone
```

## Date Conversion After Time Zone Conversion

The order of operations matters.

Suppose:

```text
UTC:
2026-08-30 23:30
```

In India:

```text
2026-08-31 05:00
```

If the business asks for the **local calendar date**, convert to the required time zone first and then extract the date.

Conceptually:

```text
UTC timestamp
    ↓
Convert to business/user timezone
    ↓
Extract DATE
```

not:

```text
UTC timestamp
    ↓
Extract DATE
    ↓
Convert timezone
```

The latter can produce the wrong business date near midnight.

## Filtering by Date

A common production query is:

> Return all orders created on 2026-08-30.

Avoid:

```sql
SELECT *
FROM orders
WHERE CAST(created_at AS DATE) = '2026-08-30';
```

Although logically correct, applying a function to the indexed column can make efficient index access more difficult.

Prefer a half-open timestamp range:

```sql
SELECT *
FROM orders
WHERE created_at >= '2026-08-30T00:00:00'
  AND created_at <  '2026-08-31T00:00:00';
```

This preserves the native column type.

The pattern is:

```text
[start_of_day, start_of_next_day)
```

It avoids problems with fractional-second precision and does not require inventing an end-of-day timestamp such as `23:59:59.999`.

## Filtering by Local Business Date

If `created_at` is stored in UTC but the business query is based on a local time zone, calculate the UTC boundaries first.

Conceptually:

```text
Local business date
       ↓
Start/end local timestamps
       ↓
Convert boundaries to UTC
       ↓
Range predicate on UTC column
       ↓
Index-friendly query
```

The exact implementation should use the database's time-zone rules rather than fixed offset arithmetic.

For high-volume workloads, precomputing query boundaries in the application can also be appropriate, provided the application and database use consistent time-zone rules.

## Conversion in WHERE Clauses

Avoid:

```sql
WHERE CONVERT(DATE, created_at) = @business_date
```

for a large indexed table when a range predicate can express the same condition.

Prefer:

```sql
WHERE created_at >= @start_utc
  AND created_at < @end_utc
```

This keeps the predicate aligned with the stored type and typically provides a better path for index seeks.

The optimizer's actual choice depends on indexes, statistics, cardinality, and query shape, so validate with the execution plan.

## Conversion in JOIN Conditions

Temporal type mismatches can also affect joins.

Avoid repeatedly converting one side of a large join:

```sql
SELECT ...
FROM events e
JOIN legacy_events l
    ON CAST(e.event_time AS DATE) = l.event_date;
```

If the business requirement is a date-level relationship, consider whether the data model should contain a normalized date key or whether the join should be expressed using a range.

For high-volume analytical workloads, a calendar/date dimension can also simplify date-oriented joins and reporting.

## Precision and Rounding

Temporal precision matters when converting between types.

For example:

```sql
SELECT CAST(
    '2026-08-30 14:35:42.1234567'
    AS DATETIME2(3)
);
```

reduces the precision to milliseconds.

Use precision based on the domain:

| Requirement | Typical choice |
| --- | --- |
| Date only | `DATE` |
| Second-level precision | `DATETIME2(0)` |
| Millisecond precision | `DATETIME2(3)` |
| Higher precision | `DATETIME2(6)` or `DATETIME2(7)` |
| Offset-aware value | `DATETIMEOFFSET` |

Do not choose maximum precision automatically. Precision should reflect the business requirement and storage/query characteristics.

## Conversion and Backend APIs

An API should generally preserve temporal semantics rather than rely on database-specific formatting.

A database query can return:

```sql
SELECT
    order_id,
    created_at
FROM orders;
```

The Python application can serialize the timestamp using its API contract.

For example, a REST response may expose:

```json
{
  "order_id": 102481,
  "created_at": "2026-08-30T14:35:42.123456Z"
}
```

The important architectural boundary is:

```text
Database temporal type
        ↓
Application temporal type
        ↓
API serialization format
```

Do not force database queries to produce presentation strings unless the database is explicitly responsible for the output format.

## Django and FastAPI Considerations

In Django and FastAPI applications, timestamps should normally remain temporal values until serialization.

For example, application code can receive a database timestamp as a Python `datetime` and serialize it according to the API contract.

A typical service architecture is:

```text
PostgreSQL / SQL Server
        ↓
ORM / Database Driver
        ↓
Python datetime
        ↓
Pydantic / Django Serializer
        ↓
ISO 8601 JSON
```

The exact database type differs by engine, but the architectural principle is the same: keep temporal values typed for as long as possible.

For distributed services, ensure all services agree on:

- UTC vs local time.
- Offset handling.
- Precision.
- ISO 8601 representation.
- Date-only semantics.
- Nullability.

## Production Example: Event Processing

Consider an order-processing service using Kafka.

An event may contain:

```json
{
  "event_type": "order.created",
  "occurred_at": "2026-08-30T09:15:42.123Z"
}
```

The ingestion service should:

1. Parse the timestamp.
2. Validate the representation.
3. Normalize it to the system's canonical temporal representation.
4. Persist it without losing precision.
5. Convert to a local time zone only when required for business logic or presentation.

Avoid storing:

```text
"30/08/2026 14:45"
```

as the canonical event timestamp.

It loses information about the time zone and makes interoperability harder.

## Production Example: Daily Reports

Suppose a business wants:

> Orders created during August 30 in India Standard Time.

If the database stores UTC timestamps, the reporting system should define the local-day boundaries and query the corresponding UTC interval.

The important distinction is:

```text
Calendar day ≠ fixed UTC interval without timezone context
```

A "day" is a business concept whose boundaries depend on the relevant time zone.

This becomes especially important for systems operating across multiple regions.

## Production Example: Data Import

Suppose a legacy system provides:

```text
order_id | created_at_text
---------+---------------------------
1001     | 2026-08-30T09:15:42.123Z
1002     | invalid
1003     | 2026-08-30T10:22:11.500Z
```

A staging query can validate the input:

```sql
SELECT
    order_id,
    created_at_text,
    TRY_CONVERT(
        DATETIMEOFFSET,
        created_at_text,
        127
    ) AS created_at
FROM legacy_orders;
```

Invalid rows can then be isolated:

```sql
SELECT
    order_id,
    created_at_text
FROM legacy_orders
WHERE created_at_text IS NOT NULL
  AND TRY_CONVERT(
      DATETIMEOFFSET,
      created_at_text,
      127
  ) IS NULL;
```

This creates a clear ingestion pipeline:

```text
Raw text
   ↓
Parse
   ↓
Validate
   ↓
Normalize timezone
   ↓
Persist typed value
```

## Performance Considerations

Temporal conversions can become expensive when applied to millions of rows.

Be particularly cautious with:

```sql
WHERE CAST(created_at AS DATE) = @date
```

and:

```sql
WHERE FORMAT(created_at, 'yyyy-MM-dd') = @date_text
```

The second form is especially unsuitable for high-volume filtering because it converts values into presentation strings before comparison.

Prefer:

```sql
WHERE created_at >= @start
  AND created_at < @end
```

For production workloads:

- Keep timestamp columns in native temporal types.
- Index frequently filtered timestamp columns appropriately.
- Avoid functions on indexed columns when a range predicate is possible.
- Avoid formatting in transactional queries.
- Validate execution plans.
- Consider partitioning for very large time-series/event tables where workload characteristics justify it.

## Indexing and Date Filtering

A common index:

```sql
CREATE INDEX IX_orders_created_at
ON orders(created_at);
```

works naturally with range predicates:

```sql
SELECT order_id, created_at
FROM orders
WHERE created_at >= '2026-08-30T00:00:00'
  AND created_at <  '2026-08-31T00:00:00';
```

The database can use the ordered timestamp values to locate the relevant range.

By contrast:

```sql
WHERE CAST(created_at AS DATE) = '2026-08-30'
```

requires evaluating the expression against rows before determining whether they match, although optimizer behavior can vary by database and query shape.

Always inspect the actual execution plan for performance-critical queries.

## Security Considerations

Temporal conversion has security implications when timestamps are used for:

- Token expiration.
- Session expiry.
- Password reset links.
- Authorization windows.
- Audit records.
- Rate limiting.
- Event ordering.

Avoid using ambiguous local timestamps for security decisions.

Prefer a canonical instant, usually UTC, for comparisons such as:

```text
token_expires_at > current_time
```

Do not trust client-provided local time to determine whether an authorization window has expired.

The server should establish the authoritative current time.

## Reliability Considerations

Distributed systems can receive events with:

- Different time zones.
- Different precision.
- Missing offsets.
- Invalid strings.
- Clock skew.
- Delayed delivery.
- Duplicate timestamps.

Do not assume that timestamps alone provide a globally reliable ordering.

For event-driven systems such as Kafka consumers, distinguish:

```text
event occurred time
```

from:

```text
event received time
```

and:

```text
database inserted time
```

These can legitimately differ.

For example:

```text
occurred_at   = when producer generated event
received_at   = when consumer received event
created_at    = when database persisted record
```

Use the appropriate timestamp for each business and operational purpose.

## Monitoring and Data Quality

Temporal conversion failures should be observable.

Useful metrics include:

- Number of invalid date strings.
- Number of failed `TRY_CONVERT()` operations.
- Percentage of records missing timestamps.
- Records with timestamps outside expected ranges.
- Future-dated events.
- Unexpected time-zone offsets.
- Timestamp precision loss during migrations.

For ingestion systems, avoid silently converting invalid values to `NULL` without measuring the failures.

A successful query does not necessarily mean successful data processing.

## Common Mistakes

### Converting a Timestamp to DATE Too Early

Bad:

```sql
CAST(created_at AS DATE)
```

before applying the relevant time zone.

This can assign an event to the wrong business day.

Apply the required time-zone semantics first.

### Using Functions on Indexed Timestamp Columns

Bad:

```sql
WHERE CAST(created_at AS DATE) = @date
```

Prefer a half-open range:

```sql
WHERE created_at >= @start
  AND created_at < @end
```

### Manual Time-Zone Arithmetic

Bad:

```sql
DATEADD(HOUR, 5, created_at)
```

when the business logic actually requires a time-zone conversion.

Named time zones can account for regional rules such as daylight saving time.

### Treating DATETIME2 as UTC Automatically

`DATETIME2` does not contain time-zone information.

This:

```text
2026-08-30 14:00:00
```

does not inherently mean UTC.

The application/database contract must define its semantics.

### Storing Dates as VARCHAR

Bad:

```sql
created_at VARCHAR(50)
```

for actual timestamps.

This causes:

- Validation problems.
- Sorting problems.
- Comparison complexity.
- Time-zone ambiguity.
- More expensive queries.
- Increased data-quality risk.

Use native temporal types.

### Formatting for APIs in SQL

Bad:

```sql
CONVERT(VARCHAR(30), created_at, 126)
```

for every API query when the application serializer can produce the required representation.

Keep the value typed until the serialization boundary.

### Assuming Midnight Represents an Actual Event Time

Converting:

```text
2026-08-30
```

to:

```text
2026-08-30 00:00:00
```

does not mean the event happened at midnight.

It means the original data contained no time information.

### Using `TRY_CONVERT()` to Hide Data Problems

`TRY_CONVERT()` is valuable for controlled ingestion, but this can be dangerous:

```sql
UPDATE orders
SET created_at = TRY_CONVERT(DATETIME2, raw_created_at);
```

without measuring invalid rows.

Malformed data can silently become `NULL`.

Use staging tables, validation metrics, and explicit remediation for important data.

### Confusing Event Time with Processing Time

For distributed systems:

```text
occurred_at
```

and:

```text
processed_at
```

are not interchangeable.

Use the timestamp that matches the business question.

## Production Best Practices

| Concern | Recommendation |
| --- | --- |
| Canonical timestamps | Prefer UTC for distributed event timestamps |
| Time-zone-aware data | Use `DATETIMEOFFSET` when offset semantics must be retained |
| New SQL Server timestamp columns | Prefer `DATETIME2` over legacy `DATETIME` when appropriate |
| Date-only values | Use `DATE` |
| Time-only values | Use `TIME` |
| External textual timestamps | Parse using an explicit format |
| Invalid input | Use `TRY_CONVERT()` / `TRY_CAST()` where appropriate |
| Date filtering | Prefer `[start, end)` range predicates |
| API serialization | Preserve temporal types until the application boundary |
| User-local display | Convert to the user's time zone at the presentation boundary |
| DST-aware conversion | Use named time zones rather than fixed offsets |
| High-volume queries | Avoid unnecessary per-row conversion and formatting |
| Data migrations | Measure precision loss and invalid conversions |
| Security timestamps | Use authoritative server-side time |

## Interview Traps

| Question | Strong answer |
| --- | --- |
| What happens when `DATETIME2` is converted to `DATE`? | The time component is discarded |
| Does `DATETIME2` store a time zone? | No |
| When should `DATETIMEOFFSET` be used? | When the date/time value needs an associated UTC offset |
| Why prefer a timestamp range over `CAST(timestamp AS DATE)` in a filter? | It preserves the native column type and is generally more index-friendly |
| Why use `[start, end)` for date filtering? | It avoids fractional-second boundary bugs and works cleanly with timestamp precision |
| Why is `08/30/2026` a poor machine-to-machine date representation? | It is ambiguous and can depend on parsing conventions |
| What does `TRY_CONVERT()` return for invalid input? | `NULL` rather than a conversion error |
| Does `DATETIME2` automatically mean UTC? | No; UTC is a semantic convention, not encoded by `DATETIME2` |
| Why is manual `DATEADD(HOUR, ...)` risky for time-zone conversion? | It does not account for time-zone rules such as daylight saving time |
| Should SQL format timestamps for REST APIs? | Usually no; preserve typed values and let the serialization layer enforce the API contract |
| Why can converting a timestamp to `DATE` produce the wrong business date? | The conversion may occur before the timestamp is translated into the relevant local time zone |
| Are event timestamps guaranteed to provide total ordering? | No; clock skew, delayed delivery, duplicate timestamps, and distributed processing can make ordering ambiguous |

## Key Takeaways

- **Keep temporal data in native SQL types** such as `DATE`, `TIME`, `DATETIME2`, and `DATETIMEOFFSET`; avoid storing timestamps as strings.
- **Treat time zones as data semantics, not formatting**, and apply the correct time-zone interpretation before deriving business dates.
- **Use half-open timestamp ranges for date filtering** instead of applying `CAST` or formatting functions directly to indexed timestamp columns.
- **Use explicit parsing and `TRY_CONVERT()` for external data**, while monitoring failed conversions instead of silently hiding data-quality problems.
- **Preserve temporal types through the database and application layers**, converting to strings primarily at the API, export, or presentation boundary.