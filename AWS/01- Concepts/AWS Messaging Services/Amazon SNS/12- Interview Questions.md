# Introduction

Amazon SNS is a frequently asked topic in AWS, Cloud, DevOps, and Backend Engineering interviews.

Interviewers typically evaluate your understanding of:

- Publish/Subscribe architecture
- SNS Topics
- Subscription protocols
- Fan-Out architecture
- Security
- Message filtering
- Monitoring
- Real-world architectures
- Integration with other AWS services

This chapter contains commonly asked Amazon SNS interview questions grouped by difficulty level.

---

# Beginner Level Questions

## 1. What is Amazon SNS?

**Answer**

Amazon Simple Notification Service (SNS) is a fully managed Publish/Subscribe (Pub/Sub) messaging service that enables applications to send messages to multiple subscribers simultaneously.

---

## 2. Why do we use Amazon SNS?

**Answer**

Amazon SNS is used to:

- Decouple applications
- Broadcast events
- Send notifications
- Build event-driven architectures
- Trigger multiple downstream services

---

## 3. What is a Topic in Amazon SNS?

**Answer**

A Topic is a communication channel to which publishers send messages.

Subscribers receive messages from the topic.

---

## 4. What is a Subscription?

**Answer**

A Subscription connects an endpoint to an SNS Topic.

Whenever a message is published, Amazon SNS delivers it to every active subscription.

---

## 5. What protocols does Amazon SNS support?

**Answer**

Amazon SNS supports:

- Amazon SQS
- AWS Lambda
- HTTP
- HTTPS
- Email
- Email-JSON
- SMS
- Mobile Push Notifications

---

## 6. What messaging model does Amazon SNS use?

**Answer**

Amazon SNS uses the **Publish/Subscribe (Pub/Sub)** messaging model.

---

## 7. What is Fan-Out Architecture?

**Answer**

Fan-Out Architecture allows one published message to be delivered to multiple independent subscribers.

```
Publisher

↓

SNS Topic

↓

SQS

↓

Lambda

↓

Email
```

---

## 8. Does Amazon SNS store messages?

**Answer**

No.

Amazon SNS immediately attempts to deliver messages to subscribers.

If durable storage is required, Amazon SQS should be used.

---

## 9. What is the difference between Amazon SNS and Amazon SQS?

| Amazon SNS | Amazon SQS |
|------------|------------|
| Publish/Subscribe | Message Queue |
| Push model | Pull model |
| Multiple subscribers | One consumer processes a message |
| Does not store messages | Stores messages until processed |

---

## 10. What AWS services commonly integrate with SNS?

**Answer**

Examples include:

- Amazon SQS
- AWS Lambda
- Amazon S3
- Amazon CloudWatch
- Amazon EventBridge
- AWS Auto Scaling
- Amazon EC2

---

# Intermediate Level Questions

## 11. What is Message Filtering?

**Answer**

Message Filtering allows Amazon SNS to deliver messages only to subscribers whose Filter Policy matches the published Message Attributes.

---

## 12. What are Message Attributes?

**Answer**

Message Attributes are metadata attached to a message.

They are commonly used for:

- Filtering
- Routing
- Categorization

---

## 13. What is a Filter Policy?

**Answer**

A Filter Policy defines which messages a subscriber wants to receive.

Example:

```json
{
    "EventType":[
        "Order"
    ]
}
```

---

## 14. What is the difference between Standard Topics and FIFO Topics?

| Standard Topic | FIFO Topic |
|----------------|------------|
| Best-effort ordering | Strict ordering |
| Duplicate messages possible | Duplicate prevention |
| Very high throughput | High throughput with ordering guarantees |
| Supports all protocols | Supports FIFO SQS queues |

---

## 15. Why would you use FIFO Topics?

**Answer**

FIFO Topics are used when applications require:

- Strict ordering
- Duplicate prevention
- Business consistency

Examples:

- Banking
- Payments
- Order processing

---

## 16. What is MessageGroupId?

**Answer**

MessageGroupId defines an ordered message stream within a FIFO Topic.

Messages in the same group are delivered in order.

---

## 17. What is Content-Based Deduplication?

**Answer**

Amazon SNS automatically generates a deduplication ID using the message body.

Duplicate messages are ignored within the deduplication window.

---

## 18. Can one Topic have multiple subscribers?

**Answer**

Yes.

One SNS Topic may have:

- Hundreds of subscribers
- Multiple subscription types
- Multiple AWS services

---

## 19. Why combine Amazon SNS with Amazon SQS?

**Answer**

Amazon SNS distributes messages.

Amazon SQS stores messages.

Together they provide:

- Reliable processing
- Independent scaling
- Retry capability
- Dead Letter Queue support

---

## 20. Which subscription protocol is best for backend processing?

**Answer**

Amazon SQS

It provides durable storage and reliable asynchronous processing.

---

# Advanced Level Questions

## 21. Explain the Publish/Subscribe model.

**Answer**

In the Publish/Subscribe model:

- Publishers send messages to a Topic.
- Publishers are unaware of subscribers.
- Amazon SNS distributes messages to all subscribers.

This creates loose coupling between services.

---

## 22. How does Amazon SNS ensure security?

**Answer**

Amazon SNS supports:

- IAM Policies
- Topic Policies
- AWS KMS Encryption
- HTTPS
- CloudTrail
- CloudWatch

---

## 23. What is the difference between IAM Policy and Topic Policy?

| IAM Policy | Topic Policy |
|------------|--------------|
| Identity-based | Resource-based |
| Controls what users can do | Controls who can access the topic |

---

## 24. Why is HTTPS preferred over HTTP?

**Answer**

HTTPS encrypts messages in transit using TLS, protecting them from interception and tampering.

---

## 25. What CloudWatch metrics should be monitored?

**Answer**

Important metrics include:

- NumberOfMessagesPublished
- NumberOfNotificationsDelivered
- NumberOfNotificationsFailed
- NumberOfNotificationsFilteredOut
- PublishSize

---

## 26. What happens if a subscriber is unavailable?

**Answer**

Behavior depends on the subscription protocol.

Examples:

- Amazon SQS stores messages.
- Lambda uses AWS retry behavior.
- HTTP/HTTPS endpoints follow SNS retry policies.
- Email and SMS use best-effort delivery.

---

## 27. Can Amazon SNS publish across AWS accounts?

**Answer**

Yes.

Cross-account publishing is supported using **Topic Policies**.

---

## 28. Can Amazon SNS invoke Lambda directly?

**Answer**

Yes.

Amazon SNS can invoke Lambda functions without requiring Amazon SQS.

---

## 29. What are the advantages of Message Filtering?

**Answer**

- Reduces unnecessary processing
- Lowers costs
- Improves scalability
- Simplifies subscriber logic

---

## 30. How would you secure a production SNS Topic?

**Answer**

- Enable Server-Side Encryption
- Use IAM Roles
- Configure Topic Policies
- Use HTTPS endpoints
- Enable CloudTrail
- Monitor with CloudWatch
- Apply least-privilege permissions

---

# Scenario-Based Questions

## 31. An event must be processed by five different microservices. Which AWS service would you choose?

**Expected Answer**

Amazon SNS

It broadcasts one event to multiple subscribers simultaneously.

---

## 32. You need reliable processing after broadcasting an event. Which architecture would you use?

**Expected Answer**

```
Application

↓

Amazon SNS

↓

Multiple Amazon SQS Queues

↓

Consumers
```

This combines event broadcasting with durable message storage.

---

## 33. Your subscribers are receiving unnecessary messages. How would you fix it?

**Expected Answer**

Use **Message Filtering** with **Filter Policies** and **Message Attributes**.

---

## 34. Your HTTP subscriber is missing notifications. What would you check?

**Expected Answer**

- Endpoint availability
- HTTP status codes
- CloudWatch metrics
- Topic configuration
- Retry behavior
- Network connectivity

---

## 35. Email subscriptions remain inactive. Why?

**Expected Answer**

The recipient has not confirmed the subscription.

Email subscriptions remain in the **Pending Confirmation** state until confirmed.

---

## 36. Why shouldn't SNS be used as a queue?

**Expected Answer**

Amazon SNS distributes messages immediately.

It does not provide durable message storage like Amazon SQS.

---

## 37. How would you monitor SNS in production?

**Expected Answer**

Use:

- Amazon CloudWatch
- CloudWatch Alarms
- CloudTrail
- AWS Config
- Application logs

---

## 38. How would you design a notification system for order processing?

**Expected Answer**

```
Order Service

↓

Amazon SNS

↓

Inventory Queue

↓

Billing Queue

↓

Shipping Queue

↓

Email Notifications
```

---

## 39. What is the benefit of Topic Policies?

**Expected Answer**

Topic Policies allow:

- Cross-account access
- AWS service integration
- Resource-level access control

---

## 40. Explain a real-world use case for Amazon SNS.

**Expected Answer**

An e-commerce platform publishes an **Order Created** event.

Amazon SNS distributes the event to:

- Inventory Service
- Billing Service
- Shipping Service
- Analytics
- Customer Notifications

Each service processes the event independently, improving scalability and reducing coupling.

---

# Interview Tips

- Clearly explain the **Publish/Subscribe** model.
- Understand the difference between **SNS**, **SQS**, and **Kinesis**.
- Know when to use **Standard Topics** versus **FIFO Topics**.
- Be comfortable discussing **Fan-Out Architecture**.
- Understand **Message Filtering** and **Filter Policies**.
- Explain how Amazon SNS integrates with **SQS**, **Lambda**, **CloudWatch**, and **EventBridge**.
- Discuss security using **IAM**, **Topic Policies**, and **AWS KMS**.
- Support your answers with real-world architecture examples.

---

# Summary

Amazon SNS interview questions focus on event-driven architecture, publish/subscribe messaging, service integrations, and secure application design. Strong candidates should understand how SNS distributes events, when to combine it with Amazon SQS, how Message Filtering works, and how to build scalable, loosely coupled systems using AWS messaging services.