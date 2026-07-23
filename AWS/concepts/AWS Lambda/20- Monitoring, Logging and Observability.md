# 20- Lambda Monitoring, Logging and Observability

# Introduction

Building a Lambda function that works correctly is only half the job. In production, engineers must answer questions such as:

- Why did this request fail?
- Which function is causing high latency?
- How much memory is being consumed?
- Which downstream service is slow?
- Is the function experiencing cold starts?
- When should engineers be alerted?

Without proper monitoring and observability, debugging distributed serverless systems becomes extremely difficult.

AWS provides several services to monitor Lambda functions:

- Amazon CloudWatch Logs
- Amazon CloudWatch Metrics
- CloudWatch Alarms
- AWS X-Ray
- Lambda Insights
- CloudTrail
- Third-party observability platforms

---

# Observability Pillars

Modern observability consists of three primary pillars.

```
              Observability

                   │

      ┌────────────┼────────────┐

      │            │            │

    Logs         Metrics      Traces
```

Each provides different insights.

---

# Logs

Logs answer:

> **What happened?**

Example:

```
User Login Started

↓

Database Connected

↓

JWT Generated

↓

Response Returned
```

Logs contain detailed execution information.

---

# Metrics

Metrics answer:

> **How healthy is the application?**

Examples:

- Invocation count
- Error rate
- Duration
- Memory utilization
- Concurrent executions

Metrics are numerical values collected over time.

---

# Traces

Traces answer:

> **Where is time being spent?**

Example:

```
API Gateway

↓

Lambda

↓

RDS

↓

SNS
```

Tracing identifies latency across services.

---

# CloudWatch Logs

Every Lambda automatically sends logs to CloudWatch Logs.

```
Lambda

↓

stdout

↓

CloudWatch Logs
```

Developers can view logs directly from the AWS Console.

---

# Log Groups

Each Lambda function has its own log group.

```
CloudWatch

↓

Log Groups

↓

/aws/lambda/payment-service
```

---

# Log Streams

Every execution environment creates its own log stream.

```
Log Group

│

├── Stream A

├── Stream B

└── Stream C
```

Multiple concurrent environments generate multiple streams.

---

# Automatic Log Entries

AWS automatically records:

```
START RequestId

END RequestId

REPORT RequestId
```

Example:

```
START RequestId...

END RequestId...

REPORT Duration: 87 ms

Memory Used: 122 MB
```

These entries are useful for performance analysis.

---

# Application Logging

Python example:

```python
import logging

logger = logging.getLogger()

logger.setLevel(logging.INFO)

def handler(event, context):

    logger.info("Order processing started")

    logger.info(event)
```

Avoid using excessive `print()` statements in production.

---

# Structured Logging

Instead of:

```
Payment Complete
```

Use structured JSON.

```json
{
    "order_id": 1051,
    "user_id": 889,
    "status": "SUCCESS"
}
```

Structured logs are easier to search and analyze.

---

# Log Retention

By default, CloudWatch retains logs indefinitely.

Production recommendation:

```
30 Days

↓

Archive

↓

Delete
```

Retention policies reduce storage costs.

---

# CloudWatch Metrics

Lambda automatically publishes metrics.

Important metrics include:

- Invocations
- Errors
- Duration
- Throttles
- ConcurrentExecutions
- IteratorAge
- DeadLetterErrors

---

# Invocations

Measures:

```
Number of Requests
```

Useful for:

- Traffic monitoring
- Capacity planning

---

# Errors

Measures failed executions.

```
Errors

↓

CloudWatch

↓

Alarm

↓

SNS

↓

Engineer
```

---

# Duration

Measures execution time.

```
Average

Minimum

Maximum

P95

P99
```

Useful for performance tuning.

---

# Throttles

Occurs when concurrency limits are exceeded.

```
Request

↓

Concurrency Full

↓

Throttle
```

Should be monitored continuously.

---

# Concurrent Executions

Shows current Lambda concurrency.

```
Concurrent Executions

↓

50

↓

200

↓

500
```

Helps identify scaling behavior.

---

# Custom Metrics

Applications can publish custom metrics.

Example:

```
Orders Processed

Payments Completed

Emails Sent

Cache Hit Ratio
```

These provide business-level insights.

---

# CloudWatch Alarms

CloudWatch Alarms notify engineers when thresholds are exceeded.

Example:

```
Errors > 5

↓

Alarm

↓

SNS

↓

Slack

↓

Engineer
```

---

# Common Alarms

Typical production alarms include:

- Error rate
- High duration
- High throttles
- High concurrency
- Dead Letter Queue size
- Iterator age

---

# AWS X-Ray

X-Ray provides distributed tracing.

```
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB

↓

SNS
```

Entire requests can be visualized.

---

# X-Ray Segments

Each service contributes a segment.

```
Request

↓

API Gateway

↓

Lambda

↓

RDS

↓

External API
```

Engineers can identify slow services.

---

# Lambda Insights

Lambda Insights provides deeper runtime information.

Examples:

- CPU utilization
- Memory usage
- Network activity
- Runtime statistics

This goes beyond basic CloudWatch metrics.

---

# CloudTrail

CloudTrail records AWS API activity.

Example:

```
Who Changed Lambda?

↓

CloudTrail

↓

IAM User

↓

Timestamp
```

Useful for auditing.

---

# Correlation IDs

Distributed systems should generate correlation IDs.

Example:

```
Client

↓

Correlation ID

↓

API Gateway

↓

Lambda

↓

SNS

↓

SQS

↓

Another Lambda
```

Every log contains the same identifier.

---

# Log Levels

Typical logging levels:

```
DEBUG

INFO

WARNING

ERROR

CRITICAL
```

Production usually uses:

```
INFO

ERROR
```

Avoid DEBUG unless troubleshooting.

---

# Monitoring Dashboard

Typical dashboard:

```
Invocations

Errors

Duration

Memory

Concurrency

DLQ Messages

Cold Starts
```

Everything visible on one screen.

---

# Third-Party Monitoring

Popular tools include:

- Datadog
- New Relic
- Splunk
- Dynatrace
- Elastic Observability
- Grafana Cloud

Most integrate using Lambda Extensions.

---

# Cost Considerations

Logging has costs.

Large log volumes increase:

- CloudWatch storage
- Query costs
- Data transfer

Avoid logging unnecessary payloads.

---

# Common Mistakes

## Logging Secrets

Never log:

- Passwords
- Tokens
- JWTs
- API Keys

---

## Excessive Logging

Bad:

```
Entire HTTP Request

Entire Database Response

Entire JWT

Entire Event
```

Log only what is necessary.

---

## Missing Correlation IDs

Without correlation IDs:

```
Request

↓

Many Services

↓

Impossible to Trace
```

Always include request identifiers.

---

# Best Practices

✅ Use structured JSON logging.

✅ Configure log retention.

✅ Monitor duration and error metrics.

✅ Create CloudWatch alarms.

✅ Enable X-Ray for production APIs.

✅ Publish business metrics.

✅ Use correlation IDs.

✅ Never log secrets.

---

# Real-World Architecture

```
Users

↓

CloudFront

↓

API Gateway

↓

Lambda

↓

CloudWatch Logs

↓

CloudWatch Metrics

↓

CloudWatch Alarms

↓

SNS

↓

PagerDuty

↓

Engineering Team

------------------------

AWS X-Ray

↓

Distributed Trace

↓

Root Cause Analysis
```

---

# Senior Backend Engineering Perspective

Observability is a fundamental requirement for operating distributed systems at scale. Logs, metrics, and traces complement one another, providing visibility into application behavior, performance, and failures.

A mature Lambda platform typically includes:

- Structured JSON logging
- CloudWatch metrics and alarms
- AWS X-Ray tracing
- Lambda Insights for runtime diagnostics
- Correlation IDs across microservices
- Centralized dashboards
- Automated incident notifications

Rather than reacting to failures after customers report them, engineers use observability to detect, diagnose, and resolve issues proactively.

---

# Interview Questions

### Beginner

- Where are Lambda logs stored?
- What metrics does Lambda publish automatically?
- What is CloudWatch?

### Intermediate

- What is the difference between logs, metrics, and traces?
- Why should structured logging be used?
- How do CloudWatch Alarms work?

### Senior

- How would you monitor thousands of Lambda functions?
- How would you trace a request across API Gateway, Lambda, SNS, and DynamoDB?
- How would you design an enterprise observability platform for serverless applications?
- What KPIs would you expose on an executive monitoring dashboard?

---

# Key Takeaways

- Observability is built on logs, metrics, and traces, each providing different operational insights.
- CloudWatch automatically collects Lambda logs and key metrics such as invocations, duration, errors, and throttles.
- AWS X-Ray and Lambda Insights provide deep visibility into request flow and runtime performance.
- Structured logging, correlation IDs, and CloudWatch alarms are essential for diagnosing issues in distributed systems.
- A production-grade serverless platform combines native AWS monitoring with centralized dashboards and proactive alerting to ensure reliability and rapid incident response.