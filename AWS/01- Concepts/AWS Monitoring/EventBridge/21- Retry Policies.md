# Retry Policies

Temporary failures are common in distributed systems. A service may be temporarily unavailable due to network interruptions, throttling, or maintenance.

Amazon EventBridge automatically retries failed event deliveries according to a configurable **Retry Policy**, increasing the chances of successful delivery without requiring manual intervention.

------------------------------------------------------------------------

# What is a Retry Policy?

A Retry Policy defines how EventBridge should behave when an event cannot be delivered to its target.

Instead of failing immediately, EventBridge retries the delivery automatically.

------------------------------------------------------------------------

# Why Use Retry Policies?

Retry Policies help:

- Recover from temporary failures
- Improve reliability
- Reduce event loss
- Minimize manual intervention
- Increase application availability

------------------------------------------------------------------------

# Retry Workflow

```text
Event

   |

   v

Target

   |

Failure

   |

Retry

   |

Retry

   |

Retry

   |

Success?

   |

+-----------+

|           |

Yes         No

|           |

v           v

Done       DLQ
```

------------------------------------------------------------------------

# Retry Configuration

EventBridge allows you to configure:

- Maximum Retry Attempts
- Maximum Event Age

These settings determine how long EventBridge continues retrying.

------------------------------------------------------------------------

# Maximum Retry Attempts

Defines the maximum number of retries before giving up.

Example:

```text
Maximum Retry Attempts = 10
```

If all retries fail, the event is discarded or sent to a DLQ.

------------------------------------------------------------------------

# Maximum Event Age

Defines how long EventBridge should continue attempting delivery.

Example:

```text
Maximum Event Age = 24 Hours
```

If the event expires, retries stop.

------------------------------------------------------------------------

# Exponential Backoff

EventBridge uses exponential backoff between retries.

Instead of retrying continuously:

```text
1 Second

↓

2 Seconds

↓

4 Seconds

↓

8 Seconds
```

This reduces unnecessary load on target systems.

------------------------------------------------------------------------

# Common Failure Scenarios

Retry Policies help recover from:

- Temporary Lambda failures
- Network interruptions
- API throttling
- External API downtime
- Short-lived infrastructure issues

------------------------------------------------------------------------

# DLQ Integration

If retries are exhausted:

```text
Retry Failed

↓

Dead-Letter Queue
```

This prevents event loss.

------------------------------------------------------------------------

# Real-World Example

A Lambda function writes data to Amazon RDS.

The database is temporarily unavailable.

EventBridge retries the event several times.

After the database becomes available, the next retry succeeds automatically.

Without retries, the event would have failed permanently.

------------------------------------------------------------------------

# Best Practices

- Configure retry policies for all production rules.
- Use DLQs for critical workloads.
- Avoid excessively long retry periods.
- Monitor retry failures with CloudWatch.
- Review retry settings periodically.

------------------------------------------------------------------------

# Key Takeaways

- Retry Policies automatically recover from temporary delivery failures.
- EventBridge supports configurable retry attempts and event age.
- Exponential backoff improves reliability.
- Combine Retry Policies with DLQs for maximum resilience.