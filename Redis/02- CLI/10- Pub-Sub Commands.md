# Pub/Sub Commands

## Overview

Redis Pub/Sub (Publish/Subscribe) is a lightweight messaging system that enables applications to exchange messages in real time without directly communicating with each other.

Instead of sending messages to a specific client, publishers send messages to a **channel**, and every subscriber listening to that channel immediately receives the message.

Unlike Redis Streams, Pub/Sub **does not persist messages**.

If a subscriber is offline when a message is published, the message is permanently lost.

Because of this, Pub/Sub is best suited for **real-time notifications**, while Redis Streams are better suited for **reliable messaging**.

Typical production use cases include:

- Live chat
- Real-time notifications
- WebSocket broadcasting
- Cache invalidation
- Multiplayer games
- Live dashboards
- Event broadcasting
- Monitoring alerts
- Distributed signaling
- Service coordination

---

# Pub/Sub Architecture

```
                 Publisher

                     │

                     ▼

              Redis Channel

          ┌────────┼────────┐

          ▼        ▼        ▼

     Subscriber  Subscriber  Subscriber

         A           B           C
```

Every active subscriber receives every published message.

---

# Understanding Pub/Sub

Unlike queues, Pub/Sub broadcasts messages.

```
Publisher

↓

Channel

↓

Subscriber A

Subscriber B

Subscriber C
```

All subscribers receive identical messages.

---

# Common Pub/Sub Commands

| Command | Description |
|----------|-------------|
| PUBLISH | Publish a message |
| SUBSCRIBE | Subscribe to channels |
| PSUBSCRIBE | Subscribe using patterns |
| UNSUBSCRIBE | Leave channels |
| PUNSUBSCRIBE | Leave pattern subscriptions |
| PUBSUB CHANNELS | List active channels |
| PUBSUB NUMSUB | Subscriber count |
| PUBSUB NUMPAT | Pattern subscriptions |

---

# PUBLISH

Sends a message to a channel.

Syntax

```redis
PUBLISH channel message
```

Example

```redis
PUBLISH notifications "Order Created"
```

Output

```
(integer) 5
```

The number represents subscribers that received the message.

Complexity

```
O(N)
```

Where N is the number of subscribers.

---

# SUBSCRIBE

Subscribes to one or more channels.

Example

```redis
SUBSCRIBE notifications
```

Output

```
Reading messages...
```

The client now waits for incoming messages.

---

# Publishing Example

Terminal 1

```redis
SUBSCRIBE chat
```

Terminal 2

```redis
PUBLISH chat "Hello Everyone!"
```

Terminal 1 immediately receives

```
Channel

chat

↓

Message

Hello Everyone!
```

---

# Multiple Subscribers

```
Publisher

↓

sports

↓

Client A

Client B

Client C
```

One publish operation delivers the message to every subscriber.

---

# Multiple Channels

Applications can subscribe to multiple channels.

```redis
SUBSCRIBE

orders

payments

notifications
```

Messages arrive independently.

---

# PSUBSCRIBE

Subscribes using wildcard patterns.

Example

```redis
PSUBSCRIBE orders:*
```

Matches

```
orders:new

orders:update

orders:cancelled
```

Very useful in microservice architectures.

---

# Pattern Matching Example

```
orders:*

↓

orders:new

orders:cancelled

orders:updated

orders:shipped
```

A single subscription receives every matching channel.

---

# UNSUBSCRIBE

Leaves subscribed channels.

Example

```redis
UNSUBSCRIBE notifications
```

The client stops receiving messages.

---

# PUNSUBSCRIBE

Stops pattern subscriptions.

Example

```redis
PUNSUBSCRIBE orders:*
```

---

# PUBSUB CHANNELS

Lists active channels.

Example

```redis
PUBSUB CHANNELS
```

Output

```
chat

orders

payments

notifications
```

Useful for monitoring.

---

# PUBSUB NUMSUB

Shows subscriber counts.

Example

```redis
PUBSUB NUMSUB

notifications

chat
```

Output

```
notifications

5

chat

20
```

---

# PUBSUB NUMPAT

Returns the number of active pattern subscriptions.

Example

```redis
PUBSUB NUMPAT
```

Output

```
(integer) 8
```

---

# Live Chat Example

```
User A

↓

PUBLISH

↓

chat-room

↓

User B

↓

User C

↓

User D
```

All connected users receive the message instantly.

---

# Notification System

```
Application

↓

PUBLISH

↓

notifications

↓

Mobile App

↓

Web Browser

↓

Desktop Client
```

---

# Cache Invalidation

```
Database Updated

↓

PUBLISH

↓

cache:invalidate

↓

Backend Servers

↓

Clear Local Cache
```

A common pattern in distributed systems.

---

# Real-Time Dashboard

```
Backend Service

↓

metrics

↓

Redis Pub/Sub

↓

Dashboard

↓

Instant Update
```

---

# Multiplayer Gaming

```
Player Action

↓

Game Channel

↓

Redis

↓

Other Players
```

Game events propagate with very low latency.

---

# Microservice Communication

```
Order Service

↓

orders

↓

Redis

↓

Inventory Service

↓

Shipping Service

↓

Notification Service
```

Each service receives the same event.

---

# Monitoring Alerts

```
Monitoring

↓

CPU Alert

↓

Redis Channel

↓

Operations Dashboard

↓

Slack Bot

↓

Email Service
```

One event reaches multiple systems.

---

# Message Lifecycle

```
Publisher

↓

Redis Channel

↓

Subscribers

↓

Delivered

↓

Gone Forever
```

Messages are **not stored**.

---

# What Happens if Nobody is Listening?

```
Publisher

↓

Redis

↓

No Subscribers

↓

Message Lost
```

Redis does not queue messages.

---

# Pub/Sub vs Streams

| Feature | Pub/Sub | Streams |
|---------|----------|----------|
| Persistent | ❌ | ✅ |
| Replay Messages | ❌ | ✅ |
| Consumer Groups | ❌ | ✅ |
| Acknowledgements | ❌ | ✅ |
| Broadcast | ✅ | Limited |
| Historical Messages | ❌ | ✅ |

---

# Pub/Sub vs Message Queues

| Feature | Pub/Sub | Queue |
|----------|----------|-------|
| Broadcast | ✅ | ❌ |
| One Consumer | ❌ | ✅ |
| Persistence | ❌ | Usually ✅ |
| Replay | ❌ | Usually ✅ |

---

# Common Production Use Cases

Redis Pub/Sub is commonly used for:

- Live chat
- Notification broadcasting
- Cache invalidation
- WebSocket messaging
- Monitoring alerts
- Multiplayer games
- Service notifications
- Distributed signaling
- Real-time dashboards
- Feature toggle broadcasts

---

# Common Mistakes

## Expecting Persistence

Messages disappear immediately after delivery.

```
Publisher

↓

Redis

↓

Subscriber Offline

↓

Message Lost
```

Use Redis Streams when persistence is required.

---

## Using Pub/Sub for Job Queues

Pub/Sub is not designed for:

- Reliable processing
- Retries
- Acknowledgements

Use Streams instead.

---

## Publishing Large Payloads

Avoid sending large JSON documents.

Instead:

```
Publish

↓

Object ID

↓

Consumer Reads Object
```

This reduces network traffic.

---

## Too Many Channels

Creating thousands of channels may complicate monitoring.

Use consistent naming conventions.

---

# Best Practices

- Keep messages lightweight.
- Use descriptive channel names.
- Use prefixes for channel organization.
- Prefer Streams for reliable messaging.
- Design subscribers to reconnect automatically.
- Avoid using Pub/Sub for critical business events.
- Monitor subscriber counts.
- Secure channels in multi-tenant environments.

---

# Performance Considerations

| Command | Complexity |
|----------|------------|
| PUBLISH | O(N) |
| SUBSCRIBE | O(1) |
| PSUBSCRIBE | O(1) |
| UNSUBSCRIBE | O(1) |
| PUNSUBSCRIBE | O(1) |
| PUBSUB CHANNELS | O(N) |
| PUBSUB NUMSUB | O(N) |
| PUBSUB NUMPAT | O(1) |

*N = number of channels or subscribers, depending on the operation.*

---

# Production Considerations

For production deployments:

- Use Pub/Sub only for transient, real-time events.
- Do not rely on Pub/Sub for guaranteed message delivery.
- Implement automatic subscriber reconnection logic.
- Monitor subscriber counts and channel activity.
- Use Redis Streams or a dedicated message broker when message durability, retries, or acknowledgements are required.
- Combine Pub/Sub with WebSocket gateways for scalable real-time applications.
- Establish clear channel naming conventions (for example, `orders.created`, `notifications.email`, `cache.invalidate`).

---

# Pub/Sub Workflow

```
                Publisher
                    │
                    ▼
         PUBLISH notifications
                    │
                    ▼
            Redis Pub/Sub Channel
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
 Subscriber A   Subscriber B   Subscriber C
      │             │             │
      ▼             ▼             ▼
Receive Event  Receive Event  Receive Event
```

---

# Summary

Redis Pub/Sub provides a fast and efficient mechanism for broadcasting real-time messages to multiple subscribers. It is ideal for applications where low latency is more important than message durability, such as chat systems, live dashboards, WebSocket notifications, and cache invalidation. Since messages are not persisted or acknowledged, Pub/Sub should not be used for critical workflows that require guaranteed delivery. For those scenarios, Redis Streams offer a more robust alternative.

---

# Key Takeaways

- `PUBLISH` sends a message to a channel.
- `SUBSCRIBE` listens for messages on one or more channels.
- `PSUBSCRIBE` enables wildcard-based subscriptions.
- Messages are delivered only to currently connected subscribers.
- Pub/Sub provides **broadcast messaging**, not queue semantics.
- Messages are **not persisted** and cannot be replayed.
- Use Pub/Sub for live notifications and Streams for reliable event processing.
- Keep payloads lightweight and organize channels using consistent naming conventions.