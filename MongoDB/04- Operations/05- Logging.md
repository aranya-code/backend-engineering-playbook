# 05- Logging

## Overview

MongoDB logging provides the detailed operational record required to understand database behavior, investigate failures, diagnose performance problems, and support security and compliance workflows.

Metrics answer questions such as:

```text
How much?
How often?
How fast?
```

Logs answer questions such as:

```text
What happened?
When did it happen?
What component reported it?
What operation was involved?
What error occurred?
```

Production MongoDB logging should be designed as part of the complete observability system:

```mermaid
flowchart LR
    A[Application] --> B[MongoDB Driver]
    B --> C[MongoDB]

    C --> D[MongoDB Logs]
    C --> E[Database Metrics]
    C --> F[Query Diagnostics]

    A --> G[Application Logs]
    A --> H[Distributed Traces]

    D --> I[Log Aggregation]
    E --> J[Metrics Platform]
    F --> I
    G --> I
    H --> K[Tracing Platform]

    I --> L[Incident Investigation]
    J --> L
    K --> L
```

MongoDB logs should not be treated as an unstructured text file that engineers inspect manually during every incident. In production, logs should be collected, centralized, retained appropriately, protected from unauthorized access, and correlated with metrics and traces.

## MongoDB Log Sources

MongoDB logging can originate from several sources.

| Source | Purpose |
|---|---|
| MongoDB server logs | Server lifecycle, warnings, errors, operational events |
| Audit logs | Security and administrative activity where auditing is configured |
| Profiler data | Detailed database operation diagnostics |
| Application logs | Driver errors, application context, request information |
| Infrastructure logs | Container, host, network, and storage events |
| Managed-service logs | Provider-specific database and platform events |

A production investigation often requires combining multiple sources.

For example:

```text
API timeout
    ↓
Application log
    ↓
MongoDB driver timeout
    ↓
MongoDB server log
    ↓
Storage latency metric
    ↓
Infrastructure event
```

## MongoDB Server Logs

The MongoDB server process writes operational log messages describing events such as:

- Server startup and shutdown
- Connections
- Authentication events
- Replication activity
- Elections
- Configuration changes
- Warnings
- Errors
- Storage-engine events
- Network problems
- Operational failures

The exact log structure and message identifiers depend on the MongoDB version and deployment configuration.

Treat MongoDB log messages as diagnostic telemetry rather than as a stable application API. Avoid building brittle automation around exact message wording when structured fields or supported monitoring interfaces are available.

## Log Formats

Modern MongoDB deployments can emit structured logging information that is easier for centralized logging systems to process.

A conceptual log event may contain fields such as:

```json
{
  "timestamp": "2026-09-22T10:15:30Z",
  "severity": "W",
  "component": "NETWORK",
  "message": "Connection-related event",
  "context": "conn123"
}
```

The exact fields depend on the MongoDB version and logging configuration.

Structured fields are preferable to parsing human-readable message text whenever the deployment exposes them.

## Log Severity

MongoDB log messages have severity information that helps distinguish normal operational messages from problems.

Conceptually:

| Severity | Typical interpretation |
|---|---|
| Informational | Normal operational event |
| Warning | Potential or developing problem |
| Error | Operation or subsystem failure |
| Severe/Fatal | Serious condition requiring immediate investigation |

Severity alone should not determine alerting.

For example:

```text
Warning
+
single occurrence
=
possibly harmless

Warning
+
continuous recurrence
+
latency increase
=
investigate
```

Operational significance depends on frequency, duration, context, and impact.

## MongoDB Log Components

MongoDB server logs identify the subsystem responsible for a message.

Common areas include:

- Network
- Storage
- Replication
- Access control
- Command execution
- Sharding
- Query processing
- Journaling
- Recovery
- Initialization

Component information can significantly reduce investigation time.

For example:

```text
Component: REPL
```

directs the investigation toward replication.

Whereas:

```text
Component: NETWORK
```

suggests examining connections, transport, DNS, load balancers, or network infrastructure.

## Startup and Shutdown Logging

MongoDB startup logs are important when investigating:

- Pod restarts
- Host reboots
- Process crashes
- Configuration changes
- Deployment failures
- Storage recovery

A startup investigation should correlate:

```text
MongoDB startup
+
container lifecycle
+
orchestrator events
+
host events
+
deployment history
```

For Kubernetes:

```text
Pod restart
    ↓
Container termination reason
    ↓
MongoDB process logs
    ↓
Node events
    ↓
Resource pressure / OOM / deployment
```

## Connection Logging

Connection events can help diagnose connection storms and networking problems.

A common production failure pattern is:

```text
Traffic spike
    ↓
Many application processes
    ↓
New MongoDB clients/connections
    ↓
Connection spike
    ↓
MongoDB resource pressure
    ↓
Higher latency
```

Connection-related logs should be correlated with:

- `serverStatus()` connection metrics
- Application pool metrics
- Kubernetes replica count
- Application worker count
- Traffic volume

Do not interpret every connection event as an error.

## Authentication Logging

Authentication failures are important both operationally and from a security perspective.

Potential causes include:

- Invalid credentials
- Expired credentials
- Incorrect authentication database
- Incorrect connection string
- Missing authentication mechanism
- TLS configuration problems
- Application configuration errors

A repeated authentication failure pattern may indicate either a deployment misconfiguration or an attempted unauthorized access.

Logs should therefore be correlated with:

```text
Deployment changes
+
Application identity
+
Source network
+
Security events
```

## Authorization Logging

Authentication answers:

> Who are you?

Authorization answers:

> What are you allowed to do?

Authorization failures can occur when:

- A role is missing a required privilege.
- The application uses the wrong database.
- A collection is newly introduced.
- A deployment changes access patterns.
- A service identity has been incorrectly configured.

For production debugging, capture enough context to identify the operation without logging sensitive credentials or document contents.

## Replication Logging

Replica-set logs are important during:

- Elections
- Primary changes
- Secondary lag
- Initial synchronization
- Rollbacks
- Member failures
- Replication interruptions

A useful investigation combines:

```text
MongoDB replication logs
+
rs.status()
+
replication metrics
+
network metrics
+
host resource metrics
```

Logs provide event context.

Metrics provide the time-series behavior.

## Election Events

Primary elections can cause temporary application disruption depending on driver configuration and workload behavior.

An investigation should determine:

```text
Why did the election happen?
```

Possible causes include:

- Node failure
- Network partition
- Resource exhaustion
- Process restart
- Configuration changes

Repeated elections are more concerning than a single expected failover.

## Replication Lag Logs

Replication lag should primarily be monitored through metrics and replica-set state.

Logs are useful for understanding events surrounding lag, such as:

- Synchronization problems
- Network failures
- Initial sync
- Storage problems
- Member state transitions

Do not build replication-lag monitoring solely around log messages.

## Storage and WiredTiger Logs

MongoDB's storage engine can produce logs related to:

- Recovery
- Checkpoints
- Eviction
- Storage errors
- File operations
- Cache behavior
- I/O problems

Storage logs become particularly important when:

```text
Query latency ↑
+
CPU normal
+
Application healthy
+
Disk latency ↑
```

The database may be waiting on storage rather than executing inefficient queries.

## Query Logging

MongoDB should not be configured to log every query indiscriminately in production.

High-volume query logging can create:

- Significant log volume
- Additional CPU overhead
- Storage consumption
- Network traffic
- Sensitive-data exposure
- Difficult-to-search logs

Use targeted diagnostics such as:

- Query profiler
- Slow-query analysis
- `explain()`
- Application tracing
- Query metrics

The correct goal is useful query visibility, not maximum log volume.

## Database Profiler

MongoDB's database profiler records detailed information about database operations.

It can help investigate:

- Slow queries
- Updates
- Deletes
- Aggregations
- Commands
- Query execution behavior

Profiler configuration should be deliberate.

Use it when:

```text
Normal metrics identify a problem
        ↓
Application tracing is insufficient
        ↓
Detailed database operation data is required
```

Avoid enabling aggressive profiling permanently without evaluating its operational cost.

## Profiler vs Server Logs

| Tool | Best use |
|---|---|
| Server logs | Database lifecycle and subsystem events |
| Profiler | Detailed operation-level diagnostics |
| `explain()` | Controlled analysis of a specific query |
| Application logs | Request and business-operation context |
| Metrics | Trends and alerting |
| Traces | End-to-end request correlation |

These tools complement each other.

## Slow Query Logging Strategy

A practical strategy is:

```text
Normal workload
    ↓
Metrics + application tracing
    ↓
Performance anomaly detected
    ↓
Identify affected query shape
    ↓
Targeted profiler / explain investigation
    ↓
Root cause
    ↓
Optimization
    ↓
Verify metrics
```

This reduces unnecessary database diagnostic overhead.

## Application Logging with PyMongo

The application should log database failures with operational context.

Example:

```python
import logging

from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


def create_order(collection, document):
    try:
        result = collection.insert_one(document)
        return result.inserted_id

    except PyMongoError:
        logger.exception(
            "MongoDB operation failed",
            extra={
                "operation": "create_order",
                "collection": collection.name,
            },
        )
        raise
```

The application log should provide context that MongoDB itself does not know, such as:

```text
Service
Endpoint
Operation
Request correlation ID
Deployment version
Business operation
```

Do not log the complete input document if it contains sensitive information.

## Structured Application Logs

For production services, structured JSON logging is preferable.

Example:

```json
{
  "timestamp": "2026-09-22T10:15:30.120Z",
  "level": "ERROR",
  "service": "orders-api",
  "operation": "create_order",
  "collection": "orders",
  "error_type": "DuplicateKeyError",
  "request_id": "req-8f3a",
  "trace_id": "trace-71ab"
}
```

This allows centralized logging systems to query:

```text
service = "orders-api"
operation = "create_order"
error_type = "DuplicateKeyError"
```

without parsing free-form text.

## Request Correlation

A request correlation ID connects application activity across services.

For example:

```text
Client
  ↓
Nginx
  ↓ request_id=abc123
FastAPI
  ↓ request_id=abc123
Repository
  ↓ request_id=abc123
MongoDB
```

MongoDB itself may not know the business request identifier, so the application must preserve this context.

For distributed systems, use trace context where available.

## Distributed Tracing and MongoDB

Tracing should connect application operations to database calls.

Conceptually:

```mermaid
sequenceDiagram
    participant C as Client
    participant A as FastAPI
    participant R as Repository
    participant M as MongoDB

    C->>A: GET /orders
    A->>R: list_orders()
    R->>M: find()
    M-->>R: documents
    R-->>A: results
    A-->>C: HTTP 200
```

A trace can then show:

```text
HTTP request      180 ms
Application        20 ms
MongoDB            145 ms
Serialization       15 ms
```

This is significantly more useful than a single application error log.

## Logging Query Metadata

Useful query metadata includes:

- Collection
- Operation
- Query shape
- Duration
- Result count
- Error type
- Read/write classification

Avoid logging:

- Full credentials
- Connection strings
- Authentication tokens
- Passwords
- Full sensitive documents
- Unredacted personal information

## Query Shape vs Query Values

Prefer recording a query shape such as:

```text
orders.find({
    tenant_id: ?,
    status: ?
})
```

rather than:

```text
orders.find({
    tenant_id: "customer-secret-value",
    status: "pending"
})
```

Query shapes provide useful performance information while reducing sensitive-data exposure.

## Log Sampling

High-volume systems may require sampling.

For example:

```text
Successful requests:
1% sample

Warnings:
100%

Errors:
100%

Slow database operations:
100%
```

Sampling should preserve enough information for incident investigation.

Do not blindly sample security events or critical operational failures.

## Log Levels in Backend Services

A practical application logging strategy is:

| Level | Use |
|---|---|
| DEBUG | Temporary diagnostic information |
| INFO | Normal important lifecycle events |
| WARNING | Unexpected but recoverable conditions |
| ERROR | Failed operations |
| CRITICAL | Severe service-impacting conditions |

Avoid using `ERROR` for normal MongoDB retries.

Avoid using `INFO` for every database operation in a high-throughput service.

## Retry Logging

MongoDB drivers can retry certain operations depending on configuration and operation semantics.

A retry should not automatically produce an error log.

Prefer:

```text
WARN:
Transient MongoDB operation required retry
```

only when the retry is operationally significant.

Log an error when the operation ultimately fails.

This avoids turning transient recovery behavior into noisy error streams.

## Timeout Logging

Different timeout types imply different problems.

Useful categories include:

| Timeout | Possible implication |
|---|---|
| Server selection timeout | No suitable MongoDB server available |
| Connection timeout | Connection establishment problem |
| Socket timeout | Operation/network duration exceeded |
| Pool wait timeout | Application cannot acquire a connection |
| Request timeout | End-to-end service latency exceeded |

Log the timeout category explicitly.

Example:

```json
{
  "level": "ERROR",
  "operation": "list_orders",
  "error_type": "ServerSelectionTimeoutError",
  "timeout_category": "server_selection",
  "duration_ms": 3002
}
```

## Duplicate Key Errors

Duplicate-key errors are often expected business-level outcomes rather than infrastructure failures.

For example:

```text
Unique index:
orders.external_order_id
```

A duplicate request may produce:

```text
DuplicateKeyError
```

The application should classify it correctly.

Do not automatically alert on every duplicate-key exception.

Distinguish:

```text
Expected idempotency conflict
```

from:

```text
Unexpected duplicate-key spike
```

## Log Correlation During Incidents

A production incident should be investigated across multiple telemetry sources.

```text
Alert
 ↓
Application error
 ↓
Trace ID
 ↓
MongoDB operation
 ↓
MongoDB server log
 ↓
Infrastructure event
```

For example:

```text
10:15:00  Deployment begins
10:16:10  MongoDB latency increases
10:16:15  API timeout rate increases
10:16:18  Connection-pool wait increases
10:16:25  Error logs increase
```

The temporal relationship can reveal whether the deployment caused or merely coincided with the incident.

## Centralized Log Collection

Production MongoDB logs should generally be shipped to a centralized system.

Common architectures include:

```mermaid
flowchart LR
    A[MongoDB] --> B[Local Log Files / stdout]
    B --> C[Log Collector]
    C --> D[Central Log Store]

    E[FastAPI] --> C
    F[Kubernetes] --> C
    G[Nginx] --> C

    D --> H[Search]
    D --> I[Dashboards]
    D --> J[Alerts]
```

Depending on the deployment, the collector may be implemented using tools such as:

- Fluent Bit
- Fluentd
- Vector
- Filebeat
- CloudWatch agents
- Managed logging integrations

The exact tool is an infrastructure decision rather than a MongoDB requirement.

## Kubernetes Logging

When MongoDB runs in Kubernetes, logging architecture should account for:

- Container stdout/stderr
- Persistent log files
- Pod restarts
- Node replacement
- Sidecar or DaemonSet collectors
- Log retention

A critical requirement is that logs survive the lifetime of an individual pod.

Do not depend solely on ephemeral container-local storage for production incident investigation.

## Docker Logging

For Docker-based deployments, logs may be exposed through the container logging driver or collected from configured log files.

A production architecture should ensure:

```text
Container restart
≠
Permanent loss of required logs
```

Log retention should be implemented outside the application container wherever possible.

## AWS Logging

When MongoDB is deployed on AWS, MongoDB logs can be integrated with AWS logging infrastructure depending on the deployment architecture.

Possible destinations include:

- Amazon CloudWatch Logs
- Amazon S3
- OpenSearch-based logging platforms
- Third-party observability platforms

The important design principle is:

```text
MongoDB logs
+
Application logs
+
Infrastructure logs
```

should be searchable and correlatable.

## Log Retention

Retention should be based on:

- Incident investigation requirements
- Security requirements
- Compliance requirements
- Storage cost
- Operational value

A practical model may be:

```text
Hot logs:
7–30 days

Warm logs:
30–90 days

Archived logs:
Longer retention where required
```

Actual retention should follow organizational requirements.

## Log Rotation

Log rotation prevents unbounded local log growth.

Consider:

- Maximum file size
- Rotation frequency
- Compression
- Retention count
- External shipping
- Failure behavior

The goal is to prevent:

```text
Log growth
    ↓
Disk exhaustion
    ↓
MongoDB instability
```

Logging itself must never become the cause of database failure.

## Security of Logs

Logs are operational data and may contain sensitive information.

Protect them using:

- Access control
- Encryption in transit
- Encryption at rest
- Least privilege
- Retention policies
- Redaction
- Secure aggregation infrastructure

Treat logs as sensitive even when they do not contain primary business data.

## Secrets in Logs

Never log:

```text
mongodb://user:password@host
```

or:

```text
MONGODB_URI=mongodb+srv://user:password@...
```

Never log:

- Database passwords
- API keys
- JWTs
- TLS private keys
- Cloud credentials
- Session tokens

Connection errors should identify the type of failure without exposing the connection string.

## Personal and Business Data

MongoDB documents can contain:

- Names
- Emails
- Addresses
- Payment-related data
- Internal identifiers
- Business records

Avoid logging entire MongoDB documents unless there is a strong and controlled diagnostic requirement.

Prefer:

```text
document_id
operation
query_shape
result_count
duration
```

over:

```text
complete document
```

## Log Injection

Application values can contain unexpected characters.

Structured logging reduces the risk of log-format corruption compared with manual string concatenation.

Prefer:

```python
logger.info(
    "MongoDB operation completed",
    extra={
        "operation": operation,
        "collection": collection_name,
    },
)
```

over:

```python
logger.info(
    f"MongoDB operation completed: {operation} {collection_name}"
)
```

Structured fields are also easier to query.

## Logging Performance

Logging has a measurable cost.

High-volume database logging can consume:

```text
CPU
+
memory
+
disk I/O
+
network bandwidth
+
log storage
```

A common mistake is logging every database operation at `INFO`.

For high-throughput services:

```text
Metrics → aggregate behavior
Traces → representative requests
Logs → important events and failures
Profiler → targeted database diagnostics
```

This separation is usually more scalable.

## Logging in FastAPI

A FastAPI service can log MongoDB failures at the repository or service boundary.

Example:

```python
import logging

from fastapi import FastAPI, HTTPException
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    try:
        document = repository.get_order(order_id)

        if document is None:
            raise HTTPException(status_code=404, detail="Order not found")

        return document

    except HTTPException:
        raise

    except PyMongoError:
        logger.exception(
            "MongoDB read failed",
            extra={
                "operation": "get_order",
                "collection": "orders",
            },
        )
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable",
        )
```

The application should avoid returning internal MongoDB errors directly to clients.

## Logging in Background Workers

Celery or other background workers require additional context.

Useful fields include:

```text
task_name
task_id
attempt
operation
collection
duration
error_type
```

Example:

```python
logger.exception(
    "MongoDB update failed in background task",
    extra={
        "task_name": "sync_orders",
        "task_id": task_id,
        "attempt": attempt,
        "operation": "update_order",
    },
)
```

This makes asynchronous failures easier to trace.

## Logging Kafka Consumers

For Kafka consumers interacting with MongoDB, correlate:

```text
topic
partition
offset
consumer group
MongoDB operation
```

A useful event flow is:

```text
Kafka message
    ↓
Consumer
    ↓
MongoDB operation
    ↓
Commit offset
```

The logs should make it possible to determine whether failure occurred before or after the MongoDB write.

This is especially important for idempotency and retry analysis.

## Logging Change Stream Consumers

Change-stream consumers should log:

- Collection
- Event type
- Resume token metadata where appropriate
- Consumer identity
- Retry state
- Processing duration
- Failure reason

Avoid logging complete change events when they contain sensitive documents.

## Log-Based Troubleshooting

Use a structured methodology:

```text
Symptom
↓
Possible causes
↓
Isolation strategy
↓
Log search
↓
Metric correlation
↓
Trace correlation
↓
Diagnostic commands
↓
Root cause
↓
Corrective action
↓
Prevention
```

Example:

```text
Symptom:
API requests intermittently timeout

Possible causes:
- MongoDB query latency
- Connection pool exhaustion
- Network failure
- MongoDB failover
- Application regression

Isolation:
Compare API latency, pool wait, MongoDB latency, and errors.

Logs:
Search for timeout and server-selection errors.

Metrics:
Check connections, CPU, storage, replication.

Traces:
Identify whether time is spent waiting for a connection
or executing the MongoDB operation.

Corrective action:
Address the identified bottleneck.

Prevention:
Add targeted alerts and regression monitoring.
```

## Common Logging Mistakes

### Logging Every Query

**Problem:** Massive log volume and unnecessary overhead.

**Fix:** Use metrics, traces, and targeted query diagnostics.

### Logging Full Documents

**Problem:** Sensitive information leaks into operational systems.

**Fix:** Log identifiers and metadata rather than complete documents.

### Logging Connection Strings

**Problem:** Credentials can be exposed.

**Fix:** Never log connection strings containing credentials.

### Treating All Errors as Infrastructure Failures

**Problem:** Expected business conflicts create false alerts.

**Fix:** Classify duplicate-key, validation, not-found, and transient errors appropriately.

### Using Free-Form Logs Everywhere

**Problem:** Centralized search becomes difficult.

**Fix:** Use structured fields with stable names.

### No Request Correlation

**Problem:** Engineers cannot connect API failures to database operations.

**Fix:** Propagate request IDs or distributed trace context.

### No Log Retention Strategy

**Problem:** Logs become expensive or disappear before incidents can be investigated.

**Fix:** Define hot, warm, and archive retention based on operational requirements.

### Excessive Debug Logging in Production

**Problem:** Log volume and sensitive-data exposure increase.

**Fix:** Enable detailed diagnostics temporarily and deliberately.

### Logging Only Application Errors

**Problem:** Database-side events such as elections, storage issues, or replication problems remain invisible.

**Fix:** Centralize MongoDB server logs alongside application logs.

## Production Logging Checklist

### MongoDB

- [ ] MongoDB server logs are collected.
- [ ] Logs are centralized.
- [ ] Log rotation is configured.
- [ ] Retention is defined.
- [ ] Startup and shutdown events are observable.
- [ ] Authentication and authorization failures are observable.
- [ ] Replication events can be investigated.
- [ ] Storage-related events are searchable.

### Application

- [ ] MongoDB driver errors are logged.
- [ ] Error types are classified.
- [ ] Request IDs are propagated.
- [ ] Trace IDs are available where applicable.
- [ ] Database operation names are recorded.
- [ ] Sensitive fields are redacted.

### Performance

- [ ] Slow operations can be identified.
- [ ] Query diagnostics are available.
- [ ] Database latency is measured separately from API latency.
- [ ] Connection-pool wait can be observed.
- [ ] Profiler usage is controlled.

### Security

- [ ] Passwords are never logged.
- [ ] Connection strings are never logged.
- [ ] Tokens are never logged.
- [ ] Sensitive documents are not logged by default.
- [ ] Log access follows least privilege.
- [ ] Logs are encrypted where required.

### Operations

- [ ] Logs survive container/pod restarts.
- [ ] Centralized search is available.
- [ ] Alerting is based on actionable conditions.
- [ ] Retention matches operational and compliance requirements.
- [ ] Incident runbooks reference relevant log sources.

## Interview Considerations

### Why should MongoDB logs be centralized?

Centralization provides:

- Searchability
- Retention
- Correlation
- Access control
- Cross-service investigation
- Persistence beyond individual hosts or containers

### Should every MongoDB query be logged?

Generally no.

High-volume query logging can create substantial overhead and noise.

Use:

```text
Metrics
+
Tracing
+
Targeted profiling
+
Explain plans
```

for query performance analysis.

### What should application logs add beyond MongoDB logs?

Application logs provide business and request context that MongoDB does not know:

```text
Endpoint
Service
Request ID
Trace ID
Business operation
Deployment version
```

### How would you debug a MongoDB timeout?

Start with:

```text
Application error
↓
Timeout category
↓
Connection-pool wait
↓
MongoDB latency
↓
Server selection
↓
MongoDB server logs
↓
Network/resource metrics
↓
Replica-set health
```

The exact sequence depends on the timeout type.

### Why should logs be structured?

Structured logs allow reliable filtering and aggregation without fragile text parsing.

For example:

```text
service = orders-api
operation = create_order
error_type = DuplicateKeyError
```

is easier to analyze than parsing arbitrary message strings.

## Key Takeaways

- **MongoDB logging should complement metrics, traces, query diagnostics, and application logs rather than replace them.**
- **Use structured, centralized, searchable logs and preserve request or trace correlation so database failures can be connected to application behavior.**
- **Avoid logging credentials, connection strings, tokens, and complete sensitive documents; prefer query shapes, operation metadata, identifiers, and classified errors.**
- **Use targeted diagnostics such as the MongoDB profiler and `explain()` for detailed query investigation instead of continuously logging every database operation.**
- **Treat log volume, retention, rotation, access control, and security as production concerns because poorly designed logging can itself create cost, performance, and security problems.**