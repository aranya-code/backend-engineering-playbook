# Subsegments

A **subsegment** represents a smaller unit of work performed within a segment.

While a segment represents an entire service, subsegments capture individual operations such as database queries, HTTP requests, external API calls, or business logic.

Subsegments provide detailed visibility into how time is spent inside a service.

------------------------------------------------------------------------

# What is a Subsegment?

A subsegment is a child component of a segment.

Example:

```text
Lambda Segment

├── Validate Request

├── Query DynamoDB

├── Call Payment API

└── Generate Response
```

------------------------------------------------------------------------

# Why Use Subsegments?

Subsegments help:

- Identify slow database queries
- Measure external API latency
- Track internal business logic
- Debug application code
- Locate bottlenecks

------------------------------------------------------------------------

# Parent-Child Relationship

```text
Trace

↓

Segment

↓

Subsegment

↓

Nested Subsegment
```

A segment may contain multiple subsegments.

------------------------------------------------------------------------

# Common Types of Subsegments

Examples include:

- SQL queries
- DynamoDB operations
- HTTP requests
- AWS SDK calls
- External REST APIs
- File operations
- Business logic

------------------------------------------------------------------------

# Timing Information

Each subsegment records:

- Start time
- End time
- Duration

Example:

```text
Validate Request

5 ms

↓

Query Database

45 ms

↓

Call External API

310 ms
```

This allows developers to pinpoint slow operations.

------------------------------------------------------------------------

# Errors in Subsegments

Subsegments can record:

- Exceptions
- HTTP errors
- Database failures
- Timeout errors
- Validation failures

These errors are displayed in the trace timeline.

------------------------------------------------------------------------

# Nested Subsegments

Subsegments may contain additional subsegments.

Example:

```text
Lambda

↓

Payment API

↓

Authentication

↓

Database Lookup
```

This creates a hierarchical view of application execution.

------------------------------------------------------------------------

# Real-World Example

An online shopping application processes an order.

```text
Order Service Segment

├── Validate Customer

├── Check Inventory

├── Process Payment

├── Send Email

└── Save Order
```

If **Process Payment** takes significantly longer than other operations, X-Ray highlights it as the primary bottleneck.

------------------------------------------------------------------------

# Best Practices

- Instrument important operations.
- Avoid creating excessive subsegments.
- Trace external API calls.
- Record exceptions.
- Use annotations for searchable fields.

------------------------------------------------------------------------

# Key Takeaways

- Subsegments divide a segment into smaller operations.
- They provide detailed performance insights.
- Subsegments help identify slow database queries, API calls, and business logic.
- Nested subsegments create a complete view of request execution within a service.