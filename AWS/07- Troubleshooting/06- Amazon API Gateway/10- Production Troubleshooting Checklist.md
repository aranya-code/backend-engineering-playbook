# Production Troubleshooting Checklist

## Overview

Production incidents require a structured troubleshooting approach. Jumping directly into application code often wastes valuable time because the root cause may lie in API Gateway configuration, authentication, networking, or backend infrastructure.

This chapter provides a practical troubleshooting checklist that can be used during production incidents involving Amazon API Gateway.

Rather than guessing, engineers should isolate each layer of the request path and verify it independently.

---

# Production Request Flow

```text
Client

↓

DNS

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

Authentication

↓

Authorization

↓

Request Validation

↓

Integration

↓

Backend

↓

Database

↓

Response
```

Every component should be verified individually.

---

# High-Level Troubleshooting Workflow

```text
Issue Reported

↓

Reproduce

↓

Identify HTTP Status

↓

Locate Failure Layer

↓

Review Logs

↓

Fix

↓

Validate

↓

Deploy

↓

Monitor
```

Never skip the reproduction step.

---

# Step 1 — Reproduce the Issue

Determine:

- Exact endpoint
- HTTP method
- Request headers
- Request body
- Authentication method
- Environment

Example:

```http
GET /products/100
```

Collect:

- Timestamp
- Request ID
- User
- Region

---

# Step 2 — Identify the Status Code

| Status Code | Usually Indicates |
|-------------|------------------|
| 400 | Invalid Request |
| 401 | Authentication |
| 403 | Authorization |
| 404 | Route/Stage |
| 429 | Throttling |
| 500 | Backend Error |
| 502 | Integration Error |
| 503 | Backend Unavailable |
| 504 | Backend Timeout |

The HTTP status code immediately narrows the investigation.

---

# Step 3 — Verify the Endpoint

Confirm:

```text
Correct URL

↓

Correct Stage

↓

Correct Route

↓

Correct Method
```

Many production incidents are caused by incorrect URLs.

---

# Step 4 — Verify Deployment

For REST APIs confirm:

```text
Latest Deployment

↓

Latest Stage
```

If configuration changes were made recently:

```text
Deploy Again
```

---

# Step 5 — Verify Authentication

Check:

- JWT
- Cognito
- IAM
- Lambda Authorizer

Confirm:

```text
Authorization Header

↓

JWT Expiration

↓

Issuer

↓

Audience
```

---

# Step 6 — Verify Authorization

Review:

- IAM Policy
- Resource Policy
- API Key
- Usage Plan
- WAF

Confirm client has permission.

---

# Step 7 — Review CloudWatch Metrics

Start with:

- Count
- 4XXError
- 5XXError
- Latency
- IntegrationLatency
- ThrottleCount

These metrics often reveal whether the problem is widespread or isolated.

---

# Step 8 — Review API Gateway Logs

Inspect:

Execution Logs

↓

Access Logs

Look for:

- Request ID
- Status Code
- Integration Error
- Validation Error

---

# Step 9 — Review Backend Logs

Depending on the backend:

Lambda

↓

CloudWatch Logs

or

ECS

↓

Container Logs

or

EC2

↓

Application Logs

Check for:

- Exceptions
- Stack traces
- Timeouts

---

# Step 10 — Review X-Ray

Trace:

```text
API Gateway

↓

Lambda

↓

Database

↓

External APIs
```

Locate the component contributing most of the latency.

---

# Step 11 — Verify Backend Health

If using ECS:

Verify:

- Running Tasks
- Service Events
- Target Group Health

If using Lambda:

Verify:

- Errors
- Duration
- Throttles

---

# Step 12 — Verify Database

Check:

- CPU
- Connections
- Slow Queries
- Locks
- Deadlocks

Common databases:

- PostgreSQL
- MySQL
- DynamoDB

---

# Step 13 — Verify Networking

Review:

- VPC
- Route Tables
- Security Groups
- Network ACLs
- VPC Link
- Interface Endpoints

Networking issues frequently appear as:

```http
502

503

504
```

---

# Step 14 — Review CloudFront

If CloudFront is used:

Verify:

- Origin
- Cache
- Behaviors
- Error Responses

Sometimes the problem is cached.

---

# Step 15 — Review AWS WAF

Check:

AWS WAF

↓

Blocked Requests

↓

Rules

↓

IP Sets

Many unexpected:

```http
403 Forbidden
```

responses originate from WAF.

---

# Step 16 — Verify API Gateway Configuration

Review:

- Integration
- Stage
- Deployment
- Mapping Templates
- Stage Variables
- Caching

---

# Step 17 — Review Service Quotas

Check:

- Request Rate
- Burst Limit
- Usage Plans
- API Keys

Symptoms:

```http
429 Too Many Requests
```

---

# Step 18 — Validate the Fix

Repeat the original request.

Confirm:

- Correct response
- Expected latency
- No new errors

---

# Step 19 — Monitor

Continue monitoring:

CloudWatch

↓

Metrics

↓

Logs

↓

X-Ray

Ensure the issue does not recur.

---

# Incident Troubleshooting Matrix

| Symptom | First Place to Check |
|---------|----------------------|
| 400 | Request Validation |
| 401 | JWT / Cognito |
| 403 | IAM / WAF / API Key |
| 404 | Route / Stage |
| 429 | Usage Plan / Throttling |
| 500 | Backend Logs |
| 502 | Integration |
| 503 | Backend Health |
| 504 | Backend Performance |

---

# Useful AWS Services

Use:

- CloudWatch Logs
- CloudWatch Metrics
- CloudWatch Alarms
- AWS X-Ray
- CloudTrail
- API Gateway Console
- Lambda Console
- ECS Console
- EC2 Console
- Route 53
- AWS WAF
- Service Quotas

---

# Production Incident Flow

```text
Alert

↓

CloudWatch Alarm

↓

Engineer

↓

Logs

↓

Metrics

↓

Tracing

↓

Root Cause

↓

Fix

↓

Validation

↓

Monitoring
```

---

# Production Readiness Checklist

Before deploying an API, verify:

- Latest deployment
- Correct stage
- CloudWatch logging enabled
- Access logs enabled
- X-Ray enabled
- CloudWatch alarms configured
- IAM permissions reviewed
- JWT configuration verified
- API Keys tested
- Usage Plans tested
- WAF configured
- CORS tested
- Health endpoint available
- Backend health checks passing
- Database monitoring enabled
- Load testing completed

---

# Operational Best Practices

- Always start with the HTTP status code.
- Reproduce the issue before making changes.
- Check CloudWatch before modifying infrastructure.
- Use Request IDs to correlate logs across services.
- Enable X-Ray for distributed tracing.
- Monitor trends instead of isolated failures.
- Automate deployments to reduce configuration drift.
- Document every production incident and its root cause.

---

# Common Interview Questions

### What is your troubleshooting approach when an API Gateway endpoint fails in production?

Start by reproducing the issue and identifying the HTTP status code. Review CloudWatch Metrics and Logs, inspect authentication and authorization, verify the API deployment and stage, trace the request with AWS X-Ray, and then investigate the backend service, database, or networking components as needed.

---

### Which AWS services are most useful for troubleshooting API Gateway?

The primary services are Amazon CloudWatch (Metrics, Logs, and Alarms), AWS X-Ray, AWS WAF, CloudTrail, and the backend service consoles such as Lambda or ECS.

---

### How do you determine whether the issue is API Gateway or the backend?

Compare CloudWatch **Latency** and **IntegrationLatency**, review execution logs, and inspect backend logs. If Integration Latency is high or the backend returns errors, the problem is likely behind API Gateway.

---

### Why is a structured troubleshooting workflow important?

A systematic approach reduces Mean Time to Resolution (MTTR), minimizes unnecessary changes, prevents overlooking configuration issues, and helps engineers identify the true root cause efficiently.

---

### What should be monitored after fixing an incident?

Continue monitoring CloudWatch Metrics, CloudWatch Logs, AWS X-Ray traces, application logs, and alarms to ensure the issue has been fully resolved and does not recur.

---

# Key Takeaways

- Effective troubleshooting begins with reproducing the issue and identifying the HTTP status code.
- API Gateway problems should be investigated layer by layer, from the client through authentication, integrations, backend services, and databases.
- CloudWatch, AWS X-Ray, and backend logs provide the most valuable diagnostic information during production incidents.
- Following a repeatable troubleshooting checklist reduces downtime and improves operational reliability.
- Documenting incidents and their resolutions helps teams build operational knowledge and improve future response times.