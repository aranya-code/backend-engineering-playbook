# Architecture Decision Records (ADRs)

Not an AWS service — a practice. Included here because documenting *why* an architectural decision was made is as much a senior-level skill as making the decision itself, and its absence is a recurring, painful gap in real codebases.

## What an ADR Is

A short, immutable document capturing a single architectural decision: the context that led to it, the decision itself, and the consequences (including trade-offs knowingly accepted). Once written, an ADR isn't edited to reflect new information — a new ADR supersedes it, preserving the historical record of what was actually known and decided at the time.

## A Minimal ADR Template

```text
# ADR 012: Use SQS for Order Processing Instead of Direct Synchronous Calls

## Status
Accepted

## Context
The Order Service currently calls Inventory and Payment synchronously.
A Payment Service outage on 2024-03-02 caused Order Service to become
unresponsive as well, despite Order Service itself having no bug.

## Decision
Introduce an SQS queue between Order Service and Payment Service.
Order Service publishes an event and returns immediately; Payment
Service consumes asynchronously.

## Consequences
- Order Service availability no longer depends on Payment Service being up
- Order confirmation is no longer immediate — UI must reflect a
  "processing" state rather than instant confirmation
- Requires idempotent payment processing, since SQS delivers at-least-once
```

## Why This Matters More Than It Seems

Six months after a decision, "why did we do it this way?" is one of the most common and most expensive questions a team asks — expensive because, without a record, answering it requires either finding whoever made the decision (if they're still on the team) or re-deriving the reasoning from scratch, sometimes leading someone to "fix" a deliberate trade-off because its rationale was lost.

## When to Write One

Any decision that would be genuinely costly to reverse, that involves a real trade-off (not an obviously-correct choice), or that a future engineer is likely to question without the original context. Not every decision needs one — the discipline is in judgment about which decisions matter enough to record.

## Senior-Level Considerations

- ADRs are for the team's future self as much as for anyone new joining — the person most likely to ask "wait, why is this like this?" is often the same person who made the decision, eighteen months later, having forgotten the context
- Keep them short. An ADR that takes twenty minutes to write and two minutes to read gets written and read; a lengthy design document often gets neither
- Storing ADRs directly alongside the code they describe (in the same repo, like this playbook does with its own notes) keeps them discoverable in the place people are already looking
