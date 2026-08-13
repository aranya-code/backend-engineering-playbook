# Custom Events

Custom Events are application-defined events published directly to Amazon EventBridge using the **PutEvents API**.

They allow your own applications, microservices, and backend systems to communicate through EventBridge using an event-driven architecture.

------------------------------------------------------------------------

# What are Custom Events?

Unlike AWS service events, Custom Events are created by developers.

Examples:

- Order Created
- Payment Completed
- User Registered
- Invoice Generated
- Shipment Dispatched

------------------------------------------------------------------------

# Why Use Custom Events?

Custom Events help you:

- Decouple microservices
- Share business events
- Build scalable applications
- Reduce direct service dependencies
- Enable asynchronous processing

------------------------------------------------------------------------

# How Custom Events Work

```text
Application

      |

PutEvents API

      |

      v

Custom Event Bus

      |

      v

Rules

      |

      v

Targets
```

------------------------------------------------------------------------

# Publishing Custom Events

Applications publish events using the **PutEvents** API.

Example event:

```json
{
  "Source": "com.company.orders",
  "DetailType": "Order Created",
  "Detail": "{\"orderId\":\"1001\",\"amount\":250}"
}
```

EventBridge routes the event according to matching rules.

------------------------------------------------------------------------

# Event Structure

Every custom event typically contains:

- Source
- DetailType
- Detail
- EventBusName
- Time (optional)
- Resources (optional)

------------------------------------------------------------------------

# Naming Conventions

Good examples:

```text
com.company.orders

com.company.payments

com.company.inventory
```

Avoid generic names such as:

```text
app

test

service
```

------------------------------------------------------------------------

# Event Flow

```text
Order Service

      |

PutEvents

      |

Custom Event Bus

      |

Rule

      |

Lambda

↓

Inventory Service

↓

Email Service
```

------------------------------------------------------------------------

# Common Use Cases

- Order processing
- Payment workflows
- Inventory updates
- Customer notifications
- Audit logging
- Analytics

------------------------------------------------------------------------

# Real-World Example

A customer places an order.

The Order Service publishes:

```text
Order Created
```

EventBridge delivers the event to:

- Payment Service
- Inventory Service
- Shipping Service
- Email Service
- Analytics Service

Each service processes the event independently.

------------------------------------------------------------------------

# Best Practices

- Use meaningful event names.
- Keep event payloads small.
- Avoid sensitive information.
- Version event schemas.
- Publish immutable business events.
- Monitor failures using CloudWatch.

------------------------------------------------------------------------

# Common Mistakes

- Large event payloads
- Poor naming conventions
- Breaking schema compatibility
- Publishing duplicate events
- Tight coupling between services

------------------------------------------------------------------------

# Key Takeaways

- Custom Events enable communication between your own applications.
- Events are published using the **PutEvents API**.
- Custom Event Buses help organize application events.
- Custom Events are the foundation of event-driven microservices on AWS.