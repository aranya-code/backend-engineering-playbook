# API Gateway Architecture

## Overview

Senior backend interviews frequently move beyond API Gateway features and focus on **architecture**.

Interviewers want to evaluate whether you can:

- Design scalable APIs
- Choose the appropriate API Gateway type
- Integrate multiple AWS services
- Secure APIs
- Design for high availability
- Build cost-efficient architectures

This chapter covers the most common architecture discussions asked during Senior Backend Developer, Solutions Architect, and Cloud Engineer interviews.

---

# Question 1

## Design a Serverless REST API using AWS.

### Answer

Typical architecture:

```text
Client

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
```

### Explanation

CloudFront

- Global caching
- Lower latency

↓

AWS WAF

- DDoS protection
- IP filtering

↓

API Gateway

- Authentication
- Authorization
- Rate limiting

↓

Lambda

- Business logic

↓

DynamoDB

- Persistent storage

↓

CloudWatch

- Monitoring

---

## Follow-up

Why Lambda?

Because:

- No server management
- Auto scaling
- Pay-per-use
- Fast development

---

# Question 2

## Design a Container-based API.

### Answer

```text
Users

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

VPC Link

↓

Application Load Balancer

↓

Amazon ECS

↓

Amazon RDS
```

---

### Why use VPC Link?

API Gateway cannot directly access private ECS services.

VPC Link provides secure connectivity into the VPC.

---

### When would you choose ECS instead of Lambda?

Choose ECS when:

- Long-running processes
- Heavy CPU workloads
- GPU requirements
- Large dependencies
- Stateful workloads

---

# Question 3

## How would you design APIs for microservices?

### Answer

```text
Client

↓

API Gateway

↓

Users Service

Orders Service

Products Service

Payments Service
```

Each microservice owns:

- Database
- Business logic
- Deployment

API Gateway becomes the single entry point.

---

### Benefits

- Independent deployments

- Better scalability

- Fault isolation

- Independent teams

---

# Question 4

## How would you secure an API?

### Answer

```text
Client

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

JWT Authorizer

↓

Lambda

↓

Database
```

Security layers:

- HTTPS
- JWT
- IAM
- WAF
- Rate limiting
- Logging

---

## Follow-up

Why multiple layers?

Defense in Depth.

If one layer fails,

another still protects the application.

---

# Question 5

## How would you build a highly available API?

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

Multiple Regions

↓

Automatic failover

↓

High Availability

---

## AWS Services

- Route 53

- CloudFront

- Regional API Gateway

- DynamoDB Global Tables

---

# Question 6

## Design a Private Enterprise API.

### Answer

```text
Internal Users

↓

Interface VPC Endpoint

↓

Private API Gateway

↓

Lambda

↓

Aurora
```

No public internet exposure.

---

### Benefits

- Higher security

- Internal access only

- Private networking

---

# Question 7

## Design an API for Millions of Requests.

### Answer

```text
Users

↓

CloudFront

↓

API Gateway

↓

Lambda

↓

Redis

↓

Aurora
```

Scaling strategy:

CloudFront

↓

Cache

↓

API Gateway

↓

Auto Scaling

↓

Redis

↓

Database

---

### Optimization

- CDN

- API Caching

- Redis

- Database indexes

- Pagination

- Compression

---

# Question 8

## Design a SaaS API.

### Answer

```text
Customers

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

Access is isolated.

---

# Question 9

## Design an Event-driven API.

### Answer

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

---

### Benefits

- Loose coupling

- Retry support

- Asynchronous processing

- Better scalability

---

# Question 10

## API Gateway with ECS or Lambda?

### Answer

Choose Lambda when:

- Serverless
- Event-driven
- Short execution
- Small workloads

Choose ECS when:

- Containers
- Long-running tasks
- Custom runtimes
- Heavy processing

---

# Question 11

## Why put CloudFront before API Gateway?

### Answer

CloudFront provides:

- Global edge locations
- Lower latency
- Response caching
- DDoS mitigation
- Lower API Gateway requests

---

# Question 12

## Why use WAF with API Gateway?

### Answer

WAF protects against:

- SQL Injection
- Cross-Site Scripting (XSS)
- Bots
- IP attacks
- Rate-based attacks

---

# Question 13

## Why use Cognito instead of a custom login?

### Answer

Advantages:

- Managed authentication

- OAuth

- OpenID Connect

- MFA

- Social Login

- Password Policies

Less code.

More secure.

---

# Question 14

## Why use HTTP APIs instead of REST APIs?

### Answer

Choose HTTP APIs when:

- Lower latency

- Lower cost

- JWT authorization

- Modern microservices

Use REST APIs when you need:

- API Keys

- Usage Plans

- Request validation

- Advanced transformations

---

# Question 15

## How would you monitor this architecture?

### Answer

Use:

- CloudWatch Metrics

- CloudWatch Logs

- AWS X-Ray

- CloudTrail

- CloudWatch Alarms

Monitor:

- Latency

- 4XX Errors

- 5XX Errors

- Integration Latency

- Throttling

---

# Architecture Comparison

| Architecture | Best Choice |
|-------------|-------------|
| Serverless | API Gateway + Lambda |
| Containers | API Gateway + ECS |
| Internal APIs | Private API + VPC Endpoint |
| Enterprise | API Gateway + ALB + ECS |
| Global APIs | CloudFront + Regional API |
| Event-driven | API Gateway + Lambda + SNS/SQS |
| SaaS | API Gateway + JWT + Multi-tenancy |

---

# Common Follow-up Questions

### Why use API Gateway instead of ALB?

Because API Gateway provides:

- Authentication

- Authorization

- Rate limiting

- API Keys

- Request validation

- Monitoring

- API lifecycle management

ALB is primarily a Layer 7 load balancer.

---

### Why shouldn't API Gateway directly connect to a database?

Because:

- Business logic belongs in backend services.

- Security.

- Validation.

- Scalability.

Always introduce:

- Lambda

or

- ECS

between API Gateway and the database.

---

### Would you always choose Lambda?

No.

Lambda is excellent for serverless workloads.

For long-running, CPU-intensive, or containerized applications, ECS or EKS may be a better fit.

---

### Why use CloudFront if API Gateway is already managed?

CloudFront reduces latency by caching responses at edge locations, decreases API Gateway requests, improves global performance, and adds another layer of DDoS protection.

---

### How would you make this architecture production-ready?

I would:

- Add CloudFront
- Protect with AWS WAF
- Enable JWT authentication
- Configure CloudWatch Logs and Metrics
- Enable AWS X-Ray
- Use Infrastructure as Code
- Enable CI/CD
- Configure CloudWatch Alarms
- Implement API throttling
- Add caching where appropriate
- Design for multi-AZ and, if required, multi-Region resilience

---

# Senior Interview Tips

Architecture interviews are rarely about finding a single "correct" answer.

Interviewers evaluate:

- Trade-offs
- Scalability
- Security
- Cost
- Operational complexity
- Failure handling

Always explain **why** you chose a particular architecture instead of simply drawing a diagram.

---

# Key Takeaways

- API Gateway is typically the entry point to modern cloud-native architectures.
- Choosing between Lambda, ECS, and other backend integrations depends on workload characteristics, operational requirements, and cost considerations.
- Production architectures should incorporate CloudFront, WAF, monitoring, authentication, and high availability.
- Enterprise systems benefit from domain-driven microservices, secure networking, and event-driven communication where appropriate.
- Strong architecture interview answers focus on design decisions, trade-offs, and operational considerations rather than only describing AWS services.