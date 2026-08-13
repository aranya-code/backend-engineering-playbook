# API Gateway Integrations

API Gateway integrations define **how Amazon API Gateway communicates with backend services**. They determine where requests are sent, whether request and response transformations occur, and how backend services process incoming requests.

This section covers every major integration type supported by Amazon API Gateway, from modern serverless architectures using AWS Lambda to direct integrations with AWS services and existing HTTP applications.

The goal is to help you understand **when to use each integration**, their trade-offs, and how they fit into real-world production architectures.

---

# Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Integration Types Overview](./01-%20Integration%20Types%20Overview.md) | Learn the different API Gateway integration types, their architecture, and when to choose each one. |
| [02 - Lambda Proxy Integration](./02-%20Lambda%20Proxy%20Integration.md) | Understand the recommended integration for modern serverless applications and how API Gateway forwards requests directly to Lambda. |
| [03 - Lambda Non-Proxy Integration](./03-%20Lambda%20Non-Proxy%20Integration.md) | Learn how Mapping Templates transform requests and responses before communicating with Lambda functions. |
| [04 - HTTP Proxy Integration](./04-%20HTTP%20Proxy%20Integration.md) | Explore how API Gateway acts as a reverse proxy for existing HTTP services such as FastAPI, Django, Spring Boot, and Express.js. |
| [05 - HTTP Custom Integration](./05-%20HTTP%20Custom%20Integration.md) | Learn how to transform requests and responses when integrating with HTTP backends using Mapping Templates (VTL). |
| [06 - AWS Service Integrations](./06-%20AWS%20Service%20Integrations.md) | Learn how API Gateway communicates directly with AWS services such as SQS, SNS, Step Functions, DynamoDB, EventBridge, and Kinesis without using Lambda. |
| [07 - Mock Integrations](./07-%20Mock%20Integrations.md) | Understand how Mock Integrations are used for API prototyping, frontend development, testing, and static responses without any backend service. |
| [08 - Mapping Templates (VTL)](./08-%20Mapping%20Templates%20(VTL).md) | Learn how Velocity Template Language (VTL) transforms requests and responses, supports legacy systems, and enables payload customization. |

---

# Learning Path

```text
Integration Types

        │

        ▼

Lambda Proxy

        │

        ▼

Lambda Non-Proxy

        │

        ▼

HTTP Proxy

        │

        ▼

HTTP Custom

        │

        ▼

AWS Service Integrations

        │

        ▼

Mock Integrations

        │

        ▼

Mapping Templates (VTL)
```

The chapters progress from simple proxy integrations to advanced request and response transformation techniques.

---

# Prerequisites

Before studying API Gateway integrations, you should understand:

- API Gateway fundamentals
- REST APIs
- HTTP request/response lifecycle
- AWS Lambda basics
- Basic IAM concepts
- JSON
- HTTP methods and status codes

---

# What You'll Learn

After completing this section, you will understand:

- The different API Gateway integration types
- How Lambda Proxy Integration works
- When Lambda Non-Proxy Integration is appropriate
- How HTTP Proxy Integration exposes existing REST APIs
- How HTTP Custom Integration transforms payloads
- Direct integration with AWS services
- How Mock Integrations simplify testing and frontend development
- Request and response transformation using Mapping Templates (VTL)
- Best practices for selecting the appropriate integration type

---

# Integration Decision Flow

```text
Need AWS Lambda?

        │

        ├────────────── Yes ──────────────┐
        │                                │
        ▼                                ▼
Need Request Mapping?             No Mapping Needed
        │                                │
        ▼                                ▼
Lambda Non-Proxy                Lambda Proxy


Need Existing HTTP Backend?

        │

        ├────────────── Yes ──────────────┐
        │                                │
        ▼                                ▼
Need Request Mapping?             No Mapping Needed
        │                                │
        ▼                                ▼
HTTP Custom                    HTTP Proxy


Need Direct AWS Service?

        │

        ▼

AWS Service Integration


Need Static Responses?

        │

        ▼

Mock Integration
```

This decision tree covers the majority of production API Gateway integration scenarios.

---

# Integration Comparison

| Integration Type | Backend | Mapping Templates | Recommended For |
|------------------|----------|-------------------|-----------------|
| Lambda Proxy | AWS Lambda | ❌ | Modern serverless APIs |
| Lambda Non-Proxy | AWS Lambda | ✅ | Legacy payload transformations |
| HTTP Proxy | HTTP Backend | ❌ | Existing REST services |
| HTTP Custom | HTTP Backend | ✅ | Legacy HTTP integrations |
| AWS Service Integration | AWS Services | Optional | Direct service invocations |
| Mock Integration | None | Optional | Testing and prototyping |

---

# Production Recommendations

For most production systems:

- Use **Lambda Proxy Integration** for serverless applications.
- Use **HTTP Proxy Integration** for existing HTTP services.
- Use **AWS Service Integrations** when Lambda only forwards requests.
- Use **Mock Integrations** during development or for static endpoints.
- Use **Mapping Templates** only when request or response transformation is necessary.

Keeping integrations as simple as possible improves maintainability and reduces operational overhead.

---

# Real-World Architectures

Typical production architectures include:

### Serverless API

```text
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB
```

---

### Container-Based API

```text
Client

↓

API Gateway

↓

Application Load Balancer

↓

Amazon ECS

↓

PostgreSQL
```

---

### Event-Driven API

```text
Client

↓

API Gateway

↓

Amazon SQS

↓

Worker Service
```

---

### Legacy Enterprise API

```text
Client

↓

API Gateway

↓

Mapping Templates

↓

Legacy Java/XML Service
```

---

# Interview Focus

This section prepares you for common Backend Developer and AWS Solution Architect interview topics, including:

- Lambda Proxy vs Lambda Non-Proxy
- HTTP Proxy vs HTTP Custom
- AWS Service Integrations
- Mapping Templates (VTL)
- Mock Integrations
- Request and response transformation
- Integration design decisions
- Cost and performance trade-offs
- Real-world architecture scenarios

---

# Repository Structure

```text
integrations/
│
├── 01- Integration Types Overview.md
├── 02- Lambda Proxy Integration.md
├── 03- Lambda Non-Proxy Integration.md
├── 04- HTTP Proxy Integration.md
├── 05- HTTP Custom Integration.md
├── 06- AWS Service Integrations.md
├── 07- Mock Integrations.md
├── 08- Mapping Templates (VTL).md
└── README.md
```

---

# Best Practices

Throughout this section, you'll learn to:

- Choose the simplest integration that satisfies your requirements.
- Prefer proxy integrations unless transformation is necessary.
- Reduce unnecessary Lambda functions using AWS Service Integrations.
- Keep API Gateway responsible for API management rather than business logic.
- Use Mapping Templates only for payload transformation and legacy compatibility.
- Design integrations that are scalable, maintainable, and cost-effective.