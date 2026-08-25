# API Types (REST vs HTTP vs WebSocket)

## Overview

Amazon API Gateway supports three different types of APIs:

- REST API
- HTTP API
- WebSocket API

Each API type is designed for different use cases and offers a different set of features.

Choosing the right API type affects:

- Cost
- Performance
- Security
- Scalability
- Available features

Understanding when to use each API type is a common interview topic and an important architectural decision.

---

# API Types at a Glance

| Feature | REST API | HTTP API | WebSocket API |
|----------|-----------|-----------|---------------|
| Communication | Request/Response | Request/Response | Full Duplex |
| Protocol | HTTP | HTTP | WebSocket |
| Lowest Cost | ❌ | ✅ | ❌ |
| Lowest Latency | ❌ | ✅ | Real-Time |
| API Keys | ✅ | ❌ |
| Usage Plans | ✅ | ❌ |
| Request Validation | ✅ | Limited |
| Mapping Templates | ✅ | Limited |
| Caching | ✅ | ❌ |
| Custom Authorizers | ✅ | ✅ |
| JWT Authorizers | Limited | ✅ |
| Best For | Enterprise APIs | Modern REST APIs | Real-time Apps |

---

# 1. REST API

## Overview

REST API is the original and most feature-rich API Gateway offering.

It provides complete API management capabilities, making it suitable for enterprise applications that require advanced features.

---

## Architecture

```text
Client
   │
   ▼
REST API Gateway
   │
   ▼
Lambda / ECS / EC2 / ALB
```

---

## Features

REST APIs support:

- API Keys
- Usage Plans
- Request Validation
- Response Validation
- Mapping Templates (VTL)
- API Caching
- Custom Domain Names
- IAM Authorization
- Lambda Authorizers
- Cognito Authorizers
- Stage Variables
- Canary Deployments

---

## Advantages

- Most powerful API type
- Rich feature set
- Enterprise-ready
- Highly configurable
- Mature ecosystem

---

## Disadvantages

- Higher pricing
- Slightly higher latency
- More configuration required

---

## Best Use Cases

- Enterprise applications
- Banking APIs
- Government systems
- APIs requiring request validation
- APIs using API Keys
- APIs requiring caching

---

# Example

```text
Client

↓

REST API Gateway

↓

Lambda

↓

DynamoDB
```

---

# 2. HTTP API

## Overview

HTTP API is a newer, lightweight version of API Gateway.

AWS designed HTTP APIs to provide a simpler, faster, and cheaper solution for modern REST services.

If you don't need advanced API management features, HTTP API is usually the preferred choice.

---

## Architecture

```text
Client
   │
   ▼
HTTP API Gateway
   │
   ▼
Lambda / ECS / HTTP Backend
```

---

## Features

HTTP APIs support:

- JWT Authentication
- Lambda Authorizers
- IAM Authorization
- Custom Domains
- CORS
- Lambda Integration
- HTTP Integration

Unlike REST APIs, HTTP APIs intentionally remove several advanced features to reduce complexity.

---

## Advantages

- Lower cost
- Lower latency
- Faster deployments
- Simpler configuration
- Easier maintenance

---

## Disadvantages

Missing features include:

- API Keys
- Usage Plans
- API Caching
- Request Validation
- Response Validation
- Full Mapping Templates
- Canary Deployments

---

## Best Use Cases

- Microservices
- Serverless applications
- Internal APIs
- Public REST APIs
- Mobile backends

---

# Example

```text
Client

↓

HTTP API

↓

Lambda

↓

Database
```

---

# Why is HTTP API Faster?

REST API performs many additional processing steps.

```text
REST API

↓

Authentication

↓

Validation

↓

Mapping Template

↓

Transformation

↓

Backend
```

HTTP API removes many optional processing layers.

```text
HTTP API

↓

Authentication

↓

Backend
```

Less processing means:

- Lower latency
- Lower cost
- Better performance

---

# 3. WebSocket API

## Overview

Unlike REST and HTTP APIs, WebSocket APIs provide **bidirectional communication**.

After a client establishes a WebSocket connection, both the client and the server can send messages at any time.

The connection remains open until one side disconnects.

---

## Architecture

```text
            Client
               ▲
               │
         Two-way Communication
               │
               ▼
        WebSocket API Gateway
               │
               ▼
        Lambda / Backend
```

---

# Request Flow

```text
Client

↓

Connect

↓

WebSocket API

↓

Connection Established

↓

Client ⇄ Server

↓

Disconnect
```

Unlike REST APIs, every message does not require a new HTTP request.

---

## Common Routes

WebSocket APIs define routes instead of HTTP methods.

Typical routes include:

```text
$connect

$disconnect

$default

sendMessage

joinRoom

leaveRoom
```

---

## Advantages

- Real-time communication
- Low latency
- Persistent connection
- Server can push data
- Efficient for live updates

---

## Disadvantages

- More complex architecture
- Requires connection management
- Not suitable for traditional REST APIs

---

## Best Use Cases

- Chat applications
- Multiplayer games
- Live dashboards
- Financial trading platforms
- Notification systems
- IoT applications

---

# Communication Comparison

## REST API

Every request creates a new HTTP connection.

```text
Request

↓

Response

Connection Closed
```

---

## HTTP API

Works the same way as REST but with fewer processing steps.

```text
Request

↓

Response

Connection Closed
```

---

## WebSocket API

One connection remains open.

```text
Connect

↓

Message

↓

Message

↓

Message

↓

Disconnect
```

---

# Cost Comparison

| API Type | Relative Cost |
|-----------|---------------|
| HTTP API | Lowest |
| REST API | Higher |
| WebSocket API | Depends on connection duration and messages |

If you are building a simple REST API today, HTTP API is generally the most cost-effective option.

---

# Feature Comparison

| Capability | REST | HTTP | WebSocket |
|------------|------|------|------------|
| RESTful Endpoints | ✅ | ✅ | ❌ |
| Real-Time Messaging | ❌ | ❌ | ✅ |
| API Keys | ✅ | ❌ | ❌ |
| Usage Plans | ✅ | ❌ | ❌ |
| API Caching | ✅ | ❌ | ❌ |
| JWT Authorizer | Limited | ✅ | ❌ |
| Lambda Integration | ✅ | ✅ | ✅ |
| Custom Domains | ✅ | ✅ | ✅ |
| CORS | ✅ | ✅ | ❌ |

---

# Which API Type Should You Choose?

### Choose REST API when:

- You need API Keys.
- You need Usage Plans.
- You need request validation.
- You require API caching.
- You need advanced API management features.

---

### Choose HTTP API when:

- You are building modern REST services.
- You want the lowest cost.
- You want the lowest latency.
- JWT authentication is sufficient.
- You don't need enterprise API management features.

---

### Choose WebSocket API when:

- Clients need live updates.
- The server must push messages.
- Communication must be bidirectional.
- You are building real-time applications.

---

# Real-World Examples

## E-Commerce Platform

Customers browse products and place orders.

**Recommended API:** HTTP API

Reason:

Simple REST endpoints with lower cost and better performance.

---

## Banking Platform

Requires:

- API Keys
- Request Validation
- Usage Plans
- Enterprise Security

**Recommended API:** REST API

---

## Live Chat Application

Users send and receive messages instantly.

**Recommended API:** WebSocket API

---

## Live Stock Trading Dashboard

Prices update every second.

**Recommended API:** WebSocket API

---

# Interview Questions

### Which API type should you use for a new serverless REST API?

**Answer:**

HTTP API is generally the preferred choice because it offers lower latency, lower cost, and simpler configuration. REST API should be chosen only if advanced features such as API Keys, Usage Plans, request validation, or caching are required.

---

### Why does AWS recommend HTTP APIs for new applications?

Because HTTP APIs are:

- Faster
- Cheaper
- Easier to configure
- Optimized for modern serverless architectures

---

### When should you choose REST API instead of HTTP API?

When your application requires enterprise API management features such as:

- API Keys
- Usage Plans
- Request Validation
- Response Validation
- Mapping Templates
- API Caching
- Canary Deployments

---

### Can WebSocket APIs replace REST APIs?

No.

WebSocket APIs are designed for persistent, bidirectional communication. REST and HTTP APIs remain the better choice for standard CRUD operations and request-response workflows.

---

# Best Practices

- Prefer **HTTP APIs** for new REST-based serverless applications.
- Use **REST APIs** only when advanced API Gateway features are required.
- Use **WebSocket APIs** only for real-time communication.
- Avoid using WebSocket connections for traditional CRUD APIs.
- Consider both feature requirements and pricing before selecting an API type.

---

# Key Takeaways

- Amazon API Gateway supports **REST APIs**, **HTTP APIs**, and **WebSocket APIs**.
- **REST APIs** provide the richest feature set and are ideal for enterprise-grade API management.
- **HTTP APIs** offer lower cost, lower latency, and simpler configuration, making them the preferred choice for most modern REST services.
- **WebSocket APIs** enable persistent, bidirectional communication for real-time applications such as chat, gaming, and live dashboards.
- Choosing the appropriate API type depends on the application's functional requirements, performance expectations, and API management needs.