# Troubleshooting Interview Questions

## Overview

One of the biggest differences between a **Mid-Level** and a **Senior Backend Developer** interview is the emphasis on troubleshooting.

Junior interviews focus on:

- What is API Gateway?
- What is Lambda?
- What is JWT?

Senior interviews focus on:

- Why is the production API failing?
- How would you diagnose it?
- Which AWS service would you check first?
- How would you reduce MTTR?
- How would you prevent this from happening again?

Interviewers are looking for a structured debugging process rather than memorized AWS knowledge.

---

# Question 1

## Your production API suddenly returns 502 Bad Gateway.

How would you troubleshoot it?

### Answer

A 502 generally indicates an integration problem.

I would investigate in this order:

```text
Client

↓

API Gateway

↓

Integration

↓

Backend
```

Checklist:

- CloudWatch Metrics
- API Gateway Execution Logs
- Lambda Logs
- ECS Container Logs
- ALB Target Health
- Integration configuration

For Lambda:

- Verify response format
- Check exceptions
- Check permissions

For ECS:

- Verify Target Group
- Review application logs

I would avoid making changes before identifying the root cause.

---

# Question 2

## Your API returns 504 Gateway Timeout.

Where would you start?

### Answer

504 indicates the backend is taking too long.

I would investigate:

```text
CloudWatch Metrics

↓

IntegrationLatency

↓

X-Ray

↓

Backend

↓

Database
```

Possible causes:

- Slow SQL
- External API
- Lambda timeout
- ECS bottleneck

Increasing timeouts is not my first solution.

---

# Question 3

## Users receive 401 Unauthorized.

How would you debug it?

### Answer

Authentication issue.

I would verify:

- Authorization header
- JWT expiration
- JWT issuer
- JWT audience
- Cognito configuration
- JWT Authorizer

CloudWatch Execution Logs usually identify where authentication failed.

---

# Question 4

## Users receive 403 Forbidden.

### Answer

Authorization problem.

Checklist:

- IAM Policy
- Resource Policy
- API Key
- Usage Plan
- WAF
- VPC Endpoint Policy

403 means the user is authenticated but lacks permission.

---

# Question 5

## The API works in Postman but not in Chrome.

### Answer

The first thing I would suspect is:

```text
CORS
```

I would inspect:

Browser

↓

Developer Tools

↓

Network

↓

OPTIONS Request

Verify:

- Access-Control-Allow-Origin
- Access-Control-Allow-Headers
- Access-Control-Allow-Methods

---

# Question 6

## API changes are not visible after deployment.

### Answer

For REST APIs I would verify:

```text
Deployment

↓

Stage

↓

Latest Version
```

Common causes:

- Deployment not created
- Wrong stage
- Wrong custom domain mapping
- CloudFront cache

---

# Question 7

## CloudWatch shows high latency.

What next?

### Answer

Compare:

```text
Latency

vs

IntegrationLatency
```

If IntegrationLatency is high:

Backend issue.

If only Latency is high:

Review:

- Authorizers
- Request validation
- Mapping templates

---

# Question 8

## Customers receive intermittent failures.

How would you investigate?

### Answer

Intermittent failures usually indicate:

- Auto Scaling
- Database
- Network
- Third-party APIs

I would review:

- CloudWatch
- X-Ray
- ECS Tasks
- Lambda concurrency
- Database connections

before making infrastructure changes.

---

# Question 9

## Lambda logs are empty.

Why?

### Answer

Possible reasons:

- Lambda never invoked
- API Gateway integration incorrect
- Invoke permission missing
- Wrong Lambda ARN

Verify:

```bash
aws lambda get-policy
```

and API Gateway integration.

---

# Question 10

## API Gateway logs are empty.

### Answer

Possible causes:

- Logging disabled
- CloudWatch role missing
- Wrong stage
- IAM permission issue

Verify:

```text
API Gateway

↓

Stages

↓

Logs
```

---

# Question 11

## CloudWatch metrics suddenly show increasing 429 errors.

### Answer

I would check:

- Throttling
- Burst limits
- Usage Plans
- CloudWatch Metrics

If traffic is legitimate:

- Increase limits
- Cache responses

If traffic is malicious:

- AWS WAF
- Rate-based rules

---

# Question 12

## Your backend is healthy, but users still receive errors.

### Answer

I would verify:

- API Gateway deployment
- Integration configuration
- Custom Domain
- DNS
- Stage variables
- API Mapping

Sometimes infrastructure configuration is the problem.

---

# Question 13

## One endpoint is slow while others are fast.

### Answer

That usually indicates:

- SQL issue
- External API
- Missing index
- Large payload

I would trace only that endpoint using X-Ray.

---

# Question 14

## How do you isolate whether the problem is API Gateway or Lambda?

### Answer

Compare:

```text
Latency

↓

IntegrationLatency
```

Then inspect:

```text
CloudWatch Logs

↓

Lambda Logs

↓

X-Ray
```

This quickly identifies where time is spent.

---

# Question 15

## Customers report random 500 errors.

### Answer

I would investigate:

- Lambda exceptions
- ECS logs
- Database errors
- Third-party APIs

CloudWatch Logs usually reveal stack traces.

---

# Question 16

## Your API becomes slow only during peak traffic.

### Answer

I would investigate:

- Database CPU
- Lambda concurrency
- ECS Auto Scaling
- Redis hit ratio
- Connection pools

The database is frequently the first bottleneck.

---

# Question 17

## How do you troubleshoot Private APIs?

### Answer

Verify:

- Interface VPC Endpoint
- Resource Policy
- Security Groups
- Route Tables
- Private DNS

Private APIs introduce networking considerations beyond standard public APIs.

---

# Question 18

## How would you troubleshoot VPC Link failures?

### Answer

Review:

```text
API Gateway

↓

VPC Link

↓

ALB

↓

Target Group

↓

Backend
```

Check:

- Health checks
- Security Groups
- ECS Tasks
- DNS

---

# Question 19

## CloudFront returns stale responses.

### Answer

Possible causes:

- Cache TTL
- Cache invalidation missing
- Origin Cache-Control headers

I would verify CloudFront behavior before changing API Gateway.

---

# Question 20

## How do you reduce MTTR during production incidents?

### Answer

I follow a standard workflow.

```text
Alert

↓

CloudWatch Metrics

↓

CloudWatch Logs

↓

X-Ray

↓

Backend

↓

Root Cause

↓

Fix

↓

Validation
```

A repeatable process reduces investigation time.

---

# Whiteboard Question

## Draw your production troubleshooting workflow.

### Answer

```text
Client

↓

CloudFront

↓

WAF

↓

API Gateway

↓

CloudWatch

↓

Lambda / ECS

↓

Database

↓

External APIs

↓

Root Cause
```

Each layer should be verified independently.

---

# Rapid Fire Questions

- Why does API Gateway return 502?
- Difference between 502 and 504?
- Why compare Latency and IntegrationLatency?
- Why use X-Ray?
- What causes 429?
- Why is Lambda not invoked?
- Why are CloudWatch logs empty?
- Why does Postman work but Chrome fails?
- Why use CloudFront?
- Why use API Gateway caching?
- Why enable Access Logs?
- What causes Missing Authentication Token?
- Why use Request IDs?
- Why monitor ThrottleCount?

---

# Senior Interview Tips

Senior troubleshooting interviews evaluate **how you think under pressure**.

A strong answer follows a consistent pattern:

1. Reproduce the issue.
2. Identify the HTTP status code.
3. Review CloudWatch Metrics.
4. Examine CloudWatch Logs.
5. Trace the request with AWS X-Ray.
6. Isolate the failing component.
7. Fix the root cause.
8. Validate the solution.
9. Monitor for recurrence.

Avoid saying:

> "I would restart the service."

Instead explain **how you determine whether restarting is necessary**. Interviewers value systematic diagnosis over instinctive fixes.

---

# Key Takeaways

- Troubleshooting interviews assess production experience rather than theoretical knowledge.
- CloudWatch Metrics, CloudWatch Logs, and AWS X-Ray should form the foundation of your investigation process.
- HTTP status codes provide the first clue about where a failure originates.
- Isolating each layer of the request path helps identify root causes quickly and reduces Mean Time to Resolution (MTTR).
- Senior engineers are expected to explain not only how they would resolve an incident, but also how they would prevent similar issues in the future.