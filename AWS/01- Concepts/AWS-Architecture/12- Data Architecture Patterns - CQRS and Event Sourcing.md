# Data Architecture Patterns — CQRS and Event Sourcing

## CQRS (Command Query Responsibility Segregation)

Separates the model used to **write** data (commands) from the model used to **read** data (queries) — rather than one model trying to serve both well.

```text
Write Path:  Command → Write Model → Write Database
Read Path:   Query   → Read Model  → Read Database (optimized for queries)
```

## Why Separate Them

A write model optimized for consistency and business-rule enforcement (normalized, transactional) is often a poor fit for read-heavy access patterns that want denormalized, pre-joined, query-optimized data. CQRS lets each side use the data shape and even the database technology best suited to its job — e.g., DynamoDB or Aurora for writes, OpenSearch or a denormalized read replica for queries.

## The Synchronization Problem CQRS Introduces

If reads and writes use separate stores, something has to keep the read store updated as writes happen — typically via events published on write, consumed to update the read model asynchronously. This means the read model is **eventually consistent** with the write model, not immediately consistent — a read immediately after a write may not yet reflect it.

## Event Sourcing

Instead of storing only the *current state* of an entity, store the full sequence of events that led to that state. Current state is derived by replaying events, not stored directly as the source of truth.

```text
Traditional: Account balance = $500 (current state stored directly)

Event Sourced:
  AccountOpened ($0)
  Deposited ($300)
  Deposited ($300)
  Withdrew ($100)
  → Current balance ($500) is derived by replaying these events
```

## Why Event Sourcing Is Powerful — and Heavy

**Benefits:** a complete audit trail is inherent to the model (not a bolted-on log); you can answer "what did this look like at any point in time" trivially; new read models can be built later by replaying historical events, even for questions nobody thought to ask when the events were first recorded.

**Costs:** replaying a long event history to reconstruct current state is slow without periodic **snapshots**; the mental model is genuinely more complex for a team to learn and operate; querying "current state" requires either replay or a separately maintained projection (which is CQRS's read model, in practice — the two patterns are frequently used together for exactly this reason).

## AWS Building Blocks

| Need | AWS Service |
|---|---|
| Event store | DynamoDB (with an append-only table design) or Kinesis |
| Event replay/streaming to build read models | Kinesis, DynamoDB Streams, EventBridge Pipes |
| Read-optimized query store | OpenSearch, DynamoDB (denormalized), ElastiCache |

## Senior-Level Considerations

- Both patterns are frequently reached for by teams who don't actually need their complexity — a straightforward CRUD service with a single well-indexed database is often the right answer, and CQRS/Event Sourcing earn their complexity cost specifically when audit history, complex read patterns, and write/read scaling needs genuinely diverge
- If you adopt Event Sourcing, plan for snapshotting from day one, not as a later optimization — the "replay everything" cost only gets worse as event history grows
- CQRS without Event Sourcing is common and much lighter-weight — you can separate read and write *models* while still storing current state (not a full event log) on the write side
