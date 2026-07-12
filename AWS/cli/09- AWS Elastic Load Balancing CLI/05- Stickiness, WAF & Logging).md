# Advanced Features (Stickiness, WAF & Logging)

> Learn advanced capabilities of AWS Elastic Load Balancing including Sticky Sessions, AWS WAF integration, Access Logs, HTTP Headers, Idle Timeouts, HTTP/2, WebSockets, gRPC, and production security best practices using the AWS CLI.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Configure Sticky Sessions
- Understand Session Persistence
- Integrate AWS WAF
- Configure Access Logs
- Understand HTTP/2 and WebSockets
- Configure Idle Timeout
- Apply production security best practices

---

# Why Advanced Features?

A production Load Balancer does much more than distribute traffic.

It also provides:

- Session persistence
- Web Application Firewall
- Logging
- Request tracing
- Security
- Modern protocol support

---

# Sticky Sessions

Normally:

```text
User

↓

EC2-A

↓

Next Request

↓

EC2-B
```

Each request can reach a different backend.

Sometimes this is undesirable.

---

# What are Sticky Sessions?

Sticky Sessions keep a user connected to the same backend instance.

```text
User

↓

ALB

↓

EC2-A

↓

Next Request

↓

EC2-A
```

---

# How Stickiness Works

The Load Balancer sends a cookie.

```text
Client

↓

Cookie

↓

ALB

↓

Same Target
```

Subsequent requests use the cookie to reach the same backend.

---

# Types of Sticky Sessions

```text
Stickiness

│

├── Load Balancer Cookie

└── Application Cookie
```

---

# Load Balancer Cookie

The ALB creates and manages the cookie automatically.

Example:

```text
AWSALB

↓

Cookie
```

Recommended for most applications.

---

# Application Cookie

The application generates its own cookie.

Useful when:

- Existing session management exists
- Legacy applications
- Custom authentication

---

# Enable Stickiness

```bash
aws elbv2 modify-target-group-attributes \
--target-group-arn arn:aws:elasticloadbalancing:... \
--attributes \
Key=stickiness.enabled,Value=true \
Key=stickiness.type,Value=lb_cookie
```

---

# Disable Stickiness

```bash
aws elbv2 modify-target-group-attributes \
--target-group-arn arn:aws:elasticloadbalancing:... \
--attributes Key=stickiness.enabled,Value=false
```

---

# When to Use Sticky Sessions

Suitable for:

- Legacy applications
- Shopping carts
- Stateful sessions

Avoid for:

- Stateless REST APIs
- Microservices
- JWT authentication

---

# What is AWS WAF?

AWS WAF (Web Application Firewall) protects web applications from common attacks.

Example:

```text
Users

↓

AWS WAF

↓

ALB

↓

Application
```

---

# WAF Protection

AWS WAF helps defend against:

- SQL Injection
- Cross-Site Scripting (XSS)
- Bot traffic
- IP reputation attacks
- Rate-based attacks

---

# WAF Architecture

```text
Internet

↓

AWS WAF

↓

Application Load Balancer

↓

Application
```

Traffic is inspected before reaching the application.

---

# Associate WAF with ALB

```bash
aws wafv2 associate-web-acl \
--web-acl-arn arn:aws:wafv2:... \
--resource-arn arn:aws:elasticloadbalancing:...
```

---

# View WAF Association

```bash
aws wafv2 get-web-acl-for-resource \
--resource-arn arn:aws:elasticloadbalancing:...
```

---

# Access Logs

ALB can write request logs to Amazon S3.

Example:

```text
Users

↓

ALB

↓

S3 Bucket
```

---

# Enable Access Logs

```bash
aws elbv2 modify-load-balancer-attributes \
--load-balancer-arn arn:aws:elasticloadbalancing:... \
--attributes \
Key=access_logs.s3.enabled,Value=true \
Key=access_logs.s3.bucket,Value=my-log-bucket
```

---

# Access Log Contents

Each log contains:

- Client IP
- Target IP
- HTTP Method
- URL
- Response Code
- Request Time
- Processing Time
- User Agent

---

# Why Enable Access Logs?

Useful for:

- Troubleshooting
- Security analysis
- Compliance
- Auditing
- Performance monitoring

---

# HTTP/2 Support

Application Load Balancer supports:

```text
HTTP/2
```

Benefits:

- Multiplexing
- Header compression
- Lower latency
- Improved performance

---

# WebSocket Support

ALB supports WebSockets.

Example:

```text
Browser

↓

WebSocket

↓

ALB

↓

Application
```

Useful for:

- Chat applications
- Live dashboards
- Notifications
- Real-time collaboration

---

# gRPC Support

ALB supports gRPC applications.

Architecture:

```text
Client

↓

gRPC

↓

ALB

↓

Microservice
```

---

# Idle Timeout

Idle Timeout determines how long inactive connections remain open.

Default:

```text
60 Seconds
```

---

# Modify Idle Timeout

```bash
aws elbv2 modify-load-balancer-attributes \
--load-balancer-arn arn:aws:elasticloadbalancing:... \
--attributes Key=idle_timeout.timeout_seconds,Value=120
```

---

# HTTP Headers

ALB automatically adds useful headers.

Examples:

```text
X-Forwarded-For
```

Contains:

Client IP Address

---

```text
X-Forwarded-Proto
```

Contains:

HTTP or HTTPS

---

```text
X-Forwarded-Port
```

Contains:

Client port

---

Applications should trust these headers rather than direct client IPs.

---

# Request Flow

```text
Browser

↓

HTTPS

↓

ALB

↓

Headers Added

↓

Application
```

---

# Deletion Protection

Prevent accidental deletion.

Enable:

```bash
aws elbv2 modify-load-balancer-attributes \
--load-balancer-arn arn:aws:elasticloadbalancing:... \
--attributes Key=deletion_protection.enabled,Value=true
```

---

# Disable Deletion Protection

```bash
aws elbv2 modify-load-balancer-attributes \
--load-balancer-arn arn:aws:elasticloadbalancing:... \
--attributes Key=deletion_protection.enabled,Value=false
```

---

# Common Errors

## Access Logs Not Generated

Verify:

- S3 Bucket Policy
- Bucket Region
- Logging enabled

---

## WAF Not Protecting ALB

Verify:

- Web ACL association
- Rule priorities
- WAF Region
- Resource ARN

---

## Sticky Sessions Not Working

Verify:

- Target Group attributes
- Browser cookies
- Cookie expiration
- Application configuration

---

## Idle Timeout Errors

Possible causes:

- Long-running requests
- Streaming applications
- WebSocket misconfiguration

Increase Idle Timeout if necessary.

---

# Production Best Practices

- Prefer stateless applications over Sticky Sessions.
- Enable AWS WAF for internet-facing ALBs.
- Store Access Logs in a dedicated S3 bucket.
- Enable Deletion Protection for production Load Balancers.
- Use HTTPS exclusively.
- Monitor logs using CloudWatch or Athena.
- Configure appropriate Idle Timeout values.
- Review WAF rules regularly.

---

# Real-World Workflow

```text
Deploy ALB

↓

Configure HTTPS

↓

Enable WAF

↓

Enable Access Logs

↓

Configure Health Checks

↓

Production
```

---

# Architecture Note

```text
Users
      │
      ▼
AWS WAF
      │
      ▼
Application Load Balancer
      │
      ├── HTTPS
      ├── Sticky Sessions
      ├── Access Logs
      ├── HTTP/2
      └── WebSockets
              │
              ▼
      Application
```

An Application Load Balancer acts as both a traffic distribution layer and a security gateway, integrating routing, TLS termination, WAF protection, logging, and modern protocol support.

---

# Interview Note

### Question

**When should you enable Sticky Sessions on an Application Load Balancer?**

### Answer

Sticky Sessions should be enabled only when an application requires session persistence, such as legacy web applications or shopping cart implementations that store session data locally on application servers. Modern cloud-native applications are typically designed to be stateless by storing session information in shared data stores like Redis or DynamoDB, making Sticky Sessions unnecessary and improving scalability.

---

# Key Takeaways

- Sticky Sessions provide session persistence when required.
- AWS WAF protects applications from common web attacks.
- Access Logs are essential for troubleshooting, auditing, and security analysis.
- ALBs support HTTP/2, WebSockets, and gRPC.
- Idle Timeout affects long-lived connections and streaming applications.
- X-Forwarded-* headers provide important client information to backend services.
- Advanced ELB features enhance security, observability, and performance in production environments.