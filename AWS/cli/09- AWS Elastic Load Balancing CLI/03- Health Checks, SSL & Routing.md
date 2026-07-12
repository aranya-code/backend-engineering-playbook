# Health Checks, SSL & Routing

> Learn how AWS Elastic Load Balancing monitors backend health, terminates SSL/TLS connections, manages certificates, and intelligently routes traffic using Listener Rules. This chapter covers Health Checks, HTTPS configuration, AWS Certificate Manager (ACM), SSL termination, redirects, and production routing strategies.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Configure Health Checks
- Monitor Target Health
- Configure HTTPS Listeners
- Use AWS Certificate Manager (ACM)
- Understand SSL Termination
- Configure advanced Listener Rules
- Build secure production Load Balancers

---

# Why Health Checks Matter

A Load Balancer should never send traffic to unhealthy servers.

Without Health Checks:

```text
Users

↓

ALB

↓

Healthy EC2

↓

Unhealthy EC2

↓

Healthy EC2
```

Users may receive failed requests.

With Health Checks:

```text
Users

↓

ALB

↓

Healthy EC2

↓

Healthy EC2
```

Unhealthy targets are automatically removed.

---

# Health Check Workflow

```text
ALB

↓

Health Check

↓

Healthy?

↓

Forward Traffic

────────────

Unhealthy?

↓

Stop Forwarding
```

---

# Default Health Check

By default:

```text
Protocol

↓

HTTP
```

```text
Path

↓

/
```

Applications usually expose a dedicated endpoint.

Example:

```text
/health
```

---

# Create a Target Group with Health Checks

```bash
aws elbv2 create-target-group \
--name web-targets \
--protocol HTTP \
--port 80 \
--vpc-id vpc-0123456789abcdef0 \
--health-check-path /health
```

---

# Modify Health Check

```bash
aws elbv2 modify-target-group \
--target-group-arn arn:aws:elasticloadbalancing:... \
--health-check-path /health
```

---

# View Target Health

```bash
aws elbv2 describe-target-health \
--target-group-arn arn:aws:elasticloadbalancing:...
```

Returns:

- Healthy
- Unhealthy
- Initial
- Draining

---

# Health Check Parameters

Important settings:

| Setting | Description |
|----------|-------------|
| Protocol | HTTP / HTTPS |
| Port | Target Port |
| Path | `/health` |
| Interval | Check frequency |
| Timeout | Wait time |
| Healthy Threshold | Success count |
| Unhealthy Threshold | Failure count |

---

# Example Health Check

```text
Path

↓

/health

Interval

↓

30 seconds

Healthy Threshold

↓

5

Unhealthy Threshold

↓

2
```

---

# Health Check Response Codes

ALB expects successful HTTP responses.

Typical values:

```text
200

↓

Healthy
```

Custom example:

```text
200-299
```

---

# Health Check States

```text
Initial

↓

Healthy

↓

Unhealthy

↓

Draining
```

---

# Draining

During deployments:

```text
Old EC2

↓

Draining

↓

Finish Existing Requests

↓

Removed
```

This prevents dropped client connections.

---

# What is SSL/TLS?

SSL/TLS encrypts communication between clients and servers.

Without HTTPS:

```text
Browser

↓

Plain Text

↓

Internet
```

With HTTPS:

```text
Browser

↓

Encrypted

↓

Internet
```

---

# HTTPS Architecture

```text
Users

↓

HTTPS

↓

Application Load Balancer

↓

HTTP

↓

Application
```

This is called **SSL Termination**.

---

# SSL Termination

The ALB decrypts HTTPS traffic.

```text
HTTPS

↓

ALB

↓

HTTP

↓

EC2
```

Benefits:

- Reduced CPU usage
- Centralized certificate management
- Easier certificate rotation

---

# End-to-End Encryption

Some applications require encryption all the way to the backend.

```text
Users

↓

HTTPS

↓

ALB

↓

HTTPS

↓

Application
```

Common in:

- Banking
- Healthcare
- Government

---

# AWS Certificate Manager (ACM)

AWS recommends using ACM for certificates.

Benefits:

- Free public certificates
- Automatic renewal
- Managed lifecycle
- Easy ALB integration

---

# List ACM Certificates

```bash
aws acm list-certificates
```

---

# Describe Certificate

```bash
aws acm describe-certificate \
--certificate-arn arn:aws:acm:...
```

---

# HTTPS Listener

```bash
aws elbv2 create-listener \
--load-balancer-arn arn:aws:elasticloadbalancing:... \
--protocol HTTPS \
--port 443 \
--certificates CertificateArn=arn:aws:acm:... \
--default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

---

# Redirect HTTP to HTTPS

Common production setup:

```text
Port 80

↓

Redirect

↓

Port 443
```

CLI example:

```bash
aws elbv2 create-listener \
--load-balancer-arn arn:aws:elasticloadbalancing:... \
--protocol HTTP \
--port 80 \
--default-actions Type=redirect,RedirectConfig='{
"Protocol":"HTTPS",
"Port":"443",
"StatusCode":"HTTP_301"
}'
```

---

# Listener Rule Conditions

ALB supports routing based on:

- Host Header
- URL Path
- HTTP Header
- Query String
- Source IP
- HTTP Method

---

# Host-Based Routing

Example:

```text
api.example.com

↓

API Service
```

```text
admin.example.com

↓

Admin Service
```

---

# Path-Based Routing

Example:

```text
/api/*

↓

API Servers
```

```text
/images/*

↓

Image Service
```

---

# Header-Based Routing

Example:

```text
User-Agent

↓

Mobile

↓

Mobile Backend
```

---

# Query String Routing

Example:

```text
?version=beta

↓

Beta Service
```

Useful during testing.

---

# Source IP Routing

Example:

```text
Corporate Office

↓

Internal Admin Portal
```

---

# Multi-Service Architecture

```text
Users

↓

ALB

│

├── api.example.com

│      ↓

│   API

│

├── admin.example.com

│      ↓

│   Admin

│

└── www.example.com

       ↓

    Website
```

---

# SSL Certificate Workflow

```text
Request Certificate

↓

Validate Domain

↓

Certificate Issued

↓

Attach to ALB

↓

HTTPS Enabled
```

---

# Common Errors

## Target Unhealthy

Verify:

- Health endpoint
- Security Group
- Application running
- Correct port

---

## SSL Certificate Not Found

Verify:

- ACM Region
- Certificate ARN
- Validation status

---

## HTTPS Not Working

Check:

- HTTPS Listener
- Security Group
- Certificate
- DNS record

---

## Health Check Timeout

Possible causes:

- Slow application
- Database dependency
- Incorrect endpoint

---

# Production Best Practices

- Use HTTPS everywhere.
- Redirect HTTP to HTTPS.
- Store certificates in ACM.
- Expose a lightweight `/health` endpoint.
- Configure appropriate Health Check intervals.
- Use connection draining during deployments.
- Rotate certificates automatically.
- Monitor Target Health continuously.

---

# Real-World Workflow

```text
Deploy Application

↓

Create Target Group

↓

Configure Health Check

↓

Request ACM Certificate

↓

Create HTTPS Listener

↓

Redirect HTTP

↓

Production
```

---

# Architecture Note

```text
Users
      │
      ▼
HTTPS
      │
      ▼
Application Load Balancer
      │
      ├── Health Checks
      ├── SSL Termination
      ├── Listener Rules
      └── Target Groups
              │
              ▼
      EC2 / ECS / Lambda
```

Health Checks ensure requests reach only healthy targets, while SSL termination and advanced routing provide secure and intelligent traffic management.

---

# Interview Note

### Question

**What is SSL Termination in an Application Load Balancer?**

### Answer

SSL Termination is the process where the Application Load Balancer decrypts incoming HTTPS traffic before forwarding requests to backend targets. This centralizes certificate management, reduces encryption overhead on application servers, and simplifies certificate rotation. For workloads requiring end-to-end encryption, the Load Balancer can also forward traffic to backend targets over HTTPS.

---

# Key Takeaways

- Health Checks automatically remove unhealthy targets from service.
- Target Groups define health check behavior.
- HTTPS Listeners require ACM certificates.
- SSL Termination simplifies secure application deployment.
- HTTP requests should be redirected to HTTPS in production.
- ALBs support advanced routing using host headers, paths, headers, query strings, and source IPs.
- Combining Health Checks, HTTPS, and intelligent routing creates secure, highly available production architectures.