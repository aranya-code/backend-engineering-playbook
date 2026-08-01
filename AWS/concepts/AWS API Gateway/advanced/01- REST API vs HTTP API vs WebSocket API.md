# REST API vs HTTP API vs WebSocket API

## Overview

Amazon API Gateway supports **three different API types**, each designed for different workloads and architectural patterns.

Choosing the correct API type is an important architectural decision because it directly affects:

- Features
- Performance
- Cost
- Latency
- Security options
- Scalability

The three API types are:

- REST APIs
- HTTP APIs
- WebSocket APIs

Each solves a different class of problems.

---

# API Gateway API Types

```text
                Amazon API Gateway

                      │

        ┌─────────────┼─────────────┐

        ▼             ▼             ▼

    REST API      HTTP API     WebSocket API
```

---

# REST API

REST API is the original and most feature-rich API Gateway offering.

It supports:

- RESTful APIs
- Advanced authentication
- API Keys
- Usage Plans
- Request Validation
- API Caching
- Canary Deployments
- Mapping Templates
- AWS WAF
- Mutual TLS

REST APIs are intended for production workloads requiring advanced capabilities.

---

# HTTP API

HTTP API is a newer offering focused on:

- Lower cost
- Lower latency
- Simpler configuration

It supports:

- JWT Authorizers
- Lambda Authorizers
- IAM Authentication
- CORS
- Custom Domains
- OpenAPI
- Auto Deployments

HTTP APIs intentionally omit several advanced REST API features.

---

# WebSocket API

Unlike REST and HTTP APIs:

```text
Request

↓

Response

↓

Connection Closed
```

WebSocket APIs maintain:

```text
Persistent Connection
```

allowing two-way communication between client and server.

---

# Communication Model

REST & HTTP APIs:

```text
Client

↓

Request

↓

Response
```

WebSocket API:

```text
Client

⇅

Persistent Connection

⇅

Server
```

---

# Common Use Cases

REST API:

- Banking APIs
- Payment APIs
- Enterprise APIs
- Public APIs

HTTP API:

- Microservices
- Serverless APIs
- CRUD APIs
- Internal APIs

WebSocket API:

- Chat Applications
- Multiplayer Games
- Live Dashboards
- Trading Platforms
- Notification Systems

---

# Feature Comparison

| Feature | REST API | HTTP API | WebSocket API |
|----------|:-------:|:--------:|:-------------:|
| REST Support | ✅ | ✅ | ❌ |
| Persistent Connections | ❌ | ❌ | ✅ |
| Lowest Cost | ❌ | ✅ | ❌ |
| Lowest Latency | ❌ | ✅ | ✅ |
| API Keys | ✅ | ❌ | ❌ |
| Usage Plans | ✅ | ❌ | ❌ |
| API Caching | ✅ | ❌ | ❌ |
| Request Validation | ✅ | Limited | ❌ |
| Mapping Templates | ✅ | Limited | Limited |
| Canary Deployments | ✅ | ❌ | ❌ |
| JWT Authorizers | ❌ | ✅ | ❌ |
| Cognito Authorizers | ✅ | Via JWT | ❌ |
| AWS WAF | ✅ | ✅ | ❌ |
| Mutual TLS | ✅ | ✅ | ❌ |

---

# REST API Architecture

```text
Client

↓

REST API

↓

Lambda

↓

DynamoDB
```

Designed for feature-rich enterprise APIs.

---

# HTTP API Architecture

```text
Client

↓

HTTP API

↓

Lambda

↓

Amazon RDS
```

Optimized for simplicity and performance.

---

# WebSocket Architecture

```text
Browser

⇅

WebSocket API

⇅

Lambda

⇅

Backend
```

Communication remains open until either side disconnects.

---

# Performance

Approximate comparison:

```text
Fastest

↓

HTTP API

↓

REST API

↓

WebSocket

(Depends on workload)
```

HTTP APIs have lower overhead because fewer features are processed.

---

# Pricing

Generally:

```text
Lowest Cost

↓

HTTP API

↓

REST API

↓

WebSocket
```

HTTP APIs can be significantly cheaper for high-volume workloads.

---

# Decision Guide

```text
Need API Keys?

↓

REST API

-------------------------

Need JWT Authentication?

↓

HTTP API

-------------------------

Need Real-Time Communication?

↓

WebSocket API

-------------------------

Need API Caching?

↓

REST API

-------------------------

Need Lowest Cost?

↓

HTTP API
```

---

# Choosing the Right API

Choose **REST API** when:

- Advanced security is required
- API Keys are needed
- Usage Plans are required
- Request Validation is important
- API Caching is required
- Canary Deployments are needed

Choose **HTTP API** when:

- Building modern serverless APIs
- Cost is important
- Low latency is required
- JWT authentication is sufficient
- Simplicity is preferred

Choose **WebSocket API** when:

- The server must push data to clients
- Real-time communication is required
- Persistent connections are necessary

---

# Real-World Examples

### Banking Platform

```text
REST API
```

Reason:

- Strong authentication
- API Keys
- Usage Plans
- Request Validation

---

### Serverless Microservices

```text
HTTP API
```

Reason:

- Lower cost
- Lower latency
- JWT authentication

---

### Stock Trading Dashboard

```text
WebSocket API
```

Reason:

- Live market updates
- Continuous server push

---

# Best Practices

- Prefer **HTTP APIs** for new serverless REST applications unless advanced REST API features are required.
- Use **REST APIs** when API Caching, Usage Plans, Request Validation, or advanced API management features are needed.
- Choose **WebSocket APIs** only for genuine real-time bidirectional communication.
- Evaluate feature requirements before optimizing for cost.
- Avoid using WebSocket APIs for request-response workloads.

---

# Common Interview Questions

### What are the three API Gateway API types?

- REST API
- HTTP API
- WebSocket API

---

### Which API Gateway type is the cheapest?

HTTP API.

---

### Which API Gateway type supports API Caching?

REST API.

---

### Which API Gateway type is used for real-time applications?

WebSocket API.

---

### Should new serverless APIs use REST API or HTTP API?

For most modern workloads, **HTTP API** is recommended because it provides lower latency and lower cost. Choose **REST API** only when advanced features such as API Keys, Usage Plans, API Caching, or Canary Deployments are required.

---

# Key Takeaways

- Amazon API Gateway offers REST APIs, HTTP APIs, and WebSocket APIs, each optimized for different workloads.
- REST APIs provide the richest feature set for enterprise and production environments.
- HTTP APIs offer lower cost, lower latency, and simpler configuration for modern serverless applications.
- WebSocket APIs enable persistent, bidirectional communication for real-time applications.
- Selecting the appropriate API type requires balancing features, performance, cost, and architectural requirements.