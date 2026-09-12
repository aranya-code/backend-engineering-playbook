# 09- Datetime Filtering

## Overview

Datetime filtering selects records based on temporal conditions such as:

```text
before a timestamp
after a timestamp
between two timestamps
during a specific day
within a rolling window
inside an incremental ETL interval
```

In Pandas, datetime filtering should be performed against properly typed datetime columns rather than timestamp strings.

A typical workflow is:

```text
raw timestamp
    ↓
pd.to_datetime()
    ↓
timezone normalization
    ↓
define time boundaries
    ↓
boolean datetime mask
    ↓
filtered DataFrame
```

Datetime filtering is foundational for:

```text
ETL pipelines
API pagination
reporting
event processing
database synchronization
incremental loads
SLA analysis
monitoring
```

The most important production concern is semantic correctness. A filter can execute successfully while selecting the wrong records because of timezone differences, ambiguous boundaries, or incorrect timestamp types.

---

## Why Datetime Filtering Matters

Most data-processing jobs operate on a time window.

Examples include:

```text
orders created today
payments from the previous hour
events after a watermark
requests during business hours
transactions for a reporting month
records modified since the previous ETL run
```

A common incremental query is:

```text
last_successful_watermark <= event_time < current_watermark
```

In Pandas:

```python
batch = events.loc[
    (events["event_time"] >= window_start)
    & (events["event_time"] < window_end)
]
```

This pattern provides deterministic, non-overlapping processing windows.

---

## Prerequisite: Datetime Dtype

Before filtering, ensure the column is datetime-like.

```python
events["event_time"] = pd.to_datetime(
    events["event_time"],
    utc=True,
    errors="raise",
)
```

Inspect the dtype:

```python
print(events["event_time"].dtype)
```

A properly typed column can be compared directly with Pandas timestamps.

Avoid filtering raw timestamp strings such as:

```python
events[
    events["event_time"] >= "2026-09-10"
]
```

unless the data model and string format are explicitly guaranteed to support lexical ordering.

Typed datetime comparisons are clearer and safer.

---

## Basic Greater-Than Filtering

To select records after a timestamp:

```python
cutoff = pd.Timestamp(
    "2026-09-10 12:00:00",
    tz="UTC",
)

recent = events.loc[
    events["event_time"] > cutoff
]
```

This includes only records strictly later than the cutoff.

For inclusive semantics:

```python
recent = events.loc[
    events["event_time"] >= cutoff
]
```

Choose `>` versus `>=` deliberately because boundary records can affect incremental processing.

---

## Less-Than Filtering

To select records before a timestamp:

```python
cutoff = pd.Timestamp(
    "2026-09-11 00:00:00",
    tz="UTC",
)

historical = events.loc[
    events["event_time"] < cutoff
]
```

This is useful for upper boundaries in incremental windows.

---

## Filtering Between Two Timestamps

The safest general-purpose pattern is an explicit boolean expression:

```python
start = pd.Timestamp(
    "2026-09-10 00:00:00",
    tz="UTC",
)

end = pd.Timestamp(
    "2026-09-11 00:00:00",
    tz="UTC",
)

daily_events = events.loc[
    (events["event_time"] >= start)
    & (events["event_time"] < end)
]
```

This represents:

```text
[start, end)
```

or:

```text
inclusive lower bound
exclusive upper bound
```

This convention is particularly useful for ETL and time-window processing.

---

## Why Half-Open Intervals Are Useful

Suppose two adjacent hourly jobs use:

```text
[10:00, 11:00)
[11:00, 12:00)
```

A record at exactly:

```text
11:00:00
```

belongs only to the second window.

This avoids:

```text
duplicate processing
overlapping reports
double-counted events
ambiguous watermark behavior
```

For incremental pipelines, prefer:

```python
event_time >= start
event_time < end
```

over:

```python
event_time >= start
event_time <= end
```

when windows are adjacent.

---

## `Series.between()`

Pandas provides a convenient helper:

```python
mask = events["event_time"].between(
    start,
    end,
)
```

By default, both endpoints are inclusive.

You can control boundary behavior:

```python
mask = events["event_time"].between(
    start,
    end,
    inclusive="left",
)
```

This represents:

```text
[start, end)
```

Possible `inclusive` values are conceptually:

```text
both
left
right
neither
```

For ETL windows, `inclusive="left"` is often useful.

---

## `between()` Versus Explicit Conditions

Both are valid:

```python
events["event_time"].between(
    start,
    end,
    inclusive="left",
)
```

and:

```python
(
    events["event_time"] >= start
) & (
    events["event_time"] < end
)
```

Use `between()` when the intent is simply a range check.

Use explicit conditions when:

```text
the boundaries have different business semantics
additional conditions are involved
the expression is easier to read explicitly
```

---

## Filtering by a Specific Day

If the requirement is:

> Select all events occurring on September 10, 2026 UTC.

Use a day window:

```python
start = pd.Timestamp(
    "2026-09-10",
    tz="UTC",
)

end = pd.Timestamp(
    "2026-09-11",
    tz="UTC",
)

daily_events = events.loc[
    (events["event_time"] >= start)
    & (events["event_time"] < end)
]
```

This is preferable to repeatedly extracting `.dt.date` for large datasets.

It also preserves efficient datetime comparisons.

---

## Filtering by Month

For a reporting month:

```python
start = pd.Timestamp(
    "2026-09-01",
    tz="UTC",
)

end = pd.Timestamp(
    "2026-10-01",
    tz="UTC",
)

monthly_events = events.loc[
    (events["event_time"] >= start)
    & (events["event_time"] < end)
]
```

Using the first instant of the next month as the exclusive upper boundary handles months with different lengths naturally.

Avoid hard-coding:

```textSeptember 30
```

or:

```text30 days
```

because calendar months are not uniformly sized.

---

## Filtering by Year

For a complete year:

```python
start = pd.Timestamp(
    "2026-01-01",
    tz="UTC",
)

end = pd.Timestamp(
    "2027-01-01",
    tz="UTC",
)

events_2026 = events.loc[
    (events["event_time"] >= start)
    & (events["event_time"] < end)
]
```

This pattern works for leap years without special cases.

---

## Filtering by Hour

For records during a particular hour:

```python
start = pd.Timestamp(
    "2026-09-10 14:00:00",
    tz="UTC",
)

end = pd.Timestamp(
    "2026-09-10 15:00:00",
    tz="UTC",
)

hourly_events = events.loc[
    (events["event_time"] >= start)
    & (events["event_time"] < end)
]
```

This is preferable to:

```python
events[
    events["event_time"].dt.hour == 14
]
```

when the requirement is a specific calendar hour.

The `.dt.hour` approach selects hour 14 across every date.

---

## Filtering by Recurring Hour

If the requirement truly is:

> Select all events that occurred between 09:00 and 17:00 on any day.

derive the local hour:

```python
events["hour"] = (
    events["event_time"]
    .dt.hour
)

business_hours = events.loc[
    events["hour"].between(
        9,
        16,
    )
]
```

A better alternative for precise minute-level boundaries is to compare time-of-day values or derive a normalized local timestamp depending on the use case.

Do not confuse:

```text
specific datetime interval
```

with:

```text
recurring time-of-day filter
```

---

## Timezone-Aware Filtering

Timezone-aware data should be compared with timezone-aware boundaries.

```python
events["event_time"] = pd.to_datetime(
    events["event_time"],
    utc=True,
)

start = pd.Timestamp(
    "2026-09-10 00:00:00",
    tz="UTC",
)

end = pd.Timestamp(
    "2026-09-11 00:00:00",
    tz="UTC",
)
```

Then:

```python
filtered = events.loc[
    (events["event_time"] >= start)
    & (events["event_time"] < end)
]
```

Do not compare a UTC-aware Series with a naive timestamp and assume Pandas can infer the intended timezone.

---

## Filtering in a Local Business Timezone

Suppose the source timestamps are stored in UTC but the business report uses:

```text
Asia/Kolkata
```

Convert before deriving local calendar boundaries:

```python
local_time = (
    events["event_time"]
    .dt.tz_convert("Asia/Kolkata")
)

start_local = pd.Timestamp(
    "2026-09-10 00:00:00",
    tz="Asia/Kolkata",
)

end_local = pd.Timestamp(
    "2026-09-11 00:00:00",
    tz="Asia/Kolkata",
)

daily_events = events.loc[
    (local_time >= start_local)
    & (local_time < end_local)
]
```

The filtering is then based on the business calendar rather than UTC calendar boundaries.

---

## Reporting Timezone Versus Storage Timezone

A common architecture is:

```text
storage
   ↓
UTC timestamp
   ↓
business timezone conversion
   ↓
reporting window
```

For example:

```text
PostgreSQL
    ↓
UTC
    ↓
Pandas
    ↓
Asia/Kolkata
    ↓
daily report
```

This avoids accidentally assigning a late-night UTC event to the wrong local business day.

---

## Filtering Missing Datetimes

Missing values do not satisfy normal datetime comparisons.

For example:

```python
filtered = events.loc[
    events["event_time"] >= start
]
```

will not include `NaT` records.

If missing timestamps need explicit handling:

```python
missing = events.loc[
    events["event_time"].isna()
]
```

Then decide whether they should be:

```text
rejected
quarantined
filled
investigated
excluded
```

Do not silently treat missing timestamps as belonging outside every business window without understanding the data-quality implications.

---

## Filtering Invalid Dates

If timestamps were parsed with coercion:

```python
events["event_time"] = pd.to_datetime(
    events["event_time"],
    utc=True,
    errors="coerce",
)
```

then invalid source values become `NaT`.

Separate them:

```python
invalid = events.loc[
    events["event_time"].isna()
]
```

before applying the business window.

This allows the pipeline to distinguish:

```text
not in time range
```

from:

```text
timestamp could not be parsed
```

---

## Additional Conditions

Datetime filters are often combined with business conditions.

Example:

```python
start = pd.Timestamp(
    "2026-09-10",
    tz="UTC",
)

end = pd.Timestamp(
    "2026-09-11",
    tz="UTC",
)

completed_orders = orders.loc[
    (orders["created_at"] >= start)
    & (orders["created_at"] < end)
    & orders["status"].eq("completed")
]
```

Use `&` for element-wise AND:

```python
condition_a & condition_b
```

and `|` for element-wise OR:

```python
condition_a | condition_b
```

Wrap each condition in parentheses.

---

## `query()` for Datetime Filtering

`query()` can improve readability for some conditions.

Example:

```python
filtered = events.query(
    "@start <= event_time < @end"
)
```

Here:

```text
@start
@end
```

refer to Python variables outside the DataFrame.

This can be useful for readable filter expressions.

For complex logic, explicit `.loc[]` conditions are often easier to debug.

---

## Datetime Filtering With `.loc`

For production pipelines, `.loc` provides a clear filtering boundary:

```python
filtered = events.loc[
    (events["event_time"] >= start)
    & (events["event_time"] < end)
]
```

It explicitly indicates row selection.

Add `.copy()` when a separate mutable DataFrame is required:

```python
filtered = events.loc[
    (events["event_time"] >= start)
    & (events["event_time"] < end)
].copy()
```

This avoids ambiguity when subsequent transformations are applied to the filtered result.

---

## Filtering by Date Components

You can filter by components:

```python
september_orders = orders.loc[
    orders["created_at"].dt.month.eq(9)
]
```

This means:

> every September record

not:

> September 2026.

For a specific year and month:

```python
september_2026 = orders.loc[
    orders["created_at"].dt.year.eq(2026)
    & orders["created_at"].dt.month.eq(9)
]
```

For large datasets, a timestamp range is often more directly aligned with an indexed database predicate and avoids unnecessary component extraction.

---

## Range Filtering Versus Component Filtering

| Requirement | Preferred approach |
| --- | --- |
| Specific day | Timestamp range |
| Specific month | Timestamp range |
| Specific year | Timestamp range |
| Specific reporting period | Timestamp range |
| Any September across years | `.dt.month` |
| Any Monday across years | `.dt.dayofweek` |
| Specific hour on every day | Time-of-day logic |
| Arbitrary start/end window | Timestamp comparison |

The distinction is important because component filters describe recurring calendar properties, while ranges describe a specific temporal interval.

---

## Incremental ETL Filtering

Datetime filtering is central to incremental ingestion.

Suppose the previous successful watermark is:

```python
watermark = pd.Timestamp(
    "2026-09-10 10:00:00",
    tz="UTC",
)

current = pd.Timestamp(
    "2026-09-10 11:00:00",
    tz="UTC",
)
```

Select:

```python
batch = events.loc[
    (events["updated_at"] >= watermark)
    & (events["updated_at"] < current)
]
```

Then process the batch.

A robust pipeline should advance the watermark only after the batch has been successfully persisted.

---

## Watermark and Failure Recovery

A reliable incremental pipeline resembles:

```mermaid
flowchart LR
    A[Previous Watermark] --> B[Define [start, end)]
    B --> C[Filter Events]
    C --> D[Transform and Validate]
    D --> E[Persist Successfully]
    E --> F[Commit New Watermark]
    D --> G[Failure / Retry]
    G --> C
```

The important reliability property is:

```text
process success
        ↓
commit watermark
```

not:

```text
select records
        ↓
advance watermark
        ↓
process
```

Otherwise failed work can be skipped permanently.

---

## Late-Arriving Data

A strict watermark may miss events that arrive late.

For example:

```text
event_time = 09:55
ingested_at = 10:07
```

A job that processed:

```text
[09:00, 10:00)
```

may not have seen the event.

Production systems may use a lookback interval:

```text
read from watermark - lookback
        ↓
deduplicate
        ↓
reprocess safely
```

Example:

```python
lookback_start = watermark - pd.Timedelta(
    minutes=10
)

batch = events.loc[
    (events["event_time"] >= lookback_start)
    & (events["event_time"] < current)
]
```

Lookback windows require idempotency or deduplication.

---

## Event Time Versus Updated Time

A database table may contain:

```text
created_at
updated_at
event_time
ingested_at
```

Choose the correct timestamp for the job.

For incremental synchronization, `updated_at` may be appropriate.

For business-event analytics, `event_time` may be the correct field.

Using the wrong timestamp can produce:

```text
missed records
duplicate records
incorrect reporting
```

---

## Filtering PostgreSQL Data

When the source is a database, push time filtering into SQL when practical.

Instead of:

```python
events = pd.read_sql(
    "SELECT * FROM events",
    connection,
)

events["created_at"] = pd.to_datetime(
    events["created_at"],
    utc=True,
)

events = events.loc[
    (events["created_at"] >= start)
    & (events["created_at"] < end)
]
```

prefer:

```sql
SELECT
    event_id,
    created_at,
    event_type
FROM events
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

This reduces:

```text
rows transferred
network usage
Pandas memory
downstream processing
```

It also allows PostgreSQL to use an appropriate index on the timestamp column.

---

## API Date Filtering

REST APIs commonly expose temporal filters such as:

```text
created_after
created_before
updated_since
```

A client-side Pandas filter may be required after fetching data:

```python
response_df["updated_at"] = pd.to_datetime(
    response_df["updated_at"],
    utc=True,
    errors="raise",
)

filtered = response_df.loc[
    (response_df["updated_at"] >= start)
    & (response_df["updated_at"] < end)
]
```

When the API supports server-side filtering, use it first.

Pandas should not download millions of records merely to discard most of them locally.

---

## CSV Batch Processing

For large CSV inputs:

```python
for chunk in pd.read_csv(
    "events.csv",
    usecols=[
        "event_id",
        "event_time",
        "event_type",
    ],
    chunksize=100_000,
):
    chunk["event_time"] = pd.to_datetime(
        chunk["event_time"],
        utc=True,
        errors="coerce",
    )

    filtered = chunk.loc[
        (chunk["event_time"] >= start)
        & (chunk["event_time"] < end)
    ]

    process(filtered)
```

Chunking controls memory usage.

The global correctness of the time window remains independent of the individual chunk boundaries.

---

## Filtering on a DatetimeIndex

If time is the index:

```python
events = events.set_index(
    "event_time"
).sort_index()
```

time-based slicing becomes convenient.

For a suitable sorted `DatetimeIndex`:

```python
daily = events.loc[
    "2026-09-10":"2026-09-10"
]
```

However, explicit timestamp ranges are often clearer in reusable ETL functions because the exact boundary semantics remain visible.

---

## Sorted Datetime Data

Sort before relying on time-oriented operations that benefit from ordered data:

```python
events = events.sort_values(
    "event_time"
)
```

Sorting can support:

```text
binary-search-style indexing
time-window processing
rolling operations
as-of joins
ordered event analysis
```

The performance trade-off matters: sorting a large dataset has a cost, so avoid repeatedly sorting the same unchanged data.

---

## Filtering With Duplicate Timestamps

A time range can contain many records with identical timestamps.

Example:

```text
10:00:00 → event A
10:00:00 → event B
10:00:00 → event C
```

A timestamp is not an identity key.

Do not deduplicate simply because timestamps are equal.

Use the appropriate business identifier:

```python
events = events.drop_duplicates(
    subset=["event_id"],
)
```

---

## Performance Characteristics

Datetime filtering is generally efficient when operating on a properly typed Series.

Performance can still be affected by:

```text
dataset size
timezone conversions
additional component extraction
boolean mask creation
unnecessary DataFrame copies
sorting
database I/O
```

Prefer:

```python
events.loc[
    (events["event_time"] >= start)
    & (events["event_time"] < end)
]
```

over row-wise functions:

```python
events[
    events["event_time"].apply(
        lambda value: value >= start
        and value < end
    )
]
```

The vectorized expression matches Pandas' column-oriented execution model.

---

## Avoid Repeated Timezone Conversion

If the same local reporting timezone is required across several operations:

```python
local_time = (
    events["event_time"]
    .dt.tz_convert("Asia/Kolkata")
)
```

reuse the result rather than repeatedly converting the same column.

For example:

```python
local_time = (
    events["event_time"]
    .dt.tz_convert("Asia/Kolkata")
)

business_day = (
    local_time.dt.normalize()
)

business_hours = (
    local_time.dt.hour.between(9, 17)
)
```

Use intermediate variables when they make temporal semantics explicit.

---

## Memory Considerations

Filtering itself creates a new selection result.

For large DataFrames:

```text
project only required columns
filter early
avoid unnecessary copies
process in chunks
```

Example:

```python
filtered = events.loc[
    condition,
    [
        "event_id",
        "event_time",
        "event_type",
    ],
]
```

Selecting only required columns can reduce the memory footprint of subsequent processing.

Use `.copy()` only when an independent mutable result is actually required.

---

## Filtering Empty DataFrames

A valid time window may contain zero records.

```python
filtered = events.loc[
    (events["event_time"] >= start)
    & (events["event_time"] < end)
]
```

The result should be an empty DataFrame with the expected schema.

Production code should distinguish:

```text
empty valid window
```

from:

```text
failed ingestion
```

An empty result is not necessarily an error.

---

## Validation of Time Windows

Validate window definitions before filtering.

Example:

```python
if end <= start:
    raise ValueError(
        "Window end must be after window start."
    )
```

This catches configuration errors before they silently produce empty or incorrect batches.

For incremental jobs:

```text
start
end
timezone
frequency
lookback
watermark
```

should be explicit configuration values.

---

## Security Considerations

Datetime filters are often exposed through REST APIs.

Do not allow unrestricted time ranges to become an uncontrolled database or Pandas workload.

For example:

```text
client asks for 10 years of high-volume events
```

can cause:

```text
large database scans
high network transfer
high memory consumption
long request latency
```

Apply controls such as:

```text
maximum query range
pagination
server-side filtering
authentication and authorization
rate limiting
database indexes
```

For user-facing endpoints, enforce limits before materializing large DataFrames.

---

## Monitoring

Production pipelines should monitor:

| Metric | Why it matters |
| --- | --- |
| Rows per time window | Detect unexpected volume changes |
| Empty-window frequency | Detect upstream or scheduling issues |
| Late-event count | Detect delivery delays |
| Watermark lag | Detect processing backlog |
| Future-event count | Detect clock/source problems |
| Null timestamp count | Detect data-quality issues |
| Window processing duration | Track performance |
| Reprocessed row count | Detect excessive overlap or instability |

Unexpected changes in records per window can identify upstream failures before downstream reports become obviously incorrect.

---

## Common Mistakes

### Comparing Strings Instead of Datetimes

String comparisons depend on formatting.

Prefer:

```python
pd.to_datetime(...)
```

followed by datetime comparison.

---

### Using Inclusive Endpoints Everywhere

Using:

```python
timestamp <= end
```

for every batch can double-count boundary records.

Prefer half-open windows:

```text
[start, end)
```

for adjacent ETL intervals.

---

### Mixing Timezones

Comparing UTC timestamps with naive or local timestamps can produce incorrect results or errors.

Normalize timezone semantics before filtering.

---

### Filtering by `.dt.month` for a Specific Month

This:

```python
events["event_time"].dt.month == 9
```

selects every September across every year.

For September 2026, use a timestamp range.

---

### Extracting `.dt.date` for Every Filter

Creating Python date objects for large datasets is unnecessary when a timestamp boundary can express the filter directly.

Prefer:

```python
event_time >= start
```

and:

```python
event_time < end
```

---

### Advancing the Watermark Before Successful Processing

This can permanently skip records after a failure.

Commit the new watermark only after successful downstream persistence.

---

### Ignoring Late-Arriving Events

Event time and ingestion time can differ.

Use lookback and idempotent processing when late data matters.

---

### Downloading Everything From a Database or API

Filter at the source whenever practical.

Pandas should not become a substitute for indexed database predicates or server-side API filtering.

---

### Treating Empty Results as Failures

An empty time window can be perfectly valid.

Use explicit pipeline expectations to distinguish empty data from system failure.

---

### Treating Timestamp Equality as Uniqueness

Multiple records can share the same timestamp.

Use business keys for deduplication.

---

## Interview Traps

### Why Prefer `[start, end)`?

It prevents adjacent time windows from overlapping.

For example:

```text
[10:00, 11:00)
[11:00, 12:00)
```

has no duplicated boundary.

---

### `between()` and Explicit Comparisons

`between()` provides concise range filtering and supports explicit inclusivity.

Explicit comparisons can be clearer for complex business logic.

---

### Why Use `.loc[]`?

It provides explicit row selection and works naturally with combined boolean masks.

---

### Why Can a Datetime Filter Return No Rows Without an Error?

Possible causes include:

```text
wrong timezone
wrong date range
incorrect boundary
incorrect dtype
NaT values
wrong timestamp column
```

A technically valid filter can still be semantically incorrect.

---

### Why Filter in SQL Before Pandas?

Because the database can often:

```text
use indexes
reduce rows
reduce network transfer
reduce Pandas memory usage
```

before materialization.

---

### What Is a Watermark?

A watermark records the temporal progress of an incremental pipeline.

It helps determine the next processing window and supports recovery after successful processing.

---

### Why Is Late Data a Problem?

An event can have:

```text
event_time earlier than the current watermark
```

but arrive after that time window was processed.

Lookback and idempotent processing can address this.

---

### Why Isn't Timestamp Enough for Deduplication?

Many events can legitimately share the exact same timestamp.

Deduplication should use the actual business identity.

---

## Production Checklist

Before deploying datetime filtering logic, verify:

```text
[ ] Datetime columns are correctly typed
[ ] Timezone semantics are documented
[ ] Filter boundaries are explicit
[ ] Inclusive/exclusive behavior is deliberate
[ ] Half-open intervals are used where appropriate
[ ] Specific periods use timestamp ranges
[ ] Recurring calendar components are distinguished from fixed ranges
[ ] Missing timestamps have a defined policy
[ ] Invalid parsed values are separated from out-of-range values
[ ] Start and end boundaries are validated
[ ] Event time versus processing/update time is intentional
[ ] Incremental watermark behavior is transactional
[ ] Watermarks advance only after successful processing
[ ] Late-arriving data has a defined strategy
[ ] Duplicate handling uses business keys
[ ] Database filters are pushed down where practical
[ ] API-side time filtering is used where available
[ ] Large CSV workloads use projection/chunking where appropriate
[ ] Unnecessary timezone conversions are avoided
[ ] Unnecessary DataFrame copies are avoided
[ ] Empty windows are treated correctly
[ ] Query ranges are bounded for user-facing APIs
[ ] Time-window volume is monitored
[ ] Watermark lag is monitored
[ ] Boundary, timezone, null, and late-event cases are tested
```

## Key Takeaways

- Filter against properly typed datetime columns using vectorized comparisons, preferably with explicit boundaries such as `[start, end)` for ETL and incremental processing.
- Timezone semantics are part of filter correctness: normalize timestamps and boundaries consistently before selecting business-sensitive dates or reporting windows.
- Use timestamp ranges for specific days, months, years, and arbitrary intervals; use `.dt` components only when the requirement is a recurring calendar property across dates.
- Reliable incremental filtering requires correct watermark management, late-event handling, idempotency, and advancing the watermark only after successful persistence.
- Push temporal predicates into PostgreSQL or API queries when practical, and monitor window volume, watermark lag, null timestamps, late data, and other anomalies in production.