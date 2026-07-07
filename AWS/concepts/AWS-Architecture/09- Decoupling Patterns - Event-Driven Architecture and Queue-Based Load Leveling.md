# Decoupling Patterns — Event-Driven Architecture and Queue-Based Load Leveling

## The Problem: Synchronous Coupling

If Service A calls Service B synchronously and waits for a response, A's availability is now capped by B's availability — A can never be more reliable than the least reliable thing it directly, synchronously depends on. This compounds across a chain of synchronous calls.

## Event-Driven Architecture

Services communicate by publishing and reacting to events, rather than calling each other directly. A producer publishes "OrderPlaced" without knowing or caring what (if anything) consumes it; consumers subscribe to events relevant to them.

```text
Order Service → publishes "OrderPlaced" event
                    ↓                    ↓
          Inventory Service      Notification Service
          (reacts independently)  (reacts independently)
```

**Benefit:** the Order Service's availability no longer depends on the Inventory or Notification services being up at that exact moment — they process the event whenever they're able to.

## Queue-Based Load Leveling

Inserting a queue (SQS) between a producer and consumer so bursts of incoming work are absorbed by the queue rather than overwhelming the consumer directly.

```text
Traffic Spike → SQS Queue (absorbs the burst) → Consumer processes at its own sustainable rate
```

This converts a burst that could overwhelm a fixed-capacity consumer into a smoother, sustained processing rate — the queue acts as a shock absorber.

## AWS Building Blocks

| Service | Role |
|---|---|
| SQS | Point-to-point queue — one message, processed by one consumer |
| SNS | Pub/Sub — one message, fanned out to multiple subscribers |
| EventBridge | Event bus with content-based routing rules across many producers/consumers |
| Kinesis | High-throughput streaming for ordered, replayable event data |

## Trade-offs of Going Async

- **Gained:** independent scaling and availability per service; natural load leveling; easier to add new consumers later without touching the producer
- **Lost:** immediate consistency (the producer doesn't know the outcome right away); harder end-to-end debugging (a request's effects are now spread across time and services rather than a single traceable call stack); eventual consistency becomes something the whole system — and its users — have to accept

## Senior-Level Considerations

- Not everything should be async — a login request needs a synchronous answer; a request to generate a large report probably doesn't. The decision hinges on whether the caller genuinely needs to wait for the result before doing anything else
- Event-driven systems need their own tracing strategy (correlation IDs propagated through events) since a distributed trace can't rely on a single unbroken call stack the way a synchronous chain can
- A queue absorbing a burst doesn't mean the burst is "handled" — if the consumer's average processing rate is genuinely lower than the sustained arrival rate (not just a burst), the queue will grow indefinitely; load leveling smooths spikes, it doesn't create capacity that doesn't exist
