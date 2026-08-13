# API Gateway Fundamentals

## Overview

This chapter covers the most frequently asked **Amazon API Gateway fundamentals** in backend developer interviews.

These questions are commonly asked in interviews for:

- Backend Developer
- Senior Backend Developer
- Python Developer
- Java Developer
- Cloud Engineer
- DevOps Engineer
- AWS Developer
- Solutions Architect

The questions begin with fundamental concepts and gradually move toward production-level discussions.

---

# Basic Interview Questions

## 1. What is Amazon API Gateway?

**Answer**

Amazon API Gateway is a fully managed AWS service that allows developers to create, publish, secure, monitor, and manage APIs at any scale.

It acts as the entry point for backend services such as:

- AWS Lambda
- ECS
- EC2
- Application Load Balancer
- HTTP Services

It provides features including:

- Authentication
- Authorization
- Rate limiting
- Caching
- Monitoring
- Logging
- API Versioning
- Traffic Management

---

## 2. Why do we need API Gateway?

**Answer**

Without API Gateway, clients communicate directly with backend services.

```text
Client

↓

Backend
```

This causes several problems:

- No centralized authentication
- No rate limiting
- No monitoring
- No API versioning
- No request validation
- Difficult scaling

Using API Gateway:

```text
Client

↓

API Gateway

↓

Backend
```

API Gateway becomes the single entry point for all API requests.

---

## 3. What API types does API Gateway support?

**Answer**

Amazon API Gateway supports three API types.

| API Type | Use Case |
|----------|----------|
| REST API | Enterprise APIs with advanced features |
| HTTP API | Modern REST APIs with lower latency and lower cost |
| WebSocket API | Real-time bidirectional communication |

---

## 4. REST API vs HTTP API

**Answer**

| REST API | HTTP API |
|----------|----------|
| Older | Newer |
| More features | Lightweight |
| Supports API Keys | Limited feature set |
| Supports Usage Plans | No Usage Plans |
| Higher cost | Lower cost |
| Higher latency | Lower latency |

**Interview Tip**

Choose HTTP APIs unless you specifically require REST API features like API Keys, Usage Plans, request validation, or advanced transformations.

---

## 5. What is an API Resource?

**Answer**

A resource represents a path.

Example:

```text
/products

/orders

/users
```

Resources form a hierarchical tree.

Example:

```text
/

↓

products

↓

{id}
```

---

## 6. What is an HTTP Method?

**Answer**

Methods define operations on a resource.

Example:

```text
GET /products

POST /products

PUT /products/{id}

DELETE /products/{id}
```

---

## 7. What is an Integration?

**Answer**

An integration defines where API Gateway forwards requests.

Examples:

- Lambda
- ECS
- ALB
- EC2
- HTTP Service
- Mock Integration

---

## 8. What is Lambda Proxy Integration?

**Answer**

Lambda Proxy Integration forwards the complete HTTP request directly to Lambda.

Lambda receives:

- Headers
- Query Parameters
- Body
- Path Parameters
- Request Context

Lambda returns:

```json
{
    "statusCode":200,
    "body":"..."
}
```

This is the recommended integration for most serverless applications.

---

## 9. What is a Stage?

**Answer**

A Stage represents an environment.

Examples:

```text
dev

test

staging

production
```

Each stage points to a deployment.

---

## 10. What is a Deployment?

**Answer**

A deployment is an immutable snapshot of an API configuration.

Flow:

```text
API

↓

Deployment

↓

Stage
```

REST APIs require a new deployment before changes become visible.

---

## 11. What are Stage Variables?

**Answer**

Stage Variables store configuration values for a specific stage.

Example:

Development:

```text
backend=dev
```

Production:

```text
backend=prod
```

They allow the same API configuration to behave differently across environments.

---

## 12. What is an Authorizer?

**Answer**

An Authorizer determines whether a request is allowed before it reaches the backend.

Supported authorizers include:

- IAM
- Cognito
- JWT
- Lambda Authorizer

---

## 13. JWT Authorizer vs Lambda Authorizer

**JWT Authorizer**

- Faster
- Native validation
- No Lambda execution
- Lower cost

**Lambda Authorizer**

- Custom logic
- External identity providers
- More flexible
- Higher latency

---

## 14. What is an API Key?

**Answer**

An API Key identifies a client application.

It is used for:

- Usage tracking
- Quotas
- Rate limiting

It is **not** an authentication mechanism.

---

## 15. What is a Usage Plan?

**Answer**

A Usage Plan controls:

- Requests per second
- Burst requests
- Monthly or daily quotas

Different plans can be assigned to different API consumers.

---

## 16. What is Throttling?

**Answer**

Throttling protects backend services from excessive traffic.

Example:

```text
Rate Limit

↓

100 Requests/Second
```

If exceeded:

```http
429 Too Many Requests
```

---

## 17. What is API Gateway Caching?

**Answer**

API Gateway can cache responses to reduce backend load.

Benefits:

- Lower latency
- Reduced backend traffic
- Lower Lambda invocations
- Cost savings

Suitable for read-heavy APIs.

---

## 18. What is CORS?

**Answer**

Cross-Origin Resource Sharing (CORS) allows browsers to access APIs hosted on different origins.

Example:

Frontend:

```text
https://app.company.com
```

Backend:

```text
https://api.company.com
```

Without proper CORS headers, browsers block the request.

---

## 19. What Monitoring Features Does API Gateway Provide?

**Answer**

API Gateway integrates with:

- CloudWatch Logs
- CloudWatch Metrics
- AWS X-Ray
- CloudTrail

Common metrics include:

- Latency
- IntegrationLatency
- 4XXError
- 5XXError
- Count

---

## 20. What Endpoint Types Are Available?

**Answer**

REST APIs support:

- Edge Optimized
- Regional
- Private

---

### Edge Optimized

Uses CloudFront automatically.

Best for:

Global users.

---

### Regional

Traffic stays within one AWS Region.

Best for:

Regional applications.

---

### Private

Accessible only inside a VPC through Interface Endpoints.

Best for:

Internal enterprise APIs.

---

## 21. What is VPC Link?

**Answer**

VPC Link allows API Gateway to privately communicate with resources inside a VPC, such as:

- Application Load Balancers
- Network Load Balancers

without exposing backend services to the public internet.

---

## 22. What is the difference between Authentication and Authorization?

**Authentication**

Verifies:

```text
Who are you?
```

**Authorization**

Determines:

```text
What are you allowed to do?
```

---

## 23. What causes 502 Bad Gateway?

**Answer**

Usually one of:

- Invalid Lambda response
- Backend unavailable
- Incorrect integration
- ALB failure

---

## 24. What causes 504 Gateway Timeout?

**Answer**

The backend did not respond within the allowed integration timeout.

Common causes:

- Slow database
- Slow Lambda
- External APIs
- Long-running processing

---

## 25. What AWS services commonly integrate with API Gateway?

Examples:

- AWS Lambda
- Amazon ECS
- EC2
- ALB
- Cognito
- CloudFront
- Route 53
- AWS WAF
- DynamoDB
- SQS
- SNS
- Step Functions

---

# Rapid Fire Interview Questions

- REST API vs HTTP API?
- What is a Stage?
- What is a Deployment?
- What is Integration Latency?
- What is Lambda Proxy Integration?
- What is VPC Link?
- What is API Caching?
- What is CORS?
- What is JWT Authorizer?
- What is Usage Plan?
- What is an API Key?
- Difference between 401 and 403?
- Difference between 502 and 504?
- Difference between Latency and IntegrationLatency?
- What causes 429 Too Many Requests?
- Why use CloudWatch?
- Why use X-Ray?
- What are Stage Variables?
- Why use Private APIs?
- Why use CloudFront with API Gateway?

---

# Senior Interview Tips

Interviewers rarely stop after a definition. They usually ask **"Why?"** or **"When would you choose this?"**

For example:

**Question**

"What is the difference between REST API and HTTP API?"

**Weak Answer**

"HTTP APIs are cheaper."

**Strong Answer**

"I generally choose HTTP APIs for modern microservices because they provide lower latency, lower cost, and built-in JWT authorization. I only choose REST APIs when I need advanced capabilities such as API Keys, Usage Plans, request validation, or request/response transformations."

This demonstrates practical decision-making rather than memorization.

---

# Key Takeaways

- Amazon API Gateway is the managed entry point for backend services in AWS.
- Understanding core concepts such as resources, methods, integrations, deployments, stages, and authorizers is essential for backend interviews.
- HTTP APIs are preferred for most modern workloads, while REST APIs remain valuable for advanced enterprise features.
- Security, traffic management, monitoring, and observability are fundamental responsibilities of API Gateway.
- Strong interview answers explain not only **what** a feature is, but also **when** and **why** it should be used in production.