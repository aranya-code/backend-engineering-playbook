# Health Checks & Failover

> Learn how Amazon Route 53 Health Checks monitor application availability and automatically route traffic during failures. This chapter covers Health Checks, CloudWatch integration, Failover Routing, Recovery strategies, DNS failover, and production disaster recovery best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Route 53 Health Checks
- Configure Health Checks using AWS CLI
- Monitor application availability
- Implement DNS Failover
- Integrate Route 53 with CloudWatch
- Design highly available DNS architectures
- Build disaster recovery solutions

---

# Why Health Checks?

DNS alone cannot determine whether an application is healthy.

Example:

```text
www.example.com

↓

54.201.x.x
```

If the server crashes, DNS still returns the same IP.

Health Checks solve this problem by continuously monitoring endpoints.

---

# What is a Health Check?

A Health Check periodically sends requests to an endpoint.

Example:

```text
Route 53

↓

HTTP Request

↓

Application

↓

Healthy?
```

If the application fails, Route 53 can stop directing traffic to it.

---

# Supported Health Check Types

Route 53 supports:

```text
Health Checks

│

├── HTTP

├── HTTPS

├── TCP

├── CloudWatch Alarm
```

---

# HTTP Health Check

Checks whether a web server responds successfully.

```text
Route 53

↓

HTTP GET

↓

http://example.com
```

Expected response:

```text
HTTP 200 OK
```

---

# HTTPS Health Check

Checks secure web applications.

```text
Route 53

↓

HTTPS

↓

https://example.com
```

---

# TCP Health Check

Verifies that a TCP port is reachable.

Example:

```text
Route 53

↓

TCP

↓

Port 443
```

Useful for:

- Databases
- Mail Servers
- Custom Applications

---

# CloudWatch Alarm Health Check

Instead of checking an endpoint directly:

```text
CloudWatch Alarm

↓

Healthy

↓

Route 53
```

Useful when:

- Applications are inside private VPCs
- Endpoints are inaccessible from the Internet

---

# Health Check Architecture

```text
Users

↓

Route 53

↓

Health Check

↓

Application
```

---

# Create a Health Check

Example:

```bash
aws route53 create-health-check \
--caller-reference "$(date +%s)" \
--health-check-config '{
  "IPAddress":"203.0.113.10",
  "Port":443,
  "Type":"HTTPS",
  "ResourcePath":"/health",
  "RequestInterval":30,
  "FailureThreshold":3
}'
```

---

# List Health Checks

```bash
aws route53 list-health-checks
```

---

# Get Health Check Details

```bash
aws route53 get-health-check \
--health-check-id abc12345-6789-def0-1234-56789abcdef0
```

---

# Delete a Health Check

```bash
aws route53 delete-health-check \
--health-check-id abc12345-6789-def0-1234-56789abcdef0
```

---

# Health Check Status

Typical workflow:

```text
Healthy

↓

Continue Serving Traffic
```

If failures occur:

```text
Failure

↓

Retry

↓

Threshold Reached

↓

Unhealthy
```

---

# Request Interval

Two options:

| Interval | Description |
|-----------|-------------|
| 30 Seconds | Standard |
| 10 Seconds | Faster detection (additional cost) |

---

# Failure Threshold

Determines how many failed checks are required.

Example:

```text
Failure Threshold

↓

3
```

After three consecutive failures:

```text
Healthy

↓

Unhealthy
```

---

# Endpoint Health Workflow

```text
Request

↓

Success

↓

Healthy

────────────

Request

↓

Failure

↓

Retry

↓

Failure Threshold

↓

Unhealthy
```

---

# What is DNS Failover?

DNS Failover automatically redirects users when the primary application becomes unavailable.

---

# Failover Architecture

```text
Users

↓

Route 53

↓

Health Check

│

├── Healthy

│      ↓

│  Primary Region

│

└── Failed

       ↓

Secondary Region
```

---

# Primary and Secondary Records

Primary Record

```text
Primary

↓

Health Check
```

Secondary Record

```text
Backup

↓

No Health Check Required
```

When the primary fails, Route 53 returns the secondary record.

---

# Active-Passive Disaster Recovery

```text
Primary Region

↓

Application

↓

Failure

↓

Secondary Region

↓

Application
```

Only one Region actively serves traffic.

---

# Active-Active Architecture

Instead of one backup:

```text
Users

↓

Route 53

↓

Multiple Healthy Regions
```

All Regions serve traffic simultaneously.

Typically combined with:

- Latency Routing
- Weighted Routing
- Health Checks

---

# CloudWatch Integration

Health Checks can monitor CloudWatch Alarms.

Example:

```text
Application

↓

CloudWatch

↓

Alarm

↓

Route 53
```

Useful for:

- CPU utilization
- Memory usage
- Custom application metrics

---

# Monitoring Health Checks

Useful commands:

```bash
aws route53 list-health-checks
```

```bash
aws cloudwatch describe-alarms
```

---

# Typical Health Check Endpoint

Production applications often expose:

```text
/health
```

Example response:

```json
{
  "status": "UP"
}
```

The endpoint should perform lightweight dependency checks and return quickly.

---

# Common Errors

## Health Check Always Failing

Possible causes:

- Incorrect IP address
- Firewall blocking Route 53
- Invalid URL
- Wrong port
- SSL certificate problems

---

## Incorrect Resource Path

Example:

Incorrect:

```text
/status
```

Correct:

```text
/health
```

---

## Security Group Blocking Requests

Allow inbound traffic from Route 53 Health Checkers if your architecture requires public endpoint monitoring.

---

## CloudWatch Alarm Never Healthy

Verify:

- Alarm state
- Metric configuration
- Evaluation period

---

# Production Best Practices

- Create dedicated `/health` endpoints.
- Keep health checks lightweight.
- Avoid expensive database queries in health endpoints.
- Use HTTPS whenever possible.
- Deploy applications across multiple Availability Zones.
- Use Failover Routing for disaster recovery.
- Combine Health Checks with CloudWatch Alarms.
- Regularly test failover procedures.

---

# Real-World Workflow

```text
Deploy Application

↓

Create Health Check

↓

Associate DNS Record

↓

Configure Failover Routing

↓

Test Failure

↓

Production
```

---

# Architecture Note

```text
Users
      │
      ▼
Amazon Route 53
      │
      ▼
Health Check
      │
      ├── Healthy
      │      │
      │      ▼
      │  Primary Application
      │
      └── Unhealthy
             │
             ▼
      Secondary Application
```

Route 53 Health Checks ensure that DNS responses point only to healthy application endpoints, improving availability and enabling automated disaster recovery.

---

# Interview Note

### Question

**How does Route 53 Failover Routing work?**

### Answer

Route 53 Failover Routing uses Health Checks to monitor the availability of a primary endpoint. As long as the Health Check reports the endpoint as healthy, Route 53 returns the primary DNS record. If the Health Check fails and the configured failure threshold is reached, Route 53 automatically returns the secondary (backup) record instead. This enables DNS-based disaster recovery without requiring manual intervention.

---

# Key Takeaways

- Health Checks continuously monitor application availability.
- Route 53 supports HTTP, HTTPS, TCP, and CloudWatch Alarm Health Checks.
- DNS Failover automatically redirects traffic to backup endpoints.
- Active-Passive architectures commonly use Failover Routing.
- Active-Active architectures combine Health Checks with Latency or Weighted Routing.
- Lightweight `/health` endpoints improve monitoring reliability.
- Regular failover testing is essential for production disaster recovery.