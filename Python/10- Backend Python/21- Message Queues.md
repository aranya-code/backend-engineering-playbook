# 21- Message Queues

## Overview

A message queue is an asynchronous communication mechanism in which a producer sends a message to a broker or queue and a consumer processes that message independently.

Message queues decouple the request path from work that does not need to complete before an HTTP or gRPC response is returned.

A synchronous workflow might look like:

```text
Client
  ↓
API
  ↓
Application
  ↓
Database
  ↓
External Service
  ↓
Response
```

A queue-based workflow can become:

```text
Client
  ↓
API
  ↓
Database
  ↓
Queue
  ↓
202 Accepted
```

and later:

```text
Queue
  ↓
Worker
  ↓
External Service
  ↓
Result / Database Update
```

This provides:

- asynchronous processing;
- workload buffering;
- producer/consumer decoupling;
- independent worker scaling;
- retry mechanisms;
- failure isolation;
- controlled concurrency;
- smoother traffic handling.

Message queues also introduce distributed-systems concerns:

- duplicate delivery;
- message ordering;
- retries;
- visibility timeouts;
- dead-letter queues;
- backpressure;
- poison messages;
- consumer crashes;
- broker failures;
- eventual consistency.

The central engineering principle is:

> A message is a request for work, not proof that the work has completed.

---

## Why Message Queues Exist

A synchronous API forces the client to wait for downstream work:

```text
POST /orders
     ↓
Create order
     ↓
Charge payment
     ↓
Send email
     ↓
Generate invoice
     ↓
Response
```

If email delivery takes 500 ms and invoice generation takes 2 seconds, the client experiences all of that latency.

With asynchronous processing:

```text
POST /orders
     ↓
Create order
     ↓
Publish events/jobs
     ↓
Response
```

Workers process:

```text
Email Worker
Invoice Worker
Payment Worker
Notification Worker
```

This reduces request latency and allows each workload to scale independently.

---

## Queue vs Message Broker

These terms are related but not identical.

A **queue** is primarily a work-distribution abstraction.

A **message broker** is infrastructure that accepts, stores, routes, and delivers messages.

Examples include:

- RabbitMQ;
- Amazon SQS;
- Kafka;
- Redis-based queue systems.

Kafka is technically a distributed event-streaming platform rather than a traditional queue, although consumers can use Kafka topics for queue-like workload distribution.

---

## Queue-Based Architecture

A typical backend architecture is:

```mermaid
flowchart LR
    C[Client] --> API[FastAPI / Django]
    API --> DB[(PostgreSQL)]
    API --> Q[Message Broker]
    Q --> W1[Worker A]
    Q --> W2[Worker B]
    W1 --> EXT[External Service]
    W2 --> DB
```

The API and workers can scale independently.

```text
API traffic
    ↓
scale API replicas

Queue depth
    ↓
scale worker replicas
```

This is one of the main operational benefits of asynchronous architectures.

---

## Producer

The producer creates and publishes a message.

Example:

```python
message = {
    "event_type": "order.created",
    "order_id": "ord_123",
}
```

The producer should generally avoid embedding assumptions about which worker instance will process the message.

A producer may be:

- FastAPI endpoint;
- Django application;
- Celery task;
- scheduled job;
- another microservice.

---

## Consumer

A consumer receives and processes messages.

Conceptually:

```python
def process_message(message: dict) -> None:
    order_id = message["order_id"]
    generate_invoice(order_id)
```

A consumer should be designed for:

- retries;
- duplicate delivery;
- malformed messages;
- timeouts;
- graceful shutdown;
- observability;
- partial downstream failures.

---

## Worker

A worker is a long-running process that consumes messages and performs background work.

Typical worker workloads include:

- email delivery;
- image processing;
- report generation;
- webhook delivery;
- data processing;
- payment reconciliation;
- search indexing;
- notifications;
- asynchronous API calls.

Celery is commonly used in Python applications for distributed task processing.

---

## Message Lifecycle

A simplified lifecycle is:

```text
Producer
   ↓
Publish
   ↓
Broker
   ↓
Available
   ↓
Consumer receives
   ↓
Processing
   ↓
Success ─────→ Acknowledge / complete
   │
   └── Failure → Retry / requeue / dead-letter
```

The exact semantics depend on the messaging system.

---

## Acknowledgment

Acknowledgment tells the broker that a consumer has successfully handled a message.

A common model is:

```text
Receive
   ↓
Process
   ↓
ACK
```

If the worker crashes before ACK:

```text
Receive
   ↓
Process
   X
Crash
```

the broker can make the message available again depending on its delivery semantics.

This is why consumers should generally be idempotent.

---

## At-Most-Once Delivery

At-most-once means a message is delivered zero or one time.

```text
Message
 ↓
Deliver
 ↓
ACK / remove
 ↓
Processing
```

If processing fails after removal, the message may be lost.

Advantages:

- fewer duplicates;
- simpler broker behavior;
- lower redelivery overhead.

Limitation:

- messages can be lost.

Use only when occasional loss is acceptable.

---

## At-Least-Once Delivery

At-least-once delivery attempts to ensure the message is eventually processed, but duplicates can occur.

```text
Receive
 ↓
Process
 ↓
Crash before ACK
 ↓
Redeliver
 ↓
Process again
```

This is common in production messaging systems.

Consumers should therefore assume:

> The same message may be delivered more than once.

---

## Exactly-Once Semantics

"Exactly once" is frequently misunderstood.

End-to-end exactly-once business effects are difficult in distributed systems.

Even if a broker provides exactly-once processing semantics within specific boundaries, the entire workflow may still include:

```text
Broker
 ↓
Python worker
 ↓
PostgreSQL
 ↓
External HTTP API
```

A network failure can make the external operation's outcome ambiguous.

For business correctness, idempotency and durable state are usually more important than relying on the phrase "exactly once."

---

## Idempotent Consumers

An idempotent consumer produces the same intended business result when the same message is processed multiple times.

Example:

```text
Message ID = evt_123

First delivery
    ↓
Create invoice
    ↓
Record evt_123 as processed

Duplicate delivery
    ↓
evt_123 already processed
    ↓
Skip
```

A PostgreSQL uniqueness constraint can enforce this:

```sql
CREATE UNIQUE INDEX processed_events_event_id_idx
ON processed_events (event_id);
```

---

## Idempotency Pattern

```python
def process_event(session, event_id: str, order_id: str) -> None:
    with session.begin():
        inserted = insert_processed_event(
            session,
            event_id=event_id,
        )

        if not inserted:
            return

        generate_invoice(session, order_id)
```

The exact implementation depends on how the insert reports conflicts.

The important property is that duplicate detection and the business state change occur within the same transaction.

---

## Queue Types

| Type | Typical semantics | Example use |
|---|---|---|
| Work queue | One worker handles each task | Background jobs |
| Pub/sub | Multiple subscribers receive messages | Domain events |
| Event stream | Durable ordered log | Event processing |
| Delay queue | Deliver after a delay | Scheduled retry |
| Priority queue | Higher-priority messages processed first | Urgent workloads |
| Dead-letter queue | Failed messages isolated | Poison-message handling |

A system may support several of these patterns.

---

## Work Queues

A work queue distributes tasks among consumers.

```text
             ┌── Worker A
Producer → Queue ── Worker B
             └── Worker C
```

Each task is generally intended to be processed by one worker.

This is useful for:

- CPU-intensive jobs;
- external API calls;
- emails;
- file processing;
- asynchronous database work.

---

## Publish/Subscribe

In pub/sub:

```text
                ┌── Consumer A
Producer → Topic├── Consumer B
                └── Consumer C
```

Each subscriber can independently receive the event.

This is useful when multiple services need to react to the same business event.

Example:

```text
OrderCreated
    ├── Inventory Service
    ├── Notification Service
    ├── Analytics Service
    └── Search Service
```

---

## Queue vs Pub/Sub

| Characteristic | Queue | Pub/Sub |
|---|---|---|
| Primary purpose | Work distribution | Event distribution |
| Consumers | Usually one worker per message | Multiple subscribers |
| Typical use | Background tasks | Domain events |
| Scaling | Add workers | Add consumer groups/subscribers |
| Message ownership | Worker receives task | Each subscription receives event |

Kafka consumer groups combine durable event streams with queue-like load balancing.

---

## Kafka

Kafka organizes messages into topics and partitions.

```text
Topic: orders

Partition 0
 ├── event 1
 ├── event 2
 └── event 3

Partition 1
 ├── event 4
 └── event 5
```

Consumers use consumer groups to distribute partitions:

```text
orders topic
    ↓
Consumer Group
 ├── Worker A
 ├── Worker B
 └── Worker C
```

Within a partition, Kafka preserves message order.

It does not provide one global ordering across all partitions.

---

## Kafka vs Traditional Queues

| Concern | Kafka | RabbitMQ / SQS-style queue |
|---|---|---|
| Primary model | Event log / stream | Message/task queue |
| Retention | Configurable durable retention | Usually message lifecycle based |
| Replay | Strong capability | Depends on system |
| Ordering | Per partition / ordered log | Depends on queue semantics |
| Consumer groups | Native | Different mechanism |
| High-throughput streaming | Excellent fit | Depends on broker |
| Background tasks | Possible | Natural fit |
| Event sourcing | Strong fit | Less natural |

The choice should follow workload semantics rather than popularity.

---

## Celery

Celery provides distributed task execution for Python.

A common architecture is:

```text
FastAPI / Django
      ↓
Celery
      ↓
Broker
      ↓
Celery Workers
      ↓
Result Backend
```

Celery commonly integrates with brokers such as RabbitMQ or Redis.

Example:

```python
from celery import Celery

app = Celery(
    "orders",
    broker="amqp://user:password@rabbitmq:5672//",
)


@app.task
def generate_invoice(order_id: str) -> None:
    create_invoice(order_id)
```

In production, credentials and broker URLs should come from configuration rather than source code.

---

## Celery Task Semantics

A Celery task should generally be treated as:

```text
at-least-once-ish distributed work
```

depending on broker, acknowledgment, retry, and worker configuration.

Do not assume a task executes exactly once merely because the task was submitted once.

Design tasks to be idempotent.

---

## Message Schema

Messages should have explicit schemas.

Example:

```json
{
  "id": "evt_01JXYZ",
  "type": "order.created",
  "version": 1,
  "occurred_at": "2026-09-06T12:30:00Z",
  "producer": "order-service",
  "data": {
    "order_id": "ord_123",
    "customer_id": "cus_456"
  }
}
```

Useful metadata includes:

- message ID;
- event type;
- schema version;
- timestamp;
- producer;
- correlation ID;
- trace ID;
- payload.

---

## Message Versioning

Messages often outlive the application deployment that created them.

Therefore:

```text
Producer V1
   ↓
Queue
   ↓
Consumer V2
```

must remain compatible during rolling deployments.

Use:

- explicit schema versions;
- additive changes where possible;
- backward-compatible consumers;
- migration strategies;
- schema registries where appropriate.

Avoid silently changing the meaning of existing fields.

---

## Commands vs Events

A **command** asks a specific consumer to perform work:

```text
GenerateInvoice
```

An **event** describes something that already happened:

```text
InvoiceGenerated
```

| Type | Meaning | Typical ownership |
|---|---|---|
| Command | "Do this" | Producer chooses intended handler |
| Event | "This happened" | Consumers decide whether to react |

Keeping these semantics explicit makes distributed architectures easier to reason about.

---

## Message Ordering

Ordering requirements must be explicit.

Suppose:

```text
OrderCreated
OrderCancelled
```

If cancellation is processed before creation, the consumer may fail.

Possible solutions include:

- partitioning by aggregate ID;
- sequence numbers;
- consumer-side state validation;
- version checks;
- ordering-aware processing.

For Kafka, partitioning events by `order_id` keeps events for the same order in one partition and therefore preserves their partition order.

---

## Global Ordering

Global ordering is expensive and often unnecessary.

Instead of requiring:

```text
all orders globally ordered
```

prefer:

```text
events for order A ordered
events for order B ordered
```

This allows horizontal scaling across partitions.

---

## Queue Depth

Queue depth represents work waiting to be processed.

```text
Producer rate > Consumer rate
        ↓
Queue depth increases
```

A growing queue is a capacity signal.

If:

```text
incoming = 1,000 msg/s
processing = 800 msg/s
```

the backlog grows by roughly:

```text
200 msg/s
```

assuming the rates remain stable.

---

## Backpressure

Queues naturally buffer bursts:

```text
Traffic spike
    ↓
Producer rate increases
    ↓
Queue absorbs work
    ↓
Workers process at sustainable rate
```

But queues do not create infinite capacity.

Eventually:

```text
queue fills
 ↓
latency increases
 ↓
messages expire/reject
```

Backpressure must therefore be explicitly managed.

---

## Consumer Scaling

Suppose:

```text
1,000 messages/sec
100 messages/sec/worker
```

Approximately ten workers are required to keep up under steady-state conditions.

But real sizing must account for:

- message size;
- processing-time distribution;
- downstream latency;
- concurrency;
- retries;
- CPU;
- memory;
- broker throughput.

Average throughput alone is insufficient for capacity planning.

---

## Queue Latency

Measure not only processing duration but also queue wait time.

```text
Message created
     ↓
Queue wait
     ↓
Consumer starts
     ↓
Processing
     ↓
Completed
```

Total user-visible asynchronous latency may be:

```text
queue wait + processing + downstream work
```

A fast worker does not help if messages spend minutes waiting in the queue.

---

## Retry

Transient failures should often be retried.

Examples:

- temporary network failure;
- HTTP 503;
- rate limiting;
- database failover;
- temporary broker error.

Use bounded retries with backoff.

```text
Attempt 1
   ↓
failure
   ↓
wait
   ↓
Attempt 2
   ↓
failure
   ↓
longer wait
   ↓
Attempt 3
```

---

## Exponential Backoff

A common pattern is:

```text
delay = base × 2^attempt
```

with jitter:

```text
delay + random_jitter
```

Jitter prevents many consumers from retrying simultaneously.

---

## Retryable vs Non-Retryable Errors

Not every failure should be retried.

| Error | Typical handling |
|---|---|
| Network timeout | Retry |
| HTTP 503 | Retry |
| HTTP 429 | Retry according to server guidance |
| Invalid schema | Dead-letter |
| Missing required field | Dead-letter |
| Authorization failure | Usually no immediate retry |
| Business rule violation | Usually no retry |
| Duplicate message | Treat as idempotent success |

Incorrect retry classification can create retry storms.

---

## Retry Storm

Consider:

```text
Database outage
    ↓
1,000 workers fail
    ↓
all retry immediately
    ↓
database receives another spike
    ↓
fails again
```

Mitigate with:

- exponential backoff;
- jitter;
- bounded concurrency;
- circuit breakers;
- rate limits;
- retry budgets.

---

## Dead-Letter Queues

A dead-letter queue isolates messages that repeatedly fail.

```text
Main Queue
    ↓
Consumer
    ├── Success → ACK
    │
    └── Repeated Failure
              ↓
          Dead Letter Queue
```

DLQs prevent one poison message from being retried indefinitely.

---

## Poison Messages

A poison message is a message that consistently fails processing.

Examples:

- malformed payload;
- unsupported schema;
- impossible state;
- unexpected data;
- permanent downstream validation failure.

A DLQ allows operators to inspect and remediate these messages without blocking healthy work.

---

## DLQ Operations

A DLQ should not become a graveyard.

Operational processes should define:

- alert thresholds;
- message inspection;
- root-cause analysis;
- replay procedure;
- quarantine rules;
- retention;
- ownership.

A replay should occur only after the underlying failure is understood.

---

## Visibility Timeout

Some queue systems use a visibility timeout.

Conceptually:

```text
Queue
 ↓
Worker receives message
 ↓
Message temporarily hidden
 ↓
Worker processes
 ↓
Delete / ACK
```

If the worker fails before completion:

```text
visibility timeout expires
 ↓
message becomes visible again
```

The timeout should exceed normal processing time while still allowing failed work to become recoverable.

---

## Visibility Timeout Pitfall

If processing takes 10 minutes but visibility timeout is 2 minutes:

```text
Worker A starts
    ↓
2 minutes
    ↓
message visible again
    ↓
Worker B starts same message
```

Now two workers may process the same message concurrently.

Long-running tasks require appropriate timeout configuration or periodic lease extension where supported.

---

## Message Ordering vs Parallelism

Ordering and concurrency often trade off.

```text
Single partition
    ↓
strict order
    ↓
limited parallelism
```

Partitioning can provide:

```text
Order A → Partition 1
Order B → Partition 2
Order C → Partition 3
```

allowing independent work to proceed concurrently.

---

## Hot Partitions

Poor partition keys can concentrate traffic:

```text
99% traffic
    ↓
Partition 0
```

while other partitions remain underutilized.

Choose partition keys that preserve required ordering while distributing workload.

---

## Message Size

Large messages increase:

- network traffic;
- broker storage;
- serialization cost;
- memory consumption;
- processing latency.

Prefer:

```text
message
→ identifiers + metadata
```

rather than embedding huge binary objects.

For large files:

```text
Object Storage
    ↓
S3 key
    ↓
Message
```

Example:

```json
{
  "event_type": "report.ready",
  "report_id": "rpt_123",
  "object_key": "reports/rpt_123.parquet"
}
```

---

## Queue Messages and Transactions

Publishing a message and committing a database transaction are separate operations.

Bad dual-write:

```text
BEGIN
 ↓
UPDATE PostgreSQL
 ↓
COMMIT
 ↓
Publish message
```

If publishing fails:

```text
database updated
message missing
```

The opposite ordering creates the reverse problem.

---

## Transactional Outbox

A reliable approach is:

```text
BEGIN
 ├── Update business data
 └── Insert outbox event
 ↓
COMMIT
 ↓
Outbox Publisher
 ↓
Message Broker
```

The database transaction atomically persists:

```text
business state
+
event
```

A publisher later sends the event to the broker.

This is particularly useful for PostgreSQL + Kafka/RabbitMQ integrations.

---

## Outbox Example

```python
def create_order(session, order_id: str, customer_id: str) -> None:
    with session.begin():
        insert_order(
            session,
            order_id=order_id,
            customer_id=customer_id,
        )

        insert_outbox_event(
            session,
            event_id=generate_event_id(),
            event_type="order.created",
            aggregate_id=order_id,
            payload={
                "order_id": order_id,
                "customer_id": customer_id,
            },
        )
```

A separate publisher reads pending outbox rows and publishes them.

The publisher must tolerate duplicate publication because a crash can occur after publishing but before marking the outbox row complete.

---

## Queue Publishing Guarantees

A producer should understand what the broker guarantees.

Potential failure:

```text
Producer
  ↓
Broker receives message
  ↓
Network failure
  ↓
Producer sees timeout
```

The producer does not necessarily know whether the broker accepted the message.

Idempotent message IDs and broker-specific producer semantics can help.

---

## Consumer Transactions

A consumer may need to coordinate:

```text
message processing
+
database update
```

A common pattern is:

```text
Receive message
    ↓
BEGIN
    ↓
Apply business state
    ↓
Record processed message
    ↓
COMMIT
    ↓
ACK
```

Acknowledging before the database commit can lose work if the process crashes.

---

## ACK Ordering

For database-backed consumers:

```text
message
 ↓
process
 ↓
database commit
 ↓
ACK
```

is generally safer than:

```text
message
 ↓
ACK
 ↓
database commit
```

because the second ordering can lose the message if the worker crashes after ACK but before commit.

---

## Consumer Failure

A robust consumer must handle:

```text
process crash
database timeout
broker disconnect
network partition
external API failure
serialization failure
application bug
```

The desired outcome is usually:

```text
temporary failure
    ↓
message remains recoverable
```

rather than silent loss.

---

## Graceful Shutdown

Workers should stop accepting new work and allow active work to finish or safely become retryable.

```text
SIGTERM
  ↓
Stop receiving new messages
  ↓
Finish active tasks
  ↓
ACK completed messages
  ↓
Close connections
  ↓
Exit
```

Kubernetes `terminationGracePeriodSeconds` should be compatible with expected task duration.

---

## Kubernetes Worker Deployment

A typical worker deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: invoice-worker
spec:
  replicas: 3
  template:
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: worker
          image: example/invoice-worker:1.0.0
```

Production deployments should additionally define appropriate:

- resource requests;
- resource limits;
- probes where meaningful;
- security context;
- autoscaling;
- shutdown handling.

---

## Autoscaling Workers

Worker scaling can be based on:

```text
queue depth
queue age
processing latency
CPU
memory
```

Queue depth alone can be misleading.

For example:

```text
10,000 tiny messages
```

and:

```text
10,000 expensive messages
```

require very different capacity.

Queue age is often a valuable signal because it directly indicates user-visible delay for asynchronous work.

---

## Kubernetes HPA and Queue Workloads

CPU-based autoscaling may fail for I/O-heavy workers.

A worker can have:

```text
CPU = 20%
queue depth = 100,000
```

and still be severely underprovisioned.

Queue-aware scaling through metrics or an event-driven autoscaler can be more appropriate.

---

## Celery Worker Concurrency

Celery workers can execute multiple tasks concurrently depending on the configured execution pool.

Capacity depends on:

```text
worker replicas
×
processes/threads
×
task throughput
```

Increasing concurrency can overload:

- PostgreSQL;
- Redis;
- external APIs;
- CPU;
- memory.

Worker concurrency should therefore be treated as downstream capacity, not simply a way to maximize throughput.

---

## Database Protection

A queue can hide a database overload.

Example:

```text
Queue
 ↓
100 workers
 ↓
PostgreSQL
```

If PostgreSQL can safely handle only 20 concurrent operations, 100 workers may make the system less reliable.

Use:

- bounded worker concurrency;
- database connection pools;
- rate limits;
- batch operations;
- backpressure.

---

## External API Protection

The same applies to external services.

```text
Queue
 ↓
1,000 workers
 ↓
External API
 ↓
HTTP 429
 ↓
Retry
 ↓
More traffic
```

Use:

- concurrency limits;
- rate limiting;
- exponential backoff;
- circuit breakers;
- provider-specific quotas.

---

## Queue-Based Rate Limiting

Queues can smooth request rates.

For example:

```text
API
 ↓
Queue
 ↓
20 workers
 ↓
External API
```

If the external API permits 20 concurrent operations, worker concurrency can act as a coarse control.

More precise rate limiting may still be necessary for requests-per-second or token-bucket limits.

---

## Priority Queues

Some workloads need different priorities:

```text
High:
payment confirmation

Medium:
email

Low:
analytics export
```

Priority mechanisms vary by broker.

Do not assume priority processing is free; it can complicate fairness and throughput.

A simpler architecture may use separate queues:

```text
high-priority queue
normal queue
low-priority queue
```

with dedicated worker capacity.

---

## Fairness and Starvation

A priority queue can starve low-priority work:

```text
High-priority traffic
    ↓
continuous
    ↓
Low-priority queue never drains
```

Monitor queue age across priority classes.

Use capacity reservations or weighted scheduling where fairness matters.

---

## Delayed Messages

Delayed delivery is useful for:

- retry scheduling;
- reminders;
- payment reconciliation;
- timeout workflows.

Example:

```text
Task
 ↓
wait 60 seconds
 ↓
retry
```

Implementation depends on the broker.

Do not implement long delays with:

```python
time.sleep(3600)
```

inside a worker unless the workload and worker architecture explicitly support that resource usage.

---

## Scheduled Work

Long-term scheduling is often better handled by:

- Celery Beat;
- Kubernetes CronJobs;
- EventBridge;
- a dedicated scheduler.

A message queue is primarily a delivery mechanism; it does not necessarily provide durable calendar scheduling semantics.

---

## Queue Poisoning and Malicious Messages

Message consumers should treat broker messages as untrusted input.

Validate:

- schema;
- field types;
- payload size;
- identifiers;
- allowed event types;
- authorization context where applicable.

Do not deserialize arbitrary untrusted Python objects using `pickle`.

---

## Message Security

Use:

- TLS for broker connections;
- authentication;
- least-privilege credentials;
- network isolation;
- topic/queue-level permissions;
- encryption at rest where required;
- secret management;
- payload minimization.

Do not place credentials or sensitive data into messages unless there is a clear requirement and appropriate protection.

---

## Sensitive Data in Messages

Messages may persist longer than expected because of:

- retries;
- DLQs;
- broker retention;
- consumer lag;
- backups.

Therefore:

```text
message lifetime
```

may exceed:

```text
request lifetime
```

Minimize sensitive data in payloads.

Prefer identifiers and retrieve current authorized state when appropriate.

---

## Multi-Tenant Queues

For shared infrastructure, tenant context may be part of the message:

```json
{
  "tenant_id": "tenant_42",
  "event_type": "invoice.generate",
  "invoice_id": "inv_123"
}
```

Consumers must enforce tenant isolation.

Do not trust `tenant_id` merely because it exists in the message; authorization and data-access boundaries must still be enforced.

---

## Observability

A production messaging system should provide visibility into:

```text
Producer
  ↓
Publish latency
  ↓
Queue depth
  ↓
Queue age
  ↓
Consumer start
  ↓
Processing duration
  ↓
ACK / retry / DLQ
```

Useful metrics include:

- messages published;
- messages consumed;
- processing duration;
- queue depth;
- oldest message age;
- retry count;
- DLQ count;
- consumer errors;
- broker errors;
- acknowledgment latency.

---

## Correlation and Trace IDs

Messages should carry correlation information:

```json
{
  "message_id": "msg_123",
  "correlation_id": "req_456",
  "trace_id": "trace_789",
  "type": "order.created"
}
```

This allows a distributed trace to connect:

```text
HTTP Request
    ↓
Database Transaction
    ↓
Message
    ↓
Worker
    ↓
External API
```

Without correlation IDs, asynchronous debugging becomes significantly harder.

---

## Logging

A worker should log structured events such as:

```json
{
  "event": "message_processed",
  "message_id": "msg_123",
  "message_type": "order.created",
  "duration_ms": 37,
  "status": "success"
}
```

Avoid logging entire payloads when they contain sensitive or large data.

---

## Monitoring Queue Age

Queue depth can remain constant while latency changes.

For example:

```text
Queue depth = 1,000
```

is not enough information.

If processing is:

```text
100 msg/sec
```

the backlog is very different from:

```text
10 msg/sec
```

Measure age of the oldest message and processing latency.

---

## Alerting

Useful alerts include:

```text
queue age > SLO
queue depth growing continuously
DLQ rate increasing
consumer error rate increasing
consumer group lag increasing
broker unavailable
retry rate unusually high
```

Alerts should focus on user-visible impact and sustained abnormal behavior rather than every individual message failure.

---

## Consumer Lag

For Kafka, consumer lag represents how far a consumer group is behind the available log.

Conceptually:

```text
Latest offset
     │
     │  lag
     ↓
Consumer offset
```

Growing lag indicates that consumers are not keeping up with producers.

Lag should be evaluated together with:

- production rate;
- processing latency;
- partition distribution;
- consumer capacity.

---

## Message Processing SLOs

Asynchronous workloads need explicit objectives.

For example:

```text
99% of invoice jobs begin within 30 seconds
99% complete within 2 minutes
```

These are more meaningful than simply stating:

```text
queue should be fast
```

Queue age and processing duration should map directly to these objectives.

---

## Reliability Patterns

Useful production patterns include:

- idempotent consumers;
- transactional outbox;
- retries with backoff;
- dead-letter queues;
- bounded concurrency;
- graceful shutdown;
- durable message retention;
- schema versioning;
- correlation IDs;
- replay procedures;
- circuit breakers;
- poison-message isolation.

---

## Exactly-Once Business Effects

A practical strategy is often:

```text
At-least-once delivery
        +
idempotent consumer
        +
database uniqueness / transactions
        =
effectively-once business outcome
```

This is often more achievable than attempting to make every infrastructure component participate in one global exactly-once protocol.

---

## Replay

A durable queue or Kafka topic can allow messages to be replayed.

Replay is useful for:

- rebuilding projections;
- recovering from consumer bugs;
- populating a new service;
- backfilling derived data.

Replay requires consumers to tolerate historical messages and schema evolution.

Do not blindly replay production events against code that assumes only current state.

---

## Replay Safety

Before replaying messages, verify:

- idempotency;
- event schema compatibility;
- database constraints;
- downstream side effects;
- external API calls;
- rate limits;
- ordering assumptions.

A replay can otherwise send duplicate emails, duplicate webhooks, or repeat external operations.

---

## Event Retention

For event streams, retention determines how long consumers can recover or replay historical data.

Retention must balance:

```text
recovery capability
+
replay capability
-
storage cost
```

Longer retention is useful but increases storage requirements.

---

## Disaster Recovery

A production messaging architecture should define:

- broker replication;
- durability;
- backup strategy where applicable;
- cross-region strategy;
- message retention;
- replay procedures;
- consumer recovery;
- DLQ recovery;
- RPO;
- RTO.

For critical workflows, determine what happens if the broker is unavailable for:

```text
1 minute
1 hour
1 day
```

---

## Queue Availability vs Data Durability

Not every queue requires the same durability.

| Workload | Typical durability requirement |
|---|---|
| User notification | Recoverable, but potentially rebuildable |
| Payment processing | Very high |
| Analytics event | Often durable and replayable |
| Cache refresh | Low |
| Audit event | Very high |
| Temporary background computation | Workload-dependent |

The business consequence of message loss should drive infrastructure choices.

---

## Cost Considerations

Queue infrastructure costs include:

- broker capacity;
- storage;
- network traffic;
- replication;
- worker compute;
- retries;
- DLQ retention;
- observability;
- cross-region traffic.

Retries can be surprisingly expensive because one failed message can generate many additional operations.

Monitor retry volume as a cost signal as well as a reliability signal.

---

## Queue Capacity Planning

A simplified throughput model is:

```text
effective throughput
≈
worker concurrency
×
messages processed per worker per second
```

For example:

```text
20 workers
×
50 messages/sec
≈
1,000 messages/sec
```

This assumes the workload scales linearly, which often stops being true because of:

- database contention;
- external API limits;
- CPU saturation;
- broker bottlenecks;
- network limits.

Capacity testing should validate the actual system.

---

## Batch Consumption

When supported, consuming messages in batches can improve throughput.

```text
Receive 100 messages
      ↓
Batch database operation
      ↓
Commit
      ↓
ACK messages
```

Benefits include:

- fewer network round trips;
- fewer database transactions;
- better throughput.

Trade-offs include:

- higher memory usage;
- larger failure scope;
- increased retry complexity;
- longer processing latency.

---

## Batch Failure Semantics

If one message in a batch fails:

```text
Message 1 ✓
Message 2 ✓
Message 3 ✗
Message 4 ✓
```

the system needs a defined policy.

Possible approaches include:

- individual acknowledgment;
- partial batch acknowledgment;
- retry only failed messages;
- reject the entire batch.

The broker's capabilities and business semantics determine the appropriate strategy.

---

## Database Batch Processing

For high-throughput consumers:

```text
Queue
 ↓
Consumer
 ↓
Batch
 ↓
PostgreSQL
 ↓
Commit
 ↓
ACK
```

Batching can dramatically reduce transaction overhead.

However, avoid making batches so large that they create:

- long transactions;
- excessive memory usage;
- long lock durations;
- large retry units.

---

## Queue and REST APIs

A REST endpoint may return `202 Accepted` when work has been accepted for asynchronous processing.

Example:

```http
POST /reports
```

Response:

```http
HTTP/1.1 202 Accepted
Location: /reports/rpt_123
```

The client can later retrieve:

```http
GET /reports/rpt_123
```

A status resource can represent:

```text
queued
processing
completed
failed
```

---

## Queue and gRPC

gRPC can synchronously submit work:

```text
CreateReport()
     ↓
Queue
     ↓
Report Worker
```

The gRPC response can return an operation identifier instead of waiting for completion.

The same asynchronous semantics apply regardless of transport.

---

## Queue and Webhooks

Webhook delivery is a strong queue use case:

```text
Business Event
     ↓
Outbox
     ↓
Queue
     ↓
Webhook Worker
     ↓
External Client
```

The worker can implement:

- retries;
- exponential backoff;
- signatures;
- timeout limits;
- idempotency;
- delivery status;
- DLQ handling.

---

## Queue and Email

Email should often be asynchronous:

```text
API
 ↓
Database
 ↓
Queue
 ↓
Email Worker
 ↓
SMTP / Email Provider
```

This prevents slow email-provider responses from blocking API requests.

The worker should record delivery status where the business requires it.

---

## Queue and File Processing

Large file workflows can use:

```text
Upload → S3
          ↓
      queue message
          ↓
     processing worker
          ↓
      output artifact
```

The message contains a reference to the object rather than the file itself.

This avoids large broker payloads.

---

## Queue and Microservices

Queues can decouple microservices:

```text
Order Service
      ↓
Kafka
 ┌────┼────┐
 ↓    ↓    ↓
Inventory  Billing  Notifications
```

This reduces direct synchronous dependencies but introduces eventual consistency.

Microservices should not use queues merely to avoid designing clear service contracts.

---

## Eventual Consistency

Asynchronous processing means state may temporarily differ:

```text
Order Service
→ order = created

Inventory Service
→ still processing

Notification Service
→ not yet sent
```

Clients and business workflows must tolerate this state when appropriate.

If immediate consistency is required, a synchronous transactional workflow may be more suitable.

---

## Queue-Based State Machines

Long-running business workflows can be modeled explicitly:

```text
created
   ↓
payment_pending
   ↓
paid
   ↓
fulfillment_pending
   ↓
fulfilled
```

Each transition can produce a message.

Explicit states are preferable to relying on implicit assumptions about message processing order.

---

## Queue Ordering Is Not Business State

A message arriving first does not guarantee that its business state is still valid.

For example:

```text
OrderCreated
    ↓
OrderCancelled
    ↓
Worker receives OrderCreated late
```

The worker should validate current state when required rather than blindly applying historical instructions.

---

## Message Schema Validation

Python consumers should validate external messages.

For example, with Pydantic:

```python
from datetime import datetime

from pydantic import BaseModel


class OrderCreated(BaseModel):
    id: str
    type: str
    version: int
    occurred_at: datetime
    order_id: str
    customer_id: str
```

Schema validation should be separate from business-state validation.

---

## Consumer Architecture

A maintainable consumer can separate:

```text
Broker Adapter
      ↓
Message Validation
      ↓
Application Service
      ↓
Repository / External Clients
      ↓
Transaction
```

This keeps broker-specific APIs out of core business logic.

---

## Dependency Injection

A worker should depend on abstractions where practical:

```python
class OrderEventHandler:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier

    def handle(self, event: OrderCreated) -> None:
        order = self.repository.get(event.order_id)
        self.notifier.notify(order)
```

The broker consumer becomes an adapter rather than the location of business rules.

---

## Testing Consumers

Test at multiple levels.

### Unit Tests

Test:

- validation;
- business rules;
- idempotency;
- retry classification;
- error handling.

### Integration Tests

Test:

- real broker behavior where important;
- acknowledgment semantics;
- transaction behavior;
- serialization;
- retries;
- DLQ routing.

### End-to-End Tests

Test:

```text
Producer
 ↓
Broker
 ↓
Consumer
 ↓
Database
 ↓
External integration
```

for critical workflows.

---

## Consumer Test Example

```python
def test_duplicate_event_is_ignored(repository):
    event = OrderCreated(
        id="evt_123",
        type="order.created",
        version=1,
        occurred_at=datetime.now(UTC),
        order_id="ord_123",
        customer_id="cus_456",
    )

    repository.mark_processed.return_value = False

    handler.handle(event)

    repository.create_order.assert_not_called()
```

The exact mocking strategy should follow the application's testing architecture.

---

## Common Mistakes

### Assuming One Publish Means One Execution

At-least-once systems can deliver duplicates.

Design consumers to be idempotent.

### Acknowledging Before Commit

If the worker ACKs first and crashes before committing database state, the message may be lost.

Commit durable work before acknowledging.

### Retrying Everything

Permanent failures should not be retried indefinitely.

Classify errors.

### No DLQ

Poison messages can block healthy processing or generate endless retries.

### Unlimited Retries

A retry loop can create infinite workload and hide permanent failures.

Use bounded retries.

### No Queue Capacity Planning

Queues can absorb bursts but cannot compensate indefinitely for insufficient consumer capacity.

### Putting Large Payloads in Messages

Large messages increase memory, storage, network, and processing costs.

Store large objects in object storage and send references.

### Relying on Global Ordering

Distributed systems rarely provide useful global ordering at scale.

Define ordering per entity or partition where possible.

### Treating Kafka Like Redis

Kafka is an event log, not a low-latency key-value cache.

### Treating Redis Like a Durable Event Log

Redis can support queue workloads, but its durability and replay characteristics differ from dedicated event-streaming systems.

---

## Production Pitfalls

### Retry Storms

A downstream outage can cause every worker to retry simultaneously.

Use backoff, jitter, retry limits, and concurrency control.

### Consumer Lag

A healthy broker can still have severe application latency if consumers fall behind.

Monitor lag and queue age.

### Hot Partitions

Poor partition keys can prevent Kafka consumers from scaling effectively.

### Duplicate Side Effects

A worker retry can send the same email or charge an external system twice.

Use idempotency keys and durable operation records.

### Database Overload

Adding workers increases downstream database concurrency.

Worker scaling must respect PostgreSQL connection and query capacity.

### Graceful Shutdown Failures

Workers terminated by Kubernetes while processing messages can create duplicates unless acknowledgment and task interruption are handled correctly.

### Schema Incompatibility

Rolling deployments can place old and new consumers against the same queue.

Use backward-compatible schemas.

### DLQ Accumulation

A growing DLQ indicates unresolved production failures, not merely "handled errors."

### Unbounded Queue Growth

An indefinitely growing queue eventually becomes a reliability and storage problem.

Alert on queue age and sustained growth.

---

## Queue Selection

| Requirement | Good starting point |
|---|---|
| Simple Python background jobs | Celery + RabbitMQ/Redis |
| Managed AWS task queue | Amazon SQS |
| Durable event streaming | Kafka |
| High-throughput event pipelines | Kafka |
| Complex routing / traditional messaging | RabbitMQ |
| Small internal queue workload | Redis-backed queue |
| Public HTTP response caching | HTTP/CDN cache, not a message queue |

The final choice should consider operational ownership, ordering, retention, throughput, delivery semantics, replay, and ecosystem integration.

---

## Queue Design Checklist

Before introducing a queue, define:

- producer;
- consumer;
- message schema;
- message ID;
- delivery semantics;
- acknowledgment behavior;
- retry policy;
- maximum attempts;
- backoff;
- DLQ;
- ordering requirements;
- partitioning strategy;
- message retention;
- maximum message size;
- idempotency strategy;
- transaction boundary;
- database interaction;
- external side effects;
- observability;
- capacity limits;
- autoscaling;
- graceful shutdown;
- security;
- disaster recovery;
- replay procedure.

---

## Production Architecture Pattern

A robust order-processing architecture can look like:

```mermaid
flowchart TD
    C[Client] --> API[FastAPI / Django]
    API --> DB[(PostgreSQL)]

    DB --> OUTBOX[Transactional Outbox]
    OUTBOX --> BROKER[Kafka / RabbitMQ / SQS]

    BROKER --> PAYMENT[Payment Worker]
    BROKER --> EMAIL[Notification Worker]
    BROKER --> INDEX[Search Worker]

    PAYMENT --> PSP[Payment Provider]
    EMAIL --> EMAILP[Email Provider]
    INDEX --> SEARCH[Search Store]

    BROKER --> DLQ[Dead Letter Queue]
```

The key boundaries are:

```text
PostgreSQL
→ authoritative business state

Outbox
→ durable event handoff

Broker
→ asynchronous delivery

Workers
→ side effects / processing

DLQ
→ failed-message isolation
```

---

## Operational Best Practices

- Define delivery semantics explicitly.
- Assume duplicate delivery unless exactly-once behavior is rigorously guaranteed within the entire workflow.
- Make consumers idempotent.
- ACK only after required durable work succeeds.
- Use transactional outbox for critical database-to-message publication.
- Use bounded retries with exponential backoff and jitter.
- Route permanent failures to a DLQ.
- Monitor queue depth, queue age, processing latency, retries, and DLQ volume.
- Protect databases and external APIs with bounded consumer concurrency.
- Use correlation and trace IDs across asynchronous boundaries.
- Version message schemas.
- Keep messages small.
- Store large files in object storage.
- Design graceful worker shutdown.
- Test broker failure and consumer crash scenarios.
- Load-test cold, normal, burst, and degraded workloads.
- Document replay procedures before production incidents require them.
- Treat messages as untrusted input.
- Use TLS, authentication, authorization, and least-privilege broker access.
- Include asynchronous processing in SLO, capacity, and disaster-recovery planning.

## Key Takeaways

- **Message queues decouple producers from asynchronous work:** they reduce request latency, absorb bursts, and allow workers to scale independently, but they introduce eventual consistency and distributed failure modes.
- **Assume messages can be duplicated:** at-least-once delivery is common, so consumers should be idempotent and durable side effects should be protected with transactions, unique constraints, or idempotency keys.
- **Reliability requires explicit failure handling:** use bounded retries, exponential backoff with jitter, dead-letter queues, graceful shutdown, and clear acknowledgment semantics.
- **Database and messaging consistency needs deliberate architecture:** use transactional outbox patterns when PostgreSQL state and message publication must remain reliably correlated.
- **Operate queues as capacity systems:** monitor queue age, depth, consumer lag, processing latency, retries, and downstream saturation; scale workers without exceeding database or external-service capacity.