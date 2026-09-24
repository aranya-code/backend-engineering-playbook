# 10- Change Streams in Python

## Overview

MongoDB Change Streams provide a database-level mechanism for observing changes to data without continuously polling collections.

A change stream can expose events such as:

- Document insertion
- Document update
- Document replacement
- Document deletion
- Collection or database changes
- Deployment-wide changes, depending on the stream scope

For backend systems, change streams are useful when MongoDB mutations need to trigger downstream processing:

```text
MongoDB
   ↓
Change Stream
   ↓
Python Consumer
   ├── Kafka
   ├── Redis
   ├── Celery
   ├── Search Index
   ├── Cache Invalidation
   └── External Integration
```

A typical event-driven architecture is:

```mermaid
flowchart LR
    API[Backend API]
    Mongo[(MongoDB)]
    CS[Change Stream]
    Consumer[Python Consumer]
    Kafka[Kafka]
    Worker[Background Workers]
    Search[Search / Read Model]
    Cache[Redis]

    API --> Mongo
    Mongo --> CS
    CS --> Consumer
    Consumer --> Kafka
    Kafka --> Worker
    Worker --> Search
    Worker --> Cache
```

Change streams are particularly valuable when polling would introduce unnecessary database load, latency, or complicated change-detection logic.

They are not a general-purpose message broker. They provide database change notifications, while systems such as Kafka provide broader event-streaming capabilities, durable independent event retention, partitioning, and consumer-group semantics.

## What Is a Change Stream?

A change stream is a continuously available cursor over MongoDB changes.

Conceptually:

```text
Application writes document
        ↓
MongoDB records the operation
        ↓
Replication/change stream infrastructure
        ↓
Change stream cursor
        ↓
Consumer receives event
```

A Python application can subscribe to the stream:

```python
with collection.watch() as stream:
    for change in stream:
        print(change)
```

The consumer remains connected and waits for new changes.

Unlike polling:

```python
while True:
    changes = collection.find({
        "updated_at": {"$gt": last_seen}
    })
```

a change stream lets MongoDB notify the consumer when relevant changes become available.

## Why Change Streams Exist

Traditional polling has several problems:

```text
Every N seconds
      ↓
Query database
      ↓
Did anything change?
      ↓
No → repeat
```

This can create:

- Unnecessary database queries
- Increased latency
- Duplicate processing
- Difficult checkpointing
- Race conditions
- Complex timestamp logic
- Increased load as the number of consumers grows

Change streams provide a database-native change notification mechanism.

## Change Stream Requirements

Change streams depend on MongoDB's replication infrastructure.

They are supported on deployments such as:

- Replica sets
- Sharded clusters

A standalone MongoDB server is not the normal topology for production change streams.

For local development, use a replica-set-enabled MongoDB instance rather than assuming a basic standalone container is sufficient.

## Change Stream Scope

Change streams can be opened at different scopes.

| Scope | Python API | Use case |
|---|---|---|
| Collection | `collection.watch()` | Monitor one collection |
| Database | `database.watch()` | Monitor collections in one database |
| Client/deployment | `client.watch()` | Monitor changes across databases and collections |

Prefer the narrowest scope that satisfies the requirement.

For example:

```python
collection.watch()
```

is usually preferable to monitoring an entire deployment when only one collection matters.

## Collection-Level Change Stream

Example:

```python
with orders.watch() as stream:
    for change in stream:
        print(change)
```

This consumer receives changes from the `orders` collection.

Typical use cases:

- Order event processing
- Cache invalidation
- Search indexing
- Audit processing
- Read-model updates

## Database-Level Change Stream

A database-level stream can observe changes across collections in a database.

```python
with db.watch() as stream:
    for change in stream:
        print(change)
```

This is useful when multiple collections participate in a domain workflow.

For example:

```text
commerce database
 ├── orders
 ├── payments
 ├── inventory
 └── customers
```

A domain event processor may need to observe multiple collections.

## Deployment-Level Change Stream

At the client level:

```python
with client.watch() as stream:
    for change in stream:
        print(change)
```

This provides a broader event source.

Use this carefully because the volume can become significant in large deployments.

## Change Event Structure

A change stream event contains metadata describing the database change.

A simplified insert event can look like:

```json
{
  "_id": {
    "_data": "..."
  },
  "operationType": "insert",
  "clusterTime": "...",
  "wallTime": "...",
  "ns": {
    "db": "commerce",
    "coll": "orders"
  },
  "documentKey": {
    "_id": "order-1001"
  },
  "fullDocument": {
    "_id": "order-1001",
    "status": "created"
  }
}
```

The exact event fields depend on:

- Operation type
- MongoDB version
- Change stream options
- Requested lookup behavior
- Deployment configuration

## Operation Types

Common operation types include:

| Operation | Meaning |
|---|---|
| `insert` | New document inserted |
| `update` | Existing document updated |
| `replace` | Existing document replaced |
| `delete` | Document deleted |
| `invalidate` | Stream can no longer continue normally |
| `drop` | Collection was dropped |
| `rename` | Collection was renamed |
| `dropDatabase` | Database was dropped |

Application logic should explicitly handle the event types relevant to its use case.

## Insert Events

Example:

```json
{
  "operationType": "insert",
  "documentKey": {
    "_id": "order-1001"
  },
  "fullDocument": {
    "_id": "order-1001",
    "status": "created"
  }
}
```

An insert event can be used to trigger downstream processing.

Example:

```text
MongoDB insert
      ↓
Change stream
      ↓
Python consumer
      ↓
Publish order.created
```

## Update Events

An update event typically identifies the modified document and can contain update descriptions.

Example:

```json
{
  "operationType": "update",
  "documentKey": {
    "_id": "order-1001"
  },
  "updateDescription": {
    "updatedFields": {
      "status": "confirmed"
    },
    "removedFields": []
  }
}
```

This can be useful when downstream processing only needs the changed fields.

## Replace Events

A replacement operation replaces the entire document.

Example:

```python
collection.replace_one(
    {"_id": order_id},
    replacement_document,
)
```

The resulting change event has:

```json
{
  "operationType": "replace"
}
```

Do not assume an `update` event and a `replace` event have identical semantics.

## Delete Events

A delete event generally contains the document key:

```json
{
  "operationType": "delete",
  "documentKey": {
    "_id": "order-1001"
  }
}
```

The deleted document itself is not automatically available simply because the delete event exists.

If the downstream consumer needs the deleted document's contents, design the system accordingly.

## Full Document Lookup

For update events, consumers can request the current document using change stream options.

Example:

```python
with collection.watch(
    full_document="updateLookup"
) as stream:
    for change in stream:
        print(change)
```

This can produce:

```json
{
  "operationType": "update",
  "documentKey": {
    "_id": "order-1001"
  },
  "fullDocument": {
    "_id": "order-1001",
    "status": "confirmed"
  }
}
```

### Important Limitation

`updateLookup` retrieves the document after the update when the lookup occurs. It should not be treated as a historical snapshot of exactly what the document looked like immediately after the original update.

This matters for rapidly changing documents.

If exact historical state is required, store the required state explicitly in the event or use an appropriate event-sourcing/audit architecture.

## Update Description

When only changed fields are required, `updateDescription` can reduce the need to retrieve the full document.

Example:

```python
with collection.watch() as stream:
    for change in stream:
        if change["operationType"] == "update":
            updated = change["updateDescription"]["updatedFields"]
            print(updated)
```

This can be more efficient than requesting the complete document for every update.

## Resume Tokens

A change stream event contains a resume token.

Example:

```python
with collection.watch() as stream:
    for change in stream:
        resume_token = change["_id"]
        process(change)
```

The token identifies a position in the change stream.

A consumer can use it to resume processing after a restart.

Conceptually:

```text
Event A
Event B
Event C
Event D
Event E
       ↑
  Last processed
```

After restart:

```text
Resume from Event D
       ↓
Event E
```

This is one of the most important features for production consumers.

## Resume Token vs Document ID

Do not confuse:

```text
Change stream resume token
```

with:

```text
document _id
```

They represent different concepts.

A resume token represents a position in the change stream.

A document `_id` identifies the MongoDB document.

## Storing Resume Tokens

For production systems, the resume position should be persisted somewhere durable.

Possible storage mechanisms include:

- Dedicated MongoDB checkpoint collection
- Durable application state store
- Consumer-specific metadata storage

Example document:

```json
{
  "_id": "orders-consumer",
  "resume_token": {
    "_data": "..."
  },
  "updated_at": "2026-09-22T10:00:00Z"
}
```

The checkpoint should only advance after the corresponding event has been processed successfully.

## At-Least-Once Processing

Change stream consumers should generally be designed assuming an event may be processed more than once.

Consider:

```text
Read event
 ↓
Process event
 ↓
Application crashes
 ↓
Resume from previous checkpoint
 ↓
Process event again
```

Therefore:

```text
Change stream
    ↓
At-least-once application processing
    ↓
Idempotent consumer
```

Do not assume exactly-once processing simply because MongoDB provides ordered change stream events.

## Idempotent Consumers

A consumer should safely handle duplicate processing.

For example, use a deterministic event identifier:

```python
event_id = str(change["_id"])
```

Store processed-event metadata when appropriate:

```json
{
  "_id": "event-id",
  "processed_at": "2026-09-22T10:00:00Z"
}
```

However, storing a processed marker and performing the business side effect must itself be designed carefully.

A naive sequence:

```text
Process side effect
 ↓
Store processed marker
```

can still duplicate the side effect if the process crashes between the two operations.

For strong consistency, combine the side effect and checkpoint in one transaction where both operations are inside the same MongoDB deployment and transaction semantics are appropriate.

## Exactly-Once Processing

Do not casually claim that a change stream consumer provides exactly-once processing.

A more realistic model is:

```text
MongoDB change stream
        ↓
At-least-once delivery/processing model
        ↓
Idempotent application
        ↓
Effectively-once business outcome
```

Exactly-once business effects depend on the complete architecture.

## Python and PyMongo

PyMongo provides change stream support through `watch()`.

Basic example:

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017/?replicaSet=rs0"
)

collection = client["commerce"]["orders"]

with collection.watch() as stream:
    for change in stream:
        print(change)
```

The cursor blocks while waiting for new changes.

This is expected behavior.

## Long-Running Consumers

A change stream consumer is typically a long-running process:

```text
Process starts
     ↓
Connect to MongoDB
     ↓
Open change stream
     ↓
Wait for events
     ↓
Process event
     ↓
Continue
```

This is different from normal request/response code.

Do not create a new change stream for every HTTP request.

## Consumer Architecture

A production deployment can use a dedicated worker:

```mermaid
flowchart TD
    Mongo[(MongoDB)]
    Stream[Change Stream]
    Consumer[Python Change Stream Consumer]
    Handler[Event Handler]
    Kafka[Kafka]
    Redis[Redis]
    Search[Search Index]

    Mongo --> Stream
    Stream --> Consumer
    Consumer --> Handler
    Handler --> Kafka
    Handler --> Redis
    Handler --> Search
```

The consumer should be deployed independently from the API service when its lifecycle and scaling characteristics differ.

## FastAPI Considerations

A FastAPI application can start a background consumer during application startup, but this requires careful process and deployment design.

For example:

```text
FastAPI worker
 ├── HTTP server
 └── Change stream consumer
```

This can become problematic when Kubernetes runs multiple replicas:

```text
Pod 1 → consumer
Pod 2 → consumer
Pod 3 → consumer
```

All three consumers may process the same change stream independently.

That may be acceptable if each consumer is intentionally part of a fan-out architecture, but it is usually undesirable when the goal is one logical processor.

For production systems, a dedicated worker deployment is often clearer:

```text
Kubernetes
 ├── API Deployment
 │    ├── Pod
 │    ├── Pod
 │    └── Pod
 │
 └── Change Stream Deployment
      └── Consumer Pod(s)
```

## Async Python

For asynchronous applications, current PyMongo provides `AsyncMongoClient`.

Conceptually:

```python
from pymongo import AsyncMongoClient


async def consume(client):
    collection = client["commerce"]["orders"]

    async with collection.watch() as stream:
        async for change in stream:
            await handle_change(change)
```

Use the asynchronous client when the surrounding architecture is async.

Do not block an asyncio event loop with synchronous MongoDB operations.

## Async Consumer Lifecycle

An async consumer should have explicit startup and shutdown behavior:

```text
Application startup
       ↓
Create MongoDB client
       ↓
Open change stream
       ↓
Consume events
       ↓
Cancellation / shutdown
       ↓
Close stream
       ↓
Close client
```

Graceful shutdown is important in Kubernetes so that termination does not repeatedly interrupt processing at arbitrary points.

## Django Considerations

A Django application can use PyMongo directly for change streams.

However, the change stream consumer should generally not run as part of every Django web worker.

Prefer:

```text
Django API
     │
     └── MongoDB
            ↑
      Change Stream Worker
```

Run the consumer as a separate process, management command, or worker deployment depending on the deployment architecture.

## Change Streams and Celery

A change stream can feed Celery:

```text
MongoDB
   ↓
Change Stream
   ↓
Python Consumer
   ↓
Celery
   ↓
Workers
```

Example:

```python
from celery import Celery

celery_app = Celery("events")


@celery_app.task
def process_order_event(change):
    ...
```

The change stream consumer can enqueue work rather than performing expensive processing directly.

This helps keep the stream consumer responsive.

## Change Streams and Kafka

Change streams can act as a bridge from MongoDB to Kafka:

```text
MongoDB
   ↓
Change Stream
   ↓
Python Connector
   ↓
Kafka
   ├── Search consumer
   ├── Analytics consumer
   └── Notification consumer
```

This architecture is useful when multiple independent downstream systems need the same database changes.

Kafka becomes the durable event distribution layer rather than forcing the MongoDB change stream consumer to perform every downstream operation itself.

## Change Streams vs Kafka

| Concern | MongoDB Change Streams | Kafka |
|---|---|---|
| Primary purpose | Observe MongoDB changes | Distributed event streaming |
| Source | MongoDB | Any producer |
| Persistence model | Based on MongoDB replication/change stream history | Independent event log |
| Consumer groups | Not equivalent to Kafka consumer groups | Native |
| Partitioning | Not Kafka-style partitioning | Core feature |
| Replay model | Resume from MongoDB change stream position subject to oplog/history availability | Retention-based replay |
| Best use | React to MongoDB changes | Distribute events across many systems |
| Event ownership | Database-derived | Application/event-platform derived |

Change streams and Kafka can complement each other.

## Change Streams vs Polling

| Concern | Change Streams | Polling |
|---|---|---|
| Database queries | Event-driven | Repeated queries |
| Latency | Typically low | Polling interval dependent |
| Database load | Lower for idle workloads | Repeatedly generated |
| Checkpointing | Resume tokens | Application-defined |
| Duplicate handling | Still required | Usually required |
| Infrastructure | Requires supported MongoDB topology | Works with ordinary queries |
| Historical replay | Limited by available stream history | Depends on query model |
| Best use | Near-real-time change processing | Simple periodic synchronization |

## Filtering Events

Do not process every change if only a subset matters.

Use an aggregation pipeline with `watch()`.

Example:

```python
pipeline = [
    {
        "$match": {
            "operationType": {
                "$in": ["insert", "update"]
            }
        }
    }
]

with collection.watch(pipeline) as stream:
    for change in stream:
        process(change)
```

Filtering at the change stream level can reduce unnecessary application work.

## Filtering by Document Fields

Change stream pipelines can also filter based on event content.

For example:

```python
pipeline = [
    {
        "$match": {
            "operationType": "update",
            "updateDescription.updatedFields.status": "confirmed",
        }
    }
]
```

This is useful for workflows such as:

```text
Order status changes to confirmed
        ↓
Trigger downstream processing
```

Be careful with complex filters because the stream consumer should remain efficient and operationally simple.

## Change Stream Options

Common options include:

| Option | Purpose |
|---|---|
| `full_document` | Controls full-document lookup behavior for updates |
| `full_document_before_change` | Requests pre-image data where supported/configured |
| `resume_after` | Resume from a stored resume token |
| `start_after` | Start after a specified resume point |
| `start_at_operation_time` | Start from a specific operation time |
| `batch_size` | Controls cursor batch behavior |
| `max_await_time_ms` | Controls how long the server may wait for new data |

Exact support depends on MongoDB and PyMongo versions.

## Resume After

A stored resume token can be supplied when reopening the stream.

Conceptually:

```python
resume_token = load_resume_token()

with collection.watch(
    resume_after=resume_token
) as stream:
    for change in stream:
        process(change)
```

This is the basic mechanism for recovering after process restarts.

## Start After

`start_after` is useful when the application wants to resume after a token while allowing certain stream lifecycle events to be handled differently.

The exact semantics differ from `resume_after`.

Use the PyMongo and MongoDB documentation for the exact behavior required by the application version.

## Start at Operation Time

A stream can also start at an operation time where supported.

Conceptually:

```python
with collection.watch(
    start_at_operation_time=operation_time
) as stream:
    ...
```

This is useful when rebuilding a consumer from a known temporal position.

It should not be treated as an unlimited historical event store.

## Change Stream History and Oplog

Change streams depend on MongoDB's replication history.

The practical consequence is important:

```text
Consumer offline
      ↓
Resume token
      ↓
Required history still available
      ↓
Resume successfully
```

But:

```text
Consumer offline for too long
      ↓
Required history no longer available
      ↓
Resume may fail
      ↓
Rebuild/resynchronization required
```

Therefore, a production architecture needs a recovery strategy beyond simply storing a resume token.

## Resynchronization Strategy

A robust consumer should have a plan for resume failure.

Example:

```text
Start consumer
      ↓
Load checkpoint
      ↓
Resume stream
      │
      ├── Success → Process normally
      │
      └── Resume failure
             ↓
       Reconciliation
             ↓
       Rebuild state
             ↓
       Start new stream
```

The reconciliation strategy depends on the business system.

For a search index:

```text
MongoDB source of truth
        ↓
Full/incremental rebuild
        ↓
Search index
```

## Event Ordering

Change streams provide ordering semantics within the stream, but application-level processing can destroy ordering.

Example:

```text
MongoDB:
A → B → C
```

If the consumer sends events to parallel workers:

```text
Worker 1 → A
Worker 2 → B
Worker 3 → C
```

they may complete:

```text
B → C → A
```

If ordering matters, the downstream architecture must preserve the required ordering.

Do not assume change stream ordering automatically applies to asynchronous workers.

## Parallel Processing

A common scaling strategy is:

```text
Change Stream
      ↓
Dispatcher
 ├── Worker 1
 ├── Worker 2
 ├── Worker 3
 └── Worker 4
```

This increases throughput but introduces:

- Ordering concerns
- Duplicate processing
- Checkpoint coordination
- Backpressure
- Failure recovery complexity

If event ordering matters per entity, partition by a stable key such as:

```text
customer_id
```

or:

```text
order_id
```

before parallel processing.

## Backpressure

A slow downstream system can cause the change stream consumer to fall behind.

Example:

```text
MongoDB
   ↓
Change Stream
   ↓
Consumer
   ↓
Slow API
```

The consumer may accumulate processing lag.

Use a durable intermediary such as Kafka or a task queue when downstream work is expensive or bursty.

Architecture:

```text
MongoDB
   ↓
Change Stream
   ↓
Fast Consumer
   ↓
Kafka
   ↓
Workers
```

This separates database event capture from downstream processing.

## Change Stream Consumer State

A production consumer should maintain state such as:

```text
Consumer identity
Last successful resume token
Last processed event timestamp
Processing lag
Error count
Retry count
```

Example checkpoint model:

```json
{
  "_id": "order-indexer",
  "resume_token": {
    "_data": "..."
  },
  "last_processed_at": "2026-09-22T10:00:00Z",
  "status": "healthy"
}
```

Do not update the checkpoint before the event's required processing has succeeded.

## Checkpointing Strategy

The safest conceptual sequence is:

```text
Read event
    ↓
Process event
    ↓
Confirm processing succeeded
    ↓
Persist checkpoint
```

If the process fails before checkpoint persistence:

```text
Event may be processed again
```

That is acceptable when the consumer is idempotent.

The dangerous sequence is:

```text
Read event
    ↓
Persist checkpoint
    ↓
Process event
    ↓
Crash
```

The event may be skipped permanently after restart.

## Error Handling

Separate errors into categories.

| Error | Typical response |
|---|---|
| Validation/business error | Dead-letter or record failure |
| Temporary downstream failure | Retry |
| MongoDB transient error | Reconnect/resume where supported |
| Duplicate event | Treat idempotently |
| Invalid resume position | Reconcile/rebuild |
| Poison event | Isolate and alert |

Do not let one malformed event permanently kill the consumer without alerting and recovery.

## Dead-Letter Handling

For downstream systems that can reject an event:

```text
Change Stream
      ↓
Consumer
      ↓
Processing
   ┌──┴──┐
Success Failure
  ↓       ↓
Done    Dead Letter
```

A dead-letter collection or Kafka topic can preserve problematic events for investigation.

Do not silently discard failed events.

## Poison Messages

A poison event repeatedly fails:

```text
Event
 ↓
Failure
 ↓
Retry
 ↓
Failure
 ↓
Retry
```

This can create an infinite retry loop.

Use:

- Maximum retry attempts
- Backoff
- Dead-letter handling
- Alerting
- Manual replay procedures

## Change Streams and Transactions

Change streams can observe changes committed through MongoDB transactions.

A transaction can produce multiple document changes:

```text
Transaction
 ├── Update order
 ├── Update inventory
 └── Insert audit
        ↓
      COMMIT
        ↓
Change stream events
```

Applications should understand the transaction event semantics rather than assuming each event represents an independently committed business operation.

When transactional grouping matters, design the event processing model around the transaction metadata available in the change event.

## Change Streams and Outbox Patterns

There are two related architectural approaches.

### Change Stream as Event Source

```text
MongoDB business data
       ↓
Change Stream
       ↓
Event processing
```

This is useful when the event is fundamentally derived from database state changes.

### Transactional Outbox

```text
MongoDB transaction
 ├── Business state
 └── Outbox event
          ↓
      Publisher
          ↓
         Kafka
```

The outbox approach provides explicit application-owned event payloads and event semantics.

Use an outbox when downstream consumers need a stable domain event contract rather than raw database change events.

## Change Streams vs Domain Events

A MongoDB change event is not necessarily a domain event.

Example change:

```json
{
  "operationType": "update",
  "updateDescription": {
    "updatedFields": {
      "status": "confirmed"
    }
  }
}
```

A domain event might be:

```json
{
  "event_type": "order.confirmed",
  "order_id": "order-1001",
  "occurred_at": "2026-09-22T10:00:00Z"
}
```

The second expresses business meaning explicitly.

A change stream can be used to derive domain events, but the two concepts should not be conflated.

## Security

Change stream consumers require MongoDB permissions appropriate to the resources they access.

Use:

- Dedicated service accounts
- Least-privilege roles
- TLS
- Network restrictions
- Secret management
- Credential rotation

Do not give a consumer broad administrative privileges simply because it needs to observe changes.

## Credential Management

Avoid:

```python
MongoClient(
    "mongodb://admin:password@mongodb:27017"
)
```

in source code.

Prefer:

```python
import os

mongo_uri = os.environ["MONGODB_URI"]
client = MongoClient(mongo_uri)
```

In production, obtain the secret through the platform's secret-management mechanism.

Examples include:

- Kubernetes Secrets with appropriate protection
- AWS Secrets Manager
- Environment injection from a secret manager
- MongoDB Atlas secret/configuration integrations

## Monitoring Change Stream Consumers

Monitor the consumer independently from MongoDB.

Important metrics include:

| Metric | Why it matters |
|---|---|
| Events processed | Throughput |
| Processing failures | Reliability |
| Retry count | Downstream health |
| Processing latency | Consumer performance |
| Event lag | Freshness |
| Resume failures | Recovery health |
| Reconciliation count | Data consistency |
| Queue depth | Backpressure |
| Consumer restarts | Deployment/process stability |

## Measuring Event Lag

A useful application metric is:

```text
Event processing lag =
Current time - event time
```

Track this over time.

Example:

```text
0-1 seconds   → healthy
1-10 seconds  → investigate
10+ seconds   → operational issue
```

Do not use fixed thresholds blindly. Define acceptable lag based on the application's SLA.

## Logging

Use structured logs.

Example:

```python
logger.info(
    "change_event_processed",
    extra={
        "operation_type": change["operationType"],
        "collection": change["ns"]["coll"],
        "document_id": str(change["documentKey"]["_id"]),
    },
)
```

Avoid logging full documents when they may contain sensitive information.

## Distributed Tracing

If a change stream triggers downstream services:

```text
MongoDB
   ↓
Consumer
   ↓
Kafka
   ↓
Worker
   ↓
REST/gRPC service
```

Propagate correlation or trace identifiers where possible.

This makes asynchronous workflows easier to diagnose.

## Kubernetes Deployment

A dedicated deployment is often preferable:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb-change-consumer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mongodb-change-consumer
  template:
    metadata:
      labels:
        app: mongodb-change-consumer
    spec:
      containers:
        - name: consumer
          image: example/change-consumer:1.0.0
          env:
            - name: MONGODB_URI
              valueFrom:
                secretKeyRef:
                  name: mongodb
                  key: uri
```

The replica count should be based on the application's event-processing model.

If multiple replicas independently consume the same change stream, duplicate downstream effects may occur unless that fan-out behavior is intentional and idempotency is guaranteed.

## High Availability

A production consumer should handle:

- MongoDB primary elections
- Network interruptions
- Consumer restarts
- Pod termination
- Temporary downstream outages
- Resume failures

A robust lifecycle is:

```text
Connect
 ↓
Open stream
 ↓
Process
 ↓
Temporary failure
 ↓
Reconnect
 ↓
Resume
 ↓
Continue
```

Use bounded retry delays with backoff rather than a tight reconnect loop.

## Graceful Shutdown

Kubernetes may terminate a consumer during deployment.

The consumer should:

1. Stop accepting new work.
2. Finish or safely interrupt the current event.
3. Persist the checkpoint after successful processing.
4. Close the change stream.
5. Close the MongoDB client.
6. Exit cleanly.

Conceptually:

```text
SIGTERM
  ↓
Stop intake
  ↓
Finish current event
  ↓
Checkpoint
  ↓
Close stream
  ↓
Exit
```

## Performance Considerations

Change stream performance depends on:

- Number of changes
- Event size
- Filter complexity
- Full-document lookup usage
- Consumer processing time
- Network latency
- Downstream workload
- Number of consumers
- MongoDB deployment capacity

Avoid requesting full documents when the consumer only needs the changed fields.

## Large Documents

Large documents create larger change events and increase:

- Network bandwidth
- Deserialization cost
- Memory usage
- Downstream processing time

If event consumers need only a few fields, consider whether the change-stream event itself can provide enough information without retrieving the full document.

## Hot Collections

A high-write collection can generate a large stream:

```text
10,000 writes/sec
      ↓
Large change stream
      ↓
Consumer bottleneck
```

At high volume, consider:

- Filtering at the stream
- Fast event capture
- Kafka as an intermediary
- Horizontal worker scaling
- Partitioning downstream processing
- Backpressure controls

## Change Stream Scaling

Change stream scaling is different from HTTP scaling.

Scaling an API from:

```text
3 pods → 10 pods
```

does not automatically mean a change stream should also become:

```text
3 consumers → 10 consumers
```

Instead, define the desired event-processing topology:

```text
MongoDB
   ↓
One logical capture layer
   ↓
Kafka
 ┌─┼─┐
 ↓ ↓ ↓
Workers
```

This often scales more predictably.

## Cost Considerations

Change streams can reduce polling-related database load, but downstream infrastructure still consumes resources.

Potential costs include:

- Consumer compute
- Network traffic
- Kafka infrastructure
- Logging
- Metrics
- Search/indexing workloads
- Additional MongoDB resource consumption

Avoid deploying a broad client-level stream when a collection-level stream is sufficient.

## Disaster Recovery

Change stream consumers should have a recovery plan.

At minimum define:

- Resume token persistence
- Resume failure handling
- Reconciliation process
- Consumer restart behavior
- Dead-letter recovery
- Data consistency verification

A resume token alone is not a disaster recovery strategy.

## Reconciliation

For systems such as search indexes or caches, periodic reconciliation can provide an additional correctness mechanism.

Example:

```text
Normal operation
MongoDB → Change Stream → Search

Periodic reconciliation
MongoDB → Compare → Search
```

This detects missed events, processing bugs, and inconsistent downstream state.

## Testing

A realistic test environment should use a MongoDB deployment that supports change streams.

Test:

- Insert events
- Update events
- Replace events
- Delete events
- Event filtering
- Resume behavior
- Consumer restart
- Duplicate processing
- Transient MongoDB errors
- Primary elections
- Downstream failures
- Dead-letter handling
- Graceful shutdown

## Integration Test Example

```python
def test_change_stream_receives_insert(client):
    collection = client["test_db"]["orders"]

    with collection.watch() as stream:
        collection.insert_one(
            {
                "_id": "order-1001",
                "status": "created",
            }
        )

        change = next(stream)

    assert change["operationType"] == "insert"
    assert change["documentKey"]["_id"] == "order-1001"
```

In production-grade test suites, avoid relying on timing-sensitive assumptions. Use controlled test infrastructure and explicit timeouts.

## Failure Injection

Senior-level testing should intentionally introduce failures.

Examples:

```text
Consumer crashes after processing
        ↓
Restart
        ↓
Verify duplicate safety
```

```text
MongoDB primary changes
        ↓
Consumer reconnects
        ↓
Verify resume
```

```text
Kafka unavailable
        ↓
Consumer retries
        ↓
Verify no event loss
```

Failure injection exposes problems that happy-path integration tests often miss.

## Troubleshooting

### Consumer Cannot Open Change Stream

```text
Symptom
↓
watch() fails or stream cannot be established
↓
Possible causes
    - Unsupported MongoDB topology
    - Authentication/authorization problem
    - TLS configuration problem
    - Invalid connection string
    - Network connectivity problem
    - MongoDB deployment unavailable
↓
Isolation strategy
↓
Verify MongoDB deployment topology
↓
Verify connectivity with mongosh
↓
Verify credentials and roles
↓
Inspect server logs
↓
Root cause
↓
Corrective action
    - Use supported replica-set/sharded deployment
    - Fix credentials
    - Fix TLS/network configuration
↓
Prevention
    - Production topology validation
    - Connection health checks
    - Automated integration tests
```

### Consumer Keeps Reprocessing Events

```text
Symptom
↓
Same event is processed repeatedly
↓
Possible causes
    - Checkpoint saved before processing
    - Checkpoint never saved after success
    - Consumer crashes after side effect
    - Non-idempotent handler
↓
Isolation strategy
↓
Inspect checkpoint lifecycle
↓
Compare event IDs with stored checkpoints
↓
Inspect consumer restart logs
↓
Root cause
↓
Corrective action
    - Checkpoint after successful processing
    - Make handler idempotent
    - Use stable event identifiers
↓
Prevention
    - Failure-injection tests
    - Explicit checkpoint contract
```

### Consumer Falls Behind

```text
Symptom
↓
Event processing lag increases
↓
Possible causes
    - Slow handler
    - Downstream service latency
    - Large events
    - Full-document lookups
    - Insufficient worker capacity
    - High MongoDB write volume
↓
Isolation strategy
↓
Measure event rate
↓
Measure handler latency
↓
Measure downstream latency
↓
Inspect event size
↓
Root cause
↓
Corrective action
    - Filter events
    - Remove unnecessary full-document lookups
    - Add worker capacity
    - Introduce Kafka/task queue
↓
Prevention
    - Lag monitoring
    - Capacity testing
    - Backpressure strategy
```

### Resume Fails After Long Downtime

```text
Symptom
↓
Consumer cannot resume from stored token
↓
Possible causes
    - Required replication history is no longer available
    - Invalid/expired resume position
    - Deployment changes
↓
Isolation strategy
↓
Inspect MongoDB error
↓
Check replication history availability
↓
Verify stored resume token
↓
Root cause
↓
Corrective action
    - Reconcile downstream state
    - Perform controlled rebuild
    - Establish a new stream position
↓
Prevention
    - Consumer health monitoring
    - Recovery runbooks
    - Periodic reconciliation
```

### Duplicate Downstream Effects

```text
Symptom
↓
One MongoDB change causes multiple downstream effects
↓
Possible causes
    - Multiple consumers
    - Consumer restart
    - At-least-once processing
    - Kubernetes replica scaling
↓
Isolation strategy
↓
Inspect consumer topology
↓
Compare event identifiers
↓
Inspect deployment replica count
↓
Root cause
↓
Corrective action
    - Introduce idempotency
    - Correct consumer topology
    - Use Kafka consumer groups where appropriate
↓
Prevention
    - Explicit event ownership
    - Duplicate-processing tests
```

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Treating change streams as Kafka | Database events look like a message stream | Use Kafka when independent event streaming is required |
| Assuming exactly-once processing | Confusing database ordering with application processing | Design idempotent consumers |
| Saving checkpoint before processing | Optimizing checkpoint writes incorrectly | Checkpoint after successful processing |
| Running consumer in every API pod | API and consumer lifecycle are coupled | Deploy a dedicated consumer |
| Ignoring resume failures | Assuming tokens remain valid indefinitely | Implement reconciliation |
| Using full-document lookup everywhere | Easier event handling | Request full documents only when needed |
| Performing expensive work in stream loop | Consumer falls behind | Delegate work to workers/queues |
| Ignoring ordering | Parallel workers reorder events | Partition by entity when ordering matters |
| Blindly retrying poison events | Infinite retry loop | Use bounded retries and dead-letter handling |
| Logging entire documents | Convenient debugging | Log safe structured metadata |

## Production Architecture

A robust architecture for a moderate-to-high-volume backend can be:

```mermaid
flowchart LR
    API[FastAPI / Django]
    Mongo[(MongoDB Replica Set / Cluster)]
    CS[Change Stream Consumer]
    Kafka[Kafka]
    Workers[Python Workers]
    Redis[Redis]
    Search[Search / Read Model]
    DLQ[Dead Letter Topic]

    API --> Mongo
    Mongo --> CS
    CS --> Kafka
    Kafka --> Workers
    Workers --> Redis
    Workers --> Search
    Workers --> DLQ
```

Responsibilities are separated:

| Component | Responsibility |
|---|---|
| MongoDB | Source of truth |
| Change stream consumer | Capture database changes |
| Kafka | Durable event distribution |
| Workers | Business/event processing |
| Redis | Cache/read acceleration |
| Search | Derived read model |
| Dead-letter system | Failed-event isolation |

This architecture is preferable when downstream processing is expensive or multiple consumers require the same event stream.

## Change Stream Design Checklist

### Stream Configuration

- [ ] Use the narrowest appropriate stream scope.
- [ ] Filter irrelevant events.
- [ ] Configure full-document lookup only when needed.
- [ ] Understand resume-token behavior.
- [ ] Verify deployment topology supports change streams.

### Consumer Reliability

- [ ] Persist resume state durably.
- [ ] Process before checkpointing.
- [ ] Make processing idempotent.
- [ ] Handle transient MongoDB failures.
- [ ] Handle resume failures.
- [ ] Implement dead-letter handling.
- [ ] Test graceful shutdown.

### Performance

- [ ] Monitor event processing lag.
- [ ] Keep handlers lightweight.
- [ ] Avoid unnecessary full-document lookups.
- [ ] Introduce Kafka or a task queue for expensive workloads.
- [ ] Test expected event throughput.
- [ ] Monitor downstream bottlenecks.

### Production Operations

- [ ] Monitor consumer restarts.
- [ ] Monitor event lag.
- [ ] Monitor processing failures.
- [ ] Alert on resume failures.
- [ ] Maintain reconciliation procedures.
- [ ] Test primary elections and network failures.
- [ ] Document replay and recovery procedures.

## Interview Considerations

### What is a MongoDB Change Stream?

A change stream is a MongoDB mechanism for observing data changes in near real time without repeatedly polling collections.

### What deployment is required?

Change streams depend on MongoDB replication infrastructure and are intended for replica sets and sharded clusters rather than a basic standalone deployment.

### What is a resume token?

A resume token identifies a position in a change stream and allows a consumer to attempt to continue processing after a restart.

### Does a resume token guarantee that an event can always be replayed?

No. The required MongoDB replication history must still be available. A production consumer therefore needs a reconciliation strategy for cases where resumption is no longer possible.

### Are change streams exactly once?

No. Application processing should be designed for at-least-once behavior and idempotency.

### What is `fullDocument: "updateLookup"`?

It requests the current version of the updated document to be included with update events. It should not be treated as an immutable historical snapshot of the document immediately after the update.

### Should a change stream consumer run inside FastAPI?

It can, but this can create lifecycle and scaling problems when multiple web workers or Kubernetes replicas are running. A dedicated consumer deployment is often easier to operate.

### How would you scale change stream processing?

A common architecture is:

```text
MongoDB
   ↓
Change Stream Consumer
   ↓
Kafka
   ↓
Partitioned Consumers
```

The capture layer remains focused on reliably reading MongoDB changes while Kafka provides durable distribution and independent downstream scaling.

### Change streams or transactional outbox?

Use change streams when database changes themselves are the appropriate source of downstream events.

Use a transactional outbox when the application needs explicit domain-event contracts that are atomically written alongside business state.

### How do you prevent duplicate processing?

Use idempotent handlers and stable event identifiers. Persist processing state carefully and ensure the checkpoint is advanced only after successful processing.

## Key Takeaways

- **MongoDB Change Streams provide near-real-time observation of database changes and are useful for building event-driven backend workflows without polling.**
- **Production consumers must persist resume state, tolerate duplicate processing, and use idempotent handlers because application-level processing is not inherently exactly once.**
- **Keep change stream consumers lightweight; use Kafka, Celery, or another durable processing layer when downstream work is expensive, bursty, or requires independent scaling.**
- **Resume tokens are not a complete recovery strategy: consumers need reconciliation and rebuild procedures for cases where the required MongoDB replication history is no longer available.**
- **Treat change streams as database-derived events rather than a replacement for domain events or Kafka; choose the architecture based on event ownership, replay, ordering, durability, and downstream scaling requirements.**