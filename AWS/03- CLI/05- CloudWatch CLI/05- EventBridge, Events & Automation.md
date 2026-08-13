# EventBridge, Events & Automation

> Learn how Amazon EventBridge integrates with CloudWatch to build event-driven architectures, automate operational tasks, trigger serverless workflows, and respond to infrastructure events. This chapter covers EventBridge, Event Buses, Rules, Targets, Event Patterns, Scheduled Events, and automation using the AWS CLI.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Amazon EventBridge
- Understand event-driven architecture
- Create EventBridge Rules
- Work with Event Buses
- Configure Event Targets
- Schedule automated tasks
- Trigger AWS services automatically
- Build production event-driven workflows

---

# What is Amazon EventBridge?

Amazon EventBridge is AWS's serverless event bus.

It receives events from:

- AWS Services
- Custom Applications
- SaaS Applications
- Scheduled Rules

and routes them to one or more targets.

---

# Event-Driven Architecture

Traditional architecture:

```text
Application

↓

Direct API Call

↓

Another Service
```

Event-driven architecture:

```text
Application

↓

Event

↓

EventBridge

↓

Multiple Services
```

Services become loosely coupled and easier to scale.

---

# EventBridge Architecture

```text
AWS Services

Applications

SaaS

        │

        ▼

EventBridge

        │

 ┌──────┼────────┐

 ▼      ▼        ▼

Lambda  SQS     SNS
```

One event can trigger multiple downstream services.

---

# Common Event Sources

AWS services that publish events include:

- EC2
- Lambda
- ECS
- EKS
- CloudFormation
- CodePipeline
- CodeBuild
- Auto Scaling
- RDS
- S3

Applications can also publish custom events.

---

# Event Buses

An Event Bus receives events.

Types:

```text
Default Event Bus

Custom Event Bus

Partner Event Bus
```

---

# Default Event Bus

Automatically receives events from AWS services.

Example:

```text
EC2 State Change

↓

Default Event Bus
```

---

# Custom Event Bus

Applications publish custom events.

Example:

```text
Backend API

↓

Custom Event Bus

↓

Processing Services
```

Useful for microservices.

---

# List Event Buses

```bash
aws events list-event-buses
```

---

# Create a Custom Event Bus

```bash
aws events create-event-bus \
--name backend-events
```

---

# Delete an Event Bus

```bash
aws events delete-event-bus \
--name backend-events
```

---

# Event Rules

Rules determine which events should be processed.

```text
Incoming Event

↓

Rule

↓

Target
```

Rules filter events using patterns.

---

# List Rules

```bash
aws events list-rules
```

---

# Create a Rule

```bash
aws events put-rule \
--name EC2StateChange \
--event-pattern file://event-pattern.json
```

---

# Describe a Rule

```bash
aws events describe-rule \
--name EC2StateChange
```

---

# Delete a Rule

```bash
aws events delete-rule \
--name EC2StateChange
```

---

# Event Patterns

Rules evaluate JSON event patterns.

Example:

```json
{
  "source": [
    "aws.ec2"
  ],
  "detail-type": [
    "EC2 Instance State-change Notification"
  ]
}
```

Only matching events trigger the rule.

---

# Event Targets

Targets define what happens after a rule matches.

Supported targets include:

- Lambda
- SNS
- SQS
- Step Functions
- ECS
- API Gateway
- CloudWatch Logs
- Kinesis

---

# Add a Target

```bash
aws events put-targets \
--rule EC2StateChange \
--targets file://targets.json
```

---

# List Targets

```bash
aws events list-targets-by-rule \
--rule EC2StateChange
```

---

# Remove Targets

```bash
aws events remove-targets \
--rule EC2StateChange \
--ids 1
```

---

# Scheduled Events

EventBridge replaces traditional CloudWatch scheduled events.

Example:

```text
Every Day

↓

02:00 AM

↓

Backup Lambda
```

---

# Create a Scheduled Rule

```bash
aws events put-rule \
--name DailyBackup \
--schedule-expression "cron(0 2 * * ? *)"
```

---

# Rate Expressions

Example:

```text
rate(5 minutes)

rate(1 hour)

rate(1 day)
```

---

# Cron Expressions

Example:

```text
cron(0 8 * * ? *)

↓

Every day at 08:00 UTC
```

---

# Publish Custom Events

Applications can publish events.

```bash
aws events put-events \
--entries file://events.json
```

Example use cases:

- Order Created
- Payment Successful
- User Registered
- Invoice Generated

---

# Event Workflow

```text
Application

↓

Publish Event

↓

EventBridge

↓

Rule

↓

Lambda

↓

Database Updated
```

---

# Event Replay

Archived events can be replayed.

Useful for:

- Disaster Recovery
- Testing
- Bug Fixes
- Reprocessing Failed Events

---

# Common Errors

## ResourceNotFoundException

Verify:

- Rule
- Event Bus
- Target

---

## ValidationException

Possible causes:

- Invalid Event Pattern
- Invalid Target
- Invalid ARN

---

## AccessDeniedException

Verify IAM permissions for:

- EventBridge
- Lambda
- SNS
- SQS

---

# Production Best Practices

- Use Custom Event Buses for microservices.
- Keep Event Rules focused on one purpose.
- Avoid complex event patterns.
- Use Dead Letter Queues (DLQs) for failed targets.
- Monitor EventBridge metrics.
- Use idempotent event processing.
- Archive important events.
- Follow least-privilege IAM permissions.

---

# Real-World Workflow

Order processing.

```text
Customer Places Order

↓

OrderCreated Event

↓

EventBridge

├────────────┬─────────────┐

▼            ▼             ▼

Inventory   Billing      Notification

              │

              ▼

          Email Sent
```

One event triggers multiple independent services.

---

# Architecture Note

```text
AWS Services
Applications
       │
       ▼
EventBridge
       │
 ┌─────┼──────────┐
 ▼     ▼          ▼
SNS   Lambda    SQS
       │
       ▼
Automation
```

EventBridge enables scalable, loosely coupled, event-driven architectures without requiring services to communicate directly.

---

# Interview Note

### Question

**What is the difference between CloudWatch Alarms and EventBridge?**

### Answer

CloudWatch Alarms monitor metrics and trigger actions when predefined thresholds are crossed, making them ideal for operational monitoring and alerting. EventBridge routes events based on event patterns rather than metric thresholds, enabling event-driven architectures and automation. In practice, CloudWatch answers **"Is something wrong?"**, while EventBridge answers **"What should happen when an event occurs?"**

---

# Key Takeaways

- EventBridge is AWS's event routing service.
- Event Buses receive events from AWS services and applications.
- Rules filter events using JSON event patterns.
- Targets define the action taken when a rule matches.
- Scheduled Rules replace traditional CloudWatch scheduled events.
- Custom Events enable event-driven microservice architectures.
- EventBridge is a core service for serverless automation and operational workflows.