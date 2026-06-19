# ECS Monitoring and Logging

# Why Monitoring Matters

Deploying containers is only half the job.

The real challenge is:

```text
How Do You Know
When Something Breaks?
```

Without monitoring:

- Failures go unnoticed
- Performance degrades
- Users complain before engineers know

---

# Observability Pillars

Modern observability consists of:

```text
Metrics
Logs
Traces
```

---

# Metrics

Answer:

```text
What Is Happening?
```

Examples:

- CPU Usage
- Memory Usage
- Request Count

---

# Logs

Answer:

```text
Why Did It Happen?
```

Examples:

- Errors
- Exceptions
- Application Events

---

# Traces

Answer:

```text
Where Did It Happen?
```

Useful for microservices.

---

# ECS Monitoring Architecture

```text
ECS Tasks
     ↓
CloudWatch Metrics

ECS Tasks
     ↓
CloudWatch Logs

ECS Tasks
     ↓
Tracing System
```

---

# CloudWatch Metrics

CloudWatch collects metrics automatically.

Examples:

```text
CPU Utilization
Memory Utilization
Network Traffic
Running Task Count
```

---

# Service Metrics

Common ECS service metrics:

```text
RunningTaskCount
PendingTaskCount
DesiredTaskCount
```

---

# Why These Matter

Example:

Desired:

```text
10 Tasks
```

Running:

```text
4 Tasks
```

Problem exists.

---

# CPU Monitoring

High CPU may indicate:

```text
Traffic Spike
Infinite Loop
Resource Bottleneck
```

---

Example

```text
CPU > 80%
```

Possible action:

```text
Scale Out
```

---

# Memory Monitoring

Memory exhaustion often causes:

```text
OOM Kill
```

Container terminated.

---

Warning Threshold

Example:

```text
Memory > 75%
```

---

Critical Threshold

```text
Memory > 90%
```

---

# Network Metrics

Monitor:

```text
Inbound Traffic
Outbound Traffic
Network Errors
```

Useful for:

- Traffic analysis
- Capacity planning

---

# Container Insights

Container Insights provides enhanced ECS monitoring.

Collects:

```text
Task Metrics
Container Metrics
Infrastructure Metrics
```

---

# Benefits

Provides:

- Performance visibility
- Capacity planning
- Operational insights

---

# Task-Level Monitoring

Monitor:

```text
CPU
Memory
Network
Status
```

for each task.

---

# Example

Task A:

```text
CPU = 40%
```

Healthy.

---

Task B:

```text
CPU = 95%
```

Potential bottleneck.

---

# Service-Level Monitoring

Monitor:

```text
Service Health
Task Counts
Deployment Status
```

---

# CloudWatch Logs

Most ECS workloads use:

```text
awslogs
```

log driver.

---

Architecture

```text
Container
     ↓
stdout/stderr
     ↓
CloudWatch Logs
```

---

# Why Centralized Logging?

Benefits:

- Searchability
- Retention
- Alerting
- Auditing

---

# Log Groups

Example:

```text
/ecs/user-service
```

---

# Log Streams

Each task generates:

```text
Unique Log Stream
```

---

# Structured Logging

Bad:

```text
Error occurred
```

---

Good:

```json
{
  "level": "ERROR",
  "service": "user-service",
  "message": "Database timeout"
}
```

---

# Benefits

- Easier searching
- Better analytics
- Improved troubleshooting

---

# Log Retention

Avoid storing logs forever.

Example:

```text
30 Days
90 Days
365 Days
```

depending on requirements.

---

# CloudWatch Alarms

Alarms notify engineers when thresholds are exceeded.

---

Example

```text
CPU > 80%
```

Trigger:

```text
CloudWatch Alarm
```

---

# Notification Flow

```text
Metric
 ↓
Alarm
 ↓
SNS
 ↓
Email / Slack
```

---

# Common Alarms

Examples:

```text
High CPU
High Memory
Task Failures
Low Healthy Targets
```

---

# Dashboards

Dashboards visualize metrics.

Typical dashboard includes:

```text
CPU
Memory
Requests
Errors
Latency
```

---

# Golden Signals

Monitor:

```text
Latency
Traffic
Errors
Saturation
```

These are critical production indicators.

---

# Distributed Tracing

Microservices often involve:

```text
User Service
 ↓
Order Service
 ↓
Payment Service
```

Tracing follows requests across services.

---

# AWS X-Ray

Provides:

```text
Request Tracing
Dependency Mapping
Latency Analysis
```

---

# OpenTelemetry

Industry standard observability framework.

Supports:

```text
Metrics
Logs
Traces
```

---

# Incident Response Workflow

```text
Alert
 ↓
Investigate Metrics
 ↓
Check Logs
 ↓
Analyze Traces
 ↓
Identify Root Cause
```

---

# Monitoring Example

Problem:

```text
API Slow
```

---

Step 1:

Check:

```text
CPU
Memory
```

---

Step 2:

Check:

```text
Application Logs
```

---

Step 3:

Check:

```text
Database Metrics
```

---

Step 4:

Check:

```text
Distributed Traces
```

---

# Production Monitoring Strategy

Monitor:

```text
Infrastructure
Containers
Applications
Business Metrics
```

Not just servers.

---

# Business Metrics

Examples:

```text
Orders Per Minute
Payments Processed
Users Logged In
```

Business impact matters.

---

# Common Monitoring Mistakes

## Monitoring Only Infrastructure

Problem:

Application issues missed.

---

## No Alerts

Problem:

Failures detected too late.

---

## No Log Retention Policy

Problem:

Higher costs.

---

## Ignoring Memory Usage

Problem:

Unexpected task crashes.

---

## No Dashboards

Problem:

Poor visibility.

---

# Troubleshooting Methodology

When an incident occurs:

Step 1:

```text
Check Alarms
```

---

Step 2:

```text
Check Metrics
```

---

Step 3:

```text
Check Logs
```

---

Step 4:

```text
Check Traces
```

---

Step 5:

```text
Determine Root Cause
```

---

# Common Interview Questions

## What Metrics Should You Monitor?

- CPU
- Memory
- Network
- Task Count

---

## Why Use CloudWatch Logs?

Centralized logging.

---

## What Are Container Insights?

Enhanced ECS monitoring.

---

## What Are Golden Signals?

Latency, Traffic, Errors, Saturation.

---

## What Is Distributed Tracing?

Tracking requests across services.

---

## How Would You Troubleshoot a Slow ECS Service?

Metrics → Logs → Traces → Root Cause.

---

# Senior Engineer Perspective

Monitoring is not about collecting data.

It is about:

```text
Detecting Problems
Understanding Problems
Fixing Problems Quickly
```

The best monitoring system helps engineers answer:

- What failed?
- Why did it fail?
- How many users were affected?
- How do we prevent recurrence?

Monitoring is a critical part of operating reliable production systems.

---

# Key Takeaways

- Observability consists of metrics, logs, and traces.
- CloudWatch is the primary ECS monitoring platform.
- Container Insights provides enhanced visibility.
- Structured logging improves troubleshooting.
- CloudWatch Alarms enable proactive monitoring.
- Distributed tracing helps diagnose microservice issues.
- Monitoring is essential for production reliability.
