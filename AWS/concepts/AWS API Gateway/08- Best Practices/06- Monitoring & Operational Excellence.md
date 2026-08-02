# Monitoring & Operational Excellence

## Overview

Building an API is only half the job. Running it reliably in production requires continuous monitoring, alerting, troubleshooting, and operational discipline.

Operational Excellence is one of the **AWS Well-Architected Framework pillars** and focuses on:

- Monitoring systems
- Detecting failures quickly
- Responding efficiently
- Learning from incidents
- Continuously improving operations

A production API should answer questions like:

- Is the API healthy?
- Is latency increasing?
- Are users experiencing errors?
- Is a deployment causing failures?
- Which backend is slow?
- Are infrastructure costs increasing?

Monitoring provides these answers before customers report problems.

---

# Operational Excellence Lifecycle

```text
Deploy

↓

Monitor

↓

Detect

↓

Investigate

↓

Resolve

↓

Improve
```

Monitoring is a continuous process.

---

# Observability vs Monitoring

Monitoring answers:

```text
What happened?
```

Observability answers:

```text
Why did it happen?
```

Both are essential for production systems.

---

# Key Operational Metrics

Every API should monitor:

- Availability
- Latency
- Error Rate
- Throughput
- Resource Utilization
- Request Volume
- Cost

These metrics provide a complete view of API health.

---

# Golden Signals

Google's Site Reliability Engineering (SRE) defines four Golden Signals.

```text
Latency

↓

Traffic

↓

Errors

↓

Saturation
```

Every production API should monitor these signals.

---

# Latency

Latency measures how long requests take.

Example:

```text
Client

↓

API Gateway

↓

Backend

↓

Response
```

Monitor:

- Average latency
- P95 latency
- P99 latency

High tail latency often impacts user experience more than average latency.

---

# Traffic

Monitor request volume.

Example:

```text
100 Requests/minute

↓

5,000 Requests/minute
```

Traffic spikes may indicate:

- Successful marketing campaigns
- Abuse
- DDoS attacks
- Scaling issues

---

# Error Rate

Monitor:

```text
2XX

↓

Success

--------------------

4XX

↓

Client Errors

--------------------

5XX

↓

Server Errors
```

A sudden increase in 5XX errors requires immediate investigation.

---

# Saturation

Monitor resource utilization.

Examples:

- CPU
- Memory
- Database Connections
- Lambda Concurrency

Resources operating near capacity become bottlenecks.

---

# CloudWatch Metrics

API Gateway automatically publishes metrics including:

- Request Count
- Latency
- Integration Latency
- Cache Hit Count
- Cache Miss Count
- 4XX Errors
- 5XX Errors

These metrics form the foundation of API monitoring.

---

# CloudWatch Logs

Logs provide detailed request information.

Typical log data includes:

- Request ID
- Endpoint
- Status Code
- Integration Response
- Error Details

Logs complement metrics during troubleshooting.

---

# Structured Logging

Instead of:

```text
Error occurred
```

Use structured logs.

Example:

```json
{
  "requestId":"12345",
  "userId":"789",
  "endpoint":"/orders",
  "status":500,
  "duration":180
}
```

Structured logs simplify searching and analysis.

---

# Correlation IDs

Every request should carry a Correlation ID.

```text
Client

↓

API Gateway

↓

Microservice A

↓

Microservice B
```

The same ID appears in every log entry, enabling end-to-end tracing.

---

# Distributed Tracing

AWS X-Ray visualizes request flow.

```text
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB
```

Identify slow services and bottlenecks quickly.

---

# Dashboards

Create dashboards displaying:

- Request Count
- Latency
- Error Rate
- CPU
- Memory
- Database Health

Operations teams should be able to assess system health at a glance.

---

# CloudWatch Alarms

Configure alarms for:

- High Latency
- High 5XX Errors
- High Throttling
- High CPU
- Low Healthy Hosts

Alerts should notify engineers before users experience significant issues.

---

# Notification Architecture

```text
CloudWatch Alarm

↓

Amazon SNS

↓

Email

Slack

PagerDuty

Microsoft Teams
```

Critical alerts should reach the on-call engineer immediately.

---

# Monitor Backend Services

Monitor not only API Gateway but also:

- Lambda Duration
- ECS CPU
- EC2 Memory
- Database Response Time
- Redis Hit Ratio

Backend failures often cause API failures.

---

# Monitor Database Health

Track:

- Slow Queries
- Connection Count
- CPU
- Storage
- Replication Lag

Databases are frequently the primary performance bottleneck.

---

# Monitor Third-Party APIs

External dependencies should expose metrics for:

- Availability
- Response Time
- Timeout Rate
- Failure Rate

Set appropriate timeout and retry policies.

---

# Define Service Level Indicators (SLIs)

Examples:

```text
Availability

99.95%

---------------------

Latency

P95 < 300 ms

---------------------

Success Rate

99.9%
```

SLIs measure service performance objectively.

---

# Define Service Level Objectives (SLOs)

Example:

```text
99.9%

Availability

Per Month
```

SLOs define operational targets for the engineering team.

---

# Incident Response

Typical workflow:

```text
Alarm

↓

Investigation

↓

Mitigation

↓

Recovery

↓

Postmortem
```

Document every production incident.

---

# Runbooks

Every operational issue should have a documented procedure.

Example:

```text
High Latency

↓

Check CloudWatch

↓

Review X-Ray

↓

Check Database

↓

Scale Backend
```

Runbooks reduce recovery time.

---

# Post-Incident Reviews

After resolving an incident:

- Identify root cause.
- Document timeline.
- Record customer impact.
- Define preventive actions.

The goal is continuous improvement rather than assigning blame.

---

# Capacity Planning

Monitor long-term trends.

Example:

```text
Traffic Growth

↓

Forecast

↓

Scale Infrastructure
```

Avoid reacting only after resources are exhausted.

---

# Cost Monitoring

Monitor:

- API Requests
- CloudWatch Costs
- Lambda Costs
- Data Transfer
- Cache Usage

Operational excellence includes financial efficiency.

---

# Production Monitoring Architecture

```text
                  Client

                     │

                     ▼

              Amazon API Gateway

                     │

      CloudWatch Metrics & Logs

                     │

                     ▼

              AWS X-Ray Traces

                     │

                     ▼

         Lambda / ECS / EC2 Services

                     │

                     ▼

      CloudWatch Dashboard & Alarms

                     │

                     ▼

             Amazon SNS Alerts
```

This architecture provides visibility across the entire request lifecycle.

---

# Common Operational Mistakes

Avoid:

- Monitoring only API Gateway
- Missing CloudWatch Alarms
- Logging sensitive information
- No centralized dashboards
- Ignoring tail latency
- Missing correlation IDs
- Keeping logs indefinitely
- No incident documentation
- No runbooks

---

# Operational Excellence Checklist

Before production:

- CloudWatch Metrics enabled
- Access Logs enabled
- Structured Logging implemented
- Correlation IDs supported
- X-Ray tracing enabled
- Dashboards created
- CloudWatch Alarms configured
- SNS notifications configured
- Runbooks documented
- Incident response process defined
- Cost monitoring enabled
- Log retention configured

---

# Common Interview Questions

### What is the difference between monitoring and observability?

Monitoring tells you **what** is happening by collecting metrics and logs, while observability helps explain **why** it is happening by correlating metrics, logs, and traces.

---

### What are the Four Golden Signals?

The Four Golden Signals are:

- Latency
- Traffic
- Errors
- Saturation

They provide a comprehensive view of application health.

---

### Why are Correlation IDs important?

Correlation IDs allow engineers to trace a single request across multiple services, simplifying debugging in distributed systems.

---

### What should trigger a CloudWatch Alarm?

Common triggers include:

- Increased latency
- High 5XX error rate
- High throttling
- High CPU or memory utilization
- Unhealthy backend instances

---

### What is a runbook?

A runbook is a documented operational procedure that guides engineers through diagnosing and resolving common production issues consistently and efficiently.

---

# Key Takeaways

- Monitoring and Operational Excellence are continuous processes that extend beyond application deployment.
- Combine metrics, logs, traces, dashboards, and alarms to achieve full visibility into API health.
- Monitor the Four Golden Signals—Latency, Traffic, Errors, and Saturation—to detect issues early.
- Structured logging, correlation IDs, and distributed tracing simplify troubleshooting in distributed architectures.
- Strong operational practices, including runbooks, incident reviews, capacity planning, and cost monitoring, improve system reliability and reduce recovery time.