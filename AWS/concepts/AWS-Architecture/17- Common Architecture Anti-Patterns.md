# Common Architecture Anti-Patterns

Recognizing these is as valuable at a senior level as knowing the patterns themselves — often more so, since anti-patterns tend to look reasonable in the moment they're introduced.

## The Distributed Monolith

Services are deployed independently but are so tightly coupled (synchronous call chains, shared databases, lockstep deployment requirements) that they must effectively be released together to work. Combines the operational overhead of microservices with the coupling of a monolith, gaining neither's benefits.

## Chatty Services

Two services that need many small, synchronous round-trips to complete one logical operation. Each hop adds latency and a new failure point; the fix is usually redesigning the API boundary (batch the calls, or use an event that carries enough data to avoid the round-trip entirely) rather than optimizing the individual calls.

## The Shared Database Anti-Pattern

Multiple services reading and writing the same database directly "because it's faster than building an API." This silently recreates tight coupling — any service can be broken by a schema change made by a team that doesn't know it's depended upon — while looking, superficially, like a clean microservices setup.

## Premature Optimization for Scale You Don't Have

Building a fully sharded, multi-region, event-sourced architecture for a product with a hundred users. The complexity cost is paid immediately and continuously; the scale benefit may never be needed, and if it is, requirements will likely have changed enough by then that the early design was speculative anyway.

## No Idempotency, Retries Everywhere

Adding retries (a good instinct, per the Backoff/Jitter file) to operations that aren't idempotent — resulting in duplicate charges, duplicate emails, or duplicate side effects exactly during the failure conditions retries were meant to handle gracefully.

## Ignoring Backpressure

A fast producer feeding a slower consumer with no queue, no rate limiting, and no bounded buffer — the consumer either falls further and further behind (unbounded queue growth) or falls over entirely. Queue-based load leveling exists specifically to prevent this, but only if it's actually in the design.

## Single Point of Failure Hiding in a "Redundant" Design

A system with multiple AZs and instances that all depend on one un-replicated component — a single NAT gateway, a single self-managed database with no standby, a single hardcoded IP somewhere in configuration. Redundancy has to be checked end-to-end, not assumed because the visible parts of the diagram look redundant.

## Treating Monitoring as an Afterthought

Building the system first, adding logging/metrics/alarms later "once it's in production." By the time an incident happens, the team is debugging blind, and the fastest fix is usually just "add the observability that should have existed from day one."

## Senior-Level Takeaway

Most anti-patterns aren't the result of ignorance — they're reasonable-sounding shortcuts taken under real time pressure that don't get revisited once the system is live. Part of the senior role is noticing which shortcuts are being taken silently, and making the resulting trade-off an explicit decision rather than an accident.
