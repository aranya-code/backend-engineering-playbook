# 11- MongoDB in Background Workers

## Overview

Background workers move MongoDB operations out of synchronous request paths and execute them asynchronously through systems such as Celery, task queues, scheduled jobs, or dedicated worker processes.

Typical architecture:

```text
API Request
    ↓
MongoDB / Task Queue
    ↓
Background Worker
    ↓
MongoDB
    ↓
External Services / Kafka / Redis
```

MongoDB is commonly used by workers for:

- Asynchronous business processing
- Scheduled jobs
- Batch processing
- Data synchronization
- Event processing
- Change stream consumers
- Search index updates
- Notifications
- Reconciliation
- ETL workloads
- Retryable workflows

The main engineering concern is not simply how to call MongoDB from a worker. It is how to make database access reliable when workers can be retried, duplicated, restarted, scaled horizontally, or terminated unexpectedly.

A production worker should therefore be designed around:

- Idempotency
- Connection lifecycle
- Retry behavior
- Transaction boundaries
- Atomic state transitions
- Concurrency control
- Timeouts
- Backpressure
- Observability
- Graceful shutdown
- Failure recovery

## Worker Architecture

A typical backend architecture is:

```mermaid
flowchart LR
    API[FastAPI / Django]
    Queue[Celery / Task Queue]
    Worker[Python Worker]
    Mongo[(MongoDB)]
    Redis[Redis]
    Kafka[Kafka]
    External[External Service]

    API --> Queue
    Queue --> Worker
    Worker --> Mongo
    Worker --> Redis
    Worker --> Kafka
    Worker --> External
```

The worker is a separate execution environment from the web application.

For example:

```text
Web Process
    └── Handles HTTP requests

Worker Process
    └── Handles background jobs

Scheduler
    └── Creates scheduled jobs

MongoDB
    └── Persistent application state
```

This separation allows worker capacity to be scaled independently.

## Why Use Background Workers with MongoDB?

A synchronous API should generally avoid performing long-running operations such as:

```text
HTTP request
    ↓
Read 500,000 MongoDB documents
    ↓
Transform documents
    ↓
Call external API
    ↓
Generate report
    ↓
Return response
```

Instead:

```text
HTTP request
    ↓
Create job
    ↓
Return 202 Accepted
    ↓
Worker processes job
```

The client can later retrieve job status.

## Background Worker Use Cases

| Use case | Worker benefit |
|---|---|
| Email processing | Avoid blocking HTTP request |
| Report generation | Long-running computation |
| Data synchronization | Retryable processing |
| Search indexing | Asynchronous derived state |
| MongoDB aggregation | Isolate expensive workload |
| External API integration | Retry and backoff |
| Scheduled cleanup | Run independently |
| Change stream processing | Long-lived consumer |
| Reconciliation | Periodic consistency checks |
| Batch migration | Controlled throughput |

## Worker Lifecycle

A worker typically follows:

```text
Process starts
    ↓
Load configuration
    ↓
Initialize MongoDB client
    ↓
Connect to task broker
    ↓
Receive task
    ↓
Execute task
    ↓
Commit database changes
    ↓
Acknowledge task
    ↓
Receive next task
```

A production worker should also handle:

```text
SIGTERM
   ↓
Stop accepting new work
   ↓
Finish or safely interrupt current work
   ↓
Close resources
   ↓
Exit
```

## PyMongo Client Lifecycle

A MongoDB client should normally be long-lived within a worker process.

Good:

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017",
    maxPoolSize=50,
)

db = client["commerce"]
orders = db["orders"]
```

The worker reuses the client for many tasks.

Avoid:

```python
def process_order(order_id):
    client = MongoClient("mongodb://localhost:27017")
    ...
```

Creating a new client for every task can cause:

- Excessive connection creation
- Connection churn
- Increased latency
- Increased server load
- Inefficient resource utilization

## Connection Pooling

Each `MongoClient` maintains connection pools.

The effective connection count depends on:

```text
Worker processes
    ×
MongoClient instances per process
    ×
Pool configuration
    ×
MongoDB topology
```

For example:

```text
4 worker processes
×
1 MongoClient/process
×
maxPoolSize 50
```

can potentially create a much larger connection footprint than expected when multiplied across multiple MongoDB servers and deployments.

The important principle is:

> Configure the pool based on total worker concurrency, not one process in isolation.

## One Client per Process

A common pattern is:

```text
Worker Process 1
 └── MongoClient 1

Worker Process 2
 └── MongoClient 2

Worker Process 3
 └── MongoClient 3
```

Each process owns its client and pool.

Do not unnecessarily create multiple clients for the same MongoDB deployment inside one worker process.

## Forking and Worker Processes

Process-based worker systems require careful client initialization.

Do not create a MongoDB client in a parent process and blindly reuse the same client across forked child processes.

Prefer:

```text
Worker process starts
    ↓
Initialize MongoClient
    ↓
Create connection pool
    ↓
Process tasks
```

This is especially important for process-based systems such as Celery prefork workers.

## Celery and MongoDB

A common architecture is:

```text
FastAPI / Django
      ↓
Celery Broker
      ↓
Celery Worker
      ↓
MongoDB
```

Redis or RabbitMQ can act as the Celery broker.

MongoDB remains the application database.

Example task:

```python
from celery import Celery
from pymongo import MongoClient

celery_app = Celery(
    "commerce",
    broker="redis://redis:6379/0",
)

mongo_client = MongoClient(
    "mongodb://mongodb:27017",
)

db = mongo_client["commerce"]


@celery_app.task
def process_order(order_id: str):
    order = db.orders.find_one({"_id": order_id})

    if order is None:
        return

    # Perform background processing.
```

For production deployments, configuration should come from environment or secret management rather than hard-coded connection strings.

## Celery Task and MongoDB Connection

The worker process should generally initialize its MongoDB client once and reuse it.

Conceptually:

```text
Celery worker process
        ↓
MongoClient
        ↓
Connection pool
        ↓
Task 1
Task 2
Task 3
Task 4
```

This avoids creating a new pool for every task.

## Task Idempotency

Worker systems commonly provide at-least-once execution semantics.

A task may execute more than once because of:

- Worker crash
- Task timeout
- Broker redelivery
- Manual retry
- Network failure
- Worker termination
- Acknowledgment failure

Therefore, this is unsafe:

```python
@celery_app.task
def charge_order(order_id):
    charge_customer(order_id)
```

if repeated execution causes duplicate charges.

The task should have an idempotency strategy.

## Idempotency with MongoDB

One approach is to store a unique operation identifier.

Example:

```python
def process_payment(order_id: str, operation_id: str):
    existing = db.processed_operations.find_one(
        {"_id": operation_id}
    )

    if existing:
        return existing["result"]

    # Perform processing...
```

A unique index should enforce the invariant:

```javascript
db.processed_operations.createIndex(
  { _id: 1 },
  { unique: true }
)
```

However, the idempotency record and business state should be designed together. A check-then-insert sequence without atomic protection can still race.

## Atomic Claiming

A stronger worker pattern is to atomically claim a job.

Example:

```python
from datetime import datetime, timezone

job = db.jobs.find_one_and_update(
    {
        "_id": job_id,
        "status": "pending",
    },
    {
        "$set": {
            "status": "processing",
            "started_at": datetime.now(timezone.utc),
        }
    },
)

if job is None:
    return
```

Only one worker that successfully changes the state from `pending` to `processing` should proceed.

This is an important concurrency pattern.

## Job State Machine

A worker-backed job can use:

```text
pending
   ↓
processing
   ├──→ completed
   │
   └──→ failed
          ↓
       retrying
          ↓
       processing
```

A typical document:

```json
{
  "_id": "job-1001",
  "type": "generate_report",
  "status": "processing",
  "attempts": 2,
  "started_at": "2026-09-22T10:00:00Z",
  "updated_at": "2026-09-22T10:01:00Z"
}
```

## Atomic State Transitions

Do not update job status using separate read and write operations when another worker can race.

Risky:

```python
job = db.jobs.find_one({"_id": job_id})

if job["status"] == "pending":
    db.jobs.update_one(
        {"_id": job_id},
        {"$set": {"status": "processing"}},
    )
```

Two workers can both observe `pending`.

Prefer an atomic conditional update:

```python
job = db.jobs.find_one_and_update(
    {
        "_id": job_id,
        "status": "pending",
    },
    {
        "$set": {
            "status": "processing",
        }
    },
)
```

The database performs the state transition atomically.

## Worker Concurrency

Suppose:

```text
Worker concurrency = 10
```

and each task can perform several MongoDB operations.

The MongoDB pool must support the expected concurrent database workload without becoming an unbounded resource.

Do not blindly set:

```text
worker concurrency = 100
maxPoolSize = 1000
```

because total connections may become excessive:

```text
Pods
 ×
Processes
 ×
Worker concurrency
 ×
MongoDB pools
```

Capacity planning should consider the entire deployment.

## Worker Concurrency vs Pool Size

These settings solve different problems.

| Setting | Controls |
|---|---|
| Worker concurrency | Number of tasks executing concurrently |
| `maxPoolSize` | Maximum connections available to a client pool |
| `minPoolSize` | Minimum maintained connections |
| `maxConnecting` | Concurrent connection establishment |
| `waitQueueTimeoutMS` | Maximum wait for an available pool connection |

If the worker concurrency is high but the pool is too small, tasks may wait for connections.

If the pool is unnecessarily large, MongoDB may receive excessive connection pressure.

## MongoDB Timeouts in Workers

Workers should use explicit timeouts.

Important timeout categories include:

```text
serverSelectionTimeoutMS
connectTimeoutMS
socketTimeoutMS
waitQueueTimeoutMS
```

Example:

```python
client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=30000,
    waitQueueTimeoutMS=5000,
)
```

Timeout values should be selected according to the task's SLA.

Do not allow a worker task to wait indefinitely for a database operation.

## Task Timeout vs MongoDB Timeout

These are different.

```text
Celery task timeout
        ↓
Limits overall task execution
```

while:

```text
MongoDB socket timeout
        ↓
Limits individual database operation
```

A task may contain:

```text
MongoDB operation
+
External API call
+
File processing
```

Therefore, database timeouts should generally be shorter than the overall task timeout.

## Retry Strategy

A worker should distinguish transient failures from permanent failures.

Transient examples:

- Temporary network failure
- MongoDB primary election
- Temporary service unavailable
- Rate limiting
- Connection interruption

Permanent examples:

- Invalid document
- Invalid business state
- Authorization failure
- Unsupported operation
- Malformed input

Retrying permanent failures wastes resources.

## Exponential Backoff

A typical retry strategy is:

```text
Attempt 1 → immediate
Attempt 2 → 1 second
Attempt 3 → 2 seconds
Attempt 4 → 4 seconds
Attempt 5 → 8 seconds
```

Add jitter when many workers may retry simultaneously.

Conceptually:

```text
Retry delay
    =
base backoff
+
random jitter
```

This reduces retry storms.

## Celery Retry Example

```python
from celery import Celery
from pymongo.errors import PyMongoError

celery_app = Celery("commerce")


@celery_app.task(
    bind=True,
    autoretry_for=(PyMongoError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_order(self, order_id: str):
    order = db.orders.find_one({"_id": order_id})

    if order is None:
        return

    # Process order.
```

Do not automatically configure broad retries for every exception type.

Business validation failures should generally not be retried.

## Retry Storms

Suppose:

```text
100 workers
     ↓
MongoDB unavailable
     ↓
100 failures
     ↓
100 immediate retries
     ↓
MongoDB still unavailable
     ↓
More load
```

This creates a retry storm.

Use:

- Exponential backoff
- Jitter
- Maximum attempts
- Circuit-breaking where appropriate
- Queue-level rate control
- Database capacity monitoring

## MongoDB Transactions in Workers

Background workers are often good candidates for transactions.

Example:

```text
Task
 ↓
Start transaction
 ├── Update inventory
 ├── Update order
 └── Insert audit event
 ↓
Commit
```

Python:

```python
def process_order(order_id):
    with mongo_client.start_session() as session:
        with session.start_transaction():
            db.inventory.update_one(
                {"order_id": order_id},
                {"$set": {"reserved": True}},
                session=session,
            )

            db.orders.update_one(
                {"_id": order_id},
                {"$set": {"status": "processed"}},
                session=session,
            )
```

The same transaction principles apply as in request-driven code.

## Keep Worker Transactions Short

Avoid:

```text
Transaction
 ↓
MongoDB operation
 ↓
External API
 ↓
File download
 ↓
Long computation
 ↓
Commit
```

Prefer:

```text
Prepare external work
 ↓
Short MongoDB transaction
 ↓
Commit
```

or use a workflow/outbox architecture.

## Transaction and Task Retry Interaction

This is an important production issue.

Consider:

```text
Task attempt 1
    ↓
Transaction commits
    ↓
Worker crashes before task acknowledgment
    ↓
Broker redelivers task
    ↓
Task attempt 2
```

The MongoDB transaction already committed.

A second attempt must therefore recognize the operation as already completed.

This is why:

```text
Transaction atomicity
+
Task idempotency
```

must be designed together.

A transaction does not automatically make a background task idempotent.

## Job Idempotency with Unique Constraints

Suppose every order can be processed once:

```javascript
db.order_processing.createIndex(
  { order_id: 1 },
  { unique: true }
)
```

Then the worker can use the database to enforce uniqueness.

This is stronger than relying only on:

```python
if not processed:
    process()
```

because the check itself can race.

## Atomic Upsert

A worker can use an upsert to create an idempotency record atomically.

```python
result = db.processed_orders.update_one(
    {
        "order_id": order_id,
    },
    {
        "$setOnInsert": {
            "created_at": datetime.now(timezone.utc),
        }
    },
    upsert=True,
)
```

The exact business logic should determine whether a duplicate operation should be ignored, resumed, or treated as an error.

## Lease-Based Processing

For jobs that can become stuck, a lease can prevent permanent ownership.

Example:

```json
{
  "_id": "job-1001",
  "status": "processing",
  "lease_until": "2026-09-22T10:05:00Z"
}
```

A worker claims:

```text
status = pending
```

and sets:

```text
status = processing
lease_until = now + 5 minutes
```

If the worker crashes, another worker can recover the job after the lease expires.

## Lease Claim Example

```python
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
lease_until = now + timedelta(minutes=5)

job = db.jobs.find_one_and_update(
    {
        "_id": job_id,
        "$or": [
            {"status": "pending"},
            {
                "status": "processing",
                "lease_until": {"$lt": now},
            },
        ],
    },
    {
        "$set": {
            "status": "processing",
            "lease_until": lease_until,
            "updated_at": now,
        },
        "$inc": {
            "attempts": 1,
        },
    },
)
```

This pattern is useful for database-backed job queues, although dedicated task brokers are often preferable at high scale.

## Heartbeats and Long Jobs

For long-running jobs, a lease may need periodic renewal.

```text
Worker
   ↓
Claim job
   ↓
Process
   ↓
Renew lease
   ↓
Process
   ↓
Renew lease
   ↓
Complete
```

Without lease renewal, another worker may incorrectly assume the job has failed.

## Job Completion

Use an atomic state transition:

```python
result = db.jobs.update_one(
    {
        "_id": job_id,
        "status": "processing",
    },
    {
        "$set": {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc),
        }
    },
)
```

The condition ensures that only the expected worker state is transitioned.

## MongoDB as a Task Queue

MongoDB can technically be used as a queue:

```text
jobs collection
    ↓
find pending job
    ↓
claim job
    ↓
process
    ↓
mark completed
```

This can work for modest workloads.

However, a dedicated broker such as:

- Redis
- RabbitMQ
- Kafka
- Managed queue services

may provide better queue semantics, throughput, visibility, and operational tooling.

Use MongoDB as the queue only when its characteristics match the workload.

## MongoDB and Celery Broker Separation

A common architecture is:

```text
Celery
  ├── Broker → Redis/RabbitMQ
  │
  └── Result/state → application-specific
                       ↓
                    MongoDB
```

MongoDB does not need to be the Celery broker simply because the application database is MongoDB.

Keep responsibilities clear:

```text
Queue → delivery
MongoDB → persistent business state
```

## Scheduled Jobs

Scheduled workers commonly perform:

- Expired-document cleanup
- Data reconciliation
- Aggregation
- Report generation
- TTL-related business processing
- Synchronization
- Periodic health checks

Example:

```text
Scheduler
   ↓
Celery task
   ↓
MongoDB
   ↓
Process batch
```

Do not allow scheduled jobs to overlap unintentionally.

## Preventing Scheduled Job Overlap

Suppose a job runs every 5 minutes but sometimes takes 20 minutes.

Without coordination:

```text
10:00 → Job A starts
10:05 → Job B starts
10:10 → Job C starts
```

Multiple workers may process the same data concurrently.

Use a distributed lock or a job-state mechanism where required.

MongoDB can provide an atomic lock record:

```python
lock = db.locks.find_one_and_update(
    {
        "_id": "daily-reconciliation",
        "locked_until": {"$lt": now},
    },
    {
        "$set": {
            "locked_until": lease_until,
        }
    },
)
```

The locking design must include expiration and failure recovery.

## Batch Processing

MongoDB workers frequently process large collections.

Avoid:

```python
documents = list(
    db.orders.find({"status": "pending"})
)
```

for an unbounded result set.

This loads the entire result set into memory.

Prefer cursor-based processing:

```python
cursor = db.orders.find(
    {"status": "pending"},
    batch_size=500,
)

for order in cursor:
    process_order(order)
```

## Batch Size

Batch size affects:

- Memory usage
- Network round trips
- Processing latency
- Failure recovery
- Throughput

A larger batch can improve throughput but increases memory and retry scope.

Choose based on measured workload characteristics.

## Bulk Writes

When processing many documents, use bulk operations where appropriate.

```python
from pymongo import UpdateOne

operations = []

for order in orders:
    operations.append(
        UpdateOne(
            {"_id": order["_id"]},
            {"$set": {"processed": True}},
        )
    )

if operations:
    db.orders.bulk_write(
        operations,
        ordered=False,
    )
```

`ordered=False` can improve throughput when operations are independent and ordering is not required.

## Bulk Write Trade-Offs

| Choice | Benefit | Trade-off |
|---|---|---|
| Small batches | Easier failure recovery | More round trips |
| Large batches | Higher throughput | More memory and larger failure scope |
| `ordered=True` | Preserves operation order | Can stop earlier and reduce throughput |
| `ordered=False` | Better parallelism/server efficiency for independent writes | No operation ordering guarantee |

Do not use unordered writes when application correctness depends on ordering.

## Cursor Management

Workers should avoid unnecessarily materializing large query results.

Prefer:

```python
for document in db.events.find(
    {"processed": False}
).batch_size(500):
    process(document)
```

rather than:

```python
documents = list(
    db.events.find({"processed": False})
)
```

Cursor-based processing provides more predictable memory usage.

## Pagination for Workers

For large or changing datasets, avoid relying exclusively on:

```python
skip(offset)
```

because large offsets can become inefficient.

Prefer range-based processing using an indexed field.

Example:

```python
last_id = None

while True:
    query = {}

    if last_id is not None:
        query["_id"] = {"$gt": last_id}

    batch = list(
        db.orders.find(query)
        .sort("_id", 1)
        .limit(500)
    )

    if not batch:
        break

    for order in batch:
        process(order)

    last_id = batch[-1]["_id"]
```

This approach works well when the chosen ordering field and processing semantics support it.

## Aggregation in Workers

Background workers are appropriate for expensive aggregation workloads that should not block API requests.

Example:

```python
pipeline = [
    {
        "$match": {
            "created_at": {
                "$gte": start,
                "$lt": end,
            }
        }
    },
    {
        "$group": {
            "_id": "$customer_id",
            "total": {"$sum": "$amount"},
        }
    },
]

for row in db.orders.aggregate(pipeline):
    process_aggregate(row)
```

The aggregation should still be optimized with:

- Appropriate indexes
- Early `$match`
- Controlled result size
- Explain plans
- Appropriate memory usage

Moving an inefficient query to a worker does not make it efficient.

## Worker and Change Streams

Change stream consumers are a specialized type of background worker.

Architecture:

```text
MongoDB
   ↓
Change Stream
   ↓
Long-lived Python Worker
   ↓
Kafka / Celery / Direct Handler
```

The consumer should be treated differently from short-lived tasks because it:

- Runs continuously
- Maintains a cursor
- Needs resume handling
- Requires graceful shutdown
- Has different scaling characteristics

## MongoDB Operations in Async Workers

For asyncio-based workers, use the current asynchronous PyMongo client where appropriate.

Conceptually:

```python
from pymongo import AsyncMongoClient


async def process_job(client, job_id):
    db = client["commerce"]

    job = await db.jobs.find_one(
        {"_id": job_id}
    )

    if job is None:
        return

    await db.jobs.update_one(
        {"_id": job_id},
        {"$set": {"status": "completed"}},
    )
```

Do not use synchronous database calls directly in an asyncio event loop when they can block the event loop.

## Thread-Based Workers

PyMongo's synchronous client is designed for concurrent use by threads.

A single long-lived client can generally be shared across threads within a process.

Example architecture:

```text
Worker Process
      ↓
MongoClient
   ┌──┼──┐
 Thread Thread Thread
   ↓     ↓     ↓
MongoDB operations
```

However, process boundaries are different. Do not share a MongoDB client across forked processes.

## CPU-Bound Worker Tasks

MongoDB access is often I/O-bound.

CPU-heavy tasks should be separated appropriately.

Example:

```text
Task
 ├── MongoDB read
 ├── CPU-heavy transformation
 └── MongoDB write
```

For very CPU-intensive workloads, use process-based workers or specialized compute infrastructure rather than increasing MongoDB connection concurrency indefinitely.

## Worker and Redis

Redis may be used for:

- Celery broker
- Distributed locks
- Caching
- Rate limiting
- Short-lived coordination state

MongoDB remains the durable source of business state.

Do not move critical persistent state into Redis merely because the worker already uses Redis.

## Worker and Kafka

For high-volume event processing:

```text
MongoDB
   ↓
Change Stream
   ↓
Capture Worker
   ↓
Kafka
   ↓
Consumer Groups
```

MongoDB handles application state while Kafka handles event distribution.

This separation allows multiple independent consumers without requiring every service to maintain its own MongoDB change stream.

## Error Handling

A worker should classify failures.

```text
Task failure
     ↓
Is it transient?
 ┌───┴────┐
Yes       No
 ↓         ↓
Retry    Fail / DLQ
```

Examples:

| Failure | Typical handling |
|---|---|
| Temporary MongoDB connectivity | Retry |
| Primary election | Retry |
| Duplicate key | Business-specific |
| Validation error | Fail |
| Authorization failure | Fail and alert |
| External API timeout | Retry with backoff |
| Malformed data | Dead-letter |
| Programmer bug | Fail and alert |

## Dead-Letter Queues

Repeatedly failing tasks should not remain in an infinite retry loop.

A dead-letter architecture:

```text
Task
 ↓
Retry 1
 ↓
Retry 2
 ↓
Retry 3
 ↓
Dead Letter
```

The dead-letter record should retain enough metadata for diagnosis and replay:

```json
{
  "job_id": "job-1001",
  "task": "process_order",
  "attempts": 5,
  "error": "validation_failed",
  "failed_at": "2026-09-22T10:00:00Z"
}
```

## Observability

Monitor workers and MongoDB together.

Important metrics include:

| Metric | Purpose |
|---|---|
| Task throughput | Worker capacity |
| Task latency | Processing performance |
| Task failure rate | Reliability |
| Retry count | Failure pressure |
| Queue depth | Backlog |
| MongoDB latency | Database performance |
| Pool wait time | Connection pressure |
| Active connections | Capacity |
| Batch size | Processing efficiency |
| Job age | Staleness |
| Dead-letter count | Unhandled failures |

## MongoDB Metrics for Workers

Monitor:

- Connections
- Operation latency
- Query execution
- Replication lag
- CPU
- Memory
- Disk
- Working set
- Lock/contention indicators
- Slow queries
- Pool utilization

A worker backlog may be caused by MongoDB rather than worker CPU.

## Logging

Use structured logs with:

- Task ID
- Job ID
- MongoDB operation type
- Entity ID
- Attempt number
- Duration
- Error category

Example:

```python
logger.info(
    "background_job_completed",
    extra={
        "job_id": job_id,
        "attempt": attempt,
        "duration_ms": duration_ms,
    },
)
```

Do not log complete MongoDB documents if they contain sensitive information.

## Correlation IDs

For request-triggered tasks:

```text
HTTP request
    ↓
correlation_id
    ↓
Celery task
    ↓
MongoDB operation
```

Propagate the correlation ID into task metadata and structured logs.

This makes asynchronous request tracing much easier.

## Graceful Shutdown

A worker may receive:

```text
SIGTERM
```

during:

- Kubernetes deployment
- Auto scaling
- Node maintenance
- Manual restart

The worker should:

```text
SIGTERM
   ↓
Stop accepting new tasks
   ↓
Finish safe work
   ↓
Commit required MongoDB changes
   ↓
Release resources
   ↓
Exit
```

Long-running jobs should have explicit checkpointing if they cannot safely complete within the termination window.

## Kubernetes Deployment

A typical architecture separates API and worker deployments:

```text
Kubernetes Cluster
 ├── API Deployment
 │    ├── Pod
 │    └── Pod
 │
 ├── Worker Deployment
 │    ├── Pod
 │    └── Pod
 │
 └── Scheduler
```

Example worker configuration:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: commerce-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: commerce-worker
  template:
    metadata:
      labels:
        app: commerce-worker
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: worker
          image: example/commerce-worker:1.0.0
          env:
            - name: MONGODB_URI
              valueFrom:
                secretKeyRef:
                  name: mongodb
                  key: uri
```

Worker replica count should be based on:

- Queue depth
- Task throughput
- MongoDB capacity
- External dependency capacity
- Memory
- CPU
- Connection limits

## Kubernetes Autoscaling

Scaling workers without considering MongoDB can overload the database.

For example:

```text
3 worker pods
   ↓
Moderate MongoDB load

20 worker pods
   ↓
High MongoDB concurrency
   ↓
Connection pressure
   ↓
Latency increases
```

Autoscaling should consider database capacity.

Possible signals include:

- Queue depth
- Task latency
- Worker CPU
- MongoDB connection utilization
- MongoDB operation latency

## AWS Deployment Considerations

Workers may run on:

- ECS
- EKS
- EC2
- Lambda for suitable short-lived workloads

MongoDB may run on:

- MongoDB Atlas
- Self-managed infrastructure

The worker architecture should account for:

- Network latency
- Security groups
- Private connectivity
- TLS
- Secrets Manager
- Connection limits
- Autoscaling
- Deployment lifecycle

Avoid opening MongoDB to the public internet solely to simplify worker connectivity.

## Security

Workers often have more database privileges than APIs because they perform internal processing.

This can become a security risk.

Use separate credentials where appropriate:

```text
API service account
    ↓
Limited MongoDB permissions

Worker service account
    ↓
Worker-specific permissions
```

Use:

- TLS
- Least privilege
- Secret management
- Network restrictions
- Credential rotation
- Auditing
- Separate service identities

## Secret Management

Do not hard-code:

```python
MONGODB_URI = "mongodb://admin:password@host"
```

Prefer:

```python
import os

mongo_uri = os.environ["MONGODB_URI"]
```

Production secrets should originate from a secure secret-management system.

Examples:

- AWS Secrets Manager
- Kubernetes Secrets with appropriate controls
- MongoDB Atlas integrations
- CI/CD secret injection

## Backup and Recovery

Workers can create or modify large amounts of MongoDB data.

Backups must therefore account for:

- Worker-generated documents
- Job state
- Idempotency records
- Outbox records
- Processing checkpoints
- Audit records

If the worker rebuilds a derived collection, recovery may require:

```text
Restore MongoDB
     ↓
Restart workers
     ↓
Reconcile derived state
```

## Data Consistency

A worker often creates eventual consistency:

```text
Primary state
    ↓
Queue delay
    ↓
Worker
    ↓
Derived state
```

This is normal.

Do not expose derived state as strongly consistent unless the architecture guarantees it.

For example:

```text
orders collection
    ↓
Search index
```

The search index may temporarily lag behind MongoDB.

The application should define acceptable consistency windows.

## Worker Transactions vs Distributed Workflows

A MongoDB transaction can guarantee atomicity within MongoDB.

It cannot atomically coordinate:

```text
MongoDB
+
Stripe
+
Kafka
+
PostgreSQL
```

For multi-system workflows, consider:

- Transactional outbox
- Saga
- Idempotency keys
- State machines
- Compensating actions

Example:

```mermaid
flowchart TD
    Task[Background Task]
    MongoTxn[MongoDB Transaction]
    Outbox[Outbox Event]
    Kafka[Kafka]
    Consumer[Downstream Worker]
    External[External Service]

    Task --> MongoTxn
    MongoTxn --> Outbox
    Outbox --> Kafka
    Kafka --> Consumer
    Consumer --> External
```

## Production Anti-Patterns

### New MongoClient Per Task

```python
def task():
    client = MongoClient(uri)
```

Problem:

- Connection churn
- Pool creation overhead
- Increased MongoDB connection pressure

Use a long-lived client per process.

### Read-Then-Update Job Claim

```python
job = find_one(...)
if job:
    update(...)
```

Problem:

Two workers can claim the same job.

Use an atomic conditional update.

### Infinite Retries

Problem:

A permanent failure creates an endless task loop.

Use bounded retries and dead-letter handling.

### Retry Without Idempotency

Problem:

A task can execute its side effect multiple times.

Use stable operation IDs and database constraints.

### Unbounded Query Materialization

```python
documents = list(collection.find(...))
```

Problem:

Potentially unbounded memory usage.

Use cursors and batches.

### Huge Transactions

Problem:

Long transactions increase resource usage and contention.

Keep transactions short.

### Worker Autoscaling Without Database Capacity Planning

Problem:

More workers can overwhelm MongoDB.

Scale workers according to both queue demand and database capacity.

### Running Workers Inside API Processes

Problem:

Every API replica may create another worker instance.

Prefer separate worker deployments.

## Production Checklist

### MongoDB Client

- [ ] Reuse one `MongoClient` per worker process.
- [ ] Do not create clients per task.
- [ ] Do not share clients across forked processes.
- [ ] Configure connection pools intentionally.
- [ ] Configure explicit timeouts.

### Task Reliability

- [ ] Design tasks to be idempotent.
- [ ] Use atomic job claims.
- [ ] Use stable operation identifiers.
- [ ] Configure bounded retries.
- [ ] Use exponential backoff and jitter.
- [ ] Implement dead-letter handling.
- [ ] Handle worker crashes safely.

### MongoDB Performance

- [ ] Use appropriate indexes.
- [ ] Process large collections with cursors.
- [ ] Use bounded batch sizes.
- [ ] Use bulk writes where appropriate.
- [ ] Avoid unnecessary full-document reads.
- [ ] Monitor MongoDB latency and pool pressure.

### Transactions

- [ ] Keep transactions short.
- [ ] Pass the same session to all transactional operations.
- [ ] Avoid external calls inside transactions.
- [ ] Combine transaction design with task idempotency.
- [ ] Test retry and crash scenarios.

### Operations

- [ ] Monitor queue depth.
- [ ] Monitor task latency.
- [ ] Monitor retry rates.
- [ ] Monitor dead-letter volume.
- [ ] Monitor MongoDB connections.
- [ ] Test graceful shutdown.
- [ ] Document recovery procedures.

### Security

- [ ] Use dedicated worker credentials where appropriate.
- [ ] Apply least privilege.
- [ ] Use TLS.
- [ ] Store credentials in a secret manager.
- [ ] Restrict network access.
- [ ] Avoid logging sensitive documents.

## Troubleshooting

### Worker Cannot Connect to MongoDB

```text
Symptom
↓
Background task fails to connect
↓
Possible causes
    - Invalid connection string
    - DNS failure
    - Network/security-group restriction
    - TLS mismatch
    - Authentication failure
    - MongoDB unavailable
↓
Isolation strategy
↓
Test DNS/network connectivity from worker
↓
Test connection with mongosh
↓
Check MongoDB credentials
↓
Inspect worker and MongoDB logs
↓
Root cause
↓
Corrective action
    - Fix URI/network/TLS/credentials
↓
Prevention
    - Startup connectivity checks
    - Secret validation
    - Network monitoring
```

### Worker Tasks Are Slow

```text
Symptom
↓
Task latency increases
↓
Possible causes
    - Slow MongoDB query
    - Missing index
    - Pool exhaustion
    - External service latency
    - Large documents
    - Excessive batch size
↓
Isolation strategy
↓
Measure MongoDB operation latency
↓
Inspect explain plan
↓
Check connection pool wait
↓
Measure external calls
↓
Root cause
↓
Corrective action
    - Optimize query/index
    - Tune pool/concurrency
    - Reduce batch size
    - Optimize downstream calls
↓
Prevention
    - Task latency metrics
    - Query performance testing
```

### Duplicate Processing

```text
Symptom
↓
Same business operation executes more than once
↓
Possible causes
    - Task redelivery
    - Worker crash
    - Manual retry
    - Multiple workers claiming one job
↓
Isolation strategy
↓
Inspect task IDs and operation IDs
↓
Inspect job state transitions
↓
Check atomic claim logic
↓
Root cause
↓
Corrective action
    - Add idempotency key
    - Add unique constraint
    - Use atomic state transition
↓
Prevention
    - Failure-injection testing
    - Idempotency by design
```

### MongoDB Connection Pool Exhaustion

```text
Symptom
↓
Tasks wait for MongoDB connections
↓
Possible causes
    - Too many concurrent tasks
    - Pool too small
    - Long-running database operations
    - Too many worker processes
    - Too many MongoClient instances
↓
Isolation strategy
↓
Inspect worker concurrency
↓
Inspect MongoDB connection metrics
↓
Inspect pool wait time
↓
Calculate total client/pool footprint
↓
Root cause
↓
Corrective action
    - Reduce concurrency
    - Tune pool size
    - Optimize slow operations
    - Reduce unnecessary clients
↓
Prevention
    - Capacity planning
    - Connection monitoring
```

### Jobs Remain Stuck in Processing

```text
Symptom
↓
Jobs remain in processing state indefinitely
↓
Possible causes
    - Worker crash
    - Missing lease expiration
    - No heartbeat
    - Incorrect state transition
↓
Isolation strategy
↓
Inspect worker logs
↓
Inspect job timestamps
↓
Check lease expiration
↓
Root cause
↓
Corrective action
    - Recover expired jobs
    - Implement leases
    - Add heartbeat for long tasks
↓
Prevention
    - Worker liveness monitoring
    - Job recovery automation
```

## Interview Considerations

### Why should MongoClient be reused by background workers?

`MongoClient` maintains connection pools and is designed for reuse. Creating a client for every task causes connection churn and unnecessary resource consumption.

### How do you prevent two workers from processing the same MongoDB job?

Use an atomic state transition:

```python
job = db.jobs.find_one_and_update(
    {
        "_id": job_id,
        "status": "pending",
    },
    {
        "$set": {
            "status": "processing",
        }
    },
)
```

Only the worker that successfully performs the transition should process the job.

### Why must background tasks be idempotent?

Task queues can deliver or execute work more than once because of retries, worker failures, acknowledgment problems, or operational restarts.

Idempotency ensures repeated execution does not produce an incorrect business result.

### Does a MongoDB transaction make a Celery task exactly once?

No.

A transaction provides atomicity for MongoDB operations. It does not control task delivery or acknowledgment.

A task can commit a MongoDB transaction and then crash before the task broker records successful completion.

The task may then execute again.

Therefore:

```text
MongoDB transaction
+
Task idempotency
```

are separate requirements.

### How would you process millions of MongoDB documents?

Avoid loading them all into memory.

Use:

- Indexed queries
- Cursors
- Bounded batches
- Bulk writes
- Checkpointing
- Controlled concurrency
- Retryable processing

For very large workloads, partition the work rather than using one giant task.

### When would you use MongoDB as a queue?

For relatively simple, moderate workloads where MongoDB's atomic update and persistence semantics are sufficient.

For high-throughput task delivery or sophisticated queue semantics, a dedicated broker is generally more appropriate.

### How should workers handle MongoDB transient failures?

Use bounded retries with appropriate backoff and jitter, while distinguishing transient database failures from permanent business or validation errors.

### Why can increasing worker replicas make MongoDB slower?

Every worker process can create its own MongoDB client and connection pool. Increasing worker count can therefore multiply concurrent connections and database operations.

Worker scaling must be coordinated with MongoDB capacity.

### How would you handle a worker that crashes halfway through a job?

Use a combination of:

- Idempotent processing
- Atomic state transitions
- Leases or visibility timeouts
- Checkpointing for long jobs
- Task retries
- Dead-letter handling

The exact design depends on whether the job's operations are transactional, independently retryable, or externally observable.

## Key Takeaways

- **Background workers should reuse a long-lived MongoClient per process, use explicit timeouts, and size connection pools according to total worker concurrency rather than individual tasks.**
- **Assume tasks can execute more than once: combine atomic MongoDB state transitions, unique constraints, stable operation identifiers, and idempotent business logic.**
- **Keep MongoDB transactions short and treat transaction atomicity separately from task-delivery semantics; a committed transaction does not make a Celery task exactly once.**
- **For large workloads, use cursors, bounded batches, bulk writes, checkpointing, and controlled concurrency instead of loading or processing unbounded datasets in one task.**
- **Scale workers together with MongoDB capacity, queue depth, connection limits, and downstream dependencies; worker autoscaling without database-aware capacity planning can turn backlog into database saturation.**