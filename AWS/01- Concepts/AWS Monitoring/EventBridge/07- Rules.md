# Rules

Rules are the decision-making component of Amazon EventBridge. They evaluate incoming events or scheduled times and determine whether an action should be taken.

If a rule matches, EventBridge forwards the event to one or more targets.

------------------------------------------------------------------------

# What are Rules?

A Rule consists of:

- Event Pattern or Schedule
- One or more Targets

Rules determine where events should go.

------------------------------------------------------------------------

# Types of Rules

EventBridge supports two types of rules:

- Event Pattern Rules
- Schedule Rules

------------------------------------------------------------------------

# Event Pattern Rules

These rules evaluate incoming events.

Example:

```text
Source = aws.s3

↓

Invoke Lambda
```

------------------------------------------------------------------------

# Schedule Rules

Schedule Rules trigger actions at specific times.

Example:

```text
Every Day

↓

8:00 AM

↓

Run Lambda
```

**Note:** AWS now recommends **EventBridge Scheduler** for new scheduled workloads.

------------------------------------------------------------------------

# Rule Workflow

```text
Incoming Event

      |

      v

Rule

      |

Pattern Match

      |

      v

Target
```

------------------------------------------------------------------------

# Multiple Targets

A single rule can invoke multiple targets.

```text
Order Created

↓

Rule

↓

+-------+-------+--------+

|       |       |

v       v       v

Lambda SNS     SQS
```

This enables one event to trigger several workflows simultaneously.

------------------------------------------------------------------------

# Rule States

Rules can be:

- Enabled
- Disabled

Disabled rules ignore incoming events until re-enabled.

------------------------------------------------------------------------

# Rule Priority

If multiple rules match the same event:

- Every matching rule executes independently.
- There is no priority order.

One event can trigger multiple rules.

------------------------------------------------------------------------

# Retry Behavior

If a target invocation fails, EventBridge automatically retries delivery.

Options include:

- Retry Policy
- Dead-Letter Queue (DLQ)

These improve reliability.

------------------------------------------------------------------------

# Common Use Cases

Rules are commonly used for:

- EC2 state changes
- S3 uploads
- Scheduled jobs
- Notifications
- Workflow automation
- Security events

------------------------------------------------------------------------

# Real-World Example

A customer uploads an image to Amazon S3.

A Rule matches:

```text
Source = aws.s3

AND

Object Created
```

The event triggers:

- Image resizing Lambda
- Virus scanning Lambda
- Notification service

Each service runs independently.

------------------------------------------------------------------------

# Best Practices

- Create focused rules.
- Avoid overlapping patterns.
- Disable unused rules.
- Use descriptive rule names.
- Monitor rule failures using CloudWatch.

------------------------------------------------------------------------

# Key Takeaways

- Rules evaluate incoming events or schedules.
- Rules contain Event Patterns or Schedules.
- One rule can invoke multiple targets.
- Multiple rules can process the same event.
- Rules are the core routing mechanism of Amazon EventBridge.