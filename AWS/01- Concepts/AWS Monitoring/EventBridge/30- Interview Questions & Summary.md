# Interview Questions & Summary

Amazon EventBridge is one of the most frequently discussed AWS services in interviews for Cloud Engineers, DevOps Engineers, Backend Developers, Solutions Architects, and Site Reliability Engineers (SREs).

This chapter summarizes the most important concepts and includes commonly asked interview questions.

------------------------------------------------------------------------

# Quick Revision

Remember these core EventBridge concepts:

- Event
- Event Bus
- Rules
- Event Patterns
- Targets
- Scheduler
- Cron Expressions
- Pipes
- Archives
- Replay
- Schema Registry
- Resource Policies
- API Destinations
- Partner Event Sources
- Custom Events
- Dead-Letter Queues
- Retry Policies
- Monitoring
- Security
- Cost Optimization

------------------------------------------------------------------------

# Beginner Interview Questions

## 1. What is Amazon EventBridge?

**Answer**

Amazon EventBridge is a fully managed serverless event bus that routes events between AWS services, applications, and SaaS providers.

---

## 2. What is an Event?

**Answer**

An event is a JSON document describing something that has happened in a system.

---

## 3. What is an Event Bus?

**Answer**

An Event Bus receives events and routes them to matching targets using rules.

---

## 4. What are the three Event Bus types?

**Answer**

- Default Event Bus
- Custom Event Bus
- Partner Event Bus

---

## 5. What is an Event Pattern?

**Answer**

An Event Pattern is a JSON filter used to determine whether an event matches a rule.

---

## 6. What is a Rule?

**Answer**

A Rule evaluates events or schedules and forwards matching events to one or more targets.

---

## 7. What are Targets?

**Answer**

Targets are AWS services or external APIs that receive events.

Examples:

- Lambda
- SQS
- SNS
- Step Functions
- ECS

------------------------------------------------------------------------

# Intermediate Interview Questions

## 8. What is EventBridge Scheduler?

**Answer**

A serverless scheduling service supporting one-time and recurring tasks using cron or rate expressions.

---

## 9. What are API Destinations?

**Answer**

API Destinations allow EventBridge to invoke external HTTP APIs securely.

---

## 10. What is Schema Registry?

**Answer**

Schema Registry stores event schemas and supports automatic discovery and versioning.

---

## 11. What is Event Replay?

**Answer**

Replay republishes archived events for testing, recovery, or debugging.

---

## 12. What are EventBridge Pipes?

**Answer**

Pipes connect event sources to targets with optional filtering and enrichment.

---

## 13. What is a Partner Event Source?

**Answer**

A Partner Event Source allows SaaS providers to publish events directly into EventBridge.

------------------------------------------------------------------------

# Advanced Interview Questions

## 14. What is the difference between EventBridge and SNS?

| EventBridge | SNS |
|--------------|-----|
| Event routing | Pub/Sub messaging |
| Event filtering | Broadcast messaging |
| Scheduler | No Scheduler |
| Archives | No Archives |

---

## 15. What is the difference between EventBridge and SQS?

| EventBridge | SQS |
|--------------|-----|
| Event routing | Message queue |
| No message persistence | Stores messages |
| Multiple targets | Single consumer pattern |

---

## 16. Why should EventBridge events be immutable?

**Answer**

Events represent facts that have already occurred. Modifying them can break consumers and compromise system consistency.

---

## 17. How does EventBridge improve scalability?

**Answer**

By decoupling producers and consumers, allowing services to scale independently.

---

## 18. What happens if target delivery fails?

**Answer**

EventBridge retries delivery according to the Retry Policy. If retries fail, the event can be sent to a Dead-Letter Queue.

------------------------------------------------------------------------

# Scenario-Based Interview Questions

## Scenario 1

A Lambda function processing EventBridge events is temporarily unavailable.

**Answer**

- Retry Policy handles temporary failures.
- Failed events go to a DLQ if retries are exhausted.
- Replay events after fixing the issue if necessary.

---

## Scenario 2

A new Analytics Service needs order events.

**Answer**

Simply create a new EventBridge Rule that routes **Order Created** events to the Analytics Service. Existing producers remain unchanged.

---

## Scenario 3

How would you integrate AWS with Slack?

**Answer**

Use:

- EventBridge Rule
- API Destination
- Slack Webhook

---

## Scenario 4

How would you recover missed business events?

**Answer**

- Archive events.
- Replay the required time range.
- Ensure consumers are idempotent.

------------------------------------------------------------------------

# Best Practices for Interviews

Remember these key points:

- EventBridge is **event routing**, not a message queue.
- Use **Event Patterns** to filter events.
- Use **Custom Event Buses** for application events.
- Configure **Retries** and **DLQs**.
- Use **Archives** and **Replay** for recovery.
- Use **Schema Registry** for schema management.
- Monitor EventBridge using **CloudWatch**.
- Secure Event Buses using **IAM** and **Resource Policies**.

------------------------------------------------------------------------

# Final Summary

Amazon EventBridge enables modern event-driven architectures by routing events between AWS services, applications, and SaaS platforms.

It provides:

- Serverless event routing
- Event filtering
- Scheduling
- Event replay
- Schema management
- Cross-account communication
- External API integration
- Monitoring and security features

By mastering EventBridge, you can build scalable, loosely coupled, and resilient cloud-native applications.

------------------------------------------------------------------------
