# Core Components of Amazon EventBridge

Amazon EventBridge is built around several core components that work together to route events from producers to consumers. Understanding these components is essential for designing scalable, event-driven architectures.

The major components include:

- Events
- Event Buses
- Rules
- Event Patterns
- Targets
- Scheduler
- Archives
- Replay
- Schema Registry
- API Destinations
- Pipes

Each component plays a specific role in the event lifecycle.

------------------------------------------------------------------------

# Event

An **Event** is a JSON object that represents something that has happened in your application or AWS environment.

Examples include:

- An EC2 instance is launched.
- A file is uploaded to Amazon S3.
- A Lambda function completes execution.
- A payment is processed.
- A customer places an order.

Example Event:

```json
{
  "source": "com.mycompany.orders",
  "detail-type": "Order Created",
  "detail": {
    "orderId": "1001",
    "customer": "John Doe",
    "amount": 250
  }
}
```

Events are immutable and describe actions that have already occurred.

------------------------------------------------------------------------

# Event Bus

The **Event Bus** is the central router in Amazon EventBridge.

It receives events from producers and routes them to matching targets based on configured rules.

EventBridge provides three types of Event Buses:

- Default Event Bus
- Custom Event Bus
- Partner Event Bus

We'll explore each type in detail in a later chapter.

------------------------------------------------------------------------

# Rules

Rules determine **which events should be processed**.

Each rule contains:

- An Event Pattern or Schedule
- One or more Targets

When an incoming event matches the rule, EventBridge forwards the event to the configured targets.

Example:

```text
If Source = AWS EC2

↓

Invoke Lambda Function
```

------------------------------------------------------------------------

# Event Patterns

An **Event Pattern** is a JSON filter used to determine whether an event matches a rule.

Example:

```json
{
  "source": ["aws.ec2"],
  "detail-type": ["EC2 Instance State-change Notification"]
}
```

Only matching events trigger the associated targets.

Event patterns help reduce unnecessary processing by filtering events before they reach consumers.

------------------------------------------------------------------------

# Targets

A **Target** is the destination that receives a matching event.

Common EventBridge targets include:

- AWS Lambda
- Amazon SQS
- Amazon SNS
- AWS Step Functions
- Amazon ECS
- Amazon Kinesis
- CloudWatch Logs
- Event Bus
- API Destinations

A single rule can send an event to multiple targets simultaneously.

------------------------------------------------------------------------

# Scheduler

Amazon EventBridge Scheduler enables you to execute tasks at scheduled times without managing cron servers.

It supports:

- One-time schedules
- Recurring schedules
- Cron expressions
- Rate expressions

Example:

```text
Every day at 8:00 AM

↓

Invoke Lambda Function
```

Scheduler is the recommended AWS service for scheduled workloads.

------------------------------------------------------------------------

# Archives

An **Archive** stores historical events that pass through an Event Bus.

Benefits include:

- Auditing
- Compliance
- Debugging
- Event Recovery

Archived events can be retained for future analysis or replay.

------------------------------------------------------------------------

# Replay

Replay allows previously archived events to be sent back to an Event Bus.

Common use cases:

- Testing
- Debugging
- Recovering from failures
- Reprocessing historical events

Instead of recreating events manually, EventBridge can replay archived events automatically.

------------------------------------------------------------------------

# Schema Registry

Schema Registry stores the structure (schema) of events.

Benefits include:

- Automatic schema discovery
- Code generation
- Version management
- Improved developer productivity

Applications can generate strongly typed code based on registered schemas.

------------------------------------------------------------------------

# API Destinations

API Destinations allow EventBridge to send events directly to external HTTP APIs.

Examples:

- Slack
- Jira
- GitHub
- ServiceNow
- Third-party REST APIs

Authentication methods include:

- API Key
- Basic Authentication
- OAuth

This enables seamless integration with external services.

------------------------------------------------------------------------

# EventBridge Pipes

EventBridge Pipes provide a simple way to move data between event producers and consumers.

A Pipe consists of:

- Source
- Optional Filter
- Optional Enrichment
- Target

Example:

```text
Amazon SQS

↓

Filter Messages

↓

AWS Lambda

↓

Amazon EventBridge
```

Pipes reduce the need for custom integration code.

------------------------------------------------------------------------

# How the Components Work Together

```text
Event Producer

      |

      v

Event Bus

      |

      v

Rule

      |

Event Pattern

      |

      v

Target

(Lambda / SQS / SNS)

      |

      v

Optional Archive

      |

      v

Replay (if needed)
```

Every event flows through these components before reaching its destination.

------------------------------------------------------------------------

# Real-World Example

A customer uploads a file to Amazon S3.

1. Amazon S3 generates an event.
2. The event is sent to the Default Event Bus.
3. An Event Pattern matches object creation events.
4. A Rule is triggered.
5. The event is delivered to an AWS Lambda function.
6. Lambda resizes the uploaded image.
7. The event is archived for future auditing.

This workflow is completely serverless and requires no direct communication between services.

------------------------------------------------------------------------

# Best Practices

- Use Custom Event Buses for application-specific events.
- Design simple and focused Event Patterns.
- Send events to multiple targets only when necessary.
- Archive important business events.
- Use Replay for testing and recovery.
- Version schemas using Schema Registry.
- Monitor EventBridge using Amazon CloudWatch.

------------------------------------------------------------------------

# Key Takeaways

- EventBridge consists of Events, Event Buses, Rules, Event Patterns, Targets, Scheduler, Archives, Replay, Schema Registry, API Destinations, and Pipes.
- Each component has a specific responsibility in the event routing process.
- Together, these components enable scalable, serverless, and loosely coupled event-driven architectures.
- Understanding these core components is the foundation for mastering Amazon EventBridge.