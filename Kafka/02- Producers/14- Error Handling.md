# Error Handling

## Overview

Failures are unavoidable in distributed systems. Networks become unavailable, brokers restart, partitions move between brokers, leaders change, and client applications may encounter invalid data.

A robust Kafka producer must be able to detect, classify, and recover from these failures without compromising data integrity.

Kafka provides several mechanisms for handling producer errors, including:

- Exception handling
- Automatic retries
- Idempotent producers
- Transactions
- Timeout management
- Error callbacks

Understanding these mechanisms helps build reliable, fault-tolerant event-driven applications.

---

# Why Error Handling Matters

Consider an Order Service.

```text
Customer

↓

Place Order

↓

Kafka Producer

↓

Kafka Broker
```

Suppose the broker becomes unavailable.

Without proper error handling:

```text
Send Message

↓

Failure

↓

Application Crash
```

With proper error handling:

```text
Send Message

↓

Failure

↓

Retry

↓

Success
```

The application continues without losing data.

---

# Types of Producer Errors

Kafka producer errors fall into two categories.

```text
Retryable Errors

↓

Temporary

---------------------

Non-Retryable Errors

↓

Permanent
```

Understanding this distinction is essential.

---

# Retryable Errors

Retryable errors are temporary failures.

Kafka can usually recover automatically.

Examples include:

- Network interruption
- Leader election
- Broker restart
- Request timeout
- Connection reset
- Temporary broker overload

Workflow:

```text
Producer

↓

Failure

↓

Retry

↓

Success
```

---

# Non-Retryable Errors

These errors require application intervention.

Examples:

- Invalid topic
- Authorization failure
- Authentication failure
- Serialization error
- Message too large
- Invalid configuration

Workflow:

```text
Producer

↓

Failure

↓

Exception

↓

Application Handles Error
```

Retries will not solve these problems.

---

# Error Handling Workflow

```text
Producer

↓

Send Message

↓

Success?

↓

Yes

↓

ACK

↓

Complete

---------------------

No

↓

Retryable?

↓

Yes

↓

Retry

↓

Success

---------------------

No

↓

Exception

↓

Application
```

---

# Common Producer Exceptions

Kafka exposes several exceptions.

Examples include:

- `TimeoutException`
- `SerializationException`
- `AuthorizationException`
- `AuthenticationException`
- `RecordTooLargeException`
- `UnknownTopicOrPartitionException`
- `NetworkException`

Applications should understand what each exception means.

---

# Serialization Errors

Suppose the producer attempts to serialize an unsupported object.

```text
Application Object

↓

Serializer

↓

Failure
```

Example:

```text
SerializationException
```

This occurs before the message reaches Kafka.

---

# Timeout Errors

Sometimes the producer waits too long for an acknowledgement.

```text
Producer

↓

Broker

↓

No Response

↓

Timeout
```

Typical exception:

```text
TimeoutException
```

Kafka may retry automatically depending on configuration.

---

# Network Errors

Temporary network failures are common.

```text
Producer

↓

Network Failure

↓

Retry

↓

Broker
```

Kafka handles most network interruptions automatically.

---

# Leader Election Errors

Suppose the leader broker crashes.

```text
Producer

↓

Old Leader

↓

Failure

↓

New Leader

↓

Retry
```

Kafka refreshes metadata and resends the request.

---

# Message Too Large

Every Kafka cluster has maximum message limits.

Suppose:

```text
Producer

↓

20 MB Message
```

Broker limit:

```text
10 MB
```

Result:

```text
RecordTooLargeException
```

The application must reduce the message size.

---

# Authentication Errors

Secure Kafka clusters require authentication.

```text
Producer

↓

Authenticate

↓

Failure
```

Example:

```text
AuthenticationException
```

Retries do not solve incorrect credentials.

---

# Authorization Errors

Suppose the producer lacks permission.

```text
Producer

↓

Write Topic

↓

Denied
```

Example:

```text
AuthorizationException
```

The producer must be granted appropriate permissions.

---

# Unknown Topic Errors

The producer attempts to send a message to a non-existent topic.

```text
Producer

↓

Unknown Topic

↓

Failure
```

Example:

```text
UnknownTopicOrPartitionException
```

The topic must exist before producing messages.

---

# Retry Strategy

Retryable failures follow this pattern.

```text
Attempt 1

↓

Failure

↓

Retry

↓

Failure

↓

Retry

↓

Success
```

Modern Kafka producers handle this automatically.

---

# Error Callbacks

Asynchronous producers provide callbacks.

Workflow:

```text
Producer

↓

Send

↓

Callback

↓

Success

or

↓

Exception
```

Applications can log or react to failures without blocking.

---

# Logging Errors

Every production producer should log meaningful errors.

Example:

```text
Timestamp

↓

Topic

↓

Partition

↓

Exception

↓

Retry Count
```

Detailed logs simplify troubleshooting.

---

# Dead Letter Queue (DLQ)

Sometimes a message cannot be processed successfully.

Instead of discarding it:

```text
Producer

↓

Failure

↓

Dead Letter Topic
```

Benefits:

- No data loss
- Easier debugging
- Later reprocessing

DLQs are especially useful in event-driven architectures.

---

# Circuit Breaker Pattern

Suppose Kafka becomes unavailable.

Instead of retrying endlessly:

```text
Failure

↓

Circuit Opens

↓

Reject Requests

↓

Recovery

↓

Circuit Closes
```

This protects the application from cascading failures.

---

# Error Handling with Transactions

Suppose a transaction fails.

```text
Begin Transaction

↓

Message A

↓

Failure

↓

Abort Transaction
```

Kafka removes all transactional writes.

No partial state remains.

---

# Error Monitoring

Monitor:

- Retry rate
- Error rate
- Timeout count
- Authentication failures
- Serialization failures

Increasing error rates usually indicate:

- Infrastructure problems
- Configuration mistakes
- Application bugs

---

# Recovery Strategies

Different failures require different responses.

| Error | Recommended Action |
|--------|--------------------|
| Network Failure | Retry |
| Leader Election | Retry |
| Timeout | Retry |
| Serialization Error | Fix application data |
| Authentication Error | Verify credentials |
| Authorization Error | Update permissions |
| Message Too Large | Reduce payload size |
| Unknown Topic | Create topic |

---

# Production Configuration

Reliable producer configuration:

```properties
acks=all

enable.idempotence=true

retries=Integer.MAX_VALUE

retry.backoff.ms=100

delivery.timeout.ms=120000
```

This configuration automatically recovers from most temporary failures.

---

# Best Practices

- Handle producer exceptions explicitly.
- Enable retries and idempotence.
- Log all producer failures.
- Monitor retry and error metrics.
- Use Dead Letter Topics when appropriate.
- Keep messages reasonably small.
- Validate data before serialization.
- Test failure scenarios during development.

---

# Common Mistakes

- Ignoring producer exceptions.
- Retrying non-retryable errors.
- Logging insufficient error information.
- Disabling retries.
- Assuming all failures are temporary.
- Not monitoring producer health.

---

# Summary

Error handling is a critical aspect of building reliable Kafka producers. Kafka automatically recovers from many temporary failures through retries, metadata refreshes, and idempotent producers. However, permanent errors such as serialization failures, authentication issues, and authorization problems require application-level handling. By combining retries, monitoring, logging, and appropriate recovery strategies, developers can build resilient producer applications capable of operating reliably in distributed environments.

---

# Key Takeaways

- Producer errors are classified as retryable or non-retryable.
- Kafka automatically retries temporary failures.
- Serialization, authentication, and authorization errors require application fixes.
- Idempotent producers prevent duplicate messages during retries.
- Transactions provide atomic recovery for multi-message operations.
- Error callbacks allow asynchronous failure handling.
- Monitoring and logging are essential for troubleshooting production issues.
- Effective error handling is fundamental to building resilient Kafka applications.