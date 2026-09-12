# 11- Timedeltas

## Overview

A `Timedelta` represents a duration or elapsed amount of time.

In Pandas, `Timedelta` is used when the requirement is about:

```text
how long something took
how far apart two events are
adding a fixed duration
subtracting a fixed duration
measuring latency
calculating SLA duration
building rolling time windows
```

The key distinction is:

```text
Timestamp
→ a point in time

Timedelta
→ a duration between points in time
```

For example:

```text
order_created_at   = 10:00:00
order_completed_at = 10:07:30

processing_time = 7 minutes 30 seconds
```

A typical processing flow is:

```text
timestamp A
    +
timestamp B
    ↓
datetime subtraction
    ↓
Timedelta
    ↓
duration / SLA / latency metric
```

---

## Why Timedeltas Matter

Backend and data-engineering systems routinely measure durations:

```text
API response time
payment processing time
order fulfillment time
Kafka event lag
Celery task runtime
database query duration
job execution time
customer response time
```

Example:

```python
orders["processing_time"] = (
    orders["completed_at"]
    - orders["created_at"]
)
```

The result is a timedelta-like Series.

From that result, you can derive:

```python
orders["processing_seconds"] = (
    orders["processing_time"]
    .dt.total_seconds()
)
```

This is more reliable than manually subtracting individual hour, minute, and second components.

---

## Timestamp Versus Timedelta

| Concept | Represents | Example |
| --- | --- | --- |
| `Timestamp` | Point in time | `2026-09-10 14:30:00` |
| `Timedelta` | Duration | `2 days 03:15:00` |
| `DateOffset` | Calendar-relative movement | `1 month later` |

This distinction is fundamental.

Use:

```python
Timestamp
```

for event times.

Use:

```python
Timedelta
```

for elapsed time.

Use:

```python
DateOffset
```

for calendar operations such as:

```text
one month later
next business day
month end
```

---

## Creating a Timedelta

The main constructor is:

```python
pd.Timedelta(...)
```

Examples:

```python
import pandas as pd


five_minutes = pd.Timedelta(
    minutes=5
)

two_hours = pd.Timedelta(
    hours=2
)

three_days = pd.Timedelta(
    days=3
)

combined = pd.Timedelta(
    days=1,
    hours=4,
    minutes=30,
)
```

These represent elapsed durations rather than calendar dates.

---

## Common Timedelta Units

| Unit | Example |
| --- | --- |
| `days` | `days=2` |
| `hours` | `hours=6` |
| `minutes` | `minutes=45` |
| `seconds` | `seconds=30` |
| `milliseconds` | `milliseconds=250` |
| `microseconds` | `microseconds=500` |
| `nanoseconds` | `nanoseconds=100` |

Use the highest meaningful precision supported by the source data.

Do not create artificial precision merely because the datatype supports it.

---

## String Construction

A Timedelta can also be constructed from a duration string:

```python
duration = pd.Timedelta(
    "2 days 04:30:00"
)
```

This is useful for:

```text
configuration
tests
human-readable duration inputs
```

For application configuration, validate the accepted format rather than allowing arbitrary user input to become an implicit duration contract.

---

## Parsing Durations With `pd.to_timedelta()`

For a Series of duration values:

```python
durations = pd.to_timedelta(
    values,
)
```

Example:

```python
durations = pd.Series(
    [
        "00:05:00",
        "00:15:30",
        "01:20:00",
    ]
)

parsed = pd.to_timedelta(
    durations,
)
```

This produces a timedelta-like Series.

`pd.to_timedelta()` is the duration equivalent of `pd.to_datetime()` for temporal points.

---

## Parsing Numeric Durations

Numeric values require an explicit unit when their meaning is not inherently clear.

Example:

```python
latency = pd.to_timedelta(
    metrics["latency_ms"],
    unit="ms",
)
```

If:

```text
latency_ms = 250
```

the resulting duration is:

```text
250 milliseconds
```

The unit is part of the source schema.

A value of:

```text
250
```

without a documented unit is ambiguous.

---

## Error Handling With `to_timedelta()`

Strict parsing:

```python
durations = pd.to_timedelta(
    values,
    errors="raise",
)
```

Coercion:

```python
durations = pd.to_timedelta(
    values,
    errors="coerce",
)
```

Invalid values become `NaT` when coercion is used.

Validate the result:

```python
invalid = durations.isna()

if invalid.any():
    raise ValueError(
        "Invalid duration values detected."
    )
```

As with datetime parsing, coercion without validation can silently hide source-data problems.

---

## Subtracting Timestamps

The most common source of Timedelta values is datetime subtraction.

```python
orders["processing_time"] = (
    orders["completed_at"]
    - orders["created_at"]
)
```

Example:

```text
created_at   = 10:15:00
completed_at = 10:22:30

processing_time
= 7 minutes 30 seconds
```

This is the correct representation for elapsed processing time.

---

## Example: Order Processing

```python
orders = pd.DataFrame(
    {
        "order_id": [
            "ORD-1001",
            "ORD-1002",
            "ORD-1003",
        ],
        "created_at": pd.to_datetime(
            [
                "2026-09-10 09:00:00+00:00",
                "2026-09-10 09:15:00+00:00",
                "2026-09-10 10:00:00+00:00",
            ]
        ),
        "completed_at": pd.to_datetime(
            [
                "2026-09-10 09:04:30+00:00",
                "2026-09-10 09:50:00+00:00",
                "2026-09-10 10:25:00+00:00",
            ]
        ),
    }
)

orders["processing_time"] = (
    orders["completed_at"]
    - orders["created_at"]
)
```

The resulting durations are:

```text
0 days 00:04:30
0 days 00:35:00
0 days 00:25:00
```

---

## Converting Timedelta to Seconds

Use:

```python
orders["processing_seconds"] = (
    orders["processing_time"]
    .dt.total_seconds()
)
```

This produces numeric values such as:

```text
270.0
2100.0
1500.0
```

This is useful for:

```text
metrics
thresholds
percentiles
dashboards
alerting
SLA calculations
```

---

## Other Timedelta Components

Timedeltas expose components through `.dt`.

Common properties include:

```python
duration.dt.days
duration.dt.seconds
duration.dt.microseconds
duration.dt.nanoseconds
```

However, these should not be confused with total duration units.

For example:

```python
duration = pd.Timedelta(
    days=2,
    hours=3,
)
```

then:

```python
duration.days
```

returns:

```text
2
```

while:

```python
duration.seconds
```

contains the seconds within the day rather than total elapsed seconds.

For total elapsed units, prefer:

```python
duration.dt.total_seconds()
```

or the corresponding total-unit methods.

---

## Total Duration Methods

Useful conversions include:

```python
duration.dt.total_seconds()
duration.dt.total_seconds() / 60
duration.dt.total_seconds() / 3600
```

Example:

```python
orders["processing_minutes"] = (
    orders["processing_time"]
    .dt.total_seconds()
    / 60
)
```

For clear semantics, name the resulting column explicitly:

```text
processing_seconds
processing_minutes
processing_hours
```

rather than using a generic name such as:

```text
duration
```

---

## Timedelta Arithmetic

Timedeltas can be added or subtracted.

Example:

```python
buffer = pd.Timedelta(
    minutes=15,
)

orders["deadline"] = (
    orders["completed_at"]
    + buffer
)
```

This is useful for:

```text
grace periods
timeouts
retry windows
processing deadlines
```

---

## Multiplying Timedeltas

A timedelta can be scaled:

```python
delay = pd.Timedelta(
    minutes=5
)

total_delay = delay * 3
```

This produces:

```text
15 minutes
```

This is useful when calculating repeated fixed-duration intervals.

Do not use this as a substitute for calendar arithmetic.

---

## Negative Timedeltas

A duration can be negative.

Example:

```python
negative = pd.Timedelta(
    minutes=-5
)
```

Negative values are useful for representing:

```text
early completion
clock skew
reverse differences
offsets
```

In event pipelines, negative durations can also signal invalid event ordering:

```python
invalid = orders.loc[
    orders["completed_at"]
    < orders["created_at"]
]
```

A negative processing time may indicate a data-quality problem rather than a meaningful business duration.

---

## SLA Validation

Suppose an API request must complete within two seconds:

```python
sla = pd.Timedelta(
    seconds=2,
)

requests["within_sla"] = (
    requests["completed_at"]
    - requests["started_at"]
) <= sla
```

This creates a clear operational rule.

You can then calculate the failure rate:

```python
sla_failure_rate = (
    ~requests["within_sla"]
).mean()
```

This can feed:

```text
monitoring
alerting
service-level reporting
```

---

## SLA Durations and Timezones

Elapsed duration should generally be calculated from timestamps that represent actual instants.

For example:

```python
requests["started_at"] = pd.to_datetime(
    requests["started_at"],
    utc=True,
)

requests["completed_at"] = pd.to_datetime(
    requests["completed_at"],
    utc=True,
)

requests["latency"] = (
    requests["completed_at"]
    - requests["started_at"]
)
```

This avoids calculating durations from unrelated local-time representations.

---

## Timedelta Versus DateOffset

These tools solve different problems.

```python
timestamp + pd.Timedelta(days=30)
```

means:

```text
30 fixed elapsed days
```

while:

```python
timestamp + pd.DateOffset(months=1)
```

means:

```text
one calendar month later
```

Choose based on the requirement.

Examples:

```text
API timeout → Timedelta
retry delay → Timedelta
SLA → Timedelta
cache TTL → Timedelta

monthly subscription renewal → DateOffset
next calendar month → DateOffset
month end → MonthEnd
```

---

## Timedelta Versus Timezone Conversion

Timezone conversion changes the representation of an instant:

```python
event_time.dt.tz_convert(
    "Asia/Kolkata"
)
```

A Timedelta measures separation between instants:

```python
completed_at - started_at
```

Do not use timezone conversion as a substitute for duration calculation.

---

## Datetime Plus Timedelta

A common pattern is:

```python
events["expires_at"] = (
    events["created_at"]
    + pd.Timedelta(hours=24)
)
```

This is appropriate when the requirement is:

```text
24 hours after creation
```

For:

```text
same local time tomorrow
```

calendar and timezone semantics may require additional consideration.

---

## Date Filtering With Timedelta

Timedeltas can define relative windows.

For example:

```python
now = pd.Timestamp.now(
    tz="UTC"
)

lookback = (
    now
    - pd.Timedelta(hours=1)
)

recent = events.loc[
    events["event_time"] >= lookback
]
```

This pattern is common for:

```text
operational monitoring
recent-event queries
incremental APIs
rolling ingestion
```

For reproducible pipelines, prefer a fixed run timestamp rather than repeatedly calling the system clock.

---

## Incremental Processing

A lookback window can be represented with a Timedelta:

```python
lookback = pd.Timedelta(
    minutes=15
)

window_start = (
    watermark - lookback
)

window_end = current_time

batch = events.loc[
    (events["event_time"] >= window_start)
    & (events["event_time"] < window_end)
]
```

This helps capture late-arriving events.

Because the lookback creates overlap with previously processed data, the pipeline must also support:

```text
idempotency
deduplication
upserts
```

---

## Retry Windows

Suppose a failed job should be retried after five minutes:

```python
retry_at = (
    failed_at
    + pd.Timedelta(minutes=5)
)
```

This is a fixed-duration rule.

If the requirement were:

```text
retry on the next business day
```

a business-calendar offset would be more appropriate.

---

## Event Lag

For event processing systems:

```python
events["processing_lag"] = (
    events["processed_at"]
    - events["event_time"]
)
```

Convert to seconds:

```python
events["processing_lag_seconds"] = (
    events["processing_lag"]
    .dt.total_seconds()
)
```

This supports monitoring of:

```text
Kafka consumers
batch pipelines
ETL jobs
stream-processing lag
```

A growing lag distribution can indicate:

```text
consumer saturation
downstream latency
network delays
database bottlenecks
```

---

## Queue and Task Duration

Celery or similar job systems can calculate execution duration:

```python
tasks["runtime"] = (
    tasks["finished_at"]
    - tasks["started_at"]
)

tasks["runtime_seconds"] = (
    tasks["runtime"]
    .dt.total_seconds()
)
```

These metrics can support:

```text
worker capacity planning
queue monitoring
SLA analysis
performance regression detection
```

The raw duration should remain available if more detailed analysis may be required.

---

## Timedelta and Rolling Windows

Timedeltas can define time-based window boundaries.

Example:

```python
window = pd.Timedelta(
    hours=24
)

cutoff = (
    reference_time
    - window
)

recent = events.loc[
    events["event_time"] >= cutoff
]
```

This is different from:

```text
calendar day
```

because 24 elapsed hours may cross local calendar boundaries differently depending on timezone and DST.

---

## Timedelta Comparison

Timelike values can be compared directly:

```python
orders["within_target"] = (
    orders["processing_time"]
    <= pd.Timedelta(minutes=30)
)
```

This produces a boolean Series.

Other examples:

```python
slow = orders.loc[
    orders["processing_time"]
    > pd.Timedelta(hours=1)
]
```

Use a `Timedelta` object instead of manually comparing multiple duration components.

---

## Missing Timedeltas

Missing durations are represented using `NaT`.

Example:

```python
orders["processing_time"] = (
    orders["completed_at"]
    - orders["created_at"]
)
```

If `completed_at` is missing:

```text
processing_time = NaT
```

This is useful for incomplete workflows:

```text
order still processing
task still running
request still active
```

Do not replace missing duration with zero unless zero has the intended business meaning.

---

## Invalid Negative Durations

A completed event occurring before its start is often invalid:

```python
orders["processing_time"] = (
    orders["completed_at"]
    - orders["created_at"]
)

invalid = orders.loc[
    orders["processing_time"] < pd.Timedelta(0)
]
```

Negative durations may reveal:

```text
clock problems
timezone mistakes
incorrect source ordering
bad joins
duplicate or malformed records
```

Treat them according to the domain rather than silently clipping them to zero.

---

## Duplicate Records

Duplicate events can produce duplicate durations.

Do not deduplicate based only on:

```text
duration
```

or:

```text
timestamp pair
```

Use the appropriate business identity:

```python
events = events.drop_duplicates(
    subset=["event_id"]
)
```

Duration is a derived attribute, not a unique identifier.

---

## Empty DataFrames

Timedelta calculations should work predictably on empty inputs.

```python
orders = pd.DataFrame(
    {
        "created_at": pd.Series(
            dtype="datetime64[ns, UTC]"
        ),
        "completed_at": pd.Series(
            dtype="datetime64[ns, UTC]"
        ),
    }
)

orders["processing_time"] = (
    orders["completed_at"]
    - orders["created_at"]
)
```

This should result in an empty timedelta column with a predictable dtype.

Test empty batches explicitly in ETL systems.

---

## Timedelta and SQL

PostgreSQL supports interval arithmetic:

```sql
SELECT
    completed_at - started_at AS processing_time
FROM job_runs;
```

or:

```sql
SELECT
    *
FROM job_runs
WHERE completed_at - started_at <= INTERVAL '2 seconds';
```

When the database can efficiently filter or aggregate using its own timestamp and interval operations, consider pushing that work into SQL.

Pandas is appropriate when the result is already being processed in memory or when further DataFrame transformations are required.

---

## Timedelta and APIs

API responses frequently expose duration values as:

```text
milliseconds
seconds
ISO-like duration strings
numeric integers
```

Normalize them explicitly.

Example:

```python
metrics["latency"] = pd.to_timedelta(
    metrics["latency_ms"],
    unit="ms",
)
```

Then derive a standard numeric metric:

```python
metrics["latency_seconds"] = (
    metrics["latency"]
    .dt.total_seconds()
)
```

A stable internal representation prevents each downstream consumer from interpreting raw duration units independently.

---

## Timedelta and Parquet

Persist typed durations when they are frequently reused.

```python
metrics["processing_time"] = (
    metrics["completed_at"]
    - metrics["started_at"]
)

metrics.to_parquet(
    "job_metrics.parquet",
    index=False,
)
```

Typed storage avoids reparsing textual durations in downstream pipelines.

Document the semantic unit even when the physical storage format already preserves the timedelta type.

---

## Performance Considerations

Timedelta arithmetic is vectorized:

```python
events["latency"] = (
    events["completed_at"]
    - events["started_at"]
)
```

Prefer this over:

```python
events["latency"] = events.apply(
    lambda row:
        row["completed_at"]
        - row["started_at"],
    axis=1,
)
```

The vectorized form is clearer and avoids Python-level row iteration.

For large workloads:

```text
parse once
calculate once
reuse duration columns
avoid unnecessary copies
filter before expensive downstream processing
```

---

## Avoid Manual Duration Arithmetic

Avoid:

```python
(
    completed_hour - started_hour
) * 3600 + (
    completed_minute - started_minute
) * 60
```

This ignores important details such as:

```text
day boundaries
timezone semantics
missing values
negative durations
precision
```

Use datetime subtraction:

```python
completed_at - started_at
```

and obtain the required unit afterward.

---

## Avoid Converting Timedeltas to Strings Too Early

Prefer:

```python
orders["processing_time"]
```

as a timedelta dtype for computation.

Do not convert immediately to:

```text
"00:15:30"
```

unless the output is intended for presentation.

String conversion makes subsequent numerical comparisons and aggregations more difficult.

---

## Aggregating Timedeltas

You can aggregate duration data:

```python
average_processing_time = (
    orders["processing_time"]
    .mean()
)
```

This produces a timedelta-like result.

Similarly:

```python
max_processing_time = (
    orders["processing_time"]
    .max()
)
```

For reporting:

```python
average_minutes = (
    orders["processing_time"]
    .dt.total_seconds()
    .mean()
    / 60
)
```

Choose the representation appropriate for the consumer.

---

## Median and Percentiles

Duration metrics often have skewed distributions.

Instead of relying only on the mean:

```python
median_latency = (
    metrics["latency"]
    .median()
)
```

For percentile analysis, convert to a numeric unit:

```python
latency_seconds = (
    metrics["latency"]
    .dt.total_seconds()
)

p95 = latency_seconds.quantile(
    0.95
)
```

This is useful for:

```text
API latency
job runtime
queue delay
ETL processing time
```

Averages can conceal long-tail performance problems.

---

## Duration-Based Monitoring

A production monitoring pipeline can derive:

```python
metrics["latency_seconds"] = (
    metrics["completed_at"]
    - metrics["started_at"]
).dt.total_seconds()
```

Then monitor:

```text
mean
median
p95
p99
max
SLA breach rate
```

A single average latency metric is often insufficient for operational health.

---

## Reliability Considerations

Duration metrics depend on the correctness of their source timestamps.

For distributed systems, validate:

```text
timezone consistency
clock behavior
event ordering
missing timestamps
duplicate events
source precision
```

A technically valid subtraction can still produce incorrect latency if the timestamps come from unsynchronized or semantically different clocks.

Keep distinctions such as:

```text
event_time
received_at
processed_at
completed_at
```

explicit.

---

## Monitoring Timedelta Quality

Useful metrics include:

| Metric | Purpose |
| --- | --- |
| Null durations | Detect incomplete records |
| Negative durations | Detect ordering or clock problems |
| SLA breach rate | Monitor service quality |
| P95/P99 duration | Monitor tail latency |
| Maximum duration | Identify severe anomalies |
| Duration distribution | Detect behavioral changes |
| Parse failure count | Detect malformed source durations |

Monitor both performance and data quality.

---

## Security Considerations

Durations themselves are usually not sensitive, but their source data may reveal operational information.

For example:

```text
payment processing time
internal service latency
job execution time
customer workflow timing
```

Avoid exposing internal infrastructure timing unnecessarily through public APIs.

When accepting user-provided durations:

```text
validate acceptable units
validate maximum values
reject unreasonable ranges
```

This helps prevent expensive or abusive requests.

---

## Testing Timedelta Calculations

Test exact duration semantics.

```python
def test_processing_duration() -> None:
    created_at = pd.Series(
        pd.to_datetime(
            [
                "2026-09-10T10:00:00Z",
            ],
            utc=True,
        )
    )

    completed_at = pd.Series(
        pd.to_datetime(
            [
                "2026-09-10T10:07:30Z",
            ],
            utc=True,
        )
    )

    duration = (
        completed_at
        - created_at
    )

    assert duration.iloc[0] == pd.Timedelta(
        minutes=7,
        seconds=30,
    )
```

This validates the business calculation directly.

---

## Testing SLA Rules

```python
def test_sla_threshold() -> None:
    durations = pd.Series(
        [
            pd.Timedelta(seconds=1.5),
            pd.Timedelta(seconds=2.5),
        ]
    )

    within_sla = (
        durations
        <= pd.Timedelta(seconds=2)
    )

    assert within_sla.tolist() == [
        True,
        False,
    ]
```

This verifies both the threshold and boundary semantics.

---

## Testing Invalid Ordering

```python
def test_negative_duration_is_detected() -> None:
    started_at = pd.Timestamp(
        "2026-09-10T10:00:00Z"
    )

    completed_at = pd.Timestamp(
        "2026-09-10T09:59:00Z"
    )

    duration = (
        completed_at
        - started_at
    )

    assert duration < pd.Timedelta(0)
```

Production validation can then reject or quarantine such records.

---

## Testing Missing Durations

```python
def test_missing_completion_produces_nat() -> None:
    started_at = pd.Series(
        pd.to_datetime(
            ["2026-09-10T10:00:00Z"],
            utc=True,
        )
    )

    completed_at = pd.Series(
        pd.to_datetime(
            [None],
            utc=True,
        )
    )

    duration = (
        completed_at
        - started_at
    )

    assert duration.isna().all()
```

This verifies that incomplete workflows remain distinguishable from zero-duration operations.

---

## Common Mistakes

### Confusing Timedelta With DateOffset

Use:

```text
Timedelta
→ elapsed duration

DateOffset
→ calendar-relative movement
```

Do not use 30 days as a substitute for one calendar month.

---

### Using `.dt.seconds` for Total Seconds

For multi-day durations:

```python
duration.dt.seconds
```

contains only the seconds component within the day.

Use:

```python
duration.dt.total_seconds()
```

for total elapsed seconds.

---

### Treating Missing Duration as Zero

These are different:

```text
0 seconds
```

and:

```text
unknown / incomplete
```

Use `NaT` when the duration cannot be determined.

---

### Ignoring Negative Durations

A negative duration may reveal:

```text
clock skew
timezone mistakes
bad event ordering
```

Do not silently clip negative values.

---

### Manually Calculating Hours and Minutes

Manual component arithmetic is fragile around:

```text
day boundaries
timezone changes
missing values
```

Subtract timestamps directly.

---

### Converting Durations to Strings Too Early

Keep timedelta dtype for computation.

Format as strings only at the presentation boundary.

---

### Using Fixed Duration for Calendar Requirements

`Timedelta(days=30)` is not the same as:

```python
pd.DateOffset(months=1)
```

The business rule determines the correct abstraction.

---

### Ignoring Source Units

A value of:

```text
250
```

could mean:

```text
250 seconds
250 milliseconds
250 microseconds
```

Make the unit explicit.

---

### Calculating Latency From Semantically Different Clocks

For example:

```text
database created_at
+
application completed_at
```

may not represent the same timing domain.

Use timestamps with compatible semantics.

---

## Interview Traps

### What Is a Timedelta?

A `Timedelta` represents elapsed duration rather than a point in time.

---

### How Do You Calculate Processing Time?

Subtract two datetime values:

```python
completed_at - started_at
```

The result is a timedelta.

---

### Why Use `total_seconds()`?

Because `.dt.seconds` represents only the seconds component within a day, while `total_seconds()` returns the complete duration in seconds.

---

### Timedelta Versus DateOffset?

```text
Timedelta
→ fixed elapsed duration

DateOffset
→ calendar-relative adjustment
```

---

### Why Can a Duration Be Negative?

Because the end timestamp can be earlier than the start timestamp.

In production this may indicate invalid data, clock issues, or incorrect event semantics.

---

### Why Use UTC for Duration Calculations?

UTC provides a consistent representation of instants across systems.

It reduces ambiguity when calculating elapsed time between timestamps originating in different timezones.

---

### How Should API Durations Be Stored?

Normalize the source unit explicitly:

```python
pd.to_timedelta(
    latency_ms,
    unit="ms",
)
```

Then use a typed timedelta representation internally.

---

### Why Can Average Latency Be Misleading?

Latency distributions are often skewed.

Median, p95, and p99 can reveal tail behavior hidden by the mean.

---

## Production Checklist

Before using Timedelta in production, verify:

```text
[ ] Timestamp inputs are correctly parsed
[ ] Timestamp timezone semantics are defined
[ ] Start and end timestamps represent compatible events
[ ] Timedelta is used for elapsed time rather than calendar movement
[ ] DateOffset is used for calendar-relative requirements
[ ] Source duration units are documented
[ ] pd.to_timedelta() uses an explicit unit when required
[ ] Invalid durations are handled intentionally
[ ] Missing durations remain distinguishable from zero
[ ] Negative durations are validated
[ ] total_seconds() is used when total elapsed seconds are required
[ ] Duration dtype is preserved during computation
[ ] String formatting is deferred until presentation
[ ] SLA boundaries are explicit
[ ] Retry/lookback windows use the correct duration semantics
[ ] Late-event processing is idempotent when Timedelta lookbacks overlap
[ ] Large workloads use vectorized arithmetic
[ ] Database-side interval filtering is considered
[ ] Empty DataFrames are tested
[ ] Missing timestamp cases are tested
[ ] Negative durations are tested
[ ] Boundary SLA values are tested
[ ] Duration distributions are monitored
[ ] P95/P99 latency is considered for operational metrics
[ ] Sensitive operational timing is not unnecessarily exposed
```

## Key Takeaways

- `Timedelta` represents elapsed time between timestamps and is the correct abstraction for latency, SLA duration, retry delays, lookback windows, and task runtimes.
- Use `pd.Timedelta()` for fixed durations and `pd.to_timedelta()` for converting duration columns; always make numeric duration units explicit.
- Calculate elapsed time by subtracting compatible datetime values, and use `total_seconds()` or other total-unit methods instead of relying on individual duration components.
- Keep missing durations as `NaT`, investigate negative durations, and distinguish incomplete or invalid timing data from legitimate zero-duration events.
- Choose `Timedelta` versus `DateOffset` based on semantics, preserve typed durations through the processing pipeline, and monitor duration distributions rather than relying only on average latency.