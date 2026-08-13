# Event Buses

An **Event Bus** is the central communication channel in Amazon EventBridge. It receives events from producers, evaluates them against configured rules, and routes matching events to one or more targets.

Think of an Event Bus as a message router that connects event producers with event consumers.

------------------------------------------------------------------------

# What is an Event Bus?

An Event Bus is a logical container that receives events.

Instead of producers sending events directly to consumers, they publish events to an Event Bus.

The Event Bus then determines where each event should be delivered.

```text
Producer

    |

    v

Event Bus

    |

+---+-----------+-----------+

|               |           |

v               v           v

Lambda         SQS      Step Functions
```

------------------------------------------------------------------------

# Why Use Event Buses?

Event Buses help you:

- Decouple applications
- Route events efficiently
- Support multiple consumers
- Filter unwanted events
- Simplify event management
- Enable cross-account communication

------------------------------------------------------------------------

# Types of Event Buses

Amazon EventBridge provides three types of Event Buses:

- Default Event Bus
- Custom Event Bus
- Partner Event Bus

Each serves a different purpose.

------------------------------------------------------------------------

# Default Event Bus

Every AWS account automatically includes a **Default Event Bus**.

AWS services publish their events here automatically.

Examples:

- EC2 State Changes
- S3 Object Events
- CloudTrail Events
- Lambda Events

Example:

```text
Amazon EC2

↓

Default Event Bus

↓

Rule

↓

Lambda
```

------------------------------------------------------------------------

# Custom Event Bus

A **Custom Event Bus** is created by users.

It is primarily used for application-specific events.

Example:

```text
Order Service

↓

Custom Event Bus

↓

Inventory Service

↓

Payment Service
```

Benefits:

- Better isolation
- Easier management
- Independent permissions
- Application-specific routing

------------------------------------------------------------------------

# Partner Event Bus

A **Partner Event Bus** receives events from integrated SaaS providers.

Examples:

- Datadog
- Zendesk
- Shopify
- PagerDuty
- Auth0

This enables seamless integration between AWS and external applications.

------------------------------------------------------------------------

# Event Bus Flow

```text
Event Producer

      |

      v

Event Bus

      |

Event Rule

      |

      v

Target
```

Every event enters an Event Bus before being evaluated by rules.

------------------------------------------------------------------------

# Cross-Account Event Buses

An Event Bus can receive events from another AWS account.

Benefits include:

- Centralized monitoring
- Multi-account architectures
- Organizational event routing

Cross-account communication requires resource-based policies.

------------------------------------------------------------------------

# Choosing the Right Event Bus

| Event Bus | Best Use Case |
|------------|---------------|
| Default | AWS Service Events |
| Custom | Application Events |
| Partner | SaaS Integrations |

------------------------------------------------------------------------

# Real-World Example

An e-commerce company has separate applications for:

- Orders
- Payments
- Shipping

Each application publishes events to its own Custom Event Bus.

A central analytics system subscribes to all buses and generates business reports without modifying the existing applications.

------------------------------------------------------------------------

# Best Practices

- Use the Default Event Bus for AWS service events.
- Create Custom Event Buses for large applications.
- Use meaningful Event Bus names.
- Restrict access using resource-based policies.
- Monitor Event Bus activity with CloudWatch.

------------------------------------------------------------------------

# Key Takeaways

- Every event enters an Event Bus before routing.
- EventBridge supports Default, Custom, and Partner Event Buses.
- Custom Event Buses improve isolation and scalability.
- Event Buses enable loose coupling between producers and consumers.