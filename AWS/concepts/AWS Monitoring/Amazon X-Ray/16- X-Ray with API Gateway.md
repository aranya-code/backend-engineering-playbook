# AWS X-Ray with API Gateway

Amazon API Gateway integrates natively with AWS X-Ray, allowing developers to trace incoming API requests as they flow through backend services.

By enabling X-Ray tracing, every API request can be monitored from the client to downstream services such as AWS Lambda, Amazon ECS, Amazon EC2, and databases.

------------------------------------------------------------------------

# Why Use X-Ray with API Gateway?

API Gateway is often the entry point for distributed applications.

X-Ray helps you:

- Measure API latency
- Detect backend failures
- Monitor request flow
- Analyze response times
- Identify bottlenecks
- Troubleshoot APIs

------------------------------------------------------------------------

# Architecture

```text
Client

↓

API Gateway

↓

AWS Lambda

↓

DynamoDB

↓

Response
```

Each request generates a distributed trace.

------------------------------------------------------------------------

# How API Gateway Tracing Works

When tracing is enabled:

1. API Gateway receives the request.
2. A Trace ID is generated.
3. The trace is forwarded to backend services.
4. Each service contributes segments.
5. AWS X-Ray builds the complete trace.

------------------------------------------------------------------------

# Enabling X-Ray

To enable tracing:

1. Open API Gateway Console.
2. Select your API.
3. Choose **Stages**.
4. Select the deployment stage.
5. Enable **X-Ray Tracing**.
6. Deploy the API.

------------------------------------------------------------------------

# Information Captured

API Gateway records:

- Request path
- HTTP method
- Response status
- Request latency
- Integration latency
- Errors
- Throttling

------------------------------------------------------------------------

# Service Map

Example:

```text
Client

↓

API Gateway

↓

Lambda

↓

Amazon RDS
```

The Service Map shows the relationships between services along with latency and error rates.

------------------------------------------------------------------------

# Common Use Cases

- REST APIs
- HTTP APIs
- Serverless applications
- Microservices
- Public APIs

------------------------------------------------------------------------

# Real-World Example

A food delivery application exposes an API.

```text
Mobile App

↓

API Gateway

↓

Order Service

↓

Payment Service

↓

Inventory Service

↓

Amazon RDS
```

Users report slow checkout times.

X-Ray reveals that the Payment Service consistently takes 1.5 seconds, making it the primary performance bottleneck.

------------------------------------------------------------------------

# Best Practices

- Enable tracing in production stages.
- Combine with Lambda Active Tracing.
- Monitor API latency regularly.
- Investigate throttled requests.
- Use CloudWatch Alarms for API failures.

------------------------------------------------------------------------

# Key Takeaways

- API Gateway integrates directly with AWS X-Ray.
- Each API request generates a trace.
- X-Ray measures request and integration latency.
- Service Maps simplify API troubleshooting.