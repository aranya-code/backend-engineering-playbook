# Segments

A **segment** represents the work performed by a single service while processing a request.

Each service participating in a trace creates its own segment. AWS X-Ray combines all segments to build the complete request trace.

------------------------------------------------------------------------

# What is a Segment?

A segment contains detailed information about one service's execution.

Example:

```text
Trace

↓

API Gateway Segment

↓

Lambda Segment

↓

DynamoDB Segment
```

Each service contributes exactly one segment for its portion of the request.

------------------------------------------------------------------------

# Information Stored in a Segment

A segment can include:

- Segment ID
- Trace ID
- Service name
- Start time
- End time
- Duration
- HTTP request
- HTTP response
- Errors
- Faults
- Throttles
- User information
- AWS resource details

------------------------------------------------------------------------

# Segment Structure

```text
Segment

├── Trace ID

├── Segment ID

├── Start Time

├── End Time

├── HTTP Information

├── Annotations

├── Metadata

└── Subsegments
```

------------------------------------------------------------------------

# Segment Timing

Every segment records:

```text
Start Time

↓

Processing

↓

End Time
```

Duration is calculated automatically.

------------------------------------------------------------------------

# Errors and Faults

Segments record application issues.

Examples:

- HTTP 404
- HTTP 500
- Timeout
- Exception
- Database error

These errors appear in the X-Ray console.

------------------------------------------------------------------------

# AWS Resource Information

Segments can automatically include information about AWS resources such as:

- Lambda Function
- EC2 Instance
- ECS Task
- API Gateway
- DynamoDB Table
- S3 Bucket

------------------------------------------------------------------------

# Segment Document

Internally, X-Ray stores segments as JSON documents.

A segment document contains:

- Request details
- Timing information
- Errors
- Metadata
- Annotations

------------------------------------------------------------------------

# Real-World Example

```text
Client

↓

API Gateway Segment

↓

Lambda Segment

↓

Payment Service Segment

↓

Amazon RDS Segment
```

Each component creates its own segment.

The collection of all segments forms a complete trace.

------------------------------------------------------------------------

# Best Practices

- Create meaningful service names.
- Keep segment data concise.
- Record exceptions.
- Add annotations where appropriate.
- Monitor segment latency.

------------------------------------------------------------------------

# Key Takeaways

- A segment represents one service's work.
- Multiple segments form a trace.
- Segments store timing, errors, metadata, and service information.
- Segments help identify performance bottlenecks.