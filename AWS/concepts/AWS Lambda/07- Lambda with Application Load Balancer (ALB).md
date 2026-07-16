# 07- Lambda with Application Load Balancer (ALB)

# Lambda with Application Load Balancer (ALB)

Although API Gateway is the most popular way to expose Lambda functions over HTTP, AWS also allows an **Application Load Balancer (ALB)** to invoke Lambda functions directly.

This enables serverless architectures to integrate seamlessly with existing load-balanced environments and supports scenarios where traditional applications and Lambda functions coexist.

Unlike API Gateway, ALB is primarily a Layer 7 load balancer and is often already deployed in enterprises running ECS, EKS, or EC2 workloads.

---

# Why Use ALB with Lambda?

Instead of deploying another web server behind the ALB, AWS allows Lambda functions to act as ALB targets.

Traditional architecture:

```text
Internet

↓

ALB

↓

EC2

↓

Application
```

Serverless architecture:

```text
Internet

↓

ALB

↓

Lambda
```

Hybrid architecture:

```text
Internet

↓

Application Load Balancer

        │

 ┌──────┴──────────┐

 │                 │

 ▼                 ▼

EC2             Lambda
```

This allows gradual migration from monolithic applications to serverless microservices.

---

# How ALB Invokes Lambda

Request flow:

```text
Client

↓

HTTPS Request

↓

Application Load Balancer

↓

Target Group

↓

Lambda Function

↓

Response

↓

Client
```

Unlike API Gateway, the ALB forwards requests using **Lambda Target Groups**.

---

# Lambda Target Groups

Normally ALB forwards traffic to:

- EC2
- ECS Tasks
- IP Addresses

With Lambda:

```text
ALB

↓

Lambda Target Group

↓

Lambda Function
```

A Lambda function must be registered as a target in the target group.

---

# Request Flow

Example:

```
GET /products/100
```

Flow:

```text
Browser

↓

ALB

↓

Target Group

↓

Lambda

↓

Database

↓

Lambda

↓

ALB

↓

Browser
```

---

# ALB Event Structure

ALB converts the HTTP request into a JSON event.

Example:

```json
{
  "httpMethod": "GET",
  "path": "/products/100",
  "queryStringParameters": {
      "page":"1"
  },
  "headers": {
      "host":"example.com"
  },
  "body":"",
  "isBase64Encoded":false
}
```

Notice that the structure is similar—but **not identical**—to API Gateway events.

Always write handlers based on the event format of the trigger.

---

# Lambda Example

```python
import json

def handler(event, context):

    return {

        "statusCode":200,

        "statusDescription":"200 OK",

        "isBase64Encoded":False,

        "headers":{

            "Content-Type":"application/json"

        },

        "body":json.dumps({

            "message":"Hello from Lambda"

        })
    }
```

---

# Response Format

ALB requires:

```python
{
    "statusCode":200,
    "statusDescription":"200 OK",
    "headers":{},
    "body":"..."
}
```

Notice:

```
statusDescription
```

is expected for ALB integrations.

---

# HTTP Methods

Supported:

```
GET
POST
PUT
PATCH
DELETE
OPTIONS
HEAD
```

Exactly like a normal HTTP application.

---

# Path Routing

ALB listener rules determine which Lambda function receives a request.

Example:

```
/users/*
```

↓

Lambda A

```
/orders/*
```

↓

Lambda B

```
/payments/*
```

↓

Lambda C

Architecture:

```text
ALB

│

├── /users/*

│      ↓

│   Lambda A

│

├── /orders/*

│      ↓

│   Lambda B

│

└── /payments/*

       ↓

   Lambda C
```

---

# Host-Based Routing

Example:

```
api.company.com

↓

Lambda A
```

```
admin.company.com

↓

Lambda B
```

Useful for microservices.

---

# HTTPS Support

ALB supports:

- HTTPS
- TLS termination
- ACM certificates

Architecture:

```text
Internet

↓

HTTPS

↓

ALB

↓

HTTP

↓

Lambda
```

The Lambda function never manages SSL certificates.

---

# Authentication

Unlike API Gateway, ALB has fewer built-in authentication features.

Common options include:

- OIDC
- Cognito Authentication
- Application-level JWT validation

For advanced API authentication, API Gateway generally offers more features.

---

# Health Checks

Unlike EC2 targets, Lambda functions do not require traditional health checks.

AWS automatically manages Lambda availability.

---

# Scaling

```text
10 Requests

↓

ALB

↓

10 Lambda Invocations
```

Later:

```text
20,000 Requests

↓

ALB

↓

Thousands of Lambda Invocations
```

Scaling is automatic.

---

# Logging

ALB logs:

- Request path
- Status code
- Client IP
- Target response time

Lambda logs:

```python
print(event)
```

↓

CloudWatch Logs

---

# Monitoring

Monitor:

- Target response time
- HTTP 4XX
- HTTP 5XX
- Lambda Duration
- Lambda Errors
- Lambda Throttles
- Request Count

---

# ALB vs API Gateway

| Feature | ALB | API Gateway |
|----------|-----|-------------|
| HTTP APIs | ✅ | ✅ |
| REST Features | Basic | Excellent |
| WebSockets | ❌ | ✅ |
| API Keys | ❌ | ✅ |
| Usage Plans | ❌ | ✅ |
| Request Validation | ❌ | ✅ |
| JWT Authorizers | Limited | ✅ |
| Lambda Authorizers | ❌ | ✅ |
| Caching | ❌ | ✅ |
| Cost for Large Traffic | Lower | Higher |
| Existing Load Balancer Integration | Excellent | Limited |

---

# When to Choose ALB

Choose ALB when:

- Existing applications already use ALB.
- Migrating gradually from EC2/ECS to Lambda.
- Routing requests to both EC2 and Lambda.
- Cost optimization is important for very high HTTP traffic.
- Advanced API management is unnecessary.

---

# When to Choose API Gateway

Choose API Gateway when:

- Building public REST APIs.
- Using OAuth/JWT authentication.
- Need API Keys.
- Need Usage Plans.
- Need Request Validation.
- Need WebSocket APIs.
- Need API versioning and lifecycle management.

---

# Production Architecture

```text
Internet

↓

Route53

↓

CloudFront

↓

AWS WAF

↓

Application Load Balancer

      │

 ┌────┴─────────┐

 │              │

 ▼              ▼

Lambda       ECS Cluster

                 │

              PostgreSQL
```

This hybrid architecture is common during cloud modernization projects.

---

# Common Mistakes

## Assuming ALB and API Gateway Events Are Identical

Although similar, their JSON structures differ.

Always inspect the incoming event before parsing it.

---

## Using ALB for Public API Management

ALB lacks:

- Usage plans
- API keys
- Request validation
- Native authorizers

If these are required, API Gateway is a better choice.

---

## Ignoring Listener Rules

Well-designed listener rules reduce routing complexity and allow different services to evolve independently.

---

# Best Practices

✅ Use ALB when integrating Lambda into existing load-balanced environments.

✅ Keep Lambda functions stateless.

✅ Configure listener rules carefully.

✅ Use ACM certificates for HTTPS.

✅ Enable ALB access logs.

✅ Monitor Lambda and ALB metrics together.

---

# Senior Backend Engineering Perspective

Application Load Balancer provides an excellent bridge between traditional infrastructure and serverless architectures. In many enterprises, it enables **incremental migration** by allowing EC2, ECS, and Lambda to coexist behind a single endpoint.

For modern public APIs, API Gateway remains the preferred option because of its rich API management capabilities. However, for internal services, hybrid environments, or cost-sensitive HTTP workloads, ALB with Lambda offers a lightweight and highly scalable alternative.

Choosing between API Gateway and ALB should be based on **functional requirements, operational complexity, authentication needs, and traffic patterns**, not simply on familiarity.

---

# Interview Questions

### Beginner

- Can ALB invoke Lambda?
- How does ALB communicate with Lambda?
- What is a Lambda Target Group?

### Intermediate

- How does ALB differ from API Gateway?
- Can ALB route traffic to both EC2 and Lambda?
- What response format does ALB expect?

### Senior

- When would you choose ALB instead of API Gateway?
- How would you migrate an EC2 application to Lambda using ALB?
- How would you design a hybrid architecture with ECS and Lambda behind the same load balancer?
- What are the operational trade-offs between ALB and API Gateway?

---

# Key Takeaways

- ALB can invoke Lambda functions through Lambda Target Groups.
- It is ideal for hybrid architectures where EC2, ECS, and Lambda coexist.
- ALB offers lower-cost HTTP routing but lacks many advanced API management features provided by API Gateway.
- The Lambda event and response format differ slightly from API Gateway integrations.
- Selecting ALB or API Gateway depends on workload characteristics, security requirements, API management needs, and existing infrastructure.