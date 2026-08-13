# Amazon API Gateway

Amazon API Gateway is a fully managed AWS service that enables developers to create, publish, secure, monitor, and maintain APIs at any scale. It acts as the **front door** for applications, providing a single entry point for clients while routing requests to backend services such as AWS Lambda, Amazon ECS, EC2, Application Load Balancers, and external HTTP endpoints.

These notes are designed for **Backend Developers**, **Senior Software Engineers**, and **System Design interview preparation**, focusing on production-ready architectures, best practices, real-world use cases, and interview concepts.

---

# Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Introduction to API Gateway](./01-%20Introduction%20to%20API%20Gateway.md) | Learn what Amazon API Gateway is, why it exists, its benefits, supported integrations, and common use cases. |
| [02 - API Gateway Architecture](./02-%20API%20Gateway%20Architecture.md) | Understand API Gateway architecture, request flow, core components, and how it fits into serverless and microservices architectures. |
| [03 - Endpoint Types](./03-%20Endpoint%20Types.md) | Explore Edge-Optimized, Regional, and Private endpoints, their architectures, use cases, and selection criteria. |
| [04 - API Types (REST vs HTTP vs WebSocket)](./04-%20API%20Types.md) | Compare REST APIs, HTTP APIs, and WebSocket APIs, including features, pricing, performance, and when to choose each. |
| [05 - Resources, Methods & Routes](./05-%20Resources,%20Methods%20%26%20Routes.md) | Learn how API Gateway organizes APIs using resources, HTTP methods, routes, and path parameters following REST principles. |
| [06 - Request & Response Lifecycle](./06-%20Request%20%26%20Response%20Lifecycle.md) | Understand the complete lifecycle of an API request, from authentication and validation to backend integration and response handling. |
| [07 - Deployments, Stages & Stage Variables](./07-%20Deployments,%20Stages%20%26%20Stage%20Variables.md) | Learn how deployments work, manage multiple environments using stages, configure stage variables, and implement safe deployment strategies. |

---

# Learning Path

```text
Introduction
      │
      ▼
Architecture
      │
      ▼
Endpoint Types
      │
      ▼
API Types
      │
      ▼
Resources & Methods
      │
      ▼
Request Lifecycle
      │
      ▼
Deployments & Stages
```

This sequence builds a strong conceptual foundation before moving into integrations, security, traffic management, and production features.

---

# Prerequisites

Before studying API Gateway, you should be familiar with:

- Basic HTTP and HTTPS
- REST API fundamentals
- JSON
- AWS IAM basics
- AWS Lambda (recommended)
- Basic networking concepts
- Microservices architecture (recommended)

---

# What You'll Learn

After completing this section, you will understand:

- Why API Gateway is used in modern architectures
- API Gateway architecture and request flow
- Differences between REST, HTTP, and WebSocket APIs
- Endpoint types and their use cases
- Resources, methods, routes, and path parameters
- Complete request and response lifecycle
- Deployments, stages, and stage variables
- Production deployment strategies
- Common interview questions and best practices

---

# Repository Structure

```text
concepts/
│
├── 01- Introduction to API Gateway.md
├── 02- API Gateway Architecture.md
├── 03- Endpoint Types.md
├── 04- API Types.md
├── 05- Resources, Methods & Routes.md
├── 06- Request & Response Lifecycle.md
├── 07- Deployments, Stages & Stage Variables.md
└── README.md
```

---

# Recommended Study Order

Study the chapters in sequence.

1. Introduction to API Gateway
2. API Gateway Architecture
3. Endpoint Types
4. API Types
5. Resources, Methods & Routes
6. Request & Response Lifecycle
7. Deployments, Stages & Stage Variables

Each chapter builds upon the concepts introduced in the previous one.

---

# Best Practices Covered

Throughout this guide, you'll learn how to:

- Design scalable API architectures
- Select the appropriate API type
- Choose the correct endpoint type
- Design RESTful APIs
- Organize resources and routes effectively
- Secure APIs using API Gateway features
- Deploy APIs safely across multiple environments
- Configure stages for development and production
- Follow AWS-recommended architectural patterns

---

# Interview Focus

This section includes concepts frequently discussed in Backend Developer and Solution Architect interviews, including:

- API Gateway architecture
- REST vs HTTP APIs
- Endpoint selection
- Request lifecycle
- Stage management
- Deployment strategies
- RESTful API design
- Real-world architecture scenarios
- Best practices and trade-offs

---

