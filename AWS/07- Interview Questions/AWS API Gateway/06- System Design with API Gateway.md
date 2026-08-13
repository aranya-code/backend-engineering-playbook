# System Design with API Gateway

## Overview

Senior Backend and Solutions Architect interviews often include a system design round where API Gateway serves as the entry point to the entire architecture.

The interviewer is no longer evaluating whether you know API Gateway features—they want to understand whether you can build systems that are:

- Highly Available
- Scalable
- Secure
- Fault Tolerant
- Cost Efficient
- Observable
- Easy to Operate

This chapter discusses common system design questions involving Amazon API Gateway and the architectural trade-offs behind them.

---

# Question 1

## Design an E-commerce Platform

### Requirements

- Millions of users
- Product catalog
- Shopping cart
- Orders
- Payments
- Authentication

---

## Architecture

```text
                Users

                  │

                  ▼

            Amazon CloudFront

                  │

                  ▼

               AWS WAF

                  │

                  ▼

            API Gateway (HTTP)

      ┌────────┼────────┬────────┐
      ▼        ▼        ▼        ▼

 Products   Orders   Payments   Users
 Service    Service   Service   Service

      │        │         │         │

      ▼        ▼         ▼         ▼

 Aurora    Aurora     SQS      Cognito
            Redis
```

---

### Why API Gateway?

API Gateway provides:

- Single Entry Point
- Authentication
- Authorization
- Monitoring
- Rate Limiting
- API Versioning

---

### Follow-up

Why split services?

Because each service:

- Scales independently
- Deploys independently
- Owns its database

---

# Question 2

## Design a Ride Sharing Platform

### Architecture

```text
Mobile Apps

↓

CloudFront

↓

API Gateway

↓

Ride Service

Driver Service

Location Service

Payment Service

↓

Redis

↓

Aurora
```

---

### Design Decisions

Use:

Redis

for

- Driver locations
- Frequently accessed data

Use:

SQS

for

- Ride notifications
- Emails
- Billing

---

# Question 3

## Design a Banking API

### Requirements

- Very high security
- Low latency
- Audit logging
- MFA
- Encryption

---

## Architecture

```text
Users

↓

CloudFront

↓

AWS Shield

↓

AWS WAF

↓

API Gateway

↓

mTLS

↓

JWT

↓

Lambda

↓

Aurora
```

---

### Security Layers

- HTTPS
- WAF
- JWT
- mTLS
- IAM
- CloudTrail
- CloudWatch

---

### Why mTLS?

Both client and server authenticate each other.

Useful for:

- Banks
- Healthcare
- Enterprise

---

# Question 4

## Design a Public SaaS Platform

### Architecture

```text
Customers

↓

CloudFront

↓

API Gateway

↓

JWT

↓

Tenant Resolver

↓

Microservices

↓

Tenant Database
```

---

### Multi-tenancy

Every request contains:

```text
Tenant ID
```

Tenant isolation happens before business logic.

---

### Benefits

- Single platform
- Multiple customers
- Better scalability

---

# Question 5

## Design a Global API

### Requirements

Users from:

- US
- Europe
- Asia

---

## Architecture

```text
Users

↓

Route53

↓

CloudFront

↓

Regional API Gateway

↓

Lambda

↓

DynamoDB Global Tables
```

---

### Benefits

- Low latency

- High availability

- Regional failover

---

# Question 6

## Design a Video Processing API

### Requirements

Videos require several minutes.

---

### Wrong Design

```text
Client

↓

API Gateway

↓

Lambda

↓

Video Processing
```

Timeout.

---

### Better Design

```text
Client

↓

API Gateway

↓

Lambda

↓

SQS

↓

Workers

↓

S3
```

Return:

```http
202 Accepted
```

Client checks status later.

---

# Question 7

## Design a Notification System

### Architecture

```text
Client

↓

API Gateway

↓

Lambda

↓

SNS

↓

SQS

↓

Workers
```

Notifications:

- Email
- SMS
- Push
- Webhooks

---

### Why SNS?

One message.

Multiple subscribers.

---

# Question 8

## Design a High-Traffic Read API

### Requirements

Millions of reads.

Few writes.

---

### Architecture

```text
Users

↓

CloudFront

↓

API Gateway

↓

Cache

↓

Redis

↓

Database
```

---

### Optimization

- API Gateway Cache

- Redis

- CloudFront

- Read Replicas

---

# Question 9

## Design a Partner API

### Requirements

Only trusted companies.

---

### Architecture

```text
Partners

↓

CloudFront

↓

WAF

↓

API Gateway

↓

JWT

↓

API Key

↓

Usage Plan

↓

Backend
```

---

### Why combine JWT and API Keys?

JWT

↓

User Identity

API Key

↓

Application Identity

Usage Plan

↓

Traffic Control

---

# Question 10

## Design an Internal Enterprise API

### Architecture

```text
Employees

↓

Private API Gateway

↓

Interface Endpoint

↓

VPC Link

↓

ALB

↓

ECS
```

---

### Benefits

- No Internet

- Internal networking

- Better security

---

# Question 11

## How would you version APIs?

### Preferred

```text
/v1/orders

/v2/orders
```

Avoid:

```text
orders_new
```

---

### Migration

```text
v1

↓

v2

↓

Deprecate

↓

Remove
```

---

# Question 12

## How would you monitor the system?

### Monitor

CloudWatch Metrics

↓

CloudWatch Logs

↓

X-Ray

↓

CloudTrail

↓

CloudWatch Alarms

---

### Metrics

- Latency
- 4XX
- 5XX
- IntegrationLatency
- Throttling

---

# Question 13

## How would you reduce operational cost?

### Possible optimizations

- CloudFront

- API Cache

- Redis

- Compression

- HTTP APIs

- Smaller Lambda packages

- Reserved Capacity where appropriate

Measure before optimizing.

---

# Question 14

## How would you make this architecture highly available?

### Answer

```text
Route53

↓

CloudFront

↓

Regional API Gateway

↓

Multi-AZ Backend

↓

Multi-AZ Database

↓

Backups
```

---

### Additional Improvements

- Health Checks

- Auto Scaling

- Disaster Recovery

- Infrastructure as Code

---

# Question 15

## Which architecture would you choose?

### API Gateway + Lambda

Choose for:

- Serverless
- Event-driven
- Small services
- Fast development

---

### API Gateway + ECS

Choose for:

- Containers
- Heavy workloads
- Long-running APIs
- Existing Docker ecosystem

---

### API Gateway + ALB

Choose when:

- Existing container platform
- Multiple services
- Kubernetes/ECS

---

# Architecture Comparison

| Requirement | Recommended Architecture |
|-------------|--------------------------|
| Serverless | API Gateway + Lambda |
| Containers | API Gateway + ECS |
| Enterprise | API Gateway + ALB + ECS |
| Internal APIs | Private API Gateway |
| Global Users | CloudFront + Regional APIs |
| Multi-tenant SaaS | API Gateway + JWT |
| Async Processing | API Gateway + SQS |
| Event-driven | API Gateway + SNS/SQS |

---

# Common Follow-up Questions

### Why not expose Lambda directly?

API Gateway provides:

- Authentication
- Authorization
- Rate Limiting
- Logging
- Monitoring
- Versioning
- Custom Domains

Without API Gateway, these features must be implemented elsewhere.

---

### Why not expose ECS directly?

Using API Gateway centralizes:

- Authentication
- API lifecycle
- Monitoring
- Security

instead of duplicating them across services.

---

### Where does API Gateway fit in System Design?

API Gateway sits at the edge of the system.

```text
Users

↓

CloudFront

↓

API Gateway

↓

Business Services

↓

Data Layer
```

It should remain focused on:

- Routing
- Authentication
- Authorization
- Traffic management

Business logic belongs in backend services.

---

# Senior Interview Tips

In system design interviews, avoid explaining AWS services one by one.

Instead, discuss:

- Functional requirements
- Non-functional requirements
- Scalability
- Security
- High availability
- Failure handling
- Cost optimization
- Monitoring
- Trade-offs

A strong answer explains **why the architecture is appropriate** rather than simply drawing a diagram.

---

# Key Takeaways

- API Gateway is the edge component that manages client communication with backend services.
- Production architectures combine API Gateway with services such as CloudFront, WAF, Lambda, ECS, Cognito, SQS, SNS, and managed databases.
- The choice of architecture depends on workload characteristics, operational requirements, scalability goals, and security needs.
- System design interviews emphasize architectural trade-offs, resilience, observability, and operational excellence.
- Strong candidates explain design decisions and justify why a particular architecture best satisfies the stated requirements.