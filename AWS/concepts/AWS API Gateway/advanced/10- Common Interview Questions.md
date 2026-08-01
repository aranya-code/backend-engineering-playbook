# Common Interview Questions

## Overview

This chapter consolidates the most frequently asked Amazon API Gateway interview questions for **Senior Backend Developers**, **Cloud Engineers**, **AWS Solution Architects**, and **Platform Engineers**.

Rather than testing memorization, these questions evaluate your understanding of:

- API Gateway architecture
- Security
- Performance
- Scalability
- High Availability
- Networking
- Observability
- Production Operations
- AWS integrations

Many companies also ask scenario-based questions to evaluate architectural decision-making.

---

# API Gateway Fundamentals

### What is Amazon API Gateway?

Amazon API Gateway is a fully managed service that enables developers to create, publish, secure, monitor, and manage APIs at any scale.

It acts as the entry point between clients and backend services such as:

- AWS Lambda
- Amazon ECS
- Amazon EC2
- AWS Services
- Private services inside a VPC

---

### Why use API Gateway instead of exposing a Lambda Function URL?

API Gateway provides many production features that Lambda Function URLs do not.

These include:

- Authentication
- Authorization
- API Keys
- Usage Plans
- Throttling
- Caching
- Request Validation
- Monitoring
- Custom Domains
- WAF Integration

Lambda Function URLs are suitable only for simple use cases.

---

### What are the three API Gateway API types?

- REST API
- HTTP API
- WebSocket API

---

### When would you choose HTTP API over REST API?

Choose HTTP API when:

- Lower cost is important
- Lower latency is required
- JWT authentication is sufficient
- Advanced REST API features are unnecessary

---

### When would you choose REST API?

Choose REST API when you require:

- API Keys
- Usage Plans
- Request Validation
- API Caching
- Canary Deployments
- Advanced Mapping Templates

---

# Security

### How does API Gateway authenticate users?

Authentication options include:

- IAM
- Amazon Cognito
- JWT Authorizers
- Lambda Authorizers
- Mutual TLS

---

### What is the difference between Authentication and Authorization?

Authentication verifies:

```text
Who are you?
```

Authorization verifies:

```text
What are you allowed to do?
```

---

### What is a Resource Policy?

A Resource Policy controls which AWS accounts, VPCs, IP addresses, or VPC Endpoints can invoke an API.

---

### When would you use Mutual TLS?

Mutual TLS is used when both the client and server must authenticate each other using X.509 certificates.

Common use cases include:

- Banking
- Government
- Healthcare
- B2B integrations

---

# Performance

### What is API Gateway Caching?

API Gateway stores responses in memory so repeated requests can be served without invoking backend services.

Benefits:

- Lower latency
- Reduced backend load
- Lower costs

---

### What is the difference between Latency and Integration Latency?

Latency:

```text
Entire Request
```

Integration Latency:

```text
Backend Processing Only
```

---

### Why is Compression useful?

Compression reduces payload size using Gzip.

Benefits:

- Lower bandwidth usage
- Faster responses
- Better mobile performance

---

# Architecture

### Why is API Gateway considered a Facade?

Because it hides multiple backend services behind a single public API.

Clients communicate with:

```text
API Gateway
```

instead of individual services.

---

### How does API Gateway fit into a Microservices Architecture?

```text
Client

↓

API Gateway

↓

Microservices
```

API Gateway centralizes:

- Authentication
- Authorization
- Routing
- Monitoring
- Rate limiting

---

### What is Backend for Frontend (BFF)?

A Backend for Frontend is a dedicated API layer designed for a specific client application.

Example:

```text
Mobile

↓

Mobile BFF

-----------------

Web

↓

Web BFF
```

Each frontend receives APIs optimized for its needs.

---

# Networking

### What is a Private API?

A Private API is accessible only through Interface VPC Endpoints using AWS PrivateLink.

It cannot be accessed from the public internet.

---

### What is VPC Link?

VPC Link allows API Gateway to communicate securely with private resources inside a VPC, such as internal Application Load Balancers or Network Load Balancers.

---

### Regional API vs Edge-Optimized API?

Regional API:

- Best for applications within a Region.

Edge-Optimized API:

- Uses CloudFront.
- Best for global users.

---

# Scaling

### Does API Gateway automatically scale?

Yes.

API Gateway automatically scales without provisioning servers.

---

### What usually becomes the bottleneck?

Usually:

- Lambda concurrency
- Database connections
- Third-party APIs

not API Gateway itself.

---

### How do you protect backend services?

Use:

- Throttling
- API Caching
- CloudFront
- Rate limiting
- SQS
- Auto Scaling

---

# Observability

### Which AWS services are used to monitor API Gateway?

- CloudWatch Metrics
- CloudWatch Logs
- Access Logs
- AWS X-Ray

---

### What is the difference between Metrics and Logs?

Metrics show:

```text
What happened
```

Logs explain:

```text
Why it happened
```

---

### What is AWS X-Ray?

AWS X-Ray provides distributed tracing across multiple AWS services, helping identify latency bottlenecks and failures.

---

# Request Processing

### Explain the API Gateway request lifecycle.

A request typically flows through:

```text
DNS

↓

TLS

↓

Authentication

↓

Authorization

↓

Validation

↓

API Keys

↓

Throttling

↓

Cache

↓

Request Transformation

↓

Backend

↓

Response Transformation

↓

Compression

↓

Client
```

---

### When does Request Validation occur?

Before the backend is invoked.

Invalid requests are rejected immediately.

---

### When is the cache checked?

After security and validation, but before backend invocation.

---

# Production

### What makes an API production-ready?

A production API should include:

- HTTPS
- Authentication
- Authorization
- Validation
- Throttling
- Monitoring
- Logging
- Caching
- CI/CD
- Versioning
- Disaster Recovery

---

### How would you deploy a new API version safely?

Use:

- Canary Deployments
- Monitoring
- CloudWatch Alarms

Gradually increase traffic before a full rollout.

---

### How would you reduce API costs?

- Use HTTP APIs when appropriate.
- Enable API Gateway Cache.
- Compress responses.
- Use CloudFront.
- Optimize Lambda execution.
- Configure CloudWatch log retention.

---

# Scenario-Based Questions

### Scenario 1

Users report:

```text
Slow API
```

How would you investigate?

Expected approach:

1. Check CloudWatch Metrics.
2. Compare Latency vs Integration Latency.
3. Review CloudWatch Logs.
4. Inspect X-Ray traces.
5. Identify backend bottlenecks.

---

### Scenario 2

Your API suddenly returns:

```http
429
```

What happened?

Likely causes:

- Throttling
- Rate limits exceeded
- Traffic spike

Investigate:

- Request Count
- ThrottleCount
- Usage Plans

---

### Scenario 3

Your Lambda scales correctly, but requests are still slow.

Possible causes:

- Database bottleneck
- Third-party API
- Network latency
- Connection exhaustion

---

### Scenario 4

How would you expose an internal API?

Recommended architecture:

```text
Private API

↓

PrivateLink

↓

VPC Endpoint

↓

Internal Services
```

---

### Scenario 5

How would you build a global API?

Example architecture:

```text
Route 53

↓

Multiple Regions

↓

API Gateway

↓

Regional Backends
```

Use:

- Multi-Region deployment
- Route 53
- DynamoDB Global Tables
- Aurora Global Database

---

# Frequently Asked Senior-Level Questions

### REST API vs HTTP API?

Know:

- Features
- Cost
- Performance
- Limitations

---

### Why use API Gateway instead of an ALB?

API Gateway provides:

- Authentication
- Authorization
- Usage Plans
- API Keys
- Request Validation
- Mapping Templates
- API Management

Application Load Balancer focuses primarily on Layer 7 load balancing.

---

### How would you secure an enterprise API?

Typical answer:

```text
AWS WAF

↓

API Gateway

↓

JWT

↓

IAM

↓

Resource Policies

↓

Private APIs

↓

CloudWatch Monitoring
```

---

### How would you improve API performance?

Discuss:

- Caching
- Compression
- CloudFront
- Optimized Lambda
- Efficient databases
- Pagination
- Batch operations

---

### What would your production architecture look like?

```text
Route 53

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

Lambda

↓

DynamoDB

↓

CloudWatch

↓

X-Ray
```

Explain why every component exists.

---

# Final Interview Tips

During interviews:

- Explain architectural trade-offs instead of listing AWS services.
- Discuss why one API type is chosen over another.
- Mention security, monitoring, and scalability together.
- Use real production examples whenever possible.
- Focus on designing reliable, maintainable, and cost-effective systems rather than simply making APIs work.

---

# Key Takeaways

- Senior API Gateway interviews emphasize architectural thinking rather than memorization.
- Be comfortable discussing API Gateway security, networking, observability, scaling, performance, and production operations.
- Understand the complete request lifecycle and how API Gateway integrates with Lambda, ECS, VPCs, CloudWatch, X-Ray, Route 53, WAF, and CloudFront.
- Be prepared for scenario-based questions involving latency, throttling, high availability, disaster recovery, and cost optimization.
- Strong answers explain not only **how** a feature works but also **when**, **why**, and **what trade-offs** it introduces.