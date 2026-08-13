# AWS X-Ray with Lambda

AWS Lambda integrates directly with AWS X-Ray, allowing developers to trace serverless applications without managing infrastructure.

When tracing is enabled, Lambda automatically records request information, execution time, downstream service calls, and errors.

------------------------------------------------------------------------

# Why Use X-Ray with Lambda?

Lambda functions often interact with multiple AWS services.

Examples:

- Amazon DynamoDB
- Amazon S3
- Amazon SQS
- Amazon SNS
- Step Functions

X-Ray provides complete visibility into these interactions.

------------------------------------------------------------------------

# How Lambda Tracing Works

```text
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB

↓

SNS

↓

Response
```

Each request becomes a distributed trace.

------------------------------------------------------------------------

# Active Tracing

Active Tracing enables Lambda to send trace data automatically to AWS X-Ray.

When enabled:

- Lambda creates segments.
- Downstream AWS SDK calls are traced.
- Service Maps are generated automatically.

------------------------------------------------------------------------

# Passive Tracing

If another service (such as API Gateway) already started a trace, Lambda joins the existing trace.

This creates a continuous end-to-end request path.

------------------------------------------------------------------------

# Enabling Active Tracing

Steps:

1. Open the Lambda Console.
2. Select the function.
3. Open **Configuration**.
4. Choose **Monitoring and Operations Tools**.
5. Enable **Active Tracing**.
6. Save changes.

------------------------------------------------------------------------

# What Gets Traced?

X-Ray records:

- Invocation time
- Cold starts
- Initialization time
- Function duration
- Errors
- Exceptions
- AWS SDK calls

------------------------------------------------------------------------

# Lambda Service Map

Example:

```text
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB

↓

S3
```

Latency and errors appear automatically.

------------------------------------------------------------------------

# Cold Start Visibility

One advantage of X-Ray is identifying Lambda cold starts.

Example:

```text
Initialization

320 ms

↓

Execution

45 ms
```

Developers can distinguish startup time from actual execution time.

------------------------------------------------------------------------

# IAM Permissions

Lambda requires permission to send trace data.

Example managed policy:

```text
AWSXRayDaemonWriteAccess
```

Without the required permissions, traces cannot be uploaded.

------------------------------------------------------------------------

# Real-World Example

A serverless image processing application:

```text
User Upload

↓

API Gateway

↓

Lambda

↓

S3

↓

DynamoDB

↓

SNS
```

X-Ray shows the complete request path and highlights slow operations, such as large file uploads or slow database writes.

------------------------------------------------------------------------

# Best Practices

- Enable Active Tracing for production functions.
- Trace downstream AWS SDK calls.
- Add annotations for business identifiers.
- Monitor cold starts.
- Review Service Maps regularly.
- Combine X-Ray with CloudWatch Logs.

------------------------------------------------------------------------

# Key Takeaways

- AWS Lambda integrates natively with AWS X-Ray.
- Active Tracing automatically generates traces.
- X-Ray records execution time, cold starts, errors, and downstream service calls.
- Service Maps provide end-to-end visibility for serverless applications.
- Combining X-Ray with CloudWatch creates a powerful observability solution.