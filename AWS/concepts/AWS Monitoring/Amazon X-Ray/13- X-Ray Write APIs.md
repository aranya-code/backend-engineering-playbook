# X-Ray Write APIs

AWS X-Ray provides several **Write APIs** that allow the X-Ray SDK and X-Ray Daemon to upload trace data and retrieve sampling information.

Applications typically do not call these APIs directly. Instead, the X-Ray SDK and Daemon communicate with these APIs automatically.

------------------------------------------------------------------------

# Why are Write APIs Needed?

When an application generates trace data, AWS X-Ray must receive and process that information.

The Write APIs are responsible for:

- Uploading trace segments
- Sending daemon telemetry
- Retrieving sampling rules
- Retrieving sampling targets
- Reporting sampling statistics

------------------------------------------------------------------------

# Write API Workflow

```text
Application

↓

X-Ray SDK

↓

X-Ray Daemon

↓

AWS X-Ray Write APIs

↓

Store Trace Data
```

------------------------------------------------------------------------

# PutTraceSegments

**Purpose**

Uploads trace segments and subsegments to AWS X-Ray.

This is the most important Write API because every trace eventually reaches AWS X-Ray through this operation.

Example workflow:

```text
Application

↓

Segment Created

↓

PutTraceSegments

↓

AWS X-Ray
```

------------------------------------------------------------------------

# PutTelemetryRecords

**Purpose**

Uploads daemon health information.

Telemetry includes:

- Segments received
- Segments uploaded
- Upload failures
- Buffer utilization

This information helps AWS monitor daemon performance.

------------------------------------------------------------------------

# GetSamplingRules

**Purpose**

Downloads sampling rules configured in AWS X-Ray.

Example:

```text
Production API

↓

Sampling Rule

↓

5%
```

Applications use these rules to determine which requests should be traced.

------------------------------------------------------------------------

# GetSamplingTargets

**Purpose**

Retrieves the latest sampling targets from AWS X-Ray.

These targets dynamically adjust the sampling rate based on traffic.

Benefits include:

- Improved scalability
- Reduced tracing overhead
- Better trace distribution

------------------------------------------------------------------------

# GetSamplingStatisticSummaries

**Purpose**

Uploads sampling statistics collected by the SDK.

Statistics include:

- Requests traced
- Requests ignored
- Reservoir usage

AWS uses these statistics to optimize future sampling decisions.

------------------------------------------------------------------------

# Complete Write API Flow

```text
Client Request

↓

X-Ray SDK

↓

Segment

↓

Daemon

↓

PutTraceSegments

↓

AWS X-Ray
```

Meanwhile:

```text
Daemon

↓

PutTelemetryRecords
```

And:

```text
SDK

↓

GetSamplingRules

↓

GetSamplingTargets

↓

GetSamplingStatisticSummaries
```

------------------------------------------------------------------------

# Best Practices

- Allow the SDK and Daemon to manage Write APIs automatically.
- Keep the daemon updated.
- Monitor upload failures.
- Configure sampling rules carefully.
- Verify IAM permissions.

------------------------------------------------------------------------

# Key Takeaways

- Write APIs upload trace data to AWS X-Ray.
- PutTraceSegments stores traces.
- PutTelemetryRecords uploads daemon health.
- Sampling APIs optimize trace collection.
- Developers rarely call these APIs directly.