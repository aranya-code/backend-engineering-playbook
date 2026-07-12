# Troubleshooting & Best Practices

> Learn how to troubleshoot AWS Elastic Load Balancing (ELB) issues and apply production-ready best practices. This chapter covers Load Balancer failures, unhealthy targets, SSL issues, routing problems, Auto Scaling integration, monitoring, and operational recommendations for highly available applications.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot ELB issues
- Diagnose unhealthy targets
- Resolve SSL/TLS problems
- Debug Listener and Target Group issues
- Monitor Load Balancers
- Apply production deployment practices
- Build resilient ELB architectures

---

# ELB Troubleshooting Workflow

When requests fail:

```text
Client

↓

Route 53

↓

Load Balancer

↓

Listener

↓

Target Group

↓

Target

↓

Application
```

Always troubleshoot from the frontend toward the backend.

---

# Verify Load Balancer

List all Load Balancers.

```bash
aws elbv2 describe-load-balancers
```

Verify:

- State
- DNS Name
- Scheme
- VPC
- Availability Zones

---

# Verify Listeners

```bash
aws elbv2 describe-listeners \
--load-balancer-arn arn:aws:elasticloadbalancing:...
```

Check:

- Protocol
- Port
- Default Actions
- SSL Certificate

---

# Verify Target Groups

```bash
aws elbv2 describe-target-groups
```

Verify:

- Protocol
- Port
- Target Type
- Health Check configuration

---

# Verify Registered Targets

```bash
aws elbv2 describe-target-health \
--target-group-arn arn:aws:elasticloadbalancing:...
```

Review:

- Health State
- Reason
- Description

---

# Load Balancer Not Accessible

Possible causes:

- Incorrect DNS
- Security Group
- Public/Private mismatch
- Listener missing

Workflow:

```text
DNS

↓

Load Balancer

↓

Listener

↓

Target Group

↓

Application
```

---

# Targets Remain Unhealthy

Verify:

- Application running
- Correct port
- Health Check path
- Security Group
- Network ACL
- Route Table

---

# Health Check Failing

Example:

```text
Health Check

↓

GET /health

↓

404

↓

Unhealthy
```

Ensure:

```text
GET /health

↓

200 OK
```

---

# Security Group Issues

Load Balancer Security Group

Should allow:

```text
80

443
```

Target Security Group

Should allow traffic from the Load Balancer Security Group.

Avoid using wide CIDR ranges such as:

```text
0.0.0.0/0
```

for backend instances.

---

# Listener Problems

Verify:

```bash
aws elbv2 describe-listeners
```

Common issues:

- Wrong port
- Missing HTTPS Listener
- Missing redirect
- Incorrect Target Group

---

# SSL Certificate Problems

Verify:

```bash
aws acm list-certificates
```

Check:

- Certificate status
- Domain validation
- Correct Region
- Expiration

---

# HTTPS Not Working

Confirm:

- HTTPS Listener exists
- ACM Certificate attached
- Security Group allows 443
- DNS points to Load Balancer

---

# HTTP Redirect Missing

Production websites should redirect:

```text
HTTP

↓

HTTPS
```

Verify redirect rules.

---

# Routing Problems

Verify:

- Host Header rules
- Path rules
- Rule priorities
- Default rule

Example:

```text
/api/*

↓

API Target Group
```

---

# Target Registration Problems

Verify:

```text
Instance

↓

Correct VPC

↓

Correct Target Group

↓

Running

↓

Healthy
```

---

# Auto Scaling Issues

If new instances never receive traffic:

Verify:

- Target Group attached
- Health Checks
- Auto Scaling lifecycle
- Instance state

---

# Uneven Traffic Distribution

Possible causes:

- Cross-Zone Load Balancing disabled
- Unhealthy targets
- AZ imbalance

Verify:

```text
Cross-Zone

↓

Enabled
```

---

# Sticky Session Issues

Check:

- Browser cookies
- Stickiness enabled
- Cookie duration
- Target Group attributes

---

# WAF Blocking Requests

Verify:

- Web ACL
- Rule priority
- IP rules
- Managed Rules

Temporarily review WAF logs before modifying rules.

---

# Access Logs Missing

Verify:

- S3 bucket policy
- Logging enabled
- Correct bucket Region
- Permissions

---

# Idle Timeout Issues

Symptoms:

- Long uploads fail
- Streaming interrupted
- WebSockets disconnect

Increase timeout if appropriate.

---

# CloudWatch Monitoring

Useful metrics include:

- RequestCount
- HTTPCode_ELB_5XX_Count
- HTTPCode_Target_5XX_Count
- TargetResponseTime
- HealthyHostCount
- UnHealthyHostCount

---

# Enable CloudWatch Alarms

Recommended alarms:

```text
Healthy Hosts

↓

Less Than 2
```

```text
Target 5XX

↓

Greater Than 0
```

```text
Latency

↓

Above Threshold
```

---

# Common Errors

## LoadBalancerNotFound

Verify:

- ARN
- Region
- Account

---

## TargetGroupNotFound

Verify:

- Target Group ARN
- VPC
- Region

---

## ListenerNotFound

Listener has been deleted or ARN is incorrect.

---

## Target.NotRegistered

The instance has not been registered with the Target Group.

---

## Target.Timeout

Application is not responding before the Health Check timeout expires.

---

## SSLHandshakeError

Possible causes:

- Expired certificate
- Invalid certificate
- TLS version mismatch

---

## HTTP 502 Bad Gateway

Possible causes:

- Application crash
- Wrong target port
- Security Group
- Health Check mismatch

---

## HTTP 503 Service Unavailable

Usually indicates:

- No healthy targets
- Empty Target Group
- All instances unhealthy

---

## HTTP 504 Gateway Timeout

Possible causes:

- Slow backend
- Database latency
- Long-running requests
- Idle timeout

---

# Production Best Practices

## Deploy Across Multiple Availability Zones

Avoid:

```text
Single AZ
```

Prefer:

```text
AZ-A

↓

AZ-B

↓

AZ-C
```

---

## Use HTTPS Everywhere

Always:

```text
HTTP

↓

301 Redirect

↓

HTTPS
```

---

## Enable Access Logs

Store logs in S3.

Analyze using:

- Athena
- CloudWatch
- OpenSearch

---

## Use Auto Scaling

Never attach standalone production instances.

Prefer:

```text
ALB

↓

Target Group

↓

Auto Scaling Group
```

---

## Monitor Health Continuously

Use:

- CloudWatch
- ELB Metrics
- Health Checks
- AWS Health Dashboard

---

## Keep Applications Stateless

Avoid:

```text
Session

↓

EC2 Memory
```

Prefer:

```text
Session

↓

Redis

↓

DynamoDB
```

---

## Protect the Load Balancer

Enable:

- AWS WAF
- HTTPS
- Deletion Protection
- Security Groups

---

# Real-World Workflow

```text
Deploy ALB

↓

Deploy Target Group

↓

Attach Auto Scaling

↓

Configure HTTPS

↓

Enable WAF

↓

Enable Monitoring

↓

Production
```

---

# Architecture Note

```text
Internet
      │
      ▼
Route 53
      │
      ▼
Application Load Balancer
      │
      ├── HTTPS Listener
      ├── Health Checks
      ├── WAF
      ├── Access Logs
      └── Target Groups
              │
              ▼
      Auto Scaling Group
              │
              ▼
      EC2 / ECS / Lambda
```

A production ELB architecture combines secure traffic handling, health monitoring, automatic scaling, and observability to deliver highly available applications.

---

# Interview Note

### Question

**How would you troubleshoot an Application Load Balancer returning HTTP 503 errors?**

### Answer

I would first verify that the Target Group contains registered targets and inspect their health using `describe-target-health`. If all targets are unhealthy, I would review the Health Check configuration, ensure the application is running on the expected port, verify Security Group and Network ACL rules, and confirm the application returns a successful response (such as HTTP 200) from the configured health check path. I would also review CloudWatch metrics, ALB access logs, and application logs to identify the root cause before making configuration changes.

---

# Key Takeaways

- Troubleshoot ELB from the client to the backend application.
- Health Checks determine whether targets receive traffic.
- Security Groups and Listener configuration are common causes of connectivity issues.
- CloudWatch metrics and Access Logs are essential for production monitoring.
- Auto Scaling and Multi-AZ deployments improve availability.
- HTTPS, WAF, and Access Logs strengthen security and observability.
- A well-configured ELB is a critical component of scalable and resilient AWS architectures.