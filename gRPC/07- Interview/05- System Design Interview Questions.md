# Overview

System Design interviews evaluate your ability to architect scalable, reliable, maintainable, and fault-tolerant distributed systems. Unlike coding interviews, there is rarely a single "correct" solution. Interviewers are interested in your thought process, architectural decisions, trade-off analysis, scalability planning, and understanding of distributed systems.

When gRPC is involved, the discussion usually focuses on service-to-service communication rather than frontend APIs. You should understand where gRPC fits within a larger architecture and where other technologies such as REST, Kafka, message queues, caches, databases, and API Gateways are more appropriate.

This chapter presents common system design interview questions where gRPC plays an important role. Each scenario includes the interviewer's expectations, a high-level design approach, architectural considerations, follow-up questions, and common trade-offs.

---

# Question 1

## Design a Chat Application using gRPC

### What the Interviewer is Testing

- Bidirectional Streaming
- Low latency communication
- Horizontal scalability
- Connection management

### Requirements

- Real-time messaging
- Online presence
- Typing indicators
- Message delivery
- Read receipts
- Multiple chat rooms

### High-Level Architecture

```text
               Mobile/Web Clients
                       │
               Load Balancer
                       │
              Chat Gateway Service
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Chat Service   Presence Service   Notification Service
        │              │              │
        └──────────────┼──────────────┘
                       │
                     Kafka
                       │
                 Message Database
```

### Where gRPC Fits

- Gateway → Chat Service
- Chat Service → Presence Service
- Chat Service → Notification Service
- Internal streaming between services

### Discussion Points

- Bidirectional Streaming
- Keepalive
- Connection pooling
- Sticky sessions
- Horizontal scaling
- Distributed tracing

### Follow-up Questions

- How would you support millions of concurrent users?
- Would you store messages synchronously?
- Where would Kafka fit?

---

# Question 2

## Design a Payment Processing System

### What the Interviewer is Testing

- Reliability
- Idempotency
- Security
- Service orchestration

### Services

- Payment Service
- Order Service
- Inventory Service
- Fraud Detection
- Notification Service

### High-Level Architecture

```text
Client

↓

API Gateway

↓

Order Service

↓

Payment Service

↓

Fraud Service

↓

Inventory Service

↓

Notification Service
```

### Where gRPC Fits

Internal synchronous communication:

- Order → Payment
- Payment → Fraud
- Payment → Inventory

Kafka handles:

- Order completed events
- Email notifications
- Analytics
- Audit logs

### Discussion Points

- Timeouts
- Retries
- Circuit breakers
- Idempotency
- Deadlines
- Authentication

### Follow-up Questions

- Should retries always be enabled?
- How do you prevent duplicate payments?
- What if Inventory fails after Payment succeeds?

---

# Question 3

## Design a Notification Platform

### What the Interviewer is Testing

- Scalability
- Streaming
- Event-driven architecture

### Requirements

- Email
- SMS
- Push Notifications
- Millions of users
- Retry support

### High-Level Architecture

```text
Application

↓

Notification API

↓

Kafka

↓

Notification Workers

↓

Email

SMS

Push Providers
```

### Where gRPC Fits

- Notification API → User Service
- Notification API → Preference Service
- Worker → Template Service

Kafka is used for asynchronous delivery.

### Discussion Points

- Retry queues
- Dead Letter Queues
- Rate limiting
- Template caching
- User preferences

---

# Question 4

## Design a Ride Booking Platform

### What the Interviewer is Testing

- Real-time communication
- Location updates
- Streaming

### Services

- Rider Service
- Driver Service
- Matching Service
- Pricing Service
- Notification Service

### High-Level Architecture

```text
Mobile Apps

↓

API Gateway

↓

Ride Service

↓

Matching Engine

↓

Driver Service

↓

Pricing Service
```

### Where gRPC Fits

- Driver location streaming
- Ride matching
- ETA calculation
- Driver availability

Streaming significantly reduces latency compared to repeated REST polling.

### Follow-up Questions

- Would REST polling work?
- How frequently should locations be updated?

---

# Question 5

## Design a Video Streaming Backend

### What the Interviewer is Testing

- Streaming architecture
- Scalability
- Metadata services

### Services

- Metadata
- Recommendation
- User Profile
- Analytics
- CDN

### High-Level Architecture

```text
Client

↓

API Gateway

↓

Metadata Service

↓

Recommendation Service

↓

CDN
```

### Where gRPC Fits

Internal metadata communication:

- Recommendation Service
- User Profile Service
- Analytics Service

Actual video delivery should use a CDN rather than gRPC.

### Follow-up Questions

- Why not stream video using gRPC?
- Where should caching be introduced?

---

# Question 6

## Design a Real-Time Analytics Platform

### What the Interviewer is Testing

- Streaming
- High throughput
- Distributed processing

### Requirements

- Millions of events
- Dashboards
- Live metrics
- Alerting

### High-Level Architecture

```text
Applications

↓

Collectors

↓

Kafka

↓

Processing Engine

↓

Analytics Service

↓

Dashboard
```

### Where gRPC Fits

- Collectors → Analytics Service
- Dashboard → Analytics Service
- Alert Service → Notification Service

Kafka handles event ingestion.

### Discussion Points

- Batch vs streaming
- Compression
- Backpressure
- Horizontal scaling

---

# Question 7

## Design Service Discovery for Hundreds of Microservices

### What the Interviewer is Testing

- Infrastructure knowledge
- Cloud-native architecture

### High-Level Architecture

```text
Client

↓

Service Discovery

↓

Healthy Instance

↓

gRPC Connection
```

### Technologies

- Kubernetes Services
- Consul
- etcd
- DNS
- Envoy

### Discussion Points

- Health checks
- Dynamic discovery
- Load balancing
- Failover

### Follow-up Questions

- How does Kubernetes discover services?
- How does Envoy help?

---

# Question 8

## Design an API Gateway for gRPC Services

### What the Interviewer is Testing

- API Gateway concepts
- Protocol translation

### Responsibilities

- Authentication
- Authorization
- Rate limiting
- Logging
- Routing
- TLS termination

### High-Level Architecture

```text
Client

↓

API Gateway

↓

REST

↓

gRPC Services
```

### Discussion Points

- gRPC-Web
- REST Gateway
- JWT validation
- Request routing

### Follow-up Questions

- Why expose REST externally?
- Why use gRPC internally?

---

# Question 9

## Design a Highly Available gRPC Platform

### What the Interviewer is Testing

- Reliability
- Fault tolerance
- Disaster recovery

### High-Level Architecture

```text
Clients

↓

Global Load Balancer

↓

Region A

↓

Region B

↓

Region C
```

### Considerations

- Multi-region deployment
- Health checks
- Automatic failover
- Circuit breakers
- Retry policies
- Connection draining

### Follow-up Questions

- How would clients reconnect after failover?
- How do you avoid split-brain scenarios?

---

# Question 10

## Design a Large E-commerce Backend using gRPC

### What the Interviewer is Testing

- End-to-end architecture
- Service decomposition
- Communication patterns

### Services

- User
- Product
- Inventory
- Cart
- Checkout
- Payment
- Shipping
- Recommendation
- Notification

### High-Level Architecture

```text
Client

↓

API Gateway

↓

REST

↓

gRPC Internal Services

↓

Kafka

↓

Background Workers
```

### Discussion Points

- Which services require synchronous communication?
- Which workflows should be event-driven?
- Where should Redis be introduced?
- How would caching improve performance?
- How would you prevent cascading failures?

### Follow-up Questions

- Would every service communicate with every other service?
- How would you secure service-to-service communication?
- Which services should be independently scalable?

---

# Best Practices

- Begin every design by clarifying functional and non-functional requirements.
- Identify which interactions require synchronous communication and which are better suited for asynchronous messaging.
- Explain why gRPC is chosen for internal communication and when REST or message brokers are more appropriate.
- Discuss scalability, fault tolerance, observability, and security throughout the design.
- Consider deployment environments such as Kubernetes and cloud-native infrastructure.
- Clearly explain trade-offs and justify architectural decisions.

---

# Common Mistakes

- Recommending gRPC for every communication pattern without considering alternatives.
- Ignoring asynchronous workflows where event-driven architecture is more suitable.
- Designing tightly coupled microservices with excessive service-to-service calls.
- Forgetting about retries, timeouts, and circuit breakers.
- Overlooking observability, monitoring, and distributed tracing.
- Neglecting API versioning and backward compatibility.
- Failing to consider scalability and high availability from the beginning.

---

# Key Takeaways

- System design interviews assess architectural thinking, communication skills, and the ability to build scalable distributed systems rather than knowledge of specific APIs.
- gRPC excels at low-latency, high-performance service-to-service communication but is often complemented by REST, Kafka, caches, and databases in modern architectures.
- Strong candidates explain requirements, justify trade-offs, address operational concerns, and design systems that are reliable, secure, observable, and maintainable.
- Understanding where gRPC fits within a broader distributed system is essential for succeeding in senior backend and system design interviews.