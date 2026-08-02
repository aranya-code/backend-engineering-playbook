# Scenario-Based Questions

## Overview

Senior backend interviews are increasingly focused on **real-world scenarios** rather than theoretical knowledge.

Instead of asking:

> "What is API Gateway?"

Interviewers often ask:

> "Your production API suddenly starts returning 502 errors. How would you investigate?"

The goal is to evaluate your:

- Debugging approach
- Architectural thinking
- Production experience
- Decision making
- Ability to balance cost, performance, and security

The best answers explain:

1. What you would investigate
2. Why you would investigate it
3. What tools you would use
4. How you would resolve the issue

---

# Scenario 1

## Your API suddenly starts returning 502 Bad Gateway.

How would you troubleshoot it?

### Answer

A 502 usually indicates an integration problem.

My troubleshooting approach:

```text
Client

↓

API Gateway

↓

Integration

↓

Backend
```

I would investigate in this order:

1. CloudWatch Metrics
2. API Gateway Execution Logs
3. Lambda/ECS Logs
4. Integration configuration
5. Backend health

For Lambda:

- Verify response format
- Check exceptions
- Check timeout

For ECS:

- Verify Target Group health
- Check ALB
- Review container logs

I would avoid making configuration changes until the root cause is identified.

---

# Scenario 2

## The API works in Postman but fails in the browser.

### Answer

The first thing I suspect is:

```text
CORS
```

I would verify:

- OPTIONS request
- Access-Control-Allow-Origin
- Access-Control-Allow-Headers
- Access-Control-Allow-Methods

I would inspect the browser's Developer Tools rather than relying on Postman, since Postman does not enforce CORS.

---

# Scenario 3

## Users report intermittent 504 Gateway Timeout errors.

### Answer

Timeouts usually indicate backend performance problems.

Investigation flow:

```text
CloudWatch

↓

Latency

↓

IntegrationLatency

↓

X-Ray

↓

Backend

↓

Database
```

Things to check:

- Lambda duration
- ECS response time
- Database queries
- Third-party APIs

I would identify the slowest component before attempting to increase timeout values.

---

# Scenario 4

## Your API receives ten times more traffic than expected.

How would you prepare?

### Answer

Before scaling infrastructure, I would reduce unnecessary backend traffic.

Architecture:

```text
Users

↓

CloudFront

↓

API Gateway

↓

Cache

↓

Backend
```

Actions:

- Enable CloudFront
- Enable API Gateway caching
- Review Usage Plans
- Configure throttling
- Load test
- Scale backend
- Monitor CloudWatch

The database would receive special attention because it often becomes the bottleneck.

---

# Scenario 5

## You need to expose an internal API to another AWS account.

### Answer

I would avoid making the API public.

Preferred architecture:

```text
AWS Account A

↓

Private API

↓

Resource Policy

↓

VPC Endpoint

↓

AWS Account B
```

This keeps communication on the AWS network while limiting access to trusted accounts.

---

# Scenario 6

## A frontend team asks for an API Key.

Would you give them one?

### Answer

Not by itself.

API Keys identify applications.

They do **not** authenticate users.

I would recommend:

```text
JWT Authentication

+

API Key

+

Usage Plan
```

JWT authenticates the user.

API Keys identify the client application.

---

# Scenario 7

## Your Lambda-based API has become expensive.

How would you reduce cost?

### Answer

I would investigate:

- Invocation count
- Duration
- Memory allocation

Possible optimizations:

- API Gateway caching
- CloudFront caching
- Redis
- Reduce cold starts
- Optimize code
- Remove unnecessary invocations

I would use CloudWatch before making scaling decisions.

---

# Scenario 8

## The business wants global low-latency APIs.

How would you design them?

### Answer

```text
Users

↓

Route 53

↓

CloudFront

↓

Regional API Gateway

↓

Lambda

↓

DynamoDB Global Tables
```

Benefits:

- Global caching
- Lower latency
- Multi-region resilience

---

# Scenario 9

## Your company wants to migrate from a monolithic API.

How would you approach it?

### Answer

Instead of rewriting everything at once:

```text
Monolith

↓

API Gateway

↓

Users Service

Orders Service

Payments Service
```

Gradually route endpoints to new microservices while the remaining endpoints continue to use the monolith.

This minimizes migration risk.

---

# Scenario 10

## A partner company requires highly secure API access.

### Answer

Architecture:

```text
Partner

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

mTLS

↓

JWT

↓

Backend
```

Additional controls:

- API Keys
- Usage Plans
- CloudWatch
- CloudTrail

---

# Scenario 11

## Your API must process requests that take several minutes.

Would you use API Gateway synchronously?

### Answer

No.

API Gateway is not intended for long-running synchronous operations.

Preferred design:

```text
Client

↓

API Gateway

↓

Lambda

↓

SQS

↓

Worker

↓

Database
```

The API immediately returns:

```http
202 Accepted
```

The client later checks the job status.

---

# Scenario 12

## Customers are seeing 429 Too Many Requests.

How would you respond?

### Answer

I would verify:

- Usage Plans
- Throttling
- Burst limits
- CloudWatch metrics

If traffic is legitimate:

- Increase quotas
- Optimize backend
- Add caching

If traffic is malicious:

- Enable WAF rate limiting
- Block offending clients

---

# Scenario 13

## A deployment completed successfully, but users still see the old API.

### Answer

For REST APIs, I would verify:

- Deployment created
- Correct stage
- Stage variables
- Custom domain mappings
- CloudFront cache

A successful deployment does not always mean clients receive the latest version.

---

# Scenario 14

## Your manager wants to reduce API costs by 40%.

What would you optimize first?

### Answer

I would review:

- CloudWatch Metrics
- Lambda duration
- Invocation count
- Cache hit ratio

Potential optimizations:

- CloudFront
- API Gateway cache
- Redis
- Compression
- Pagination
- Efficient SQL

I would avoid changing architecture before identifying where costs are incurred.

---

# Scenario 15

## Which AWS service would you investigate first during a production outage?

### Answer

My order would be:

```text
CloudWatch Metrics

↓

CloudWatch Logs

↓

X-Ray

↓

Backend Logs

↓

Database
```

Metrics provide a high-level view.

Logs identify the failure.

Tracing identifies where the request spends time.

---

# Scenario 16

## Would you choose REST API or HTTP API for a new project?

### Answer

My default choice would be:

```text
HTTP API
```

Reasons:

- Lower cost
- Lower latency
- Simpler configuration
- Native JWT support

I would choose REST API only if I require:

- API Keys
- Usage Plans
- Request validation
- Advanced request/response transformations

---

# Scenario 17

## How would you troubleshoot increasing latency over the last week?

### Answer

I would compare:

- Current CloudWatch metrics
- Historical metrics
- X-Ray traces
- Recent deployments
- Database performance
- External dependencies

Trend analysis is often more useful than examining a single request.

---

# Scenario 18

## How would you convince your team to use API Gateway instead of exposing ECS directly?

### Answer

I would explain that API Gateway provides:

- Authentication
- Authorization
- Rate limiting
- API versioning
- Monitoring
- Logging
- Request validation

These capabilities would otherwise need to be implemented separately.

---

# Rapid Fire Scenarios

- API works locally but not in production.
- JWT suddenly becomes invalid.
- CloudWatch shows increasing latency.
- Only one endpoint is slow.
- Customers receive intermittent 502 errors.
- Database CPU reaches 100%.
- CloudFront serves stale responses.
- API deployment succeeds but users see old data.
- One tenant receives another tenant's data.
- Partner API starts failing after certificate rotation.

---

# Senior Interview Tips

For scenario-based interviews:

Do not immediately jump to the solution.

Explain:

1. How you would gather information.
2. Which AWS services you would inspect.
3. How you would isolate the problem.
4. The trade-offs of different solutions.
5. How you would prevent the issue from recurring.

This demonstrates operational maturity rather than memorized AWS knowledge.

---

# Key Takeaways

- Scenario-based interviews evaluate production thinking, not memorization.
- Begin with observation and diagnosis before proposing changes.
- CloudWatch, AWS X-Ray, backend logs, and metrics are the primary tools for troubleshooting.
- Strong answers explain both the investigation process and the reasoning behind architectural decisions.
- Senior engineers are expected to balance scalability, security, performance, cost, and operational reliability when solving real-world problems.