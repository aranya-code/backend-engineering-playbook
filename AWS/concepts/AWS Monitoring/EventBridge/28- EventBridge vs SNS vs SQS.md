# EventBridge vs SNS vs SQS

Amazon EventBridge, Amazon SNS, and Amazon SQS are all messaging services, but they solve different problems.

Choosing the correct service depends on your application's communication pattern and business requirements.

------------------------------------------------------------------------

# Overview

| Service | Primary Purpose |
|----------|-----------------|
| EventBridge | Event routing |
| SNS | Pub/Sub notifications |
| SQS | Message queuing |

------------------------------------------------------------------------

# Amazon EventBridge

EventBridge routes events based on rules.

Features:

- Event filtering
- Event buses
- Rules
- Multiple targets
- Scheduler
- Archives
- Replay

Best for:

- Event-driven architectures
- AWS integrations
- SaaS integrations

------------------------------------------------------------------------

# Amazon SNS

SNS publishes messages to multiple subscribers simultaneously.

```text
SNS Topic

↓

Email

SMS

Lambda

SQS
```

Best for:

- Notifications
- Fan-out messaging
- Mobile push notifications

------------------------------------------------------------------------

# Amazon SQS

SQS stores messages until they are processed.

```text
Producer

↓

Queue

↓

Consumer
```

Best for:

- Decoupling applications
- Asynchronous processing
- Reliable message delivery

------------------------------------------------------------------------

# Feature Comparison

| Feature | EventBridge | SNS | SQS |
|----------|-------------|-----|-----|
| Event Routing | ✅ | ❌ | ❌ |
| Message Queue | ❌ | ❌ | ✅ |
| Publish/Subscribe | Limited | ✅ | ❌ |
| Event Filtering | Advanced | Basic | ❌ |
| Scheduling | ✅ | ❌ | ❌ |
| Archives | ✅ | ❌ | ❌ |
| Replay | ✅ | ❌ | ❌ |
| Ordering | ❌ | ❌ | FIFO Queues Only |

------------------------------------------------------------------------

# When to Use EventBridge

Choose EventBridge when:

- Building event-driven architectures
- Routing AWS events
- Integrating SaaS applications
- Automating workflows

------------------------------------------------------------------------

# When to Use SNS

Choose SNS when:

- Sending notifications
- Broadcasting messages
- Fan-out messaging

------------------------------------------------------------------------

# When to Use SQS

Choose SQS when:

- Buffering workloads
- Decoupling services
- Reliable asynchronous processing

------------------------------------------------------------------------

# Real-World Example

An online retailer:

```text
Customer Places Order

↓

EventBridge

↓

Payment Service

↓

Inventory Service

↓

SNS

↓

Customer Notification

↓

SQS

↓

Background Processing
```

Each AWS messaging service solves a different part of the architecture.

------------------------------------------------------------------------

# Best Practices

- Use EventBridge for event routing.
- Use SNS for broadcasting.
- Use SQS for buffering.
- Combine services when appropriate.

------------------------------------------------------------------------

# Key Takeaways

- EventBridge routes events.
- SNS broadcasts messages.
- SQS queues messages.
- These services complement one another and are frequently used together in modern AWS architectures.