# Decoupling Patterns — Pub/Sub and Fan-Out

## Pub/Sub

A publisher sends a message without knowing who (if anyone) will consume it; subscribers register interest and receive a copy independently.

## The Fan-Out Pattern on AWS

A very common combination: SNS as the pub/sub layer, fanning a single published message out to multiple SQS queues, each consumed independently by a different service.

```text
                    → SQS Queue A → Service A
SNS Topic (publish) → SQS Queue B → Service B
                    → SQS Queue C → Service C
```

## Why SNS + SQS, Not SNS Alone

SNS alone can push directly to subscribers (HTTP endpoints, Lambda, email, etc.), but pushing directly means a slow or temporarily unavailable subscriber can lose messages or apply backpressure poorly. Putting an SQS queue between SNS and each consumer gives every consumer its own durable buffer — if Service B is down for ten minutes, its messages simply wait in its queue rather than being lost or blocking the other consumers.

## Benefits of Fan-Out

- Adding a new consumer (a new SQS queue subscribed to the same SNS topic) requires **zero changes** to the publisher or to existing consumers — this is the core promise of decoupling actually paying off
- Each consumer processes at its own pace, with its own retry and DLQ behavior, fully isolated from the others
- The publisher's job stays simple: publish once, don't worry about who's listening

## Ordering Considerations

Standard SNS/SQS do not guarantee message ordering across the system. If strict ordering matters (e.g., "CreateOrder" must be processed before "CancelOrder" for the same order), FIFO variants of SNS and SQS provide ordering *within a message group*, at some throughput cost compared to standard queues.

## Senior-Level Considerations

- Fan-out is a strong default for "I need multiple independent things to happen when X occurs" — resist the temptation to have the publisher call each consumer directly just because there are only two or three today; that coupling tends to grow, not shrink
- Idempotent consumers matter here too — at-least-once delivery (the norm for SQS) means a consumer may see the same message more than once, and must handle that safely
- Fan-out multiplies the "blast radius" question: a malformed event published once now potentially breaks every subscriber simultaneously, which argues for schema validation at publish time, not just per-consumer
