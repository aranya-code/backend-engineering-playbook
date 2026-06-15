# AWS CloudFront - Section 09: Monitoring and Logging

# Why Monitoring Matters

CloudFront sits between users and your origin.

```text
Users
   |
CloudFront
   |
Origin
```

If something goes wrong, the issue could be:

- CloudFront
- Cache
- Network
- Origin
- Security
- Application

Monitoring helps identify the root cause quickly.

---

# Monitoring Goals

A CloudFront engineer should be able to answer:

```text
Is CloudFront healthy?

Is the origin healthy?

Is caching working?

Are users experiencing errors?

Is latency increasing?

Are costs increasing?
```

---

# CloudFront Monitoring Architecture

```text
Users
   |
CloudFront
   |
CloudWatch Metrics
   |
Logs
   |
Dashboards
   |
Alerts
```

---

# CloudWatch Metrics

CloudFront automatically publishes metrics to CloudWatch.

These metrics provide visibility into:

- Requests
- Traffic
- Errors
- Cache performance

---

# Important CloudFront Metrics

## Requests

Measures:

```text
Total Request Count
```

Example:

```text
10 Million Requests/Day
```

Used to:

- Measure traffic growth
- Detect unusual spikes

---

# Bytes Downloaded

Measures:

```text
Data Sent To Users
```

Example:

```text
500 GB Downloaded
```

Useful for:

- Capacity planning
- Cost analysis

---

# Bytes Uploaded

Measures:

```text
Data Uploaded By Users
```

Common with:

```text
POST Requests
PUT Requests
```

---

# Cache Hit Rate

One of the most important CloudFront metrics.

Measures:

```text
Percentage of Requests
Served From Cache
```

---

## Formula

```text
(Cache Hits / Total Requests)
× 100
```

---

## Example

Requests:

```text
1000
```

Cache Hits:

```text
900
```

Result:

```text
90%
```

---

# Why Cache Hit Rate Matters

Higher cache hit rate means:

```text
Lower Costs
Better Performance
Reduced Origin Load
```

---

# Good Cache Hit Rate

| Cache Hit Rate | Assessment |
|---------------|------------|
| < 50% | Poor |
| 50% - 70% | Average |
| 70% - 90% | Good |
| > 90% | Excellent |

---

# Error Rate Metrics

CloudFront tracks:

```text
4xx Errors
5xx Errors
```

---

# 4xx Error Rate

Represents:

```text
Client Errors
```

Examples:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
```

---

## Common Causes

### 403

Possible Reasons:

- OAC Misconfiguration
- WAF Block
- Geo Restriction
- Expired Signed URL

---

### 404

Possible Reasons:

- Object Missing
- Incorrect Path
- Wrong Origin Configuration

---

# 5xx Error Rate

Represents:

```text
Server Errors
```

Examples:

```text
500 Internal Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
```

---

# Common Causes

### 502

Possible Reasons:

```text
Origin Down
DNS Issue
SSL Mismatch
```

---

### 503

Possible Reasons:

```text
Origin Overloaded
Capacity Issue
```

---

### 504

Possible Reasons:

```text
Origin Timeout
Slow Backend
```

---

# Monitoring Error Rates

Healthy Distribution:

```text
Near Zero Errors
```

Sudden Increase:

```text
Requires Investigation
```

---

# Origin Latency

Measures:

```text
Time Taken
For Origin To Respond
```

---

# Why Important?

CloudFront may be healthy while the origin is slow.

Example:

```text
CloudFront = Healthy
Origin = Slow
```

Users still experience delays.

---

# Example

Normal:

```text
50 ms
```

Problematic:

```text
3000 ms
```

Possible Causes:

- Database Issues
- Application Bottlenecks
- Network Problems

---

# CloudFront Access Logs

## What Are Access Logs?

Detailed records of requests processed by CloudFront.

Stored in:

```text
Amazon S3
```

---

# Why Access Logs Matter

Access Logs help answer:

```text
Who accessed content?

What content was accessed?

When was it accessed?

Was it successful?
```

---

# Information Available

Each log entry may contain:

```text
Timestamp
Client IP
Request URI
HTTP Method
Status Code
User Agent
Referrer
```

---

# Example Log Data

```text
2026-01-01
203.0.113.10
GET
/logo.png
200
Chrome
```

---

# Common Log Use Cases

## Security Analysis

Identify:

```text
Suspicious Traffic
Bots
Attack Patterns
```

---

## Troubleshooting

Investigate:

```text
403 Errors
404 Errors
5xx Errors
```

---

## User Analytics

Understand:

```text
Popular Content
Traffic Sources
```

---

# Real-Time Logs

## What Are Real-Time Logs?

Real-Time Logs provide near real-time visibility into requests.

---

# Difference From Standard Logs

Standard Logs:

```text
Delayed Delivery
```

---

Real-Time Logs:

```text
Near Real-Time
```

---

# Use Cases

### Security Monitoring

Detect attacks immediately.

---

### Live Troubleshooting

Investigate incidents in real time.

---

### Performance Analysis

Track user experience instantly.

---

# Monitoring Cache Performance

## Key Questions

```text
Are cache hits increasing?

Are cache misses increasing?

Is origin traffic growing?
```

---

# Signs of Poor Caching

Symptoms:

```text
Low Cache Hit Rate
High Origin Traffic
Higher Costs
```

---

# Investigation Areas

Review:

```text
TTL Values
Cache Policies
Headers
Cookies
Query Strings
```

---

# CloudWatch Dashboards

## Purpose

Visualize CloudFront metrics.

---

# Recommended Dashboard Widgets

### Requests

```text
Requests Per Minute
```

---

### Cache Hit Rate

```text
Percentage Trend
```

---

### Error Rates

```text
4xx
5xx
```

---

### Origin Latency

```text
Response Time Trend
```

---

### Data Transfer

```text
Bytes Downloaded
Bytes Uploaded
```

---

# CloudWatch Alarms

## Why Use Alarms?

Detect issues automatically.

---

# Example Alarm

Trigger if:

```text
5xx Error Rate > 5%
```

for:

```text
5 Minutes
```

---

# Example Alert

```text
SNS Notification
Email
Slack
PagerDuty
```

---

# Common Monitoring Scenarios

## Scenario 1

Users report:

```text
Website Slow
```

Investigation:

```text
Origin Latency
Cache Hit Rate
5xx Errors
```

---

## Scenario 2

AWS Bill Increased

Investigation:

```text
Cache Hit Ratio
Origin Requests
Traffic Growth
```

---

## Scenario 3

Users Getting 403 Errors

Investigation:

```text
WAF
OAC
Signed URLs
Geo Restrictions
```

---

## Scenario 4

Origin Overloaded

Investigation:

```text
Cache Misses
TTL Settings
Cache Keys
```

---

# Troubleshooting Workflow

Step 1:

```text
Check CloudWatch Metrics
```

---

Step 2:

```text
Review Error Rates
```

---

Step 3:

```text
Review Cache Hit Ratio
```

---

Step 4:

```text
Review Access Logs
```

---

Step 5:

```text
Validate Origin Health
```

---

# Monitoring Best Practices

## Enable Logging

Always enable:

```text
Access Logs
```

---

## Monitor Cache Hit Rate

One of the most important KPIs.

---

## Create Alarms

Monitor:

```text
5xx Errors
Origin Latency
Traffic Spikes
```

---

## Use Dashboards

Centralize visibility.

---

## Analyze Trends

Look for:

```text
Traffic Growth
Cost Growth
Error Patterns
```

---

# Real-World Monitoring Architecture

```text
Users
   |
CloudFront
   |
CloudWatch Metrics
   |
CloudWatch Dashboard
   |
CloudWatch Alarm
   |
SNS
   |
Email / Slack
```

---

# Interview Questions

## Q1. Which service is used to monitor CloudFront?

```text
Amazon CloudWatch
```

---

## Q2. What is Cache Hit Rate?

The percentage of requests served from cache.

---

## Q3. Why is Cache Hit Rate important?

Because it impacts:

- Cost
- Performance
- Scalability
- Origin Load

---

## Q4. Where are CloudFront Access Logs stored?

```text
Amazon S3
```

---

## Q5. Difference Between Access Logs and Real-Time Logs?

Access Logs:

```text
Delayed
```

Real-Time Logs:

```text
Near Real-Time
```

---

## Q6. What would you investigate if 5xx errors suddenly increased?

Check:

- Origin Health
- Origin Latency
- Application Errors
- Infrastructure Issues

---

## Q7. What would you investigate if costs suddenly increased?

Check:

- Traffic Growth
- Cache Hit Ratio
- Origin Requests
- Invalidations

---

# Summary

Key Takeaways:

- CloudWatch is the primary monitoring service for CloudFront.
- Cache Hit Rate is one of the most critical metrics.
- 4xx errors indicate client-side issues.
- 5xx errors indicate server-side or origin issues.
- Access Logs provide historical visibility.
- Real-Time Logs provide immediate visibility.
- Dashboards and alarms improve operational awareness.
- Monitoring is essential for performance optimization, cost control, and troubleshooting.

For production workloads, always monitor:

```text
Requests
Cache Hit Rate
4xx Errors
5xx Errors
Origin Latency
Bytes Downloaded
```

