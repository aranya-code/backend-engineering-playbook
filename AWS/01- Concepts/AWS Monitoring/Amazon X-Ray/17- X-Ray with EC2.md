# AWS X-Ray with EC2

Applications running on Amazon EC2 can integrate with AWS X-Ray to provide detailed distributed tracing.

Unlike AWS Lambda, EC2 instances require developers to install the X-Ray Daemon and instrument their applications using the X-Ray SDK.

------------------------------------------------------------------------

# Why Use X-Ray with EC2?

EC2 applications often consist of:

- Web servers
- REST APIs
- Background workers
- Microservices

X-Ray helps monitor:

- Request flow
- Database queries
- External API calls
- Application latency
- Exceptions

------------------------------------------------------------------------

# Architecture

```text
Client

↓

Application

↓

X-Ray SDK

↓

X-Ray Daemon

↓

AWS X-Ray
```

------------------------------------------------------------------------

# Components Required

To enable tracing:

- X-Ray SDK
- X-Ray Daemon
- IAM Role
- AWS X-Ray Service

------------------------------------------------------------------------

# Installing the X-Ray Daemon

The daemon runs as a background service on the EC2 instance.

Responsibilities:

- Receive segments
- Buffer requests
- Upload traces
- Retry failed uploads

------------------------------------------------------------------------

# Instrumenting Applications

Applications must use the AWS X-Ray SDK.

The SDK records:

- HTTP requests
- Database calls
- AWS SDK calls
- Exceptions
- Custom subsegments

------------------------------------------------------------------------

# IAM Permissions

Attach an IAM Role with permissions such as:

```text
AWSXRayDaemonWriteAccess
```

This allows the daemon to upload trace data.

------------------------------------------------------------------------

# Trace Flow

```text
Browser

↓

EC2 Application

↓

SDK

↓

Daemon

↓

AWS X-Ray
```

------------------------------------------------------------------------

# Monitoring

Combine X-Ray with:

- Amazon CloudWatch
- CloudWatch Logs
- CloudTrail

This provides complete observability.

------------------------------------------------------------------------

# Real-World Example

A Django application runs on Amazon EC2.

```text
User

↓

Nginx

↓

Django

↓

PostgreSQL

↓

External Payment API
```

X-Ray shows that the external Payment API contributes 800 ms of latency, allowing developers to optimize or replace the service.

------------------------------------------------------------------------

# Best Practices

- Install the latest X-Ray Daemon.
- Instrument all critical endpoints.
- Trace database operations.
- Record exceptions.
- Monitor daemon health.

------------------------------------------------------------------------

# Key Takeaways

- EC2 applications require both the SDK and X-Ray Daemon.
- IAM permissions are required to upload traces.
- X-Ray provides detailed visibility into application performance on EC2.