# Introduction

In many event-driven architectures, not every subscriber is interested in every published message.

For example:

- The Billing Service only needs **payment events**.
- The Inventory Service only needs **inventory events**.
- The Shipping Service only needs **shipping events**.

Without filtering, every subscriber receives every message, resulting in unnecessary processing, increased costs, and more complex application logic.

Amazon SNS solves this problem using **Message Filtering**.

Message Filtering allows Amazon SNS to deliver messages **only to subscribers whose filter policies match the message attributes**.

---

# What is Message Filtering?

Message Filtering enables selective message delivery based on **Message Attributes**.

Instead of broadcasting every message to every subscriber, Amazon SNS evaluates the subscriber's **Filter Policy** before delivering the message.

```
Publisher

↓

SNS Topic

↓

Evaluate Filter Policy

↓

Matching Subscriber

↓

Deliver Message
```

Subscribers whose filter policies do not match simply do not receive the message.

---

# Why Use Message Filtering?

Without filtering:

```
Order Created

↓

SNS Topic

↓

Inventory

↓

Billing

↓

Shipping

↓

Analytics

↓

Notification
```

Every service receives the message.

Even services that don't need it.

---

With filtering:

```
Order Created

↓

SNS Topic

↓

Inventory ✅

↓

Billing ❌

↓

Shipping ❌

↓

Analytics ❌
```

Only the Inventory Service receives the message.

---

# How Message Filtering Works

Amazon SNS follows this workflow.

```
Publisher

↓

Publish Message

↓

SNS Topic

↓

Read Message Attributes

↓

Evaluate Filter Policy

↓

Match?

↓

Yes → Deliver

No → Ignore
```

Filtering occurs before message delivery.

---

# Message Attributes

Filtering works using **Message Attributes**.

Example

```python
sns.publish(
    TopicArn=TOPIC_ARN,
    Message="Order Created",
    MessageAttributes={
        "EventType": {
            "DataType": "String",
            "StringValue": "Order"
        }
    }
)
```

Amazon SNS compares these attributes against subscriber filter policies.

---

# Filter Policy

A Filter Policy defines which messages a subscriber wants to receive.

Example

```json
{
    "EventType": [
        "Order"
    ]
}
```

Only messages where:

```
EventType = Order
```

will be delivered.

---

# Architecture Example

```
                    SNS Topic

                        │

        ┌───────────────┼────────────────┐

        ▼               ▼                ▼

 Inventory Queue   Billing Queue   Shipping Queue

 EventType=Order  EventType=Pay   EventType=Ship
```

Published message

```
EventType = Order
```

Result

```
Inventory Queue

↓

Delivered

--------------------

Billing Queue

↓

Ignored

--------------------

Shipping Queue

↓

Ignored
```

---

# Configuring a Filter Policy

## AWS Management Console

1. Open Amazon SNS.
2. Select the Topic.
3. Open **Subscriptions**.
4. Select a subscription.
5. Choose **Edit**.
6. Configure the **Filter Policy**.
7. Save changes.

---

## AWS CLI

```bash
aws sns set-subscription-attributes \
    --subscription-arn SUBSCRIPTION_ARN \
    --attribute-name FilterPolicy \
    --attribute-value '{"EventType":["Order"]}'
```

---

## Boto3

```python
import json

sns.set_subscription_attributes(
    SubscriptionArn=SUBSCRIPTION_ARN,
    AttributeName="FilterPolicy",
    AttributeValue=json.dumps({
        "EventType": ["Order"]
    })
)
```

---

# Exact Match Filtering

The simplest filter matches an exact value.

Filter

```json
{
    "Department": [
        "Finance"
    ]
}
```

Message

```text
Department = Finance
```

Result

```
Delivered
```

---

# Multiple Values

Subscribers can receive multiple event types.

Filter

```json
{
    "EventType": [
        "Order",
        "Payment",
        "Refund"
    ]
}
```

Any matching event will be delivered.

---

# Numeric Filtering

Numeric values can also be filtered.

Filter

```json
{
    "Amount": [
        {
            "numeric": [
                ">",
                1000
            ]
        }
    ]
}
```

Messages with:

```
Amount > 1000
```

will be delivered.

---

# Prefix Matching

SNS supports string prefix filtering.

Filter

```json
{
    "Region": [
        {
            "prefix": "us-"
        }
    ]
}
```

Examples

```
us-east-1

↓

Delivered

----------------

us-west-2

↓

Delivered

----------------

eu-west-1

↓

Ignored
```

---

# Anything-But Matching

Subscribers can exclude specific values.

Filter

```json
{
    "Environment": [
        {
            "anything-but": "Development"
        }
    ]
}
```

Messages from every environment except Development are delivered.

---

# Exists Filtering

SNS can determine whether an attribute exists.

Filter

```json
{
    "Priority": [
        {
            "exists": true
        }
    ]
}
```

Only messages containing the **Priority** attribute are delivered.

---

# Multiple Attributes

Filter policies may contain multiple conditions.

Example

```json
{
    "Department": [
        "Finance"
    ],
    "Priority": [
        "High"
    ]
}
```

Both conditions must match.

---

# Real-World Example

Suppose an e-commerce platform publishes different business events.

```
Publisher

↓

SNS Topic

↓

Inventory Queue

EventType = Inventory

↓

Billing Queue

EventType = Payment

↓

Shipping Queue

EventType = Shipping
```

Published message

```
EventType = Payment
```

Result

```
Billing Queue

↓

Delivered

----------------

Inventory Queue

↓

Ignored

----------------

Shipping Queue

↓

Ignored
```

---

# Monitoring Filtered Messages

Amazon CloudWatch provides metrics such as:

- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed
- NumberOfNotificationsFilteredOut

The **NumberOfNotificationsFilteredOut** metric indicates how many messages were intentionally filtered.

---

# Advantages

- Reduces unnecessary processing
- Lowers infrastructure costs
- Improves application performance
- Simplifies subscriber logic
- Supports scalable event-driven architectures

---

# Limitations

- Filtering only works with **Message Attributes**.
- Filtering is evaluated before delivery.
- Messages without matching attributes are ignored.
- Filter policies apply per subscription.

---

# Best Practices

- Use Message Attributes instead of embedding metadata inside the message body.
- Keep filter policies simple and easy to maintain.
- Create separate topics for unrelated business domains.
- Monitor filtered message metrics using CloudWatch.
- Use meaningful attribute names such as:

  - EventType
  - Department
  - Priority
  - Region
  - Environment

---

# Common Mistakes

## Publishing Without Message Attributes

Filter Policies rely on Message Attributes.

Without them, filtering cannot occur.

---

## Putting Metadata Inside the Message Body

Amazon SNS cannot filter using message body fields (unless explicitly using newer payload-based filtering features).

Use Message Attributes for predictable filtering.

---

## Creating Overly Complex Filter Policies

Simple policies are easier to understand and maintain.

---

## Using One Topic for Every Business Event

Separate major business domains into different topics whenever possible.

---

# Summary

Message Filtering allows Amazon SNS to intelligently route messages to only the subscribers that need them. By evaluating subscription filter policies against message attributes, Amazon SNS reduces unnecessary message delivery, improves application performance, lowers processing costs, and enables highly scalable event-driven architectures. It is one of the most powerful features for building efficient publish/subscribe systems.