# API Types

## Overview

Amazon API Gateway provides three primary API types:

1. **REST APIs**
2. **HTTP APIs**
3. **WebSocket APIs**

Although REST APIs and HTTP APIs are both designed for HTTP-based request/response workloads, they differ significantly in features, configuration model, pricing characteristics, and supported capabilities. WebSocket APIs solve a different problem by providing persistent, bidirectional communication between clients and backends. :contentReference[oaicite:0]{index=0}

The most important architectural decision is therefore not:

> "Which API type is newer?"

It is:

> **"Which API type provides the capabilities required by this workload without adding unnecessary complexity or cost?"**

---

# 1. API Gateway API Types

```text
                    API Gateway
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
       REST API       HTTP API      WebSocket API
          │              │              │
          ▼              ▼              ▼
   Feature-rich      Lightweight    Real-time
   HTTP APIs         HTTP APIs      bidirectional
```

---

# 2. REST API

A REST API in API Gateway models an API around **resources and methods**.

For example:

```text
/products
/orders
/users
```

with methods such as:

```text
GET
POST
PUT
DELETE
```

AWS describes a REST API as being composed of resources and methods, where a resource represents a logical entity accessible through a resource path and a method represents an API operation. :contentReference[oaicite:1]{index=1}

Example:

```text
GET /products
POST /products

GET /products/{id}
PUT /products/{id}
DELETE /products/{id}
```

---

## REST API Architecture

```text
Client

        │
        │ HTTPS
        ▼
┌───────────────────┐
│   API Gateway     │
│    REST API       │
└─────────┬─────────┘
          │
          ▼
     Integration
          │
     ┌────┴─────┐
     │          │
   Lambda      HTTP
     │         Backend
     │
     ▼
  Database
```

---

# 3. REST API Characteristics

REST APIs provide the broadest feature set of the API Gateway API types.

Important capabilities include:

- Resources
- Methods
- Request validation
- Request/response transformations
- Mapping templates
- API Keys
- Usage Plans
- Per-client throttling
- AWS WAF integration
- Private API endpoints
- Custom authorizers
- Caching
- OpenAPI import/export

AWS specifically recommends REST APIs when you require features such as API Keys, per-client throttling, request validation, AWS WAF integration, or private API endpoints. :contentReference[oaicite:2]{index=2}

---

# 4. When Should You Use REST APIs?

REST APIs are appropriate when you require advanced API Gateway functionality.

Typical examples:

```text
Enterprise API

        ↓

Advanced API Management

        ↓

REST API
```

Use REST APIs when requirements include:

- API Keys
- Usage Plans
- Per-client throttling
- Request validation
- Advanced transformations
- Private API endpoints
- REST API-specific features

---

# 5. HTTP API

HTTP APIs are designed as a simpler and lower-cost alternative for many modern HTTP workloads.

AWS describes REST APIs and HTTP APIs as both being RESTful API products, while HTTP APIs intentionally provide a more minimal feature set so they can be offered at a lower price. :contentReference[oaicite:3]{index=3}

An HTTP API can route requests to:

- AWS Lambda
- Routable HTTP endpoints

:contentReference[oaicite:4]{index=4}

---

# 6. HTTP API Architecture

```text
Client

        │
        │ HTTPS
        ▼
┌───────────────────┐
│   API Gateway     │
│    HTTP API       │
└─────────┬─────────┘
          │
          ▼
     Integration
          │
     ┌────┴─────┐
     │          │
   Lambda      HTTP
     │         Backend
     │
     ▼
  Database
```

---

# 7. HTTP API Characteristics

HTTP APIs provide a simpler API model and include capabilities such as:

- HTTP routing
- Lambda integrations
- HTTP integrations
- JWT authorization
- OAuth 2.0 / OpenID Connect authorization
- CORS
- Automatic deployments

AWS explicitly documents built-in support for CORS and automatic deployments for HTTP APIs. :contentReference[oaicite:5]{index=5}

HTTP API JWT authorizers can validate JWTs issued through OAuth 2.0 or OpenID Connect frameworks and can enforce authorization scopes. :contentReference[oaicite:6]{index=6}

---

# 8. When Should You Use HTTP APIs?

HTTP APIs are usually a strong default for modern APIs when you don't require REST API-specific features.

Typical architecture:

```text
Frontend

        ↓

HTTP API

        ↓

Lambda / ECS / HTTP Backend
```

Good use cases include:

- Modern REST-style APIs
- Serverless applications
- Microservices
- Internal services
- Lightweight APIs
- APIs using standard JWT/OIDC authorization

---

# 9. WebSocket API

WebSocket APIs solve a fundamentally different problem.

REST and HTTP APIs generally follow:

```text
Request

↓

Response
```

WebSocket APIs support:

```text
Client

↕
Persistent Connection
↕

Server
```

The client and backend can communicate independently after the connection is established. AWS describes WebSocket APIs as bidirectional and suitable for applications where the server needs to push information to connected clients. :contentReference[oaicite:7]{index=7}

---

# 10. WebSocket Architecture

```text
                 Client
                    │
                    │
              WebSocket
                    │
                    ▼
          ┌─────────────────┐
          │   API Gateway   │
          │ WebSocket API   │
          └────────┬────────┘
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
       Lambda   HTTP       AWS
                Service   Services
```

The API Gateway WebSocket connection is persistent between the client and API Gateway. The backend integration itself does not maintain that persistent connection; API Gateway invokes backend integrations as messages arrive. :contentReference[oaicite:8]{index=8}

---

# 11. WebSocket Routes

WebSocket APIs use **routes** to determine which backend integration should process an incoming message.

Three predefined routes are available:

```text
$connect
$disconnect
$default
```

You can also create custom routes.

For example:

```text
sendMessage
joinRoom
leaveRoom
typing
```

AWS documents `$connect`, `$disconnect`, and `$default` as predefined WebSocket routes. :contentReference[oaicite:9]{index=9}

---

# 12. WebSocket Route Selection

A WebSocket API can use a route selection expression.

Example message:

```json
{
    "action": "sendMessage",
    "message": "Hello"
}
```

Route selection expression:

```text
${request.body.action}
```

API Gateway evaluates:

```text
request.body.action

        ↓

sendMessage

        ↓

sendMessage route

        ↓

Backend integration
```

This allows different message types to invoke different backend integrations. :contentReference[oaicite:10]{index=10}

---

# 13. WebSocket Use Cases

WebSocket APIs are useful when the server needs to communicate with clients without waiting for another client request.

Common examples:

### Chat

```text
User A
  ↕
Chat Service
  ↕
User B
```

### Collaboration

```text
User A
  ↕
Collaboration Service
  ↕
User B
```

### Multiplayer Applications

```text
Player A
Player B
Player C
   ↕
Game Backend
```

### Real-Time Dashboards

```text
Backend

↓

WebSocket

↓

Connected Clients
```

### Trading / Market Data

```text
Market Data

↓

WebSocket API

↓

Connected Clients
```

AWS lists chat, collaboration, multiplayer games, and financial trading as examples of WebSocket use cases. :contentReference[oaicite:11]{index=11}

---

# 14. REST API vs HTTP API

This is one of the most important API Gateway interview questions.

| Capability | REST API | HTTP API |
|---|---|---|
| HTTP request/response | Yes | Yes |
| Lambda integration | Yes | Yes |
| HTTP integration | Yes | Yes |
| JWT authorization | Not the same native model | Yes |
| API Keys | Yes | No |
| Usage Plans | Yes | No |
| Per-client throttling | Yes | No |
| Request validation | Yes | Limited compared with REST API |
| AWS WAF integration | Yes | Not supported in the same REST API feature set |
| Private API endpoints | Yes | Not supported in the same REST API feature set |
| CORS | Supported | Built-in support |
| Automatic deployments | No | Yes |
| Feature set | Broader | More minimal |
| Pricing | Higher | Lower |

AWS explicitly positions HTTP APIs as the lower-cost, minimal-feature option and REST APIs as the more feature-rich option. :contentReference[oaicite:12]{index=12}

---

# 15. REST API vs HTTP API Decision

Use this decision process:

```text
Do you need advanced REST API features?
                │
          ┌─────┴─────┐
          │           │
         Yes          No
          │           │
          ▼           ▼
      REST API     HTTP API
```

---

# 16. REST API Feature Decision

Choose REST API if you require:

```text
API Keys
   OR
Usage Plans
   OR
Per-client throttling
   OR
Request validation
   OR
AWS WAF integration
   OR
Private API endpoint
   OR
Other REST-specific features
```

AWS explicitly identifies these as reasons to choose REST APIs. :contentReference[oaicite:13]{index=13}

---

# 17. HTTP API Feature Decision

Choose HTTP API when your requirements are primarily:

```text
HTTP Routing

+

Lambda / HTTP Integration

+

JWT Authorization

+

CORS

+

Automatic Deployment
```

and you don't require REST API-only features.

---

# 18. REST API vs WebSocket API

These APIs solve different problems.

| REST API | WebSocket API |
|---|---|
| Request/response | Bidirectional |
| Stateless interaction model | Persistent connection |
| HTTP methods | WebSocket messages |
| GET/POST/PUT/DELETE | Routes |
| CRUD APIs | Real-time applications |
| Client initiates requests | Either side can send messages |

WebSocket APIs are specifically designed for persistent, bidirectional communication. :contentReference[oaicite:14]{index=14}

---

# 19. HTTP API vs WebSocket API

Similarly:

```text
Need standard HTTP API?
        │
        ▼
     HTTP API
```

versus:

```text
Need persistent bidirectional communication?
        │
        ▼
   WebSocket API
```

---

# 20. Example: E-Commerce API

For a typical e-commerce backend:

```text
GET /products
POST /orders
GET /orders/{id}
DELETE /cart/items/{id}
```

An HTTP API is often an appropriate choice.

Architecture:

```text
Frontend

↓

HTTP API

↓

Microservices

↓

Database
```

If the application also needs real-time order updates:

```text
Frontend

├── HTTP API
│      │
│      └── CRUD operations
│
└── WebSocket API
       │
       └── Real-time updates
```

The same application can use different API types for different communication patterns.

---

# 21. Example: Chat Application

A chat application requires messages to be pushed to connected users.

A WebSocket API is appropriate:

```text
Mobile App

       ↕

WebSocket API

       ↕

Chat Backend
```

Messages can flow in both directions without requiring repeated polling.

---

# 22. Example: Serverless CRUD API

For a simple serverless application:

```text
Frontend

↓

HTTP API

↓

Lambda

↓

DynamoDB
```

HTTP API is often appropriate because the application primarily needs:

- HTTP routing
- JWT authorization
- CORS
- Lambda integration

---

# 23. Example: Enterprise API Management

Suppose an organization requires:

```text
Multiple external customers

+

API Keys

+

Per-client throttling

+

Usage Plans

+

Private API endpoints
```

A REST API is a better fit because these are REST API capabilities. :contentReference[oaicite:15]{index=15}

---

# 24. Example: Real-Time Dashboard

Suppose a dashboard displays continuously changing information.

Instead of:

```text
Client

↓

GET /status

↓

Wait

↓

GET /status

↓

Wait

↓

GET /status
```

a WebSocket architecture can maintain a connection:

```text
Client

↕

WebSocket API

↕

Backend

↓

Push Updates
```

This avoids implementing application-level polling for every update.

---

# 25. Can You Use Multiple API Types?

Yes.

A production application can use different API Gateway API types for different workloads.

Example:

```text
                    Application
                         │
             ┌───────────┴───────────┐
             │                       │
             ▼                       ▼
         HTTP API              WebSocket API
             │                       │
             ▼                       ▼
       REST-style API          Real-time events
             │                       │
             ▼                       ▼
       Lambda / ECS             Lambda / ECS
```

The API type should be selected according to communication requirements.

---

# 26. API Type Selection Framework

Use this mental model during architecture discussions:

```text
                         API Requirement
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       Standard HTTP      Advanced API       Real-time
         workload         management        communication
              │                │                │
              ▼                ▼                ▼
          HTTP API         REST API        WebSocket API
```

---

# 27. Common Interview Question

## Which API Gateway API type would you choose for a new REST API?

### Strong Answer

"I would start with an HTTP API if the application only needs standard HTTP routing, Lambda or HTTP integrations, JWT authorization, CORS, and automatic deployments. HTTP APIs have a smaller feature set and lower pricing.

If the requirements include API Keys, Usage Plans, per-client throttling, request validation, AWS WAF integration, private API endpoints, or other REST API-specific capabilities, I would choose a REST API instead." :contentReference[oaicite:16]{index=16}

---

# 28. Common Interview Question

## Is HTTP API a replacement for REST API?

### Answer

No.

HTTP APIs and REST APIs overlap significantly, but they are intentionally different products.

HTTP APIs provide a simpler feature set at a lower price.

REST APIs provide additional API management and integration capabilities.

The correct choice depends on requirements. :contentReference[oaicite:17]{index=17}

---

# 29. Common Interview Question

## When would you use WebSocket instead of HTTP?

### Answer

I would use WebSocket when the application requires persistent, bidirectional communication and the server needs to push events to connected clients.

Examples include:

- Chat
- Collaboration
- Multiplayer applications
- Real-time dashboards
- Trading applications

For conventional CRUD operations, I would normally use an HTTP API instead. :contentReference[oaicite:18]{index=18}

---

# 30. Common Interview Question

## Can HTTP APIs use JWT authentication?

### Answer

Yes.

HTTP APIs support JWT authorizers. API Gateway can validate JWTs and optionally enforce authorization scopes before forwarding the request to the backend. :contentReference[oaicite:19]{index=19}

---

# 31. Common Interview Question

## Why wouldn't you automatically choose REST API for everything?

### Answer

Because more features do not automatically mean a better architecture.

If an application only needs:

```text
HTTP Routing

+

JWT

+

Lambda

+

CORS
```

using an HTTP API can provide the required functionality with a simpler configuration and lower pricing.

I would avoid paying for or operating features the application does not require.

---

# 32. Common Interview Question

## Why wouldn't you use WebSocket for every API?

### Answer

WebSocket introduces a different communication model.

For conventional request/response operations:

```text
GET /products
POST /orders
GET /users/{id}
```

HTTP is simpler and more appropriate.

WebSocket is justified when persistent bidirectional communication provides real application value.

---

# 33. Important Architectural Distinction

Do not confuse:

```text
REST API
```

with:

```text
RESTful API design
```

REST API in API Gateway is an AWS product.

RESTful API is an architectural style for designing HTTP APIs.

Therefore:

```text
HTTP API
```

can also be used to implement a RESTful API.

AWS itself describes both REST APIs and HTTP APIs as RESTful API products. :contentReference[oaicite:20]{index=20}

---

# 34. Production Decision Matrix

| Requirement | Recommended API |
|---|---|
| Simple HTTP API | HTTP API |
| Lambda-based REST-style API | HTTP API |
| JWT/OIDC authorization | HTTP API |
| CORS + automatic deployment | HTTP API |
| API Keys | REST API |
| Usage Plans | REST API |
| Per-client throttling | REST API |
| Request validation | REST API |
| AWS WAF integration | REST API |
| Private API endpoint | REST API |
| Advanced API management | REST API |
| Chat | WebSocket API |
| Real-time collaboration | WebSocket API |
| Multiplayer | WebSocket API |
| Server-to-client push | WebSocket API |

The REST-vs-HTTP distinctions above reflect AWS's current feature comparison. :contentReference[oaicite:21]{index=21}

---

# 35. Decision Tree

```text
Start
  │
  ▼
Is communication real-time
and bidirectional?
  │
  ├── Yes ───────────────► WebSocket API
  │
  └── No
       │
       ▼
Do you need REST API-specific
advanced features?
       │
       ├── Yes ───────────► REST API
       │
       └── No
            │
            ▼
         HTTP API
```

This is a useful mental model for interviews.

---

# 36. Common Mistakes

### Mistake 1 — "REST API is always better"

Incorrect.

REST APIs have more features, but those features may not be required.

---

### Mistake 2 — "HTTP API isn't RESTful"

Incorrect.

AWS describes both REST APIs and HTTP APIs as RESTful API products. :contentReference[oaicite:22]{index=22}

---

### Mistake 3 — "API Key means authentication"

Incorrect.

API Keys are primarily used to identify API clients and support usage controls for REST APIs. They should not be treated as a replacement for user authentication.

---

### Mistake 4 — "WebSocket is just faster HTTP"

Incorrect.

WebSocket provides a different communication model:

```text
Persistent

+

Bidirectional
```

rather than conventional HTTP request/response.

---

### Mistake 5 — "Use WebSocket whenever data changes frequently"

Not necessarily.

The real question is whether the client needs **server-initiated, low-latency updates over a persistent connection**.

For some workloads, polling, Server-Sent Events, queues, or other architectures may be more appropriate.

---

# 37. Senior Architecture Perspective

When selecting an API type, evaluate:

```text
Functional Requirements
        │
        ▼
Communication Pattern
        │
        ▼
Security Requirements
        │
        ▼
API Management Requirements
        │
        ▼
Performance Requirements
        │
        ▼
Operational Requirements
        │
        ▼
Cost
        │
        ▼
API Type
```

Do not start with:

> "I always use REST API."

Start with:

> "What capabilities does the system require?"

---

# 38. Key Takeaways

- API Gateway provides **REST APIs, HTTP APIs, and WebSocket APIs**, each designed for different requirements. :contentReference[oaicite:23]{index=23}
- REST APIs provide the broader feature set and are appropriate when advanced API management capabilities are required.
- HTTP APIs provide a simpler, lower-cost option for many modern HTTP workloads. :contentReference[oaicite:24]{index=24}
- HTTP APIs support JWT authorization, CORS, and automatic deployments. :contentReference[oaicite:25]{index=25}
- WebSocket APIs provide persistent, bidirectional communication and are appropriate for real-time applications. :contentReference[oaicite:26]{index=26}
- Choose REST API when you need REST-specific capabilities such as API Keys, Usage Plans, per-client throttling, request validation, AWS WAF integration, or private API endpoints. :contentReference[oaicite:27]{index=27}
- Choose HTTP API when your application primarily requires lightweight HTTP routing and standard authorization/integration capabilities.
- Choose WebSocket API when the system requires persistent, bidirectional communication.
- The correct API type is determined by **requirements and trade-offs**, not by which product has the most features.