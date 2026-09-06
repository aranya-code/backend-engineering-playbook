# 08- Logging

## Overview

Logging is the structured recording of application and infrastructure events so engineers can understand system behavior, diagnose failures, investigate incidents, and operate services safely.

In backend systems, logging is part of observability rather than a replacement for metrics or distributed tracing.

A production observability model is:

```text
                    Application
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
        Logs         Metrics        Traces
          │             │             │
          └─────────────┼─────────────┘
                        ↓
              Observability Platform
                        ↓
             Engineers / Automation
```

Logs answer questions such as:

- What happened?
- When did it happen?
- Which request or job was involved?
- Which user or tenant was affected?
- Which service and instance produced the event?
- What error occurred?
- What relevant context existed at the time?

Good logging is **structured, actionable, bounded, secure, and operationally useful**.

---

## Why Logging Matters

Without useful logs, production debugging often becomes guesswork.

Consider an API request:

```text
Client
  ↓
Nginx
  ↓
FastAPI
  ↓
Service Layer
  ↓
PostgreSQL
  ↓
Redis
  ↓
Kafka
```

If the request fails, engineers may need to determine:

```text
Was the request received?
        ↓
Did authentication succeed?
        ↓
Did application validation fail?
        ↓
Did PostgreSQL fail?
        ↓
Did Redis time out?
        ↓
Was a Kafka event published?
```

Logs provide event-level evidence throughout this lifecycle.

---

## Python Logging Architecture

Python provides the standard `logging` package.

The core components are:

```text
Logger
   ↓
LogRecord
   ↓
Handler
   ↓
Formatter
   ↓
Output
```

A more complete flow is:

```text
Application Code
      ↓
    Logger
      ↓
   LogRecord
      ↓
   Filters
      ↓
   Handlers
      ↓
   Formatter
      ↓
stdout / stderr / file / external sink
      ↓
Log Collector
      ↓
Centralized Logging Platform
```

In containers, application logs should generally be written to standard output/error and collected by the platform.

---

## Loggers

A logger represents a named source of log events.

```python
import logging

logger = logging.getLogger(__name__)
```

Using:

```python
__name__
```

creates a logger hierarchy such as:

```text
order_service
order_service.api
order_service.services.orders
order_service.infrastructure.database
```

This makes selective configuration possible.

---

## Why `__name__` Is Preferred

Avoid:

```python
logger = logging.getLogger("app")
```

in every module.

Prefer:

```python
logger = logging.getLogger(__name__)
```

because the module path naturally identifies where the event originated.

For example:

```text
order_service.api.orders
```

is more useful than:

```text
app
```

when diagnosing a large codebase.

---

## Log Levels

Python provides standard severity levels:

| Level | Purpose | Typical usage |
|---|---|---|
| `DEBUG` | Detailed diagnostic information | Development/troubleshooting |
| `INFO` | Normal operational events | Startup, lifecycle, important state changes |
| `WARNING` | Unexpected but recoverable condition | Fallback, deprecated behavior, retry |
| `ERROR` | Operation failed | Request/job failure |
| `CRITICAL` | Severe system-level failure | Process/service-threatening condition |

Example:

```python
logger.debug("Parsed request payload")
logger.info("Order created")
logger.warning("Retrying database operation")
logger.error("Order creation failed")
logger.critical("Unable to initialize required infrastructure")
```

Log severity should describe operational significance, not developer emotion.

---

## Choosing Log Levels

A useful rule is:

```text
DEBUG
  Detailed information needed primarily during investigation

INFO
  Normal operational events worth observing

WARNING
  Something unexpected happened, but the system recovered

ERROR
  An operation failed and requires investigation or attention

CRITICAL
  The service may be unable to continue safely
```

Avoid logging every event as `ERROR`.

If everything is an error, severity loses meaning.

---

## Logging vs `print`

Avoid:

```python
print("Order created")
```

in production backend code.

`print()` does not provide standard logging features such as:

- severity levels;
- logger hierarchy;
- structured metadata;
- filtering;
- configurable handlers;
- timestamps;
- exception information;
- centralized configuration.

Use:

```python
logger.info("Order created")
```

instead.

---

## Basic Configuration

A simple application can configure logging centrally:

```python
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)
```

Application modules should generally obtain loggers rather than configure the root logger themselves.

---

## Root Logger

Python has a root logger:

```text
root
 ├── order_service
 │    ├── api
 │    ├── services
 │    └── database
 └── third_party_library
```

Configuration applied to the root logger can affect descendant loggers.

This is useful for application-wide defaults but can become problematic when libraries unexpectedly modify global logging behavior.

---

## Logger Propagation

By default, log records can propagate from child loggers to ancestor loggers.

For example:

```text
order_service.api.orders
          ↓
order_service.api
          ↓
order_service
          ↓
root
```

This is useful when handlers are configured centrally.

A common mistake is configuring handlers at multiple levels and accidentally emitting duplicate records.

---

## Handlers

A handler determines where log records go.

Common handlers include:

```text
StreamHandler
FileHandler
RotatingFileHandler
```

For containerized services, prefer:

```text
Python
  ↓
stdout/stderr
  ↓
Docker/container runtime
  ↓
Kubernetes logging pipeline
```

rather than application-managed log files inside containers.

---

## Formatters

A formatter converts a `LogRecord` into an output representation.

Traditional text logging:

```text
2026-09-06 20:10:30 INFO order_service.orders Order created
```

Structured logging:

```json
{
  "timestamp": "2026-09-06T20:10:30Z",
  "level": "INFO",
  "logger": "order_service.orders",
  "message": "Order created",
  "order_id": "ord_123"
}
```

Structured logs are generally preferable for production systems because log platforms can index individual fields.

---

## Structured Logging

Structured logging represents events as machine-readable fields rather than embedding all context into a message string.

Prefer:

```python
logger.info(
    "Order created",
    extra={
        "order_id": order.id,
        "customer_id": order.customer_id,
    },
)
```

when using a formatter or logging framework that exposes those fields.

A structured logging library can provide a more ergonomic API.

The important architectural principle is:

```text
Event
+
Typed fields
+
Severity
+
Timestamp
+
Context
```

rather than:

```text
One large human-formatted string
```

---

## Structured vs Unstructured Logs

| Aspect | Unstructured | Structured |
|---|---|---|
| Human readability | Good | Good |
| Machine parsing | Difficult | Easy |
| Field filtering | Limited | Excellent |
| Searchability | Lower | Higher |
| Aggregation | Harder | Easier |
| Production recommendation | Limited | Preferred |

Structured logging becomes increasingly valuable as the number of services and log volume grows.

---

## Recommended Log Fields

A backend log event may contain:

```text
timestamp
level
service
environment
logger
message
request_id
trace_id
span_id
user_id / tenant_id
route
method
status_code
duration_ms
error_type
```

Only include fields that are safe and operationally useful.

---

## Request Correlation

One of the most important logging patterns in distributed systems is request correlation.

Example:

```text
Client
  ↓
request_id = req_8f21
  ↓
API Gateway
  ↓
FastAPI
  ↓
PostgreSQL
  ↓
Kafka
  ↓
Worker
```

Logs across services can include:

```text
request_id=req_8f21
```

This allows engineers to reconstruct the lifecycle of a request.

---

## Request ID vs Trace ID

These concepts are related but different.

| Identifier | Purpose |
|---|---|
| Request ID | Identifies an application request |
| Trace ID | Identifies a distributed trace |
| Span ID | Identifies one operation within a trace |
| Job ID | Identifies a background task |
| Event ID | Identifies a specific event |

For distributed systems, trace IDs generally provide richer correlation because one request can generate many spans across services.

---

## Request Lifecycle Logging

A REST API might produce:

```text
request_received
      ↓
authentication_completed
      ↓
validation_completed
      ↓
database_operation
      ↓
response_sent
```

Avoid logging every internal function call.

Log meaningful boundaries.

---

## FastAPI Request Logging

A middleware layer can establish request context.

Conceptually:

```python
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request

app = FastAPI()
logger = logging.getLogger(__name__)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled request failure",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )
        raise

    duration_ms = (time.perf_counter() - started) * 1000

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )

    return response
```

In production, prefer a centralized logging/context implementation rather than duplicating request metadata manually.

---

## Django Logging

Django integrates with Python's `logging` system.

A production Django deployment should configure loggers by subsystem:

```text
django
django.request
django.db.backends
application
application.api
application.tasks
```

For example:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
```

The exact configuration should be adapted to the application's deployment and logging pipeline.

---

## Logging Exceptions

Use `logger.exception()` when handling an exception and wanting traceback information.

```python
try:
    process_order(order)
except PaymentError:
    logger.exception(
        "Payment processing failed",
        extra={"order_id": order.id},
    )
    raise
```

`logger.exception()` should normally be called inside an exception handler.

It records the exception traceback.

---

## `logger.error()` vs `logger.exception()`

Use:

```python
logger.error("Payment failed")
```

when traceback information is not required.

Use:

```python
logger.exception("Payment failed")
```

when the exception context and traceback are useful.

Do not blindly log the same exception at every layer.

---

## Exception Logging and Propagation

Avoid:

```python
try:
    service.execute()
except Exception:
    logger.exception("Failed")
    raise
```

at every layer.

This can generate:

```text
same exception
  ↓
repository log
  ↓
service log
  ↓
API log
  ↓
middleware log
```

One meaningful error event with sufficient context is usually better.

Add context as the exception crosses boundaries, but avoid repetitive stack traces.

---

## Logging Exceptions Without Leaking Data

Exception messages can contain sensitive values.

For example:

```python
logger.exception(
    "Authentication failed",
    extra={"username": username},
)
```

may be inappropriate depending on the application's privacy requirements.

Never log:

- passwords;
- access tokens;
- refresh tokens;
- API keys;
- session cookies;
- private encryption keys;
- authorization headers.

---

## Lazy Log Formatting

Prefer:

```python
logger.debug("Processing order %s", order_id)
```

over:

```python
logger.debug(f"Processing order {order_id}")
```

The logging API can avoid formatting work when the log level is disabled.

For example:

```python
logger.debug("Large object: %s", expensive_object)
```

is preferable to eagerly constructing a formatted string.

For structured logging, use the structured logger's native field mechanism.

---

## Expensive Logging

Avoid:

```python
logger.debug(
    "Payload=%s",
    json.dumps(huge_payload),
)
```

because serialization may happen before logging determines whether the message will be emitted.

Prefer:

```python
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("Payload=%s", summarize_payload(payload))
```

when generating the log data itself is expensive.

Do not optimize ordinary logging prematurely; optimize expensive serialization, object traversal, or formatting when profiling demonstrates a real cost.

---

## Logging in Hot Paths

High-frequency code requires careful logging.

Dangerous:

```python
for record in millions_of_records:
    logger.info("Processed record %s", record.id)
```

This can produce:

```text
millions of events
↓
CPU overhead
↓
I/O overhead
↓
storage cost
↓
network traffic
↓
log ingestion pressure
```

Prefer aggregation:

```python
logger.info(
    "Batch processed",
    extra={
        "records_processed": count,
        "duration_ms": duration_ms,
    },
)
```

---

## Logging and Performance

Logging consumes:

- CPU;
- memory;
- serialization time;
- network bandwidth;
- storage;
- ingestion capacity.

The cost increases with:

```text
event volume
×
event size
×
serialization complexity
```

High-volume systems should carefully control log levels and payload sizes.

---

## Logging Levels by Environment

A common strategy is:

| Environment | Typical level |
|---|---|
| Local development | `DEBUG` |
| CI | `INFO` |
| Staging | `INFO` |
| Production | `INFO` or higher |
| Temporary investigation | Controlled `DEBUG` |

Avoid permanently running production systems at verbose debug levels without a clear reason.

---

## Logging Configuration

Logging configuration belongs in application configuration management.

Example:

```dotenv
APP_LOG_LEVEL=INFO
APP_LOG_FORMAT=json
```

The logging system should read these settings during application initialization.

This keeps deployment behavior separate from source code.

---

## JSON Logging

A production service commonly emits one JSON object per line:

```json
{"timestamp":"2026-09-06T14:30:00Z","level":"INFO","service":"orders","message":"Order created","order_id":"ord_123","request_id":"req_456"}
```

This works well with log collectors and search systems.

Avoid embedding multiline JSON inside one log event.

---

## Log Collection in Kubernetes

A typical Kubernetes architecture is:

```mermaid
flowchart LR
    A[Python Application] --> B[stdout / stderr]
    B --> C[Container Runtime]
    C --> D[Node Log Files]
    D --> E[Log Collector]
    E --> F[Central Logging Platform]
    F --> G[Search / Alerts / Dashboards]
```

Common collection technologies include:

- Fluent Bit;
- Fluentd;
- OpenTelemetry Collector;
- cloud-native logging agents.

The exact stack depends on the platform.

---

## Why Containers Should Usually Log to stdout

Avoid relying on:

```text
/app/logs/service.log
```

inside an ephemeral container.

Container filesystems may disappear when containers are replaced.

Prefer:

```text
Application
   ↓
stdout/stderr
   ↓
container runtime
   ↓
log collector
```

The infrastructure owns collection and retention.

---

## Log Rotation

Traditional applications writing local files need rotation.

Without rotation:

```text
service.log
    ↓
10 MB
    ↓
1 GB
    ↓
50 GB
    ↓
disk full
```

Containerized applications generally delegate rotation and retention to the platform rather than implementing custom file rotation inside every application.

---

## Centralized Logging

Microservices require centralized log aggregation.

Without centralization:

```text
Service A → pod logs
Service B → pod logs
Service C → pod logs
```

Debugging a distributed request becomes difficult.

Centralization provides:

- cross-service search;
- correlation;
- retention;
- access control;
- alerting;
- dashboards;
- incident investigation.

---

## Logs and Distributed Tracing

Logs and traces solve different problems.

```text
Trace
  ↓
Where did latency occur?

Logs
  ↓
What happened inside that operation?

Metrics
  ↓
How often is the problem occurring?
```

A strong production system correlates them using:

```text
trace_id
span_id
request_id
```

For example:

```text
Trace
 ├── API request
 │     ├── authentication
 │     ├── PostgreSQL query
 │     └── Redis lookup
 │
 └── Kafka publish
```

Each span can have associated logs/events.

---

## Logs and Metrics

Do not use logs as a substitute for metrics.

Bad approach:

```text
logger.info("Request succeeded")
```

for every request and then count logs to estimate request volume.

Prefer:

```text
Metric:
http_requests_total

Log:
Request completed with request_id=...
```

Metrics are optimized for aggregation; logs are optimized for event investigation.

---

## Logs and Alerts

Alerts should generally be based on metrics or well-defined event signals rather than arbitrary log strings.

Prefer:

```text
5xx rate > 2%
```

over:

```text
message contains "error"
```

Logs can provide diagnostic context after an alert fires.

---

## Database Logging

Avoid logging every SQL query in production unless there is a specific diagnostic need.

For example:

```text
SELECT * FROM orders WHERE ...
```

may contain:

- sensitive values;
- large query volume;
- excessive storage;
- unnecessary latency.

Use database observability tools and query analysis for systematic database performance investigation.

---

## PostgreSQL and Application Logs

Application logs should capture useful database operation context:

```text
operation=order_lookup
duration_ms=18
rows=1
```

rather than dumping complete SQL statements and parameters.

PostgreSQL's own logging and `EXPLAIN ANALYZE` are better tools for database-level diagnosis.

---

## Redis Logging

For Redis operations, useful application-level logs might include:

```text
cache_operation=get
key_namespace=order
result=miss
duration_ms=2
```

Avoid logging full values if they may contain sensitive or large payloads.

---

## Kafka Logging

Kafka consumers and producers benefit from operational logs such as:

```text
consumer_group=orders
topic=order-events
partition=4
offset=18291
event_id=evt_123
processing_duration_ms=12
```

Avoid logging entire event payloads by default.

Event identifiers and metadata are usually more useful.

---

## Celery Logging

Background jobs need identifiers different from HTTP requests.

Useful fields include:

```text
task_name
task_id
queue
attempt
duration_ms
status
```

Example:

```python
logger.info(
    "Task completed",
    extra={
        "task_name": "orders.send_confirmation",
        "task_id": task_id,
        "duration_ms": duration_ms,
    },
)
```

A background job may continue long after its originating HTTP request has completed, so `task_id` is often essential for correlation.

---

## Logging Background Jobs

A useful lifecycle is:

```text
Job submitted
     ↓
Job received
     ↓
Job started
     ↓
External dependency call
     ↓
Job completed / failed
```

Do not log every internal operation unless needed for debugging.

---

## Logging Retries

Retries are operationally significant.

Useful:

```text
operation=payment_request
attempt=2
max_attempts=3
reason=timeout
backoff_ms=500
```

Avoid producing a full stack trace for every expected transient retry.

Log the final failure at an appropriate severity if the operation ultimately fails.

---

## Logging Timeouts

Timeout logs should include enough context to identify the dependency:

```text
dependency=payment-api
operation=charge
timeout_ms=3000
attempt=2
```

Avoid logging sensitive request payloads.

---

## Logging Authentication Events

Security-relevant events may include:

```text
authentication_success
authentication_failure
authorization_denied
token_refresh_failure
session_revoked
```

Security logs should be carefully designed to avoid leaking credentials or personal data.

---

## Security Logging

Logging can itself become a security vulnerability.

Never log:

```text
Authorization: Bearer <token>
Cookie: session=<secret>
password=<secret>
api_key=<secret>
private_key=<secret>
```

Use redaction where necessary:

```text
Authorization: [REDACTED]
```

Prefer preventing sensitive data from entering log records in the first place.

---

## Log Injection

Never blindly concatenate untrusted input into multiline logs.

For example, attacker-controlled input could contain:

```text
\nERROR fake security event
```

Structured logging reduces parsing ambiguity.

Sanitize or encode user-controlled values when necessary.

---

## Privacy and PII

Logs may contain personally identifiable information.

Potentially sensitive data includes:

- email addresses;
- phone numbers;
- IP addresses;
- names;
- addresses;
- customer identifiers;
- request payloads.

Define explicit logging policies for sensitive data.

Do not assume internal logs are automatically safe.

---

## Data Retention

Log retention should be based on:

```text
Operational value
+
Compliance requirements
+
Security requirements
+
Storage cost
```

Not every debug event needs months of retention.

A common strategy is:

```text
High-value operational logs → longer retention
Debug logs                 → shorter retention
Security audit events      → policy-driven retention
```

---

## Cost Management

Logging can become a significant cloud expense.

Cost roughly grows with:

```text
log volume
×
retention duration
×
ingestion cost
×
storage/query cost
```

Reduce cost through:

- appropriate log levels;
- compact structured fields;
- avoiding payload dumps;
- sampling high-volume events where appropriate;
- retention policies;
- separate high-value audit logs;
- aggregation of repetitive events.

---

## Sampling

High-volume systems may sample certain logs.

For example:

```text
100,000 successful requests
       ↓
Sample 1% for detailed request logs
```

But errors and security events generally require stronger guarantees than ordinary success events.

Sampling policy must be explicit.

Do not blindly sample events needed for audit or incident response.

---

## Audit Logs vs Application Logs

These should not automatically be treated as the same thing.

### Application Logs

Used for:

```text
debugging
operations
performance investigation
failure diagnosis
```

### Audit Logs

Used for:

```text
who performed an action
what changed
when it changed
what resource was affected
```

Audit events may require:

- stronger integrity;
- controlled access;
- longer retention;
- dedicated storage;
- stricter compliance controls.

---

## Logging Configuration Example

A simple centralized configuration can use `dictConfig`:

```python
import logging
import logging.config


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": (
                "%(asctime)s %(levelname)s "
                "%(name)s %(message)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}


logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)
```

For production JSON logging, use a formatter or structured logging implementation appropriate for the application's observability stack.

---

## Contextual Logging

Request context can be propagated through logging context.

Python provides mechanisms such as:

```text
contextvars
LoggerAdapter
Filters
structured logging context
```

For asynchronous applications, `contextvars` is particularly useful because context can follow asyncio task execution without relying on mutable global state.

Conceptually:

```text
HTTP Request
    ↓
ContextVar(request_id)
    ↓
Service code
    ↓
Database layer
    ↓
Logging
```

---

## `contextvars` Example

```python
import logging
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

logger = logging.getLogger(__name__)


def log_order_created(order_id: str) -> None:
    logger.info(
        "Order created",
        extra={
            "request_id": request_id_var.get(),
            "order_id": order_id,
        },
    )
```

Middleware can set the request ID at the request boundary.

The implementation should also reset context appropriately when the request completes.

---

## Asyncio Considerations

Logging from asyncio applications should not block the event loop unnecessarily.

Potentially expensive operations include:

- large JSON serialization;
- slow file handlers;
- network logging handlers;
- synchronous external logging calls.

A synchronous logging handler performing blocking I/O can delay unrelated requests sharing the event loop.

For high-volume async applications, consider queue-based logging or an external collector architecture.

---

## Queue-Based Logging

Python provides `QueueHandler` and `QueueListener` for decoupling log production from log output.

Conceptually:

```text
Application
     ↓
QueueHandler
     ↓
In-memory queue
     ↓
QueueListener
     ↓
Output handler
```

This can reduce blocking in application threads.

However, queues introduce:

- memory usage;
- queue saturation;
- shutdown complexity;
- potential event loss depending on design.

They should be used when the performance characteristics justify them.

---

## Logging and Multiprocessing

Multiple Python worker processes produce independent log streams.

For example:

```text
Gunicorn
 ├── Worker 1 → stdout
 ├── Worker 2 → stdout
 ├── Worker 3 → stdout
 └── Worker 4 → stdout
```

The infrastructure should aggregate these streams.

Avoid assuming that in-process state can coordinate logging across workers.

---

## Logging and Threads

Python's standard logging system is designed to support concurrent use from multiple threads.

The main concern is not thread safety of ordinary logging calls but:

- volume;
- blocking handlers;
- shared contextual state;
- output ordering;
- expensive formatting.

Do not store request-specific context in mutable global variables.

---

## Logging and Forking

Applications using pre-fork servers such as Gunicorn should configure logging carefully.

Handlers created before forking can have undesirable interactions depending on the handler and output destination.

Prefer server/framework-supported logging configuration and validate behavior under the actual deployment model.

---

## Log Ordering

Distributed logs are not guaranteed to appear in global chronological order.

Factors include:

- multiple processes;
- multiple hosts;
- buffering;
- network transport;
- collector delays;
- clock skew.

Use identifiers and timestamps for correlation rather than assuming ingestion order equals event order.

---

## Clock Considerations

Distributed systems should use consistent timestamps.

Prefer UTC:

```text
2026-09-06T14:30:00.123Z
```

rather than local timezone timestamps.

For latency measurements inside a process, use a monotonic clock such as:

```python
time.perf_counter()
```

Do not calculate durations by subtracting wall-clock timestamps when clock adjustments can affect the result.

---

## Log Schema Stability

Structured logs should have relatively stable field names.

Prefer:

```text
request_id
status_code
duration_ms
```

rather than inconsistent variants:

```text
requestId
request-id
req_id
```

Stable schemas make dashboards, searches, alerts, and automated analysis more reliable.

---

## Versioning Log Schemas

If logs are consumed by downstream systems, schema changes should be treated carefully.

For example:

```text
log_schema_version=2
```

may be useful when the format evolves significantly.

Avoid unnecessary schema versioning for every small application change.

---

## Logging and Error Responses

Do not expose internal log details directly to API clients.

Bad:

```json
{
  "error": "psycopg2.OperationalError: password authentication failed..."
}
```

Prefer:

```json
{
  "error": "internal_server_error",
  "request_id": "req_123"
}
```

The client receives a safe identifier; engineers use the identifier to locate detailed logs.

---

## Logging and REST APIs

Useful request-level fields include:

```text
method
route
status_code
duration_ms
request_id
trace_id
```

Avoid:

```text
full Authorization header
full cookies
full request body
```

unless specifically required and safely redacted.

---

## Logging and gRPC

gRPC services can log:

```text
grpc.service
grpc.method
grpc.status_code
duration_ms
trace_id
```

For example:

```text
service=OrderService
method=CreateOrder
status=OK
duration_ms=12
```

gRPC metadata can carry correlation information, but sensitive metadata should not automatically be logged.

---

## Logging and Microservices

Each service should produce consistent fields:

```text
timestamp
service
environment
level
trace_id
request_id
message
```

Example:

```text
orders-service
payments-service
inventory-service
notification-service
```

A centralized schema makes cross-service debugging significantly easier.

---

## Logging and Kubernetes

Production logging should account for:

```text
Pods
Containers
Nodes
Replica changes
Restarts
Deployments
```

Useful metadata includes:

```text
service
namespace
pod
container
environment
deployment_version
```

Infrastructure collectors often enrich logs with these fields automatically.

---

## Logging and AWS

AWS environments may integrate logs with services such as:

```text
CloudWatch Logs
OpenTelemetry-compatible pipelines
Amazon OpenSearch Service
S3-based archival
```

A common architecture is:

```text
Python container
      ↓
stdout
      ↓
collector
      ↓
CloudWatch / logging platform
      ↓
search + alerting + retention
```

Choose the destination based on query requirements, retention, compliance, and cost.

---

## Logging During Deployments

Deployment logs should make version information available:

```text
service=orders
version=2026.09.06
environment=production
```

This helps answer:

```text
Did errors start after deployment X?
```

Useful deployment correlation fields include:

```text
deployment_version
git_sha
build_id
```

Do not log unnecessary internal repository information if it creates security concerns.

---

## Logging Startup and Shutdown

Important lifecycle events include:

```text
application_starting
configuration_validated
database_pool_initialized
consumer_started
application_ready
application_shutdown
```

Example:

```python
logger.info(
    "Application ready",
    extra={
        "service": settings.service_name,
        "version": settings.version,
    },
)
```

Startup logs should not indicate readiness before required dependencies are initialized.

---

## Graceful Shutdown Logging

A service should make shutdown behavior observable:

```text
shutdown_requested
stop_accepting_requests
draining_requests
stopping_consumers
closing_database_pool
shutdown_complete
```

This is particularly useful during Kubernetes rolling deployments.

---

## Logging Health Checks

Do not log every Kubernetes liveness probe request at `INFO`.

For example:

```text
GET /healthz
GET /readyz
```

may occur frequently across many replicas.

Use lower severity or filtering where appropriate.

Health endpoints should be observable through metrics without generating excessive logs.

---

## Logging Metrics

Useful metrics include:

```text
log_events_total
log_errors_total
log_dropped_total
logging_queue_depth
```

Application-specific metrics remain more useful for business and service health.

Logging infrastructure should itself be observable when it can become a bottleneck.

---

## Handling Logging Failures

Logging should not normally take the application down.

For example:

```text
Central logging unavailable
        ↓
Application continues
        ↓
Logs buffered/dropped according to policy
```

The exact behavior depends on the criticality of the logs.

For audit/security events, stronger durability guarantees may be required.

---

## Reliability and Log Loss

Logs can be lost because of:

- process crashes;
- buffering;
- collector failures;
- network failures;
- disk pressure;
- queue overflow;
- container termination.

Do not assume ordinary application logs are durable records.

If an event is business-critical, persist it in an appropriate durable system rather than relying on logs.

---

## Logging Business Events

Logging:

```python
logger.info("Payment completed")
```

does not guarantee that the business event is durable.

If another service must consume the event, use:

```text
Database transaction
      +
Outbox/event mechanism
      ↓
Kafka
```

Logs are observability artifacts, not reliable event buses.

---

## Logging and Transactions

For a database transaction:

```text
BEGIN
  ↓
Update order
  ↓
COMMIT
```

log the successful business operation after the relevant transaction outcome is known.

Avoid emitting misleading logs such as:

```text
"Order created"
```

before the transaction actually commits.

---

## Logging and Performance Profiling

Logs can help identify latency but should not replace profiling.

Use:

```text
Logs
→ individual events and context

Metrics
→ aggregate latency/error rates

Tracing
→ distributed request path

cProfile / py-spy
→ CPU behavior

tracemalloc
→ Python allocation behavior
```

Each tool answers a different question.

---

## Testing Logging

Logging behavior can be tested when it is part of an operational contract.

With pytest:

```python
def test_invalid_order_logs_warning(caplog):
    with caplog.at_level("WARNING"):
        validate_order(...)

    assert "Invalid order" in caplog.text
```

Prefer testing important fields or event semantics rather than brittle exact formatting.

---

## Testing Sensitive Data Redaction

Redaction should be explicitly tested.

```python
def test_password_is_not_logged(caplog):
    process_login(
        username="customer@example.com",
        password="super-secret",
    )

    assert "super-secret" not in caplog.text
```

Security-sensitive logging behavior deserves regression tests.

---

## Testing Log Volume

High-volume components can benefit from tests or benchmarks that ensure logging does not accidentally become excessive.

For example:

```text
One batch
    ↓
One operational log
```

is often preferable to:

```text
One batch
    ↓
100,000 per-record INFO logs
```

---

## Common Mistakes

### Using `print()`

`print()` lacks logging levels, filtering, context, and centralized configuration.

### Logging Everything at `INFO`

This creates excessive volume and reduces the signal-to-noise ratio.

### Logging Every Exception at Every Layer

This produces duplicate stack traces and inflated error counts.

### Logging Entire Request Bodies

Request bodies can contain secrets, PII, and large payloads.

### Logging Credentials

Never log passwords, tokens, API keys, or authorization headers.

### Using Dynamic Log Messages as Schemas

Messages such as:

```text
Order 123 failed
Order 456 failed
```

are harder to query than:

```text
event=order_failed order_id=123
```

### Writing Application Logs to Container Files

Ephemeral container files are a poor primary logging architecture.

### Performing Blocking Logging on an Async Event Loop

Slow handlers can increase request latency.

### Using Logs as a Database

Logs are not transactional or authoritative business state.

---

## Production Pitfalls

### Log Volume Explosion

A small per-request log can become enormous at high traffic.

Estimate:

```text
requests/sec
×
logs/request
×
average bytes/log
```

before enabling verbose logging.

### Duplicate Logs

Incorrect handler and propagation configuration can emit the same event multiple times.

### Missing Correlation IDs

Without request or trace correlation, distributed debugging becomes significantly harder.

### Unstable Field Names

Changing:

```text
request_id
```

to:

```text
requestId
```

breaks queries, dashboards, and downstream consumers.

### Logging Secrets Through Exceptions

Third-party exceptions may contain connection strings or request metadata.

Inspect and sanitize exception output before exposing it to logs.

### Assuming Log Arrival Order

Distributed logging pipelines are asynchronous. Ingestion order is not necessarily event order.

---

## Recommended Production Log Schema

A practical baseline is:

```json
{
  "timestamp": "2026-09-06T14:30:00.123Z",
  "level": "INFO",
  "service": "order-service",
  "environment": "production",
  "logger": "order_service.api.orders",
  "message": "Order created",
  "trace_id": "trace_123",
  "span_id": "span_456",
  "request_id": "req_789",
  "route": "/orders",
  "method": "POST",
  "status_code": 201,
  "duration_ms": 42,
  "order_id": "ord_123"
}
```

The exact schema should reflect the organization's observability platform.

---

## Recommended Logging Strategy

A mature backend can follow:

```text
Application Boundary
    ↓
Request / Job Context
    ↓
Structured Event
    ↓
Appropriate Severity
    ↓
stdout / stderr
    ↓
Collector
    ↓
Centralized Storage
    ↓
Search / Dashboards / Alerting

          +
       Metrics
          +
        Traces
```

The application produces useful events; the infrastructure handles collection, transport, retention, and analysis.

---

## Logging Decision Framework

Before adding a log statement, ask:

1. Is this event operationally meaningful?
2. What severity should it have?
3. What context is required to investigate it?
4. Could the same information be represented more effectively as a metric or trace?
5. Does it contain sensitive information?
6. Could it execute at high frequency?
7. Does it add meaningful CPU, memory, or I/O overhead?
8. Can the event be correlated with a request, trace, job, or event ID?
9. Is the message/schema stable enough for production queries?
10. Does the log need long-term retention?

---

## Best Practices

- Use Python's `logging` infrastructure rather than `print()`.
- Create module-level loggers with `logging.getLogger(__name__)`.
- Centralize logging configuration.
- Prefer structured JSON logs in production.
- Use stable field names.
- Include request/trace/job identifiers.
- Use UTC timestamps.
- Use `logger.exception()` when traceback context is genuinely useful.
- Avoid duplicate exception logging.
- Never log credentials or secrets.
- Minimize PII.
- Avoid full request/response payload logging by default.
- Keep high-volume paths quiet.
- Emit logs to stdout/stderr in containers.
- Let infrastructure handle collection and retention.
- Correlate logs with traces and metrics.
- Keep audit logging separate when stronger durability or compliance guarantees are required.
- Test redaction and important logging behavior.
- Monitor logging volume and infrastructure health.

---

## Operational Checklist

### Application

- [ ] Every module uses a named logger.
- [ ] Logging configuration is centralized.
- [ ] Log levels have clear semantics.
- [ ] Important operations have useful context.
- [ ] Exceptions are not logged redundantly.
- [ ] High-frequency paths are controlled.

### Structured Logging

- [ ] Logs have stable field names.
- [ ] Timestamps use UTC.
- [ ] Request or trace correlation is available.
- [ ] Job IDs are logged for background work.
- [ ] Error events contain actionable context.

### Security

- [ ] Passwords are never logged.
- [ ] Tokens and API keys are never logged.
- [ ] Authorization headers are redacted.
- [ ] Sensitive request data is controlled.
- [ ] PII logging follows policy.
- [ ] Audit events have appropriate access controls and retention.

### Infrastructure

- [ ] Containers write logs to stdout/stderr.
- [ ] Kubernetes log collection is configured.
- [ ] Log retention is defined.
- [ ] Log ingestion failures are observable.
- [ ] Log volume and cost are monitored.
- [ ] Production logging is tested under realistic traffic.

### Observability

- [ ] Logs correlate with traces.
- [ ] Metrics are used for aggregate health signals.
- [ ] Alerts do not depend solely on arbitrary log strings.
- [ ] Deployment versions can be correlated with events.
- [ ] Distributed log ordering assumptions are avoided.

## Interview Traps

### Are Logs Observability?

Logs are one pillar of observability. Metrics and traces provide complementary information.

### Should Every Exception Be Logged?

No. Log exceptions at meaningful boundaries. Repeatedly logging and re-raising the same exception creates duplicate events.

### Why Use Structured Logging?

Structured fields are easier for machines to index, filter, aggregate, correlate, and analyze than arbitrary message strings.

### Why Log to stdout in Containers?

Container platforms can collect stdout/stderr reliably across ephemeral containers and route the output to centralized logging infrastructure.

### Should Logs Contain Request Bodies?

Usually not by default. Bodies may contain secrets, PII, and large payloads. Log selected safe fields instead.

### Why Are Logs Not a Replacement for Metrics?

Logs represent individual events. Metrics efficiently represent aggregated quantities such as request rate, error rate, and latency distributions.

### Why Are Logs Not a Replacement for Tracing?

Logs show event details, while distributed tracing reconstructs the path and timing of a request across services.

### What Happens If the Logging System Is Down?

Application logging should have a defined failure policy. Ordinary diagnostic logs may be buffered or dropped, while security/audit records may require stronger durability guarantees.

### Why Can Logging Hurt an Async Application?

Synchronous or expensive logging can perform blocking I/O or serialization on the event-loop thread, increasing request latency.

### Why Should Application Logs Not Be Used as Business Events?

Logs are not transactional or durable business state. Business events that other systems depend on should use appropriate durable mechanisms such as database transactions and event/outbox patterns.

## Key Takeaways

- **Treat logging as an observability system:** use structured events for investigation, metrics for aggregation, and traces for distributed request flow.
- **Make production logs structured and correlated:** stable fields such as `service`, `level`, `timestamp`, `trace_id`, `request_id`, and operation-specific identifiers make distributed debugging practical.
- **Control logging for security and performance:** never log secrets, minimize sensitive data, avoid high-volume payload logging, and prevent expensive or blocking logging from degrading application performance.
- **Let the platform handle log collection:** containerized Python services should generally emit logs to stdout/stderr and rely on Kubernetes, AWS, or an observability pipeline for collection, retention, and search.
- **Design logging as part of system architecture:** account for concurrency, background jobs, databases, Kafka, rolling deployments, log loss, retention, cost, audit requirements, and failure behavior.