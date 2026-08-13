# What is Amazon EventBridge?

Amazon EventBridge is a **fully managed serverless event bus service** provided by AWS that enables applications, AWS services, and SaaS applications to communicate using events.

It allows you to build **event-driven architectures** by routing events from producers to consumers without requiring the components to know about each other.

Instead of applications communicating directly, EventBridge acts as a central event router that receives events, filters them using rules, and delivers them to one or more targets.

------------------------------------------------------------------------

# Why Do We Need Amazon EventBridge?

In modern applications, services often need to communicate with one another.

For example:

- An order is placed.
- A payment is processed.
- An email is sent.
- Inventory is updated.
- A notification is delivered.

Without EventBridge, every service would need to directly call every other service, creating tight coupling and making the system difficult to maintain.

EventBridge solves this problem by enabling **loosely coupled, event-driven communication**.

------------------------------------------------------------------------

# What is Event-Driven Architecture?

Event-driven architecture is a software design pattern where services communicate by producing and consuming events.

Instead of directly invoking another service, a producer publishes an event to EventBridge.

Interested services receive the event automatically and perform their own processing.

```text
Producer

    |

    v

Amazon EventBridge

    |

+---+-----------+------------+

|               |            |

v               v            v

Lambda        SQS         Step Functions
```

This architecture improves scalability, flexibility, and maintainability.

------------------------------------------------------------------------

# Core Components

Amazon EventBridge consists of several core components:

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

These components work together to deliver events to the appropriate destinations.

------------------------------------------------------------------------

# What Can EventBridge Connect?

EventBridge integrates with hundreds of AWS services and external SaaS applications.

Common AWS integrations include:

- AWS Lambda
- Amazon EC2
- Amazon ECS
- Amazon EKS
- Amazon SQS
- Amazon SNS
- AWS Step Functions
- Amazon S3
- AWS CloudTrail
- AWS CodePipeline
- Amazon DynamoDB
- Amazon API Gateway

It also supports partner integrations such as:

- Datadog
- Zendesk
- Auth0
- PagerDuty
- Shopify
- Snowflake

------------------------------------------------------------------------

# Event Flow

A typical EventBridge workflow looks like this:

```text
Event Producer

      |

      v

Amazon EventBridge

      |

Event Pattern Rule

      |

      v

Target

(Lambda / SQS / SNS / Step Functions)
```

The producer sends an event.

EventBridge evaluates the event against its configured rules.

If a rule matches, EventBridge forwards the event to one or more targets.

------------------------------------------------------------------------

# Benefits of Amazon EventBridge

- Fully managed service
- Serverless architecture
- Event-driven communication
- Loose coupling between services
- Automatic scaling
- Native AWS integration
- SaaS application integration
- Multiple targets per event
- Built-in scheduling
- Event filtering
- Event replay
- Schema discovery
- High availability

------------------------------------------------------------------------

# Common Use Cases

Amazon EventBridge is commonly used for:

- Serverless applications
- Microservices communication
- Workflow automation
- Scheduled jobs
- Application integration
- Security automation
- Infrastructure automation
- CI/CD pipelines
- Notifications
- Audit processing

------------------------------------------------------------------------

# Real-World Example

An e-commerce application receives a new customer order.

Instead of the Order Service directly calling multiple downstream services, it publishes an event to Amazon EventBridge.

```text
Customer Places Order

        |

        v

Amazon EventBridge

        |

+-------+--------+---------+

|        |        |         |

v        v        v         v

Payment  Inventory  Email  Analytics

Service   Service   Service Service
```

Each service independently processes the event.

This allows new services to be added later without modifying the Order Service.

------------------------------------------------------------------------

# Key Features

- Event Buses
- Event Rules
- Event Patterns
- Event Targets
- Scheduler
- Event Replay
- Event Archives
- Schema Registry
- Resource Policies
- Cross-Account Event Routing
- API Destinations
- EventBridge Pipes

------------------------------------------------------------------------

# Advantages

- Fully managed
- Serverless
- Highly scalable
- Highly available
- Decouples applications
- Easy integration with AWS services
- Supports SaaS integrations
- Secure event routing
- Built-in scheduling
- Minimal operational overhead

------------------------------------------------------------------------

# Key Takeaways

- Amazon EventBridge is AWS's fully managed event bus service.
- It enables event-driven architectures using producers and consumers.
- Events are routed using Event Buses, Rules, and Event Patterns.
- EventBridge integrates with AWS services, SaaS providers, and custom applications.
- It supports scheduling, event replay, schema discovery, API destinations, and cross-account event routing.
- EventBridge helps build scalable, loosely coupled, and highly available cloud applications.