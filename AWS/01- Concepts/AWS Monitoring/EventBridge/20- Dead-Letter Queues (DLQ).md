# Dead-Letter Queues (DLQ)

In distributed systems, event delivery can sometimes fail due to network issues, service outages, permission errors, or application failures.

Amazon EventBridge supports **Dead-Letter Queues (DLQs)** to ensure that failed events are not lost. Instead, undelivered events are stored in an Amazon SQS queue for later analysis and reprocessing.

------------------------------------------------------------------------

# What is a Dead-Letter Queue?

A Dead-Letter Queue (DLQ) is an Amazon SQS queue that stores events which EventBridge could not deliver successfully after exhausting all retry attempts.

Instead of discarding failed events, EventBridge sends them to the DLQ.

------------------------------------------------------------------------

# Why Use a DLQ?

DLQs help you:

- Prevent event loss
- Troubleshoot failures
- Replay failed events
- Improve application reliability
- Audit delivery failures

------------------------------------------------------------------------

# How DLQs Work

```text
Event

   |

   v

EventBridge Rule

   |

   v

Target

   |

Delivery Failed

   |

Retry Attempts

   |

Still Failed?

   |

   v

Dead-Letter Queue (Amazon SQS)
```

------------------------------------------------------------------------

# Failure Scenarios

Events may fail because of:

- Lambda execution failures
- Missing IAM permissions
- Network errors
- Target service outages
- Invalid API responses
- Resource deletion

Instead of losing these events, they are stored in the DLQ.

------------------------------------------------------------------------

# Supported Targets

DLQs are supported by many EventBridge targets, including:

- AWS Lambda
- Amazon SNS
- Amazon SQS
- AWS Step Functions
- API Destinations

------------------------------------------------------------------------

# Viewing Failed Events

Since the DLQ is an Amazon SQS queue, engineers can:

- Read messages
- Analyze failures
- Replay events
- Delete processed messages

Each message contains the original event payload and failure metadata.

------------------------------------------------------------------------

# Replaying Failed Events

After resolving the issue:

1. Read events from the DLQ.
2. Reprocess them manually or automatically.
3. Publish them back to EventBridge if required.

This prevents permanent data loss.

------------------------------------------------------------------------

# Real-World Example

An EventBridge Rule invokes a Lambda function.

The Lambda function fails because the downstream database is unavailable.

```text
Order Created

↓

EventBridge

↓

Lambda

↓

Database Offline

↓

Retry

↓

Retry

↓

Retry

↓

DLQ (Amazon SQS)
```

After the database is restored, the operations team processes the failed events from the DLQ.

------------------------------------------------------------------------

# Best Practices

- Configure a DLQ for critical EventBridge rules.
- Monitor DLQ message count using CloudWatch.
- Investigate failures promptly.
- Remove successfully reprocessed messages.
- Secure DLQs using IAM policies.

------------------------------------------------------------------------

# Common Mistakes

- Not configuring a DLQ.
- Ignoring failed messages.
- Deleting messages before analysis.
- Using the same DLQ for unrelated applications.

------------------------------------------------------------------------

# Key Takeaways

- A Dead-Letter Queue stores events that could not be delivered.
- EventBridge uses Amazon SQS as the DLQ.
- DLQs prevent event loss and simplify troubleshooting.
- Every production EventBridge workflow should consider using a DLQ.