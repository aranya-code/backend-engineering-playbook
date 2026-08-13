# AWS CloudFront - Section 11: Troubleshooting

# CloudFront Troubleshooting Methodology

When troubleshooting CloudFront, always follow a structured approach.

Never guess.

Use the following framework:

```text
1. Identify Symptoms
2. Check CloudFront Metrics
3. Check CloudFront Logs
4. Check Origin Health
5. Check Security Configuration
6. Validate Cache Behavior
7. Confirm Resolution
```

---

# Troubleshooting Architecture

```text
Users
   |
CloudFront
   |
Origin
```

Problems may exist at:

```text
Client
CloudFront
Network
Origin
Security Layer
```

---

# Step 1: Identify the Problem

Questions to ask:

```text
Is the issue affecting all users?

Specific countries?

Specific objects?

Entire application?

Recent deployment?
```

---

# Common Problem Categories

```text
403 Errors
404 Errors
502 Errors
503 Errors
504 Errors

High Latency

Low Cache Hit Ratio

Origin Overload

Signed URL Failures

TLS/SSL Errors
```

---

# Troubleshooting 403 Forbidden

## What Does 403 Mean?

CloudFront understood the request.

However:

```text
Access Denied
```

---

# Common Causes

## OAC Misconfiguration

Architecture:

```text
CloudFront
   |
S3
```

CloudFront lacks permission.

---

## Bucket Policy Problems

Example:

```text
S3 Denies CloudFront Access
```

---

## WAF Blocking Requests

Possible:

```text
SQL Injection Rule
Bot Protection Rule
Rate Limit Rule
```

---

## Geo Restriction

Blocked country.

Example:

```text
Country Not Allowed
```

---

## Expired Signed URL

CloudFront rejects request.

---

## Invalid Signed Cookie

Authentication fails.

---

# 403 Troubleshooting Workflow

Step 1:

```text
Check CloudFront Logs
```

---

Step 2:

```text
Check WAF Logs
```

---

Step 3:

```text
Validate OAC
```

---

Step 4:

```text
Review Bucket Policy
```

---

Step 5:

```text
Check Signed URL Expiration
```

---

# Troubleshooting 404 Not Found

## What Does 404 Mean?

Requested object does not exist.

---

# Common Causes

## Object Missing

Example:

```text
/logo.png
```

not found in origin.

---

## Wrong Path Pattern

Cache behavior mismatch.

Example:

```text
/images/*
```

request routed incorrectly.

---

## Incorrect Origin

Request routed to wrong backend.

---

# Investigation

Verify:

```text
Object Exists

Correct Origin

Correct Path
```

---

# Troubleshooting 502 Bad Gateway

## What Does 502 Mean?

CloudFront cannot communicate properly with the origin.

---

# Common Causes

## Origin Offline

Example:

```text
NGINX Down
```

---

## SSL Certificate Problems

Example:

```text
CloudFront HTTPS
Origin Invalid Certificate
```

---

## DNS Resolution Failure

Origin hostname unavailable.

---

# Investigation

Verify:

```text
Origin Reachability

Certificate Validity

DNS Resolution
```

---

# Troubleshooting 503 Service Unavailable

## What Does 503 Mean?

Origin unavailable or overloaded.

---

# Common Causes

## Traffic Spike

Example:

```text
Black Friday
```

---

## Insufficient Backend Capacity

Example:

```text
Single EC2 Instance
```

---

## Application Failure

Backend application unhealthy.

---

# Resolution

Scale:

```text
ALB
Auto Scaling
ECS
EKS
```

---

# Troubleshooting 504 Gateway Timeout

## What Does 504 Mean?

Origin did not respond within expected time.

---

# Common Causes

## Slow Database

Example:

```text
Long Running Query
```

---

## Application Bottleneck

Slow processing.

---

## Network Latency

Connectivity issues.

---

# Investigation

Review:

```text
Origin Latency

Application Logs

Database Metrics
```

---

# Troubleshooting High Latency

## Symptoms

Users report:

```text
Slow Website
```

---

# Investigation Areas

## Cache Hit Ratio

Low cache hit ratio often causes latency.

---

## Origin Latency

Slow origin responses.

---

## Geographic Distance

Origin far from users.

---

## Large Objects

Huge files.

Example:

```text
2 GB Video
```

---

# Resolution

Improve:

```text
Caching
Compression
Origin Performance
```

---

# Troubleshooting Low Cache Hit Ratio

## Symptoms

```text
High Origin Traffic
High Costs
Slow Performance
```

---

# Common Causes

## Low TTL

Example:

```text
TTL = 60 Seconds
```

---

## Large Cache Key

Includes:

```text
Cookies
Headers
Query Strings
```

---

## Frequent Invalidations

Objects removed too often.

---

# Investigation

Review:

```text
Cache Policy

TTL

Headers

Cookies
```

---

# Example

Bad Cache Key:

```text
User-Agent
Session Cookie
Tracking Parameters
```

Result:

```text
Thousands of Cache Variations
```

---

# Troubleshooting Origin Overload

## Symptoms

```text
High CPU

High Memory

Slow Responses
```

---

# Causes

## Cache Misses

Too many requests reaching origin.

---

## Traffic Spike

Unexpected traffic growth.

---

## Poor Cache Strategy

Low cache efficiency.

---

# Resolution

Increase:

```text
TTL

Cache Hit Ratio

Origin Capacity
```

---

# Troubleshooting Signed URL Issues

## Symptoms

```text
Access Denied
```

---

# Common Causes

## Expired URL

Current time exceeds expiration.

---

## Invalid Signature

Signature mismatch.

---

## Wrong Key Group

CloudFront cannot validate signature.

---

## Incorrect Policy

Access restrictions not satisfied.

---

# Investigation

Verify:

```text
Expiration

Key Pair

Signature

Policy
```

---

# Troubleshooting Signed Cookie Issues

## Symptoms

```text
Content Access Fails
```

---

# Common Causes

## Cookie Missing

Browser not sending cookie.

---

## Cookie Expired

Authentication invalid.

---

## Domain Mismatch

Cookie attached to wrong domain.

---

# Investigation

Check:

```text
Browser Developer Tools

Cookie Values

Cookie Expiration
```

---

# Troubleshooting TLS/SSL Errors

## Symptoms

```text
SSL Handshake Failure
```

---

# Common Causes

## Expired Certificate

Certificate validity ended.

---

## Wrong Domain

Certificate does not match hostname.

---

## Missing Intermediate Certificate

Chain incomplete.

---

# Investigation

Verify:

```text
Certificate

Domain Mapping

ACM Configuration
```

---

# Troubleshooting WAF Issues

## Symptoms

Legitimate users blocked.

---

# Common Causes

## Aggressive Rules

False positives.

---

## Rate Limiting

Users exceed limits.

---

## Geo Blocking

Country blocked unintentionally.

---

# Investigation

Review:

```text
WAF Logs

Rule Matches

Blocked Requests
```

---

# CloudWatch Metrics for Troubleshooting

Important Metrics:

```text
Requests

Cache Hit Rate

4xx Errors

5xx Errors

Origin Latency

Bytes Downloaded
```

---

# Log Analysis Strategy

## CloudFront Access Logs

Look for:

```text
Status Codes

Requested Objects

IP Addresses

User Agents
```

---

## WAF Logs

Look for:

```text
Blocked Requests

Matched Rules
```

---

## Application Logs

Look for:

```text
Backend Errors

Timeouts

Exceptions
```

---

# Real-World Scenario 1

## Problem

Users report:

```text
Website Slow
```

---

# Investigation

CloudWatch:

```text
Cache Hit Rate = 25%
```

---

# Root Cause

Large Cache Key.

---

# Resolution

Remove:

```text
User-Agent

Tracking Parameters
```

---

# Result

```text
Cache Hit Rate = 88%
```

Performance improves.

---

# Real-World Scenario 2

## Problem

Users receive:

```text
403 Errors
```

---

# Investigation

CloudFront Logs:

```text
403
```

WAF Logs:

```text
Blocked
```

---

# Root Cause

Rate Limit Rule.

---

# Resolution

Adjust WAF threshold.

---

# Real-World Scenario 3

## Problem

CloudFront returns:

```text
502
```

---

# Investigation

Origin unreachable.

---

# Root Cause

Expired SSL certificate.

---

# Resolution

Renew certificate.

---

# Troubleshooting Checklist

### Security

```text
OAC

WAF

Signed URLs

Signed Cookies

Geo Restrictions
```

---

### Origin

```text
Health

Capacity

Latency

Certificates
```

---

### Cache

```text
TTL

Cache Key

Invalidations
```

---

### Monitoring

```text
Metrics

Logs

Alarms
```

---

# Interview Questions

## Q1. How would you troubleshoot a sudden increase in 5xx errors?

Check:

```text
Origin Health

Origin Latency

Application Logs
```

---

## Q2. What would you investigate if CloudFront costs increased suddenly?

Review:

```text
Traffic

Cache Hit Ratio

Origin Requests
```

---

## Q3. How would you troubleshoot low Cache Hit Ratio?

Check:

```text
TTL

Headers

Cookies

Query Strings
```

---

## Q4. Why might users receive 403 errors?

Possible causes:

```text
WAF

OAC

Geo Restriction

Expired Signed URL
```

---

## Q5. What metrics are most useful during troubleshooting?

```text
Cache Hit Rate

4xx Errors

5xx Errors

Origin Latency
```

---

# Summary

Key Takeaways:

- Always follow a structured troubleshooting process.
- 4xx errors usually indicate client or security issues.
- 5xx errors usually indicate origin issues.
- Cache Hit Ratio is one of the most important troubleshooting metrics.
- Logs and metrics should always be analyzed together.
- Most CloudFront issues can be traced to:
  - Security Configuration
  - Cache Configuration
  - Origin Configuration
  - Application Problems

Mastering troubleshooting scenarios is critical because CloudFront interviewers frequently ask:

```text
"A production issue occurred. How would you investigate it?"
```
