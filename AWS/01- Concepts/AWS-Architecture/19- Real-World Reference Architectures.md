# Real-World Reference Architectures

Composite patterns, showing how the individual building blocks in this folder combine in practice.

## 1. E-Commerce Order Processing (Event-Driven, Saga-Based)

```text
API Gateway → Order Service → publishes "OrderPlaced" (EventBridge)
                                   ↓                    ↓
                          Inventory Service      Payment Service
                          (reserve stock)         (charge card)
                                   ↓                    ↓
                          On failure: Step Functions triggers
                          compensating transactions (release stock, refund)
```

Combines: event-driven decoupling, the Saga pattern for the multi-step transaction, DLQs for messages that fail processing entirely.

## 2. Read-Heavy Content Platform (CQRS + Caching + CDN)

```text
Write Path:  Admin API → Write DB (Aurora)
                            ↓ (DynamoDB Streams / CDC)
Read Path:   User Request → CloudFront → ElastiCache → Read-optimized DB (OpenSearch)
```

Combines: CQRS to separate write consistency needs from read scale needs, multi-layer caching (CDN + application cache), read replicas conceptually extended into a fully separate read store.

## 3. Multi-Region Active-Active SaaS

```text
Route 53 (Latency-Based, health-checked)
 ├── us-east-1: Full stack + DynamoDB Global Table replica
 └── eu-west-1: Full stack + DynamoDB Global Table replica
```

Combines: Multi-Region high availability, DynamoDB Global Tables for cross-region data replication, Route 53 latency routing with health-check-driven exclusion of an unhealthy region.

## 4. Resilient Third-Party API Integration

```text
Service → Circuit Breaker → Exponential Backoff + Jitter → Third-Party API
             ↓ (open)
        Fallback: cached last-known-good response
```

Combines: circuit breaker to stop hammering a struggling dependency, backoff+jitter for the retries that do go through, a fallback path so the caller degrades gracefully instead of failing outright.

## 5. Serverless Data Processing Pipeline

```text
S3 Upload → S3 Event → Lambda (validate) → SQS → Lambda (process) → DynamoDB
                                              ↓ (on repeated failure)
                                             DLQ → Alarm
```

Combines: serverless event-driven processing, queue-based load leveling between two processing stages, DLQ-based failure isolation with alerting.

## 6. Legacy Modernization — Strangler Fig Pattern

```text
API Gateway (routes by path)
 ├── /v2/* → New microservice (Lambda/ECS)
 └── /*    → Legacy monolith (unchanged, still in production)
```

Gradually route specific endpoints to newly-built services behind a shared gateway, shrinking the legacy monolith's surface area over time without a risky big-bang rewrite — named for how a strangler fig gradually grows around and eventually replaces its host tree.

## Senior-Level Takeaway

None of these are exotic — each is a straightforward composition of the individual patterns covered elsewhere in this folder. Reference architectures are less about memorizing specific diagrams and more about recognizing which combination of patterns actually fits a given set of requirements and constraints.
