# X-Ray Read APIs

AWS X-Ray provides several Read APIs that allow developers and monitoring tools to retrieve trace data, service maps, and analytics information.

These APIs power the AWS X-Ray Console and can also be used by custom monitoring applications.

------------------------------------------------------------------------

# Why Use Read APIs?

Read APIs help retrieve:

- Traces
- Service Maps
- Trace Summaries
- Groups
- Service Statistics
- Analytics

------------------------------------------------------------------------

# Read API Workflow

```text
AWS X-Ray

↓

Read API

↓

Application

↓

Display Results
```

------------------------------------------------------------------------

# BatchGetTraces

**Purpose**

Retrieves complete trace documents.

Useful when detailed trace analysis is required.

Returns:

- Trace timeline
- Segments
- Subsegments
- Metadata
- Exceptions

------------------------------------------------------------------------

# GetTraceSummaries

**Purpose**

Returns summaries of traces within a specified time range.

Information includes:

- Duration
- Response status
- Errors
- Faults

Useful for searching traces.

------------------------------------------------------------------------

# GetServiceGraph

**Purpose**

Returns the Service Map.

Example:

```text
API Gateway

↓

Lambda

↓

DynamoDB

↓

SNS
```

Applications use this API to visualize dependencies.

------------------------------------------------------------------------

# GetTraceGraph

**Purpose**

Retrieves relationships between segments within a trace.

Useful for advanced trace visualization.

------------------------------------------------------------------------

# GetGroups

**Purpose**

Lists all X-Ray Groups.

Groups organize traces based on filter expressions.

Example:

```text
Production

Development

Payments

Authentication
```

------------------------------------------------------------------------

# GetGroup

**Purpose**

Returns information about a specific X-Ray Group.

------------------------------------------------------------------------

# GetTimeSeriesServiceStatistics

**Purpose**

Retrieves historical service performance.

Examples:

- Average latency
- Error rate
- Fault rate
- Request count

Useful for trend analysis.

------------------------------------------------------------------------

# Read API Flow

```text
AWS X-Ray

↓

Trace Storage

↓

Read APIs

↓

X-Ray Console

↓

Developer
```

------------------------------------------------------------------------

# Common Use Cases

- Performance dashboards
- Service dependency visualization
- Root cause analysis
- Monitoring tools
- Historical analysis

------------------------------------------------------------------------

# Best Practices

- Use filters to reduce API responses.
- Limit large time ranges.
- Monitor API usage.
- Protect access using IAM.

------------------------------------------------------------------------

# Key Takeaways

- Read APIs retrieve traces and analytics.
- BatchGetTraces returns detailed trace data.
- GetServiceGraph builds the Service Map.
- GetTraceSummaries supports efficient searching.
- Read APIs power the AWS X-Ray Console.