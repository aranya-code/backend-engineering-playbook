# Introduction

A message in Amazon SQS goes through several stages from the moment it is created until it is permanently removed from the queue.

Understanding this lifecycle is critical because it explains:

- Why duplicate messages occur
- Why Visibility Timeout exists
- Why messages sometimes reappear
- How retries work
- How Dead Letter Queues (DLQs) function

Most production issues involving Amazon SQS can be understood by knowing the message lifecycle.

---

# What is a Message Lifecycle?

A message lifecycle is the complete journey of a message inside an Amazon SQS queue.

The lifecycle begins when a producer sends a message and ends when the message is successfully deleted or expires.

```
Producer

↓

Queue

↓

Consumer

↓

Processing

↓

Delete
```

If processing fails, the message returns to the queue for another attempt.

---

# Complete Message Lifecycle

```
                 SendMessage()
                       │
                       ▼
              Message Stored
                       │
                       ▼
             ReceiveMessage()
                       │
                       ▼
          Visibility Timeout Starts
                       │
              Message Becomes Invisible
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
 Processing Successful        Processing Failed
         │                           │
         ▼                           ▼
 DeleteMessage()          Visibility Timeout Expires
         │                           │
         ▼                           ▼
 Message Removed           Message Visible Again
                                       │
                                       ▼
                                Another Consumer
```

---

# Step 1 - Send Message

The producer sends a message using the

```
SendMessage()
```

API.

Example

```
Order Service

↓

SendMessage()

↓

Amazon SQS
```

The message immediately becomes durable and available inside the queue.

---

## What Happens Internally?

Amazon SQS

- Accepts the request
- Stores the message
- Replicates the message across multiple Availability Zones
- Assigns a unique Message ID
- Returns a successful response

```
Producer

↓

Message

↓

Stored

↓

Replicated

↓

Success Response
```

---

# Step 2 - Message Stored in Queue

Once stored, the message waits until a consumer retrieves it.

```
Queue

↓

Waiting

↓

Waiting

↓

Waiting
```

The message remains available until one of the following occurs:

- It is deleted.
- It expires.
- It is moved to a Dead Letter Queue.

---

## Message Retention

Messages remain in the queue for the configured retention period.

| Property | Value |
|----------|-------|
| Default | 4 Days |
| Minimum | 1 Minute |
| Maximum | 14 Days |

Example

```
Day 1

↓

Day 2

↓

Day 3

↓

Processed

OR

Day 14

↓

Automatically Deleted
```

---

# Step 3 - Receive Message

A consumer requests messages using

```
ReceiveMessage()
```

```
Queue

↓

ReceiveMessage()

↓

Consumer
```

Receiving a message **does not delete it**.

Instead, Amazon SQS marks the message as temporarily invisible.

---

## Why Isn't It Deleted?

Imagine the application crashes immediately after receiving the message.

If the message were deleted instantly,

the work would be permanently lost.

Amazon SQS therefore waits until the application confirms successful processing.

---

# Step 4 - Visibility Timeout

Immediately after a message is received,

Amazon SQS starts the **Visibility Timeout**.

```
Receive

↓

Invisible

↓

Processing

↓

Delete
```

While invisible,

other consumers cannot retrieve the message.

---

## Example

Suppose Consumer A receives a message.

```
Queue

↓

Consumer A

✔ Receives Message

Consumer B

❌ Cannot Receive
```

Consumer B must wait until either:

- Consumer A deletes the message.
- The Visibility Timeout expires.

---

## Default Value

```
30 Seconds
```

Maximum

```
12 Hours
```

Visibility Timeout will be covered in detail in a dedicated chapter.

---

# Step 5 - Process Message

The application performs the required business logic.

Examples include:

- Processing an order
- Sending an email
- Resizing an image
- Charging a credit card
- Updating inventory
- Generating a PDF

```
Receive

↓

Business Logic

↓

Success
```

Processing time depends on the workload.

---

# Step 6 - Delete Message

Once processing completes successfully,

the consumer calls

```
DeleteMessage()
```

```
Consumer

↓

DeleteMessage()

↓

Message Permanently Removed
```

After deletion,

the message can never be retrieved again.

---

# What Happens When Processing Fails?

Failures are common in distributed systems.

Examples include:

- Application crash
- Server restart
- Database unavailable
- Network timeout
- Exception during processing

Example

```
Receive

↓

Processing

↓

Crash

↓

Message Not Deleted
```

Since the message wasn't deleted,

Amazon SQS keeps it.

---

# Retry Mechanism

When the Visibility Timeout expires,

Amazon SQS automatically makes the message visible again.

```
Receive

↓

Invisible

↓

Crash

↓

Timeout Ends

↓

Visible Again

↓

Retry
```

A different consumer may process the message next time.

---

## Why Retries Matter

Retries prevent message loss.

Without retries:

```
Receive

↓

Crash

↓

Lost Forever
```

With retries:

```
Receive

↓

Crash

↓

Retry

↓

Success
```

This is one reason Amazon SQS is highly reliable.

---

# Dead Letter Queue Integration

Sometimes retries never succeed.

Example:

```
Invalid JSON

↓

Retry

↓

Retry

↓

Retry

↓

Retry

↓

Failure
```

Instead of retrying forever,

Amazon SQS can move the message into a **Dead Letter Queue (DLQ)**.

```
Main Queue

↓

Retry

↓

Retry

↓

Retry

↓

Dead Letter Queue
```

This prevents problematic ("poison") messages from blocking normal processing.

A dedicated chapter covers DLQs in detail.

---

# Message States

A message can exist in several different states.

```
Created

↓

Stored

↓

Available

↓

Received

↓

Invisible

↓

Processing

↓

Deleted
```

If processing fails,

the flow changes to:

```
Available

↓

Received

↓

Invisible

↓

Failure

↓

Visible Again

↓

Retry
```

---

# Lifecycle APIs

The following APIs participate in the lifecycle.

| API | Purpose |
|------|---------|
| SendMessage() | Sends a message to the queue |
| ReceiveMessage() | Retrieves one or more messages |
| DeleteMessage() | Removes a processed message |
| ChangeMessageVisibility() | Changes the visibility timeout |
| SendMessageBatch() | Sends multiple messages |
| DeleteMessageBatch() | Deletes multiple messages |

---

# Real-World Example

Suppose an online shopping application receives an order.

```
Customer

↓

Order API

↓

SendMessage()

↓

Amazon SQS

↓

Payment Worker

↓

Inventory Worker

↓

Shipping Worker

↓

DeleteMessage()
```

If the Payment Worker crashes,

the order message isn't lost.

Instead:

```
Receive

↓

Crash

↓

Timeout

↓

Retry

↓

Another Worker

↓

Success

↓

Delete
```

This design ensures reliable order processing.

---

# Best Practices

- Delete messages immediately after successful processing.
- Set an appropriate Visibility Timeout based on expected processing time.
- Design consumers to be idempotent.
- Configure Dead Letter Queues for failed messages.
- Monitor retry counts using CloudWatch.
- Avoid extremely short Visibility Timeout values for long-running tasks.
- Use batch APIs to improve throughput and reduce costs.

---

# Common Mistakes

## Assuming ReceiveMessage() Deletes the Message

Receiving a message only makes it invisible.

Deletion is a separate operation.

---

## Forgetting DeleteMessage()

If the consumer never deletes the message,

it will be delivered again.

---

## Ignoring Retries

Applications should be prepared for the same message to be delivered multiple times, especially with Standard Queues.

---

## Not Configuring a Dead Letter Queue

Without a DLQ,

poison messages can remain in the queue and repeatedly fail, consuming resources and delaying valid messages.

---

# Key Takeaways

- Every message follows a well-defined lifecycle.
- Messages are **not deleted** when received.
- Visibility Timeout prevents multiple consumers from processing the same message simultaneously.
- Messages are removed only after `DeleteMessage()` is called.
- Failed processing results in automatic retries.
- Dead Letter Queues isolate messages that repeatedly fail.

---

# Summary

The Amazon SQS message lifecycle is the foundation of reliable asynchronous messaging. By separating message receipt from message deletion, SQS ensures that temporary failures do not result in lost data. Features such as Visibility Timeout, automatic retries, and Dead Letter Queues work together to provide durable, fault-tolerant message processing.
