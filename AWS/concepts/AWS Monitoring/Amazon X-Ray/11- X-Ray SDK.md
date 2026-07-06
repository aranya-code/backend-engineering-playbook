# AWS X-Ray SDK

The AWS X-Ray SDK enables applications to generate trace data. It instruments your application so that requests, service calls, database queries, and external API calls can be recorded and sent to AWS X-Ray.

Without the SDK, X-Ray cannot collect detailed application-level tracing information.

------------------------------------------------------------------------

# What is the X-Ray SDK?

The SDK is a programming library that integrates tracing into your application.

It automatically records:

- Incoming requests
- Outgoing requests
- AWS SDK calls
- Database operations
- Exceptions
- Latency

------------------------------------------------------------------------

# Supported Programming Languages

AWS provides SDKs for:

- Java
- Python
- Node.js
- .NET
- Go

These SDKs integrate with popular web frameworks and AWS services.

------------------------------------------------------------------------

# SDK Responsibilities

The SDK performs several important tasks:

- Creates traces
- Generates segments
- Generates subsegments
- Records exceptions
- Adds annotations
- Adds metadata
- Sends trace data to the X-Ray Daemon

------------------------------------------------------------------------

# Automatic Instrumentation

Many frameworks support automatic instrumentation.

Examples:

- Flask
- Django
- Spring Boot
- Express.js
- ASP.NET

The SDK automatically traces supported operations without additional code.

------------------------------------------------------------------------

# Manual Instrumentation

For custom business logic, developers can manually create subsegments.

Example use cases:

- Complex calculations
- External REST APIs
- Custom authentication
- Internal workflows

------------------------------------------------------------------------

# SDK Workflow

```text
Client Request

↓

Application

↓

X-Ray SDK

↓

Segment

↓

Subsegment

↓

X-Ray Daemon
```

------------------------------------------------------------------------

# Recording Exceptions

The SDK automatically records:

- Exceptions
- Stack traces
- Error messages

These appear directly within trace details.

------------------------------------------------------------------------

# AWS SDK Integration

The X-Ray SDK automatically traces calls made using AWS SDKs.

Examples:

- Amazon S3
- DynamoDB
- Amazon SQS
- SNS
- Lambda

This eliminates the need for manual instrumentation of AWS service calls.

------------------------------------------------------------------------

# Real-World Example

An order processing service performs:

```text
Receive Request

↓

Validate Order

↓

Save to DynamoDB

↓

Send SNS Notification

↓

Return Response
```

The SDK records each operation as segments and subsegments.

------------------------------------------------------------------------

# Best Practices

- Instrument all critical services.
- Use automatic instrumentation whenever possible.
- Manually instrument custom logic.
- Record exceptions.
- Add useful annotations.

------------------------------------------------------------------------

# Key Takeaways

- The X-Ray SDK generates trace data.
- It supports multiple programming languages.
- The SDK automatically records AWS SDK calls.
- Manual instrumentation provides deeper visibility into business logic.