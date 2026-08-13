# EventBridge Pipes

Amazon EventBridge Pipes is a fully managed integration service that connects event producers to event consumers without requiring custom integration code.

A Pipe can read events from a source, optionally filter them, enrich them with additional data, and deliver them to a target.

Pipes simplify event-driven architectures by reducing the amount of custom code needed to move data between AWS services.

------------------------------------------------------------------------

# What are EventBridge Pipes?

An EventBridge Pipe is a point-to-point integration between a source and a target.

A Pipe consists of four components:

- Source
- Filter (Optional)
- Enrichment (Optional)
- Target

```text
Source

   |

   v

Filter

   |

   v

Enrichment

   |

   v

Target
```

------------------------------------------------------------------------

# Why Use EventBridge Pipes?

Pipes help you:

- Reduce custom integration code
- Filter events before processing
- Enrich events automatically
- Connect AWS services easily
- Build serverless integrations
- Improve maintainability

------------------------------------------------------------------------

# Pipe Components

## Source

The source is where events originate.

Supported sources include:

- Amazon SQS
- Amazon Kinesis
- Amazon DynamoDB Streams
- Amazon MQ
- Amazon MSK

------------------------------------------------------------------------

## Filter

Filters remove unwanted events before processing.

Example:

```text
Process only Orders

Ignore Payments
```

Filtering reduces unnecessary processing.

------------------------------------------------------------------------

## Enrichment

Enrichment modifies or enhances an event before sending it to the target.

Enrichment can use:

- AWS Lambda
- API Gateway
- Step Functions

Example:

```text
Customer ID

↓

Lambda

↓

Customer Details
```

------------------------------------------------------------------------

## Target

The target receives the enriched event.

Supported targets include:

- Lambda
- Step Functions
- EventBridge
- SQS
- SNS
- ECS
- API Destinations

------------------------------------------------------------------------

# Pipe Workflow

```text
Amazon SQS

      |

      v

EventBridge Pipe

      |

+-----------+

|  Filter   |

+-----------+

      |

      v

Enrichment

      |

      v

Lambda
```

------------------------------------------------------------------------

# Filtering Events

Instead of processing every event:

```text
Order Created

↓

Process
```

```text
Payment Created

↓

Ignore
```

Only matching events continue through the Pipe.

------------------------------------------------------------------------

# Event Enrichment

Example:

Original Event

```json
{
  "customerId": 501
}
```

Lambda enriches it:

```json
{
  "customerId": 501,
  "customerName": "John Doe",
  "membership": "Gold"
}
```

The enriched event is sent to the target.

------------------------------------------------------------------------

# Common Use Cases

- SQS → Lambda
- DynamoDB Streams → Step Functions
- Kinesis → EventBridge
- Event filtering
- Data transformation
- ETL workflows

------------------------------------------------------------------------

# EventBridge Pipes vs Rules

| Rules | Pipes |
|--------|-------|
| Event routing | Point-to-point integration |
| Multiple targets | Single target |
| No enrichment | Supports enrichment |
| Event Bus required | Direct integration |

------------------------------------------------------------------------

# Real-World Example

An order processing system stores new orders in Amazon SQS.

EventBridge Pipes:

1. Reads messages from SQS.
2. Filters only premium orders.
3. Calls Lambda to enrich customer information.
4. Sends enriched orders to Step Functions for fulfillment.

No custom polling application is required.

------------------------------------------------------------------------

# Best Practices

- Filter events as early as possible.
- Keep enrichment lightweight.
- Use Lambda only when necessary.
- Monitor Pipes using CloudWatch.
- Configure retry policies.

------------------------------------------------------------------------

# Key Takeaways

- EventBridge Pipes simplify event integrations.
- Pipes support filtering and enrichment.
- They eliminate the need for custom integration code.
- Pipes are ideal for point-to-point AWS service integrations.