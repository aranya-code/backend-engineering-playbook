# Amazon EventBridge

A deep-dive study guide into **Amazon EventBridge** — AWS's fully managed serverless event bus service for building event-driven architectures with routing, filtering, scheduling, replay, and SaaS integrations.

---

## 📚 Table of Contents

- [What is EventBridge?](#what-is-eventbridge)
- [Topics Covered](#topics-covered)
- [Module Structure](#module-structure)
- [Key Concepts at a Glance](#key-concepts-at-a-glance)
- [Architecture Overview](#architecture-overview)
- [Integrations](#integrations)
- [Navigation](#navigation)

---

## What is EventBridge?

Amazon EventBridge is a **fully managed serverless event bus service** that enables applications, AWS services, and SaaS applications to communicate using events.

It allows you to build **event-driven architectures** by routing events from producers to consumers — without requiring the components to know about each other. Instead of services communicating directly, EventBridge acts as a **central event router** that receives events, filters them using rules, and delivers them to one or more targets.

---

## Topics Covered

| # | Topic | Focus Area |
|---|-------|------------|
| 01 | [Introduction](./01-%20Introduction.md) | What EventBridge is, event-driven architecture basics |
| 02 | [Event-Driven Architecture](./02-%20Event-Driven%20Architecture.md) | Design patterns and principles |
| 03 | [Core Components](./03-%20Core%20Components.md) | Events, Buses, Rules, Patterns, Targets |
| 04 | [Events](./04-%20Events.md) | Event structure, format, and lifecycle |
| 05 | [Event Buses](./05-%20Event%20Buses.md) | Default, custom, and partner event buses |
| 06 | [Event Patterns](./06-%20Event%20Patterns.md) | Content-based event filtering |
| 07 | [Rules](./07-%20Rules.md) | Matching events and routing to targets |
| 08 | [Targets](./08-%20Targets.md) | Supported destinations for matched events |
| 09 | [Scheduler](./09-%20Scheduler.md) | One-time and recurring scheduled events |
| 10 | [Cron Expressions](./10-%20Cron%20Expressions.md) | Cron and rate expression syntax |
| 11 | [EventBridge Pipes](./11-%20EventBridge%20Pipes.md) | Point-to-point integrations with filtering and enrichment |
| 12 | [EventBridge Archives](./12-%20EventBridge%20Archives.md) | Storing events for later replay |
| 13 | [Event Replay](./13-%20Event%20Replay.md) | Replaying archived events for recovery or testing |
| 14 | [Schema Registry](./14-%20Schema%20Registry.md) | Automatic schema discovery and code generation |
| 15 | [Resource Policies](./15-%20Resource%20Policies.md) | Cross-account event bus access control |
| 16 | [EventBridge Integrations](./16-%20EventBridge%20Integrations.md) | Native AWS service integrations |
| 17 | [API Destinations](./17-%20API%20Destinations.md) | Sending events to external HTTP endpoints |
| 18 | [Partner Event Sources](./18-%20Partner%20Event%20Sources.md) | SaaS integrations (Datadog, Zendesk, etc.) |
| 19 | [Custom Events](./19-%20Custom%20Events.md) | Publishing application-specific events |
| 20 | [Dead-Letter Queues (DLQ)](./20-%20Dead-Letter%20Queues%20(DLQ).md) | Handling failed event deliveries |
| 21 | [Retry Policies](./21-%20Retry%20Policies.md) | Configuring retry behavior for targets |
| 22 | [EventBridge Security](./22-%20EventBridge%20Security.md) | IAM, encryption, and access control |
| 23 | [Monitoring EventBridge](./23-%20Monitoring%20EventBridge.md) | CloudWatch metrics and operational visibility |
| 24 | [EventBridge Best Practices](./24-%20EventBridge%20Best%20Practices.md) | Design and operational guidelines |
| 25 | [Cost Optimization](./25-%20Cost%20Optimization.md) | Strategies to reduce EventBridge costs |
| 26 | [Real-World Architectures](./26-%20Real-World%20Architectures.md) | Production architecture patterns |
| 27 | [Common Mistakes](./27-%20Common%20Mistakes.md) | Pitfalls to avoid |
| 28 | [EventBridge vs SNS vs SQS](./28-%20EventBridge%20vs%20SNS%20vs%20SQS.md) | Messaging service comparison guide |
| 29 | [Production Best Practices](./29-%20Production%20Best%20Practices.md) | Enterprise-grade configuration |
| 30 | [Interview Questions & Summary](./30-%20Interview%20Questions%20%26%20Summary.md) | Interview prep and key takeaways |

---

## Module Structure

This module is organized into progressive learning sections:

```
EventBridge/
│
├── Fundamentals (01–03)
│   └── Introduction, Event-Driven Architecture, Core Components
│
├── Core Concepts (04–10)
│   └── Events, Event Buses, Patterns, Rules,
│       Targets, Scheduler, Cron Expressions
│
├── Advanced Features (11–14)
│   └── Pipes, Archives, Event Replay, Schema Registry
│
├── Integrations & Events (15–19)
│   └── Resource Policies, AWS Integrations, API Destinations,
│       Partner Event Sources, Custom Events
│
├── Reliability & Security (20–23)
│   └── Dead-Letter Queues, Retry Policies, Security, Monitoring
│
└── Production & Interview Prep (24–30)
    └── Best Practices, Cost Optimization, Real-World Architectures,
        Common Mistakes, SNS/SQS Comparison, Interview Questions
```

---

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **Event** | A JSON object representing a state change or occurrence |
| **Event Bus** | A router that receives events and evaluates rules against them |
| **Rule** | Matches incoming events by pattern and routes them to targets |
| **Event Pattern** | A JSON-based filter that selects events by their content |
| **Target** | A destination that receives matched events (Lambda, SQS, SNS, etc.) |
| **Scheduler** | Create one-time or recurring scheduled invocations |
| **Pipes** | Point-to-point integrations with optional filtering and enrichment |
| **Archives** | Store events for later replay |
| **Event Replay** | Re-process archived events for recovery or testing |
| **Schema Registry** | Auto-discover event schemas and generate code bindings |
| **API Destinations** | Route events to external HTTP endpoints |
| **Dead-Letter Queue** | SQS queue that captures events that failed delivery |

---

## Architecture Overview

```
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ AWS Services │  │  SaaS Apps   │  │ Custom Apps  │
  │  (Producers) │  │  (Partners)  │  │  (PutEvents) │
  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
         │                 │                  │
         └────────────┬────┴──────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │  Event Bus    │
              │  (Default /   │
              │   Custom)     │
              └───────┬───────┘
                      │
              ┌───────┴───────┐
              │    Rules      │
              │(Event Pattern)│
              └───────┬───────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
    ┌─────────┐ ┌──────────┐ ┌──────────┐
    │ Lambda  │ │   SQS    │ │  Step    │
    │         │ │          │ │Functions │
    └─────────┘ └──────────┘ └──────────┘
```

---

## Integrations

**AWS Services:** Lambda · EC2 · ECS · EKS · SQS · SNS · Step Functions · S3 · CloudTrail · CodePipeline · DynamoDB · API Gateway

**SaaS Partners:** Datadog · Zendesk · Auth0 · PagerDuty · Shopify · Snowflake

**External:** Any HTTP endpoint via API Destinations

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Monitoring](../README.md) |
| ⬅️ Previous | [AWS X-Ray](../Amazon%20X-Ray/README.md) |

---

> **Part of the [AWS Monitoring](../README.md) section in the Backend Engineering Playbook.**
