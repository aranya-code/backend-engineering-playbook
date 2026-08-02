# Monitoring & Alarms

## Overview

Collecting metrics is only the first step in operating production APIs. The real value comes from **continuous monitoring** and **automatic alerting**.

Amazon CloudWatch Alarms continuously evaluate CloudWatch Metrics and automatically notify engineers when predefined thresholds are exceeded.

Instead of waiting for customers to report issues, operations teams can proactively detect:

- Increasing latency
- Rising error rates
- Backend failures
- Throttling
- Unusual traffic spikes
- Availability issues

CloudWatch Monitoring and Alarms form the foundation of a production-ready observability strategy.

---

# Why Monitoring?

Imagine an API normally serves requests with:

```text
Latency

↓

120 ms
```

Suddenly:

```text
Latency

↓

2500 ms
```

Without monitoring:

```text
Customers Notice First
```

With CloudWatch Alarms:

```text
Latency Spike

↓

CloudWatch Alarm

↓

SNS Notification

↓

Engineering Team
```

The issue is detected immediately.

---

# Architecture

```text
              Client

                 │

                 ▼

         Amazon API Gateway

                 │

         CloudWatch Metrics

                 │

                 ▼

        CloudWatch Alarm

                 │

                 ▼

            Amazon SNS

                 │

        ┌────────┴────────┐

        ▼                 ▼

     Email             Slack
```

---

# Monitoring Flow

```text
API Requests

↓

CloudWatch Metrics

↓

Alarm Evaluation

↓

Threshold Crossed?

│

├── No

│

└── Yes

      │

      ▼

SNS Notification
```

CloudWatch continuously evaluates incoming metrics.

---

# CloudWatch Alarm States

Every alarm exists in one of three states.

```text
OK

↓

Healthy

--------------------

ALARM

↓

Threshold Breached

--------------------

INSUFFICIENT_DATA

↓

Not Enough Data
```

---

# OK State

Example:

```text
Latency

150 ms

Threshold

500 ms
```

Result:

```text
OK
```

Everything is operating normally.

---

# ALARM State

Suppose:

```text
Latency

↓

850 ms

Threshold

↓

500 ms
```

CloudWatch changes state to:

```text
ALARM
```

Configured actions execute automatically.

---

# INSUFFICIENT_DATA

Occurs when CloudWatch has not collected enough metric data.

Examples:

- Newly created API
- Recently deployed stage
- No traffic

CloudWatch waits until sufficient data is available.

---

# Alarm Evaluation

Example:

```text
Evaluate

Every Minute

↓

Last 5 Minutes

↓

Average Latency
```

If the threshold is exceeded for the configured evaluation period, the alarm triggers.

---

# Common Metrics to Monitor

Production APIs commonly monitor:

- Count
- Latency
- IntegrationLatency
- 4XXError
- 5XXError
- CacheHitCount
- CacheMissCount
- ThrottleCount

These metrics provide a comprehensive view of API health.

---

# Latency Alarm

Example:

```text
Metric

Latency

Threshold

500 ms

Evaluation

5 Minutes
```

If latency exceeds 500 ms for five consecutive minutes:

```text
Alarm Triggered
```

---

# 5XX Error Alarm

Configuration:

```text
Metric

5XXError

Threshold

5 Errors

Evaluation

1 Minute
```

Useful for detecting backend failures.

---

# 4XX Error Alarm

High 4XX rates may indicate:

- Invalid client requests
- Authentication failures
- Authorization problems
- API misuse

Monitoring helps identify client-side issues.

---

# Throttling Alarm

Monitor:

```text
ThrottleCount
```

Example:

```text
Threshold

100 Requests

Per Minute
```

Frequent throttling may indicate:

- Traffic spikes
- Incorrect rate limits
- Abuse

---

# Request Count Alarm

Traffic monitoring helps detect:

```text
Sudden Spike

↓

Potential DDoS

-------------------

Sudden Drop

↓

Possible Outage
```

Both conditions may require investigation.

---

# Cache Monitoring

Monitor:

```text
CacheHitCount

CacheMissCount
```

Healthy cache:

```text
95% Hits
```

Poor cache:

```text
40% Hits
```

Low hit ratios may require cache tuning.

---

# Alarm Actions

CloudWatch can trigger:

- Amazon SNS
- AWS Lambda
- Auto Scaling
- EventBridge

For API Gateway, SNS notifications are the most common.

---

# Amazon SNS Notifications

Example:

```text
CloudWatch Alarm

↓

Amazon SNS

↓

Email

↓

Operations Team
```

SNS can also notify:

- Slack
- Microsoft Teams
- PagerDuty
- Incident Management Systems

---

# Composite Alarms

Instead of monitoring one metric:

```text
Latency

AND

5XX Errors

↓

Composite Alarm
```

This reduces false positives.

---

# Dashboard Monitoring

Production dashboards commonly include:

```text
Request Count

Latency

Integration Latency

4XX Errors

5XX Errors

Throttle Count

Cache Hit Ratio
```

Operations teams can monitor overall system health at a glance.

---

# Monitoring Strategy

```text
Metrics

↓

Dashboards

↓

Alarms

↓

Notifications

↓

Incident Response
```

This forms a complete monitoring pipeline.

---

# Alarm Example

Production API:

```text
Latency

↓

800 ms

↓

Alarm

↓

SNS

↓

Email

↓

Engineer
```

The engineer investigates before customers experience widespread failures.

---

# Alarm Tuning

Poor thresholds cause:

```text
Too Low

↓

Alert Fatigue

--------------------

Too High

↓

Late Detection
```

Thresholds should be based on normal production behavior.

---

# Real-World Example

An online payment API normally responds within:

```text
200 ms
```

After deployment:

```text
Latency

↓

2200 ms

↓

CloudWatch Alarm

↓

SNS

↓

Rollback
```

Automatic monitoring prevents a prolonged outage.

---

# Best Practices

- Monitor every production API.
- Create alarms for latency and 5XX errors.
- Monitor throttling separately.
- Use composite alarms to reduce unnecessary alerts.
- Send notifications through Amazon SNS.
- Review alarm thresholds regularly.
- Build CloudWatch Dashboards for operational visibility.
- Combine metrics, logs, and X-Ray during incident investigations.

---

# Common Interview Questions

### What is a CloudWatch Alarm?

A CloudWatch Alarm continuously evaluates CloudWatch Metrics and performs actions such as sending notifications when specified thresholds are exceeded.

---

### What are the three CloudWatch Alarm states?

- OK
- ALARM
- INSUFFICIENT_DATA

---

### Which API Gateway metrics are commonly monitored?

Common metrics include:

- Count
- Latency
- IntegrationLatency
- 4XXError
- 5XXError
- CacheHitCount
- CacheMissCount
- ThrottleCount

---

### What is a Composite Alarm?

A Composite Alarm combines multiple alarms into a single logical condition, helping reduce false alerts.

---

### Why integrate CloudWatch Alarms with Amazon SNS?

SNS enables automatic notifications through email, SMS, Slack, PagerDuty, and other incident management systems when alarms are triggered.

---

# Key Takeaways

- CloudWatch Monitoring provides continuous visibility into API Gateway performance using operational metrics.
- CloudWatch Alarms automatically detect abnormal conditions and trigger notifications or automated actions.
- Production APIs should monitor latency, error rates, request volume, throttling, and cache efficiency.
- Amazon SNS is commonly used to notify operations teams when alarms enter the ALARM state.
- Well-designed dashboards, meaningful alarm thresholds, and proactive monitoring are essential for maintaining highly available and reliable APIs.