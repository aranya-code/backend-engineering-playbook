# Schema Registry

Amazon EventBridge Schema Registry is a feature that automatically discovers, stores, and manages the schemas of events flowing through EventBridge. It helps developers understand event structures and generate code bindings for strongly typed applications.

Instead of manually documenting event formats, Schema Registry automatically captures and versions them.

------------------------------------------------------------------------

# What is a Schema?

A schema defines the structure of an event.

It describes:

- Field names
- Data types
- Nested objects
- Required properties

Example:

```json
{
  "orderId": "string",
  "customerId": "string",
  "amount": "number",
  "status": "string"
}
```

------------------------------------------------------------------------

# What is Schema Registry?

Schema Registry is a centralized repository for event schemas.

It allows developers to:

- Discover event structures
- Store schemas
- Version schemas
- Generate application code
- Share schemas across teams

------------------------------------------------------------------------

# Why Use Schema Registry?

Schema Registry helps you:

- Eliminate manual documentation
- Improve developer productivity
- Detect schema changes
- Generate strongly typed code
- Reduce integration errors

------------------------------------------------------------------------

# How Schema Registry Works

```text
Application

      |

      v

EventBridge

      |

      v

Schema Discovery

      |

      v

Schema Registry

      |

      v

Developer
```

------------------------------------------------------------------------

# Registry Types

EventBridge supports two registry types.

## AWS Managed Registry

Stores schemas discovered automatically from AWS services.

Examples:

- Amazon EC2
- Amazon S3
- AWS Lambda

------------------------------------------------------------------------

## Custom Registry

Stores schemas for your own applications.

Example:

```text
Order Created

Payment Completed

Customer Registered
```

------------------------------------------------------------------------

# Schema Discovery

Schema Discovery automatically detects event structures.

Example:

```text
Application

↓

Publishes Event

↓

EventBridge

↓

Schema Automatically Created
```

No manual schema creation is required.

------------------------------------------------------------------------

# Schema Versioning

As applications evolve, event structures change.

Schema Registry automatically maintains versions.

Example:

Version 1

```json
{
  "orderId": "1001"
}
```

Version 2

```json
{
  "orderId": "1001",
  "discount": 20
}
```

Older applications continue using Version 1 while newer applications adopt Version 2.

------------------------------------------------------------------------

# Code Bindings

Schema Registry can generate code for multiple programming languages.

Examples:

- Java
- Python
- TypeScript

Benefits:

- Strong typing
- IDE auto-completion
- Fewer runtime errors

------------------------------------------------------------------------

# Common Use Cases

- Microservices
- Event-driven applications
- API integration
- Enterprise applications
- Large development teams

------------------------------------------------------------------------

# Real-World Example

An order service publishes an **Order Created** event.

Schema Registry automatically discovers the event.

Developers working on the Payment Service generate Python classes directly from the schema instead of manually writing data models.

This speeds up development and reduces integration issues.

------------------------------------------------------------------------

# Best Practices

- Enable Schema Discovery for development environments.
- Version schemas carefully.
- Avoid breaking schema changes.
- Use meaningful event names.
- Generate code bindings for strongly typed applications.

------------------------------------------------------------------------

# Key Takeaways

- Schema Registry stores and manages event schemas.
- Schema Discovery automatically captures event structures.
- Versioning supports application evolution.
- Code bindings improve developer productivity and reduce errors.